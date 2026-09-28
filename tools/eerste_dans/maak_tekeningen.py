"""Tekeningen voor het ontwerp Eerste dans (designs/eerste-dans/v1/): het bruidspaar, de kroonluchter en de
bloemenslinger. Eigen tekeningen in SVG, zonder verwijzingen naar verlopen (url(#...)), zodat ze vaker op één pagina
kunnen staan. De kleuren van zaal, bloemen en goud komen uit de kleurvariant (CSS-klassen ed-...); het bruidspaar
heeft vaste kleuren: blond haar, een witte bruidsjurk en een zwart pak.

Gebruik: python tools/eerste_dans/maak_tekeningen.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "designs" / "eerste-dans" / "v1"
KOP = "{# Gemaakt door tools/eerste_dans/maak_tekeningen.py; niet met de hand aanpassen. #}\n"

# ------------------------------------------------------------------ het bruidspaar
# De groepen ed-dans, ed-rok en ed-sluier bewegen (alleen met beweging aan, zie style.css).
PAAR = """<svg class="ed-paar__svg" viewBox="60 50 240 384" aria-hidden="true" focusable="false">
<ellipse class="ed-vloerschaduw" cx="166" cy="426" rx="128" ry="9"/>
<g class="ed-dans">
<g class="ed-bruidegom">
<path d="M88 138 Q80 180 84 226 L94 226 Q92 184 98 146 Z" fill="#17171C"/>
<path d="M84 226 Q84 236 90 238 Q96 236 94 226 Z" fill="#EBC6AE"/>
<path d="M94 252 L88 414 L106 414 L114 300 L121 414 L139 414 L136 252 Z" fill="#1B1B20"/>
<path d="M114 300 L114 262" stroke="#101014" stroke-width="1"/>
<path d="M84 413 Q86 407 96 407 L108 409 Q110 415 106 417 L84 417 Z" fill="#0B0B0E"/>
<path d="M117 413 Q119 407 129 407 L144 410 Q146 416 142 417 L117 417 Z" fill="#0B0B0E"/>
<path d="M86 134 Q100 120 119 119 Q139 120 151 134 Q156 168 154 196 Q150 228 146 262 L129 266 L121 234 L109 266 L90 262 Q84 226 84 192 Q83 160 86 134 Z" fill="#202027"/>
<path d="M90 132 Q104 121 119 120" fill="none" stroke="#3A3A45" stroke-width="2" stroke-linecap="round"/>
<path d="M109 123 L119 122 L129 124 L121 170 Z" fill="#F8F6F1"/>
<path d="M107 123 L121 171 L99 150 L104 132 Z" fill="#30303A"/>
<path d="M131 125 L121 171 L139 147 L136 132 Z" fill="#30303A"/>
<path d="M113 129 L119 132 L125 129 L125 136 L119 133 L113 136 Z" fill="#0E0E11"/>
<path d="M134 150 L142 148 L141 153 Z" fill="#F8F6F1"/>
<circle cx="122" cy="192" r="1.6" fill="#0E0E11"/><circle cx="122" cy="206" r="1.6" fill="#0E0E11"/>
<path d="M140 132 Q160 156 174 196 L180 206 L170 212 Q154 178 132 150 Z" fill="#26262E"/>
<path d="M142 134 Q158 152 170 184" fill="none" stroke="#3A3A45" stroke-width="1.4" stroke-linecap="round"/>
<path d="M113 106 L124 106 L125 123 L112 123 Z" fill="#EBC6AE"/>
<ellipse cx="119" cy="88" rx="15" ry="19" fill="#F1D2BC"/>
<ellipse cx="105.5" cy="91" rx="3" ry="5" fill="#E5BDA3"/>
<path d="M103 90 Q98 64 119 62 Q140 62 136 84 Q131 74 121 73 Q113 73 110 80 Q107 84 106 94 Z" fill="#6B4A2E"/>
<path d="M112 66 Q122 62 132 68" fill="none" stroke="#86613F" stroke-width="2" stroke-linecap="round"/>
<path d="M121 88 Q124 90 127 88" fill="none" stroke="#5B3E2B" stroke-width="1.1" stroke-linecap="round"/>
<path d="M132 89 Q134 95 131 98" fill="none" stroke="#D5A386" stroke-width="1"/>
<path d="M125 102 Q128 104 131 102" fill="none" stroke="#B1705F" stroke-width="1.2" stroke-linecap="round"/>
</g>
<g class="ed-bruid">
<path d="M176 78 Q170 112 180 140 Q188 164 182 182 Q198 178 208 160 Q218 132 212 100 Q208 80 200 72 Z" fill="#D2A75E"/>
<g class="ed-sluier">
<path d="M198 70 Q238 98 252 168 Q266 262 290 404 Q252 414 222 406 Q228 300 216 210 Q210 150 194 94 Z" fill="#FFFFFF" opacity=".55"/>
<path d="M204 90 Q232 160 238 250 Q244 330 262 404" fill="none" stroke="#FFFFFF" stroke-width="1.5" opacity=".7"/>
</g>
<g class="ed-rok">
<path d="M170 208 Q146 262 126 330 Q112 380 100 418 Q182 432 270 418 Q256 360 238 300 Q222 250 206 208 Z" fill="#FFFFFF"/>
<path d="M196 212 Q222 262 236 312 Q252 370 270 418 Q246 422 226 423 Q224 350 206 280 Q200 244 196 212 Z" fill="#EFEAE3"/>
<path d="M100 418 Q182 432 270 418" fill="none" stroke="#E2DAD0" stroke-width="2.2"/>
<path d="M178 216 Q162 300 142 420" fill="none" stroke="#E9E3DB" stroke-width="2"/>
<path d="M188 216 Q186 320 180 424" fill="none" stroke="#E9E3DB" stroke-width="2"/>
<path d="M198 216 Q210 300 222 422" fill="none" stroke="#E4DDD4" stroke-width="2"/>
<path d="M124 340 Q170 350 234 336" fill="none" stroke="#F1ECE6" stroke-width="1.5"/>
<g fill="#E4DCD1"><circle cx="118" cy="412" r="1.3"/><circle cx="138" cy="416" r="1.3"/><circle cx="158" cy="419" r="1.3"/><circle cx="178" cy="420" r="1.3"/><circle cx="198" cy="420" r="1.3"/><circle cx="218" cy="419" r="1.3"/><circle cx="238" cy="416" r="1.3"/><circle cx="256" cy="413" r="1.3"/></g>
</g>
<path d="M172 130 Q188 124 202 130 L206 208 Q188 214 170 208 Z" fill="#FFFFFF"/>
<path d="M172 130 Q180 139 187 132 Q194 139 202 130" fill="none" stroke="#E4DDD4" stroke-width="1.4"/>
<g fill="#EAE4DC"><circle cx="182" cy="150" r="1"/><circle cx="192" cy="156" r="1"/><circle cx="184" cy="168" r="1"/><circle cx="194" cy="178" r="1"/><circle cx="182" cy="188" r="1"/></g>
<path class="ed-ceintuur" d="M170 202 Q188 208 206 202 L206 210 Q188 216 170 210 Z"/>
<path d="M168 121 Q187 114 206 121 L204 133 Q187 126 170 133 Z" fill="#F4D9C6"/>
<path d="M182 104 L192 104 L193 121 L181 121 Z" fill="#EDCCB6"/>
<path d="M174 123 Q160 124 148 134 L151 141 Q162 133 177 132 Z" fill="#F4D9C6"/>
<ellipse cx="147" cy="137" rx="5" ry="4" fill="#F4D9C6"/>
<path d="M144 135 L141 138 M146 134 L143 137.5" stroke="#E6C3AE" stroke-width=".8" stroke-linecap="round"/>
<ellipse cx="185" cy="88" rx="13.5" ry="17.5" fill="#F6DDCB"/>
<path d="M170 92 Q164 64 187 64 Q208 64 202 94 Q198 78 188 76 Q177 78 175 98 Z" fill="#E4BD72"/>
<path d="M200 76 Q210 98 204 120 Q214 106 211 86 Z" fill="#E4BD72"/>
<path d="M178 69 Q187 64 196 69" fill="none" stroke="#F5E0A8" stroke-width="2.2" stroke-linecap="round"/>
<g fill="#FFFFFF"><circle cx="198" cy="70" r="2"/><circle cx="202" cy="74" r="1.6"/><circle cx="194" cy="67" r="1.4"/></g>
<path d="M177 88 Q180 90 183 88" fill="none" stroke="#6B4A33" stroke-width="1.1" stroke-linecap="round"/>
<path d="M179 99 Q182 101 185 99" fill="none" stroke="#C4766B" stroke-width="1.3" stroke-linecap="round"/>
<circle cx="191" cy="94" r="3" fill="#F2B7A6" opacity=".45"/>
</g>
</g>
</svg>"""


def kroonluchter() -> str:
    """Kristallen kroonluchter: gouden armen, kaarsjes en druppels (de glinstering doet style.css)."""
    parts = ['<svg class="ed-kroon__svg" viewBox="0 0 200 150" aria-hidden="true" focusable="false">',
             '<path class="ed-goudlijn" d="M100 0 L100 34"/>',
             '<ellipse class="ed-goud" cx="100" cy="40" rx="9" ry="6"/>',
             '<path class="ed-goud" d="M86 44 Q100 66 114 44 Q108 56 100 58 Q92 56 86 44 Z"/>']
    # Armen met kaarsjes.
    for i, x in enumerate((24, 56, 144, 176)):
        up = 70 if i in (0, 3) else 62
        parts.append(f'<path class="ed-goudlijn" d="M100 56 Q{(x + 100) / 2:.0f} {up + 22} {x} {up}"/>')
        parts.append(f'<path class="ed-goud" d="M{x - 6} {up} L{x + 6} {up} L{x + 4} {up + 4} L{x - 4} {up + 4} Z"/>')
        parts.append(f'<rect class="ed-kaars" x="{x - 2}" y="{up - 12}" width="4" height="12" rx="1"/>')
        parts.append(f'<path class="ed-vlam" d="M{x} {up - 21} Q{x + 3} {up - 15} {x} {up - 12} Q{x - 3} {up - 15} {x} {up - 21} Z"/>')
    parts.append('<path class="ed-goudlijn" d="M100 56 L100 92"/>')
    parts.append('<path class="ed-goud" d="M94 92 L106 92 L100 104 Z"/>')
    # Slingers van kristal onder de armen.
    rnd = random.Random(7)
    for x0, x1, sag in ((24, 56, 18), (56, 100, 22), (100, 144, 22), (144, 176, 18)):
        n = 7
        for k in range(1, n):
            t = k / n
            x = x0 + (x1 - x0) * t
            y = 72 + sag * math.sin(math.pi * t)
            parts.append(f'<circle class="ed-kristal" cx="{x:.1f}" cy="{y:.1f}" r="{1.6 + rnd.random() * .8:.1f}"/>')
    # Druppels die naar beneden hangen.
    for i, x in enumerate(range(30, 175, 12)):
        length = 18 + 22 * math.sin(math.pi * (x - 30) / 144)
        top = 76 + 10 * math.sin(math.pi * (x - 30) / 144)
        parts.append(f'<path class="ed-kristaldraad" d="M{x} {top:.1f} L{x} {top + length:.1f}"/>')
        y = top + length
        parts.append(f'<path class="ed-kristal ed-kristal--{i % 3}" d="M{x} {y:.1f} Q{x + 3.5} {y + 5:.1f} {x} {y + 10:.1f} Q{x - 3.5} {y + 5:.1f} {x} {y:.1f} Z"/>')
    parts.append('<path class="ed-kristal ed-kristal--1" d="M100 106 Q106 118 100 130 Q94 118 100 106 Z"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def hortensia(cx: float, cy: float, r: float, rnd: random.Random, cls: str) -> list[str]:
    """Een tros hortensia: veel kleine bloemetjes van vier ronde blaadjes, in twee tinten."""
    out = [f'<circle class="{cls}-schaduw" cx="{cx:.1f}" cy="{cy + r * .12:.1f}" r="{r:.1f}"/>']
    for _ in range(int(r * 1.5)):
        a = rnd.random() * 2 * math.pi
        d = r * math.sqrt(rnd.random()) * .82
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        s = r * (.13 + rnd.random() * .05)
        k = rnd.choice(("", "-2"))
        rot = rnd.random() * math.pi / 2
        for j in range(4):
            b = rot + j * math.pi / 2
            out.append(f'<circle class="{cls}{k}" cx="{x + s * .75 * math.cos(b):.1f}" cy="{y + s * .75 * math.sin(b):.1f}" r="{s * .78:.1f}"/>')
        out.append(f'<circle class="ed-hart" cx="{x:.1f}" cy="{y:.1f}" r="{s * .25:.2f}"/>')
    return out


def roos(cx: float, cy: float, r: float, rnd: random.Random) -> list[str]:
    """Een witte roos van bovenaf: overlappende ronde blaadjes in lagen, naar het hart toe iets donkerder."""
    out = [f'<circle class="ed-roos-schaduw" cx="{cx:.1f}" cy="{cy + r * .12:.1f}" r="{r * 1.02:.1f}"/>']
    for ring, (d, pr, n, cls) in enumerate(((.55, .55, 6, "ed-roos"), (.32, .45, 5, "ed-roos-2"), (.12, .32, 4, "ed-roos-3"))):
        off = rnd.random() * math.pi
        for k in range(n):
            a = off + k * 2 * math.pi / n
            x, y = cx + r * d * math.cos(a), cy + r * d * math.sin(a)
            out.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r * pr:.1f}"/>')
    out.append(f'<circle class="ed-roos-hart" cx="{cx:.1f}" cy="{cy:.1f}" r="{r * .16:.1f}"/>')
    return out


def blad(x: float, y: float, length: float, angle: float, cls: str = "ed-blad") -> str:
    w = length * .38
    return (f'<path class="{cls}" d="M0 0 Q{length * .5:.1f} -{w:.1f} {length:.1f} 0 Q{length * .5:.1f} {w:.1f} 0 0 Z" '
            f'transform="translate({x:.1f} {y:.1f}) rotate({angle:.0f})"/>')


def slinger() -> str:
    """Bloemenslinger voor de boog boven het bruidspaar (breed; ook los te gebruiken als rand)."""
    rnd = random.Random(21)
    parts = ['<svg class="ed-slinger__svg" viewBox="0 0 400 120" aria-hidden="true" focusable="false">']
    # Groene ranken en blaadjes langs de boog.
    for i in range(34):
        t = i / 33
        x = 10 + 380 * t
        y = 30 + 50 * math.sin(math.pi * t) * .5 + rnd.uniform(-8, 8)
        parts.append(blad(x, y, rnd.uniform(14, 24), rnd.uniform(-180, 180), rnd.choice(("ed-blad", "ed-blad-2"))))
    # Hangende ranken met blaadjes.
    for x in (40, 120, 280, 360):
        for k in range(4):
            parts.append(blad(x + rnd.uniform(-4, 4), 60 + k * 12, 12, 70 + rnd.uniform(-40, 40), "ed-blad-2"))
    # Hortensia's en rozen afwisselend.
    for i, (x, y, r) in enumerate(((28, 34, 24), (86, 56, 26), (150, 70, 22), (200, 76, 28), (250, 70, 22), (314, 56, 26), (372, 34, 24))):
        parts += hortensia(x, y, r, rnd, "ed-bloem")
    for x, y, r in ((58, 60, 11), (118, 72, 12), (176, 84, 10), (226, 88, 12), (282, 72, 12), (342, 60, 11), (200, 48, 9)):
        parts += roos(x, y, r, rnd)
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in (("_paar.html", PAAR), ("_kroonluchter.html", kroonluchter()), ("_slinger.html", slinger())):
        (OUT / name).write_text(KOP + svg + "\n", encoding="utf-8", newline="\n")
        print(name, len(svg), "tekens")


if __name__ == "__main__":
    main()
