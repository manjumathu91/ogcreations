"""Authenticated admin API (staff session + CSRF). CRUD for every content module.

Mounted at /api/admin/. Browsable list: GET /api/admin/
"""
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework import serializers, status
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.ai_assistant.models import AIConversation, AIMessage, AISettings
from apps.ai_assistant.services import (
    TASKS, AIConfigError, AIServiceError, admin_chat_system_prompt, ai_status, build_admin_task_messages, groq_chat,
)
from apps.communications.models import EmailLog
from apps.dashboard.utils import log_activity
from apps.gallery.models import BTSImage
from apps.leads.models import Lead
from apps.media_library.models import MediaItem
from apps.navigation.models import FooterContent, FooterLink, FooterLinkGroup, NavbarSettings, NavItem, SocialLink
from apps.pages.models import AboutSection, HeroSection, ProcessStep
from apps.portfolio.models import PortfolioProject
from apps.projects.models import UpcomingProject
from apps.services.models import Service
from apps.site_settings.models import SiteSettings

PARSERS = [JSONParser, MultiPartParser, FormParser]


class AdminCRUDMixin:
    key = ""
    filter_fields = []
    parser_classes = PARSERS
    permission_classes = [IsAdminUser]
    filter_backends = [SearchFilter]

    def get_queryset(self):
        qs = self.queryset.all()
        model = self.queryset.model
        for name in self.filter_fields:
            value = self.request.query_params.get(name)
            if value in (None, ""):
                continue
            try:
                if isinstance(model._meta.get_field(name), models.BooleanField):
                    value = value.lower() in ("1", "true", "yes")
                qs = qs.filter(**{name: value})
            except (ValueError, TypeError, ValidationError):
                return qs.none()
        return qs

    def perform_create(self, serializer):
        extra = {"uploaded_by": self.request.user} if hasattr(self.queryset.model, "uploaded_by") else {}
        obj = serializer.save(**extra)
        log_activity(self.request.user, "created", f"{self.key} (API)", obj)

    def perform_update(self, serializer):
        obj = serializer.save()
        log_activity(self.request.user, "updated", f"{self.key} (API)", obj)

    def perform_destroy(self, instance):
        log_activity(self.request.user, "deleted", f"{self.key} (API)", instance)
        instance.delete()


def _serializer_for(model, base=serializers.ModelSerializer, **attrs):
    meta = type("Meta", (), {"model": model, "fields": "__all__"})
    return type(f"{model.__name__}AdminSerializer", (base,), {"Meta": meta, **attrs})


class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = ["id", "role", "content", "created_at"]


def build_viewset(key, model, search_fields, filter_fields=(), read_only=False, serializer=None):
    base = ReadOnlyModelViewSet if read_only else ModelViewSet
    attrs = {
        "key": key,
        "queryset": model.objects.all(),
        "serializer_class": serializer or _serializer_for(model),
        "search_fields": list(search_fields),
        "filter_fields": list(filter_fields),
    }
    return type(f"{model.__name__}AdminViewSet", (AdminCRUDMixin, base), attrs)


def build_singleton(model):
    class SingletonView(RetrieveUpdateAPIView):
        permission_classes = [IsAdminUser]
        parser_classes = PARSERS
        pagination_class = None
        serializer_class = _serializer_for(model)

        def get_object(self):
            return model.load()

    SingletonView.__name__ = f"{model.__name__}AdminView"
    return SingletonView


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = AIMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AIConversation
        fields = ["id", "scope", "title", "session_id", "user", "created_at", "updated_at", "messages"]


VIEWSETS = [
    ("hero", HeroSection, ["heading", "subheading"], ["is_active"], False),
    ("studio", AboutSection, ["title", "description"], ["is_active"], False),
    ("services", Service, ["title", "category", "description"], ["is_active", "category"], False),
    ("portfolio", PortfolioProject, ["title", "category", "client_name"], ["is_active", "is_featured", "category"], False),
    ("process", ProcessStep, ["title", "description"], ["is_active"], False),
    ("gallery", BTSImage, ["title", "category"], ["is_active", "category"], False),
    ("upcoming", UpcomingProject, ["title", "description"], ["is_active", "status"], False),
    ("nav-items", NavItem, ["title", "url"], ["is_active", "parent"], False),
    ("footer-groups", FooterLinkGroup, ["title"], ["is_active"], False),
    ("footer-links", FooterLink, ["title", "url"], ["is_active", "group"], False),
    ("social-links", SocialLink, ["label", "url"], ["is_active", "platform"], False),
    ("leads", Lead, ["name", "email", "phone", "project_type", "message"], ["status", "lead_type"], False),
    ("media", MediaItem, ["title", "alt_text"], ["is_public"], False),
    ("email-logs", EmailLog, ["to_email", "subject"], ["status", "kind"], True),
]

SINGLETONS = [
    ("settings", SiteSettings),
    ("navbar", NavbarSettings),
    ("footer-content", FooterContent),
    ("ai-settings", AISettings),
]

router = SimpleRouter()
for _key, _model, _search, _filters, _ro in VIEWSETS:
    router.register(_key, build_viewset(_key, _model, _search, _filters, _ro), basename=f"admin-{_key}")
router.register(
    "ai-conversations",
    build_viewset("ai-conversations", AIConversation, ["title"], ["scope"], True, serializer=ConversationDetailSerializer),
    basename="admin-ai-conversations",
)


# ------------------------------------------------------------------ admin AI endpoints
class AdminAIStatusView(APIView):
    def get(self, request):
        return Response({**ai_status(), "tasks": {k: {"label": v["label"], "hint": v["hint"]} for k, v in TASKS.items()}})


class _AdminAIBase(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_admin"

    def check_ready(self):
        st = ai_status()
        cfg = AISettings.load()
        if not st["available"]:
            return Response({"error": st["message"], "code": "ai_not_configured" if not st["configured"] else "ai_disabled"}, status=503)
        if not cfg.admin_assistant_enabled:
            return Response({"error": "The admin AI assistant is disabled in AI Settings.", "code": "ai_disabled"}, status=503)
        return None

    def get_conversation(self, request, conversation_id, title):
        if conversation_id:
            conv = AIConversation.objects.filter(pk=conversation_id, scope="admin", user=request.user).first()
            if conv:
                return conv
        return AIConversation.objects.create(scope="admin", user=request.user, title=title[:80])

    def run(self, messages):
        try:
            return groq_chat(messages), None
        except AIConfigError as exc:
            return None, Response({"error": str(exc), "code": "ai_not_configured"}, status=503)
        except AIServiceError as exc:
            return None, Response({"error": str(exc), "code": "ai_error"}, status=502)


class AdminChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)


class AdminGenerateSerializer(serializers.Serializer):
    task = serializers.ChoiceField(choices=list(TASKS.keys()))
    input = serializers.CharField(max_length=4000, required=False, allow_blank=True, default="")
    conversation_id = serializers.IntegerField(required=False, allow_null=True)


class AdminChatView(_AdminAIBase):
    def post(self, request):
        ser = AdminChatSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        blocked = self.check_ready()
        if blocked:
            return blocked
        message = ser.validated_data["message"]
        conv = self.get_conversation(request, ser.validated_data.get("conversation_id"), message)
        history = [{"role": m.role, "content": m.content} for m in list(conv.messages.order_by("-id")[:10])[::-1]]
        reply, error = self.run([{"role": "system", "content": admin_chat_system_prompt()}] + history + [{"role": "user", "content": message}])
        if error:
            return error
        AIMessage.objects.create(conversation=conv, role="user", content=message)
        AIMessage.objects.create(conversation=conv, role="assistant", content=reply)
        conv.save(update_fields=["updated_at"])
        return Response({"reply": reply, "conversation_id": conv.id, "draft": True})


class AdminGenerateView(_AdminAIBase):
    def post(self, request):
        ser = AdminGenerateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        blocked = self.check_ready()
        if blocked:
            return blocked
        task, user_input = ser.validated_data["task"], ser.validated_data["input"]
        label = TASKS[task]["label"]
        if TASKS[task]["needs_input"] and not user_input.strip():
            return Response({"error": f"'{label}' needs some input: {TASKS[task]['hint']}"}, status=status.HTTP_400_BAD_REQUEST)
        conv = self.get_conversation(request, ser.validated_data.get("conversation_id"), label)
        history = [{"role": m.role, "content": m.content} for m in list(conv.messages.order_by("-id")[:6])[::-1]]
        reply, error = self.run(build_admin_task_messages(task, user_input, history))
        if error:
            return error
        AIMessage.objects.create(conversation=conv, role="user", content=f"[{label}] {user_input}".strip())
        AIMessage.objects.create(conversation=conv, role="assistant", content=reply)
        conv.save(update_fields=["updated_at"])
        return Response({
            "reply": reply, "conversation_id": conv.id, "task": task, "draft": True,
            "notice": "AI-generated draft. Review and edit before saving it to the website or sending it to anyone.",
        })
