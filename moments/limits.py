"""Grenzen van Moments. Waarden per album kunnen lager worden gezet; nooit hoger dan het harde plafond."""
from __future__ import annotations

# Plafonds die altijd gelden, ook als een album niets instelt.
# Voorlopig gelijk aan variant A (Classic: 15 foto's per gast, 100 gasten, harde stop op 125%); Signature heeft 25 per gast en 200 gasten.
DEFAULT_MAX_PER_GUEST = 15
DEFAULT_MAX_PER_ALBUM = 1875
HARD_MAX_PER_GUEST = 50
HARD_MAX_PER_ALBUM = 6250
# Gasten die echt iets uploadden ("actieve gasten"): 1,5 x het pakketaantal.
DEFAULT_MAX_GUESTS = 150
HARD_MAX_GUESTS = 300

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
SIGNUP_BUCKET_CAPACITY = 60
SIGNUP_BUCKET_REFILL_PER_MIN = 30
PROCESS_MAX_ATTEMPTS = 3
PROCESS_STALE_MINUTES = 15
NETWORK_HASH_RETENTION_DAYS = 30
