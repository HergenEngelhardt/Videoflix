"""
Utility functions for video processing and HLS conversion.

This module provides functions for converting videos to HLS format,
managing video processing queues, and handling HLS file operations.
"""
import os
import subprocess
import shutil
import logging
from typing import List, Dict, Any, Optional, Union
from django.conf import settings
import django_rq

logger = logging.getLogger(__name__)


def get_resolution_configs() -> List[Dict[str, Union[str, int]]]:
    """
    Get HLS resolution configurations for video conversion.
    
    Returns:
        List[Dict]: List of resolution configurations containing:
            - name (str): Resolution name (e.g., '120p', '360p', '480p', '720p', '1080p')
            - width (int): Video width in pixels
            - height (int): Video height in pixels
            - bitrate (str): Target bitrate (e.g., '1000k')
    """
    return [
        {'name': '120p', 'width': 214, 'height': 120, 'bitrate': '300k'},
        {'name': '360p', 'width': 640, 'height': 360, 'bitrate': '800k'},
        {'name': '480p', 'width': 854, 'height': 480, 'bitrate': '1200k'},
        {'name': '720p', 'width': 1280, 'height': 720, 'bitrate': '2500k'},
        {'name': '1080p', 'width': 1920, 'height': 1080, 'bitrate': '5000k'},
    ]


def validate_video_file(video_path: str) -> bool:
    """
    Validate if video file exists and is accessible.
    
    Args:
        video_path (str): Path to video file
        
    Returns:
        bool: True if file is valid, False otherwise
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False
        
    if not os.access(video_path, os.R_OK):
        logger.error(f"Video file not readable: {video_path}")
        return False
        
    return True


def get_basic_ffmpeg_args(video_path: str) -> List[str]:
    """Get basic FFmpeg arguments."""
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


def run_ffmpeg_conversion(ffmpeg_command: List[str], resolution_name: str) -> bool:
    """Execute FFmpeg conversion with error handling."""
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
    """Convert video to single HLS resolution."""
    res_dir = setup_resolution_directory(hls_dir, resolution['name'])
    output_path = os.path.join(res_dir, 'index.m3u8')
    ffmpeg_command = build_ffmpeg_command(video_path, resolution, output_path, res_dir)
    return run_ffmpeg_conversion(ffmpeg_command, resolution['name'])


def prepare_video_conversion(video_instance) -> tuple:
    """Prepare video for HLS conversion and validate."""
    if not video_instance.video_file:
        logger.error(f"No video file found for video ID {video_instance.id}")
        return None, None, None
    
    video_path = video_instance.video_file.path
    if not validate_video_file(video_path):
        return None, None, None
    
    video_id = video_instance.id
    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_id))
    os.makedirs(hls_dir, exist_ok=True)
    
    return video_path, video_id, hls_dir


def process_all_resolutions(video_path: str, hls_dir: str) -> int:
    """Process video for all resolutions and return success count."""
    successful_conversions = 0
    for resolution in get_resolution_configs():
        if convert_single_resolution(video_path, resolution, hls_dir):
            successful_conversions += 1
    return successful_conversions


def finalize_video_conversion(video_instance, video_id: int, success_count: int) -> bool:
    """Finalize video conversion and update instance."""
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
    """Convert video to HLS format with multiple resolutions."""
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


def get_hls_resolutions(video_instance) -> List[str]:
    """
    Get available HLS resolutions for a video instance.
    
    Scans the HLS directory for the video to find available resolution folders.
    
    Args:
        video_instance: Video model instance to check
        
    Returns:
        List[str]: Sorted list of available resolutions (e.g., ['120p', '360p', '480p', '720p', '1080p'])
    """
    if not video_instance.hls_processed or not video_instance.hls_path:
        return []
    
    resolutions = []
    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_instance.id))
    
    if os.path.exists(hls_dir):
        for item in os.listdir(hls_dir):
            item_path = os.path.join(hls_dir, item)
            if os.path.isdir(item_path) and item.endswith('p'):
                if os.path.exists(os.path.join(item_path, 'index.m3u8')):
                    resolutions.append(item)
    
    return sorted(resolutions, key=lambda x: int(x[:-1]))


def cleanup_hls_files(video_instance) -> bool:
    """
    Clean up HLS files when video is deleted.
    
    Removes all HLS-related files and directories for the given video instance.
    
    Args:
        video_instance: Video model instance whose HLS files should be cleaned
        
    Returns:
        bool: True if cleanup successful or no files to clean, False on error
    """
    if not video_instance.hls_path:
        return True
        
    hls_dir = os.path.join(settings.MEDIA_ROOT, video_instance.hls_path)
    if os.path.exists(hls_dir):
        try:
            shutil.rmtree(hls_dir)
            logger.info(f"Cleaned up HLS files for video ID {video_instance.id}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up HLS files for video {video_instance.id}: {str(e)}")
            return False
    
    return True


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


def build_video_info(video_metadata: Dict, video_stream: Optional[Dict]) -> Dict[str, Any]:
    """Build video information dictionary."""
    video_info = {
        'duration': float(video_metadata.get('format', {}).get('duration', 0)),
        'size': int(video_metadata.get('format', {}).get('size', 0)),
        'format': video_metadata.get('format', {}).get('format_name', 'unknown'),
    }
    
    if video_stream:
        video_info.update({
            'width': video_stream.get('width', 0),
            'height': video_stream.get('height', 0),
            'codec': video_stream.get('codec_name', 'unknown'),
        })
    
    return video_info


def get_video_file_info(video_path: str) -> Dict[str, Any]:
    """Get basic information about video file using ffprobe."""
    try:
        command = build_ffprobe_command(video_path)
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            metadata = json.loads(result.stdout)
            video_stream = extract_video_stream(metadata)
            return build_video_info(metadata, video_stream)
        else:
            logger.error(f"FFprobe error: {result.stderr}")
            return {}
            
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return {}


def get_hls_playlist_url(video_instance, resolution: str) -> Optional[str]:
    """
    Get the HLS playlist URL for a specific resolution.
    
    Args:
        video_instance: Video model instance
        resolution (str): Requested resolution (e.g., '720p')
        
    Returns:
        Optional[str]: HLS playlist URL if available, None otherwise
    """
    available_resolutions = get_hls_resolutions(video_instance)
    if resolution not in available_resolutions:
        return None
        
    return f"{settings.MEDIA_URL}hls/{video_instance.id}/{resolution}/index.m3u8"


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


def create_base_status_info(video_instance) -> Dict[str, Any]:
    """Create base status information structure."""
    return {
        'is_processed': video_instance.hls_processed,
        'hls_path': video_instance.hls_path,
        'available_resolutions': [],
        'total_resolutions': len(get_resolution_configs()),
    }


def calculate_conversion_progress(status_info: Dict[str, Any], video_instance) -> None:
    """Calculate and set conversion progress."""
    if video_instance.hls_processed:
        status_info['available_resolutions'] = get_hls_resolutions(video_instance)
        progress = len(status_info['available_resolutions']) / status_info['total_resolutions'] * 100
        status_info['progress'] = progress
    else:
        status_info['progress'] = 0


def check_conversion_status(video_instance) -> Dict[str, Any]:
    """Check the status of HLS conversion for a video."""
    status_info = create_base_status_info(video_instance)
    calculate_conversion_progress(status_info, video_instance)
    return status_info