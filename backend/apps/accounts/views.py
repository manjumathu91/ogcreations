from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from .decorators import staff_required
from .forms import ProfileForm, StaffAuthenticationForm, StyledPasswordChangeForm

class StaffLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = StaffAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.site_settings.models import SiteSettings
        context["brand"] = SiteSettings.load()
        return context

class StaffLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")  # POST only (Django 5)


@method_decorator(staff_required, name="dispatch")
class StaffPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")
    success_message = "Your password was changed successfully."


@staff_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
        messages.error(request, "Please correct the errors below.")
    return render(request, "accounts/profile.html", {"form": form, "page_title": "Profile"})


# --- secure, branded error pages (no stack traces / internals) ------------------
def _error(request, template, status):
    try:
        return render(request, template, status=status)
    except Exception:
        return HttpResponse(f"Error {status}", status=status)


def error_403(request, exception=None):
    return _error(request, "403.html", 403)


def error_404(request, exception=None):
    return _error(request, "404.html", 404)


def error_500(request):
    try:
        return HttpResponse(render_to_string("500.html"), status=500)
    except Exception:
        return HttpResponse("Server error", status=500)
