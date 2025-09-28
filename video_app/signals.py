from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Video
from .utils import queue_video_conversion, cleanup_hls_files


@receiver(post_save, sender=Video)
def process_video(sender, instance, created, **kwargs):
    """
    Signal to automatically process video after upload.
    """
    if created and instance.video_file:
        queue_video_conversion(instance)


def cleanup_video_file(instance):
    """Clean up video file safely."""
    if instance.video_file:
        try:
            instance.video_file.delete(save=False)
        except:
            pass


def cleanup_thumbnail_file(instance):
    """Clean up thumbnail file safely."""
    if instance.thumbnail:
        try:
            instance.thumbnail.delete(save=False)
        except:
            pass


@receiver(post_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    """Signal to cleanup files when video is deleted."""
    cleanup_video_file(instance)
    cleanup_thumbnail_file(instance)
    
    cleanup_hls_files(instance)