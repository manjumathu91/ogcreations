from django.db import models


class EmailLog(models.Model):
    KIND_CHOICES = [
        ("admin_notification", "Admin notification"),
        ("customer_ack", "Customer acknowledgement"),
        ("test", "Test email"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [("sent", "Sent"), ("failed", "Failed")]

    kind = models.CharField(max_length=30, choices=KIND_CHOICES, default="other")
    to_email = models.CharField(max_length=254)
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="failed")
    error_message = models.TextField(blank=True)
    lead = models.ForeignKey("leads.Lead", null=True, blank=True, on_delete=models.SET_NULL, related_name="email_logs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.get_kind_display()} to {self.to_email} - {self.status}"
