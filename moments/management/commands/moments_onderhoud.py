"""Onderhoud van Moments: ontvangen foto's verwerken, verlopen reserveringen vrijgeven, losse objecten opruimen en oude netwerkhashes wissen.
Los van de betaalverwerking (`processing/`). Veilig om vaak te draaien, ook meerdere keren tegelijk."""
from django.core.management.base import BaseCommand, CommandError

from moments import services
from moments.flags import moments_enabled
from moments.storage import StorageNotReady, get_storage


class Command(BaseCommand):
    help = "Verwerkt ontvangen Moments-foto's en ruimt op."

    def add_arguments(self, parser):
        parser.add_argument("--max", type=int, default=50, help="Hoogstens zoveel foto's per aanroep verwerken.")

    def handle(self, *args, **opts):
        if not moments_enabled():
            self.stdout.write("Moments staat uit: niets gedaan.")
            return
        try:
            storage = get_storage()
        except StorageNotReady as exc:
            raise CommandError(str(exc))
        expired = services.expire_reservations(storage)
        done = 0
        while done < opts["max"] and services.process_next_photo(storage) is not None:
            done += 1
        orphans = services.cleanup_orphans(storage)
        hashes = services.purge_network_hashes()
        self.stdout.write(f"verlopen: {expired}, verwerkt: {done}, losse objecten: {orphans}, netwerkhashes gewist: {hashes}")
