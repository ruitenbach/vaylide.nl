"""Toestemming voor de nieuwsbrief en acties. Altijd via een eigen vinkje dat standaard uit staat (AVG en
Telecommunicatiewet): een vooraf aangevinkt vakje of akkoord met de voorwaarden telt niet als toestemming."""
from __future__ import annotations

from django.utils import timezone

CONSENT_TEXT = "Ja, ik wil de nieuwsbrief met inspiratie, nieuwe ontwerpen en acties van VAYLIDE ontvangen. Afmelden kan altijd."


def subscribe(user, text: str = CONSENT_TEXT) -> None:
    if user.newsletter:
        return
    user.newsletter = True
    user.newsletter_since = timezone.now()
    user.newsletter_consent = text[:300]
    user.save(update_fields=["newsletter", "newsletter_since", "newsletter_consent"])


def unsubscribe(user) -> None:
    if not user.newsletter:
        return
    user.newsletter = False
    user.newsletter_since = None
    user.newsletter_consent = ""
    user.save(update_fields=["newsletter", "newsletter_since", "newsletter_consent"])
