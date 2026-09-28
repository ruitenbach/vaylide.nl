"""Maakt de tekeningen van het kerstontwerp Gloria: een grote engelenvleugel (openingsscherm) en een engel met bazuin.

Gebruik (vanuit de projectmap): python tools/gloria/maak_tekeningen.py
Schrijft designs/gloria/v1/_vleugel.html en designs/gloria/v1/_engel.html.

De veren zijn druppelvormen die in rijen uitwaaieren vanuit de schouder: achteraan de lange slagpennen, daarvoor
steeds kortere dekveren. Kleuren komen uit CSS-klassen (gl-f1 tot gl-f4, gl-lijn), zodat elke kleurvariant ze zelf
kiest. Er zijn geen verlopen met id's: de tekeningen staan meerdere keren op één pagina.
"""
from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "designs" / "gloria" / "v1"


def veer(x: float, y: float, hoek: float, lengte: float, breedte: float, cls: str, schacht: bool = True) -> str:
    """Eén veer: een druppel met punt, vanaf (x, y) in de richting `hoek` (graden, 0 = rechts, 90 = omlaag)."""
    L, W = lengte, breedte
    d = (f"M0 0C{L * .28:.1f} {-W:.1f} {L * .8:.1f} {-W * .78:.1f} {L:.1f} {-W * .08:.1f}"
         f"C{L * .82:.1f} {W * .62:.1f} {L * .3:.1f} {W:.1f} 0 0Z")
    out = f'<path class="{cls}" d="{d}"/>'
    if schacht:
        out += f'<path class="gl-schacht" d="M{L * .04:.1f} 0Q{L * .5:.1f} {W * .08:.1f} {L * .9:.1f} {-W * .06:.1f}"/>'
    return f'<g transform="translate({x:.1f} {y:.1f}) rotate({hoek:.1f})">{out}</g>'


def rij(x, y, van, tot, stap, lengte_fn, breedte, cls, schacht=True):
    hoeken = []
    a = van
    while a <= tot + 1e-6:
        hoeken.append(a)
        a += stap
    return "".join(veer(x, y, h, lengte_fn(h), breedte, cls, schacht) for h in hoeken)


def vleugel() -> str:
    """Linkervleugel voor het openingsscherm (viewBox 0 0 300 640): schouder rechtsboven, veren naar links en omlaag.
    De rechtervleugel is dezelfde tekening, gespiegeld met CSS."""
    sx, sy = 292, 70

    def tot_rand(h: float, factor: float) -> float:
        r = math.radians(h)
        dx, dy = math.cos(r), math.sin(r)
        afstanden = []
        if dx < -1e-3:
            afstanden.append((sx + 30) / -dx)
        if dy > 1e-3:
            afstanden.append((640 + 40 - sy) / dy)
        if dy < -1e-3:
            afstanden.append((sy + 30) / -dy)
        return min(afstanden) * factor

    delen = [
        rij(sx, sy, 86, 196, 6.5, lambda h: tot_rand(h, 1.02), 40, "gl-f4"),
        rij(sx - 4, sy + 4, 92, 190, 7, lambda h: tot_rand(h, .72), 34, "gl-f3"),
        rij(sx - 6, sy + 6, 98, 186, 8.5, lambda h: tot_rand(h, .46), 28, "gl-f2"),
        rij(sx - 8, sy + 8, 104, 180, 10, lambda h: tot_rand(h, .26), 22, "gl-f1"),
        rij(sx - 8, sy + 10, 112, 172, 12, lambda h: tot_rand(h, .13), 15, "gl-f1", schacht=False),
    ]
    schouder = f'<ellipse class="gl-f1" cx="{sx - 4}" cy="{sy + 6}" rx="26" ry="20"/>'
    return (
        '<svg class="gl-vleugel__svg" viewBox="0 0 300 640" preserveAspectRatio="xMaxYMin slice" aria-hidden="true" focusable="false">'
        + "".join(delen) + schouder + "</svg>\n"
    )


def engel() -> str:
    """Engel met bazuin, naar rechts kijkend (viewBox 0 0 220 250). Lijntekening in goud met lichte vullingen."""
    sx, sy = 84, 100  # schouder
    vleugel_achter = rij(sx, sy, 196, 272, 9, lambda h: 118 - abs(h - 236) * 1.1, 17, "gl-f3")
    vleugel_mid = rij(sx + 2, sy + 2, 204, 262, 11, lambda h: 74 - abs(h - 234) * .7, 14, "gl-f2")
    vleugel_voor = rij(sx + 3, sy + 3, 212, 252, 13, lambda h: 40, 11, "gl-f1", schacht=False)
    gewaad = (
        '<path class="gl-kleed" d="M80 96C70 140 52 190 34 236C62 229 96 243 120 234C136 240 152 236 166 240C150 194 128 142 110 96Z"/>'
        '<path class="gl-plooi" d="M92 108C86 150 76 196 66 234M100 108C100 152 98 198 96 238M106 110C114 150 126 196 138 236"/>'
        '<path class="gl-kleed" d="M78 96Q95 88 112 96L110 106Q95 100 80 106Z"/>'
    )
    arm = (
        '<path class="gl-kleed" d="M104 104C118 104 128 96 138 88L144 96C134 106 120 116 104 116Z"/>'
        '<circle class="gl-huid" cx="141" cy="90" r="5"/>'
    )
    hoofd = (
        '<path class="gl-haar" d="M84 74C80 56 96 46 108 52C118 58 118 70 112 78C112 88 104 94 94 92C86 92 80 86 84 74Z"/>'
        '<circle class="gl-huid" cx="104" cy="72" r="12"/>'
        '<path class="gl-haar" d="M92 66C96 56 110 54 116 62C110 60 102 62 96 70Z"/>'
        '<ellipse class="gl-aureool" cx="100" cy="50" rx="17" ry="5"/>'
    )
    bazuin = (
        '<path class="gl-goud" d="M114 76L196 54L197 58L115 80Z"/>'
        '<path class="gl-goud" d="M194 50C202 46 212 36 216 30C218 46 218 66 216 82C210 76 202 66 194 62Z"/>'
        '<path class="gl-vaandel" d="M150 66C156 80 170 92 186 90C178 98 176 110 180 118C164 118 150 106 146 90Z"/>'
        '<circle class="gl-goud" cx="120" cy="77" r="2.4"/>'
    )
    return (
        '<svg class="gl-engel__svg" viewBox="0 0 220 250" aria-hidden="true" focusable="false">'
        f'<g class="gl-engel__vleugel">{vleugel_achter}{vleugel_mid}{vleugel_voor}</g>'
        f"{gewaad}{arm}{hoofd}<g class=\"gl-engel__bazuin\">{bazuin}</g></svg>\n"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    kop = "{# Gemaakt met tools/gloria/maak_tekeningen.py; niet met de hand aanpassen. #}\n"
    (OUT / "_vleugel.html").write_text(kop + vleugel(), encoding="utf-8")
    (OUT / "_engel.html").write_text(kop + engel(), encoding="utf-8")
    print("geschreven: _vleugel.html, _engel.html")


if __name__ == "__main__":
    main()
