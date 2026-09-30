from django.conf import settings
from django.utils import timezone

from orders.methods import available_methods

from .ai import ai_configured
from .company import company


def social_links() -> list[dict]:
    """Instagram en TikTok uit de instellingen (Beheer → Instellingen); alleen wat is ingevuld."""
    from .models import SiteConfig

    config = SiteConfig.get()
    links = [("instagram", "Instagram", config.instagram_url), ("tiktok", "TikTok", config.tiktok_url)]
    return [{"icon": icon, "label": label, "url": url} for icon, label, url in links if url]


def test_banner() -> str:
    """Wat de testbalk zegt: met Mollie zijn het echte testbetalingen (geen geld), anders gesimuleerd."""
    payments = "Mollie-testbetalingen, er wordt niets afgeschreven" if settings.PAYMENT_PROVIDER == "mollie" else "betalingen zijn gesimuleerd"
    emails = "e-mails worden niet verstuurd" if settings.EMAIL_MODE == "outbox" else "e-mails worden echt verstuurd"
    return f"{payments} · {emails}"


def vierlief(request):
    return {
        "TEST_MODE": settings.TEST_MODE,
        "TEST_BANNER": test_banner(),
        # Of e-mails alleen worden bewaard (testmodus zonder SMTP); teksten over verzenden hangen hiervan af.
        "EMAIL_OUTBOX": settings.EMAIL_MODE == "outbox",
        # Pas uitgerekend als een template ze gebruikt (voettekst, bestelstap).
        "PAYMENT_METHODS": available_methods,
        "SOCIAL_LINKS": social_links,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "KVK": settings.COMPANY_KVK,
        "BEDRIJF": company,
        "BTW": settings.COMPANY_VAT,
        "BASE_URL": settings.BASE_URL,
        "CURRENT_YEAR": timezone.localdate().year,
        "SLOGAN": "Elk bijzonder moment begint met een uitnodiging.",
        # Tekstvoorstellen via Anthropic (alleen met sleutel); de uitleg bij de knop hangt ervan af.
        "AI_EXTERN": ai_configured,
    }
