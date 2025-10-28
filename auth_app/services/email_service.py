import logging
import os
import mimetypes
import base64
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from email.mime.image import MIMEImage

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails (simplified):
    - Password reset
    - Registration confirmation
    This mirrors the smaller implementation you referenced.
    """

    @staticmethod
    def send_password_reset_email(user):
        from ..utils import build_frontend_url

        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        reset_url = build_frontend_url(f"pages/auth/confirm_password.html?uid={uidb64}&token={token}")

        site_name = getattr(settings, "SITE_NAME", "Videoflix")

        context = {
            "user": user,
            "reset_url": reset_url,
            "site_name": site_name,
        }

        EmailService._send_templated_email(
            template_name="password_reset_email",
            subject="Reset Your Password",
            recipient=user.email,
            context=context,
        )

    @staticmethod
    def send_registration_confirmation_email(user, token):
        from ..utils import build_frontend_url

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        confirmation_url = build_frontend_url(f"pages/auth/activate.html?uid={uidb64}&token={token}")

        context = {
            "user": user,
            "confirmation_url": confirmation_url,
            "site_name": getattr(settings, "SITE_NAME", "Videoflix"),
        }

        EmailService._send_templated_email(
            template_name="activation_email",
            subject="Confirm Your Registration",
            recipient=user.email,
            context=context,
        )

    @staticmethod
    def _render_text_template(template_name, context):
        try:
            return render_to_string(f"{template_name}.html", context=context)
        except TemplateDoesNotExist:
            logger.error("Required html template '%s.html' not found.", template_name)
            raise

    @staticmethod
    def _render_html_template(template_name, context):
        try:
            return render_to_string(f"{template_name}.html", context=context)
        except TemplateDoesNotExist:
            return None

    @staticmethod
    def _attach_inline_images(msg, inline_attachments):
        if not inline_attachments:
            return
        for att in inline_attachments:
            try:
                data = att.get("data")
                mimetype = att.get("mimetype", "image/png")
                maintype, subtype = mimetype.split("/", 1)
                if maintype != "image":
                    continue
                mime = MIMEImage(data, _subtype=subtype)
                cid = att.get("cid")
                if cid: mime.add_header("Content-ID", f"<{cid}>")
                mime.add_header("Content-Disposition", "inline")
                msg.attach(mime)
            except Exception:
                logger.exception("Failed to attach inline image %s", att.get("filename"))

    @staticmethod
    def _deliver_message(subject, message, recipient, html_message=None, inline_attachments=None):
        if inline_attachments:
            msg = EmailMultiAlternatives(subject=subject, body=message,
                                         from_email=settings.DEFAULT_FROM_EMAIL,
                                         to=[recipient])
            if html_message: msg.attach_alternative(html_message, "text/html")
            EmailService._attach_inline_images(msg, inline_attachments)
            msg.send(fail_silently=False)
            logger.info("Email sent to %s | Subject: %s", recipient, subject)
            return
        send_mail(subject=subject, message=message,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[recipient], html_message=html_message,
                  fail_silently=False)

    @staticmethod
    def _get_logo_inline_attachment():
        base = getattr(settings, "BASE_DIR", ".")
        candidates = [os.path.join(base, "auth_app", "templates", "img", n)
                      for n in ("logo_videoflix.png", "logo_videoflix.svg")]
        for p in candidates:
            try:
                if not os.path.exists(p):
                    continue
                with open(p, "rb") as f:
                    data = f.read()
                mimetype, _ = mimetypes.guess_type(p)
                if not mimetype:
                    mimetype = "image/png" if p.lower().endswith(".png") else "image/svg+xml"
                return [{"filename": os.path.basename(p), "data": data, "mimetype": mimetype, "cid": "logo_videoflix"}]
            except Exception:
                logger.debug("Could not read logo %s", p)
        return None

    @staticmethod
    def _get_logo_data_uri():
        item = EmailService._get_logo_inline_attachment()
        if not item:
            return None
        try:
            b64 = base64.b64encode(item[0]["data"]).decode("ascii")
            return f"data:{item[0]['mimetype']};base64,{b64}"
        except Exception:
            logger.debug("Failed to build data-uri for logo")
            return None

    @staticmethod
    def _get_logo_static_url():
        backend = getattr(settings, "BACKEND_URL", None)
        if not backend and getattr(settings, "DEBUG", False):
            backend = "http://127.0.0.1:8000"
        if not backend:
            return None
        static_seg = getattr(settings, "STATIC_URL", "/static/").strip("/")
        base = getattr(settings, "BASE_DIR", ".")
        for fname in ("logo_videoflix.png", "logo_videoflix.svg", "logo.png"):
            for p in (os.path.join(base, "static", "auth_app", fname), os.path.join(base, "auth_app", "templates", "img", fname)):
                try:
                    if os.path.exists(p):
                        return f"{backend.rstrip('/')}/{static_seg}/auth_app/{fname}"
                except Exception:
                    continue
        return None

    @staticmethod
    def _send_templated_email(template_name, subject, recipient, context):
        message = EmailService._render_text_template(template_name, context)
        html_message = EmailService._render_html_template(template_name, context)
        static = EmailService._get_logo_static_url(); inline = EmailService._get_logo_inline_attachment(); data_uri = EmailService._get_logo_data_uri()
        if static: context["logo_src"] = static
        elif inline: context["logo_src"] = "cid:logo_videoflix"
        elif data_uri: context["logo_data_uri"] = data_uri
        EmailService._deliver_message(subject, message, recipient, html_message=html_message, inline_attachments=inline)

