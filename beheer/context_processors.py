"""Tellers in het beheermenu (alleen voor beheerders op /beheer/)."""
from django.db.models import Q


def nav_counts(request):
    if not request.path.startswith("/beheer/") or not getattr(request, "user", None) or not request.user.is_authenticated or not request.user.is_staff or not getattr(request, "tweestaps_ok", True):
        return {}
    from core.models import ContactMessage
    from orders.models import Order
    from processing.models import Job
    from wishes.models import CustomRequest

    from django.conf import settings

    from catalog import prijsbeheer

    return {
        "prijs_problemen": prijsbeheer.problemen(),     # leeg zolang prijsbeheer uit staat of alle bedragen geldig zijn
        "korting_aan": settings.DISCOUNTS_ENABLED,
        "aanbod_aan": settings.OFFERS_ENABLED,
        "nav_counts": {
            "wishes": CustomRequest.objects.filter(unread_by_staff=True).exclude(status=CustomRequest.Status.CLOSED).count(),
            "orders": Order.objects.filter(fulfilment_status=Order.Fulfilment.ATTENTION).count(),
            "jobs": Job.objects.filter(Q(status=Job.Status.DEAD) | Q(status=Job.Status.FAILED)).count(),
            "contact": ContactMessage.objects.filter(handled_at__isnull=True).count(),
        }
    }
