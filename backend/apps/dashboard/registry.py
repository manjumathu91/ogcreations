"""Declarative registry of every dashboard module. Each entry powers a full CRUD UI
(list + search + filters + pagination + add/edit/delete/toggle/reorder) via generic views."""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from django.contrib.auth import get_user_model

from apps.ai_assistant.models import AIConversation, AISettings
from apps.gallery.models import BTSImage
from apps.leads.models import Lead
from apps.media_library.models import MediaItem
from apps.navigation.models import FooterContent, FooterLink, FooterLinkGroup, NavbarSettings, NavItem, SocialLink
from apps.pages.models import AboutSection, HeroSection, ProcessStep
from apps.portfolio.models import PortfolioProject
from apps.projects.models import UpcomingProject
from apps.services.models import Service
from apps.site_settings.models import SiteSettings

from .forms import UserCreateForm, UserEditForm

User = get_user_model()


@dataclass
class Module:
    key: str
    model: Any
    title: str
    list_fields: list = field(default_factory=list)
    icon: str = "grid"
    description: str = ""
    search_fields: list = field(default_factory=list)
    filters: list = field(default_factory=list)
    fields: Optional[list] = None
    exclude: list = field(default_factory=list)
    singleton: bool = False
    can_add: bool = True
    can_delete: bool = True
    read_only: bool = False
    list_template: str = "dashboard/list.html"
    form_template: str = "dashboard/form.html"
    detail_template: Optional[str] = None
    form_class: Any = None
    form_class_create: Any = None
    superuser_only: bool = False
    queryset: Optional[Callable] = None
    reorder_scope: Optional[str] = None
    form_init: Optional[Callable] = None
    extra_context: Optional[Callable] = None
    protect: Optional[Callable] = None
    delete_warning: str = ""
    add_label: str = ""

    @property
    def has_order(self):
        return any(f.name == "order" for f in self.model._meta.get_fields())

    @property
    def has_active(self):
        return any(f.name == "is_active" for f in self.model._meta.get_fields())

    @property
    def can_toggle(self):
        return self.has_active and not self.singleton and not self.read_only

    @property
    def can_reorder(self):
        return self.has_order and not self.singleton

    def base_queryset(self):
        return self.queryset() if self.queryset else self.model.objects.all()


# ---- hooks -------------------------------------------------------------------------
def _sub_nav_form(form):
    if "parent" in form.fields:
        form.fields["parent"].queryset = NavItem.objects.filter(parent__isnull=True)
        form.fields["parent"].required = True
        form.fields["parent"].empty_label = "— select parent item —"
        form.fields["parent"].label = "Parent navigation item"


def _protect_user(obj, request, action):
    if action in ("delete", "toggle") and obj.pk == request.user.pk:
        return "You cannot delete or deactivate your own account."
    if obj.is_superuser and obj.is_active and action in ("delete", "toggle"):
        if not User.objects.filter(is_superuser=True, is_active=True).exclude(pk=obj.pk).exists():
            return "You cannot remove or deactivate the last active superuser."
    return None


def _role(user):
    return "Superuser" if user.is_superuser else ("Staff" if user.is_staff else "No access")


def _whatsapp_ctx(request, obj):
    return {"whatsapp_preview": obj.whatsapp_url() if obj else ""}


def _msg_count(conv):
    return conv.messages.count()


MODULES = {m.key: m for m in [
    # ---------------- website content
    Module("hero", HeroSection, "Hero Section", ["heading", "subheading", "hero_image", "order", "is_active"], icon="star",
           description="The main banner at the top of the homepage.", search_fields=["heading", "subheading"], filters=["is_active"], add_label="Add hero"),
    Module("about", AboutSection, "About Studio", ["title", "image", "experience_years", "order", "is_active"], icon="info",
           description="Studio story, images and highlights.", search_fields=["title", "description"], filters=["is_active"], add_label="Add about section"),
    Module("services", Service, "Services", ["title", "category", "image", "order", "is_active"], icon="briefcase",
           description="What the studio offers.", search_fields=["title", "category", "description"], filters=["is_active", "category"], add_label="Add service"),
    Module("portfolio", PortfolioProject, "Portfolio / Featured Works", ["title", "category", "thumbnail", "is_featured", "project_date", "order", "is_active"], icon="film",
           description="Projects shown in the portfolio section.", search_fields=["title", "category", "client_name", "description"], filters=["is_active", "is_featured", "category"], add_label="Add project"),
    Module("process", ProcessStep, "Production Process", ["step_number", "title", "icon", "order", "is_active"], icon="tool",
           description="The steps of your production workflow.", search_fields=["title", "description"], filters=["is_active"], add_label="Add step"),
    Module("bts", BTSImage, "BTS Gallery", ["image", "title", "category", "order", "is_active"], icon="image",
           description="Behind-the-scenes photos.", search_fields=["title", "description", "category"], filters=["is_active", "category"], add_label="Add BTS image"),
    Module("upcoming", UpcomingProject, "Upcoming Projects", ["title", "poster", "release_date", "status", "order", "is_active"], icon="calendar",
           description="Projects that are announced or in production.", search_fields=["title", "description"], filters=["is_active", "status"], add_label="Add upcoming project"),
    # ---------------- navigation
    Module("navbar", NavbarSettings, "Main Navbar", icon="menu", singleton=True,
           description="Navbar brand text and optional call-to-action button. Manage the links under 'Main Navigation Links'."),
    Module("nav_main", NavItem, "Main Navigation Links", ["title", "url", "link_type", "open_in_new_tab", "order", "is_active"], icon="link",
           description="Top-level navbar links (internal, external or #anchor).", search_fields=["title", "url"], filters=["is_active"],
           queryset=lambda: NavItem.objects.filter(parent__isnull=True), exclude=["parent"], add_label="Add link",
           delete_warning="Deleting a main link also deletes all of its sub-links."),
    Module("nav_sub", NavItem, "Sub Navigation Links", ["title", "parent", "url", "link_type", "order", "is_active"], icon="link",
           description="Dropdown links that belong to a main navigation item.", search_fields=["title", "url", "parent__title"], filters=["is_active", "parent"],
           queryset=lambda: NavItem.objects.filter(parent__isnull=False).select_related("parent"), reorder_scope="parent", form_init=_sub_nav_form, add_label="Add sub-link"),
    # ---------------- footer
    Module("footer_content", FooterContent, "Footer Content", icon="layers", singleton=True,
           description="Footer description, logo, copyright and contact display. Social links, link groups and links have their own pages."),
    Module("footer_groups", FooterLinkGroup, "Footer Link Groups", ["title", "order", "is_active"], icon="layers",
           description="Columns of footer links (e.g. Quick Links).", search_fields=["title"], filters=["is_active"], add_label="Add group",
           delete_warning="Deleting a group also deletes the links inside it."),
    Module("footer_links", FooterLink, "Footer Links", ["title", "group", "url", "order", "is_active"], icon="link",
           description="Links inside each footer group.", search_fields=["title", "url", "group__title"], filters=["is_active", "group"],
           queryset=lambda: FooterLink.objects.select_related("group"), reorder_scope="group", add_label="Add footer link"),
    Module("social", SocialLink, "Social Media Links", ["platform", "label", "url", "order", "is_active"], icon="globe",
           description="Social profiles shown in the footer.", search_fields=["label", "url"], filters=["is_active", "platform"], add_label="Add social link"),
    # ---------------- site settings (all on one SiteSettings row)
    Module("logo", SiteSettings, "Website Logo", icon="image", singleton=True, fields=["logo", "favicon"],
           description="Logo and favicon used across the website."),
    Module("brand", SiteSettings, "Brand Settings", icon="star", singleton=True,
           fields=["site_name", "tagline", "background_color", "primary_color", "accent_color", "secondary_color", "text_color"],
           description="Website name and brand colours."),
    Module("contact_details", SiteSettings, "Contact Details", icon="phone", singleton=True,
           fields=["email", "phone", "whatsapp_number", "business_hours"],
           description="Email, phone, WhatsApp number and business hours (loaded by the website from the API)."),
    Module("location", SiteSettings, "Address and Location", icon="map-pin", singleton=True,
           fields=["address", "city", "state", "country", "postal_code", "latitude", "longitude", "google_maps_url", "google_maps_embed_url"],
           description="Enter the real studio address and map links. Nothing is pre-filled or invented."),
    Module("seo", SiteSettings, "SEO Settings", icon="search", singleton=True, fields=["seo_title", "seo_description", "seo_keywords"],
           description="Search-engine title, description and keywords."),
    # ---------------- leads
    Module("contact_leads", Lead, "Contact Form Submissions", ["name", "email", "phone", "project_type", "status", "created_at"], icon="mail",
           description="Messages sent through the website contact form.", search_fields=["name", "email", "phone", "project_type", "message"], filters=["status"],
           queryset=lambda: Lead.objects.filter(lead_type="contact"), fields=["status", "internal_notes"], can_add=False,
           detail_template="dashboard/lead_detail.html"),
    Module("project_leads", Lead, "Project Enquiries", ["name", "email", "project_type", "project_reference", "status", "created_at"], icon="briefcase",
           description="Enquiries about starting or discussing a project.", search_fields=["name", "email", "phone", "project_type", "project_reference", "message"], filters=["status"],
           queryset=lambda: Lead.objects.filter(lead_type="project"), fields=["status", "internal_notes"], can_add=False,
           detail_template="dashboard/lead_detail.html"),
    # ---------------- media
    Module("media", MediaItem, "Media Library", ["file", "title", "alt_text", "file_size", "is_public", "created_at"], icon="image",
           description="Upload and manage images used across the website.", search_fields=["title", "alt_text"], filters=["is_public"],
           fields=["title", "alt_text", "file", "is_public"], list_template="dashboard/media_list.html", add_label="Upload image"),
    # ---------------- WhatsApp
    Module("whatsapp", SiteSettings, "WhatsApp Management", icon="message", singleton=True,
           fields=["whatsapp_enabled", "whatsapp_number", "whatsapp_default_message"],
           description="Click-to-chat (wa.me) number and default message used by the floating button, contact section, footer and project enquiries.",
           extra_context=_whatsapp_ctx, form_template="dashboard/whatsapp_form.html"),
    # ---------------- AI
    Module("ai_settings", AISettings, "AI Settings", icon="sparkles", singleton=True,
           description="Enable/disable the AI assistants and tune the public chat. The API key and model are set in the server environment.",
           form_template="dashboard/ai_settings_form.html"),
    Module("ai_conversations", AIConversation, "AI Conversations", ["title", "scope", ("Messages", _msg_count), "updated_at"], icon="message",
           description="Previous public and admin AI conversations.", search_fields=["title", "messages__content"], filters=["scope"],
           can_add=False, read_only=True, detail_template="dashboard/conversation_detail.html"),
    # ---------------- users
    Module("users", User, "User Management", ["username", "email", ("Role", _role), "is_active", "last_login"], icon="users",
           description="Create and manage dashboard users.", search_fields=["username", "email", "first_name", "last_name"], filters=["is_active", "is_staff"],
           form_class=UserEditForm, form_class_create=UserCreateForm, superuser_only=True, protect=_protect_user, add_label="Add user"),
]}
