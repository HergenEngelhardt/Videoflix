from django.db import models
from django.conf import settings
import os


class Category(models.Model):
    """Model for video categories."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    
    class Meta:
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Video(models.Model):
    """Model for videos with HLS streaming support."""
    title = models.CharField(max_length=200, verbose_name="Titel")
    description = models.TextField(verbose_name="Beschreibung")
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name="videos",
        verbose_name="Kategorie"
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/', 
        blank=True, 
        null=True,
        verbose_name="Thumbnail"
    )
    video_file = models.FileField(
        upload_to='videos/', 
        blank=True, 
        null=True,
        verbose_name="Video Datei"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")
    
    # HLS specific fields
    hls_processed = models.BooleanField(default=False, verbose_name="HLS verarbeitet")
    hls_path = models.CharField(
        max_length=500, 
        blank=True, 
        null=True,
        verbose_name="HLS Pfad"
    )
    
    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def thumbnail_url(self):
        """Return full URL for thumbnail."""
        if self.thumbnail:
            return f"{settings.MEDIA_URL}{self.thumbnail}"
        return None
    
    def get_hls_resolutions(self):
        """Get available HLS resolutions for this video."""
        if not self.hls_processed or not self.hls_path:
            return []
        
        resolutions = []
        hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(self.id))
        
        if os.path.exists(hls_dir):
            for item in os.listdir(hls_dir):
                if os.path.isdir(os.path.join(hls_dir, item)) and item.endswith('p'):
                    resolutions.append(item)
        
        return sorted(resolutions, key=lambda x: int(x[:-1]))  # Sort by resolution number
