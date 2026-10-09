"""Vindbaarheid: gestructureerde gegevens (JSON-LD) en de teksten per gelegenheid.

Alleen feiten die ook op de website staan: geen reviews, beoordelingen, klantenaantallen, prijzen, adressen of andere bedrijfsgegevens
(die staan bewust niet in de gegevensblokken). De teksten per gelegenheid zijn rustig en natuurlijk bedoeld, geen opsomming van zoekwoorden.
"""
from __future__ import annotations

import json

from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from .content import OCCASION_TILE_NOTES
from .social import same_as

MERK = "VAYLIDE"
SLOGAN_LANG = "digitale uitnodigingen die je beleeft"

# Titel (zonder het achtervoegsel ' · VAYLIDE') en beschrijving (70 tot 160 tekens) van de pagina per gelegenheid: /ontwerpen/?gelegenheid=<sleutel>.
OCCASION_SEO = {
    "bruiloft": (
        "Digitale trouwuitnodiging voor je bruiloft",
        "Kies een digitale trouwuitnodiging met een eigen opening, afteller, route en aanmelden voor je gasten. Bekijk het werkende voorbeeld.",
    ),
    "verloving": (
        "Digitale uitnodiging voor je verloving",
        "Nodig familie en vrienden uit voor jullie verloving met een digitale uitnodiging die je beleeft. Bekijk de ontwerpen en probeer het voorbeeld.",
    ),
    "verjaardag": (
        "Digitale uitnodiging voor een verjaardag",
        "Een digitale uitnodiging voor een verjaardag, met aanmelden, afteller en route. Kies een ontwerp en bekijk het werkende voorbeeld.",
    ),
    "jubileum": (
        "Digitale uitnodiging voor een jubileum",
        "Een feestelijke digitale uitnodiging voor een jubileum, met aanmelden, afteller en route. Bekijk de ontwerpen en probeer het voorbeeld.",
    ),
    "babyshower": (
        "Digitale uitnodiging voor een babyshower",
        "Een zachte digitale uitnodiging voor een babyshower, met aanmelden, afteller en route. Kies een ontwerp en bekijk het werkende voorbeeld.",
    ),
    "zakelijk": (
        "Digitale uitnodiging voor een zakelijk evenement",
        "Een verzorgde digitale zakelijke uitnodiging met aanmelden, programma en route. Bekijk de ontwerpen en probeer het werkende voorbeeld.",
    ),
    "kerst": (
        "Digitale kerstkaarten en kerstuitnodigingen",
        OCCASION_TILE_NOTES.get("kerst", "") + " Bekijk de ontwerpen en probeer het werkende voorbeeld.",
    ),
}


def design_description(tagline: str, kind: str) -> str:
    """Meta-beschrijving van een ontwerppagina (70 tot 160 tekens): de eigen ondertitel van het ontwerp, daarna een korte zin over wat het is."""
    tagline = (tagline or "").strip().rstrip(".")
    slot = f" Digitale {kind} van VAYLIDE."
    ruimte = 160 - len(slot) - 1
    if len(tagline) > ruimte:
        tagline = tagline[: ruimte - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    tekst = f"{tagline}.{slot}"
    if len(tekst) < 70:
        tekst += " Met aanmelden, afteller en route."
    return tekst


def absolute(path: str) -> str:
    return path if path.startswith("http") else f"{settings.BASE_URL}{path}"


def organization() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{settings.BASE_URL}/#organisatie",
        "name": MERK,
        "url": f"{settings.BASE_URL}/",
        "logo": absolute(static("img/merk/vaylide-logo.png")),
        "sameAs": same_as(),
    }


def website() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": f"{settings.BASE_URL}/#website",
        "name": MERK,
        "url": f"{settings.BASE_URL}/",
        "inLanguage": "nl-NL",
        "publisher": {"@id": f"{settings.BASE_URL}/#organisatie"},
    }


def breadcrumbs(items: list[tuple[str, str]]) -> dict:
    """items: lijst van (naam, pad), van de homepage naar de huidige pagina."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": absolute(path)}
            for i, (name, path) in enumerate(items, start=1)
        ],
    }


def faq_page(pairs: list[tuple[str, str]]) -> dict:
    """FAQPage voor een pagina waarop dezelfde vragen en antwoorden zichtbaar staan (pairs: (vraag, antwoord) in gewone tekst)."""
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs
        ],
    }


def render_json_ld(data: dict) -> str:
    """Veilige <script type="application/ld+json">: een gegevensblok, geen uitvoerbaar script."""
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')
