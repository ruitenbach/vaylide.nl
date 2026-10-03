"""Maakt de beelden van Rosé Royale V2 (WebP met doorzichtige achtergrond) uit eigen SVG-tekeningen.

De scènes worden hier als SVG opgebouwd (rozen met echte diepte, een roségouden boog als metaal, een hart-sculptuur met
parels en kristallen, een oranjerie met glas, fontein, lantaarns en pad) en met Chromium (Playwright) één keer gerenderd.
De pagina gebruikt alleen de WebP-beelden: goedkoop te tekenen, dus soepel, ook met veel lagen. Vaste seeds.

Gebruik (vanuit de projectmap, Node met Playwright zoals voor de e2e-controles):
    python tools/rose_royale/maak_beelden.py [naam ...]       (zonder namen: alles)
Uitvoer: designs/rose-royale/v1/img/*.webp
"""
from __future__ import annotations

import io
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from beeld_bouwstenen import (blad, euca, f, gipskruid, knop, parel, plaats, roos,  # noqa: E402
                              svg_document)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "designs" / "rose-royale" / "v1" / "img"
RENDER_JS = r"""
const { chromium } = require(process.argv[2]);
const fs = require("fs");
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
  const browser = await chromium.launch();
  for (const job of jobs) {
    const page = await browser.newPage({ viewport: { width: job.w, height: job.h }, deviceScaleFactor: 1 });
    await page.setContent(`<html><body style="margin:0;background:transparent">${fs.readFileSync(job.svg, "utf8")}</body></html>`);
    await page.waitForTimeout(150);
    await page.screenshot({ path: job.png, omitBackground: true, clip: { x: 0, y: 0, width: job.w, height: job.h } });
    await page.close();
  }
  await browser.close();
})();
"""


def zachte_rand(im: Image.Image, links: float = 0, rechts: float = 0, boven: float = 0, onder: float = 0) -> Image.Image:
    """Laat de rand van een beeld zacht uitlopen naar doorzichtig (breedte als aandeel van het beeld), zodat een
    compositie die tegen de rand van het canvas aan komt nooit een harde snede laat zien."""
    w, h = im.size
    a = im.getchannel("A")
    mask = Image.new("L", (w, h), 255)
    px = mask.load()
    for y in range(h):
        for x in range(w):
            k = 1.0
            if links and x < w * links: k = min(k, x / (w * links))
            if rechts and x > w * (1 - rechts): k = min(k, (w - 1 - x) / (w * rechts))
            if boven and y < h * boven: k = min(k, y / (h * boven))
            if onder and y > h * (1 - onder): k = min(k, (h - 1 - y) / (h * onder))
            if k < 1.0: px[x, y] = int(255 * (k * k * (3 - 2 * k)))
    out = im.copy()
    from PIL import ImageChops
    out.putalpha(ImageChops.multiply(a, mask))
    return out


RANDEN = {"rozen-links": dict(links=.07, rechts=.14, boven=.14, onder=.06), "rozen-rechts": dict(links=.14, rechts=.07, boven=.14, onder=.06),
          "rozen-boven": dict(links=.12, rechts=.06, boven=.05, onder=.14),
          "oranjerie-donker": dict(links=.14, rechts=.14, boven=.10, onder=.10), "oranjerie-licht": dict(links=.14, rechts=.14, boven=.10, onder=.10),
          "stralen": dict(links=.18, rechts=.18, boven=.24)}


def render(jobs: list[tuple[str, str, int, int, int]]) -> None:
    """jobs: (naam, svg-tekst, breedte, hoogte, kwaliteit). Rendert alles in één Chromium-sessie naar WebP."""
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        spec = []
        for naam, svg, w, h, _ in jobs:
            (tmp_path / f"{naam}.svg").write_text(svg, encoding="utf-8")
            spec.append({"svg": str(tmp_path / f"{naam}.svg"), "png": str(tmp_path / f"{naam}.png"), "w": w, "h": h})
        (tmp_path / "jobs.json").write_text(__import__("json").dumps(spec), encoding="utf-8")
        (tmp_path / "render.cjs").write_text(RENDER_JS, encoding="utf-8")
        playwright = str(ROOT / "e2e" / "node_modules" / "playwright")
        subprocess.run(["node", str(tmp_path / "render.cjs"), playwright, str(tmp_path / "jobs.json")], check=True)
        for naam, _, w, h, q in jobs:
            im = Image.open(tmp_path / f"{naam}.png").convert("RGBA")
            if naam in RANDEN:
                im = zachte_rand(im, **RANDEN[naam])
            im.save(OUT / f"{naam}.webp", "WEBP", quality=q, method=6, alpha_quality=92)
            print(f"{naam}.webp  {w}x{h}  {(OUT / f'{naam}.webp').stat().st_size // 1024} kB")


def vervaag(body: str, sd: float, w: int, h: int) -> str:
    return (f'<filter id="vervaag" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="{sd}"/></filter>'
            f'<g filter="url(#vervaag)">{body}</g>')


# ---------------------------------------------------------------------------------------------- rozencomposities
def cluster(rnd: random.Random, regels: list, w: int, h: int, sd: float = 0.0, schaduw: bool = True) -> str:
    """regels: (soort, x, y, grootte, hoek, toon). Soorten: euca, gips, blad, knop, roos, parel. Volgorde = diepte."""
    delen = []
    for soort, x, y, g, a, toon in regels:
        if soort == "euca":
            delen.append(plaats(euca(rnd, g), x, y, a))
        elif soort == "gips":
            delen.append(plaats(gipskruid(rnd, g, 5), x, y, a))
        elif soort == "blad":
            delen.append(plaats(blad(g, g * .42, licht=toon == "licht"), x, y, a))
        elif soort == "knop":
            delen.append(plaats(knop(toon, g, rnd), x, y, a))
        elif soort == "roos":
            delen.append(plaats(f'<g filter="url(#korrel)">{roos(rnd, toon, g / 2)}</g>', x, y, a, 1.0, .9))
        elif soort == "parel":
            delen.append(plaats(parel(g, toon == "roze"), x, y, a))
    body = f'<g filter="url(#ds-groot)">{"".join(delen)}</g>' if schaduw else "".join(delen)
    return vervaag(body, sd, w, h) if sd else body


def links_boeket(rnd, sd=0.0, schaal=1.0):
    r = [("gips", 90, 800, 360, -20, ""), ("gips", 300, 860, 330, 24, ""), ("euca", 150, 760, 380, -34, ""), ("euca", 420, 880, 330, 20, ""),
         ("blad", 60, 560, 200, -62, ""), ("blad", 200, 830, 190, 36, "licht"), ("blad", 380, 700, 170, 70, ""), ("blad", 520, 860, 180, 12, "licht"),
         ("blad", 120, 700, 190, -20, "licht"), ("blad", 300, 560, 160, -52, ""), ("knop", 70, 470, 150, -14, "blush"), ("knop", 640, 800, 130, 62, "ivoor"),
         ("knop", 330, 500, 120, 10, "blush"),
         ("roos", 250, 620, 360, 14, "ivoor"), ("roos", 540, 720, 300, -22, "blush"), ("roos", 120, 440, 240, 40, "mauve"),
         ("roos", 420, 470, 230, 70, "roze"), ("roos", 600, 580, 150, 20, "ivoor"), ("roos", 300, 800, 220, -8, "blush"),
         ("parel", 480, 560, 9, 0, ""), ("parel", 190, 520, 8, 0, "roze"), ("parel", 560, 640, 7, 0, ""), ("parel", 380, 640, 8, 0, "roze")]
    return cluster(rnd, [(s, x * schaal, y * schaal, g * schaal, a, t) for s, x, y, g, a, t in r], 900, 900, sd)


def rechts_boeket(rnd, sd=0.0):
    r = [("gips", 560, 640, 330, 22, ""), ("euca", 580, 600, 340, 38, ""), ("euca", 300, 680, 300, -30, ""),
         ("blad", 660, 400, 180, 18, "licht"), ("blad", 330, 640, 170, -58, ""), ("blad", 520, 660, 170, 24, "licht"), ("blad", 640, 520, 160, 48, ""),
         ("blad", 420, 540, 150, -10, "licht"), ("knop", 640, 260, 140, 12, "ivoor"), ("knop", 250, 600, 120, -48, "blush"),
         ("roos", 450, 520, 330, -8, "blush"), ("roos", 270, 620, 220, 30, "ivoor"), ("roos", 610, 380, 210, -34, "mauve"),
         ("roos", 560, 590, 160, 10, "roze"), ("parel", 360, 470, 9, 0, ""), ("parel", 620, 500, 8, 0, "roze"), ("parel", 250, 520, 7, 0, "")]
    return cluster(rnd, r, 700, 700, sd)


def boven_boeket(rnd, sd=0.0):
    r = [("euca", 470, 20, 330, 168, ""), ("gips", 330, 40, 280, 160, ""), ("blad", 540, 190, 170, 160, "licht"), ("blad", 380, 150, 150, 120, ""),
         ("blad", 450, 330, 150, 195, "licht"), ("blad", 270, 120, 140, 105, "licht"), ("knop", 390, 280, 130, 190, "blush"),
         ("roos", 470, 130, 270, 20, "blush"), ("roos", 300, 60, 190, -30, "ivoor"), ("roos", 530, 300, 150, 40, "mauve"), ("parel", 380, 200, 8, 0, "roze")]
    return cluster(rnd, r, 600, 480, sd)


def voor_boeket(rnd, welke: str):
    """Voorgrond: grote, onscherpe rozen en bladeren (diepteonscherpte) die langs de camera schuiven."""
    if welke == "links":
        r = [("blad", 110, 880, 460, -30, ""), ("blad", 380, 980, 420, 20, "licht"), ("blad", 60, 560, 400, -70, "licht"),
             ("roos", 230, 700, 640, 12, "blush"), ("roos", 480, 920, 520, -30, "ivoor"), ("roos", 90, 420, 420, 40, "roze")]
    else:
        r = [("blad", 680, 880, 440, 30, ""), ("blad", 330, 1000, 400, -24, "licht"), ("blad", 740, 560, 380, 70, "licht"),
             ("roos", 560, 740, 600, -14, "ivoor"), ("roos", 310, 940, 500, 24, "blush"), ("roos", 700, 420, 400, -36, "mauve")]
    return cluster(rnd, r, 800, 1100, 0.0, schaduw=False)


def rankje_scene(rnd):
    """Horizontaal rozenrankje (1200x260) voor de overgangen tussen hoofdstukken."""
    r = []
    for x, a in ((70, -76), (160, -84), (250, -96), (350, -100), (850, 100), (950, 96), (1040, 84), (1130, 76)):
        r.append(("blad", x, 150 + abs(600 - x) * .06, 110, a, "licht" if x % 160 < 90 else ""))
    r += [("euca", 300, 150, 150, -98, ""), ("euca", 900, 150, 150, 98, ""), ("gips", 430, 150, 130, -80, ""), ("gips", 770, 150, 130, 80, "")]
    r += [("knop", 470, 140, 80, -62, "ivoor"), ("knop", 730, 138, 80, 62, "blush")]
    r += [("roos", 500, 150, 120, 10, "ivoor"), ("roos", 700, 148, 120, -16, "blush"), ("roos", 600, 132, 160, 30, "mauve")]
    return cluster(rnd, r, 1200, 260)


# ---------------------------------------------------------------------------------------------- hoofdlijst
def jobs_rozen(rnd_seed: int = 7):
    rnd = random.Random(rnd_seed)
    jobs = []
    jobs.append(("rozen-links", svg_document(900, 900, links_boeket(random.Random(11))), 900, 900, 82))
    jobs.append(("rozen-rechts", svg_document(700, 700, rechts_boeket(random.Random(12))), 700, 700, 82))
    jobs.append(("rozen-boven", svg_document(600, 480, boven_boeket(random.Random(13))), 600, 480, 82))
    jobs.append(("voor-links", svg_document(800, 1100, vervaag(voor_boeket(random.Random(14), "links"), 11, 800, 1100)), 800, 1100, 74))
    jobs.append(("voor-rechts", svg_document(800, 1100, vervaag(voor_boeket(random.Random(15), "rechts"), 11, 800, 1100)), 800, 1100, 74))
    jobs.append(("rankje", svg_document(1200, 260, rankje_scene(random.Random(16))), 1200, 260, 84))
    jobs.append(("knop", svg_document(200, 260, plaats(knop("blush", 200, random.Random(1)), 100, 230)), 200, 260, 86))
    return jobs


BOUWERS = {"rozen": jobs_rozen}



# ---------------------------------------------------------------------------------------------- metaal: roségoud
METAAL = (
    '<filter id="metaal" x="-12%" y="-12%" width="124%" height="124%" color-interpolation-filters="sRGB">'
    '<feGaussianBlur in="SourceAlpha" stdDeviation="{sd}" result="b"/>'
    '<feSpecularLighting in="b" surfaceScale="{ss}" specularConstant="1.3" specularExponent="36" lighting-color="#FFF1E8" result="spec">'
    '<feDistantLight azimuth="235" elevation="46"/></feSpecularLighting>'
    '<feComposite in="spec" in2="SourceAlpha" operator="in" result="specIn"/>'
    '<feDiffuseLighting in="b" surfaceScale="{ss}" diffuseConstant="1.08" lighting-color="#FFFFFF" result="diff">'
    '<feDistantLight azimuth="235" elevation="55"/></feDiffuseLighting>'
    '<feComposite in="SourceGraphic" in2="diff" operator="arithmetic" k1="1.2" k2="0" k3="0" k4="0" result="shaded"/>'
    '<feComposite in="shaded" in2="SourceAlpha" operator="in" result="s2"/>'
    '<feBlend in="specIn" in2="s2" mode="screen"/></filter>')


def hart_punten(cx: float, cy: float, s: float, n: int = 240):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s, cy + y * s))
    return pts


def pad_van(pts) -> str:
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"


def langs_pad(pts, afstand: float, voorbij: float = 0.0):
    """Punten op gelijke afstand langs een gesloten lijn."""
    lengtes = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        lengtes.append(lengtes[-1] + math.hypot(x1 - x0, y1 - y0))
    totaal = lengtes[-1]
    n = max(3, round(totaal / afstand))
    out = []
    for k in range(n):
        d = (totaal * k / n + voorbij) % totaal
        j = next(i for i in range(len(lengtes) - 1) if lengtes[i + 1] >= d)
        t = (d - lengtes[j]) / max(1e-6, lengtes[j + 1] - lengtes[j])
        (x0, y0), (x1, y1) = pts[j], pts[(j + 1) % len(pts)]
        out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    return out


def punt_in_hart(x: float, y: float, pts) -> bool:
    """Ligt (x, y) binnen de hartvorm (veelhoek, met de even-oneven regel)?"""
    binnen = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            binnen = not binnen
        j = i
    return binnen


def kristal(x: float, y: float, r: float, kleur: tuple[str, str, str]) -> str:
    """Een gefacetteerd steentje met glans (een achthoek met facetten)."""
    licht, mid, donker = kleur
    pts = [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(22, 382, 45)]
    tinten = [licht, mid, licht, donker, donker, mid, licht, mid]
    facetten = []
    for i in range(8):
        a, b = pts[i], pts[(i + 1) % 8]
        facetten.append(f'<path d="M{f(x)} {f(y)}L{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}Z" fill="{tinten[i]}"/>')
    tafel = [(x + r * .46 * math.cos(math.radians(a)), y + r * .46 * math.sin(math.radians(a))) for a in range(22, 382, 45)]
    return (f'<g><circle cx="{f(x)}" cy="{f(y)}" r="{f(r * 1.06)}" fill="#8E4F4F" fill-opacity=".55"/>{"".join(facetten)}'
            f'<path d="{pad_van(tafel)}" fill="#FFFFFF" fill-opacity=".55"/><circle cx="{f(x - r * .3)}" cy="{f(y - r * .34)}" r="{f(r * .18)}" fill="#FFFFFF"/></g>')


def ster4(x: float, y: float, r: float, o: float = .95) -> str:
    q = r * .22
    return (f'<path d="M{f(x)} {f(y - r)}L{f(x + q)} {f(y - q)}L{f(x + r)} {f(y)}L{f(x + q)} {f(y + q)}L{f(x)} {f(y + r)}L{f(x - q)} {f(y + q)}L{f(x - r)} {f(y)}L{f(x - q)} {f(y - q)}Z" '
            f'fill="#FFFFFF" fill-opacity="{o}"/>')


def schakel(x: float, y: float, rot: float, w: float = 15, h: float = 26) -> str:
    return (f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(w / 2)}" ry="{f(h / 2)}" transform="rotate({f(rot)} {f(x)} {f(y)})" fill="none" '
            f'stroke="url(#roseGoud)" stroke-width="5.2"/>')


def hart_scene() -> str:
    """Het hero-object: een roségouden hartsculptuur aan een kettinkje, met een parelrij, een veld van fonkelende kristallen,
    een grote geslepen steen in het midden en druppels onderaan. Eigen ontwerp. Canvas 660x860, ketting boven (330, 0)."""
    rnd = random.Random(2024)
    cx, cy, sc = 330, 338, 17.2
    buiten = hart_punten(cx, cy, sc)
    binnen = hart_punten(cx, cy + 4, sc * .79)
    kader = pad_van(buiten) + pad_van(binnen[::-1])
    delen = []
    for i in range(7):
        delen.append(schakel(330, 12 + i * 20, 0 if i % 2 else 90, 14, 28))
    delen.append('<circle cx="330" cy="140" r="17" fill="none" stroke="url(#roseGoud)" stroke-width="8"/>')
    delen.append(f'<g filter="url(#metaal)"><path d="{kader}" fill="url(#roseGoud)" fill-rule="evenodd"/></g>')
    delen.append(f'<clipPath id="veld"><path d="{pad_van(binnen)}"/></clipPath>')
    delen.append(f'<path d="{pad_van(binnen)}" fill="#B76A78"/>')
    stenen = []
    tinten = [("#FFFFFF", "#F7DCDD", "#C9959C"), ("#FFF2E6", "#F1D2B8", "#C49F86"), ("#FFE3E6", "#F2B3BE", "#B9677A"),
              ("#FDEAF0", "#E9B8D0", "#A9678A"), ("#FFFFFF", "#F4E6E8", "#B9A1A8")]
    r = 8.2
    stap = r * 1.92
    rij = 0
    y = cy - 12 * sc
    while y < cy + 17 * sc:
        x = cx - 17 * sc + (stap / 2 if rij % 2 else 0)
        while x < cx + 17 * sc:
            if punt_in_hart(x, y, binnen):
                jx, jy = rnd.uniform(-.8, .8), rnd.uniform(-.8, .8)
                rr = r * rnd.uniform(.9, 1.05)
                t = tinten[rnd.randrange(len(tinten))]
                stenen.append(f'<circle cx="{f(x + jx)}" cy="{f(y + jy)}" r="{f(rr * 1.04)}" fill="#7C3F4F" fill-opacity=".6"/>'
                              f'<circle cx="{f(x + jx)}" cy="{f(y + jy)}" r="{f(rr)}" fill="{t[1]}"/>'
                              f'<path d="M{f(x + jx - rr)} {f(y + jy)}A{f(rr)} {f(rr)} 0 0 1 {f(x + jx + rr)} {f(y + jy)}" fill="{t[0]}" fill-opacity=".75"/>'
                              f'<circle cx="{f(x + jx - rr * .3)}" cy="{f(y + jy - rr * .34)}" r="{f(rr * .2)}" fill="#FFFFFF"/>')
            x += stap
        y += stap * .87
        rij += 1
    delen.append(f'<g clip-path="url(#veld)">{"".join(stenen)}</g>')
    delen.append(f'<g clip-path="url(#veld)"><path d="M0 0H{cx + 40}L{cx - 120} {cy + 300}H0Z" fill="#FFFFFF" fill-opacity=".10"/></g>')
    for x, y in langs_pad(hart_punten(cx, cy + 2, sc * .895), 33):
        delen.append(plaats(parel(12.5), x, y))
    delen.append(kristal(cx, cy + 12, 56, ("#FFFFFF", "#F6D3DA", "#D08FA3")))
    delen.append(ster4(cx - 24, cy - 22, 24))
    for x, y, rr in ((cx - 150, cy - 90, 20), (cx + 140, cy - 40, 15), (cx + 60, cy + 150, 17), (cx - 90, cy + 120, 12), (cx + 20, cy - 120, 12)):
        delen.append(ster4(x, y, rr, .95))
    ty = cy + 17 * sc
    delen.append(f'<circle cx="{cx}" cy="{f(ty + 6)}" r="11" fill="none" stroke="url(#roseGoud)" stroke-width="6"/>')
    for i in range(3):
        delen.append(schakel(cx, ty + 30 + i * 18, 0 if i % 2 == 0 else 90, 11, 20))
    delen.append(f'<g filter="url(#ds)"><path d="M{cx} {f(ty + 82)}C{cx - 32} {f(ty + 108)} {cx - 28} {f(ty + 150)} {cx} {f(ty + 160)}C{cx + 28} {f(ty + 150)} {cx + 32} {f(ty + 108)} {cx} {f(ty + 82)}Z" fill="url(#parel)"/>'
                  f'<ellipse cx="{cx - 9}" cy="{f(ty + 110)}" rx="6" ry="12" fill="#FFFFFF" fill-opacity=".85" transform="rotate(14 {cx - 9} {f(ty + 110)})"/></g>')
    for dx in (-52, 52):
        delen.append(f'<path d="M{cx} {f(ty + 6)}Q{cx + dx * .6} {f(ty + 30)} {cx + dx} {f(ty + 62)}" fill="none" stroke="url(#roseGoud)" stroke-width="3.4"/>')
        delen.append(kristal(cx + dx, ty + 74, 13, ("#FFFFFF", "#F6D3DA", "#D08FA3")))
    return svg_document(660, 860, f'<g filter="url(#ds-groot)">{"".join(delen)}</g>', extra_defs=METAAL.format(sd=6, ss=8))


# ---------------------------------------------------------------------------------------------- boog (metaal)
def boog_scene() -> str:
    """De roségouden boog (canvas 600x900): een dubbele lijst van metaal met een parelrij en voetstukken."""
    buiten = "M24 872V300A276 276 0 0 1 576 300V872"
    binnen = "M52 872V300A248 248 0 0 1 548 300V872"
    delen = [f'<g filter="url(#metaal)"><path d="{buiten}" fill="none" stroke="url(#roseGoud-v)" stroke-width="20"/>'
             f'<path d="{binnen}" fill="none" stroke="url(#roseGoud-v)" stroke-width="9"/>'
             '<rect x="8" y="864" width="68" height="30" rx="4" fill="url(#roseGoud)"/><rect x="524" y="864" width="68" height="30" rx="4" fill="url(#roseGoud)"/>'
             '<rect x="14" y="852" width="56" height="14" rx="3" fill="url(#roseGoud)"/><rect x="530" y="852" width="56" height="14" rx="3" fill="url(#roseGoud)"/></g>']
    pts = []
    for i in range(61):
        t = math.pi * i / 60
        pts.append((300 - 262 * math.cos(t), 300 - 262 * math.sin(t)))
    for y in range(312, 850, 30):
        pts += [(38, y), (562, y)]
    for x, y in pts:
        delen.append(plaats(parel(6.4), x, y))
    delen.append('<g filter="url(#metaal)"><circle cx="300" cy="26" r="17" fill="none" stroke="url(#roseGoud)" stroke-width="8"/></g>')
    return svg_document(600, 900, f'<g filter="url(#ds)">{"".join(delen)}</g>', extra_defs=METAAL.format(sd=2.4, ss=6))


# ---------------------------------------------------------------------------------------------- lichtstralen
def stralen_scene() -> str:
    """Zachte stralen vanuit één punt omhoog, voor het licht van de oranjerie (canvas 1400x900)."""
    rnd = random.Random(31)
    defs = ('<filter id="zacht" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="9"/></filter>'
            '<linearGradient id="straal" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#FFE3C2" stop-opacity=".75"/>'
            '<stop offset=".6" stop-color="#FFD0B0" stop-opacity=".22"/><stop offset="1" stop-color="#FFC4A6" stop-opacity="0"/></linearGradient>')
    delen = []
    ox, oy = 700, 760
    for _ in range(15):
        a = math.radians(-90 + rnd.uniform(-52, 52))
        w = rnd.uniform(.012, .05)
        L = 900
        x1, y1 = ox + L * math.cos(a - w), oy + L * math.sin(a - w)
        x2, y2 = ox + L * math.cos(a + w), oy + L * math.sin(a + w)
        delen.append(f'<path d="M{ox - 10} {oy}L{f(x1)} {f(y1)}L{f(x2)} {f(y2)}L{ox + 10} {oy}Z" fill="url(#straal)" opacity="{f(rnd.uniform(.45, 1))}"/>')
    return svg_document(1400, 900, f'<g filter="url(#zacht)">{"".join(delen)}</g>', extra_defs=defs)


def jobs_object():
    return [("hart", hart_scene(), 660, 860, 88), ("boog", boog_scene(), 600, 900, 88), ("stralen", stralen_scene(), 1400, 900, 70)]


BOUWERS["object"] = jobs_object



# ---------------------------------------------------------------------------------------------- de oranjerie in de tuin
def oranj_defs(lit: bool) -> str:
    glas = (("#FFF6DE", "#FFDCA8", "#FFB887", "#F59474") if lit else ("#5A4568", "#3E2E50", "#2C2040", "#231936"))
    muur = (("#7C5A6C", "#59404F", "#3E2A39") if lit else ("#6B4B5E", "#4A3446", "#33222F"))
    return (
        f'<linearGradient id="glas" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{glas[0]}"/><stop offset=".4" stop-color="{glas[1]}"/>'
        f'<stop offset=".78" stop-color="{glas[2]}"/><stop offset="1" stop-color="{glas[3]}"/></linearGradient>'
        f'<linearGradient id="muur" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{muur[0]}"/><stop offset=".5" stop-color="{muur[1]}"/><stop offset="1" stop-color="{muur[2]}"/></linearGradient>'
        '<linearGradient id="steen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8E6C78"/><stop offset=".5" stop-color="#C9A8A4"/><stop offset="1" stop-color="#8E6C78"/></linearGradient>'
        f'<radialGradient id="koepel" cx="50%" cy="85%" r="85%"><stop offset="0" stop-color="{"#FFE3B8" if lit else "#E4A793"}"/>'
        f'<stop offset=".5" stop-color="{"#D99A82" if lit else "#9C6377"}"/><stop offset="1" stop-color="{"#7C4D5F" if lit else "#4A2D40"}"/></radialGradient>'
        f'<linearGradient id="water" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{"#F7C9A8" if lit else "#EFB9A5"}"/><stop offset=".3" stop-color="#B7778A"/>'
        '<stop offset="1" stop-color="#4A2C43"/></linearGradient>'
        '<linearGradient id="pad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#EBCCC4"/><stop offset=".5" stop-color="#C9A4A6"/><stop offset="1" stop-color="#8E6877"/></linearGradient>'
        '<radialGradient id="gloed"><stop offset="0" stop-color="#FFE7BF" stop-opacity=".95"/><stop offset=".35" stop-color="#FFC38A" stop-opacity=".42"/><stop offset="1" stop-color="#FFB27A" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="vervaag" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset=".6" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<mask id="reflmasker"><rect x="0" y="560" width="1600" height="340" fill="url(#vervaag)"/></mask>'
        '<filter id="rimpel" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.004 0.07" numOctaves="2" seed="8" result="t"/>'
        '<feDisplacementMap in="SourceGraphic" in2="t" scale="22" xChannelSelector="R" yChannelSelector="G" result="d"/><feGaussianBlur in="d" stdDeviation="1.6"/></filter>'
        '<filter id="mist" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter>'
        '<filter id="zachtje" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>')


def boograam(x: float, top: float, w: float, h: float, lit: bool, kruis: bool = True) -> str:
    """Een hoog boograam met glas, sprosjes, waaier en lijst. x = midden."""
    l, r = x - w / 2, x + w / 2
    boog = top + w / 2
    pad = f"M{f(l)} {f(top + h)}V{f(boog)}A{f(w / 2)} {f(w / 2)} 0 0 1 {f(r)} {f(boog)}V{f(top + h)}Z"
    o = [f'<path d="{pad}" fill="url(#glas)"/>']
    if lit:
        # warm licht in het raam en een kroonluchter-silhouet
        o.append(f'<ellipse cx="{f(x)}" cy="{f(top + h * .42)}" rx="{f(w * .46)}" ry="{f(h * .3)}" fill="#FFF3D6" fill-opacity=".55" filter="url(#zachtje)"/>')
        cy = top + h * .22
        o.append(f'<g fill="#6A3B2F" fill-opacity=".55"><path d="M{f(x)} {f(top + 6)}V{f(cy)}"/><rect x="{f(x - w * .2)}" y="{f(cy)}" width="{f(w * .4)}" height="3" rx="1.5"/>'
                 f'<rect x="{f(x - w * .13)}" y="{f(cy + 6)}" width="{f(w * .26)}" height="3" rx="1.5"/><circle cx="{f(x - w * .2)}" cy="{f(cy - 5)}" r="2"/><circle cx="{f(x + w * .2)}" cy="{f(cy - 5)}" r="2"/><circle cx="{f(x)}" cy="{f(cy - 7)}" r="2.4"/></g>')
    else:
        o.append(f'<path d="M{f(l + w * .1)} {f(top + h)}L{f(x + w * .1)} {f(boog - w * .2)}L{f(x + w * .28)} {f(boog - w * .1)}L{f(l + w * .34)} {f(top + h)}Z" fill="#FFFFFF" fill-opacity=".07"/>')
    if kruis:
        o.append(f'<path d="M{f(x)} {f(top + 2)}V{f(top + h)}M{f(l)} {f(top + h * .52)}H{f(r)}M{f(l)} {f(top + h * .76)}H{f(r)}" stroke="#2B1A27" stroke-width="2.6" fill="none"/>')
        o.append(f'<path d="M{f(l)} {f(boog)}L{f(x)} {f(top + 4)}L{f(r)} {f(boog)}" stroke="#2B1A27" stroke-width="1.6" fill="none"/>')
    o.append(f'<path d="{pad}" fill="none" stroke="#2B1A27" stroke-width="4"/><path d="{pad}" fill="none" stroke="#F3B9A4" stroke-opacity=".28" stroke-width="1.4" transform="translate(-1.6 -1.4)"/>')
    return "".join(o)


def gebouw(lit: bool) -> str:
    p = []
    wand = "url(#muur)"
    kleur_rand = "#F6C2AC"
    # vleugels, middenbouw, trommel
    for x0, x1 in ((150, 630), (970, 1450)):
        p.append(f'<rect x="{x0}" y="384" width="{x1 - x0}" height="176" fill="{wand}"/>')
        p.append(f'<path d="M{x0 - 8} 384H{x1 + 8}" stroke="{kleur_rand}" stroke-opacity=".6" stroke-width="3"/><rect x="{x0 - 8}" y="384" width="{x1 - x0 + 16}" height="12" fill="#3A2536"/>')
        # balustrade
        p.append(f'<rect x="{x0 - 4}" y="366" width="{x1 - x0 + 8}" height="5" fill="#3A2536"/>')
        for x in range(x0, x1, 15):
            p.append(f'<rect x="{x}" y="371" width="6" height="14" fill="#3A2536"/>')
        for x in (x0 - 2, x1 - 10):
            p.append(f'<path d="M{x} 366l10 0l-2 -22l-6 0z" fill="#3E2A39"/><circle cx="{x + 5}" cy="338" r="9" fill="#46303F"/><path d="M{x + 1} 336Q{x + 5} 330 {x + 9} 336" stroke="{kleur_rand}" stroke-opacity=".6" fill="none"/>')
    p.append(f'<rect x="560" y="296" width="480" height="264" fill="{wand}"/><rect x="552" y="286" width="496" height="14" fill="#3A2536"/>'
             f'<path d="M552 286H1048" stroke="{kleur_rand}" stroke-opacity=".7" stroke-width="3"/>')
    for x in range(560, 1040, 15):
        p.append(f'<rect x="{x}" y="270" width="6" height="16" fill="#3A2536"/>')
    p.append(f'<rect x="548" y="268" width="504" height="5" fill="#3A2536"/>')
    p.append(f'<rect x="640" y="214" width="320" height="58" fill="{wand}"/><rect x="632" y="208" width="336" height="9" fill="#3A2536"/>')
    # koepel
    koepel = "M640 214C640 116 716 76 800 76C884 76 960 116 960 214Z"
    p.append(f'<path d="{koepel}" fill="url(#koepel)"/>')
    ribben = "".join(f"M{x} 214Q{x + (800 - x) * .2} 112 800 76" for x in range(640, 961, 40))
    p.append(f'<path d="{ribben}" stroke="#FFE0C8" stroke-opacity=".38" stroke-width="2.4" fill="none"/>')
    p.append('<path d="M652 168Q800 138 948 168M644 196Q800 170 956 196M664 140Q800 112 936 140" stroke="#FFE0C8" stroke-opacity=".28" stroke-width="2" fill="none"/>')
    p.append(f'<path d="{koepel}" fill="none" stroke="{kleur_rand}" stroke-opacity=".7" stroke-width="3"/>')
    p.append('<path d="M800 76V46M792 56H808" stroke="#3A2536" stroke-width="4"/><circle cx="800" cy="42" r="7" fill="#F6D0BF"/><circle cx="798" cy="40" r="2" fill="#FFFFFF"/>')
    # ramen: trommel, middenhal, vleugels
    for i in range(7):
        p.append(boograam(676 + i * 41, 228, 22, 40, lit, False))
    for i in range(5):
        p.append(boograam(640 + i * 80, 322, 58, 232, lit))
    for x0 in (150, 970):
        for i in range(6):
            p.append(boograam(x0 + 40 + i * 80, 412, 48, 140, lit))
    # pilasters en sokkel
    for x in [600 + 80 * i for i in range(6)] + [560, 1040]:
        p.append(f'<rect x="{x - 5}" y="310" width="10" height="250" fill="#FFFFFF" fill-opacity=".05"/><path d="M{x - 5} 310V560" stroke="{kleur_rand}" stroke-opacity=".22" stroke-width="2"/>')
    p.append('<rect x="140" y="552" width="1320" height="14" fill="#2F1D2A"/><path d="M140 552H1460" stroke="#F3B9A4" stroke-opacity=".35" stroke-width="2"/>')
    # trap
    for k, (a, b, y) in enumerate(((730, 870, 566), (716, 884, 580), (702, 898, 596))):
        p.append(f'<path d="M{a} {y}H{b}V{y + 14}H{a}Z" fill="url(#steen)"/><path d="M{a} {y}H{b}" stroke="#FBE3D8" stroke-opacity=".7" stroke-width="2"/>')
    return "".join(p)


def lantaarn(x: float, y: float, s: float, lit: bool) -> str:
    """Een lantaarnpaal; (x, y) is de voet. In de gloed staat een warm lichtje."""
    h = 120 * s
    o = [f'<path d="M{f(x)} {f(y)}V{f(y - h)}" stroke="#2B1A27" stroke-width="{f(5 * s)}"/>'
         f'<path d="M{f(x - 9 * s)} {f(y)}H{f(x + 9 * s)}L{f(x + 5 * s)} {f(y - 10 * s)}H{f(x - 5 * s)}Z" fill="#2B1A27"/>']
    top = y - h
    o.append(f'<path d="M{f(x - 13 * s)} {f(top)}L{f(x - 9 * s)} {f(top - 30 * s)}H{f(x + 9 * s)}L{f(x + 13 * s)} {f(top)}Z" fill="{"#FFEDC8" if lit else "#4A3858"}" stroke="#2B1A27" stroke-width="{f(3 * s)}"/>'
             f'<path d="M{f(x - 16 * s)} {f(top - 30 * s)}L{f(x)} {f(top - 46 * s)}L{f(x + 16 * s)} {f(top - 30 * s)}Z" fill="#2B1A27"/><circle cx="{f(x)}" cy="{f(top - 49 * s)}" r="{f(3 * s)}" fill="#F3B9A4"/>')
    if lit:
        o.append(f'<circle cx="{f(x)}" cy="{f(top - 16 * s)}" r="{f(70 * s)}" fill="url(#gloed)"/><circle cx="{f(x)}" cy="{f(top - 16 * s)}" r="{f(5 * s)}" fill="#FFFFFF"/>')
    return "".join(o)


def fontein(cx: float, cy: float, lit: bool) -> str:
    """Een fontein op het pad: ronde bak, middenzuil, schaal en stralen die zachtjes terugvallen."""
    o = [f'<ellipse cx="{cx}" cy="{cy + 8}" rx="148" ry="38" fill="#2B1A27" fill-opacity=".5" filter="url(#zachtje)"/>',
         f'<ellipse cx="{cx}" cy="{cy}" rx="140" ry="36" fill="url(#steen)"/><path d="M{cx - 140} {cy}A140 36 0 0 0 {cx + 140} {cy}V{cy + 18}A140 36 0 0 1 {cx - 140} {cy + 18}Z" fill="#8C6A76"/>'
         f'<ellipse cx="{cx}" cy="{cy - 3}" rx="124" ry="30" fill="url(#water)"/>',
         f'<ellipse cx="{cx}" cy="{cy - 3}" rx="124" ry="30" fill="none" stroke="#FFE7D6" stroke-opacity=".55" stroke-width="2"/>',
         f'<path d="M{cx - 14} {cy - 6}L{cx - 9} {cy - 78}H{cx + 9}L{cx + 14} {cy - 6}Z" fill="url(#steen)"/>',
         f'<ellipse cx="{cx}" cy="{cy - 80}" rx="58" ry="14" fill="url(#steen)"/><path d="M{cx - 58} {cy - 80}Q{cx} {cy - 52} {cx + 58} {cy - 80}Z" fill="#9C7A86"/>'
         f'<ellipse cx="{cx}" cy="{cy - 82}" rx="50" ry="10" fill="url(#water)"/>',
         f'<path d="M{cx - 6} {cy - 82}L{cx - 4} {cy - 112}H{cx + 4}L{cx + 6} {cy - 82}Z" fill="url(#steen)"/><ellipse cx="{cx}" cy="{cy - 114}" rx="22" ry="6" fill="url(#steen)"/>']
    straal = 'stroke="#FFF3EA" stroke-opacity=".78" stroke-linecap="round" fill="none"'
    for dx, hoog, w in ((0, 74, 3.2), (-26, 50, 2.6), (26, 50, 2.6), (-52, 30, 2.2), (52, 30, 2.2)):
        o.append(f'<path d="M{cx} {cy - 118}Q{cx + dx * .55} {cy - 118 - hoog} {cx + dx} {cy - 98}T{cx + dx * 1.6} {cy - 12}" stroke-width="{w}" {straal}/>')
    for dx, dy in ((-60, -48), (-34, -70), (-14, -92), (14, -92), (34, -70), (60, -48), (-80, -22), (80, -22), (0, -126)):
        o.append(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="2.4" fill="#FFF3EA" fill-opacity=".85"/>')
    o.append(f'<ellipse cx="{cx}" cy="{cy - 12}" rx="120" ry="22" fill="#FFF3EA" fill-opacity=".12" filter="url(#mist)"/>')
    if lit:
        o.append(f'<ellipse cx="{cx}" cy="{cy - 6}" rx="120" ry="26" fill="url(#gloed)" opacity=".7"/>')
    return "".join(o)


def haag(x: float, y: float, w: float, h: float, rnd: random.Random) -> str:
    """Een heg of bolvormige taxus in silhouet met rand van licht."""
    o = [f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(w / 2)}" ry="{f(h / 2)}" fill="#2A1823"/>',
         f'<path d="M{f(x - w / 2 + 6)} {f(y - h * .12)}Q{f(x)} {f(y - h * .62)} {f(x + w / 2 - 6)} {f(y - h * .12)}" stroke="#F3B9A4" stroke-opacity=".28" stroke-width="2.4" fill="none"/>']
    for _ in range(int(w / 26)):
        bx, by = x + rnd.uniform(-w * .4, w * .4), y + rnd.uniform(-h * .3, h * .2)
        o.append(f'<circle cx="{f(bx)}" cy="{f(by)}" r="{f(rnd.uniform(3, 5.5))}" fill="#D17A8B" fill-opacity=".78"/>')
    return "".join(o)


def oranjerie_scene(lit: bool) -> str:
    rnd = random.Random(404)
    bld = gebouw(lit)
    delen = []
    # achtergrondbomen/heggen achter het gebouw
    achter = []
    for i in range(14):
        x = 40 + i * 118 + rnd.uniform(-20, 20)
        achter.append(f'<ellipse cx="{f(x)}" cy="{f(500 + rnd.uniform(-10, 20))}" rx="{f(rnd.uniform(60, 96))}" ry="{f(rnd.uniform(60, 96))}" fill="#33202D"/>')
    delen.append(f'<g opacity=".92">{"".join(achter)}</g>')
    delen.append(f'<rect x="0" y="540" width="1600" height="40" fill="#2B1A27"/>')
    # water met spiegeling van het gebouw
    delen.append('<rect x="0" y="566" width="1600" height="334" fill="url(#water)"/>')
    delen.append(f'<g mask="url(#reflmasker)" opacity="{".78" if lit else ".5"}"><g filter="url(#rimpel)"><g transform="translate(0 1132) scale(1 -1)">{bld}</g></g></g>')
    delen.append('<path d="M0 620H1600M0 668H1600M0 724H1600M0 792H1600" stroke="#FFEFE4" stroke-opacity=".10" stroke-width="2"/>')
    # het gebouw zelf
    delen.append(f'<g id="gebouw">{bld}</g>')
    if lit:
        for x in (800, 560, 1040, 330, 1270):
            delen.append(f'<ellipse cx="{x}" cy="470" rx="{240 if x == 800 else 150}" ry="130" fill="url(#gloed)" opacity="{".75" if x == 800 else ".45"}"/>')
    # pad
    delen.append('<path d="M752 612H848L1040 900H560Z" fill="url(#pad)"/>')
    delen.append('<path d="M752 612L560 900M848 612L1040 900" stroke="#FFF1E8" stroke-opacity=".55" stroke-width="3"/>')
    delen.append('<path d="M800 612V900" stroke="#FFF1E8" stroke-opacity=".12" stroke-width="40" filter="url(#zachtje)"/>')
    if lit:
        delen.append('<path d="M752 612H848L1040 900H560Z" fill="url(#gloed)" opacity=".28"/>')
    # lantaarns langs het pad (klein achter, groot vooraan)
    for (x, y, s) in ((704, 632, .46), (896, 632, .46), (640, 704, .7), (960, 704, .7), (560, 806, 1.0), (1040, 806, 1.0)):
        delen.append(lantaarn(x, y, s, lit))
    delen.append(fontein(800, 742, lit))
    # lage heggen en bolvormige taxus voor
    for x, y, w, h in ((190, 800, 250, 150), (430, 850, 200, 120), (1170, 850, 200, 120), (1410, 800, 250, 150), (60, 880, 160, 110), (1540, 880, 160, 110)):
        delen.append(haag(x, y, w, h, rnd))
    # kleine mist over het water
    delen.append('<ellipse cx="800" cy="640" rx="760" ry="38" fill="#FFE9DD" fill-opacity=".16" filter="url(#mist)"/>')
    return svg_document(1600, 900, "".join(delen), extra_defs=oranj_defs(lit))


def jobs_oranjerie():
    return [("oranjerie-donker", oranjerie_scene(False), 1600, 900, 80), ("oranjerie-licht", oranjerie_scene(True), 1600, 900, 80)]


BOUWERS["oranjerie"] = jobs_oranjerie


def main() -> None:
    gevraagd = sys.argv[1:] or list(BOUWERS)
    jobs = []
    for naam in gevraagd:
        jobs += BOUWERS[naam]()
    render(jobs)


if __name__ == "__main__":
    main()
