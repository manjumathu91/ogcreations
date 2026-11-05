from django.db import models


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrderedActive(models.Model):
    """Display order + active flag shared by every website content model."""

    order = models.PositiveIntegerField("Display order", default=0, help_text="Lower numbers appear first.")
    is_active = models.BooleanField("Active", default=True, help_text="Only active items appear on the website.")

    class Meta:
        abstract = True


class SingletonModel(TimeStamped):
    """A model that only ever has one row (pk=1), e.g. site settings."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # singletons are never deleted
        return (0, {})

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
