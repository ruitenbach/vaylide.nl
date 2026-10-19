"""Beeld bij "Jullie verhaal verdient iets bijzonders" (homepage), stap 2: de scène rond de envelop met de kaart Gouden Avond.

Gebruik: .venv/bin/python tools/merkbeelden/maak_op_maat_gouden_avond.py <open.png>
<open.png> komt uit tools/merkbeelden/render_gouden_avond_envelop.cjs (echte envelop-engine met de echte kaart, doorzichtig).
Dit script bouwt er een ton-sur-ton scène omheen, helemaal procedureel (geen AI-beeld): bladschaduwen, een zachte travertijnen sokkel,
een vleug zijde en fijn gipskruid, en schrijft static/img/site/op-maat-gouden-avond.webp (1100x1000), -700.webp (700x636) en
-mobiel.webp (700x720), met doorzichtige randen zodat ze in de crèmekaart op de homepage overlopen.
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

UIT = Path(__file__).resolve().parents[2] / "static/img/site"
SS = 2  # tekenen op dubbele schaal voor gladde randen


def laag(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def schaduw_van(masker, kleur, alpha, blur, dx=0, dy=0):
    """Zachte schaduw met `kleur` (RGB) uit een L-masker; RGB overal gevuld zodat vervagen geen grijze rand geeft."""
    s = Image.new("RGBA", masker.size, kleur + (0,))
    s.putalpha(masker.point(lambda v: int(v * alpha)))
    s = s.filter(ImageFilter.GaussianBlur(blur))
    if dx or dy:
        s = ImageChops.offset(s, dx, dy)
    return s


def bladschaduwen(w, h, rng):
    """Zachte schaduw van bladeren die van rechtsboven in beeld hangen."""
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for (x0, y0, x1, y1, n, ls) in ((w * 1.02, -h * .02, w * .52, h * .30, 15, h * .085), (w * .98, h * .12, w * .70, h * .52, 10, h * .07),
                                    (w * .30, -h * .03, w * .06, h * .16, 7, h * .06)):
        for i in range(n):
            t = i / (n - 1)
            x = x0 + (x1 - x0) * t + math.sin(t * 3) * w * .015
            y = y0 + (y1 - y0) * t + math.sin(t * 2.4) * h * .02
            ang = math.atan2(y1 - y0, x1 - x0) + (1.0 if i % 2 else -1.0) * (.9 + rng.random() * .4)
            ln = ls * (1.05 - .5 * t) * (.8 + rng.random() * .4)
            pts = []
            for k in range(-10, 11):
                u = k / 10
                wd = ln * .30 * (1 - u * u) ** .85
                pts.append((u, wd))
            poly = [(x + (u + 1) * ln / 2 * math.cos(ang) - wd * math.sin(ang), y + (u + 1) * ln / 2 * math.sin(ang) + wd * math.cos(ang)) for u, wd in pts]
            poly += [(x + (u + 1) * ln / 2 * math.cos(ang) + wd * math.sin(ang), y + (u + 1) * ln / 2 * math.sin(ang) - wd * math.cos(ang)) for u, wd in reversed(pts)]
            d.polygon(poly, fill=255)
        d.line([(x0, y0), (x1, y1)], fill=255, width=SS * 2)
    return schaduw_van(m, (96, 68, 36), .17, 9 * SS)


def sokkel(w, h, cx, cy, rx, ry, dikte, rng):
    """Zachte travertijnen sokkel (ronde plaat): bovenvlak met fijne adering, zijkant met cilinderschaduw en een slagschaduw."""
    uit = laag(w, h)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse((cx - rx * 1.04, cy + dikte - ry * .4, cx + rx * 1.04, cy + dikte + ry * 1.5), fill=255)
    uit.alpha_composite(schaduw_van(m, (84, 58, 28), .42, 26 * SS, 0, 10 * SS))
    # zijkant
    zm = Image.new("L", (w, h), 0)
    zd = ImageDraw.Draw(zm)
    zd.ellipse((cx - rx, cy + dikte - ry, cx + rx, cy + dikte + ry), fill=255)
    zd.rectangle((cx - rx, cy, cx + rx, cy + dikte), fill=255)
    xs = np.linspace(-1, 1, w)[None, :].repeat(h, 0)
    zijde = np.clip(1 - .22 * np.abs(xs) ** 2.2 - .10 * (xs > 0), 0, 1)
    kl = np.array([218, 204, 180])[None, None, :] * zijde[..., None]
    zij = Image.fromarray(kl.clip(0, 255).astype("uint8"), "RGB").convert("RGBA")
    zij.putalpha(zm)
    uit.alpha_composite(zij)
    # bovenvlak met adering
    tm = Image.new("L", (w, h), 0)
    ImageDraw.Draw(tm).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    ruis = np.array(Image.fromarray((np.random.RandomState(7).rand(h // 8 + 1, w // 8 + 1) * 255).astype("uint8")).resize((w, h), Image.BICUBIC), dtype=float) / 255
    ruis2 = np.array(Image.fromarray((np.random.RandomState(9).rand(h // 24 + 1, w // 24 + 1) * 255).astype("uint8")).resize((w, h), Image.BICUBIC), dtype=float) / 255
    yy, xx = np.mgrid[0:h, 0:w]
    ader = np.abs(np.sin((xx * .006 + yy * .011) + ruis2 * 7.0)) ** 14
    top = np.array([240, 231, 214])[None, None, :] * np.ones((h, w, 1))
    glans = np.clip(1 - ((xx - cx + rx * .25) / rx) ** 2 * .5 - ((yy - cy) / ry) ** 2 * .5, 0, 1)
    top = top * (.965 + .035 * glans[..., None]) * (1 - .035 * ruis[..., None]) - 6 * ader[..., None]
    tp = Image.fromarray(top.clip(0, 255).astype("uint8"), "RGB").convert("RGBA")
    tp.putalpha(tm)
    uit.alpha_composite(tp)
    ImageDraw.Draw(uit).arc((cx - rx, cy - ry, cx + rx, cy + ry), 0, 180, fill=(252, 247, 236, 200), width=SS * 2)
    return uit


def zijde(w, h, vorm, rng):
    """Een vleug satijn: golvende plooien uit een hoogtekaart, belicht van linksboven, in ivoor en champagne."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    u = (xx / w) * .9 + (yy / h) * .55
    hoogte = (np.sin(u * 17 + np.sin(yy / h * 5.3) * 1.6) * .55 + np.sin(u * 7.3 + 1.3 + np.sin(xx / w * 4.1) * 1.2) * .9 + np.sin(u * 31 + yy / h * 9) * .12)
    gy, gx = np.gradient(hoogte)
    licht = np.clip(.5 + (-gx * .8 - gy * .6) * 9, 0, 1)
    spec = np.clip((licht - .66) / .34, 0, 1) ** 2.2
    basis = np.array([232, 218, 190]) + (np.array([249, 243, 230]) - np.array([232, 218, 190])) * licht[..., None]
    basis = basis * (1 - .10 * (1 - licht[..., None])) + 14 * spec[..., None]
    img = Image.fromarray(basis.clip(0, 255).astype("uint8"), "RGB").convert("RGBA")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon(vorm, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.2 * SS))
    img.putalpha(m)
    uit = laag(w, h)
    uit.alpha_composite(schaduw_van(m, (84, 58, 28), .38, 16 * SS, -8 * SS, -4 * SS))
    uit.alpha_composite(img)
    return uit


def gipskruid(w, h, takken, rng):
    """Fijn gipskruid: dunne, vertakte stelen met kleine, romige bloempjes en knopjes."""
    stelen = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(stelen)
    bloemen = []

    def tak(x, y, hoek, lengte, diep):
        n = 7
        pts = [(x, y)]
        a = hoek
        for _ in range(n):
            a += rng.uniform(-.13, .13)
            x += math.cos(a) * lengte / n
            y += math.sin(a) * lengte / n
            pts.append((x, y))
        sd.line(pts, fill=255, width=max(1, round(SS * (1.7 if diep < 2 else 1.1))), joint="curve")
        if diep >= 3:
            bloemen.append((x, y, rng.uniform(.8, 1.15)))
            return
        for k in range(2, n, 3):
            bx, by = pts[k]
            for side in (-1, 1):
                if rng.random() < .7:
                    tak(bx, by, a + side * rng.uniform(.42, .85), lengte * rng.uniform(.5, .66), diep + 1)
        tak(x, y, a + rng.uniform(-.2, .2), lengte * .6, diep + 1)

    for (x, y, hoek, lengte) in takken:
        tak(x, y, hoek, lengte, 0)
    uit = laag(w, h)
    uit.alpha_composite(schaduw_van(stelen, (70, 50, 24), .32, 4 * SS, 5 * SS, 7 * SS))
    st = Image.new("RGBA", (w, h), (146, 134, 100, 0))
    st.putalpha(stelen)
    uit.alpha_composite(st)
    d = ImageDraw.Draw(uit)
    fm = Image.new("L", (w, h), 0)
    fd = ImageDraw.Draw(fm)
    for (x, y, s) in bloemen:
        r = 5.0 * SS * s
        for k in range(5):
            a = k * 2 * math.pi / 5 + rng.uniform(0, 1)
            fd.ellipse((x + math.cos(a) * r * .62 - r * .5, y + math.sin(a) * r * .62 - r * .5, x + math.cos(a) * r * .62 + r * .5, y + math.sin(a) * r * .62 + r * .5), fill=255)
    uit.alpha_composite(schaduw_van(fm, (70, 50, 24), .30, 3 * SS, 4 * SS, 6 * SS))
    uit.alpha_composite(Image.composite(Image.new("RGBA", (w, h), (252, 249, 242, 255)), laag(w, h), fm))
    for (x, y, s) in bloemen:
        r = 5.0 * SS * s
        d.ellipse((x - r * .17, y - r * .17, x + r * .17, y + r * .17), fill=(212, 184, 128, 255))
        for k in range(5):
            a = k * 2 * math.pi / 5 + .6
            d.line([(x, y), (x + math.cos(a) * r * .95, y + math.sin(a) * r * .95)], fill=(226, 212, 186, 130), width=1)
    return uit


def zegelschaduw(env):
    """Zachte, warme slagschaduw van het lakzegel op het papier (zegel wordt herkend aan de wijnrode kleur)."""
    a = np.asarray(env).astype(int)
    zegel = ((a[..., 0] - a[..., 1]) > 30) & (a[..., 0] < 205) & (a[..., 3] > 200)
    zm = Image.fromarray((zegel * 255).astype("uint8")).filter(ImageFilter.MaxFilter(3))
    w, h = env.size
    sh = Image.new("L", (w, h), 0)
    sh.paste(zm.filter(ImageFilter.GaussianBlur(h * .012)), (round(h * .004), round(h * .012)))
    sh2 = Image.new("L", (w, h), 0)
    sh2.paste(zm.filter(ImageFilter.GaussianBlur(h * .004)), (round(h * .002), round(h * .005)))
    al = (np.asarray(sh).astype(float) * .45 + np.asarray(sh2).astype(float) * .35).clip(0, 255) * (a[..., 3] / 255)
    lagen = Image.new("RGBA", (w, h), (70, 28, 20, 0))
    lagen.putalpha(Image.fromarray(al.astype("uint8")))
    uit = env.copy()
    uit.alpha_composite(lagen)
    herstel = Image.composite(env, uit, zm.filter(ImageFilter.GaussianBlur(.8)))
    return herstel


def roos(doek, W, H, img, breed, x, y_onder, hoek=0):
    """Plaatst een vrijgestelde rozengroep met zachte contactschaduw (x = linkerrand, y_onder = onderrand)."""
    r = img.resize((round(breed * SS), round(img.height * breed * SS / img.width)), Image.LANCZOS)
    if hoek:
        r = r.rotate(hoek, resample=Image.BICUBIC, expand=True)
    px, py = round(x * SS), round(y_onder * SS - r.height)
    m = Image.new("L", (W, H), 0)
    m.paste(r.getchannel("A"), (px, py))
    doek.alpha_composite(schaduw_van(m, (74, 50, 24), .22, 30 * SS, 4 * SS, 18 * SS))
    doek.alpha_composite(schaduw_van(m, (60, 40, 20), .16, 7 * SS, 1 * SS, 4 * SS))
    doek.alpha_composite(r, (px, py))


def scene(breed, hoog, env, env_h, env_cx, plint, silk, bloem, seed):
    W, H = breed * SS, hoog * SS
    rng = random.Random(seed)
    doek = laag(W, H)
    doek.alpha_composite(bladschaduwen(W, H, rng))
    cx, cy, rx, ry, dk = (v * SS for v in plint)
    doek.alpha_composite(sokkel(W, H, cx, cy, rx, ry, dk, rng))
    # envelop: contactschaduw op de sokkel en de envelop zelf, licht gekanteld
    env = zegelschaduw(env)
    k = env_h * SS / env.height
    e = env.resize((round(env.width * k), round(env.height * k)), Image.LANCZOS).rotate(-2.5, resample=Image.BICUBIC, expand=True)
    ex, ey = round(env_cx * SS - e.width / 2), round(cy + ry * .30 - e.height + 6 * SS)
    for (img, b, x, yo, hk) in bloem[1]:
        roos(doek, W, H, img, b, x, yo, hk)
    cm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(cm).ellipse((ex + e.width * .06, ey + e.height - 30 * SS, ex + e.width * .98, ey + e.height + 34 * SS), fill=255)
    doek.alpha_composite(schaduw_van(cm, (70, 46, 20), .55, 16 * SS, 0, 4 * SS))
    doek.alpha_composite(e, (ex, ey))
    if silk:
        doek.alpha_composite(zijde(W, H, [(x * SS, y * SS) for x, y in silk], rng))
    for (img, b, x, yo, hk) in bloem[0]:
        roos(doek, W, H, img, b, x, yo, hk)
    # zachte overgang naar de crèmekaart aan de linkerrand
    f = np.clip(np.linspace(0, 1, W) / .16, 0, 1) ** 1.5
    t = np.clip(np.linspace(0, 1, H) / .16, 0, 1) ** 1.5
    a = np.array(doek.getchannel("A"), dtype=float) * f[None, :] * t[:, None]
    doek.putalpha(Image.fromarray(a.astype("uint8")))
    return doek.resize((breed, hoog), Image.LANCZOS)


def sla_op(img, naam):
    pad = UIT / naam
    img.save(pad, "WEBP", quality=90, alpha_quality=95, method=6)
    print(naam, img.size, pad.stat().st_size)


GROOT = Image.open(UIT / "rozen-groot.webp").convert("RGBA")
KLEIN = Image.open(UIT / "rozen-klein.webp").convert("RGBA")
bron = Image.open(sys.argv[1]).convert("RGBA")
bron = bron.crop(bron.getchannel("A").point(lambda v: 255 if v > 6 else 0).getbbox())

# Bureaublad: envelop groot en iets naar het midden, sokkel eronder, zijde rechtsonder, gipskruid links en rechts
d = scene(
    1100, 1000, bron, 800, 600, (560, 850, 520, 96, 46),
    None,
    ([(GROOT, 450, 70, 962, 0)], [(KLEIN, 285, 735, 902, 0)]),
    5,
)
sla_op(d, "op-maat-gouden-avond.webp")
sla_op(d.resize((700, 636), Image.LANCZOS), "op-maat-gouden-avond-700.webp")

# Mobiel: dezelfde scène, envelop gecentreerd en groot, gipskruid links, zijde rechtsonder
m = scene(
    700, 720, bron, 560, 355, (350, 612, 330, 66, 34),
    None,
    ([(GROOT, 290, 30, 704, 0)], [(KLEIN, 205, 440, 614, 0)]),
    9,
)
sla_op(m, "op-maat-gouden-avond-mobiel.webp")
