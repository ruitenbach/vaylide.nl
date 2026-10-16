"""Versies van de algemene voorwaarden.

Elke bestelling legt vast welke versie de klant heeft geaccepteerd (Order.terms_version); die versie blijft
bereikbaar op /voorwaarden/versie/<versie>/ en gaat als bijlage mee met de bestelbevestiging. Een nieuwe tekst krijgt
een nieuwe versie (nieuw sjabloon in core/templates/core/voorwaarden/); een oude versie wijzig je niet meer.
"""
from __future__ import annotations

from datetime import date

# CURRENT is de versie bij de huidige structuur (Essentieel en Compleet). NIEUW hoort bij de nieuwe prijsstructuur (Basis, Luxe, Special;
# VIERLIEF_PRICING_V2). Wat geldt bij het bestellen bepaalt current(): prijzen en voorwaarden gaan zo altijd samen live, en de schakelaar
# terugzetten zet ook de voorwaarden terug. Beide versies blijven bereikbaar; een bestaande bestelling houdt de versie waarop ze is gemaakt.
CURRENT = "2026-09-29"
NIEUW = "2026-10-16"
VERSIONS = {
    "2026-09-29": {"template": "core/voorwaarden/2026-09-29.html", "date": date(2026, 9, 29), "status": "Concept"},
    # Status blijft "Concept" tot de eigenaar de definitieve tekst goedkeurt (dan "Definitief" en vervalt de conceptmelding).
    # strikt: bedrijfsgegevens die de eigenaar niet zelf heeft gezet, verschijnen als invulveld (core/company.py).
    "2026-10-16": {"template": "core/voorwaarden/2026-10-16.html", "date": date(2026, 10, 16), "status": "Concept", "strikt": True},
}


def current() -> str:
    """De versie die nu bij een bestelling hoort: NIEUW met de nieuwe prijsstructuur, anders CURRENT."""
    from django.conf import settings

    return NIEUW if getattr(settings, "PRICING_V2", False) else CURRENT

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


def activation_date() -> date | None:
    """De activeringsdatum van de nieuwe prijzen, alleen als de eigenaar hem als geldige datum (YYYY-MM-DD) heeft gezet (VIERLIEF_ACTIVERINGSDATUM)."""
    from django.conf import settings

    try:
        return date.fromisoformat((getattr(settings, "PRICING_V2_ACTIVATION", "") or "").strip())
    except ValueError:
        return None


def version_info(version: str | None = None) -> dict:
    version = version or current()
    info = VERSIONS[version]
    if version == NIEUW:
        from django.conf import settings

        # Pas "Definitief" als de eigenaar de tekst zelf heeft goedgekeurd (VIERLIEF_TEKSTEN_DEFINITIEF); anders blijft het een concept.
        info = {**info, "status": "Definitief" if getattr(settings, "TEXTS_DEFINITIVE", False) else "Concept"}
    return {"version": version, **info}


def filename(version: str | None = None) -> str:
    return f"algemene-voorwaarden-vaylide-{version or CURRENT}.html"


def pdf_filename(version: str | None = None) -> str:
    return f"algemene-voorwaarden-vaylide-{version or CURRENT}.pdf"
