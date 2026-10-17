"""Automatische aanbiedingen: welke aanbieding geldt voor een kaart, wat is de actieprijs en mag er een doorgestreepte prijs bij.

Kernregels:
- Eén rekenpad. De aanbieding wordt een negatieve regel in de offerte (orders.pricing.build_tier_quote), net als een kortingscode. Kaart, ontwerppagina,
  Studio, bon, bestelling, Mollie-bedrag en e-mail tonen daardoor hetzelfde bedrag. De vaste Basis-, Luxe- en Special-prijzen (catalog.prijzen) blijven ongemoeid.
- Alleen met settings.OFFERS_ENABLED (standaard uit, los van de kortingscodes) en alleen in de nieuwe prijsstructuur.
- Meerdere aanbiedingen stapelen niet: de voordeligste geldt. Aanbieding en kortingscode stapelen ook niet (zie kortingen.services.toepassen).
- Een doorgestreepte referentieprijs staat er alleen bij als de prijshistorie aantoont dat die klopt: de laagste prijs die in de AANBIEDING_REFERENTIE_DAGEN
  dagen vóór de start van de aanbieding gold (ook als dat een eerdere aanbieding was). Ontbreekt de historie, of is er twijfel, dan staat er alleen
  de actieprijs. Er is bewust geen uitzondering voor nieuwe ontwerpen of 'progressieve' verlagingen ingebouwd: zie docs/AANBIEDINGEN.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from catalog import prijzen
from catalog.models import format_euro
from .models import Offer, PriceStand

LINE_PREFIX = "korting:aanbieding:"


@dataclass
class OfferResult:
    offer: Offer
    regular_cents: int
    discount_cents: int
    reference_cents: int | None = None
    reference_reason: str = ""

    @property
    def price_cents(self) -> int:
        return self.regular_cents - self.discount_cents

    @property
    def price_display(self) -> str:
        return format_euro(self.price_cents)

    @property
    def reference_display(self) -> str:
        return format_euro(self.reference_cents) if self.reference_cents else ""

    @property
    def ends_at(self):
        return self.offer.ends_at

    @property
    def name(self) -> str:
        return self.offer.name


def enabled() -> bool:
    return bool(getattr(settings, "OFFERS_ENABLED", False)) and prijzen.actief()


def reference_days() -> int:
    return int(getattr(settings, "AANBIEDING_REFERENTIE_DAGEN", 30))


def _template(template_or_version):
    return getattr(template_or_version, "template", None) or template_or_version


def history_key(template_or_version, occasion: str, soort: str = "") -> str | None:
    rij = prijzen.categorie(occasion, soort)
    slug = getattr(_template(template_or_version), "slug", "")
    return f"{slug}:{rij}" if slug and rij else None


# ------------------------------------------------------------------ prijshistorie

def sync_history(now=None, since=None) -> int:
    """Legt de huidige gewone prijzen vast: een nieuwe stand als het bedrag veranderde of nog niet bestond. Idempotent; draait bij migrate en als
    management command. `since` (alleen als de eigenaar bevestigt vanaf wanneer een prijs echt geldt) geeft een nieuwe stand een eerdere begindatum."""
    from catalog.models import Template

    now = now or timezone.now()
    changed = 0
    wanted = {}
    for template in Template.objects.filter(is_active=True):
        for occasion in template.occasions or []:
            for soort in ("", "wenskaart"):
                key, cents = history_key(template, occasion, soort), prijzen.prijs_cents(template, occasion, soort)
                if key and cents is not None:
                    wanted[key] = cents
    open_rows = {r.key: r for r in PriceStand.objects.filter(until__isnull=True)}
    for key, cents in wanted.items():
        row = open_rows.get(key)
        if row is not None and row.price_cents == cents:
            continue
        start = now
        if row is not None:
            row.until = now
            row.save(update_fields=["until"])
        elif since is not None:
            start = since
        PriceStand.objects.create(key=key, price_cents=cents, since=start)
        changed += 1
    return changed


class Context:
    """Laadt aanbiedingen en prijshistorie hoogstens één keer per pagina."""

    def __init__(self, now=None):
        self.now = now or timezone.now()
        self._active = None
        self._started = None
        self._history = {}

    @property
    def active(self) -> list[Offer]:
        if self._active is None:
            self._active = list(Offer.objects.filter(is_active=True, starts_at__lte=self.now, ends_at__gte=self.now).prefetch_related("templates"))
        return self._active

    @property
    def started(self) -> list[Offer]:
        """Alle aanbiedingen die ooit zijn gestart (ook uitgezette): voor de referentie tellen ze mee zolang niet vaststaat dat ze niet liepen."""
        if self._started is None:
            self._started = list(Offer.objects.filter(starts_at__lte=self.now).prefetch_related("templates"))
        return self._started

    def preload_history(self) -> None:
        """Alle standen in één keer (voor een overzicht in Beheer)."""
        self._history = {}
        for row in PriceStand.objects.order_by("key", "since"):
            self._history.setdefault(row.key, []).append(row)

    def history(self, key: str) -> list[PriceStand]:
        if key not in self._history:
            self._history[key] = list(PriceStand.objects.filter(key=key).order_by("since"))
        return self._history[key]


def matches(offer: Offer, template, occasion: str) -> bool:
    if offer.occasions and occasion not in offer.occasions:
        return False
    if offer.tiers and prijzen.tier(template) not in offer.tiers:
        return False
    if offer.whole_collection:
        return True
    return any(t.pk == template.pk for t in offer.templates.all())


def discount_for(offer: Offer, regular_cents: int) -> int:
    """De korting op het gewone bedrag, nooit zo hoog dat het te betalen bedrag onder het minimum komt (kortingen.services.min_total_cents)."""
    from .services import min_total_cents

    if offer.kind == Offer.Kind.PERCENT:
        raw = (regular_cents * (offer.percent or 0) + 50) // 100
    else:
        raw = min(offer.amount_cents or 0, regular_cents)
    return max(0, min(raw, regular_cents - min_total_cents()))


def reference_for(offer: Offer, template, occasion: str, soort: str, regular_cents: int, price_cents: int, ctx: Context) -> tuple[int | None, str]:
    """(referentieprijs, reden). De referentie is de laagste prijs in de dagen vóór de start van de aanbieding. Alleen als de historie die hele
    periode dekt, de huidige stand klopt en de referentie hoger is dan de actieprijs. Anders (None, uitleg voor Beheer)."""
    if not offer.show_reference:
        return None, "Doorgestreepte prijs staat uit voor deze aanbieding."
    key = history_key(template, occasion, soort)
    rows = ctx.history(key) if key else []
    if not rows:
        return None, "Geen prijshistorie voor dit ontwerp."
    current = next((r for r in rows if r.until is None), None)
    if current is None or current.price_cents != regular_cents:
        return None, "De prijshistorie loopt achter op de huidige prijs."
    days = reference_days()
    window_start = offer.starts_at - timedelta(days=days)
    first = rows[0].since
    if first > window_start:
        return None, f"De prijshistorie begint pas op {first:%d-%m-%Y}; een doorgestreepte prijs kan vanaf {(first + timedelta(days=days)):%d-%m-%Y} (start van de aanbieding op of na die datum)."
    inside = [r for r in rows if r.since < offer.starts_at and (r.until is None or r.until > window_start)]
    lowest = min(r.price_cents for r in inside) if inside else regular_cents
    for other in ctx.started:
        if other.pk == offer.pk or other.starts_at >= offer.starts_at or other.ends_at <= window_start:
            continue
        if matches(other, template, occasion):
            lowest = min(lowest, lowest - discount_for(other, lowest))    # een eerdere aanbieding verlaagt de referentie
    if lowest <= price_cents:
        return None, "In de voorgaande periode gold al een prijs die even laag of lager is."
    return lowest, ""


def _result(offer: Offer, template, occasion: str, soort: str, regular: int, ctx: Context) -> OfferResult | None:
    discount = discount_for(offer, regular)
    if discount <= 0:
        return None
    reference, reason = reference_for(offer, template, occasion, soort, regular, regular - discount, ctx)
    return OfferResult(offer=offer, regular_cents=regular, discount_cents=discount, reference_cents=reference, reference_reason=reason)


def beste(template_version, occasion: str, soort: str = "", *, ctx: Context | None = None) -> OfferResult | None:
    """De voordeligste aanbieding die nu voor deze kaart geldt (of None). Aanbiedingen stapelen niet."""
    if not enabled() or template_version is None:
        return None
    regular = prijzen.prijs_cents(template_version, occasion, soort)
    if regular is None:
        return None
    ctx = ctx or Context()
    template = _template(template_version)
    best = None
    for offer in ctx.active:
        if not matches(offer, template, occasion):
            continue
        res = _result(offer, template, occasion, soort, regular, ctx)
        if res and (best is None or (res.discount_cents, -res.offer.ends_at.timestamp(), -res.offer.pk) > (best.discount_cents, -best.offer.ends_at.timestamp(), -best.offer.pk)):
            best = res
    return best


def beste_per_kaart(templates, occasion: str, soort: str = "") -> dict:
    """Voor een overzicht van kaarten: {slug: OfferResult}, met één keer laden. Leeg zolang de vlag uit staat."""
    if not enabled():
        return {}
    ctx = Context()
    if not ctx.active:
        return {}
    uit = {}
    for template in templates:
        res = beste(template, occasion, soort, ctx=ctx)
        if res:
            uit[template.slug] = res
    return uit


# ------------------------------------------------------------------ offerte

def apply_to_quote(quote, result: OfferResult | None) -> None:
    from orders.pricing import QuoteLine

    if result is None:
        return
    quote.lines.append(QuoteLine(code=f"{LINE_PREFIX}{result.offer.pk}", description=f"Aanbieding {result.offer.name}"[:200], unit_price_cents=-result.discount_cents))
    quote.discount_cents = result.discount_cents
    quote.offer = result


def remove_from_quote(quote) -> None:
    quote.lines = [line for line in quote.lines if not line.code.startswith(LINE_PREFIX)]
    quote.discount_cents = 0
    quote.offer = None


# ------------------------------------------------------------------ weergave

def prijs(template_version, occasion: str, soort: str = "", *, res: OfferResult | None = None, ctx: Context | None = None) -> dict | None:
    """catalog.prijzen.prijs_info plus de aanbieding: 'aanbieding' (OfferResult of None), 'nu_cents', 'nu_display' en 'nu_label' ('Luxe € 29,95').
    Alles wat een pagina over de prijs toont, komt hieruit; het bedrag is hetzelfde als in de offerte (zie orders.pricing.build_tier_quote)."""
    info = prijzen.prijs_info(template_version, occasion, soort)
    if info is None:
        return None
    res = res if res is not None else beste(template_version, occasion, soort, ctx=ctx)
    nu = res.price_cents if res else info["cents"]
    return {**info, "aanbieding": res, "nu_cents": nu, "nu_display": format_euro(nu), "nu_label": f"{info['naam']} {format_euro(nu)}"}


def reference_overview(offer: Offer) -> dict:
    """Voor Beheer: bij hoeveel ontwerpen (in de gelegenheden van de aanbieding) mag een doorgestreepte prijs, en waarom niet bij de rest."""
    from catalog.models import Template

    ctx = Context(now=offer.starts_at)
    ctx.preload_history()
    toegestaan = totaal = 0
    redenen: dict[str, int] = {}
    for template in Template.objects.filter(is_active=True):
        for occasion in template.occasions or []:
            if (offer.occasions and occasion not in offer.occasions) or prijzen.prijs_cents(template, occasion, "") is None:
                continue
            if offer.tiers and prijzen.tier(template) not in offer.tiers:
                continue
            if not offer.whole_collection and not offer.templates.filter(pk=template.pk).exists():
                continue
            regular = prijzen.prijs_cents(template, occasion, "")
            discount = discount_for(offer, regular)
            if discount <= 0:
                continue
            totaal += 1
            ref, reason = reference_for(offer, template, occasion, "", regular, regular - discount, ctx)
            if ref:
                toegestaan += 1
            else:
                redenen[reason] = redenen.get(reason, 0) + 1
    return {"totaal": totaal, "toegestaan": toegestaan, "redenen": sorted(redenen.items(), key=lambda r: -r[1])}
