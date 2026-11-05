from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.cache import cache
from django.core.exceptions import ValidationError

User = get_user_model()
MAX_ATTEMPTS = 10
LOCK_SECONDS = 15 * 60


class StaffAuthenticationForm(AuthenticationForm):
    """Only staff users may log in; repeated failures temporarily lock the username."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "input", "autofocus": True, "autocomplete": "username"})
        self.fields["password"].widget.attrs.update({"class": "input", "autocomplete": "current-password"})

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError("This account does not have dashboard access.", code="no_access")

    def clean(self):
        username = (self.cleaned_data.get("username") or "").strip().lower()
        key = f"login_fail:{username}"
        if username and cache.get(key, 0) >= MAX_ATTEMPTS:
            raise ValidationError("Too many failed attempts. Please try again in 15 minutes.", code="locked")
        try:
            cleaned = super().clean()
        except ValidationError:
            if username:
                cache.set(key, cache.get(key, 0) + 1, LOCK_SECONDS)
            raise
        if username:
            cache.delete(key)
        return cleaned


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"
