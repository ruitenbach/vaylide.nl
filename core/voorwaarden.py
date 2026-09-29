"""Versies van de algemene voorwaarden.

Elke bestelling legt vast welke versie de klant heeft geaccepteerd (Order.terms_version); die versie blijft
bereikbaar op /voorwaarden/versie/<versie>/ en gaat als bijlage mee met de bestelbevestiging. Een nieuwe tekst krijgt
een nieuwe versie (nieuw sjabloon in core/templates/core/voorwaarden/); een oude versie wijzig je niet meer.
"""
from __future__ import annotations

from datetime import date

CURRENT = "2026-09-29"
VERSIONS = {
    "2026-09-29": {"template": "core/voorwaarden/2026-09-29.html", "date": date(2026, 9, 29), "status": "Concept"},
}

# De afzonderlijke toestemming bij het bestellen (artikel 9.2). Letterlijk vastgelegd op de bestelling en herhaald in de
# bestelbevestiging. Juridisch nog te beoordelen: zie docs/VOORWAARDEN.md.
DELIVERY_CONSENT = (
    "Ik wil dat VAYLIDE direct na de bevestigde betaling begint met de levering van mijn digitale kaart. Ik weet dat ik "
    "daardoor mijn herroepingsrecht voor de digitale kaart (digitale inhoud) verlies zodra de levering begint."
)


def version_info(version: str | None = None) -> dict:
    version = version or CURRENT
    info = VERSIONS[version]
    return {"version": version, **info}


def filename(version: str | None = None) -> str:
    return f"algemene-voorwaarden-vaylide-{version or CURRENT}.html"
