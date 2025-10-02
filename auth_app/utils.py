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
import django_rq

logger = logging.getLogger(__name__)


def generate_activation_link(user):
    """Generate activation link for user.
    Creates secure URL with encoded UID and token for email verification.
    Returns complete frontend URL for account activation process."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/frontend/pages/auth/activate.html?uid={uid}&token={token}"


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
        text_content = f"Please activate your Videoflix account: {activation_link}"
        email = EmailMultiAlternatives(
            subject='Activate your Videoflix Account',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        email.attach_alternative(html_content, "text/html")
        
        logo_path = settings.BASE_DIR / 'static' / 'emails' / 'img' / 'logo_videoflix.svg'
        if logo_path.exists():
            with open(logo_path, 'rb') as logo_file:
                email.attach('logo_videoflix.svg', logo_file.read(), 'image/svg+xml')
                email.mixed_subtype = 'related'
            for attachment in email.attachments:
                if isinstance(attachment, tuple) and attachment[0] == 'logo_videoflix.svg':
                    email.attachments[-1] = (attachment[0], attachment[1], attachment[2])
        
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
    return f"{settings.FRONTEND_URL}/frontend/pages/auth/confirm_password.html?uid={uid}&token={token}"


def render_password_reset_email(user, reset_link):
    """Render password reset email HTML template."""
    return render_to_string('password_reset_email.html', {
        'reset_link': reset_link,
        'user': user,
    })


def send_password_reset_email_task(user_email, html_content, reset_link):
    """Send password reset email directly using EmailMultiAlternatives."""
    try:
        text_content = f"Please reset your Videoflix password: {reset_link}"
        email = EmailMultiAlternatives(
            subject='Password Reset - Videoflix',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        email.attach_alternative(html_content, "text/html")
        
        logo_path = settings.BASE_DIR / 'static' / 'emails' / 'img' / 'logo_videoflix.svg'
        if logo_path.exists():
            with open(logo_path, 'rb') as logo_file:
                email.attach('logo_videoflix.svg', logo_file.read(), 'image/svg+xml')
                email.mixed_subtype = 'related'
        
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
