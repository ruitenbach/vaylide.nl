"""Bedrijfslogica rond uitnodigingen: concepten, versies, publiceren en herstellen.

Wijzigingen aan een concept gebruiken optimistische vergrendeling (`draft_rev`):
wie opslaat op basis van een verouderde versie krijgt een conflictmelding in
plaats van ongemerkt andermans (bijv. handmatige) aanpassingen te overschrijven.
"""
from __future__ import annotations

import secrets
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone
from django.utils.text import slugify

from catalog.occasions import display_title, occasion_config

from .content import SOORTEN, default_content, event_times, normalize_content, publish_issues, referenced_assets
from .models import Invitation, InvitationVersion, MediaAsset, Source

SLUG_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


class DraftConflict(Exception):
    """Het concept is intussen door iemand anders (of in een ander venster) gewijzigd."""

    def __init__(self, invitation: Invitation):
        super().__init__("Concept is intussen gewijzigd")
        self.invitation = invitation


class PublishBlocked(Exception):
    def __init__(self, issues):
        super().__init__("Uitnodiging is nog niet compleet")
        self.issues = issues


def create_draft(*, occasion: str, template, owner=None, palette: str = "", soort: str = "") -> Invitation:
    version = template.current_version
    # Een onbekende kleur valt terug op de standaardkleur van het ontwerp.
    keys = [p.get("key") for p in version.palettes]
    content = default_content(occasion, palette if palette in keys else version.default_palette_key)
    # Uitnodiging of wenskaart (alleen waar de gelegenheid dat kent, zoals Kerst).
    if soort in SOORTEN and occasion_config(occasion).get("event_optional"):
        content["soort"] = soort
    return Invitation.objects.create(
        owner=owner,
        occasion=occasion,
        template_version=version,
        draft_content=content,
        wizard_step="gegevens",
        draft_updated_by=owner,
        draft_updated_source=Source.CUSTOMER,
    )


def clean_asset_refs(invitation: Invitation, content: dict) -> dict:
    """Verwijdert verwijzingen naar uploads die niet bij deze uitnodiging horen."""
    photos = set(
        str(u) for u in MediaAsset.objects.filter(invitation=invitation, kind=MediaAsset.Kind.PHOTO).values_list("uid", flat=True)
    )
    audio = set(
        str(u) for u in MediaAsset.objects.filter(invitation=invitation, kind=MediaAsset.Kind.AUDIO).values_list("uid", flat=True)
    )
    hero = (content.get("photos") or {}).get("hero")
    if isinstance(hero, dict) and "asset" in hero and str(hero.get("asset")) not in photos:
        content["photos"]["hero"] = None
    gallery = []
    for item in (content.get("photos") or {}).get("gallery") or []:
        if isinstance(item, dict) and str(item.get("asset")) in photos:
            gallery.append(item)
    content.setdefault("photos", {})["gallery"] = gallery
    music = content.get("music") or {}
    if music.get("asset") and str(music["asset"]) not in audio:
        content["music"]["asset"] = None
    return content


def save_draft(
    invitation: Invitation,
    *,
    expected_rev: int | None,
    user=None,
    source: str = Source.CUSTOMER,
    content: dict | None = None,
    overrides: dict | None = None,
    template_version=None,
    occasion: str | None = None,
    step: str | None = None,
) -> Invitation:
    with transaction.atomic():
        inv = Invitation.objects.select_for_update().get(pk=invitation.pk)
        if expected_rev is not None and inv.draft_rev != expected_rev:
            raise DraftConflict(inv)
        if occasion is not None and occasion != inv.occasion:
            inv.occasion = occasion
        if template_version is not None:
            inv.template_version = template_version
        if content is not None:
            palette = (content.get("style") or {}).get("palette") or inv.template_version.default_palette_key
            normalized = normalize_content(content, inv.occasion, palette)
            # Kleurvariant moet bij het (eventueel nieuwe) ontwerp horen.
            keys = [p.get("key") for p in inv.template_version.palettes]
            if normalized["style"]["palette"] not in keys:
                normalized["style"]["palette"] = inv.template_version.default_palette_key
            inv.draft_content = clean_asset_refs(inv, normalized)
        if overrides is not None:
            inv.draft_overrides = overrides
        inv.title = display_title(inv.occasion, inv.draft_content)[:200]
        inv.draft_rev += 1
        inv.draft_updated_at = timezone.now()
        inv.draft_updated_by = user if getattr(user, "is_authenticated", False) else None
        inv.draft_updated_source = source
        if step:
            inv.wizard_step = step
        inv.save()
    return inv


def _next_version_number(invitation: Invitation) -> int:
    return (invitation.versions.aggregate(m=Max("number"))["m"] or 0) + 1


def snapshot(invitation: Invitation, *, source: str, user=None, note: str = "") -> InvitationVersion:
    for _ in range(3):
        try:
            with transaction.atomic():
                return InvitationVersion.objects.create(
                    invitation=invitation,
                    number=_next_version_number(invitation),
                    content=invitation.draft_content,
                    overrides=invitation.draft_overrides,
                    template_version=invitation.template_version,
                    source=source,
                    created_by=user if getattr(user, "is_authenticated", False) else None,
                    note=note[:200],
                )
        except IntegrityError:
            continue
    raise RuntimeError("Versie kon niet worden opgeslagen")


def assign_slug(invitation: Invitation) -> str:
    if invitation.slug:
        return invitation.slug
    base = slugify(invitation.title.replace("&", "en"))[:40].strip("-") or "uitnodiging"
    for _ in range(20):
        # 8 tekens (31^8 ≈ 8,5·10^11): de titel is vaak te raden, het achtervoegsel niet.
        suffix = "".join(secrets.choice(SLUG_ALPHABET) for _ in range(8))
        candidate = f"{base}-{suffix}"
        if not Invitation.objects.filter(slug=candidate).exists():
            invitation.slug = candidate
            return candidate
    raise RuntimeError("Kon geen unieke link maken")


def publish_version(invitation: Invitation, version: InvitationVersion, *, available_until=None) -> Invitation:
    """Maakt een versie publiek op de vaste link van de uitnodiging (idempotent)."""
    with transaction.atomic():
        inv = Invitation.objects.select_for_update().get(pk=invitation.pk)
        now = timezone.now()
        assign_slug(inv)
        if inv.published_version_id == version.pk and inv.status == Invitation.Status.LIVE:
            return inv
        version.published_at = now
        version.save(update_fields=["published_at"])
        inv.published_version = version
        inv.status = Invitation.Status.LIVE
        inv.first_published_at = inv.first_published_at or now
        inv.last_published_at = now
        if available_until is not None:
            inv.available_until = available_until
        times = event_times(version.content)
        inv.event_start = times.start
        inv.rsvp_deadline = times.rsvp_deadline
        if inv.draft_content == version.content and inv.draft_overrides == version.overrides:
            inv.draft_base_version = version
        inv.save()
    return inv


def publish_draft(invitation: Invitation, *, user, source: str, expected_rev: int | None, note: str = "") -> InvitationVersion:
    """Publiceert het huidige concept van een al betaalde uitnodiging op dezelfde link."""
    with transaction.atomic():
        inv = Invitation.objects.select_for_update().get(pk=invitation.pk)
        if expected_rev is not None and inv.draft_rev != expected_rev:
            raise DraftConflict(inv)
        issues = [i for i in publish_issues(inv.draft_content, inv.occasion, first_publication=False) if i.blocking]
        if issues:
            raise PublishBlocked(issues)
        version = snapshot(inv, source=source, user=user, note=note or "Wijzigingen gepubliceerd")
        inv = publish_version(inv, version)
        inv.draft_base_version = version
        inv.save(update_fields=["draft_base_version"])
    return version


def restore_version(invitation: Invitation, version: InvitationVersion, *, user, source: str, expected_rev: int | None) -> Invitation:
    """Zet een eerdere versie terug in het concept. Het huidige concept wordt eerst bewaard."""
    with transaction.atomic():
        inv = Invitation.objects.select_for_update().get(pk=invitation.pk)
        if expected_rev is not None and inv.draft_rev != expected_rev:
            raise DraftConflict(inv)
        latest = inv.versions.order_by("-number").first()
        unchanged = latest and latest.content == inv.draft_content and latest.overrides == inv.draft_overrides
        if not unchanged:
            snapshot(inv, source=Source.SYSTEM, user=user, note=f"Automatisch bewaard vóór herstel van versie {version.number}")
        inv.draft_content = version.content
        inv.draft_overrides = version.overrides
        inv.template_version = version.template_version
        inv.title = display_title(inv.occasion, inv.draft_content)[:200]
        inv.draft_rev += 1
        inv.draft_updated_at = timezone.now()
        inv.draft_updated_by = user if getattr(user, "is_authenticated", False) else None
        inv.draft_updated_source = source
        inv.save()
    return inv


def availability_end(months: int, start=None):
    start = start or timezone.now()
    return start + timedelta(days=round(months * 30.44))


def referenced_by_any_version(invitation: Invitation) -> set[str]:
    uids = referenced_assets(invitation.draft_content)
    for content in invitation.versions.values_list("content", flat=True):
        uids |= referenced_assets(content)
    return uids
