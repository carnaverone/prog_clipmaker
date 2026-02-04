"""
Command-line interface for PanZoom Slideshow
"""

import argparse
import sys
import os
from pathlib import Path

from . import __version__
from .config import (
    ProjectConfig, VideoConfig, AudioConfig, WatermarkConfig, TitleConfig,
    load_config, save_config, apply_preset, apply_export_profile,
    PRESETS, TRANSITIONS, EXPORT_PROFILES
)
from .slideshow import (
    SlideshowGenerator, check_ffmpeg, get_ffmpeg_version,
    format_time, format_progress_bar, ProgressInfo
)
from .album import AlbumProcessor


# Terminal colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    @classmethod
    def disable(cls):
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = ''
        cls.MAGENTA = cls.CYAN = cls.WHITE = cls.NC = ''
        cls.BOLD = cls.DIM = ''


def print_banner():
    """Print application banner"""
    print(f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════╗
║  {Colors.WHITE}PanZoom Slideshow{Colors.CYAN}  -  Ken Burns Video Generator         ║
║  {Colors.YELLOW}Version {__version__}{Colors.CYAN}                                           ║
╚═══════════════════════════════════════════════════════════╝{Colors.NC}
""")


def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.NC} {msg}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.NC} {msg}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.NC} {msg}")


def cmd_video(args):
    """Handle video generation command"""
    print_banner()
    
    # Check FFmpeg
    if not check_ffmpeg():
        print_error("FFmpeg not found. Please install FFmpeg first.")
        return 1
    
    # Load config
    config = load_config(args.config) if args.config else ProjectConfig()
    
    # Apply export profile if specified
    if args.export:
        try:
            apply_export_profile(config.video, args.export)
            profile = EXPORT_PROFILES[args.export]
            print_info(f"Using export profile: {profile['name']}")
        except ValueError as e:
            print_error(str(e))
            return 1
    
    # Apply preset if specified (after export profile so it can override)
    if args.preset:
        try:
            apply_preset(config.video, args.preset)
            print_info(f"Using preset: {args.preset}")
        except ValueError as e:
            print_error(str(e))
            return 1
    
    # Override with command line arguments
    if args.duration:
        config.video.duration = args.duration
    if args.crossfade:
        config.video.crossfade = args.crossfade
    if args.fps:
        config.video.fps = args.fps
    if args.width:
        config.video.width = args.width
    if args.height:
        config.video.height = args.height
    if args.zoom:
        config.video.zoom_intensity = args.zoom
    if args.pan:
        config.video.pan_intensity = args.pan
    if args.zoom_dir:
        config.video.zoom_direction = args.zoom_dir
    if args.pan_dir:
        config.video.pan_direction = args.pan_dir
    if args.transition:
        config.video.transition = args.transition
    if args.shuffle:
        config.video.shuffle = True
    if args.reverse:
        config.video.reverse = True
    if args.quality:
        config.video.crf = args.quality
    
    # Watermark configuration
    watermark = WatermarkConfig()
    if args.watermark:
        if os.path.exists(args.watermark):
            watermark.enabled = True
            watermark.image_path = args.watermark
            if args.watermark_pos:
                watermark.position = args.watermark_pos
            if args.watermark_opacity:
                watermark.opacity = args.watermark_opacity
            if args.watermark_scale:
                watermark.scale = args.watermark_scale
        else:
            print_warning(f"Watermark file not found: {args.watermark}")
    
    # Title configuration
    title = TitleConfig()
    if args.title:
        title.enabled = True
        title.text = args.title
        if args.subtitle:
            title.subtitle = args.subtitle
    
    # Validate inputs
    images_path = args.images or "."
    audio_path = args.audio
    output_path = args.output or "slideshow.mp4"
    is_preview = args.preview
    
    if not os.path.exists(images_path):
        print_error(f"Images path not found: {images_path}")
        return 1
    
    if not os.path.exists(audio_path):
        print_error(f"Audio file not found: {audio_path}")
        return 1
    
    # Create generator
    generator = SlideshowGenerator(
        config.video,
        watermark=watermark if watermark.enabled else None,
        title=title if title.enabled else None
    )
    
    # Find images first to show summary
    image_files = generator.find_images(images_path)
    if not image_files:
        print_error(f"No images found in: {images_path}")
        return 1
    
    generator.prepare_images(image_files)
    
    # Show configuration
    print(f"{Colors.WHITE}Configuration:{Colors.NC}")
    print(f"  Images:      {len(generator.images)} files")
    print(f"  Audio:       {audio_path}")
    print(f"  Output:      {output_path}")
    print(f"  Duration:    {config.video.duration}s per image")
    print(f"  Resolution:  {config.video.width}x{config.video.height} @ {config.video.fps}fps")
    print(f"  Zoom:        {config.video.zoom_intensity:.0%} ({config.video.zoom_direction})")
    print(f"  Pan:         {config.video.pan_intensity:.0%} ({config.video.pan_direction})")
    print(f"  Transition:  {config.video.transition}")
    print(f"  Shuffle:     {'Yes' if config.video.shuffle else 'No'}")
    if watermark.enabled:
        print(f"  Watermark:   {watermark.position} ({watermark.opacity:.0%})")
    if title.enabled:
        print(f"  Title:       {title.text}")
    print(f"  Est. length: {format_time(generator.estimate_duration())}")
    if is_preview:
        print(f"  {Colors.YELLOW}Mode:        PREVIEW (basse qualité){Colors.NC}")
    print()
    
    # Progress tracking
    last_percent = [0]
    
    def progress(msg):
        print_info(msg)
    
    def progress_bar(info: ProgressInfo):
        if info.percent > last_percent[0] + 2:  # Update every 2%
            last_percent[0] = info.percent
            bar = format_progress_bar(info.percent)
            eta = format_time(info.eta_seconds) if info.eta_seconds > 0 else "--:--"
            speed = f"{info.speed:.1f}x" if info.speed > 0 else "-.-x"
            sys.stdout.write(f"\r  {bar} | ETA: {eta} | Speed: {speed}   ")
            sys.stdout.flush()
    
    # Generate
    if is_preview:
        success, message = generator.generate_preview(
            images_path,
            audio_path,
            output_path,
            progress_callback=progress,
            progress_bar_callback=progress_bar
        )
    else:
        success, message = generator.generate(
            images_path,
            audio_path,
            output_path,
            progress_callback=progress,
            progress_bar_callback=progress_bar
        )
    
    # Clear progress line
    sys.stdout.write("\r" + " " * 70 + "\r")
    
    if success:
        print_success(message)
        return 0
    else:
        print_error(message)
        return 1


def cmd_album(args):
    """Handle album processing command"""
    print_banner()
    
    # Check FFmpeg
    if not check_ffmpeg():
        print_error("FFmpeg not found. Please install FFmpeg first.")
        return 1
    
    # Load config
    config = load_config(args.config) if args.config else ProjectConfig()
    
    # Override with command line arguments
    if args.loudness:
        config.audio.loudness = args.loudness
    if args.sample_rate:
        config.audio.sample_rate = args.sample_rate
    if args.artist:
        config.artist = args.artist
    if args.genre:
        config.genre = args.genre
    if args.no_silence_removal:
        config.audio.remove_silence = False
    
    input_path = args.input or "."
    output_dir = args.output or "export_ready"
    
    if not os.path.exists(input_path):
        print_error(f"Input path not found: {input_path}")
        return 1
    
    # Create processor
    processor = AlbumProcessor(config.audio)
    
    # Show configuration
    print(f"{Colors.WHITE}Configuration:{Colors.NC}")
    print(f"  Input:       {input_path}")
    print(f"  Output:      {output_dir}")
    print(f"  Loudness:    {config.audio.loudness} LUFS")
    print(f"  Sample rate: {config.audio.sample_rate} Hz")
    print(f"  Artist:      {config.artist}")
    print(f"  Genre:       {config.genre}")
    print()
    
    # Process
    def progress(msg):
        print_info(msg)
    
    success_count, error_count, tracks = processor.process_album(
        input_path,
        output_dir,
        progress_callback=progress
    )
    
    if not tracks:
        print_error("No audio files found")
        return 1
    
    # Generate metadata
    album_name = Path(input_path).name if Path(input_path).is_dir() else "Album"
    processor.generate_metadata(output_dir, album_name, config.artist, config.genre)
    processor.generate_cue_sheet(output_dir, album_name, config.artist)
    
    # Summary
    print()
    print(f"{Colors.WHITE}Results:{Colors.NC}")
    for track in tracks:
        if track.success:
            print_success(f"{track.track_number:02d}. {track.clean_name}")
        else:
            print_error(f"{track.track_number:02d}. {track.clean_name}: {track.error}")
    
    print()
    if error_count == 0:
        print_success(f"Album ready in {output_dir}/ ({success_count} tracks)")
    else:
        print_warning(f"Completed with {error_count} error(s)")
    
    return 0 if error_count == 0 else 1


def cmd_init(args):
    """Create default configuration file"""
    print_banner()
    
    config_path = args.output or "panzoom.yaml"
    
    if os.path.exists(config_path) and not args.force:
        print_error(f"Config file already exists: {config_path}")
        print_info("Use --force to overwrite")
        return 1
    
    config = ProjectConfig()
    save_config(config, config_path)
    
    print_success(f"Configuration file created: {config_path}")
    print_info("Edit this file to customize default settings")
    return 0


def cmd_presets(args):
    """List available presets"""
    print_banner()
    
    print(f"{Colors.WHITE}Available Presets:{Colors.NC}")
    print()
    
    for name, settings in PRESETS.items():
        print(f"  {Colors.CYAN}{name}{Colors.NC}")
        for key, value in settings.items():
            print(f"    {key}: {value}")
        print()
    
    print_info("Use with: panzoom video --preset <name>")
    return 0


def cmd_transitions(args):
    """List available transitions"""
    print_banner()
    
    print(f"{Colors.WHITE}Available Transitions:{Colors.NC}")
    print()
    
    # Group transitions by type
    groups = {
        "Fondu": ["fade", "fadeblack", "fadewhite", "dissolve"],
        "Balayage": ["wipeleft", "wiperight", "wipeup", "wipedown"],
        "Glissement": ["slideleft", "slideright", "slideup", "slidedown", "smoothleft", "smoothright"],
        "Cercle": ["circlecrop", "circleclose", "circleopen", "radial"],
        "Effets": ["pixelize", "hblur", "zoomin", "squeezeh", "squeezev", "hlslice", "vlslice"]
    }
    
    for group_name, trans_list in groups.items():
        print(f"  {Colors.YELLOW}{group_name}:{Colors.NC}")
        for t in trans_list:
            if t in TRANSITIONS:
                print(f"    {Colors.CYAN}{t:15}{Colors.NC} {TRANSITIONS[t]}")
        print()
    
    print(f"  {Colors.MAGENTA}random{Colors.NC}           Transition aléatoire à chaque image")
    print()
    print_info("Use with: panzoom video --transition <name>")
    return 0


def cmd_exports(args):
    """List available export profiles"""
    print_banner()
    
    print(f"{Colors.WHITE}Export Profiles:{Colors.NC}")
    print()
    
    for name, profile in EXPORT_PROFILES.items():
        res = f"{profile['width']}x{profile['height']}"
        fps = profile['fps']
        print(f"  {Colors.CYAN}{name:20}{Colors.NC} {res:10} {fps}fps  {Colors.DIM}{profile['description']}{Colors.NC}")
    
    print()
    print_info("Use with: panzoom video --export <profile>")
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        prog='panzoom',
        description='Professional Ken Burns slideshow and audio album generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s video -a music.wav -i ./photos -o slideshow.mp4
  %(prog)s video -a music.wav --preset cinematic --shuffle
  %(prog)s video -a music.wav --export youtube --transition wipeleft
  %(prog)s video -a music.wav --preview  # Quick preview
  %(prog)s video -a music.wav --watermark logo.png
  %(prog)s album -i ./audio -o ./export --artist "My Band"
  %(prog)s transitions  # List all transitions
  %(prog)s exports      # List export profiles
"""
    )
    
    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Video command
    video_parser = subparsers.add_parser('video', help='Generate slideshow video')
    video_parser.add_argument('-i', '--images', help='Images directory (default: current)')
    video_parser.add_argument('-a', '--audio', required=True, help='Audio file')
    video_parser.add_argument('-o', '--output', help='Output file (default: slideshow.mp4)')
    video_parser.add_argument('-c', '--config', help='Config file')
    video_parser.add_argument('--preset', choices=list(PRESETS.keys()), help='Use style preset')
    video_parser.add_argument('--export', choices=list(EXPORT_PROFILES.keys()), help='Use export profile')
    video_parser.add_argument('--preview', action='store_true', help='Generate quick low-quality preview')
    
    # Video settings
    video_parser.add_argument('-d', '--duration', type=float, help='Duration per image (seconds)')
    video_parser.add_argument('-x', '--crossfade', type=float, help='Crossfade duration (seconds)')
    video_parser.add_argument('-f', '--fps', type=int, help='Frames per second')
    video_parser.add_argument('-w', '--width', type=int, help='Video width')
    video_parser.add_argument('-g', '--height', type=int, help='Video height')
    video_parser.add_argument('--zoom', type=float, help='Zoom intensity (0.0-0.2)')
    video_parser.add_argument('--pan', type=float, help='Pan intensity (0.0-1.0)')
    video_parser.add_argument('--zoom-dir', choices=['in', 'out', 'alternate', 'random'], help='Zoom direction')
    video_parser.add_argument('--pan-dir', choices=['left', 'right', 'alternate', 'random'], help='Pan direction')
    
    # Transitions
    all_transitions = list(TRANSITIONS.keys()) + ['random']
    video_parser.add_argument('--transition', choices=all_transitions, help='Transition type')
    
    # Image order
    video_parser.add_argument('--shuffle', action='store_true', help='Randomize image order')
    video_parser.add_argument('--reverse', action='store_true', help='Reverse image order')
    video_parser.add_argument('-q', '--quality', type=int, help='Quality (0-51, lower=better)')
    
    # Watermark options
    video_parser.add_argument('--watermark', help='Watermark image file (PNG)')
    video_parser.add_argument('--watermark-pos', 
                              choices=['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'],
                              help='Watermark position')
    video_parser.add_argument('--watermark-opacity', type=float, help='Watermark opacity (0.0-1.0)')
    video_parser.add_argument('--watermark-scale', type=float, help='Watermark size (0.0-1.0)')
    
    # Title options
    video_parser.add_argument('--title', help='Add title card with text')
    video_parser.add_argument('--subtitle', help='Subtitle for title card')
    
    # Album command
    album_parser = subparsers.add_parser('album', help='Process audio album')
    album_parser.add_argument('-i', '--input', help='Input directory (default: current)')
    album_parser.add_argument('-o', '--output', help='Output directory (default: export_ready)')
    album_parser.add_argument('-c', '--config', help='Config file')
    album_parser.add_argument('--artist', help='Artist name')
    album_parser.add_argument('--genre', help='Music genre')
    album_parser.add_argument('-l', '--loudness', type=float, help='Target loudness (LUFS)')
    album_parser.add_argument('-r', '--sample-rate', type=int, help='Sample rate (Hz)')
    album_parser.add_argument('--no-silence-removal', action='store_true', help='Keep silence')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Create config file')
    init_parser.add_argument('-o', '--output', help='Output path (default: panzoom.yaml)')
    init_parser.add_argument('-f', '--force', action='store_true', help='Overwrite existing')
    
    # List commands
    subparsers.add_parser('presets', help='List style presets')
    subparsers.add_parser('transitions', help='List available transitions')
    subparsers.add_parser('exports', help='List export profiles')
    
    args = parser.parse_args()
    
    if args.no_color:
        Colors.disable()
    
    if args.command == 'video':
        return cmd_video(args)
    elif args.command == 'album':
        return cmd_album(args)
    elif args.command == 'init':
        return cmd_init(args)
    elif args.command == 'presets':
        return cmd_presets(args)
    elif args.command == 'transitions':
        return cmd_transitions(args)
    elif args.command == 'exports':
        return cmd_exports(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
