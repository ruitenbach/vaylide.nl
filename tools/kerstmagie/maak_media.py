"""Maakt de bestanden in designs/kerstmagie/v1/media/ opnieuw uit de bronfilm.

Gebruik (vanuit de projectmap; ffmpeg en Pillow nodig):
    .venv/bin/python tools/kerstmagie/maak_media.py <bronfilm.mp4> [uitvoermap]

De bronfilm is een stille film van 10 seconden, 720 × 1280 (staand): een sneeuwkristal dat opent naar een
kerstdorp met een stoomtrein. De bronfilm zelf staat niet in git (25 MB); de eigenaar heeft hem aangeleverd.
Zonder uitvoermap worden de bestanden in designs/kerstmagie/v1/media/ overschreven.

De uitsneden horen bij dit beeld. Gebruik je een andere film, kijk dan eerst naar het
laatste beeld (dorp.webp) en pas de vakjes in UITSNEDEN aan.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

MEDIA = Path(__file__).resolve().parents[2] / "designs" / "kerstmagie" / "v1" / "media"
# Uitsneden uit losse beelden van de film: (naam, moment in seconden, (links, boven, rechts, onder)) op het beeld van 720 x 1280.
# Het eindbeeld is 9,95 s; het kristal met gloed 3,6 s; het kristal dat in het dorp overvloeit 4,2 s; de trein met stoom 8 s.
UITSNEDEN = [
    ("pano.webp", 9.95, (0, 70, 720, 420)),        # bergen, viaduct en klokkentoren (strook onder de kop)
    ("gloed.webp", 3.6, (40, 260, 680, 1060)),     # kristal met warme gloed (boogvenster)
    ("trein.webp", 8.0, (0, 430, 460, 1005)),      # trein met stoom op de brug (boogvenster)
    ("plein.webp", 9.95, (330, 560, 720, 1080)),   # plein, draaimolen en kerstboom (drieluik)
    ("tussen.webp", 4.2, (0, 160, 720, 1120)),     # kristal dat in het dorp overvloeit (drieluik)
    ("rivier.webp", 9.95, (90, 800, 450, 1280)),   # lichtjes bij de rivier (drieluik)
    ("water.webp", 9.95, (0, 980, 720, 1280)),     # water en verlichte sparren (achtergrond van de locatie)
]
# Het sneeuwkristal staat midden in het eerste beeld.
KRISTAL = (0, 280, 720, 1000)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def main(bron: str, uit: Path) -> None:
    uit.mkdir(parents=True, exist_ok=True)
    # Film voor de telefoon: geen geluid, H.264 met snelle start (mp4), en VP9 (webm) voor browsers zonder H.264.
    ffmpeg("-i", bron, "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "30", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-g", "30", str(uit / "intro.mp4"))
    ffmpeg("-i", bron, "-an", "-c:v", "libvpx-vp9", "-crf", "43", "-b:v", "0", "-row-mt", "1",
           "-deadline", "good", "-cpu-used", "2", "-pix_fmt", "yuv420p", str(uit / "intro.webm"))
    with tempfile.TemporaryDirectory() as tmp:
        def beeld(seconde):
            pad = Path(tmp) / f"b{seconde}.png"
            if not pad.exists():
                ffmpeg("-ss", str(seconde), "-i", bron, "-frames:v", "1", str(pad))
            return Image.open(pad).convert("RGB")

        first, last = beeld(0), beeld(9.95)
        first.save(uit / "poster.webp", quality=74, method=6)  # beeld op het openingsscherm, voordat de film speelt
        last.save(uit / "dorp.webp", quality=82, method=6)  # eindbeeld: de kop van de uitnodiging begint hierop
        first.crop(KRISTAL).resize((640, 640), Image.LANCZOS).save(uit / "sneeuwvlok.webp", quality=76, method=6)
        for naam, seconde, vak in UITSNEDEN:
            beeld(seconde).crop(vak).save(uit / naam, quality=82, method=6)
    for f in sorted(uit.iterdir()):
        print(f"{f.name:16} {f.stat().st_size / 1000:8.0f} KB")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else MEDIA)
