"""Accounts: klanten loggen in met een eenmalige code per e-mail (zonder wachtwoord).

De eigenaar/beheerders hebben een wachtwoord en `is_staff=True`.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

LOGIN_CODE_TTL = timedelta(minutes=20)
LOGIN_CODE_MAX_ATTEMPTS = 5


def normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def _digest(value: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        email = normalize_email(email)
        if not email:
            raise ValueError("Een e-mailadres is verplicht.")
        user = self.model(email=email, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if not password:
            raise ValueError("Een beheerder heeft een wachtwoord nodig.")
        return self._create_user(email, password, **extra)

    def get_by_natural_key(self, username):
        return self.get(email=normalize_email(username))


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("e-mailadres", unique=True)
    name = models.CharField("naam", max_length=120, blank=True)
    is_staff = models.BooleanField("beheerder", default=False)
    is_active = models.BooleanField("actief", default=True)
    date_joined = models.DateTimeField("aangemaakt", default=timezone.now)
    email_verified_at = models.DateTimeField("e-mail bevestigd op", null=True, blank=True)
    anonymized_at = models.DateTimeField("gegevens verwijderd op", null=True, blank=True)
    # Nieuwsbrief en acties: alleen met een eigen vinkje (standaard uit). Tijdstip en tekst van de toestemming bewaard.
    newsletter = models.BooleanField("nieuwsbrief", default=False)
    newsletter_since = models.DateTimeField("nieuwsbrief sinds", null=True, blank=True)
    newsletter_consent = models.CharField("tekst bij de toestemming", max_length=300, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "gebruiker"
        verbose_name_plural = "gebruikers"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        self.email = normalize_email(self.email)
        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        return self.name or self.email

    def get_short_name(self) -> str:
        return self.name or self.email.split("@")[0]

    @property
    def display_name(self) -> str:
        return self.name or self.email


class LoginCode(models.Model):
    """Eenmalige inlogcode (6 cijfers) plus een inloglink-token, beide gehasht opgeslagen."""

    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=64)
    token_hash = models.CharField(max_length=64, unique=True)
    next_url = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "inlogcode"
        verbose_name_plural = "inlogcodes"
        ordering = ["-created_at"]

    @classmethod
    def issue(cls, email: str, next_url: str = "") -> tuple["LoginCode", str, str]:
        email = normalize_email(email)
        code = f"{secrets.randbelow(1_000_000):06d}"
        token = secrets.token_urlsafe(32)
        # Eerdere openstaande codes voor dit adres vervallen.
        cls.objects.filter(email=email, used_at__isnull=True).update(expires_at=timezone.now())
        obj = cls.objects.create(
            email=email,
            code_hash=_digest(f"code:{email}:{code}"),
            token_hash=_digest(f"token:{token}"),
            next_url=next_url[:300],
            expires_at=timezone.now() + LOGIN_CODE_TTL,
        )
        return obj, code, token

    @property
    def is_usable(self) -> bool:
        return (
            self.used_at is None
            and self.expires_at > timezone.now()
            and self.attempts < LOGIN_CODE_MAX_ATTEMPTS
        )

    def check_code(self, code: str) -> bool:
        code = "".join(ch for ch in (code or "") if ch.isdigit())
        return hmac.compare_digest(self.code_hash, _digest(f"code:{self.email}:{code}"))

    @classmethod
    def find_by_token(cls, token: str) -> "LoginCode | None":
        if not token or len(token) > 100:
            return None
        return cls.objects.filter(token_hash=_digest(f"token:{token}")).first()
