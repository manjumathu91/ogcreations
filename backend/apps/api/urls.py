from django.urls import include, path

from . import admin_api, views


from rest_framework.routers import SimpleRouter  # noqa: E402

public = SimpleRouter()
public.register("services", views.ServiceViewSet, basename="services")
public.register("portfolio", views.PortfolioViewSet, basename="portfolio")

admin_patterns = [
    path("ai/status/", admin_api.AdminAIStatusView.as_view(), name="admin-ai-status"),
    path("ai/chat/", admin_api.AdminChatView.as_view(), name="admin-ai-chat"),
    path("ai/generate/", admin_api.AdminGenerateView.as_view(), name="admin-ai-generate"),
]
for _key, _model in admin_api.SINGLETONS:
    admin_patterns.append(path(f"{_key}/", admin_api.build_singleton(_model).as_view(), name=f"admin-{_key}"))
admin_patterns.append(path("", include(admin_api.router.urls)))

urlpatterns = [
    path("", views.APIRootView.as_view(), name="api-root"),
    path("settings/", views.SettingsView.as_view(), name="api-settings"),
    path("navigation/", views.NavigationView.as_view(), name="api-navigation"),
    path("footer/", views.FooterView.as_view(), name="api-footer"),
    path("hero/", views.HeroView.as_view(), name="api-hero"),
    path("studio/", views.StudioView.as_view(), name="api-studio"),
    path("process/", views.ProcessView.as_view(), name="api-process"),
    path("gallery/", views.GalleryView.as_view(), name="api-gallery"),
    path("upcoming/", views.UpcomingView.as_view(), name="api-upcoming"),
    path("location/", views.LocationView.as_view(), name="api-location"),
    path("media/", views.MediaView.as_view(), name="api-media"),
    path("leads/", views.LeadCreateView.as_view(), name="api-leads"),
    path("ai/status/", views.PublicAIStatusView.as_view(), name="api-ai-status"),
    path("ai/chat/", views.PublicChatView.as_view(), name="api-ai-chat"),
    path("admin/", include(admin_patterns)),
    path("", include(public.urls)),
]
