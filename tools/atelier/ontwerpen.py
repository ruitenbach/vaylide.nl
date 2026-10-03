"""Schrijft de Atelier-ontwerpen (designs/<code>/v1/) uit een compacte beschrijving.

Per ontwerp: manifest.json, invitation.html en style.css. De opbouw, openingen en versiering
staan in designs/_atelier/v1/. Bestaande ontwerpmappen worden niet overschreven, tenzij je
--overschrijven meegeeft (alleen tijdens het ontwikkelen: een uitgebrachte versie wijzig je niet).

Gebruik: .venv/bin/python tools/atelier/ontwerpen.py [--overschrijven] [code ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from catalog.atelier import ATELIER_VARS, OPENING_LABELS, palette_problems  # noqa: E402
from catalog.effects import effects_errors, shine_color  # noqa: E402
from tools.atelier.specs import DESIGNS  # noqa: E402

FONTS = {
    # sleutel: (familie, bestand normaal, bestand cursief of None, gewichten, reserve)
    "cormorant": ("Cormorant Garamond", "cormorant-garamond-latin-wght-normal.woff2", "cormorant-garamond-latin-wght-italic.woff2", "300 700", "Georgia, serif"),
    "playfair": ("Playfair Display", "playfair-display-latin-wght-normal.woff2", "playfair-display-latin-wght-italic.woff2", "400 900", "Georgia, serif"),
    "figtree": ("Figtree", "figtree-latin-wght-normal.woff2", None, "300 900", "system-ui, sans-serif"),
    "cinzel": ("Cinzel", "cinzel-latin-wght-normal.woff2", None, "400 900", "Georgia, serif"),
    "greatvibes": ("Great Vibes", "great-vibes-latin-400-normal.woff2", None, "400", "cursive"),
    "parisienne": ("Parisienne", "parisienne-latin-400-normal.woff2", None, "400", "cursive"),
    "caveat": ("Caveat", "caveat-latin-400-normal.woff2", None, "400", "cursive"),
    "bodoni": ("Bodoni Moda", "bodoni-moda-latin-wght-normal.woff2", "bodoni-moda-latin-wght-italic.woff2", "400 900", "Didot, Georgia, serif"),
    "marcellus": ("Marcellus", "marcellus-latin-400-normal.woff2", None, "400", "Georgia, serif"),
    "italiana": ("Italiana", "italiana-latin-400-normal.woff2", None, "400", "Georgia, serif"),
    "fraunces": ("Fraunces", "fraunces-latin-wght-normal.woff2", "fraunces-latin-wght-italic.woff2", "100 900", "Georgia, serif"),
    "ebgaramond": ("EB Garamond", "eb-garamond-latin-wght-normal.woff2", "eb-garamond-latin-wght-italic.woff2", "400 800", "Garamond, Georgia, serif"),
    "josefin": ("Josefin Sans", "josefin-sans-latin-wght-normal.woff2", None, "100 700", "system-ui, sans-serif"),
    "montserrat": ("Montserrat", "montserrat-latin-wght-normal.woff2", None, "100 900", "system-ui, sans-serif"),
    "quicksand": ("Quicksand", "quicksand-latin-wght-normal.woff2", None, "300 700", "system-ui, sans-serif"),
    "nunito": ("Nunito", "nunito-latin-wght-normal.woff2", None, "200 1000", "system-ui, sans-serif"),
    "manrope": ("Manrope", "manrope-latin-wght-normal.woff2", None, "200 800", "system-ui, sans-serif"),
    "fredoka": ("Fredoka", "fredoka-latin-wght-normal.woff2", None, "300 700", "system-ui, sans-serif"),
    "tenor": ("Tenor Sans", "tenor-sans-latin-400-normal.woff2", None, "400", "system-ui, sans-serif"),
    "courier": ("Courier Prime", "courier-prime-latin-400-normal.woff2", None, "400", "\"Courier New\", monospace"),
    "tiltneon": ("Tilt Neon", "tilt-neon-latin-400-normal.woff2", None, "400", "system-ui, sans-serif"),
    "abril": ("Abril Fatface", "abril-fatface-latin-400-normal.woff2", None, "400", "Georgia, serif"),
    "syne": ("Syne", "syne-latin-wght-normal.woff2", None, "400 800", "system-ui, sans-serif"),
    "gilda": ("Gilda Display", "gilda-display-latin-400-normal.woff2", None, "400", "Georgia, serif"),
    "jost": ("Jost", "jost-latin-wght-normal.woff2", None, "100 900", "system-ui, sans-serif"),
    "lora": ("Lora", "lora-latin-wght-normal.woff2", "lora-latin-wght-italic.woff2", "400 700", "Georgia, serif"),
    "instrument": ("Instrument Serif", "instrument-serif-latin-400-normal.woff2", "instrument-serif-latin-400-italic.woff2", "400", "Georgia, serif"),
}
ROLES = ("display", "body", "script", "ui", "text", "number")
# text: ondertitel, welkomsttekst en datum in woorden; number: cijfers (datum, aftellen, leeftijd).
# Beide zijn optioneel en vallen terug op display, handig bij een sierletter die klein slecht leest.
VAR_NAMES = ATELIER_VARS
SECTIONS = ["countdown", "story", "gallery", "program", "location", "dresscode", "practical", "rsvp", "contact", "closing", "music"]


def names_colors(spec: dict, colors: dict) -> tuple[str, str]:
    """Kleur van de namen en de achtergrond eronder, per kleurvariant."""
    hero = spec["atelier"]["hero"]
    if hero == "band":
        return colors.get("band_ink", colors["accent_ink"]), colors.get("band", colors["accent"])
    if hero == "volbeeld":
        return colors.get("hero_ink", "#FFFDF9"), colors.get("cover_bg", colors["ink"])
    if ".a-names { color: var(--a-text); }" in spec.get("css", ""):
        return colors.get("accent_text", colors["accent"]), colors["bg"]
    return colors["ink"], colors["bg"]


def manifest(spec: dict) -> dict:
    effects = spec.get("effects")
    palettes = []
    for pal in spec["palettes"]:
        colors = dict(pal["colors"])
        colors.setdefault("scheme", "light")
        vars_ = {VAR_NAMES[k]: v for k, v in colors.items()}
        vars_["--a-page"] = colors["bg"]
        if effects and effects.get("namen") == "folie":
            fg, bg = names_colors(spec, colors)
            vars_["--fx-shine"] = shine_color(fg, bg, colors.get("accent_text", colors["accent"]))
        palettes.append({"key": pal["key"], "name": pal["name"], "swatch": [colors["bg"], colors.get("c2", colors["line"]), colors["accent"]], "vars": vars_})
    data = {
        "slug": spec["slug"], "version": 1, "name": spec["name"], "tagline": spec["tagline"], "description": spec["description"],
        "style_notes": spec["style_notes"], "occasions": spec["occasions"], "sort_order": spec["sort_order"],
        "opening": spec["atelier"]["opening"], "opening_label": OPENING_LABELS[spec["atelier"]["opening"]],
        "envelope_mode": spec.get("envelope_mode", "built_in"),   # optional: de klant mag een envelop uit de Envelope Collection kiezen
        "atelier": spec["atelier"], "palettes": palettes, "sections": SECTIONS, "changelog": "Eerste versie.",
    }
    if effects:
        data["effects"] = effects
    return data


def font_faces(keys: list[str]) -> str:
    rules = []
    for key in keys:
        family, normal, italic, weights, _ = FONTS[key]
        rules.append(f'@font-face {{ font-family: "{family}"; src: url("../../../fonts/{normal}") format("woff2"); font-weight: {weights}; font-display: swap; }}')
        if italic:
            rules.append(f'@font-face {{ font-family: "{family}"; src: url("../../../fonts/{italic}") format("woff2"); font-weight: {weights}; font-style: italic; font-display: swap; }}')
    return "\n".join(rules)


def stylesheet(spec: dict) -> str:
    fonts = spec["fonts"]
    used = list(dict.fromkeys(fonts[r] for r in ROLES if r in fonts))
    for extra in spec.get("extra_fonts", []):
        if extra not in used:
            used.append(extra)
    stack = {role: f'"{FONTS[fonts[role]][0]}", {FONTS[fonts[role]][4]}' for role in ROLES if role in fonts}
    lines = [f"/* {spec['name']} v1 — {spec['style_notes'].lower()}.",
             "   Opbouw, opening en versiering: designs/_atelier/v1. Wijzig een uitgebrachte versie niet: maak een v2. */", "",
             font_faces(used), "", "body {"]
    lines.append(f"  --a-display: {stack['display']};")
    lines.append(f"  --a-body: {stack.get('body', stack['display'])};")
    lines.append(f"  --a-script: {stack.get('script', stack['display'])};")
    lines.append(f"  --a-ui: {stack.get('ui', stack.get('body', stack['display']))};")
    if "text" in stack:
        lines.append(f"  --a-text-font: {stack['text']};")
    if "number" in stack:
        lines.append(f"  --a-number-font: {stack['number']};")
    for key, value in spec.get("tokens", {}).items():
        lines.append(f"  {key}: {value};")
    lines.append("}")
    if spec.get("css"):
        lines.append("")
        lines.append(spec["css"].strip())
    return "\n".join(lines) + "\n"


def template(spec: dict) -> str:
    preload = []
    for role in spec.get("preload", ["display"]):
        key = spec["fonts"][role]
        preload.append(f"<link rel=\"preload\" href=\"{{% static 'fonts/{FONTS[key][1]}' %}}\" as=\"font\" type=\"font/woff2\" crossorigin>")
    return ("{% extends \"_atelier/v1/base.html\" %}{% load static %}\n"
            f"{{# {spec['name']} v1 — {spec['style_notes'].lower()}. Opbouw: designs/_atelier/v1. Wijzig een uitgebrachte versie niet: maak een v2. #}}\n"
            "{% block preload %}" + "\n".join(preload) + "{% endblock %}\n")


def write(spec: dict, overwrite: bool) -> str:
    folder = ROOT / "designs" / spec["slug"] / "v1"
    if folder.exists() and not overwrite:
        return f"overgeslagen (bestaat al): {spec['slug']}"
    problems = []
    for pal in spec["palettes"]:
        problems += [f"{pal['key']}: {p}" for p in palette_problems(pal["colors"], spec["atelier"])]
    if problems:
        raise SystemExit(f"Contrast te laag in {spec['slug']}:\n  " + "\n  ".join(problems))
    if spec.get("effects") and effects_errors(spec["effects"]):
        raise SystemExit(f"Effecten kloppen niet in {spec['slug']}: " + "; ".join(effects_errors(spec["effects"])))
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.json").write_text(json.dumps(manifest(spec), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "invitation.html").write_text(template(spec), encoding="utf-8")
    (folder / "style.css").write_text(stylesheet(spec), encoding="utf-8")
    return f"geschreven: {spec['slug']}"


if __name__ == "__main__":
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    overwrite = "--overschrijven" in sys.argv
    for spec in DESIGNS:
        if args and spec["slug"] not in args:
            continue
        print(write(spec, overwrite))
