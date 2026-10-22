"""Melding bij uitzonderlijk veel onbekende uitnodigingslinks (alleen waarschuwen, nooit blokkeren).

Telt alle missers van alle bezoekers samen per venster, zonder IP-adressen of linkteksten. Bij het overschrijden van de
drempel komt per venster hooguit één logregel en per periode van 6 uur hooguit één e-mail aan de eigenaar. Een aanval kan
dus niet leiden tot een stroom meldingen of onbeperkt veel databasewerk: na de melding telt dit proces in dat venster
niet meer. De melding mag het tonen van een pagina nooit verstoren.
"""
from __future__ import annotations

import logging
import time

from django.conf import settings
from django.utils import timezone

from core.utils import rate_limit

log = logging.getLogger(__name__)

WINDOW = 600  # 10 minuten
THRESHOLD = 100  # missers van alle bezoekers samen per venster
MAIL_PERIOD_HOURS = 6

_alarmed_window: int | None = None


def register_miss() -> None:
    global _alarmed_window
    try:
        window = int(time.time() // WINDOW)
        if _alarmed_window == window:
            return
        if rate_limit("slug-miss-global", THRESHOLD, WINDOW):
            return
        _alarmed_window = window
        _notify()
    except Exception:  # een melding mag nooit een pagina laten falen
        log.exception("Melding onbekende uitnodigingslinks mislukt")


def _notify() -> None:
    log.warning(
        "Uitzonderlijk veel onbekende uitnodigingslinks: meer dan %s in %s minuten. "
        "Alleen een melding; er wordt niets geblokkeerd. Zie docs/BEVEILIGING.md.",
        THRESHOLD, WINDOW // 60,
    )
    from processing.emails import queue_email

    now = timezone.now()
    queue_email(
        to=settings.OWNER_NOTIFY_EMAIL,
        subject="Veel onbekende uitnodigingslinks bezocht",
        template="owner_link_alarm",
        context={"threshold": THRESHOLD, "minutes": WINDOW // 60},
        unique_key=f"link-alarm:{now:%Y-%m-%d}:{now.hour // MAIL_PERIOD_HOURS}",
        kind="owner_link_alarm",
        owner_alert=True,
        max_attempts=3,
    )
