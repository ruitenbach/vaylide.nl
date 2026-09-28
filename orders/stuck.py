"""Vastgelopen bestellingen voor het beheer: betaald maar niet (op tijd) gepubliceerd of geleverd.

Een bestelling staat hier als:
- de verwerking 'aandacht nodig' heeft (bijv. afwijkend bedrag, dubbele betaling, herhaald mislukt);
- ze betaald is maar na STUCK_MINUTES nog niet gepubliceerd;
- ze gepubliceerd is maar de e-mail met link en QR-code na STUCK_MINUTES nog niet verstuurd (of bewaard in testmodus).
`restart` start de juiste taak opnieuw; dankzij de unieke sleutels ontstaat er nooit een tweede publicatie of e-mail.
"""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from processing.jobs import enqueue, retry
from processing.models import Job, OutboundEmail

from .models import Order

STUCK_MINUTES = 15
DELIVERED = (OutboundEmail.Status.SENT, OutboundEmail.Status.TEST)


def stuck_orders(now=None) -> list[tuple[Order, str]]:
    now = now or timezone.now()
    limit = now - timedelta(minutes=STUCK_MINUTES)
    rows = []
    paid = Order.objects.filter(status=Order.Status.PAID).select_related("customer", "invitation").order_by("-paid_at")
    for order in paid.filter(fulfilment_status=Order.Fulfilment.ATTENTION):
        rows.append((order, order.fulfilment_note or "Aandacht nodig."))
    for order in paid.filter(fulfilment_status__in=[Order.Fulfilment.NONE, Order.Fulfilment.PROCESSING], paid_at__lt=limit):
        rows.append((order, f"Betaald, maar na {STUCK_MINUTES} minuten nog niet gepubliceerd."))
    delivered = OutboundEmail.objects.filter(kind="invitation_live", status__in=DELIVERED).values_list("order_id", flat=True)
    for order in paid.filter(kind=Order.Kind.INVITATION, fulfilment_status=Order.Fulfilment.DONE, paid_at__lt=limit).exclude(pk__in=delivered):
        rows.append((order, "Gepubliceerd, maar de e-mail met link en QR-code is nog niet verstuurd."))
    return rows


def restart(order: Order) -> str:
    """Start de verwerking of de levering opnieuw. Geeft een korte uitleg terug voor het beheer."""
    if order.status != Order.Status.PAID:
        return "Deze bestelling is niet betaald; er is niets te verwerken."
    if order.fulfilment_status == Order.Fulfilment.DONE:
        from .fulfilment import enqueue_delivery

        job = enqueue_delivery(order)
        if job.status in (Job.Status.FAILED, Job.Status.DEAD):
            retry(job)
        email = OutboundEmail.objects.filter(kind="invitation_live", order=order).first()
        email_job = Job.objects.filter(unique_key=f"email:{email.pk}").first() if email else None
        if email_job and email_job.status in (Job.Status.FAILED, Job.Status.DEAD):
            retry(email_job)
        return "Levering opnieuw gestart."
    kind = "fulfil_order" if order.kind == Order.Kind.INVITATION else "fulfil_custom_order"
    job = Job.objects.filter(unique_key=f"{kind}:{order.pk}").first()
    if job is None:
        enqueue(kind, {"order_id": order.pk}, unique_key=f"{kind}:{order.pk}", order=order, invitation=order.invitation)
    elif job.status != Job.Status.RUNNING:
        retry(job)
    return "Verwerking opnieuw gestart."
