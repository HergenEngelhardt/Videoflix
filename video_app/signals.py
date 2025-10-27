from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Video
from .utils.core import queue_video_processing
from .utils.files import cleanup_hls_files
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Video)
def process_video(sender, instance, created, **kwargs):
    """
    Signal to automatically process video after upload.
    Queues HLS conversion and thumbnail generation in background when new video is created with file.
    Includes comprehensive error handling and duplicate prevention.
    """
    if not created:
        return 
    
    if not instance.video_file:
        logger.info(f"No video file for new video: {instance.title} (ID: {instance.id})")
        return
    
    if instance.processing_status in ['processing', 'completed']:
        logger.info(f"Video {instance.title} (ID: {instance.id}) already {instance.processing_status}, skipping signal processing")
        return
    
    try:
        # queue_video_processing already imported at top
        
        logger.info(f"Signal triggered for new video: {instance.title} (ID: {instance.id})")
        
        try:
            if instance.processing_status == 'pending':
                instance.processing_status = 'pending'
                instance.save(update_fields=['processing_status'])
        except Exception as status_error:
            logger.warning(f"Could not update initial status for video {instance.id}: {str(status_error)}")
        
        success = queue_video_processing(instance)
        
        if success:
            logger.info(f"Successfully queued video processing for: {instance.title} (ID: {instance.id})")
        else:
            logger.error(f"Failed to queue video processing for: {instance.title} (ID: {instance.id})")
            
            try:
                instance.processing_status = 'failed'
                instance.save(update_fields=['processing_status'])
            except Exception as save_error:
                logger.error(f"Failed to update failed status after queue error: {str(save_error)}")
        
    except ImportError as e:
        logger.error(f"Import error in video processing signal: {str(e)}")
        try:
            instance.processing_status = 'failed'
            instance.save(update_fields=['processing_status'])
        except:
            pass
            
    except Exception as e:
        logger.error(f"Unexpected error in video processing signal for {instance.title} (ID: {instance.id}): {str(e)}")
        try:
            instance.processing_status = 'failed'
            instance.save(update_fields=['processing_status'])
        except Exception as save_error:
            logger.error(f"Failed to update error status in signal: {str(save_error)}")
    
    logger.info(f"Video processing signal completed for: {instance.title} (ID: {instance.id})")


def cleanup_video_file(instance):
    """Clean up video file safely.
    Removes original video file from filesystem with error handling."""
    if instance.video_file:
        try:
            instance.video_file.delete(save=False)
        except Exception:
            pass


def cleanup_thumbnail_file(instance):
    """Clean up thumbnail file safely.
    Removes thumbnail image from filesystem with error handling."""
    if instance.thumbnail:
        try:
            instance.thumbnail.delete(save=False)
        except Exception:
            pass


@receiver(post_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    """
    Signal to cleanup files when video is deleted.
    Removes original video, thumbnail, and all HLS files from storage with comprehensive error handling.
    """
    try:
        logger.info(f"Starting file cleanup for deleted video: {instance.title} (ID: {instance.id})")
        
        cleanup_results = {
            'video_file': False,
            'thumbnail': False,
            'hls_files': False
        }
        
        try:
            cleanup_video_file(instance)
            cleanup_results['video_file'] = True
            logger.info(f"Video file cleanup successful for: {instance.title}")
        except Exception as e:
            logger.error(f"Video file cleanup failed for {instance.title}: {str(e)}")
        
        try:
            cleanup_thumbnail_file(instance)
            cleanup_results['thumbnail'] = True
            logger.info(f"Thumbnail cleanup successful for: {instance.title}")
        except Exception as e:
            logger.error(f"Thumbnail cleanup failed for {instance.title}: {str(e)}")
        
        try:
            cleanup_hls_files(instance)
            cleanup_results['hls_files'] = True
            logger.info(f"HLS files cleanup successful for: {instance.title}")
        except Exception as e:
            logger.error(f"HLS files cleanup failed for {instance.title}: {str(e)}")
        
        successful_cleanups = sum(cleanup_results.values())
        total_cleanups = len(cleanup_results)
        
        if successful_cleanups == total_cleanups:
            logger.info(f"Complete file cleanup successful for: {instance.title} ({successful_cleanups}/{total_cleanups})")
        else:
            logger.warning(f"Partial file cleanup for: {instance.title} ({successful_cleanups}/{total_cleanups} successful)")
            
    except Exception as e:
        logger.error(f"Unexpected error during file cleanup for video {instance.title}: {str(e)}")
