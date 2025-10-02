"""
This is the main utils module that imports from specialized sub-modules:
- ffmpeg_utils: FFmpeg operations and video processing
- hls_utils: HLS conversion workflows and queue management  
- file_utils: File management and HLS utilities

This module provides functions for converting videos to HLS format,
managing video processing queues, and handling HLS file operations.
- ffmpeg_utils: FFmpeg operations and video processing
- hls_utils: HLS conversion workflows and queue management
- file_utils: File management and HLS utilities
"""
import logging

logger = logging.getLogger(__name__)

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
    'get_hls_playlist_url',
    'queue_video_processing'
]


def queue_video_processing(video_instance):
    """
    Queue both thumbnail generation and HLS conversion for a video.
    This function is called by the video post_save signal.
    """
    import django_rq
    from .hls_utils import convert_video_to_hls
    
    try:
        queue = django_rq.get_queue('default')
        # Queue video processing (includes both thumbnail and HLS conversion)
        queue.enqueue(process_video_with_thumbnail, video_instance)
        logger.info(f"Video ID {video_instance.id} queued for complete processing")
    except Exception as e:
        logger.error(f"Failed to queue video processing for ID {video_instance.id}: {str(e)}")


def process_video_with_thumbnail(video_instance):
    """
    Process video by generating thumbnail and converting to HLS.
    This combines both operations in the correct order.
    """
    import os
    from django.conf import settings
    
    try:
        # Generate thumbnail first
        if video_instance.video_file and not video_instance.thumbnail:
            thumbnail_success = generate_video_thumbnail_for_instance(video_instance)
            if thumbnail_success:
                logger.info(f"Thumbnail generated for video ID {video_instance.id}")
            else:
                logger.warning(f"Failed to generate thumbnail for video ID {video_instance.id}")
        
        # Then convert to HLS
        from .hls_utils import convert_video_to_hls
        hls_success = convert_video_to_hls(video_instance)
        
        if hls_success:
            logger.info(f"Complete video processing successful for ID {video_instance.id}")
        else:
            logger.error(f"HLS conversion failed for video ID {video_instance.id}")
            
        return hls_success
        
    except Exception as e:
        logger.error(f"Error in complete video processing for ID {video_instance.id}: {str(e)}")
        return False


def generate_video_thumbnail_for_instance(video_instance):
    """
    Generate and save thumbnail for a video instance.
    Automatically creates thumbnail at 10-second mark and saves to instance.
    """
    import os
    from django.conf import settings
    from django.core.files.base import ContentFile
    
    try:
        if not video_instance.video_file:
            logger.error(f"No video file found for video ID {video_instance.id}")
            return False
            
        video_path = video_instance.video_file.path
        
        # Create thumbnail filename
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        thumbnail_filename = f"{video_name}_thumbnail.jpg"
        
        # Create temporary thumbnail path
        temp_thumbnail_path = os.path.join(settings.MEDIA_ROOT, 'temp', thumbnail_filename)
        os.makedirs(os.path.dirname(temp_thumbnail_path), exist_ok=True)
        
        # Generate thumbnail using FFmpeg
        success = generate_video_thumbnail(video_path, temp_thumbnail_path, "00:00:10")
        
        if success and os.path.exists(temp_thumbnail_path):
            # Read the generated thumbnail
            with open(temp_thumbnail_path, 'rb') as f:
                thumbnail_content = f.read()
            
            # Save to video instance
            video_instance.thumbnail.save(
                thumbnail_filename,
                ContentFile(thumbnail_content),
                save=True
            )
            
            # Clean up temporary file
            try:
                os.remove(temp_thumbnail_path)
            except:
                pass
                
            logger.info(f"Thumbnail saved for video ID {video_instance.id}")
            return True
        else:
            logger.error(f"Failed to generate thumbnail file for video ID {video_instance.id}")
            return False
            
    except Exception as e:
        logger.error(f"Error generating thumbnail for video ID {video_instance.id}: {str(e)}")
        return False


def queue_video_processing(video_instance):
    """
    Queue both HLS conversion and thumbnail generation for a video.
    
    Args:
        video_instance: Video model instance to process
    """
    from .hls_utils import queue_video_conversion
    from .ffmpeg_utils import generate_video_thumbnail
    import django_rq
    
    try:
        # Queue HLS conversion
        queue_video_conversion(video_instance)
        
        # Queue thumbnail generation
        queue = django_rq.get_queue('default')
        queue.enqueue(generate_video_thumbnail, video_instance)
        
        logger.info(f"Video ID {video_instance.id} queued for full processing (HLS + thumbnail)")
    except Exception as e:
        logger.error(f"Error queuing video processing for video ID {video_instance.id}: {str(e)}")
