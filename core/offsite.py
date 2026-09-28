"""Tweede back-uplocatie: een versleutelde kopie van elke back-up naar een S3-compatibele opslag.

Werkt met elke aanbieder met een S3-koppeling (bijvoorbeeld in de EU: Hetzner Object Storage, Scaleway,
OVHcloud of Backblaze B2 in Amsterdam). Uit zolang niet alles is ingevuld; zie docs/BACKUP.md.

- Versleuteling vóór het versturen, met een eigen sleutel (VIERLIEF_BACKUP_ENCRYPTION_KEY, Fernet). De
  aanbieder ziet alleen versleutelde gegevens. Zonder sleutel wordt er niets verstuurd.
- Het bestand wordt in blokken van 4 MB versleuteld, zodat ook grote back-ups weinig geheugen gebruiken.
- Een mislukte upload breekt de gewone back-up nooit; de eigenaar krijgt een melding en het staat in de log.
"""
from __future__ import annotations

import logging
import struct
from pathlib import Path

from django.conf import settings

log = logging.getLogger(__name__)

MAGIC = b"VAYLIDE-ENC1\n"
CHUNK = 4 * 1024 * 1024


class OffsiteError(RuntimeError):
    pass


def configured() -> bool:
    return bool(settings.BACKUP_S3_BUCKET and settings.BACKUP_S3_ACCESS_KEY and settings.BACKUP_S3_SECRET_KEY
                and settings.BACKUP_ENCRYPTION_KEY)


def _fernet():
    from cryptography.fernet import Fernet

    try:
        return Fernet(settings.BACKUP_ENCRYPTION_KEY.encode())
    except (ValueError, TypeError) as exc:
        raise OffsiteError("VIERLIEF_BACKUP_ENCRYPTION_KEY is geen geldige sleutel (maak er een met: python manage.py backup --nieuwe-sleutel).") from exc


def encrypt_file(src: Path, dst: Path) -> Path:
    f = _fernet()
    with open(src, "rb") as inp, open(dst, "wb") as out:
        out.write(MAGIC)
        while block := inp.read(CHUNK):
            token = f.encrypt(block)
            out.write(struct.pack(">I", len(token)))
            out.write(token)
    return dst


def decrypt_file(src: Path, dst: Path) -> Path:
    from cryptography.fernet import InvalidToken

    f = _fernet()
    with open(src, "rb") as inp, open(dst, "wb") as out:
        if inp.read(len(MAGIC)) != MAGIC:
            raise OffsiteError("Dit is geen versleutelde Vaylide-back-up.")
        while head := inp.read(4):
            (size,) = struct.unpack(">I", head)
            try:
                out.write(f.decrypt(inp.read(size)))
            except InvalidToken as exc:
                raise OffsiteError("De sleutel past niet bij deze back-up, of het bestand is beschadigd.") from exc
    return dst


def _client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.BACKUP_S3_ENDPOINT or None,
        region_name=settings.BACKUP_S3_REGION or None,
        aws_access_key_id=settings.BACKUP_S3_ACCESS_KEY,
        aws_secret_access_key=settings.BACKUP_S3_SECRET_KEY,
    )


def upload(path: Path) -> str:
    """Versleutelt `path` en zet het in de bucket. Geeft de sleutel (bestandsnaam) in de bucket terug."""
    if not configured():
        raise OffsiteError("Tweede back-uplocatie is niet ingesteld.")
    encrypted = encrypt_file(path, path.with_name(path.name + ".enc"))
    key = f"{settings.BACKUP_S3_PREFIX.strip('/')}/{encrypted.name}".lstrip("/")
    try:
        _client().upload_file(str(encrypted), settings.BACKUP_S3_BUCKET, key)
    except Exception as exc:  # noqa: BLE001 - elke fout van de opslag moet als OffsiteError terugkomen
        raise OffsiteError(f"Uploaden naar de tweede back-uplocatie mislukt: {exc}") from exc
    finally:
        encrypted.unlink(missing_ok=True)
    return key


def copy_offsite(path: Path) -> str:
    """Voor de nachtelijke taak: probeert de kopie, meldt een fout maar gooit hem niet op."""
    if not configured():
        return "niet ingesteld"
    try:
        key = upload(path)
    except OffsiteError as exc:
        log.error("%s", exc)
        from processing.emails import queue_email

        queue_email(to=settings.OWNER_NOTIFY_EMAIL, subject="Back-up niet naar de tweede locatie gekopieerd",
                    template="owner_offsite", context={"reason": str(exc)}, unique_key=f"offsite-fail:{path.name}")
        return "mislukt"
    return key
