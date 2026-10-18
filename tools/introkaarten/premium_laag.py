#!/usr/bin/env python3
"""Premium laag (licht, nevel, glinsteringen, spaarzame blaadjes) voor Zijden gordijn, Bloesemwaaier, Kerstsprookje en Gouden poort.

Bloesemmeer (het voorbeeld, 18 oktober 2026) is met de hand gemaakt en blijft zoals hij is; de andere vier krijgen dezelfde techniek,
met een eigen identiteit per kaart (plekken in het eindbeeld, kleuren, dichtheid). Het script is herhaalbaar: het vervangt alleen wat tussen de
markeringen staat. Uitleg: docs/INTROKAARTEN.md.

Gebruik (vanuit de projectmap):  python tools/introkaarten/premium_laag.py [slug ...]   en daarna   python manage.py sync_designs --update-manifest

Plekken zijn percentages van het eindbeeld (end.webp, 720 x 1280); in het kader van 9:16 vallen beeld en laag samen.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BEGIN_HTML, END_HTML = "{# premium-laag begin #}", "{# premium-laag einde #}"
BEGIN_CSS, END_CSS = "/* premium-laag begin */", "/* premium-laag einde */"

# glow: x, y, grootte (% van de breedte), kleurtje (rgb), tempo (s), vertraging (s)   twinkle: x, y, grootte (cqw), tempo, vertraging
KAARTEN = {
    "zijden-gordijn": {
        "dichtheid": 0.3,
        "kleuren": {"--fx-1": "#F8DEDA", "--fx-2": "#E9A7AB", "--fx-3": "#D88C97"},
        "effects": {"sfeer": "blaadjes"},
        "licht": "255,214,150",
        "mist": [("far", "33%", "15%", "255,236,214", .30), ("near", "58%", "16%", "255,240,222", .38)],
        "water": {"top": "79%", "hoogte": "18%", "links": "17%", "rechts": "17%", "glint": "255,246,224"},
        "glows": [(30, 44, 30, "255,196,110", 7, 0), (50, 62, 20, "255,226,170", 5, -2), (25, 83, 9, "255,190,100", 3.4, -1), (70, 83, 9, "255,190,100", 4.1, -2.5),
                  (86, 87, 8, "255,190,100", 3.8, -0.5), (61, 52, 8, "255,214,140", 6, -3), (72, 52, 8, "255,214,140", 5.4, -1.2), (80, 53, 7, "255,214,140", 6.6, -4)],
        "twinkles": [(46, 55, 1.4, 5.2, 0), (54, 58, 1.2, 6.1, -2.2), (50, 50, 1.1, 5.6, -4), (62, 46, 1.3, 7, -1), (36, 89, 1.2, 6.4, -3), (56, 92, 1.4, 5.8, -0.6),
                     (63, 86, 1.1, 6.8, -5), (28, 78, 1.1, 7.2, -2)],
    },
    "bloesemwaaier": {
        "dichtheid": 0.8,
        "kleuren": {},
        "effects": {},
        "licht": "255,184,92",
        "mist": [("far", "35%", "17%", "255,226,204", .30), ("near", "46%", "15%", "255,230,212", .42)],
        "water": {"top": "67%", "hoogte": "26%", "links": "40%", "rechts": "0%", "glint": "255,240,214", "zon": "62%"},
        "glows": [(4, 10, 11, "255,176,80", 4.6, 0), (27, 12, 10, "255,176,80", 5.4, -1.8), (4, 40, 11, "255,176,80", 5, -3), (23, 40, 10, "255,176,80", 4.2, -0.7),
                  (31, 52, 9, "255,176,80", 5.8, -2.4), (40, 53, 8, "255,176,80", 4.8, -3.6), (49, 55, 8, "255,176,80", 5.2, -1.1), (57, 53, 8, "255,176,80", 6.2, -4.2),
                  (87, 54, 8, "255,176,80", 4.4, -2), (95, 58, 9, "255,176,80", 5.6, -0.4), (13, 68, 12, "255,170,70", 4.0, -1.5), (72, 27, 30, "255,200,120", 7.5, 0)],
        "twinkles": [(83, 45, 1.3, 5.6, 0), (80, 52, 1.1, 6.4, -2.4), (72, 76, 1.2, 5.2, -1), (75, 84, 1.3, 6.8, -3.5), (69, 90, 1.1, 6, -4.4), (62, 32, 1.1, 7, -2)],
    },
    "kerstsprookje": {
        "dichtheid": 0.6,
        "kleuren": {},
        "effects": {},
        "licht": "255,200,100",
        "mist": [("far", "40%", "16%", "150,176,226", .22), ("near", "58%", "16%", "214,200,170", .20)],
        "water": {"top": "66%", "hoogte": "30%", "links": "0%", "rechts": "0%", "glint": "255,226,160"},
        "glows": [(10, 38, 13, "255,196,96", 4.6, 0), (95, 41, 12, "255,196,96", 5.2, -2), (48, 26, 12, "255,220,140", 5.6, -1.2), (45, 5, 10, "255,214,130", 6.4, -3),
                  (77, 14, 10, "255,214,130", 5.8, -2.6), (82, 52, 15, "255,190,90", 6.8, -1), (48, 56, 26, "255,196,100", 8, -3)],
        "twinkles": [(42, 40, 1.3, 4.6, 0), (52, 36, 1.2, 5.4, -1.6), (46, 47, 1.4, 5, -3), (56, 50, 1.2, 6, -0.8), (40, 55, 1.2, 5.6, -2.4), (50, 60, 1.3, 4.8, -3.8),
                     (36, 46, 1.1, 6.4, -1.1), (58, 42, 1.1, 5.2, -4.4), (30, 52, 1.2, 6.8, -2), (68, 46, 1.1, 5.8, -3.1), (88, 46, 1.2, 6.2, -0.2), (22, 62, 1.1, 5.4, -4.9)],
    },
    "gouden-poort": {
        "dichtheid": 0.18,
        "kleuren": {"--fx-1": "#FFF7E0", "--fx-2": "#F2E0B4", "--fx-3": "#E5C887"},
        "effects": {"sfeer": "blaadjes"},
        "licht": "255,208,120",
        "mist": [("far", "30%", "14%", "255,238,196", .22)],
        "water": {"top": "69%", "hoogte": "14%", "links": "24%", "rechts": "7%", "glint": "255,244,214"},
        "sheen": {"top": "0%", "hoogte": "62%"},
        "glows": [(69, 33, 22, "255,206,120", 7, 0), (51, 27, 14, "255,222,150", 6.2, -2), (15, 48, 8, "255,190,100", 4.6, -1), (86, 48, 8, "255,190,100", 5.2, -2.6),
                  (13, 70, 9, "255,190,100", 5.8, -3.4), (88, 72, 9, "255,190,100", 4.4, -0.8)],
        "twinkles": [(51, 23, 1.2, 6.4, 0), (60, 31, 1.1, 7.2, -3), (44, 31, 1.1, 6.8, -1.6), (24, 14, 1.1, 7.6, -4), (78, 12, 1.1, 7, -2.2), (50, 72, 1.2, 6.2, -3.6)],
    },
}


def html_blok(k) -> str:
    regels = [BEGIN_HTML, '    {# Premium laag (zie docs/INTROKAARTEN.md): decoratief, achter de tekst, alleen als beweging mag. Gemaakt door tools/introkaarten/premium_laag.py. #}',
              '    <div class="fk-fx" aria-hidden="true">']
    for naam, *_ in k["mist"]:
        regels.append(f'      <span class="fk-mist fk-mist--{naam}"></span>')
    if "sheen" in k:
        regels.append('      <span class="fk-sheen"></span>')
    w = k["water"]
    regels.append('      <span class="fk-water"><span class="fk-water__glint fk-water__glint--a"></span><span class="fk-water__glint fk-water__glint--b"></span>'
                  '<span class="fk-water__glint fk-water__glint--c"></span>' + ('<span class="fk-water__sun"></span>' if "zon" in w else "") + "</span>")
    for x, y, s, kleur, t, d in k["glows"]:
        regels.append(f'      <span class="fk-glow" style="--x:{x}%;--y:{y}%;--s:{s}%;--gc:{kleur};--t:{t}s;--d:{d}s"></span>')
    for x, y, s, t, d in k["twinkles"]:
        regels.append(f'      <span class="fk-twinkle" style="--x:{x}%;--y:{y}%;--s:{s}cqw;--t:{t}s;--d:{d}s"></span>')
    regels.append("    </div>")
    regels.append('    {% if v.effects %}<div class="fx-slot" data-fx-slot="page" aria-hidden="true"></div>{% endif %}')
    regels.append("    " + END_HTML)
    return "\n".join(regels) + "\n"


def css_blok(k) -> str:
    w = k["water"]
    mist = "\n".join(
        f'.fk-mist--{n} {{ top: {top}; height: {h}; background: radial-gradient(ellipse 50% 50% at 50% 50%, rgba({kl}, {a}), rgba({kl}, 0) 70%); '
        f'animation: fk-mist-{"far" if n == "far" else "near"} {46 if n == "far" else 34}s ease-in-out infinite alternate; }}'
        for n, top, h, kl, a in k["mist"])
    depth = "\n".join(
        f'  .fx-motion .fk-mist--{n} {{ animation: fk-mist-{n} {46 if n == "far" else 34}s ease-in-out infinite alternate, fk-depth linear both; animation-timeline: auto, scroll(root block); '
        f'animation-range: normal, 0 100svh; --fk-dz: {-10 if n == "far" else -26}px; }}' for n, *_ in k["mist"])
    sheen = ""
    sheen_depth = ""
    if "sheen" in k:
        s = k["sheen"]
        sheen = f'''
/* Een zachte lichtbaan trekt af en toe over de gouden bogen en de koepel (eens per 18 seconden, de rest van de tijd is het rustig). */
.fk-sheen {{ position: absolute; left: 0; right: 0; top: {s["top"]}; height: {s["hoogte"]}; overflow: hidden; }}
.fk-sheen::before {{
  content: ""; position: absolute; top: 0; bottom: 0; left: 0; width: 52%; will-change: transform;
  background: linear-gradient(104deg, rgba(255, 243, 208, 0) 18%, rgba(255, 243, 208, .30) 50%, rgba(255, 243, 208, 0) 82%);
  transform: translateX(-130%) skewX(-8deg); animation: fk-sheen 18s ease-in-out infinite;
}}
@keyframes fk-sheen {{ 0%, 42% {{ transform: translateX(-130%) skewX(-8deg); }} 80%, 100% {{ transform: translateX(270%) skewX(-8deg); }} }}
'''
    zon = ""
    if "zon" in w:
        zon = f'''
.fk-water__sun {{
  position: absolute; left: {w["zon"]}; width: 22%; top: 8%; height: 84%; will-change: transform, opacity;
  background: repeating-linear-gradient(to bottom, rgba(255, 232, 190, 0) 0 7px, rgba(255, 232, 190, .6) 7px 9px, rgba(255, 232, 190, 0) 9px 17px);
  -webkit-mask-image: radial-gradient(ellipse 50% 50% at 50% 38%, #000 18%, transparent 74%); mask-image: radial-gradient(ellipse 50% 50% at 50% 38%, #000 18%, transparent 74%);
  animation: fk-sun 6.5s ease-in-out infinite alternate;
}}
@keyframes fk-sun {{ from {{ opacity: .35; transform: scaleX(.86); }} to {{ opacity: .85; transform: scaleX(1.08); }} }}'''
    gl = w["glint"]
    return f'''{BEGIN_CSS}
/* ---------- Premium laag (voorbeeld Bloesemmeer, doorgetrokken op 18 oktober 2026; eigen plekken en kleuren per kaart) ----------
   Decoratief en achter de tekst (z-index 0; namen en datum liggen op 1), niet aanklikbaar, alleen onder .fx-motion (dus niet bij 'minder
   beweging' of na stilzetten met de knop Beweging). Alleen transform en opacity bewegen. Plekken zijn percentages van end.webp. */
.fk-fx {{ display: none; }}
.fx-motion .fk-fx {{ display: block; position: absolute; inset: 0; z-index: 0; overflow: hidden; pointer-events: none; opacity: 0; transition: opacity 3.2s ease .6s; }}
.fx-motion.is-open .fk-fx, .fx-motion.is-opening-reduced .fk-fx {{ opacity: 1; }}

.fk-mist {{ position: absolute; left: -25%; right: -25%; border-radius: 50%; will-change: transform; }}
{mist}
@keyframes fk-mist-far  {{ from {{ transform: translateX(-4%); }} to {{ transform: translateX(5%); }} }}
@keyframes fk-mist-near {{ from {{ transform: translateX(5%); }} to {{ transform: translateX(-5%); }} }}

.fk-water {{
  position: absolute; left: {w["links"]}; right: {w["rechts"]}; top: {w["top"]}; height: {w["hoogte"]}; overflow: hidden;
  -webkit-mask-image: linear-gradient(to bottom, transparent, #000 16%, #000 70%, transparent); mask-image: linear-gradient(to bottom, transparent, #000 16%, #000 70%, transparent);
}}
.fk-water__glint {{ position: absolute; inset: 0 -12%; opacity: .3; will-change: opacity, transform; }}
.fk-water__glint--a {{
  background-size: 173px 97px;
  background-image: radial-gradient(ellipse 22px 2.7px at 18% 24%, rgba({gl}, .95), transparent), radial-gradient(ellipse 15px 2.1px at 63% 68%, rgba({gl}, .9), transparent), radial-gradient(ellipse 18px 2.4px at 88% 40%, rgba({gl}, .85), transparent);
  animation: fk-glint 5.2s ease-in-out infinite alternate, fk-glint-sway 19s ease-in-out infinite alternate;
}}
.fk-water__glint--b {{
  background-size: 131px 71px;
  background-image: radial-gradient(ellipse 16px 2.2px at 30% 52%, rgba({gl}, .9), transparent), radial-gradient(ellipse 21px 2.5px at 76% 20%, rgba({gl}, .85), transparent);
  animation: fk-glint 7.1s ease-in-out -2.4s infinite alternate, fk-glint-sway 25s ease-in-out -9s infinite alternate-reverse;
}}
.fk-water__glint--c {{
  background-size: 229px 123px;
  background-image: radial-gradient(ellipse 27px 3px at 44% 36%, rgba({gl}, .95), transparent), radial-gradient(ellipse 19px 2.4px at 12% 80%, rgba({gl}, .8), transparent);
  animation: fk-glint 9.3s ease-in-out -5s infinite alternate, fk-glint-sway 31s ease-in-out -14s infinite alternate;
}}
@keyframes fk-glint {{ from {{ opacity: .15; }} to {{ opacity: .95; }} }}
@keyframes fk-glint-sway {{ from {{ transform: translateX(-9px); }} to {{ transform: translateX(9px); }} }}{zon}
{sheen}
/* Warme lichtjes: lantaarns, ramen, kaarsen, de zon. Zacht ademend, nooit tegelijk. */
.fk-glow {{
  position: absolute; left: var(--x); top: var(--y); width: var(--s, 12%); aspect-ratio: 1; translate: -50% -50%; border-radius: 50%; opacity: .2; will-change: opacity, transform;
  background: radial-gradient(circle, rgba(var(--gc, {k["licht"]}), .6), rgba(var(--gc, {k["licht"]}), 0) 66%);
  animation: fk-glow var(--t, 6s) ease-in-out var(--d, 0s) infinite alternate;
}}
@keyframes fk-glow {{ from {{ opacity: .16; transform: scale(.9); }} to {{ opacity: .8; transform: scale(1.08); }} }}
/* Een enkel lichtpuntje dat even oplicht en weer verdwijnt (geen glitter: weinig, klein, ver uit elkaar in tijd). */
.fk-twinkle {{
  position: absolute; left: var(--x); top: var(--y); width: var(--s, 1.2cqw); aspect-ratio: 1; translate: -50% -50%; border-radius: 50%; opacity: 0; will-change: opacity, transform;
  background: radial-gradient(circle, rgba(255, 252, 240, 1) 0 22%, rgba({k["licht"]}, .75) 42%, rgba({k["licht"]}, 0) 72%);
  animation: fk-twinkle var(--t, 5s) ease-in-out var(--d, 0s) infinite;
}}
@keyframes fk-twinkle {{ 0%, 100% {{ opacity: 0; transform: scale(.5); }} 46%, 54% {{ opacity: .95; transform: scale(1.15); }} }}

/* Diepte bij het scrollen: nevel en water schuiven iets sneller omhoog dan het beeld (alleen waar de browser scrollgestuurde animaties kent). */
@supports (animation-timeline: scroll()) {{
{depth}
  .fx-motion .fk-water {{ animation: fk-depth linear both; animation-timeline: scroll(root block); animation-range: 0 100svh; --fk-dz: -38px; }}
}}
@keyframes fk-depth {{ from {{ translate: 0 0; }} to {{ translate: 0 var(--fk-dz, 0px); }} }}
/* De afkorting 'animation' zet de speelstand terug op 'lopend'; daarom staat hij hier nog eens, voor alle lagen (ook de pseudo-elementen). */
.fx-motion .fk-fx *, .fx-motion .fk-fx *::before {{ animation-play-state: var(--fx-play, running); }}

/* Blaadjes en sneeuw over het beeld van de kop: een eigen laag, zelfde sfeer als de pagina, loopt alleen terwijl de kop in beeld is, boven
   de nevel, onder de namen en de datum. Minder deeltjes dan de pagina (--fx-density). */
.fk-frame--hero > .fx-slot {{ z-index: 0; }}
html.inv-{k["slug"]} {{ --fx-density: {k["dichtheid"]}; }}
{END_CSS}
'''


def vervang(tekst: str, begin: str, einde: str, blok: str) -> str:
    """Vervangt wat tussen de markeringen staat (de markeringen zelf zitten in het blok)."""
    patroon = re.compile(re.escape(begin) + r".*?" + re.escape(einde) + r"\n?", re.S)
    return patroon.sub(lambda m: blok, tekst, count=1)


def maak(slug: str) -> None:
    k = dict(KAARTEN[slug], slug=slug)
    map_ = ROOT / "designs" / slug / "v1"
    html_pad, css_pad, man_pad = map_ / "invitation.html", map_ / "style.css", map_ / "manifest.json"
    html = html_pad.read_text(encoding="utf-8")
    anker = re.search(r'<div class="fk-frame fk-frame--hero"[^>]*>\n', html)
    if not anker:
        raise SystemExit(f"{slug}: kop niet gevonden")
    if BEGIN_HTML in html:
        html = vervang(html, BEGIN_HTML, END_HTML, html_blok(k))
    else:
        html = html[:anker.end()] + html_blok(k) + html[anker.end():]
    html_pad.write_text(html, encoding="utf-8")
    css = css_pad.read_text(encoding="utf-8")
    css = vervang(css, BEGIN_CSS, END_CSS, css_blok(k)) if BEGIN_CSS in css else css.rstrip("\n") + "\n\n" + css_blok(k)
    css_pad.write_text(css, encoding="utf-8")
    man = json.loads(man_pad.read_text(encoding="utf-8"))
    man["effects"].update(k["effects"])
    extra = man["effects"].setdefault("extra", [])
    if "scrollwind" not in extra:
        extra.append("scrollwind")
    man["palettes"][0]["vars"].update(k["kleuren"])
    man_pad.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("klaar", slug)


if __name__ == "__main__":
    for slug in (sys.argv[1:] or list(KAARTEN)):
        maak(slug)
