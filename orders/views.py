"""Betaalstatus, testbetaling en webhooks."""
from __future__ import annotations

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from catalog.occasions import doc_kind
from processing.models import OutboundEmail

from .models import Order, Payment
from .providers import ProviderError
from .services import CheckoutError, create_payment, sync_payment

log = logging.getLogger(__name__)


def _own_order(request, uid) -> Order:
    order = get_object_or_404(Order.objects.select_related("invitation", "customer"), uid=uid)
    if not request.user.is_authenticated or (order.customer_id != request.user.id and not request.user.is_staff):
        raise Http404()
    return order


def _state(order: Order) -> dict:
    payment = order.latest_payment
    invitation = order.invitation
    live = bool(invitation and invitation.is_publicly_visible and order.status == Order.Status.PAID and order.fulfilment_status == Order.Fulfilment.DONE)
    emails = OutboundEmail.objects.filter(order=order, kind__in=["order_confirmation", "invitation_live"])
    email_state = {e.kind: e.status for e in emails}
    if order.status == Order.Status.PAID:
        phase = "live" if live else ("attention" if order.fulfilment_status == Order.Fulfilment.ATTENTION else "processing")
    elif payment and payment.status in (Payment.Status.FAILED, Payment.Status.EXPIRED):
        phase = "failed"
    elif payment and payment.status == Payment.Status.CANCELED:
        phase = "cancelled"
    elif order.status == Order.Status.CANCELLED:
        phase = "superseded"
    else:
        phase = "waiting"
    return {
        "phase": phase,
        "order_status": order.status,
        "payment_status": payment.status if payment else "",
        "fulfilment": order.fulfilment_status,
        "public_url": invitation.public_url if live else "",
        "confirmation_email": email_state.get("order_confirmation", ""),
        "live_email": email_state.get("invitation_live", ""),
    }


def _maybe_sync(order: Order) -> None:
    """Bij terugkeer van de betaalpagina de status serverzijdig bij de provider nagaan."""
    payment = order.latest_payment
    if payment is None or payment.status in Payment.FINAL or order.status == Order.Status.PAID:
        return
    if (timezone.now() - payment.updated_at).total_seconds() < 3 and payment.status != Payment.Status.OPEN:
        return
    try:
        sync_payment(payment, source="terugkeer")
    except ProviderError as exc:
        log.warning("Statuscontrole bij terugkeer mislukt: %s", exc)


@login_required
def status(request, uid):
    order = _own_order(request, uid)
    _maybe_sync(order)
    order.refresh_from_db()
    state = _state(order)
    kind = doc_kind(order.invitation.occasion) if order.invitation else "uitnodiging"
    payment = order.latest_payment
    from .methods import LABELS

    method_label = LABELS.get((payment.method or "").lower(), "") if payment else ""
    return render(request, "orders/status.html", {"order": order, "state": state, "payment": payment, "doc_kind": kind, "method_label": method_label})


@login_required
def status_json(request, uid):
    order = _own_order(request, uid)
    _maybe_sync(order)
    order.refresh_from_db()
    return JsonResponse(_state(order))


@login_required
@require_POST
def retry_payment(request, uid):
    order = _own_order(request, uid)
    if order.status not in (Order.Status.PENDING, Order.Status.FAILED, Order.Status.EXPIRED):
        messages.error(request, "Deze bestelling kan niet opnieuw worden betaald.")
        return redirect("orders:status", uid=order.uid)
    try:
        payment = create_payment(order)
    except CheckoutError as exc:
        messages.error(request, str(exc))
        return redirect("orders:status", uid=order.uid)
    return redirect(payment.checkout_url)


@require_http_methods(["GET", "POST"])
def test_checkout(request, ref):
    if not settings.TEST_MODE or settings.PAYMENT_PROVIDER != "test":
        raise Http404()
    payment = get_object_or_404(Payment.objects.select_related("order"), provider="test", provider_ref=ref)
    if request.method == "POST":
        outcome = request.POST.get("uitkomst")
        mapping = {
            "betaald": Payment.Status.PAID,
            "mislukt": Payment.Status.FAILED,
            "geannuleerd": Payment.Status.CANCELED,
            "verlopen": Payment.Status.EXPIRED,
            "open": Payment.Status.OPEN,
        }
        if outcome not in mapping:
            messages.error(request, "Kies een uitkomst.")
            return redirect(request.path)
        if payment.status not in Payment.FINAL:
            payment.test_remote_status = mapping[outcome]
            payment.save(update_fields=["test_remote_status", "updated_at"])
            if request.POST.get("webhook") != "uit":
                # Simuleert de melding van de provider aan onze server.
                sync_payment(payment, source="webhook")
        return redirect("orders:status", uid=payment.order.uid)
    return render(request, "orders/test_checkout.html", {"payment": payment, "order": payment.order})


@csrf_exempt
@require_POST
def webhook(request, provider):
    if provider not in ("test", "mollie") or provider != settings.PAYMENT_PROVIDER:
        raise Http404()
    ref = (request.POST.get("id") or "").strip()[:80]
    if not ref:
        return HttpResponse("ontbrekend id", status=400)
    payment = Payment.objects.filter(provider=provider, provider_ref=ref).first()
    if payment is None:
        # Onbekend id: geen informatie prijsgeven.
        return HttpResponse("ok")
    try:
        sync_payment(payment, source="webhook")
    except ProviderError as exc:
        log.error("Webhook-verwerking mislukt voor %s: %s", ref, exc)
        return HttpResponse("tijdelijk niet beschikbaar", status=503)
    return HttpResponse("ok")
