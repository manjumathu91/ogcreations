import re
from urllib.parse import quote

from django.utils.text import slugify


def unique_slug(instance, source, max_length=200):
    base = slugify(source or "")[: max_length - 6] or "item"
    slug, n = base, 2
    model = instance.__class__
    while model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def build_whatsapp_url(number, message=""):
    """Standard wa.me click-to-chat link. `number` must include the country code."""
    digits = re.sub(r"\D", "", number or "")
    if not digits:
        return ""
    url = f"https://wa.me/{digits}"
    if message:
        url += f"?text={quote(message, safe='')}"
    return url
