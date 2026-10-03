"""Mijn Vaylide: concepten, bestellingen, uitnodigingen, aanmeldingen en extra wensen.

Iedere view controleert aan de serverzijde dat de gegevens van de ingelogde
klant zijn. Anders volgt een 404 (we verklappen niet dat iets bestaat).
"""
from __future__ import annotations

import csv
import io

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from core.privacy import anonymize_user, delete_invitation
from invitations.models import GuestResponse, Invitation
from invitations.qr import qr_png, qr_svg
from orders.models import Order
from orders.services import CheckoutError, invitation_is_paid
from studio.steps import heeft_envelopstap
from wishes.forms import MessageForm, WishForm
from wishes.models import CustomRequest
from wishes.services import WishError, accept_proposal, add_message, create_request, pay_open_proposal


def customer_required(view):
    """Alleen voor klanten; beheerders gebruiken /beheer/."""

    @login_required
    def wrapper(request, *args, **kwargs):
        return view(request, *args, **kwargs)

    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    return wrapper


def _own_invitation(request, uid) -> Invitation:
    invitation = get_object_or_404(
        Invitation.objects.select_related("template_version__template", "published_version"), uid=uid
    )
    if invitation.owner_id != request.user.id:
        raise Http404()
    return invitation


def _rsvp_stats(invitation: Invitation) -> dict:
    agg = invitation.responses.aggregate(
        total=Count("id"),
        yes=Count("id", filter=Q(attending=True)),
        no=Count("id", filter=Q(attending=False)),
        persons=Sum("party_size", filter=Q(attending=True)),
    )
    agg["persons"] = agg["persons"] or 0
    return agg


@customer_required
def home(request):
    # Eén query voor alle uitnodigingen, inclusief betaalstatus en aanmeldcijfers.
    paid_orders = Order.objects.filter(invitation=OuterRef("pk"), kind=Order.Kind.INVITATION, status=Order.Status.PAID)
    invitations = list(
        Invitation.objects.filter(owner=request.user)
        .select_related("template_version__template")
        .annotate(
            paid=Exists(paid_orders),
            stat_total=Count("responses", distinct=True),
            stat_yes=Count("responses", filter=Q(responses__attending=True), distinct=True),
            stat_no=Count("responses", filter=Q(responses__attending=False), distinct=True),
            stat_persons=Sum("responses__party_size", filter=Q(responses__attending=True)),
        )
        .order_by("-updated_at")
    )
    for invitation in invitations:
        invitation.stats = (
            {"total": invitation.stat_total, "yes": invitation.stat_yes, "no": invitation.stat_no, "persons": invitation.stat_persons or 0}
            if invitation.is_published
            else None
        )
    orders = Order.objects.filter(customer=request.user).order_by("-created_at")[:10]
    wishes = CustomRequest.objects.filter(customer=request.user).order_by("-updated_at")[:10]
    return render(request, "portal/home.html", {"invitations": invitations, "orders": orders, "wishes": wishes})


@customer_required
def invitation_detail(request, uid):
    invitation = _own_invitation(request, uid)
    paid = invitation_is_paid(invitation)
    orders = invitation.orders.order_by("-created_at")
    recent = invitation.responses.order_by("-created_at")[:8]
    return render(
        request,
        "portal/invitation.html",
        {
            "inv": invitation,
            "paid": paid,
            "stats": _rsvp_stats(invitation),
            "recent": recent,
            "orders": orders,
            "pending_order": orders.filter(status__in=[Order.Status.PENDING, Order.Status.FAILED]).first(),
            "has_changes": invitation.has_unpublished_changes,
            "processing_order": orders.filter(status=Order.Status.PAID).exclude(fulfilment_status=Order.Fulfilment.DONE).first(),
            "wishes": invitation.custom_requests.order_by("-updated_at")[:5],
            "envelop_stap": heeft_envelopstap(invitation),
        },
    )


@customer_required
def guests(request, uid):
    invitation = _own_invitation(request, uid)
    shown = request.GET.get("filter", "")
    responses = invitation.responses.order_by("name")
    if shown == "ja":
        responses = responses.filter(attending=True)
    elif shown == "nee":
        responses = responses.filter(attending=False)
    query = request.GET.get("zoek", "").strip()
    if query:
        responses = responses.filter(name__icontains=query)
    page = Paginator(responses, 50).get_page(request.GET.get("pagina"))
    questions = []
    if invitation.published_version:
        questions = (invitation.published_version.content.get("rsvp") or {}).get("questions") or []
    return render(
        request,
        "portal/guests.html",
        {"inv": invitation, "page": page, "stats": _rsvp_stats(invitation), "filter": shown, "zoek": query, "questions": questions},
    )


@customer_required
@require_POST
def delete_guest(request, uid, response_uid):
    invitation = _own_invitation(request, uid)
    response = get_object_or_404(GuestResponse, invitation=invitation, uid=response_uid)
    name = response.name
    response.delete()
    messages.success(request, f"De aanmelding van {name} is verwijderd.")
    return redirect("portal:guests", uid=invitation.uid)


def _csv_safe(value) -> str:
    text = "" if value is None else str(value)
    # Voorkomt dat spreadsheetprogramma's tekst als formule uitvoeren.
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


def guest_csv(invitation: Invitation) -> HttpResponse:
    questions = []
    if invitation.published_version:
        questions = (invitation.published_version.content.get("rsvp") or {}).get("questions") or []
    buffer = io.StringIO()
    buffer.write("﻿")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["Naam", "Aanwezig", "Aantal personen"] + [q.get("label", "") for q in questions] + ["Toelichting", "Ontvangen op", "Laatst gewijzigd"])
    for response in invitation.responses.order_by("name"):
        answers = {a.get("id"): a.get("value") for a in response.answers or []}
        writer.writerow(
            [_csv_safe(response.name), "ja" if response.attending else "nee", response.persons]
            + [_csv_safe(answers.get(q.get("id"), "")) for q in questions]
            + [_csv_safe(response.remark), timezone.localtime(response.created_at).strftime("%d-%m-%Y %H:%M"),
               timezone.localtime(response.updated_at).strftime("%d-%m-%Y %H:%M")]
        )
    filename = f"gastenlijst-{invitation.slug or invitation.uid}.csv"
    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@customer_required
def guests_export(request, uid):
    return guest_csv(_own_invitation(request, uid))


@customer_required
def qr_code(request, uid, fmt):
    invitation = _own_invitation(request, uid)
    if not invitation.slug or not invitation.is_published:
        raise Http404()
    if fmt == "png":
        response = HttpResponse(qr_png(invitation.public_url), content_type="image/png")
    elif fmt == "svg":
        response = HttpResponse(qr_svg(invitation.public_url), content_type="image/svg+xml")
    else:
        raise Http404()
    if request.GET.get("download") == "1":
        response["Content-Disposition"] = f'attachment; filename="qr-{invitation.slug}.{fmt}"'
    return response


@customer_required
@require_http_methods(["GET", "POST"])
def invitation_delete(request, uid):
    invitation = _own_invitation(request, uid)
    if request.method == "POST":
        if request.POST.get("bevestig") != "verwijderen":
            messages.error(request, "Typ 'verwijderen' om te bevestigen.")
            return redirect("portal:invitation_delete", uid=invitation.uid)
        title = invitation.title or "Je uitnodiging"
        delete_invitation(invitation)
        messages.success(request, f"{title} en alle bijbehorende aanmeldingen en foto's zijn verwijderd.")
        return redirect("portal:home")
    return render(request, "portal/invitation_delete.html", {"inv": invitation, "stats": _rsvp_stats(invitation)})


@customer_required
@require_http_methods(["GET", "POST"])
def account(request):
    if request.method == "POST":
        action = request.POST.get("actie")
        if action == "naam":
            request.user.name = (request.POST.get("name") or "").strip()[:120]
            request.user.save(update_fields=["name"])
            messages.success(request, "Je naam is opgeslagen.")
            return redirect("portal:account")
        if action == "nieuwsbrief":
            from accounts.newsletter import subscribe, unsubscribe

            if request.POST.get("nieuwsbrief") == "ja":
                subscribe(request.user)
                messages.success(request, "Je ontvangt voortaan onze nieuwsbrief. Afmelden kan altijd hier.")
            else:
                unsubscribe(request.user)
                messages.success(request, "Je bent afgemeld voor de nieuwsbrief.")
            return redirect("portal:account")
        if action == "verwijderen":
            if request.POST.get("bevestig") != "verwijderen":
                messages.error(request, "Typ 'verwijderen' om te bevestigen.")
                return redirect("portal:account")
            user = request.user
            logout(request)
            anonymize_user(user)
            messages.success(request, "Je account en gegevens zijn verwijderd. Bestelgegevens bewaren we alleen voor de boekhouding.")
            return redirect("core:home")
    from accounts.newsletter import CONSENT_TEXT

    return render(request, "portal/account.html", {"nieuwsbrief_tekst": CONSENT_TEXT})


# ------------------------------------------------------------ extra wensen

@customer_required
def wishes(request):
    items = CustomRequest.objects.filter(customer=request.user).select_related("invitation").order_by("-updated_at")
    return render(request, "portal/wishes.html", {"wishes": items})


@customer_required
@require_http_methods(["GET", "POST"])
def wish_new(request):
    invitations = Invitation.objects.filter(owner=request.user).order_by("-updated_at")
    initial = {}
    preselect = request.GET.get("uitnodiging", "")
    if preselect and invitations.filter(uid=preselect).exists():
        initial["invitation"] = preselect
    form = WishForm(request.POST or None, request.FILES or None, invitations=invitations, initial=initial)
    if request.method == "POST" and form.is_valid():
        invitation = None
        if form.cleaned_data.get("invitation"):
            invitation = invitations.filter(uid=form.cleaned_data["invitation"]).first()
        try:
            req = create_request(
                customer=request.user,
                invitation=invitation,
                subject=form.cleaned_data["subject"],
                description=form.cleaned_data["description"],
                attachment=form.cleaned_data.get("attachment"),
            )
        except WishError as exc:
            form.add_error("attachment", str(exc))
        else:
            messages.success(request, "Bedankt! We hebben je aanvraag ontvangen en nemen contact met je op. Je krijgt ook een bevestiging per e-mail.")
            return redirect("portal:wish", uid=req.uid)
    return render(request, "portal/wish_new.html", {"form": form})


def _own_wish(request, uid) -> CustomRequest:
    req = get_object_or_404(CustomRequest.objects.select_related("invitation"), uid=uid)
    if req.customer_id != request.user.id:
        raise Http404()
    return req


@customer_required
@require_http_methods(["GET", "POST"])
def wish_detail(request, uid):
    req = _own_wish(request, uid)
    if req.unread_by_customer:
        req.unread_by_customer = False
        req.save(update_fields=["unread_by_customer"])
    form = MessageForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        action = request.POST.get("actie")
        try:
            if action == "akkoord":
                payment = accept_proposal(req, user=request.user)
                if payment is not None:
                    return redirect(payment.checkout_url)
                messages.success(request, "Bedankt voor je akkoord. We gaan aan de slag.")
                return redirect("portal:wish", uid=req.uid)
            if action == "betalen":
                payment = pay_open_proposal(req, user=request.user)
                return redirect(payment.checkout_url)
            if form.is_valid():
                add_message(req, author=request.user, body=form.cleaned_data.get("body") or "", from_staff=False,
                            attachment=form.cleaned_data.get("attachment"))
                messages.success(request, "Je bericht is verstuurd.")
                return redirect("portal:wish", uid=req.uid)
        except (WishError, CheckoutError) as exc:
            messages.error(request, str(exc))
    thread = req.messages.filter(internal=False).select_related("author").prefetch_related("attachments")
    attachments = req.attachments.filter(Q(message__isnull=True) | Q(message__internal=False))
    return render(request, "portal/wish.html", {"req": req, "thread": thread, "form": form, "attachments": attachments})


@customer_required
def wish_attachment(request, uid, attachment_uid):
    req = _own_wish(request, uid)
    attachment = get_object_or_404(req.attachments, uid=attachment_uid)
    if attachment.message_id and attachment.message.internal:
        raise Http404()
    return _attachment_response(attachment)


def _attachment_response(attachment):
    if not attachment.file or not attachment.file.storage.exists(attachment.file.name):
        raise Http404()
    response = FileResponse(attachment.file.open("rb"), content_type=attachment.content_type)
    response["Content-Disposition"] = f'attachment; filename="{attachment.original_name}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response
