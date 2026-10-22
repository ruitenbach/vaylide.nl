"""Het IP-adres van de bezoeker bepalen, beoordelen of dat betrouwbaar is, en veilig meten hoe de proxyketen eruitziet.

Vertrouwen is positioneel en expliciet: alleen de laatste `TRUSTED_PROXY_HOPS` plaatsen van `X-Forwarded-For` zijn
door onze eigen proxy's toegevoegd. Alles links daarvan is bezoekersinvoer en wordt nooit gebruikt.

Of dat getal klopt, kan de code niet weten. Daarom is er een tripwire (`assess`): is het gekozen adres geen aannemelijk
openbaar bezoekersadres (privé, Cloudflare, ongeldig, of de keten is korter dan ingesteld), dan geldt het als
ONBETROUWBAAR. Limieten per IP gebruiken zo'n adres niet; er blijft altijd minstens één IP-onafhankelijke grens
(per account, per uitnodiging of een globale teller met alarm). De Cloudflare-lijst hieronder is alleen voor de
tripwire; raakt hij verouderd, dan valt hooguit de waarschuwing weg, het vertrouwen blijft de ingestelde waarde.
"""
from __future__ import annotations

import ipaddress
import logging
import os
import time
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger(__name__)

# Gepubliceerde Cloudflare-bereiken (https://www.cloudflare.com/ips/), alleen voor de tripwire.
CLOUDFLARE_NETWORKS = tuple(
    ipaddress.ip_network(n)
    for n in (
        "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22", "141.101.64.0/18",
        "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22", "198.41.128.0/17",
        "162.158.0.0/15", "104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
        "2400:cb00::/32", "2606:4700::/32", "2803:f800::/32", "2405:b500::/32", "2405:8100::/32",
        "2a06:98c0::/29", "2c0f:f248::/32",
    )
)

WARN_SECONDS = 3600
_warned_at: dict[str, float] = {}


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


def _forwarded(request) -> list[str]:
    return [p for p in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if p.strip()]


def client_ip(request) -> str:
    """Het IP-adres van de bezoeker, alleen op basis van wat onze eigen proxy's achteraan hebben toegevoegd.

    Met TRUSTED_PROXY_HOPS=N tellen we N plaatsen van rechts. Klopt N niet met de werkelijke keten of is de waarde geen
    geldig IP-adres, dan vallen we terug op REMOTE_ADDR (het adres van de proxy). Of het resultaat bruikbaar is voor
    limieten, beoordeelt `assess`.
    """
    hops = getattr(settings, "TRUSTED_PROXY_HOPS", 0)
    if hops > 0:
        forwarded = _forwarded(request)
        if len(forwarded) >= hops:
            candidate = _valid_ip(forwarded[-hops])
            if candidate:
                return candidate
    return _valid_ip(request.META.get("REMOTE_ADDR", "")) or "onbekend"


def limit_network(ip: str) -> str:
    """Voor limieten telt een heel IPv6-/64-netwerk als één bezoeker (anders is elk adres in zo'n netwerk 'nieuw')."""
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if isinstance(address, ipaddress.IPv6Address):
        return str(ipaddress.ip_network(f"{address}/64", strict=False))
    return ip


def kind_of(value: str) -> str:
    """'openbaar', 'privé' (ook loopback, link-local en documentatiebereiken), 'cloudflare' of 'ongeldig'."""
    ip = _valid_ip(value)
    if not ip:
        return "ongeldig"
    address = ipaddress.ip_address(ip)
    if any(address in network for network in CLOUDFLARE_NETWORKS if network.version == address.version):
        return "cloudflare"
    return "openbaar" if address.is_global else "privé"


def mask_ip(value: str) -> str:
    """Gemaskeerd adres voor het meetscherm: 81.107.x.x of 2001:db8::x. Nooit het volledige adres."""
    ip = _valid_ip(value)
    if not ip:
        return "ongeldig"
    address = ipaddress.ip_address(ip)
    if isinstance(address, ipaddress.IPv4Address):
        a, b, _, _ = ip.split(".")
        return f"{a}.{b}.x.x"
    first = address.exploded.split(":")[:2]
    return f"{first[0]}:{first[1]}::x"


@dataclass(frozen=True)
class IpStatus:
    ip: str
    reliable: bool
    reason: str = ""


REASONS = {
    "geen-proxyinstelling": "VIERLIEF_TRUSTED_PROXY_HOPS staat op 0 terwijl de site achter een proxy draait (alle bezoekers lijken hetzelfde adres te hebben)",
    "keten-te-kort": "X-Forwarded-For bevat minder adressen dan VIERLIEF_TRUSTED_PROXY_HOPS",
    "ongeldig": "de gekozen plaats in X-Forwarded-For is geen geldig IP-adres",
    "niet-openbaar": "de gekozen plaats is een privé- of intern adres (waarde waarschijnlijk te laag)",
    "cloudflare": "de gekozen plaats is een Cloudflare-adres (waarde waarschijnlijk te laag)",
}


def assess(request) -> IpStatus:
    """Is het gekozen adres aannemelijk een bezoeker? Zo niet, dan mag geen limiet erop vertrouwen."""
    hops = getattr(settings, "TRUSTED_PROXY_HOPS", 0)
    ip = client_ip(request)
    if hops <= 0:
        # Zonder proxyinstelling is REMOTE_ADDR de bezoeker (lokaal), behalve op Render: daar is het de proxy.
        if os.environ.get("RENDER"):
            return IpStatus(ip, False, "geen-proxyinstelling")
        return IpStatus(ip, True)
    forwarded = _forwarded(request)
    if len(forwarded) < hops:
        return IpStatus(ip, False, "keten-te-kort")
    chosen = forwarded[-hops]
    kind = kind_of(chosen)
    if kind == "ongeldig":
        return IpStatus(ip, False, "ongeldig")
    if kind == "privé":
        return IpStatus(ip, False, "niet-openbaar")
    if kind == "cloudflare":
        return IpStatus(ip, False, "cloudflare")
    return IpStatus(ip, True)


def warn_if_unreliable(request) -> IpStatus:
    """Beoordeelt het adres en meldt een onbetrouwbaar resultaat hooguit één keer per uur per reden (log, geen mail)."""
    status = assess(request)
    if status.reliable:
        return status
    now = time.monotonic()
    if now - _warned_at.get(status.reason, -WARN_SECONDS) >= 60:  # per proces hooguit eens per minuut naar de cache
        _warned_at[status.reason] = now
        if cache.add(f"ipwarn:{status.reason}", 1, WARN_SECONDS):
            log.warning(
                "IP-herkenning onbetrouwbaar (%s): %s. Limieten per IP-adres worden niet gebruikt; "
                "zie Beheer → Instellingen en docs/BEVEILIGING.md.",
                status.reason, REASONS.get(status.reason, status.reason),
            )
    return status


def measure(request) -> list[tuple[str, str, bool]]:
    """Meetregels voor Beheer → Instellingen (alleen staff, alleen met VIERLIEF_IP_METING in testmodus).

    Geeft per plaats alleen de soort en een gemaskeerd adres; niets wordt opgeslagen of gelogd.
    """
    rows: list[tuple[str, str, bool]] = []
    hops = getattr(settings, "TRUSTED_PROXY_HOPS", 0)
    forwarded = _forwarded(request)
    rows.append(("Gekozen plaats van rechts", str(hops) if hops > 0 else "geen (REMOTE_ADDR)", False))
    for i, entry in enumerate(reversed(forwarded[-8:]), start=1):
        rows.append((f"X-Forwarded-For, plaats {i} van rechts", f"{kind_of(entry)}, {mask_ip(entry)}", False))
    rows.append(("REMOTE_ADDR", f"{kind_of(request.META.get('REMOTE_ADDR', ''))}, {mask_ip(request.META.get('REMOTE_ADDR', ''))}", False))
    chosen = _valid_ip(client_ip(request))
    for header in ("CF-Connecting-IP", "True-Client-IP", "X-Real-IP"):
        raw = request.headers.get(header)
        if raw is None:
            rows.append((header, "afwezig", False))
        else:
            same = "gelijk aan het gekozen adres" if _valid_ip(raw) == chosen else "afwijkend van het gekozen adres"
            rows.append((header, f"aanwezig, {kind_of(raw)}, {mask_ip(raw)}, {same}", False))
    rows.append(("Forwarded", "aanwezig" if request.headers.get("Forwarded") is not None else "afwezig", False))
    return rows
