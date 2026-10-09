from django.conf import settings
from django.utils import timezone
from django.utils.functional import SimpleLazyObject

from orders.methods import available_methods

from .ai import ai_configured
from .analytics import analyse_op_pagina, clarity_op_pagina, gtm_context
from .company import company
from .social import social_links


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
        # Microsoft Clarity: alleen als het project-id is ingesteld; 'hier' zegt of het op deze pagina mag draaien (na toestemming).
        "CLARITY": {"id": settings.CLARITY_ID, "hier": clarity_op_pagina(request.path)} if settings.CLARITY_ID else None,
        # Google Analytics 4 via Google Tag Manager (zelfde toestemming). Lazy: de gebeurtenissen in de sessie worden pas uit de wachtrij gehaald als de
        # toestemmingsbalk ze echt rendert (één keer per pagina), niet als een los stuk template (zoals de live kaart) dezelfde context krijgt.
        "GTM": SimpleLazyObject(lambda: gtm_context(request)),
        # Is er iets om toestemming voor te vragen (Clarity of Google), en mag er op deze pagina iets gemeten worden?
        "ANALYSE": bool(settings.CLARITY_ID or settings.GTM_ID),
        "ANALYSE_HIER": analyse_op_pagina(request.path),
    }
