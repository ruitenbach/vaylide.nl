"""Maakt de bestanden in designs/kerstmagie/v1/media/ opnieuw uit de bronfilm.

Gebruik (vanuit de projectmap; ffmpeg en Pillow nodig):
    .venv/bin/python tools/kerstmagie/maak_media.py <bronfilm.mp4> [uitvoermap]

De bronfilm is een stille film van 10 seconden, 720 × 1280 (staand): een sneeuwkristal dat opent naar een
kerstdorp met een stoomtrein. De bronfilm zelf staat niet in git (25 MB); de eigenaar heeft hem aangeleverd.
Zonder uitvoermap worden de bestanden in designs/kerstmagie/v1/media/ overschreven.

De uitsneden (trein, plein) horen bij dit beeld. Gebruik je een andere film, kijk dan eerst naar het
laatste beeld (dorp.webp) en pas de vakjes in UITSNEDEN aan.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

MEDIA = Path(__file__).resolve().parents[2] / "designs" / "kerstmagie" / "v1" / "media"
# (naam, (links, boven, rechts, onder)) op het laatste beeld van 720 × 1280.
UITSNEDEN = {"trein.webp": (0, 560, 540, 860), "plein.webp": (300, 640, 720, 980)}
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
        eerste, laatste = Path(tmp) / "eerste.png", Path(tmp) / "laatste.png"
        ffmpeg("-i", bron, "-frames:v", "1", str(eerste))
        ffmpeg("-ss", "9.95", "-i", bron, "-frames:v", "1", str(laatste))
        first, last = Image.open(eerste).convert("RGB"), Image.open(laatste).convert("RGB")
    first.save(uit / "poster.webp", quality=74, method=6)  # beeld op het openingsscherm, voordat de film speelt
    last.save(uit / "dorp.webp", quality=82, method=6)  # eindbeeld: de kop van de uitnodiging begint hierop
    first.crop(KRISTAL).resize((640, 640), Image.LANCZOS).save(uit / "sneeuwvlok.webp", quality=76, method=6)
    for naam, vak in UITSNEDEN.items():
        last.crop(vak).save(uit / naam, quality=82, method=6)
    for f in sorted(uit.iterdir()):
        print(f"{f.name:16} {f.stat().st_size / 1000:8.0f} KB")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else MEDIA)
