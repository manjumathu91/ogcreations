from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    ACTIONS = [("created", "Created"), ("updated", "Updated"), ("deleted", "Deleted"), ("toggled", "Toggled"), ("moved", "Reordered"), ("other", "Other")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    action = models.CharField(max_length=10, choices=ACTIONS, default="other")
    module = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.get_action_display()} {self.module}: {self.object_repr}"
