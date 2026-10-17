"""Mollie-testbetalingen met kortingen: drie fictieve scenario's, zonder echt geld.

Scenario's (elk een eigen fictief concept en klant): A alleen een kortingscode, B alleen een automatische aanbieding, C beide tegelijk
(de aanbieding is voordeliger, dus alleen die telt en de code wordt niet verbruikt).

Voorwaarden (het script weigert anders): VIERLIEF_MODE=test, VIERLIEF_PAYMENT_PROVIDER=mollie, MOLLIE_API_KEY=test_... (een Mollie-TESTsleutel,
alleen via de omgeving, nooit in Git of een chat; de instellingen weigeren in testmodus al een live_-sleutel), VIERLIEF_PRICING_V2=1,
VIERLIEF_KORTINGSCODES=1 en VIERLIEF_AANBIEDINGEN=1 (alleen voor dit proces; niets wordt op een omgeving geactiveerd) en een eigen, lege testdatabase.
Gebruik een afzonderlijke database (bijvoorbeeld VIERLIEF_DATA_DIR=/tmp/mollie-test); het script maakt gegevens aan.

Stap 1:  .venv/bin/python e2e/mollie_kortingen.py maak        -> maakt de drie bestellingen en toont per scenario het bedrag en de Mollie-testlink
Stap 2:  open elke link, kies bij Mollie 'betaald' (scenario A en B) en bij C bijvoorbeeld 'geannuleerd', daarna:
         .venv/bin/python e2e/mollie_kortingen.py controleer  -> haalt de status bij Mollie op (zonder webhook) en vergelijkt bedrag, status, korting en gebruik
De uitkomst per scenario is 'ok' of 'AFWIJKING: ...'; de exitcode is 1 bij een afwijking."""
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.utils import timezone  # noqa: E402

STAAT = Path(os.environ.get("MOLLIE_KORTINGEN_STAAT", "/tmp/mollie_kortingen.json"))

if not settings.TEST_MODE:
    raise SystemExit("Alleen in testmodus (VIERLIEF_MODE=test).")
if settings.PAYMENT_PROVIDER != "mollie" or not settings.MOLLIE_API_KEY.startswith("test_"):
    raise SystemExit("Zet VIERLIEF_PAYMENT_PROVIDER=mollie en een Mollie-TESTsleutel (MOLLIE_API_KEY=test_...) in de omgeving.")
if not (settings.PRICING_V2 and settings.DISCOUNTS_ENABLED and settings.OFFERS_ENABLED):
    raise SystemExit("Zet voor dit proces VIERLIEF_PRICING_V2=1, VIERLIEF_KORTINGSCODES=1 en VIERLIEF_AANBIEDINGEN=1.")
if not settings.BASE_URL.startswith("https://"):
    print("Let op: zonder https-adres (VIERLIEF_BASE_URL) stuurt de site geen webhook mee; 'controleer' haalt de status dan zelf op.")

from accounts.models import User  # noqa: E402
from catalog.models import Template, format_euro  # noqa: E402
from invitations.services import create_draft, save_draft  # noqa: E402
from kortingen.models import DiscountCode, DiscountRedemption, Offer  # noqa: E402
from orders.models import Order  # noqa: E402
from orders.services import start_checkout, sync_payment  # noqa: E402
from tests.helpers import VaylideTestCase, future_date  # noqa: E402


def concept(email):
    user, _ = User.objects.get_or_create(email=email)
    user.email_verified_at = timezone.now()
    user.save()
    inv = create_draft(occasion="bruiloft", template=Template.objects.get(slug="liefde-op-papier"), owner=user)
    content = VaylideTestCase.complete_content(None, inv)
    return user, save_draft(inv, expected_rev=None, content=content, user=user)


def maak():
    now = timezone.now()
    DiscountCode.objects.get_or_create(code="MOLLIE10", defaults=dict(kind="percent", percent=10))
    DiscountCode.objects.get_or_create(code="MOLLIE5", defaults=dict(kind="percent", percent=5))
    scenarios = {}
    for naam, code, aanbieding in (("A code", "MOLLIE10", False), ("B aanbieding", "", True), ("C beide", "MOLLIE5", True)):
        Offer.objects.get_or_create(name="Mollietest", defaults=dict(kind="percent", percent=20, starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=2), whole_collection=True))
        Offer.objects.filter(name="Mollietest").update(is_active=aanbieding)    # een aanbieding met bestellingen wordt nooit verwijderd (alleen uitgezet)
        user, inv = concept(f"mollie-{naam[0].lower()}@vaylide.test")
        payment = start_checkout(inv, user=user, package_code="luxe", optional_codes=[], terms_accepted=True, delivery_consent=True, service_consent=True,
                                 discount_code=code)
        o = payment.order
        scenarios[naam] = {"order": o.number, "payment": payment.pk, "totaal": o.total_cents, "korting": o.discount_cents, "code": o.discount_code_text,
                           "aanbieding": o.discount_offer_text}
        print(f"{naam}: {o.number}  totaal {format_euro(o.total_cents)} (korting {format_euro(o.discount_cents)}, code '{o.discount_code_text}', aanbieding '{o.discount_offer_text}')\n   {payment.checkout_url}")
    STAAT.write_text(json.dumps(scenarios, indent=1))


def controleer():
    scenarios = json.loads(STAAT.read_text())
    slecht = 0
    from orders.models import Payment

    for naam, s in scenarios.items():
        payment = Payment.objects.get(pk=s["payment"])
        sync_payment(payment, source="controle")
        payment.refresh_from_db()
        order = Order.objects.get(number=s["order"])
        fouten = []
        if payment.amount_cents != s["totaal"] or order.total_cents != s["totaal"]:
            fouten.append("bedrag bij de betaling wijkt af van de bestelling")
        red = DiscountRedemption.objects.filter(order=order).first()
        if s["code"] and red is None:
            fouten.append("kortingscode zonder gebruiksregel")
        if not s["code"] and red is not None:
            fouten.append("gebruiksregel terwijl er geen code is toegepast")
        if payment.status == "paid" and s["code"] and red.state != "redeemed":
            fouten.append("betaald maar de code is niet 'gebruikt'")
        if payment.status in ("canceled", "failed", "expired") and red is not None and red.state == "redeemed":
            fouten.append("niet betaald maar de code staat als gebruikt")
        print(f"{naam}: status {payment.status}, bestelling {order.get_status_display()}, bedrag {format_euro(payment.amount_cents)} -> " + ("ok" if not fouten else "AFWIJKING: " + "; ".join(fouten)))
        slecht += bool(fouten)
    sys.exit(1 if slecht else 0)


if __name__ == "__main__":
    {"maak": maak, "controleer": controleer}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
