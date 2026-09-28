"""Maakt een back-up van database en uploads: python manage.py backup [--keep 14] [--offsite]

--offsite            ook een versleutelde kopie naar de tweede back-uplocatie (VIERLIEF_BACKUP_S3_*)
--nieuwe-sleutel     toont een nieuwe sleutel voor VIERLIEF_BACKUP_ENCRYPTION_KEY (bewaar hem ook buiten de server)
--ontsleutel A B     zet een versleutelde kopie (.enc) om naar een gewone back-up, om te herstellen
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.backup import make_backup
from core.offsite import OffsiteError, configured, decrypt_file, upload


class Command(BaseCommand):
    help = "Maakt een back-up (database en uploads samen) in <VIERLIEF_DATA_DIR>/backups/."

    def add_arguments(self, parser):
        parser.add_argument("--keep", type=int, default=14, help="Aantal back-ups dat bewaard blijft (standaard 14).")
        parser.add_argument("--offsite", action="store_true", help="Ook naar de tweede back-uplocatie kopiëren.")
        parser.add_argument("--nieuwe-sleutel", action="store_true", help="Maak een versleutelingssleutel aan en stop.")
        parser.add_argument("--ontsleutel", nargs=2, metavar=("VERSLEUTELD", "UITVOER"), help="Ontsleutel een kopie en stop.")

    def handle(self, *args, **options):
        if options["nieuwe_sleutel"]:
            from cryptography.fernet import Fernet

            self.stdout.write(Fernet.generate_key().decode())
            self.stdout.write("Zet deze waarde in VIERLIEF_BACKUP_ENCRYPTION_KEY en bewaar hem ook op een veilige plek buiten de server.")
            return
        if options["ontsleutel"]:
            src, dst = (Path(p) for p in options["ontsleutel"])
            try:
                decrypt_file(src, dst)
            except OffsiteError as exc:
                raise CommandError(str(exc)) from exc
            self.stdout.write(f"Ontsleuteld: {dst}. Herstellen: python manage.py restore_backup {dst} --ja")
            return
        if options["offsite"] and not configured():
            raise CommandError("De tweede back-uplocatie is niet ingesteld (VIERLIEF_BACKUP_S3_* en VIERLIEF_BACKUP_ENCRYPTION_KEY).")
        path = make_backup(keep=options["keep"])
        self.stdout.write(f"Back-up gemaakt: {path} ({path.stat().st_size // 1024} kB)")
        if options["offsite"]:
            try:
                key = upload(path)
            except OffsiteError as exc:
                raise CommandError(str(exc)) from exc
            self.stdout.write(f"Versleutelde kopie op de tweede locatie: {key}")
