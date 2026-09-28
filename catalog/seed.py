"""Standaardgegevens: ontwerpen uit designs/*/v*/manifest.json, pakketten en opties.

Alles is idempotent en overschrijft nooit wijzigingen van de eigenaar:
- bestaande ontwerpversies worden niet aangepast (versies zijn onveranderlijk);
- pakketten en opties worden alleen aangemaakt als er nog geen enkele bestaat.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import transaction

log = logging.getLogger(__name__)

DEFAULT_PACKAGES = [
    {
        "code": "essentieel",
        "name": "Essentieel",
        "description": "Alles voor een complete, persoonlijke uitnodiging.",
        "price_cents": 3900,
        "availability_months": 6,
        "features": [],
        "max_gallery_photos": 0,
        "highlights": [
            "Alle ontwerpen en kleurvarianten",
            "Openingsanimatie met standaard lakzegel (rood of groen)",
            "Afteller, programma, locatie en routeknop",
            "Aanmeldformulier met gastenlijst en export",
            "Eigen link, QR-code en agenda-knop",
            "Wijzigingen publiceren op dezelfde link",
            "6 maanden online",
        ],
        "is_featured": False,
        "sort_order": 10,
    },
    {
        "code": "compleet",
        "name": "Compleet",
        "description": "Met jullie verhaal, fotogalerij, muziek en extra vragen.",
        "price_cents": 6900,
        "availability_months": 12,
        "features": ["story", "gallery", "music", "extra_questions", "zegel"],
        "max_gallery_photos": 12,
        "highlights": [
            "Alles uit Essentieel",
            "Persoonlijk zegel met jullie initialen",
            "Persoonlijk verhaal",
            "Fotogalerij tot 12 foto's",
            "Eigen muziek (start pas na een tik)",
            "Extra vragen bij het aanmelden",
            "12 maanden online",
        ],
        "is_featured": True,
        "sort_order": 20,
    },
]

DEFAULT_ADDONS = [
    {"code": "muziek", "name": "Muziek", "description": "Eigen muziek bij je uitnodiging; gasten zetten die zelf aan.",
     "price_cents": 900, "feature": "music", "sort_order": 10},
    {"code": "fotogalerij", "name": "Fotogalerij", "description": "Een galerij met maximaal 12 foto's.",
     "price_cents": 1200, "feature": "gallery", "gallery_photos": 12, "sort_order": 20},
    {"code": "verhaal", "name": "Persoonlijk verhaal", "description": "Een eigen sectie voor jullie verhaal.",
     "price_cents": 600, "feature": "story", "sort_order": 30},
    {"code": "extra-vragen", "name": "Extra vragen bij aanmelden",
     "description": "Tot 5 eigen vragen, bijvoorbeeld over dieetwensen.",
     "price_cents": 600, "feature": "extra_questions", "sort_order": 40},
    {"code": "langer-online", "name": "Langer online", "description": "Je uitnodiging blijft 12 maanden langer online.",
     "price_cents": 1200, "extra_months": 12, "sort_order": 50},
]


class DesignError(ValueError):
    """Een ontwerpmap is niet compleet of niet consistent."""


REQUIRED_MANIFEST_KEYS = ("slug", "version", "name", "occasions", "palettes")


def validate_manifest(path: Path, data: dict) -> None:
    folder = path.parent
    where = f"{folder.parent.name}/{folder.name}"
    missing = [key for key in REQUIRED_MANIFEST_KEYS if not data.get(key)]
    if missing:
        raise DesignError(f"{where}/manifest.json mist: {', '.join(missing)}.")
    if data["slug"] != folder.parent.name:
        raise DesignError(f"{where}: 'slug' in het manifest ({data['slug']}) moet gelijk zijn aan de mapnaam ({folder.parent.name}).")
    if f"v{data['version']}" != folder.name:
        raise DesignError(f"{where}: 'version' in het manifest ({data['version']}) hoort bij map v{data['version']}, niet {folder.name}.")
    for filename in ("invitation.html", "style.css"):
        if not (folder / filename).exists():
            raise DesignError(f"{where}: {filename} ontbreekt.")
    for palette in data["palettes"]:
        if not palette.get("key") or not palette.get("name") or not isinstance(palette.get("vars"), dict):
            raise DesignError(f"{where}: elke kleurvariant heeft 'key', 'name' en 'vars' nodig.")
    from .occasions import OCCASIONS

    unknown = [o for o in data["occasions"] if o not in OCCASIONS]
    if unknown:
        raise DesignError(f"{where}: onbekende gelegenheid: {', '.join(unknown)}. Kies uit: {', '.join(OCCASIONS)}.")
    if "atelier" in data:
        from .atelier import atelier_errors

        problems = atelier_errors(data["atelier"])
        if problems:
            raise DesignError(f"{where}: {'; '.join(problems)}.")
    if "effects" in data:
        from .effects import effects_errors

        problems = effects_errors(data["effects"])
        if problems:
            raise DesignError(f"{where}: {'; '.join(problems)}.")


def design_manifests() -> list[tuple[Path, dict]]:
    root = Path(settings.BASE_DIR) / "designs"
    found = []
    for path in sorted(root.glob("*/v*/manifest.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DesignError(f"{path.parent.parent.name}/{path.parent.name}/manifest.json is geen geldige JSON: {exc}") from exc
        validate_manifest(path, data)
        found.append((path, data))
    return found


@transaction.atomic
def sync_designs(update_existing_manifest: bool = False) -> list[str]:
    from .models import Template, TemplateVersion

    messages = []
    for path, data in design_manifests():
        slug = data["slug"]
        number = int(data["version"])
        renderer = f"{path.parent.parent.name}/{path.parent.name}"
        template, created = Template.objects.get_or_create(
            slug=slug,
            defaults={
                "name": data["name"],
                "tagline": data.get("tagline", ""),
                "description": data.get("description", ""),
                "style_notes": data.get("style_notes", ""),
                "occasions": data.get("occasions", []),
                "sort_order": data.get("sort_order", 100),
            },
        )
        if created:
            messages.append(f"Ontwerp aangemaakt: {template.name}")
        version, v_created = TemplateVersion.objects.get_or_create(
            template=template,
            number=number,
            defaults={
                "renderer": renderer,
                "manifest": data,
                "changelog": data.get("changelog", ""),
            },
        )
        if v_created:
            messages.append(f"Versie geregistreerd: {template.name} v{number}")
        elif update_existing_manifest and version.manifest != data:
            version.manifest = data
            version.renderer = renderer
            version.save(update_fields=["manifest", "renderer"])
            messages.append(f"Manifest bijgewerkt (ontwikkelmodus): {template.name} v{number}")
        if template.current_version_id is None:
            template.current_version = version
            template.save(update_fields=["current_version"])
    return messages


@transaction.atomic
def ensure_pricing() -> None:
    from .models import AddOn, Package

    if not Package.objects.exists():
        for data in DEFAULT_PACKAGES:
            Package.objects.create(**data)
    if not AddOn.objects.exists():
        for data in DEFAULT_ADDONS:
            AddOn.objects.create(**data)


def ensure_catalog() -> None:
    from core.models import SiteConfig

    sync_designs()
    ensure_pricing()
    SiteConfig.get()


def ensure_catalog_on_migrate(sender, **kwargs):
    using = kwargs.get("using", "default")
    try:
        call_command("createcachetable", database=using, verbosity=0)
        ensure_catalog()
    except Exception:  # pragma: no cover - alleen relevant bij een halve migratie
        log.exception("Standaardcatalogus kon niet worden aangemaakt")
