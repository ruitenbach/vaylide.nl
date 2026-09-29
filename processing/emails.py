"""Uitgaande e-mail: opstellen, idempotent in de wachtrij zetten en versturen.

In testmodus (VIERLIEF_EMAIL_MODE=outbox) worden e-mails alleen bewaard en in de
beheeromgeving getoond; er wordt niets echt verzonden.
"""
from __future__ import annotations

import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from catalog.occasions import occasion_config

from .jobs import enqueue
from .models import OutboundEmail

log = logging.getLogger(__name__)


class SimulatedFailure(RuntimeError):
    """Alleen in testmodus: bewust veroorzaakte storing om het herstel te testen."""


def consume_fault(name: str) -> bool:
    """Testmodus: verbruikt een ingestelde storing (zie beheer → Testmodus)."""
    if not settings.TEST_MODE:
        return False
    key = f"vierlief:fault:{name}"
    remaining = cache.get(key, 0)
    if remaining and remaining > 0:
        cache.set(key, remaining - 1, 24 * 3600)
        return True
    return False


def set_fault(name: str, count: int) -> None:
    if settings.TEST_MODE:
        cache.set(f"vierlief:fault:{name}", max(0, count), 24 * 3600)


def get_fault(name: str) -> int:
    return cache.get(f"vierlief:fault:{name}", 0) if settings.TEST_MODE else 0


def absolute(path: str) -> str:
    return f"{settings.BASE_URL}{path}"


def queue_email(*, to: str, subject: str, template: str, context: dict | None = None, unique_key: str | None = None,
                kind: str = "", user=None, order=None, invitation=None, custom_request=None, attach_qr_for=None,
                max_attempts: int = 6, owner_alert: bool = False, attach_terms_version: str = "") -> OutboundEmail:
    if unique_key:
        existing = OutboundEmail.objects.filter(unique_key=unique_key).first()
        if existing:
            return existing
    ctx = {"base_url": settings.BASE_URL, "test_mode": settings.TEST_MODE, **(context or {})}
    body_text = render_to_string(f"emails/{template}.txt", ctx).strip() + "\n"
    body_html = render_to_string("emails/base.html", {**ctx, "body_text": body_text, "subject": subject})
    if settings.TEST_MODE and not subject.startswith("[TEST]"):
        subject = f"[TEST] {subject}"
    email = OutboundEmail.objects.create(
        unique_key=unique_key,
        kind=kind or template,
        to=to,
        subject=subject[:200],
        body_text=body_text,
        body_html=body_html,
        user=user,
        order=order,
        invitation=invitation,
        custom_request=custom_request,
        attach_qr_for=attach_qr_for,
        attach_terms_version=attach_terms_version,
    )
    enqueue(
        "send_email",
        {"email_id": email.pk, "owner_alert": owner_alert},
        unique_key=f"email:{email.pk}",
        order=order,
        invitation=invitation,
        max_attempts=max_attempts,
    )
    return email


def handle_send_email(job) -> None:
    email = OutboundEmail.objects.get(pk=job.payload["email_id"])
    if email.delivered:
        return
    email.attempts += 1
    try:
        if consume_fault("email"):
            raise SimulatedFailure("Gesimuleerde storing bij e-mailverzending (testmodus)")
        if settings.EMAIL_MODE == "outbox":
            email.status = OutboundEmail.Status.TEST
        else:
            message = EmailMultiAlternatives(
                subject=email.subject,
                body=email.body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email.to],
                reply_to=[settings.CONTACT_EMAIL],
            )
            message.attach_alternative(email.body_html, "text/html")
            if email.attach_qr_for_id and email.attach_qr_for.public_url:
                from invitations.qr import qr_png

                message.attach("qr-code-uitnodiging.png", qr_png(email.attach_qr_for.public_url), "image/png")
            if email.attach_terms_version:
                message.attach(*terms_attachment(email.attach_terms_version))
            message.send(fail_silently=False)
            email.status = OutboundEmail.Status.SENT
        email.sent_at = timezone.now()
        email.last_error = ""
        email.save()
    except Exception as exc:
        email.status = OutboundEmail.Status.FAILED
        email.last_error = f"{type(exc).__name__}: {exc}"[:2000]
        email.save()
        raise


# ------------------------------------------------------------ concrete e-mails

def send_login_code(email: str, code: str, link_path: str, *, purpose: str = "login") -> OutboundEmail:
    subject = "Je inlogcode voor VAYLIDE" if purpose == "login" else "Bevestig je e-mailadres voor VAYLIDE"
    return queue_email(
        to=email,
        subject=subject,
        template="login_code",
        context={"code": code, "link": absolute(link_path), "purpose": purpose},
        kind="login_code",
        max_attempts=2,
    )


def send_draft_saved(invitation, user) -> OutboundEmail:
    return queue_email(
        to=user.email,
        subject="Je ontwerp is bewaard",
        template="draft_saved",
        context={"invitation": invitation, "link": absolute(reverse("studio:resume", args=[invitation.uid]))},
        unique_key=f"draft-saved:{invitation.pk}",
        user=user,
        invitation=invitation,
    )


def _kind(invitation) -> dict:
    """'uitnodiging voor …' of, bij een kerstkaart, 'kerstkaart van …'."""
    cfg = occasion_config(invitation.occasion if invitation else "")
    return {"doc_kind": cfg.get("doc_kind", "uitnodiging"), "title_prep": cfg.get("title_prep", "voor")}


def send_order_confirmation(order) -> OutboundEmail:
    """De bewaarbare bestelbevestiging: bedrijfsgegevens, pakket, prijs, aankoop- en einddatum, de toestemming voor
    directe levering en de algemene voorwaarden (versie van de bestelling) als bijlage."""
    from core.voorwaarden import CURRENT, version_info

    version = order.terms_version or CURRENT
    return queue_email(
        to=order.customer.email,
        subject=f"Bevestiging van je bestelling {order.number}",
        template="order_confirmation",
        context={"order": order, "lines": list(order.lines.all()), "portal": absolute(reverse("portal:home")), **_kind(order.invitation),
                 "company": _company_text(), "terms": version_info(version),
                 "terms_url": absolute(reverse("core:terms_version", args=[version])),
                 "withdraw_url": absolute(reverse("orders:withdraw"))},
        unique_key=f"order-confirmation:{order.pk}",
        user=order.customer,
        order=order,
        invitation=order.invitation,
        attach_terms_version=version,
    )


def terms_attachment(version: str) -> tuple[str, str, str]:
    """(bestandsnaam, inhoud, type) van de algemene voorwaarden als bijlage."""
    from django.template.loader import render_to_string

    from core.views import _terms_context
    from core.voorwaarden import filename

    return filename(version), render_to_string("core/terms_download.html", _terms_context(version)), "text/html"


def send_invitation_live(order) -> OutboundEmail:
    invitation = order.invitation
    kind = _kind(invitation)
    return queue_email(
        to=order.customer.email,
        subject=f"Je {kind['doc_kind']} staat online",
        template="invitation_live",
        context={
            "order": order,
            "invitation": invitation,
            "portal": absolute(reverse("portal:invitation", args=[invitation.uid])),
            **kind,
        },
        unique_key=f"invitation-live:{order.pk}",
        user=order.customer,
        order=order,
        invitation=invitation,
        attach_qr_for=invitation,
    )


def send_contact_receipt(msg) -> OutboundEmail:
    return queue_email(
        to=msg.email,
        subject="We hebben je bericht ontvangen",
        template="contact_receipt",
        context={"msg": msg},
        unique_key=f"contact-receipt:{msg.pk}",
    )


def notify_owner_contact(msg) -> OutboundEmail:
    return queue_email(
        to=settings.OWNER_NOTIFY_EMAIL,
        subject=f"Nieuw contactbericht: {msg.get_topic_display()}",
        template="owner_contact",
        context={"msg": msg, "link": absolute(reverse("beheer:contact_messages"))},
        unique_key=f"owner-contact:{msg.pk}",
        owner_alert=True,
    )


def send_wish_received(req) -> OutboundEmail:
    return queue_email(
        to=req.customer.email,
        subject=f"We hebben je aanvraag ontvangen ({req.reference})",
        template="wish_received",
        context={"req": req, "link": absolute(reverse("portal:wish", args=[req.uid]))},
        unique_key=f"wish-received:{req.pk}",
        user=req.customer,
        custom_request=req,
    )


def notify_owner_wish(req) -> OutboundEmail:
    return queue_email(
        to=settings.OWNER_NOTIFY_EMAIL,
        subject=f"Nieuwe extra wens {req.reference}: {req.subject}",
        template="owner_wish",
        context={"req": req, "link": absolute(reverse("beheer:wish", args=[req.uid]))},
        unique_key=f"owner-wish:{req.pk}",
        custom_request=req,
        owner_alert=True,
    )


def send_wish_update(req, *, event_key: str, headline: str) -> OutboundEmail:
    return queue_email(
        to=req.customer.email,
        subject=f"{headline} ({req.reference})",
        template="wish_update",
        context={"req": req, "headline": headline, "link": absolute(reverse("portal:wish", args=[req.uid]))},
        unique_key=f"wish-update:{req.pk}:{event_key}",
        user=req.customer,
        custom_request=req,
    )


def notify_owner_customer_message(req, message) -> OutboundEmail:
    return queue_email(
        to=settings.OWNER_NOTIFY_EMAIL,
        subject=f"Nieuw bericht bij {req.reference}",
        template="owner_wish_message",
        context={"req": req, "message": message, "link": absolute(reverse("beheer:wish", args=[req.uid]))},
        unique_key=f"owner-wish-message:{message.pk}",
        custom_request=req,
        owner_alert=True,
    )


def notify_owner_failure(job) -> OutboundEmail:
    return queue_email(
        to=settings.OWNER_NOTIFY_EMAIL,
        subject=f"Actie nodig: verwerking mislukt ({job.label})",
        template="owner_failure",
        context={"job": job, "link": absolute(reverse("beheer:processing"))},
        unique_key=f"owner-failure:{job.pk}:{job.attempts}",
        owner_alert=True,
        max_attempts=3,
    )


def notify_owner_order_attention(order, reason: str) -> OutboundEmail:
    return queue_email(
        to=settings.OWNER_NOTIFY_EMAIL,
        subject=f"Actie nodig: bestelling {order.number}",
        template="owner_order_attention",
        context={"order": order, "reason": reason, "link": absolute(reverse("beheer:order", args=[order.uid]))},
        unique_key=f"owner-order-attention:{order.pk}:{hashlib.sha1(reason.encode()).hexdigest()[:10]}",
        order=order,
        owner_alert=True,
    )


def send_withdrawal_receipt(w) -> OutboundEmail:
    """Ontvangstbevestiging van een herroeping, met inhoud en datum en tijd (bewaarbaar)."""
    return queue_email(
        to=w.email,
        subject="Ontvangstbevestiging van je herroeping",
        template="herroeping_ontvangen",
        context={"w": w, "company": _company_text()},
        unique_key=f"withdrawal-receipt:{w.pk}",
        order=w.order,
    )


def notify_owner_withdrawal(w) -> OutboundEmail:
    return queue_email(
        to=settings.OWNER_NOTIFY_EMAIL,
        subject=f"Herroeping ontvangen: {w.order_number or w.email}",
        template="owner_herroeping",
        context={"w": w, "link": absolute(reverse("beheer:withdrawals"))},
        unique_key=f"owner-withdrawal:{w.pk}",
        owner_alert=True,
    )


def _company_text() -> str:
    from core.company import as_text

    return as_text()
