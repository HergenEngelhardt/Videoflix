import logging
import os
import base64
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails
    currently: Password Reset + Registration Confirmation
    """

    @staticmethod
    def send_password_reset_email(user):
        from ..utils import build_frontend_url
        
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        
        reset_url = build_frontend_url(f"pages/auth/confirm_password.html?uid={uidb64}&token={token}")

        site_name = getattr(settings, 'SITE_NAME', 'Videoflix')

        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': site_name,
        }

        logo_path = os.path.join(settings.BASE_DIR, 'auth_app', 'templates', 'img', 'logo_videoflix.svg')
        logger.info(f"Logo path: {logo_path}, exists: {os.path.exists(logo_path)}")
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
            encoded = base64.b64encode(logo_data).decode('utf-8')
            context['logo_src'] = f"data:image/svg+xml;base64,{encoded}"
        else:
            context['logo_src'] = '' 
        EmailService._send_templated_email(
            template_name='password_reset_email',
            subject='Reset Your Password',
            recipient=user.email,
            context=context
        )

    @staticmethod
    def send_registration_confirmation_email(user, token):
        from ..utils import build_frontend_url
        
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        
        confirmation_url = build_frontend_url(f"pages/auth/activate.html?uid={uidb64}&token={token}")
        
        context = {
            'user': user,
            'confirmation_url': confirmation_url,
            'site_name': getattr(settings, 'SITE_NAME', 'Videoflix'),
        }

        logo_path = os.path.join(settings.BASE_DIR, 'auth_app', 'templates', 'img', 'logo_videoflix.svg')
        logger.info(f"Logo path: {logo_path}, exists: {os.path.exists(logo_path)}")
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
            encoded = base64.b64encode(logo_data).decode('utf-8')
            context['logo_src'] = f"data:image/svg+xml;base64,{encoded}"
        else:
            context['logo_src'] = '' 

        EmailService._send_templated_email(
            template_name='activation_email',
            subject='Confirm Your Registration',
            recipient=user.email,
            context=context
        )

    @staticmethod
    def _send_templated_email(template_name, subject, recipient, context):
        """
        Render and send a templated HTML email with embedded logo.
        """
        try:
            html_message = render_to_string(f'{template_name}.html', context=context)
        except TemplateDoesNotExist:
            logger.error(f"Required HTML template '{template_name}.html' not found. Email not sent.")
            raise

        try:
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient],
            )
            email.content_subtype = 'html'
            
            email.send(fail_silently=False)
            logger.info(f"Email successfully sent to {recipient} | Subject: '{subject}'")
        except SMTPException as e:
            logger.error(f"SMTP error while sending email to {recipient}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while sending email to {recipient}: {e}")
            raise