"""
Utility functions for video processing and HLS conversion.

This module provides functions for converting videos to HLS format,
managing video processing queues, and handling HLS file operations.
"""
import os
import subprocess
import shutil
from typing import List, Dict, Any, Optional, Union
from django.conf import settings
import django_rq


def get_resolution_configs() -> List[Dict[str, Union[str, int]]]:
    """
    Get HLS resolution configurations for video conversion.
    
    Returns:
        List[Dict]: List of resolution configurations containing:
            - name (str): Resolution name (e.g., '480p', '720p')
            - width (int): Video width in pixels
            - height (int): Video height in pixels
            - bitrate (str): Target bitrate (e.g., '1000k')
    """
    return [
        {'name': '480p', 'width': 854, 'height': 480, 'bitrate': '1000k'},
        {'name': '720p', 'width': 1280, 'height': 720, 'bitrate': '2500k'},
        {'name': '1080p', 'width': 1920, 'height': 1080, 'bitrate': '5000k'},
    ]


def build_ffmpeg_command(
    video_path: str, 
    resolution: Dict[str, Union[str, int]], 
    output_path: str, 
    res_dir: str
) -> List[str]:
    """
    Build FFmpeg command for HLS conversion with specified resolution.
    
    Args:
        video_path (str): Path to source video file
        resolution (Dict): Resolution configuration dict
        output_path (str): Path for output m3u8 file
        res_dir (str): Directory for HLS segments
        
    Returns:
        List[str]: Complete FFmpeg command as list of arguments
    """
    return [
        'ffmpeg', '-i', video_path, '-c:v', 'libx264', '-c:a', 'aac',
        '-strict', 'experimental', '-ac', '2', '-b:a', '128k', '-ar', '44100',
        '-vf', f'scale={resolution["width"]}:{resolution["height"]}',
        '-b:v', resolution['bitrate'], '-maxrate', resolution['bitrate'],
        '-bufsize', str(int(resolution['bitrate'][:-1]) * 2) + 'k',
        '-hls_time', '10', '-hls_list_size', '0',
        '-hls_segment_filename', os.path.join(res_dir, '%03d.ts'),
        '-f', 'hls', output_path, '-y'
    ]


def convert_single_resolution(
    video_path: str, 
    resolution: Dict[str, Union[str, int]], 
    hls_dir: str
) -> bool:
    """
    Convert video to single HLS resolution.
    
    Args:
        video_path (str): Path to source video file
        resolution (Dict): Resolution configuration
        hls_dir (str): Base HLS directory
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    res_dir = os.path.join(hls_dir, resolution['name'])
    os.makedirs(res_dir, exist_ok=True)
    
    output_path = os.path.join(res_dir, 'index.m3u8')
    cmd = build_ffmpeg_command(video_path, resolution, output_path, res_dir)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            print(f"Error converting {resolution['name']}: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"Timeout converting {resolution['name']}")
        return False
    except Exception as e:
        print(f"Unexpected error converting {resolution['name']}: {str(e)}")
        return False


def convert_video_to_hls(video_instance) -> bool:
    """
    Convert video to HLS format with multiple resolutions.
    
    Processes the video file associated with the given video instance,
    converting it to HLS format with multiple resolution options.
    Updates the video instance with processing status and HLS path.
    
    Args:
        video_instance: Video model instance to process
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    if not video_instance.video_file:
        return False
    
    video_path = video_instance.video_file.path
    video_id = video_instance.id
    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_id))
    os.makedirs(hls_dir, exist_ok=True)
    
    try:
        successful_conversions = 0
        for resolution in get_resolution_configs():
            if convert_single_resolution(video_path, resolution, hls_dir):
                successful_conversions += 1
        
        # Mark as processed if at least one resolution was successful
        if successful_conversions > 0:
            video_instance.hls_processed = True
            video_instance.hls_path = f'hls/{video_id}/'
            video_instance.save()
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error in HLS conversion: {str(e)}")
        return False


def queue_video_conversion(video_instance) -> None:
    """
    Queue video for HLS conversion in background using Redis Queue.
    
    Args:
        video_instance: Video model instance to queue for processing
    """
    queue = django_rq.get_queue('default')
    queue.enqueue(convert_video_to_hls, video_instance)


def get_hls_resolutions(video_instance) -> List[str]:
    """
    Get available HLS resolutions for a video instance.
    
    Scans the HLS directory for the video to find available resolution folders.
    
    Args:
        video_instance: Video model instance to check
        
    Returns:
        List[str]: Sorted list of available resolutions (e.g., ['480p', '720p'])
    """
    if not video_instance.hls_processed or not video_instance.hls_path:
        return []
    
    resolutions = []
    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_instance.id))
    
    if os.path.exists(hls_dir):
        for item in os.listdir(hls_dir):
            item_path = os.path.join(hls_dir, item)
            if os.path.isdir(item_path) and item.endswith('p'):
                # Check if the resolution folder contains the index.m3u8 file
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
            return True
        except Exception as e:
            print(f"Error cleaning up HLS files for video {video_instance.id}: {str(e)}")
            return False
    
    return True


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