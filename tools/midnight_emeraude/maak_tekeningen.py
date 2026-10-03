"""De kleine SVG-onderdelen van Midnight Émeraude die inline in de pagina staan: sterren en maan voor de lucht, de gouden draad met
een ringenmotief als scheiding tussen hoofdstukken (het pad waarlangs de lichtvonk reist), en de goudverlopen voor lijnen en het lint.
De grote beelden maakt tools/midnight_emeraude/maak_beelden.py.

Gebruik: python tools/midnight_emeraude/maak_tekeningen.py
Uitvoer: designs/midnight-emeraude/v1/_defs.html, _sterren.svg, _draad.svg, _ringen.svg
"""
from __future__ import annotations

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "designs" / "midnight-emeraude" / "v1"

VERLOPEN = """
<linearGradient id="me-goud" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7A6330"/><stop offset=".2" stop-color="#C2A55F"/><stop offset=".36" stop-color="#F6E7BC"/><stop offset=".5" stop-color="#D3B66F"/><stop offset=".68" stop-color="#8F7438"/><stop offset=".84" stop-color="#EBD7A0"/><stop offset="1" stop-color="#7A6330"/></linearGradient>
<linearGradient id="me-draad-goud" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#C2A55F" stop-opacity="0"/><stop offset=".18" stop-color="#C2A55F"/><stop offset=".5" stop-color="#F6E7BC"/><stop offset=".82" stop-color="#C2A55F"/><stop offset="1" stop-color="#C2A55F" stop-opacity="0"/></linearGradient>
<radialGradient id="me-vonk"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".28" stop-color="#FFF1CC"/><stop offset=".6" stop-color="#F0D690" stop-opacity=".45"/><stop offset="1" stop-color="#E8C878" stop-opacity="0"/></radialGradient>
<radialGradient id="me-maan"><stop offset="0" stop-color="#FFF8E3" stop-opacity=".6"/><stop offset=".4" stop-color="#F3E3B6" stop-opacity=".18"/><stop offset="1" stop-color="#E8D5A0" stop-opacity="0"/></radialGradient>
"""


def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def defs() -> None:
    html = ('{% comment %}Midnight Émeraude: goudverlopen en de lichtvonk. Gemaakt met tools/midnight_emeraude/maak_tekeningen.py; niet met de hand aanpassen.{% endcomment %}\n'
            '<svg class="me-defs" width="0" height="0" aria-hidden="true" focusable="false"><defs>' + VERLOPEN.strip() + "</defs></svg>\n")
    (OUT / "_defs.html").write_text(html, encoding="utf-8")


def sterren(rnd: random.Random) -> None:
    """Sterren en een maan met maanlicht voor de lucht (viewBox 0 0 1000 500)."""
    p = ['<circle cx="800" cy="104" r="86" fill="url(#me-maan)"/>',
         '<path d="M800 70a34 34 0 1 0 24 58a28 28 0 1 1-24-58z" fill="#FFF6DC"/>']
    for _ in range(52):
        x, y, r = rnd.uniform(10, 990), rnd.uniform(8, 400), rnd.uniform(.7, 2.0)
        p.append(f'<circle class="me-ster" cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>')
    (OUT / "_sterren.svg").write_text("".join(p) + "\n", encoding="utf-8")


def draad() -> None:
    """De gouden draad (viewBox 0 0 600 90): een zachte golf met een klein ringenmotief in het midden. Het pad met klasse
    me-draad__pad is de route van de lichtvonk (MotionPath) en wordt bij het scrollen getekend (stroke-dashoffset)."""
    pad = "M10 46C110 12 190 82 300 46S490 14 590 46"
    p = [f'<path class="me-draad__pad" d="{pad}" fill="none" stroke="url(#me-draad-goud)" stroke-width="1.6" stroke-linecap="round"/>',
         '<path class="me-draad__fijn" d="M60 52C140 30 200 70 300 52S470 30 540 52" fill="none" stroke="url(#me-draad-goud)" stroke-width=".8" opacity=".6"/>']
    # twee kleine, in elkaar grijpende ringen in het midden
    p.append('<g class="me-draad__ringen" fill="none" stroke="url(#me-goud)" stroke-width="2.2"><circle cx="290" cy="46" r="11"/><circle cx="310" cy="46" r="11"/></g>')
    p.append('<circle class="me-draad__steen" cx="320" cy="36" r="2.6" fill="#FFFFFF"/>')
    (OUT / "_draad.svg").write_text("".join(p) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    defs()
    sterren(random.Random(1969))
    draad()
    print("klaar: _defs.html, _sterren.svg, _draad.svg")


if __name__ == "__main__":
    main()
