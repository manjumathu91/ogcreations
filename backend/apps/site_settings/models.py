from urllib.parse import quote_plus

from django.db import models

from apps.core.models import SingletonModel
from apps.core.utils import build_whatsapp_url
from apps.core.validators import hex_color_validator, validate_image, validate_maps_embed


class SiteSettings(SingletonModel):
    # Brand
    site_name = models.CharField(max_length=100, default="OG Creations")
    tagline = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to="branding/", blank=True, validators=[validate_image])
    favicon = models.ImageField(upload_to="branding/", blank=True, validators=[validate_image])
    background_color = models.CharField(max_length=7, default="#FAF6F2", validators=[hex_color_validator])
    primary_color = models.CharField(max_length=7, default="#8D2236", validators=[hex_color_validator])
    accent_color = models.CharField(max_length=7, default="#FBBF24", validators=[hex_color_validator])
    secondary_color = models.CharField(max_length=7, default="#FAF5F0", validators=[hex_color_validator])
    text_color = models.CharField(max_length=7, default="#1A1A1A", validators=[hex_color_validator])
    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField(
        max_length=30, blank=True, help_text="International format with country code, e.g. +91XXXXXXXXXX."
    )
    whatsapp_enabled = models.BooleanField(default=True)
    whatsapp_default_message = models.TextField(
        default="Hi! I'd like to know more about your services.", help_text="Pre-filled message when visitors click WhatsApp."
    )
    business_hours = models.TextField(blank=True, help_text="One line per entry, e.g. Mon-Sat: 10:00 - 18:00")
    # Address & location (enter the real studio details here - nothing is invented)
    address = models.TextField("Studio address", blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    google_maps_url = models.URLField("Google Maps URL", max_length=500, blank=True)
    google_maps_embed_url = models.URLField(
        "Google Maps embed URL", max_length=1000, blank=True, validators=[validate_maps_embed],
        help_text="Only the src URL from Google Maps > Share > Embed a map.",
    )
    # SEO
    seo_title = models.CharField("SEO title", max_length=70, blank=True)
    seo_description = models.CharField("SEO description", max_length=300, blank=True)
    seo_keywords = models.CharField("SEO keywords", max_length=300, blank=True)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self):
        return self.site_name

    @property
    def full_address(self):
        parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ", ".join(p.strip() for p in parts if p and p.strip())

    def whatsapp_url(self, message=None):
        if not self.whatsapp_enabled:
            return ""
        return build_whatsapp_url(self.whatsapp_number, self.whatsapp_default_message if message is None else message)

    @property
    def maps_url(self):
        if self.google_maps_url:
            return self.google_maps_url
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"
        if self.full_address:
            return f"https://www.google.com/maps/search/?api=1&query={quote_plus(self.full_address)}"
        return ""

    @property
    def directions_url(self):
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps/dir/?api=1&destination={self.latitude},{self.longitude}"
        if self.full_address:
            return f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(self.full_address)}"
        return self.google_maps_url
