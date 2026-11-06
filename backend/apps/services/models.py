from django.db import models

from apps.core.models import OrderedActive, TimeStamped
from apps.core.utils import unique_slug
from apps.core.validators import validate_image


class Service(TimeStamped, OrderedActive):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="Leave blank to generate from the title.")
    category = models.CharField(max_length=80, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=60, blank=True, help_text="Emoji or icon class name.")
    image = models.ImageField(upload_to="services/", blank=True, validators=[validate_image])
    additional_images = models.ManyToManyField(
    "media_library.MediaItem",
    blank=True,
    related_name="+",
)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)
