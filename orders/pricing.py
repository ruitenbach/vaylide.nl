"""Prijsberekening aan de serverzijde.

De klant kiest alleen een pakket en eventueel extra opties. Welke betaalde
functies nodig zijn, volgt uit de inhoud van de uitnodiging (bijv. muziek of
een fotogalerij). Ontbreken die in het pakket, dan wordt de goedkoopste extra
optie automatisch toegevoegd. Het totaal wordt nooit uit de browser overgenomen.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from catalog import prijzen, wenskaart
from catalog.features import feature_label
from catalog.specials import is_special, special_addon
from catalog.models import AddOn, Package, format_euro
from invitations.content import required_features


class PricingError(ValueError):
    pass


@dataclass
class QuoteLine:
    code: str
    description: str
    unit_price_cents: int
    quantity: int = 1
    reason: str = ""

    @property
    def total_cents(self) -> int:
        return self.unit_price_cents * self.quantity

    @property
    def total_display(self) -> str:
        return format_euro(self.total_cents)

    @property
    def is_discount(self) -> bool:
        return self.code.startswith("korting:")

    @property
    def is_offer(self) -> bool:
        return self.code.startswith("korting:aanbieding:")

    @property
    def is_code_discount(self) -> bool:
        return self.is_discount and not self.is_offer


@dataclass
class Quote:
    package: Package
    lines: list[QuoteLine] = field(default_factory=list)
    features: set[str] = field(default_factory=set)
    max_gallery_photos: int = 0
    availability_months: int = 0
    selected_optional: list[str] = field(default_factory=list)
    discount_cents: int = 0     # kortingscode (app kortingen): staat als negatieve regel in `lines`
    discount_code: str = ""
    offer: object = None        # kortingen.aanbiedingen.OfferResult: de automatische aanbieding die in `lines` staat (of None)

    @property
    def total_cents(self) -> int:
        return sum(line.total_cents for line in self.lines)

    @property
    def subtotal_cents(self) -> int:
        """Het bedrag vóór korting."""
        return self.total_cents + self.discount_cents

    @property
    def total_display(self) -> str:
        return format_euro(self.total_cents)

    @property
    def required_addon_lines(self) -> list[QuoteLine]:
        return [line for line in self.lines if line.reason]

    @property
    def has_discount(self) -> bool:
        return self.discount_cents > 0

    @property
    def has_code(self) -> bool:
        return bool(self.discount_code)


def optional_addons() -> list[AddOn]:
    return list(AddOn.objects.filter(is_active=True, extra_months__gt=0).order_by("sort_order"))


def build_tier_quote(content: dict, template_version, occasion: str) -> Quote:
    """De nieuwe prijsstructuur: één regel, één prijs, geen toeslagen. De indeling van het ontwerp en de gelegenheid bepalen het bedrag (catalog.prijzen);
    alles wat de klant kan personaliseren zit erin. Zonder prijs voor dit ontwerp of deze gelegenheid is het niet te bestellen (nooit een verzonnen prijs).
    Eigen gezichten (Balzaal) zijn geen onderdeel van de indeling en blijven een aparte, nu uitgeschakelde optie."""
    soort = "wenskaart" if wenskaart.is_wenskaart(content) else ""
    if template_version is None or prijzen.prijs_cents(template_version, occasion, soort) is None:
        raise PricingError("Voor dit ontwerp en deze gelegenheid is op dit moment geen prijs beschikbaar. Kies een ander ontwerp.")
    package = prijzen.tier_package(template_version, occasion, soort)
    info = prijzen.prijs_info(template_version, occasion, soort)
    quote = Quote(package=package, features=set(package.features or []), max_gallery_photos=package.max_gallery_photos, availability_months=package.availability_months)
    naam = getattr(getattr(template_version, "template", template_version), "name", "")
    quote.lines.append(QuoteLine(code=f"tier:{package.code}:{info['rij']}", description=f"{package.name}: {naam} ({info['rij_label']})"[:200], unit_price_cents=package.price_cents))
    from kortingen import aanbiedingen

    aanbiedingen.apply_to_quote(quote, aanbiedingen.beste(template_version, occasion, soort))    # no-op zolang de vlag uit staat
    missing = required_features(content) - quote.features
    if missing:   # alleen eigen gezichten kunnen hier nog ontbreken
        raise PricingError(f"'{feature_label(sorted(missing)[0])}' is op dit moment niet beschikbaar. Zet dit onderdeel uit.")
    return quote


def build_wenskaart_quote(content: dict, template_version=None) -> Quote:
    """Een wenskaart: één vaste prijs (€ 14,95, bij een special-ontwerp € 24,95, incl. btw), geen pakketten, opties of meerprijzen."""
    package = wenskaart.package(template_version)
    quote = Quote(package=package, features=set(), max_gallery_photos=0, availability_months=package.availability_months)
    quote.lines.append(QuoteLine(code=f"pakket:{package.code}", description=package.name, unit_price_cents=package.price_cents))
    return quote


def build_quote(content: dict, package: Package | None, optional_codes: list[str] | None = None, template_version=None, occasion: str = "") -> Quote:
    if prijzen.actief():
        return build_tier_quote(content, template_version, occasion)
    if wenskaart.is_wenskaart(content):
        return build_wenskaart_quote(content, template_version)
    if not package.is_active:
        raise PricingError("Dit pakket is niet meer beschikbaar.")
    quote = Quote(
        package=package,
        features=set(package.features or []),
        max_gallery_photos=package.max_gallery_photos,
        availability_months=package.availability_months,
    )
    quote.lines.append(QuoteLine(code=f"pakket:{package.code}", description=f"Pakket {package.name}", unit_price_cents=package.price_cents))
    needed = required_features(content)
    if template_version is not None and is_special(template_version):
        needed.add("special")
    for feature in sorted(needed - quote.features):
        if feature == "special":
            # Elke special kan een eigen meerprijs hebben (code special-<ontwerp>). Zonder die optie geldt tijdelijk
            # gewoon de pakketprijs (keuze van de eigenaar, september 2026).
            addon = special_addon(template_version.template)
            if addon is None:
                quote.features.add(feature)
                continue
        else:
            addon = AddOn.objects.filter(is_active=True, feature=feature).order_by("price_cents").first()
        if addon is None:
            raise PricingError(f"'{feature_label(feature)}' is op dit moment niet beschikbaar. Zet dit onderdeel uit of kies een ander pakket.")
        quote.lines.append(
            QuoteLine(
                code=f"optie:{addon.code}",
                description=addon.name,
                unit_price_cents=addon.price_cents,
                reason=f"Toegevoegd omdat je {feature_label(feature).lower()} gebruikt",
            )
        )
        quote.features.add(feature)
        quote.max_gallery_photos = max(quote.max_gallery_photos, addon.gallery_photos)
    allowed = {a.code: a for a in optional_addons()}
    for code in optional_codes or []:
        addon = allowed.get(code)
        if addon is None:
            raise PricingError("Een gekozen extra optie is niet (meer) beschikbaar.")
        if code in quote.selected_optional:
            continue
        quote.selected_optional.append(code)
        quote.lines.append(QuoteLine(code=f"optie:{addon.code}", description=addon.name, unit_price_cents=addon.price_cents))
        quote.availability_months += addon.extra_months
    return quote


def compare_packages(content: dict, optional_codes: list[str] | None = None, template_version=None, occasion: str = "") -> list[Quote]:
    if prijzen.actief():
        return [build_tier_quote(content, template_version, occasion)]
    if wenskaart.is_wenskaart(content):
        return [build_wenskaart_quote(content, template_version)]
    quotes = []
    for package in Package.objects.filter(is_active=True).order_by("sort_order", "price_cents"):
        try:
            quotes.append(build_quote(content, package, optional_codes, template_version=template_version))
        except PricingError:
            continue
    return quotes


def recommended(quotes: list[Quote]) -> Quote | None:
    if not quotes:
        return None
    # Goedkoopste totaal; bij gelijke prijs het pakket met de meeste functies.
    return sorted(quotes, key=lambda q: (q.total_cents, -len(q.features)))[0]
