"""Kortingscodes: controleren, berekenen, reserveren en vrijgeven.

Kernregels:
- De korting wordt aan de serverzijde berekend en wordt een negatieve regel in de offerte (orders.pricing.Quote). Daardoor volgen bestelling,
  betaling, Mollie-bedrag, bon en e-mail vanzelf hetzelfde bedrag. De browser stuurt alleen de code mee.
- Het te betalen bedrag wordt nooit lager dan settings.DISCOUNT_MIN_TOTAL_CENTS en nooit negatief. Een korting die daar overheen zou gaan, wordt afgetopt.
- Eén code per bestelling; codes stapelen niet.
- Een code wordt gereserveerd bij het aanmaken van de bestelling (in dezelfde vergrendelde transactie), definitief bij de bevestigde betaling en
  vrijgegeven als de bestelling vervalt, mislukt of vervangen wordt. Een reservering telt maar DISCOUNT_RESERVATION_MINUTES mee.
- Een gebruikte code blijft meetellen, ook na een terugbetaling. Alleen een beheerder kan hem handmatig vrijgeven (met reden, vastgelegd).
- Controle per klant: op het account én op een afgeleide sleutel van het e-mailadres (zonder plusje, bij Gmail zonder puntjes). Dat vangt de
  eenvoudigste omwegen, maar is geen waterdichte fraudepreventie: wie een heel ander e-mailadres gebruikt, is een andere klant.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from catalog import prijzen
from catalog.models import format_euro
from .models import DiscountCode, DiscountRedemption, normalize_code

LINE_PREFIX = "korting:"
GMAIL = {"gmail.com", "googlemail.com"}


class DiscountError(ValueError):
    """Een code die niet bruikbaar is. `reason` is een korte sleutel voor tests en logboek, de tekst is voor de klant."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message


@dataclass
class DiscountResult:
    code: DiscountCode
    discount_cents: int
    capped: bool = False
    note: str = ""
    used: bool = True       # False: een lopende aanbieding is voordeliger; de code wordt dan niet gebruikt (en dus ook niet gereserveerd)


def enabled() -> bool:
    return bool(getattr(settings, "DISCOUNTS_ENABLED", False))


def min_total_cents() -> int:
    return max(1, int(getattr(settings, "DISCOUNT_MIN_TOTAL_CENTS", 100)))


def eur(cents: int) -> str:
    """Altijd met twee decimalen, in meldingen: € 1,00."""
    return f"\u20ac {cents // 100},{cents % 100:02d}"


def customer_key(email: str) -> str:
    """Niet-omkeerbare sleutel van het genormaliseerde e-mailadres: kleine letters, zonder plusje, bij Gmail zonder puntjes."""
    email = (email or "").strip().lower()
    local, _, domain = email.partition("@")
    local = local.split("+", 1)[0]
    if domain in GMAIL:
        local = local.replace(".", "")
        domain = "gmail.com"
    return hmac.new(settings.SECRET_KEY.encode(), f"{local}@{domain}".encode(), hashlib.sha256).hexdigest()[:40]


def vat_part_cents(total_cents: int, rate_percent: int | None = None) -> int:
    """Het btw-deel van een bedrag inclusief btw: totaal × tarief / (100 + tarief), op hele centen afgerond (halve naar boven)."""
    rate = settings.VAT_RATE_PERCENT if rate_percent is None else rate_percent
    return (total_cents * rate + (100 + rate) // 2) // (100 + rate)


def end_of_day(day) -> datetime:
    """Het einde van een datum in de tijdzone van de site: 'geldig tot en met'."""
    return timezone.make_aware(datetime.combine(day, time(23, 59, 59, 999999)))


def start_of_day(day) -> datetime:
    return timezone.make_aware(datetime.combine(day, time.min))


def _live(now):
    return Q(state=DiscountRedemption.State.REDEEMED) | Q(state=DiscountRedemption.State.RESERVED, reserved_until__gt=now)


def active_redemptions(code: DiscountCode, *, now=None, exclude_order=None) -> int:
    """Gebruikt of nog geldig gereserveerd."""
    qs = DiscountRedemption.objects.filter(_live(now or timezone.now()), code=code)
    if exclude_order is not None:
        qs = qs.exclude(order=exclude_order)
    return qs.count()


def customer_uses(code: DiscountCode, customer, *, now=None, exclude_order=None) -> int:
    qs = DiscountRedemption.objects.filter(_live(now or timezone.now()), code=code).filter(
        Q(customer=customer) | Q(customer_key=customer_key(customer.email))
    )
    if exclude_order is not None:
        qs = qs.exclude(order=exclude_order)
    return qs.count()


def find_code(raw: str) -> DiscountCode:
    norm = normalize_code(raw)
    code = DiscountCode.objects.filter(code_norm=norm).first() if norm else None
    if code is None:
        raise DiscountError("onbekend", "Deze code kennen we niet. Controleer de spelling.")
    return code


def _date_nl(value) -> str:
    months = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]
    value = timezone.localtime(value)
    return f"{value.day} {months[value.month - 1]} {value.year}"


def check_code(code: DiscountCode, *, subtotal_cents: int, template_version, occasion: str, customer=None, now=None,
               exclude_order=None, count_use: bool = True) -> DiscountResult:
    """Alle regels, in een vaste volgorde. Zonder klant (nog niet ingelogd) wordt de controle per klant overgeslagen; die volgt bij het bestellen."""
    now = now or timezone.now()
    if not code.is_active:
        raise DiscountError("uitgezet", "Deze code is helaas niet meer beschikbaar.")
    if code.starts_at and now < code.starts_at:
        raise DiscountError("nog_niet", f"Deze code is geldig vanaf {_date_nl(code.starts_at)}.")
    if code.ends_at and now > code.ends_at:
        raise DiscountError("verlopen", f"Deze code is verlopen op {_date_nl(code.ends_at)}.")
    if code.occasions and occasion not in code.occasions:
        raise DiscountError("bereik", "Deze code geldt niet voor deze gelegenheid.")
    if code.tiers:
        try:
            indeling = prijzen.tier(template_version)
        except Exception:
            indeling = None
        if indeling not in code.tiers:
            raise DiscountError("bereik", "Deze code geldt niet voor dit ontwerp.")
    if code.pk and code.templates.exists():
        template = getattr(template_version, "template", template_version)
        if template is None or not code.templates.filter(pk=template.pk).exists():
            raise DiscountError("bereik", "Deze code geldt niet voor dit ontwerp.")
    if subtotal_cents < code.min_order_cents:
        raise DiscountError("minimum", f"Deze code geldt vanaf een bestelbedrag van {eur(code.min_order_cents)}.")
    if count_use and code.max_redemptions is not None and active_redemptions(code, now=now, exclude_order=exclude_order) >= code.max_redemptions:
        raise DiscountError("opgebruikt", "Deze code is helaas niet meer beschikbaar.")
    if count_use and customer is not None and customer_uses(code, customer, now=now, exclude_order=exclude_order) >= code.max_per_customer:
        raise DiscountError("al_gebruikt", "Je hebt deze code al gebruikt.")
    if code.kind == DiscountCode.Kind.PERCENT:
        raw = (subtotal_cents * (code.percent or 0) + 50) // 100
    else:
        raw = min(code.amount_cents or 0, subtotal_cents)
    room = subtotal_cents - min_total_cents()
    if room <= 0 or raw <= 0:
        raise DiscountError("ondergrens", f"Met deze code kan het bedrag van deze kaart niet lager dan {eur(min_total_cents())}.")
    discount = min(raw, room)
    capped = discount < raw
    note = f"De korting is aangepast: het bedrag blijft minimaal {eur(min_total_cents())}." if capped else ""
    return DiscountResult(code=code, discount_cents=discount, capped=capped, note=note)


def evaluate(raw: str, *, subtotal_cents: int, template_version, occasion: str, customer=None, now=None) -> DiscountResult:
    """Alleen lezen, om de korting te tonen. Bij het bestellen volgt altijd opnieuw `prepare` onder een slot."""
    return check_code(find_code(raw), subtotal_cents=subtotal_cents, template_version=template_version, occasion=occasion, customer=customer, now=now)


def toepassen(quote, result: DiscountResult) -> DiscountResult:
    """Code en automatische aanbieding stapelen niet: alleen de voordeligste geldt (bij gelijk de aanbieding, zodat er geen code verbruikt wordt).
    Staat er al een aanbieding in de offerte, dan vervangt de code die alleen als hij méér korting geeft. Zet `result.used` en een korte uitleg."""
    from . import aanbiedingen

    offer = quote.offer
    if offer is not None:
        if result.discount_cents <= offer.discount_cents:
            result.used = False
            result.note = f"De aanbieding {offer.name} is voordeliger dan je code, dus die gebruiken we. Je betaalt {format_euro(offer.price_cents)}."
            return result
        aanbiedingen.remove_from_quote(quote)
        result.note = (result.note + " " if result.note else "") + f"Je kortingscode is voordeliger dan de aanbieding {offer.name}, dus die gebruiken we."
    apply_to_quote(quote, result)
    return result


def apply_to_quote(quote, result: DiscountResult) -> None:
    """Zet de korting als negatieve regel in de offerte. De prijsregels zelf blijven ongemoeid."""
    from orders.pricing import QuoteLine

    quote.lines.append(QuoteLine(code=f"{LINE_PREFIX}{result.code.code_norm}", description=f"Kortingscode {result.code.code}", unit_price_cents=-result.discount_cents))
    quote.discount_cents = result.discount_cents
    quote.discount_code = result.code.code


def prepare(raw: str, quote, *, template_version, occasion: str, customer, now=None) -> DiscountResult:
    """Voor het aanmaken van de bestelling, binnen de transactie van start_checkout: vergrendelt de code, controleert alles opnieuw en
    zet de korting in de offerte. Twee klanten tegelijk op de laatste plek: de tweede krijgt 'opgebruikt'."""
    if not enabled():
        raise DiscountError("uit", "Kortingscodes zijn op dit moment niet beschikbaar.")
    code = find_code(raw)
    code = DiscountCode.objects.select_for_update().get(pk=code.pk)
    result = check_code(code, subtotal_cents=quote.subtotal_cents, template_version=template_version, occasion=occasion, customer=customer, now=now)
    return toepassen(quote, result)


def reserve(order, result: DiscountResult, customer, *, now=None) -> DiscountRedemption:
    now = now or timezone.now()
    return DiscountRedemption.objects.create(
        code=result.code, order=order, customer=customer, customer_key=customer_key(customer.email), amount_cents=result.discount_cents,
        state=DiscountRedemption.State.RESERVED, reserved_until=now + timedelta(minutes=settings.DISCOUNT_RESERVATION_MINUTES),
    )


def _redemption(order, lock=False):
    qs = DiscountRedemption.objects.filter(order=order)
    return (qs.select_for_update() if lock else qs).first()


def release_reserved(orders, reason: str = "bestelling vervallen") -> int:
    """Geeft gereserveerde (nog niet betaalde) codes vrij. Een gebruikte code blijft gebruikt."""
    ids = [o.pk if hasattr(o, "pk") else o for o in orders]
    return DiscountRedemption.objects.filter(order_id__in=ids, state=DiscountRedemption.State.RESERVED).update(
        state=DiscountRedemption.State.RELEASED, released_at=timezone.now(), released_reason=reason[:200]
    )


def confirm(order, *, now=None) -> str:
    """Bij de eerste bevestigde betaling (in dezelfde transactie): gereserveerd → gebruikt. Is de reservering intussen verlopen of vrijgegeven
    en zou het maximum nu overschreden zijn, dan blijft de korting staan (de klant heeft dit bedrag betaald) en wordt het vastgelegd.
    Geeft een korte tekst voor het betalingslogboek terug, of een lege tekst."""
    now = now or timezone.now()
    red = _redemption(order, lock=True)
    if red is None or red.state == DiscountRedemption.State.REDEEMED:
        return ""
    code = DiscountCode.objects.select_for_update().get(pk=red.code_id)
    was = red.state
    over = []
    if code.max_redemptions is not None and active_redemptions(code, now=now, exclude_order=order) >= code.max_redemptions:
        over.append("maximum aantal keer overschreden")
    if customer_uses(code, red.customer, now=now, exclude_order=order) >= code.max_per_customer:
        over.append("maximum per klant overschreden")
    red.state = DiscountRedemption.State.REDEEMED
    red.redeemed_at = now
    red.reserved_until = None
    red.released_at = None
    red.released_reason = ""
    if over or was == DiscountRedemption.State.RELEASED:
        red.note = ("Betaling kwam binnen na vrijgave van de code" if was == DiscountRedemption.State.RELEASED else "Betaling na verlopen reservering") + (
            "; " + ", ".join(over) if over else "") + "."
    red.save()
    return f" Kortingscode {code.code} gebruikt." + (f" Let op: {red.note}" if red.note else "")


def ensure_reserved(order, *, now=None) -> None:
    """Vóór een nieuwe betaalpoging voor een bestaande bestelling met korting: de reservering verlengen, of opnieuw maken als hij vervallen
    is. Kan dat niet meer (code uitgezet, verlopen of opgebruikt), dan volgt een DiscountError en wordt er niet betaald."""
    now = now or timezone.now()
    red = _redemption(order, lock=True)
    if red is None or red.state == DiscountRedemption.State.REDEEMED:
        return
    code = DiscountCode.objects.select_for_update().get(pk=red.code_id)
    if red.state == DiscountRedemption.State.RESERVED and red.reserved_until and red.reserved_until > now:
        pass    # staat nog, telt al mee
    else:
        # Opnieuw reserveren: alles opnieuw toetsen, behalve het bereik en het bedrag (de bestelling zelf ligt vast).
        if not code.is_active or (code.starts_at and now < code.starts_at) or (code.ends_at and now > code.ends_at):
            raise DiscountError("verlopen", "De kortingscode bij deze bestelling is niet meer geldig.")
        if code.max_redemptions is not None and active_redemptions(code, now=now, exclude_order=order) >= code.max_redemptions:
            raise DiscountError("opgebruikt", "De kortingscode bij deze bestelling is niet meer beschikbaar.")
        if customer_uses(code, red.customer, now=now, exclude_order=order) >= code.max_per_customer:
            raise DiscountError("al_gebruikt", "Je hebt deze kortingscode al gebruikt.")
    red.state = DiscountRedemption.State.RESERVED
    red.reserved_until = now + timedelta(minutes=settings.DISCOUNT_RESERVATION_MINUTES)
    red.released_at = None
    red.released_reason = ""
    red.save()


def release_by_staff(order, user, reason: str) -> bool:
    """Een beheerder maakt een gebruikte (of gereserveerde) code weer beschikbaar, bijvoorbeeld na een terugbetaling. De reden is verplicht en
    het gebeurt met naam en tijdstip in het logboek van de bestelling."""
    from orders.models import PaymentEvent

    reason = (reason or "").strip()
    if not reason:
        raise ValueError("Geef een reden op.")
    with transaction.atomic():
        red = _redemption(order, lock=True)
        if red is None or red.state == DiscountRedemption.State.RELEASED:
            return False
        was = red.get_state_display().lower()
        red.state = DiscountRedemption.State.RELEASED
        red.released_at = timezone.now()
        red.released_by = user
        red.released_reason = reason[:200]
        red.save()
        payment = order.latest_payment
        if payment is not None:
            PaymentEvent.objects.create(
                payment=payment, provider=payment.provider, provider_ref=payment.provider_ref, source="beheer", remote_status=order.status,
                outcome=f"Kortingscode {red.code.code} ({was}) vrijgegeven door {user.email}: {reason}"[:200],
            )
    return True
