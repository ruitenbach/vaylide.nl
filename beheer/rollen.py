"""Rollen en rechten in Beheer (voorbereid; er wordt hier niemand automatisch een rol toegekend).

- Eigenaar: een superuser, of lid van de groep 'Eigenaar'. Mag alles, ook prijzen wijzigen en terugdraaien.
- Hoofdbeheerder: lid van de groep 'Hoofdbeheerder'. Mag prijzen bekijken, wijzigen en terugdraaien (besluit van de eigenaar, 17 oktober 2026).
- Beheerder: elke andere gebruiker met is_staff. Mag prijzen alleen bekijken.

De groepen en hun rechten worden na `migrate` aangemaakt (catalog.apps, ensure_roles). Het toekennen van een rol aan een account gebeurt nooit
automatisch en nooit via Beheer, alleen met het commando `wijs_rol_toe` op de server. Een eigenaarsaccount wordt door geen enkele andere beheerder
gewijzigd (zie mag_account_wijzigen); er is bovendien geen scherm in Beheer dat een medewerkersaccount kan bewerken, verwijderen of anonimiseren."""
from __future__ import annotations

EIGENAAR = "Eigenaar"
HOOFDBEHEERDER = "Hoofdbeheerder"
PERM_WIJZIGEN = "catalog.prijzen_wijzigen"
PERM_TERUGDRAAIEN = "catalog.prijzen_terugdraaien"


def _actief_staff(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False) and user.is_active and user.is_staff)


def in_groep(user, naam: str) -> bool:
    return _actief_staff(user) and user.groups.filter(name=naam).exists()


def is_eigenaar(user) -> bool:
    return _actief_staff(user) and (user.is_superuser or in_groep(user, EIGENAAR))


def rol(user) -> str:
    if is_eigenaar(user):
        return EIGENAAR
    if in_groep(user, HOOFDBEHEERDER):
        return HOOFDBEHEERDER
    return "Beheerder" if _actief_staff(user) else ""


def mag_prijzen_bekijken(user) -> bool:
    return _actief_staff(user)


def mag_prijzen_wijzigen(user) -> bool:
    return _actief_staff(user) and (user.is_superuser or user.has_perm(PERM_WIJZIGEN))


def mag_prijzen_terugdraaien(user) -> bool:
    return _actief_staff(user) and (user.is_superuser or user.has_perm(PERM_TERUGDRAAIEN))


def mag_account_wijzigen(actor, target) -> bool:
    """Een eigenaarsaccount wijzigt alleen zichzelf. Een ander staff-account wijzigt alleen een eigenaar. Een klantaccount staat los van deze regel."""
    if target is None or actor is None or not getattr(actor, "is_authenticated", False):
        return False
    if actor.pk == target.pk:
        return True
    if is_eigenaar(target) or target.is_superuser:
        return False
    if target.is_staff:
        return is_eigenaar(actor)
    return _actief_staff(actor)


def ensure_roles(**kwargs) -> None:
    """Maakt de groepen en hun rechten aan (idempotent; wijst niemand toe). Draait na elke `migrate`."""
    from django.contrib.auth.models import Group, Permission

    rechten = {p.codename: p for p in Permission.objects.filter(content_type__app_label="catalog", codename__in=["prijzen_wijzigen", "prijzen_terugdraaien"])}
    if len(rechten) < 2:
        return      # de rechten bestaan nog niet (eerste migrate); post_migrate van auth maakt ze eerst aan en dit draait daarna opnieuw
    eigenaar, _ = Group.objects.get_or_create(name=EIGENAAR)
    eigenaar.permissions.add(*rechten.values())
    hoofd, _ = Group.objects.get_or_create(name=HOOFDBEHEERDER)
    hoofd.permissions.add(*rechten.values())
