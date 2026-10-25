"""Grenzen van Moments. Waarden per album kunnen lager worden gezet; nooit hoger dan het harde plafond."""
from __future__ import annotations

# Plafonds die altijd gelden, ook als een album niets instelt.
# Voorlopig gelijk aan variant A (Classic: 15 foto's per gast, 100 gasten, harde stop op 125%); Signature heeft 25 per gast en 200 gasten.
DEFAULT_MAX_PER_GUEST = 15
DEFAULT_MAX_PER_ALBUM = 1875
HARD_MAX_PER_GUEST = 50
HARD_MAX_PER_ALBUM = 6250
# Actieve gastsessies (gasten die echt iets uploadden): een technische WAARSCHUWINGSgrens, geen weigergrens. Classic 200 (2 x 100 gasten),
# Signature 400 (2 x 200). Overschrijding wordt alleen intern vastgelegd (`Album.guest_warning_at`); een geldige upload wordt daardoor nooit geweigerd.
# De foto-, opslag-, reserverings- en tempolimieten blijven de bescherming tegen misbruik.
DEFAULT_MAX_GUESTS = 200
SIGNATURE_MAX_GUESTS = 400

# Toekomstige eis (nog niet gebouwd): de albummaster, het hoogwaardige eindbestand, is hoogstens 6000 px op de lange zijde.
ALBUM_MASTER_MAX_EDGE_PX = 6000

# Gasten zien alleen hun eigen inzendingen (nooit die van andere gasten of de organisator-weergave).
GUEST_VISIBILITY = "own"

# Voorlopige pakketten (besluit 25 oktober 2026, variant A). Prijzen, opslagleverancier en definitieve limieten volgen later.
PACKAGES = {
    "classic": {"guests": 100, "photos_per_guest": 15, "videos_per_guest": 2, "video_seconds": 30},
    "signature": {"guests": 200, "photos_per_guest": 25, "videos_per_guest": 2, "video_seconds": 60},
}
RETENTION_MONTHS = 12

# ---------- Foto-uploads (stap 3A) ----------
# Toegestane invoer. HEIC/HEIF staat er bewust niet bij: Pillow leest dat niet zonder extra pakket (open punt voor de eigenaar).
PHOTO_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
PHOTO_MIN_BYTES = 1024
PHOTO_MAX_INPUT_BYTES = 25 * 1024 * 1024
PHOTO_MAX_PIXELS = 80_000_000
# Wat wij bewaren: de albummaster, nooit groter dan dit. Het bytesplafond van een album is aantallen x deze waarde.
PHOTO_MAX_STORED_BYTES = 8 * 1024 * 1024
PHOTO_JPEG_QUALITIES = (90, 88, 85, 80)

# Reserveringen en tempo.
RESERVATION_MINUTES = 30
MAX_CONCURRENT_UPLOADS = 3
MAX_STARTS_PER_10_MIN = 60
SIGNUP_BUCKET_CAPACITY = 300
SIGNUP_BUCKET_REFILL_PER_MIN = 120
VALIDATE_CLAIM_SECONDS = 120  # hoe lang een lopende controle van één upload als 'bezig' geldt
PROCESS_MAX_ATTEMPTS = 3
PROCESS_STALE_MINUTES = 15
NETWORK_HASH_RETENTION_DAYS = 30
