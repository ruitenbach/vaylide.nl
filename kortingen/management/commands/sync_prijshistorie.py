from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from kortingen.aanbiedingen import sync_history


class Command(BaseCommand):
    help = "Legt de huidige gewone prijzen vast in de prijshistorie (draait ook bij migrate). Alleen nieuwe of gewijzigde prijzen krijgen een nieuwe stand."

    def add_arguments(self, parser):
        parser.add_argument("--sinds", help="JJJJ-MM-DD: voor prijzen die nog niet in de historie staan, de datum vanaf wanneer ze aantoonbaar gelden. "
                                           "Alleen gebruiken met bewijs van de eigenaar; anders begint de historie vandaag.")

    def handle(self, *args, **options):
        since = None
        if options["sinds"]:
            try:
                since = timezone.make_aware(datetime.strptime(options["sinds"], "%Y-%m-%d"))
            except ValueError as exc:
                raise CommandError("Gebruik de vorm JJJJ-MM-DD.") from exc
            if since > timezone.now():
                raise CommandError("De datum ligt in de toekomst.")
        self.stdout.write(f"{sync_history(since=since)} prijsstanden bijgewerkt.")
