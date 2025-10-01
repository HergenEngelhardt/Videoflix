from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """Django app configuration for the video_app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'

    def ready(self):
        """Import signals module to register signal handlers."""
        from . import signals  # noqa: F401
