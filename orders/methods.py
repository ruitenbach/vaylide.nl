"""Welke betaalmethoden de website toont (voettekst en bestelstap).

Met Mollie: de methoden die in het Mollie-account aanstaan (opgevraagd bij Mollie en een uur bewaard),
zodat de site nooit een methode belooft die niet werkt. Zonder Mollie, of als Mollie even niet
antwoordt: de lijst uit VIERLIEF_PAYMENT_METHODS (standaard iDEAL en PayPal).
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger(__name__)

LABELS = {
    "ideal": "iDEAL",
    "paypal": "PayPal",
    "creditcard": "Creditcard",
    "bancontact": "Bancontact",
    "applepay": "Apple Pay",
    "banktransfer": "Overboeking",
    "klarna": "Klarna",
    "belfius": "Belfius",
    "kbc": "KBC/CBC",
    "giftcard": "Cadeaukaart",
}
# Volgorde op de site: de bekendste eerst.
ORDER = ["ideal", "paypal", "applepay", "creditcard", "bancontact", "klarna", "banktransfer"]


def _as_list(ids) -> list[dict]:
    seen = []
    for m in ids:
        m = (m or "").strip().lower()
        if m and m not in seen:
            seen.append(m)
    seen.sort(key=lambda m: ORDER.index(m) if m in ORDER else len(ORDER))
    return [{"id": m, "label": LABELS.get(m, m.capitalize())} for m in seen]


def configured_methods() -> list[dict]:
    return _as_list(settings.PAYMENT_METHODS)


def available_methods() -> list[dict]:
    if settings.PAYMENT_PROVIDER != "mollie" or not settings.MOLLIE_API_KEY:
        return configured_methods()
    key = f"betaalmethoden:{settings.MOLLIE_API_KEY[:5]}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    from .providers import MollieProvider, ProviderError

    try:
        data = MollieProvider()._request("GET", "/methods?locale=nl_NL")
        methods = _as_list(m.get("id") for m in (data.get("_embedded") or {}).get("methods") or [])
        if not methods:
            raise ProviderError("geen methoden in het antwoord")
        cache.set(key, methods, 3600)
    except (ProviderError, AttributeError, TypeError) as exc:
        log.warning("Betaalmethoden niet opgehaald bij Mollie: %s", exc)
        methods = configured_methods()
        cache.set(key, methods, 600)
    return methods
