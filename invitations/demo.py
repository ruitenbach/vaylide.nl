"""Fictieve voorbeeldevenementen voor de werkende voorbeelden per ontwerp.

Alle namen, locaties en teksten zijn verzonnen en worden op de pagina duidelijk
als voorbeeld gemarkeerd. De datum ligt altijd in de toekomst, zodat de afteller
werkt. Beelden zijn eigen, abstracte illustraties (zie tools/generate_demo_images.py).
"""
from __future__ import annotations

from datetime import date, timedelta

from django.utils import timezone

from .content import default_content

DEFAULT_DEMO_OCCASION = {
    "liefde-op-papier": "bruiloft",
    "avondgoud": "verjaardag",
    "puur-moment": "verloving",
    "gouden-licht": "bruiloft",
}

DESIGN_IMAGES = {
    "liefde-op-papier": ["waterverf-bloesem", "bloemblaadjes", "waterverf-lavendel", "zee-horizon", "duinen-staand"],
    "avondgoud": ["goud-lichtjes", "kaarslicht", "bloemblaadjes", "zee-horizon", "duinen-ochtend"],
    "puur-moment": ["duinen-ochtend", "zee-horizon", "duinen-staand", "waterverf-lavendel", "bloemblaadjes"],
    "gouden-licht": ["rozen", "kaarslicht", "bloemblaadjes", "goud-lichtjes", "duinen-ochtend"],
    # Atelier-ontwerpen: eerste beeld is de kop, de rest de fotogalerij.
    "eucalyptus": ["eucalyptus", "bloemblaadjes", "zee-horizon", "duinen-staand", "waterverf-bloesem"],
    "gatsby": ["zijde-goud", "goud-lichtjes", "kaarslicht", "stadslicht", "zee-horizon"],
    "rozentuin": ["rozen", "bloemblaadjes", "waterverf-bloesem", "duinen-staand", "zee-horizon"],
    "lijnenspel": ["architectuur", "zee-horizon", "duinen-staand", "bloemblaadjes", "duinen-ochtend"],
    "zuiden": ["terracotta", "pampas", "duinen-ochtend", "zee-horizon", "duinen-staand"],
    "ja-woord": ["zijde-goud", "bloemblaadjes", "waterverf-bloesem", "zee-horizon", "duinen-staand"],
    "polaroid": ["duinen-ochtend", "zee-horizon", "bloemblaadjes", "palmbladeren", "duinen-staand"],
    "sterrennacht": ["sterrenhemel", "kaarslicht", "goud-lichtjes", "zee-horizon", "duinen-staand"],
    "pampas": ["pampas", "duinen-ochtend", "bloemblaadjes", "terracotta", "duinen-staand"],
    "monogram": ["waterverf-lavendel", "zee-horizon", "architectuur", "duinen-staand", "bloemblaadjes"],
    "confetti": ["confetti", "ballonnen", "goud-lichtjes", "kaarslicht", "neon"],
    "neon": ["neon", "stadslicht", "confetti", "goud-lichtjes", "kaarslicht"],
    "ballonfeest": ["ballonnen", "confetti", "bloemblaadjes", "wolken", "zee-horizon"],
    "glitter": ["zijde-goud", "goud-lichtjes", "kaarslicht", "confetti", "stadslicht"],
    "tropisch": ["palmbladeren", "zee-horizon", "terracotta", "duinen-ochtend", "confetti"],
    "lauwerkrans": ["zijde-goud", "kaarslicht", "waterverf-bloesem", "duinen-ochtend", "zee-horizon"],
    "zilveren-feest": ["zijde-zilver", "zee-horizon", "waterverf-lavendel", "duinen-staand", "kaarslicht"],
    "gouden-jaren": ["zijde-goud", "goud-lichtjes", "kaarslicht", "duinen-ochtend", "bloemblaadjes"],
    "door-de-jaren": ["duinen-ochtend", "zee-horizon", "bloemblaadjes", "duinen-staand", "waterverf-bloesem"],
    "robijn": ["rozen", "kaarslicht", "bloemblaadjes", "goud-lichtjes", "zee-horizon"],
    "wolkje": ["wolken", "ballonnen", "waterverf-lavendel", "zee-horizon", "duinen-staand"],
    "maanlicht": ["sterrenhemel", "wolken", "waterverf-lavendel", "zee-horizon", "duinen-staand"],
    "regenboog": ["wolken", "terracotta", "pampas", "duinen-ochtend", "bloemblaadjes"],
    "lentebloesem": ["bloesemtak", "bloemblaadjes", "waterverf-bloesem", "wolken", "zee-horizon"],
    "stipjes": ["confetti", "ballonnen", "bloemblaadjes", "wolken", "waterverf-bloesem"],
    "strak": ["architectuur", "stadslicht", "zee-horizon", "duinen-staand", "duinen-ochtend"],
    "gala": ["stadslicht", "kaarslicht", "goud-lichtjes", "zijde-goud", "zee-horizon"],
    "congres": ["architectuur", "stadslicht", "zee-horizon", "confetti", "duinen-staand"],
    "borrel": ["terracotta", "kaarslicht", "goud-lichtjes", "stadslicht", "zee-horizon"],
    "mijlpaal": ["zijde-goud", "stadslicht", "architectuur", "goud-lichtjes", "zee-horizon"],
}
IMAGE_SIZES = {
    "waterverf-bloesem": (1200, 1500),
    "waterverf-lavendel": (1500, 1000),
    "goud-lichtjes": (1800, 1200),
    "kaarslicht": (1200, 1600),
    "duinen-ochtend": (1800, 1150),
    "zee-horizon": (1500, 1500),
    "bloemblaadjes": (1600, 1100),
    "duinen-staand": (1200, 1500),
    "eucalyptus": (1200, 1500),
    "pampas": (1200, 1500),
    "sterrenhemel": (1500, 1200),
    "confetti": (1600, 1100),
    "neon": (1200, 1500),
    "palmbladeren": (1500, 1200),
    "terracotta": (1200, 1500),
    "architectuur": (1800, 1200),
    "stadslicht": (1800, 1200),
    "wolken": (1500, 1200),
    "zijde-goud": (1500, 1200),
    "zijde-zilver": (1500, 1200),
    "rozen": (1200, 1500),
    "bloesemtak": (1500, 1200),
    "ballonnen": (1200, 1500),
}


def _demo_date(weeks_ahead: int = 30) -> date:
    target = timezone.localdate() + timedelta(weeks=weeks_ahead)
    # Altijd op een zaterdag.
    return target + timedelta(days=(5 - target.weekday()) % 7)


def _img(name: str, x=50, y=50, caption="") -> dict:
    w, h = IMAGE_SIZES.get(name, (1600, 1100))
    return {"static": f"img/demo/{name}.webp", "static_small": f"img/demo/{name}-1000.webp", "x": x, "y": y, "zoom": 1, "w": w, "h": h,
            "alt": "Voorbeeldbeeld (abstracte illustratie)", "caption": caption}


def demo_content(design_slug: str, occasion: str, palette_key: str = "") -> dict:
    content = default_content(occasion, palette_key)
    day = _demo_date()
    deadline = day - timedelta(weeks=6)
    images = DESIGN_IMAGES.get(design_slug, DESIGN_IMAGES["liefde-op-papier"])
    content.update(
        {
            "date": day.isoformat(),
            "timezone": "Europe/Amsterdam",
            "venue_name": "De Oranjerie (voorbeeldlocatie)",
            "address": "Voorbeeldlaan 1\nUtrecht",
            "route_url": "https://www.google.com/maps/search/?api=1&query=Utrecht",
        }
    )
    content["photos"] = {
        "hero": _img(images[0], 50, 45),
        "gallery": [_img(images[1]), _img(images[2]), _img(images[3]), _img(images[4])],
    }
    content["rsvp"].update({"deadline": deadline.isoformat(), "max_party_size": 2})
    content["contact"] = {"name": "Mila (ceremoniemeester)", "phone": "", "email": "mila@example.com",
                          "note": "Voor vragen of een verrassing kun je bij Mila terecht."}
    content["sections"].update({"gallery": True, "music": True, "story": True})
    content["dresscode"] = {"text": "Zomers chic. Denk aan lichte stoffen en schoenen waarop je ook in het gras kunt lopen.",
                            "colors": ["#E9D5C9", "#C9A2A0", "#A7B8A0", "#F4EBDD"]}
    content["practical"] = [
        {"title": "Parkeren", "text": "Er is gratis parkeergelegenheid bij de locatie."},
        {"title": "Cadeautip", "text": "Jullie aanwezigheid is het mooiste cadeau. Wie toch iets wil geven: er staat een enveloppendoos."},
        {"title": "Overnachten", "text": "In de buurt zijn verschillende hotels. Vraag ons gerust om tips."},
    ]
    content["rsvp"]["questions"] = [
        {"id": "q1", "label": "Heb je dieetwensen of allergieën?", "type": "text", "options": [], "required": False},
        {"id": "q2", "label": "Blijf je ook voor het avondfeest?", "type": "yesno", "options": [], "required": False},
    ]

    if occasion == "bruiloft":
        content["names"] = {"partner_1": "Sanne", "partner_2": "Daan"}
        content.update({"start_time": "13:30", "end_time": "00:30"})
        content["welcome_text"] = (
            "Lieve familie en vrienden,\n\nna acht jaar samen zeggen we volgende zomer ja tegen elkaar. "
            "We zouden het heel bijzonder vinden om deze dag met jou te vieren."
        )
        content["story"] = {"title": "Ons verhaal", "text": (
            "We ontmoetten elkaar op een regenachtige dinsdag in de trein naar Utrecht. "
            "Wat begon met een gedeelde paraplu, werd een reis die we samen willen blijven maken.\n\n"
            "Op deze dag zeggen we ja, en we vinden het fijn als jij erbij bent."
        )}
        content["program"] = [
            {"time": "13:30", "title": "Ontvangst", "description": "Met koffie en iets lekkers in de tuin."},
            {"time": "14:00", "title": "Ceremonie", "description": ""},
            {"time": "15:00", "title": "Toost en taart", "description": ""},
            {"time": "18:00", "title": "Diner", "description": "Voor wie ook voor het diner is uitgenodigd."},
            {"time": "21:00", "title": "Feest", "description": "Dansen tot het laatste nummer."},
        ]
        content["closing_text"] = "We kijken ernaar uit om deze dag met jou te delen. Tot dan!"
    elif occasion == "verloving":
        content["names"] = {"partner_1": "Noor", "partner_2": "Yusuf"}
        content.update({"start_time": "16:00", "end_time": "21:00"})
        content["welcome_text"] = "Ze zei ja! Dat willen we graag samen met jou vieren, met een glas en goed eten."
        content["story"] = {"title": "Hoe het begon", "text": "Een gedeelde liefde voor zee, koffie en lange wandelingen. De rest is geschiedenis."}
        content["program"] = [
            {"time": "16:00", "title": "Ontvangst", "description": ""},
            {"time": "17:00", "title": "Toost", "description": ""},
            {"time": "18:00", "title": "Buffet", "description": ""},
        ]
        content["dresscode"] = {"text": "Smart casual.", "colors": []}
        content["closing_text"] = "Tot snel!"
        content["contact"]["name"] = "Mila (vriendin van Noor)"
    elif occasion == "verjaardag":
        content["names"] = {"person_name": "Lotte", "age": "30"}
        content.update({"start_time": "20:00", "end_time": "01:00"})
        content["welcome_text"] = "Dertig wordt gevierd met muziek, bubbels en de mensen die ertoe doen. Kom je ook?"
        content["story"] = {"title": "Over de jarige", "text": "Liefhebber van dansen, lange diners en spontane plannen."}
        content["program"] = [
            {"time": "20:00", "title": "Inloop", "description": "Met een welkomstdrankje."},
            {"time": "21:00", "title": "Taart", "description": ""},
            {"time": "22:00", "title": "Dansen", "description": "Met een dj tot in de late uurtjes."},
        ]
        content["dresscode"] = {"text": "Alles wat glinstert. Goud, zwart of juist een kleurtje.",
                                "colors": ["#0D1422", "#D7B878", "#F1DFB0"]}
        content["closing_text"] = "Tot op het feest!"
        content["contact"]["name"] = "Mila (vriendin van Lotte)"
    elif occasion == "jubileum":
        content["names"] = {"honorees": "Ria & Kees", "years": "40"}
        content.update({"start_time": "15:00", "end_time": "20:00"})
        content["welcome_text"] = "Veertig jaar samen: dat vieren we graag met familie, vrienden en buren."
        content["story"] = {"title": "Terugblik", "text": "Van een eerste dans in 1980-iets tot kinderen, kleinkinderen en een tuin vol herinneringen."}
        content["program"] = [
            {"time": "15:00", "title": "Ontvangst", "description": ""},
            {"time": "16:00", "title": "Een woordje", "description": ""},
            {"time": "17:30", "title": "Diner", "description": ""},
        ]
        content["closing_text"] = "Tot ziens!"
        content["contact"]["name"] = "Mila (dochter)"
    elif occasion == "babyshower":
        content["names"] = {"parents": "Emma & Thijs", "baby_name": ""}
        content.update({"start_time": "14:00", "end_time": "17:00"})
        content["welcome_text"] = "Er is iets kleins op komst! Vier het met ons met taart, thee en spelletjes."
        content["program"] = [
            {"time": "14:00", "title": "Ontvangst", "description": ""},
            {"time": "14:30", "title": "Spelletjes", "description": ""},
            {"time": "16:00", "title": "Cadeautjes", "description": ""},
        ]
        content["dresscode"] = {"text": "", "colors": []}
        content["closing_text"] = "We kijken ernaar uit je te zien!"
        content["contact"]["name"] = "Mila (vriendin)"
    elif occasion == "zakelijk":
        content["names"] = {"event_title": "Jubileumborrel", "organization": "Studio Voorbeeld", "years": "10"}
        content.update({"start_time": "16:00", "end_time": "19:00"})
        content["welcome_text"] = "Graag nodigen wij u uit om samen met ons team tien jaar Studio Voorbeeld te vieren."
        content["program"] = [
            {"time": "16:00", "title": "Ontvangst", "description": ""},
            {"time": "16:30", "title": "Korte presentatie", "description": ""},
            {"time": "17:00", "title": "Netwerkborrel", "description": ""},
        ]
        content["dresscode"] = {"text": "Zakelijk.", "colors": []}
        content["practical"] = [{"title": "Parkeren", "text": "Parkeergarage op loopafstand."}]
        content["closing_text"] = "Wij zien u graag."
        content["contact"] = {"name": "Mila (organisatie)", "phone": "", "email": "mila@example.com", "note": ""}
        content["sections"]["story"] = False
        content["rsvp"]["questions"] = [
            {"id": "q1", "label": "Heeft u dieetwensen?", "type": "text", "options": [], "required": False},
        ]
    return content
