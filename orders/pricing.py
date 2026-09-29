"""Prijsberekening aan de serverzijde.

De klant kiest alleen een pakket en eventueel extra opties. Welke betaalde
functies nodig zijn, volgt uit de inhoud van de uitnodiging (bijv. muziek of
een fotogalerij). Ontbreken die in het pakket, dan wordt de goedkoopste extra
optie automatisch toegevoegd. Het totaal wordt nooit uit de browser overgenomen.
"""
from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass
class Quote:
    package: Package
    lines: list[QuoteLine] = field(default_factory=list)
    features: set[str] = field(default_factory=set)
    max_gallery_photos: int = 0
    availability_months: int = 0
    selected_optional: list[str] = field(default_factory=list)

    @property
    def total_cents(self) -> int:
        return sum(line.total_cents for line in self.lines)

    @property
    def total_display(self) -> str:
        return format_euro(self.total_cents)

    @property
    def required_addon_lines(self) -> list[QuoteLine]:
        return [line for line in self.lines if line.reason]


def optional_addons() -> list[AddOn]:
    return list(AddOn.objects.filter(is_active=True, extra_months__gt=0).order_by("sort_order"))


def build_quote(content: dict, package: Package, optional_codes: list[str] | None = None, template_version=None) -> Quote:
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
            # Elke special heeft een eigen meerprijs (code special-<ontwerp>); zonder die optie is hij niet te bestellen.
            addon = special_addon(template_version.template)
            if addon is None:
                raise PricingError(f"{template_version.template.name} is een special en is nog niet te bestellen: de prijs wordt nog vastgesteld.")
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


def compare_packages(content: dict, optional_codes: list[str] | None = None, template_version=None) -> list[Quote]:
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
