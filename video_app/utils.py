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
        thumbnail_success = False
        
        if video_instance.video_file:
            should_generate_thumbnail = True
            
            if video_instance.thumbnail and video_instance.thumbnail.name:
                try:
                    if hasattr(video_instance.thumbnail, 'path') and os.path.exists(video_instance.thumbnail.path):
                        if os.path.getsize(video_instance.thumbnail.path) > 0:
                            should_generate_thumbnail = False
                            thumbnail_success = True
                            logger.info(f"Valid thumbnail already exists for video ID {video_instance.id}")
                except Exception:
                    should_generate_thumbnail = True
            
            if should_generate_thumbnail:
                max_retries = 3
                for attempt in range(1, max_retries + 1):
                    logger.info(f"Thumbnail generation attempt {attempt}/{max_retries} for video ID {video_instance.id}")
                    thumbnail_success = generate_video_thumbnail_for_instance(video_instance)
                    
                    if thumbnail_success:
                        logger.info(f"Thumbnail generated successfully on attempt {attempt} for video ID {video_instance.id}")
                        break
                    else:
                        logger.warning(f"Thumbnail generation attempt {attempt} failed for video ID {video_instance.id}")
                        if attempt < max_retries:
                            import time
                            time.sleep(2) 
                
                if not thumbnail_success:
                    logger.error(f"Failed to generate thumbnail after {max_retries} attempts for video ID {video_instance.id}")
                    logger.info(f"Attempting to create default thumbnail for video ID {video_instance.id}")
                    thumbnail_success = create_default_thumbnail(video_instance)
        
        from .hls_utils import convert_video_to_hls
        hls_success = convert_video_to_hls(video_instance)
        
        if hls_success:
            logger.info(f"Complete video processing successful for ID {video_instance.id}")
        else:
            logger.error(f"HLS conversion failed for video ID {video_instance.id}")
            
        return hls_success and thumbnail_success
        
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
        
        if not os.path.exists(video_path):
            logger.error(f"Video file does not exist: {video_path} for video ID {video_instance.id}")
            return False
            
        if not os.access(video_path, os.R_OK):
            logger.error(f"Video file not readable: {video_path} for video ID {video_instance.id}")
            return False
        
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        thumbnail_filename = f"{video_name}_thumbnail.jpg"
        
        temp_thumbnail_path = os.path.join(settings.MEDIA_ROOT, 'temp', thumbnail_filename)
        os.makedirs(os.path.dirname(temp_thumbnail_path), exist_ok=True)
        
        timestamps = ["00:00:10", "00:00:05", "00:00:02", "00:00:01"]
        success = False
        
        for timestamp in timestamps:
            logger.info(f"Attempting thumbnail generation at {timestamp} for video ID {video_instance.id}")
            success = generate_video_thumbnail(video_path, temp_thumbnail_path, timestamp)
            if success and os.path.exists(temp_thumbnail_path):
                if os.path.getsize(temp_thumbnail_path) > 0:
                    logger.info(f"Successfully generated thumbnail at {timestamp} for video ID {video_instance.id}")
                    break
                else:
                    logger.warning(f"Empty thumbnail file generated at {timestamp} for video ID {video_instance.id}")
                    success = False
            else:
                logger.warning(f"Failed to generate thumbnail at {timestamp} for video ID {video_instance.id}")
        
        if success and os.path.exists(temp_thumbnail_path) and os.path.getsize(temp_thumbnail_path) > 0:
            try:
                with open(temp_thumbnail_path, 'rb') as f:
                    thumbnail_content = f.read()
                
                if len(thumbnail_content) == 0:
                    logger.error(f"Thumbnail file is empty for video ID {video_instance.id}")
                    return False
                
                video_instance.thumbnail.save(
                    thumbnail_filename,
                    ContentFile(thumbnail_content),
                    save=True
                )
                
                logger.info(f"Thumbnail saved successfully for video ID {video_instance.id}")
                
            except Exception as save_error:
                logger.error(f"Failed to save thumbnail to database for video ID {video_instance.id}: {str(save_error)}")
                return False
            finally:
                try:
                    if os.path.exists(temp_thumbnail_path):
                        os.remove(temp_thumbnail_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp thumbnail for video ID {video_instance.id}: {str(cleanup_error)}")
                
            return True
        else:
            logger.error(f"Failed to generate thumbnail file for video ID {video_instance.id} after trying all timestamps")
            return False
            
    except Exception as e:
        logger.error(f"Error generating thumbnail for video ID {video_instance.id}: {str(e)}")
        return False


def regenerate_thumbnail_job(video_id):
    """
    Job function for asynchronous thumbnail regeneration.
    This function is called by django-rq for background processing.
    """
    try:
        from .models import Video
        
        video = Video.objects.get(id=video_id)
        
        if video.thumbnail:
            video.thumbnail.delete(save=False)
        
        success = generate_video_thumbnail_for_instance(video)
        
        if success:
            logger.info(f"Thumbnail regeneration successful for video ID {video_id}")
        else:
            logger.error(f"Thumbnail regeneration failed for video ID {video_id}")
            success = create_default_thumbnail(video)
        
        return success
        
    except Exception as e:
        logger.error(f"Error in thumbnail regeneration job for video ID {video_id}: {str(e)}")
        return False


def create_default_thumbnail(video_instance):
    """
    Create a default thumbnail for videos where automatic generation fails.
    This creates a simple colored placeholder image with the video title.
    """
    try:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            logger.error("Pillow not available for default thumbnail generation")
            return False
            
        from django.core.files.base import ContentFile
        import io
        
        img = Image.new('RGB', (320, 180), color=(45, 45, 45))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            try:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            except:
                font = None
                small_font = None
        
        title_text = video_instance.title[:30] + "..." if len(video_instance.title) > 30 else video_instance.title
        
        if font:
            bbox = draw.textbbox((0, 0), title_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (320 - text_width) // 2
            y = (180 - text_height) // 2 - 10
            
            draw.text((x + 2, y + 2), title_text, fill=(0, 0, 0), font=font)  
            draw.text((x, y), title_text, fill=(255, 255, 255), font=font)    
            
            if small_font:
                label_bbox = draw.textbbox((0, 0), "VIDEO", font=small_font)
                label_width = label_bbox[2] - label_bbox[0]
                label_x = (320 - label_width) // 2
                draw.text((label_x, y + text_height + 10), "VIDEO", fill=(150, 150, 150), font=small_font)
        
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=85)
        img_buffer.seek(0)
        
        filename = f"default_thumbnail_{video_instance.id}.jpg"
        
        video_instance.thumbnail.save(
            filename,
            ContentFile(img_buffer.read()),
            save=True
        )
        
        logger.info(f"Default thumbnail created for video ID {video_instance.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create default thumbnail for video ID {video_instance.id}: {str(e)}")
        return False
