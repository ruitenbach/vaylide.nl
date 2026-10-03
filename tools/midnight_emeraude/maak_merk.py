"""Het Vaylide-merkteken (de V uit het logo) in champagnegoud, voor het openingsmoment van Midnight Émeraude.

Het logo zelf blijft zoals de eigenaar het aanleverde (static/img/merk/vaylide-v.*, koper-roségoud). Alleen voor het openingsmoment van dit ontwerp
heeft de eigenaar (3 oktober 2026) gevraagd om dezelfde V in champagnegoud, zodat er in de smaragd-kleurwereld geen roze associatie ontstaat.
De vorm, de lichtval en de details blijven gelijk: elke pixel krijgt dezelfde helderheid als in het origineel, maar op een champagnegouden
kleurverloop (donker #6A5521, midden #CDB173, licht #FFF3D2). De doorzichtigheid blijft ongewijzigd.

Gebruik (vanuit de projectmap): python tools/midnight_emeraude/maak_merk.py
Uitvoer: designs/midnight-emeraude/v1/img/merk-v.webp
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BRON = ROOT / "static" / "img" / "merk" / "vaylide-v.webp"
UIT = ROOT / "designs" / "midnight-emeraude" / "v1" / "img" / "merk-v.webp"

# (positie 0..1 in helderheid, kleur)
VERLOOP = [(0.0, (0x4E, 0x3D, 0x16)), (0.30, (0x8F, 0x74, 0x38)), (0.58, (0xCD, 0xB1, 0x73)), (0.82, (0xEB, 0xD7, 0xA0)), (1.0, (0xFF, 0xF6, 0xDA))]


def kleur(t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    for (a, ca), (b, cb) in zip(VERLOOP, VERLOOP[1:]):
        if t <= b:
            f = (t - a) / (b - a)
            return tuple(round(ca[i] + (cb[i] - ca[i]) * f) for i in range(3))  # type: ignore[return-value]
    return VERLOOP[-1][1]


def main() -> None:
    im = Image.open(BRON).convert("RGBA")
    px = im.load()
    waarden = sorted(0.299 * px[x, y][0] + 0.587 * px[x, y][1] + 0.114 * px[x, y][2] for y in range(im.height) for x in range(im.width) if px[x, y][3] > 200)
    laag, hoog = waarden[int(len(waarden) * .02)], waarden[int(len(waarden) * .98)]
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            l = (0.299 * r + 0.587 * g + 0.114 * b - laag) / max(1, hoog - laag)
            px[x, y] = (*kleur(l), a)
    UIT.parent.mkdir(parents=True, exist_ok=True)
    im.save(UIT, "WEBP", quality=94, method=6, alpha_quality=100)
    print(f"{UIT.name}  {im.width}x{im.height}  {UIT.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
