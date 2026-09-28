from django.conf import settings
from django.utils import timezone


def test_banner() -> str:
    """Wat de testbalk zegt: met Mollie zijn het echte testbetalingen (geen geld), anders gesimuleerd."""
    payments = "Mollie-testbetalingen, er wordt niets afgeschreven" if settings.PAYMENT_PROVIDER == "mollie" else "betalingen zijn gesimuleerd"
    emails = "e-mails worden niet verstuurd" if settings.EMAIL_MODE == "outbox" else "e-mails worden echt verstuurd"
    return f"{payments} · {emails}"


def vierlief(request):
    return {
        "TEST_MODE": settings.TEST_MODE,
        "TEST_BANNER": test_banner(),
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "BASE_URL": settings.BASE_URL,
        "CURRENT_YEAR": timezone.localdate().year,
        "SLOGAN": "Elk bijzonder moment begint met een uitnodiging.",
    }
