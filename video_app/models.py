from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from .utils.files import video_upload_path, thumbnail_upload_path
from .utils.validators import validate_video_size, comprehensive_video_validator
import logging

logger = logging.getLogger(__name__)


class Category(models.Model):
    """Model for video categories.
    Organizes videos into logical groups for better content management."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        """String representation of Category instance."""
        return self.name


class Video(models.Model):
    """Model for videos with HLS streaming support and automatic processing."""
    
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=200, unique=True, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="videos", blank=False, null=False)
    
    video_file = models.FileField(
        upload_to=video_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'mkv']),
            validate_video_size,
            comprehensive_video_validator
        ], blank=False, null=False
    )
    thumbnail = models.ImageField(upload_to=thumbnail_upload_path, blank=True, null=True)
    
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='pending')
    
    hls_processed = models.BooleanField(default=False)
    hls_path = models.CharField(max_length=500, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    hls_480p_path = models.CharField(max_length=500, blank=True, null=True)
    hls_720p_path = models.CharField(max_length=500, blank=True, null=True)
    hls_1080p_path = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ['-created_at']

    def __str__(self):
        """String representation of Video instance.
        Returns title for display in admin interface and debugging."""
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if is_new and self.video_file:
            from .utils.core import handle_new_video_save
            failed_status = handle_new_video_save(self)
            if failed_status:
                self.processing_status = failed_status
                super().save(*args, **kwargs)
                return
        
        super().save(*args, **kwargs)

        if is_new and self.video_file:
            from .utils.core import handle_video_processing_queue
            failed_status = handle_video_processing_queue(self)
            if failed_status:
                self.processing_status = failed_status
                super().save(update_fields=['processing_status'])

    def _validate_before_processing(self):
        """Validate video file before queuing for processing."""
        from .utils.core import validate_video_file_exists, validate_video_file_size, validate_video_metadata
        
        validate_video_file_exists(self.video_file)
        
        try:
            validate_video_file_size(self.video_file, self.title)
        except (AttributeError, OSError) as e:
            logger.warning(f"Could not validate video file path for {self.title}: {str(e)}")
        
        validate_video_metadata(self.title, self.description, self.category)

    @property
    def thumbnail_url(self):
        """Return full URL for thumbnail.
        Constructs complete media URL for video thumbnail image.
        Returns None if no thumbnail is available (will be auto-generated on upload)."""
        if self.thumbnail and self.thumbnail.name:
            from django.conf import settings
            if hasattr(settings, 'SITE_URL'):
                return f"{settings.SITE_URL}{settings.MEDIA_URL}{self.thumbnail.name}"
            else:
                return f"{settings.MEDIA_URL}{self.thumbnail.name}"
        return None

    def get_hls_resolutions(self):
        """Get available HLS resolutions for this video.
        Returns list of processed resolution strings (e.g., '720p', '1080p').
        Used for determining which quality options are available to clients."""
        resolutions = []
        if self.hls_480p_path:
            resolutions.append('480p')
        if self.hls_720p_path:
            resolutions.append('720p')
        if self.hls_1080p_path:
            resolutions.append('1080p')
        return resolutions
