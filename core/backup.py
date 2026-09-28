"""Back-up en herstel van database en uploads samen, in één bestand.

Een back-up is een .tar.gz met:
- `database.json`: alle gegevens (Django dumpdata, los van SQLite of PostgreSQL);
- `uploads/`: de foto's, muziek en bijlagen van klanten;
- `info.json`: wanneer en van welke versie.

De bestanden komen in `<VIERLIEF_DATA_DIR>/backups/`; de oudste boven `keep` worden verwijderd.
Dit is een aanvulling op de back-ups van de hosting (database en schijf), geen vervanging:
kopieer back-ups ook regelmatig naar een andere plek. Zie docs/BACKUP.md.
"""
from __future__ import annotations

import io
import json
import shutil
import tarfile
import tempfile
from pathlib import Path

from django.conf import settings
from django.core import management
from django.db import connection, transaction
from django.utils import timezone

# Tabellen die bij herstel vanzelf goed komen of niet terug horen.
EXCLUDE = ["contenttypes", "auth.permission", "sessions", "admin.logentry"]


def backup_dir() -> Path:
    path = settings.DATA_DIR / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def make_backup(keep: int = 14) -> Path:
    stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    target = backup_dir() / f"vaylide-{stamp}.tar.gz"
    tmp = target.with_suffix(".part")
    data = io.StringIO()
    management.call_command(
        "dumpdata", "--natural-foreign", "--natural-primary", *[f"--exclude={e}" for e in EXCLUDE], stdout=data
    )
    info = {"gemaakt": timezone.now().isoformat(), "database": connection.vendor, "modus": settings.VIERLIEF_MODE}
    with tarfile.open(tmp, "w:gz") as tar:
        for name, text in (("database.json", data.getvalue()), ("info.json", json.dumps(info, indent=2))):
            raw = text.encode("utf-8")
            member = tarfile.TarInfo(name)
            member.size = len(raw)
            member.mtime = int(timezone.now().timestamp())
            tar.addfile(member, io.BytesIO(raw))
        uploads = Path(settings.MEDIA_ROOT)
        if uploads.is_dir():
            tar.add(uploads, arcname="uploads")
    tmp.replace(target)
    for old in sorted(backup_dir().glob("vaylide-*.tar.gz"))[:-keep] if keep > 0 else []:
        old.unlink(missing_ok=True)
    return target


def _clear_seeded_catalog() -> None:
    """`migrate` vult een lege database al met ontwerpen, pakketten, opties en instellingen (met eigen nummers).
    Die botsen met de back-up (zelfde codes, andere nummers); de back-up bevat ze zelf, dus eerst weg."""
    from catalog.models import AddOn, Package, Template, TemplateVersion

    from .models import SiteConfig

    Template.objects.update(current_version=None)
    for model in (TemplateVersion, Template, Package, AddOn, SiteConfig):
        model.objects.all().delete()


def restore_backup(path: Path) -> dict:
    """Zet een back-up terug in een LEGE, gemigreerde database. Uploads worden vervangen."""
    from accounts.models import User

    if User.objects.exists():
        raise ValueError("De database is niet leeg. Herstel alleen in een lege database, direct na migrate.")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        with tarfile.open(path, "r:gz") as tar:
            tar.extractall(tmp, filter="data")
        dump = tmp / "database.json"
        if not dump.is_file():
            raise ValueError("Dit is geen Vaylide-back-up (database.json ontbreekt).")
        with transaction.atomic():
            _clear_seeded_catalog()
            management.call_command("loaddata", str(dump), verbosity=0)
        uploads = Path(settings.MEDIA_ROOT)
        if (tmp / "uploads").is_dir():
            if uploads.exists():
                shutil.rmtree(uploads)
            shutil.copytree(tmp / "uploads", uploads)
        info = json.loads((tmp / "info.json").read_text(encoding="utf-8")) if (tmp / "info.json").is_file() else {}
    return info
