"""Foto's controleren en tot albummaster verwerken. Los van de betaalverwerking (`processing/`): hier staat geen bestelling, betaling of e-mail.

De invoer is onbetrouwbaar: het opgegeven type klopt niet per se met de inhoud, het bestand kan beschadigd zijn of onredelijk groot.
"""
from __future__ import annotations

import io

from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError

from . import limits


class PhotoRejected(Exception):
    """De foto kan niet worden bewaard. `code` is een korte vaste aanduiding."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def sniff_type(head: bytes) -> str | None:
    """Het echte type uit de eerste bytes, niet uit wat de gast opgaf."""
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def inspect(data: bytes, declared_type: str) -> tuple[int, int]:
    """Controleert type, leesbaarheid en afmetingen. Geeft (breedte, hoogte)."""
    if sniff_type(data[:16]) != declared_type:
        raise PhotoRejected("type")
    try:
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            if width * height > limits.PHOTO_MAX_PIXELS:
                raise PhotoRejected("te_groot")
            if getattr(img, "n_frames", 1) > 1 and img.format != "WEBP":
                raise PhotoRejected("onleesbaar")  # geen geanimeerde of meerlaagse bestanden
            img.verify()
    except PhotoRejected:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise PhotoRejected("onleesbaar")
    return width, height


def make_master(data: bytes) -> bytes:
    """Albummaster: draaien volgens de camera, lange zijde hoogstens 6000 px, sRGB, JPEG, zonder metadata (ook geen locatie)."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.load()
            img = ImageOps.exif_transpose(img)
            profile = img.info.get("icc_profile")
            if profile:
                try:
                    src = ImageCms.ImageCmsProfile(io.BytesIO(profile))
                    img = ImageCms.profileToProfile(img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB"), src, ImageCms.createProfile("sRGB"), outputMode="RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
                except (ImageCms.PyCMSError, OSError, ValueError):
                    pass  # onleesbaar profiel: we gaan uit van sRGB
            if img.mode in ("RGBA", "LA", "P"):
                rgba = img.convert("RGBA")
                flat = Image.new("RGB", rgba.size, (255, 255, 255))
                flat.paste(rgba, mask=rgba.getchannel("A"))
                img = flat
            elif img.mode != "RGB":
                img = img.convert("RGB")
            edge = limits.ALBUM_MASTER_MAX_EDGE_PX
            if max(img.size) > edge:
                img.thumbnail((edge, edge), Image.LANCZOS)
            # Eerst de kwaliteit stapsgewijs omlaag; past het dan nog niet (zeer korrelige foto), dan iets kleiner in plaats van weigeren.
            for _round in range(4):
                for quality in limits.PHOTO_JPEG_QUALITIES:
                    out = io.BytesIO()
                    img.save(out, "JPEG", quality=quality, optimize=True, progressive=True)  # geen exif= en geen icc_profile=: metadata valt weg
                    if out.tell() <= limits.PHOTO_MAX_STORED_BYTES:
                        return out.getvalue()
                img = img.resize((int(img.width * 0.8), int(img.height * 0.8)), Image.LANCZOS)
    except PhotoRejected:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise PhotoRejected("onleesbaar")
    raise PhotoRejected("te_groot")
