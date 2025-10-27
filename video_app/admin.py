from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Category, Video
import logging
import os

logger = logging.getLogger(__name__)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for Video model."""
    list_display = ('title', 'category', 'has_thumbnail', 'processing_status', 'created_at')
    list_filter = ('category', 'processing_status', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview', 'processing_status_display', 'hls_processed', 'hls_path', 'hls_480p_path', 'hls_720p_path', 'hls_1080p_path')
    actions = ['regenerate_thumbnails']

    def processing_status_display(self, obj):
        """Display processing status as read-only text with color coding."""
        status_colors = {
            'pending': '#ffa500',
            'processing': '#0066cc', 
            'completed': '#008000',
            'failed': '#cc0000'
        }
        color = status_colors.get(obj.processing_status, '#666666')
        return mark_safe(f'<span style="color: {color}; font-weight: bold;">{obj.get_processing_status_display()}</span>')
    
    processing_status_display.short_description = 'Processing Status'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Media Files', {
            'fields': ('video_file', 'thumbnail', 'thumbnail_preview'),
            'description': 'You can upload a custom thumbnail or it will be automatically generated from the video.'
        }),
        ('Processing Status (Read-Only)', {
            'fields': ('processing_status_display',),
            'description': 'Processing status is automatically managed by the system.',
            'classes': ('collapse',)
        }),
        ('HLS Settings (Read-Only)', {
            'fields': ('hls_processed', 'hls_path', 'hls_480p_path', 'hls_720p_path', 'hls_1080p_path'),
            'classes': ('collapse',),
            'description': 'HLS conversion data is automatically managed by the system.'
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
        from .utils.core import queue_video_processing
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
        from .utils.ffmpeg import generate_video_thumbnail_for_instance
        
        try:
            video = Video.objects.get(id=video_id)
            if video.thumbnail:
                video.thumbnail.delete(save=False)
            
            success = generate_video_thumbnail_for_instance(video)
            return success
        except Video.DoesNotExist:
            logger.error(f"Video with ID {video_id} not found for thumbnail regeneration")
            return False
        except Exception as e:
            logger.error(f"Error regenerating thumbnail for video ID {video_id}: {str(e)}")
            return False

    def save_model(self, request, obj, form, change):
        """Override save_model to add comprehensive validation before processing."""
        try:
            if not change and obj.video_file:
                self._validate_video_upload(request, obj)
            
            super().save_model(request, obj, form, change)
            
            if not change and obj.video_file:
                self._post_save_video_checks(request, obj)
                
        except ValidationError as e:
            messages.error(request, f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving video {obj.title}: {str(e)}")
            messages.error(request, f"Unexpected error while saving: {str(e)}")
            raise

    def _validate_video_upload(self, request, obj):
        """Comprehensive validation for video uploads before worker processing."""
        try:
            from .utils.validators import comprehensive_video_validator, validate_video_size
            
            # Ensure we have a video file
            if not obj.video_file:
                raise ValidationError("Video file could not be found.")
            
            # Reset file pointer to beginning before validation
            obj.video_file.seek(0)
            
            # These validators will handle all the validation logic
            validate_video_size(obj.video_file)
            
            # Reset file pointer again before comprehensive validation
            obj.video_file.seek(0)
            comprehensive_video_validator(obj.video_file)
            
            # Reset file pointer one more time so Django can save the file
            obj.video_file.seek(0)
            
            self._check_ffmpeg_availability(request)
            logger.info(f"Video validation successful for: {obj.title}")
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error during video validation for {obj.title}: {str(e)}")
            raise ValidationError(f"Error during video validation: {str(e)}")

    def _check_ffmpeg_availability(self, request):
        """Check if FFmpeg is available for video processing."""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode != 0:
                raise ValidationError("FFmpeg is not available or not working properly.")
            logger.info("FFmpeg availability check passed")
        except subprocess.TimeoutExpired:
            raise ValidationError("FFmpeg availability check failed (timeout).")
        except FileNotFoundError:
            raise ValidationError("FFmpeg is not installed or not available in PATH.")
        except Exception as e:
            logger.error(f"FFmpeg availability check failed: {str(e)}")
            raise ValidationError(f"FFmpeg availability check failed: {str(e)}")



    def _post_save_video_checks(self, request, obj):
        """Additional checks and messaging after video is saved."""
        try:
            try:
                import django_rq
                queue = django_rq.get_queue('default')
                queue_length = len(queue)
                
                if queue_length > 10:
                    messages.warning(request, 
                        f"The processing queue is overloaded ({queue_length} jobs). "
                        f"Processing of your video may take longer.")
                else:
                    messages.success(request, 
                        f"Video '{obj.title}' was successfully uploaded and queued for processing. "
                        f"Thumbnail creation and HLS conversion will happen automatically in the background.")
                        
            except Exception as e:
                logger.warning(f"Could not check RQ queue status: {str(e)}")
                messages.info(request, 
                    f"Video '{obj.title}' was uploaded. Processing is happening in the background.")
            
            messages.info(request, 
                "You can track the processing status in the video list. "
                "Processing may take several minutes depending on video size.")
                
        except Exception as e:
            logger.error(f"Error in post-save checks for video {obj.title}: {str(e)}")
