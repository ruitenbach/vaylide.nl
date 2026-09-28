"""Zet een back-up terug: python manage.py restore_backup <bestand> --ja

Alleen in een lege database, direct na `migrate`. Uploads worden vervangen. Zie docs/BACKUP.md.
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from core.backup import restore_backup


class Command(BaseCommand):
    help = "Zet een back-up (database en uploads) terug in een lege, gemigreerde database."

    def add_arguments(self, parser):
        parser.add_argument("bestand")
        parser.add_argument("--ja", action="store_true", help="Bevestig dat de uploads worden vervangen.")

    def handle(self, *args, **options):
        path = Path(options["bestand"])
        if not path.is_file():
            raise CommandError(f"Bestand niet gevonden: {path}")
        if not options["ja"]:
            raise CommandError("Voeg --ja toe: de huidige uploads worden vervangen.")
        if User.objects.exists():
            raise CommandError("De database is niet leeg. Herstel alleen in een lege database, direct na migrate.")
        info = restore_backup(path)
        self.stdout.write(f"Teruggezet: {path.name} (gemaakt {info.get('gemaakt', 'onbekend')}).")
