from django.urls import path

from . import views, views_extra

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("m/<slug:key>/", views.module_list, name="module_list"),
    path("m/<slug:key>/add/", views.module_create, name="module_create"),
    path("m/<slug:key>/<int:pk>/edit/", views.module_edit, name="module_edit"),
    path("m/<slug:key>/<int:pk>/delete/", views.module_delete, name="module_delete"),
    path("m/<slug:key>/<int:pk>/toggle/", views.module_toggle, name="module_toggle"),
    path("m/<slug:key>/<int:pk>/move/<str:direction>/", views.module_move, name="module_move"),
    path("leads/status/", views_extra.lead_status, name="lead_status"),
    path("leads/<int:pk>/status/", views_extra.lead_quick_status, name="lead_quick_status"),
    path("media/upload/", views_extra.media_upload, name="media_upload"),
    path("email/", views_extra.email_management, name="email"),
    path("email/test/", views_extra.email_test, name="email_test"),
    path("ai/chat/", views_extra.ai_chat, name="ai_chat"),
    path("ai/insights/", views_extra.ai_insights, name="ai_insights"),
]
