"""Gelegenheden en de bijbehorende vragen.

Per gelegenheid staat hier welke naam-/titelvelden gevraagd worden, welke
standaardkop op de uitnodiging staat en welke onderdelen standaard aan staan.
Zo toont de vragenlijst alleen vragen die bij de gelegenheid passen.
"""
from __future__ import annotations

import re

OCCASION_CHOICES = [
    ("bruiloft", "Bruiloft"),
    ("verloving", "Verloving"),
    ("verjaardag", "Verjaardag"),
    ("jubileum", "Jubileum"),
    ("babyshower", "Babyshower"),
    ("zakelijk", "Zakelijk evenement"),
    ("kerst", "Kerst"),
]
OCCASION_LABELS = dict(OCCASION_CHOICES)

# Velden voor namen/titel per gelegenheid: (sleutel, label, verplicht, max_lengte, hulptekst)
OCCASIONS: dict[str, dict] = {
    "bruiloft": {
        "label": "Bruiloft",
        "intro": "Voor jullie trouwdag, van ceremonie tot feest.",
        "name_fields": [
            ("partner_1", "Naam partner 1", True, 60, ""),
            ("partner_2", "Naam partner 2", True, 60, ""),
        ],
        "default_headline": "Wij gaan trouwen",
        "invite_line": "nodigen je van harte uit voor hun bruiloft",
        "story_title": "Ons verhaal",
        "story_default": True,
        "program_hint": "Bijv. 14:00 Ceremonie, 15:30 Toost, 18:00 Diner, 21:00 Feest",
    },
    "verloving": {
        "label": "Verloving",
        "intro": "Vier jullie ja-woord met familie en vrienden.",
        "name_fields": [
            ("partner_1", "Naam partner 1", True, 60, ""),
            ("partner_2", "Naam partner 2", True, 60, ""),
        ],
        "default_headline": "Wij zijn verloofd",
        "invite_line": "nodigen je uit om hun verloving te vieren",
        "story_title": "Hoe het begon",
        "story_default": True,
        "program_hint": "Bijv. 16:00 Ontvangst, 17:00 Toost, 18:00 Buffet",
    },
    "verjaardag": {
        "label": "Verjaardag",
        "intro": "Voor een verjaardag die je niet wilt laten voorbijgaan.",
        "name_fields": [
            ("person_name", "Naam jarige", True, 60, ""),
            ("age", "Leeftijd (optioneel)", False, 3, "Laat leeg als je de leeftijd niet wilt noemen."),
        ],
        "default_headline": "Kom je ook?",
        "invite_line": "nodigt je uit voor een feestje",
        "story_title": "Over de jarige",
        "story_default": False,
        "program_hint": "Bijv. 20:00 Inloop, 20:30 Taart, 22:00 Muziek",
    },
    "jubileum": {
        "label": "Jubileum",
        "intro": "Voor een huwelijks- of bedrijfsjubileum.",
        "name_fields": [
            ("honorees", "Wie vieren het jubileum?", True, 90, "Bijv. Ria & Kees of de naam van een organisatie."),
            ("years", "Aantal jaar (optioneel)", False, 3, ""),
        ],
        "default_headline": "Wij vieren ons jubileum",
        "invite_line": "nodigen je uit om dit bijzondere jubileum te vieren",
        "story_title": "Terugblik",
        "story_default": True,
        "program_hint": "Bijv. 15:00 Ontvangst, 16:00 Woordje, 17:30 Diner",
    },
    "babyshower": {
        "label": "Babyshower",
        "intro": "Een warm welkom voor de kleine die op komst is.",
        "name_fields": [
            ("parents", "Naam (aanstaande) ouder(s)", True, 90, ""),
            ("baby_name", "Naam van de baby (optioneel)", False, 60, "Alleen invullen als die al bekend mag zijn."),
        ],
        "default_headline": "Er is iets kleins op komst",
        "invite_line": "nodigen je uit voor een babyshower",
        "story_title": "Over ons",
        "story_default": False,
        "program_hint": "Bijv. 14:00 Ontvangst, 14:30 Spelletjes, 16:00 Cadeautjes",
    },
    "zakelijk": {
        "label": "Zakelijk evenement",
        "intro": "Voor een lancering, relatie-evenement of zakelijke viering.",
        "name_fields": [
            ("event_title", "Naam van het evenement", True, 90, "Bijv. Jubileumborrel of Productlancering."),
            ("organization", "Organisatie", True, 90, ""),
            ("years", "Aantal jaar (optioneel)", False, 3, "Alleen bij een jubileum, bijv. 10. Sommige ontwerpen zetten dit getal groot in beeld."),
        ],
        "default_headline": "Graag nodigen wij u uit",
        "invite_line": "nodigt u uit",
        "story_title": "Over dit evenement",
        "story_default": False,
        "program_hint": "Bijv. 16:00 Ontvangst, 16:30 Presentatie, 17:30 Netwerkborrel",
        "formal": True,
    },
    # Een kerstkaart is een groet; een kerstdiner, -borrel of -brunch erbij is optioneel.
    # Zonder datum telt de afteller af naar kerst en vervallen locatie, agenda en aanmelden.
    "kerst": {
        "label": "Kerst",
        "intro": "Een warme kerstgroet, met of zonder uitnodiging voor het kerstdiner.",
        "name_fields": [
            ("family", "Van wie komt de kerstkaart?", True, 60, "Bijv. Familie Jansen, of Sanne & Daan."),
            ("members", "Namen eronder (optioneel)", False, 120, "Bijv. Sanne, Daan, Lotte en Siem. Staat klein onder de afzender."),
        ],
        "default_headline": "Warme kerstgroeten",
        "invite_line": "wenst je fijne feestdagen",
        "story_title": "Ons jaar",
        "story_default": True,
        "program_hint": "Bijv. 17:00 Glühwein bij de haard, 18:30 Kerstdiner, 21:00 Cadeautjes onder de boom",
        "event_optional": True,
        # In teksten over de bestelling: "je kerstkaart van Familie Jansen" in plaats van "je uitnodiging voor ...".
        "doc_kind": "kerstkaart",
        "title_prep": "van",
    },
}

# Voorvoegsels die niet in het zegel komen ("Familie Jansen" wordt "J").
_FAMILY_WORDS = {"familie", "fam", "fam.", "gezin", "het", "de", "van", "der", "den", "ten", "ter", "te", "'t", "family", "the"}


def _aangemaakt(template) -> int:
    """De dag (als getal) waarop het ontwerp aan de catalogus is toegevoegd; hoger = nieuwer. Een ontwerp zonder datum telt als oud."""
    moment = getattr(template, "created_at", None)
    if not moment:
        return 0
    from django.utils import timezone

    return timezone.localtime(moment).date().toordinal() if timezone.is_aware(moment) else moment.date().toordinal()


def collectie_volgorde(designs) -> list:
    """De volgorde van de collectie, op één plek: eerst alle Specials, daarna de gewone ontwerpen; binnen elk deel het nieuwst toegevoegde
    ontwerp eerst (op het moment van toevoegen aan de catalogus, `Template.created_at`), bij gelijke tijd de vaste volgorde (`sort_order`, naam).
    Een nieuw Special staat dus automatisch op plek 1. Filtert niets: wie alleen gepubliceerde of passende ontwerpen wil, filtert eerst."""
    def sleutel(t):
        moment = getattr(t, "created_at", None)
        return (0 if getattr(t, "special", False) else 1, -(moment.timestamp() if moment else 0), t.sort_order, t.name)

    return sorted(designs, key=sleutel)


def by_occasion(designs, occasion: str) -> list:
    """De volgorde van de collectie, centraal: eerst de ontwerpen die voor deze gelegenheid zijn gemaakt (eerste in hun lijst), daarna de rest.
    Binnen elk deel staan de nieuwste ontwerpen vooraan (op de dag waarop ze zijn toegevoegd) en de oudere daarna. Een nieuw ontwerp staat dus
    automatisch bovenaan, zonder nummers aan te passen; `sort_order` bepaalt alleen de volgorde van ontwerpen van dezelfde dag.
    Wie de lijst filtert op actief (is_active en een versie) houdt alleen gepubliceerde ontwerpen over."""
    def sleutel(t):
        eerst = 0 if (not occasion or (t.occasions or [""])[0] == occasion) else 1
        return (eerst, -_aangemaakt(t), t.sort_order, t.name)

    return sorted(designs, key=sleutel)


def occasion_config(key: str) -> dict:
    return OCCASIONS.get(key) or OCCASIONS["bruiloft"]


def doc_kind(occasion: str) -> str:
    """Hoe het product heet in teksten: 'kerstkaart' bij Kerst, anders 'uitnodiging'."""
    return occasion_config(occasion).get("doc_kind", "uitnodiging")


def display_title(occasion: str, content: dict) -> str:
    """Leesbare titel van een uitnodiging op basis van de ingevulde namen."""
    n = content.get("names") or {}
    if occasion in ("bruiloft", "verloving"):
        a, b = (n.get("partner_1") or "").strip(), (n.get("partner_2") or "").strip()
        if a and b:
            return f"{a} & {b}"
        return a or b
    if occasion == "verjaardag":
        return (n.get("person_name") or "").strip()
    if occasion == "jubileum":
        return (n.get("honorees") or "").strip()
    if occasion == "babyshower":
        return (n.get("parents") or "").strip()
    if occasion == "zakelijk":
        return (n.get("event_title") or "").strip()
    if occasion == "kerst":
        return (n.get("family") or "").strip()
    return ""


def _kerst_monogram(sender: str) -> str:
    """Zegel van een kerstkaart: 'Familie De Vries' wordt 'V', 'Sanne & Daan' wordt 'S&D'."""
    words = [w for w in re.split(r"[\s-]+", sender) if w]
    if words and words[0].lower().strip(".") in ("familie", "fam", "gezin", "family", "het", "the"):
        rest = [w for w in words if w.lower() not in _FAMILY_WORDS and w[0].isalnum()]
        return rest[0][0].upper() if rest else ""
    parts = [p.strip() for p in re.split(r"\s+(?:&|en|and)\s+|\s*&\s*", sender) if p.strip()]
    if len(parts) == 2 and parts[0][0].isalnum() and parts[1][0].isalnum():
        return f"{parts[0][0].upper()}&{parts[1][0].upper()}"
    return ""


def monogram(occasion: str, content: dict) -> str:
    """Initialen voor het zegel, bijv. 'S&D'."""
    n = content.get("names") or {}
    if occasion in ("bruiloft", "verloving"):
        a, b = (n.get("partner_1") or "").strip(), (n.get("partner_2") or "").strip()
        if a and b:
            return f"{a[0].upper()}&{b[0].upper()}"
        return (a or b or "V")[0].upper()
    if occasion == "kerst":
        found = _kerst_monogram((n.get("family") or "").strip())
        if found:
            return found
    title = display_title(occasion, content)
    letters = [w[0].upper() for w in title.replace("&", " ").split() if w and w[0].isalnum()]
    return "".join(letters[:2]) or "V"
