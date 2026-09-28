"""Eenvoudige, betrouwbare takenwachtrij in de database.

- `enqueue` is idempotent via `unique_key` (herhaalde betalingsmeldingen maken
  dus geen tweede publicatie- of e-mailtaak aan).
- Taken worden direct na de transactie geprobeerd (inline) en bij een fout
  later opnieuw door `manage.py process_jobs` (cron of worker).
- Na het maximale aantal pogingen krijgt een taak de status 'dead' en is hij
  zichtbaar in de beheeromgeving met een knop 'Opnieuw proberen'.
"""
from __future__ import annotations

import logging
import traceback
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.module_loading import import_string

from .models import Job

log = logging.getLogger(__name__)

HANDLERS = {
    "send_email": "processing.emails.handle_send_email",
    "fulfil_order": "orders.fulfilment.handle_fulfil_order",
    "deliver_order": "orders.fulfilment.handle_deliver_order",
    "fulfil_custom_order": "orders.fulfilment.handle_fulfil_custom_order",
    "assess_request": "wishes.services.handle_assess_request",
}
BACKOFF_SECONDS = [60, 5 * 60, 15 * 60, 60 * 60, 3 * 60 * 60, 12 * 60 * 60]
LOCK_MINUTES = 10


def enqueue(kind: str, payload: dict | None = None, *, unique_key: str | None = None, order=None,
            invitation=None, max_attempts: int = 6, run_inline: bool | None = None) -> Job:
    if kind not in HANDLERS:
        raise ValueError(f"Onbekend taaktype: {kind}")
    job = None
    if unique_key:
        job = Job.objects.filter(unique_key=unique_key).first()
    if job is None:
        try:
            with transaction.atomic():
                job = Job.objects.create(
                    kind=kind,
                    payload=payload or {},
                    unique_key=unique_key,
                    order=order,
                    invitation=invitation,
                    max_attempts=max_attempts,
                )
        except IntegrityError:
            job = Job.objects.get(unique_key=unique_key)
            return job
        inline = settings.JOBS_RUN_INLINE if run_inline is None else run_inline
        if inline:
            job_id = job.pk
            transaction.on_commit(lambda: run_job(job_id))
    return job


def _claim(job_id: int) -> bool:
    now = timezone.now()
    claimed = (
        Job.objects.filter(pk=job_id, status__in=[Job.Status.PENDING, Job.Status.FAILED], run_after__lte=now)
        .exclude(locked_until__gt=now)
        .update(status=Job.Status.RUNNING, locked_until=now + timedelta(minutes=LOCK_MINUTES), updated_at=now)
    )
    return claimed == 1


def run_job(job_id: int) -> bool:
    """Voert één taak uit. Geeft True bij succes."""
    if not _claim(job_id):
        return False
    job = Job.objects.get(pk=job_id)
    handler = import_string(HANDLERS[job.kind])
    try:
        handler(job)
    except Exception as exc:  # noqa: BLE001 - elke fout moet zichtbaar worden in beheer
        job.attempts += 1
        job.last_error = f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc(limit=6)}"[:4000]
        job.locked_until = None
        if job.attempts >= job.max_attempts:
            job.status = Job.Status.DEAD
            job.finished_at = timezone.now()
            _on_dead(job)
        else:
            job.status = Job.Status.FAILED
            delay = BACKOFF_SECONDS[min(job.attempts - 1, len(BACKOFF_SECONDS) - 1)]
            job.run_after = timezone.now() + timedelta(seconds=delay)
        job.save()
        log.warning("Taak %s (%s) mislukt, poging %s: %s", job.pk, job.kind, job.attempts, exc)
        _after_failure(job)
        return False
    job.attempts += 1
    job.status = Job.Status.DONE
    job.last_error = ""
    job.locked_until = None
    job.finished_at = timezone.now()
    job.save()
    return True


def _after_failure(job: Job) -> None:
    """Werkt de verwerkingsstatus van de bestelling bij, zodat klant en eigenaar het zien."""
    if job.kind == "fulfil_order" and job.order_id:
        from orders.models import Order

        Order.objects.filter(pk=job.order_id).exclude(fulfilment_status=Order.Fulfilment.DONE).update(
            fulfilment_status=Order.Fulfilment.ATTENTION if job.status == Job.Status.DEAD else Order.Fulfilment.PROCESSING,
            fulfilment_note="Publiceren is nog niet gelukt; we proberen het automatisch opnieuw."
            if job.status != Job.Status.DEAD
            else "Publiceren is meerdere keren mislukt. Het Vaylide-team is ingeschakeld.",
        )


def _on_dead(job: Job) -> None:
    try:
        from .emails import notify_owner_failure

        if job.kind != "send_email" or not (job.payload or {}).get("owner_alert"):
            notify_owner_failure(job)
    except Exception:  # pragma: no cover - melden mag de verwerking nooit breken
        log.exception("Kon eigenaar niet informeren over mislukte taak %s", job.pk)


def retry(job: Job, *, run_now: bool = True) -> Job:
    job.status = Job.Status.PENDING
    job.run_after = timezone.now()
    job.locked_until = None
    if job.attempts >= job.max_attempts:
        job.max_attempts = job.attempts + 3
    job.save()
    if run_now:
        run_job(job.pk)
        job.refresh_from_db()
    return job


def process_due(limit: int = 50) -> int:
    now = timezone.now()
    ids = list(
        Job.objects.filter(status__in=[Job.Status.PENDING, Job.Status.FAILED], run_after__lte=now)
        .exclude(locked_until__gt=now)
        .order_by("run_after")
        .values_list("pk", flat=True)[:limit]
    )
    # Taken die hangen (proces gestopt tijdens uitvoering) komen na de lock-tijd terug.
    Job.objects.filter(status=Job.Status.RUNNING, locked_until__lt=now).update(status=Job.Status.FAILED, locked_until=None)
    done = 0
    for job_id in ids:
        if run_job(job_id):
            done += 1
    return done
