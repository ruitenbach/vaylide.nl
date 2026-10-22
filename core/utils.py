"""Hulpfuncties: IP-adres, ondertekende tijdstempels, rate limiting en tokens."""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import secrets
import time

from django.conf import settings
from django.core import signing
from django.core.cache import cache

FORM_TS_SALT = "vierlief.form-ts"


def _valid_ip(value: str) -> str:
    """Geeft het genormaliseerde IP-adres terug, of "" als het geen geldig adres is (bijv. een vervalste waarde)."""
    value = value.strip()
    if value.startswith("[") and "]" in value:  # [ipv6]:poort
        value = value[1:value.index("]")]
    elif value.count(":") == 1:  # ipv4:poort
        value = value.split(":", 1)[0]
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return ""
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return str(address)


def client_ip(request) -> str:
    """Het IP-adres van de bezoeker, alleen op basis van wat onze eigen proxy's hebben toegevoegd.

    Een proxy voegt achteraan toe wat hij zelf zag; wat een bezoeker zelf in X-Forwarded-For zet, staat links en wordt
    nooit gebruikt. Met TRUSTED_PROXY_HOPS=N tellen we N plaatsen van rechts. Klopt N niet met de werkelijke keten
    of is de waarde geen geldig IP-adres, dan vallen we terug op REMOTE_ADDR (het adres van de proxy: niemand kan
    zich daarmee een ander adres aanmeten, hooguit delen bezoekers dan een limiet).
    """
    hops = getattr(settings, "TRUSTED_PROXY_HOPS", 0)
    if hops > 0:
        forwarded = [p for p in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if p.strip()]
        if len(forwarded) >= hops:
            candidate = _valid_ip(forwarded[-hops])
            if candidate:
                return candidate
    return _valid_ip(request.META.get("REMOTE_ADDR", "")) or "onbekend"


def _limit_network(ip: str) -> str:
    """Voor limieten telt een heel IPv6-/64-netwerk als één bezoeker (anders is elk adres in zo'n netwerk 'nieuw')."""
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if isinstance(address, ipaddress.IPv6Address):
        return str(ipaddress.ip_network(f"{address}/64", strict=False))
    return ip


def ip_fingerprint(request) -> str:
    """Niet-omkeerbare verkorte hash van het IP-adres (alleen voor limieten)."""
    return hmac.new(settings.SECRET_KEY.encode(), _limit_network(client_ip(request)).encode(), hashlib.sha256).hexdigest()[:24]


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
