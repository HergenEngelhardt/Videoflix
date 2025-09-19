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


@receiver(post_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    """
    Signal to cleanup files when video is deleted.
    """
    if instance.video_file:
        try:
            instance.video_file.delete(save=False)
        except:
            pass
    
    if instance.thumbnail:
        try:
            instance.thumbnail.delete(save=False)
        except:
            pass
    
    cleanup_hls_files(instance)