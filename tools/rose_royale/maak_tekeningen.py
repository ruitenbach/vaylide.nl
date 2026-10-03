"""De kleine SVG-onderdelen van Rosé Royale die inline in de pagina staan: de sterren en maan voor de lucht en de drie
roségoud-verlopen die de CSS gebruikt (kaderlijn van de cartouche, het lint met de datum). De grote beelden (rozen, boog, hart,
oranjerie, stralen) maakt tools/rose_royale/maak_beelden.py als WebP.

Gebruik: python tools/rose_royale/maak_tekeningen.py
Uitvoer: designs/rose-royale/v1/_defs.html en _sterren.svg
"""
from __future__ import annotations

import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "designs" / "rose-royale" / "v1"

VERLOPEN = """
<linearGradient id="rr-goud" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8E4F4F"/><stop offset=".2" stop-color="#C98B7E"/><stop offset=".38" stop-color="#F6D3C3"/><stop offset=".52" stop-color="#D9A08F"/><stop offset=".72" stop-color="#A8625E"/><stop offset=".88" stop-color="#F0C3B0"/><stop offset="1" stop-color="#8E4F4F"/></linearGradient>
<linearGradient id="rr-goud-v" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F6D3C3"/><stop offset=".35" stop-color="#C98B7E"/><stop offset=".6" stop-color="#F0C3B0"/><stop offset="1" stop-color="#9A5A57"/></linearGradient>
<linearGradient id="rr-lint-goud" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#E9B6A4"/><stop offset=".3" stop-color="#F8DDD0"/><stop offset=".5" stop-color="#FFF0E8"/><stop offset=".7" stop-color="#F3CDBE"/><stop offset="1" stop-color="#EAB8A6"/></linearGradient>
<radialGradient id="rr-gloed"><stop offset="0" stop-color="#FFE3C2" stop-opacity=".9"/><stop offset=".4" stop-color="#FFC7A6" stop-opacity=".35"/><stop offset="1" stop-color="#FFB49A" stop-opacity="0"/></radialGradient>
"""


def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def defs() -> None:
    html = ('{% comment %}Rosé Royale: de roségoud-verlopen die de CSS gebruikt. Gemaakt met tools/rose_royale/maak_tekeningen.py; niet met de hand aanpassen.{% endcomment %}\n'
            '<svg class="rr-defs" width="0" height="0" aria-hidden="true" focusable="false"><defs>' + VERLOPEN.strip() + "</defs></svg>\n")
    (OUT / "_defs.html").write_text(html, encoding="utf-8")


def sterren(rnd: random.Random) -> None:
    """Sterren en een sikkelmaan voor de lucht (viewBox 0 0 1000 500)."""
    p = ['<circle cx="790" cy="110" r="70" fill="url(#rr-gloed)" opacity=".7"/>',
         '<path d="M790 74a36 36 0 1 0 26 62a30 30 0 1 1-26-62z" fill="#FFF0E6"/>']
    for _ in range(46):
        x, y, r = rnd.uniform(10, 990), rnd.uniform(8, 380), rnd.uniform(.8, 2.1)
        p.append(f'<circle class="rr-ster" cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>')
    (OUT / "_sterren.svg").write_text("".join(p) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    defs()
    sterren(random.Random(919))
    print("klaar: _defs.html, _sterren.svg")


if __name__ == "__main__":
    main()
