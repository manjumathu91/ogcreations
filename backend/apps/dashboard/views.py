from django.contrib import messages
from django.core.exceptions import FieldDoesNotExist, PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.accounts.decorators import staff_required
from apps.ai_assistant.services import ai_status
from apps.communications.services import email_is_configured
from apps.gallery.models import BTSImage
from apps.leads.models import Lead
from apps.media_library.models import MediaItem
from apps.portfolio.models import PortfolioProject
from apps.projects.models import UpcomingProject
from apps.services.models import Service

from .forms import build_modelform
from .models import ActivityLog
from .registry import MODULES
from .utils import log_activity

PAGE_SIZE = 12


# ----------------------------------------------------------------------------- helpers
def get_module(request, key):
    module = MODULES.get(key)
    if module is None:
        raise Http404("Unknown module")
    if module.superuser_only and not request.user.is_superuser:
        raise PermissionDenied
    return module


def _label(module, spec):
    if isinstance(spec, tuple):
        return spec[0]
    try:
        return str(module.model._meta.get_field(spec).verbose_name).replace("_", " ").title()
    except FieldDoesNotExist:
        return spec.replace("_", " ").title()


def _cell(obj, spec):
    if isinstance(spec, tuple):
        return {"kind": "text", "value": spec[1](obj)}
    try:
        f = obj._meta.get_field(spec)
    except FieldDoesNotExist:
        value = getattr(obj, spec, "")
        return {"kind": "text", "value": value() if callable(value) else value}
    value = getattr(obj, spec)
    if isinstance(f, models.ImageField):
        try:
            return {"kind": "image", "value": value.url if value else ""}
        except ValueError:
            return {"kind": "image", "value": ""}
    if isinstance(f, models.BooleanField):
        return {"kind": "bool", "value": bool(value)}
    if f.choices:
        return {"kind": "badge", "value": getattr(obj, f"get_{spec}_display")(), "raw": value}
    if isinstance(f, models.DateTimeField):
        return {"kind": "datetime", "value": value}
    if isinstance(f, models.DateField):
        return {"kind": "date", "value": value}
    if spec == "file_size":
        return {"kind": "text", "value": filesizeformat(value or 0)}
    text = "" if value is None else str(value)
    return {"kind": "text", "value": text if len(text) <= 70 else text[:69] + "…"}


def _build_filters(module, request, base_qs):
    out = []
    for name in module.filters:
        f = module.model._meta.get_field(name)
        if isinstance(f, models.BooleanField):
            if name == "is_active":
                choices, label = [("1", "Active"), ("0", "Inactive")], "Status"
            else:
                choices, label = [("1", "Yes"), ("0", "No")], str(f.verbose_name).title()
        elif f.choices:
            choices, label = list(f.choices), str(f.verbose_name).title()
        elif f.is_relation:
            choices, label = [(str(o.pk), str(o)) for o in f.related_model.objects.all()[:200]], str(f.verbose_name).title()
        else:
            values = base_qs.order_by().values_list(name, flat=True).distinct()[:100]
            choices, label = [(v, v) for v in values if v], str(f.verbose_name).title()
        out.append({"param": "f_" + name, "label": label, "choices": choices, "current": request.GET.get("f_" + name, "")})
    return out


def _apply_filters(module, request, qs):
    for name in module.filters:
        value = request.GET.get("f_" + name, "")
        if value == "":
            continue
        try:
            f = module.model._meta.get_field(name)
            if isinstance(f, models.BooleanField):
                qs = qs.filter(**{name: value == "1"})
            else:
                qs = qs.filter(**{name: value})
        except (ValueError, TypeError, ValidationError):
            return qs.none()
    return qs


def _safe_next(request, fallback):
    nxt = request.POST.get("next") or request.GET.get("next") or ""
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return nxt
    return fallback


def _list_url(module):
    return reverse("dashboard:module_list", args=[module.key])


# ----------------------------------------------------------------------------- dashboard home
@staff_required
def home(request):
    counts = dict(Lead.objects.values_list("status").annotate(c=Count("id")).order_by())
    total = Lead.objects.count()
    status_rows = []
    for value, label in Lead.STATUS_CHOICES:
        n = counts.get(value, 0)
        status_rows.append({"value": value, "label": label, "count": n, "pct": round(n * 100 / total) if total else 0})
    cards = [
        {"label": "Total enquiries", "value": total, "icon": "mail", "url": reverse("dashboard:lead_status")},
        {"label": "New enquiries", "value": counts.get("new", 0), "icon": "inbox", "url": reverse("dashboard:lead_status") + "?status=new", "accent": True},
        {"label": "Contacted leads", "value": counts.get("contacted", 0), "icon": "phone", "url": reverse("dashboard:lead_status") + "?status=contacted"},
        {"label": "Active services", "value": Service.objects.filter(is_active=True).count(), "icon": "briefcase", "url": reverse("dashboard:module_list", args=["services"])},
        {"label": "Portfolio projects", "value": PortfolioProject.objects.filter(is_active=True).count(), "icon": "film", "url": reverse("dashboard:module_list", args=["portfolio"])},
        {"label": "Gallery images", "value": BTSImage.objects.filter(is_active=True).count(), "icon": "image", "url": reverse("dashboard:module_list", args=["bts"])},
        {"label": "Upcoming projects", "value": UpcomingProject.objects.filter(is_active=True).count(), "icon": "calendar", "url": reverse("dashboard:module_list", args=["upcoming"])},
        {"label": "Media files", "value": MediaItem.objects.count(), "icon": "image", "url": reverse("dashboard:module_list", args=["media"])},
    ]
    ai = ai_status()
    context = {
        "page_title": "Dashboard",
        "cards": cards,
        "status_rows": status_rows,
        "recent_leads": Lead.objects.all()[:6],
        "activities": ActivityLog.objects.select_related("user")[:10],
        "ai": ai,
        "email_ok": email_is_configured(),
    }
    return render(request, "dashboard/home.html", context)


# ----------------------------------------------------------------------------- generic CRUD
@staff_required
def module_list(request, key):
    module = get_module(request, key)
    if module.singleton:
        return _form_view(request, module, module.model.load(), creating=False)

    base_qs = module.base_queryset()
    qs = base_qs
    q = request.GET.get("q", "").strip()
    if q and module.search_fields:
        cond = Q()
        for field_name in module.search_fields:
            cond |= Q(**{f"{field_name}__icontains": q})
        qs = qs.filter(cond).distinct()
    qs = _apply_filters(module, request, qs)
    if not qs.ordered:
        qs = qs.order_by("pk")

    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    rows = [{"obj": o, "cells": [_cell(o, s) for s in module.list_fields]} for o in page.object_list]
    params = request.GET.copy()
    params.pop("page", None)
    context = {
        "module": module,
        "page_title": module.title,
        "headers": [_label(module, s) for s in module.list_fields],
        "rows": rows,
        "page": page,
        "q": q,
        "filters": _build_filters(module, request, base_qs),
        "querystring": params.urlencode(),
        "has_filters": bool(q or any(request.GET.get("f_" + n) for n in module.filters)),
        "next": request.get_full_path(),
    }
    return render(request, module.list_template, context)


def _get_form_class(module, creating):
    if creating and module.form_class_create:
        return module.form_class_create
    return module.form_class or build_modelform(module)


def _form_view(request, module, obj, creating):
    ctx = {"module": module, "obj": obj, "creating": creating, "page_title": module.title}
    if module.extra_context:
        ctx.update(module.extra_context(request, obj))

    if module.read_only:  # detail only (e.g. AI conversations)
        return render(request, module.detail_template, ctx)

    form_class = _get_form_class(module, creating)
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=obj)
    else:
        initial = {k: v for k, v in request.GET.items() if k in ("parent", "group")} if creating else None
        form = form_class(instance=obj, initial=initial) if initial else form_class(instance=obj)
    if module.form_init:
        module.form_init(form)  # must run before validation (e.g. limit/require the parent field)
    if request.method == "POST":
        if form.is_valid():
            saved = form.save()
            log_activity(request.user, "created" if creating else "updated", module.title, saved)
            messages.success(request, f"{module.title}: {'created' if creating else 'saved'} successfully.")
            if module.singleton:
                return redirect(request.path)
            return redirect(_safe_next(request, _list_url(module)))
        messages.error(request, "Please correct the errors below.")
    ctx.update({"form": form, "next": request.GET.get("next", "")})
    return render(request, module.detail_template or module.form_template, ctx)


@staff_required
def module_create(request, key):
    module = get_module(request, key)
    if module.singleton or not module.can_add:
        raise Http404
    return _form_view(request, module, None, creating=True)


@staff_required
def module_edit(request, key, pk):
    module = get_module(request, key)
    obj = get_object_or_404(module.base_queryset(), pk=pk)
    return _form_view(request, module, obj, creating=False)


def _guard(module, obj, request, action):
    if module.protect:
        error = module.protect(obj, request, action)
        if error:
            messages.error(request, error)
            return True
    return False


@staff_required
@require_POST
def module_delete(request, key, pk):
    module = get_module(request, key)
    if module.singleton or not module.can_delete:
        raise Http404
    obj = get_object_or_404(module.base_queryset(), pk=pk)
    if _guard(module, obj, request, "delete"):
        return redirect(_safe_next(request, _list_url(module)))
    label = str(obj)
    try:
        obj.delete()
    except ProtectedError:
        messages.error(request, "This item is in use and cannot be deleted.")
    else:
        log_activity(request.user, "deleted", module.title, label)
        messages.success(request, f"{module.title}: '{label}' deleted.")
    return redirect(_safe_next(request, _list_url(module)))


@staff_required
@require_POST
def module_toggle(request, key, pk):
    module = get_module(request, key)
    if not module.can_toggle:
        raise Http404
    obj = get_object_or_404(module.base_queryset(), pk=pk)
    if _guard(module, obj, request, "toggle"):
        return redirect(_safe_next(request, _list_url(module)))
    obj.is_active = not obj.is_active
    obj.save(update_fields=["is_active"] + (["updated_at"] if hasattr(obj, "updated_at") else []))
    log_activity(request.user, "toggled", module.title, f"{obj} -> {'active' if obj.is_active else 'inactive'}")
    messages.success(request, f"'{obj}' is now {'active' if obj.is_active else 'inactive'}.")
    return redirect(_safe_next(request, _list_url(module)))


@staff_required
@require_POST
def module_move(request, key, pk, direction):
    module = get_module(request, key)
    if not module.can_reorder or direction not in ("up", "down"):
        raise Http404
    obj = get_object_or_404(module.base_queryset(), pk=pk)
    siblings_qs = module.base_queryset()
    if module.reorder_scope:
        siblings_qs = siblings_qs.filter(**{module.reorder_scope: getattr(obj, module.reorder_scope + "_id")})
    siblings = list(siblings_qs.order_by("order", "id"))
    ids = [s.pk for s in siblings]
    pos = ids.index(obj.pk)
    swap = pos - 1 if direction == "up" else pos + 1
    if 0 <= swap < len(siblings):
        siblings[pos], siblings[swap] = siblings[swap], siblings[pos]
    for index, sibling in enumerate(siblings):
        sibling.order = index
    module.model.objects.bulk_update(siblings, ["order"])
    log_activity(request.user, "moved", module.title, obj)
    return redirect(_safe_next(request, _list_url(module)))
