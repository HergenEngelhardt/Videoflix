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
    
    subject = 'Aktiviere dein Videoflix Konto'
    message = f"""
    Hallo,
    
    bitte klicke auf den folgenden Link, um dein Konto zu aktivieren:
    {activation_link}
    
    Falls du dich nicht bei Videoflix registriert hast, ignoriere diese E-Mail.
    
    Viele Grüße
    Das Videoflix Team
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
    
    subject = 'Passwort zurücksetzen - Videoflix'
    message = f"""
    Hallo,
    
    du hast eine Passwort-Zurücksetzung für dein Videoflix Konto angefordert.
    
    Klicke auf den folgenden Link, um ein neues Passwort zu setzen:
    {reset_link}
    
    Falls du diese Anfrage nicht gestellt hast, ignoriere diese E-Mail.
    
    Viele Grüße
    Das Videoflix Team
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