"""Bedrijfsgegevens voor de voorwaarden, de contactpagina en de bestelbevestiging.

Niets verzonnen: ontbrekende gegevens blijven herkenbare invulvelden (alleen op de afgeschermde testversie; in
live-modus start de site niet zonder juridische naam en vestigingsadres, zie config/settings.py).
"""
from __future__ import annotations

from django.conf import settings

TRADE_NAME = "VAYLIDE"
NEWLINE = chr(10)


def company() -> dict:
    raw = (settings.COMPANY_ADDRESS or "").replace(NEWLINE, "|")
    address = [line.strip() for line in raw.split("|") if line.strip()]
    data = {
        "handelsnaam": TRADE_NAME,
        "juridische_naam": settings.COMPANY_LEGAL_NAME,
        "adres": address,
        "kvk": settings.COMPANY_KVK,
        "btw": settings.COMPANY_VAT,
        "email": settings.CONTACT_EMAIL,
        "telefoon": settings.COMPANY_PHONE,
    }
    data["ontbreekt"] = [label for key, label in (("juridische_naam", "juridische naam en rechtsvorm"), ("adres", "vestigingsadres"),
                                                  ("kvk", "KvK-nummer")) if not data[key]]
    return data


def as_text(data: dict | None = None) -> str:
    """Voor e-mails: de bedrijfsgegevens als platte tekst (met invulvelden als iets ontbreekt)."""
    data = data or company()
    lines = [f"{TRADE_NAME} is een handelsnaam van {data['juridische_naam'] or '[juridische naam onderneming en rechtsvorm]'}"]
    lines.append("Vestigingsadres: " + (", ".join(data["adres"]) if data["adres"] else "[vestigingsadres]"))
    lines.append(f"KvK-nummer: {data['kvk'] or '[KvK-nummer]'}")
    if data["btw"]:
        lines.append(f"Btw-id: {data['btw']}")
    lines.append(f"E-mail: {data['email']}")
    if data["telefoon"]:
        lines.append(f"Telefoon: {data['telefoon']}")
    return NEWLINE.join(lines)
