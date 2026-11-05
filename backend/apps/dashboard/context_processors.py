from django.conf import settings
from django.urls import reverse

from apps.leads.models import Lead
from apps.site_settings.models import SiteSettings

# (label, icon, target). target "m:<key>" -> generic module, otherwise a URL name.
SIDEBAR = [
    ("link", "Dashboard", "home", "dashboard:home"),
    ("group", "Website Content", "layout", [
        ("Hero Section", "m:hero"), ("About Studio", "m:about"), ("Services", "m:services"),
        ("Portfolio / Featured Works", "m:portfolio"), ("Production Process", "m:process"),
        ("BTS Gallery", "m:bts"), ("Upcoming Projects", "m:upcoming"),
    ]),
    ("group", "Navigation Management", "link", [
        ("Main Navbar", "m:navbar"), ("Main Navigation Links", "m:nav_main"), ("Sub Navigation Links", "m:nav_sub"),
    ]),
    ("group", "Footer Management", "layers", [
        ("Footer Content", "m:footer_content"), ("Footer Link Groups", "m:footer_groups"),
        ("Footer Links", "m:footer_links"), ("Social Media Links", "m:social"),
    ]),
    ("group", "Site Settings", "sliders", [
        ("Website Logo", "m:logo"), ("Brand Settings", "m:brand"), ("Contact Details", "m:contact_details"),
        ("Address and Location", "m:location"), ("SEO Settings", "m:seo"),
    ]),
    ("group", "Contact & Leads", "mail", [
        ("Contact Form Submissions", "m:contact_leads"), ("Project Enquiries", "m:project_leads"),
        ("Lead Status", "dashboard:lead_status"),
    ]),
    ("link", "Media Library", "image", "m:media"),
    ("link", "Email Management", "send", "dashboard:email"),
    ("link", "WhatsApp Management", "message", "m:whatsapp"),
    ("group", "AI Studio Assistant", "sparkles", [
        ("AI Chat", "dashboard:ai_chat"), ("AI Settings", "m:ai_settings"),
        ("AI Conversations", "m:ai_conversations"), ("AI Insights", "dashboard:ai_insights"),
    ]),
    ("link", "User Management", "users", "m:users"),
    ("link", "Profile", "user", "accounts:profile"),
    ("logout", "Logout", "log-out", None),
]


def _url(target):
    if target.startswith("m:"):
        return reverse("dashboard:module_list", args=[target[2:]])
    return reverse(target)


def dashboard(request):
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated and user.is_staff) or request.path.startswith("/api/"):
        return {}
    path = request.path
    sidebar = []
    for entry in SIDEBAR:
        kind, label, icon = entry[0], entry[1], entry[2]
        if kind == "link":
            if entry[3] == "m:users" and not user.is_superuser:
                continue
            url = _url(entry[3])
            active = path == url if entry[3] == "dashboard:home" else path.startswith(url)
            item = {"kind": "link", "label": label, "icon": icon, "url": url, "active": active}
            if label == "Dashboard":
                pass
            sidebar.append(item)
        elif kind == "group":
            children = []
            for child_label, target in entry[3]:
                url = _url(target)
                children.append({"label": child_label, "url": url, "active": path.startswith(url)})
            sidebar.append({"kind": "group", "label": label, "icon": icon, "children": children, "open": any(c["active"] for c in children)})
        else:
            sidebar.append({"kind": "logout", "label": label, "icon": icon})
    site = SiteSettings.load()
    return {
        "sidebar": sidebar,
        "brand": site,
        "new_leads_count": Lead.objects.filter(status="new").count(),
        "frontend_url": settings.FRONTEND_URL,
    }
