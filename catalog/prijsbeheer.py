"""Prijzenbeheer: de verkoopprijzen in de database (catalog.PriceRule), met bevestiging, logboek en terugdraaien.

Eén bron, twee standen (settings.PRICES_ADMIN, VIERLIEF_PRIJZENBEHEER, standaard UIT):
- Uit: de bedragen uit catalog/prijzen.py (PRIJZEN) gelden, precies zoals voorheen. Beheer toont ze alleen ter inzage.
- Aan: de bedragen komen uit de database. Ontbreekt een bedrag of is het ongeldig (geen geheel getal tussen € 1,00 en € 500,00), dan is dat bedrag
  `None`: de kaart is dan niet te bestellen (prijzen.prijs_cents geeft None, de offerte weigert, er ontstaat geen bestelling). Er is bewust GEEN stille
  terugval op de code-bedragen: een afwijkende prijs bij de kassa is erger dan een tijdelijk niet bestelbare kaart. Beheer meldt het probleem bovenaan.

Alle prijzen zijn in centen, inclusief btw. Het btw-deel volgt uit kortingen.services.vat_part_cents (zelfde berekening als bij kortingen).
De prijstabel wordt hoogstens één keer per verzoek gelezen (PrijsCacheMiddleware); buiten een verzoek wordt altijd vers gelezen, zodat er nergens een
verouderde prijs kan blijven hangen."""
from __future__ import annotations

import contextlib
import contextvars
import logging
import re
from dataclasses import dataclass, field

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from . import prijzen
from .models import PriceChange, PriceChangeSet, PriceRule, Template, format_euro

log = logging.getLogger("vaylide.prijzen")

MIN_CENTS = 100          # € 1,00: gelijk aan het minimale bedrag dat een klant betaalt (settings.DISCOUNT_MIN_TOTAL_CENTS)
MAX_CENTS = 50000        # € 500,00: vangt een tikfout als 2995 in plaats van 29,95
GROTE_SPRONG_PROCENT = 50
REDEN_MAX = 300

# De volgorde en de namen in Beheer. De prijsrij 'bedank' heet in Beheer 'Wenskaart buiten Kerst' (op de site blijft de naam 'Bedankkaart / felicitatie').
RIJEN = ("kerst", "verjaardag", "zakelijk", "babyshower", "bruiloft", "jubileum_verloving", "bedank", "geboorte", "savethedate")
BEHEER_LABEL = {**prijzen.CATEGORIE_LABEL, "bedank": "Wenskaart buiten Kerst"}
# Welke gelegenheden of kaartsoorten een prijsrij raakt: zo is duidelijk dat Verloving en Jubileum één prijsrij delen.
GELDT_VOOR = {
    "kerst": "Kerst, ook een wenskaart bij Kerst",
    "verjaardag": "Verjaardag",
    "zakelijk": "Zakelijk evenement",
    "babyshower": "Babyshower en gender reveal",
    "bruiloft": "Bruiloft",
    "jubileum_verloving": "Verloving én Jubileum: beide gebruiken dezelfde prijsrij, een wijziging geldt voor allebei",
    "bedank": "Een wenskaart bij elke gelegenheid behalve Kerst",
    "geboorte": "Nog geen gelegenheid in de site",
    "savethedate": "Nog geen gelegenheid in de site",
}


def enabled() -> bool:
    return bool(getattr(settings, "PRICES_ADMIN", False)) and prijzen.actief()


# ---------------------------------------------------------------- lezen (één query per verzoek)

_scope: contextvars.ContextVar = contextvars.ContextVar("prijsbeheer_scope", default=None)


class PrijsCacheMiddleware:
    """Houdt de prijstabel binnen één verzoek vast. Over verzoeken heen wordt niets onthouden (geen proces-cache): een prijswijziging werkt direct overal."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _scope.set({"regels": None, "gemeld": set()})
        try:
            return self.get_response(request)
        finally:
            _scope.reset(token)


@contextlib.contextmanager
def cache_scope():
    """Voor commando's en taken buiten een verzoek: de tabel eenmaal lezen binnen dit blok."""
    token = _scope.set({"regels": None, "gemeld": set()})
    try:
        yield
    finally:
        _scope.reset(token)


def invalidate() -> None:
    scope = _scope.get()
    if scope is not None:
        scope["regels"] = None


def geldig(cents) -> bool:
    return isinstance(cents, int) and not isinstance(cents, bool) and MIN_CENTS <= cents <= MAX_CENTS


def regels() -> dict[tuple[str, str], int]:
    scope = _scope.get()
    if scope is not None and scope["regels"] is not None:
        return scope["regels"]
    gelezen = {(r.rij, r.tier): r.price_cents for r in PriceRule.objects.all()}
    if scope is not None:
        scope["regels"] = gelezen
    return gelezen


def _meld_een_keer(sleutel: str, bericht: str) -> None:
    scope = _scope.get()
    if scope is not None:
        if sleutel in scope["gemeld"]:
            return
        scope["gemeld"].add(sleutel)
    log.error(bericht)


def lees(rij: str, tier: str) -> int | None:
    """Het geldende bedrag van één cel, in centen incl. btw, of None als er (met databaseprijzen aan) geen geldig bedrag is. None = niet te bestellen."""
    if rij not in prijzen.PRIJZEN or tier not in prijzen.TIERS:
        return None
    if not enabled():
        return prijzen.PRIJZEN[rij][prijzen.TIERS.index(tier)]
    cents = regels().get((rij, tier))
    if cents is None:
        _meld_een_keer(f"mist:{rij}:{tier}", f"Prijsbeheer: geen databaseprijs voor {rij}/{tier}; die kaart is niet te bestellen.")
        return None
    if not geldig(cents):
        _meld_een_keer(f"ongeldig:{rij}:{tier}", f"Prijsbeheer: ongeldige databaseprijs {cents} voor {rij}/{tier}; die kaart is niet te bestellen.")
        return None
    return cents


# ---------------------------------------------------------------- het overzicht voor Beheer

@dataclass
class Cel:
    rij: str
    tier: str
    cents: int | None          # None: ontbreekt of ongeldig (alleen met databaseprijzen aan)
    ontwerpen: int             # zichtbare, bestelbare ontwerpen in deze cel; 0 = nu niet te koop
    code_cents: int            # het bedrag in de code (ter vergelijking)
    db_cents: int | None       # het bedrag in de database (ook als de vlag uit staat, ter vergelijking)

    @property
    def display(self) -> str:
        return format_euro(self.cents) if self.cents is not None else "ontbreekt"

    @property
    def sleutel(self) -> str:
        return f"p_{self.rij}_{self.tier}"

    @property
    def probleem(self) -> bool:
        return self.cents is None

    @property
    def euro_invoer(self) -> str:
        return f"{self.cents // 100},{self.cents % 100:02d}" if self.cents is not None else ""


@dataclass
class Rij:
    rij: str
    label: str
    geldt_voor: str
    cellen: list[Cel] = field(default_factory=list)
    gedeeld: bool = False


def ontwerpen_per_cel() -> dict[tuple[str, str], int]:
    """Hoeveel zichtbare ontwerpen er per prijsrij en indeling te koop zijn (ook als wenskaart)."""
    gevonden: dict[tuple[str, str], set[str]] = {}
    for t in Template.objects.filter(is_active=True):
        indeling = prijzen.tier(t)
        if indeling is None:
            continue
        for occasion in t.occasions or []:
            for soort in ("", "wenskaart"):
                rij = prijzen.categorie(occasion, soort)
                if rij:
                    gevonden.setdefault((rij, indeling), set()).add(t.slug)
    return {k: len(v) for k, v in gevonden.items()}


def raster() -> list[Rij]:
    tellers = ontwerpen_per_cel()
    db = {(r.rij, r.tier): r.price_cents for r in PriceRule.objects.all()}
    uit = []
    for rij in RIJEN:
        r = Rij(rij=rij, label=BEHEER_LABEL[rij], geldt_voor=GELDT_VOOR[rij], gedeeld=(rij == "jubileum_verloving"))
        for i, tier in enumerate(prijzen.TIERS):
            r.cellen.append(Cel(rij=rij, tier=tier, cents=lees(rij, tier), ontwerpen=tellers.get((rij, tier), 0),
                                code_cents=prijzen.PRIJZEN[rij][i], db_cents=db.get((rij, tier))))
        uit.append(r)
    return uit


def problemen() -> list[str]:
    """Cellen die nu te koop zouden zijn maar geen geldig bedrag hebben (alleen met databaseprijzen aan). Beheer toont dit bovenaan."""
    if not enabled():
        return []
    return [f"{BEHEER_LABEL[c.rij]} · {prijzen.TIER_NAAM[c.tier]}" for r in raster() for c in r.cellen if c.probleem and c.ontwerpen > 0]


def verschillen_met_code() -> list[str]:
    """De cellen waar de database afwijkt van de code of ontbreekt (ook met de vlag uit). Leeg = de database is een exacte kopie van de code."""
    uit = []
    db = {(r.rij, r.tier): r.price_cents for r in PriceRule.objects.all()}
    for rij in RIJEN:
        for i, tier in enumerate(prijzen.TIERS):
            code, gelezen = prijzen.PRIJZEN[rij][i], db.get((rij, tier))
            if gelezen != code:
                uit.append(f"{rij}/{tier}: code {format_euro(code)}, database {format_euro(gelezen) if gelezen is not None else 'ontbreekt'}")
    return uit


# ---------------------------------------------------------------- invoer en controle

class PrijsFout(Exception):
    """Een wijziging die niet doorgaat. `fouten` hoort per veld (sleutel 'p_<rij>_<tier>') of algemeen (sleutel '')."""

    def __init__(self, fouten: dict[str, str]):
        super().__init__("; ".join(fouten.values()))
        self.fouten = fouten


_EURO = re.compile(r"^\s*(?:€|eur)?\s*(\d{1,6})(?:[.,](\d{1,2}))?\s*$", re.IGNORECASE)


def parse_euro(tekst: str) -> int:
    """'29,95', '29.95', '€ 29,95' of '30' naar centen. Meer dan twee decimalen, negatief, leeg, letters of '1e3' is een fout."""
    m = _EURO.match(tekst or "")
    if not m:
        raise ValueError("Vul een bedrag in met maximaal twee decimalen, bijvoorbeeld 29,95.")
    euro, rest = int(m.group(1)), (m.group(2) or "").ljust(2, "0")
    return euro * 100 + int(rest or 0)


def alle_cellen() -> list[tuple[str, str]]:
    return [(rij, tier) for rij in RIJEN for tier in prijzen.TIERS]


def huidige() -> dict[tuple[str, str], int | None]:
    return {cel: lees(*cel) for cel in alle_cellen()}


@dataclass
class Beoordeling:
    nieuw: dict[tuple[str, str], int]          # alleen de cellen die echt veranderen
    oud: dict[tuple[str, str], int | None]
    fouten: dict[str, str]
    waarschuwingen: list[str]
    grote_sprong: bool = False

    @property
    def ok(self) -> bool:
        return not self.fouten


def beoordeel(invoer: dict[tuple[str, str], int | str]) -> Beoordeling:
    """Controleert een voorstel. `invoer` mag tekst (uit het formulier) of centen bevatten; cellen die ontbreken blijven zoals ze zijn."""
    nu = huidige()
    fouten: dict[str, str] = {}
    gewenst: dict[tuple[str, str], int] = {}
    for cel, waarde in invoer.items():
        rij, tier = cel
        sleutel = f"p_{rij}_{tier}"
        if cel not in nu:
            fouten[sleutel] = "Onbekende prijs."
            continue
        if isinstance(waarde, str):
            try:
                waarde = parse_euro(waarde)
            except ValueError as exc:
                fouten[sleutel] = str(exc)
                continue
        if not geldig(waarde):
            fouten[sleutel] = f"Een prijs ligt tussen {format_euro(MIN_CENTS)} en {format_euro(MAX_CENTS)}."
            continue
        gewenst[cel] = waarde
    eind = {cel: gewenst.get(cel, nu[cel]) for cel in nu}
    for rij in RIJEN:
        trio = [eind[(rij, t)] for t in prijzen.TIERS]
        if None in trio:
            continue
        for lager, hoger, naam in ((0, 1, "Luxe"), (1, 2, "Special")):
            if trio[hoger] < trio[lager]:
                fouten[f"p_{rij}_{prijzen.TIERS[hoger]}"] = f"{naam} kan niet goedkoper zijn dan {prijzen.TIER_NAAM[prijzen.TIERS[lager]]}."
    nieuw = {cel: c for cel, c in gewenst.items() if nu[cel] != c}
    waarschuwingen, sprong = [], False
    for (rij, tier), c in nieuw.items():
        oud = nu[(rij, tier)]
        if oud and abs(c - oud) * 100 > oud * GROTE_SPRONG_PROCENT:
            sprong = True
            waarschuwingen.append(f"{BEHEER_LABEL[rij]} · {prijzen.TIER_NAAM[tier]} verandert met meer dan {GROTE_SPRONG_PROCENT}%: {format_euro(oud)} wordt {format_euro(c)}.")
    for rij in RIJEN:
        trio = [eind[(rij, t)] for t in prijzen.TIERS]
        if None not in trio and (trio[0] == trio[1] or trio[1] == trio[2]) and any((rij, t) in nieuw for t in prijzen.TIERS):
            waarschuwingen.append(f"{BEHEER_LABEL[rij]}: twee indelingen hebben nu dezelfde prijs.")
    return Beoordeling(nieuw=nieuw, oud=nu, fouten=fouten, waarschuwingen=waarschuwingen, grote_sprong=sprong)


def btw_regel(cents: int) -> dict:
    from kortingen.services import vat_part_cents

    btw = vat_part_cents(cents)
    return {"btw": btw, "excl": cents - btw, "tarief": settings.VAT_RATE_PERCENT}


def impact(nieuw: dict[tuple[str, str], int]) -> dict:
    """Wat een wijziging raakt: ontwerpen per cel, en de actieve of geplande kortingscodes en aanbiedingen op die rij en indeling."""
    from kortingen.models import DiscountCode, Offer

    tellers = ontwerpen_per_cel()
    rijen_tiers = set(nieuw)

    def raakt(occasions, tiers) -> bool:
        for rij, tier in rijen_tiers:
            if tiers and tier not in tiers:
                continue
            if not occasions:
                return True
            for o in occasions:
                if prijzen.categorie(o, "") == rij or (rij == "bedank" and o != "kerst"):
                    return True
        return False

    now = timezone.now()
    codes = [c for c in DiscountCode.objects.all() if c.status(now) in ("actief", "gepland") and raakt(c.occasions, c.tiers)]
    aanbod = [o for o in Offer.objects.all() if o.status(now) in ("actief", "gepland") and raakt(o.occasions, o.tiers)]
    return {"ontwerpen": {cel: tellers.get(cel, 0) for cel in nieuw}, "codes": codes, "aanbiedingen": aanbod}


def verhoging_voor_aanbieding(nieuw: dict[tuple[str, str], int], oud: dict) -> list[str]:
    """Een prijsverhoging vlak voor een geplande aanbieding: de doorgestreepte 'was'-prijs volgt de laagste prijs van de 30 dagen ervoor."""
    from datetime import timedelta

    from kortingen.models import Offer

    if not any(c > (oud.get(cel) or 0) for cel, c in nieuw.items()):
        return []
    now = timezone.now()
    grens = now + timedelta(days=getattr(settings, "AANBIEDING_REFERENTIE_DAGEN", 30))
    return [f"Aanbieding '{o.name}' start binnen {getattr(settings, 'AANBIEDING_REFERENTIE_DAGEN', 30)} dagen. Bij een prijsverhoging toont die geen doorgestreepte prijs of een lagere."
            for o in Offer.objects.filter(is_active=True, starts_at__gt=now, starts_at__lte=grens)]


# ---------------------------------------------------------------- doorvoeren en logboek

def stempel() -> int:
    """Het nummer van de laatste prijswijziging. Het formulier neemt het mee: is er intussen iets veranderd, dan weigert de server."""
    last = PriceChangeSet.objects.order_by("-id").values_list("id", flat=True).first()
    return last or 0


def voer_door(user, invoer: dict[tuple[str, str], int | str], *, reden: str, stempel_in: int, kind: str = PriceChangeSet.Kind.CHANGE,
              reverts: PriceChangeSet | None = None, grote_sprong_bevestigd: bool = False) -> PriceChangeSet:
    """Controleert opnieuw (nooit op het formulier vertrouwen) en schrijft de wijziging, het logboek en de prijshistorie in één transactie."""
    from beheer import rollen

    if not enabled():
        raise PrijsFout({"": "Prijsbeheer staat uit. Er is niets gewijzigd."})
    benodigd = rollen.mag_prijzen_terugdraaien if kind == PriceChangeSet.Kind.REVERT else rollen.mag_prijzen_wijzigen
    if not benodigd(user):
        raise PermissionError("Geen recht om prijzen te wijzigen.")
    reden = (reden or "").strip()
    if len(reden) < 3:
        raise PrijsFout({"reden": "Geef een korte reden op (minstens 3 tekens)."})
    if len(reden) > REDEN_MAX:
        raise PrijsFout({"reden": f"Houd de reden onder de {REDEN_MAX} tekens."})
    with transaction.atomic():
        list(PriceRule.objects.select_for_update().order_by("id"))     # serialiseert gelijktijdige wijzigingen (PostgreSQL)
        if stempel() != stempel_in:
            raise PrijsFout({"": "Er is intussen een andere prijswijziging doorgevoerd. Bekijk de nieuwe stand en probeer het opnieuw."})
        invalidate()
        b = beoordeel(invoer)
        if not b.ok:
            raise PrijsFout(b.fouten)
        if not b.nieuw:
            raise PrijsFout({"": "Er is niets gewijzigd."})
        if b.grote_sprong and not grote_sprong_bevestigd:
            raise PrijsFout({"": "Een grote prijssprong moet je apart bevestigen."})
        zet = PriceChangeSet.objects.create(user=user, kind=kind, reason=reden, reverts=reverts)
        for (rij, tier), cents in b.nieuw.items():
            PriceChange.objects.create(change_set=zet, rij=rij, tier=tier, old_cents=b.oud[(rij, tier)], new_cents=cents)
            PriceRule.objects.update_or_create(rij=rij, tier=tier, defaults={"price_cents": cents, "updated_by": user})
        invalidate()
        from kortingen.aanbiedingen import sync_history

        sync_history(now=zet.created_at)       # de prijshistorie (referentieprijs bij aanbiedingen) loopt nooit achter op de prijs
        invalidate()
    log.info("Prijswijziging #%s door %s: %s", zet.pk, getattr(user, "pk", None), {f"{r}/{t}": c for (r, t), c in b.nieuw.items()})
    return zet


def terugdraai_voorstel(zet: PriceChangeSet) -> list[dict]:
    """De cellen van een set met het bedrag van vóór de set. Een cel die intussen opnieuw is gewijzigd staat er wel bij, maar niet aangevinkt."""
    nu = huidige()
    uit = []
    for ch in zet.changes.all():
        if ch.old_cents is None:
            continue
        cel = (ch.rij, ch.tier)
        uit.append({"rij": ch.rij, "tier": ch.tier, "label": BEHEER_LABEL.get(ch.rij, ch.rij), "tier_naam": prijzen.TIER_NAAM.get(ch.tier, ch.tier),
                    "huidig": nu.get(cel), "terug_naar": ch.old_cents, "gezet": ch.new_cents, "sleutel": f"p_{ch.rij}_{ch.tier}",
                    "nog_zoals_gezet": nu.get(cel) == ch.new_cents})
    return uit
