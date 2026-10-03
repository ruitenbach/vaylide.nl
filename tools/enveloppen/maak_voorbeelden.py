"""Zet de schermafbeeldingen van e2e/envelop_voorbeelden.cjs om naar de voorbeeldbeelden voor de keuze in de Studio.

Gebruik (vanuit de projectmap):
    node e2e/envelop_voorbeelden.cjs http://127.0.0.1:8000 <map>      # server met DEBUG; maakt PNG's van de bestaande envelopstudio
    python tools/enveloppen/maak_voorbeelden.py <map>
Uitvoer: static/img/envelop/voorbeeld/<stijl>.webp (dichte envelop, 560 breed) en static/img/envelop/zegel/<zegel>.webp (zegel, 200 vierkant).
Er is geen nieuw artwork: het zijn beelden van de bestaande envelopstijlen en zegels.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "static" / "img" / "envelop"


def main() -> None:
    bron = Path(sys.argv[1])
    (IMG / "voorbeeld").mkdir(parents=True, exist_ok=True)
    (IMG / "zegel").mkdir(parents=True, exist_ok=True)
    for png in sorted(bron.glob("envelop-*.png")):
        naam = png.stem.removeprefix("envelop-")
        im = Image.open(png).convert("RGB")
        im = im.resize((560, round(560 * im.height / im.width)), Image.LANCZOS)
        im.save(IMG / "voorbeeld" / f"{naam}.webp", "WEBP", quality=88, method=6)
        print("voorbeeld", naam, im.size)
    for png in sorted(bron.glob("zegel-*.png")):
        naam = png.stem.removeprefix("zegel-")
        im = Image.open(png).convert("RGB").resize((200, 200), Image.LANCZOS)
        im.save(IMG / "zegel" / f"{naam}.webp", "WEBP", quality=90, method=6)
        print("zegel", naam)


if __name__ == "__main__":
    main()
