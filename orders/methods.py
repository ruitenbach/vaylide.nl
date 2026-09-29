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
    "klarnapaylater": "Klarna",
    "klarnasliceit": "Klarna",
    "klarnapaynow": "Klarna",
    "riverty": "Riverty",
    "belfius": "Belfius",
    "kbc": "KBC/CBC",
    "giftcard": "Cadeaukaart",
}
# Logo's zoals aangeleverd door de eigenaar (static/img/betalen/, bijgesneden en verkleind). Zonder logo: de naam.
LOGOS = {
    "ideal": ("img/betalen/ideal.webp", 110, 96),
    "paypal": ("img/betalen/paypal.webp", 97, 96),
}
# Volgorde op de site: de bekendste eerst.
ORDER = ["ideal", "paypal", "applepay", "creditcard", "bancontact", "klarna", "klarnapaylater", "klarnasliceit", "klarnapaynow", "riverty", "banktransfer"]


def _as_list(ids) -> list[dict]:
    allowed = {m.strip().lower() for m in settings.PAYMENT_METHODS_SHOWN}
    seen = []
    for m in ids:
        m = (m or "").strip().lower()
        if m and m not in seen and m in allowed:
            seen.append(m)
    seen.sort(key=lambda m: ORDER.index(m) if m in ORDER else len(ORDER))
    methods = []
    shown = set()
    for m in seen:
        if LABELS.get(m) in shown:
            continue  # bijv. Klarna 'achteraf' en 'in delen': één logo
        shown.add(LABELS.get(m, m))
        logo, width, height = LOGOS.get(m, ("", 0, 0))
        methods.append({"id": m, "label": LABELS.get(m, m.capitalize()), "logo": logo, "width": width, "height": height})
    return methods


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
