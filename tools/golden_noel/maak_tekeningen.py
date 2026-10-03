"""Tekent de decoratie van Golden Noël (kerstspecial) als SVG-fragmenten: een boog van wintergroen met warme lichtjes,
een slinger voor de bovenkant van een sectie, hoektakken, een scheiding met ster en een sneeuwkristal.

Wintergroen in gedempte natuurlijke tinten (den, eucalyptus, hulst), fijne gouden takjes en warme lichtjes; de kleuren
staan in designs/golden-noel/v1/style.css (klassen gn-*). Vormen hergebruiken de takjes en bladeren van de envelop
(tools/enveloppen/maak_ornamenten.py). Vaste seeds: reproduceerbaar, maar nergens gespiegeld.

Gebruik: python tools/golden_noel/maak_tekeningen.py
Uitvoer: designs/golden-noel/v1/_boog.svg, _slinger_sectie.svg, _hoek.svg, _scheiding.svg, _kristal.svg
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "enveloppen"))
from maak_ornamenten import (bloom, cubic, dots, fir_branch, fmt, holly_leaf, leaf, sprig, star4,  # noqa: E402
                             tangent)

OUT = ROOT / "designs" / "golden-noel" / "v1"


def euca(rnd, p0, p1, p2, p3, pairs, size):
    """Eucalyptus: een slanke steel met ronde blaadjes in paren, naar de top toe kleiner."""
    stem = f"M{fmt(p0[0])} {fmt(p0[1])}C{fmt(p1[0])} {fmt(p1[1])} {fmt(p2[0])} {fmt(p2[1])} {fmt(p3[0])} {fmt(p3[1])}"
    parts = []
    for i in range(pairs):
        t = 0.08 + 0.88 * i / max(1, pairs - 1)
        x, y = cubic(p0, p1, p2, p3, t)
        tx, ty = tangent(p0, p1, p2, p3, t)
        base = math.atan2(ty, tx)
        length = size * (1.0 - 0.5 * t) * rnd.uniform(0.9, 1.1)
        for side in (-1, 1):
            a = base + side * math.radians(68 + rnd.uniform(-8, 8))
            parts.append(leaf(x, y, length, length * 0.86, a, rnd.uniform(-0.06, 0.06)))
    return stem, " ".join(parts)


def gold_twig(rnd, p0, p1, p2, p3, n=5, size=12):
    """Fijn gouden takje: een lijn met korte zijsprietjes en een besje aan het eind (alleen lijnen en punten)."""
    d = [f"M{fmt(p0[0])} {fmt(p0[1])}C{fmt(p1[0])} {fmt(p1[1])} {fmt(p2[0])} {fmt(p2[1])} {fmt(p3[0])} {fmt(p3[1])}"]
    ends = [p3]
    for i in range(n):
        t = 0.25 + 0.7 * i / max(1, n - 1)
        x, y = cubic(p0, p1, p2, p3, t)
        tx, ty = tangent(p0, p1, p2, p3, t)
        a = math.atan2(ty, tx) + (1 if i % 2 else -1) * math.radians(40 + rnd.uniform(-8, 8))
        L = size * (1 - 0.4 * t)
        e = (x + math.cos(a) * L, y + math.sin(a) * L)
        d.append(f"M{fmt(x)} {fmt(y)}L{fmt(e[0])} {fmt(e[1])}")
        ends.append(e)
    return " ".join(d), dots(ends, 1.9)


class Layer:
    """Verzamelt paden per klasse, zodat elke soort één pad wordt (klein en snel)."""

    def __init__(self):
        self.p = {}

    def add(self, cls, d):
        if d:
            self.p.setdefault(cls, []).append(d if isinstance(d, str) else " ".join(d))

    def svg(self, order):
        return "".join(f'<path class="{c}" d="{" ".join(self.p[c])}"/>' for c in order if c in self.p)


ORDER = ["gn-stem", "gn-euca", "gn-needle-d", "gn-needle-l", "gn-holly", "gn-twig", "gn-twig-dot", "gn-berry", "gn-pearl"]


def along_arc(cx, cy, r, a_deg):
    a = math.radians(a_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def branch_on_arc(rnd, layer, cx, cy, r, a0, a1, kind, scale=1.0):
    """Een tak die de boog volgt van hoek a0 naar a1 (graden; 180 = links, 270 = boven, 360 = rechts)."""
    pts = [along_arc(cx, cy, r + rnd.uniform(-10, 10), a0 + (a1 - a0) * t) for t in (0, .33, .66, 1)]
    if kind == "den":
        s, l, d = fir_branch(rnd, *pts, density=1.0, needle=19 * scale, twigs=3)
        layer.add("gn-stem", s)
        layer.add("gn-needle-l", l)
        layer.add("gn-needle-d", d)
    else:
        s, lv = euca(rnd, *pts, pairs=max(4, int(abs(a1 - a0) / 3.2)), size=17 * scale)
        layer.add("gn-stem", s)
        layer.add("gn-euca", lv)


def boog(rnd):
    """Boog van wintergroen langs de gewelfde bovenkant van de kaart (viewBox 0 0 1000 560; middelpunt 500,500,
    straal 455), met hulst, gouden takjes, parels en warme lichtjes. Lichtjes staan los in de lijst (om te twinkelen)."""
    layer = Layer()
    cx, cy, r = 500, 500, 455
    # Den in twee lagen (achter iets groter), eucalyptus ertussen; overlappend langs de hele boog.
    a = 172
    while a < 368:
        span = rnd.uniform(20, 28)
        direction = 1 if a < 270 else -1  # takken wijzen naar de top toe: van buiten naar het midden
        a0, a1 = (a, a + span) if direction > 0 else (a + span, a)
        branch_on_arc(rnd, layer, cx, cy, r + 6, a0, a1, "den", 1.1)
        if rnd.random() < 0.75:
            m = a + span * rnd.uniform(0.3, 0.7)
            branch_on_arc(rnd, layer, cx, cy, r - 22, m - 9 * direction, m + 9 * direction, "euca", 1.0)
        a += span * 0.62
    # Hulst met bessen (champagnegoud en een paar warm-rode), gouden takjes en parels.
    berries, pearls = [], []
    for ang in (196, 228, 262, 300, 336):
        x, y = along_arc(cx, cy, r - 4, ang)
        for k in range(3):
            layer.add("gn-holly", holly_leaf(x, y, rnd.uniform(26, 32), math.radians(ang + 90 + (k - 1) * 70 + rnd.uniform(-10, 10))))
        berries += [(x + rnd.uniform(-7, 7), y + rnd.uniform(-7, 7)) for _ in range(4)]
    for ang in (185, 212, 245, 283, 318, 352):
        x, y = along_arc(cx, cy, r - 30, ang)
        out = along_arc(cx, cy, r - 78, ang + rnd.uniform(-6, 6))
        p1 = (x + (out[0] - x) * .35, y + (out[1] - y) * .35)
        p2 = (x + (out[0] - x) * .7, y + (out[1] - y) * .7)
        tw, td = gold_twig(rnd, (x, y), p1, p2, out)
        layer.add("gn-twig", tw)
        layer.add("gn-twig-dot", td)
        pearls += [along_arc(cx, cy, r + rnd.uniform(-14, 14), ang + rnd.uniform(4, 9)) for _ in range(2)]
    layer.add("gn-berry", dots(berries, 4.2))
    layer.add("gn-pearl", dots(pearls, 3.6))
    lights = [along_arc(cx, cy, r + rnd.uniform(-26, 24), ang) for ang in [176 + i * 7.4 for i in range(26)]]
    lichtjes = "".join(
        f'<g class="gn-licht" style="--d:{rnd.uniform(0, 6):.1f}s"><circle class="gn-licht__gloed" cx="{fmt(x)}" cy="{fmt(y)}" r="15"/>'
        f'<circle class="gn-licht__kern" cx="{fmt(x)}" cy="{fmt(y)}" r="3"/></g>' for x, y in lights)
    (OUT / "_boog.svg").write_text(layer.svg(ORDER) + "\n", encoding="utf-8")
    (OUT / "_boog_lichtjes.svg").write_text(lichtjes + "\n", encoding="utf-8")


def slinger_sectie(rnd):
    """Kleine slinger voor de bovenkant van een sectie (viewBox 0 0 600 90): den en eucalyptus in een zachte boog,
    met drie lichtjes en een gouden takje in het midden."""
    layer = Layer()
    for (x0, x1), sign in (((20, 300), 1), ((580, 300), -1)):
        mid = (x0 + x1) / 2
        p0, p3 = (x0, 18), (x1 + sign * 10, 44)
        s, l, d = fir_branch(rnd, p0, (mid - sign * 60, 40), (mid + sign * 40, 50), p3, density=1.0, needle=14, twigs=2)
        layer.add("gn-stem", s)
        layer.add("gn-needle-l", l)
        layer.add("gn-needle-d", d)
        es, el = euca(rnd, (x0 + sign * 60, 30), (mid - sign * 10, 58), (mid + sign * 40, 60), (x1 - sign * 30, 52), 6, 13)
        layer.add("gn-stem", es)
        layer.add("gn-euca", el)
    tw, td = gold_twig(rnd, (300, 46), (300, 60), (296, 70), (300, 82), 4, 10)
    layer.add("gn-twig", tw)
    layer.add("gn-twig-dot", td)
    layer.add("gn-berry", dots([(292, 44), (300, 40), (308, 45)], 4))
    lights = [(150, 34), (300, 30), (450, 34)]
    lichtjes = "".join(f'<g class="gn-licht" style="--d:{i * 1.7:.1f}s"><circle class="gn-licht__gloed" cx="{x}" cy="{y}" r="12"/>'
                       f'<circle class="gn-licht__kern" cx="{x}" cy="{y}" r="2.6"/></g>' for i, (x, y) in enumerate(lights))
    (OUT / "_slinger_sectie.svg").write_text(layer.svg(ORDER) + lichtjes + "\n", encoding="utf-8")


def hoek(rnd):
    """Hoektak (viewBox 0 0 240 240, vanuit de linkerbovenhoek): den, eucalyptus, hulst en een gouden takje."""
    layer = Layer()
    for p0, p1, p2, p3, kind in (((0, 6), (60, 20), (120, 40), (200, 46), "den"), ((4, 0), (20, 60), (40, 120), (46, 200), "den"),
                                  ((10, 20), (60, 60), (100, 90), (150, 118), "euca"), ((20, 10), (70, 30), (110, 60), (130, 96), "euca")):
        if kind == "den":
            s, l, d = fir_branch(rnd, p0, p1, p2, p3, density=1.0, needle=15, twigs=2)
            layer.add("gn-stem", s)
            layer.add("gn-needle-l", l)
            layer.add("gn-needle-d", d)
        else:
            s, lv = euca(rnd, p0, p1, p2, p3, 6, 13)
            layer.add("gn-stem", s)
            layer.add("gn-euca", lv)
    for ang in (30, 60):
        layer.add("gn-holly", holly_leaf(34, 34, 28, math.radians(ang)))
    layer.add("gn-berry", dots([(30, 30), (38, 28), (34, 38)], 4.4))
    tw, td = gold_twig(rnd, (30, 40), (80, 110), (120, 150), (170, 170), 6, 14)
    layer.add("gn-twig", tw)
    layer.add("gn-twig-dot", td)
    (OUT / "_hoek.svg").write_text(layer.svg(ORDER) + "\n", encoding="utf-8")


def scheiding(rnd):
    """Scheiding tussen hoofdstukken (viewBox 0 0 600 80): dubbele folielijn, kleine takjes en een ster met gloed."""
    layer = Layer()
    for sign in (1, -1):
        x0 = 300 - sign * 34
        s, lv = euca(rnd, (x0, 40), (x0 - sign * 40, 30), (x0 - sign * 80, 34), (x0 - sign * 118, 26), 5, 10)
        layer.add("gn-stem", s)
        layer.add("gn-euca", lv)
        tw, td = gold_twig(rnd, (x0, 42), (x0 - sign * 40, 52), (x0 - sign * 80, 50), (x0 - sign * 120, 56), 4, 9)
        layer.add("gn-twig", tw)
        layer.add("gn-twig-dot", td)
    lines = "M40 40H150M450 40H560M60 46H150M450 46H540"
    star = star4(300, 40, 13)
    (OUT / "_scheiding.svg").write_text(layer.svg(ORDER) + f'<path class="gn-foil-line" d="{lines}"/>'
                                         f'<circle class="gn-licht__gloed" cx="300" cy="40" r="22"/><path class="gn-star" d="{star}"/>\n',
                                         encoding="utf-8")


def kristal():
    """Sneeuwkristal (viewBox 0 0 40 40): zes armen met zijtakjes."""
    d = []
    for k in range(6):
        a = math.radians(60 * k - 90)
        ex, ey = 20 + 17 * math.cos(a), 20 + 17 * math.sin(a)
        d.append(f"M20 20L{fmt(ex)} {fmt(ey)}")
        for f, L in ((0.5, 5), (0.75, 3.5)):
            bx, by = 20 + 17 * f * math.cos(a), 20 + 17 * f * math.sin(a)
            for side in (-1, 1):
                b = a + side * math.radians(45)
                d.append(f"M{fmt(bx)} {fmt(by)}l{fmt(math.cos(b) * L)} {fmt(math.sin(b) * L)}")
    (OUT / "_kristal.svg").write_text(f'<path d="{" ".join(d)}"/>\n', encoding="utf-8")


def main() -> None:
    boog(random.Random(2512))
    slinger_sectie(random.Random(1224))
    hoek(random.Random(1231))
    scheiding(random.Random(101))
    kristal()
    print("klaar:", ", ".join(p.name for p in sorted(OUT.glob("_*.svg"))))


if __name__ == "__main__":
    main()
