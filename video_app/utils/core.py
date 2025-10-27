"""
Core video processing utilities.

This module contains the main video processing functions that coordinate
thumbnail generation and HLS conversion using specialized modules.
"""
import logging

logger = logging.getLogger(__name__)


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
