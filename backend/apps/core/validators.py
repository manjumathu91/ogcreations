import os
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}

hex_color_validator = RegexValidator(r"^#[0-9a-fA-F]{6}$", "Enter a colour like #8D2236.")


def _safe_size(f):
    try:
        return f.size
    except Exception:  # file missing from storage etc.
        return None


def validate_image(f):
    """Allow only real raster images (no SVG/HTML) under the configured size limit."""
    ext = os.path.splitext(getattr(f, "name", "") or "")[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        raise ValidationError("Unsupported image type. Allowed: JPG, PNG, WEBP, GIF.")
    size = _safe_size(f)
    limit = settings.MAX_IMAGE_UPLOAD_MB * 1024 * 1024
    if size is not None and size > limit:
        raise ValidationError(f"Image is too large. Maximum size is {settings.MAX_IMAGE_UPLOAD_MB} MB.")
    # Verify the bytes really are an image (only for new, not-yet-saved uploads).
    if not getattr(f, "_committed", True):
        from PIL import Image

        try:
            f.file.seek(0)
            Image.open(f.file).verify()
        except Exception:
            raise ValidationError("The uploaded file is not a valid image.")
        finally:
            try:
                f.file.seek(0)
            except Exception:
                pass


def validate_video(f):
    ext = os.path.splitext(getattr(f, "name", "") or "")[1].lower()
    if ext not in VIDEO_EXTENSIONS:
        raise ValidationError("Unsupported video type. Allowed: MP4, WEBM.")
    size = _safe_size(f)
    limit = settings.MAX_VIDEO_UPLOAD_MB * 1024 * 1024
    if size is not None and size > limit:
        raise ValidationError(f"Video is too large. Maximum size is {settings.MAX_VIDEO_UPLOAD_MB} MB.")


def validate_link(value):
    """Internal path (/about), anchor (#about), mailto:/tel: or http(s) URL. Blocks javascript: etc."""
    v = (value or "").strip().lower()
    if not v:
        return
    if v.startswith(("http://", "https://", "/", "#", "mailto:", "tel:")):
        return
    raise ValidationError("Enter an internal path (/about), an anchor (#about), mailto:/tel: or a full http(s) URL.")


def validate_maps_embed(value):
    if value and not re.match(r"^https://(www\.)?(google\.com/maps|maps\.google\.com)/", value):
        raise ValidationError("Paste the src URL of the Google Maps embed (it starts with https://www.google.com/maps/embed).")
