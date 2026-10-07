"""Kerststad: de camerabeweging van de liggende (16:9) video meten voor de levende laag (designs/kerststad/v1/kerststad-spoor.js).

    python tools/kerststad/maak_spoor.py <pad-naar-de-16x9-bron>

De video zelf wordt niet bewerkt. Voor twee stukken van het beeld wordt per beeld tussen 12,0 en 20,04 s een affiene uitlijning (ECC) op het referentiebeeld (16,0 s) gemeten, in beeldpunten
van 960 x 540: "gevel" (het huis links naast de kerk, voor de officiële V) en "plein" (de grond rond de kerstboom, voor de figuurtjes). De uitkomst is één rij [a, b, tx, c, d, ty] per twee beelden.
Draai dit opnieuw als de liggende video verandert; pas daarna ook de ankerpunten en paden in kerststad.js en invitation.html aan.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

BRON = sys.argv[1]
REF, VAN = 384, 12 * 24                       # referentiebeeld 16,0 s; begin van het spoor 12,0 s
UIT = Path(__file__).resolve().parents[2] / "designs/kerststad/v1/kerststad-spoor.js"

cap = cv2.VideoCapture(BRON)
beelden = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    grijs = cv2.cvtColor(cv2.resize(f, (960, 540), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    beelden.append(cv2.GaussianBlur(grijs, (5, 5), 0).astype(np.float32) / 255)


def vlak(x0, y0, x1, y1):
    m = np.zeros((540, 960), np.uint8)
    m[y0:y1, x0:x1] = 255
    return m


GEBIEDEN = {"gevel": vlak(240, 180, 350, 285), "plein": vlak(250, 275, 700, 420)}
CRITERIUM = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
resultaat = {}
for naam, masker in GEBIEDEN.items():
    matrices = {REF: np.eye(2, 3, dtype=np.float32)}
    for richting in (1, -1):
        w, i = np.eye(2, 3, dtype=np.float32), REF
        while VAN <= i + richting < len(beelden):
            j = i + richting
            try:
                _, w = cv2.findTransformECC(beelden[REF], beelden[j], w.copy(), cv2.MOTION_AFFINE, CRITERIUM, masker, 5)
            except cv2.error:
                pass
            matrices[j] = w.copy()
            i = j
    frames = sorted(matrices)
    rij = np.array([matrices[i].flatten() for i in frames])
    glad = np.vstack([np.convolve(np.pad(rij[:, k], (2, 2), mode="edge"), np.ones(5) / 5, mode="valid") for k in range(6)]).T
    resultaat[naam] = [[round(float(v), 4) for v in glad[n]] for n, i in enumerate(frames) if (i - VAN) % 2 == 0]

tekst = ("/* Kerststad: de camerabeweging van de liggende video tussen 12,0 en 20,04 s, gemeten uit de video zelf (tools/kerststad/maak_spoor.py, ECC-uitlijning). Elke rij is [a, b, tx, c, d, ty]\n"
         "   en beeldt een punt van het referentiebeeld (16,0 s) in een beeld van 960 x 540 af op het beeld op dat tijdstip: x' = a*x + b*y + tx, y' = c*x + d*y + ty. Eén rij per twee beelden\n"
         "   (12 per seconde, vanaf 12,0 s). \"gevel\" volgt het huis links naast de kerk, \"plein\" de grond rond de kerstboom. De overlay (V en figuurtjes) in kerststad.js blijft hiermee op zijn plek. */\n"
         "window.KERSTSTAD_SPOOR = {van: 12, stap: 2 / 24, ref: 16, gevel: %s, plein: %s};\n") % (
    json.dumps(resultaat["gevel"], separators=(",", ":")), json.dumps(resultaat["plein"], separators=(",", ":")))
UIT.write_text(tekst, encoding="utf-8", newline="\n")
print("klaar:", UIT)
