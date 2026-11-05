from django.conf import settings
from django.db import models

from apps.core.models import SingletonModel, TimeStamped


class AISettings(SingletonModel):
    is_enabled = models.BooleanField("AI enabled", default=True, help_text="Master switch (also requires AI_ENABLED=True in the environment).")
    public_chat_enabled = models.BooleanField("Public chat widget enabled", default=True)
    admin_assistant_enabled = models.BooleanField("Admin AI assistant enabled", default=True)
    assistant_name = models.CharField(max_length=60, default="Studio Assistant")
    welcome_message = models.CharField(max_length=300, default="Hi! Ask me about our studio, services, portfolio or how to start a project.")
    extra_instructions = models.TextField(
        blank=True, help_text="Optional extra tone/behaviour instructions for the public assistant. It still only uses approved website content.",
    )
    temperature = models.FloatField(default=0.4, help_text="0 = precise, 1 = creative.")
    max_tokens = models.PositiveIntegerField(default=600)

    class Meta:
        verbose_name = "AI settings"
        verbose_name_plural = "AI settings"

    def __str__(self):
        return "AI settings"


class AIConversation(TimeStamped):
    SCOPE_CHOICES = [("public", "Public visitor"), ("admin", "Admin")]
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, default="public", db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="ai_conversations")
    session_id = models.CharField(max_length=64, blank=True, db_index=True)
    title = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-updated_at", "-id"]

    def __str__(self):
        return self.title or f"Conversation #{self.pk}"


class AIMessage(models.Model):
    ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant")]
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
