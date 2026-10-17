#!/usr/bin/env python3
"""Maakt de vijf filmkaarten (zijden-gordijn, bloesemmeer, bloesemwaaier, kerstsprookje, gouden-poort) uit de aangeleverde films.

Gebruik (vanuit de hoofdmap van het project):
    python tools/introkaarten/maak_introkaarten.py <map met de vijf bronfilms> [slug ...]

De bronmap bevat curtains.mp4, blossom.mp4, fan.mp4, christmas.mp4 en palace.mp4 (720x1280, 10 s, zonder geluid; de namen staan in BRON hieronder).
Per kaart komt in designs/<slug>/v1/ te staan: manifest.json, invitation.html, style.css (uit het sjabloon in tools/introkaarten/sjabloon, met de gegevens
hieronder), opening.mp4 (opnieuw gecodeerd), poster.webp (eerste beeld), end.webp (laatste beeld, gelijk aan het laatste beeld van de film), de uitsneden
cut-*.webp, band.webp en gal-*.webp uit de film zelf, en static/img/designs/<slug>.webp (kaartbeeld voor de collectie, 800x1000).
Vereist: ffmpeg en Pillow. De films zelf staan niet in Git; in Git staat alleen het resultaat.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SJABLOON = Path(__file__).resolve().parent / "sjabloon"
ADDED = "2026-10-18T09:00:00Z"

# Uitsneden (x, y, breedte, hoogte in pixels van het bronbeeld van 720x1280) en het tijdstip van het beeld waaruit ze komen.
# a, b, d: brede stroken; c: staand (boog); band: afsluiting; g1..g4: staande voorbeeldbeelden (3:4).
STANDAARD_UITSNEDEN = {
    "a": (0, 300, 720, 427, 9.9), "b": (0, 640, 720, 450, 7.0), "c": (60, 380, 600, 652, 9.0), "d": (0, 880, 720, 263, 8.0),
    "band": (0, 620, 720, 560, 6.5),
    "g1": (90, 60, 540, 720, 9.9), "g2": (90, 480, 540, 720, 9.9), "g3": (0, 300, 540, 720, 8.5), "g4": (180, 360, 540, 720, 7.5),
}

BRON = {"zijden-gordijn": "curtains.mp4", "bloesemmeer": "blossom.mp4", "bloesemwaaier": "fan.mp4", "kerstsprookje": "christmas.mp4", "gouden-poort": "palace.mp4"}

KLEUR_LICHT = {"--fk-accent-ink": "#FFFFFF", "--fk-field-bg": "#FFFFFF", "--fk-field-ink": "#1F1A1A", "--fk-shadow": "92, 58, 30"}

KAARTEN = [
    {
        "slug": "zijden-gordijn", "naam": "Zijden gordijn", "sort_order": 50,
        "tagline": "Zijden gordijnen vol bloemen schuiven open naar een kasteel in het avondlicht",
        "beschrijving": "Zijden gordijnen met gouden borduursel en witte rozen.",
        "omschrijving": "Je ziet eerst gesloten ivoren zijden gordijnen met witte rozen en gouden borduursel. Na een tik schuiven ze open en kijk je door naar een terras met een fontein, kaarsen en een kasteel in het licht van de ondergaande zon. Daarna staan jullie namen in de lucht en loopt de uitnodiging door met aftellen, programma, locatie en aanmelden, in ivoor en goud. De opening is over te slaan en rustig bij minder beweging. De film is een gegenereerde scène zonder personen.",
        "stijl": "Ivoren zijde, witte rozen, gouden borduursel, een kasteel bij zonsondergang; romantisch en tijdloos",
        "gelegenheden": ["bruiloft", "verloving", "jubileum"], "label": "Zijden gordijnen die opengaan naar een kasteel (film)",
        "film_aria": "Zijden gordijnen met witte rozen schuiven open naar een terras met een kasteel in het avondlicht",
        "palet": ("ivoor-goud", "Ivoor en goud", ["#FFFBF3", "#C9A45C", "#3A2E22"]),
        "namen": ("Pinyon Script", "pinyon-script-latin-400-normal.woff2"), "sky": (18, 18, 6, 27),
        "effecten": {"sfeer": "goudstof", "knal": "blaadjes", "viering": "blaadjes", "namen": "schrijf", "onthul": "zacht", "extra": ["kenburns", "tik"]},
        "kleuren": {"--fk-page": "#F7EFE2", "--fk-page-2": "#FBF6EC", "--fk-dusk": "#EBD9BD", "--fk-paper": "#FFFBF3", "--fk-paper-2": "#F6ECDC",
                    "--fk-paper-rgb": "255, 251, 243", "--fk-ink": "#3A2E22", "--fk-muted": "#66543F", "--fk-accent": "#8B5E2B", "--fk-gold": "#C9A45C",
                    "--fk-gold-line": "#9A7330", "--fk-sky-ink": "#3E2F20", "--fk-sky-muted": "#5B4630", "--fk-glow": "255, 248, 236",
                    "--fk-veil": "244, 234, 218", "--fk-date-1": "#B98A3E", "--fk-date-2": "#8B5E2B", "--fk-date-3": "#6A4519",
                    "--fx-1": "#FFFBF0", "--fx-2": "#F3D9A8", "--fx-3": "#E2C07A", "--fx-4": "#FFFFFF", "--fx-bg": "#3A2E22", **KLEUR_LICHT},
    },
    {
        "slug": "bloesemmeer", "naam": "Bloesemmeer", "sort_order": 51,
        "tagline": "Een wand van kersenbloesem opent naar een bergmeer met een waterval in het zonlicht",
        "beschrijving": "Een wand van roze kersenbloesem.",
        "omschrijving": "Je ziet eerst een wand van roze kersenbloesem. Na een tik gaat die langzaam open en kijk je uit over een helder meer met een waterval tussen de bergen, terwijl de zon opkomt achter de takken. Daarna staan jullie namen in de lucht en loopt de uitnodiging door met aftellen, programma, locatie en aanmelden, in zachtroze en goud. De opening is over te slaan en rustig bij minder beweging. De film is een gegenereerde scène zonder personen en zonder gebouwen.",
        "stijl": "Roze kersenbloesem, bergmeer met waterval, zonsopgang; zacht, helder en bloemrijk",
        "gelegenheden": ["bruiloft", "verloving", "verjaardag", "babyshower"], "label": "Kersenbloesem die opengaat naar een bergmeer (film)",
        "film_aria": "Een wand van roze kersenbloesem gaat open en toont een bergmeer met een waterval in het zonlicht",
        "palet": ("bloesem-roze", "Bloesemroze", ["#FFFAF8", "#D3A25A", "#43292F"]),
        "namen": ("Parisienne", "parisienne-latin-400-normal.woff2"), "sky": (12, 12, 7, 26),
        "effecten": {"sfeer": "bloesem", "knal": "bloesem", "viering": "bloesem", "namen": "zacht", "onthul": "zacht", "extra": ["kenburns", "tik"]},
        "kleuren": {"--fk-page": "#FBEFEE", "--fk-page-2": "#FFF7F5", "--fk-dusk": "#F3D5D3", "--fk-paper": "#FFFAF8", "--fk-paper-2": "#FBEBE8",
                    "--fk-paper-rgb": "255, 250, 248", "--fk-ink": "#43292F", "--fk-muted": "#6E4A52", "--fk-accent": "#A23E62", "--fk-gold": "#D3A25A",
                    "--fk-gold-line": "#A06A2D", "--fk-sky-ink": "#4A2A33", "--fk-sky-muted": "#6B3F4B", "--fk-glow": "255, 244, 242",
                    "--fk-veil": "252, 236, 234", "--fk-date-1": "#C8506F", "--fk-date-2": "#A23E62", "--fk-date-3": "#7E2C49",
                    "--fx-1": "#FFE3E8", "--fx-2": "#F8BCCB", "--fx-3": "#F4A3B8", "--fx-4": "#FFFFFF", "--fx-bg": "#43292F", **KLEUR_LICHT, "--fk-shadow": "110, 50, 62"},
    },
    {
        "slug": "bloesemwaaier", "naam": "Bloesemwaaier", "sort_order": 52,
        "tagline": "Een bloesemwaaier trekt weg en onthult een lantaarntuin bij zonsondergang",
        "beschrijving": "Een ivoren waaier met kersenbloesem en een gouden kwast.",
        "omschrijving": "Je ziet eerst een grote ivoren waaier met kersenbloesem en een gouden kwast. Na een tik klapt hij dicht en trekt weg: daarachter ligt een tuin met gloeiende lantaarns, een houten brug over het water en een waterval, bij een ondergaande zon. Daarna staan jullie namen in de lucht en loopt de uitnodiging door met aftellen, programma, locatie en aanmelden, in roze en goud. De opening is over te slaan en rustig bij minder beweging. De film is een gegenereerde scène zonder personen.",
        "stijl": "Ivoren waaier met bloesem, lantaarns, houten brug over het water, zonsondergang; verfijnd en sfeervol",
        "gelegenheden": ["bruiloft", "verloving", "jubileum", "verjaardag"], "label": "Een waaier die wegtrekt voor een lantaarntuin (film)",
        "film_aria": "Een ivoren waaier met kersenbloesem klapt dicht en onthult een tuin met lantaarns en een brug over het water bij zonsondergang",
        "palet": ("zonsondergang", "Zonsondergang", ["#FFFAF4", "#D2A45C", "#40281F"]),
        "namen": ("Great Vibes", "great-vibes-latin-400-normal.woff2"), "sky": (22, 8, 7, 25),
        "effecten": {"sfeer": "bloesem", "knal": "bloesem", "viering": "blaadjes", "namen": "schrijf", "onthul": "zacht", "extra": ["kenburns", "tik"]},
        "kleuren": {"--fk-page": "#F8ECE3", "--fk-page-2": "#FDF5EE", "--fk-dusk": "#EFCFB8", "--fk-paper": "#FFFAF4", "--fk-paper-2": "#F8E9DC",
                    "--fk-paper-rgb": "255, 250, 244", "--fk-ink": "#40281F", "--fk-muted": "#6B4A3B", "--fk-accent": "#9B4A2E", "--fk-gold": "#D2A45C",
                    "--fk-gold-line": "#9A6A2C", "--fk-sky-ink": "#43271C", "--fk-sky-muted": "#6A4030", "--fk-glow": "255, 244, 232",
                    "--fk-veil": "250, 234, 224", "--fk-date-1": "#BE6A3C", "--fk-date-2": "#9B4A2E", "--fk-date-3": "#753320",
                    "--fx-1": "#FFE6EA", "--fx-2": "#F8C2CC", "--fx-3": "#F2A9A0", "--fx-4": "#FFF4E2", "--fx-bg": "#40281F", **KLEUR_LICHT},
    },
    {
        "slug": "kerstsprookje", "naam": "Kerstsprookje", "sort_order": 53,
        "tagline": "Een muur van besneeuwde dennen schuift open naar een kerstplein vol lichtjes",
        "beschrijving": "Besneeuwde dennen vol gouden ballen en lichtjes.",
        "omschrijving": "Je ziet eerst een muur van besneeuwde dennentakken met gouden ballen, sterren en lichtjes. Na een tik schuift hij open en sta je op een kerstplein onder een sterrenhemel, met een hoge verlichte kerstboom, een draaimolen, cadeaus en een glanzende, natte straat vol goudlicht. Daarna staan jullie namen in de lucht en loopt de kerstkaart door met aftellen, programma, locatie en aanmelden, in nachtblauw en goud. De opening is over te slaan en rustig bij minder beweging. De film is een gegenereerde scène zonder personen.",
        "stijl": "Besneeuwde dennen, gouden lichtjes, kerstplein onder de sterren; nachtblauw en goud, sprookjesachtig",
        "gelegenheden": ["kerst"], "label": "Besneeuwde dennen die opengaan naar een kerstplein (film)",
        "film_aria": "Een muur van besneeuwde dennen met gouden lichtjes schuift open naar een kerstplein met een hoge kerstboom onder de sterren",
        "palet": ("nachtblauw-goud", "Nachtblauw en goud", ["#14223F", "#E2B65A", "#F6ECD6"]),
        "namen": ("Great Vibes", "great-vibes-latin-400-normal.woff2"), "sky": (14, 10, 9, 22),
        "effecten": {"sfeer": "sneeuw", "knal": "sterren", "viering": "sterren", "namen": "gloed", "onthul": "zacht", "extra": ["tik"]},
        "kleuren": {"--fk-page": "#0F1A33", "--fk-page-2": "#16264A", "--fk-dusk": "#1C2E58", "--fk-paper": "#14223F", "--fk-paper-2": "#1B2C52",
                    "--fk-paper-rgb": "20, 34, 63", "--fk-ink": "#F6ECD6", "--fk-muted": "#D2C6A8", "--fk-accent": "#F0C66B", "--fk-gold": "#E2B65A",
                    "--fk-gold-line": "#E2B65A", "--fk-sky-ink": "#FFF3D6", "--fk-sky-muted": "#F1DFB4", "--fk-glow": "10, 18, 40",
                    "--fk-veil": "13, 22, 46", "--fk-date-1": "#FFE7A8", "--fk-date-2": "#F0C66B", "--fk-date-3": "#D9A63F",
                    "--fx-1": "#FFFFFF", "--fx-2": "#FFF3D6", "--fx-3": "#F0C66B", "--fx-4": "#DCE8FF", "--fx-bg": "#0F1A33",
                    "--fk-accent-ink": "#14182B", "--fk-field-bg": "#FFF9EA", "--fk-field-ink": "#1F1A1A", "--fk-shadow": "0, 0, 0"},
    },
    {
        "slug": "gouden-poort", "naam": "Gouden poort", "sort_order": 54,
        "tagline": "Gouden deuren gaan open naar een paleistuin met fonteinen in het avondlicht",
        "beschrijving": "Gouden deuren met een fijn sterpatroon.",
        "omschrijving": "Je ziet eerst gouden deuren met een fijn, stralend sterpatroon. Na een tik gaan ze open en kijk je door een hoge boog naar een paleis met een gouden koepel, palmen, bloemen, lantaarns en een lange waterpartij in het licht van de avondzon. Daarna staan jullie namen in de lucht en loopt de uitnodiging door met aftellen, programma, locatie en aanmelden, in champagne en goud. De opening is over te slaan en rustig bij minder beweging. De film is een gegenereerde scène zonder personen.",
        "stijl": "Gouden deuren met sterpatroon, paleis met koepel, palmen en fonteinen, avondzon; weelderig en feestelijk",
        "gelegenheden": ["bruiloft", "verloving", "jubileum", "verjaardag"], "label": "Gouden deuren die opengaan naar een paleistuin (film)",
        "film_aria": "Gouden deuren met een sterpatroon gaan open en tonen door een hoge boog een paleis met een gouden koepel, palmen en fonteinen",
        "palet": ("champagne-goud", "Champagne en goud", ["#FFFAEE", "#C9A24A", "#35291A"]),
        "namen": ("Gilda Display", "gilda-display-latin-400-normal.woff2"), "sky": (12, 12, 5, 20),
        "effecten": {"sfeer": "goudstof", "knal": "vonken", "viering": "vonken", "namen": "folie", "onthul": "zacht", "extra": ["tik"]},
        "kleuren": {"--fk-page": "#F6ECD8", "--fk-page-2": "#FBF3E2", "--fk-dusk": "#E8D2A8", "--fk-paper": "#FFFAEE", "--fk-paper-2": "#F4E7CC",
                    "--fk-paper-rgb": "255, 250, 238", "--fk-ink": "#35291A", "--fk-muted": "#5F4D32", "--fk-accent": "#7A5518", "--fk-gold": "#C9A24A",
                    "--fk-gold-line": "#8F6A1E", "--fk-sky-ink": "#3A2A12", "--fk-sky-muted": "#5A4220", "--fk-glow": "255, 246, 226",
                    "--fk-veil": "246, 236, 214", "--fk-date-1": "#B58A2E", "--fk-date-2": "#7A5518", "--fk-date-3": "#5C3F0E",
                    "--fx-1": "#FFF4D0", "--fx-2": "#F0D082", "--fx-3": "#DDB255", "--fx-4": "#FFFFFF", "--fx-bg": "#35291A", **KLEUR_LICHT},
    },
]


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def frame(bron: Path, tijd: float, uit: Path):
    if tijd >= 9.9:
        ffmpeg("-sseof", "-0.04", "-i", str(bron), "-frames:v", "1", str(uit))
    else:
        ffmpeg("-ss", str(tijd), "-i", str(bron), "-frames:v", "1", str(uit))


def webp(afbeelding: Image.Image, uit: Path, breedte: int | None = None, hoogte: int | None = None, kwaliteit: int = 80):
    if breedte and hoogte:
        afbeelding = afbeelding.resize((breedte, hoogte), Image.LANCZOS)
    afbeelding.convert("RGB").save(uit, "WEBP", quality=kwaliteit, method=6)


def maak_media(kaart: dict, bron: Path, map_: Path, uitsneden: dict):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # De film: opnieuw gecodeerd voor het web (H.264, geen geluid, vooraan de index), en precies het eerste en laatste beeld als stills.
        ffmpeg("-i", str(bron), "-an", "-c:v", "libx264", "-profile:v", "high", "-level", "3.1", "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "30",
               "-movflags", "+faststart", str(map_ / "opening.mp4"))
        frame(bron, 0.0, tmp / "eerste.png")
        frame(bron, 9.9, tmp / "laatste.png")
        # Het laatste beeld van de gecodeerde film is de eindstill (zo sluit de kop exact aan op de film).
        ffmpeg("-sseof", "-0.04", "-i", str(map_ / "opening.mp4"), "-frames:v", "1", str(tmp / "laatste.png"))
        webp(Image.open(tmp / "eerste.png"), map_ / "poster.webp", kwaliteit=78)
        webp(Image.open(tmp / "laatste.png"), map_ / "end.webp", kwaliteit=82)
        afmetingen = {"a": (640, 380), "b": (640, 400), "c": (460, 500), "d": (520, 190), "band": (720, 560),
                      "g1": (360, 480), "g2": (360, 480), "g3": (360, 480), "g4": (360, 480)}
        for naam, (x, y, b, h, t) in uitsneden.items():
            frame(bron, t, tmp / f"{naam}.png")
            beeld = Image.open(tmp / f"{naam}.png").crop((x, y, x + b, y + h))
            uit = {"band": "band.webp"}.get(naam) or (f"gal-{naam[1]}.webp" if naam.startswith("g") else f"cut-{naam}.webp")
            webp(beeld, map_ / uit, *afmetingen[naam], kwaliteit=76)
        # Kaartbeeld voor de collectie (4:5): de bovenkant van het eindbeeld, met het hoogtepunt van de scène.
        kaartbeeld = Image.open(tmp / "laatste.png").crop((0, 80, 720, 980))
        webp(kaartbeeld, ROOT / "static" / "img" / "designs" / f"{kaart['slug']}.webp", 800, 1000, kwaliteit=80)


def vul(tekst: str, kaart: dict) -> str:
    leden = {"__SLUG__": kaart["slug"], "__NAAM__": kaart["naam"], "__BESCHRIJVING__": kaart["beschrijving"],
             "__NAMESFONT__": kaart["namen"][0], "__NAMESFILE__": kaart["namen"][1]}
    for sleutel, waarde in leden.items():
        tekst = tekst.replace(sleutel, waarde)
    return tekst


def maak_tekst(kaart: dict, map_: Path):
    (map_ / "invitation.html").write_text(vul((SJABLOON / "invitation.html").read_text(encoding="utf-8"), kaart), encoding="utf-8")
    links, rechts, boven, hoogte = kaart["sky"]
    eigen = (f"\n/* ---------- Eigen instellingen van dit ontwerp (tools/introkaarten/maak_introkaarten.py) ---------- */\n"
             f"body {{ --fk-sky-l: {links}%; --fk-sky-r: {rechts}%; --fk-sky-t: {boven}%; --fk-sky-h: {hoogte}%; }}\n")
    (map_ / "style.css").write_text(vul((SJABLOON / "style.css").read_text(encoding="utf-8"), kaart) + eigen, encoding="utf-8")
    sleutel, naam, swatch = kaart["palet"]
    manifest = {
        "slug": kaart["slug"], "added_at": ADDED, "version": 1, "name": kaart["naam"], "tagline": kaart["tagline"],
        "description": kaart["omschrijving"], "style_notes": kaart["stijl"], "occasions": kaart["gelegenheden"], "sort_order": kaart["sort_order"],
        "opening": "film", "opening_label": kaart["label"],
        "palettes": [{"key": sleutel, "name": naam, "swatch": swatch, "vars": kaart["kleuren"]}],
        "sections": ["countdown", "story", "gallery", "program", "location", "dresscode", "practical", "rsvp", "contact", "closing", "music"],
        "effects": kaart["effecten"],
        "film": {"src": "opening.mp4", "poster": "poster.webp", "end": "end.webp", "seconds": 10.0, "kaartbeeld": "kop"},
        "changelog": "Eerste versie: opening met een film van de eigenaar (gegenereerde scène zonder personen), een tik start hem; de kop toont het laatste beeld met de namen in de lucht en de datum in het licht eronder. Verborgen voor klanten tot de rechten op de film zijn bevestigd.",
        "envelope_mode": "built_in", "hidden": True,
    }
    (map_ / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    bronmap = Path(sys.argv[1])
    gekozen = set(sys.argv[2:])
    for kaart in KAARTEN:
        if gekozen and kaart["slug"] not in gekozen:
            continue
        map_ = ROOT / "designs" / kaart["slug"] / "v1"
        map_.mkdir(parents=True, exist_ok=True)
        maak_media(kaart, bronmap / BRON[kaart["slug"]], map_, kaart.get("uitsneden") or STANDAARD_UITSNEDEN)
        maak_tekst(kaart, map_)
        print("klaar:", kaart["slug"])


if __name__ == "__main__":
    main()
