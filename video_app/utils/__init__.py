"""
Video processing utilities package.

This package contains specialized modules for video processing:
- core: Main video processing coordination
- validators: File validation and format checking  
- ffmpeg: FFmpeg operations and thumbnail generation
- hls: HLS conversion workflows
- files: File management and path utilities
"""

from .core import queue_video_processing, process_video_with_thumbnail
from .validators import (
    validate_video_size, 
    comprehensive_video_validator,
    validate_video_for_processing,
    get_video_file_info
)
from .ffmpeg import (
    generate_video_thumbnail, 
    generate_video_thumbnail_for_instance,
    create_default_thumbnail
)
from .hls import (
    convert_video_to_hls, 
    check_conversion_status,
    get_resolution_configs,
    validate_video_file
)
from .files import (
    cleanup_hls_files, 
    get_hls_resolutions,
    video_upload_path,
    thumbnail_upload_path
)

__all__ = [
    'queue_video_processing',
    'process_video_with_thumbnail',
    'validate_video_size',
    'comprehensive_video_validator', 
    'validate_video_for_processing',
    'get_video_file_info',
    'generate_video_thumbnail',
    'generate_video_thumbnail_for_instance',
    'create_default_thumbnail',
    'convert_video_to_hls',
    'check_conversion_status',
    'get_resolution_configs',
    'validate_video_file',
    'cleanup_hls_files',
    'get_hls_resolutions',
    'video_upload_path',
    'thumbnail_upload_path',
]