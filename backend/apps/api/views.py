"""Public (read-only, active-only) API + lead submission + public AI chat."""
from django.core.validators import RegexValidator
from django.db.models import Prefetch
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.ai_assistant.models import AIConversation, AIMessage, AISettings
from apps.ai_assistant.services import AIConfigError, AIServiceError, ai_status, groq_chat, public_system_prompt
from apps.communications.services import notify_new_lead
from apps.gallery.models import BTSImage
from apps.media_library.models import MediaItem
from apps.navigation.models import FooterContent, FooterLinkGroup, NavbarSettings, NavItem, SocialLink
from apps.pages.models import AboutSection, HeroSection, ProcessStep
from apps.portfolio.models import PortfolioProject
from apps.projects.models import UpcomingProject
from apps.services.models import Service
from apps.site_settings.models import SiteSettings

from .serializers import (
    AboutSerializer, BTSSerializer, HeroSerializer, LeadCreateSerializer, MediaPublicSerializer, NavItemSerializer,
    PortfolioPublicSerializer, ProcessSerializer, ServicePublicSerializer, SiteSettingsPublicSerializer,
    UpcomingSerializer, abs_url,
)


class PublicMixin:
    """Public endpoints: no session auth (so no CSRF needed), no pagination."""

    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = None


class PublicAPIView(PublicMixin, APIView):
    pass


class PublicListView(PublicAPIView):
    serializer_class = None
    queryset_fn = None

    def get(self, request):
        data = self.serializer_class(self.queryset_fn(), many=True, context={"request": request}).data
        return Response(data)


# ------------------------------------------------------------------ index
class APIRootView(PublicAPIView):
    def get(self, request):
        base = request.build_absolute_uri("/api/")
        return Response({
            "name": "OG Creations API",
            "public": {
                "settings": base + "settings/", "navigation": base + "navigation/", "footer": base + "footer/",
                "hero": base + "hero/", "studio": base + "studio/", "services": base + "services/",
                "portfolio": base + "portfolio/", "process": base + "process/", "gallery": base + "gallery/",
                "upcoming": base + "upcoming/", "location": base + "location/", "media": base + "media/",
                "leads (POST)": base + "leads/", "ai_status": base + "ai/status/", "ai_chat (POST)": base + "ai/chat/",
            },
            "admin": base + "admin/ (staff session required)",
        })


# ------------------------------------------------------------------ settings / location
class SettingsView(PublicAPIView):
    def get(self, request):
        return Response(SiteSettingsPublicSerializer(SiteSettings.load(), context={"request": request}).data)


class LocationView(PublicAPIView):
    def get(self, request):
        s = SiteSettings.load()
        return Response({
            "address": s.address, "city": s.city, "state": s.state, "country": s.country, "postal_code": s.postal_code,
            "full_address": s.full_address, "latitude": s.latitude, "longitude": s.longitude,
            "maps_url": s.maps_url, "directions_url": s.directions_url, "embed_url": s.google_maps_embed_url,
            "business_hours": s.business_hours, "has_location": bool(s.full_address or s.google_maps_url or s.latitude),
        })


# ------------------------------------------------------------------ navigation / footer
class NavigationView(PublicAPIView):
    def get(self, request):
        nav = NavbarSettings.load()
        site = SiteSettings.load()
        items = NavItem.objects.filter(is_active=True, parent__isnull=True).prefetch_related(
            Prefetch("children", queryset=NavItem.objects.filter(is_active=True), to_attr="active_children")
        )
        return Response({
            "navbar": {
                "brand_text": nav.brand_text, "show_logo": nav.show_logo, "logo": abs_url(request, site.logo),
                "cta": {"enabled": nav.cta_enabled and bool(nav.cta_text), "text": nav.cta_text, "url": nav.cta_url, "open_in_new_tab": nav.cta_new_tab},
            },
            "items": NavItemSerializer(items, many=True, context={"request": request}).data,
        })


class FooterView(PublicAPIView):
    def get(self, request):
        f = FooterContent.load()
        s = SiteSettings.load()
        groups = FooterLinkGroup.objects.filter(is_active=True).prefetch_related(
            Prefetch("links", to_attr="all_links")
        )
        group_data = []
        for g in groups:
            links = [
                {"id": l.id, "title": l.title, "url": l.url, "open_in_new_tab": l.open_in_new_tab}
                for l in g.all_links if l.is_active
            ]
            group_data.append({"id": g.id, "title": g.title, "links": links})
        contact = None
        if f.show_contact_details:
            contact = {
                "heading": f.contact_heading,
                "email": f.contact_email or s.email,
                "phone": f.contact_phone or s.phone,
                "address": f.contact_address or s.full_address,
                "maps_url": s.maps_url, "directions_url": s.directions_url,
            }
        whatsapp = None
        if f.show_whatsapp and s.whatsapp_enabled and s.whatsapp_number:
            whatsapp = {"label": f.whatsapp_label, "url": s.whatsapp_url()}
        social = []
        if f.show_social:
            social = [
                {"id": x.id, "platform": x.platform, "label": x.label or x.get_platform_display(), "url": x.url}
                for x in SocialLink.objects.filter(is_active=True)
            ]
        return Response({
            "description": f.description, "logo": abs_url(request, f.logo) or abs_url(request, s.logo),
            "copyright": f.copyright_text, "contact": contact, "whatsapp": whatsapp,
            "groups": group_data, "social": social, "site_name": s.site_name,
        })


# ------------------------------------------------------------------ content
class HeroView(PublicAPIView):
    def get(self, request):
        hero = HeroSection.objects.filter(is_active=True).first()
        return Response(HeroSerializer(hero, context={"request": request}).data if hero else {})


class StudioView(PublicListView):
    serializer_class = AboutSerializer
    queryset_fn = staticmethod(lambda: AboutSection.objects.filter(is_active=True).prefetch_related("additional_images"))


class ProcessView(PublicListView):
    serializer_class = ProcessSerializer
    queryset_fn = staticmethod(lambda: ProcessStep.objects.filter(is_active=True))


class GalleryView(PublicAPIView):
    def get(self, request):
        qs = BTSImage.objects.filter(is_active=True)
        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category__iexact=category)
        return Response(BTSSerializer(qs, many=True, context={"request": request}).data)


class UpcomingView(PublicListView):
    serializer_class = UpcomingSerializer
    queryset_fn = staticmethod(lambda: UpcomingProject.objects.filter(is_active=True))


class MediaView(PublicListView):
    serializer_class = MediaPublicSerializer
    queryset_fn = staticmethod(lambda: MediaItem.objects.filter(is_public=True)[:200])


class ServiceViewSet(PublicMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ServicePublicSerializer
    lookup_field = "slug"

    def get_queryset(self):
        qs = Service.objects.filter(is_active=True)
        category = self.request.query_params.get("category")
        return qs.filter(category__iexact=category) if category else qs


class PortfolioViewSet(PublicMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = PortfolioPublicSerializer
    lookup_field = "slug"

    def get_queryset(self):
        qs = PortfolioProject.objects.filter(is_active=True).prefetch_related("gallery_images")
        params = self.request.query_params
        if params.get("category"):
            qs = qs.filter(category__iexact=params["category"])
        if params.get("featured", "").lower() in ("1", "true", "yes"):
            qs = qs.filter(is_featured=True)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["site"] = SiteSettings.load()
        return ctx


# ------------------------------------------------------------------ leads
class LeadCreateView(PublicAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "leads"

    def post(self, request):
        # Honeypot: bots fill the hidden "website" field. Pretend success, save nothing.
        if str(request.data.get("website", "")).strip():
            return Response({"success": True, "message": "Thank you! We'll be in touch soon."}, status=status.HTTP_201_CREATED)
        serializer = LeadCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        lead = serializer.save()  # 1) saved to the database first
        try:
            notify_new_lead(lead)  # 2) emails afterwards; failures are logged, never raised
        except Exception:
            pass
        site = SiteSettings.load()
        return Response(
            {
                "success": True,
                "message": "Thank you! Your message has been received and we'll be in touch soon.",
                "reference": lead.id,
                "whatsapp_url": site.whatsapp_url(f"Hi! I just sent an enquiry on your website (ref #{lead.id})."),
            },
            status=status.HTTP_201_CREATED,
        )


# ------------------------------------------------------------------ public AI
class PublicChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, trim_whitespace=True)
    session_id = serializers.CharField(
        max_length=64, validators=[RegexValidator(r"^[A-Za-z0-9_-]{8,64}$", "Invalid session id.")]
    )


class PublicAIStatusView(PublicAPIView):
    def get(self, request):
        st = ai_status()
        cfg = AISettings.load()
        available = st["available"] and cfg.public_chat_enabled
        return Response({"available": available, "assistant_name": cfg.assistant_name, "welcome_message": cfg.welcome_message})


class PublicChatView(PublicAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_public"

    def post(self, request):
        serializer = PublicChatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "Invalid request.", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        message = serializer.validated_data["message"]
        session_id = serializer.validated_data["session_id"]
        st = ai_status()
        cfg = AISettings.load()
        unavailable = "The assistant is not available right now. Please use the contact form or WhatsApp."
        if not cfg.public_chat_enabled or not st["enabled"]:
            return Response({"error": unavailable, "code": "ai_disabled"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not st["configured"]:
            return Response({"error": unavailable, "code": "ai_not_configured"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        conv = AIConversation.objects.filter(scope="public", session_id=session_id).first()
        if conv is None:
            conv = AIConversation.objects.create(scope="public", session_id=session_id, title=message[:80])
        recent = list(conv.messages.order_by("-id")[:8])[::-1]
        history = [{"role": m.role, "content": m.content} for m in recent]
        messages = [{"role": "system", "content": public_system_prompt()}] + history + [{"role": "user", "content": message}]
        try:
            reply = groq_chat(messages)
        except AIConfigError:
            return Response({"error": unavailable, "code": "ai_not_configured"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIServiceError:
            return Response(
                {"error": "The assistant couldn't answer right now. Please try again in a moment.", "code": "ai_error"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        AIMessage.objects.create(conversation=conv, role="user", content=message)
        AIMessage.objects.create(conversation=conv, role="assistant", content=reply)
        conv.save(update_fields=["updated_at"])
        return Response({"reply": reply, "session_id": session_id})
