"""Zet opgeslagen inhoud om naar een weergavemodel voor de ontwerpen.

Het weergavemodel verbergt lege optionele secties, rekent tijden om met de juiste
tijdzone en bepaalt of aanmelden open is. Ontwerpbestanden (designs/*) krijgen
alleen dit model en hoeven zelf geen logica te bevatten.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone as dt_timezone
from urllib.parse import quote, urlencode

from django.templatetags.static import static
from django.utils import timezone

from catalog.effects import effect_view
from catalog.occasions import display_title, doc_kind, monogram, occasion_config

from .content import HEX_COLOR, TIMEZONE_LABELS, card_kind, event_expected, event_times, normalize_content, parse_date, without_event

WEEKDAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MONTHS = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december",
]
ALL_FEATURES = ["story", "gallery", "music", "extra_questions", "zegel"]


def nl_date(d) -> str:
    return f"{WEEKDAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]} {d.year}"


def nl_date_short(d) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def _plural(text: str) -> bool:
    lowered = f" {text.lower()} "
    return " & " in lowered or " en " in lowered or "," in lowered


# Een passend lijntekeningetje per programmaonderdeel (voor ontwerpen die er een tonen), op trefwoord.
PROGRAM_ICONS = [
    ("drank", ("glühwein", "gluhwein", "chocolademelk", "warme chocolade", "ontvangst", "inloop", "borrel", "welkom", "drankje", "aperitief", "thee")),
    ("proost", ("proost", "toost", "champagne", "bubbels", "aftellen", "oud en nieuw", "nieuwjaar", "vuurwerk")),
    ("diner", ("diner", "eten", "buffet", "lunch", "brunch", "gourmet", "hapjes", "gang", "maaltijd", "tafelen", "ontbijt")),
    ("dessert", ("dessert", "toetje", "koffie", "kransjes", "koekjes", "taart", "kerststol", "stol", "bonbons")),
    ("cadeau", ("cadeau", "pakjes", "kado", "surprise", "cadeauspel", "sinterklaas")),
    ("muziek", ("zingen", "liedjes", "muziek", "koor", "concert", "karaoke", "dansen")),
    ("kerk", ("kerk", "nachtmis", "mis ", "viering", "dienst")),
    ("haard", ("haard", "verhalen", "voorlezen", "film", "bank")),
    ("boom", ("boom", "optuigen", "versieren")),
    ("wandeling", ("wandel", "schaatsen", "sneeuw", "buiten", "lichtjesroute", "kerstmarkt", "slee")),
]
PROGRAM_ICON_FALLBACK = ["ster", "bel", "kaars", "kerstbal"]


def program_icon(title: str, index: int) -> str:
    lowered = f" {title.lower()} "
    for icon, words in PROGRAM_ICONS:
        if any(word in lowered for word in words):
            return icon
    return PROGRAM_ICON_FALLBACK[index % len(PROGRAM_ICON_FALLBACK)]


def new_year(day, now) -> int:
    """Het nieuwe jaar bij een kerstkaart: vanaf juli het volgende jaar, tot en met juni het lopende."""
    ref = day or timezone.localtime(now).date()
    return ref.year + 1 if ref.month >= 7 else ref.year


def christmas_target(zone, now):
    """Eerste kerstdag (00:00) om naar af te tellen, alleen van juli tot en met kerstavond."""
    today = now.astimezone(zone).date()
    if today.month < 7 or (today.month == 12 and today.day > 24):
        return None
    return datetime(today.year, 12, 25, tzinfo=zone)


class AssetResolver:
    """Bepaalt de URL van foto's en muziek per weergavemodus."""

    def __init__(self, assets: dict | None = None):
        self.assets = assets or {}

    def url(self, uid: str, variant: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def meta(self, uid: str):
        return self.assets.get(str(uid))


class PathResolver(AssetResolver):
    def __init__(self, base_path: str, assets: dict):
        super().__init__(assets)
        self.base_path = base_path.rstrip("/")

    def url(self, uid: str, variant: str) -> str:
        return f"{self.base_path}/{uid}/{variant}/"


@dataclass
class Photo:
    src: str
    src_small: str
    x: float = 50
    y: float = 50
    zoom: float = 1.0
    alt: str = ""
    caption: str = ""
    width: int | None = None
    height: int | None = None

    @property
    def style(self) -> str:
        style = f"object-position:{self.x:.1f}% {self.y:.1f}%;"
        if self.zoom and self.zoom > 1.001:
            style += f"transform:scale({self.zoom:.3f});transform-origin:{self.x:.1f}% {self.y:.1f}%;"
        return style

    @property
    def orientation(self) -> str:
        if not self.width or not self.height:
            return "liggend"
        ratio = self.width / self.height
        return "liggend" if ratio > 1.15 else ("staand" if ratio < 0.87 else "vierkant")


def _clamp(value, low, high, default):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def resolve_photo(ref, resolver: AssetResolver | None, alt: str) -> Photo | None:
    if not isinstance(ref, dict):
        return None
    x = _clamp(ref.get("x"), 0, 100, 50)
    y = _clamp(ref.get("y"), 0, 100, 50)
    zoom = _clamp(ref.get("zoom"), 1, 3, 1)
    caption = str(ref.get("caption") or "")[:140]
    if ref.get("static"):
        path = static(ref["static"])
        small = static(ref["static_small"]) if ref.get("static_small") else path
        return Photo(path, small, x, y, zoom, ref.get("alt") or alt, caption, ref.get("w"), ref.get("h"))
    uid = ref.get("asset")
    if not uid or resolver is None:
        return None
    meta = resolver.meta(uid)
    if meta is None:
        return None
    return Photo(
        resolver.url(uid, "groot"),
        resolver.url(uid, "middel"),
        x,
        y,
        zoom,
        alt,
        caption,
        getattr(meta, "width", None),
        getattr(meta, "height", None),
    )


@dataclass
class RenderOptions:
    mode: str  # "live", "preview" of "demo"
    features: list[str] = field(default_factory=lambda: list(ALL_FEATURES))
    max_gallery_photos: int = 12
    resolver: AssetResolver | None = None
    share_url: str = ""
    ics_url: str = ""
    rsvp_action: str = ""
    responses_count_persons: int = 0
    now: datetime | None = None
    existing_response: object | None = None
    music_synth: bool = False
    embed: bool = False


# Standaard lakzegel (zonder de functie 'zegel'): een motief in plaats van initialen, in rood of in groen.
SEAL_COLORS = {
    "rood": {"base": "#8E1B26", "light": "#BD4650", "ink": "#F4D99E"},
    "groen": {"base": "#2C5A3C", "light": "#4F8158", "ink": "#F4E3B0"},
}
GREEN_PALETTE_WORDS = ("salie", "groen", "smaragd", "eucalyptus", "mint", "olijf", "dennen", "hulst", "jungle")


def seal_color(palette_key: str) -> str:
    """Rood, of groen bij een groene kleurvariant."""
    key = (palette_key or "").lower()
    return "groen" if any(w in key for w in GREEN_PALETTE_WORDS) else "rood"


def _paragraphs(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _google_calendar_url(title, start, end, location, details) -> str:
    fmt = "%Y%m%dT%H%M%SZ"
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start.astimezone(dt_timezone.utc).strftime(fmt)}/{end.astimezone(dt_timezone.utc).strftime(fmt)}",
        "location": location,
        "details": details,
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(params, quote_via=quote)


def build_view(
    *,
    occasion: str,
    content: dict,
    overrides: dict | None,
    template_version,
    options: RenderOptions,
) -> dict:
    overrides = overrides or {}
    palette_key = (content.get("style") or {}).get("palette") or template_version.default_palette_key
    content = normalize_content(content, occasion, palette_key)
    if not event_expected(content, occasion):
        content = without_event(content)
    cfg = occasion_config(occasion)
    now = options.now or timezone.now()
    features = set(options.features)
    formal = bool(cfg.get("formal"))
    names_raw = content["names"]

    title = display_title(occasion, content) or cfg["label"]
    # Namen en koptekst per gelegenheid.
    if occasion in ("bruiloft", "verloving"):
        names = [n for n in (names_raw.get("partner_1", "").strip(), names_raw.get("partner_2", "").strip()) if n]
        kicker = cfg["default_headline"]
        tagline = cfg["invite_line"]
    elif occasion == "verjaardag":
        names = [names_raw.get("person_name", "").strip()]
        age = names_raw.get("age", "").strip()
        kicker = f"{age} jaar" if age else "Feest"
        tagline = f"wordt {age} en nodigt je uit om dat te vieren" if age else cfg["invite_line"]
    elif occasion == "jubileum":
        honorees = names_raw.get("honorees", "").strip()
        names = [honorees]
        years = names_raw.get("years", "").strip()
        kicker = f"{years} jaar" if years else "Jubileum"
        if _plural(honorees):
            tagline = (
                f"vieren hun {years}-jarig jubileum en nodigen je van harte uit"
                if years
                else "nodigen je uit om hun jubileum te vieren"
            )
        else:
            tagline = (
                f"viert het {years}-jarig jubileum en nodigt je van harte uit"
                if years
                else "nodigt je uit om het jubileum te vieren"
            )
    elif occasion == "babyshower":
        parents = names_raw.get("parents", "").strip()
        names = [parents]
        baby = names_raw.get("baby_name", "").strip()
        kicker = "Babyshower"
        verb = "nodigen" if _plural(parents) else "nodigt"
        tagline = f"{verb} je uit voor de babyshower van {baby}" if baby else f"{verb} je uit voor een babyshower"
    elif occasion == "kerst":
        family = names_raw.get("family", "").strip()
        names = [family]
        kicker = cfg["default_headline"]
        verb = "wensen" if _plural(family) else "wenst"
        tagline = f"{verb} je fijne feestdagen en een gelukkig {new_year(parse_date(content.get('date')), now)}"
    else:  # zakelijk
        names = [names_raw.get("event_title", "").strip()]
        organization = names_raw.get("organization", "").strip()
        kicker = organization or "Uitnodiging"
        tagline = f"{organization} nodigt u graag uit" if organization else "Graag nodigen wij u uit"
    names = [n for n in names if n] or [title]
    # Groot getal voor ontwerpen die de leeftijd of het aantal jaren uitlichten.
    number = ""
    if occasion == "verjaardag":
        number = names_raw.get("age", "").strip()
    elif occasion in ("jubileum", "zakelijk"):
        number = names_raw.get("years", "").strip()
    number = number if number.isdigit() and len(number) <= 3 else ""
    longest = max(len(n) for n in names)
    longest_word = max((len(w) for n in names for w in re.split(r"[\s-]+", n) if w), default=0)
    names_size = "xlong" if longest > 18 or longest_word > 15 else ("long" if longest > 11 else "normal")
    headline = (overrides.get("headline") or content.get("headline") or "").strip()
    if headline:
        kicker = headline

    times = event_times(content)
    start, end = times.start, times.end
    day = parse_date(content.get("date"))
    is_past = bool(start and (end or start + timedelta(hours=6)) < now)
    with_event = event_expected(content, occasion)
    # Kerstkaart zonder evenement: aftellen naar eerste kerstdag (van juli tot en met kerstavond).
    countdown_target, countdown_label = start, ""
    if start is None and cfg.get("event_optional"):
        countdown_target, countdown_label = christmas_target(times.zone, now), "kerst"
    days_until = None
    countdown = None
    if countdown_target and countdown_target > now:
        delta = countdown_target - now
        days_until = delta.days
        countdown = {
            "days": delta.days,
            "hours": delta.seconds // 3600,
            "minutes": (delta.seconds % 3600) // 60,
            "seconds": delta.seconds % 60,
        }
    tz_name = content.get("timezone") or "Europe/Amsterdam"
    tz_label = TIMEZONE_LABELS.get(tz_name, tz_name)
    time_display = ""
    if content.get("start_time"):
        time_display = content["start_time"]
        if content.get("end_time"):
            time_display += f" – {content['end_time']}"
        time_display += " uur"

    venue = (content.get("venue_name") or "").strip()
    address = (content.get("address") or "").strip()
    address_lines = [line.strip() for line in address.splitlines() if line.strip()]
    route_url = (content.get("route_url") or "").strip()
    if not route_url.startswith("https://"):
        route_url = ""
    if not route_url and (venue or address):
        route_url = "https://www.google.com/maps/search/?api=1&query=" + quote(", ".join([venue] + address_lines))

    sections = content["sections"]
    hidden = set(overrides.get("hide_sections") or [])

    def enabled(key: str) -> bool:
        return bool(sections.get(key)) and key not in hidden

    resolver = options.resolver
    hero = resolve_photo(content["photos"].get("hero"), resolver, f"Foto bij de uitnodiging van {title}")
    gallery = []
    if "gallery" in features:
        for i, ref in enumerate(content["photos"].get("gallery") or []):
            if len(gallery) >= options.max_gallery_photos:
                break
            photo = resolve_photo(ref, resolver, f"Foto {i + 1} van {title}")
            if photo:
                gallery.append(photo)

    program = []
    for item in content.get("program") or []:
        item_title = str(item.get("title") or "").strip()
        if not item_title:
            continue
        program.append(
            {
                "time": str(item.get("time") or "").strip()[:5],
                "title": item_title[:80],
                "description": str(item.get("description") or "").strip()[:300],
                "icon": program_icon(item_title, len(program)),
            }
        )
    practical = [
        {"title": str(p.get("title") or "").strip()[:60], "text": str(p.get("text") or "").strip()[:600]}
        for p in content.get("practical") or []
        if str(p.get("title") or "").strip() or str(p.get("text") or "").strip()
    ]
    dresscode = content.get("dresscode") or {}
    contact = content.get("contact") or {}
    phone = re.sub(r"[^\d+]", "", contact.get("phone") or "")
    story = content.get("story") or {}
    rsvp_cfg = content.get("rsvp") or {}

    music_url = ""
    music_title = (content.get("music") or {}).get("title", "")
    music_asset = (content.get("music") or {}).get("asset")
    if music_asset and resolver and resolver.meta(music_asset):
        music_url = resolver.url(music_asset, "audio")

    show = {
        "countdown": enabled("countdown") and (start is not None or countdown is not None),
        "story": enabled("story") and "story" in features and bool(_paragraphs(story.get("text"))),
        "gallery": enabled("gallery") and bool(gallery),
        "program": enabled("program") and bool(program),
        "location": bool(venue or address),
        "dresscode": enabled("dresscode") and bool((dresscode.get("text") or "").strip() or dresscode.get("colors")),
        "practical": enabled("practical") and bool(practical),
        "rsvp": enabled("rsvp") and with_event,
        "contact": enabled("contact")
        and bool((contact.get("name") or "").strip())
        and bool(phone or (contact.get("email") or "").strip() or (contact.get("note") or "").strip()),
        "closing": enabled("closing") and bool((content.get("closing_text") or "").strip()),
        "music": enabled("music") and "music" in features and (bool(music_url) or options.music_synth),
    }
    # Een wenskaart is alleen een groet: geen dresscode, 'Goed om te weten' of 'Vragen' (programma, locatie en
    # aanmelden vallen al weg omdat er geen evenement is).
    if not with_event and cfg.get("event_optional"):
        for key in ("dresscode", "practical", "contact"):
            show[key] = False

    # Aanmelden: deadline, verstreken datum en maximale capaciteit.
    rsvp_deadline = times.rsvp_deadline
    capacity = rsvp_cfg.get("capacity")
    try:
        capacity = int(capacity) if capacity not in (None, "") else None
    except (TypeError, ValueError):
        capacity = None
    closed_reason = ""
    if is_past:
        closed_reason = "past"
    elif rsvp_deadline and rsvp_deadline < now:
        closed_reason = "deadline"
    elif capacity and options.responses_count_persons >= capacity:
        closed_reason = "full"
    try:
        max_party = max(1, min(20, int(rsvp_cfg.get("max_party_size") or 1)))
    except (TypeError, ValueError):
        max_party = 1
    questions = []
    if "extra_questions" in features:
        for q in rsvp_cfg.get("questions") or []:
            label = str(q.get("label") or "").strip()
            if not label:
                continue
            qtype = q.get("type") if q.get("type") in ("text", "yesno", "choice") else "text"
            opts = [str(o).strip()[:60] for o in (q.get("options") or []) if str(o).strip()][:8]
            if qtype == "choice" and len(opts) < 2:
                qtype = "text"
            qid = re.sub(r"[^a-z0-9]", "", str(q.get("id") or "").lower())[:12]
            if not qid:
                continue
            questions.append(
                {"id": qid, "field": f"q_{qid}", "label": label[:140], "type": qtype, "options": opts,
                 "required": bool(q.get("required"))}
            )

    palette = template_version.palette(palette_key)
    css_vars = dict(palette.get("vars") or {})
    for key, value in (overrides.get("css_vars") or {}).items():
        if key in css_vars and isinstance(value, str) and (HEX_COLOR.match(value) or value.startswith("rgba(")):
            css_vars[key] = value
    palette_style = "".join(f"{k}:{v};" for k, v in css_vars.items())

    location_text = ", ".join([venue] + address_lines)
    calendar = None
    if start:
        cal_end = end or start + timedelta(hours=4)
        details = f"Uitnodiging: {options.share_url}" if options.share_url else "Uitnodiging via Vaylide"
        calendar = {
            "google": _google_calendar_url(title, start, cal_end, location_text, details),
            "ics": options.ics_url,
        }
    share_text = f"{title} – {nl_date_short(day) if day else ''}".strip(" –")
    whatsapp_url = ""
    if options.share_url:
        whatsapp_url = "https://wa.me/?text=" + quote(f"{share_text}\n{options.share_url}")

    return {
        "mode": options.mode,
        "is_live": options.mode == "live",
        "is_preview": options.mode == "preview",
        "is_demo": options.mode == "demo",
        "embed": options.embed,
        "formal": formal,
        "occasion": occasion,
        "occasion_label": cfg["label"],
        "title": title,
        "page_title": f"{title} · {doc_kind(occasion)}",
        "doc_kind": doc_kind(occasion),
        "names": names,
        # Kleine regel onder de namen (bij een kerstkaart: de namen van het gezin).
        "subnames": (names_raw.get("members") or "").strip() if occasion == "kerst" else "",
        "has_event": with_event,
        "card_kind": card_kind(content, occasion),
        "is_couple": len(names) == 2,
        "names_size": names_size,
        "number": number,
        "kicker": kicker,
        "headline_custom": bool(headline),
        "tagline": tagline,
        "monogram": monogram(occasion, content),
        # Lakzegel: initialen alleen met de functie 'zegel' (Compleet); anders een standaardmotief in rood of groen.
        "seal_personal": "zegel" in features,
        "seal_color": seal_color(palette_key),
        "seal_std": SEAL_COLORS[seal_color(palette_key)],
        "welcome": _paragraphs(content.get("welcome_text")),
        "date": day,
        "date_display": nl_date(day) if day else "",
        "date_short": nl_date_short(day) if day else "",
        "date_numeric": day.strftime("%d · %m · %Y") if day else "",
        "weekday": WEEKDAYS[day.weekday()] if day else "",
        "day": day.day if day else "",
        "month_name": MONTHS[day.month - 1] if day else "",
        "year": day.year if day else "",
        "time_display": time_display,
        "start_time": content.get("start_time") or "",
        "start_iso": start.isoformat() if start else "",
        "tz_name": tz_name,
        "tz_label": tz_label,
        "is_past": is_past,
        "days_until": days_until,
        "countdown": countdown,
        "countdown_iso": countdown_target.isoformat() if countdown_target else "",
        "countdown_label": countdown_label,
        "venue": venue,
        "address_lines": address_lines,
        "route_url": route_url,
        "story_title": (story.get("title") or cfg["story_title"]).strip()[:60],
        "story": _paragraphs(story.get("text")),
        "program": program,
        "dresscode_text": _paragraphs(dresscode.get("text")),
        "dresscode_colors": dresscode.get("colors") or [],
        "practical": practical,
        "contact": {
            "name": (contact.get("name") or "").strip(),
            "phone": (contact.get("phone") or "").strip(),
            "tel": phone,
            "email": (contact.get("email") or "").strip(),
            "note": (contact.get("note") or "").strip(),
        },
        "closing": _paragraphs(content.get("closing_text")),
        "hero": hero,
        "gallery": gallery,
        "music_url": music_url,
        "music_title": music_title,
        "music_synth": options.music_synth and not music_url,
        # Welke melodie het speeldoosje in een voorbeeld speelt (manifest: demo_melody), anders de standaard.
        "music_melody": str((template_version.manifest or {}).get("demo_melody") or "") if options.music_synth and not music_url else "",
        "show": show,
        "rsvp": {
            "open": show["rsvp"] and not closed_reason and options.mode == "live",
            "closed_reason": closed_reason,
            "deadline_display": nl_date_short(rsvp_deadline.date()) if rsvp_deadline else "",
            "max_party": max_party,
            "party_range": list(range(1, max_party + 1)),
            "ask_remark": bool(rsvp_cfg.get("ask_remark", True)),
            "remark_label": (rsvp_cfg.get("remark_label") or "Wil je nog iets laten weten?").strip()[:120],
            "questions": questions,
            "action": options.rsvp_action,
            "existing": options.existing_response,
        },
        "palette_key": palette.get("key"),
        "palette_style": palette_style,
        "opening_enabled": bool((content.get("style") or {}).get("opening", True)),
        "calendar": calendar,
        "share_url": options.share_url,
        "whatsapp_url": whatsapp_url,
        "share_text": share_text,
        "template_version": template_version,
        "design_slug": template_version.template.slug,
        "effects": effect_view((template_version.manifest or {}).get("effects")),
        "stylesheet": template_version.stylesheet,
        "notice": (overrides.get("notice") or "").strip()[:300],
    }
