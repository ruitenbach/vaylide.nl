"""Beveiligingsheaders, een harde limiet op de grootte van verzoeken en een optioneel wachtwoord voor de hele site."""
from __future__ import annotations

import base64
import hmac
from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponse
from django.middleware.gzip import GZipMiddleware

from .csp import SCRIPT_HASHES
from .utils import ip_fingerprint, rate_limit

PRIVATE_PREFIXES = (
    "/u/",
    "/account/",
    "/beheer/",
    "/maken/",
    "/bestelling/",
    "/betalen/",
    "/inloggen/",
    "/voorbeeld/",
    "/voorwaarden/versie/",       # kopieën van /voorwaarden/ (per versie, download en pdf): niet in zoekmachines
    "/voorwaarden/download/",
    "/voorwaarden/pdf/",
    f"/{settings.ADMIN_URL}",
)
NO_STORE_PREFIXES = ("/account/", "/beheer/", "/maken/", "/bestelling/", "/betalen/", "/inloggen/", f"/{settings.ADMIN_URL}")


def _form_action_sources() -> str:
    sources = ["'self'"]
    if settings.PAYMENT_PROVIDER == "mollie":
        sources.append("https://www.mollie.com")
    return " ".join(sources)


class SecurityHeadersMiddleware:
    """Content-Security-Policy, Permissions-Policy en noindex voor privépagina's."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.form_action = _form_action_sources()

    def __call__(self, request):
        response = self.get_response(request)
        frame_ancestors = "'self'" if response.get("X-Frame-Options") == "SAMEORIGIN" else "'none'"
        response.setdefault(
            "Content-Security-Policy",
            "; ".join(
                [
                    "default-src 'self'",
                    "script-src 'self' " + " ".join(SCRIPT_HASHES),
                    "style-src 'self'",
                    "style-src-attr 'unsafe-inline'",
                    "img-src 'self' data: blob:",
                    "font-src 'self'",
                    "media-src 'self' blob:",
                    "connect-src 'self'",
                    "frame-src 'self'",
                    "object-src 'none'",
                    "base-uri 'self'",
                    f"form-action {self.form_action}",
                    f"frame-ancestors {frame_ancestors}",
                ]
            ),
        )
        response.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), browsing-topics=()"
        )
        path = request.path
        # Een afgeschermde testversie (previewwachtwoord) hoort nergens in zoekmachines, ook niet als de
        # informatiepagina's tijdelijk open staan.
        if path.startswith(PRIVATE_PREFIXES) or settings.PREVIEW_PASSWORD:
            response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        if path.startswith(NO_STORE_PREFIXES):
            response["Cache-Control"] = "private, no-store"
        elif path.startswith("/u/") and "Cache-Control" not in response:
            response["Cache-Control"] = "private, no-cache"
        return response


class MediaHotlinkMiddleware:
    """Eigen VAYLIDE-beelden en -video's laden alleen op onze eigen pagina's, niet als insluiting op een andere website.

    Staat vóór WhiteNoise, anders komt een statisch bestand nooit langs de middleware. Wat het wel en niet doet:
    - Een verzoek met een Referer van een vreemde website krijgt 403. Zonder Referer (typen van het adres, zoekmachines, deelkaarten,
      mailprogramma's) en met een eigen Referer gaat het gewoon door.
    - `Sec-Fetch-Site: cross-site` bij een afbeelding of video vangt wie zijn Referer onderdrukt (moderne browsers).
    - `Cross-Origin-Resource-Policy: same-site` laat de browser het insluiten door een andere website zelf weigeren.
    Beperkt tot media in de ontwerpen en in de afbeeldingen van de site; logo, mailafbeeldingen en deelbeelden blijven buiten schot.
    Dit stopt hotlinken, geen kopiëren: wie de pagina opent kan het bestand altijd uit het netwerkverkeer halen.
    """

    PROTECTED_PREFIXES = ("/static/designs/", "/static/img/designs/", "/static/img/site/", "/static/img/demo/", "/static/img/envelop/")
    MEDIA_EXTENSIONS = (".webp", ".jpg", ".jpeg", ".png", ".gif", ".avif", ".mp4", ".webm")
    EMBED_DESTINATIONS = {"image", "video", "audio", "embed", "object", "iframe", "frame"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if not (path.startswith(self.PROTECTED_PREFIXES) and path.lower().endswith(self.MEDIA_EXTENSIONS)):
            return self.get_response(request)
        if self._is_foreign(request):
            return HttpResponse("Niet beschikbaar buiten VAYLIDE.", status=403, content_type="text/plain; charset=utf-8", headers={"Cache-Control": "no-store"})
        response = self.get_response(request)
        if response.status_code < 400:
            response["Cross-Origin-Resource-Policy"] = "same-site"
        return response

    def _own_hosts(self, request) -> set[str]:
        hosts = {h.lower().lstrip(".") for h in settings.ALLOWED_HOSTS if h and h != "*"}
        hosts.add((urlsplit(settings.BASE_URL).hostname or "").lower())
        hosts.add(request.get_host().split(":")[0].lower())
        return hosts

    def _is_foreign(self, request) -> bool:
        referer = request.headers.get("Referer", "")
        if referer:
            host = (urlsplit(referer).hostname or "").lower()
            if host and host not in self._own_hosts(request):
                return True
        return (request.headers.get("Sec-Fetch-Site") == "cross-site"
                and request.headers.get("Sec-Fetch-Dest", "") in self.EMBED_DESTINATIONS)


class RequestSizeLimitMiddleware:
    """Weigert verzoeken die groter zijn dan VIERLIEF_MAX_REQUEST_BYTES (413)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.limit = settings.VIERLIEF_MAX_REQUEST_BYTES

    def __call__(self, request):
        try:
            length = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        if length > self.limit:
            return HttpResponse(
                "Het bestand of formulier is te groot. Probeer een kleiner bestand.",
                status=413,
                content_type="text/plain; charset=utf-8",
            )
        return self.get_response(request)


class CompressTextMiddleware(GZipMiddleware):
    """Comprimeert alleen tekst (HTML, JSON, CSV, agenda); geen afbeeldingen, audio of deelverzoeken.

    Django voegt willekeurige bytes toe tegen BREACH; CSRF-tokens zijn per verzoek gemaskeerd.
    Statische bestanden komen al gecomprimeerd uit WhiteNoise.
    """

    COMPRESSIBLE = {"text/html", "application/json", "text/csv", "text/calendar", "text/plain", "image/svg+xml"}

    def process_response(self, request, response):
        if response.status_code == 206 or response.has_header("Content-Range"):
            return response
        content_type = response.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type not in self.COMPRESSIBLE:
            return response
        return super().process_response(request, response)


class PreviewPasswordMiddleware:
    """Optioneel één wachtwoord voor de hele site (VIERLIEF_PREVIEW_PASSWORD), bijvoorbeeld zolang een
    testversie online staat: in testmodus staat de inlogcode op het scherm, dus zonder afscherming kan
    iedereen inloggen met elk e-mailadres. Uit als er geen wachtwoord is ingesteld.

    Vrij toegankelijk blijven de controle door de hosting (/healthz), de openbare opmaak en beelden
    (/static/), de taken voor een externe cron (eigen token) en de meldingen van de betaalprovider.
    """

    EXEMPT = ("/healthz", "/static/", "/intern/taken/", "/webhooks/")
    # Met VIERLIEF_PREVIEW_OPEN_PUBLIC (bijvoorbeeld voor de websitecontrole door Mollie) zijn alleen deze
    # informatiepagina's zonder wachtwoord te bekijken, en alleen lezen (GET/HEAD). Formulieren versturen, inloggen,
    # een kaart maken of bestellen, Mijn VAYLIDE, uitnodigingen (/u/), beheer en het systeembeheer blijven afgeschermd.
    PUBLIC_PAGES = {"/", "/ontwerpen/", "/zo-werkt-het/", "/prijzen/", "/veelgestelde-vragen/", "/inspiratie/",
                    "/over-ons/", "/zoeken/", "/contact/", "/privacy/", "/voorwaarden/", "/herroepen/", "/robots.txt",
                    "/sitemap.xml", "/favicon.ico"}
    PUBLIC_PREFIXES = ("/ontwerpen/", "/voorwaarden/", "/voorbeeld/")

    def __init__(self, get_response):
        self.get_response = get_response

    def _public(self, request) -> bool:
        if not settings.PREVIEW_OPEN_PUBLIC or request.method not in ("GET", "HEAD"):
            return False
        path = request.path
        # Zonder slot-slash (/prijzen) stuurt Django daarna zelf door naar /prijzen/; die moet dan ook open zijn.
        if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
            path += "/"
        return path in self.PUBLIC_PAGES or path.startswith(self.PUBLIC_PREFIXES)

    def __call__(self, request):
        password = settings.PREVIEW_PASSWORD
        if (not password or request.path.startswith(self.EXEMPT) or self._public(request)
                or self._authorized(request, password)):
            return self.get_response(request)
        if not rate_limit(f"preview:{ip_fingerprint(request)}", 30, 300):
            return HttpResponse("Te veel pogingen. Probeer het over een paar minuten opnieuw.", status=429,
                                content_type="text/plain; charset=utf-8")
        response = HttpResponse("Deze testversie is afgeschermd met een wachtwoord.", status=401,
                                content_type="text/plain; charset=utf-8")
        response["WWW-Authenticate"] = 'Basic realm="Testversie", charset="UTF-8"'
        response["Cache-Control"] = "no-store"
        return response

    @staticmethod
    def _authorized(request, password: str) -> bool:
        kind, _, value = request.META.get("HTTP_AUTHORIZATION", "").partition(" ")
        if kind.lower() != "basic" or not value:
            return False
        try:
            user, _, given = base64.b64decode(value, validate=True).decode("utf-8").partition(":")
        except (ValueError, UnicodeDecodeError):
            return False
        same_user = hmac.compare_digest(user.encode(), settings.PREVIEW_USER.encode())
        same_password = hmac.compare_digest(given.encode(), password.encode())
        return same_user and same_password
