from .models import ActivityLog


def log_activity(user, action, module, obj=None):
    try:
        ActivityLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            action=action,
            module=str(module)[:100],
            object_repr=str(obj)[:255] if obj is not None else "",
        )
    except Exception:  # logging must never break a request
        pass
