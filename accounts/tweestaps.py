"""Tweestapsverificatie (TOTP, RFC 6238) voor Beheer en Django-admin. Alleen voor medewerkers (is_staff); klanten en gasten niet.

- Het TOTP-geheim wordt versleuteld bewaard (Fernet) met een eigen sleutel uit de omgeving (VIERLIEF_2FA_SLEUTEL), niet met SECRET_KEY.
  Meerdere sleutels (komma) mogen: de eerste versleutelt, alle ontsleutelen (sleutel vervangen zonder alles opnieuw in te stellen).
- Herstelcodes worden alleen als HMAC-hash bewaard en zijn eenmalig. Ze worden één keer getoond, nooit gelogd of gemaild.
- Een code werkt maar één keer (last_used_step) en het invoeren is begrensd per account en per IP-netwerk.
- De poort (accounts/middleware.py) behandelt een medewerker zonder bevestigde tweede stap als niet ingelogd, op elke URL.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import os
import secrets
import struct
import time
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from core.utils import rate_exceeded, rate_limit, reliable_ip_fingerprint

from .models import RecoveryCode, TwoFactor

PERIOD = 30
DIGITS = 6
WINDOW_STEPS = 1            # een code van de vorige of volgende periode telt ook (klokverschil)
ISSUER = "VAYLIDE"
RECOVERY_COUNT = 10
RECOVERY_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"   # zonder i, l, o, 0, 1
RECOVERY_LENGTH = 12
SESSION_KEY = "vierlief_2fa_ok"
SESSION_PENDING = "vierlief_2fa_nieuw"

ATTEMPT_WINDOW = 900
USER_FAILURES = 5
IP_FAILURES = 20
BLOCK_MESSAGE = "Te veel pogingen met een code. Wacht een kwartier en probeer het opnieuw."


class NietBeschikbaar(Exception):
    """Er is geen sleutel voor het versleutelen van 2FA-geheimen ingesteld."""


def sleutelfouten() -> tuple[type[Exception], ...]:
    """Fouten die betekenen dat de sleutel ontbreekt of niet bij de opgeslagen geheimen past."""
    from cryptography.fernet import InvalidToken

    return (NietBeschikbaar, InvalidToken)


# --- versleuteling ------------------------------------------------------------
def _keys() -> list[str]:
    return [key for key in getattr(settings, "TWOFA_KEYS", []) if key]


def beschikbaar() -> bool:
    return bool(_keys())


def _fernet():
    from cryptography.fernet import Fernet, MultiFernet

    keys = _keys()
    if not keys:
        raise NietBeschikbaar("VIERLIEF_2FA_SLEUTEL ontbreekt.")
    return MultiFernet([Fernet(key.encode()) for key in keys])


def versleutel(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def ontsleutel(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


def _hash_key() -> bytes:
    keys = _keys()
    if not keys:
        raise NietBeschikbaar("VIERLIEF_2FA_SLEUTEL ontbreekt.")
    return hashlib.sha256(b"vaylide-herstelcodes:" + keys[0].encode()).digest()


# --- TOTP ---------------------------------------------------------------------
def nieuw_geheim() -> str:
    return base64.b32encode(os.urandom(20)).decode()      # 160 bit, base32 zoals authenticator-apps verwachten


def _code(secret: str, step: int) -> str:
    key = base64.b32decode(secret.replace(" ", "").upper() + "=" * (-len(secret.replace(" ", "")) % 8))
    digest = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** DIGITS)
    return f"{number:0{DIGITS}d}"


def huidige_stap() -> int:
    return int(time.time() // PERIOD)


def passende_stap(secret: str, invoer: str, na_stap: int = 0) -> int | None:
    """De periode waarin de code klopt (hoger dan na_stap), of None."""
    invoer = "".join(invoer.split())
    if len(invoer) != DIGITS or not invoer.isdigit():
        return None
    nu = huidige_stap()
    gevonden = None
    for stap in range(nu - WINDOW_STEPS, nu + WINDOW_STEPS + 1):       # altijd alles vergelijken, zonder vroegtijdig stoppen
        if hmac.compare_digest(_code(secret, stap), invoer) and stap > na_stap:
            gevonden = stap
    return gevonden


def provisioning_uri(email: str, secret: str) -> str:
    label = quote(f"{ISSUER}:{email}", safe="")
    return f"otpauth://totp/{label}?secret={secret}&issuer={ISSUER}&algorithm=SHA1&digits={DIGITS}&period={PERIOD}"


def qr_svg(uri: str) -> bytes:
    import segno

    buffer = io.BytesIO()
    segno.make(uri, error="m").save(buffer, kind="svg", scale=6, border=3, dark="#000000", light="#ffffff", xmldecl=False)
    return buffer.getvalue()


def groepeer(secret: str) -> str:
    return " ".join(secret[i:i + 4] for i in range(0, len(secret), 4))


# --- status en sessie ---------------------------------------------------------
def van(user) -> TwoFactor | None:
    if not getattr(user, "pk", None):
        return None
    try:
        return user.tweestaps
    except TwoFactor.DoesNotExist:
        return None


def _token(tf: TwoFactor) -> str:
    message = f"2fa:{tf.user_id}:{tf.pk}:{tf.confirmed_at.isoformat()}"
    return hmac.new(settings.SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()


def markeer_geverifieerd(request, tf: TwoFactor) -> None:
    request.session.cycle_key()
    request.session[SESSION_KEY] = _token(tf)


def is_geverifieerd(request, tf: TwoFactor) -> bool:
    return hmac.compare_digest(str(request.session.get(SESSION_KEY, "")), _token(tf))


def toegang(request) -> str:
    """'ok', 'controle' (code nodig) of 'instellen' (verplicht maar nog niet ingesteld) voor een ingelogde medewerker."""
    tf = van(request.user)
    if tf is None:
        return "instellen" if settings.TWOFA_REQUIRED else "ok"
    return "ok" if is_geverifieerd(request, tf) else "controle"


# --- herstelcodes -------------------------------------------------------------
def _normaliseer(invoer: str) -> str:
    return "".join(ch for ch in invoer.lower() if ch.isalnum())


def _hash_code(invoer: str) -> str:
    return hmac.new(_hash_key(), _normaliseer(invoer).encode(), hashlib.sha256).hexdigest()


def maak_herstelcodes(user) -> list[str]:
    """Vervangt alle herstelcodes door nieuwe. Geeft de codes terug om één keer te tonen."""
    RecoveryCode.objects.filter(user=user).delete()
    codes = []
    for _ in range(RECOVERY_COUNT):
        raw = "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(RECOVERY_LENGTH))
        RecoveryCode.objects.create(user=user, code_hash=_hash_code(raw))
        codes.append("-".join(raw[i:i + 4] for i in range(0, RECOVERY_LENGTH, 4)))
    return codes


def herstelcodes_over(user) -> int:
    return RecoveryCode.objects.filter(user=user, used_at__isnull=True).count()


def gebruik_herstelcode(user, invoer: str) -> bool:
    if len(_normaliseer(invoer)) != RECOVERY_LENGTH:
        return False
    return RecoveryCode.objects.filter(user=user, code_hash=_hash_code(invoer), used_at__isnull=True).update(used_at=timezone.now()) == 1


# --- controleren van invoer ---------------------------------------------------
def controleer_totp(tf: TwoFactor, invoer: str) -> bool:
    """Klopt de code én is hij nog niet gebruikt? Legt het gebruik vast (atomair, dus ook tegen twee gelijktijdige pogingen)."""
    stap = passende_stap(ontsleutel(tf.secret_enc), invoer, tf.last_used_step)
    if stap is None:
        return False
    if TwoFactor.objects.filter(pk=tf.pk, last_used_step__lt=stap).update(last_used_step=stap) != 1:
        return False
    tf.last_used_step = stap
    return True


def controleer_invoer(tf: TwoFactor, invoer: str) -> str | None:
    """'totp' of 'herstel' als de invoer klopt, anders None. Geeft een sleutelfout (zie sleutelfouten) als de sleutel niet past."""
    ontsleutel(tf.secret_enc)       # past de sleutel niet, dan stopt het hier, ook voor herstelcodes
    schoon = "".join(invoer.split())
    if schoon.isdigit() and len(schoon) == DIGITS:
        return "totp" if controleer_totp(tf, schoon) else None
    return "herstel" if gebruik_herstelcode(tf.user, invoer) else None


# --- begrenzing ---------------------------------------------------------------
def _user_key(user) -> str:
    return f"2fa-user:{user.pk}"


def _ip_key(request) -> str | None:
    fingerprint = reliable_ip_fingerprint(request)
    return f"2fa-ip:{fingerprint}" if fingerprint else None


def geblokkeerd(request, user) -> bool:
    ip_key = _ip_key(request)
    if ip_key and rate_exceeded(ip_key, IP_FAILURES, ATTEMPT_WINDOW):
        return True
    return rate_exceeded(_user_key(user), USER_FAILURES, ATTEMPT_WINDOW)


def registreer_mislukking(request, user) -> None:
    ip_key = _ip_key(request)
    if ip_key:
        rate_limit(ip_key, IP_FAILURES, ATTEMPT_WINDOW)
    rate_limit(_user_key(user), USER_FAILURES, ATTEMPT_WINDOW)


def registreer_succes(user) -> None:
    cache.delete(f"rl:{_user_key(user)}:{int(time.time() // ATTEMPT_WINDOW)}")
