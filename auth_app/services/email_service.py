import logging
import os
import mimetypes
import base64

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from email.mime.image import MIMEImage

logger = logging.getLogger(__name__)


class EmailService:

    @staticmethod
    def send_email(recipient, subject, template_name=None, context=None, html_message=None, inline_attachments=None):
        """Orchestrate sending an email using template or provided HTML.
        """
        context = context or {}
        html = EmailService._render_html(template_name, context) if html_message is None else html_message
        body = context.get("body") or context.get("message") or "Please check the requested action."
        msg = EmailService._create_message(subject, body, recipient)
        if html: msg.attach_alternative(html, "text/html")
        EmailService._attach_inline_images(msg, inline_attachments)
        try:
            msg.send(fail_silently=False)
            logger.info("Email sent to %s", recipient)
        except Exception:
            logger.exception("Failed to send email to %s", recipient)
            raise

    @staticmethod
    def _render_html(template_name, context):
        """Render HTML template or return None if missing.
        """
        if not template_name: return None
        try:
            return render_to_string(f"{template_name}.html", context=context)
        except TemplateDoesNotExist:
            logger.debug("Template %s.html not found", template_name)
            return None

    @staticmethod
    def _create_message(subject, body, recipient):
        """Create EmailMultiAlternatives with standard headers.
        """
        return EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[recipient],
        )

    @staticmethod
    def _attach_inline_images(msg, inline_attachments):
        """Attach simple image attachments as inline CID images.
        """
        if not inline_attachments: return
        for att in inline_attachments:
            try:
                data = att.get("data")
                mimetype = att.get("mimetype", "image/png")
                cid = att.get("cid")
                maintype, subtype = mimetype.split("/", 1)
                if maintype != "image":
                    continue
                mime = MIMEImage(data, _subtype=subtype)
                if cid: mime.add_header("Content-ID", f"<{cid}>")
                mime.add_header("Content-Disposition", "inline")
                msg.attach(mime)
            except Exception:
                logger.exception("Failed to attach inline image %s", att.get("filename"))
                continue

    @staticmethod
    def send_password_reset_email(user):
        """Create token, build a frontend reset URL and send the password email.
        """
        from ..utils import build_frontend_url
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = build_frontend_url(f"pages/auth/confirm_password.html?uid={uid}&token={token}")
        context = {"user": user, "reset_url": reset_url, "site_name": getattr(settings, "SITE_NAME", "Videoflix")}
        static = EmailService._get_logo_static_url(); inline = EmailService._get_logo_inline_attachment(); data_uri = EmailService._get_logo_data_uri()
        if static: context["logo_src"] = static
        elif inline: context["logo_src"] = "cid:logo_videoflix"
        elif data_uri: context["logo_data_uri"] = data_uri
        EmailService.send_email(user.email, "Reset your password", template_name="password_reset_email", context=context, inline_attachments=inline)

    @staticmethod
    def send_registration_confirmation_email(user, token):
        """Build confirmation link and send registration confirmation email.
        """
        from ..utils import build_frontend_url
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        confirm = build_frontend_url(f"pages/auth/activate.html?uid={uid}&token={token}")
        context = {"user": user, "confirmation_url": confirm, "site_name": getattr(settings, "SITE_NAME", "Videoflix")}
        static = EmailService._get_logo_static_url(); inline = EmailService._get_logo_inline_attachment(); data_uri = EmailService._get_logo_data_uri()
        if static: context["logo_src"] = static
        elif inline: context["logo_src"] = "cid:logo_videoflix"
        elif data_uri: context["logo_data_uri"] = data_uri
        EmailService.send_email(user.email, "Confirm registration", template_name="activation_email", context=context, inline_attachments=inline)

    @staticmethod
    def _get_logo_inline_attachment():
        """Return a single inline attachment dict for the logo or None.
        """
        base = getattr(settings, "BASE_DIR", ".")
        candidates = [os.path.join(base, "auth_app", "templates", "img", n) for n in ("logo_videoflix.png", "logo_videoflix.svg")]
        for p in candidates:
            try:
                if not os.path.exists(p): continue
                with open(p, "rb") as f: data = f.read()
                mimetype, _ = mimetypes.guess_type(p)
                if not mimetype: mimetype = "image/png" if p.lower().endswith(".png") else "image/svg+xml"
                return [{"filename": os.path.basename(p), "data": data, "mimetype": mimetype, "cid": "logo_videoflix"}]
            except Exception:
                logger.debug("Could not read logo %s", p)
        return None

    @staticmethod
    def _get_logo_data_uri():
        """Return a base64 data URI for the logo or None.
        """
        item = EmailService._get_logo_inline_attachment()
        if not item: return None
        try: b64 = base64.b64encode(item[0]["data"]).decode("ascii"); return f"data:{item[0]['mimetype']};base64,{b64}"
        except Exception:
            logger.debug("Failed to build data-uri for logo"); return None

    @staticmethod
    def _get_logo_static_url():
        """Return a full static URL to the logo if the file exists locally.
        """
        backend = getattr(settings, "BACKEND_URL", None)
        if not backend and getattr(settings, "DEBUG", False): backend = "http://127.0.0.1:8000"
        if not backend: return None
        static_seg = getattr(settings, "STATIC_URL", "/static/").strip("/")
        base = getattr(settings, "BASE_DIR", ".")
        for fname in ("logo_videoflix.png", "logo_videoflix.svg", "logo.png"):
            for p in (os.path.join(base, "static", "auth_app", fname), os.path.join(base, "auth_app", "templates", "img", fname)):
                try:
                    if os.path.exists(p): return f"{backend.rstrip('/')}/{static_seg}/auth_app/{fname}"
                except Exception:
                    continue
        return None

