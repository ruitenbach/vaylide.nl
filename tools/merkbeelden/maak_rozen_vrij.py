"""Haalt de twee rozenfoto's (witte achtergrond) vrij en schrijft transparante webp-bestanden naar static/img/site/.

Gebruik: python tools/merkbeelden/maak_rozen_vrij.py <rozen-1.png> <rozen-2.png>
De foto's zijn aangeleverd door de eigenaar (gemaakt met een beeldgenerator); dit script bewerkt ze alleen."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

UIT = Path(__file__).resolve().parents[2] / "static" / "img" / "site"


def vrij(pad, drempel=243):
    im = Image.open(pad).convert("RGB")
    a = np.asarray(im).astype(float)
    licht = (a.min(axis=2) >= 140) & ((a.max(axis=2) - a.min(axis=2)) <= 9)
    lab, n = ndimage.label(licht)
    rand = set(lab[0].tolist()) | set(lab[-1].tolist()) | set(lab[:, 0].tolist()) | set(lab[:, -1].tolist())
    bg = np.isin(lab, [r for r in rand if r])
    # zachte schaduwrand onder de rozen (neutraal grijs) alleen onderin als achtergrond tellen
    los = (a.min(axis=2) >= 150) & ((a.max(axis=2) - a.min(axis=2)) <= 13)
    los[: int(a.shape[0] * .78)] = False
    bg = ndimage.binary_dilation(bg, iterations=60, mask=los) | bg
    voor = ~bg
    voor = ndimage.binary_opening(voor, iterations=2)
    lab2, n2 = ndimage.label(voor)
    if n2:
        groottes = ndimage.sum(voor, lab2, range(1, n2 + 1))
        voor = np.isin(lab2, [i + 1 for i, g in enumerate(groottes) if g > 400])
    gaten = ndimage.binary_fill_holes(voor) & ~voor
    lg, ng = ndimage.label(gaten)
    if ng:
        gg = ndimage.sum(gaten, lg, range(1, ng + 1))
        voor = voor | np.isin(lg, [i + 1 for i, g in enumerate(gg) if g < 600])
    m = Image.fromarray((voor * 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.1))
    alpha = np.asarray(m).astype(float) / 255
    # kleur van de rand vervangen door de dichtstbijzijnde binnenpixel (geen witte rand)
    binnen = ndimage.binary_erosion(voor, iterations=3)
    idx = ndimage.distance_transform_edt(~binnen, return_distances=False, return_indices=True)
    kleur = a[idx[0], idx[1]]
    out = np.where(binnen[..., None], a, kleur)
    rgba = np.dstack([out, alpha * 255]).clip(0, 255).astype("uint8")
    img = Image.fromarray(rgba, "RGBA")
    return img.crop(img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())


def sla_op(img, naam, breed):
    if img.width > breed:
        img = img.resize((breed, round(img.height * breed / img.width)), Image.LANCZOS)
    p = UIT / naam
    img.save(p, "WEBP", quality=88, alpha_quality=92, method=6)
    print(naam, img.size, p.stat().st_size)


if __name__ == "__main__":
    r1, r2 = vrij(sys.argv[1]), vrij(sys.argv[2])
    sla_op(r1, "rozen-groot.webp", 1500)
    sla_op(r2, "rozen-klein.webp", 1100)
