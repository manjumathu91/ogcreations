from django.db import models

from apps.core.models import OrderedActive, TimeStamped
from apps.core.utils import unique_slug
from apps.core.validators import validate_image


class PortfolioProject(TimeStamped, OrderedActive):
    title = models.CharField("Project title", max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="Leave blank to generate from the title.")
    category = models.CharField(max_length=80, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="portfolio/", blank=True, validators=[validate_image])
    gallery_images = models.ManyToManyField("media_library.MediaItem", blank=True, related_name="+")
    video_url = models.URLField("Project video URL", max_length=500, blank=True)
    client_name = models.CharField(max_length=150, blank=True)
    project_date = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField("Featured", default=False)

    class Meta:
        ordering = ["order", "-project_date", "id"]
        verbose_name = "portfolio project"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)
