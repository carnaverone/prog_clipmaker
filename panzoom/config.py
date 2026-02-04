"""
Configuration management for PanZoom Slideshow
"""

import os
import yaml
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from pathlib import Path


@dataclass
class VideoConfig:
    """Video generation settings"""
    duration: float = 10.0          # Duration per image (seconds)
    crossfade: float = 2.0          # Crossfade duration (seconds)
    fps: int = 60                   # Frames per second
    width: int = 1920               # Output width
    height: int = 1080              # Output height
    
    # Pan & Zoom settings
    zoom_intensity: float = 0.08    # Zoom amount (0.0 - 0.2)
    pan_intensity: float = 0.25     # Pan amount (0.0 - 1.0)
    zoom_direction: str = "alternate"  # "in", "out", "alternate", "random"
    pan_direction: str = "alternate"   # "left", "right", "alternate", "random"
    vertical_position: float = 0.3  # Y position (0=top, 0.5=center, 1=bottom)
    
    # Transition
    transition: str = "fade"        # Transition type
    
    # Image ordering
    shuffle: bool = False           # Random image order
    reverse: bool = False           # Reverse order
    
    # Quality
    crf: int = 18                   # Quality (0-51, lower=better)
    preset: str = "slow"            # Encoding preset
    audio_bitrate: str = "320k"     # Audio quality


@dataclass
class AudioConfig:
    """Audio processing settings"""
    loudness: float = -14.0         # Target LUFS
    lra: float = 7.0                # Loudness range
    true_peak: float = -1.5         # True peak limit
    sample_rate: int = 44100        # Output sample rate
    channels: int = 2               # Output channels
    remove_silence: bool = True     # Remove silence at start/end
    silence_threshold: str = "-50dB"  # Silence detection threshold


@dataclass
class TextOverlay:
    """Text overlay settings"""
    enabled: bool = False
    text: str = ""
    position: str = "bottom"        # top, center, bottom
    font_size: int = 48
    font_color: str = "white"
    background: bool = True
    background_color: str = "black@0.5"
    duration: float = 0.0           # 0 = full duration
    fade_in: float = 1.0
    fade_out: float = 1.0


@dataclass
class WatermarkConfig:
    """Watermark settings"""
    enabled: bool = False
    image_path: str = ""
    position: str = "bottom-right"  # top-left, top-right, bottom-left, bottom-right, center
    opacity: float = 0.7
    scale: float = 0.15             # Size relative to video width
    margin: int = 20


@dataclass
class TitleConfig:
    """Title/intro settings"""
    enabled: bool = False
    text: str = ""
    subtitle: str = ""
    duration: float = 4.0
    font_size: int = 72
    subtitle_size: int = 36
    font_color: str = "white"
    background_color: str = "black"
    fade_in: float = 1.0
    fade_out: float = 1.0


@dataclass 
class ProjectConfig:
    """Main project configuration"""
    video: VideoConfig = field(default_factory=VideoConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    watermark: WatermarkConfig = field(default_factory=WatermarkConfig)
    title: TitleConfig = field(default_factory=TitleConfig)
    
    # Metadata
    artist: str = "Carnaverone Studio"
    genre: str = "Instrumental"
    
    # Paths
    output_dir: str = "output"


# Available transitions (FFmpeg xfade)
TRANSITIONS = {
    "fade": "Fondu classique",
    "fadeblack": "Fondu par le noir",
    "fadewhite": "Fondu par le blanc",
    "wipeleft": "Balayage vers la gauche",
    "wiperight": "Balayage vers la droite",
    "wipeup": "Balayage vers le haut",
    "wipedown": "Balayage vers le bas",
    "slideleft": "Glissement vers la gauche",
    "slideright": "Glissement vers la droite",
    "slideup": "Glissement vers le haut",
    "slidedown": "Glissement vers le bas",
    "smoothleft": "Glissement fluide gauche",
    "smoothright": "Glissement fluide droite",
    "circlecrop": "Cercle",
    "circleclose": "Cercle fermeture",
    "circleopen": "Cercle ouverture",
    "dissolve": "Dissolution",
    "pixelize": "Pixelisation",
    "radial": "Radial",
    "hblur": "Flou horizontal",
    "hlslice": "Tranches horizontales",
    "vlslice": "Tranches verticales",
    "zoomin": "Zoom avant",
    "squeezeh": "Compression horizontale",
    "squeezev": "Compression verticale",
}

# Export profiles for different platforms
EXPORT_PROFILES = {
    "youtube": {
        "name": "YouTube HD",
        "width": 1920,
        "height": 1080,
        "fps": 60,
        "crf": 18,
        "preset": "slow",
        "audio_bitrate": "320k",
        "description": "Optimal pour YouTube (1080p60)"
    },
    "youtube4k": {
        "name": "YouTube 4K",
        "width": 3840,
        "height": 2160,
        "fps": 60,
        "crf": 18,
        "preset": "slow",
        "audio_bitrate": "320k",
        "description": "YouTube 4K UHD"
    },
    "instagram_feed": {
        "name": "Instagram Feed",
        "width": 1080,
        "height": 1080,
        "fps": 30,
        "crf": 20,
        "preset": "medium",
        "audio_bitrate": "256k",
        "description": "Instagram carré (1:1)"
    },
    "instagram_portrait": {
        "name": "Instagram Portrait",
        "width": 1080,
        "height": 1350,
        "fps": 30,
        "crf": 20,
        "preset": "medium",
        "audio_bitrate": "256k",
        "description": "Instagram portrait (4:5)"
    },
    "instagram_reels": {
        "name": "Instagram Reels",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "crf": 20,
        "preset": "medium",
        "audio_bitrate": "256k",
        "description": "Instagram/TikTok vertical (9:16)"
    },
    "tiktok": {
        "name": "TikTok",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "crf": 20,
        "preset": "medium",
        "audio_bitrate": "256k",
        "description": "TikTok vertical (9:16)"
    },
    "facebook": {
        "name": "Facebook",
        "width": 1280,
        "height": 720,
        "fps": 30,
        "crf": 22,
        "preset": "medium",
        "audio_bitrate": "192k",
        "description": "Facebook 720p"
    },
    "twitter": {
        "name": "Twitter/X",
        "width": 1280,
        "height": 720,
        "fps": 30,
        "crf": 22,
        "preset": "medium",
        "audio_bitrate": "192k",
        "description": "Twitter/X 720p"
    },
    "preview": {
        "name": "Preview (rapide)",
        "width": 640,
        "height": 360,
        "fps": 15,
        "crf": 35,
        "preset": "ultrafast",
        "audio_bitrate": "96k",
        "description": "Aperçu rapide basse qualité"
    }
}

# Preset configurations
PRESETS = {
    "fast": {
        "duration": 6.0,
        "crossfade": 1.0,
        "fps": 30,
        "zoom_intensity": 0.04,
        "pan_intensity": 0.15,
        "preset": "fast",
        "crf": 23
    },
    "cinematic": {
        "duration": 12.0,
        "crossfade": 3.0,
        "fps": 60,
        "zoom_intensity": 0.06,
        "pan_intensity": 0.20,
        "preset": "slow",
        "crf": 16
    },
    "slow": {
        "duration": 15.0,
        "crossfade": 4.0,
        "fps": 60,
        "zoom_intensity": 0.04,
        "pan_intensity": 0.15,
        "preset": "slow",
        "crf": 18
    },
    "dynamic": {
        "duration": 8.0,
        "crossfade": 1.5,
        "fps": 60,
        "zoom_intensity": 0.12,
        "pan_intensity": 0.35,
        "preset": "medium",
        "crf": 20
    },
    "minimal": {
        "duration": 10.0,
        "crossfade": 2.0,
        "fps": 30,
        "zoom_intensity": 0.02,
        "pan_intensity": 0.10,
        "preset": "medium",
        "crf": 22
    }
}


def load_config(config_path: Optional[str] = None) -> ProjectConfig:
    """Load configuration from YAML file"""
    config = ProjectConfig()
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            
        if data:
            if 'video' in data:
                for key, value in data['video'].items():
                    if hasattr(config.video, key):
                        setattr(config.video, key, value)
            
            if 'audio' in data:
                for key, value in data['audio'].items():
                    if hasattr(config.audio, key):
                        setattr(config.audio, key, value)
            
            if 'watermark' in data:
                for key, value in data['watermark'].items():
                    if hasattr(config.watermark, key):
                        setattr(config.watermark, key, value)
            
            if 'title' in data:
                for key, value in data['title'].items():
                    if hasattr(config.title, key):
                        setattr(config.title, key, value)
            
            if 'artist' in data:
                config.artist = data['artist']
            if 'genre' in data:
                config.genre = data['genre']
            if 'output_dir' in data:
                config.output_dir = data['output_dir']
    
    return config


def save_config(config: ProjectConfig, config_path: str):
    """Save configuration to YAML file"""
    data = {
        'video': asdict(config.video),
        'audio': asdict(config.audio),
        'watermark': asdict(config.watermark),
        'title': asdict(config.title),
        'artist': config.artist,
        'genre': config.genre,
        'output_dir': config.output_dir
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def apply_preset(config: VideoConfig, preset_name: str) -> VideoConfig:
    """Apply a preset to video configuration"""
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(PRESETS.keys())}")
    
    preset = PRESETS[preset_name]
    for key, value in preset.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config


def apply_export_profile(config: VideoConfig, profile_name: str) -> VideoConfig:
    """Apply an export profile to video configuration"""
    if profile_name not in EXPORT_PROFILES:
        raise ValueError(f"Unknown profile: {profile_name}. Available: {list(EXPORT_PROFILES.keys())}")
    
    profile = EXPORT_PROFILES[profile_name]
    for key in ['width', 'height', 'fps', 'crf', 'preset', 'audio_bitrate']:
        if key in profile and hasattr(config, key):
            setattr(config, key, profile[key])
    
    return config


def get_transition_list() -> List[str]:
    """Get list of available transitions"""
    return list(TRANSITIONS.keys())


def get_export_profiles() -> dict:
    """Get all export profiles"""
    return EXPORT_PROFILES
