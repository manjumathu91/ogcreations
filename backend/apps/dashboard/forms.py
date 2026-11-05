import os

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.forms import modelform_factory

from apps.media_library.models import MediaItem

User = get_user_model()


def style_fields(form):
    """Apply the dashboard CSS classes/widgets to every field of a form."""
    for name, field in form.fields.items():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = "check"
        elif isinstance(widget, forms.CheckboxSelectMultiple):
            widget.attrs["class"] = "checks"
        elif isinstance(widget, forms.ClearableFileInput):
            widget.attrs["class"] = "file"
            if "image" in name or "logo" in name or "favicon" in name or "poster" in name or "thumbnail" in name or "icon_image" in name or name == "file":
                widget.attrs["accept"] = "image/*"
        else:
            widget.attrs["class"] = "input"
        if isinstance(widget, forms.Textarea):
            widget.attrs.setdefault("rows", 4)
        if isinstance(field, forms.DateField) and not isinstance(field, forms.DateTimeField):
            field.widget = forms.DateInput(attrs={"type": "date", "class": "input"}, format="%Y-%m-%d")
        if name.endswith("_color"):
            field.widget = forms.TextInput(attrs={"type": "color", "class": "input color"})


class ModuleForm(forms.ModelForm):
    """Base ModelForm for generic CRUD: styling + 'choose from Media Library' for image fields."""

    class Meta:
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model = self._meta.model
        self.library_fields = []
        self.image_required = {}
        if model is not MediaItem:
            for name in list(self.fields):
                try:
                    mf = model._meta.get_field(name)
                except Exception:
                    continue
                if isinstance(mf, models.ImageField):
                    self.library_fields.append(name)
                    self.image_required[name] = not mf.blank
                    self.fields[name].required = False
                    self.fields["library_" + name] = forms.ModelChoiceField(
                        queryset=MediaItem.objects.all(), required=False, empty_label="— none —",
                        label=f"{self.fields[name].label or name.replace('_', ' ').title()}: or pick from Media Library",
                    )
        style_fields(self)
        order = []
        for name in self.fields:
            if name.startswith("library_") and name[8:] in self.library_fields:
                continue
            order.append(name)
            if name in self.library_fields:
                order.append("library_" + name)
        self.order_fields(order)
        if "gallery_images" in self.fields:
            self.fields["gallery_images"].queryset = MediaItem.objects.all()
            self.fields["gallery_images"].help_text = "Tick images from the Media Library (upload new ones there first)."
        if "additional_images" in self.fields:
            self.fields["additional_images"].queryset = MediaItem.objects.all()
            self.fields["additional_images"].help_text = "Tick images from the Media Library (upload new ones there first)."
        for m2m in ("gallery_images", "additional_images"):
            if m2m in self.fields:
                self.fields[m2m].widget = forms.CheckboxSelectMultiple(attrs={"class": "checks"})
                self.fields[m2m].queryset = MediaItem.objects.all()

    def clean(self):
        cleaned = super().clean()
        for name in self.library_fields:
            if self.image_required.get(name) and not (cleaned.get(name) or cleaned.get("library_" + name)):
                self.add_error(name, "Upload an image or choose one from the Media Library.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        for name in self.library_fields:
            media = self.cleaned_data.get("library_" + name)
            if media and not self.files.get(name):
                media.file.open("rb")
                try:
                    data = media.file.read()
                finally:
                    media.file.close()
                getattr(instance, name).save(os.path.basename(media.file.name), ContentFile(data), save=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


def build_modelform(module):
    return modelform_factory(
        module.model, form=ModuleForm, fields=module.fields or "__all__", exclude=module.exclude or None
    )


# ----------------------------------------------------------------------------- users
class _UserBase(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_staff", "is_superuser", "is_active"]
        help_texts = {
            "is_staff": "Can sign in to this dashboard.",
            "is_superuser": "Full access, including User Management.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class UserCreateForm(_UserBase):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_staff"].initial = True
        self.fields["is_active"].initial = True
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", "The two passwords do not match.")
            else:
                try:
                    validate_password(p1, user=self.instance)
                except ValidationError as exc:
                    self.add_error("password1", exc)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if user.is_superuser:
            user.is_staff = True
        if commit:
            user.save()
        return user


class UserEditForm(_UserBase):
    new_password = forms.CharField(label="New password", required=False, widget=forms.PasswordInput, help_text="Leave blank to keep the current password.")

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("new_password")
        if pw:
            try:
                validate_password(pw, user=self.instance)
            except ValidationError as exc:
                self.add_error("new_password", exc)
        if self.instance.pk and self.instance.is_superuser and (not cleaned.get("is_superuser") or not cleaned.get("is_active")):
            others = User.objects.filter(is_superuser=True, is_active=True).exclude(pk=self.instance.pk).exists()
            if not others:
                raise ValidationError("You cannot demote or deactivate the last active superuser.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("new_password"):
            user.set_password(self.cleaned_data["new_password"])
        if user.is_superuser:
            user.is_staff = True
        if commit:
            user.save()
        return user


class EmailTestForm(forms.Form):
    to_email = forms.EmailField(label="Send test email to", widget=forms.EmailInput(attrs={"class": "input", "placeholder": "you@example.com"}))
