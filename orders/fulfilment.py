"""Automatische levering na een bevestigde betaling.

Volgorde: bestelling bevestigen → uitnodiging publiceren (met rechten en
beschikbaarheidsduur) → levering aan de koper als aparte taak (e-mail met link en
QR-code). Publiceren en het toekennen van rechten gebeuren in één transactie,
zodat een herhaalde of opnieuw gestarte taak de beschikbaarheid nooit dubbel
verlengt. Alle stappen zijn idempotent (unieke taak- en e-mailsleutels): een
herhaling maakt nooit een tweede publicatie, levering of e-mail.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from invitations.models import Invitation, Source
from invitations.services import availability_end, publish_version, snapshot
from processing.emails import SimulatedFailure, consume_fault, notify_owner_order_attention, send_invitation_live, send_order_confirmation, send_wish_update
from processing.jobs import enqueue

from .models import Order


def enqueue_delivery(order: Order):
    """Levering aan de koper als eigen taak; dezelfde sleutel voorkomt een tweede levering."""
    return enqueue("deliver_order", {"order_id": order.pk}, unique_key=f"deliver_order:{order.pk}", order=order, invitation=order.invitation)


def handle_fulfil_order(job) -> None:
    order = Order.objects.select_related("invitation", "customer").get(pk=job.payload["order_id"])
    if order.status != Order.Status.PAID:
        return
    if order.fulfilment_status == Order.Fulfilment.DONE:
        # Al gepubliceerd (bijv. herhaling na een onderbreking): zorg alleen dat de levering er is.
        enqueue_delivery(order)
        return
    invitation = order.invitation
    if invitation is None:
        _attention(order, "De uitnodiging bij deze betaalde bestelling bestaat niet meer.")
        return
    duplicate = (
        invitation.orders.filter(kind=Order.Kind.INVITATION, status=Order.Status.PAID, fulfilment_status=Order.Fulfilment.DONE)
        .exclude(pk=order.pk)
        .exists()
    )
    if duplicate:
        _attention(order, "Dubbele betaling: deze uitnodiging was al betaald en gepubliceerd. Controleer en betaal zo nodig terug.")
        return

    if order.fulfilment_status == Order.Fulfilment.NONE:
        Order.objects.filter(pk=order.pk).update(fulfilment_status=Order.Fulfilment.PROCESSING, fulfilment_note="")
    send_order_confirmation(order)

    if consume_fault("publish"):
        raise SimulatedFailure("Gesimuleerde storing bij publiceren (testmodus)")

    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        if locked.fulfilment_status == Order.Fulfilment.DONE:
            return
        inv = Invitation.objects.select_for_update().get(pk=invitation.pk)
        now = timezone.now()
        inv.features = sorted(set(inv.features or []) | set(locked.features or []))
        inv.max_gallery_photos = max(inv.max_gallery_photos, locked.max_gallery_photos)
        start = inv.available_until if inv.available_until and inv.available_until > now else now
        inv.save(update_fields=["features", "max_gallery_photos", "updated_at"])
        version = locked.version_to_publish
        if version is None:
            version = snapshot(inv, source=Source.SYSTEM, note="Gepubliceerd na betaling")
        publish_version(inv, version, available_until=availability_end(locked.availability_months, start))
        locked.fulfilment_status = Order.Fulfilment.DONE
        locked.fulfilment_note = ""
        locked.save(update_fields=["fulfilment_status", "fulfilment_note", "updated_at"])

    order.refresh_from_db()
    enqueue_delivery(order)


def handle_deliver_order(job) -> None:
    order = Order.objects.select_related("invitation", "customer").get(pk=job.payload["order_id"])
    if order.status != Order.Status.PAID or order.fulfilment_status != Order.Fulfilment.DONE or order.invitation is None:
        return
    send_invitation_live(order)


def handle_fulfil_custom_order(job) -> None:
    order = Order.objects.select_related("custom_request", "customer").get(pk=job.payload["order_id"])
    if order.status != Order.Status.PAID or order.fulfilment_status == Order.Fulfilment.DONE:
        return
    req = order.custom_request
    send_order_confirmation(order)
    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        if locked.fulfilment_status == Order.Fulfilment.DONE:
            return
        if req is not None:
            from wishes.models import CustomRequest

            CustomRequest.objects.filter(pk=req.pk, status=CustomRequest.Status.AWAITING_PAYMENT).update(
                status=CustomRequest.Status.EXECUTING, unread_by_staff=True, updated_at=timezone.now()
            )
        locked.fulfilment_status = Order.Fulfilment.DONE
        locked.save(update_fields=["fulfilment_status", "updated_at"])
    if req is not None:
        req.refresh_from_db()
        send_wish_update(req, event_key=f"paid:{order.pk}", headline="Betaling ontvangen, we gaan aan de slag")


def _attention(order: Order, reason: str) -> None:
    Order.objects.filter(pk=order.pk).update(fulfilment_status=Order.Fulfilment.ATTENTION, fulfilment_note=reason)
    order.refresh_from_db()
    notify_owner_order_attention(order, reason)
