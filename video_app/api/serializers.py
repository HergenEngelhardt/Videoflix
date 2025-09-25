from rest_framework import serializers
from ..models import Video, Category


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
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
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
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
        return None
    
    def get_available_resolutions(self, obj):
        """Get available HLS resolutions."""
        return obj.get_hls_resolutions()