"""Inhoudsschema van een uitnodiging.

De inhoud is een JSON-document dat los staat van het ontwerp. Hetzelfde document
werkt in ieder ontwerp; alleen de kleurvariant is ontwerpspecifiek. Hier staan
de standaardwaarden, het normaliseren van oudere concepten en de controles die
nodig zijn vóór publicatie.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from catalog.occasions import OCCASIONS, occasion_config

SCHEMA_VERSION = 1
MAX_PROGRAM_ITEMS = 20
MAX_PRACTICAL_ITEMS = 10
MAX_QUESTIONS = 5
MAX_DRESSCODE_COLORS = 6
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

TIMEZONES = [
    ("Europe/Amsterdam", "Nederland"),
    ("Europe/Brussels", "België"),
    ("Europe/Luxembourg", "Luxemburg"),
    ("Europe/Berlin", "Duitsland"),
    ("Europe/Paris", "Frankrijk"),
    ("Europe/London", "Verenigd Koninkrijk"),
    ("Europe/Lisbon", "Portugal"),
    ("Europe/Madrid", "Spanje"),
    ("Europe/Rome", "Italië"),
    ("Europe/Athens", "Griekenland"),
    ("Europe/Istanbul", "Turkije"),
    ("Africa/Casablanca", "Marokko"),
    ("America/Curacao", "Curaçao"),
    ("America/Aruba", "Aruba"),
    ("America/Kralendijk", "Bonaire"),
    ("America/Paramaribo", "Suriname"),
    ("America/New_York", "Verenigde Staten (New York)"),
    ("Asia/Dubai", "Verenigde Arabische Emiraten"),
    ("Asia/Jakarta", "Indonesië (Jakarta)"),
    ("Asia/Makassar", "Indonesië (Bali)"),
    ("Asia/Bangkok", "Thailand"),
    ("Australia/Sydney", "Australië (Sydney)"),
]
TIMEZONE_LABELS = dict(TIMEZONES)

SECTION_LABELS = {
    "countdown": "Afteller",
    "story": "Persoonlijk verhaal",
    "gallery": "Fotogalerij",
    "program": "Programma",
    "location": "Locatie en route",
    "dresscode": "Dresscode",
    "practical": "Praktische informatie",
    "rsvp": "Aanmelden",
    "contact": "Contactpersoon",
    "closing": "Afsluiting",
    "music": "Muziek",
}
# Onderdelen die de klant aan/uit kan zetten (locatie staat altijd aan).
TOGGLE_SECTIONS = ["countdown", "story", "gallery", "program", "dresscode", "practical", "rsvp", "contact", "closing", "music"]

QUESTION_TYPES = [("text", "Open vraag"), ("yesno", "Ja/nee"), ("choice", "Keuze uit opties")]


def default_content(occasion: str, palette_key: str = "") -> dict:
    cfg = occasion_config(occasion)
    return {
        "schema": SCHEMA_VERSION,
        "names": {key: "" for key, *_ in cfg["name_fields"]},
        "headline": "",
        # Soort kaart bij gelegenheden met een optioneel evenement (Kerst): "uitnodiging" of "wenskaart".
        # Leeg = zoals vroeger: een uitnodiging zodra er een datum of locatie is ingevuld.
        "soort": "",
        "date": "",
        "start_time": "",
        "end_time": "",
        "timezone": "Europe/Amsterdam",
        "venue_name": "",
        "address": "",
        "route_url": "",
        "welcome_text": "",
        "story": {"title": cfg["story_title"], "text": ""},
        "program": [],
        "dresscode": {"text": "", "colors": []},
        "practical": [],
        "contact": {"name": "", "phone": "", "email": "", "note": ""},
        "rsvp": {
            "deadline": "",
            "max_party_size": 2,
            "capacity": None,
            # Standaard alleen naam, aanwezigheid en aantal personen (keuze eigenaar 30-09-2026, zie invitations/vragen.py).
            "ask_remark": False,
            "remark_label": "Wilt u nog iets laten weten?" if cfg.get("formal") else "Wil je nog iets laten weten?",
            "questions": [],
        },
        "closing_text": "",
        "photos": {"hero": None, "gallery": []},
        "music": {"asset": None, "title": ""},
        # haar: gekozen haarkleuren van het bruidspaar (alleen bij ontwerpen met een paar, zie catalog/paar.py).
        # paar_eigen: goedgekeurde eigen versie van het bruidspaar (upload-id, zie gezichten/).
        # envelop: envelop en lakzegel naar keuze (catalog/envelop.py); envelop.collectie: de Envelope Collection als losse laag om het ontwerp.
        "style": {"palette": palette_key, "opening": True, "haar": {"man": "", "vrouw": ""}, "paar_eigen": "",
                  "envelop": {"kleur": "", "zegel_kleur": "", "zegel": "initialen", "initialen": "", "logo": "",
                              # Envelope Collection (catalog/envelop_collectie.py): envelop ("" = de opening van het ontwerp, "geen" of een stijl),
                              # zegel, teken ("standaard" of "initialen") en initialen. Leeg = het gedrag van bestaande uitnodigingen.
                              "collectie": {"envelop": "", "zegel": "", "teken": "standaard", "initialen": ""}}},
        "sections": {
            "countdown": True,
            "story": bool(cfg.get("story_default")),
            "gallery": False,
            "program": True,
            "dresscode": True,
            "practical": True,
            "rsvp": True,
            "contact": True,
            "closing": True,
            "music": False,
        },
    }


def _merge(defaults: dict, data: dict) -> dict:
    out = copy.deepcopy(defaults)
    for key, value in (data or {}).items():
        if key not in out:
            continue
        if isinstance(out[key], dict) and isinstance(value, dict) and key not in ("names",):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def normalize_content(content: dict | None, occasion: str, palette_key: str = "") -> dict:
    """Vult ontbrekende velden aan (bijv. bij oudere concepten) en verwijdert onbekende."""
    base = default_content(occasion, palette_key)
    merged = _merge(base, content or {})
    # Namenvelden volgen de gelegenheid.
    names = merged.get("names") or {}
    merged["names"] = {key: str(names.get(key) or "") for key, *_ in occasion_config(occasion)["name_fields"]}
    merged["schema"] = SCHEMA_VERSION
    if not merged["style"].get("palette"):
        merged["style"]["palette"] = palette_key
    merged["program"] = [p for p in merged.get("program") or [] if isinstance(p, dict)][:MAX_PROGRAM_ITEMS]
    merged["practical"] = [p for p in merged.get("practical") or [] if isinstance(p, dict)][:MAX_PRACTICAL_ITEMS]
    merged["rsvp"]["questions"] = [q for q in merged["rsvp"].get("questions") or [] if isinstance(q, dict)][:MAX_QUESTIONS]
    colors = merged["dresscode"].get("colors") or []
    merged["dresscode"]["colors"] = [c for c in colors if isinstance(c, str) and HEX_COLOR.match(c)][:MAX_DRESSCODE_COLORS]
    photos = merged.get("photos") or {}
    merged["photos"] = {"hero": photos.get("hero") or None, "gallery": list(photos.get("gallery") or [])}
    return merged


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except (TypeError, ValueError):
        return None


def parse_time(value: str) -> time | None:
    if not value or not TIME_RE.match(value):
        return None
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def get_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name or "Europe/Amsterdam")
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("Europe/Amsterdam")


@dataclass
class EventTimes:
    start: datetime | None  # tijdzonebewust, in de tijdzone van het evenement
    end: datetime | None
    rsvp_deadline: datetime | None  # einde van de deadlinedag in de tijdzone van het evenement
    zone: ZoneInfo


def event_times(content: dict) -> EventTimes:
    zone = get_zone(content.get("timezone"))
    day = parse_date(content.get("date"))
    start_t = parse_time(content.get("start_time")) or (time(0, 0) if day else None)
    start = datetime.combine(day, start_t, tzinfo=zone) if day else None
    end = None
    end_t = parse_time(content.get("end_time"))
    if day and end_t:
        end = datetime.combine(day, end_t, tzinfo=zone)
        if start and end <= start:  # eindigt na middernacht
            end += timedelta(days=1)
    deadline_day = parse_date((content.get("rsvp") or {}).get("deadline"))
    deadline = datetime.combine(deadline_day, time(23, 59, 59), tzinfo=zone) if deadline_day else None
    return EventTimes(start=start, end=end, rsvp_deadline=deadline, zone=zone)


def has_event_details(content: dict) -> bool:
    """Of er iets over een evenement is ingevuld (datum, tijd of locatie)."""
    return any(str(content.get(key) or "").strip() for key in ("date", "start_time", "end_time", "venue_name", "address"))


SOORTEN = ("uitnodiging", "wenskaart")


def card_kind(content: dict, occasion: str) -> str:
    """'uitnodiging' of 'wenskaart'. Alleen gelegenheden met een optioneel evenement (Kerst) kennen een wenskaart;
    zonder expliciete keuze geldt wat er is ingevuld (oudere concepten)."""
    if not occasion_config(occasion).get("event_optional"):
        return "uitnodiging"
    soort = content.get("soort")
    if soort in SOORTEN:
        return soort
    return "uitnodiging" if has_event_details(content) else "wenskaart"


def event_expected(content: dict, occasion: str) -> bool:
    """Hoort er een evenement bij? Bij een wenskaart niet; dan tellen datum, locatie en aanmelden niet mee."""
    return card_kind(content, occasion) == "uitnodiging"


def without_event(content: dict) -> dict:
    """De inhoud zoals een wenskaart hem toont: zonder datum, tijd, locatie en programma. De ingevulde gegevens blijven
    in het concept bewaard, zodat de klant kan terugwisselen naar een uitnodiging."""
    return {**content, "date": "", "start_time": "", "end_time": "", "venue_name": "", "address": "", "route_url": "", "program": []}


@dataclass
class Issue:
    step: str
    field: str
    message: str
    blocking: bool = True


def publish_issues(content: dict, occasion: str, *, first_publication: bool, now: datetime | None = None) -> list[Issue]:
    """Controleert of een uitnodiging compleet genoeg is om te publiceren."""
    from django.utils import timezone as dj_tz

    now = now or dj_tz.now()
    issues: list[Issue] = []
    cfg = OCCASIONS.get(occasion) or occasion_config(occasion)
    names = content.get("names") or {}
    for key, label, required, *_ in cfg["name_fields"]:
        if required and not str(names.get(key) or "").strip():
            issues.append(Issue("gegevens", key, f"Vul '{label}' in."))
    # Een kerstkaart zonder datum en locatie is een groet: dan hoort er geen evenement bij.
    with_event = event_expected(content, occasion)
    if with_event:
        day = parse_date(content.get("date"))
        if not day:
            issues.append(Issue("gegevens", "date", "Vul de datum van het evenement in."))
        if not parse_time(content.get("start_time")):
            issues.append(Issue("gegevens", "start_time", "Vul de begintijd in."))
        if not str(content.get("venue_name") or "").strip():
            issues.append(Issue("gegevens", "venue_name", "Vul de naam van de locatie in."))
        if not str(content.get("address") or "").strip():
            issues.append(Issue("gegevens", "address", "Vul het adres van de locatie in, zodat de routeknop werkt.", blocking=False))
    times = event_times(content if with_event else without_event(content))
    if first_publication and times.start and times.start < now:
        issues.append(Issue("gegevens", "date", "De datum en begintijd liggen in het verleden."))
    sections = content.get("sections") or {}
    if sections.get("rsvp") and with_event:
        rsvp = content.get("rsvp") or {}
        if not parse_date(rsvp.get("deadline")):
            issues.append(Issue("aanmelden", "deadline", "Kies een aanmelddeadline (of zet aanmelden uit)."))
        elif times.start and times.rsvp_deadline and times.rsvp_deadline.date() > times.start.date():
            issues.append(Issue("aanmelden", "deadline", "De aanmelddeadline ligt na de datum van het evenement."))
        elif first_publication and times.rsvp_deadline and times.rsvp_deadline < now:
            issues.append(Issue("aanmelden", "deadline", "De aanmelddeadline ligt in het verleden."))
    if sections.get("music") and not (content.get("music") or {}).get("asset"):
        issues.append(Issue("fotos", "music", "Upload een muziekbestand of zet muziek uit.", blocking=False))
    if sections.get("gallery") and not (content.get("photos") or {}).get("gallery"):
        issues.append(Issue("fotos", "gallery", "Voeg foto's toe aan de galerij of zet de galerij uit.", blocking=False))
    return issues


def referenced_assets(content: dict) -> set[str]:
    """Alle upload-id's waarnaar de inhoud verwijst."""
    uids: set[str] = set()
    photos = content.get("photos") or {}
    hero = photos.get("hero")
    if isinstance(hero, dict) and hero.get("asset"):
        uids.add(str(hero["asset"]))
    for item in photos.get("gallery") or []:
        if isinstance(item, dict) and item.get("asset"):
            uids.add(str(item["asset"]))
    music = content.get("music") or {}
    if music.get("asset"):
        uids.add(str(music["asset"]))
    eigen = ((content.get("style") or {}).get("paar_eigen")) or ""
    if eigen:
        uids.add(str(eigen))
    logo = (((content.get("style") or {}).get("envelop")) or {}).get("logo") or ""
    if logo:
        uids.add(str(logo))
    return uids


def required_features(content: dict) -> set[str]:
    """Welke betaalde functies deze inhoud gebruikt."""
    sections = content.get("sections") or {}
    needed = set()
    if sections.get("story") and ((content.get("story") or {}).get("text") or "").strip():
        needed.add("story")
    if sections.get("gallery") and (content.get("photos") or {}).get("gallery"):
        needed.add("gallery")
    if sections.get("music") and (content.get("music") or {}).get("asset"):
        needed.add("music")
    if sections.get("rsvp") and (content.get("rsvp") or {}).get("questions"):
        needed.add("extra_questions")
    if ((content.get("style") or {}).get("paar_eigen")):
        needed.add("gezichten")
    return needed
