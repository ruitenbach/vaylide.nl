"""Verwerking van uploads: controle van type en grootte, EXIF verwijderen en verkleinen.

Foto's worden altijd opnieuw opgeslagen als WebP in drie formaten. Daardoor
verdwijnen metadata zoals GPS-locaties en worden verborgen inhoud of
ongebruikelijke formaten niet ongewijzigd doorgegeven.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

log = logging.getLogger(__name__)

PHOTO_SIZES = {"groot": 2000, "middel": 1000, "klein": 420}
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "MPO": "image/jpeg"}
AUDIO_SIGNATURES = (
    (b"ID3", "audio/mpeg"),
    (b"\xff\xfb", "audio/mpeg"),
    (b"\xff\xf3", "audio/mpeg"),
    (b"\xff\xf2", "audio/mpeg"),
)


class UploadError(ValueError):
    """Begrijpelijke foutmelding voor de gebruiker."""


@dataclass
class ProcessedPhoto:
    large: ContentFile
    medium: ContentFile
    thumb: ContentFile
    width: int
    height: int
    size_bytes: int
    focus: object = None  # focus.Focus: automatisch middelpunt en aantal gezichten


def _human_mb(num: int) -> str:
    return f"{num / (1024 * 1024):.0f} MB"


def process_photo(uploaded) -> ProcessedPhoto:
    limits = settings.UPLOAD_LIMITS
    if uploaded.size > limits["photo_max_bytes"]:
        raise UploadError(f"Deze foto is te groot ({_human_mb(uploaded.size)}). Het maximum is {_human_mb(limits['photo_max_bytes'])}.")
    Image.MAX_IMAGE_PIXELS = limits["photo_max_pixels"]
    try:
        uploaded.seek(0)
        with Image.open(uploaded) as probe:
            fmt = probe.format
            probe.verify()
        if fmt not in ALLOWED_FORMATS:
            raise UploadError("Dit bestandstype wordt niet ondersteund. Gebruik een JPG-, PNG- of WebP-foto.")
        uploaded.seek(0)
        with Image.open(uploaded) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
            if img.mode == "RGBA":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.getchannel("A"))
                img = background
            width, height = img.size
            if min(width, height) < limits["photo_min_side"]:
                raise UploadError(
                    f"Deze foto is te klein ({width}×{height} pixels). Kies een foto van minimaal {limits['photo_min_side']} pixels breed en hoog."
                )
            focus = _focus(img)
            outputs = {}
            for name, max_side in PHOTO_SIZES.items():
                copy = img.copy()
                copy.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                copy.save(buffer, "WEBP", quality=82 if name != "klein" else 75, method=4)
                outputs[name] = ContentFile(buffer.getvalue(), name=f"{name}.webp")
    except Image.DecompressionBombError:
        raise UploadError("Deze foto heeft te veel pixels. Verklein de foto en probeer het opnieuw.")
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise UploadError("Dit bestand is geen geldige foto. Gebruik een JPG-, PNG- of WebP-foto.")
    return ProcessedPhoto(
        large=outputs["groot"],
        medium=outputs["middel"],
        thumb=outputs["klein"],
        width=width,
        height=height,
        size_bytes=outputs["groot"].size,
        focus=focus,
    )


def _focus(img):
    """Automatisch uitlijnen (gezichten, anders het drukste deel). Mag het uploaden nooit laten mislukken."""
    from .focus import detect

    try:
        return detect(img)
    except Exception:
        log.warning("Automatisch uitlijnen mislukt", exc_info=True)
        return None


def sniff_audio(uploaded) -> str:
    limits = settings.UPLOAD_LIMITS
    if uploaded.size > limits["audio_max_bytes"]:
        raise UploadError(f"Dit muziekbestand is te groot ({_human_mb(uploaded.size)}). Het maximum is {_human_mb(limits['audio_max_bytes'])}.")
    uploaded.seek(0)
    head = uploaded.read(16)
    uploaded.seek(0)
    for signature, content_type in AUDIO_SIGNATURES:
        if head.startswith(signature):
            return content_type
    if len(head) >= 12 and head[4:8] == b"ftyp" and head[8:12] in (b"M4A ", b"mp42", b"isom", b"M4B "):
        return "audio/mp4"
    raise UploadError("Dit muziekbestand wordt niet ondersteund. Gebruik een MP3- of M4A-bestand.")


ATTACHMENT_TYPES = {
    b"%PDF": ("application/pdf", ".pdf"),
    b"\x89PNG": ("image/png", ".png"),
    b"\xff\xd8\xff": ("image/jpeg", ".jpg"),
    b"RIFF": ("image/webp", ".webp"),
}


def sniff_attachment(uploaded) -> tuple[str, str]:
    limits = settings.UPLOAD_LIMITS
    if uploaded.size > limits["attachment_max_bytes"]:
        raise UploadError(f"Dit bestand is te groot ({_human_mb(uploaded.size)}). Het maximum is {_human_mb(limits['attachment_max_bytes'])}.")
    uploaded.seek(0)
    head = uploaded.read(12)
    uploaded.seek(0)
    for signature, (content_type, ext) in ATTACHMENT_TYPES.items():
        if head.startswith(signature):
            if signature == b"RIFF" and head[8:12] != b"WEBP":
                continue
            return content_type, ext
    raise UploadError("Dit bestandstype wordt niet ondersteund. Gebruik een PDF, JPG, PNG of WebP.")
