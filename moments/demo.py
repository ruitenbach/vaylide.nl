"""Demonstratiegegevens voor de gastpagina (stap 2). Verzonnen evenement; niets hiervan komt uit de database of gaat ergens heen."""
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
        "venue": "Kasteel Test, Utrecht",
        "welcome": _("Jullie zijn erbij, en dat maakt de dag compleet. Deel de mooiste momenten van vandaag met ons."),
        "photos_max": pkg["photos_per_guest"],
        "videos_max": pkg["videos_per_guest"],
        "video_seconds": pkg["video_seconds"],
        "retention_months": limits.RETENTION_MONTHS,
        "questions": [
            _("Welke wens heb je voor Anna en Bram?"),
            _("Wat is jouw mooiste herinnering aan jullie samen?"),
        ],
        "examples": [
            ("img/demo/eucalyptus-1000.webp", _("Voorbeeld: een bos eucalyptus")),
            ("img/demo/bloesemtak-1000.webp", _("Voorbeeld: een bloesemtak")),
            ("img/demo/kaarslicht-1000.webp", _("Voorbeeld: kaarslicht")),
        ],
    }
