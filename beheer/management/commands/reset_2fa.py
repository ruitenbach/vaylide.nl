"""Noodprocedure: tweestapsverificatie van een medewerker uitzetten (telefoon kwijt én geen herstelcodes meer).

Draait alleen op de server (Render-shell of lokaal), dus alleen wie al toegang heeft tot de server kan dit.
Het commando verwijdert de tweede stap en alle herstelcodes van dat ene account en beëindigt zijn sessies.
Daarna logt de medewerker in met alleen het wachtwoord en stelt 2FA opnieuw in (of moet dat doen, als 2FA verplicht is).
Zonder --bevestig toont het alleen wat er zou gebeuren.
"""
import logging

from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError

from accounts import tweestaps
from accounts.models import RecoveryCode, TwoFactor, User

log = logging.getLogger("vaylide.tweestaps")


class Command(BaseCommand):
    help = "Zet tweestapsverificatie van één medewerker uit (noodprocedure, alleen op de server)."

    def add_arguments(self, parser):
        parser.add_argument("email", help="E-mailadres van het medewerkersaccount")
        parser.add_argument("--bevestig", action="store_true", help="Voer de reset echt uit")

    def handle(self, *args, **opts):
        user = User.objects.filter(email__iexact=opts["email"].strip(), is_staff=True).first()
        if user is None:
            raise CommandError("Geen medewerkersaccount (is_staff) met dit e-mailadres. Er wordt niets gewijzigd.")
        tf = tweestaps.van(user)
        if tf is None:
            self.stdout.write(f"{user.email} heeft geen tweestapsverificatie. Er is niets te doen.")
            return
        over = tweestaps.herstelcodes_over(user)
        if not opts["bevestig"]:
            self.stdout.write(f"{user.email}: 2FA staat aan, {over} herstelcode(s) over. Voeg --bevestig toe om te resetten.")
            return
        beeindigd = 0
        for session in Session.objects.all().iterator():
            if str(session.get_decoded().get("_auth_user_id")) == str(user.pk):
                session.delete()
                beeindigd += 1
        RecoveryCode.objects.filter(user=user).delete()
        TwoFactor.objects.filter(pk=tf.pk).delete()
        log.warning("2FA gereset via servercommando voor gebruiker %s (%s sessies beëindigd)", user.pk, beeindigd)
        self.stdout.write(f"2FA van {user.email} is uitgezet en {beeindigd} sessie(s) zijn beëindigd. Log in met het wachtwoord en stel 2FA opnieuw in.")
