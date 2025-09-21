"""
Utility functions for authentication app.
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
import django_rq


def generate_activation_link(user):
    """Generate activation link for user."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"


def create_activation_message(activation_link):
    """Create activation email message."""
    return f"""
    Hello,
    
    please click on the following link to activate your account:
    {activation_link}
    
    If you did not register at Videoflix, please ignore this email.
    
    Best regards
    The Videoflix Team
    """


def send_activation_email(user):
    """Send activation email to user."""
    activation_link = generate_activation_link(user)
    message = create_activation_message(activation_link)
    
    queue = django_rq.get_queue('default')
    queue.enqueue(
        send_mail, 'Activate your Videoflix Account', message,
        settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False,
    )


def generate_reset_link(user):
    """Generate password reset link for user."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/password-reset/{uid}/{token}/"


def create_reset_message(reset_link):
    """Create password reset email message."""
    return f"""
    Hello,
    
    you have requested a password reset for your Videoflix account.
    
    Click on the following link to set a new password:
    {reset_link}
    
    If you did not make this request, please ignore this email.
    
    Best regards
    The Videoflix Team
    """


def send_password_reset_email(user):
    """Send password reset email to user."""
    reset_link = generate_reset_link(user)
    message = create_reset_message(reset_link)
    
    queue = django_rq.get_queue('default')
    queue.enqueue(
        send_mail, 'Password Reset - Videoflix', message,
        settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False,
    )