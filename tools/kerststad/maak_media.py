"""Kerststad: webmedia maken uit de goedgekeurde video (de video zelf wordt niet opnieuw gegenereerd of bijgewerkt).

Bron (blijft buiten Git): de definitief goedgekeurde video, 1080x1920, 24 fps, 20,04 s, HEVC 10-bit, 71 MB.
    python tools/kerststad/maak_media.py <pad-naar-de-bronvideo> [pad-naar-ffmpeg]

Maakt in designs/kerststad/v1/media/:
  opening.mp4    dezelfde beelden, alleen web-klaar gemaakt: H.264 8-bit, 720x1280, CRF 23, zonder geluid, sleutelframe om de 2 seconden
                 en precies op LOOP_START (16,0 s), zodat de lus daar exact en zonder wachten kan inspringen. Geen bijsnijding, geen kleurcorrectie.
  poster.webp    het eerste beeld (de badge met de V), voor het laden en voor de dichte stand
  eind.webp      het laatste beeld, voor 'minder beweging' en als terugval
  badge.webp     de ronde badge met de officiële VAYLIDE-V, uitgesneden uit het eerste beeld (medaillon in de kaart)
  dorp-*.webp    uitsneden uit latere beelden als achtergrond van de kaart
en het kaartbeeld static/img/designs/kerststad.webp (800x1000).
"""
import subprocess
import sys
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

LOOP_START = 16.0
BRON = Path(sys.argv[1])
FFMPEG = sys.argv[2] if len(sys.argv) > 2 else "ffmpeg"
ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "designs/kerststad/v1/media"
MEDIA.mkdir(parents=True, exist_ok=True)

subprocess.run([
    FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(BRON),
    "-vf", "scale=720:1280:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-profile:v", "high", "-level", "4.0", "-r", "24",
    "-x264-params", "keyint=48:min-keyint=12:scenecut=0", "-force_key_frames", str(LOOP_START),
    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-an", "-movflags", "+faststart", str(MEDIA / "opening.mp4"),
], check=True)


def frame(t: float) -> Image.Image:
    cap = cv2.VideoCapture(str(BRON))
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1, round(t * 24)))
    ok, bgr = cap.read()
    assert ok, t
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def sla_op(im: Image.Image, naam: str, kwaliteit: int = 80, **kw) -> None:
    im.save(MEDIA / naam, "WEBP", quality=kwaliteit, method=6, **kw)


eerste, laatste = frame(0), frame(19.95)
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
nacht = frame(17.0)
sla_op(nacht.crop((0, 120, 1080, 1100)).resize((900, 817), Image.LANCZOS), "dorp-kerk.webp", 62)         # kerk, kerstboom, huisjes
sla_op(nacht.crop((0, 1000, 1080, 1920)).resize((900, 767), Image.LANCZOS), "dorp-ijs.webp", 62)         # ijsbaan, pad, lantaarns
brug = frame(12.0)
sla_op(brug.crop((0, 700, 1080, 1700)).resize((900, 833), Image.LANCZOS), "dorp-brug.webp", 62)          # de brug met de badge, lampjes

# Kaartbeeld voor de ontwerpkaarten (4:5): het dorp in de nacht.
kaart = laatste.crop((0, 120, 1080, 1470)).resize((800, 1000), Image.LANCZOS)
kaart.save(ROOT / "static/img/designs/kerststad.webp", "WEBP", quality=74, method=6)
print("klaar")
