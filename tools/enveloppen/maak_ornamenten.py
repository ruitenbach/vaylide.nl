"""Tekent de vormen van de VAYLIDE Envelope Collection als SVG-paden: een botanisch takje (voor het blinddruk-reliëf) en
de onregelmatige rand van een lakzegel. Met een vaste seed: elk blad en elke uitloper is net anders (geen
spiegelsymmetrie), maar het resultaat is reproduceerbaar.

Gebruik: python tools/enveloppen/maak_ornamenten.py
Uitvoer: templates/partials/envelop/ (bloemen op de flap, zegelrand, -veld en -krans, kaartrand) als SVG-fragmenten,
en static/img/envelop/voering-<stijl>.svg (voeringprints). Kerst: _kerst_evergreen_flap.svg en voering-royal-evergreen.svg
"""
from __future__ import annotations

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "templates" / "partials" / "envelop"


def fmt(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))


def tangent(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(3 * u * u * (b - a) + 6 * u * t * (c - b) + 3 * t * t * (d - c) for a, b, c, d in zip(p0, p1, p2, p3))


def leaf(cx, cy, length, width, angle, curl):
    """Amandelvormig blad vanaf de steel (cx, cy), met een lichte kromming (curl) en een asymmetrische buik."""
    ca, sa = math.cos(angle), math.sin(angle)
    tip = (cx + ca * length, cy + sa * length)
    nx, ny = -sa, ca
    w1, w2 = width * (0.5 + curl), width * (0.5 - curl * 0.6)
    c1 = (cx + ca * length * 0.35 + nx * w1, cy + sa * length * 0.35 + ny * w1)
    c2 = (cx + ca * length * 0.82 + nx * w1 * 0.55, cy + sa * length * 0.82 + ny * w1 * 0.55)
    c3 = (cx + ca * length * 0.80 - nx * w2 * 0.5, cy + sa * length * 0.80 - ny * w2 * 0.5)
    c4 = (cx + ca * length * 0.30 - nx * w2, cy + sa * length * 0.30 - ny * w2)
    return (f"M{fmt(cx)} {fmt(cy)}C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(tip[0])} {fmt(tip[1])}"
            f"C{fmt(c3[0])} {fmt(c3[1])} {fmt(c4[0])} {fmt(c4[1])} {fmt(cx)} {fmt(cy)}Z")


def leaf_vein(cx, cy, length, angle, curl):
    """Middennerf van een blad: een licht gebogen lijn van de steel tot ruim driekwart van het blad."""
    ca, sa = math.cos(angle), math.sin(angle)
    nx, ny = -sa, ca
    bend = length * curl * 0.35
    mid = (cx + ca * length * 0.45 + nx * bend, cy + sa * length * 0.45 + ny * bend)
    end = (cx + ca * length * 0.8, cy + sa * length * 0.8)
    return f"M{fmt(cx + ca * 1.5)} {fmt(cy + sa * 1.5)}Q{fmt(mid[0])} {fmt(mid[1])} {fmt(end[0])} {fmt(end[1])}"


def bloom(rnd, cx, cy, r, petals=5):
    """Klein bloempje: brede, net ongelijke blaadjes rond een hartje. Geeft (blaadjes, hartje)."""
    start = rnd.uniform(0, math.tau)
    parts = []
    for i in range(petals):
        a = start + math.tau * i / petals + rnd.uniform(-0.12, 0.12)
        length = r * rnd.uniform(0.88, 1.08)
        parts.append(leaf(cx, cy, length, length * rnd.uniform(0.86, 0.98), a, rnd.uniform(-0.08, 0.08)))
    hr = r * 0.26
    return " ".join(parts), dots([(cx, cy)], hr)


def dots(points, r):
    """Cirkeltjes als één pad (bessen, parels, gaatjes)."""
    return " ".join(f"M{fmt(x - r)} {fmt(y)}a{fmt(r)} {fmt(r)} 0 1 0 {fmt(2 * r)} 0a{fmt(r)} {fmt(r)} 0 1 0 {fmt(-2 * r)} 0Z"
                    for x, y in points)


def sprig(rnd, p0, p1, p2, p3, leaves, size, spread, veins=None, tip=True, wide=(0.34, 0.42)):
    stem = f"M{fmt(p0[0])} {fmt(p0[1])}C{fmt(p1[0])} {fmt(p1[1])} {fmt(p2[0])} {fmt(p2[1])} {fmt(p3[0])} {fmt(p3[1])}"
    parts = []
    for i in range(leaves):
        t = 0.08 + 0.88 * (i / max(1, leaves - 1)) + rnd.uniform(-0.025, 0.025)
        x, y = cubic(p0, p1, p2, p3, min(t, 0.99))
        tx, ty = tangent(p0, p1, p2, p3, min(t, 0.99))
        base = math.atan2(ty, tx)
        side = 1 if i % 2 else -1
        angle = base + side * math.radians(spread + rnd.uniform(-9, 9))
        length = size * (1.05 - 0.55 * t) * rnd.uniform(0.86, 1.12)
        curl = rnd.uniform(-0.12, 0.12)
        parts.append(leaf(x, y, length, length * rnd.uniform(*wide), angle, curl))
        if veins is not None:
            veins.append(leaf_vein(x, y, length, angle, curl))
    if tip:
        tip_angle = math.atan2(*reversed(tangent(p0, p1, p2, p3, 0.99)))
        parts.append(leaf(*p3, size * 0.42, size * 0.15, tip_angle + rnd.uniform(-0.15, 0.15), 0.05))
    return stem, " ".join(parts)


def svg_sprig(name, viewbox, stems, leaves, veins=(), hearts=(), berries=""):
    body = ("".join(f'<path class="vx-stem" d="{s}"/>' for s in stems) + "".join(f'<path class="vx-leaf" d="{l}"/>' for l in leaves)
            + (f'<path class="vx-berry" d="{berries}"/>' if berries else "")
            + "".join(f'<path class="vx-vein" d="{v}"/>' for v in veins) + "".join(f'<path class="vx-heart" d="{h}"/>' for h in hearts))
    (OUT / name).write_text(f'<svg class="vx-orn" viewBox="{viewbox}" aria-hidden="true" focusable="false">{body}</svg>\n', encoding="utf-8")


def seal_edge(rnd, r=50.0, points=72, amp=1.0, lobe_count=3, cx=60.0, cy=60.0):
    """Rand van gesmolten was: lage harmonischen (lichte ovaliteit), kleine golfjes en uitgeperste lobben.
    Met amp < 1 en zonder lobben: het ingedrukte veld van de stempel (bijna rond, nooit een perfecte cirkel)."""
    harmonics = [(k, amp * rnd.uniform(0.004, 0.018) / (1 + k * 0.15), rnd.uniform(0, math.tau)) for k in range(2, 9)]
    lobes = [(rnd.uniform(0, math.tau), rnd.uniform(0.05, 0.09), rnd.uniform(0.18, 0.32)) for _ in range(lobe_count)]
    pts = []
    for i in range(points):
        th = math.tau * i / points
        rr = 1 + sum(a * math.cos(k * th + ph) for k, a, ph in harmonics)
        for center, height, width in lobes:
            d = math.atan2(math.sin(th - center), math.cos(th - center))
            rr += height * math.exp(-(d / width) ** 2)
        rr += amp * rnd.uniform(-0.004, 0.004)
        pts.append((cx + r * rr * math.cos(th), cy + r * rr * math.sin(th)))
    # Catmull-Rom naar Bézier: een vloeiende, niet-geometrische rand
    d = f"M{fmt(pts[0][0])} {fmt(pts[0][1])}"
    n = len(pts)
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{fmt(c1[0])} {fmt(c1[1])} {fmt(c2[0])} {fmt(c2[1])} {fmt(p2[0])} {fmt(p2[1])}"
    return d + "Z"


def fern(rnd, p0, p1, p2, p3, pairs, size, veins=None):
    """Varenblad: een gebogen nerf met smalle blaadjes in paren, naar de top toe kleiner."""
    stem = f"M{fmt(p0[0])} {fmt(p0[1])}C{fmt(p1[0])} {fmt(p1[1])} {fmt(p2[0])} {fmt(p2[1])} {fmt(p3[0])} {fmt(p3[1])}"
    parts = []
    for i in range(pairs):
        t = 0.06 + 0.9 * i / max(1, pairs - 1)
        x, y = cubic(p0, p1, p2, p3, t)
        tx, ty = tangent(p0, p1, p2, p3, t)
        base = math.atan2(ty, tx)
        length = size * (1.0 - 0.62 * t) * rnd.uniform(0.9, 1.08)
        for side in (-1, 1):
            a = base + side * math.radians(58 + rnd.uniform(-7, 7))
            parts.append(leaf(x, y, length, length * 0.3, a, rnd.uniform(-0.06, 0.06)))
    return stem, " ".join(parts)


def spike(rnd, p0, p1, p2, p3, grains, size):
    """Grashalm of aar: korte, smalle korreltjes dicht langs een slanke stengel."""
    stem = f"M{fmt(p0[0])} {fmt(p0[1])}C{fmt(p1[0])} {fmt(p1[1])} {fmt(p2[0])} {fmt(p2[1])} {fmt(p3[0])} {fmt(p3[1])}"
    parts = []
    for i in range(grains):
        t = 0.45 + 0.55 * i / max(1, grains - 1)
        x, y = cubic(p0, p1, p2, p3, min(t, 0.99))
        tx, ty = tangent(p0, p1, p2, p3, min(t, 0.99))
        a = math.atan2(ty, tx) + (1 if i % 2 else -1) * math.radians(22 + rnd.uniform(-5, 5))
        parts.append(leaf(x, y, size * rnd.uniform(0.85, 1.1), size * 0.42, a, 0))
    return stem, " ".join(parts)


def anemone(rnd, cx, cy, r, petals=7):
    """Grote open bloem: brede, golvende blaadjes met nerven, een donker hart met een krans van meeldraden."""
    start = rnd.uniform(0, math.tau)
    parts, veins = [], []
    for i in range(petals):
        a = start + math.tau * i / petals + rnd.uniform(-0.1, 0.1)
        length = r * rnd.uniform(0.9, 1.06)
        parts.append(leaf(cx, cy, length, length * rnd.uniform(0.92, 1.02), a, rnd.uniform(-0.1, 0.1)))
        for off in (-0.16, 0, 0.16):  # drie fijne nerven per blad
            aa = a + off
            veins.append(f"M{fmt(cx + math.cos(aa) * r * 0.36)} {fmt(cy + math.sin(aa) * r * 0.36)}"
                         f"L{fmt(cx + math.cos(aa) * r * (0.78 - abs(off)))} {fmt(cy + math.sin(aa) * r * (0.78 - abs(off)))}")
    heart = dots([(cx, cy)], r * 0.22)
    stamens = dots([(cx + r * 0.32 * math.cos(math.tau * k / 16), cy + r * 0.32 * math.sin(math.tau * k / 16)) for k in range(16)], r * 0.035)
    return " ".join(parts), veins, heart, stamens


def flap_florals(rnd):
    """Botanische blinddruk over de hele flap (viewBox 0 0 1000 476, punt onderaan in het midden): een vol boeket dat
    vanuit de punt naar de bovenhoeken waaiert, met een grote bloem rechts, een middelgrote links, varens, aren,
    bloempjes en bessen. Eigen compositie; links en rechts bewust verschillend."""
    stems, leaves, veins, hearts, berries = [], [], [], [], []

    def add(sl):
        stems.append(sl[0])
        leaves.append(sl[1])

    def curve(b, e, bend):
        dx, dy = e[0] - b[0], e[1] - b[1]
        length = math.hypot(dx, dy)
        nx, ny = -dy / length, dx / length
        p1 = (b[0] + dx * 0.32 + nx * bend, b[1] + dy * 0.32 + ny * bend)
        p2 = (b[0] + dx * 0.7 + nx * bend * 0.7, b[1] + dy * 0.7 + ny * bend * 0.7)
        return b, p1, p2, e

    w = (0.42, 0.54)
    # (eind, soort, aantal, maat, buiging); buiging > 0 buigt naar buiten. Links en rechts verschillend.
    left = [((116, 66), "sprig", 26, 40, -110), ((246, 40), "sprig", 18, 30, -70), ((350, 96), "fern", 13, 30, 40),
            ((176, 176), "sprig", 16, 34, -90), ((296, 206), "spike", 11, 12, -40), ((412, 128), "spike", 10, 10, 30),
            ((210, 110), "fern", 11, 22, -80), ((372, 250), "sprig", 8, 24, -30), ((316, 36), "sprig", 15, 28, -50),
            ((92, 28), "fern", 14, 24, -100), ((462, 66), "spike", 12, 12, 12)]
    right = [((886, 78), "sprig", 24, 38, 110), ((766, 48), "fern", 15, 28, 70), ((636, 92), "spike", 11, 11, -36),
             ((832, 196), "sprig", 15, 32, 90), ((578, 168), "sprig", 10, 24, -30), ((910, 140), "fern", 10, 22, 100),
             ((690, 296), "sprig", 8, 24, 34), ((690, 34), "sprig", 15, 28, 46), ((928, 34), "fern", 14, 24, 100),
             ((546, 58), "sprig", 12, 24, -12)]
    for side, items in ((-1, left), (1, right)):
        for end, kind, n, size, bend in items:
            b = (500 + side * rnd.uniform(8, 22), rnd.uniform(404, 424))
            pts = curve(b, end, bend)
            size *= 1.25  # op een telefoon moet een blad een blad blijven, geen streepje
            if kind == "sprig":
                add(sprig(rnd, *pts, round(n * 1.2), size, 44, veins, tip=True, wide=w))
            elif kind == "fern":
                add(fern(rnd, *pts, round(n * 1.15), size))
            else:
                add(spike(rnd, *pts, n, size))
    for cx, cy, r, n in ((706, 198, 60, 7), (282, 150, 36, 6)):
        petals, pveins, heart, stamens = anemone(rnd, cx, cy, r, n)
        leaves.append(petals)
        veins += pveins
        hearts.append(heart)
        berries.append(stamens)
    for cx, cy, r in ((246, 40, 13), (116, 66, 12), (412, 128, 9), (578, 168, 10), (886, 78, 13), (636, 92, 9),
                      (440, 300, 9), (566, 318, 8), (176, 176, 10), (832, 196, 11)):
        p, h = bloom(rnd, cx, cy, r)
        leaves.append(p)
        hearts.append(h)
    berries.append(dots([(262, 228), (272, 220), (270, 234), (796, 262), (806, 254), (804, 268), (466, 220), (474, 212),
                         (522, 240), (530, 232), (150, 240), (158, 232)], 3.2))
    svg_sprig("_flap_bloei.svg", "0 0 1000 476", stems, leaves, veins, hearts, " ".join(berries))


def flap_florals_signature(rnd):
    """Blinddruk-boeket van Signature Ivory (zelfde compositie als flap_florals, dezelfde seed), maar met hoogteverschillen: stelen laag,
    varens en aren iets hoger, takjes middenhoog en de bloemen het hoogst, met een tweede, hogere krans blaadjes in de grote bloemen.
    In het hoogtebeeld (wit = hoog) geeft dat laagjes in het papier in plaats van één plat vlak: het licht valt per laag anders.
    Klassen: vx-lo (steel), vx-h3 (varen, aar), vx-h2 (takje, buitenste bloemblad), vx-h1 (binnenste bloemblad, bloempje)."""
    stems, groups, veins, hearts, berries = [], [], [], [], []

    def curve(b, e, bend):
        dx, dy = e[0] - b[0], e[1] - b[1]
        length = math.hypot(dx, dy)
        nx, ny = -dy / length, dx / length
        p1 = (b[0] + dx * 0.32 + nx * bend, b[1] + dy * 0.32 + ny * bend)
        p2 = (b[0] + dx * 0.7 + nx * bend * 0.7, b[1] + dy * 0.7 + ny * bend * 0.7)
        return b, p1, p2, e

    w = (0.42, 0.54)
    left = [((116, 66), "sprig", 26, 40, -110), ((246, 40), "sprig", 18, 30, -70), ((350, 96), "fern", 13, 30, 40),
            ((176, 176), "sprig", 16, 34, -90), ((296, 206), "spike", 11, 12, -40), ((412, 128), "spike", 10, 10, 30),
            ((210, 110), "fern", 11, 22, -80), ((372, 250), "sprig", 8, 24, -30), ((316, 36), "sprig", 15, 28, -50),
            ((92, 28), "fern", 14, 24, -100), ((462, 66), "spike", 12, 12, 12)]
    right = [((886, 78), "sprig", 24, 38, 110), ((766, 48), "fern", 15, 28, 70), ((636, 92), "spike", 11, 11, -36),
             ((832, 196), "sprig", 15, 32, 90), ((578, 168), "sprig", 10, 24, -30), ((910, 140), "fern", 10, 22, 100),
             ((690, 296), "sprig", 8, 24, 34), ((690, 34), "sprig", 15, 28, 46), ((928, 34), "fern", 14, 24, 100),
             ((546, 58), "sprig", 12, 24, -12)]
    for side, items in ((-1, left), (1, right)):
        for end, kind, n, size, bend in items:
            b = (500 + side * rnd.uniform(8, 22), rnd.uniform(404, 424))
            pts = curve(b, end, bend)
            size *= 1.25
            if kind == "sprig":
                st, lv = sprig(rnd, *pts, round(n * 1.2), size, 44, veins, tip=True, wide=w)
                groups.append(("vx-leaf vx-h2", lv))
            elif kind == "fern":
                st, lv = fern(rnd, *pts, round(n * 1.15), size)
                groups.append(("vx-leaf vx-h3", lv))
            else:
                st, lv = spike(rnd, *pts, n, size)
                groups.append(("vx-leaf vx-h3", lv))
            stems.append(st)
    extra = random.Random(4417)   # eigen reeks: de compositie hierboven blijft precies zoals ze was
    for cx, cy, r, n in ((706, 198, 60, 7), (282, 150, 36, 6)):
        petals, pveins, heart, stamens = anemone(rnd, cx, cy, r, n)
        groups.append(("vx-leaf vx-h2", petals))
        veins += pveins
        hearts.append(heart)
        berries.append(stamens)
        # tweede, hogere krans: kortere, bredere blaadjes tussen de buitenste door, en een zacht verdiept hart (de vorm van het hart komt boven)
        start = extra.uniform(0, math.tau)
        inner = [leaf(cx, cy, r * extra.uniform(0.58, 0.68), r * extra.uniform(0.5, 0.58), start + math.tau * (i + 0.5) / n + extra.uniform(-0.08, 0.08), extra.uniform(-0.08, 0.08))
                 for i in range(n)]
        groups.append(("vx-leaf vx-h1", " ".join(inner)))
    for cx, cy, r in ((246, 40, 13), (116, 66, 12), (412, 128, 9), (578, 168, 10), (886, 78, 13), (636, 92, 9),
                      (440, 300, 9), (566, 318, 8), (176, 176, 10), (832, 196, 11)):
        pt, h = bloom(rnd, cx, cy, r)
        groups.append(("vx-leaf vx-h1", pt))
        hearts.append(h)
    berries.append(dots([(262, 228), (272, 220), (270, 234), (796, 262), (806, 254), (804, 268), (466, 220), (474, 212),
                         (522, 240), (530, 232), (150, 240), (158, 232)], 3.2))
    body = ("".join(f'<path class="vx-stem vx-lo" d="{st}"/>' for st in stems) + "".join(f'<path class="{c}" d="{d}"/>' for c, d in groups)
            + f'<path class="vx-berry" d="{" ".join(berries)}"/>' + "".join(f'<path class="vx-vein" d="{v}"/>' for v in veins)
            + "".join(f'<path class="vx-heart" d="{h}"/>' for h in hearts))
    (OUT / "_flap_signature.svg").write_text(f'<svg class="vx-orn" viewBox="0 0 1000 476" aria-hidden="true" focusable="false">{body}</svg>\n', encoding="utf-8")


def liner_meadow(rnd, size=240):
    """Voering: fijne veldbloemenprint (halmen, varentjes, bloempjes) op een naadloze tegel, in een gedempte tint."""
    items = []
    placed = []
    for _ in range(400):
        if len(placed) >= 16:
            break
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        if any(min(abs(x - px), size - abs(x - px)) ** 2 + min(abs(y - py), size - abs(y - py)) ** 2 < 54 ** 2 for px, py in placed):
            continue
        placed.append((x, y))
        kind = len(placed) % 3
        angle = rnd.uniform(-35, 35) - 90  # vooral omhoog, zoals een veldje
        if kind == 0:
            s, l = sprig(rnd, (0, 0), (20, -6), (44, -10), (70, -8), 7, 15, 44, wide=(0.36, 0.44))
            p, h = bloom(rnd, 72, -8, 7)
            l += " " + p
        elif kind == 1:
            s, l = fern(rnd, (0, 0), (22, -4), (46, -6), (72, -2), 9, 13)
        else:
            s, l = spike(rnd, (0, 0), (24, -3), (50, -4), (76, 0), 9, 7)
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                cx, cy = x + ox, y + oy
                if -90 < cx < size + 90 and -90 < cy < size + 90:
                    items.append(f'<g transform="translate({fmt(cx)} {fmt(cy)}) rotate({fmt(angle)}) scale(1.15) translate(-36 0)">'
                                 f'<path class="s" d="{s}"/><path class="l" d="{l}"/></g>')
    colours = {"signature": ("#ECE5D7", "#B3A27C"), "sage": ("#E4E7DC", "#8E9C80"), "noisette": ("#3D2A20", "#B08F5E"), "rose-blush": ("#F2DFD5", "#C4927E"), "midnight-emeraude": ("#14382C", "#CDB173")}
    out = ROOT / "static" / "img" / "envelop"
    for name, (bg, ink) in colours.items():
        style = f".s{{fill:none;stroke:{ink};stroke-width:1.3;stroke-linecap:round}}.l{{fill:{ink}}}"
        (out / f"voering-{name}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<style>{style}</style><rect width="{size}" height="{size}" fill="{bg}"/>'
            f'<g opacity=".62">{"".join(items)}</g></svg>\n', encoding="utf-8")


def seal_wreath(rnd, cx=60.5, cy=59.5, r=24.5):
    """Krans in het zegel: twee boogjes blad die onderaan samenkomen (links en rechts net verschillend)."""
    stems, leaves = [], []
    for side, a_end in ((1, 238), (-1, -58)):
        a0 = math.radians(90 + side * 16)
        a1 = math.radians(a_end + rnd.uniform(-6, 6))
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        stems.append(f"M{fmt(p0[0])} {fmt(p0[1])}A{fmt(r)} {fmt(r)} 0 0 {1 if side > 0 else 0} {fmt(p1[0])} {fmt(p1[1])}")
        n = 8
        for i in range(n):
            t = (i + 0.5) / n
            a = a0 + (a1 - a0) * t
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            tang = a + side * math.pi / 2
            out = 1 if i % 2 else -1
            length = rnd.uniform(6.2, 7.6) * (1.05 - 0.25 * t)
            angle = tang - side * out * math.radians(38 + rnd.uniform(-6, 6))
            leaves.append(leaf(x, y, length, length * 0.44, angle, rnd.uniform(-0.1, 0.1)))
        leaves.append(leaf(p1[0], p1[1], 5.2, 2.2, a1 + side * math.pi / 2 + rnd.uniform(-0.2, 0.2), 0.05))
    berries = dots([(cx - 2.2, cy + r + 1.2), (cx + 2.4, cy + r + 0.6), (cx + 0.2, cy + r + 3.6)], 1.45)
    body = ("".join(f'<path class="vx-stem" d="{s}"/>' for s in stems) + f'<path class="vx-leaf" d="{" ".join(leaves)}"/>'
            + f'<path class="vx-berry" d="{berries}"/>')
    (OUT / "_zegel_krans.svg").write_text(body + "\n", encoding="utf-8")


def fir_branch(rnd, p0, p1, p2, p3, density=1.0, needle=13.0, twigs=3):
    """Dennentak: een gebogen steel met korte naalden aan twee kanten (naar de top toe korter) en een paar zijtakjes.
    Geeft (stelen, naalden licht, naalden donker) als paden voor lijnen."""
    stems = [f"M{fmt(p0[0])} {fmt(p0[1])}C{fmt(p1[0])} {fmt(p1[1])} {fmt(p2[0])} {fmt(p2[1])} {fmt(p3[0])} {fmt(p3[1])}"]
    light, dark = [], []

    def needles(q0, q1, q2, q3, n, size):
        for i in range(n):
            t = 0.04 + 0.95 * i / max(1, n - 1)
            x, y = cubic(q0, q1, q2, q3, min(t, 0.99))
            tx, ty = tangent(q0, q1, q2, q3, min(t, 0.99))
            base = math.atan2(ty, tx)
            length = size * (1.05 - 0.45 * t) * rnd.uniform(0.85, 1.12)
            for side in (-1, 1):
                a = base + side * math.radians(48 + rnd.uniform(-9, 9))
                seg = f"M{fmt(x)} {fmt(y)}l{fmt(math.cos(a) * length)} {fmt(math.sin(a) * length)}"
                (light if rnd.random() < 0.45 else dark).append(seg)

    length = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
    needles(p0, p1, p2, p3, max(8, int(length / 4.2 * density)), needle)
    for k in range(twigs):
        t = 0.18 + 0.62 * (k + rnd.uniform(0, 0.6)) / twigs
        x, y = cubic(p0, p1, p2, p3, t)
        tx, ty = tangent(p0, p1, p2, p3, t)
        base = math.atan2(ty, tx) + (1 if k % 2 else -1) * math.radians(30 + rnd.uniform(-7, 7))
        tl = min(length * rnd.uniform(0.1, 0.16), 70)
        q3 = (x + math.cos(base) * tl, y + math.sin(base) * tl)
        q1 = (x + math.cos(base) * tl * 0.35, y + math.sin(base) * tl * 0.35)
        q2 = (x + math.cos(base) * tl * 0.7, y + math.sin(base) * tl * 0.7)
        stems.append(f"M{fmt(x)} {fmt(y)}C{fmt(q1[0])} {fmt(q1[1])} {fmt(q2[0])} {fmt(q2[1])} {fmt(q3[0])} {fmt(q3[1])}")
        needles((x, y), q1, q2, q3, max(5, int(tl / 4.2 * density)), needle * 0.8)
    return stems, light, dark


def holly_leaf(cx, cy, length, angle, spikes=4):
    """Hulstblad: een langwerpig blad met puntige uitsteeksels aan beide kanten (licht onregelmatig door de hoek)."""
    ca, sa = math.cos(angle), math.sin(angle)
    nx, ny = -sa, ca
    width = length * 0.36
    pts = []
    for side in (1, -1):
        rng = range(spikes * 2 + 1) if side == 1 else range(spikes * 2, -1, -1)
        for k in rng:
            t = k / (spikes * 2)
            w = width * math.sin(math.pi * t) ** 0.8
            w *= 1.18 if k % 2 else 0.78  # puntjes en inkepingen
            px = cx + ca * length * t + nx * w * side
            py = cy + sa * length * t + ny * w * side
            pts.append((px, py))
    return "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + "Z"


def evergreen_flap(rnd):
    """Royal Evergreen: twee dennenslingers langs de flapranden naar de punt, met hulst, rode bessen en een paar
    kerstballen (rood en champagnegoud) vlak bij het zegel. viewBox 0 0 1000 476. Eigen compositie, niet gespiegeld."""
    stems, light, dark, holly, berries, red, gold, shine, shade = [], [], [], [], [], [], [], [], []
    for (a, b), bend in ((((74, 34), (452, 396)), -26), (((926, 34), (548, 396)), 24)):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        for off, scale in ((0, 1.0), (-14, 0.8), (16, 0.75)):
            p0 = (a[0] + nx * off + rnd.uniform(-6, 6), a[1] + ny * off)
            p3 = (b[0] + nx * off * 0.3, b[1] + ny * off * 0.3)
            p1 = (p0[0] + dx * 0.33 + nx * bend, p0[1] + dy * 0.33 + ny * bend)
            p2 = (p0[0] + dx * 0.66 + nx * bend * 0.6, p0[1] + dy * 0.66 + ny * bend * 0.6)
            s, l, d = fir_branch(rnd, p0, p1, p2, p3, density=1.05 * scale, needle=17 * scale, twigs=8)
            stems += s
            light += l
            dark += d
        # hulst en bessen langs de slinger
        for t in (0.2, 0.4, 0.6, 0.8):
            x, y = a[0] + dx * t, a[1] + dy * t
            for k in range(2):
                ang = math.atan2(dy, dx) + (1 if k else -1) * math.radians(70 + rnd.uniform(-12, 12))
                holly.append(holly_leaf(x, y, rnd.uniform(22, 27), ang))
            berries += [(x + rnd.uniform(-8, 8), y + rnd.uniform(-8, 8)) for _ in range(4)]
    # kerstballen: rood en champagnegoud, met een dopje, schaduwzijde en één lichtpuntje
    for cx, cy, r, kind in ((404, 364, 15, "r"), (604, 380, 12.5, "g"), (650, 346, 14, "r"), (742, 178, 11.5, "r"), (262, 208, 10.5, "g")):
        (red if kind == "r" else gold).append(dots([(cx, cy)], r))
        shade.append(f"M{fmt(cx - r * 0.2)} {fmt(cy + r * 0.98)}a{fmt(r)} {fmt(r)} 0 0 0 {fmt(r * 1.18)} {fmt(-r * 1.02)}"
                     f"a{fmt(r * 0.86)} {fmt(r * 0.86)} 0 0 1 {fmt(-r * 1.18)} {fmt(r * 1.02)}Z")
        shine.append(dots([(cx - r * 0.36, cy - r * 0.38)], r * 0.17))
        gold.append(f"M{fmt(cx - r * 0.22)} {fmt(cy - r * 1.18)}h{fmt(r * 0.44)}v{fmt(r * 0.28)}h{fmt(-r * 0.44)}Z")  # dopje
    body = ("".join(f'<path class="vx-stem" d="{s}"/>' for s in stems)
            + f'<path class="vx-needle vx-needle--dark" d="{" ".join(dark)}"/>'
            + f'<path class="vx-needle vx-needle--light" d="{" ".join(light)}"/>'
            + f'<path class="vx-holly" d="{" ".join(holly)}"/>'
            + f'<path class="vx-berry vx-berry--red" d="{dots(berries, 3.3)}"/>'
            + f'<path class="vx-bauble vx-bauble--red" d="{" ".join(red)}"/>'
            + f'<path class="vx-bauble vx-bauble--gold" d="{" ".join(gold)}"/>'
            + f'<path class="vx-bauble-shade" d="{" ".join(shade)}"/>'
            + f'<path class="vx-bauble-shine" d="{" ".join(shine)}"/>')
    (OUT / "_kerst_evergreen_flap.svg").write_text(
        f'<svg class="vx-orn" viewBox="0 0 1000 476" aria-hidden="true" focusable="false">{body}</svg>\n', encoding="utf-8")


def evergreen_liner(rnd, size=260, name="royal-evergreen", bg="#EEE6D6", twig="#6F5B40", dark="#4E6B4A", light="#86A07A",
                    star="#C8A35A", berry="#9A3A35"):
    """Voering met dennentakjes (naadloos): Royal Evergreen in groen op ivoor, Golden Noël in goud op champagne."""
    items, placed = [], []
    for _ in range(500):
        if len(placed) >= 11:
            break
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        if any(min(abs(x - px), size - abs(x - px)) ** 2 + min(abs(y - py), size - abs(y - py)) ** 2 < 64 ** 2 for px, py in placed):
            continue
        placed.append((x, y))
        s, l, d = fir_branch(rnd, (0, 0), (24, -5), (50, -6), (78, -2), density=1.0, needle=10, twigs=2)
        angle = rnd.uniform(-50, 50) - 90
        extra = (f'<path class="g" d="{star4(84, -2, 4.5)}"/>' if len(placed) % 3 == 0
                 else f'<path class="b" d="{dots([(80, 2), (85, -3), (86, 4)], 1.8)}"/>' if len(placed) % 3 == 1 else "")
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                cx, cy = x + ox, y + oy
                if -90 < cx < size + 90 and -90 < cy < size + 90:
                    items.append(f'<g transform="translate({fmt(cx)} {fmt(cy)}) rotate({fmt(angle)}) translate(-39 0)">'
                                 f'<path class="s" d="{" ".join(s)}"/><path class="d" d="{" ".join(d)}"/><path class="l" d="{" ".join(l)}"/>{extra}</g>')
    style = (f".g{{fill:{star}}}.b{{fill:{berry}}}.s{{fill:none;stroke:{twig};stroke-width:1.2;stroke-linecap:round}}"
             f".d{{fill:none;stroke:{dark};stroke-width:1.5;stroke-linecap:round}}.l{{fill:none;stroke:{light};stroke-width:1.4;stroke-linecap:round}}")
    (ROOT / "static" / "img" / "envelop" / f"voering-{name}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<style>{style}</style><rect width="{size}" height="{size}" fill="{bg}"/>'
        f'<g opacity=".78">{"".join(items)}</g></svg>\n', encoding="utf-8")


def star4(cx, cy, r):
    """Klein vierpuntig sterretje (goudaccent)."""
    q = r * 0.28
    return (f"M{fmt(cx)} {fmt(cy - r)}L{fmt(cx + q)} {fmt(cy - q)}L{fmt(cx + r)} {fmt(cy)}L{fmt(cx + q)} {fmt(cy + q)}"
            f"L{fmt(cx)} {fmt(cy + r)}L{fmt(cx - q)} {fmt(cy + q)}L{fmt(cx - r)} {fmt(cy)}L{fmt(cx - q)} {fmt(cy - q)}Z")


def binnen_signature(rnd):
    """Binnenkant flap Signature Ivory: een klein champagne botanisch kroontje onder de punt (twee takjes die uit
    een bloempje opbuigen). viewBox 0 0 200 120, bedoeld voor goudfolie met licht reliëf."""
    veins, stems, leaves = [], [], []
    for side in (-1, 1):
        p0 = (100 + side * 6, 92)
        p3 = (100 + side * 88, 36 + rnd.uniform(-4, 4))
        p1 = (100 + side * 32, 96)
        p2 = (100 + side * 66, 70)
        s, l = sprig(rnd, p0, p1, p2, p3, 9, 17, 46, veins, wide=(0.4, 0.5))
        stems.append(s)
        leaves.append(l)
    p, h = bloom(rnd, 100, 90, 11)
    leaves.append(p)
    svg_sprig("_binnen_signature.svg", "0 0 200 120", stems, leaves, veins, [h], dots([(70, 64), (132, 62)], 2.4))


def binnen_evergreen(rnd):
    """Binnenkant flap Royal Evergreen: een kransje van dennennaalden met rode bessen en een goud sterretje bovenin.
    viewBox 0 0 160 160."""
    stems, light, dark = [], [], []
    cx, cy, r = 80, 84, 46
    for k in range(6):
        a0 = math.radians(-90 + 60 * k + rnd.uniform(-5, 5))
        a1 = a0 + math.radians(70)
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        p3 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        am = (a0 + a1) / 2
        p1 = (cx + r * 1.08 * math.cos(a0 + (a1 - a0) * 0.33), cy + r * 1.08 * math.sin(a0 + (a1 - a0) * 0.33))
        p2 = (cx + r * 1.08 * math.cos(a0 + (a1 - a0) * 0.66), cy + r * 1.08 * math.sin(a0 + (a1 - a0) * 0.66))
        s, l, d = fir_branch(rnd, p0, p1, p2, p3, density=1.1, needle=9, twigs=1)
        stems += s
        light += l
        dark += d
    berries = []
    for a in (150, 30, 270):
        bx, by = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        berries += [(bx + rnd.uniform(-5, 5), by + rnd.uniform(-5, 5)) for _ in range(3)]
    body = ("".join(f'<path class="vx-stem" d="{s}"/>' for s in stems)
            + f'<path class="vx-needle vx-needle--dark" d="{" ".join(dark)}"/>'
            + f'<path class="vx-needle vx-needle--light" d="{" ".join(light)}"/>'
            + f'<path class="vx-berry vx-berry--red" d="{dots(berries, 2.8)}"/>'
            + f'<path class="vx-star" d="{star4(cx, cy - r - 2, 9)}"/>')
    (OUT / "_binnen_evergreen.svg").write_text(
        f'<svg class="vx-orn" viewBox="0 0 160 160" aria-hidden="true" focusable="false">{body}</svg>\n', encoding="utf-8")


def flap_rose(rnd):
    """Rose Blush: drie slanke takken met smalle wilgenblaadjes in blinddruk, waaierend vanaf het midden van de flap
    naar de bovenhoeken (viewBox 0 0 1000 476). Rustiger en luchtiger dan Signature. Eigen compositie."""
    stems, leaves, veins = [], [], []
    w = (0.36, 0.44)
    for p0, p1, p2, p3, n, size in (
        ((372, 330), (330, 230), (230, 120), (118, 62), 16, 48),
        ((452, 306), (416, 220), (430, 130), (476, 58), 12, 40),
        ((560, 296), (630, 196), (760, 116), (880, 84), 15, 48),
        ((300, 248), (270, 210), (236, 190), (196, 186), 6, 26),
        ((700, 186), (730, 150), (770, 128), (812, 126), 6, 26),
    ):
        s, l = sprig(rnd, p0, p1, p2, p3, n, size, 34, veins, wide=w)
        stems.append(s)
        leaves.append(l)
    svg_sprig("_flap_rose.svg", "0 0 1000 476", stems, leaves, veins)


def seal_rose():
    """Zegelmotief roos (viewBox van het zegel, 0 0 120): een roos met spiraalvormige bloemblaadjes, een steel en twee
    blaadjes. Hoogtekaart: lichtgrijs = verhoogd, donkere lijnen = groeven tussen de blaadjes."""
    cx, cy, r = 60.5, 48.5, 12.5
    outline = dots([(cx + r * 0.62 * math.cos(math.tau * k / 6 + 0.3), cy + r * 0.62 * math.sin(math.tau * k / 6 + 0.3)) for k in range(6)], r * 0.5)
    outline += " " + dots([(cx, cy)], r * 0.62)
    pts = []
    for i in range(70):  # spiraal: de gevouwen blaadjes in het hart
        t = i / 69
        a = t * math.tau * 2.3 + 0.6
        rr = 1.2 + t * (r * 0.82)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.92))
    spiral = "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts)
    cup = (f"M{fmt(cx - r)} {fmt(cy + 1)}Q{fmt(cx)} {fmt(cy + r * 1.35)} {fmt(cx + r)} {fmt(cy + 1)}"
           f"M{fmt(cx - r * 0.8)} {fmt(cy + 4)}Q{fmt(cx)} {fmt(cy + r * 1.1)} {fmt(cx + r * 0.8)} {fmt(cy + 4)}")
    stem = f"M{fmt(cx)} {fmt(cy + r * 0.95)}C{fmt(cx + 1.2)} {fmt(cy + 19)} {fmt(cx - 1.4)} {fmt(cy + 27)} {fmt(cx - 0.4)} {fmt(cy + 35)}"
    lv = [leaf(cx - 0.2, cy + 22, 13.5, 5.8, math.radians(200), 0.08), leaf(cx + 0.2, cy + 27, 12.5, 5.4, math.radians(-24), -0.08)]
    vn = [leaf_vein(cx - 0.2, cy + 22, 13.5, math.radians(200), 0.08), leaf_vein(cx + 0.2, cy + 27, 12.5, math.radians(-24), -0.08)]
    body = (f'<path fill="#CFCFCF" d="{outline}"/>'
            f'<path fill="none" stroke="#CFCFCF" stroke-width="2.2" stroke-linecap="round" d="{stem}"/>'
            f'<path fill="#CFCFCF" d="{" ".join(lv)}"/>'
            f'<path fill="none" stroke="#8C8C8C" stroke-width=".9" stroke-linecap="round" d="{spiral} {cup} {" ".join(vn)}"/>')
    (OUT / "_zegel_roos.svg").write_text(body + "\n", encoding="utf-8")


def card_deckle(rnd):
    """Geschepte rand van de kaart (handgeschept papier): een clip-path-polygon met een zachte, onregelmatige rand.
    De afwijking is vloeiend (gemiddelde van buren), zodat het een vezelrand wordt en geen zaagtand."""

    def wobble(n, depth):
        raw = [rnd.uniform(0, 1) for _ in range(n)]
        smooth = [(raw[i - 1] + 2 * raw[i] + raw[(i + 1) % n]) / 4 for i in range(n)]
        return [depth * v for v in smooth]

    pts = []
    top, right, bottom, left = wobble(70, 0.9), wobble(60, 0.75), wobble(70, 0.9), wobble(60, 0.75)
    pts += [(100 * i / 70, top[i]) for i in range(70)]
    pts += [(100 - right[i], 100 * i / 60) for i in range(60)]
    pts += [(100 - 100 * i / 70, 100 - bottom[i]) for i in range(70)]
    pts += [(left[i], 100 - 100 * i / 60) for i in range(60)]
    (OUT / "_kaart_rand.txt").write_text(", ".join(f"{x:.2f}% {y:.2f}%" for x, y in pts), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_zegel_rand.svg").write_text(seal_edge(random.Random(311)) + "\n", encoding="utf-8")
    field = seal_edge(random.Random(902), r=33.5, amp=0.45, lobe_count=0, cx=60.5, cy=59.5)
    (OUT / "_zegel_veld.svg").write_text(field + "\n", encoding="utf-8")
    seal_wreath(random.Random(77), r=27.5)
    flap_florals(random.Random(2208))
    flap_florals_signature(random.Random(2208))
    liner_meadow(random.Random(53))
    card_deckle(random.Random(64))
    evergreen_flap(random.Random(1225))
    evergreen_liner(random.Random(2412))
    evergreen_liner(random.Random(2412), name="golden-noel", bg="#F3ECDD", twig="#A88848", dark="#B8934E", light="#D9C08A",
                    star="#B08A42", berry="#C9A35C")
    binnen_signature(random.Random(808))
    binnen_evergreen(random.Random(1912))
    flap_rose(random.Random(1402))
    seal_rose()
    print("klaar:", ", ".join(p.name for p in sorted(OUT.iterdir())))


if __name__ == "__main__":
    main()
