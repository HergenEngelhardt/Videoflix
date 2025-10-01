"""
FFmpeg operations and video processing utilities.

This module handles all FFmpeg-related operations including HLS conversion,
thumbnail generation, and video file information extraction.
"""
import os
import subprocess
import logging
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


def get_resolution_configs() -> List[Dict[str, Union[str, int]]]:
    """Get HLS resolution configurations for video conversion.
    Returns list of resolution configs with name, dimensions, and bitrate."""
    return [
        {'name': '120p', 'width': 214, 'height': 120, 'bitrate': '300k'},
        {'name': '360p', 'width': 640, 'height': 360, 'bitrate': '800k'},
        {'name': '480p', 'width': 854, 'height': 480, 'bitrate': '1200k'},
        {'name': '720p', 'width': 1280, 'height': 720, 'bitrate': '2500k'},
        {'name': '1080p', 'width': 1920, 'height': 1080, 'bitrate': '5000k'},
    ]


def check_video_file_exists(video_path: str) -> bool:
    """Check if video file exists."""
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False
    return True


def check_video_file_readable(video_path: str) -> bool:
    """Check if video file is readable."""
    if not os.access(video_path, os.R_OK):
        logger.error(f"Video file not readable: {video_path}")
        return False
    return True


def validate_video_file(video_path: str) -> bool:
    """Validate if video file exists and is accessible."""
    return (check_video_file_exists(video_path) and
            check_video_file_readable(video_path))


def get_basic_ffmpeg_args(video_path: str) -> List[str]:
    """Get basic FFmpeg arguments.
    Sets up input file and baseline encoding settings for H.264/AAC."""
    return ['ffmpeg', '-i', video_path, '-c:v', 'libx264', '-c:a', 'aac']


def get_audio_args() -> List[str]:
    """Get audio encoding arguments."""
    return ['-strict', 'experimental', '-ac', '2', '-b:a', '128k', '-ar', '44100']


def get_video_args(resolution: Dict[str, Union[str, int]]) -> List[str]:
    """Get video encoding arguments for resolution."""
    return [
        '-vf', f'scale={resolution["width"]}:{resolution["height"]}',
        '-b:v', resolution['bitrate'], '-maxrate', resolution['bitrate'],
        '-bufsize', str(int(resolution['bitrate'][:-1]) * 2) + 'k'
    ]


def get_hls_args(res_dir: str, output_path: str) -> List[str]:
    """Get HLS-specific arguments."""
    return [
        '-hls_time', '10', '-hls_list_size', '0',
        '-hls_segment_filename', os.path.join(res_dir, '%03d.ts'),
        '-f', 'hls', output_path, '-y'
    ]


def build_ffmpeg_command(
    video_path: str,
    resolution: Dict[str, Union[str, int]],
    output_path: str,
    res_dir: str
) -> List[str]:
    """Build complete FFmpeg command for HLS conversion.
    Combines all arguments for resolution-specific adaptive streaming output."""
    command = get_basic_ffmpeg_args(video_path)
    command.extend(get_audio_args())
    command.extend(get_video_args(resolution))
    command.extend(get_hls_args(res_dir, output_path))
    return command


def setup_resolution_directory(hls_dir: str, resolution_name: str) -> str:
    """Setup directory for specific resolution."""
    res_dir = os.path.join(hls_dir, resolution_name)
    os.makedirs(res_dir, exist_ok=True)
    return res_dir


def run_ffmpeg_conversion(ffmpeg_command: List[str], resolution_name: str) -> bool:
    """Execute FFmpeg conversion with error handling.
    Runs subprocess with timeout protection and comprehensive error logging."""
    try:
        logger.info(f"Starting conversion for {resolution_name}")
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True, timeout=3600)
        return handle_conversion_result(result, resolution_name)
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout converting {resolution_name}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error converting {resolution_name}: {str(e)}")
        return False


def handle_conversion_result(result, resolution_name: str) -> bool:
    """Handle FFmpeg conversion result."""
    if result.returncode != 0:
        logger.error(f"FFmpeg error for {resolution_name}: {result.stderr}")
        return False
    logger.info(f"Successfully converted {resolution_name}")
    return True


def convert_single_resolution(
    video_path: str,
    resolution: Dict[str, Union[str, int]],
    hls_dir: str
) -> bool:
    """Convert video to single HLS resolution.
    Creates directory structure and processes video for specific quality level."""
    res_dir = setup_resolution_directory(hls_dir, resolution['name'])
    output_path = os.path.join(res_dir, 'index.m3u8')
    ffmpeg_command = build_ffmpeg_command(video_path, resolution, output_path, res_dir)
    return run_ffmpeg_conversion(ffmpeg_command, resolution['name'])


def build_ffprobe_command(video_path: str) -> List[str]:
    """Build FFprobe command for video analysis."""
    return [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ]


def extract_video_stream(video_metadata: Dict) -> Optional[Dict]:
    """Extract video stream from metadata."""
    for stream in video_metadata.get('streams', []):
        if stream.get('codec_type') == 'video':
            return stream
    return None


def extract_format_info(video_metadata: Dict) -> Dict[str, Any]:
    """Extract format information from video metadata."""
    format_data = video_metadata.get('format', {})
    return {
        'duration': float(format_data.get('duration', 0)),
        'size': int(format_data.get('size', 0)),
        'format': format_data.get('format_name', 'unknown'),
    }


def extract_stream_info(video_stream: Optional[Dict]) -> Dict[str, Any]:
    """Extract stream information from video stream."""
    if not video_stream:
        return {}
    return {
        'width': video_stream.get('width', 0),
        'height': video_stream.get('height', 0),
        'codec': video_stream.get('codec_name', 'unknown'),
    }


def build_video_info(video_metadata: Dict, video_stream: Optional[Dict]) -> Dict[str, Any]:
    """Build video information dictionary."""
    video_info = extract_format_info(video_metadata)
    video_info.update(extract_stream_info(video_stream))
    return video_info


def execute_ffprobe_command(video_path):
    """Execute ffprobe command and return result."""
    command = build_ffprobe_command(video_path)
    return subprocess.run(command, capture_output=True, text=True)


def process_ffprobe_result(result):
    """Process ffprobe result and return video info."""
    if result.returncode == 0:
        import json
        metadata = json.loads(result.stdout)
        video_stream = extract_video_stream(metadata)
        return build_video_info(metadata, video_stream)
    else:
        logger.error(f"FFprobe error: {result.stderr}")
        return {}


def get_video_file_info(video_path: str) -> Dict[str, Any]:
    """Get basic information about video file using ffprobe."""
    try:
        result = execute_ffprobe_command(video_path)
        return process_ffprobe_result(result)
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return {}


def build_thumbnail_command(video_path: str, output_path: str, timestamp: str) -> List[str]:
    """Build FFmpeg command for thumbnail generation."""
    return [
        'ffmpeg', '-i', video_path, '-ss', timestamp, '-vframes', '1',
        '-vf', 'scale=320:180', output_path, '-y'
    ]


def execute_thumbnail_generation(command: List[str], output_path: str) -> bool:
    """Execute thumbnail generation command."""
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0 and os.path.exists(output_path):
        logger.info(f"Generated thumbnail: {output_path}")
        return True
    else:
        logger.error(f"Failed to generate thumbnail: {result.stderr}")
        return False


def generate_video_thumbnail(video_path: str, output_path: str, timestamp: str = "00:00:10") -> bool:
    """Generate thumbnail image from video at specified timestamp."""
    try:
        command = build_thumbnail_command(video_path, output_path, timestamp)
        return execute_thumbnail_generation(command, output_path)
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        return False
