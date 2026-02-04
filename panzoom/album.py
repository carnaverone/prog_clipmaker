"""
Audio album preparation and normalization
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from .config import AudioConfig


@dataclass
class TrackInfo:
    """Information about an audio track"""
    original_path: str
    track_number: int
    clean_name: str
    output_path: str
    success: bool = False
    error: Optional[str] = None


class AlbumProcessor:
    """Process and normalize audio albums"""
    
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a'}
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.tracks: List[TrackInfo] = []
    
    def find_audio_files(self, path: str) -> List[str]:
        """Find all audio files in directory"""
        audio_files = []
        path = Path(path)
        
        if path.is_file():
            if path.suffix.lower() in self.SUPPORTED_FORMATS:
                audio_files.append(str(path))
        elif path.is_dir():
            for ext in self.SUPPORTED_FORMATS:
                audio_files.extend([str(p) for p in path.glob(f'*{ext}')])
                audio_files.extend([str(p) for p in path.glob(f'*{ext.upper()}')])
        
        return sorted(set(audio_files))
    
    def clean_filename(self, filename: str) -> str:
        """Clean up filename for display"""
        # Remove extension
        name = Path(filename).stem
        # Replace underscores with spaces
        name = name.replace('_', ' ')
        # Remove multiple spaces
        name = re.sub(r'\s+', ' ', name)
        # Trim
        name = name.strip()
        return name
    
    def prepare_tracks(self, audio_files: List[str], output_dir: str) -> List[TrackInfo]:
        """Prepare track list with output paths"""
        tracks = []
        
        os.makedirs(output_dir, exist_ok=True)
        
        for i, file_path in enumerate(audio_files, 1):
            clean_name = self.clean_filename(file_path)
            track_num = f"{i:02d}"
            output_name = f"{track_num} - {clean_name}.wav"
            output_path = os.path.join(output_dir, output_name)
            
            tracks.append(TrackInfo(
                original_path=file_path,
                track_number=i,
                clean_name=clean_name,
                output_path=output_path
            ))
        
        self.tracks = tracks
        return tracks
    
    def _build_audio_filter(self) -> str:
        """Build FFmpeg audio filter string"""
        cfg = self.config
        filters = []
        
        # Loudness normalization
        filters.append(
            f"loudnorm=I={cfg.loudness}:LRA={cfg.lra}:TP={cfg.true_peak}"
        )
        
        # Silence removal
        if cfg.remove_silence:
            filters.append(
                f"silenceremove=start_periods=1:start_duration=0.2:"
                f"start_threshold={cfg.silence_threshold}:"
                f"stop_periods=1:stop_duration=0.2:"
                f"stop_threshold={cfg.silence_threshold}"
            )
        
        return ",".join(filters)
    
    def process_track(self, track: TrackInfo) -> TrackInfo:
        """Process a single audio track"""
        cfg = self.config
        
        cmd = [
            "ffmpeg", "-y",
            "-hide_banner", "-loglevel", "warning",
            "-i", track.original_path,
            "-af", self._build_audio_filter(),
            "-ar", str(cfg.sample_rate),
            "-ac", str(cfg.channels),
            track.output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(track.output_path):
                track.success = True
            else:
                track.success = False
                track.error = result.stderr or "Unknown error"
                
        except Exception as e:
            track.success = False
            track.error = str(e)
        
        return track
    
    def process_album(
        self,
        input_path: str,
        output_dir: str,
        progress_callback=None
    ) -> Tuple[int, int, List[TrackInfo]]:
        """
        Process entire album
        
        Args:
            input_path: Directory with audio files
            output_dir: Output directory
            progress_callback: Optional callback for progress
        
        Returns:
            Tuple of (success_count, error_count, tracks)
        """
        # Find audio files
        audio_files = self.find_audio_files(input_path)
        if not audio_files:
            return 0, 0, []
        
        # Prepare tracks
        self.prepare_tracks(audio_files, output_dir)
        
        if progress_callback:
            progress_callback(f"Found {len(self.tracks)} audio files")
        
        # Process each track
        success_count = 0
        error_count = 0
        
        for track in self.tracks:
            if progress_callback:
                progress_callback(f"Processing: {track.clean_name}")
            
            self.process_track(track)
            
            if track.success:
                success_count += 1
            else:
                error_count += 1
        
        return success_count, error_count, self.tracks
    
    def generate_metadata(
        self,
        output_dir: str,
        album_name: str,
        artist: str,
        genre: str
    ) -> str:
        """Generate metadata file for album"""
        metadata_path = os.path.join(output_dir, "metadata.txt")
        
        lines = [
            f"ALBUM={album_name}",
            f"ARTIST={artist}",
            f"YEAR={datetime.now().year}",
            f"GENRE={genre}",
            "",
            "TRACKLIST:",
        ]
        
        for track in self.tracks:
            if track.success:
                lines.append(f"  {track.track_number:02d}. {track.clean_name}")
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return metadata_path
    
    def generate_cue_sheet(
        self,
        output_dir: str,
        album_name: str,
        artist: str
    ) -> str:
        """Generate CUE sheet for album"""
        cue_path = os.path.join(output_dir, f"{album_name}.cue")
        
        lines = [
            f'PERFORMER "{artist}"',
            f'TITLE "{album_name}"',
            ""
        ]
        
        for track in self.tracks:
            if track.success:
                lines.extend([
                    f'FILE "{os.path.basename(track.output_path)}" WAVE',
                    f"  TRACK {track.track_number:02d} AUDIO",
                    f'    TITLE "{track.clean_name}"',
                    f'    PERFORMER "{artist}"',
                    "    INDEX 01 00:00:00",
                    ""
                ])
        
        with open(cue_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return cue_path


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available"""
    return shutil.which("ffmpeg") is not None
