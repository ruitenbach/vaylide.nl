"""Bescherming tegen het raden van wachtwoorden bij de inlog met wachtwoord (Beheer en Django-admin).

Klanten loggen in met een eenmalige code (zie accounts/) en vallen hier niet onder: alleen wie een staff-account
probeert. Twee tellers, alleen voor mislukte pogingen:
- per IP-netwerk (een aanvaller vanaf één adres),
- per gebruikersnaam (een aanvaller die veel adressen gebruikt tegen één account).
Is het IP-adres niet betrouwbaar vast te stellen (zie core/ipinfo.py), dan telt alleen de teller per gebruikersnaam;
de IP-teller wordt dan nooit gedeeld door alle bezoekers. Is een teller vol, dan wordt tot het einde van het venster ook een juist wachtwoord niet meer aangenomen.
Een geslaagde inlog zet de teller van die gebruikersnaam terug.
"""
from __future__ import annotations

import hashlib
import hmac
import time

from django.conf import settings
from django.core.cache import cache

from .utils import rate_exceeded, rate_limit, reliable_ip_fingerprint

WINDOW = 900  # 15 minuten
IP_FAILURES = 10
ACCOUNT_FAILURES = 10
MESSAGE = "Te veel inlogpogingen. Wacht een kwartier en probeer het opnieuw."


def _account_key(username: str) -> str:
    normalized = (username or "").strip().lower()[:254]
    digest = hmac.new(settings.SECRET_KEY.encode(), f"staff:{normalized}".encode(), hashlib.sha256).hexdigest()[:24]
    return f"staff-fail-user:{digest}"


def _ip_key(request) -> str | None:
    fingerprint = reliable_ip_fingerprint(request)
    return f"staff-fail-ip:{fingerprint}" if fingerprint else None


def is_blocked(request, username: str) -> bool:
    ip_key = _ip_key(request)
    if ip_key and rate_exceeded(ip_key, IP_FAILURES, WINDOW):
        return True
    return rate_exceeded(_account_key(username), ACCOUNT_FAILURES, WINDOW)


def register_failure(request, username: str) -> None:
    ip_key = _ip_key(request)
    if ip_key:
        rate_limit(ip_key, IP_FAILURES, WINDOW)
    rate_limit(_account_key(username), ACCOUNT_FAILURES, WINDOW)


def register_success(username: str) -> None:
    window = int(time.time() // WINDOW)
    cache.delete(f"rl:{_account_key(username)}:{window}")
