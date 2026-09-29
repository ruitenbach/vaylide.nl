"""Het bruidspaar (ontwerpen met "paar" in het manifest, zoals Balzaal): standaardpaar, haarkleurvarianten en de dans.

Bestanden in designs/<ontwerp>/v<N>/:
- img/paar-<man>-<vrouw>.webp en -560: het standaardpaar als transparante laag (nu: bruin-blond, aangeleverd).
- img/scene-<man>-<vrouw>.webp en -600: de hele scène (zaal met paar), 941×1672. Voor het standaardpaar gemaakt uit de
  lagen; voor de andere haarkleuren gemaakt met de beeld-API (tools/balzaal/maak_haarvarianten.py). Geen kleurfilter.
- video/dans-<man>-<vrouw>.mp4: een korte dansscène (tools/balzaal/maak_dansvideo.py). Alleen als dat bestand er is,
  toont de kaart een dans; de scène is dan de poster. Er is geen nagemaakte dans met CSS.

De haarkleurkeuze verschijnt in de editor pas als ALLE combinaties als scène bestaan; anders ziet iedereen het
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


def _default(cfg: dict) -> tuple[str, str]:
    std = cfg.get("standaard") or {}
    return std.get("man", ""), std.get("vrouw", "")


def _layer(renderer: str, man: str, vrouw: str, small: bool = False) -> str:
    return f"designs/{renderer}/img/paar-{man}-{vrouw}{'-560' if small else ''}.webp"


def _scene(renderer: str, man: str, vrouw: str, small: bool = False) -> str:
    return f"designs/{renderer}/img/scene-{man}-{vrouw}{'-600' if small else ''}.webp"


def _video(renderer: str, man: str, vrouw: str) -> str:
    return f"designs/{renderer}/video/dans-{man}-{vrouw}.mp4"


@lru_cache(maxsize=128)
def _exists(path: str) -> bool:
    return (Path(settings.BASE_DIR) / path).is_file()


def _combo_ready(renderer: str, cfg: dict, man: str, vrouw: str) -> bool:
    if (man, vrouw) == _default(cfg):
        return _exists(_layer(renderer, man, vrouw)) and _exists(_layer(renderer, man, vrouw, True))
    return _exists(_scene(renderer, man, vrouw)) and _exists(_scene(renderer, man, vrouw, True))


def available(template_version) -> list[tuple[str, str]]:
    """Combinaties (man, vrouw) waarvan een goed beeld bestaat."""
    cfg = config(template_version)
    if not cfg:
        return []
    kleuren = cfg.get("haarkleuren") or []
    return [(m, v) for m in kleuren for v in kleuren if _combo_ready(template_version.renderer, cfg, m, v)]


def missing(template_version) -> list[tuple[str, str]]:
    cfg = config(template_version) or {}
    kleuren = cfg.get("haarkleuren") or []
    have = set(available(template_version))
    return [(m, v) for m in kleuren for v in kleuren if (m, v) not in have]


def choice_enabled(template_version) -> bool:
    """De haarkleurkeuze werkt alleen als alle combinaties er zijn."""
    return bool(config(template_version)) and not missing(template_version)


def selection(template_version, content: dict) -> tuple[str, str]:
    cfg = config(template_version) or {}
    man, vrouw = _default(cfg)
    if choice_enabled(template_version):
        haar = ((content or {}).get("style") or {}).get("haar") or {}
        kleuren = cfg.get("haarkleuren") or []
        if haar.get("man") in kleuren:
            man = haar["man"]
        if haar.get("vrouw") in kleuren:
            vrouw = haar["vrouw"]
    return man, vrouw


def dance_available(template_version, man: str, vrouw: str) -> bool:
    return _exists(_video(template_version.renderer, man, vrouw))


def view(template_version, content: dict) -> dict | None:
    """Wat het ontwerp nodig heeft om het paar (en eventueel de dans) te tonen; None bij ontwerpen zonder paar."""
    cfg = config(template_version)
    if not cfg:
        return None
    renderer = template_version.renderer
    man, vrouw = selection(template_version, content)
    data = {
        "man": man,
        "vrouw": vrouw,
        "src": static(_layer(renderer, *_default(cfg))),
        "src_small": static(_layer(renderer, *_default(cfg), True)),
        "alt": cfg.get("alt", ""),
    }
    if (man, vrouw) != _default(cfg):
        data["scene"] = static(_scene(renderer, man, vrouw))
        data["scene_small"] = static(_scene(renderer, man, vrouw, True))
    if dance_available(template_version, man, vrouw) and _exists(_scene(renderer, man, vrouw, True)):
        data["video"] = static(_video(renderer, man, vrouw))
        data["poster"] = static(_scene(renderer, man, vrouw, True))
    return data
