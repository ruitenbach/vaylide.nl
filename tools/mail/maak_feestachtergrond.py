"""Maakt de feestelijke achtergrond van de leveringsmail: donker goud met stralen, gloed, confetti en sterretjes, in de
stijl van de onthulling op de bedankpagina. Het midden blijft rustig voor de tekst.

    python tools/mail/maak_feestachtergrond.py   ->  static/img/mail/feest-achtergrond.jpg

Mailprogramma's die achtergronden negeren (bijv. Outlook op Windows) tonen de effen kleur #231A12 uit de mail zelf.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 1200, 1320
BASE = (35, 26, 18)
UIT = Path(__file__).resolve().parents[2] / "static" / "img" / "mail" / "feest-achtergrond.jpg"
KLEUREN = [(233, 200, 119), (255, 233, 168), (201, 164, 92), (255, 246, 218), (242, 184, 181), (216, 167, 192), (255, 255, 255)]


def main():
    rnd = random.Random(2026)
    img = Image.new("RGB", (W, H), BASE)

    # Warme gloed van boven.
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    for r in range(760, 0, -8):
        gd.ellipse((W / 2 - r * 1.2, 260 - r, W / 2 + r * 1.2, 260 + r), fill=int(120 * (1 - r / 760) ** 1.6))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img = Image.composite(Image.new("RGB", (W, H), (120, 86, 44)), img, glow)

    # Zachte stralen vanuit het midden bovenaan.
    rays = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(rays)
    cx, cy = W / 2, 250
    for i in range(22):
        a = i / 22 * math.tau
        w = 0.055
        pts = [(cx, cy), (cx + math.cos(a - w) * 1800, cy + math.sin(a - w) * 1800), (cx + math.cos(a + w) * 1800, cy + math.sin(a + w) * 1800)]
        rd.polygon(pts, fill=26)
    rays = rays.filter(ImageFilter.GaussianBlur(6))
    img = Image.composite(Image.new("RGB", (W, H), (190, 150, 90)), img, rays)

    # Confetti en sterretjes, vooral aan de randen (het midden blijft rustig voor de tekst).
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for _ in range(230):
        x = rnd.random() * W
        if abs(x - W / 2) < 300 and rnd.random() < 0.8:
            x = rnd.choice([rnd.uniform(0, W / 2 - 300), rnd.uniform(W / 2 + 300, W)])
        y = rnd.random() * H
        kleur = rnd.choice(KLEUREN) + (rnd.randint(150, 235),)
        kind = rnd.random()
        s = rnd.uniform(5, 13)
        if kind < 0.45:  # strookje
            ang = rnd.uniform(0, math.pi)
            dx, dy = math.cos(ang) * s, math.sin(ang) * s
            ld.line((x - dx, y - dy, x + dx, y + dy), fill=kleur, width=int(rnd.uniform(3, 6)))
        elif kind < 0.8:  # rondje
            r = s / 2.2
            ld.ellipse((x - r, y - r, x + r, y + r), fill=kleur)
        else:  # sterretje
            r = s * 1.1
            ld.polygon([(x, y - r), (x + r * .25, y - r * .25), (x + r, y), (x + r * .25, y + r * .25), (x, y + r),
                        (x - r * .25, y + r * .25), (x - r, y), (x - r * .25, y - r * .25)], fill=kleur)
    for _ in range(120):  # goudstof
        x, y = rnd.random() * W, rnd.random() * H
        r = rnd.uniform(1, 2.4)
        ld.ellipse((x - r, y - r, x + r, y + r), fill=(255, 236, 180, rnd.randint(90, 200)))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

    UIT.parent.mkdir(parents=True, exist_ok=True)
    img.save(UIT, "JPEG", quality=80, optimize=True, progressive=True)
    print(f"Gemaakt: {UIT} ({UIT.stat().st_size // 1024} kB)")


if __name__ == "__main__":
    main()
