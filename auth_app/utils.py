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


def send_activation_email(user):
    """
    Send activation email to user.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
    
    subject = 'Activate your Videoflix Account'
    message = f"""
    Hello,
    
    please click on the following link to activate your account:
    {activation_link}
    
    If you did not register at Videoflix, please ignore this email.
    
    Best regards
    The Videoflix Team
    """
    
    queue = django_rq.get_queue('default')
    queue.enqueue(
        send_mail,
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(user):
    """
    Send password reset email to user.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_link = f"{settings.FRONTEND_URL}/password-reset/{uid}/{token}/"
    
    subject = 'Password Reset - Videoflix'
    message = f"""
    Hello,
    
    you have requested a password reset for your Videoflix account.
    
    Click on the following link to set a new password:
    {reset_link}
    
    If you did not make this request, please ignore this email.
    
    Best regards
    The Videoflix Team
    """
    
    queue = django_rq.get_queue('default')
    queue.enqueue(
        send_mail,
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )