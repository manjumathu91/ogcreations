import re

from rest_framework import serializers

from apps.gallery.models import BTSImage
from apps.leads.models import Lead
from apps.media_library.models import MediaItem
from apps.navigation.models import NavItem
from apps.pages.models import AboutSection, HeroSection, ProcessStep
from apps.portfolio.models import PortfolioProject
from apps.projects.models import UpcomingProject
from apps.services.models import Service
from apps.site_settings.models import SiteSettings


def abs_url(request, file_field):
    """Absolute URL for a FileField/ImageField value, or None."""
    if not file_field:
        return None
    try:
        url = file_field.url
    except Exception:
        return None
    return request.build_absolute_uri(url) if request else url


# ------------------------------------------------------------------ settings / location
class SiteSettingsPublicSerializer(serializers.ModelSerializer):
    whatsapp_url = serializers.SerializerMethodField()
    maps_url = serializers.SerializerMethodField()
    directions_url = serializers.SerializerMethodField()
    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = SiteSettings
        fields = [
            "site_name", "tagline", "logo", "favicon",
            "background_color", "primary_color", "accent_color", "secondary_color", "text_color",
            "email", "phone", "whatsapp_number", "whatsapp_enabled", "whatsapp_default_message", "whatsapp_url",
            "business_hours", "address", "city", "state", "country", "postal_code", "full_address",
            "latitude", "longitude", "google_maps_url", "google_maps_embed_url", "maps_url", "directions_url",
            "seo_title", "seo_description", "seo_keywords",
        ]

    def get_whatsapp_url(self, obj):
        return obj.whatsapp_url()

    def get_maps_url(self, obj):
        return obj.maps_url

    def get_directions_url(self, obj):
        return obj.directions_url


# ------------------------------------------------------------------ navigation
class NavChildSerializer(serializers.ModelSerializer):
    link_type = serializers.CharField(read_only=True)

    class Meta:
        model = NavItem
        fields = ["id", "title", "url", "link_type", "open_in_new_tab", "order"]


class NavItemSerializer(NavChildSerializer):
    children = serializers.SerializerMethodField()

    class Meta(NavChildSerializer.Meta):
        fields = NavChildSerializer.Meta.fields + ["children"]

    def get_children(self, obj):
        kids = getattr(obj, "active_children", None)
        if kids is None:
            kids = obj.children.filter(is_active=True)
        return NavChildSerializer(kids, many=True, context=self.context).data


# ------------------------------------------------------------------ website content
class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = [
            "id", "heading", "subheading", "description", "hero_image", "background_video",
            "primary_button_text", "primary_button_url", "secondary_button_text", "secondary_button_url",
        ]


class AboutSerializer(serializers.ModelSerializer):
    additional_images = serializers.SerializerMethodField()
    highlights = serializers.ListField(source="highlight_list", read_only=True)

    class Meta:
        model = AboutSection
        fields = ["id", "title", "description", "image", "additional_images", "experience_years", "highlights"]

    def get_additional_images(self, obj):
        request = self.context.get("request")
        return [
            {"id": m.id, "url": abs_url(request, m.file), "alt_text": m.alt_text, "title": m.title}
            for m in obj.additional_images.all()
        ]



class ServicePublicSerializer(serializers.ModelSerializer):
    additional_images = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id", "title", "slug", "category", "short_description",
            "description", "icon", "image", "additional_images"
        ]

    def get_additional_images(self, obj):
        request = self.context.get("request")
        return [
            {
                "id": m.id,
                "url": abs_url(request, m.file),
                "alt_text": m.alt_text or obj.title,
                "title": m.title,
            }
            for m in obj.additional_images.all()
        ]


class PortfolioPublicSerializer(serializers.ModelSerializer):
    gallery_images = serializers.SerializerMethodField()
    whatsapp_enquiry_url = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioProject
        fields = [
            "id", "title", "slug", "category", "short_description", "description", "thumbnail", "gallery_images",
            "video_url", "client_name", "project_date", "is_featured", "whatsapp_enquiry_url",
        ]

    def get_gallery_images(self, obj):
        request = self.context.get("request")
        return [
            {"id": m.id, "url": abs_url(request, m.file), "alt_text": m.alt_text or obj.title}
            for m in obj.gallery_images.all()
        ]

    def get_whatsapp_enquiry_url(self, obj):
        site = self.context.get("site") or SiteSettings.load()
        return site.whatsapp_url(f"Hi! I'd like to enquire about the project: {obj.title}")


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessStep
        fields = ["id", "step_number", "title", "description", "icon", "icon_image"]


class BTSSerializer(serializers.ModelSerializer):
    additional_images = serializers.SerializerMethodField()

    class Meta:
        model = BTSImage
        fields = [
            "id", "image", "title", "description",
            "category", "additional_images"
        ]

    def get_additional_images(self, obj):
        request = self.context.get("request")
        return [
            {
                "id": m.id,
                "url": abs_url(request, m.file),
                "alt_text": m.alt_text or obj.title,
                "title": m.title,
            }
            for m in obj.additional_images.all()
        ]



class UpcomingSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = UpcomingProject
        fields = ["id", "title", "description", "poster", "release_date", "status", "status_display"]


class MediaPublicSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MediaItem
        fields = ["id", "title", "alt_text", "url", "width", "height"]

    def get_url(self, obj):
        return abs_url(self.context.get("request"), obj.file)


# ------------------------------------------------------------------ leads
PHONE_RE = re.compile(r"^[0-9+()\-\s.]{0,30}$")


class LeadCreateSerializer(serializers.ModelSerializer):
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)  # honeypot

    class Meta:
        model = Lead
        fields = [
            "lead_type", "name", "email", "phone", "whatsapp_number", "project_type",
            "project_reference", "message", "preferred_contact", "website",
        ]
        extra_kwargs = {"lead_type": {"required": False}}

    def _clean_phone(self, value):
        value = (value or "").strip()
        if not PHONE_RE.match(value):
            raise serializers.ValidationError("Enter a valid phone number (digits, +, spaces, dashes).")
        return value

    def validate_phone(self, value):
        return self._clean_phone(value)

    def validate_whatsapp_number(self, value):
        return self._clean_phone(value)

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Please enter your name.")
        return value

    def validate_message(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("Please enter a message (at least 5 characters).")
        if len(value) > 5000:
            raise serializers.ValidationError("Message is too long (max 5000 characters).")
        return value

    def create(self, validated_data):
        validated_data.pop("website", None)
        return super().create(validated_data)
