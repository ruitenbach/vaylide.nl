"""Extra vragen bij het aanmelden: alleen uit een vaste lijst van vooraf beoordeelde, neutrale vragen.

Keuze van de eigenaar (30 september 2026, "optie A"): de eerste liveversie vraagt geen gevoelige gegevens uit. Een
organisator kan daarom geen eigen vraagtekst of eigen antwoordopties meer invullen, en ook de vraag bij de
toelichting ligt vast. Een waarschuwing alleen is niet genoeg (zie docs/PRIVACY.md).

Bestaande eigen vragen van vóór deze wijziging blijven staan (niets van klanten wordt stil veranderd). Ze zijn te
herkennen met `eigen_vragen()` en te tellen met `manage.py rsvp_vragen_rapport`.

Een nieuwe vraag toevoegen: alleen na beoordeling (neutraal, nodig voor de organisatie, geen gezondheid, geloof,
afkomst of andere bijzondere persoonsgegevens, ook niet via de antwoordopties). Een tekst van een bestaande vraag
wijzigen raakt al gepubliceerde uitnodigingen niet: die bewaren hun eigen kopie van de vraag.
"""
from __future__ import annotations

HINT_GEVOELIG = "Vermeld hier geen medische informatie, allergieën, religieuze gegevens of andere gevoelige persoonsgegevens."
TOELICHTING_LABEL = "Wil je nog iets laten weten?"
TOELICHTING_LABEL_U = "Wilt u nog iets laten weten?"
STANDAARD_TOELICHTING = {TOELICHTING_LABEL, TOELICHTING_LABEL_U}

VRAGEN = [
    {"key": "vervoer", "label": "Hoe kom je?", "label_u": "Hoe komt u?", "type": "choice",
     "options": ["Met de auto", "Met het openbaar vervoer", "Op de fiets of lopend", "Anders"],
     "uitleg": "Handig voor parkeren of het plannen van vervoer."},
    {"key": "parkeren", "label": "Heb je een parkeerplek nodig?", "label_u": "Heeft u een parkeerplek nodig?",
     "type": "yesno", "options": [], "uitleg": "Als het aantal parkeerplekken beperkt is."},
    {"key": "overnachten", "label": "Blijf je overnachten?", "label_u": "Blijft u overnachten?", "type": "yesno",
     "options": [], "uitleg": "Als er een overnachting of logeerplek is geregeld."},
    {"key": "pendel", "label": "Wil je gebruikmaken van het geregelde vervoer?",
     "label_u": "Wilt u gebruikmaken van het geregelde vervoer?", "type": "yesno", "options": [],
     "uitleg": "Als er bijvoorbeeld een pendelbus rijdt."},
    {"key": "aankomst", "label": "Wanneer ben je erbij?", "label_u": "Wanneer bent u erbij?", "type": "choice",
     "options": ["Vanaf het begin", "Later", "Weet ik nog niet"],
     "uitleg": "Als gasten ook later kunnen aansluiten, bijvoorbeeld bij het avondfeest."},
    {"key": "liedje", "label": "Welk nummer mag niet ontbreken?", "label_u": "Welk nummer mag volgens u niet ontbreken?",
     "type": "text", "options": [], "uitleg": "Een open vraag voor de playlist."},
]
BY_KEY = {v["key"]: v for v in VRAGEN}


def vraag(key: str, *, formal: bool, required: bool = False) -> dict:
    """De vraag zoals die in de inhoud van een uitnodiging wordt bewaard (een vaste kopie)."""
    v = BY_KEY[key]
    return {"id": key, "label": v["label_u"] if formal else v["label"], "type": v["type"], "options": list(v["options"]),
            "required": bool(required)}


def is_vast(q: dict) -> bool:
    """Klopt deze bewaarde vraag precies met een vraag uit de vaste lijst (tekst, soort en opties)?"""
    v = BY_KEY.get(str(q.get("id") or ""))
    if not v:
        return False
    return (q.get("label") in (v["label"], v["label_u"]) and q.get("type") == v["type"]
            and list(q.get("options") or []) == list(v["options"]))


def eigen_vragen(questions) -> list[dict]:
    """Vragen die niet uit de vaste lijst komen (van vóór 30 september 2026)."""
    return [q for q in questions or [] if isinstance(q, dict) and not is_vast(q)]


def eigen_toelichting(rsvp: dict) -> bool:
    label = (rsvp or {}).get("remark_label") or TOELICHTING_LABEL
    return label.strip() not in STANDAARD_TOELICHTING
