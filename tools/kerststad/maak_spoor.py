"""Kerststad: de camerabeweging van beide video's meten voor de levende laag (designs/kerststad/v1/kerststad-spoor.js).

    python tools/kerststad/maak_spoor.py --liggend <pad-naar-de-16x9-bron> --staand <pad-naar-de-9x16-bron>

De video's zelf worden niet bewerkt. Voor twee stukken van het beeld wordt per beeld tussen 12,0 en 20,04 s een affiene uitlijning (ECC) op het referentiebeeld (16,0 s) gemeten, in beeldpunten
van het werkformaat (liggend 960 x 540, staand 540 x 960): "gevel" (het huis links naast de kerk, voor de officiële V) en "plein" (de grond rond de kerstboom, voor de figuurtjes).
De uitkomst is één rij [a, b, tx, c, d, ty] per twee beelden. Draai dit opnieuw als een video verandert; pas daarna ook de ankerpunten en paden in kerststad.js en invitation.html aan.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--liggend", required=True)
ap.add_argument("--staand", required=True)
args = ap.parse_args()

REF, VAN = 384, 12 * 24                       # referentiebeeld 16,0 s; begin van het spoor 12,0 s
UIT = Path(__file__).resolve().parents[2] / "designs/kerststad/v1/kerststad-spoor.js"
CRITERIUM = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)

# werkformaat en de twee uitlijngebieden (x0, y0, x1, y1) per video
FORMATEN = {
    "breed": {"bron": args.liggend, "w": 960, "h": 540, "gevel": (240, 180, 350, 285), "plein": (250, 275, 700, 420)},
    "smal": {"bron": args.staand, "w": 540, "h": 960, "gevel": (100, 325, 220, 415), "plein": (80, 430, 520, 600)},
}


def meet(f):
    cap = cv2.VideoCapture(f["bron"])
    beelden = []
    while True:
        ok, beeld = cap.read()
        if not ok:
            break
        grijs = cv2.cvtColor(cv2.resize(beeld, (f["w"], f["h"]), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        beelden.append(cv2.GaussianBlur(grijs, (5, 5), 0).astype(np.float32) / 255)
    uit = {}
    for naam in ("gevel", "plein"):
        x0, y0, x1, y1 = f[naam]
        masker = np.zeros((f["h"], f["w"]), np.uint8)
        masker[y0:y1, x0:x1] = 255
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
        uit[naam] = [[round(float(v), 4) for v in glad[n]] for n, i in enumerate(frames) if (i - VAN) % 2 == 0]
    return uit


data = {}
for sleutel, f in FORMATEN.items():
    data[sleutel] = {"w": f["w"], "h": f["h"], **meet(f)}
    print(sleutel, {k: len(v) for k, v in data[sleutel].items() if isinstance(v, list)})

tekst = ("/* Kerststad: de camerabeweging van de liggende (\"breed\") en de staande (\"smal\") video tussen 12,0 en 20,04 s, gemeten uit de video's zelf (tools/kerststad/maak_spoor.py, ECC-uitlijning).\n"
         "   Elke rij is [a, b, tx, c, d, ty] en beeldt een punt van het referentiebeeld (16,0 s) af op het beeld op dat tijdstip in beeldpunten van w x h: x' = a*x + b*y + tx, y' = c*x + d*y + ty.\n"
         "   Eén rij per twee beelden (12 per seconde, vanaf 12,0 s). \"gevel\" volgt het huis links naast de kerk, \"plein\" de grond rond de kerstboom. De levende laag in kerststad.js (de V en de\n"
         "   figuurtjes) blijft hiermee op zijn plek in het beeld. */\n"
         "window.KERSTSTAD_SPOOR = {van: 12, stap: 2 / 24, ref: 16, breed: %s, smal: %s};\n") % (
    json.dumps(data["breed"], separators=(",", ":")), json.dumps(data["smal"], separators=(",", ":")))
UIT.write_text(tekst, encoding="utf-8", newline="\n")
print("klaar:", UIT)
