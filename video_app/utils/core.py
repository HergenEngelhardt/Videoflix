"""
Core video processing utilities.

This module contains the main video processing functions that coordinate
thumbnail generation and HLS conversion using specialized modules.
"""
import logging

logger = logging.getLogger(__name__)


def handle_new_video_save(video_instance):
    """Handle save logic for new video instances."""
    try:
        video_instance._validate_before_processing()
        logger.info(f"Pre-processing validation successful for video: {video_instance.title}")
    except Exception as e:
        logger.error(f"Pre-processing validation failed for video {video_instance.title}: {str(e)}")
        return 'failed'
    return None


def handle_video_processing_queue(video_instance):
    """Queue video processing for new instances."""
    try:
        queue_video_processing(video_instance)
        logger.info(f"Video processing queued successfully for: {video_instance.title}")
        return None
    except Exception as e:
        logger.error(f"Failed to queue video processing for {video_instance.title}: {str(e)}")
        return 'failed'


def validate_video_file_exists(video_file):
    """Validate that video file exists and is readable."""
    import os
    from django.core.exceptions import ValidationError
    
    if not video_file:
        raise ValidationError("No video file provided")
    
    if not hasattr(video_file, 'path'):
        return
        
    video_path = video_file.path
    if not os.path.exists(video_path):
        raise ValidationError(f"Video file does not exist: {video_path}")
    
    if not os.access(video_path, os.R_OK):
        raise ValidationError(f"Video file is not readable: {video_path}")


def validate_video_file_size(video_file, title):
    """Validate video file size constraints."""
    import os
    from django.core.exceptions import ValidationError
    
    if not hasattr(video_file, 'path'):
        return
        
    file_size = os.path.getsize(video_file.path)
    if file_size == 0:
        raise ValidationError("Video file is empty")
    
    max_size = 100.5 * 1024 * 1024  # 100.5 MB
    if file_size > max_size:
        raise ValidationError(f"Video file too large: {file_size / 1024 / 1024:.2f}MB")
        
    logger.info(f"Video file validation passed: {video_file.path} ({file_size / 1024 / 1024:.2f}MB)")


def validate_video_metadata(title, description, category):
    """Validate video metadata fields."""
    from django.core.exceptions import ValidationError
    
    if not title or not title.strip():
        raise ValidationError("Video title is required")
    
    if not description or not description.strip():
        raise ValidationError("Video description is required")
    
    if not category:
        raise ValidationError("Video category is required")


def get_dashboard_empty_response():
    """Return empty dashboard response when no videos exist."""
    from rest_framework.response import Response
    from rest_framework import status
    return Response({
        'hero_video': None,
        'categories': {}
    }, status=status.HTTP_200_OK)


def build_categories_dict(videos):
    """Build categories dictionary from video queryset."""
    from collections import defaultdict
    categories_dict = defaultdict(list)
    for video in videos:
        if video.category:
            categories_dict[video.category.name].append(video)
    return categories_dict


def serialize_categories(categories_dict, request):
    """Serialize categories dictionary with videos."""
    from ..api.serializers import VideoListSerializer
    result_categories = {}
    for category_name, category_videos in categories_dict.items():
        serializer = VideoListSerializer(category_videos, many=True, context={'request': request})
        result_categories[category_name] = serializer.data
    return result_categories


def queue_video_processing(video_instance):
    """
    Queue both thumbnail generation and HLS conversion for a video.
    This function is called by the video post_save signal.
    Includes comprehensive pre-processing validation.
    """
    import django_rq
    from .validators import validate_video_for_processing
    
    try:
        if not validate_video_for_processing(video_instance):
            video_instance.processing_status = 'failed'
            video_instance.save(update_fields=['processing_status'])
            logger.error(f"Video ID {video_instance.id} failed pre-processing validation")
            return False
        
        try:
            queue = django_rq.get_queue('default')
            queue_length = len(queue)
            
            if queue_length > 50: 
                logger.warning(f"Queue overloaded ({queue_length} jobs), delaying video {video_instance.id}")
                video_instance.processing_status = 'pending'
                video_instance.save(update_fields=['processing_status'])
                return False
            
        except Exception as queue_error:
            logger.error(f"Failed to access RQ queue: {str(queue_error)}")
            video_instance.processing_status = 'failed'
            video_instance.save(update_fields=['processing_status'])
            return False
        
        job = queue.enqueue(
            process_video_with_thumbnail, 
            video_instance.id,
            job_timeout=3600,
            failure_ttl=86400 
        )
        
        logger.info(f"Video ID {video_instance.id} queued for complete processing (Job ID: {job.id})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to queue video processing for ID {video_instance.id}: {str(e)}")
        try:
            video_instance.processing_status = 'failed'
            video_instance.save(update_fields=['processing_status'])
        except Exception as save_error:
            logger.error(f"Failed to update video status after queue error: {str(save_error)}")
        return False


def process_video_with_thumbnail(video_id):
    """
    Process video by generating thumbnail and converting to HLS.
    This combines both operations in the correct order with robust error handling.
    Takes video ID and loads the instance from database.
    """
    from ..models import Video
    from .validators import validate_video_for_processing
    
    video_instance = None
    
    try:
        try:
            video_instance = Video.objects.get(id=video_id)
            logger.info(f"Loaded video instance for processing: {video_instance.title} (ID: {video_id})")
        except Video.DoesNotExist:
            logger.error(f"Video with ID {video_id} does not exist in database")
            return False
        except Exception as e:
            logger.error(f"Database error loading video ID {video_id}: {str(e)}")
            return False
        
        try:
            video_instance.processing_status = 'processing'
            video_instance.save(update_fields=['processing_status'])
            logger.info(f"Started processing video: {video_instance.title} (ID: {video_instance.id})")
        except Exception as e:
            logger.error(f"Failed to update processing status for video ID {video_id}: {str(e)}")
            return False
        
        if not validate_video_for_processing(video_instance):
            logger.error(f"Video ID {video_id} failed final pre-processing validation")
            video_instance.processing_status = 'failed'
            video_instance.save(update_fields=['processing_status'])
            return False
            
        thumbnail_success = False
        hls_success = False
        
        if video_instance.video_file:
            try:
                thumbnail_success = _process_video_thumbnail(video_instance)
            except Exception as e:
                logger.error(f"Thumbnail processing failed for video ID {video_id}: {str(e)}")
                thumbnail_success = False
        else:
            logger.error(f"No video file found for video ID {video_id}")
        
        if thumbnail_success or video_instance.thumbnail:  
            try:
                from .hls import convert_video_to_hls
                logger.info(f"Starting HLS conversion for video ID {video_id}")
                hls_success = convert_video_to_hls(video_instance)
                
                if hls_success:
                    logger.info(f"HLS conversion successful for video ID {video_id}")
                else:
                    logger.error(f"HLS conversion failed for video ID {video_id}")
                    
            except Exception as e:
                logger.error(f"HLS conversion error for video ID {video_id}: {str(e)}")
                hls_success = False
        else:
            logger.error(f"Skipping HLS conversion due to thumbnail failure for video ID {video_id}")
        
        try:
            if hls_success and thumbnail_success:
                video_instance.processing_status = 'completed'
                video_instance.save(update_fields=['processing_status'])
                logger.info(f"Complete video processing successful for: {video_instance.title} (ID: {video_id})")
                return True
            else:
                video_instance.processing_status = 'failed'
                video_instance.save(update_fields=['processing_status'])
                logger.error(f"Video processing failed for: {video_instance.title} (ID: {video_id}) - "
                           f"HLS: {'✓' if hls_success else '✗'}, Thumbnail: {'✓' if thumbnail_success else '✗'}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update final processing status for video ID {video_id}: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Unexpected error in complete video processing for ID {video_id}: {str(e)}")
        
        try:
            if video_instance:
                video_instance.processing_status = 'failed'
                video_instance.save(update_fields=['processing_status'])
        except Exception as save_error:
            logger.error(f"Failed to update emergency status for video ID {video_id}: {str(save_error)}")
        
        return False


def _process_video_thumbnail(video_instance):
    """
    Handle thumbnail processing with retry logic and fallback options.
    Returns True if thumbnail was successfully created or already exists.
    """
    import os
    from .ffmpeg import generate_video_thumbnail_for_instance, create_default_thumbnail
    
    try:
        should_generate_thumbnail = True
        
        if video_instance.thumbnail and video_instance.thumbnail.name:
            try:
                if hasattr(video_instance.thumbnail, 'path') and os.path.exists(video_instance.thumbnail.path):
                    if os.path.getsize(video_instance.thumbnail.path) > 0:
                        should_generate_thumbnail = False
                        logger.info(f"Valid thumbnail already exists for video ID {video_instance.id}")
                        return True
            except Exception as e:
                logger.warning(f"Error checking existing thumbnail for video ID {video_instance.id}: {str(e)}")
                should_generate_thumbnail = True
        
        if should_generate_thumbnail:
            max_retries = 3
            thumbnail_success = False
            
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Thumbnail generation attempt {attempt}/{max_retries} for video ID {video_instance.id}")
                    thumbnail_success = generate_video_thumbnail_for_instance(video_instance)
                    
                    if thumbnail_success:
                        logger.info(f"Thumbnail generated successfully on attempt {attempt} for video ID {video_instance.id}")
                        return True
                    else:
                        logger.warning(f"Thumbnail generation attempt {attempt} failed for video ID {video_instance.id}")
                        if attempt < max_retries:
                            import time
                            time.sleep(2)  
                            
                except Exception as e:
                    logger.error(f"Thumbnail generation attempt {attempt} error for video ID {video_instance.id}: {str(e)}")
                    if attempt < max_retries:
                        import time
                        time.sleep(2)
            
            if not thumbnail_success:
                logger.warning(f"Failed to generate thumbnail after {max_retries} attempts for video ID {video_instance.id}")
                logger.info(f"Attempting to create default thumbnail for video ID {video_instance.id}")
                
                try:
                    default_success = create_default_thumbnail(video_instance)
                    if default_success:
                        logger.info(f"Default thumbnail created successfully for video ID {video_instance.id}")
                        return True
                    else:
                        logger.error(f"Default thumbnail creation also failed for video ID {video_instance.id}")
                        return False
                except Exception as e:
                    logger.error(f"Default thumbnail creation error for video ID {video_instance.id}: {str(e)}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error in thumbnail processing for video ID {video_instance.id}: {str(e)}")
        return False
