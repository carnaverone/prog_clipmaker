"""
Video slideshow generation with Ken Burns effect
"""

import os
import sys
import re
import random
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass

from .config import VideoConfig, WatermarkConfig, TitleConfig, TRANSITIONS


@dataclass
class ImageInfo:
    """Information about an image file"""
    path: str
    index: int
    zoom_in: bool
    pan_left_to_right: bool
    transition: str = "fade"


@dataclass
class ProgressInfo:
    """Progress information during encoding"""
    frame: int = 0
    fps: float = 0.0
    time_encoded: float = 0.0
    speed: float = 0.0
    percent: float = 0.0
    eta_seconds: float = 0.0


class SlideshowGenerator:
    """Generate Ken Burns style slideshow videos"""
    
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
    SUPPORTED_AUDIO = {'.wav', '.mp3', '.aac', '.flac', '.ogg', '.m4a'}
    
    def __init__(
        self,
        config: VideoConfig,
        watermark: Optional[WatermarkConfig] = None,
        title: Optional[TitleConfig] = None
    ):
        self.config = config
        self.watermark = watermark
        self.title = title
        self.images: List[ImageInfo] = []
        self._progress_info = ProgressInfo()
        self._stop_flag = False
    
    def find_images(self, path: str) -> List[str]:
        """Find all supported images in a directory or file list"""
        images = []
        path = Path(path)
        
        if path.is_file():
            if path.suffix.lower() in self.SUPPORTED_FORMATS:
                images.append(str(path))
        elif path.is_dir():
            for ext in self.SUPPORTED_FORMATS:
                images.extend([str(p) for p in path.glob(f'*{ext}')])
                images.extend([str(p) for p in path.glob(f'*{ext.upper()}')])
        
        return sorted(set(images))
    
    def prepare_images(self, image_paths: List[str]) -> List[ImageInfo]:
        """Prepare image list with effects parameters"""
        if not image_paths:
            raise ValueError("No images found")
        
        # Apply ordering
        if self.config.shuffle:
            random.shuffle(image_paths)
        elif self.config.reverse:
            image_paths = list(reversed(image_paths))
        
        # Get transition list for random mode
        transition_list = list(TRANSITIONS.keys())
        
        images = []
        for i, path in enumerate(image_paths):
            # Determine zoom direction
            if self.config.zoom_direction == "in":
                zoom_in = True
            elif self.config.zoom_direction == "out":
                zoom_in = False
            elif self.config.zoom_direction == "random":
                zoom_in = random.choice([True, False])
            else:  # alternate
                zoom_in = (i % 2 == 0)
            
            # Determine pan direction
            if self.config.pan_direction == "left":
                pan_lr = True
            elif self.config.pan_direction == "right":
                pan_lr = False
            elif self.config.pan_direction == "random":
                pan_lr = random.choice([True, False])
            else:  # alternate
                pan_lr = (i % 2 == 0)
            
            # Determine transition
            if self.config.transition == "random":
                transition = random.choice(transition_list)
            else:
                transition = self.config.transition
            
            images.append(ImageInfo(
                path=path,
                index=i,
                zoom_in=zoom_in,
                pan_left_to_right=pan_lr,
                transition=transition
            ))
        
        self.images = images
        return images
    
    def _build_filter_complex(
        self,
        with_watermark: bool = False,
        with_title: bool = False
    ) -> str:
        """Build FFmpeg filter_complex string"""
        cfg = self.config
        num_frames = max(2, int(round(cfg.duration * cfg.fps)))
        zoom = cfg.zoom_intensity
        pan = cfg.pan_intensity
        y_pos = cfg.vertical_position
        
        filters = []
        
        # Calculate input offset for watermark/title
        input_offset = 0
        if with_title and self.title and self.title.enabled:
            input_offset += 1
        
        # Process each image
        for img in self.images:
            i = img.index
            input_idx = i + input_offset
            frac = f"(on/{num_frames - 1})"
            
            # Zoom expression
            if img.zoom_in:
                z_expr = f"(1+{zoom}*{frac})"
            else:
                z_expr = f"({1 + zoom}-{zoom}*{frac})"
            
            # Pan X expression
            if img.pan_left_to_right:
                x_expr = f"(iw-ow)*({pan}*{frac})"
            else:
                x_expr = f"(iw-ow)*({pan}*(1-{frac}))"
            
            # Y position
            y_expr = f"(ih-oh)*{y_pos}"
            
            filters.append(
                f"[{input_idx}:v]"
                f"scale={cfg.width * 2}:{cfg.height * 2}:force_original_aspect_ratio=increase,"
                f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
                f"d={num_frames}:s={cfg.width}x{cfg.height}:fps={cfg.fps},"
                f"format=yuv420p[v{i}]"
            )
        
        # Build crossfade chain with transitions
        if len(self.images) > 1:
            cur = "[v0]"
            t = cfg.duration - cfg.crossfade
            
            for i in range(1, len(self.images)):
                trans = self.images[i].transition
                # Validate transition
                if trans not in TRANSITIONS:
                    trans = "fade"
                
                filters.append(
                    f"{cur}[v{i}]xfade=transition={trans}:"
                    f"duration={cfg.crossfade}:offset={t}[x{i}]"
                )
                cur = f"[x{i}]"
                t += cfg.duration - cfg.crossfade
            
            # Final output label
            final_label = "vout"
            filters.append(f"{cur}format=yuv420p[{final_label}]")
        else:
            final_label = "vout"
            filters.append(f"[v0]format=yuv420p[{final_label}]")
        
        # Add watermark if enabled
        if with_watermark and self.watermark and self.watermark.enabled:
            wm = self.watermark
            # Calculate position
            positions = {
                "top-left": f"x={wm.margin}:y={wm.margin}",
                "top-right": f"x=W-w-{wm.margin}:y={wm.margin}",
                "bottom-left": f"x={wm.margin}:y=H-h-{wm.margin}",
                "bottom-right": f"x=W-w-{wm.margin}:y=H-h-{wm.margin}",
                "center": "x=(W-w)/2:y=(H-h)/2"
            }
            pos = positions.get(wm.position, positions["bottom-right"])
            
            # Get watermark input index
            wm_input = len(self.images) + input_offset + 1  # After audio
            
            filters.append(
                f"[{wm_input}:v]scale=iw*{wm.scale}:-1,format=rgba,"
                f"colorchannelmixer=aa={wm.opacity}[wm]"
            )
            filters.append(
                f"[{final_label}][wm]overlay={pos}[vfinal]"
            )
            final_label = "vfinal"
        
        # Add title overlay as intro if enabled
        if with_title and self.title and self.title.enabled:
            # Title is handled as a separate input, will be concatenated
            pass
        
        # Replace last label with [v] for output
        filters[-1] = filters[-1].rsplit('[', 1)[0] + '[v]'
        
        return ";".join(filters)
    
    def _build_title_filter(self) -> str:
        """Build filter for title card"""
        if not self.title or not self.title.enabled:
            return ""
        
        t = self.title
        cfg = self.config
        
        # Create title card with text
        filters = []
        
        # Background color
        filters.append(
            f"color=c={t.background_color}:s={cfg.width}x{cfg.height}:"
            f"d={t.duration}:r={cfg.fps}[bg]"
        )
        
        # Main title text
        title_y = f"(h-text_h)/2-{t.subtitle_size}" if t.subtitle else "(h-text_h)/2"
        filters.append(
            f"[bg]drawtext=text='{t.text}':"
            f"fontsize={t.font_size}:fontcolor={t.font_color}:"
            f"x=(w-text_w)/2:y={title_y}[titled]"
        )
        
        # Subtitle if present
        if t.subtitle:
            filters.append(
                f"[titled]drawtext=text='{t.subtitle}':"
                f"fontsize={t.subtitle_size}:fontcolor={t.font_color}:"
                f"x=(w-text_w)/2:y=(h-text_h)/2+{t.font_size//2}[titlesub]"
            )
            final = "titlesub"
        else:
            final = "titled"
        
        # Fade in/out
        filters.append(
            f"[{final}]fade=t=in:st=0:d={t.fade_in},"
            f"fade=t=out:st={t.duration - t.fade_out}:d={t.fade_out}[title]"
        )
        
        return ";".join(filters)
    
    def _parse_ffmpeg_progress(self, line: str, total_duration: float) -> Optional[ProgressInfo]:
        """Parse FFmpeg progress output"""
        info = self._progress_info
        
        # Parse frame
        match = re.search(r'frame=\s*(\d+)', line)
        if match:
            info.frame = int(match.group(1))
        
        # Parse fps
        match = re.search(r'fps=\s*([\d.]+)', line)
        if match:
            info.fps = float(match.group(1))
        
        # Parse time
        match = re.search(r'time=\s*(\d+):(\d+):(\d+\.?\d*)', line)
        if match:
            h, m, s = match.groups()
            info.time_encoded = int(h) * 3600 + int(m) * 60 + float(s)
            
            # Calculate percent and ETA
            if total_duration > 0:
                info.percent = min(100, (info.time_encoded / total_duration) * 100)
                if info.fps > 0:
                    remaining = total_duration - info.time_encoded
                    info.eta_seconds = remaining / (info.fps / self.config.fps) if info.fps > 0 else 0
        
        # Parse speed
        match = re.search(r'speed=\s*([\d.]+)x', line)
        if match:
            info.speed = float(match.group(1))
        
        return info
    
    def generate(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        progress_bar_callback: Optional[Callable[[ProgressInfo], None]] = None,
        preview: bool = False
    ) -> Tuple[bool, str]:
        """
        Generate slideshow video
        
        Args:
            image_path: Directory with images or single image
            audio_path: Audio file path
            output_path: Output video file path
            progress_callback: Optional callback for text progress updates
            progress_bar_callback: Optional callback for progress bar updates
            preview: Generate low-quality preview
        
        Returns:
            Tuple of (success, message)
        """
        self._stop_flag = False
        
        # Validate audio
        audio = Path(audio_path)
        if not audio.exists():
            return False, f"Audio file not found: {audio_path}"
        if audio.suffix.lower() not in self.SUPPORTED_AUDIO:
            return False, f"Unsupported audio format: {audio.suffix}"
        
        # Find and prepare images
        image_files = self.find_images(image_path)
        if not image_files:
            return False, f"No images found in: {image_path}"
        
        self.prepare_images(image_files)
        
        if progress_callback:
            progress_callback(f"Found {len(self.images)} images")
        
        # Adjust config for preview mode
        original_config = None
        if preview:
            original_config = (
                self.config.width, self.config.height,
                self.config.fps, self.config.crf, self.config.preset
            )
            self.config.width = 640
            self.config.height = 360
            self.config.fps = 15
            self.config.crf = 35
            self.config.preset = "ultrafast"
        
        # Check for watermark file
        has_watermark = (
            self.watermark and 
            self.watermark.enabled and 
            os.path.exists(self.watermark.image_path)
        )
        
        # Build FFmpeg command
        cmd = ["ffmpeg", "-y", "-hide_banner", "-progress", "pipe:1", "-loglevel", "error"]
        
        # Input images
        for img in self.images:
            cmd.extend(["-loop", "1", "-t", str(self.config.duration), "-i", img.path])
        
        # Input audio
        cmd.extend(["-i", audio_path])
        
        # Watermark input
        if has_watermark:
            cmd.extend(["-i", self.watermark.image_path])
        
        # Filter complex
        filter_complex = self._build_filter_complex(with_watermark=has_watermark)
        cmd.extend(["-filter_complex", filter_complex])
        
        # Output mapping and encoding
        cmd.extend([
            "-map", "[v]",
            "-map", f"{len(self.images)}:a",
            "-c:v", "libx264",
            "-crf", str(self.config.crf),
            "-preset", self.config.preset,
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", self.config.audio_bitrate,
            "-shortest",
            output_path
        ])
        
        if progress_callback:
            mode = "preview" if preview else "full quality"
            progress_callback(f"Starting video generation ({mode})...")
        
        # Estimate total duration for progress
        total_duration = self.estimate_duration()
        
        # Run FFmpeg with progress tracking
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Read progress
            while True:
                if self._stop_flag:
                    process.terminate()
                    return False, "Generation cancelled"
                
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line and progress_bar_callback:
                    info = self._parse_ffmpeg_progress(line, total_duration)
                    if info:
                        progress_bar_callback(info)
            
            # Get final result
            _, stderr = process.communicate()
            
            # Restore original config if preview
            if original_config:
                (self.config.width, self.config.height,
                 self.config.fps, self.config.crf, self.config.preset) = original_config
            
            if process.returncode != 0:
                return False, f"FFmpeg error: {stderr}"
            
            # Get output file size
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                return True, f"Video created: {output_path} ({size_mb:.1f} MB)"
            else:
                return False, "Output file was not created"
                
        except FileNotFoundError:
            return False, "FFmpeg not found. Please install FFmpeg."
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def generate_preview(
        self,
        image_path: str,
        audio_path: str,
        output_path: str = "preview.mp4",
        progress_callback: Optional[Callable[[str], None]] = None,
        progress_bar_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> Tuple[bool, str]:
        """Generate a quick low-quality preview"""
        return self.generate(
            image_path, audio_path, output_path,
            progress_callback, progress_bar_callback,
            preview=True
        )
    
    def cancel(self):
        """Cancel ongoing generation"""
        self._stop_flag = True
    
    def estimate_duration(self) -> float:
        """Estimate total video duration in seconds"""
        if not self.images:
            return 0
        
        n = len(self.images)
        total = self.config.duration * n - self.config.crossfade * (n - 1)
        
        # Add title duration if enabled
        if self.title and self.title.enabled:
            total += self.title.duration
        
        return max(0, total)
    
    def get_summary(self) -> dict:
        """Get generation summary"""
        return {
            "images": len(self.images),
            "duration_per_image": self.config.duration,
            "total_duration": self.estimate_duration(),
            "resolution": f"{self.config.width}x{self.config.height}",
            "fps": self.config.fps,
            "zoom_intensity": self.config.zoom_intensity,
            "pan_intensity": self.config.pan_intensity,
            "transition": self.config.transition,
            "shuffle": self.config.shuffle,
            "watermark": self.watermark.enabled if self.watermark else False,
            "title": self.title.text if self.title and self.title.enabled else None
        }


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available"""
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_version() -> Optional[str]:
    """Get FFmpeg version string"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            first_line = result.stdout.split('\n')[0]
            return first_line
    except:
        pass
    return None


def format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_progress_bar(percent: float, width: int = 30) -> str:
    """Create a text progress bar"""
    filled = int(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percent:.1f}%"
