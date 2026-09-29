"""Maakt de dansscène voor Balzaal met Google Veo (image-to-video): het bruidspaar danst en de bruid maakt één draai.

Kost geld per poging. Draai alleen bewust, met GEMINI_API_KEY in de omgeving (nooit in Git):

    python tools/balzaal/maak_dansvideo.py --schatting                      # alleen de kosten tonen
    python tools/balzaal/maak_dansvideo.py --proef                          # proefscène (Veo Fast, 720p) naar data/
    python tools/balzaal/maak_dansvideo.py --combo bruin-blond --model standaard --resolutie 1080p --definitief

Een proefscène komt in data/balzaal-proef/ (niet op de site). Met --definitief komt de video in
designs/balzaal/v1/video/dans-<man>-<vrouw>.mp4 en toont de kaart hem vanzelf (catalog/paar.py). Is ffmpeg
aanwezig, dan wordt de video verkleind voor mobiel (540×960, zonder geluid, ~2 MB).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def main(argv=None) -> int:
    import django

    django.setup()
    from django.conf import settings
    from PIL import Image

    from gezichten.veo import MODELS, VeoClient, VeoError, estimate

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--combo", default="bruin-blond", help="haarkleur man-vrouw, bijv. bruin-blond")
    parser.add_argument("--model", choices=sorted(MODELS), default="fast")
    parser.add_argument("--resolutie", choices=["720p", "1080p"], default="720p")
    parser.add_argument("--schatting", action="store_true", help="alleen de kosten tonen, niets aanroepen")
    parser.add_argument("--proef", action="store_true", help="proefscène naar data/balzaal-proef/")
    parser.add_argument("--definitief", action="store_true", help="naar designs/balzaal/v1/video/ (verschijnt op de kaart)")
    args = parser.parse_args(argv)

    cost = estimate(args.model, args.resolutie)
    print(f"Veo {args.model}, {args.resolutie}, 8 seconden: ca. ${cost:.2f} per poging.")
    if args.schatting or not (args.proef or args.definitief):
        return 0
    scene = ROOT / "designs/balzaal/v1/img" / f"scene-{args.combo}.webp"
    if not scene.is_file():
        print(f"Scène ontbreekt: {scene.name}. Maak eerst de haarkleurvariant (maak_haarvarianten.py).")
        return 1
    import io

    buffer = io.BytesIO()
    Image.open(scene).convert("RGB").save(buffer, "PNG")
    try:
        video = VeoClient().generate(buffer.getvalue(), model=args.model, resolution=args.resolutie)
    except VeoError as exc:
        print(f"Mislukt: {exc}")
        return 1
    target_dir = ROOT / "designs/balzaal/v1/video" if args.definitief else Path(settings.DATA_DIR) / "balzaal-proef"
    target_dir.mkdir(parents=True, exist_ok=True)
    raw = target_dir / f"dans-{args.combo}-origineel.mp4"
    raw.write_bytes(video)
    final = target_dir / f"dans-{args.combo}.mp4"
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        subprocess.run([ffmpeg, "-y", "-i", str(raw), "-an", "-vf", "scale=540:-2", "-c:v", "libx264", "-crf", "27", "-preset", "slow",
                        "-movflags", "+faststart", "-pix_fmt", "yuv420p", str(final)], check=True)
        raw.unlink()
    else:
        raw.replace(final)
        print("Let op: ffmpeg niet gevonden; de video is niet verkleind voor mobiel.")
    print(f"Klaar: {final} ({final.stat().st_size // 1024} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
