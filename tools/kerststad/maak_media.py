"""Kerststad: webmedia maken uit de goedgekeurde video's (de video's zelf worden niet opnieuw gegenereerd of bijgewerkt).

Twee masters, beide buiten Git:
  --mobiel   9:16, 1080x1920, 24 fps, 20,04 s, HEVC 10-bit, 71 MB (de oorspronkelijke goedgekeurde video)
  --desktop  16:9 (bijvoorbeeld 1920x1080), dezelfde Kerststad, bewust opnieuw gemaakt voor brede schermen

    python tools/kerststad/maak_media.py [--mobiel <9:16-bron>] [--desktop <16:9-bron> --lus-desktop <seconden>] [--ffmpeg <pad>]
Elke master is optioneel: wie alleen --desktop geeft, laat de mobiele bestanden ongemoeid.

Maakt in designs/kerststad/v1/media/:
  opening.mp4           mobiel/staand 9:16: H.264 8-bit, 720x1280, CRF 23, zonder geluid, sleutelframe om de 2 s en precies op LUS_MOBIEL (16,0 s)
  poster.webp           eerste beeld (mobiel): de badge met de V
  eind.webp             laatste beeld (mobiel)
  badge.webp            de ronde badge met de officiële VAYLIDE-V, uitgesneden uit het eerste beeld (medaillon in de kaart)
  dorp-*.webp           uitsneden uit latere beelden als achtergrond van de kaart
  opening-desktop.mp4   desktop/liggend 16:9 in de resolutie van de bron (1920x1080): H.264 High, yuv420p, 24 fps, CRF 19, zonder geluid, faststart, sleutelframe om de 2 s en precies op --lus-desktop;
                        geen tweede resize, geen scherpte- of andere filters (alleen de omzetting van 10-bit naar 8-bit die browsers nodig hebben)
  poster-desktop.webp   eerste beeld (desktop, volle resolutie)
  eind-desktop.webp     laatste beeld (desktop, volle resolutie)
en het kaartbeeld static/img/designs/kerststad.webp (800x1000, uit het laatste mobiele beeld).
Geen bijsnijding, geen kleurcorrectie: alleen verkleind en gecomprimeerd.
"""
import argparse
import subprocess
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

LUS_MOBIEL = 16.0

ap = argparse.ArgumentParser()
ap.add_argument("--mobiel")
ap.add_argument("--desktop")
ap.add_argument("--lus-desktop", type=float)
ap.add_argument("--ffmpeg", default="ffmpeg")
args = ap.parse_args()
if not (args.mobiel or args.desktop):
    ap.error("geef minstens --mobiel of --desktop")
if bool(args.desktop) != bool(args.lus_desktop):
    ap.error("--desktop en --lus-desktop horen bij elkaar")

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "designs/kerststad/v1/media"
MEDIA.mkdir(parents=True, exist_ok=True)


def encodeer(bron: str, uit: Path, breedte: int | None, hoogte: int | None, sleutelframe: float, crf: int = 23) -> None:
    filter_ = f"scale={breedte}:{hoogte}:flags=lanczos,format=yuv420p" if breedte else "format=yuv420p"   # zonder breedte: geen resize, alleen 10-bit naar 8-bit
    subprocess.run([
        args.ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", bron,
        "-vf", filter_, "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-level", "4.1", "-r", "24",
        "-x264-params", "keyint=48:min-keyint=12:scenecut=0", "-force_key_frames", str(sleutelframe),
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-an", "-movflags", "+faststart", str(uit),
    ], check=True)


def frame(bron: str, t: float) -> Image.Image:
    cap = cv2.VideoCapture(bron)
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1, round(t * 24)))
    ok, bgr = cap.read()
    assert ok, t
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def sla_op(im: Image.Image, naam: str, kwaliteit: int = 80, **kw) -> None:
    im.save(MEDIA / naam, "WEBP", quality=kwaliteit, method=6, **kw)


# ---- mobiel / staand (9:16) ----
if args.mobiel:
    BRON = args.mobiel
    encodeer(BRON, MEDIA / "opening.mp4", 720, 1280, LUS_MOBIEL)
    eerste, laatste = frame(BRON, 0), frame(BRON, 19.95)
    sla_op(eerste.resize((720, 1280), Image.LANCZOS), "poster.webp", 80)
    sla_op(laatste.resize((720, 1280), Image.LANCZOS), "eind.webp", 78)

    # De ronde badge: middelpunt (49,2 %; 50,5 %) en straal 47 % van de breedte in het eerste beeld.
    cx, cy, r = round(0.492 * 1080), round(0.505 * 1920), round(0.472 * 1080)
    badge = eerste.crop((cx - r, cy - r, cx + r, cy + r)).resize((420, 420), Image.LANCZOS).convert("RGBA")
    masker = Image.new("L", (420 * 4, 420 * 4), 0)
    ImageDraw.Draw(masker).ellipse((0, 0, 420 * 4 - 1, 420 * 4 - 1), fill=255)
    badge.putalpha(masker.resize((420, 420), Image.LANCZOS))
    sla_op(badge, "badge.webp", 86, exact=True)

    # Achtergronden voor de banden van de kaart: stukken van het dorp in het eindbeeld en van de brug eerder in de video.
    nacht = frame(BRON, 17.0)
    sla_op(nacht.crop((0, 120, 1080, 1100)).resize((900, 817), Image.LANCZOS), "dorp-kerk.webp", 62)         # kerk, kerstboom, huisjes
    sla_op(nacht.crop((0, 1000, 1080, 1920)).resize((900, 767), Image.LANCZOS), "dorp-ijs.webp", 62)         # ijsbaan, pad, lantaarns
    brug = frame(BRON, 12.0)
    sla_op(brug.crop((0, 700, 1080, 1700)).resize((900, 833), Image.LANCZOS), "dorp-brug.webp", 62)          # de brug met de badge, lampjes

    # Kaartbeeld voor de ontwerpkaarten (4:5): het dorp in de nacht.
    kaart = laatste.crop((0, 120, 1080, 1470)).resize((800, 1000), Image.LANCZOS)
    kaart.save(ROOT / "static/img/designs/kerststad.webp", "WEBP", quality=74, method=6)

# ---- desktop / liggend (16:9) ----
if args.desktop:
    encodeer(args.desktop, MEDIA / "opening-desktop.mp4", None, None, args.lus_desktop, crf=19)
    sla_op(frame(args.desktop, 0), "poster-desktop.webp", 84)
    sla_op(frame(args.desktop, 999), "eind-desktop.webp", 82)
print("klaar")
