"""Maakt de beelden van de kerstkaart Kerstcoupé uit het filmpje van de eigenaar.

Gebruik (vanuit de projectmap; ffmpeg moet geïnstalleerd zijn):
    .venv/bin/python tools/kerstcoupe/maak_film.py <filmpje.mp4> [--begin 24] [--eind 118]

Het filmpje (720 × 1280, 24 beelden per seconde, waarvan elk tweede beeld een kopie is) toont een treincoupé:
de gordijnen gaan open, daarna verschijnt er tekst op het raam. Alleen het stuk zonder tekst wordt gebruikt:
beeld 24 (1,0 s, gordijnen nog dicht) tot en met beeld 118 (4,9 s, gordijnen open, nog geen letter).
De tekst op het raam maakt de kaart zelf, met de namen van de klant.

Het script schrijft naar designs/kerstcoupe/v1/img/:
    coupe.mp4, coupe.webm   het filmpje van de gordijnen (vloeiend gemaakt naar 24 echte beelden per seconde, geen geluid)
    dicht.webp              het eerste beeld (openingsscherm en poster van het filmpje)
    open.webp               het laatste beeld (de kop van de kaart; moet precies gelijk zijn aan het einde van het filmpje)
    dicht-zacht.webp, open-zacht.webp   kleine, vage versies voor de rand op brede schermen
    tafel.webp              de tafel met de kaarsen en het kopje thee (het slot van de kaart)

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
OUT = ROOT / "designs" / "kerstcoupe" / "v1" / "img"


def run(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bron", type=Path, help="het filmpje van de eigenaar (mp4)")
    parser.add_argument("--begin", type=int, default=24, help="eerste beeld (24 = 1,0 s)")
    parser.add_argument("--eind", type=int, default=118, help="laatste beeld zonder tekst (118 = 4,9 s)")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # 1. Alleen de unieke beelden (even nummers) van het stuk zonder tekst, op 12 beelden per seconde.
        run("-i", str(args.bron), "-vf", f"select='between(n\\,{args.begin}\\,{args.eind})*not(mod(n\\,2))',setpts=N/(12*TB)",
            "-r", "12", "-an", "-c:v", "ffv1", str(tmp / "uniek.mkv"))
        # 2. Tussenbeelden berekenen, zodat de gordijnen vloeiend bewegen (24 beelden per seconde).
        run("-i", str(tmp / "uniek.mkv"), "-vf", "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
            "-c:v", "ffv1", str(tmp / "vloeiend.mkv"))
        # 3. Het filmpje voor de website: mp4 (H.264) en webm (VP9), zonder geluid.
        run("-i", str(tmp / "vloeiend.mkv"), "-an", "-c:v", "libx264", "-preset", "veryslow", "-crf", "23", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-tune", "film", str(OUT / "coupe.mp4"))
        run("-i", str(tmp / "vloeiend.mkv"), "-an", "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "33", "-deadline", "good",
            "-cpu-used", "1", "-row-mt", "1", "-pix_fmt", "yuv420p", str(OUT / "coupe.webm"))
        # 4. Eerste en laatste beeld, de vage randen en de tafel.
        run("-i", str(tmp / "vloeiend.mkv"), "-vf", "select='eq(n\\,0)'", "-frames:v", "1", str(tmp / "dicht.png"))
        run("-sseof", "-0.05", "-i", str(tmp / "vloeiend.mkv"), "-frames:v", "1", str(tmp / "open.png"))
        for name in ("dicht", "open"):
            image = Image.open(tmp / f"{name}.png").convert("RGB")
            image.save(OUT / f"{name}.webp", quality=82, method=6)
            soft = image.resize((90, 160), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3.5)).resize((270, 480), Image.BICUBIC)
            soft.save(OUT / f"{name}-zacht.webp", quality=70, method=6)
        Image.open(tmp / "open.png").convert("RGB").crop((0, 860, 720, 1280)).save(OUT / "tafel.webp", quality=82, method=6)
    for path in sorted(OUT.iterdir()):
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
