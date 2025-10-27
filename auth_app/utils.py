"""
Utility functions for authentication app.
"""
import logging

from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

logger = logging.getLogger(__name__)

_frontend_path_prefix_cache = None


def detect_frontend_path_prefix():
    """Detect whether Live Server runs from frontend/ or root directory.
    
    Returns:
        str: '' if Live Server runs from frontend/, 'frontend' if from root
    """
    global _frontend_path_prefix_cache
    
    if _frontend_path_prefix_cache is not None:
        return _frontend_path_prefix_cache
    
    _frontend_path_prefix_cache = ''
    logger.info("Default: Live Server assumed to run from frontend/ directory")
    return ''
def build_frontend_url(path):
    """Build complete frontend URL with automatic path detection.
    
    Args:
        path (str): Relative path from frontend root (e.g., 'pages/auth/activate.html')
        
    Returns:
        str: Complete frontend URL
    """
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    path = path.lstrip('/')
    
    final_url = f"{frontend_url}/frontend/{path}"
    
    return final_url


def _enqueue_or_send_now(func, *args):
    """Queue email task or execute immediately when queue is unavailable."""
    if getattr(settings, 'USE_MAILDEV', False):
        return func(*args)

    try:
        import django_rq
        queue = django_rq.get_queue('default')
        return queue.enqueue(func, *args)
    except Exception as exc:
        logger.warning(
            "Email queue unavailable (%s). Falling back to direct send.", exc,
            exc_info=True
        )
        return func(*args)