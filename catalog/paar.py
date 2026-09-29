"""Het bruidspaar als beeldlaag (ontwerpen met "paar" in het manifest, zoals Balzaal).

Per combinatie van haarkleuren (man, vrouw) is er een vooraf gemaakte afbeelding met dezelfde houding, kleding,
belichting en uitsnede: img/paar-<man>-<vrouw>.webp (900 breed) en img/paar-<man>-<vrouw>-560.webp. Een kleurfilter
over de hele persoon is bewust niet gebruikt (dat verkleurt ook huid en kleding).

De keuze voor haarkleur verschijnt in de editor pas als ALLE combinaties aanwezig zijn; anders ziet iedereen het
standaardpaar. Zo belooft de site geen keuze die nog niet werkt.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.templatetags.static import static

HAARKLEUR_LABELS = {"zwart": "Zwart", "bruin": "Bruin", "blond": "Blond"}


def config(template_version) -> dict | None:
    data = (template_version.manifest or {}).get("paar")
    return data if isinstance(data, dict) and data.get("standaard") else None


def _file(renderer: str, man: str, vrouw: str, small: bool = False) -> str:
    return f"designs/{renderer}/img/paar-{man}-{vrouw}{'-560' if small else ''}.webp"


@lru_cache(maxsize=64)
def _exists(path: str) -> bool:
    return (Path(settings.BASE_DIR) / path).is_file()


def available(template_version) -> list[tuple[str, str]]:
    """Combinaties (man, vrouw) waarvan beide formaten bestaan."""
    cfg = config(template_version)
    if not cfg:
        return []
    kleuren = cfg.get("haarkleuren") or []
    return [(m, v) for m in kleuren for v in kleuren
            if _exists(_file(template_version.renderer, m, v)) and _exists(_file(template_version.renderer, m, v, True))]


def missing(template_version) -> list[tuple[str, str]]:
    cfg = config(template_version) or {}
    kleuren = cfg.get("haarkleuren") or []
    have = set(available(template_version))
    return [(m, v) for m in kleuren for v in kleuren if (m, v) not in have]


def choice_enabled(template_version) -> bool:
    """De haarkleurkeuze werkt alleen als alle combinaties er zijn."""
    cfg = config(template_version)
    return bool(cfg) and not missing(template_version)


def selection(template_version, content: dict) -> tuple[str, str]:
    cfg = config(template_version) or {}
    std = cfg.get("standaard") or {}
    man, vrouw = std.get("man", ""), std.get("vrouw", "")
    if choice_enabled(template_version):
        haar = ((content or {}).get("style") or {}).get("haar") or {}
        kleuren = cfg.get("haarkleuren") or []
        if haar.get("man") in kleuren:
            man = haar["man"]
        if haar.get("vrouw") in kleuren:
            vrouw = haar["vrouw"]
    return man, vrouw


def view(template_version, content: dict) -> dict | None:
    """Wat het ontwerp nodig heeft om het paar te tonen (None bij ontwerpen zonder paar)."""
    cfg = config(template_version)
    if not cfg:
        return None
    man, vrouw = selection(template_version, content)
    return {
        "man": man,
        "vrouw": vrouw,
        "src": static(_file(template_version.renderer, man, vrouw)),
        "src_small": static(_file(template_version.renderer, man, vrouw, True)),
        "alt": cfg.get("alt", ""),
    }
