"""Privé-objectopslag voor Moments. Eén kleine koppeling met twee uitvoeringen:

- `LocalStorage`: een eigen map, alleen in testmodus. Het "direct uploaden" loopt dan via een ondertekend PUT-adres van deze site.
- `S3Storage`: S3-compatibele opslag (bijvoorbeeld Scaleway) met een ondertekende POST die grootte en type afdwingt.
  Nog niet in gebruik: er is geen productie- of externe opslag aangemaakt. Alleen een aparte testbucket is toegestaan.

Bestanden zijn nooit openbaar. De server geeft na de tokencontrole alleen kortlevende, ondertekende toegang tot het eigen object.
"""
from __future__ import annotations

import secrets
import time
from pathlib import Path

from django.conf import settings
from django.core import signing
from django.urls import reverse

UPLOAD_SALT = "moments-test-upload"


class StorageNotReady(Exception):
    """De opslag is niet ingesteld (of mag in deze modus niet). Uploads worden dan netjes geweigerd, nooit lokaal opgeslagen."""


def new_key(album_uid, kind: str = "obj", ext: str = "") -> str:
    suffix = f".{ext}" if ext else ""
    return f"moments/{album_uid}/{kind}/{secrets.token_hex(16)}{suffix}"


class LocalStorage:
    name = "lokaal"

    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root not in path.parents:
            raise ValueError("ongeldige sleutel")
        return path

    def upload_target(self, key: str, content_type: str, max_bytes: int, expires_in: int = 1800) -> dict:
        signed = signing.dumps({"k": key, "m": max_bytes, "t": content_type}, salt=UPLOAD_SALT)
        return {"method": "PUT", "url": reverse("moments:test_opslag", args=[signed]), "fields": {}, "headers": {"Content-Type": content_type}}

    def write(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".deel")
        tmp.write_bytes(data)
        tmp.replace(path)

    def size(self, key: str) -> int | None:
        path = self._path(key)
        return path.stat().st_size if path.is_file() else None

    def read(self, key: str, limit: int | None = None) -> bytes:
        with self._path(key).open("rb") as fh:
            return fh.read() if limit is None else fh.read(limit)

    def open(self, key: str):
        return self._path(key).open("rb")

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def keys(self, prefix: str):
        base = self._path(prefix.rstrip("/")) if prefix else self.root
        if not base.exists():
            return
        for path in base.rglob("*"):
            if path.is_file():
                yield str(path.relative_to(self.root)), path.stat().st_mtime

    def download_url(self, key: str, expires_in: int = 300) -> str | None:
        return None  # de server streamt zelf, na de tokencontrole


class S3Storage:
    name = "s3"

    def __init__(self, bucket: str, endpoint: str, region: str, access_key: str, secret_key: str):
        import boto3
        from botocore.config import Config

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint or None,
            region_name=region or None,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4", retries={"max_attempts": 3}, connect_timeout=5, read_timeout=15),
        )

    def upload_target(self, key: str, content_type: str, max_bytes: int, expires_in: int = 1800) -> dict:
        # Een ondertekende POST kan, anders dan een PUT, de grootte en het type vooraf afdwingen.
        post = self.client.generate_presigned_post(
            self.bucket,
            key,
            Fields={"Content-Type": content_type},
            Conditions=[["content-length-range", 1, max_bytes], {"Content-Type": content_type}],
            ExpiresIn=expires_in,
        )
        return {"method": "POST", "url": post["url"], "fields": post["fields"], "headers": {}}

    def write(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType="image/jpeg", ServerSideEncryption="AES256")

    def size(self, key: str) -> int | None:
        from botocore.exceptions import ClientError

        try:
            return int(self.client.head_object(Bucket=self.bucket, Key=key)["ContentLength"])
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise

    def read(self, key: str, limit: int | None = None) -> bytes:
        kwargs = {"Range": f"bytes=0-{limit - 1}"} if limit else {}
        return self.client.get_object(Bucket=self.bucket, Key=key, **kwargs)["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def keys(self, prefix: str):
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                yield obj["Key"], obj["LastModified"].timestamp()

    def download_url(self, key: str, expires_in: int = 300) -> str | None:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key, "ResponseContentDisposition": "inline", "ResponseContentType": "image/jpeg"}, ExpiresIn=expires_in
        )


def get_storage():
    kind = (getattr(settings, "MOMENTS_STORAGE", "") or "lokaal").lower()
    if kind == "lokaal":
        if not settings.TEST_MODE:
            raise StorageNotReady("Lokale opslag bestaat alleen in testmodus.")
        return LocalStorage(settings.MOMENTS_LOCAL_DIR)
    if kind == "s3":
        values = [settings.MOMENTS_S3_BUCKET, settings.MOMENTS_S3_ACCESS_KEY, settings.MOMENTS_S3_SECRET_KEY]
        if not all(values):
            raise StorageNotReady("S3-opslag is niet volledig ingesteld.")
        if settings.MOMENTS_S3_BUCKET == getattr(settings, "BACKUP_S3_BUCKET", None):
            raise StorageNotReady("De bucket voor Moments mag niet de back-upbucket zijn.")
        return S3Storage(settings.MOMENTS_S3_BUCKET, settings.MOMENTS_S3_ENDPOINT, settings.MOMENTS_S3_REGION, settings.MOMENTS_S3_ACCESS_KEY, settings.MOMENTS_S3_SECRET_KEY)
    raise StorageNotReady("Onbekende opslag.")


def now_ts() -> float:
    return time.time()
