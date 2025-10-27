from rest_framework import serializers
from ..models import Video, Category
import os


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model.
    Handles category data serialization for API endpoints."""

    class Meta:
        model = Category
        fields = ('id', 'name', 'created_at')
        read_only_fields = ('id', 'created_at')


class VideoListSerializer(serializers.ModelSerializer):
    """Serializer for Video list view.
    Provides video metadata with category names and thumbnail URLs."""
    category = serializers.CharField(source='category.name', read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            'id',
            'created_at',
            'title',
            'description',
            'thumbnail_url',
            'category'
        )
        read_only_fields = ('id', 'created_at')

    def get_thumbnail_url(self, obj):
        """Get full URL for thumbnail."""
        if obj.thumbnail and obj.thumbnail.name:
            try:
                if hasattr(obj.thumbnail, 'path') and os.path.exists(obj.thumbnail.path):
                    request = self.context.get('request')
                    if request:
                        return request.build_absolute_uri(obj.thumbnail.url)
                else:
                    if obj.video_file and hasattr(obj.video_file, 'path') and os.path.exists(obj.video_file.path):
                        from ..utils.core import queue_video_processing
                        queue_video_processing(obj)
            except Exception:
                pass  
        return None


class VideoDetailSerializer(serializers.ModelSerializer):
    """Serializer for Video detail view."""
    category = CategorySerializer(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    available_resolutions = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            'id',
            'title',
            'description',
            'category',
            'thumbnail_url',
            'available_resolutions',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_thumbnail_url(self, obj):
        """Get full URL for thumbnail."""
        if obj.thumbnail and obj.thumbnail.name:
            try:
                if hasattr(obj.thumbnail, 'path') and os.path.exists(obj.thumbnail.path):
                    request = self.context.get('request')
                    if request:
                        return request.build_absolute_uri(obj.thumbnail.url)
                else:
                    if obj.video_file and hasattr(obj.video_file, 'path') and os.path.exists(obj.video_file.path):
                        from ..utils.core import queue_video_processing
                        queue_video_processing(obj)
            except Exception:
                pass  
        return None

    def get_available_resolutions(self, obj):
        """Get available HLS resolutions."""
        return obj.get_hls_resolutions()


class ThumbnailUploadSerializer(serializers.Serializer):
    """Serializer for thumbnail upload."""
    thumbnail = serializers.ImageField(
        required=True,
        help_text="Thumbnail image file (JPEG, PNG, WebP). Max size: 5MB."
    )
    
    def validate_thumbnail(self, value):
        """Validate thumbnail file."""
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Invalid file type. Allowed formats: JPEG, PNG, WebP."
            )
        
        max_size = 5 * 1024 * 1024  
        if value.size > max_size:
            raise serializers.ValidationError(
                "File too large. Maximum size: 5MB."
            )
        
        return value
