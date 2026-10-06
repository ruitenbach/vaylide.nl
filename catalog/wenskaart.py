"""Wenskaart: een kaart met alleen een groet (naam, persoonlijke boodschap, eventueel een foto en de stijl), zonder evenement.

Een wenskaart heeft een vaste prijs, los van de pakketten voor uitnodigingen: € 14,95 per kaart en € 24,95 bij een special-ontwerp,
beide inclusief btw. De prijs staat hier in de code (niet in Beheer → Pakketten): er zit niets in de pakketten of opties van de
uitnodigingen. Een kaart is alleen een wenskaart als de klant dat zelf koos (`soort` = "wenskaart" in de inhoud); een bestaande
uitnodiging wordt nooit vanzelf een wenskaart.
"""
from __future__ import annotations

from .models import Package
from .specials import is_special

CODE = "wenskaart"
CODE_SPECIAL = "wenskaart-special"
PRIJS_CENTS = 1495
PRIJS_SPECIAL_CENTS = 2495
MAANDEN_ONLINE = 6     # zoals Essentieel; de eigenaar kan dit aanpassen

HIGHLIGHTS = [
    "Persoonlijke boodschap, naam en eventueel een foto",
    "Alle ontwerpen en kleurvarianten",
    "Eigen link en QR-code om te delen",
    f"{MAANDEN_ONLINE} maanden online",
]

# Kop en regel onder de naam van een wenskaart, per gelegenheid (Kerst heeft zijn eigen tekst in de ontwerpen).
KOP = {
    "bruiloft": ("Gefeliciteerd", "met jullie bruiloft"),
    "verloving": ("Gefeliciteerd", "met jullie verloving"),
    "verjaardag": ("Gefeliciteerd", "met je verjaardag"),
    "jubileum": ("Gefeliciteerd", "met jullie jubileum"),
    "babyshower": ("Gefeliciteerd", "met de komst van jullie kleintje"),
    "zakelijk": ("Een groet", "met een persoonlijke boodschap"),
}


def is_wenskaart(content: dict | None) -> bool:
    """Alleen op de uitdrukkelijke, opgeslagen keuze van de klant (soort = "wenskaart"); dezelfde regel als invitations.content.card_kind.
    Er wordt niets afgeleid uit de gelegenheid of uit ontbrekende gegevens: een kerstkaart zonder datum is een uitnodiging."""
    return (content or {}).get("soort") == "wenskaart"


def prijs_cents(template_or_version) -> int:
    return PRIJS_SPECIAL_CENTS if is_special(template_or_version) else PRIJS_CENTS


def package(template_or_version) -> Package:
    """Het 'pakket' van een wenskaart: een niet-opgeslagen Package, alleen om de prijsregel en de bestelling te vullen."""
    special = is_special(template_or_version)
    return Package(
        code=CODE_SPECIAL if special else CODE,
        name="Special wenskaart" if special else "Wenskaart",
        description="Een persoonlijke groet in een van onze ontwerpen.",
        price_cents=PRIJS_SPECIAL_CENTS if special else PRIJS_CENTS,
        availability_months=MAANDEN_ONLINE,
        features=[],
        max_gallery_photos=0,
        highlights=HIGHLIGHTS,
        is_active=True,
    )
