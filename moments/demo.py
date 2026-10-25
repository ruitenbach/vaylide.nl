"""Demonstratiegegevens voor de gastpagina (stap 2). Verzonnen evenement; niets hiervan komt uit de database of gaat ergens heen.

Fotoplaatsen zijn bewust vlakken zonder beeld: er zijn nog geen representatieve feestfoto's met vastgelegde gebruiksrechten.
"""
from __future__ import annotations

import datetime

from django.utils.translation import gettext_lazy as _

from . import limits


def demo_event(package: str = "classic") -> dict:
    pkg = limits.PACKAGES[package]
    return {
        "names": "Anna & Bram",
        "kicker": _("Bruiloft"),
        "date": datetime.date(2027, 6, 12),
        "welcome": _("Fijn dat je erbij bent. Deel wat je vandaag ziet en voelt, wij bewaren het."),
        "photos_max": pkg["photos_per_guest"],
        "videos_max": pkg["videos_per_guest"],
        "video_seconds": pkg["video_seconds"],
        "retention_months": limits.RETENTION_MONTHS,
        "videos": [
            {"kind": _("Een wens"), "question": _("Welke wens heb je voor Anna en Bram?")},
            {"kind": _("Een herinnering"), "question": _("Wat is jouw mooiste herinnering aan jullie samen?")},
        ],
        # Maximaal drie voorbeeldplaatsen; een toon (1 tot 3) kiest de kleur van het vlak.
        "examples": [(1, _("Voorbeeld 1")), (2, _("Voorbeeld 2")), (3, _("Voorbeeld 3"))],
    }
