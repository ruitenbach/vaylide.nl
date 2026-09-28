"""Betaalproviders.

- TestProvider: gesimuleerde betalingen met een duidelijk gemarkeerde testpagina.
  Alleen beschikbaar in testmodus.
- MollieProvider: voorbereid voor Mollie (iDEAL en andere methoden). De status
  wordt altijd serverzijdig bij Mollie opgevraagd; een webhook bevat alleen het
  betaal-id en is dus niet te vervalsen tot een betaling.
"""
from __future__ import annotations

import json
import logging
import secrets
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import Payment

log = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    pass


@dataclass
class RemoteStatus:
    status: str
    amount_cents: int
    currency: str = "EUR"
    method: str = ""
    paid_at: datetime | None = None


class TestProvider:
    code = "test"
    label = "Testbetaling"

    def create(self, payment: Payment, *, description: str, return_url: str, webhook_url: str) -> tuple[str, str]:
        if not settings.TEST_MODE:
            raise ProviderError("Testbetalingen zijn uitgeschakeld buiten testmodus.")
        ref = f"tst_{secrets.token_urlsafe(12)}"
        payment.test_remote_status = Payment.Status.OPEN
        return ref, reverse("orders:test_checkout", args=[ref])

    def fetch(self, payment: Payment) -> RemoteStatus:
        status = payment.test_remote_status or Payment.Status.OPEN
        return RemoteStatus(
            status=status,
            amount_cents=payment.amount_cents,
            currency=payment.currency,
            method="test" if status == Payment.Status.PAID else "",
            paid_at=timezone.now() if status == Payment.Status.PAID else None,
        )


MOLLIE_STATUS = {
    "open": Payment.Status.OPEN,
    "pending": Payment.Status.PENDING,
    "authorized": Payment.Status.PENDING,
    "paid": Payment.Status.PAID,
    "failed": Payment.Status.FAILED,
    "canceled": Payment.Status.CANCELED,
    "expired": Payment.Status.EXPIRED,
}


class MollieProvider:
    code = "mollie"
    label = "Mollie (iDEAL e.a.)"

    def __init__(self, api_key: str | None = None, base: str | None = None):
        self.api_key = api_key or settings.MOLLIE_API_KEY
        self.base = (base or settings.MOLLIE_API_BASE).rstrip("/")
        if not self.api_key:
            raise ProviderError("MOLLIE_API_KEY ontbreekt.")
        # Tweede slot naast de controle in de instellingen: in testmodus nooit een live-sleutel gebruiken.
        if settings.TEST_MODE and not self.api_key.startswith("test_"):
            raise ProviderError("In testmodus is alleen een Mollie-testsleutel (test_...) toegestaan.")

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Vaylide/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise ProviderError(f"Mollie gaf status {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ProviderError(f"Mollie is niet bereikbaar: {exc}") from exc

    def create(self, payment: Payment, *, description: str, return_url: str, webhook_url: str) -> tuple[str, str]:
        body = {
            "amount": {"currency": payment.currency, "value": f"{Decimal(payment.amount_cents) / 100:.2f}"},
            "description": description[:255],
            "redirectUrl": return_url,
            "locale": "nl_NL",
            "metadata": {"order": payment.order.number, "payment": str(payment.uid)},
        }
        if webhook_url.startswith("https://"):
            body["webhookUrl"] = webhook_url
        else:
            # Mollie meldt alleen aan een https-adres. Zonder webhook volgt de status pas bij terugkeer van de klant.
            log.warning("Geen webhook meegegeven: VIERLIEF_BASE_URL is geen https-adres (%s).", webhook_url)
        data = self._request("POST", "/payments", body)
        try:
            return data["id"], data["_links"]["checkout"]["href"]
        except KeyError as exc:
            raise ProviderError("Onverwacht antwoord van Mollie") from exc

    def fetch(self, payment: Payment) -> RemoteStatus:
        data = self._request("GET", f"/payments/{payment.provider_ref}")
        amount = data.get("amount") or {}
        paid_at = None
        if data.get("paidAt"):
            try:
                paid_at = datetime.fromisoformat(data["paidAt"].replace("Z", "+00:00"))
            except ValueError:
                paid_at = timezone.now()
        return RemoteStatus(
            status=MOLLIE_STATUS.get(data.get("status", ""), Payment.Status.PENDING),
            amount_cents=int((Decimal(amount.get("value", "0")) * 100).to_integral_value()),
            currency=amount.get("currency", ""),
            method=data.get("method") or "",
            paid_at=paid_at,
        )


def get_provider(code: str | None = None):
    code = code or settings.PAYMENT_PROVIDER
    if code == "test":
        return TestProvider()
    if code == "mollie":
        return MollieProvider()
    raise ProviderError(f"Onbekende betaalprovider: {code}")
