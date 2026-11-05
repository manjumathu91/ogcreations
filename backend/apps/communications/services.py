"""SMTP email sending with full status/error logging.

Leads are always saved to the database BEFORE any email is attempted, and every
function here swallows (and logs) exceptions so a mail failure can never lose an enquiry.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.site_settings.models import SiteSettings

from .models import EmailLog

logger = logging.getLogger(__name__)


def email_is_configured():
    if settings.EMAIL_BACKEND.endswith("smtp.EmailBackend"):
        return bool(settings.EMAIL_HOST and settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)
    return True  # console / locmem / custom backends


def email_config_summary():
    """Safe-to-display SMTP configuration (the password is never exposed)."""
    return {
        "backend": settings.EMAIL_BACKEND,
        "host": settings.EMAIL_HOST or "(not set)",
        "port": settings.EMAIL_PORT,
        "user": settings.EMAIL_HOST_USER or "(not set)",
        "password_set": bool(settings.EMAIL_HOST_PASSWORD),
        "use_tls": settings.EMAIL_USE_TLS,
        "use_ssl": settings.EMAIL_USE_SSL,
        "from_email": settings.DEFAULT_FROM_EMAIL,
        "admin_notify_email": settings.ADMIN_NOTIFY_EMAIL or "(falls back to Site Settings email)",
        "configured": email_is_configured(),
    }


def send_logged_email(kind, to_email, subject, template, context, lead=None, reply_to=None):
    """Render + send one email. Always returns the EmailLog; never raises."""
    subject = " ".join(str(subject).split())[:255]  # no newlines (header-injection safe)
    log = EmailLog(kind=kind, to_email=str(to_email)[:254], subject=subject, lead=lead)
    try:
        if not email_is_configured():
            raise RuntimeError("SMTP is not configured. Set EMAIL_HOST, EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in the environment.")
        html = render_to_string(template, context)
        message = EmailMultiAlternatives(
            subject=subject,
            body=strip_tags(html),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            reply_to=[reply_to] if reply_to else None,
        )
        message.attach_alternative(html, "text/html")
        message.send(fail_silently=False)
        log.status = "sent"
    except Exception as exc:
        log.status = "failed"
        log.error_message = f"{exc.__class__.__name__}: {exc}"[:2000]
        logger.warning("Email to %s failed: %s", to_email, log.error_message)
    try:
        log.save()
    except Exception:  # pragma: no cover
        logger.exception("Could not save EmailLog")
    return log


def notify_new_lead(lead):
    """Admin notification + customer acknowledgement for a saved lead."""
    site = SiteSettings.load()
    results = []
    context = {"lead": lead, "site": site}
    admin_to = settings.ADMIN_NOTIFY_EMAIL or site.email
    if admin_to:
        results.append(
            send_logged_email(
                "admin_notification", admin_to,
                f"New {lead.get_lead_type_display().lower()} from {lead.name}",
                "emails/lead_admin.html", context, lead=lead, reply_to=lead.email,
            )
        )
    else:
        EmailLog.objects.create(
            kind="admin_notification", to_email="(none)", subject="Admin notification skipped", status="failed", lead=lead,
            error_message="No admin recipient: set ADMIN_NOTIFY_EMAIL or the email in Site Settings.",
        )
    results.append(
        send_logged_email(
            "customer_ack", lead.email, f"We received your message - {site.site_name}",
            "emails/lead_ack.html", context, lead=lead, reply_to=site.email or None,
        )
    )
    return results


def send_test_email(to_email):
    site = SiteSettings.load()
    return send_logged_email("test", to_email, f"Test email from {site.site_name}", "emails/test.html", {"site": site})
