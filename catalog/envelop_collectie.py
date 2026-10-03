"""VAYLIDE Envelope Collection: de stijlen en lakzegels als configuratie voor één envelop-engine.

Eén sjabloon (templates/partials/envelop/collectie.html) met vaste lagen: achterkant met voering, kaart, voorvakken,
flap (buitenkant met decoratie en reliëf, binnenkant met voering), een lakzegel als los object en schaduwlagen.
Een stijl kiest alleen materiaal en decoratie; de bouw en de animatie zijn voor alle stijlen gelijk. Een nieuwe stijl
is dus een nieuw item hieronder (plus eventueel een decoratie uit tools/enveloppen/maak_ornamenten.py).

Visuele referentie: de Canva-ontwerpen van de eigenaar (oktober 2026). Ontwerpfase: nog niet gekoppeld aan
bestellingen of pakketten (alleen de studio /lab/enveloppen/ met DEBUG aan).
"""
from __future__ import annotations

# Lakzegels: los te kiezen object. was = (licht, basis, schaduw, glanskleur); glans = sterkte van de glans (0-1);
# teken: "v" (de V uit het logo), "v-krans" (logo-V in een krans), "roos" (een roos met steel) of "monogram" (initialen).
ZEGELS = {
    "champagne-monogram": {"naam": "Champagne Monogram", "materiaal": "Champagnegoud", "was": ("#F6E6B9", "#D4B06B", "#93703A", "#FFF3D2"), "glans": 0.85, "teken": "v"},
    "evergreen": {"naam": "Royal Evergreen", "materiaal": "Dennengroen met krans", "was": ("#5F8463", "#2E5135", "#142C1B", "#E2EFD9"), "glans": 0.5, "teken": "v-krans"},
    "sage-botanical": {"naam": "Sage Botanical", "materiaal": "Zachte saliegroen", "was": ("#D3DCCA", "#AEBBA1", "#7A8B6D", "#F4F8EE"), "glans": 0.5, "teken": "v", "vlek": 0.15},
    "noisette-gold": {"naam": "Noisette Gold", "materiaal": "Warm goud", "was": ("#F4E4BE", "#D2B275", "#8D6B34", "#FFF1CF"), "glans": 0.85, "teken": "v", "vlek": 0.17},
    "rose-floral": {"naam": "Rose Floral", "materiaal": "Roségoud met roos", "was": ("#EDC2A4", "#C88C69", "#874F35", "#FFE7D4"), "glans": 0.8, "teken": "roos"},
}

# Envelopstijlen. lijn: "trouw" of "kerst". flap: decoratie op de buitenkant van de flap; soort "blind" = alleen
# reliëf in het papier, "print" = gekleurde print met licht reliëf. voering: tegel in static/img/envelop/.
# binnen: motief op de binnenkant van de flap, onder de punt (fragment, viewBox en plek in de binnenflap 0 0 1000 476).
# twinkel: één heel kort lichtpuntje op een gouden accent (flapcoördinaten), alleen bij kerst. klaar: uitgewerkt.
STIJLEN = {
    "signature": {
        "naam": "VAYLIDE Signature Ivory", "lijn": "trouw", "klaar": True,
        "tekst": "Warm ivoor papier, een botanisch boeket in blinddruk en een gouden lakzegel met de V. Tijdloos en rustig.",
        "zegel": "champagne-monogram",
        "flap": {"fragment": "partials/envelop/_flap_signature.svg", "soort": "blind"},
        "relief": {"blur": "2.3", "schaal": "3.2"},   # iets zachter en dieper dan de standaard (2.1 en 3), met hoogteverschillen in het boeket; teksten, omdat Django kommagetallen in het Nederlands schrijft
        "voering": "voering-signature.svg",
        "binnen": {"fragment": "partials/envelop/_binnen_signature.svg", "vb": "0 0 200 120", "x": 360, "y": 168, "w": 280, "h": 168},
    },
    "royal-evergreen": {
        "naam": "Royal Evergreen", "lijn": "kerst", "klaar": True,
        "tekst": "Warm ivoor met dennentakken, hulst en kerstballen in diep groen, rood en champagnegoud. Een groen lakzegel met krans.",
        "zegel": "evergreen",
        "flap": {"fragment": "partials/envelop/_kerst_evergreen_flap.svg", "soort": "print"},
        "voering": "voering-royal-evergreen.svg",
        "binnen": {"fragment": "partials/envelop/_binnen_evergreen.svg", "vb": "0 0 160 160", "x": 425, "y": 146, "w": 150, "h": 150},
        "twinkel": (598, 374),
    },
    "rose-blush": {
        "naam": "Rose Blush", "lijn": "trouw", "klaar": True,
        "tekst": "Zacht poederroze papier met slanke takjes in blinddruk en een roségouden lakzegel met een roos. Romantisch en licht.",
        "zegel": "rose-floral",
        "flap": {"fragment": "partials/envelop/_flap_rose.svg", "soort": "blind"},
        "voering": "voering-rose-blush.svg",
        "binnen": {"fragment": "partials/envelop/_binnen_signature.svg", "vb": "0 0 200 120", "x": 360, "y": 168, "w": 280, "h": 168},
    },
    "golden-noel": {
        "naam": "Golden Noël", "lijn": "kerst", "klaar": True,
        "tekst": "Warm ivoor en champagne met wintergroen in goudfolie, gouden kerstballen en een champagnegouden zegel met de V.",
        "zegel": "champagne-monogram",
        "flap": {"fragment": "partials/envelop/_kerst_evergreen_flap.svg", "soort": "print"},
        "voering": "voering-golden-noel.svg",
        "binnen": {"fragment": "partials/envelop/_binnen_evergreen.svg", "vb": "0 0 160 160", "x": 425, "y": 146, "w": 150, "h": 150},
        "twinkel": (598, 374),
    },
    "midnight-emeraude": {
        "naam": "Midnight Émeraude", "lijn": "trouw", "klaar": True,
        "tekst": "Diepgroen fluwelig papier met botanisch blinddruk, een champagnegouden lakzegel en een gouden voering. Avondlijk en exclusief.",
        "zegel": "champagne-monogram",
        "flap": {"fragment": "partials/envelop/_flap_bloei.svg", "soort": "blind"},
        "voering": "voering-midnight-emeraude.svg",
        "binnen": {"fragment": "partials/envelop/_binnen_signature.svg", "vb": "0 0 200 120", "x": 360, "y": 168, "w": 280, "h": 168},
    },
    "sage": {
        "naam": "Sage Romance", "lijn": "trouw", "klaar": False,
        "tekst": "Ivoor met een zachte saliegroene was en nauwelijks zichtbaar reliëf. Fris, modern editorial.",
        "zegel": "sage-botanical",
        "flap": {"fragment": "partials/envelop/_flap_bloei.svg", "soort": "blind"},
        "voering": "voering-sage.svg",
    },
    "noisette": {
        "naam": "Noisette Luxe", "lijn": "trouw", "klaar": False,
        "tekst": "Diep chocolade mat papier met een warm champagnegouden zegel. Avondlijk en exclusief.",
        "zegel": "noisette-gold",
        "flap": {"fragment": "partials/envelop/_flap_bloei.svg", "soort": "blind"},
        "voering": "voering-noisette.svg",
    },
}
STANDAARD = "signature"


def _binnen_veld(s: dict) -> None:
    """Middelpunt en maat van het rustige veld achter het motief op de binnenflap (iets groter dan het motief).
    Hele getallen: Django zet kommagetallen in het Nederlands met een komma neer, en dat is geen geldige SVG."""
    b = s.get("binnen")
    if b and "cx" not in b:
        b.update(cx=b["x"] + b["w"] // 2, cy=b["y"] + b["h"] // 2, rx=round(b["w"] * 0.62), ry=round(b["h"] * 0.66))


for _s in STIJLEN.values():
    _binnen_veld(_s)


# ---------------------------------------------------------------------------------------------------------------- keuze in de Studio
# De Studio laat de klant een envelop en een zegel kiezen als losse presentatielaag rondom een uitnodigingsontwerp. Wat een envelop daarvoor
# nodig heeft staat hier (los van de tekenregels hierboven): voor welke gelegenheden hij past, welke zegels erbij horen (de eerste is de
# standaard), hoe hij beweegt en hoe lang het openingsscherm duurt (de opening plus een korte stilte), en welke achtergrond het scherm krijgt.
#   beweging: "gsap" = static/js/envelop-signature.js (Signature Ivory), "klassiek" = static/js/envelop-collectie.js
#   duur: milliseconden tot het openingsscherm sluit (data-duration); de envelop zelf is dan klaar
#   achtergrond: "licht" of "donker" (static/css/envelop-cover.css)
NIET_KERST = ["bruiloft", "verloving", "jubileum", "verjaardag", "babyshower", "zakelijk"]
KEUZE = {
    "signature": {"gelegenheden": NIET_KERST, "zegels": ["champagne-monogram", "noisette-gold", "sage-botanical", "rose-floral"],
                  "beweging": "gsap", "duur": 3900, "achtergrond": "licht"},
    "rose-blush": {"gelegenheden": ["bruiloft", "verloving", "babyshower", "verjaardag"], "zegels": ["rose-floral", "champagne-monogram", "noisette-gold"],
                   "beweging": "klassiek", "duur": 4600, "achtergrond": "licht"},
    "midnight-emeraude": {"gelegenheden": ["bruiloft", "verloving", "jubileum", "zakelijk"], "zegels": ["champagne-monogram", "noisette-gold"],
                          "beweging": "klassiek", "duur": 4600, "achtergrond": "donker"},
    "royal-evergreen": {"gelegenheden": ["kerst"], "zegels": ["evergreen", "champagne-monogram"],
                        "beweging": "klassiek", "duur": 4600, "achtergrond": "licht"},
    "golden-noel": {"gelegenheden": ["kerst"], "zegels": ["champagne-monogram", "noisette-gold", "evergreen"],
                    "beweging": "klassiek", "duur": 4600, "achtergrond": "licht"},
}

# Welke ontwerpen de Envelope Collection als keuze krijgen (envelope_mode in het manifest van een ontwerp wint, zie modus()).
#   optional: de klant kiest zelf (geen envelop, de opening van het ontwerp, of een envelop uit de collectie)
#   built_in: het ontwerp heeft een eigen, ingebouwde opening (de standaard voor elk ander ontwerp)
#   none: geen envelop mogelijk
# Hier staan ontwerpen met een rustige opening die een envelop kan vervangen zonder dat het concept van het ontwerp verandert. Een ontwerp dat
# zelf een envelop uit de collectie als opening heeft (Rosé Royale, Golden Noël, Midnight Émeraude) of een opening die bij het verhaal hoort
# (cadeau, ringdoosje, vleugels, gordijn, polaroid) blijft built_in.
ONTWERP_MODUS = {slug: "optional" for slug in (
    "puur-moment", "lijnenspel", "pampas", "eucalyptus", "monogram", "strak", "borrel", "congres",
    "lauwerkrans", "lentebloesem", "rozentuin")}
MODI = ("optional", "built_in", "none")
GEEN = "geen"        # bewuste keuze: geen envelop, direct de uitnodiging
ONTWERP = ""         # niets gekozen: de opening van het ontwerp zelf (het gedrag van bestaande uitnodigingen)


def modus(template_version) -> str:
    """envelope_mode van een ontwerp: het manifest wint; anders de tabel hierboven; anders built_in (de eigen opening blijft)."""
    manifest = getattr(template_version, "manifest", None) or {}
    waarde = manifest.get("envelope_mode")
    if waarde in MODI:
        return waarde
    return ONTWERP_MODUS.get(template_version.template.slug, "built_in")


def beschikbaar(occasion: str) -> dict[str, dict]:
    """De uitgewerkte enveloppen die bij een gelegenheid passen, in de volgorde van STIJLEN."""
    return {code: s for code, s in STIJLEN.items() if s.get("klaar") and occasion in KEUZE.get(code, {}).get("gelegenheden", [])}


def zegels_voor(stijl_code: str) -> list[str]:
    return list(KEUZE.get(stijl_code, {}).get("zegels") or [STIJLEN[stijl_code]["zegel"]])


def standaard_zegel(stijl_code: str) -> str:
    return zegels_voor(stijl_code)[0]


def keuze_van(content: dict) -> dict:
    """De ruwe keuze uit het inhoudsdocument: envelop ('' = opening van het ontwerp, 'geen' of een stijl), zegel, teken en initialen."""
    data = ((content.get("style") or {}).get("envelop") or {}).get("collectie") or {}
    return {"envelop": str(data.get("envelop") or ""), "zegel": str(data.get("zegel") or ""),
            "teken": "initialen" if data.get("teken") == "initialen" else "standaard", "initialen": str(data.get("initialen") or "")}


def gekozen(content: dict, occasion: str, template_version) -> dict | None:
    """Wat een gast te zien krijgt: None (de opening van het ontwerp, of geen opening bij 'geen') of een dict met stijl, zegel, beweging en duur.
    Een onbekende, niet-passende of niet meer bestaande keuze valt terug op het gedrag van vroeger; het ontwerp zelf blijft dus altijd werken."""
    if modus(template_version) != "optional":
        return None
    keuze = keuze_van(content)
    code = keuze["envelop"]
    if code in (ONTWERP, GEEN) or code not in beschikbaar(occasion):
        return None
    zegel_code = keuze["zegel"] if keuze["zegel"] in zegels_voor(code) else standaard_zegel(code)
    k = KEUZE[code]
    return {"stijl": code, "zegel": zegel_code, "beweging": k["beweging"], "duur": k["duur"], "intro": k["duur"] - 300, "achtergrond": k["achtergrond"],
            "monogram": keuze["initialen"] if keuze["teken"] == "initialen" else "", "teken": keuze["teken"]}


def geen_envelop(content: dict, template_version) -> bool:
    """Bewust 'geen envelop': geen openingsscherm, direct de uitnodiging (alleen bij een ontwerp met de keuze)."""
    return modus(template_version) == "optional" and keuze_van(content)["envelop"] == GEEN


def stijl(code: str | None) -> tuple[str, dict]:
    """De stijl bij een code; onbekend of leeg geeft de standaard (veilig voor oude of aangepaste verzoeken)."""
    code = code if code in STIJLEN else STANDAARD
    return code, STIJLEN[code]


def zegel(code: str | None, standaard: str) -> tuple[str, dict]:
    code = code if code in ZEGELS else standaard
    return code, ZEGELS[code]


def zegel_stijl(z: dict) -> str:
    """De waskleuren als CSS-variabelen voor het style-attribuut van het zegel (CSP staat style-attributen toe)."""
    hi, basis, lo, glans_kleur = z["was"]
    return f"--vx-wax-hi: {hi}; --vx-wax: {basis}; --vx-wax-lo: {lo}; --vx-wax-spec: {glans_kleur}; --vx-wax-gloss: {z['glans']};"


# Natuurlijke onregelmaat van het wasoppervlak (zie collectie.html). Standaard voor alle materialen; een zegel kan eigen waarden
# hebben via ZEGELS[..]["korrel"] (fijne korrel in de hoogte, 0 = glad) en ["vlek"] (zachte lichtvlekken, 0 = geen).
WAS_KORREL = 0.008
WAS_VLEK = 0.22


def was_structuur(z: dict) -> dict:
    """De getallen voor het wasoppervlak van dit zegel. De offset houdt de gemiddelde helderheid gelijk bij elke vlekkensterkte."""
    korrel = float(z.get("korrel", WAS_KORREL))
    vlek = float(z.get("vlek", WAS_VLEK))
    return {"korrel": f"{korrel:g}", "vlek": f"{vlek:g}", "vlek_offset": f"{-vlek * 0.5:g}"}


def monogram_opmaak(monogram: str) -> dict:
    """Hoe de initialen op het zegel staan: met een & tussen twee grote letters staat het teken kleiner en iets hoger (zoals
    bij een gedrukt monogram), en de lettermaat past zich aan het aantal letters aan zodat ze binnen de krans blijven.
    Geeft {'links', 'rechts', 'maat'}: 'rechts' is leeg zonder &; 'maat' is de CSS-klasse (m1 t/m m4, a2 en a3 voor met &)."""
    delen = monogram.split("&", 1)
    if len(delen) == 2 and delen[0] and delen[1]:
        aantal = len(delen[0]) + len(delen[1])
        return {"links": delen[0], "rechts": delen[1], "maat": "a2" if aantal <= 2 else "a3"}
    tekst = monogram.replace("&", "")
    return {"links": tekst, "rechts": "", "maat": f"m{min(max(len(tekst), 1), 4)}"}


def envelop(uid: str, stijl_code: str | None, zegel_code: str | None = None, monogram: str = "",
            kicker: str = "", title: str = "", date: str = "", link: str = "") -> dict:
    """Alles wat het sjabloon nodig heeft voor één envelop. Met link (bijv. "#uitnodiging") is het zegel een link met
    data-open, zodat een uitnodiging ook zonder JavaScript opent (de afspraak voor openingsschermen)."""
    code, s = stijl(stijl_code)
    zcode, z = zegel(zegel_code, s["zegel"])
    teken = "monogram" if monogram else z["teken"]
    return {"uid": uid, "stijl": code, "s": s, "zegel": z, "zegel_code": zcode, "zegel_stijl": zegel_stijl(z), "was": was_structuur(z), "teken": teken,
            "monogram": monogram[:4], "mono": monogram_opmaak(monogram[:4]), "kicker": kicker, "title": title, "date": date, "link": link}
