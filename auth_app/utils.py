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
    """Generate activation link for user.
    Creates secure URL with encoded UID and token for email verification."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"


def render_activation_email(user, activation_link):
    """Render activation email HTML template."""
    return render_to_string('emails/activation_email.html', {
        'activation_link': activation_link,
        'user': user,
    })


def queue_activation_email(user_email, html_message):
    """Queue activation email for sending via Django-RQ."""
    queue = django_rq.get_queue('default')
    queue.enqueue(
        send_mail, 
        'Activate your Videoflix Account', 
        '', 
        settings.DEFAULT_FROM_EMAIL, 
        [user_email], 
        fail_silently=False,
        html_message=html_message,
    )


def send_activation_email(user):
    """Send activation email to user.
    Queues HTML email with activation link using Django-RQ for async processing."""
    activation_link = generate_activation_link(user)
    html_message = render_activation_email(user, activation_link)
    queue_activation_email(user.email, html_message)


def generate_reset_link(user):
    """Generate password reset link for user.
    Creates secure URL with encoded UID and token for password recovery."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/password-reset/{uid}/{token}/"


def render_password_reset_email(user, reset_link):
    """Render password reset email HTML template."""
    return render_to_string('emails/password_reset_email.html', {
        'reset_link': reset_link,
        'user': user,
    })


def queue_password_reset_email(user_email, html_message):
    """Queue password reset email for sending via Django-RQ."""
    queue = django_rq.get_queue('default')
    queue.enqueue(
        send_mail, 
        'Password Reset - Videoflix', 
        '',  
        settings.DEFAULT_FROM_EMAIL, 
        [user_email], 
        fail_silently=False,
        html_message=html_message,
    )


def send_password_reset_email(user):
    """Send password reset email to user.
    Queues HTML email with reset link using Django-RQ for async processing."""
    reset_link = generate_reset_link(user)
    html_message = render_password_reset_email(user, reset_link)
    queue_password_reset_email(user.email, html_message)