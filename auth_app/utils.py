"""
Utility functions for authentication app.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
import django_rq


def generate_activation_link(user):
    """Generate activation link for user.
    Creates secure URL with encoded UID and token for email verification.
    Returns complete frontend URL for account activation process."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/pages/auth/activate.html?uid={uid}&token={token}"


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
        result = email.send()
        print(f"Activation email sent successfully to {user_email}: {result}")
        return result
    except Exception as e:
        print(f"Error sending activation email to {user_email}: {str(e)}")
        raise


def send_activation_email(user):
    """Send activation email to user.
    Queues HTML email with activation link using Django-RQ for async processing."""
    activation_link = generate_activation_link(user)
    html_message = render_activation_email(user, activation_link)
    
    # Queue the email for async sending
    queue = django_rq.get_queue('default')
    queue.enqueue(send_activation_email_task, user.email, html_message, activation_link)


def generate_reset_link(user):
    """Generate password reset link for user.
    Creates secure URL with encoded UID and token for password recovery.
    Returns complete frontend URL for password reset process."""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/pages/auth/confirm_password.html?uid={uid}&token={token}"


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
    
    # Queue the email for async sending
    queue = django_rq.get_queue('default')
    queue.enqueue(send_password_reset_email_task, user.email, html_message, reset_link)
