"""Beelden van Midnight Émeraude (WebP met doorzichtige achtergrond), eenmalig gerenderd uit eigen SVG-tekeningen met Chromium.

Kleurwereld: smaragd, middernachtblauw, champagnegoud, ivoor, parel en kristal (geen roze en geen roségoud).
Hergebruikt de gereedschappen van Rosé Royale (rozen met licht per blad, bladeren, eucalyptus, de oranjerie-scène); de oranjerie
en de lichtstralen worden hier naar de nieuwe kleuren omgezet. Het heroobject is nieuw: twee in elkaar grijpende gouden
ringen met een kristal. Vaste seeds, nergens gespiegeld.

Gebruik (vanuit de projectmap): python tools/midnight_emeraude/maak_beelden.py [naam ...]
Uitvoer: designs/midnight-emeraude/v1/img/*.webp
"""
from __future__ import annotations

import colorsys
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "rose_royale"))
import beeld_bouwstenen as bb  # noqa: E402
import maak_beelden as mb  # noqa: E402  (render, cluster, vervaag, oranjerie_scene, stralen_scene)

OUT = ROOT / "designs" / "midnight-emeraude" / "v1" / "img"
mb.OUT = OUT  # de gedeelde render() schrijft naar deze map
mb.RANDEN.clear()
mb.RANDEN.update({
    "wereld-donker": dict(links=.12, rechts=.12, boven=.08, onder=.08), "wereld-licht": dict(links=.12, rechts=.12, boven=.08, onder=.08),
    "stralen": dict(links=.18, rechts=.18, boven=.24),
    "voor-links": dict(rechts=.22, boven=.20), "voor-rechts": dict(links=.22, boven=.20),
    "bloemen-links": dict(links=.05, rechts=.14, boven=.12), "bloemen-rechts": dict(links=.14, rechts=.05, boven=.12),
    "blad-rand": dict(rechts=.20, onder=.20),
    "kristallen": dict(onder=.16, links=.04, rechts=.04),
})
f, plaats = bb.f, bb.plaats

# Champagne-pioenen: warme schaduwen (olijf/umber, die door omzetten() ingroene tinten worden), middentonen champagne, lichten ivoor.
bb.TONEN["pioen"] = ("#5A5444", "#B4A488", "#E8DCC5", "#FBF4E5", "#7A6A4C")


# ---------------------------------------------------------------------------------------------- kleuren omzetten
def omzetten(tekst: str) -> str:
    """Zet alle kleuren van een Rosé Royale-tekening om naar de wereld van Midnight Émeraude: donkere paars- en rozetinten
    worden inktgroen, middentonen blauwgroen, lichte warme tinten champagne. Groen en neutraal (wit, grijs) blijft."""
    def kleur(m: re.Match) -> str:
        h6 = m.group(1)
        r, g, b = (int(h6[i:i + 2], 16) / 255 for i in (0, 2, 4))
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        hd = h * 360
        if s < .08 or 70 <= hd <= 175:
            return m.group(0)
        if l < .30:
            nh, ns, nl = 168, min(s, .42) * .9, l * .78
        elif l < .62:
            if hd >= 240 or hd <= 15:  # paars, roze, rood: blauwgroen
                nh, ns, nl = 172, .30, l * .74
            else:  # warm: donker champagne
                nh, ns, nl = 42, .42, l
        else:  # licht en warm: champagne
            nh, ns, nl = 42, min(s * .9, .58), l
        rr, gg, bb_ = colorsys.hls_to_rgb(nh / 360, nl, ns)
        return "#{:02X}{:02X}{:02X}".format(round(rr * 255), round(gg * 255), round(bb_ * 255))
    return re.sub(r"#([0-9A-Fa-f]{6})\b", kleur, tekst)


# ---------------------------------------------------------------------------------------------- gedeelde defs
def defs_extra() -> str:
    return (
        '<linearGradient id="goudD" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7A6330"/><stop offset=".2" stop-color="#C2A55F"/>'
        '<stop offset=".36" stop-color="#F6E7BC"/><stop offset=".5" stop-color="#D3B66F"/><stop offset=".68" stop-color="#8F7438"/>'
        '<stop offset=".84" stop-color="#EBD7A0"/><stop offset="1" stop-color="#7A6330"/></linearGradient>'
        '<linearGradient id="bladD" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#04120D"/><stop offset=".5" stop-color="#0D3024"/><stop offset="1" stop-color="#1F5A45"/></linearGradient>'
        '<linearGradient id="bladD2" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#071A13"/><stop offset=".55" stop-color="#14402F"/><stop offset="1" stop-color="#2E7560"/></linearGradient>'
        '<linearGradient id="pioen-voet" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#0A1F18" stop-opacity=".5"/><stop offset=".45" stop-color="#0A1F18" stop-opacity=".12"/><stop offset="1" stop-color="#0A1F18" stop-opacity="0"/></linearGradient>'
        '<radialGradient id="orb"><stop offset="0" stop-color="#FFF3CF" stop-opacity=".95"/><stop offset=".45" stop-color="#F0D690" stop-opacity=".5"/><stop offset="1" stop-color="#E8C878" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="steen" cx="38%" cy="32%" r="80%"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".5" stop-color="#E4F1EC"/><stop offset="1" stop-color="#8FB0A6"/></radialGradient>'
        '<filter id="mg" x="-10%" y="-10%" width="120%" height="120%" color-interpolation-filters="sRGB">'
        '<feGaussianBlur in="SourceAlpha" stdDeviation="{sd}" result="b"/>'
        '<feSpecularLighting in="b" surfaceScale="{ss}" specularConstant="1.25" specularExponent="30" lighting-color="#FFF6DE" result="sp"><feDistantLight azimuth="235" elevation="48"/></feSpecularLighting>'
        '<feComposite in="sp" in2="SourceAlpha" operator="in" result="spIn"/>'
        '<feDiffuseLighting in="b" surfaceScale="{ss}" diffuseConstant="1.05" lighting-color="#FFFFFF" result="df"><feDistantLight azimuth="235" elevation="52"/></feDiffuseLighting>'
        '<feComposite in="SourceGraphic" in2="df" operator="arithmetic" k1="1.25" k2="0" k3="0" k4="0" result="sh"/>'
        '<feComposite in="sh" in2="SourceAlpha" operator="in" result="sh2"/>'
        '<feTurbulence type="fractalNoise" baseFrequency=".55 .95" numOctaves="2" seed="3" result="n"/>'
        '<feColorMatrix in="n" type="matrix" values="0 0 0 0 .55  0 0 0 0 .42  0 0 0 0 .18  0 0 0 .26 0" result="na"/>'
        '<feComposite in="na" in2="SourceAlpha" operator="in" result="naIn"/>'
        '<feBlend in="naIn" in2="sh2" mode="multiply" result="g"/><feBlend in="spIn" in2="g" mode="screen"/></filter>')


def doc(w: int, h: int, body: str, extra: str = "") -> str:
    return bb.svg_document(w, h, body, extra_defs=defs_extra().replace("{sd}", "11").replace("{ss}", "14") + extra)


# ---------------------------------------------------------------------------------------------- de wereld
def wereld(lit: bool) -> str:
    return omzetten(mb.oranjerie_scene(lit))


def stralen() -> str:
    return omzetten(mb.stralen_scene())


# ---------------------------------------------------------------------------------------------- hero-object: de ringen
def kristal(x: float, y: float, r: float) -> str:
    """Een geslepen steen (briljant) met tafel, kroonfacetten en glans, in parel- en kristaltinten."""
    rnd = random.Random(int(x * 7 + y))
    toon = ["#FFFFFF", "#DDEEE8", "#B5D2C8", "#F4FAF7", "#9FC0B5", "#E9F5F0", "#CFE4DC", "#FFFFFF"]
    pts = [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(0, 360, 45)]
    facetten = []
    for i in range(8):
        a, b = pts[i], pts[(i + 1) % 8]
        facetten.append(f'<path d="M{f(x)} {f(y)}L{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}Z" fill="{toon[i]}"/>')
    tafel = [(x + r * .5 * math.cos(math.radians(a + 22.5)), y + r * .5 * math.sin(math.radians(a + 22.5))) for a in range(0, 360, 45)]
    kroon = "".join(f'<path d="M{f(tafel[i][0])} {f(tafel[i][1])}L{f(pts[(i + 1) % 8][0])} {f(pts[(i + 1) % 8][1])}L{f(tafel[(i + 1) % 8][0])} {f(tafel[(i + 1) % 8][1])}Z" '
                    f'fill="{toon[(i + 3) % 8]}" fill-opacity=".8"/>' for i in range(8))
    tafelpad = "M" + "L".join(f"{f(a)} {f(b)}" for a, b in tafel) + "Z"
    return (f'<g><circle cx="{f(x)}" cy="{f(y)}" r="{f(r * 1.12)}" fill="#6E5A2A" fill-opacity=".5"/>{"".join(facetten)}{kroon}'
            f'<path d="{tafelpad}" fill="#FFFFFF" fill-opacity=".72"/><path d="{tafelpad}" fill="none" stroke="#FFFFFF" stroke-opacity=".9" stroke-width="1.4"/>'
            f'<circle cx="{f(x - r * .3)}" cy="{f(y - r * .34)}" r="{f(r * .16)}" fill="#FFFFFF"/></g>')


def ster4(x: float, y: float, r: float, o: float = .95) -> str:
    q = r * .2
    return (f'<path d="M{f(x)} {f(y - r)}L{f(x + q)} {f(y - q)}L{f(x + r)} {f(y)}L{f(x + q)} {f(y + q)}L{f(x)} {f(y + r)}L{f(x - q)} {f(y + q)}L{f(x - r)} {f(y)}L{f(x - q)} {f(y - q)}Z" '
            f'fill="#FFFFFF" fill-opacity="{o}"/>')


def ring_scene() -> str:
    """Het herkenbare object van Midnight Émeraude: twee in elkaar grijpende, gouden ringen (een oneindigheidsteken van twee
    trouwringen) met een geslepen kristal op de rechterring en een rij kleine steentjes op de linker. Het goud is geborsteld
    (fijne korrel) met een gepolijste glans. Canvas 900x720."""
    R = 190   # straal van de middellijn van de band
    T = 50    # breedte van de band
    ax, bx, cy = 330, 570, 392
    band = lambda cx: f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="url(#goudD)" stroke-width="{T}"/>'
    # tweede, smalle lijn in de band (een gegraveerde groef) voor een rijkere afwerking
    groef = lambda cx: f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#6E5A2A" stroke-opacity=".55" stroke-width="2.2"/>'
    ix, iy = 450, cy - math.sqrt(R * R - 120 * 120)
    delen = [
        # ring B (rechts) eerst, dan ring A (links) erover; op het bovenste kruispunt gaat A onder B door
        f'<g filter="url(#mg)">{band(bx)}</g>',
        f'<g filter="url(#mg)">{band(ax)}</g>',
        f'<clipPath id="bovenkruis"><rect x="{f(ix - 74)}" y="{f(iy - 70)}" width="148" height="140"/></clipPath>',
        f'<g clip-path="url(#bovenkruis)"><g filter="url(#mg)">{band(bx)}</g></g>',
        groef(ax), groef(bx),
    ]
    # steentjes langs ring A (links bovenboog)
    for k in range(13):
        a = math.radians(196 + k * 8.5)
        x, y = ax + R * math.cos(a), cy + R * math.sin(a)
        delen.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="9.5" fill="#6E5A2A" fill-opacity=".6"/>'
                     f'<circle cx="{f(x)}" cy="{f(y)}" r="8" fill="url(#steen)"/><circle cx="{f(x - 2.4)}" cy="{f(y - 2.6)}" r="2" fill="#FFFFFF"/>')
    # het kristal op ring B (rechterbovenkant) met vier klauwtjes
    gx, gy = bx + R * math.cos(math.radians(-62)), cy + R * math.sin(math.radians(-62))
    for hoek in (45, 135, 225, 315):
        a = math.radians(hoek)
        delen.append(f'<ellipse cx="{f(gx + 33 * math.cos(a))}" cy="{f(gy + 33 * math.sin(a))}" rx="9" ry="14" fill="url(#goudD)" '
                     f'transform="rotate({hoek + 90} {f(gx + 33 * math.cos(a))} {f(gy + 33 * math.sin(a))})"/>')
    delen.append(kristal(gx, gy, 36))
    delen.append(ster4(gx - 18, gy - 22, 30))
    delen.append(ster4(gx + 66, gy + 20, 16, .85))
    delen.append(ster4(ax - 150, cy - 120, 20, .9))
    delen.append(ster4(bx + 170, cy + 150, 17, .9))
    return doc(900, 720, f'<g filter="url(#ds-groot)">{"".join(delen)}</g>')


# ---------------------------------------------------------------------------------------------- voorgrond en bloemen
def pioen_blad(L: float, W: float) -> str:
    """Pioenblad met een gegolfde rand: meerdere zachte bulten langs de bovenkant, breed in het midden."""
    return (f"M0 0C{f(-W * .6)} {f(-L * .1)} {f(-W * .8)} {f(-L * .55)} {f(-W * .54)} {f(-L * .86)}"
            f"Q{f(-W * .42)} {f(-L * 1.0)} {f(-W * .27)} {f(-L * .93)}Q{f(-W * .14)} {f(-L * 1.05)} 0 {f(-L * .96)}"
            f"Q{f(W * .15)} {f(-L * 1.06)} {f(W * .29)} {f(-L * .94)}Q{f(W * .43)} {f(-L * 1.0)} {f(W * .54)} {f(-L * .86)}"
            f"C{f(W * .8)} {f(-L * .55)} {f(W * .6)} {f(-L * .1)} 0 0Z")


def pioen(rnd: random.Random, tone: str, R: float = 100, open_: float = 1.0) -> str:
    """Een pioen van boven: zes ringen gegolfde bladen met schaduw op de ring eronder, een donkere voet per blad, een warme rand
    van licht, een diepe kelk en een kransje meeldraden. Zachter en rijker van toon dan de roos: geen witte vlakken."""
    s = R / 100
    ringen = [(9, 100, 96, 9, 0), (8, 86, 88, 6, 20), (8, 72, 76, 4, 8), (7, 58, 64, 2, 30), (6, 44, 50, 1, 12), (5, 30, 34, 0, 36)]
    delen = []
    for i, (n, L, W, r0, off) in enumerate(ringen, start=1):
        petals = []
        for k in range(n):
            a = off + 360 * k / n + rnd.uniform(-9, 9)
            sc = rnd.uniform(.9, 1.08)
            Lk, Wk = L * sc * s, W * sc * s * (.84 + .16 * open_)
            facing = (math.sin(math.radians(a)) * -0.62 + (-math.cos(math.radians(a))) * -0.78)
            licht, donker = max(0.0, facing) * .26, max(0.0, -facing) * .34
            pad = pioen_blad(Lk, Wk)
            petals.append(
                f'<g transform="rotate({f(a)}) translate(0 {f(-r0 * s)})">'
                f'<path d="{pad}" fill="url(#r-pioen-{min(i, 5)})"/>'
                f'<path d="{pad}" fill="url(#pioen-voet)"/>'
                f'<path d="{pad}" fill="#FFF8E6" fill-opacity="{f(licht)}"/><path d="{pad}" fill="#241A10" fill-opacity="{f(donker)}"/>'
                f'<path d="M{f(-Wk * .1)} {f(-Lk * .12)}Q{f(rnd.uniform(-5, 5) * s)} {f(-Lk * .5)} {f(rnd.uniform(-4, 4) * s)} {f(-Lk * .84)}" stroke="#3A2C1C" stroke-opacity=".16" stroke-width="{f(1.3 * s)}" fill="none" stroke-linecap="round"/>'
                f'<path d="M{f(-Wk * .5)} {f(-Lk * .88)}Q{f(-Wk * .26)} {f(-Lk * 1.0)} 0 {f(-Lk * .96)}Q{f(Wk * .26)} {f(-Lk * 1.0)} {f(Wk * .5)} {f(-Lk * .88)}" stroke="#FFF1CC" stroke-opacity="{f(.34 + licht)}" stroke-width="{f(1.8 * s)}" fill="none" stroke-linecap="round" filter="url(#lip)"/>'
                f'</g>')
        delen.append(f'<g filter="url(#ds)">{"".join(petals)}</g>')
        if i == 3:
            delen.append(f'<circle r="{f(50 * s)}" fill="url(#kelk-pioen)"/>')
    delen.append(f'<circle r="{f(13 * s)}" fill="url(#h-pioen)"/>')
    for _ in range(16):
        a, r = rnd.uniform(0, 360), rnd.uniform(5, 14) * s
        delen.append(f'<circle cx="{f(r * math.cos(math.radians(a)))}" cy="{f(r * math.sin(math.radians(a)))}" r="{f(1.5 * s)}" fill="#E2C57A" fill-opacity=".85"/>')
    return "".join(delen)


mb.roos = lambda rnd, tone, R=100, open_=1.0: pioen(rnd, "pioen", R, open_)


def blad_donker(L: float, W: float, tint: str = "bladD") -> str:
    """Groot, donker blad met een dun champagne nerfje (fluweelachtig, nauwelijks glans)."""
    adern = "".join(f"M0 {f(-L * t)}Q{f(s * W * .32)} {f(-L * (t + .08))} {f(s * W * .74)} {f(-L * (t + .22))}" for t in (.14, .3, .46, .62) for s in (-1, 1))
    return (f'<path d="M0 0C{f(-W * .96)} {f(-L * .2)} {f(-W * .84)} {f(-L * .76)} 0 {f(-L)}C{f(W * .84)} {f(-L * .76)} {f(W * .96)} {f(-L * .2)} 0 0Z" fill="url(#{tint})"/>'
            f'<path d="M0 {f(-L * .03)}V{f(-L * .94)}" stroke="#D8C486" stroke-opacity=".55" stroke-width="{f(max(1.2, W * .02))}" fill="none"/>'
            f'<path d="{adern}" stroke="#D8C486" stroke-opacity=".2" stroke-width="{f(max(.8, W * .012))}" fill="none"/>'
            f'<path d="M{f(-W * .22)} {f(-L * .12)}Q{f(-W * .6)} {f(-L * .5)} {f(-W * .1)} {f(-L * .92)}" stroke="#9CD6BE" stroke-opacity=".14" stroke-width="{f(W * .16)}" fill="none" stroke-linecap="round"/>')


def orb(x: float, y: float, r: float, o: float = 1.0) -> str:
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="url(#orb)" opacity="{f(o)}"/>'


def voor_scene(kant: str) -> str:
    """Onscherpe voorgrond (diepteonscherpte): donkere bladeren, twee ivoren rozen en zachte lichtbolletjes. Canvas 800x1100."""
    rnd = random.Random(61 if kant == "links" else 62)
    s = 1 if kant == "links" else -1
    x0 = 120 if kant == "links" else 680
    bladeren = []
    for L, a, dx, dy, t in ((640, -34, 40, 1060, "bladD"), (560, -12, 190, 1100, "bladD2"), (520, -64, 20, 780, "bladD2"), (600, 18, 330, 1110, "bladD"),
                            (420, -48, 90, 540, "bladD"), (480, 40, 440, 1090, "bladD2")):
        bladeren.append(plaats(blad_donker(L, L * .4, t), x0 + s * (dx - 120), dy, s * a))
    rozen = [plaats(f'<g filter="url(#ds)">{pioen(rnd, "pioen", r / 2)}</g>', x0 + s * (px - 120), py, 0, 1, .92)
             for px, py, r in ((250, 880, 380), (110, 640, 250))]
    orbs = [orb(x0 + s * (px - 120), py, r, o) for px, py, r, o in ((60, 300, 48, .34), (330, 520, 70, .24), (210, 160, 34, .3), (420, 760, 54, .22), (30, 880, 30, .34))]
    # Bladeren onscherp (9), pioenen iets minder onscherp (6) en een stap donkerder, zodat de bladlagen zichtbaar blijven en ze niet krijtwit zijn.
    body = (f'<g filter="url(#vervaag9)"><g filter="url(#ds-groot)">{"".join(bladeren)}</g></g>'
            f'<g filter="url(#pioen-voor)">{"".join(rozen)}</g>{"".join(orbs)}')
    extra = ('<filter id="vervaag9" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="9"/></filter>'
             '<filter id="pioen-voor" x="-10%" y="-10%" width="120%" height="120%" color-interpolation-filters="sRGB">'
             '<feColorMatrix type="matrix" values=".8 0 0 0 0  0 .83 0 0 0  0 0 .78 0 0  0 0 0 1 0"/><feGaussianBlur stdDeviation="6"/></filter>')
    return doc(800, 1100, body, extra=extra)


def bloemen_scene(kant: str) -> str:
    """Een hoog bloemstuk in een stenen urn (scherp, middenlaag): ivoren rozen, eucalyptus, gipskruid en donkere bladeren. Canvas 700x800."""
    rnd = random.Random(71 if kant == "links" else 72)
    s = 1 if kant == "links" else -1
    mx = 350
    urn = ('<defs><linearGradient id="urnsteen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2E4A42"/><stop offset=".4" stop-color="#6E8F83"/><stop offset=".7" stop-color="#42635A"/>'
           '<stop offset="1" stop-color="#1E3631"/></linearGradient></defs>'
           f'<g filter="url(#ds-groot)"><path d="M{mx - 120} 790H{mx + 120}L{mx + 100} 740H{mx - 100}Z" fill="url(#urnsteen)"/>'
           f'<path d="M{mx - 88} 740C{mx - 150} 700 {mx - 150} 640 {mx - 70} 610H{mx + 70}C{mx + 150} 640 {mx + 150} 700 {mx + 88} 740Z" fill="url(#urnsteen)"/>'
           f'<path d="M{mx - 84} 612H{mx + 84}" stroke="#D8C486" stroke-opacity=".6" stroke-width="3"/><path d="M{mx - 120} 690H{mx + 120}" stroke="#D8C486" stroke-opacity=".35" stroke-width="2"/>'
           f'<path d="M{mx - 52} 700C{mx - 30} 660 {mx - 30} 640 {mx - 10} 626" stroke="#FFFFFF" stroke-opacity=".16" stroke-width="22" fill="none" stroke-linecap="round"/></g>')
    r = [("euca", mx - 20, 640, 420, -16, ""), ("euca", mx + 40, 640, 380, 24, ""), ("gips", mx, 630, 400, 8, ""),
         ("blad", mx - 90, 620, 190, -64, "licht"), ("blad", mx + 100, 630, 180, 62, ""), ("blad", mx - 20, 520, 150, -18, ""),
         ("roos", mx - 70, 470, 230, 12, "ivoor"), ("roos", mx + 80, 520, 200, -24, "ivoor"), ("roos", mx, 360, 190, 30, "ivoor"),
         ("knop", mx + 120, 420, 120, 36, "ivoor"), ("parel", mx - 20, 540, 8, 0, ""), ("parel", mx + 60, 430, 7, 0, ""), ("parel", mx - 100, 400, 7, 0, "")]
    bloemen = mb.cluster(rnd, r, 700, 800)
    bloemen = f'<g filter="url(#pioen-mid)">{bloemen}</g>'
    if s < 0:
        bloemen = f'<g transform="translate(700 0) scale(-1 1)">{bloemen}</g>'
    return doc(700, 800, bloemen + (f'<g transform="translate(700 0) scale(-1 1)">{urn}</g>' if s < 0 else urn),
               extra='<filter id="pioen-mid" x="-5%" y="-5%" width="110%" height="110%" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values=".9 0 0 0 0  0 .92 0 0 0  0 0 .88 0 0  0 0 0 1 0"/></filter>')


def prisma(x: float, y: float, L: float, W: float, rot: float, o: float = 1.0) -> str:
    """Een kristalprisma van opzij: drie lange facetten en een afgeknotte punt van drie facetten, doorzichtig (de achtergrond schijnt
    erdoor), met heldere ribben, een schuine breking in het midden en een zweempje goud en cyaan langs de rand (kleurdispersie)."""
    h, kt, tip = W / 2, -L * .66, -L
    tx = h * .06

    def P(*pts):
        return "M" + "L".join(f"{f(a)} {f(b)}" for a, b in pts) + "Z"
    facetten = [
        (P((-h, 0), (-h * .32, 0), (-h * .32, kt), (-h, kt)), "url(#kr-l)"),
        (P((-h * .32, 0), (h * .36, 0), (h * .36, kt), (-h * .32, kt)), "url(#kr-m)"),
        (P((h * .36, 0), (h, 0), (h, kt), (h * .36, kt)), "url(#kr-r)"),
        (P((-h, kt), (-h * .32, kt), (tx, tip)), "url(#kr-tl)"),
        (P((-h * .32, kt), (h * .36, kt), (tx, tip)), "url(#kr-tm)"),
        (P((h * .36, kt), (h, kt), (tx, tip)), "url(#kr-tr)"),
    ]
    delen = "".join(f'<path d="{d}" fill="{v}"/>' for d, v in facetten)
    omtrek = P((-h, 0), (h, 0), (h, kt), (tx, tip), (-h, kt))
    ribben = (f'<path d="M{f(-h * .32)} 0V{f(kt)}M{f(h * .36)} 0V{f(kt)}M{f(-h * .32)} {f(kt)}L{f(tx)} {f(tip)}M{f(h * .36)} {f(kt)}L{f(tx)} {f(tip)}M{f(-h)} {f(kt)}H{f(h)}" '
              f'stroke="#FFFFFF" stroke-opacity=".7" stroke-width=".9" fill="none"/>'
              f'<path d="M{f(-h * .12)} {f(kt * .92)}L{f(h * .26)} {f(kt * .2)}" stroke="#FFFFFF" stroke-opacity=".55" stroke-width="1.2" stroke-linecap="round"/>'
              f'<path d="M{f(h * .5)} {f(kt * .85)}L{f(h * .78)} {f(kt * .3)}" stroke="#FFFFFF" stroke-opacity=".3" stroke-width=".9" stroke-linecap="round"/>')
    dispersie = (f'<path d="{omtrek}" fill="none" stroke="#7FE0D0" stroke-opacity=".32" stroke-width="1.3" transform="translate(.9 .4)"/>'
                 f'<path d="{omtrek}" fill="none" stroke="#F2D58E" stroke-opacity=".34" stroke-width="1.3" transform="translate(-.9 -.4)"/>'
                 f'<path d="{omtrek}" fill="none" stroke="#FFFFFF" stroke-opacity=".85" stroke-width="1"/>')
    voet = f'<ellipse cx="0" cy="{f(W * .05)}" rx="{f(h * 1.1)}" ry="{f(W * .1)}" fill="#02100B" fill-opacity=".35"/>'
    return f'<g transform="translate({f(x)} {f(y)}) rotate({f(rot)})" opacity="{f(o)}">{voet}{delen}{ribben}{dispersie}</g>'


def kristal_defs() -> str:
    def lg(i, a, b, o1, o2, x2=0, y2=1):
        return f'<linearGradient id="{i}" x1="0" y1="0" x2="{x2}" y2="{y2}"><stop offset="0" stop-color="{a}" stop-opacity="{o1}"/><stop offset="1" stop-color="{b}" stop-opacity="{o2}"/></linearGradient>'
    return (lg("kr-l", "#B9E3D8", "#3E7C70", .42, .16, 1, .2) + lg("kr-m", "#FFFFFF", "#BFE3DA", .78, .22) + lg("kr-r", "#8CC9BA", "#2A5C52", .5, .18, -.4, 1)
            + lg("kr-tl", "#E8F7F2", "#9AD0C3", .7, .5, 1, 1) + lg("kr-tm", "#FFFFFF", "#DDF2EC", .92, .6) + lg("kr-tr", "#C9EBE2", "#6FB3A4", .6, .4, -.5, 1))


def kristallen_scene() -> str:
    """Kristalgroepen voor de voorgrond (canvas 1200x700): geslepen prisma's aan de randen van het beeld, een paar verre, onscherpe
    stukken, een zweempje licht en kleine fonkels. Rustig: de tekst in het midden blijft vrij."""
    rnd = random.Random(808)
    dichtbij, ver = [], []
    groepen = [(120, 590, 1.25, -1), (270, 610, .8, -1), (1090, 570, 1.3, 1), (960, 600, .85, 1), (60, 330, .9, -1), (1150, 300, .95, 1)]
    for gx, gy, sc, kant in groepen:
        ver_ = sc < .7
        for k in range(rnd.randint(3, 5)):
            L = rnd.uniform(110, 210) * sc
            W = L * rnd.uniform(.2, .3)
            rot = kant * rnd.uniform(-8, 26) + rnd.uniform(-14, 14)
            stuk = prisma(gx + rnd.uniform(-60, 60) * sc, gy + rnd.uniform(-20, 40) * sc, L, W, rot, 1 if not ver_ else .8)
            (ver if ver_ else dichtbij).append(stuk)
    licht = [orb(rnd.uniform(80, 1120), rnd.uniform(80, 620), rnd.uniform(40, 80), rnd.uniform(.04, .1)) for _ in range(6)]
    fonkels = [ster4(rnd.uniform(30, 1170), rnd.uniform(30, 670), rnd.uniform(6, 14), rnd.uniform(.4, .8)) for _ in range(12)]
    body = (f'<g filter="url(#ver-blur)">{"".join(ver)}</g><g filter="url(#ds)">{"".join(dichtbij)}</g>{"".join(licht)}{"".join(fonkels)}')
    return doc(1200, 700, body, extra=kristal_defs() + '<filter id="ver-blur" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="3.2"/></filter>')


def blad_rand_scene() -> str:
    """Donker bladwerk voor de randen van de hoofdstukken (canvas 520x640): groot blad met champagne nerven en eucalyptus."""
    rnd = random.Random(909)
    bl = [plaats(blad_donker(L, L * .42, t), x, y, a) for L, a, x, y, t in
          ((520, -24, 80, 640, "bladD"), (440, 10, 230, 650, "bladD2"), (420, -58, 30, 430, "bladD2"), (360, 30, 360, 640, "bladD"), (300, -42, 150, 360, "bladD"))]
    ec = plaats(bb.euca(rnd, 360), 120, 600, -30)
    return doc(520, 640, f'<g filter="url(#ds-groot)">{"".join(bl)}{ec}</g>')


# ---------------------------------------------------------------------------------------------- opdrachten
def jobs():
    return [
        ("wereld-donker", wereld(False), 1600, 900, 82),
        ("wereld-licht", wereld(True), 1600, 900, 82),
        ("stralen", stralen(), 1400, 900, 70),
        ("ring", ring_scene(), 900, 720, 90),
        ("voor-links", omzetten(voor_scene("links")), 800, 1100, 76),
        ("voor-rechts", omzetten(voor_scene("rechts")), 800, 1100, 76),
        ("bloemen-links", omzetten(bloemen_scene("links")), 700, 800, 84),
        ("bloemen-rechts", omzetten(bloemen_scene("rechts")), 700, 800, 84),
        ("kristallen", kristallen_scene(), 1200, 700, 84),
        ("blad-rand", omzetten(blad_rand_scene()), 520, 640, 82),
    ]


def main() -> None:
    gevraagd = set(sys.argv[1:])
    lijst = [j for j in jobs() if not gevraagd or j[0] in gevraagd]
    mb.render(lijst)


if __name__ == "__main__":
    main()
