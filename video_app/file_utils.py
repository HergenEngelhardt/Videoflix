"""
File management and HLS utilities.

This module handles file operations, directory management,
HLS file cleanup, and resolution availability checks.
"""
import os
import shutil
import logging
from typing import List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def check_hls_prerequisites(video_instance):
    """Check if video instance has HLS prerequisites.
    Verifies video has been processed and HLS path exists."""
    return video_instance.hls_processed and video_instance.hls_path


def scan_resolution_directories(hls_dir):
    """Scan HLS directory for available resolution folders.
    Checks for valid resolution directories containing m3u8 playlists."""
    resolutions = []
    if os.path.exists(hls_dir):
        for item in os.listdir(hls_dir):
            item_path = os.path.join(hls_dir, item)
            if os.path.isdir(item_path) and item.endswith('p'):
                if os.path.exists(os.path.join(item_path, 'index.m3u8')):
                    resolutions.append(item)
    return resolutions


def get_hls_resolutions(video_instance) -> List[str]:
    """Get available HLS resolutions for a video instance.
    Scans HLS directory for available resolution folders."""
    if not check_hls_prerequisites(video_instance):
        return []

    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_instance.id))
    resolutions = scan_resolution_directories(hls_dir)

    return sorted(resolutions, key=lambda x: int(x[:-1]))


def get_hls_directory_path(video_instance):
    """Get HLS directory path for video instance.
    Constructs absolute filesystem path to video's HLS directory."""
    if not video_instance.hls_path:
        return None
    return os.path.join(settings.MEDIA_ROOT, video_instance.hls_path)


def remove_hls_directory(hls_dir, video_id):
    """Remove HLS directory and log result.
    Safely deletes entire HLS directory tree with error handling."""
    try:
        shutil.rmtree(hls_dir)
        logger.info(f"Cleaned up HLS files for video ID {video_id}")
        return True
    except Exception as e:
        logger.error(f"Error cleaning up HLS files for video {video_id}: {str(e)}")
        return False


def cleanup_hls_files(video_instance) -> bool:
    """Clean up HLS files when video is deleted.
    Removes all HLS-related files and directories for the video instance."""
    hls_dir = get_hls_directory_path(video_instance)
    if not hls_dir:
        return True

    if os.path.exists(hls_dir):
        return remove_hls_directory(hls_dir, video_instance.id)

    return True


def check_resolution_availability(video_instance, resolution):
    """Check if resolution is available for video.
    Validates that specific resolution quality exists and is playable."""
    available_resolutions = get_hls_resolutions(video_instance)
    return resolution in available_resolutions


def build_hls_playlist_url(video_instance, resolution):
    """Build HLS playlist URL for video and resolution.
    Constructs complete media URL for HLS streaming endpoint."""
    return f"{settings.MEDIA_URL}hls/{video_instance.id}/{resolution}/index.m3u8"


def get_hls_playlist_url(video_instance, resolution: str) -> Optional[str]:
    """Get the HLS playlist URL for a specific resolution.
    Returns URL if resolution is available, None otherwise."""
    if not check_resolution_availability(video_instance, resolution):
        return None

    return build_hls_playlist_url(video_instance, resolution)
