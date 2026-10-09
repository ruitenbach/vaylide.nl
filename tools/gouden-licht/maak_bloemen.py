"""Tekent de reliëfbloemen op de envelop van het ontwerp Gouden licht.

Gebruik (vanuit de hoofdmap):  .venv/bin/python tools/gouden-licht/maak_bloemen.py

Schrijft designs/gouden-licht/v1/bloemen.html: één onzichtbare SVG met het symbool
"gl-bloemen" (viewBox 500 x 800, dezelfde verhouding als de envelop). De uitnodiging
gebruikt het symbool meerdere keren met <use>: als reliëf, als schaduw en als goudglans.
Alles is zelf getekend uit eenvoudige krommen; er is geen beeld van elders gebruikt.
De uitkomst is vast (geen toeval), zodat een nieuwe run hetzelfde bestand geeft.
"""
from __future__ import annotations

import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "designs" / "gouden-licht" / "v1" / "bloemen.html"


def f(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


def smooth_closed(points: list[tuple[float, float]]) -> str:
    """Gesloten vloeiende kromme door de punten (Catmull-Rom naar Bézier)."""
    n = len(points)
    d = [f"M{f(points[0][0])} {f(points[0][1])}"]
    for i in range(n):
        p0, p1, p2, p3 = points[(i - 1) % n], points[i], points[(i + 1) % n], points[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}")
    return "".join(d) + "Z"


def rose(cx: float, cy: float, r: float, turn: float = 0.0) -> list[str]:
    """Een roos in lijnen: vier golvende bladkransen en een spiraal in het hart."""
    paths = []
    layers = [(1.0, 7, 0.16), (0.76, 6, 0.18), (0.54, 5, 0.2), (0.34, 4, 0.22)]
    for k, (scale, lobes, wobble) in enumerate(layers):
        pts = []
        steps = lobes * 4
        for i in range(steps):
            a = 2 * math.pi * i / steps + turn + k * 0.7
            rr = r * scale * (1 + wobble * math.sin(lobes * (a - turn - k * 0.7)))
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.94))
        paths.append(smooth_closed(pts))
    # De spiraal in het hart.
    pts = []
    for i in range(0, 30):
        t = i / 29
        a = turn + t * 5.2
        rr = r * 0.2 * t + r * 0.02
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = f"M{f(pts[0][0])} {f(pts[0][1])}" + "".join(f"L{f(x)} {f(y)}" for x, y in pts[1:])
    paths.append(d)
    # Twee krulletjes op de buitenste bladeren, zodat de roos wat leeft.
    for j in (0.9, 3.4):
        a = turn + j
        x0, y0 = cx + r * 0.86 * math.cos(a), cy + r * 0.86 * math.sin(a)
        x1, y1 = cx + r * 0.52 * math.cos(a + 0.5), cy + r * 0.52 * math.sin(a + 0.5)
        paths.append(f"M{f(x0)} {f(y0)}Q{f((x0 + x1) / 2 + 3)} {f((y0 + y1) / 2 - 4)} {f(x1)} {f(y1)}")
    return paths


def leaf(x: float, y: float, length: float, angle_deg: float, width: float = 0.34) -> list[str]:
    """Een blad met hoofdnerf en zijnerven. Het blad wijst vanaf (x, y) onder de hoek."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)

    def pt(u: float, v: float) -> tuple[float, float]:
        return x + u * ca - v * sa, y + u * sa + v * ca

    w = length * width
    tip = pt(length, 0)
    c1, c2 = pt(length * 0.28, -w * 1.25), pt(length * 0.78, -w * 0.75)
    c3, c4 = pt(length * 0.78, w * 0.75), pt(length * 0.28, w * 1.25)
    outline = (f"M{f(x)} {f(y)}C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(tip[0])} {f(tip[1])}"
               f"C{f(c3[0])} {f(c3[1])} {f(c4[0])} {f(c4[1])} {f(x)} {f(y)}Z")
    rib_end = pt(length * 0.92, 0)
    parts = [outline, f"M{f(x)} {f(y)}L{f(rib_end[0])} {f(rib_end[1])}"]
    for u in (0.3, 0.5, 0.68):
        for side in (-1, 1):
            a0 = pt(length * u, 0)
            a1 = pt(length * (u + 0.2), side * w * 0.62 * (1 - u * 0.5))
            parts.append(f"M{f(a0[0])} {f(a0[1])}L{f(a1[0])} {f(a1[1])}")
    return parts


def stem(points: list[tuple[float, float]]) -> str:
    """Open vloeiende kromme (de rank)."""
    d = [f"M{f(points[0][0])} {f(points[0][1])}"]
    for i in range(len(points) - 1):
        p0 = points[max(i - 1, 0)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}")
    return "".join(d)


def bud(cx: float, cy: float, r: float, angle_deg: float) -> list[str]:
    """Een knop: een druppel met twee kelkblaadjes."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)

    def pt(u: float, v: float) -> tuple[float, float]:
        return cx + u * ca - v * sa, cy + u * sa + v * ca

    tip, l1, l2, base = pt(r * 1.5, 0), pt(r * 0.2, -r * 1.0), pt(r * 0.2, r * 1.0), pt(-r * 0.7, 0)
    body = (f"M{f(base[0])} {f(base[1])}C{f(l1[0])} {f(l1[1])} {f(l1[0])} {f(l1[1])} {f(tip[0])} {f(tip[1])}"
            f"C{f(l2[0])} {f(l2[1])} {f(l2[0])} {f(l2[1])} {f(base[0])} {f(base[1])}Z")
    s1, s2 = pt(r * 0.9, -r * 0.95), pt(r * 0.9, r * 0.95)
    sep = f"M{f(base[0])} {f(base[1])}L{f(s1[0])} {f(s1[1])}M{f(base[0])} {f(base[1])}L{f(s2[0])} {f(s2[1])}"
    return [body, sep]


def vine(spec: dict) -> list[str]:
    """Een rank met bladeren, een knop en een of twee rozen."""
    out = [stem(spec["stem"])]
    for lf in spec["leaves"]:
        out += leaf(*lf)
    for b in spec.get("buds", []):
        out += bud(*b)
    for rs in spec["roses"]:
        out += rose(*rs)
    return out


# Linkerkant: twee rozen met een rank langs de rand; rechterkant: één grote roos en een kleinere.
LEFT = {
    "stem": [(-10, 190), (60, 250), (95, 340), (70, 440), (105, 540), (80, 640), (20, 700)],
    "leaves": [(70, 270, 70, -50), (92, 330, 64, 20), (78, 420, 58, 205), (96, 500, 70, 12), (92, 570, 64, 200),
               (70, 610, 62, 110), (60, 660, 54, 60), (44, 300, 46, 190)],
    "buds": [(46, 410, 15, 150), (128, 488, 13, -20)],
    "roses": [(112, 366, 62, 0.4), (84, 566, 40, 1.3)],
}
RIGHT = {
    "stem": [(510, 210), (440, 270), (405, 350), (430, 450), (395, 540), (430, 640), (500, 710)],
    "leaves": [(430, 290, 66, 230), (412, 350, 70, 160), (426, 430, 60, -20), (404, 500, 66, 168), (416, 590, 64, -12),
               (434, 640, 56, 122), (450, 300, 44, -30), (470, 660, 48, 128)],
    "buds": [(454, 440, 14, 30), (380, 518, 13, 190)],
    "roses": [(396, 400, 66, 2.1), (428, 566, 38, 0.2)],
}
# Onderaan, op de onderste klep: twee losse takjes met bladeren.
SPRIGS = [
    {"stem": [(28, 770), (70, 735), (120, 722)], "leaves": [(70, 735, 56, -90), (92, 728, 54, -20), (50, 752, 50, 200), (112, 722, 48, 10), (36, 764, 44, 160)], "roses": [], "buds": [(122, 721, 8, 0)]},
    {"stem": [(476, 770), (432, 735), (380, 722)], "leaves": [(432, 735, 56, 270), (410, 728, 54, 200), (454, 752, 50, -20), (388, 722, 48, 170), (468, 764, 44, 20)], "roses": [], "buds": [(378, 721, 8, 180)]},
]
# Een rijtje bladeren langs de bovenrand van de linker- en rechterklep.
CORNERS = [
    {"stem": [(-6, 40), (40, 90), (84, 140)], "leaves": [(40, 90, 50, -50), (62, 114, 46, 40), (22, 66, 42, 200), (84, 140, 40, 20)], "roses": []},
    {"stem": [(506, 40), (460, 90), (416, 140)], "leaves": [(460, 90, 50, 230), (438, 114, 46, 140), (478, 66, 42, -20), (416, 140, 40, 160)], "roses": []},
]


def build() -> str:
    paths: list[str] = []
    for spec in [LEFT, RIGHT, *SPRIGS, *CORNERS]:
        paths += vine(spec)
    body = "".join(f'<path d="{d}"/>' for d in paths)
    return (
        "{# Gemaakt door tools/gouden-licht/maak_bloemen.py: niet met de hand wijzigen. #}\n"
        '<svg class="gl-defs" width="0" height="0" aria-hidden="true" focusable="false" style="position:absolute">'
        f'<defs><symbol id="gl-bloemen" viewBox="0 0 500 800">{body}</symbol></defs></svg>\n'
    )


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"{OUT.relative_to(OUT.parents[3])} geschreven ({OUT.stat().st_size} bytes)")
