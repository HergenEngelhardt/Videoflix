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
from .ffmpeg_utils import (
    validate_video_file, convert_single_resolution,
    get_resolution_configs
)


logger = logging.getLogger(__name__)


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
    from .file_utils import get_hls_resolutions

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