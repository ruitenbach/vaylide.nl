"""Automatisch uitlijnen: waar staat het belangrijkste in een foto?

Eerst zoeken we gezichten met YuNet, een klein neuraal netwerk (via OpenCV) dat op onze eigen server draait: foto's gaan
nergens heen en het kost niets per foto (model: `invitations/models_ai/`). Zonder gezichten nemen we het drukste deel van de foto (randen en kleur), iets naar
het midden getrokken. Het resultaat is een middelpunt in procenten, zoals de uitsnede het ook bewaart (x, y).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

log = logging.getLogger(__name__)

ANALYSE_SIDE = 900  # verkleind analyseren: snel genoeg om direct bij het uploaden te doen


@dataclass(frozen=True)
class Focus:
    x: int
    y: int
    faces: int = 0


def detect(image: Image.Image) -> Focus:
    small = ImageOps.exif_transpose(image).convert("RGB")
    small.thumbnail((ANALYSE_SIDE, ANALYSE_SIDE))
    faces = _faces(small)
    if faces:
        return _from_faces(faces, small.size)
    return _from_detail(small)


def detect_file(fileobj) -> Focus | None:
    """Voor een opgeslagen bestand; None als het niet te lezen is."""
    try:
        fileobj.seek(0)
        with Image.open(fileobj) as im:
            return detect(im)
    except Exception:  # een kapotte foto mag het uploaden nooit laten mislukken
        log.warning("Automatisch uitlijnen mislukt", exc_info=True)
        return None


MODEL = Path(__file__).resolve().parent / "models_ai" / "face_detection_yunet_2023mar.onnx"
MIN_SCORE = 0.75


def _faces(image: Image.Image) -> list[tuple[int, int, int, int]]:
    """Gezichten als (x, y, breedte, hoogte) met YuNet, een klein neuraal netwerk voor gezichtsherkenning."""
    try:
        import cv2
        import numpy as np
    except ImportError:  # zonder OpenCV valt het terug op het drukste deel
        return []
    if not MODEL.is_file():
        return []
    bgr = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    height, width = bgr.shape[:2]
    detector = cv2.FaceDetectorYN.create(str(MODEL), "", (width, height), MIN_SCORE, 0.3, 50)
    _, found = detector.detect(bgr)
    if found is None:
        return []
    side = min(width, height)
    rects = [(int(f[0]), int(f[1]), int(f[2]), int(f[3])) for f in found if min(f[2], f[3]) >= side * 0.025]
    return _merge(rects)


def _merge(rects: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    """Overlappende treffers tellen als één gezicht; kleine losse treffers naast grote gezichten vallen af (vaak ruis)."""
    rects = sorted(rects, key=lambda r: r[2] * r[3], reverse=True)
    kept: list[tuple[int, int, int, int]] = []
    for x, y, w, h in rects:
        cx, cy = x + w / 2, y + h / 2
        if any(kx <= cx <= kx + kw and ky <= cy <= ky + kh for kx, ky, kw, kh in kept):
            continue
        if kept and w < kept[0][2] * 0.35:
            continue
        kept.append((x, y, w, h))
    return kept


def _from_faces(faces, size) -> Focus:
    width, height = size
    left = min(x for x, _, _, _ in faces)
    right = max(x + w for x, _, w, _ in faces)
    top = min(y for _, y, _, _ in faces)
    bottom = max(y + h for _, y, _, h in faces)
    cx = (left + right) / 2 / width
    # Iets onder de ogen: dan blijft er ruimte boven het hoofd en valt de kin niet weg.
    cy = (top + (bottom - top) * 0.6) / height
    return Focus(_pct(cx), _pct(cy), len(faces))


def _from_detail(image: Image.Image) -> Focus:
    gray = image.convert("L")
    gray.thumbnail((160, 160))
    edges = gray.filter(ImageFilter.FIND_EDGES)
    sat = image.convert("HSV").split()[1].resize(edges.size)
    width, height = edges.size
    ep, sp = edges.load(), sat.load()
    total = sx = sy = 0.0
    for j in range(2, height - 2):  # de rand zelf geeft altijd 'randen'
        for i in range(2, width - 2):
            weight = (ep[i, j] / 255) ** 2 + 0.3 * (sp[i, j] / 255) ** 2
            total += weight
            sx += weight * i
            sy += weight * j
    if total <= 0:
        return Focus(50, 50)
    cx, cy = sx / total / width, sy / total / height
    # Naar het midden getrokken: een drukke achtergrond mag de uitsnede niet helemaal naar de rand trekken.
    return Focus(_pct(0.6 * cx + 0.2), _pct(0.6 * cy + 0.2))


def _pct(value: float) -> int:
    return int(round(max(0.0, min(1.0, value)) * 100))
