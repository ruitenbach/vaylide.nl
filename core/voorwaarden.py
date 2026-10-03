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

# De teksten bij het bestellen. Teksten van de eigenaar (3 oktober 2026), letterlijk gebruikt; de twee toestemmingen worden letterlijk met tijdstip
# vastgelegd op de bestelling en herhaald in de bestelbevestiging. Juridisch nog te beoordelen: zie docs/VOORWAARDEN.md.
CHECKOUT_UITLEG = (
    "Je bestelling bestaat uit de digitale kaart en de online beschikbaarheid daarvan. Omdat je kaart direct na betaling beschikbaar wordt "
    "gemaakt, vragen we hieronder apart toestemming voor directe levering en voor het direct starten van de online dienst."
)
TERMS_CONSENT = "Ik ga akkoord met de algemene voorwaarden van VAYLIDE."
# Digitale kaart (digitale inhoud), artikel 9.2: instemming met levering binnen de bedenktijd en erkenning van het verlies van het herroepingsrecht.
DELIVERY_CONSENT = (
    "Ik stem er uitdrukkelijk mee in dat VAYLIDE mijn digitale kaart direct na de bevestigde betaling levert, dus voordat de wettelijke "
    "bedenktijd is verstreken. Ik erken dat mijn herroepingsrecht voor de digitale kaart vervalt zodra de levering is begonnen."
)
# Online beschikbaarheid (dienst), artikel 9.3: verzoek om te starten tijdens de bedenktijd. Dit vervalt het herroepingsrecht voor de dienst NIET.
SERVICE_CONSENT = (
    "Ik verzoek VAYLIDE om de online beschikbaarheid van mijn uitnodiging direct na de bevestigde betaling te starten, ook als de wettelijke "
    "bedenktijd nog loopt. Ik begrijp dat bij herroeping tijdens de bedenktijd een vergoeding verschuldigd kan zijn voor het deel van de dienst "
    "dat tot dat moment is geleverd."
)


def version_info(version: str | None = None) -> dict:
    version = version or CURRENT
    info = VERSIONS[version]
    return {"version": version, **info}


def filename(version: str | None = None) -> str:
    return f"algemene-voorwaarden-vaylide-{version or CURRENT}.html"


def pdf_filename(version: str | None = None) -> str:
    return f"algemene-voorwaarden-vaylide-{version or CURRENT}.pdf"
