from django.db import models
from django.conf import settings
import os


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
        return self.name


class BaseVideo(models.Model):
    """Base video model with core metadata."""
    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(verbose_name="Description")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="videos", verbose_name="Category")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")
    
    class Meta:
        abstract = True


class VideoMedia(models.Model):
    """Video file storage fields."""
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True, verbose_name="Thumbnail")
    video_file = models.FileField(upload_to='videos/', blank=True, null=True, verbose_name="Video File")
    
    class Meta:
        abstract = True


class Video(BaseVideo, VideoMedia):
    """Model for videos with HLS streaming support."""
    hls_processed = models.BooleanField(default=False, verbose_name="HLS Processed")
    hls_path = models.CharField(max_length=500, blank=True, null=True, verbose_name="HLS Path")
    
    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ['-created_at']
    
    def __str__(self):
        """String representation of Video instance.
        Returns title for display in admin interface and debugging."""
        return self.title
    
    @property
    def thumbnail_url(self):
        """Return full URL for thumbnail.
        Constructs complete media URL for video thumbnail image."""
        if self.thumbnail:
            return f"{settings.MEDIA_URL}{self.thumbnail}"
        return None
    
    def get_hls_resolutions(self):
        """Get available HLS resolutions for this video.
        Returns list of processed resolution strings (e.g., '720p', '1080p')."""
        from .utils import get_hls_resolutions
        return get_hls_resolutions(self)
