"""Maakt de logobestanden van Vaylide uit het aangeleverde logo (tools/logo/vaylide-logo-bron.webp).

Het logo blijft precies zoals het is aangeleverd: de V, VAYLIDE en de regel eronder, in dezelfde
kleuren en verhoudingen. Alleen de lege crèmekleurige achtergrond wordt doorzichtig gemaakt en
de lege rand eromheen weggesneden, zodat het logo naadloos op de achtergronden van de site staat.
Op een crèmekleurige achtergrond is het resultaat gelijk aan het origineel.

Alleen voor het tabblad-icoon (16-48 pixels) wordt de V uit het logo gebruikt: het hele logo is
op dat formaat niet leesbaar.

Gebruik (vanuit de projectmap): .venv/bin/python tools/logo/maak_logo.py
Daarna: python manage.py collectstatic (alleen nodig buiten de ontwikkelserver).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
NAAM = "vaylide"
SRC = ROOT / "tools" / "logo" / f"{NAAM}-logo-bron.webp"
IMG = ROOT / "static" / "img"
MERK = IMG / "merk"

# Vanaf welk verschil met de achtergrond (0-255, per kleurkanaal) een beeldpunt meetelt, en vanaf
# welk verschil het helemaal dekt. Daaronder zit alleen ruis van de compressie.
DREMPEL_LAAG = 12
DREMPEL_HOOG = 52
# Ruis verder dan zoveel beeldpunten van het logo af valt weg.
RAND = 4


def achtergrondkleur(im: Image.Image) -> tuple[int, int, int]:
    """Mediaan van een rand van 24 beeldpunten rondom: de effen achtergrond van het origineel."""
    w, h = im.size
    band = 24
    waarden: list[tuple[int, int, int]] = []
    px = im.load()
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            if x < band or y < band or x >= w - band or y >= h - band:
                waarden.append(px[x, y])
    return tuple(sorted(v[i] for v in waarden)[len(waarden) // 2] for i in range(3))


def vrijstaand(im: Image.Image, bg: tuple[int, int, int]) -> Image.Image:
    """Maakt de achtergrond doorzichtig. Halfdoorzichtige randen krijgen hun eigen kleur terug
    (zonder crème erin), zodat samengesteld op de achtergrondkleur het origineel ontstaat."""
    r, g, b = im.split()
    verschil = ImageChops.lighter(
        ImageChops.lighter(r.point(lambda v: max(bg[0] - v, 0)), g.point(lambda v: max(bg[1] - v, 0))),
        b.point(lambda v: max(bg[2] - v, 0)),
    )
    span = DREMPEL_HOOG - DREMPEL_LAAG
    alpha = verschil.point(lambda v: 0 if v <= DREMPEL_LAAG else min(255, round((v - DREMPEL_LAAG) * 255 / span)))
    # Losse ruispuntjes ver van het logo weghalen.
    kern = verschil.point(lambda v: 255 if v > 28 else 0).filter(ImageFilter.MaxFilter(2 * RAND + 1))
    alpha = ImageChops.multiply(alpha, kern)

    uit = Image.new("RGBA", im.size)
    bron = im.load()
    a_px = alpha.load()
    u_px = uit.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            a = a_px[x, y]
            if not a:
                continue
            p = bron[x, y]
            if a == 255:
                u_px[x, y] = (*p, 255)
                continue
            f = a / 255
            u_px[x, y] = tuple(max(0, min(255, round(bg[i] + (p[i] - bg[i]) / f))) for i in range(3)) + (a,)
    return uit


def bijsnijden(logo: Image.Image, marge: int) -> Image.Image:
    x0, y0, x1, y1 = logo.getchannel("A").getbbox()
    return logo.crop((max(0, x0 - marge), max(0, y0 - marge), min(logo.width, x1 + marge), min(logo.height, y1 + marge)))


def op_hoogte(im: Image.Image, hoogte: int) -> Image.Image:
    breedte = round(im.width * hoogte / im.height)
    return im.resize((breedte, hoogte), Image.LANCZOS)


def tegel(beeld: Image.Image, maat: int, bg: tuple[int, int, int], vulling: float, hoek: float) -> Image.Image:
    """Beeld gecentreerd op een crèmekleurig vierkant (de kleur van het origineel)."""
    schaal = min(maat * vulling / beeld.width, maat * vulling / beeld.height)
    klein = beeld.resize((max(1, round(beeld.width * schaal)), max(1, round(beeld.height * schaal))), Image.LANCZOS)
    vlak = Image.new("RGBA", (maat, maat), (*bg, 255))
    vlak.alpha_composite(klein, ((maat - klein.width) // 2, (maat - klein.height) // 2))
    if hoek:
        # Afgeronde hoeken, vier keer zo groot getekend voor een zachte rand.
        masker = Image.new("L", (maat * 4, maat * 4), 0)
        ImageDraw.Draw(masker).rounded_rectangle((0, 0, maat * 4 - 1, maat * 4 - 1), radius=round(maat * 4 * hoek), fill=255)
        vlak.putalpha(masker.resize((maat, maat), Image.LANCZOS))
    return vlak


def main() -> None:
    bron = Image.open(SRC).convert("RGB")
    bg = achtergrondkleur(bron)
    logo = vrijstaand(bron, bg)
    MERK.mkdir(parents=True, exist_ok=True)

    # 1. Het hele logo, vrijstaand.
    heel = bijsnijden(logo, marge=6)
    heel.save(ROOT / "tools" / "logo" / f"{NAAM}-logo-vrijstaand.png", optimize=True)
    site = op_hoogte(heel, 240)
    site.save(MERK / f"{NAAM}-logo.webp", quality=90, method=6)
    site.save(MERK / f"{NAAM}-logo.png", optimize=True)

    # 2. De V uit het logo (het deel boven de naam), voor het tabblad-icoon.
    # Rijen met logo erin; de V loopt van de eerste gevulde rij tot de eerste lege rij daarna.
    rijen = logo.getchannel("A").resize((1, logo.height), Image.BOX).tobytes()
    boven = next(y for y, a in enumerate(rijen) if a)
    onder = next(y for y in range(boven, logo.height) if not rijen[y])
    v = bijsnijden(logo.crop((0, boven, logo.width, onder)), marge=0)
    for maat in (32, 48):
        tegel(v, maat, bg, vulling=0.86, hoek=0.22).save(IMG / f"favicon-{maat}.png", optimize=True)
    tegel(v, 192, bg, vulling=0.72, hoek=0.22).save(IMG / "icon-192.png", optimize=True)

    # 2b. De V als monogram onderaan elke uitnodiging ("merkteken", zoals LV). Uitzondering op de logoregel,
    # met uitdrukkelijk akkoord van de eigenaar (29 september 2026). Dezelfde V, niet hertekend.
    monogram = op_hoogte(bijsnijden(v, marge=2), 160)
    monogram.save(MERK / f"{NAAM}-v.png", optimize=True)
    monogram.save(MERK / f"{NAAM}-v.webp", quality=90, method=6)

    # 3. App-icoon (iPhone/iPad): het hele logo op de crèmekleur, zonder doorzichtigheid.
    tegel(heel, 180, bg, vulling=0.84, hoek=0).convert("RGB").save(IMG / "apple-touch-icon.png", optimize=True)

    for pad in sorted([*MERK.glob(f"{NAAM}-logo.*"), *MERK.glob(f"{NAAM}-v.*"), *IMG.glob("favicon-*.png"), IMG / "icon-192.png", IMG / "apple-touch-icon.png"]):
        with Image.open(pad) as i:
            print(f"{pad.relative_to(ROOT)}  {i.width}x{i.height}  {pad.stat().st_size} bytes")
    print("achtergrond van het origineel:", "#%02X%02X%02X" % bg)


if __name__ == "__main__":
    main()
