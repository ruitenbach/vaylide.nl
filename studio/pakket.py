"""Het pakket in het samenstellen: kiezen bij de start, labels bij de onderdelen en de upgrade bij Bestellen.

Prijzen komen altijd uit Beheer (Package en AddOn); hier wordt niets vastgelegd.
"""
from __future__ import annotations

from catalog.features import feature_label
from catalog.models import AddOn, Package, format_euro

# Onderdelen die bij Essentieel los bij te kopen zijn, en in welke stap je ze toevoegt.
FEATURE_STEPS = {"story": "fotos", "gallery": "fotos", "music": "fotos", "extra_questions": "aanmelden"}


def active_packages() -> list[Package]:
    return list(Package.objects.filter(is_active=True).order_by("sort_order", "price_cents"))


def default_package(packages: list[Package]) -> Package | None:
    return next((p for p in packages if p.is_featured), packages[0] if packages else None)


def chosen_package(invitation, packages: list[Package] | None = None) -> Package | None:
    packages = active_packages() if packages is None else packages
    return next((p for p in packages if p.code == invitation.package_code), None)


def feature_badges(package: Package | None) -> dict[str, str]:
    """Het label bij verhaal, galerij, muziek en extra vragen in de editor."""
    badges = {}
    for feature in FEATURE_STEPS:
        if package is None:
            badges[feature] = "Compleet of extra optie"
        elif feature in (package.features or []):
            badges[feature] = f"In {package.name}"
        else:
            addon = AddOn.objects.filter(is_active=True, feature=feature).order_by("price_cents").first()
            badges[feature] = f"Extra optie · {format_euro(addon.price_cents)}" if addon else "Niet in je pakket"
    return badges


def looptijd_uitleg(packages: list[Package], wenskaart_pakket: Package | None = None) -> str:
    """De uitleg bij 'Hoe lang blijft mijn kaart online?', uit dezelfde pakketten als de bestelling (Beheer)."""
    vanaf = "gerekend vanaf de bevestigde betaling"
    if wenskaart_pakket is not None:
        return f"Je wenskaart blijft {wenskaart_pakket.availability_months} maanden online, {vanaf}."
    if not packages:
        return ""
    eerste, *rest = packages
    if not rest:
        return f"Met {eerste.name} blijft je kaart {eerste.availability_months} maanden online, {vanaf}."
    overige = ". ".join(f"Met {p.name} {p.availability_months} maanden" for p in rest)
    return f"Met {eerste.name} blijft je kaart {eerste.availability_months} maanden online. {overige}, {vanaf}."


def muziek_uitleg(package: Package | None, ontwerp_muziek: bool) -> str:
    """De uitleg bij eigen muziek, met de prijs uit Beheer (dezelfde AddOn als op de rekening). Leeg als eigen muziek niet kan."""
    if package is not None and "music" in (package.features or []):
        prijs = f"In {package.name} zit dit erbij, zonder extra kosten."
    else:
        addon = AddOn.objects.filter(is_active=True, feature="music").order_by("price_cents").first()
        if addon is None:
            return ""
        prijs = f"Deze toevoeging kost {format_euro(addon.price_cents)}."
    tekst = f"Upload je eigen nummer voor deze kaart. {prijs}"
    if ontwerp_muziek:
        tekst += " Muziek die al onderdeel is van een ontwerp kost niets extra."
    return tekst


def upgrade_target(package: Package, packages: list[Package]) -> Package | None:
    """Het volgende, uitgebreidere pakket (bij Essentieel: Compleet)."""
    bigger = [p for p in packages if p.price_cents > package.price_cents and set(package.features or []) <= set(p.features or [])]
    return min(bigger, key=lambda p: p.price_cents) if bigger else None


def extras_for(package: Package, quote) -> list[dict]:
    """Losse onderdelen die niet in het pakket zitten: in gebruik (staat op de rekening) of toe te voegen in een stap."""
    in_use = {line.code for line in quote.required_addon_lines} if quote else set()
    rows = []
    for feature, step in FEATURE_STEPS.items():
        if feature in (package.features or []):
            continue
        addon = AddOn.objects.filter(is_active=True, feature=feature).order_by("price_cents").first()
        if addon is None:
            continue
        rows.append({"label": feature_label(feature), "price": format_euro(addon.price_cents), "description": addon.description,
                     "in_use": f"optie:{addon.code}" in in_use, "step": step})
    return rows
