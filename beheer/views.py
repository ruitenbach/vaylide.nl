"""Beheeromgeving voor de eigenaar (alleen voor gebruikers met is_staff)."""
from __future__ import annotations

import functools

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from catalog.models import AddOn, Package, Template, TemplateVersion
from core.ai import ai_configured
from orders.stuck import stuck_orders
from core.models import ContactMessage, SiteConfig
from core.privacy import anonymize_user, delete_invitation
from core.utils import ip_fingerprint, rate_limit
from invitations.content import publish_issues
from invitations.models import Invitation, InvitationVersion, Source
from invitations.services import DraftConflict, PublishBlocked, availability_end, publish_draft, restore_version, save_draft
from orders.models import Order, PaymentEvent
from orders.services import invitation_is_paid
from portal.views import _attachment_response, _rsvp_stats, guest_csv
from processing.emails import get_fault, set_fault
from processing.jobs import enqueue, retry
from processing.models import Job, OutboundEmail
from wishes.forms import ProposalForm, StaffMessageForm, StatusForm
from wishes.models import CustomRequest
from wishes.services import WishError, add_message, send_proposal, set_status

from .forms import AddOnForm, ExtendForm, OverridesForm, PackageForm, SiteConfigForm, TemplateForm


def staff_required(view):
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('beheer:login')}?next={request.path}")
        if not request.user.is_staff:
            raise Http404()
        return view(request, *args, **kwargs)

    return wrapper


class StaffLoginView(auth_views.LoginView):
    template_name = "beheer/login.html"
    redirect_authenticated_user = False

    def post(self, request, *args, **kwargs):
        if not rate_limit(f"staff-login:{ip_fingerprint(request)}", 10, 900):
            form = self.get_form()
            form.add_error(None, "Te veel inlogpogingen. Wacht een kwartier en probeer het opnieuw.")
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        if not form.get_user().is_staff:
            form.add_error(None, "Dit account heeft geen toegang tot het beheer.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return self.get_redirect_url() or reverse("beheer:dashboard")


def _attention():
    return {
        "wishes_new": CustomRequest.objects.filter(unread_by_staff=True).exclude(status=CustomRequest.Status.CLOSED).count(),
        "orders_attention": Order.objects.filter(fulfilment_status=Order.Fulfilment.ATTENTION).count(),
        "orders_stuck": len(stuck_orders()),
        "orders_processing": Order.objects.filter(status=Order.Status.PAID, fulfilment_status=Order.Fulfilment.PROCESSING).count(),
        "jobs_failed": Job.objects.filter(status__in=[Job.Status.FAILED, Job.Status.DEAD]).count(),
        "jobs_dead": Job.objects.filter(status=Job.Status.DEAD).count(),
        "emails_failed": OutboundEmail.objects.filter(status=OutboundEmail.Status.FAILED).count(),
        "contact_open": ContactMessage.objects.filter(handled_at__isnull=True).count(),
        "admin_edits_pending": Invitation.objects.filter(draft_updated_source=Source.ADMIN, status=Invitation.Status.LIVE)
        .exclude(published_version__isnull=True)
        .count(),
    }


@staff_required
def dashboard(request):
    now = timezone.now()
    context = {
        "attention": _attention(),
        "recent_orders": Order.objects.select_related("customer").order_by("-created_at")[:8],
        "recent_wishes": CustomRequest.objects.select_related("customer").order_by("-updated_at")[:6],
        "counts": {
            "live": Invitation.objects.filter(status=Invitation.Status.LIVE).count(),
            "drafts": Invitation.objects.filter(status=Invitation.Status.DRAFT).count(),
            "customers": Invitation.objects.values("owner").exclude(owner__isnull=True).distinct().count(),
            "paid_30d": Order.objects.filter(status=Order.Status.PAID, paid_at__gte=now - timezone.timedelta(days=30)).count(),
        },
        "failed_jobs": Job.objects.filter(status__in=[Job.Status.FAILED, Job.Status.DEAD]).select_related("order")[:5],
    }
    return render(request, "beheer/dashboard.html", context)


# ---------------------------------------------------------------- bestellingen

@staff_required
def orders(request):
    qs = Order.objects.select_related("customer", "invitation").order_by("-created_at")
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    fulfilment = request.GET.get("verwerking", "")
    if fulfilment:
        qs = qs.filter(fulfilment_status=fulfilment)
    query = request.GET.get("zoek", "").strip()
    if query:
        qs = qs.filter(Q(number__icontains=query) | Q(customer__email__icontains=query) | Q(invitation_title__icontains=query))
    page = Paginator(qs, 30).get_page(request.GET.get("pagina"))
    return render(request, "beheer/orders.html", {"page": page, "status": status, "verwerking": fulfilment, "zoek": query,
                                                  "statuses": Order.Status.choices, "fulfilments": Order.Fulfilment.choices})


@staff_required
def order_detail(request, uid):
    order = get_object_or_404(Order.objects.select_related("customer", "invitation", "custom_request"), uid=uid)
    if request.method == "POST":
        action = request.POST.get("actie")
        if action == "opnieuw-verwerken":
            job = Job.objects.filter(order=order, kind__in=["fulfil_order", "fulfil_custom_order"]).order_by("-created_at").first()
            if job is None and order.status == Order.Status.PAID:
                kind = "fulfil_order" if order.kind == Order.Kind.INVITATION else "fulfil_custom_order"
                job = enqueue(kind, {"order_id": order.pk}, unique_key=f"{kind}:{order.pk}", order=order, invitation=order.invitation, run_inline=False)
            if job:
                retry(job)
                messages.success(request, f"Verwerking opnieuw gestart: {job.get_status_display().lower()}.")
        elif action == "status":
            new = request.POST.get("status")
            if new in Order.Status.values and new != order.status:
                old_label = order.get_status_display()
                order.status = new
                order.save(update_fields=["status", "updated_at"])
                # Handmatige wijzigingen blijven navolgbaar in het logboek van de bestelling.
                payment = order.latest_payment
                if payment is not None:
                    PaymentEvent.objects.create(
                        payment=payment,
                        provider=payment.provider,
                        provider_ref=payment.provider_ref,
                        source="beheer",
                        remote_status=new,
                        outcome=f"Status handmatig gewijzigd van '{old_label}' naar '{order.get_status_display()}' door {request.user.email}."[:200],
                    )
                messages.success(request, "Status van de bestelling aangepast.")
        elif action == "aandacht-afgehandeld":
            order.fulfilment_status = Order.Fulfilment.DONE
            order.fulfilment_note = f"Handmatig afgehandeld door {request.user.email} op {timezone.localtime():%d-%m-%Y %H:%M}."
            order.save(update_fields=["fulfilment_status", "fulfilment_note", "updated_at"])
            messages.success(request, "Gemarkeerd als afgehandeld.")
        return redirect("beheer:order", uid=order.uid)
    return render(
        request,
        "beheer/order.html",
        {
            "order": order,
            "payments": order.payments.all(),
            "events": PaymentEvent.objects.filter(payment__order=order).order_by("-received_at")[:30],
            "jobs": order.jobs.order_by("-created_at"),
            "emails": order.emails.order_by("-created_at"),
            "statuses": Order.Status.choices,
        },
    )


# ------------------------------------------------------------- uitnodigingen

@staff_required
def invitations(request):
    qs = Invitation.objects.select_related("owner", "template_version__template").order_by("-updated_at")
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    query = request.GET.get("zoek", "").strip()
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(owner__email__icontains=query) | Q(slug__icontains=query))
    page = Paginator(qs, 30).get_page(request.GET.get("pagina"))
    return render(request, "beheer/invitations.html", {"page": page, "status": status, "zoek": query, "statuses": Invitation.Status.choices})


def _rev(request) -> int | None:
    try:
        return int(request.POST.get("rev", ""))
    except ValueError:
        return None


@staff_required
def invitation_detail(request, uid):
    inv = get_object_or_404(Invitation.objects.select_related("owner", "template_version__template", "published_version"), uid=uid)
    overrides_form = OverridesForm(initial=OverridesForm.initial_from(inv.draft_overrides or {}))
    extend_form = ExtendForm(initial={"months": 6})
    if request.method == "POST":
        action = request.POST.get("actie")
        try:
            if action == "overrides":
                overrides_form = OverridesForm(request.POST)
                if overrides_form.is_valid():
                    save_draft(inv, expected_rev=_rev(request), overrides=overrides_form.to_overrides(inv.template_version),
                               user=request.user, source=Source.ADMIN)
                    messages.success(request, "Beheer-aanpassingen opgeslagen in het concept. Publiceer om ze online te zetten.")
                    return redirect("beheer:invitation", uid=inv.uid)
            elif action == "publiceren":
                version = publish_draft(inv, user=request.user, source=Source.ADMIN, expected_rev=_rev(request),
                                        note=(request.POST.get("note") or "Gepubliceerd door het VAYLIDE-team")[:200])
                messages.success(request, f"Versie {version.number} staat online.")
                return redirect("beheer:invitation", uid=inv.uid)
            elif action == "herstellen":
                version = get_object_or_404(InvitationVersion, invitation=inv, pk=request.POST.get("versie"))
                inv = restore_version(inv, version, user=request.user, source=Source.ADMIN, expected_rev=_rev(request))
                if request.POST.get("direct_publiceren") and invitation_is_paid(inv):
                    new = publish_draft(inv, user=request.user, source=Source.RESTORE, expected_rev=inv.draft_rev,
                                        note=f"Versie {version.number} hersteld en gepubliceerd")
                    messages.success(request, f"Versie {version.number} is hersteld en gepubliceerd als versie {new.number}.")
                else:
                    messages.success(request, f"Versie {version.number} is teruggezet in het concept. Controleer en publiceer.")
                return redirect("beheer:invitation", uid=inv.uid)
            elif action == "vergrendelen":
                inv.customer_locked = not inv.customer_locked
                inv.lock_reason = (request.POST.get("reden") or "")[:200] if inv.customer_locked else ""
                inv.save(update_fields=["customer_locked", "lock_reason", "updated_at"])
                messages.success(request, "Klant kan tijdelijk niet wijzigen." if inv.customer_locked else "Klant kan weer wijzigen.")
                return redirect("beheer:invitation", uid=inv.uid)
            elif action == "verlengen":
                extend_form = ExtendForm(request.POST)
                if extend_form.is_valid():
                    start = inv.available_until if inv.available_until and inv.available_until > timezone.now() else timezone.now()
                    inv.available_until = availability_end(extend_form.cleaned_data["months"], start)
                    if inv.status == Invitation.Status.EXPIRED:
                        inv.status = Invitation.Status.LIVE
                    inv.save(update_fields=["available_until", "status", "updated_at"])
                    messages.success(request, f"Online tot {timezone.localtime(inv.available_until):%d-%m-%Y}.")
                    return redirect("beheer:invitation", uid=inv.uid)
            elif action == "offline":
                inv.status = Invitation.Status.OFFLINE
                inv.save(update_fields=["status", "updated_at"])
                messages.success(request, "De uitnodiging is offline gehaald.")
                return redirect("beheer:invitation", uid=inv.uid)
            elif action == "online":
                if not inv.published_version_id:
                    messages.error(request, "Er is nog geen gepubliceerde versie.")
                else:
                    inv.status = Invitation.Status.LIVE
                    inv.save(update_fields=["status", "updated_at"])
                    messages.success(request, "De uitnodiging staat weer online.")
                return redirect("beheer:invitation", uid=inv.uid)
            elif action == "ontwerpversie":
                target = get_object_or_404(TemplateVersion, pk=request.POST.get("versie"), template=inv.template_version.template)
                save_draft(inv, expected_rev=_rev(request), template_version=target, content=inv.draft_content,
                           user=request.user, source=Source.ADMIN)
                messages.success(request, f"Het concept gebruikt nu {target}. De gepubliceerde versie verandert pas na publiceren.")
                return redirect("beheer:invitation", uid=inv.uid)
            elif action == "verwijderen":
                if request.POST.get("bevestig") == "verwijderen":
                    delete_invitation(inv)
                    messages.success(request, "De uitnodiging en alle bijbehorende gegevens zijn verwijderd.")
                    return redirect("beheer:invitations")
                messages.error(request, "Typ 'verwijderen' om te bevestigen.")
        except DraftConflict as exc:
            messages.error(
                request,
                f"Conflict: het concept is intussen gewijzigd door {exc.invitation.get_draft_updated_source_display().lower()} "
                f"({timezone.localtime(exc.invitation.draft_updated_at):%d-%m %H:%M}). Bekijk de nieuwste stand en probeer opnieuw.",
            )
            return redirect("beheer:invitation", uid=inv.uid)
        except PublishBlocked as exc:
            messages.error(request, "Kan niet publiceren: " + " ".join(i.message for i in exc.issues))
            return redirect("beheer:invitation", uid=inv.uid)
    template = inv.template_version.template
    newer = template.versions.filter(number__gt=inv.template_version.number).order_by("-number")
    return render(
        request,
        "beheer/invitation.html",
        {
            "inv": inv,
            "versions": inv.versions.select_related("created_by", "template_version").order_by("-number"),
            "overrides_form": overrides_form,
            "extend_form": extend_form,
            "stats": _rsvp_stats(inv),
            "orders": inv.orders.order_by("-created_at"),
            "issues": publish_issues(inv.draft_content, inv.occasion, first_publication=not inv.is_published),
            "paid": invitation_is_paid(inv),
            "newer_versions": newer,
            "jobs": inv.jobs.order_by("-created_at")[:10],
            "wishes": inv.custom_requests.order_by("-updated_at")[:5],
            "has_changes": inv.has_unpublished_changes,
        },
    )


@staff_required
def invitation_guests_export(request, uid):
    return guest_csv(get_object_or_404(Invitation, uid=uid))


# ------------------------------------------------------------------ klanten

@staff_required
def customers(request):
    from accounts.models import User

    qs = User.objects.filter(is_staff=False).annotate(
        n_invitations=Count("invitations", distinct=True), n_orders=Count("orders", distinct=True)
    ).order_by("-date_joined")
    query = request.GET.get("zoek", "").strip()
    if query:
        qs = qs.filter(Q(email__icontains=query) | Q(name__icontains=query))
    only_newsletter = request.GET.get("nieuwsbrief") == "1"
    if only_newsletter:
        qs = qs.filter(newsletter=True)
    page = Paginator(qs, 40).get_page(request.GET.get("pagina"))
    total = User.objects.filter(is_staff=False, newsletter=True, is_active=True).count()
    return render(request, "beheer/customers.html", {"page": page, "zoek": query, "alleen_nieuwsbrief": only_newsletter, "nieuwsbrief_totaal": total})


@staff_required
def newsletter_export(request):
    """De nieuwsbrieflijst (alleen klanten die zelf het vinkje zetten), als CSV voor een nieuwsbriefdienst."""
    import csv

    from django.http import HttpResponse

    from accounts.models import User

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="nieuwsbrief-vaylide.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["e-mailadres", "naam", "aangemeld op", "tekst bij de toestemming"])
    for user in User.objects.filter(is_staff=False, newsletter=True, is_active=True).order_by("newsletter_since"):
        safe = [str(v or "") for v in (user.email, user.name, user.newsletter_since and timezone.localtime(user.newsletter_since).strftime("%d-%m-%Y %H:%M"), user.newsletter_consent)]
        writer.writerow(["'" + v if v[:1] in ("=", "+", "-", "@") else v for v in safe])
    return response


@staff_required
def customer_detail(request, pk):
    from accounts.models import User

    customer = get_object_or_404(User, pk=pk, is_staff=False)
    if request.method == "POST" and request.POST.get("actie") == "anonimiseren":
        if request.POST.get("bevestig") == "verwijderen":
            anonymize_user(customer)
            messages.success(request, "Klantgegevens verwijderd; bestellingen zijn geanonimiseerd bewaard.")
            return redirect("beheer:customers")
        messages.error(request, "Typ 'verwijderen' om te bevestigen.")
    return render(
        request,
        "beheer/customer.html",
        {
            "customer": customer,
            "invitations": customer.invitations.order_by("-updated_at"),
            "orders": customer.orders.order_by("-created_at"),
            "wishes": customer.custom_requests.order_by("-updated_at"),
        },
    )


# ---------------------------------------------------------------- extra wensen

@staff_required
def wishes(request):
    qs = CustomRequest.objects.select_related("customer", "invitation").order_by("-updated_at")
    status = request.GET.get("status", "open")
    if status == "open":
        qs = qs.filter(status__in=CustomRequest.OPEN_STATUSES)
    elif status:
        qs = qs.filter(status=status)
    page = Paginator(qs, 30).get_page(request.GET.get("pagina"))
    return render(request, "beheer/wishes.html", {"page": page, "status": status, "statuses": CustomRequest.Status.choices})


@staff_required
def wish_detail(request, uid):
    req = get_object_or_404(CustomRequest.objects.select_related("customer", "invitation"), uid=uid)
    if req.unread_by_staff:
        req.unread_by_staff = False
        req.save(update_fields=["unread_by_staff"])
    message_form = StaffMessageForm()
    proposal_form = ProposalForm(initial={"text": req.proposal_text, "price": (req.proposal_price_cents or 0) / 100 or None})
    status_form = StatusForm(initial={"status": req.status})
    if request.method == "POST":
        action = request.POST.get("actie")
        try:
            if action == "bericht":
                message_form = StaffMessageForm(request.POST, request.FILES)
                if message_form.is_valid():
                    add_message(req, author=request.user, body=message_form.cleaned_data.get("body") or "", from_staff=True,
                                internal=message_form.cleaned_data.get("internal"), attachment=message_form.cleaned_data.get("attachment"))
                    messages.success(request, "Bericht opgeslagen." if message_form.cleaned_data.get("internal") else "Bericht verstuurd naar de klant.")
                    return redirect("beheer:wish", uid=req.uid)
            elif action == "voorstel":
                proposal_form = ProposalForm(request.POST)
                if proposal_form.is_valid():
                    send_proposal(req, author=request.user, text=proposal_form.cleaned_data["text"], price_cents=proposal_form.price_cents())
                    messages.success(request, "Voorstel verstuurd. De klant kan het accepteren in Mijn VAYLIDE.")
                    return redirect("beheer:wish", uid=req.uid)
            elif action == "status":
                status_form = StatusForm(request.POST)
                if status_form.is_valid():
                    set_status(req, status_form.cleaned_data["status"], author=request.user, note=status_form.cleaned_data.get("note") or "")
                    messages.success(request, "Status bijgewerkt en klant geïnformeerd.")
                    return redirect("beheer:wish", uid=req.uid)
            elif action == "ai-opnieuw":
                enqueue("assess_request", {"request_id": req.pk}, unique_key=f"assess_request:{req.pk}:{int(timezone.now().timestamp())}", max_attempts=2)
                messages.success(request, "Nieuwe inschatting aangevraagd.")
                return redirect("beheer:wish", uid=req.uid)
        except WishError as exc:
            messages.error(request, str(exc))
    return render(
        request,
        "beheer/wish.html",
        {
            "req": req,
            "thread": req.messages.select_related("author").prefetch_related("attachments"),
            "attachments": req.attachments.all(),
            "message_form": message_form,
            "proposal_form": proposal_form,
            "status_form": status_form,
            "orders": req.orders.order_by("-created_at"),
            "ai_configured": ai_configured(),
            "assess_job": Job.objects.filter(kind="assess_request", payload__request_id=req.pk).order_by("-created_at").first(),
        },
    )


@staff_required
def wish_attachment(request, uid, attachment_uid):
    req = get_object_or_404(CustomRequest, uid=uid)
    return _attachment_response(get_object_or_404(req.attachments, uid=attachment_uid))


# ------------------------------------------------------------- ontwerpen

@staff_required
def templates(request):
    items = Template.objects.prefetch_related("versions").annotate(n_invitations=Count("versions__id")).order_by("sort_order")
    usage = {
        row["template_version__template"]: row["n"]
        for row in Invitation.objects.values("template_version__template").annotate(n=Count("id"))
    }
    rows = [(t, usage.get(t.pk, 0)) for t in items]
    return render(request, "beheer/templates.html", {"rows": rows})


@staff_required
def template_edit(request, pk):
    template = get_object_or_404(Template, pk=pk)
    form = TemplateForm(request.POST or None, instance=template)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ontwerp opgeslagen. Bestaande uitnodigingen blijven hun eigen ontwerpversie gebruiken.")
        return redirect("beheer:templates")
    usage = Invitation.objects.filter(template_version__template=template).values("template_version__number").annotate(n=Count("id"))
    return render(request, "beheer/template_edit.html", {"form": form, "template": template, "usage": usage})


# ---------------------------------------------------------------- prijzen

@staff_required
def pricing(request):
    return render(request, "beheer/pricing.html", {"packages": Package.objects.all(), "addons": AddOn.objects.all(),
                                                   "config": SiteConfig.get()})


@staff_required
def package_edit(request, pk=None):
    package = get_object_or_404(Package, pk=pk) if pk else None
    form = PackageForm(request.POST or None, instance=package)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Pakket opgeslagen. Nieuwe bestellingen gebruiken direct de nieuwe prijs; bestaande bestellingen veranderen niet.")
        return redirect("beheer:pricing")
    return render(request, "beheer/edit_form.html", {"form": form, "title": "Pakket bewerken" if package else "Nieuw pakket", "back": reverse("beheer:pricing")})


@staff_required
def addon_edit(request, pk=None):
    addon = get_object_or_404(AddOn, pk=pk) if pk else None
    form = AddOnForm(request.POST or None, instance=addon)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Extra optie opgeslagen.")
        return redirect("beheer:pricing")
    return render(request, "beheer/edit_form.html", {"form": form, "title": "Extra optie bewerken" if addon else "Nieuwe extra optie", "back": reverse("beheer:pricing")})


# -------------------------------------------------------------- verwerking

@staff_required
def processing(request):
    if request.method == "POST":
        action = request.POST.get("actie")
        if action == "opnieuw":
            job = get_object_or_404(Job, pk=request.POST.get("job"))
            retry(job)
            messages.success(request, f"Taak #{job.pk}: {job.get_status_display().lower()}.")
        elif action == "alles-opnieuw":
            count = 0
            for job in Job.objects.filter(status__in=[Job.Status.FAILED, Job.Status.DEAD]):
                retry(job)
                count += 1
            messages.success(request, f"{count} taak/taken opnieuw geprobeerd.")
        elif action == "bestelling-opnieuw":
            from orders.stuck import restart

            order = get_object_or_404(Order, uid=request.POST.get("bestelling"))
            messages.success(request, f"{order.number}: {restart(order)}")
        elif action == "storing" and settings.TEST_MODE:
            set_fault("publish", int(request.POST.get("publish") or 0))
            set_fault("email", int(request.POST.get("email") or 0))
            messages.success(request, "Teststoringen ingesteld.")
        return redirect("beheer:processing")
    status = request.GET.get("status", "problemen")
    jobs = Job.objects.select_related("order", "invitation").order_by("-created_at")
    if status == "problemen":
        jobs = jobs.filter(status__in=[Job.Status.FAILED, Job.Status.DEAD, Job.Status.PENDING, Job.Status.RUNNING])
    elif status:
        jobs = jobs.filter(status=status)
    return render(
        request,
        "beheer/processing.html",
        {
            "stuck": stuck_orders(),
            "jobs": jobs[:100],
            "status": status,
            "emails": OutboundEmail.objects.order_by("-created_at")[:40],
            "faults": {"publish": get_fault("publish"), "email": get_fault("email")},
        },
    )


@staff_required
def email_detail(request, pk):
    email = get_object_or_404(OutboundEmail, pk=pk)
    return render(request, "beheer/email.html", {"email": email})


# ------------------------------------------------------------ contact en instellingen

@staff_required
def contact_messages(request):
    if request.method == "POST":
        msg = get_object_or_404(ContactMessage, pk=request.POST.get("bericht"))
        msg.handled_at = None if msg.handled_at else timezone.now()
        msg.handled_by = request.user if msg.handled_at else None
        msg.save()
        return redirect("beheer:contact_messages")
    page = Paginator(ContactMessage.objects.order_by("handled_at", "-created_at"), 30).get_page(request.GET.get("pagina"))
    return render(request, "beheer/contact_messages.html", {"page": page})


@staff_required
def site_settings(request):
    config = SiteConfig.get()
    form = SiteConfigForm(request.POST or None, instance=config)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Instellingen opgeslagen.")
        return redirect("beheer:settings")
    integrations = [
        ("Modus", "Testmodus" if settings.TEST_MODE else "Live", settings.TEST_MODE),
        ("Betalingen", {"test": "Testbetalingen (gesimuleerd)", "mollie": "Mollie (testsleutel, geen echt geld)" if settings.MOLLIE_API_KEY.startswith("test_") else ("Mollie (live)" if settings.MOLLIE_API_KEY else "Mollie (sleutel ontbreekt)")}.get(settings.PAYMENT_PROVIDER, settings.PAYMENT_PROVIDER),
         settings.PAYMENT_PROVIDER == "test" or not settings.MOLLIE_API_KEY.startswith("live_")),
        ("E-mail", "Alleen bewaard (outbox)" if settings.EMAIL_MODE == "outbox" else f"SMTP via {settings.EMAIL_HOST}", settings.EMAIL_MODE == "outbox"),
        ("AI-hulp", f"Claude ({settings.AI_MODEL})" if ai_configured() else "Testmodus (geen API-sleutel)", not ai_configured()),
        ("Publieke adres", settings.BASE_URL, settings.BASE_URL.startswith("http://")),
        ("Database", settings.DATABASES["default"]["ENGINE"].rsplit(".", 1)[-1], False),
    ]
    return render(request, "beheer/settings.html", {"form": form, "integrations": integrations})
