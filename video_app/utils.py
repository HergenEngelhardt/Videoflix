"""
UThis is the main utils module that imports from specialized sub-modules:
- ffmpeg_utils: FFmpeg operations and video processing
- hls_utils: HLS conversion workflows and queue management
- file_utils: File management and HLS utilitiesty functions for video processing and HLS conversion.

This module provides functions for converting videos to HLS format,
managing video processing queues, and handling HLS file operations.

This is the main utils module that imports from specialized sub-modules:
- ffmpeg_utils: FFmpeg operations and video processing
- hls_utils: HLS conversion workflows and queue management
- file_utils: File management and HLS utilities
"""

from .ffmpeg_utils import (
    get_resolution_configs,
    validate_video_file,
    get_basic_ffmpeg_args,
    get_audio_args,
    get_video_args,
    get_hls_args,
    build_ffmpeg_command,
    setup_resolution_directory,
    run_ffmpeg_conversion,
    handle_conversion_result,
    convert_single_resolution,
    build_ffprobe_command,
    extract_video_stream,
    build_video_info,
    execute_ffprobe_command,
    process_ffprobe_result,
    get_video_file_info,
    build_thumbnail_command,
    execute_thumbnail_generation,
    generate_video_thumbnail
)

from .hls_utils import (
    prepare_video_conversion,
    process_all_resolutions,
    finalize_video_conversion,
    convert_video_to_hls,
    queue_video_conversion,
    create_base_status_info,
    calculate_conversion_progress,
    check_conversion_status
)

from .file_utils import (
    check_hls_prerequisites,
    scan_resolution_directories,
    get_hls_resolutions,
    get_hls_directory_path,
    remove_hls_directory,
    cleanup_hls_files,
    check_resolution_availability,
    build_hls_playlist_url,
    get_hls_playlist_url
)

__all__ = [
    'get_resolution_configs',
    'validate_video_file',
    'get_basic_ffmpeg_args',
    'get_audio_args',
    'get_video_args',
    'get_hls_args',
    'build_ffmpeg_command',
    'setup_resolution_directory',
    'run_ffmpeg_conversion',
    'handle_conversion_result',
    'convert_single_resolution',
    'build_ffprobe_command',
    'extract_video_stream',
    'build_video_info',
    'execute_ffprobe_command',
    'process_ffprobe_result',
    'get_video_file_info',
    'build_thumbnail_command',
    'execute_thumbnail_generation',
    'generate_video_thumbnail',

    'prepare_video_conversion',
    'process_all_resolutions',
    'finalize_video_conversion',
    'convert_video_to_hls',
    'queue_video_conversion',
    'create_base_status_info',
    'calculate_conversion_progress',
    'check_conversion_status',

    'check_hls_prerequisites',
    'scan_resolution_directories',
    'get_hls_resolutions',
    'get_hls_directory_path',
    'remove_hls_directory',
    'cleanup_hls_files',
    'check_resolution_availability',
    'build_hls_playlist_url',
    'get_hls_playlist_url'
]
