"""Bestellen, betalen en betalingsmeldingen verwerken.

Kernregels:
- Het bedrag komt uit orders.pricing (serverzijde).
- Een bestelling wordt alleen 'betaald' na een serverzijdige statuscontrole bij
  de provider (webhook of controle bij terugkeer), nooit door de bedankpagina.
- Herhaalde meldingen zijn veilig: een betaalde betaling wordt niet opnieuw
  verwerkt en de verwerkingstaak heeft een unieke sleutel.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from catalog.models import Package
from core.voorwaarden import CURRENT as TERMS_VERSION, DELIVERY_CONSENT, SERVICE_CONSENT
from invitations.content import publish_issues
from invitations.models import Invitation, Source
from invitations.services import snapshot
from processing.jobs import enqueue

from .models import Order, OrderLine, Payment, PaymentEvent
from .pricing import build_quote
from .providers import ProviderError, RemoteStatus, get_provider

log = logging.getLogger(__name__)


class CheckoutError(ValueError):
    pass


def invitation_is_paid(invitation: Invitation) -> bool:
    return invitation.orders.filter(kind=Order.Kind.INVITATION, status=Order.Status.PAID).exists()


def _create_order(**fields) -> Order:
    for _ in range(5):
        try:
            with transaction.atomic():
                return Order.objects.create(number=Order.next_number(), **fields)
        except IntegrityError:
            continue
    raise CheckoutError("De bestelling kon niet worden aangemaakt. Probeer het opnieuw.")


def refresh_open_payments(invitation: Invitation, limit: int = 3) -> None:
    """Vóór een nieuwe betaalpoging: de actuele status van nog openstaande betalingen bij de provider nagaan. Blijkt er
    al een betaald, dan volgt de gewone verwerking en weigert start_checkout een tweede bestelling."""
    open_payments = Payment.objects.filter(
        order__invitation=invitation, order__kind=Order.Kind.INVITATION, order__status=Order.Status.PENDING,
        status__in=[Payment.Status.OPEN, Payment.Status.PENDING],
    ).order_by("-created_at")[:limit]
    for payment in open_payments:
        try:
            sync_payment(payment, source="nieuwe poging")
        except ProviderError as exc:
            log.warning("Status van open betaling %s niet op te halen: %s", payment.pk, exc)


def start_checkout(invitation: Invitation, *, user, package_code: str, optional_codes: list[str], terms_accepted: bool,
                   delivery_consent: bool = False, service_consent: bool = False) -> Payment:
    if not terms_accepted:
        raise CheckoutError("Ga akkoord met de voorwaarden om te bestellen.")
    refresh_open_payments(invitation)
    with transaction.atomic():
        # Altijd de actuele, vergrendelde stand gebruiken (nooit een verouderd object).
        invitation = Invitation.objects.select_for_update().get(pk=invitation.pk)
        if invitation.owner_id != user.id:
            raise CheckoutError("Log in met het e-mailadres waarmee je dit ontwerp hebt bewaard.")
        if invitation_is_paid(invitation):
            raise CheckoutError("Deze uitnodiging is al betaald. Je vindt hem in Mijn VAYLIDE.")
        blocking = [i for i in publish_issues(invitation.draft_content, invitation.occasion, first_publication=True) if i.blocking]
        if blocking:
            raise CheckoutError("Je uitnodiging is nog niet compleet: " + " ".join(i.message for i in blocking))
        package = Package.objects.filter(code=package_code, is_active=True).first()
        if package is None:
            raise CheckoutError("Kies een pakket.")
        quote = build_quote(invitation.draft_content, package, optional_codes, template_version=invitation.template_version)
        # Eerdere, onbetaalde bestellingen voor deze uitnodiging vervallen.
        Order.objects.filter(invitation=invitation, kind=Order.Kind.INVITATION, status__in=[Order.Status.PENDING, Order.Status.FAILED]).update(
            status=Order.Status.CANCELLED
        )
        version = snapshot(invitation, source=Source.CUSTOMER, user=user, note="Besteld")
        order = _create_order(
            kind=Order.Kind.INVITATION,
            customer=user,
            invitation=invitation,
            invitation_title=invitation.title,
            version_to_publish=version,
            package_code=package.code,
            package_name=package.name,
            features=sorted(quote.features),
            max_gallery_photos=quote.max_gallery_photos,
            availability_months=quote.availability_months,
            total_cents=quote.total_cents,
            terms_accepted_at=timezone.now(),
            terms_version=TERMS_VERSION,
            delivery_consent_at=timezone.now() if delivery_consent else None,
            delivery_consent_text=DELIVERY_CONSENT if delivery_consent else "",
            service_consent_at=timezone.now() if service_consent else None,
            service_consent_text=SERVICE_CONSENT if service_consent else "",
            test_mode=settings.TEST_MODE,
        )
        for line in quote.lines:
            OrderLine.objects.create(
                order=order,
                code=line.code,
                description=line.description,
                quantity=line.quantity,
                unit_price_cents=line.unit_price_cents,
                total_cents=line.total_cents,
            )
    return create_payment(order)


def create_custom_order(custom_request, *, user) -> Order:
    order = _create_order(
        kind=Order.Kind.CUSTOM,
        customer=user,
        invitation=custom_request.invitation,
        invitation_title=custom_request.invitation.title if custom_request.invitation else "",
        custom_request=custom_request,
        total_cents=custom_request.proposal_price_cents or 0,
        terms_accepted_at=timezone.now(),
        test_mode=settings.TEST_MODE,
    )
    OrderLine.objects.create(
        order=order,
        code=f"maatwerk:{custom_request.pk}",
        description=f"Maatwerk {custom_request.reference}: {custom_request.subject}"[:200],
        unit_price_cents=order.total_cents,
        total_cents=order.total_cents,
    )
    return order


def create_payment(order: Order) -> Payment:
    if order.status == Order.Status.PAID:
        raise CheckoutError("Deze bestelling is al betaald.")
    try:
        provider = get_provider()
    except ProviderError as exc:
        log.error("Betaalprovider niet beschikbaar voor %s: %s", order.number, exc)
        raise CheckoutError("De betaalomgeving is tijdelijk niet bereikbaar. Je ontwerp is bewaard; probeer het zo opnieuw.") from exc
    payment = Payment.objects.create(order=order, provider=provider.code, amount_cents=order.total_cents, currency=order.currency)
    return_url = f"{settings.BASE_URL}{reverse('orders:status', args=[order.uid])}"
    webhook_url = f"{settings.BASE_URL}{reverse('orders:webhook', args=[provider.code])}"
    try:
        ref, checkout_url = provider.create(payment, description=f"VAYLIDE {order.number}", return_url=return_url, webhook_url=webhook_url)
    except ProviderError as exc:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
        log.error("Betaling aanmaken mislukt voor %s: %s", order.number, exc)
        raise CheckoutError("De betaalomgeving is tijdelijk niet bereikbaar. Je ontwerp is bewaard; probeer het zo opnieuw.") from exc
    payment.provider_ref = ref
    payment.checkout_url = checkout_url
    payment.save()
    if order.status in (Order.Status.FAILED, Order.Status.EXPIRED):
        order.status = Order.Status.PENDING
        order.save(update_fields=["status", "updated_at"])
    return payment


def sync_payment(payment: Payment, *, source: str) -> Payment:
    provider = get_provider(payment.provider)
    remote = provider.fetch(payment)
    return apply_remote_status(payment, remote, source=source)


def apply_remote_status(payment: Payment, remote: RemoteStatus, *, source: str) -> Payment:
    attention_reason = ""
    with transaction.atomic():
        p = Payment.objects.select_for_update().get(pk=payment.pk)
        order = Order.objects.select_for_update().get(pk=p.order_id)
        if source != "webhook" and remote.status == p.status:
            # Eigen statuscontrole (terugkeer, hervatten) zonder verandering: geen nieuwe regel in het beheer.
            # Meldingen van de provider zelf blijven altijd zichtbaar, ook herhaalde.
            return p
        event = PaymentEvent(payment=p, provider=p.provider, provider_ref=p.provider_ref, source=source, remote_status=remote.status)
        if p.status == Payment.Status.PAID:
            event.outcome = "Al verwerkt als betaald; melding genegeerd."
        elif remote.status == Payment.Status.PAID:
            if remote.amount_cents != p.amount_cents or (remote.currency or "EUR") != p.currency:
                order.fulfilment_status = Order.Fulfilment.ATTENTION
                order.fulfilment_note = (
                    f"Bedrag bij de provider ({remote.amount_cents} {remote.currency}) wijkt af van de bestelling ({p.amount_cents} {p.currency})."
                )
                order.save()
                attention_reason = order.fulfilment_note
                event.outcome = "Bedrag wijkt af: niet gepubliceerd, eigenaar ingeschakeld."
            else:
                p.status = Payment.Status.PAID
                p.paid_at = remote.paid_at or timezone.now()
                p.method = remote.method[:40]
                if order.status != Order.Status.PAID:
                    order.status = Order.Status.PAID
                    order.paid_at = p.paid_at
                    order.save()
                    kind = "fulfil_order" if order.kind == Order.Kind.INVITATION else "fulfil_custom_order"
                    enqueue(kind, {"order_id": order.pk}, unique_key=f"{kind}:{order.pk}", order=order, invitation=order.invitation)
                    event.outcome = "Betaald; verwerking gestart."
                else:
                    event.outcome = "Betaald (bestelling was al betaald)."
        elif remote.status in (Payment.Status.FAILED, Payment.Status.CANCELED, Payment.Status.EXPIRED):
            p.status = remote.status
            if order.status == Order.Status.PENDING and not order.payments.exclude(pk=p.pk).filter(
                status__in=[Payment.Status.OPEN, Payment.Status.PENDING, Payment.Status.PAID]
            ).exists():
                order.status = Order.Status.FAILED if remote.status == Payment.Status.FAILED else (
                    Order.Status.EXPIRED if remote.status == Payment.Status.EXPIRED else Order.Status.PENDING
                )
                order.save()
            event.outcome = f"Status bijgewerkt: {p.get_status_display().lower()}."
        else:
            p.status = remote.status
            event.outcome = f"Status bijgewerkt: {p.get_status_display().lower()}."
        p.save()
        event.save()
    if attention_reason:
        from processing.emails import notify_owner_order_attention

        notify_owner_order_attention(order, attention_reason)
    return p
