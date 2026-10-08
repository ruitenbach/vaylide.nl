"""Bezoekersanalyse met Microsoft Clarity: alleen na toestemming, alleen op publieke pagina's en de Studio.

Aan of uit via `VIERLIEF_CLARITY_ID` (leeg = uit: geen script, geen banner, geen uitzondering in de Content-Security-Policy).
Het laden zelf, de toestemming (Clarity consentv2) en het intrekken staan in static/js/toestemming.js; de keuze staat in de
noodzakelijke cookie `vaylide_analytics` (12 maanden). Zie docs/CLARITY.md.
"""
from __future__ import annotations

import re

from django.conf import settings

TOESTEMMING_COOKIE = "vaylide_analytics"
CLARITY_ID_PATROON = re.compile(r"^[a-z0-9]{6,20}$")

# De domeinen die Clarity nodig heeft (learn.microsoft.com/clarity/setup-and-installation/clarity-csp): het script komt van
# www.clarity.ms en scripts.clarity.ms, de gegevens gaan naar [a-z].clarity.ms en Microsoft synchroniseert via c.bing.com.
CLARITY_SCRIPT = ("https://www.clarity.ms", "https://*.clarity.ms")
CLARITY_VERBINDING = ("https://*.clarity.ms", "https://c.bing.com")
CLARITY_BEELD = ("https://*.clarity.ms", "https://c.bing.com")

# Waar Clarity mag draaien: homepage, Collectie en ontwerppagina's, Inspiratie, prijzen en de Studio tot en met Bestellen.
_EXACT = {"/", "/inspiratie/", "/prijzen/"}
_PREFIX = ("/ontwerpen/", "/maken/")
# Nooit, ook niet als een pad hierboven past: uitnodigingen van klanten, Mijn VAYLIDE en gastenlijsten, inloggen, beheer, betalen,
# en de losse voorvertoningen van een kaart (de voorbeelden van ontwerpen en, in de Studio, de kaart in het frame met namen en teksten).
# De stap Controleer (/maken/<id>/voorbeeld/) hoort wel bij de Studio; het frame met de kaart erin niet.
_NOOIT = ("/u/", "/account/", "/inloggen/", "/beheer/", "/betalen/", "/bestelling/", "/voorbeeld/")


def clarity_actief() -> bool:
    return bool(settings.CLARITY_ID)


def clarity_op_pagina(path: str) -> bool:
    """Mag Clarity op deze pagina draaien (als de bezoeker toestemming gaf)?"""
    if not clarity_actief():
        return False
    admin = f"/{settings.ADMIN_URL}".rstrip("/") + "/"
    if path.startswith(_NOOIT) or path.startswith(admin) or "/voorbeeld/weergave/" in path or "/voorbeeld/live/" in path or "/media/" in path:
        return False
    return path in _EXACT or path.startswith(_PREFIX)


def csp_bronnen(path: str) -> dict[str, tuple[str, ...]]:
    """Extra bronnen voor de Content-Security-Policy, alleen waar Clarity mag draaien."""
    if not clarity_op_pagina(path):
        return {}
    return {"script-src": CLARITY_SCRIPT, "connect-src": CLARITY_VERBINDING, "img-src": CLARITY_BEELD}
