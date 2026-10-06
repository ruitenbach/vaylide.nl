"""Betaalstatus, testbetaling en webhooks."""
from __future__ import annotations

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from catalog import wenskaart
from catalog.occasions import doc_kind
from processing.models import OutboundEmail

from .models import Order, Payment
from .providers import ProviderError
from .services import CheckoutError, create_payment, sync_payment

log = logging.getLogger(__name__)

# Wachtscherm: hoe vaak de server de status bij de provider opvraagt (hoogstens eens per SYNC_SECONDS per betaling) en
# na hoeveel seconden een nog openstaande betaling een knop 'Betaling hervatten' krijgt.
SYNC_SECONDS = 10
RESUME_AFTER_SECONDS = 60


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
    elif order.status == Order.Status.CANCELLED:
        phase = "superseded"
    elif payment and payment.status == Payment.Status.FAILED:
        phase = "failed"
    elif payment and payment.status == Payment.Status.EXPIRED:
        phase = "expired"
    elif payment and payment.status == Payment.Status.CANCELED:
        phase = "cancelled"
    else:
        phase = "waiting"
    age = int((timezone.now() - payment.created_at).total_seconds()) if payment else 0
    open_payment = bool(payment and payment.status == Payment.Status.OPEN and payment.checkout_url)
    return {
        "phase": phase,
        "order_status": order.status,
        "payment_status": payment.status if payment else "",
        "fulfilment": order.fulfilment_status,
        "public_url": invitation.public_url if live else "",
        "confirmation_email": email_state.get("order_confirmation", ""),
        "live_email": email_state.get("invitation_live", ""),
        # Wachten: 'open' = de klant heeft de betaalpagina (nog) niet afgerond; 'pending' = de bank verwerkt nog.
        "bank_pending": phase == "waiting" and bool(payment and payment.status == Payment.Status.PENDING),
        "can_resume": phase == "waiting" and open_payment and age >= RESUME_AFTER_SECONDS,
        "resume_after": max(0, RESUME_AFTER_SECONDS - age) if phase == "waiting" and open_payment else -1,
    }


def _maybe_sync(order: Order) -> None:
    """Bij terugkeer van de betaalpagina de status serverzijdig bij de provider nagaan: hoogstens eens per SYNC_SECONDS
    per betaling (het wachtscherm vraagt vaker), en niet meer zodra de betaling afgerond is."""
    payment = order.latest_payment
    if payment is None or payment.status in Payment.FINAL or order.status == Order.Status.PAID:
        return
    if not cache.add(f"betaalcheck:{payment.pk}", 1, SYNC_SECONDS):
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
    greeting = bool(order.invitation) and order.package_code in (wenskaart.CODE, wenskaart.CODE_SPECIAL)
    if greeting and order.invitation.occasion != "kerst":
        kind = "wenskaart"
    payment = order.latest_payment
    from .methods import LABELS

    method_label = LABELS.get((payment.method or "").lower(), "") if payment else ""
    return render(request, "orders/status.html", {"order": order, "state": state, "payment": payment, "doc_kind": kind, "wenskaart": greeting, "method_label": method_label})


@require_http_methods(["GET", "HEAD", "POST"])  # HEAD: controlerobots (zoals die van Mollie) vragen soms alleen de kop op
def withdraw(request):
    """De herroepingsfunctie (art. 6:230oa BW): 'Hier de overeenkomst ontbinden' -> gegevens -> 'Ontbinding bevestigen'.
    Registreert het verzoek en stuurt direct een ontvangstbevestiging; terugbetalen blijft handwerk."""
    from core.utils import form_age_seconds, ip_fingerprint, rate_limit, signed_timestamp

    from .forms import WithdrawalForm
    from .models import Withdrawal

    if request.method == "POST":
        form = WithdrawalForm(request.POST)
        age = form_age_seconds(request.POST.get("form_ts", ""))
        if request.POST.get("website") or age is None or age < 2:
            form.add_error(None, "Je verzoek kon niet worden verwerkt. Vernieuw de pagina en probeer het opnieuw.")
        elif not rate_limit(f"herroepen:{ip_fingerprint(request)}", 10, 3600):
            form.add_error(None, "Je hebt al een aantal verzoeken gestuurd. Probeer het later opnieuw of mail ons.")
        if form.is_valid():
            d = form.cleaned_data
            number = d["order_number"].strip().upper()
            order = Order.objects.filter(number__iexact=number, customer__email__iexact=d["email"]).first() if number else None
            w = Withdrawal.objects.create(order=order, name=d["name"], email=d["email"], order_number=number,
                                          product=d["product"], order_date=d["order_date"], note=d["note"])
            from processing.emails import notify_owner_withdrawal, send_withdrawal_receipt

            send_withdrawal_receipt(w)
            notify_owner_withdrawal(w)
            return redirect("orders:withdraw_done", uid=w.uid)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {"name": request.user.name, "email": request.user.email}
            order = Order.objects.filter(uid=request.GET.get("bestelling") or None, customer=request.user).first() if request.GET.get("bestelling") else None
            if order:
                initial.update({"order_number": order.number, "product": order.package_name or order.invitation_title,
                                "order_date": timezone.localtime(order.paid_at or order.created_at).strftime("%d-%m-%Y")})
        form = WithdrawalForm(initial=initial)
    return render(request, "orders/withdraw.html", {"form": form, "form_ts": signed_timestamp()})


def withdraw_done(request, uid):
    from .models import Withdrawal

    w = get_object_or_404(Withdrawal, uid=uid)
    return render(request, "orders/withdraw_done.html", {"w": w})


@login_required
def status_json(request, uid):
    order = _own_order(request, uid)
    _maybe_sync(order)
    order.refresh_from_db()
    return JsonResponse(_state(order))


@login_required
@require_POST
def retry_payment(request, uid):
    """Betaling hervatten of opnieuw proberen, veilig: eerst de actuele status bij de provider. Staat de betaling nog
    open, dan terug naar dezelfde betaalpagina (geen tweede actieve betaling); verwerkt de bank nog, dan niets nieuws;
    alleen na mislukt, geannuleerd of verlopen een nieuwe betaalpoging."""
    order = _own_order(request, uid)
    if order.status == Order.Status.PAID:
        return redirect("orders:status", uid=order.uid)
    if order.status not in (Order.Status.PENDING, Order.Status.FAILED, Order.Status.EXPIRED):
        messages.error(request, "Deze bestelling kan niet opnieuw worden betaald.")
        return redirect("orders:status", uid=order.uid)
    payment = order.latest_payment
    if payment is not None and payment.status not in Payment.FINAL:
        try:
            payment = sync_payment(payment, source="hervatten")
        except ProviderError as exc:
            log.warning("Status ophalen vóór hervatten mislukt voor %s: %s", order.number, exc)
            messages.error(request, "De betaalomgeving is even niet bereikbaar. Probeer het zo opnieuw; je ontwerp is bewaard.")
            return redirect("orders:status", uid=order.uid)
        order.refresh_from_db()
        if order.status == Order.Status.PAID or payment.status == Payment.Status.PAID:
            return redirect("orders:status", uid=order.uid)
        if payment.status == Payment.Status.OPEN and payment.checkout_url:
            return redirect(payment.checkout_url)
        if payment.status == Payment.Status.PENDING:
            messages.info(request, "Je bank verwerkt de betaling nog. Je hoeft niet opnieuw te betalen; dit scherm werkt zichzelf bij.")
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
