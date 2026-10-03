"""Bouwstenen voor de beelden van Rosé Royale V2: rozen met echte diepte (gelaagde bladen met schaduw, lip-licht, korrel),
bladeren, eucalyptus, gipskruid, knoppen en parels, als SVG-tekst. maak_beelden.py zet ze samen tot scènes en rendert
ze met Chromium naar WebP (één keer; de pagina gebruikt alleen de beelden). Eigen ontwerp, vaste seeds, nergens gespiegeld.
"""
from __future__ import annotations

import math
import random


def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------------------------- kleuren
TONEN = {
    #            donker    diep      mid       licht     kern
    "blush": ("#A9505F", "#DE9198", "#F4C3BC", "#FFEDE6", "#7C2F40"),
    "ivoor": ("#B58F78", "#E4CCB9", "#F6E8DA", "#FFFBF5", "#9C7360"),
    "mauve": ("#7E3D52", "#BA7084", "#E2AEB8", "#F6DADB", "#55223A"),
    "roze": ("#8E2F4A", "#CF6A80", "#F0A3AF", "#FFD7D8", "#6A1E38"),
}


def verlopen() -> str:
    """Verlopen en filters voor alle beelden (één <defs>)."""
    out = []
    for naam, (donker, diep, mid, licht, kern) in TONEN.items():
        for ring in range(1, 6):
            # Buitenste ring licht en open, binnenste ringen dieper in de schaduw (de bladen erboven bedekken ze).
            k = (ring - 1) / 4
            out.append(
                f'<linearGradient id="r-{naam}-{ring}" x1="0" y1="1" x2="0" y2="0">'
                f'<stop offset="0" stop-color="{donker}"/><stop offset="{f(.30 + .12 * k)}" stop-color="{diep}"/>'
                f'<stop offset="{f(.70 + .06 * k)}" stop-color="{mid}"/><stop offset="1" stop-color="{licht}"/></linearGradient>')
        out.append(f'<radialGradient id="kelk-{naam}"><stop offset="0" stop-color="{kern}" stop-opacity=".62"/>'
                   f'<stop offset=".6" stop-color="{donker}" stop-opacity=".26"/><stop offset="1" stop-color="{donker}" stop-opacity="0"/></radialGradient>')
        out.append(f'<radialGradient id="h-{naam}"><stop offset="0" stop-color="{kern}"/><stop offset=".65" stop-color="{donker}"/>'
                   f'<stop offset="1" stop-color="{diep}"/></radialGradient>')
    out.append('<linearGradient id="blad" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#34472F"/><stop offset=".55" stop-color="#5F7A55"/><stop offset="1" stop-color="#9CB38C"/></linearGradient>')
    out.append('<linearGradient id="blad-licht" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#46603F"/><stop offset=".6" stop-color="#7C9A6C"/><stop offset="1" stop-color="#B4C8A3"/></linearGradient>')
    out.append('<radialGradient id="euca" cx="38%" cy="32%"><stop offset="0" stop-color="#D5E0D3"/><stop offset=".6" stop-color="#9DB4A5"/><stop offset="1" stop-color="#6A8478"/></radialGradient>')
    out.append('<radialGradient id="parel" cx="34%" cy="30%" r="75%"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".35" stop-color="#FBEFE6"/>'
               '<stop offset=".8" stop-color="#D9BFB0"/><stop offset="1" stop-color="#B49585"/></radialGradient>')
    out.append('<radialGradient id="parel-roze" cx="34%" cy="30%" r="75%"><stop offset="0" stop-color="#FFF3EE"/><stop offset=".4" stop-color="#F3CBC0"/>'
               '<stop offset="1" stop-color="#B8787A"/></radialGradient>')
    out.append('<linearGradient id="roseGoud" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8E4F4F"/><stop offset=".18" stop-color="#C98B7E"/>'
               '<stop offset=".34" stop-color="#FBDCCB"/><stop offset=".5" stop-color="#E0A593"/><stop offset=".68" stop-color="#A8625E"/>'
               '<stop offset=".84" stop-color="#F3C8B6"/><stop offset="1" stop-color="#8E4F4F"/></linearGradient>')
    out.append('<linearGradient id="roseGoud-v" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FBDCCB"/><stop offset=".3" stop-color="#C98B7E"/>'
               '<stop offset=".55" stop-color="#F6D0BF"/><stop offset=".8" stop-color="#B26F69"/><stop offset="1" stop-color="#8E4F4F"/></linearGradient>')
    # filters
    out.append('<filter id="ds" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="2.4" stdDeviation="2.8" flood-color="#33111F" flood-opacity=".5"/></filter>')
    out.append('<filter id="ds-groot" x="-30%" y="-30%" width="170%" height="180%"><feDropShadow dx="2" dy="9" stdDeviation="9" flood-color="#2A0D18" flood-opacity=".42"/></filter>')
    out.append('<filter id="lip" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation=".9"/></filter>')
    out.append('<filter id="korrel" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4" result="n"/>'
               '<feColorMatrix in="n" type="matrix" values="0 0 0 0 .62  0 0 0 0 .34  0 0 0 0 .38  0 0 0 .26 0" result="c"/>'
               '<feComposite in="c" in2="SourceAlpha" operator="in" result="ci"/><feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="ci"/></feMerge></filter>')
    return "".join(out)


# ---------------------------------------------------------------------------------------------- vormen
def petal_path(L: float, W: float) -> str:
    """Waaiervormig rozenblad met de voet in (0,0) en de rand (lip) bovenaan, met een zachte golf."""
    return (f"M0 0C{f(-W * .58)} {f(-L * .08)} {f(-W * .68)} {f(-L * .62)} {f(-W * .44)} {f(-L * .9)}"
            f"Q{f(-W * .22)} {f(-L * 1.04)} 0 {f(-L * .97)}Q{f(W * .22)} {f(-L * 1.04)} {f(W * .44)} {f(-L * .9)}"
            f"C{f(W * .68)} {f(-L * .62)} {f(W * .58)} {f(-L * .08)} 0 0Z")


def lip_path(L: float, W: float) -> str:
    return (f"M{f(-W * .44)} {f(-L * .9)}Q{f(-W * .22)} {f(-L * 1.04)} 0 {f(-L * .97)}Q{f(W * .22)} {f(-L * 1.04)} {f(W * .44)} {f(-L * .9)}")


def roos(rnd: random.Random, tone: str, R: float = 100, open_: float = 1.0) -> str:
    """Eén roos van boven gezien, gecentreerd op (0,0), straal ongeveer R. Vijf ringen bladen, elk met schaduw op de
    ring eronder; elk blad krijgt licht of schaduw naargelang het van de lamp (linksboven) af- of toe kijkt; een diepe
    kelk in het midden en een gekrulde kern. Zo lijkt het een echte, ronde roos en geen platte bloem."""
    s = R / 100
    ringen = [(7, 100, 94, 8, 0), (6, 84, 82, 5, 24), (6, 68, 68, 3, 8), (5, 52, 54, 1, 40), (4, 36, 40, 0, 16)]
    delen = []
    for i, (n, L, W, r0, off) in enumerate(ringen, start=1):
        petals = []
        for k in range(n):
            a = off + 360 * k / n + rnd.uniform(-10, 10)
            sc = rnd.uniform(.92, 1.07)
            Lk, Wk = L * sc * s, W * sc * s * (.82 + .18 * open_)
            # richting van het blad (omhoog gedraaid over a graden) tegenover de lamp linksboven: -1 (weg) .. 1 (toe)
            facing = (math.sin(math.radians(a)) * -0.62 + (-math.cos(math.radians(a))) * -0.78)
            licht = max(0.0, facing) * .30
            donker = max(0.0, -facing) * .34
            pad = petal_path(Lk, Wk)
            petals.append(
                f'<g transform="rotate({f(a)}) translate(0 {f(-r0 * s)})">'
                f'<path d="{pad}" fill="url(#r-{tone}-{i})"/>'
                f'<path d="{pad}" fill="#FFFFFF" fill-opacity="{f(licht)}"/><path d="{pad}" fill="#34101E" fill-opacity="{f(donker)}"/>'
                f'<path d="M0 {f(-Lk * .08)}L{f(rnd.uniform(-3, 3))} {f(-Lk * .78)}" stroke="#4A1426" stroke-opacity=".18" stroke-width="{f(1.5 * s)}" fill="none" stroke-linecap="round"/>'
                f'<path d="{lip_path(Lk, Wk)}" stroke="#FFF6F1" stroke-opacity="{f(.45 + licht)}" stroke-width="{f(2.1 * s)}" fill="none" stroke-linecap="round" filter="url(#lip)"/>'
                f'</g>')
        delen.append(f'<g filter="url(#ds)">{"".join(petals)}</g>')
        if i == 3:  # de kelk: een zachte, donkere schaduw in het hart, vóór de binnenste ringen
            delen.append(f'<circle r="{f(46 * s)}" fill="url(#kelk-{tone})"/>')
    delen.append(f'<circle r="{f(14 * s)}" fill="url(#h-{tone})"/>')
    for r, a0, a1 in ((11, 20, 240), (8, 150, 390), (4.6, 270, 480)):
        x0, y0 = r * s * math.cos(math.radians(a0)), r * s * math.sin(math.radians(a0))
        x1, y1 = r * s * math.cos(math.radians(a1)), r * s * math.sin(math.radians(a1))
        delen.append(f'<path d="M{f(x0)} {f(y0)}A{f(r * s)} {f(r * s)} 0 1 1 {f(x1)} {f(y1)}" fill="none" stroke="#FFEDE6" stroke-opacity=".4" stroke-width="{f(1.4 * s)}" stroke-linecap="round"/>')
    return "".join(delen)


def blad(L: float, W: float, licht: bool = False) -> str:
    """Rozenblad met rand, nerven en een zachte glansband."""
    g = "blad-licht" if licht else "blad"
    veins = "".join(f"M0 {f(-L * t)}Q{f(s * W * .35)} {f(-L * (t + .08))} {f(s * W * .78)} {f(-L * (t + .2))}" for t in (.18, .34, .5, .64) for s in (-1, 1))
    return (f'<g filter="url(#ds)"><path d="M0 0C{f(-W * .95)} {f(-L * .22)} {f(-W * .82)} {f(-L * .78)} 0 {f(-L)}C{f(W * .82)} {f(-L * .78)} {f(W * .95)} {f(-L * .22)} 0 0Z" fill="url(#{g})"/>'
            f'<path d="M0 {f(-L * .04)}V{f(-L * .92)}" stroke="#DCE6CC" stroke-opacity=".7" stroke-width="{f(max(.8, W * .035))}" fill="none"/>'
            f'<path d="{veins}" stroke="#DCE6CC" stroke-opacity=".28" stroke-width="{f(max(.6, W * .02))}" fill="none"/>'
            f'<path d="M{f(-W * .2)} {f(-L * .1)}Q{f(-W * .62)} {f(-L * .5)} {f(-W * .12)} {f(-L * .9)}" stroke="#FFFFFF" stroke-opacity=".16" stroke-width="{f(W * .14)}" fill="none" stroke-linecap="round"/></g>')


def euca(rnd: random.Random, L: float = 200) -> str:
    """Eucalyptustakje (zilverdollar) van (0,0) omhoog: afwisselend grote, ronde, poederige blaadjes aan korte steeltjes."""
    out = [f'<path d="M0 0C{f(L * .05)} {f(-L * .3)} {f(-L * .05)} {f(-L * .7)} {f(L * .03)} {f(-L)}" stroke="#6B7D62" stroke-width="{f(L * .018)}" fill="none" stroke-linecap="round"/>']
    for i in range(9):
        y = -L * (.08 + i * .105)
        r = L * (.10 - i * .0065)
        s = 1 if i % 2 else -1
        ang = s * rnd.uniform(48, 64)
        x0 = s * L * .01
        out.append(f'<g transform="translate({f(x0)} {f(y)}) rotate({f(ang)})"><path d="M0 0V{f(-r * .5)}" stroke="#7D8F70" stroke-width="{f(L * .008)}"/>'
                   f'<ellipse cx="0" cy="{f(-r * 1.3)}" rx="{f(r * .86)}" ry="{f(r)}" fill="url(#euca)"/>'
                   f'<path d="M0 {f(-r * .4)}V{f(-r * 2.1)}" stroke="#E4ECE2" stroke-opacity=".5" stroke-width="{f(L * .006)}"/>'
                   f'<ellipse cx="{f(-r * .25)}" cy="{f(-r * 1.6)}" rx="{f(r * .25)}" ry="{f(r * .5)}" fill="#FFFFFF" fill-opacity=".22"/></g>')
    return f'<g filter="url(#ds)">{"".join(out)}</g>'


def gipskruid(rnd: random.Random, L: float = 200, takken: int = 5) -> str:
    """Gipskruid: wiebelige draadjes met kleine witte bloempjes (luchtig, maakt het boeket duurder)."""
    out = []
    for _ in range(takken):
        a = rnd.uniform(-38, 38)
        l = L * rnd.uniform(.6, 1)
        bend = rnd.uniform(-L * .16, L * .16)
        out.append(f'<g transform="rotate({f(a)})"><path d="M0 0Q{f(bend)} {f(-l * .55)} {f(bend * .6)} {f(-l)}" stroke="#7D8F6F" stroke-opacity=".8" stroke-width="{f(L * .008 + .6)}" fill="none"/>')
        for _ in range(7):
            t = rnd.uniform(.35, 1)
            x = bend * t * t * 1.0 + rnd.uniform(-L * .05, L * .05)
            y = -l * t
            r = rnd.uniform(2.4, 4.6) * L / 200
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="#FFF9F5"/><circle cx="{f(x)}" cy="{f(y)}" r="{f(r * .35)}" fill="#E9C9C0"/>')
        out.append('</g>')
    return "".join(out)


def knop(tone: str, L: float = 90, rnd: random.Random | None = None) -> str:
    """Rozenknop van opzij, met groene kelkblaadjes (voet in (0,0), top omhoog)."""
    return (f'<g filter="url(#ds)"><path d="M0 0C{f(-L * .42)} {f(-L * .1)} {f(-L * .38)} {f(-L * .62)} 0 {f(-L)}C{f(L * .38)} {f(-L * .62)} {f(L * .42)} {f(-L * .1)} 0 0Z" fill="url(#r-{tone}-2)"/>'
            f'<path d="M{f(-L * .04)} 0C{f(-L * .3)} {f(-L * .14)} {f(-L * .2)} {f(-L * .56)} {f(L * .1)} {f(-L * .86)}C{f(L * .32)} {f(-L * .52)} {f(L * .24)} {f(-L * .1)} {f(-L * .04)} 0Z" fill="url(#r-{tone}-4)"/>'
            f'<path d="M{f(-L * .05)} {f(-L * .05)}C{f(-L * .12)} {f(-L * .3)} {f(-L * .02)} {f(-L * .6)} {f(L * .14)} {f(-L * .8)}" stroke="#FFF6F1" stroke-opacity=".5" stroke-width="{f(L * .02)}" fill="none" filter="url(#lip)"/>'
            f'<path d="M0 {f(L * .06)}C{f(-L * .26)} {f(L * .02)} {f(-L * .42)} {f(-L * .14)} {f(-L * .48)} {f(-L * .34)}C{f(-L * .3)} {f(-L * .22)} {f(-L * .16)} {f(-L * .18)} {f(-L * .02)} {f(-L * .16)}'
            f'C{f(L * .12)} {f(-L * .2)} {f(L * .28)} {f(-L * .24)} {f(L * .46)} {f(-L * .3)}C{f(L * .4)} {f(-L * .1)} {f(L * .24)} {f(L * .02)} 0 {f(L * .06)}Z" fill="url(#blad)"/>'
            f'<path d="M0 {f(L * .06)}V{f(L * .6)}" stroke="#4F6249" stroke-width="{f(L * .04)}" fill="none" stroke-linecap="round"/></g>')


def parel(r: float, roze: bool = False) -> str:
    """Parel met glans (cirkel op (0,0))."""
    g = "parel-roze" if roze else "parel"
    return (f'<g filter="url(#ds)"><circle r="{f(r)}" fill="url(#{g})"/>'
            f'<ellipse cx="{f(-r * .34)}" cy="{f(-r * .4)}" rx="{f(r * .3)}" ry="{f(r * .18)}" fill="#FFFFFF" fill-opacity=".92" transform="rotate(-32 {f(-r * .34)} {f(-r * .4)})"/></g>')


# ---------------------------------------------------------------------------------------------- samenstellen
def plaats(inhoud: str, x: float, y: float, rot: float = 0, schaal: float = 1.0, sy: float = 1.0) -> str:
    return f'<g transform="translate({f(x)} {f(y)}) rotate({f(rot)}) scale({f(schaal)} {f(schaal * sy)})">{inhoud}</g>'


def svg_document(w: int, h: int, body: str, vb: str | None = None, extra_defs: str = "") -> str:
    vb = vb or f"0 0 {w} {h}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="{vb}">'
            f'<defs>{verlopen()}{extra_defs}</defs>{body}</svg>')
