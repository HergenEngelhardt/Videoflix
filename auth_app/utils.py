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
    
    print(f"DEBUG build_frontend_url - frontend_url: {frontend_url}")
    print(f"DEBUG build_frontend_url - path: {path}")
    
    final_url = f"{frontend_url}/frontend/{path}"
    
    print(f"DEBUG build_frontend_url - final_url: {final_url}")
    return final_url


def generate_activation_link(user):
    """Generate activation link for user.
    Creates secure URL with encoded UID and token for email verification.
    Returns complete frontend URL for account activation process."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return build_frontend_url(f"pages/auth/activate.html?uid={uid}&token={token}")


def render_activation_email(user, activation_link):
    """Render activation email HTML template.
    Creates formatted HTML email content with activation link."""
    return render_to_string('activation_email.html', {
        'activation_link': activation_link,
        'user': user,
    })


def _enqueue_or_send_now(func, *args):
    """Queue email task or execute immediately when queue is unavailable."""
    if getattr(settings, 'USE_MAILDEV', False):
        logger.debug("Maildev enabled – sending email immediately without queue")
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


def encode_user_id_to_base64(user_id):
    """Encode user ID to base64 (like colleague's implementation)."""
    data = str(user_id)  
    data_bytes = data.encode("utf-8") 
    uid_base64 = urlsafe_base64_encode(data_bytes)
    return uid_base64


def decode_uidb64_to_int(uidb64):
    """Decode uidb64 to integer user ID (like colleague's implementation)."""
    uid_bytes = urlsafe_base64_decode(uidb64) 
    uid_str = uid_bytes.decode("utf-8")
    uid_int = int(uid_str)
    return uid_int


def token_is_valid(token_obj):
    """Check if token object is valid and not expired (like colleague's implementation)."""
    if not token_obj:
        return False
    if token_obj.is_expired:
        token_obj.delete()
        return False
    return True
