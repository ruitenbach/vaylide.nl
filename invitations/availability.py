"""Hoe lang een uitnodiging online staat (algemene voorwaarden, artikel 6).

- Essentieel 6 maanden, Compleet 12 maanden (plus eventueel 'Langer online'), in kalendermaanden.
- Vanaf de aankoopdatum: de dag waarop de betaling is bevestigd (Order.paid_at).
- Online tot en met dezelfde dag zoveel maanden later (bestaat die dag niet, dan de laatste dag van die maand), tot
  het einde van die dag in Nederlandse tijd.
- Later publiceren, aanpassen of het evenement verplaatsen verschuift de einddatum niet; herhaalde betaalmeldingen ook
  niet (de einddatum wordt één keer vastgelegd op de bestelling).
"""
from __future__ import annotations

import calendar
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone

NL = ZoneInfo("Europe/Amsterdam")


def add_months(day: date, months: int) -> date:
    """Kalendermaanden optellen; 31 januari + 1 maand = 28 (of 29) februari."""
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def end_of_availability(start: datetime, months: int) -> datetime:
    """Het laatste moment online: het einde (23:59:59) van de laatste dag, in Nederlandse tijd."""
    start_day = timezone.localtime(start, NL).date() if timezone.is_aware(start) else start.date()
    last_day = add_months(start_day, months)
    return datetime.combine(last_day, time(23, 59, 59), tzinfo=NL)


def order_end(order, invitation=None) -> datetime:
    """De einddatum van een bestelling. Bij een verlenging van een uitnodiging die nog online staat, telt de nieuwe
    periode vanaf de huidige einddatum; anders vanaf de bevestigde betaling."""
    paid = order.paid_at or timezone.now()
    current = getattr(invitation, "available_until", None)
    if current and current > paid:
        return end_of_availability(current, order.availability_months)
    return end_of_availability(paid, order.availability_months)
