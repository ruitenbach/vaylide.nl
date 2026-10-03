"""Maakt een losse voorvertoning (zonder server) van ontwerpen: elke kleur, als uitnodiging en als wenskaart.

Gebruik (vanuit de projectmap):
    python tools/voorvertoning.py <uitvoermap> [ontwerp ...]
Zonder ontwerpen: alle kerstontwerpen. Schrijft per kaart een HTML-bestand (<ontwerp>--<kleur>--<soort>.html),
de gebruikte statische bestanden onder static/ (met dezelfde mappen, zodat relatieve paden in de CSS kloppen)
en kaarten.json met de namen, kleuren en bestanden voor een overzichtspagina.

Links naar de website (zoals 'Maak jouw uitnodiging') wijzen in de voorvertoning naar index.html; aanmelden en
betalen werken er niet. Alles gebruikt de fictieve voorbeeldgegevens.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_DEBUG", "true")

import django  # noqa: E402

django.setup()

from django.contrib.staticfiles import finders  # noqa: E402
from django.test import Client  # noqa: E402

from catalog.models import Template  # noqa: E402
from catalog.occasions import occasion_config  # noqa: E402

STATIC_REF = re.compile(r"""/static/([^"'()\s>?#]+)""")
CSS_URL = re.compile(r"""url\(\s*["']?(?!data:|https?:|#)([^"')]+)["']?\s*\)""")


def find_static(rel: str) -> Path | None:
    # Op Windows zoekt Django met het padscheidingsteken van het systeem.
    found = finders.find(rel) or finders.find(rel.replace("/", os.sep))
    return Path(found) if found else None


def copy_static(rel: str, out: Path, done: set[str]) -> None:
    """Kopieert een statisch bestand; bij CSS ook alles waar het met url(...) naar verwijst."""
    if rel in done:
        return
    done.add(rel)
    src = find_static(rel)
    if src is None:
        print(f"  niet gevonden: {rel}")
        return
    dest = out / "static" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    if rel.endswith(".css"):
        base = Path(rel).parent
        for ref in CSS_URL.findall(src.read_text(encoding="utf-8")):
            target = os.path.normpath(base / ref).replace(os.sep, "/")
            if not target.startswith(".."):
                copy_static(target, out, done)


def page(html: str) -> str:
    html = STATIC_REF.sub(lambda m: "static/" + m.group(1), html)
    # Links en formulieren naar de website: terug naar het overzicht.
    html = re.sub(r'href="/(?!/)[^"]*"', 'href="index.html"', html)
    html = re.sub(r'action="/[^"]*"', 'action="#"', html)
    # Lettertype-preload is in een losse export overbodig en geeft onder file:// alleen een CORS-melding in de console.
    html = re.sub(r'<link[^>]*rel="preload"[^>]*as="font"[^>]*>\s*', "", html)
    # Deellinks verwijzen naar het adres van de server waarop de voorvertoning is gemaakt: weglaten.
    html = re.sub(r'<a[^>]*href="https://wa\.me/[^"]*"[^>]*>.*?</a>', "", html, flags=re.S)
    return html


def main() -> None:
    out = Path(sys.argv[1]).resolve()
    only = sys.argv[2:]
    out.mkdir(parents=True, exist_ok=True)
    templates = [t for t in Template.objects.filter(is_active=True, current_version__isnull=False).order_by("sort_order")
                 if (t.slug in only if only else "kerst" in t.occasions)]
    client = Client(SERVER_NAME="127.0.0.1")
    done: set[str] = set()
    kaarten = []
    for t in templates:
        version = t.current_version
        occasion = "kerst" if "kerst" in t.occasions else t.occasions[0]
        soorten = ["uitnodiging", "wenskaart"] if occasion_config(occasion).get("event_optional") else ["uitnodiging"]
        entry = {"slug": t.slug, "name": t.name, "tagline": t.tagline, "opening": version.manifest.get("opening_label", ""),
                 "palettes": [], "soorten": soorten}
        for p in version.palettes:
            entry["palettes"].append({"key": p["key"], "name": p["name"], "swatch": p.get("swatch", [])})
            for soort in soorten:
                response = client.get(f"/voorbeeld/{t.slug}/", {"gelegenheid": occasion, "kleur": p["key"], "soort": soort})
                html = response.content.decode()
                for rel in STATIC_REF.findall(html):
                    copy_static(rel, out, done)
                (out / f"{t.slug}--{p['key']}--{soort}.html").write_text(page(html), encoding="utf-8")
        kaarten.append(entry)
        print(f"{t.name}: {len(version.palettes)} kleuren x {len(soorten)}")
    (out / "kaarten.json").write_text(json.dumps(kaarten, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(done)} statische bestanden")


if __name__ == "__main__":
    main()
