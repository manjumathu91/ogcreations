"""Custom dashboard pages that don't fit the generic CRUD: lead status, media upload,
email management, AI chat and AI insights."""
import json
import re
from collections import Counter
from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.decorators import staff_required
from apps.ai_assistant.models import AIConversation, AIMessage
from apps.ai_assistant.services import TASKS, ai_status
from apps.communications.models import EmailLog
from apps.communications.services import email_config_summary, send_test_email
from apps.leads.models import Lead
from apps.media_library.models import MediaItem

from .forms import EmailTestForm
from .utils import log_activity


# ----------------------------------------------------------------------------- leads
@staff_required
def lead_status(request):
    qs = Lead.objects.all()
    status = request.GET.get("status", "")
    lead_type = request.GET.get("type", "")
    q = request.GET.get("q", "").strip()
    if status in dict(Lead.STATUS_CHOICES):
        qs = qs.filter(status=status)
    if lead_type in dict(Lead.TYPE_CHOICES):
        qs = qs.filter(lead_type=lead_type)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(project_type__icontains=q) | Q(message__icontains=q))
    counts = dict(Lead.objects.values_list("status").annotate(c=Count("id")).order_by())
    summary = [{"value": v, "label": label, "count": counts.get(v, 0), "active": status == v} for v, label in Lead.STATUS_CHOICES]
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "dashboard/lead_status.html", {
        "page_title": "Lead Status", "summary": summary, "page": page, "q": q, "status": status, "type": lead_type,
        "status_choices": Lead.STATUS_CHOICES, "type_choices": Lead.TYPE_CHOICES, "querystring": params.urlencode(),
        "total": Lead.objects.count(), "next": request.get_full_path(),
    })


@staff_required
@require_POST
def lead_quick_status(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    new_status = request.POST.get("status", "")
    if new_status in dict(Lead.STATUS_CHOICES):
        lead.status = new_status
        lead.save(update_fields=["status", "updated_at"])
        log_activity(request.user, "updated", "Lead Status", f"{lead.name} -> {lead.get_status_display()}")
        messages.success(request, f"{lead.name}: status set to {lead.get_status_display()}.")
    else:
        messages.error(request, "Invalid status.")
    nxt = request.POST.get("next", "")
    if nxt.startswith("/dashboard/"):
        return redirect(nxt)
    return redirect("dashboard:lead_status")


# ----------------------------------------------------------------------------- media
@staff_required
@require_POST
def media_upload(request):
    files = request.FILES.getlist("files")
    if not files:
        messages.error(request, "Choose at least one image to upload.")
        return redirect("dashboard:module_list", key="media")
    ok, errors = 0, []
    alt = request.POST.get("alt_text", "").strip()[:255]
    for f in files:
        item = MediaItem(file=f, uploaded_by=request.user, alt_text=alt)
        try:
            item.full_clean()
            item.save()
            ok += 1
        except ValidationError as exc:
            detail = "; ".join(sum(exc.message_dict.values(), [])) if hasattr(exc, "error_dict") else "; ".join(exc.messages)
            errors.append(f"{f.name}: {detail}")
    if ok:
        log_activity(request.user, "created", "Media Library", f"{ok} file(s) uploaded")
        messages.success(request, f"{ok} image{'s' if ok != 1 else ''} uploaded.")
    for err in errors[:5]:
        messages.error(request, err)
    return redirect("dashboard:module_list", key="media")


# ----------------------------------------------------------------------------- email
@staff_required
def email_management(request):
    logs_qs = EmailLog.objects.select_related("lead")
    status = request.GET.get("status", "")
    if status in ("sent", "failed"):
        logs_qs = logs_qs.filter(status=status)
    page = Paginator(logs_qs, 10).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "dashboard/email.html", {
        "page_title": "Email Management", "config": email_config_summary(), "form": EmailTestForm(),
        "page": page, "status": status, "querystring": params.urlencode(),
        "sent_count": EmailLog.objects.filter(status="sent").count(),
        "failed_count": EmailLog.objects.filter(status="failed").count(),
    })


@staff_required
@require_POST
def email_test(request):
    form = EmailTestForm(request.POST)
    if form.is_valid():
        log = send_test_email(form.cleaned_data["to_email"])
        log_activity(request.user, "other", "Email Management", f"test email to {log.to_email}: {log.status}")
        if log.status == "sent":
            messages.success(request, f"Test email sent to {log.to_email}.")
        else:
            messages.error(request, f"Test email failed: {log.error_message}")
    else:
        messages.error(request, "Enter a valid email address.")
    return redirect("dashboard:email")


# ----------------------------------------------------------------------------- AI
@staff_required
def ai_chat(request):
    conversation = None
    chat_messages = []
    cid = request.GET.get("c", "")
    if cid.isdigit():
        conversation = AIConversation.objects.filter(pk=int(cid), scope="admin", user=request.user).first()
        if conversation:
            chat_messages = list(conversation.messages.all())
    return render(request, "dashboard/ai_chat.html", {
        "page_title": "AI Chat", "ai": ai_status(), "tasks": TASKS,
        "hints_json": json.dumps({k: v["hint"] for k, v in TASKS.items()}), "conversation": conversation, "chat_messages": chat_messages,
        "recent": AIConversation.objects.filter(scope="admin", user=request.user)[:6],
    })


STOPWORDS = set(
    "about above after again also been before being between could does doing from have having here into just like more most "
    "much need only other over please really should some such than that their them then there these they this those very want "
    "what when where which while will with would your you the and for are can how who why not any all our out get has".split()
)


@staff_required
def ai_insights(request):
    now = timezone.now()
    since = now - timedelta(days=7)
    user_msgs = AIMessage.objects.filter(conversation__scope="public", role="user")
    recent = list(user_msgs.order_by("-created_at")[:300])
    words = Counter()
    for m in recent:
        for w in re.findall(r"[a-zA-Z]{4,}", m.content.lower()):
            if w not in STOPWORDS:
                words[w] += 1
    by_day = Counter(timezone.localtime(m.created_at).date() for m in user_msgs.filter(created_at__gte=since))
    days = [(now - timedelta(days=i)) for i in range(6, -1, -1)]
    daily = [{"label": timezone.localtime(d).strftime("%a %d"), "count": by_day.get(timezone.localtime(d).date(), 0)} for d in days]
    peak = max([d["count"] for d in daily] + [1])
    for d in daily:
        d["pct"] = round(d["count"] * 100 / peak)
    return render(request, "dashboard/ai_insights.html", {
        "page_title": "AI Insights", "ai": ai_status(),
        "public_conversations": AIConversation.objects.filter(scope="public").count(),
        "admin_conversations": AIConversation.objects.filter(scope="admin").count(),
        "public_questions": user_msgs.count(),
        "questions_7d": user_msgs.filter(created_at__gte=since).count(),
        "daily": daily, "top_terms": words.most_common(12), "recent_questions": recent[:12],
    })
