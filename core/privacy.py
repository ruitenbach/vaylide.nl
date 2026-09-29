"""Verwijderen van klantgegevens, verlopen uitnodigingen en bewaartermijnen.

- Bestellingen blijven bewaard voor de boekhouding (wettelijke bewaarplicht),
  maar zonder namen of omschrijvingen; de koppeling met de verwijderde
  uitnodiging vervalt en het account wordt geanonimiseerd.
- Foto's, muziek, bijlagen, aanmeldingen, versies, bewaarde e-mails, inlogcodes
  en contactberichten van de klant worden echt verwijderd.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

log = logging.getLogger(__name__)


def delete_invitation(invitation) -> None:
    from invitations.models import MediaAsset

    with transaction.atomic():
        for asset in MediaAsset.objects.filter(invitation=invitation):
            asset.delete_files()
        invitation.delete()


def delete_custom_request(req) -> None:
    for attachment in req.attachments.all():
        if attachment.file and attachment.file.name:
            attachment.file.storage.delete(attachment.file.name)
    req.delete()


def anonymize_user(user) -> None:
    from django.db.models import Q

    from accounts.models import LoginCode
    from invitations.models import Invitation
    from orders.models import Order, OrderLine
    from processing.models import OutboundEmail
    from wishes.models import CustomRequest

    from .models import ContactMessage

    email = user.email
    with transaction.atomic():
        # Eerst de e-mails (ook meldingen aan de eigenaar) die over deze klant gaan.
        OutboundEmail.objects.filter(
            Q(user=user) | Q(to__iexact=email) | Q(order__customer=user)
            | Q(invitation__owner=user) | Q(custom_request__customer=user)
        ).delete()
        for invitation in Invitation.objects.filter(owner=user):
            delete_invitation(invitation)
        for req in CustomRequest.objects.filter(customer=user):
            delete_custom_request(req)
        # Bestellingen blijven voor de administratie, zonder namen of omschrijvingen.
        Order.objects.filter(customer=user).update(invitation_title="")
        OrderLine.objects.filter(order__customer=user, code__startswith="maatwerk:").update(
            description="Maatwerk (omschrijving verwijderd)"
        )
        LoginCode.objects.filter(email__iexact=email).delete()
        ContactMessage.objects.filter(email__iexact=email).delete()
        user.email = f"verwijderd-{user.pk}@vaylide.invalid"
        user.name = ""
        user.newsletter, user.newsletter_since, user.newsletter_consent = False, None, ""
        user.is_active = False
        user.set_unusable_password()
        user.anonymized_at = timezone.now()
        user.save()


def _delete_expired_cache(now) -> int:
    from django.conf import settings
    from django.db import connection

    table = settings.CACHES["default"].get("LOCATION")
    if settings.CACHES["default"].get("BACKEND") != "django.core.cache.backends.db.DatabaseCache" or not table:
        return 0
    if table not in connection.introspection.table_names():
        return 0
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {connection.ops.quote_name(table)} WHERE expires < %s", [now])
        return cursor.rowcount


def apply_retention(now=None) -> dict:
    """Voert bewaartermijnen uit. Draai dagelijks: manage.py apply_retention."""
    from accounts.models import LoginCode
    from invitations.models import GuestResponse, Invitation

    from .models import SiteConfig

    now = now or timezone.now()
    config = SiteConfig.get()
    report = {}

    expired = Invitation.objects.filter(status=Invitation.Status.LIVE, available_until__lt=now)
    report["verlopen_uitnodigingen"] = expired.update(status=Invitation.Status.EXPIRED)

    guest_cutoff = now - timedelta(days=config.guest_data_retention_days)
    old_guests = GuestResponse.objects.filter(
        invitation__status__in=[Invitation.Status.EXPIRED, Invitation.Status.OFFLINE],
        invitation__available_until__lt=guest_cutoff,
    )
    report["verwijderde_aanmeldingen"] = old_guests.count()
    old_guests.delete()

    anon_cutoff = now - timedelta(days=config.anonymous_draft_retention_days)
    anon = Invitation.objects.filter(owner__isnull=True, status=Invitation.Status.DRAFT, updated_at__lt=anon_cutoff)
    report["verwijderde_anonieme_concepten"] = anon.count()
    for invitation in anon:
        delete_invitation(invitation)

    draft_cutoff = now - timedelta(days=config.unpaid_draft_retention_days)
    stale = Invitation.objects.filter(owner__isnull=False, status=Invitation.Status.DRAFT, updated_at__lt=draft_cutoff, orders__isnull=True)
    report["verwijderde_oude_concepten"] = stale.count()
    for invitation in stale:
        delete_invitation(invitation)

    # Eigen gezichten: na betaling zijn de geüploade foto's en losse voorbeelden niet meer nodig (de goedgekeurde versie blijft).
    from gezichten.models import FaceRequest
    from orders.models import Order

    paid_invitations = Order.objects.filter(status=Order.Status.PAID).values_list("invitation_id", flat=True)
    cleaned = 0
    for req in FaceRequest.objects.filter(invitation_id__in=paid_invitations).exclude(photo_bride="", photo_groom="", result=""):
        req.delete_files()
        req.save()
        cleaned += 1
    # Onbetaald en 30 dagen niet gebruikt: de foto's en voorbeelden weg (de klant kan opnieuw uploaden).
    stale = FaceRequest.objects.exclude(invitation_id__in=paid_invitations).filter(updated_at__lt=now - timedelta(days=30))
    for req in stale.exclude(photo_bride="", photo_groom="", result=""):
        req.delete_files()
        req.save()
        cleaned += 1
    report["opgeschoonde_gezichtfotos"] = cleaned

    report["verwijderde_inlogcodes"] = LoginCode.objects.filter(created_at__lt=now - timedelta(days=2)).delete()[0]

    # Verlopen sessies (na 30 dagen onbruikbaar) staan anders voor altijd in de database.
    from django.contrib.sessions.models import Session

    report["verwijderde_sessies"] = Session.objects.filter(expire_date__lt=now).delete()[0]

    # Verlopen cachewaarden (o.a. de verkorte IP-codes van de limieten) ruimt de databasecache zelf niet altijd op.
    report["verwijderde_cachewaarden"] = _delete_expired_cache(now)
    return report
