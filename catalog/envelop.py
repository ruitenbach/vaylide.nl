"""Envelop en lakzegel naar keuze (stap Stijl): envelopkleur, zegelkleur, en op het zegel de initialen of een eigen logo.

Keuze van de eigenaar (september 2026): voor alle pakketten, dus ook Essentieel krijgt een persoonlijk zegel.
De envelopkleur overschrijft alleen de kleurvariabelen van het ontwerp (het ontwerp zelf blijft ongewijzigd);
zonder keuze ziet alles eruit zoals het ontwerp het bedoelt.
"""
from __future__ import annotations

import re

# sleutel: (naam, basis, schaduw, inkt voor tekst op de envelop)
ENVELOP_KLEUREN = {
    "ivoor": ("Ivoor", "#F6EFE3", "#E6D8C2", "#5A4630"),
    "zand": ("Zand", "#EAD9BC", "#D7C09A", "#57432B"),
    "blush": ("Blush", "#F2DCD6", "#E3C2BA", "#6B3A3A"),
    "salie": ("Salie", "#DCE4D3", "#C2CFB6", "#3E4E36"),
    "lavendel": ("Lavendel", "#E6DEEE", "#CFC3DE", "#4A3D5E"),
    "hemelsblauw": ("Hemelsblauw", "#DCE6EE", "#C1D0DE", "#2F4256"),
}

# sleutel: (naam, basis, licht, inkt op het zegel)
ZEGEL_KLEUREN = {
    "rood": ("Rood", "#8E1B26", "#BD4650", "#F4D99E"),
    "bordeaux": ("Bordeaux", "#5E1424", "#8A2E43", "#F1D3A8"),
    "groen": ("Groen", "#2C5A3C", "#4F8158", "#F4E3B0"),
    "goud": ("Goud", "#9C7429", "#CFAA58", "#FFF4D6"),
    "zwart": ("Zwart", "#26221F", "#4A4440", "#E9D6A5"),
    "nachtblauw": ("Nachtblauw", "#1F2E4D", "#3C5480", "#F1DDA6"),
    "oudroze": ("Oudroze", "#9C4E5E", "#C27A89", "#FBE3D6"),
}

ZEGEL_INHOUD = {"initialen": "Initialen", "logo": "Eigen logo"}

# Welke kleurvariabelen de envelop van een ontwerp gebruikt. Atelier-ontwerpen delen --a-env.
_ENV_VARS = {
    "liefde-op-papier": lambda b, s, i: {"--lp-envelope": b, "--lp-envelope-2": s},
    "balzaal": lambda b, s, i: {"--bz-env": b, "--bz-env-2": s, "--bz-env-ink": i},
    "winterlicht": lambda b, s, i: {"--wl-env": b},
}
_ATELIER_VARS = lambda b, s, i: {"--a-env": b}  # noqa: E731

# Ontwerpen met een lakzegel maar zonder envelop (de opening is iets anders).
_ZEGEL_ZONDER_ENVELOP = {"eerste-dans"}


# Ontwerpen die zelf de Envelope Collection als opening gebruiken (envelope_mode built_in, {% vx_envelop %} in hun sjabloon).
# Envelop en zegel komen daar uit de collectie; de oude keuzes uit de stap Stijl doen er dus niets, behalve de initialen waar het ontwerp
# ze op het zegel zet. Waarde = de oude keuzes die er wél werken (gecontroleerd in 3 oktober 2026; tests/test_envelop_stijl.py bewaakt de lijst).
# Midnight Émeraude zet de initialen op het zegel; Rosé Royale en Golden Noël hebben een vast zegel (bij Golden Noël komt het veld
# initialen alleen in een sierletter-monogram aan het eind van de kaart terecht, dus niet 'op het zegel').
COLLECTIE_INGEBOUWD = {"midnight-emeraude": {"initialen"}, "rose-royale": set(), "golden-noel": set()}


def zegelkeuzes(template_version) -> dict:
    """Welke keuzes uit het paneel 'Envelop en lakzegel' (stap Stijl) bij dit ontwerp echt iets veranderen. Nooit een keuze tonen die niets doet."""
    werkt = COLLECTIE_INGEBOUWD.get(template_version.template.slug)
    if werkt is not None:
        return {"env_kleur": False, "zegel_kleur": False, "inhoud": False, "logo": False, "initialen": "initialen" in werkt, "vast": True}
    zegel = has_seal(template_version)
    return {"env_kleur": has_envelope(template_version), "zegel_kleur": zegel, "inhoud": zegel, "logo": zegel, "initialen": zegel, "vast": False}


def defaults() -> dict:
    return {"kleur": "", "zegel_kleur": "", "zegel": "initialen", "initialen": "", "logo": ""}


def has_envelope(template_version) -> bool:
    return (template_version.manifest or {}).get("opening") == "envelop"


def has_seal(template_version) -> bool:
    return has_envelope(template_version) or template_version.template.slug in _ZEGEL_ZONDER_ENVELOP


def choice(content: dict) -> dict:
    data = dict(defaults())
    data.update(((content.get("style") or {}).get("envelop")) or {})
    return data


def envelope_vars(template_version, content: dict) -> dict:
    kleur = ENVELOP_KLEUREN.get(choice(content).get("kleur") or "")
    if not kleur or not has_envelope(template_version):
        return {}
    _, base, shade, ink = kleur
    slug = template_version.template.slug
    maker = _ENV_VARS.get(slug) or (_ATELIER_VARS if "atelier" in (template_version.manifest or {}) else None)
    return maker(base, shade, ink) if maker else {}


def seal_colors(content: dict) -> dict | None:
    kleur = ZEGEL_KLEUREN.get(choice(content).get("zegel_kleur") or "")
    if not kleur:
        return None
    _, base, light, ink = kleur
    return {"base": base, "light": light, "ink": ink}


INITIALEN_RE = re.compile(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ&+.·\- ]")


def clean_initials(value: str) -> str:
    """Hoogstens 5 tekens: letters, cijfers en '&', '+', '.', '·' of '-'."""
    return INITIALEN_RE.sub("", (value or "").strip())[:5].strip()
