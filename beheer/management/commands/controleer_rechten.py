"""Toont wie welke rol heeft in Beheer. Alleen lezen: het commando wijzigt niets en toont geen wachtwoorden of codes.

Gebruik (bijvoorbeeld op de productieserver, door de eigenaar): python manage.py controleer_rechten"""
from django.core.management.base import BaseCommand

from accounts.models import User
from beheer import rollen


class Command(BaseCommand):
    help = "Toont de rollen van alle medewerkersaccounts (alleen lezen)."

    def handle(self, *args, **opts):
        out = self.stdout.write
        staff = User.objects.filter(is_staff=True).order_by("email")
        out(f"Medewerkersaccounts (is_staff): {staff.count()}")
        for u in staff:
            groepen = ", ".join(u.groups.values_list("name", flat=True)) or "geen groep"
            out(f"- {u.email}: rol {rollen.rol(u) or '—'} · superuser {'ja' if u.is_superuser else 'nee'} · actief {'ja' if u.is_active else 'nee'} · {groepen} · "
                f"prijzen wijzigen {'ja' if rollen.mag_prijzen_wijzigen(u) else 'nee'}")
        zonder = [u for u in User.objects.filter(is_superuser=True) if not u.is_staff]
        for u in zonder:
            out(f"Let op: {u.email} is superuser maar niet is_staff.")
        if not any(rollen.is_eigenaar(u) for u in staff):
            out("Let op: er is geen eigenaarsaccount (superuser of groep Eigenaar).")
