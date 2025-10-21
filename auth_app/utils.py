"""
Utility functions for authentication app.
"""
import logging

from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

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
    
    # Simple default: assume Live Server runs from frontend/ directory (most common case)
    # This can be overridden with FRONTEND_PATH_PREFIX environment variable
    _frontend_path_prefix_cache = ''
    logger.info("Default: Live Server assumed to run from frontend/ directory")
    return ''
def build_frontend_url(path):
    """Build complete frontend URL with automatic path detection.
    
    Automatically detects whether Live Server runs from frontend/ or root directory
    by checking if the frontend files are accessible at the base URL.
    
    Args:
        path (str): Relative path from frontend root (e.g., 'pages/auth/activate.html')
        
    Returns:
        str: Complete frontend URL
        
    Examples:
        # Auto-detects and builds correct URL:
        # Live Server from frontend/: http://localhost:5500/pages/auth/activate.html
        # Live Server from root/: http://localhost:5500/frontend/pages/auth/activate.html
    """
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    path_prefix = getattr(settings, 'FRONTEND_PATH_PREFIX', 'auto').strip('/')
    path = path.lstrip('/')
    
    print(f"DEBUG build_frontend_url - frontend_url: {frontend_url}")
    print(f"DEBUG build_frontend_url - path_prefix: {path_prefix}")
    print(f"DEBUG build_frontend_url - path: {path}")
    
    if path_prefix == 'auto':
        path_prefix = detect_frontend_path_prefix()
        print(f"DEBUG build_frontend_url - detected path_prefix: {path_prefix}")
    
    if path_prefix:
        final_url = f"{frontend_url}/{path_prefix}/{path}"
    else:
        final_url = f"{frontend_url}/{path}"
    
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


def send_activation_email_task(user_email, html_content, activation_link):
    """Send activation email directly using EmailMultiAlternatives."""
    try:
        from email.mime.image import MIMEImage
        
        text_content = f"Please activate your Videoflix account: {activation_link}"
        email = EmailMultiAlternatives(
            subject='Activate your Videoflix Account',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.mixed_subtype = 'related'
        
        logo_path = settings.BASE_DIR / 'auth_app' / 'templates' / 'static' / 'images' / 'logo_videoflix.png'
        print(f"Looking for PNG logo at: {logo_path}")
        
        if logo_path.exists():
            print(f"Found PNG logo: {logo_path}")
            with open(logo_path, 'rb') as logo_file:
                logo_data = logo_file.read()
                image = MIMEImage(logo_data, 'png')
                image.add_header('Content-ID', '<logo_videoflix>')
                image.add_header('Content-Disposition', 'inline', filename='logo_videoflix.png')
                email.attach(image)
                print("PNG logo attached successfully")
        else:
            print(f"PNG logo not found at {logo_path}")
        
        result = email.send()
        print(f"Activation email sent successfully to {user_email}: {result}")
        return result
    except Exception as e:
        print(f"Error sending activation email to {user_email}: {str(e)}")
        raise


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


def send_activation_email(user):
    """Send activation email to user.
    Queues HTML email with activation link using Django-RQ for async processing."""
    activation_link = generate_activation_link(user)
    html_message = render_activation_email(user, activation_link)

    _enqueue_or_send_now(send_activation_email_task, user.email, html_message, activation_link)


def generate_reset_link(user):
    """Generate password reset link for user.
    Creates secure URL with encoded UID and token for password recovery.
    Returns complete frontend URL for password reset process."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return build_frontend_url(f"pages/auth/confirm_password.html?uid={uid}&token={token}")


def render_password_reset_email(user, reset_link):
    """Render password reset email HTML template."""
    return render_to_string('password_reset_email.html', {
        'reset_link': reset_link,
        'user': user,
    })


def send_password_reset_email_task(user_email, html_content, reset_link):
    """Send password reset email directly using EmailMultiAlternatives."""
    try:
        from email.mime.image import MIMEImage
        
        text_content = f"Please reset your Videoflix password: {reset_link}"
        email = EmailMultiAlternatives(
            subject='Password Reset - Videoflix',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.mixed_subtype = 'related'
        
        logo_path = settings.BASE_DIR / 'static' / 'emails' / 'img' / 'logo_videoflix.svg'
        if logo_path.exists():
            with open(logo_path, 'rb') as logo_file:
                logo_data = logo_file.read()
                image = MIMEImage(logo_data, 'svg+xml')
                image.add_header('Content-ID', '<logo_videoflix>')
                image.add_header('Content-Disposition', 'inline', filename='logo_videoflix.svg')
                email.attach(image)
        
        result = email.send()
        print(f"Password reset email sent successfully to {user_email}: {result}")
        return result
    except Exception as e:
        print(f"Error sending password reset email to {user_email}: {str(e)}")
        raise


def send_password_reset_email(user):
    """Send password reset email to user.
    Queues HTML email with reset link using Django-RQ for async processing."""
    reset_link = generate_reset_link(user)
    html_message = render_password_reset_email(user, reset_link)

    _enqueue_or_send_now(send_password_reset_email_task, user.email, html_message, reset_link)
