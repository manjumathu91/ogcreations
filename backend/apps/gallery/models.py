from django.db import models

from apps.core.models import OrderedActive, TimeStamped
from apps.core.validators import validate_image


class BTSImage(TimeStamped, OrderedActive):
    image = models.ImageField(upload_to="bts/", validators=[validate_image])
    title = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "BTS image"

    def __str__(self):
        return self.title or f"BTS image #{self.pk}"
