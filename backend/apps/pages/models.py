from django.db import models

from apps.core.models import OrderedActive, TimeStamped
from apps.core.validators import validate_image, validate_link, validate_video


class HeroSection(TimeStamped, OrderedActive):
    heading = models.CharField("Main heading", max_length=200)
    subheading = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    hero_image = models.ImageField(upload_to="hero/", blank=True, validators=[validate_image])
    background_video = models.FileField(upload_to="hero/videos/", blank=True, validators=[validate_video], help_text="Optional MP4/WEBM.")
    primary_button_text = models.CharField(max_length=50, blank=True)
    primary_button_url = models.CharField(max_length=500, blank=True, validators=[validate_link])
    secondary_button_text = models.CharField(max_length=50, blank=True)
    secondary_button_url = models.CharField(max_length=500, blank=True, validators=[validate_link])

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "hero section"

    def __str__(self):
        return self.heading


class AboutSection(TimeStamped, OrderedActive):
    title = models.CharField("Section title", max_length=200)
    description = models.TextField()
    image = models.ImageField("Studio image", upload_to="about/", blank=True, validators=[validate_image])
    additional_images = models.ManyToManyField("media_library.MediaItem", blank=True, related_name="+")
    experience_years = models.PositiveSmallIntegerField("Years of experience", null=True, blank=True)
    highlights = models.TextField(blank=True, help_text="One studio highlight per line.")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "about section"

    def __str__(self):
        return self.title

    @property
    def highlight_list(self):
        return [line.strip() for line in self.highlights.splitlines() if line.strip()]


class ProcessStep(TimeStamped, OrderedActive):
    step_number = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=60, blank=True, help_text="Emoji or icon class name (e.g. 🎬 or fa-film).")
    icon_image = models.ImageField(upload_to="process/", blank=True, validators=[validate_image])

    class Meta:
        ordering = ["order", "step_number", "id"]
        verbose_name = "production step"

    def __str__(self):
        return f"{self.step_number}. {self.title}"
