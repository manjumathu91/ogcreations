from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect,render
from django.urls import include, path, re_path
from django.views.static import serve


def robots(request):
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")
def public_home(request):
    return render(request, "index.html")


urlpatterns = [
    path("", public_home, name="root"),
    path("robots.txt", robots),
    path("accounts/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("api/", include("apps.api.urls")),
]

if settings.DEBUG or settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]

handler403 = "apps.accounts.views.error_403"
handler404 = "apps.accounts.views.error_404"
handler500 = "apps.accounts.views.error_500"
