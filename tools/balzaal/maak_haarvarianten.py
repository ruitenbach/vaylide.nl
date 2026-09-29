"""Maakt de acht haarkleurvarianten van het Balzaal-paar met de beeld-API (Gemini): dezelfde scène, alleen andere haarkleur.

Kost geld per beeld (ca. $0,14 met Gemini 3 Pro Image). Draai alleen bewust, met GEMINI_API_KEY in de omgeving:

    python tools/balzaal/maak_haarvarianten.py --schatting
    python tools/balzaal/maak_haarvarianten.py --alle             # alle ontbrekende combinaties
    python tools/balzaal/maak_haarvarianten.py --combo zwart-blond

Uitvoer: designs/balzaal/v1/img/scene-<man>-<vrouw>.webp en -600.webp. Bekijk ze vóór je ze vastlegt in Git; de keuze
verschijnt in de editor zodra alle negen combinaties er zijn. Geen kleurfilter: de API verandert alleen het haar.
"""
from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

KLEUREN = ("zwart", "bruin", "blond")
EN = {"zwart": "black", "bruin": "brown", "blond": "blonde"}
PRICE = 0.14  # dollar per beeld (Gemini 3 Pro Image, 2K), september 2026

PROMPT = (
    "Edit this wedding photo. Change ONLY the hair colour: the bride gets {vrouw} hair (still long, in loose waves) and the "
    "groom gets {man} hair (still short). Keep both faces, skin tones, expressions, poses, hands, the bright white wedding "
    "dress (never gold, champagne or beige), the black tuxedo with white shirt and black bow tie, the ballroom, the "
    "lighting, the framing and the image size exactly the same. Photorealistic. No text or watermarks."
)


def main(argv=None) -> int:
    import django

    django.setup()
    from PIL import Image

    from gezichten.provider import FaceProviderError, GeminiProvider

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--combo", help="man-vrouw, bijv. zwart-blond")
    parser.add_argument("--alle", action="store_true", help="alle ontbrekende combinaties")
    parser.add_argument("--schatting", action="store_true")
    args = parser.parse_args(argv)
    img = ROOT / "designs/balzaal/v1/img"
    todo = [(m, v) for m in KLEUREN for v in KLEUREN if (m, v) != ("bruin", "blond") and not (img / f"scene-{m}-{v}.webp").is_file()]
    if args.combo:
        m, v = args.combo.split("-")
        todo = [(m, v)]
    print(f"Te maken: {len(todo)} beeld(en), ca. ${len(todo) * PRICE:.2f} (plus eventuele nieuwe pogingen).")
    if args.schatting or not (args.alle or args.combo):
        return 0
    base = (img / "scene-bruin-blond.webp").read_bytes()
    provider = GeminiProvider()
    for m, v in todo:
        try:
            data = provider.edit(PROMPT.format(man=EN[m], vrouw=EN[v]), [base])
        except FaceProviderError as exc:
            print(f"{m}-{v}: mislukt ({exc})")
            continue
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert("RGB").resize((941, 1672), Image.Resampling.LANCZOS)  # zelfde maat als de zaal
            im.save(img / f"scene-{m}-{v}.webp", "WEBP", quality=82, method=6)
            im.resize((600, 1066), Image.Resampling.LANCZOS).save(img / f"scene-{m}-{v}-600.webp", "WEBP", quality=80, method=6)
        print(f"{m}-{v}: klaar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
