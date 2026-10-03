"""Maakt de papierstructuur voor de VAYLIDE Envelope Collection: een naadloze, grijze tegel met korrel, de wolkige
vervilting van katoenpapier en losse vezels. De kleur komt uit CSS (de tegel ligt er met soft-light overheen), dus één
tegel dient alle envelopstijlen.

Gebruik: python tools/enveloppen/maak_papier.py   (vaste seed, dus reproduceerbaar)
Uitvoer: static/img/envelop/papier.webp (1024 x 1024) en papier.png (bron, voor controle). De tegel wordt ongeveer op
ware grootte getoond (zie envelop-collectie.css en het patroon in collectie.html), zodat de vezels op een telefoon zichtbaar blijven.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
K = SIZE / 512  # maten hieronder zijn bedacht voor 512 px
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "static" / "img" / "envelop"


def periodic_noise(rng: np.random.Generator, sigma: float) -> np.ndarray:
    """Gaussisch vervaagde ruis via FFT: van nature naadloos (periodiek)."""
    noise = rng.standard_normal((SIZE, SIZE))
    fy = np.fft.fftfreq(SIZE)[:, None]
    fx = np.fft.fftfreq(SIZE)[None, :]
    kernel = np.exp(-2 * (math.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    out = np.real(np.fft.ifft2(np.fft.fft2(noise) * kernel))
    return out / (out.std() + 1e-9)


def fibres(seed: int) -> np.ndarray:
    """Korte, licht gebogen vezels; getekend met omloop zodat de tegel naadloos blijft. Waarde rond 0 (licht/donker)."""
    rnd = random.Random(seed)
    scale = 3  # op 3x tekenen en verkleinen: zachte, dunne vezels
    big = SIZE * scale
    light = Image.new("L", (big, big), 0)
    dark = Image.new("L", (big, big), 0)
    dl, dd = ImageDraw.Draw(light), ImageDraw.Draw(dark)
    for i in range(round(1500 * K * K)):
        length = rnd.uniform(10, 46) * scale * K
        angle = rnd.uniform(0, math.pi)
        bend = rnd.uniform(-0.6, 0.6)
        x, y = rnd.uniform(0, big), rnd.uniform(0, big)
        points = []
        steps = 8
        for s in range(steps + 1):
            t = s / steps
            a = angle + bend * (t - 0.5)
            points.append((x + math.cos(a) * length * t, y + math.sin(a) * length * t))
        width = max(1, round(rnd.uniform(0.5, 1.3) * scale * K))
        value = rnd.randint(40, 120)
        target = dl if i % 3 else dd  # meer lichte (witte katoen) dan donkere vezels
        for ox in (-big, 0, big):
            for oy in (-big, 0, big):
                target.line([(px + ox, py + oy) for px, py in points], fill=value, width=width)
    light = light.filter(ImageFilter.GaussianBlur(scale * 0.45)).resize((SIZE, SIZE), Image.LANCZOS)
    dark = dark.filter(ImageFilter.GaussianBlur(scale * 0.45)).resize((SIZE, SIZE), Image.LANCZOS)
    return (np.asarray(light, dtype=np.float64) - 0.75 * np.asarray(dark, dtype=np.float64)) / 255.0


def main() -> None:
    rng = np.random.default_rng(2026)
    grain = periodic_noise(rng, 0.7 * K)      # fijne korrel
    tooth = periodic_noise(rng, 2.2 * K)      # 'tand' van handgeschept papier
    mottle = periodic_noise(rng, 8 * K)       # vlekkerige vervilting van katoen
    clouds = periodic_noise(rng, 22 * K)      # grote wolken
    field = 128 + 3.2 * grain + 3.6 * tooth + 3.4 * mottle + 4.2 * clouds + 28.0 * fibres(7)
    img = Image.fromarray(np.clip(field, 0, 255).astype(np.uint8), "L")
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / "papier.png", optimize=True)
    img.save(OUT / "papier.webp", quality=82, method=6)
    print("klaar:", OUT / "papier.webp", round((OUT / "papier.webp").stat().st_size / 1024), "kB")


if __name__ == "__main__":
    main()
