from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import OrderedActive, SingletonModel, TimeStamped
from apps.core.validators import validate_image, validate_link


class NavbarSettings(SingletonModel):
    brand_text = models.CharField(max_length=100, blank=True, help_text="Text shown next to the logo (optional).")
    show_logo = models.BooleanField(default=True)
    cta_enabled = models.BooleanField("Show call-to-action button", default=False)
    cta_text = models.CharField("CTA text", max_length=50, blank=True)
    cta_url = models.CharField("CTA link", max_length=500, blank=True, validators=[validate_link])
    cta_new_tab = models.BooleanField("CTA opens in new tab", default=False)

    class Meta:
        verbose_name = "navbar settings"
        verbose_name_plural = "navbar settings"

    def __str__(self):
        return "Navbar settings"


class NavItem(TimeStamped, OrderedActive):
    """Main navigation link (parent=None) or a dropdown sub-link (parent set)."""

    title = models.CharField(max_length=100)
    url = models.CharField(
        "Link", max_length=500, validators=[validate_link],
        help_text="Internal path (/about), anchor (#contact) or full URL (https://...).",
    )
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    open_in_new_tab = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "navigation link"

    def __str__(self):
        return f"{self.parent.title} > {self.title}" if self.parent_id else self.title

    @property
    def link_type(self):
        u = (self.url or "").strip().lower()
        if u.startswith("#"):
            return "anchor"
        if u.startswith(("http://", "https://")):
            return "external"
        return "internal"

    def clean(self):
        super().clean()
        if self.parent_id:
            if self.pk and self.parent_id == self.pk:
                raise ValidationError({"parent": "An item cannot be its own parent."})
            if self.parent.parent_id:
                raise ValidationError({"parent": "Only top-level items can be parents (one dropdown level is supported)."})
            if self.pk and self.children.exists():
                raise ValidationError({"parent": "This item has sub-links, so it cannot become a sub-link itself."})


class FooterContent(SingletonModel):
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="branding/", blank=True, validators=[validate_image])
    copyright_text = models.CharField(max_length=255, blank=True, help_text="e.g. © 2026 OG Creations. All rights reserved.")
    contact_heading = models.CharField(max_length=60, default="Contact")
    show_contact_details = models.BooleanField(default=True)
    contact_email = models.EmailField("Footer email (override)", blank=True, help_text="Leave blank to use Site Settings.")
    contact_phone = models.CharField("Footer phone (override)", max_length=30, blank=True, help_text="Leave blank to use Site Settings.")
    contact_address = models.TextField("Footer address (override)", blank=True, help_text="Leave blank to use Site Settings.")
    show_whatsapp = models.BooleanField("Show WhatsApp button", default=True)
    whatsapp_label = models.CharField(max_length=60, default="Chat on WhatsApp")
    show_social = models.BooleanField("Show social links", default=True)

    class Meta:
        verbose_name = "footer content"
        verbose_name_plural = "footer content"

    def __str__(self):
        return "Footer content"


class FooterLinkGroup(TimeStamped, OrderedActive):
    title = models.CharField(max_length=100)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "footer link group"

    def __str__(self):
        return self.title


class FooterLink(TimeStamped, OrderedActive):
    group = models.ForeignKey(FooterLinkGroup, on_delete=models.CASCADE, related_name="links")
    title = models.CharField(max_length=100)
    url = models.CharField("Link", max_length=500, validators=[validate_link])
    open_in_new_tab = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "footer link"

    def __str__(self):
        return f"{self.group.title}: {self.title}"


class SocialLink(TimeStamped, OrderedActive):
    PLATFORMS = [
        ("instagram", "Instagram"), ("facebook", "Facebook"), ("youtube", "YouTube"), ("x", "X (Twitter)"),
        ("linkedin", "LinkedIn"), ("tiktok", "TikTok"), ("behance", "Behance"), ("vimeo", "Vimeo"),
        ("pinterest", "Pinterest"), ("website", "Website"), ("other", "Other"),
    ]
    platform = models.CharField(max_length=20, choices=PLATFORMS, default="instagram")
    label = models.CharField(max_length=60, blank=True, help_text="Optional display label.")
    url = models.URLField(max_length=500)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "social media link"

    def __str__(self):
        return self.label or self.get_platform_display()
