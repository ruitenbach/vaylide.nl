"""Django-instellingen voor Vaylide.

Alle omgevingsafhankelijke waarden komen uit omgevingsvariabelen (of een lokaal
`.env`-bestand, zie `.env.example`). Er staan geen geheimen in de broncode.

Belangrijkste schakelaar: VIERLIEF_MODE
  - "test" (standaard): betalingen zijn gesimuleerd, e-mails worden alleen in de
    database bewaard (zichtbaar in de beheeromgeving) en op iedere pagina staat
    een duidelijke testmodus-melding.
  - "live": vereist een echte betaalprovider en e-mailverzending; de applicatie
    weigert te starten als die ontbreken.
"""
from __future__ import annotations

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimale .env-lezer (KEY=waarde per regel). Bestaande variabelen winnen."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


if os.environ.get("VIERLIEF_SKIP_DOTENV") != "1":
    _load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def env_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "ja", "on"}


def env_list(key: str, default: str = "") -> list[str]:
    return [item.strip() for item in env(key, default).split(",") if item.strip()]


# --- Modus -------------------------------------------------------------------
VIERLIEF_MODE = env("VIERLIEF_MODE", "test").lower()
if VIERLIEF_MODE not in {"test", "live"}:
    raise RuntimeError("VIERLIEF_MODE moet 'test' of 'live' zijn.")
TEST_MODE = VIERLIEF_MODE == "test"

DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG or env_bool("VIERLIEF_ALLOW_DEV_SECRET", False):
        # Alleen voor lokaal ontwikkelen en geautomatiseerde tests.
        SECRET_KEY = "dev-only-insecure-vierlief-key-niet-gebruiken-in-productie"
    else:
        raise RuntimeError(
            "DJANGO_SECRET_KEY ontbreekt. Zet een lange willekeurige waarde in de omgeving."
        )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],testserver")
# Render geeft elke dienst een eigen adres (…onrender.com), bruikbaar zolang het eigen domein nog niet is gekoppeld.
if env("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(env("RENDER_EXTERNAL_HOSTNAME"))
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# Publieke basis-URL voor links in e-mails en QR-codes (zonder slash aan het eind).
BASE_URL = env("VIERLIEF_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
# Voorlopig contactadres (aangeleverd door de eigenaar, september 2026); in Render te overschrijven.
CONTACT_EMAIL = env("VIERLIEF_CONTACT_EMAIL", "info@vantorstudio.nl")
# Bedrijfsgegevens op de site (aangeleverd door de eigenaar, september 2026). Bewust zonder adres.
COMPANY_KVK = env("VIERLIEF_KVK", "94261423")
COMPANY_VAT = env("VIERLIEF_BTW", "NL212227221B02")
# Nog in te vullen door de eigenaar (alleen via Render, niet in Git): juridische naam met rechtsvorm en het
# vestigingsadres (regels scheiden met |). Een telefoonnummer is optioneel. Leeg = herkenbaar invulveld op de
# afgeschermde testversie; in live-modus weigert de site dan te starten (zie onderaan).
COMPANY_LEGAL_NAME = env("VIERLIEF_JURIDISCHE_NAAM")
# Vestigingsadres (aangeleverd door de eigenaar, 1 oktober 2026). Alleen tonen op "Contact & bedrijfsgegevens" en in de
# algemene voorwaarden (en de pdf daarvan); niet op de homepage, uitnodigingen of in de leveringsmail.
COMPANY_ADDRESS = env("VIERLIEF_ADRES", "Händellaan 73|8031 EG Zwolle")
COMPANY_PHONE = env("VIERLIEF_TELEFOON")
OWNER_NOTIFY_EMAIL = env("VIERLIEF_OWNER_EMAIL", CONTACT_EMAIL)
# Optioneel één wachtwoord voor de hele site (inlogvenster van de browser), bijvoorbeeld zolang een
# testversie online staat. Leeg = uit. Zie core.middleware.PreviewPasswordMiddleware.
PREVIEW_PASSWORD = env("VIERLIEF_PREVIEW_PASSWORD", "")
PREVIEW_USER = env("VIERLIEF_PREVIEW_USER", "voorbeeld")
# Tijdelijk alleen de informatiepagina's (home, ontwerpen, prijzen, voorwaarden, privacy, contact, voorbeelden) zonder
# wachtwoord, bijvoorbeeld voor de websitecontrole door Mollie. De rest blijft achter het previewwachtwoord.
PREVIEW_OPEN_PUBLIC = env_bool("VIERLIEF_PREVIEW_OPEN_PUBLIC", False)

# --- Applicaties -------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "core",
    "accounts",
    "catalog",
    "invitations",
    "orders",
    "wishes",
    "processing",
    "studio",
    "portal",
    "beheer",
    "gezichten",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.MediaHotlinkMiddleware",   # vóór WhiteNoise: anders komt een statisch bestand er nooit langs
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.PreviewPasswordMiddleware",
    "core.middleware.CompressTextMiddleware",
    "core.middleware.RequestSizeLimitMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # "designs" bevat de uitnodigingsontwerpen (per ontwerp en versie een map).
        "DIRS": [BASE_DIR / "templates", BASE_DIR / "designs"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.vierlief",
                "beheer.context_processors.nav_counts",
            ],
        },
    }
]

# --- Database ----------------------------------------------------------------
# Standaard SQLite (bestand in data/); voor productie PostgreSQL via DATABASE_URL.
DATA_DIR = Path(env("VIERLIEF_DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASES = {
    "default": dj_database_url.parse(
        env("DATABASE_URL", f"sqlite:///{DATA_DIR / 'vierlief.sqlite3'}"),
        conn_max_age=int(env("DATABASE_CONN_MAX_AGE", "60")),
    )
}
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"].update(
        {
            "transaction_mode": "IMMEDIATE",
            "timeout": 20,
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
        }
    )
    DATABASES["default"]["CONN_MAX_AGE"] = 0

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "vierlief_cache",
    }
}

# --- Accounts en sessies -----------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "portal:home"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "vierlief_sessie"
CSRF_COOKIE_NAME = "vierlief_csrf"

# --- Taal en tijd ------------------------------------------------------------
LANGUAGE_CODE = "nl"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

# --- Statische bestanden en uploads -----------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)
STATICFILES_DIRS = [
    BASE_DIR / "static",
    ("designs", BASE_DIR / "designs"),
]
# Uploads zijn privé: ze staan buiten de publieke map en worden alleen via
# views met toegangscontrole geserveerd (er is bewust geen MEDIA_URL-route).
MEDIA_ROOT = Path(env("VIERLIEF_UPLOAD_DIR", str(DATA_DIR / "uploads")))
MEDIA_URL = "/_uploads_niet_publiek/"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG or env_bool("VIERLIEF_PLAIN_STATIC", False)
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
        # Openbare bestanden: altijd leesbaar voor het webproces, ook als collectstatic
        # als een andere gebruiker draait (FILE_UPLOAD_PERMISSIONS geldt alleen voor uploads).
        "OPTIONS": {"file_permissions_mode": 0o644, "directory_permissions_mode": 0o755},
    },
}
FILE_UPLOAD_MAX_MEMORY_SIZE = 2_621_440
DATA_UPLOAD_MAX_MEMORY_SIZE = 2_621_440
DATA_UPLOAD_MAX_NUMBER_FIELDS = 600
FILE_UPLOAD_PERMISSIONS = 0o640
# Harde bovengrens per verzoek (bescherming tegen misbruik); zie core.middleware.
VIERLIEF_MAX_REQUEST_BYTES = int(env("VIERLIEF_MAX_REQUEST_BYTES", str(30 * 1024 * 1024)))

UPLOAD_LIMITS = {
    "photo_max_bytes": 12 * 1024 * 1024,
    "photo_types": ["image/jpeg", "image/png", "image/webp"],
    "photo_max_pixels": 60_000_000,
    "photo_min_side": 400,
    "audio_max_bytes": 12 * 1024 * 1024,
    "attachment_max_bytes": 10 * 1024 * 1024,
}

# --- E-mail ------------------------------------------------------------------
# VIERLIEF_EMAIL_MODE: "outbox" (alleen bewaren, testmodus) of "smtp".
EMAIL_MODE = env("VIERLIEF_EMAIL_MODE", "outbox" if TEST_MODE else "smtp").lower()
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("SMTP_HOST")
EMAIL_PORT = int(env("SMTP_PORT", "465"))
EMAIL_HOST_USER = env("SMTP_USER")
EMAIL_HOST_PASSWORD = env("SMTP_PASS")
EMAIL_USE_SSL = env_bool("SMTP_SSL", EMAIL_PORT == 465)
EMAIL_USE_TLS = env_bool("SMTP_STARTTLS", EMAIL_PORT == 587)
EMAIL_TIMEOUT = 20
DEFAULT_FROM_EMAIL = env("VIERLIEF_FROM_EMAIL", f"VAYLIDE <{CONTACT_EMAIL}>")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# --- Betalingen --------------------------------------------------------------
PAYMENT_PROVIDER = env("VIERLIEF_PAYMENT_PROVIDER", "test" if TEST_MODE else "mollie").lower()
MOLLIE_API_KEY = env("MOLLIE_API_KEY")
MOLLIE_API_BASE = env("MOLLIE_API_BASE", "https://api.mollie.com/v2")
# Betaalmethoden op de site als Mollie ze niet kan melden (of zonder Mollie). Met Mollie tonen we wat daar aanstaat.
PAYMENT_METHODS = env_list("VIERLIEF_PAYMENT_METHODS", "ideal,paypal")
# Welke methoden de site ooit toont (keuze van de eigenaar, september 2026: iDEAL, creditcard en PayPal). Staat er in
# Mollie meer aan (bijv. Klarna), dan verschijnt dat pas op de site als het hier wordt toegevoegd.
PAYMENT_METHODS_SHOWN = env_list("VIERLIEF_PAYMENT_METHODS_SHOWN", "ideal,creditcard,paypal")

# --- Eigen gezichten op het bruidspaar (optioneel, zie docs/GEZICHTEN.md) ------------------------------
# Standaard UIT. Pas aanzetten na akkoord over beeld-API, kosten, kwaliteit, privacytekst en de prijs (extra optie
# met functie 'gezichten' in Beheer → Prijzen). Zonder sleutel of optie blijft de knop onzichtbaar.
FACES_ENABLED = env_bool("VIERLIEF_FACES_ENABLED", False)

# Microsoft Clarity (bezoekersanalyse, alleen na toestemming; zie core/analytics.py en docs/CLARITY.md). Leeg = uit.
CLARITY_ID = env("VIERLIEF_CLARITY_ID", "").strip().lower()
if CLARITY_ID and not __import__("re").fullmatch(r"[a-z0-9]{6,20}", CLARITY_ID):
    raise RuntimeError("VIERLIEF_CLARITY_ID is geen geldig Clarity-project-id (kleine letters en cijfers).")
FACES_PROVIDER = env("VIERLIEF_FACES_PROVIDER", "gemini").lower()  # gemini, of test (alleen in testmodus: nagebootst)
GEMINI_API_KEY = env("GEMINI_API_KEY")
FACES_MODEL = env("VIERLIEF_FACES_MODEL", "gemini-3-pro-image")
FACES_API_BASE = env("VIERLIEF_FACES_API_BASE", "https://generativelanguage.googleapis.com/v1beta")
FACES_FREE_ATTEMPTS = int(env("VIERLIEF_FACES_ATTEMPTS", "3"))
FACES_MAX_BYTES = 10 * 1024 * 1024
# Een generatie kan tot ~2 minuten duren, langer dan een webverzoek mag duren: daarom in een achtergronddraad na het
# antwoord (de takenwachtrij vangt een onderbreking op). In de tests uit, zodat alles in hetzelfde proces blijft.
FACES_BACKGROUND = env_bool("VIERLIEF_FACES_BACKGROUND", True)

# --- Tweede back-uplocatie (optioneel, zie docs/BACKUP.md) -----------------------
# Een versleutelde kopie van elke nachtelijke back-up naar S3-compatibele opslag. Uit tot alles is ingevuld.
BACKUP_S3_BUCKET = env("VIERLIEF_BACKUP_S3_BUCKET")
BACKUP_S3_ENDPOINT = env("VIERLIEF_BACKUP_S3_ENDPOINT")  # leeg bij AWS; anders het adres van de aanbieder
BACKUP_S3_REGION = env("VIERLIEF_BACKUP_S3_REGION")
BACKUP_S3_ACCESS_KEY = env("VIERLIEF_BACKUP_S3_ACCESS_KEY")
BACKUP_S3_SECRET_KEY = env("VIERLIEF_BACKUP_S3_SECRET_KEY")
BACKUP_S3_PREFIX = env("VIERLIEF_BACKUP_S3_PREFIX", "vaylide")
BACKUP_ENCRYPTION_KEY = env("VIERLIEF_BACKUP_ENCRYPTION_KEY")

# --- AI (optioneel) -----------------------------------------------------------
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
AI_MODEL = env("VIERLIEF_AI_MODEL", "claude-opus-5-5")
AI_ENABLED = env_bool("VIERLIEF_AI_ENABLED", True)

# --- Privacyverklaring (zie core/privacyverklaring.py en docs/PRIVACY.md) ------
# Namen van aanbieders die de verklaring pas kan noemen als ze gekozen zijn. Leeg terwijl de koppeling actief is =
# invulveld op de testversie; in live-modus weigert `manage.py check` dan.
# Besluit eigenaar (beslislijst C1, 1 oktober 2026): Vimexx verstuurt de e-mail (SMTP via mail.zxcs.nl).
PRIVACY_EMAIL_PROVIDER = env("VIERLIEF_EMAIL_AANBIEDER", "Vimexx B.V. (Nederland)")
PRIVACY_BACKUP_PROVIDER = env("VIERLIEF_BACKUP_AANBIEDER")
PRIVACY_AI_AFSPRAKEN = env("VIERLIEF_AI_AFSPRAKEN")  # doorgifte-afspraken met Anthropic, na eigen controle

# --- Verwerking --------------------------------------------------------------
# Taken (publicatie, e-mail) worden direct na het opslaan geprobeerd. Mislukte
# taken worden opnieuw geprobeerd door `manage.py process_jobs` (cron/worker).
JOBS_RUN_INLINE = env_bool("VIERLIEF_JOBS_INLINE", True)
JOBS_CRON_TOKEN = env("VIERLIEF_CRON_TOKEN")

# --- Beveiliging -------------------------------------------------------------
CSRF_FAILURE_VIEW = "core.views.csrf_failure"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
if not DEBUG:
    SESSION_COOKIE_SECURE = env_bool("VIERLIEF_SECURE_COOKIES", True)
    CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SECURE_SSL_REDIRECT = env_bool("VIERLIEF_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = int(env("VIERLIEF_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_REDIRECT_EXEMPT = [r"^healthz$"]

# Aantal vertrouwde proxy's vóór de applicatie (bijv. 1 bij Render/Fly/een load balancer).
# Bij 0 wordt REMOTE_ADDR gebruikt. Nodig voor correcte limieten per IP-adres.
TRUSTED_PROXY_HOPS = int(env("VIERLIEF_TRUSTED_PROXY_HOPS", "0"))

ADMIN_URL = env("VIERLIEF_DJANGO_ADMIN_PATH", "systeembeheer/").strip("/") + "/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": env("VIERLIEF_LOG_LEVEL", "INFO")},
    "loggers": {"django.security": {"level": "WARNING"}},
}

# Onverwachte serverfouten (500) per e-mail aan de eigenaar, alleen als er echt gemaild wordt.
# Leeg VIERLIEF_ERROR_EMAIL = het adres van VIERLIEF_OWNER_EMAIL; "uit" = geen foutmails.
ERROR_EMAIL = env("VIERLIEF_ERROR_EMAIL", OWNER_NOTIFY_EMAIL)
if EMAIL_MODE == "smtp" and not DEBUG and ERROR_EMAIL and ERROR_EMAIL.lower() != "uit":
    ADMINS = [("VAYLIDE", ERROR_EMAIL)]
    EMAIL_SUBJECT_PREFIX = "[VAYLIDE] "
    LOGGING["handlers"]["mail_admins"] = {"class": "django.utils.log.AdminEmailHandler", "level": "ERROR"}
    LOGGING["loggers"]["django.request"] = {"handlers": ["console", "mail_admins"], "level": "ERROR", "propagate": False}

# In testmodus nooit echte betalingen: met Mollie alleen een testsleutel (test_...). Een live-sleutel
# hoort alleen bij VIERLIEF_MODE=live (zie hieronder); de site start anders niet.
if TEST_MODE and PAYMENT_PROVIDER == "mollie" and MOLLIE_API_KEY and not MOLLIE_API_KEY.startswith("test_"):
    raise RuntimeError("Testmodus accepteert alleen een Mollie-testsleutel (MOLLIE_API_KEY=test_...).")

# In live-modus mogen testvoorzieningen niet actief zijn.
if not TEST_MODE:
    if PAYMENT_PROVIDER == "test":
        raise RuntimeError("Live-modus vereist een echte betaalprovider (VIERLIEF_PAYMENT_PROVIDER=mollie).")
    if PAYMENT_PROVIDER == "mollie" and not MOLLIE_API_KEY.startswith("live_"):
        raise RuntimeError("Live-modus vereist een live Mollie-sleutel (MOLLIE_API_KEY=live_...).")
    if EMAIL_MODE != "smtp" or not (EMAIL_HOST and EMAIL_HOST_PASSWORD):
        raise RuntimeError("Live-modus vereist SMTP-instellingen (SMTP_HOST, SMTP_USER, SMTP_PASS).")
    if BASE_URL.startswith("http://"):
        raise RuntimeError("Live-modus vereist een https-adres in VIERLIEF_BASE_URL.")
    if not (COMPANY_LEGAL_NAME and COMPANY_ADDRESS):
        raise RuntimeError("Live-modus vereist de bedrijfsgegevens voor de voorwaarden en de contactpagina "
                           "(VIERLIEF_JURIDISCHE_NAAM en VIERLIEF_ADRES).")
