"""Eenvoudig zoeken in de openbare website-inhoud (pagina's, ontwerpen, gelegenheden en vragen).

Zoekt alleen in vaste teksten en actieve ontwerpen; nooit in klantgegevens of uitnodigingen.
"""
from __future__ import annotations

import unicodedata

from django.urls import reverse

from catalog.models import Template
from catalog.occasions import OCCASION_CHOICES

from .content import FAQ, TEXT_SAMPLES

MAX_QUERY = 100
MAX_RESULTS = 30


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def _pages():
    return [
        ("Zo werkt het", reverse("core:how"), "Van ontwerp kiezen tot aanmeldingen beheren, stap voor stap.", "stappen uitleg openingsanimatie afteller programma route agenda delen muziek privé"),
        ("Prijzen", reverse("core:pricing"), "Pakketten en extra opties. Eenmalig betalen, geen kosten per gast.", "kosten pakket essentieel compleet opties betalen ideal"),
        ("Collectie", reverse("core:designs"), "Alle ontwerpen, met een werkend voorbeeld.", "ontwerpen designs voorbeeld"),
        ("Inspiratie", reverse("core:inspiration"), "Voorbeeldteksten en tips voor je uitnodiging.", "tekst tips ideeën dresscode aanmelddatum"),
        ("Over ons", reverse("core:about"), "Waar VAYLIDE voor staat.", "vaylide wie privacy"),
        ("Veelgestelde vragen", reverse("core:faq"), "Antwoorden over aanmelden, betalen en privacy.", "faq vragen hulp"),
        ("Contact", reverse("core:contact"), "Stel je vraag of vertel je bijzondere wens.", "mail maatwerk wens hulp vraag"),
        ("Privacy", reverse("core:privacy"), "Hoe VAYLIDE met gegevens omgaat.", "avg gegevens bewaren verwijderen"),
        ("Voorwaarden", reverse("core:terms"), "De afspraken voor het gebruik van VAYLIDE.", "algemene voorwaarden"),
    ]


def _entries():
    for title, url, text, extra in _pages():
        yield {"kind": "Pagina", "title": title, "url": url, "text": text, "extra": extra}
    designs = Template.objects.filter(is_active=True, current_version__isnull=False)
    for template in designs:
        yield {
            "kind": "Ontwerp",
            "title": template.name,
            "url": reverse("core:design_detail", args=[template.slug]),
            "text": template.description or template.tagline,
            "extra": " ".join([template.tagline, *template.occasion_labels]),
        }
    designs_url = reverse("core:designs")
    for key, label in OCCASION_CHOICES:
        yield {"kind": "Gelegenheid", "title": f"Ontwerpen voor {label.lower()}", "url": f"{designs_url}?gelegenheid={key}",
               "text": f"Digitale uitnodigingen voor een {label.lower()}.", "extra": key}
    faq_url = reverse("core:faq")
    for number, (question, answer) in enumerate(FAQ, start=1):
        yield {"kind": "Vraag", "title": question, "url": f"{faq_url}#vraag-{number}", "text": answer, "extra": ""}
    inspiration_url = reverse("core:inspiration")
    for key, label, sample in TEXT_SAMPLES:
        yield {"kind": "Inspiratie", "title": f"Voorbeeldtekst {label.lower()}", "url": f"{inspiration_url}#tekst-{key}",
               "text": sample, "extra": key}


def search_site(query: str) -> list[dict]:
    words = [w for w in _normalize(query[:MAX_QUERY]).split() if w]
    if not words:
        return []
    ranked = []
    for entry in _entries():
        title = _normalize(entry["title"])
        haystack = " ".join([title, _normalize(entry["text"]), _normalize(entry["extra"])])
        if all(word in haystack for word in words):
            score = sum(2 for word in words if word in title)
            ranked.append((-score, len(ranked), entry))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [entry for _, _, entry in ranked[:MAX_RESULTS]]
