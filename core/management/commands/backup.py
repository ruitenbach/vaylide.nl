"""Maakt een back-up van database en uploads: python manage.py backup [--keep 14]"""
from django.core.management.base import BaseCommand

from core.backup import make_backup


class Command(BaseCommand):
    help = "Maakt een back-up (database en uploads samen) in <VIERLIEF_DATA_DIR>/backups/."

    def add_arguments(self, parser):
        parser.add_argument("--keep", type=int, default=14, help="Aantal back-ups dat bewaard blijft (standaard 14).")

    def handle(self, *args, **options):
        path = make_backup(keep=options["keep"])
        self.stdout.write(f"Back-up gemaakt: {path} ({path.stat().st_size // 1024} kB)")
