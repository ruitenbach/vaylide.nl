"""De nieuwe prijsstructuur: per ontwerp één vaste indeling (Basis, Luxe of Special) en per gelegenheid één prijs.

Het bedrag volgt altijd uit twee dingen: de indeling van het ontwerp (INDELING) en de prijsrij van de gelegenheid (PRIJZEN). Alle prijzen zijn in centen,
inclusief btw. Deze module is de enige bron: de ontwerppagina, het voorbeeld, Bestellen, de bestelling, de bevestiging en Mollie gebruiken uitsluitend
`prijs_info` of `tier_package` (via orders.pricing), zodat getoond bedrag, offerte, ordertotaal en betaalbedrag nooit uit elkaar kunnen lopen.

Alles staat achter settings.PRICING_V2 (standaard uit, per omgeving aan te zetten). Staat dat uit, dan werkt alles zoals voorheen.

Bewust niet gedaan: prijzen of pakketten in de database (Beheer → Prijzen blijft voor de oude structuur), handmatige correctierondes beloven, of extra
gelegenheden aanmaken. Een gelegenheid of indeling zonder ontwerp is vanzelf niet te kiezen: er is dan geen ontwerp dat erbij hoort.
"""
from __future__ import annotations

from django.conf import settings

from .models import Package, format_euro

BASIS, LUXE, SPECIAL = "basis", "luxe", "special"
TIERS = (BASIS, LUXE, SPECIAL)
TIER_NAAM = {BASIS: "Basis", LUXE: "Luxe", SPECIAL: "Special"}

# Hoe lang een kaart online staat: voor alle drie de indelingen 12 maanden (besluit van de eigenaar, 15 oktober 2026), ook voor een wenskaart. Eén plek per
# indeling, zodat een latere verfijning (bijvoorbeeld een andere duur voor Basis) alleen dit getal verandert. De algemene voorwaarden (artikel 6) en de
# privacyverklaring noemen nog 6 maanden bij Essentieel en 12 bij Compleet: de nieuwe tekst ligt ter goedkeuring bij de eigenaar en is nog niet doorgevoerd.
MAANDEN_ONLINE = {BASIS: 12, LUXE: 12, SPECIAL: 12}

# De prijsrijen: (Basis, Luxe, Special) in centen, inclusief btw.
PRIJZEN = {
    "kerst": (995, 2495, 4995),                 # Kerstkaart / nieuwjaarswens
    "verjaardag": (1995, 3495, 5995),           # Verjaardagsuitnodiging
    "zakelijk": (1495, 2995, 4995),             # Zakelijk evenement
    "babyshower": (1995, 3495, 5995),           # Babyshower / gender reveal
    "bruiloft": (2995, 5995, 8995),             # Trouwuitnodiging
    "jubileum_verloving": (1995, 3995, 6900),   # Jubileum / verlovingsfeest
    "bedank": (995, 1995, 3995),                # Bedankkaart / felicitatie (een wenskaart buiten Kerst)
    # Nog geen gelegenheid in de site, dus niet te kiezen; staan hier zodat de prijs klaarligt zodra er ontwerpen voor zijn.
    "geboorte": (1995, 3495, 5995),             # Geboortekaart
    "savethedate": (1995, 3995, 6900),          # Save the date
}
CATEGORIE_LABEL = {
    "kerst": "Kerstkaart / nieuwjaarswens", "verjaardag": "Verjaardagsuitnodiging", "zakelijk": "Zakelijk evenement",
    "babyshower": "Babyshower / gender reveal", "bruiloft": "Trouwuitnodiging", "jubileum_verloving": "Jubileum / verlovingsfeest",
    "bedank": "Bedankkaart / felicitatie", "geboorte": "Geboortekaart", "savethedate": "Save the date",
}
# Welke prijsrij bij welke gelegenheid van de site hoort. Een wenskaart buiten Kerst gebruikt altijd de rij 'bedank'.
GELEGENHEID_RIJ = {
    "bruiloft": "bruiloft", "verloving": "jubileum_verloving", "jubileum": "jubileum_verloving", "verjaardag": "verjaardag",
    "babyshower": "babyshower", "zakelijk": "zakelijk", "kerst": "kerst",
}

# De indeling per ontwerp. Criteria (docs/PRIJZEN.md): Special = cinematisch of zeer uitgebreid (eigen film, 3D- of illustratiescène met meerdere
# lagen en eigen muziek); Luxe = eigen ontworpen scène of opening met eigen animaties; Basis = standaardopening op de gedeelde atelier-basis.
# Een nieuw ontwerp krijgt hier bewust een eigen regel (een test bewaakt dat elk ontwerp een indeling heeft).
INDELING = {
    # Special
    "aurora-nocturne": SPECIAL, "balzaal": SPECIAL, "gouden-avond": SPECIAL, "kerstbol": SPECIAL, "kerstkaart": SPECIAL, "kerststad": SPECIAL,
    "midnight-emeraude": SPECIAL, "rose-royale": SPECIAL, "strandboog": SPECIAL, "zwanenhart": SPECIAL,
    # Luxe (Golden Noël heeft de Special-vlag, maar is een elegante enveloppe zonder eigen film of scène en staat kwalitatief naast Winterlicht: Luxe)
    "golden-noel": LUXE, "aan-tafel": LUXE, "avondgoud": LUXE, "eerste-dans": LUXE, "gloria": LUXE, "liefde-op-papier": LUXE,
    "middernacht": LUXE, "puur-moment": LUXE, "voor-altijd": LUXE, "winterlicht": LUXE,
    # Kerstmarkt, Kerstpaleis, Kerstcoupé en Kerstbal: eigen film en scène, bewust Luxe op besluit van de eigenaar (15 oktober 2026, € 24,95)
    "kerstmarkt": LUXE, "kerstpaleis": LUXE, "kerstcoupe": LUXE, "kerstbal": LUXE,
    # Kerstmagie: eigen openingsfilm, zelfde indeling en prijs als de vier hierboven (geen nieuwe prijs of toeslag)
    "kerstmagie": LUXE,
    # Rozenboog: eigen film, bewust Luxe op besluit van de eigenaar (16 oktober 2026); staat verborgen (groep C) tot de filmrechten bevestigd zijn
    "rozenboog": LUXE,
    # Basis
    **{slug: BASIS for slug in (
        "ballonfeest", "borrel", "confetti", "congres", "door-de-jaren", "eucalyptus", "gala", "gatsby", "glitter", "gouden-jaren", "ja-woord",
        "kerstman", "lauwerkrans", "lentebloesem", "lijnenspel", "maanlicht", "mijlpaal", "monogram", "neon", "pampas", "polaroid", "regenboog",
        "robijn", "rozentuin", "sneeuwpop", "sterrennacht", "stipjes", "strak", "tropisch", "wolkje", "zilveren-feest", "zuiden")},
}

# Alles wat de klant kan personaliseren zit in elke indeling (geen automatische toeslagen): de indeling bepaalt alleen het ontwerp en de prijs.
ALLE_FUNCTIES = ["story", "gallery", "music", "extra_questions", "zegel"]
BESCHRIJVING = {
    BASIS: "Een mooi ontwerp met een standaardopening.",
    LUXE: "Een geanimeerd ontwerp met een eigen opening en scène.",
    SPECIAL: "Een uitgebreid geanimeerd ontwerp uit onze collectie.",
}


def looptijd_zin(onderwerp: str = "Een kaart") -> str:
    """De zin over de online-duur, uit MAANDEN_ONLINE. Is de duur voor alle indelingen gelijk, dan 'Een kaart staat 12 maanden online'; anders per indeling."""
    waarden = set(MAANDEN_ONLINE.values())
    if len(waarden) == 1:
        return f"{onderwerp} staat {waarden.pop()} maanden online"
    return f"Een Basis-kaart staat {MAANDEN_ONLINE[BASIS]} maanden online, een Luxe-kaart {MAANDEN_ONLINE[LUXE]} en een Special {MAANDEN_ONLINE[SPECIAL]} maanden"


def actief() -> bool:
    return bool(getattr(settings, "PRICING_V2", False))


def _slug(template_or_version) -> str:
    template = getattr(template_or_version, "template", None) or template_or_version
    return getattr(template, "slug", "")


def tier(template_or_version) -> str | None:
    """De indeling van een ontwerp, of None als het ontwerp nog geen indeling heeft (dan is het niet te bestellen: nooit een verzonnen prijs)."""
    return INDELING.get(_slug(template_or_version))


def categorie(occasion: str, soort: str = "") -> str | None:
    """De prijsrij: Kerst altijd 'kerst'; een wenskaart bij een andere gelegenheid 'bedank'; anders de rij van de gelegenheid."""
    if occasion == "kerst":
        return "kerst"
    if soort == "wenskaart":
        return "bedank"
    return GELEGENHEID_RIJ.get(occasion)


def prijs_cents(template_or_version, occasion: str, soort: str = "") -> int | None:
    indeling, rij = tier(template_or_version), categorie(occasion, soort)
    if indeling is None or rij is None:
        return None
    template = getattr(template_or_version, "template", None) or template_or_version
    if occasion not in (getattr(template, "occasions", None) or []):
        return None     # een ontwerp is alleen te koop voor de gelegenheden waar het bij hoort
    return PRIJZEN[rij][TIERS.index(indeling)]


def prijs_info(template_or_version, occasion: str, soort: str = "") -> dict | None:
    """Alles wat een pagina over de prijs moet tonen, uit één plek: {'tier', 'naam', 'cents', 'display', 'label', 'maanden', 'rij'}."""
    cents = prijs_cents(template_or_version, occasion, soort)
    if cents is None:
        return None
    indeling = tier(template_or_version)
    naam = TIER_NAAM[indeling]
    rij = categorie(occasion, soort)
    return {"tier": indeling, "naam": naam, "cents": cents, "display": format_euro(cents), "label": f"{naam} {format_euro(cents)}",
            "maanden": MAANDEN_ONLINE[indeling], "rij": rij, "rij_label": CATEGORIE_LABEL[rij]}


def tier_package(template_or_version, occasion: str, soort: str = "") -> Package:
    """Het 'pakket' van een bestelling in de nieuwe structuur: een niet-opgeslagen Package (zoals bij de wenskaart), alleen om de prijsregel, de
    functies en de bestelling te vullen. De code is de indeling (bij een wenskaart met '-wenskaart' erachter)."""
    info = prijs_info(template_or_version, occasion, soort)
    if info is None:
        raise ValueError("Voor dit ontwerp en deze gelegenheid is geen prijs beschikbaar.")
    wens = soort == "wenskaart"
    functies = [] if wens else list(ALLE_FUNCTIES) + (["special"] if info["tier"] == SPECIAL else [])
    return Package(
        code=info["tier"] + ("-wenskaart" if wens else ""),
        name=info["naam"] + (" wenskaart" if wens else ""),
        description=BESCHRIJVING[info["tier"]],
        price_cents=info["cents"],
        availability_months=info["maanden"],
        features=functies,
        max_gallery_photos=0 if wens else 12,
        highlights=highlights(info["tier"], wens),
        is_active=True,
    )


def highlights(indeling: str, wens: bool = False) -> list[str]:
    if wens:
        return ["Een persoonlijke groet, met eventueel een foto", f"{MAANDEN_ONLINE[indeling]} maanden online", "Eigen link en QR-code om te delen"]
    return [
        BESCHRIJVING[indeling],
        "Eigen tekst, foto, fotogalerij, verhaal, eigen muziek en extra vragen: alles inbegrepen",
        "Aanmeldformulier, afteller, locatie en agenda-knop",
        f"{MAANDEN_ONLINE[indeling]} maanden online, met eigen link en QR-code",
    ]


def is_wenskaart_code(code: str) -> bool:
    return (code or "").endswith("wenskaart")


# ---------------------------------------------------------------- teksten en overzichten voor de site

def _actieve_ontwerpen():
    from .models import Template

    return list(Template.objects.filter(is_active=True))


def beschikbaar(rij: str, ontwerpen=None) -> list[tuple[str, int]]:
    """De indelingen waarvoor er voor deze prijsrij minstens één zichtbaar, bestelbaar ontwerp is: [(indeling, cents)]. Een indeling zonder ontwerp
    (bijvoorbeeld Basis bij Kerst) wordt nooit als prijs getoond: de klant kan die niet kopen."""
    ontwerpen = _actieve_ontwerpen() if ontwerpen is None else ontwerpen
    gevonden = set()
    for t in ontwerpen:
        indeling = tier(t)
        if indeling is None:
            continue
        for occasion in t.occasions or []:
            if rij == "bedank":
                if occasion != "kerst":
                    gevonden.add(indeling)
            elif categorie(occasion, "") == rij or (rij == "kerst" and occasion == "kerst"):
                gevonden.add(indeling)
    return [(i, PRIJZEN[rij][TIERS.index(i)]) for i in TIERS if i in gevonden]


def zin(rij: str, ontwerpen=None) -> str:
    """Eén zin over wat deze soort kaart kost, alleen met wat echt te kiezen is. Bijvoorbeeld: 'Een kerstkaart kost € 24,95 (Luxe) of € 49,95 (Special),
    afhankelijk van het ontwerp; je ziet de prijs bij het ontwerp.'"""
    opties = beschikbaar(rij, ontwerpen)
    if not opties:
        return ""
    delen = [f"{format_euro(c)} ({TIER_NAAM[i]})" for i, c in opties]
    opsomming = delen[0] if len(delen) == 1 else ", ".join(delen[:-1]) + " of " + delen[-1]
    return f"Een {CATEGORIE_LABEL[rij].split(' / ')[0].lower()} kost {opsomming}, inclusief btw en eenmalig, afhankelijk van het ontwerp. De prijs staat bij elk ontwerp."


def vanaf_cents() -> int | None:
    """De laagste prijs die een klant nu echt kan betalen (over alle zichtbare ontwerpen, gelegenheden en kaartsoorten)."""
    ontwerpen = _actieve_ontwerpen()
    laagste = None
    for t in ontwerpen:
        for occasion in t.occasions or []:
            for soort in ("", "wenskaart"):
                cents = prijs_cents(t, occasion, soort)
                if cents is not None and (laagste is None or cents < laagste):
                    laagste = cents
    return laagste


def overzicht_tabel(ontwerpen=None) -> list[dict]:
    """De prijzentabel voor de website: per prijsrij de beschikbare indelingen (alleen rijen waar echt iets te kiezen is)."""
    ontwerpen = _actieve_ontwerpen() if ontwerpen is None else ontwerpen
    rijen = []
    for rij in ("kerst", "verjaardag", "zakelijk", "babyshower", "bruiloft", "jubileum_verloving", "bedank"):
        opties = dict(beschikbaar(rij, ontwerpen))
        if opties:
            rijen.append({"rij": rij, "label": CATEGORIE_LABEL[rij], "cellen": [{"tier": i, "naam": TIER_NAAM[i], "cents": opties.get(i)} for i in TIERS]})
    return rijen


def vanaf_per_tier(ontwerpen=None) -> dict:
    """De laagste prijs per indeling over alle zichtbare ontwerpen, gelegenheden en kaartsoorten: {'basis': '€ 9,95', 'luxe': ..., 'special': ...}."""
    ontwerpen = _actieve_ontwerpen() if ontwerpen is None else ontwerpen
    laagste: dict[str, int] = {}
    for t in ontwerpen:
        indeling = tier(t)
        if indeling is None:
            continue
        for occasion in t.occasions or []:
            for soort in ("", "wenskaart"):
                cents = prijs_cents(t, occasion, soort)
                if cents is not None and (indeling not in laagste or cents < laagste[indeling]):
                    laagste[indeling] = cents
    return {i: format_euro(laagste[i]) for i in TIERS if i in laagste}


def tekst_kwargs(rij: str = "") -> dict:
    """De invulwaarden voor de teksten op de site (core/content.py) in de nieuwe structuur: één zin over de prijs van deze soort kaart en de
    'vanaf'-prijzen. Alle sleutels staan er altijd in, zodat elke tekst (ook de oude) zonder fout wordt ingevuld."""
    vanaf = vanaf_per_tier()
    return {"prijszin": zin(rij) if rij else "", "vanaf": vanaf.get(BASIS, ""), "vanaf_luxe": vanaf.get(LUXE, ""), "vanaf_special": vanaf.get(SPECIAL, ""),
            "essentieel": "", "compleet": "", "wens": vanaf.get(BASIS, ""), "wens_special": vanaf.get(SPECIAL, ""), "special_zin": ""}
