"""Maakt de tekeningen van het bruiloftsontwerp Voor altijd: een olijfkrans, een olijftakje en twee gouden ringen.

Gebruik (vanuit de projectmap): python tools/voor_altijd/maak_tekeningen.py
Schrijft designs/voor-altijd/v1/_krans.html, _takje.html en _ringen.html.

Kleuren komen uit CSS-klassen (va-blad, va-blad-2, va-steel, va-ring, va-ring-licht, va-steen), zodat elke
kleurvariant ze zelf kiest. Geen verlopen met id's: de tekeningen staan soms meer dan eens op één pagina.
Vaste startwaarde voor het toeval, zodat de tekening bij elke run hetzelfde is.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "designs" / "voor-altijd" / "v1"


def blad(x: float, y: float, hoek: float, lengte: float, breedte: float, cls: str) -> str:
    """Een smal olijfblad (lancetvormig) vanaf (x, y) in de richting `hoek` (graden)."""
    L, W = lengte, breedte
    d = f"M0 0C{L * .25:.1f} {-W:.1f} {L * .75:.1f} {-W * .7:.1f} {L:.1f} 0C{L * .75:.1f} {W * .7:.1f} {L * .25:.1f} {W:.1f} 0 0Z"
    nerf = f'<path class="va-nerf" d="M{L * .08:.1f} 0L{L * .85:.1f} 0"/>'
    return f'<g transform="translate({x:.1f} {y:.1f}) rotate({hoek:.1f})"><path class="{cls}" d="{d}"/>{nerf}</g>'


def tak_langs_boog(cx, cy, r, van, tot, kant, rnd, dichtheid=16):
    """Een tak langs een cirkelboog (hoeken in graden, 90 = onder), met bladeren om en om naar binnen en buiten."""
    steel_punten = []
    stappen = 40
    for i in range(stappen + 1):
        a = math.radians(van + (tot - van) * i / stappen)
        steel_punten.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    steel = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in steel_punten)
    delen = [f'<path class="va-steel" d="{steel}"/>']
    n = int(abs(tot - van) / 180 * dichtheid * 2)
    for i in range(1, n + 1):
        t = i / (n + 1)
        a = van + (tot - van) * t
        ar = math.radians(a)
        x, y = cx + r * math.cos(ar), cy + r * math.sin(ar)
        raak = a + (90 if tot > van else -90)  # richting van de tak
        uit = 1 if i % 2 else -1
        hoek = raak + uit * rnd.uniform(28, 42) * kant
        lengte = rnd.uniform(20, 27) * (1 - .3 * t)
        cls = "va-blad" if i % 3 else "va-blad-2"
        delen.append(blad(x, y, hoek, lengte, lengte * .26, cls))
    # Een paar olijfjes.
    for t in (.3, .62):
        a = math.radians(van + (tot - van) * t)
        x, y = cx + (r + 5 * kant) * math.cos(a), cy + (r + 5 * kant) * math.sin(a)
        delen.append(f'<ellipse class="va-olijf" cx="{x:.1f}" cy="{y:.1f}" rx="3.2" ry="4.2" transform="rotate({math.degrees(a):.0f} {x:.1f} {y:.1f})"/>')
    return "".join(delen)


def krans() -> str:
    """Olijfkrans: twee takken vanaf onder die elkaar bovenaan bijna raken (viewBox 0 0 200 200)."""
    rnd = random.Random(5)
    links = tak_langs_boog(100, 100, 78, 100, 262, 1, rnd)
    rechts = tak_langs_boog(100, 100, 78, 80, -82, -1, rnd)
    strik = ('<path class="va-lint" d="M100 178c-8-6-18-8-24-4 4 6 14 8 24 4Zm0 0c8-6 18-8 24-4-4 6-14 8-24 4Z"/>'
             '<path class="va-lint" d="M98 180l-8 14 6-2 4 4 2-15ZM102 180l8 14-6-2-4 4-2-15Z"/>'
             '<circle class="va-lint" cx="100" cy="179" r="3"/>')
    return ('<svg class="va-krans__svg" viewBox="0 0 200 200" aria-hidden="true" focusable="false">'
            + links + rechts + strik + "</svg>\n")


def takje() -> str:
    """Horizontaal olijftakje als scheiding (viewBox 0 0 240 40)."""
    rnd = random.Random(8)
    delen = ['<path class="va-steel" d="M20 22Q120 12 220 22"/>']
    for i in range(1, 24):
        x = 20 + 200 * i / 24
        y = 22 - 10 * math.sin(math.pi * i / 24)
        kant = 1 if i % 2 else -1
        hoek = (-90 + 50 * (1 if x < 120 else -1)) if kant < 0 else (90 - 50 * (1 if x < 120 else -1))
        hoek += rnd.uniform(-8, 8)
        lengte = 20 - abs(x - 120) / 14
        delen.append(blad(x, y, hoek - (0 if x < 120 else 0), lengte, lengte * .27, "va-blad" if i % 3 else "va-blad-2"))
    delen.append('<circle class="va-olijf" cx="120" cy="12" r="3"/>')
    return ('<svg class="va-takje__svg" viewBox="0 0 240 40" aria-hidden="true" focusable="false">'
            + "".join(delen) + "</svg>\n")


def ringen() -> str:
    """Twee in elkaar gehaakte ringen, de rechter met een steen (viewBox 0 0 200 140)."""
    def ring(cx, cy, r, klasse):
        # Ring als dikke omtrek, met een lichtere glans op de bovenkant en een donkerder rand onder.
        return (f'<ellipse class="va-ring {klasse}" cx="{cx}" cy="{cy}" rx="{r}" ry="{r * .92:.1f}"/>'
                f'<path class="va-ring-licht" d="M{cx - r * .8:.1f} {cy - r * .45:.1f}A{r} {r * .92:.1f} 0 0 1 {cx + r * .55:.1f} {cy - r * .75:.1f}"/>')
    links = ring(80, 80, 44, "va-ring--links")
    rechts = ring(122, 74, 44, "va-ring--rechts")
    # In elkaar gehaakt: bovenaan ligt de rechterring over de linker, onderaan de linkerring over de rechter.
    over = '<path class="va-ring va-ring--links" d="M111.1 108.6A44 40.5 0 0 1 91.4 119.1"/>'
    steen = ('<g class="va-steen-groep"><path class="va-zetting" d="M112 32l10-6 10 6-10 5Z"/>'
             '<path class="va-steen" d="M110 22l12-12 12 12-12 12Z"/>'
             '<path class="va-steen-licht" d="M116 20l6-6 4 4-6 6Z"/></g>')
    return ('<svg class="va-ringen__svg" viewBox="0 0 200 140" aria-hidden="true" focusable="false">'
            + links + rechts + over + steen + "</svg>\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    kop = "{# Gemaakt met tools/voor_altijd/maak_tekeningen.py; niet met de hand aanpassen. #}\n"
    (OUT / "_krans.html").write_text(kop + krans(), encoding="utf-8")
    (OUT / "_takje.html").write_text(kop + takje(), encoding="utf-8")
    (OUT / "_ringen.html").write_text(kop + ringen(), encoding="utf-8")
    print("geschreven: _krans.html, _takje.html, _ringen.html")


if __name__ == "__main__":
    main()
