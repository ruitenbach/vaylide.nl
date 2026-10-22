"""Hulpfuncties: IP-adres, ondertekende tijdstempels, rate limiting en tokens."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from django.conf import settings
from django.core import signing
from django.core.cache import cache

from .ipinfo import client_ip, limit_network, warn_if_unreliable  # noqa: F401  (client_ip blijft hier importeerbaar)

FORM_TS_SALT = "vierlief.form-ts"


def _fingerprint(ip: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), limit_network(ip).encode(), hashlib.sha256).hexdigest()[:24]


def ip_fingerprint(request) -> str:
    """Niet-omkeerbare verkorte hash van het IP-adres (alleen voor limieten). Meldt een onbetrouwbaar adres in het log."""
    status = warn_if_unreliable(request)
    return _fingerprint(status.ip)


def reliable_ip_fingerprint(request) -> str | None:
    """Zoals ip_fingerprint, maar None als het adres niet betrouwbaar is: dan mag een limiet er niet op vertrouwen."""
    status = warn_if_unreliable(request)
    return _fingerprint(status.ip) if status.reliable else None


def rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """Geeft True als de actie is toegestaan; telt de poging mee."""
    bucket = f"rl:{key}:{int(time.time() // window_seconds)}"
    added = cache.add(bucket, 1, window_seconds + 5)
    if added:
        return True
    try:
        count = cache.incr(bucket)
    except ValueError:
        cache.set(bucket, 1, window_seconds + 5)
        return True
    return count <= limit


def rate_exceeded(key: str, limit: int, window_seconds: int) -> bool:
    """Is de limiet al bereikt? Telt niet mee (om te kijken zonder een poging te verbruiken)."""
    bucket = f"rl:{key}:{int(time.time() // window_seconds)}"
    return (cache.get(bucket) or 0) >= limit


def signed_timestamp() -> str:
    return signing.TimestampSigner(salt=FORM_TS_SALT).sign(str(int(time.time())))


def form_age_seconds(value: str, max_age: int = 7 * 24 * 3600) -> float | None:
    """Leeftijd van het formulier in seconden, of None als ongeldig/verlopen."""
    try:
        raw = signing.TimestampSigner(salt=FORM_TS_SALT).unsign(value or "", max_age=max_age)
        return time.time() - int(raw)
    except (signing.BadSignature, ValueError):
        return None


def new_token(nbytes: int = 24) -> str:
    return secrets.token_urlsafe(nbytes)


def token_digest(token: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), f"tok:{token}".encode(), hashlib.sha256).hexdigest()


def wants_json(request) -> bool:
    return "application/json" in request.headers.get("Accept", "") or request.headers.get("X-Requested-With") == "fetch"
