"""Extra wensen: aanvragen, berichten, voorstel, akkoord en betaling.

De klant krijgt bij ontvangst alleen een ontvangstbevestiging. Een voorstel
(met eventuele prijs) komt altijd van de eigenaar; pas na akkoord en de
afgesproken betaling gaat de status naar 'In uitvoering'.
"""
from __future__ import annotations

import re

from django.db import transaction
from django.utils import timezone

from core.ai import AIUnavailable, assess_request
from invitations.images import UploadError, sniff_attachment
from processing.emails import notify_owner_customer_message, notify_owner_wish, send_wish_received, send_wish_update
from processing.jobs import enqueue

from .models import CustomRequest, RequestAttachment, RequestMessage


class WishError(ValueError):
    pass


def _safe_name(name: str) -> str:
    name = re.sub(r"[^\w.\- ]", "_", (name or "bijlage"))[:120]
    return name or "bijlage"


def save_attachment(req: CustomRequest, uploaded, *, user, message: RequestMessage | None = None) -> RequestAttachment:
    try:
        content_type, ext = sniff_attachment(uploaded)
    except UploadError as exc:
        raise WishError(str(exc)) from exc
    attachment = RequestAttachment(
        request=req,
        message=message,
        original_name=_safe_name(uploaded.name),
        content_type=content_type,
        size_bytes=uploaded.size,
        uploaded_by=user,
    )
    attachment.file.save(f"bijlage{ext}", uploaded, save=False)
    attachment.save()
    return attachment


def create_request(*, customer, invitation, subject: str, description: str, attachment=None) -> CustomRequest:
    if attachment is not None:
        # Eerst controleren, zodat er geen half aangemaakte aanvraag ontstaat.
        try:
            sniff_attachment(attachment)
        except UploadError as exc:
            raise WishError(str(exc)) from exc
    with transaction.atomic():
        req = CustomRequest.objects.create(
            customer=customer,
            invitation=invitation,
            subject=subject.strip()[:140],
            description=description.strip()[:4000],
            unread_by_staff=True,
        )
        if attachment is not None:
            save_attachment(req, attachment, user=customer)
        enqueue("assess_request", {"request_id": req.pk}, unique_key=f"assess_request:{req.pk}", invitation=invitation, max_attempts=3)
    send_wish_received(req)
    notify_owner_wish(req)
    return req


def handle_assess_request(job) -> None:
    req = CustomRequest.objects.select_related("invitation__template_version__template").get(pk=job.payload["request_id"])
    context_lines = []
    if req.invitation:
        inv = req.invitation
        context_lines.append(f"Gelegenheid: {inv.get_occasion_display()}")
        context_lines.append(f"Ontwerp: {inv.template_version.template.name}")
        context_lines.append(f"Status uitnodiging: {inv.get_status_display()}")
        if inv.features:
            context_lines.append("Betaalde functies: " + ", ".join(inv.features))
    else:
        context_lines.append("Niet gekoppeld aan een uitnodiging.")
    try:
        assessment, source = assess_request(subject=req.subject, description=req.description, context="\n".join(context_lines))
    except AIUnavailable:
        raise
    CustomRequest.objects.filter(pk=req.pk).update(
        ai_summary=assessment.summary[:2000],
        ai_fit=assessment.fit,
        ai_approach=assessment.approach[:3000],
        ai_questions="\n".join(q.strip() for q in assessment.open_questions if q.strip())[:3000],
        ai_source=source,
        ai_generated_at=timezone.now(),
    )


def add_message(req: CustomRequest, *, author, body: str, from_staff: bool, internal: bool = False, attachment=None) -> RequestMessage:
    body = body.strip()
    if not body and attachment is None:
        raise WishError("Schrijf een bericht of voeg een bestand toe.")
    with transaction.atomic():
        message = RequestMessage.objects.create(request=req, author=author, from_staff=from_staff, internal=internal, body=body[:4000])
        if attachment is not None:
            save_attachment(req, attachment, user=author, message=message)
        if from_staff and not internal:
            req.unread_by_customer = True
        elif not from_staff:
            req.unread_by_staff = True
            if req.status in (CustomRequest.Status.DONE, CustomRequest.Status.CLOSED):
                req.status = CustomRequest.Status.RECEIVED
        req.save()
    if from_staff and not internal:
        send_wish_update(req, event_key=f"msg:{message.pk}", headline="Nieuw bericht van VAYLIDE")
    elif not from_staff:
        notify_owner_customer_message(req, message)
    return message


def send_proposal(req: CustomRequest, *, author, text: str, price_cents: int | None) -> CustomRequest:
    text = text.strip()
    if not text:
        raise WishError("Beschrijf het voorstel.")
    with transaction.atomic():
        req.proposal_text = text[:4000]
        req.proposal_price_cents = price_cents if price_cents else None
        req.proposal_sent_at = timezone.now()
        req.accepted_at = None
        req.status = CustomRequest.Status.PROPOSAL
        req.unread_by_customer = True
        req.save()
        RequestMessage.objects.create(request=req, author=author, from_staff=True, body=f"Voorstel verstuurd:\n\n{req.proposal_text}\n\nPrijs: {req.proposal_price_display}")
    send_wish_update(req, event_key=f"proposal:{int(req.proposal_sent_at.timestamp())}", headline="Je voorstel staat klaar")
    return req


def accept_proposal(req: CustomRequest, *, user):
    """Akkoord van de klant. Geeft een Payment terug als er betaald moet worden, anders None."""
    from orders.services import create_custom_order, create_payment

    if req.status != CustomRequest.Status.PROPOSAL:
        raise WishError("Er staat geen voorstel open om te accepteren.")
    with transaction.atomic():
        req.accepted_at = timezone.now()
        RequestMessage.objects.create(request=req, author=user, from_staff=False, body="Akkoord met het voorstel.")
        if req.proposal_price_cents:
            req.status = CustomRequest.Status.AWAITING_PAYMENT
            req.unread_by_staff = True
            req.save()
            order = create_custom_order(req, user=user)
        else:
            req.status = CustomRequest.Status.EXECUTING
            req.unread_by_staff = True
            req.save()
            order = None
    notify_owner_customer_message(req, req.messages.order_by("-created_at").first())
    if order is not None:
        return create_payment(order)
    return None


def pay_open_proposal(req: CustomRequest, *, user):
    """Opnieuw betalen als de eerdere betaling niet lukte."""
    from orders.models import Order
    from orders.services import create_custom_order, create_payment

    if req.status != CustomRequest.Status.AWAITING_PAYMENT:
        raise WishError("Er staat geen betaling open voor deze aanvraag.")
    order = req.orders.filter(status__in=[Order.Status.PENDING, Order.Status.FAILED, Order.Status.EXPIRED]).order_by("-created_at").first()
    if order is None:
        order = create_custom_order(req, user=user)
    return create_payment(order)


def set_status(req: CustomRequest, status: str, *, author, note: str = "") -> CustomRequest:
    if status not in CustomRequest.Status.values:
        raise WishError("Onbekende status.")
    previous = req.get_status_display()
    req.status = status
    if status == CustomRequest.Status.DONE:
        req.completed_at = timezone.now()
    req.unread_by_customer = True
    req.save()
    body = f"Status gewijzigd van '{previous}' naar '{req.get_status_display()}'."
    if note.strip():
        body += f"\n\n{note.strip()}"
    RequestMessage.objects.create(request=req, author=author, from_staff=True, body=body)
    send_wish_update(req, event_key=f"status:{status}:{int(timezone.now().timestamp())}", headline=f"Status: {req.get_status_display()}")
    return req
