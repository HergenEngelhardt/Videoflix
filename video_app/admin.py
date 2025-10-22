from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category, Video


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    actions = ['create_default_categories']
    
    def create_default_categories(self, request, queryset):
        """Action to create default movie categories."""
        default_categories = [
            'Action',
            'Comedy', 
            'Drama',
            'Horror',
            'Thriller',
            'Science Fiction',
            'Fantasy',
            'Romance',
            'Adventure',
            'Crime',
            'Mystery',
            'Animation',
            'Documentary',
            'Biography',
            'History',
            'War',
            'Western',
            'Musical',
            'Family',
            'Sport'
        ]
        
        created_count = 0
        existing_count = 0
        
        for category_name in default_categories:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                created_count += 1
            else:
                existing_count += 1
        
        if created_count > 0:
            self.message_user(request, f'{created_count} neue Kategorien wurden erstellt.')
        if existing_count > 0:
            self.message_user(request, f'{existing_count} Kategorien existierten bereits.')
    
    create_default_categories.short_description = 'Standard Film-Kategorien erstellen'


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for Video model."""
    list_display = ('title', 'category', 'has_thumbnail', 'processing_status', 'created_at')
    list_filter = ('category', 'processing_status', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview')
    actions = ['regenerate_thumbnails']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Media Files', {
            'fields': ('video_file', 'thumbnail', 'thumbnail_preview'),
            'description': 'You can upload a custom thumbnail or it will be automatically generated from the video.'
        }),
        ('Processing', {
            'fields': ('processing_status',),
        }),
        ('HLS Settings', {
            'fields': ('hls_processed', 'hls_path', 'hls_480p_path', 'hls_720p_path', 'hls_1080p_path'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_thumbnail(self, obj):
        """Check if video has a thumbnail."""
        return bool(obj.thumbnail and obj.thumbnail.name)
    has_thumbnail.boolean = True
    has_thumbnail.short_description = 'Has Thumbnail'

    def thumbnail_preview(self, obj):
        """Display thumbnail preview in admin."""
        if obj.thumbnail and obj.thumbnail.name:
            try:
                return mark_safe(f'<img src="{obj.thumbnail.url}" width="160" height="90" style="border: 1px solid #ddd; border-radius: 4px;"/>')
            except:
                return 'Thumbnail file not found'
        return 'No thumbnail available'
    thumbnail_preview.short_description = 'Thumbnail Preview'

    def regenerate_thumbnails(self, request, queryset):
        """Action to regenerate thumbnails for selected videos."""
        from .utils import queue_video_processing
        import django_rq
        
        count = 0
        for video in queryset:
            if video.video_file:
                try:
                    queue = django_rq.get_queue('default')
                    queue.enqueue(self._regenerate_single_thumbnail, video.id)
                    count += 1
                except Exception as e:
                    self.message_user(request, f'Fehler bei Video "{video.title}": {str(e)}', level='ERROR')
        
        if count > 0:
            self.message_user(request, f'Thumbnail-Neugenerierung gestartet für {count} Video(s). Die Erstellung erfolgt automatisch im Hintergrund.')
        else:
            self.message_user(request, 'Keine Videos für Thumbnail-Neugenerierung gefunden.', level='WARNING')
    
    regenerate_thumbnails.short_description = 'Thumbnails für ausgewählte Videos neu generieren'

    def _regenerate_single_thumbnail(self, video_id):
        """Helper method to regenerate thumbnail for a single video."""
        from .models import Video
        from .utils import generate_video_thumbnail_for_instance
        
        try:
            video = Video.objects.get(id=video_id)
            if video.thumbnail:
                video.thumbnail.delete(save=False)
            
            success = generate_video_thumbnail_for_instance(video)
            return success
        except Video.DoesNotExist:
            return False
        except Exception:
            return False
