"""Maakt static/img/favicon.ico (16, 32 en 48 px) uit de bestaande tabblad-iconen (de V uit het logo); niets wordt hertekend.

Gebruik: python tools/logo/maak_favicon_ico.py
Het bestand wordt op /favicon.ico geserveerd voor browsers en programma's die dat adres opvragen (core.views.favicon).
"""
from pathlib import Path

from PIL import Image

IMG = Path(__file__).resolve().parents[2] / "static" / "img"
bron32 = Image.open(IMG / "favicon-32.png").convert("RGBA")
bron48 = Image.open(IMG / "favicon-48.png").convert("RGBA")
bron16 = bron32.resize((16, 16), Image.LANCZOS)
bron48.save(IMG / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[bron16, bron32])
print("favicon.ico geschreven")
