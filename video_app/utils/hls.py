"""
HLS management and video processing utilities.

This module handles HLS conversion workflows, queue management,
and video processing coordination.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
import django_rq
logger = logging.getLogger(__name__)


def get_resolution_configs():
    """Get HLS resolution configurations for video conversion."""
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


def get_basic_ffmpeg_args(video_path: str):
    """Get basic FFmpeg arguments."""
    return ['ffmpeg', '-i', video_path, '-c:v', 'libx264', '-c:a', 'aac']


def get_audio_args():
    """Get audio encoding arguments."""
    return ['-strict', 'experimental', '-ac', '2', '-b:a', '128k', '-ar', '44100']


def get_video_args(resolution):
    """Get video encoding arguments for resolution."""
    return [
        '-vf', f'scale={resolution["width"]}:{resolution["height"]}',
        '-b:v', resolution['bitrate'], '-maxrate', resolution['bitrate'],
        '-bufsize', str(int(resolution['bitrate'][:-1]) * 2) + 'k'
    ]


def get_hls_args(res_dir: str, output_path: str):
    """Get HLS-specific arguments."""
    return [
        '-hls_time', '10', '-hls_list_size', '0',
        '-hls_segment_filename', os.path.join(res_dir, '%03d.ts'),
        '-f', 'hls', output_path, '-y'
    ]


def build_ffmpeg_command(video_path: str, resolution, output_path: str, res_dir: str):
    """Build complete FFmpeg command for HLS conversion."""
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


def run_ffmpeg_conversion(ffmpeg_command, resolution_name: str) -> bool:
    """Execute FFmpeg conversion with error handling."""
    try:
        import subprocess
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


def convert_single_resolution(video_path: str, resolution, hls_dir: str) -> bool:
    """Convert video to single HLS resolution."""
    res_dir = setup_resolution_directory(hls_dir, resolution['name'])
    output_path = os.path.join(res_dir, 'index.m3u8')
    ffmpeg_command = build_ffmpeg_command(video_path, resolution, output_path, res_dir)
    return run_ffmpeg_conversion(ffmpeg_command, resolution['name'])


def validate_video_instance(video_instance) -> tuple:
    """Validate video instance and return path info.
    Checks file existence and accessibility before HLS processing."""
    if not video_instance.video_file:
        logger.error(f"No video file found for video ID {video_instance.id}")
        return None, None

    video_path = video_instance.video_file.path
    if not validate_video_file(video_path):
        return None, None

    return video_path, video_instance.id


def prepare_video_conversion(video_instance) -> tuple:
    """Prepare video for HLS conversion and validate.
    Creates HLS directory structure and validates video file access."""
    video_path, video_id = validate_video_instance(video_instance)
    if not video_path:
        return None, None, None

    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_id))
    os.makedirs(hls_dir, exist_ok=True)

    return video_path, video_id, hls_dir


def process_all_resolutions(video_path: str, hls_dir: str) -> int:
    """Process video for all resolutions and return success count.
    Converts video to multiple HLS qualities (120p to 1080p)."""
    successful_conversions = 0
    for resolution in get_resolution_configs():
        if convert_single_resolution(video_path, resolution, hls_dir):
            successful_conversions += 1
    return successful_conversions


def finalize_video_conversion(video_instance, video_id: int, success_count: int) -> bool:
    """Finalize video conversion and update instance.
    Updates database status and saves HLS path if conversions succeeded."""
    if success_count > 0:
        video_instance.hls_processed = True
        video_instance.hls_path = f'hls/{video_id}/'
        video_instance.save()
        logger.info(f"HLS conversion completed for video ID {video_id}")
        return True
    else:
        logger.error(f"All conversions failed for video ID {video_id}")
        return False


def convert_video_to_hls(video_instance) -> bool:
    """Convert video to HLS format with multiple resolutions.
    Main conversion pipeline orchestrating validation, processing, and finalization."""
    video_path, video_id, hls_dir = prepare_video_conversion(video_instance)
    if not video_path:
        return False

    try:
        logger.info(f"Starting HLS conversion for video ID {video_id}")
        success_count = process_all_resolutions(video_path, hls_dir)
        return finalize_video_conversion(video_instance, video_id, success_count)
    except Exception as e:
        logger.error(f"Error in HLS conversion for video ID {video_id}: {str(e)}")
        return False


def queue_video_conversion(video_instance) -> None:
    """
    Queue video for HLS conversion in background using Redis Queue.

    Args:
        video_instance: Video model instance to queue for processing
    """
    try:
        queue = django_rq.get_queue('default')
        queue.enqueue(convert_video_to_hls, video_instance)
        logger.info(f"Video ID {video_instance.id} queued for conversion")
    except Exception as e:
    
        logger.error(f"Failed to queue video ID {video_instance.id}: {str(e)}")

def create_base_status_info(video_instance) -> Dict[str, Any]:
    """Create base status information structure.
    Provides foundation data for HLS conversion status tracking."""
    return {
        'is_processed': video_instance.hls_processed,
        'hls_path': video_instance.hls_path,
        'available_resolutions': [],
        'total_resolutions': len(get_resolution_configs()),
    }


def calculate_conversion_progress(status_info: Dict[str, Any], video_instance) -> None:
    """Calculate and set conversion progress.
    Determines percentage completion based on successfully converted resolutions."""
    from .files import get_hls_resolutions

    if video_instance.hls_processed:
        status_info['available_resolutions'] = get_hls_resolutions(video_instance)
        progress = len(status_info['available_resolutions']) / status_info['total_resolutions'] * 100
        status_info['progress'] = progress
    else:
        status_info['progress'] = 0


def check_conversion_status(video_instance) -> Dict[str, Any]:
    """Check the status of HLS conversion for a video.
    Returns comprehensive status including progress and available resolutions."""
    status_info = create_base_status_info(video_instance)
    calculate_conversion_progress(status_info, video_instance)
    return status_info