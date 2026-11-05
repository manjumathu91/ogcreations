from django.db import models

from apps.core.models import OrderedActive, TimeStamped
from apps.core.validators import validate_image


class UpcomingProject(TimeStamped, OrderedActive):
    STATUS = [
        ("announced", "Announced"),
        ("in_production", "In production"),
        ("post_production", "Post-production"),
        ("coming_soon", "Coming soon"),
        ("released", "Released"),
    ]
    title = models.CharField("Project title", max_length=200)
    description = models.TextField(blank=True)
    poster = models.ImageField(upload_to="upcoming/", blank=True, validators=[validate_image])
    release_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="coming_soon")

    class Meta:
        ordering = ["order", "release_date", "id"]
        verbose_name = "upcoming project"

    def __str__(self):
        return self.title
