"""Kent de rol Hoofdbeheerder (of Eigenaar) toe aan één bestaand medewerkersaccount. Alleen op de server, alleen op uitdrukkelijk verzoek van de eigenaar.

Zonder --bevestig toont het commando alleen wat het zou doen. Het commando wijzigt nooit een bestaand eigenaarsaccount en maakt geen accounts aan.
Gebruik: python manage.py wijs_rol_toe collega@example.com hoofdbeheerder --bevestig
De rol Eigenaar toekennen kan alleen met --eigenaar-akkoord (een afzonderlijk akkoord van de eigenaar)."""
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from beheer import rollen


class Command(BaseCommand):
    help = "Kent een rol toe aan een bestaand medewerkersaccount (op de server, met bevestiging)."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("rol", choices=["hoofdbeheerder", "eigenaar"])
        parser.add_argument("--bevestig", action="store_true")
        parser.add_argument("--eigenaar-akkoord", action="store_true", help="Vereist voor de rol Eigenaar.")

    def handle(self, *args, **opts):
        from django.contrib.auth.models import Group

        user = User.objects.filter(email__iexact=opts["email"], is_staff=True).first()
        if user is None:
            raise CommandError("Geen medewerkersaccount (is_staff) met dit e-mailadres. Er wordt niets aangemaakt.")
        if rollen.is_eigenaar(user):
            raise CommandError("Dit is al een eigenaarsaccount; dat wordt hier nooit gewijzigd.")
        naam = rollen.EIGENAAR if opts["rol"] == "eigenaar" else rollen.HOOFDBEHEERDER
        if naam == rollen.EIGENAAR and not opts["eigenaar_akkoord"]:
            raise CommandError("De rol Eigenaar vraagt een afzonderlijk akkoord van de eigenaar: voeg --eigenaar-akkoord toe.")
        rollen.ensure_roles()
        if not opts["bevestig"]:
            self.stdout.write(f"Zou {user.email} toevoegen aan de groep {naam}. Voeg --bevestig toe om het echt te doen.")
            return
        user.groups.add(Group.objects.get(name=naam))
        self.stdout.write(f"{user.email} is nu {naam}.")
