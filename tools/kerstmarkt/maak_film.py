"""Maakt de beelden van de kerstkaart Kerstmarkt uit het filmpje van de eigenaar.

Gebruik (vanuit de projectmap; ffmpeg moet geïnstalleerd zijn):
    .venv/bin/python tools/kerstmarkt/maak_film.py <filmpje.mp4> [--eind 132]

Het filmpje (720 × 1280, 24 beelden per seconde, 10 seconden, zonder geluid) kijkt vanuit een reuzenrad
over een kerstmarkt bij avond. Rond 2,5 seconden verschijnt een lichtstreep die uitgroeit tot een lege kaart
met een ster erboven; daarna zoomt het beeld langzaam in. Alleen het begin wordt gebruikt: beeld 0 tot en met
beeld 132 (5,5 s), het moment waarop de gloed rond de kaart weg is. Daarna neemt de echte kaart het over.

Het script schrijft naar designs/kerstmarkt/v1/img/:
    markt.mp4, markt.webm     het filmpje (5,5 s, geen geluid)
    begin.webp                het eerste beeld (openingsscherm en poster van het filmpje)
    kaart.webp                het laatste beeld (de kop van de kaart; moet precies gelijk zijn aan het einde van het filmpje)
    begin-zacht.webp, kaart-zacht.webp   kleine, vage versies voor de rand op brede schermen
    slot.webp                 de kerstmarkt uit het eerste beeld (het slot van de kaart)

Wijzig je de beelden van een uitgebrachte versie, maak dan een v2 (zie docs/HANDLEIDING.md).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "designs" / "kerstmarkt" / "v1" / "img"
# Het slot: het reuzenrad, de torens, de kerstboom en de kraampjes uit het eerste beeld (4:5).
SLOT_CROP = (0, 300, 720, 1200)


def run(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bron", type=Path, help="het filmpje van de eigenaar (mp4)")
    parser.add_argument("--eind", type=int, default=132, help="laatste beeld (132 = 5,5 s, de kaart staat er zonder gloed)")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # 1. Het stuk van het filmpje dat de kaart gebruikt, verliesvrij.
        run("-i", str(args.bron), "-vf", f"select='lte(n\\,{args.eind})',setpts=N/(24*TB)", "-r", "24", "-an",
            "-c:v", "ffv1", str(tmp / "stuk.mkv"))
        # 2. Het filmpje voor de website: mp4 (H.264) en webm (VP9), zonder geluid. Het beeld zit vol fijne lichtjes en
        #    sneeuw; in twee rondes coderen met een vaste bitrate geeft bij dezelfde grootte het scherpste beeld.
        log = str(tmp / "pass")
        h264 = ["-an", "-c:v", "libx264", "-preset", "veryslow", "-b:v", "1300k", "-profile:v", "high", "-pix_fmt", "yuv420p",
                "-tune", "film", "-passlogfile", log]
        run("-i", str(tmp / "stuk.mkv"), *h264, "-pass", "1", "-f", "null", "/dev/null")
        run("-i", str(tmp / "stuk.mkv"), *h264, "-pass", "2", "-movflags", "+faststart", str(OUT / "markt.mp4"))
        vp9 = ["-an", "-c:v", "libvpx-vp9", "-b:v", "1100k", "-deadline", "good", "-row-mt", "1", "-pix_fmt", "yuv420p",
               "-passlogfile", log]
        run("-i", str(tmp / "stuk.mkv"), *vp9, "-cpu-used", "2", "-pass", "1", "-f", "null", "/dev/null")
        run("-i", str(tmp / "stuk.mkv"), *vp9, "-cpu-used", "1", "-auto-alt-ref", "1", "-lag-in-frames", "25", "-pass", "2",
            str(OUT / "markt.webm"))
        # 3. Eerste en laatste beeld, de vage randen en het slot.
        run("-i", str(tmp / "stuk.mkv"), "-vf", "select='eq(n\\,0)'", "-frames:v", "1", str(tmp / "begin.png"))
        run("-i", str(tmp / "stuk.mkv"), "-vf", f"select='eq(n\\,{args.eind})'", "-frames:v", "1", str(tmp / "kaart.png"))
        for name in ("begin", "kaart"):
            image = Image.open(tmp / f"{name}.png").convert("RGB")
            image.save(OUT / f"{name}.webp", quality=80, method=6)
            soft = image.resize((90, 160), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3.5)).resize((270, 480), Image.BICUBIC)
            soft.save(OUT / f"{name}-zacht.webp", quality=70, method=6)
        Image.open(tmp / "begin.png").convert("RGB").crop(SLOT_CROP).save(OUT / "slot.webp", quality=80, method=6)
    for path in sorted(OUT.iterdir()):
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
