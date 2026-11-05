from django.db import models

from apps.core.models import TimeStamped
from apps.core.utils import build_whatsapp_url


class Lead(TimeStamped):
    STATUS_NEW, STATUS_CONTACTED, STATUS_PROGRESS, STATUS_DONE, STATUS_REJECTED = (
        "new", "contacted", "in_progress", "completed", "rejected",
    )
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_CONTACTED, "Contacted"),
        (STATUS_PROGRESS, "In Progress"),
        (STATUS_DONE, "Completed"),
        (STATUS_REJECTED, "Rejected"),
    ]
    TYPE_CHOICES = [("contact", "Contact form"), ("project", "Project enquiry")]
    CONTACT_METHODS = [("email", "Email"), ("phone", "Phone call"), ("whatsapp", "WhatsApp")]

    lead_type = models.CharField("Type", max_length=10, choices=TYPE_CHOICES, default="contact")
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField("WhatsApp number", max_length=30, blank=True)
    project_type = models.CharField(max_length=120, blank=True)
    project_reference = models.CharField(
        max_length=200, blank=True, help_text="Portfolio project the visitor enquired about (if any)."
    )
    message = models.TextField()
    preferred_contact = models.CharField(max_length=10, choices=CONTACT_METHODS, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)
    internal_notes = models.TextField(blank=True, help_text="Private - never shown on the website or to the AI assistant.")

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["lead_type", "status"])]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def whatsapp_link(self, site_name=None):
        if site_name is None:
            from apps.site_settings.models import SiteSettings

            site_name = SiteSettings.load().site_name
        number = self.whatsapp_number or self.phone
        text = f"Hi {self.name}, thanks for contacting {site_name}"
        if self.project_type:
            text += f" about {self.project_type}"
        return build_whatsapp_url(number, text + ".")
