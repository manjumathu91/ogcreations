import os

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.core.validators import validate_image


class MediaItem(models.Model):
    title = models.CharField(max_length=150, blank=True)
    alt_text = models.CharField("Alt text", max_length=255, blank=True, help_text="Describe the image for accessibility/SEO.")
    file = models.ImageField(upload_to="library/%Y/%m/", validators=[validate_image], width_field="width", height_field="height")
    width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    file_size = models.PositiveIntegerField(default=0, editable=False)
    is_public = models.BooleanField("Public", default=True, help_text="Listed in the public /api/media/ endpoint.")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "media item"

    def __str__(self):
        return self.title or os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        if self.file:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
            if not self.title:
                self.title = os.path.splitext(os.path.basename(self.file.name))[0][:150]
        super().save(*args, **kwargs)


@receiver(post_delete, sender=MediaItem)
def delete_media_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
