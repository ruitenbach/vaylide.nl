"""Maakt de tekeningen van het kerstdiner-ontwerp Aan tafel: een dennenslinger met lichtjes en een takje hulst.

Gebruik (vanuit de projectmap): python tools/aan_tafel/maak_tekeningen.py
Schrijft designs/aan-tafel/v1/_slinger.html en designs/aan-tafel/v1/_takje.html.

Kleuren komen uit CSS-klassen (at-naald-1, at-naald-2, at-blad, at-bes, at-lampje, at-bal), zodat elke kleurvariant
ze zelf kiest. Geen verlopen met id's: de tekeningen staan soms meer dan eens op één pagina. Vaste startwaarde voor
het toeval, zodat de tekening bij elke run hetzelfde is.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "designs" / "aan-tafel" / "v1"


def slinger() -> str:
    """Een doorhangende dennenslinger over de volle breedte (viewBox 0 0 400 80), met lampjes en een paar kerstballen."""
    rnd = random.Random(12)
    w, top, zak = 400, 10, 34

    def y(x: float) -> float:
        return top + zak * math.sin(math.pi * x / w)

    def helling(x: float) -> float:
        return math.degrees(math.atan(zak * math.pi / w * math.cos(math.pi * x / w)))

    naalden = []
    x = -4.0
    while x < w + 4:
        for _ in range(3):
            hoek = helling(x) + rnd.choice([-1, 1]) * rnd.uniform(28, 74) + rnd.choice([0, 180])
            lengte = rnd.uniform(8, 15)
            dx, dy = math.cos(math.radians(hoek)) * lengte, math.sin(math.radians(hoek)) * lengte
            cls = "at-naald-1" if rnd.random() < .55 else "at-naald-2"
            naalden.append(f'<path class="{cls}" d="M{x:.1f} {y(x):.1f}l{dx:.1f} {dy:.1f}"/>')
        x += 3.2
    lampjes = []
    for i, lx in enumerate(range(14, w, 30)):
        ly = y(lx) + rnd.uniform(-5, 6)
        lampjes.append(f'<circle class="at-lampje at-lampje--{i % 3}" cx="{lx}" cy="{ly:.1f}" r="3.1"/>')
    ballen = []
    for i, bx in enumerate((70, 200, 330)):
        by = y(bx) + 10
        ballen.append(
            f'<path class="at-draad" d="M{bx} {y(bx):.1f}V{by + 1:.1f}"/>'
            f'<rect class="at-dop" x="{bx - 2.6}" y="{by:.1f}" width="5.2" height="3.6" rx="1"/>'
            f'<circle class="at-bal at-bal--{i % 2}" cx="{bx}" cy="{by + 10.5:.1f}" r="8"/>'
            f'<circle class="at-glans" cx="{bx - 2.8}" cy="{by + 7.5:.1f}" r="2.2"/>'
        )
    return (
        '<svg class="at-slinger__svg" viewBox="0 -6 400 86" preserveAspectRatio="xMidYMin slice" aria-hidden="true" focusable="false">'
        + "".join(naalden) + "".join(ballen) + "".join(lampjes) + "</svg>\n"
    )


def hulstblad(cx: float, cy: float, hoek: float, lengte: float = 36, breedte: float = 16) -> str:
    """Een hulstblad langs de x-as: stekels op de rand, met holle bogen ertussen; daarna gedraaid."""
    def rand(teken: int) -> list[tuple[float, float]]:
        pts = []
        for t in (.22, .44, .66, .86):
            h = breedte / 2 * (math.sin(math.pi * min(t, .92)) ** .6) * teken
            pts.append((lengte * t, h * 1.18))
        return pts
    boven, onder = rand(-1), rand(1)

    def langs(punten, start, eind):
        d, vorige = "", start
        for x, y in punten + [eind]:
            mx, my = (vorige[0] + x) / 2, (vorige[1] + y) / 2 * .45
            d += f"Q{mx:.1f} {my:.1f} {x:.1f} {y:.1f}"
            vorige = (x, y)
        return d
    pad = "M0 0" + langs(boven, (0, 0), (lengte, 0)) + langs(list(reversed(onder)), (lengte, 0), (0, 0)) + "Z"
    nerf = f'<path class="at-nerf" d="M2 0Q{lengte * .5:.1f} {breedte * -.05:.1f} {lengte - 4:.1f} 0"/>'
    return f'<g transform="translate({cx} {cy}) rotate({hoek})"><path class="at-blad" d="{pad}"/>{nerf}</g>'


def takje() -> str:
    """Takje hulst met drie bessen en een dennentakje (viewBox 0 0 120 80)."""
    rnd = random.Random(3)
    naalden = []
    for i in range(22):
        t = i / 21
        x, y = 18 + 70 * t, 58 - 26 * t
        for kant in (-1, 1):
            hoek = -36 + kant * rnd.uniform(40, 70)
            l = 9 - 4 * t
            naalden.append(f'<path class="at-naald-{1 + (i + (kant > 0)) % 2}" d="M{x:.1f} {y:.1f}l{math.cos(math.radians(hoek)) * l:.1f} {math.sin(math.radians(hoek)) * l:.1f}"/>')
    tak = '<path class="at-tak" d="M14 60Q52 44 92 30"/>'
    bladeren = hulstblad(58, 44, -150) + hulstblad(60, 44, -40) + hulstblad(58, 46, 70, 28, 11)
    bessen = "".join(
        f'<circle class="at-bes" cx="{x}" cy="{y}" r="5"/><circle class="at-glans" cx="{x - 1.6}" cy="{y - 1.6}" r="1.4"/>'
        for x, y in ((56, 46), (64, 43), (61, 51))
    )
    return (
        '<svg class="at-takje__svg" viewBox="0 0 120 80" aria-hidden="true" focusable="false">'
        + tak + "".join(naalden) + bladeren + bessen + "</svg>\n"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    kop = "{# Gemaakt met tools/aan_tafel/maak_tekeningen.py; niet met de hand aanpassen. #}\n"
    (OUT / "_slinger.html").write_text(kop + slinger(), encoding="utf-8")
    (OUT / "_takje.html").write_text(kop + takje(), encoding="utf-8")
    print("geschreven: _slinger.html, _takje.html")


if __name__ == "__main__":
    main()
