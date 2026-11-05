from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def staff_required(view):
    """Logged-in AND is_staff (dashboard access)."""

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def superuser_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff and request.user.is_superuser):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper
