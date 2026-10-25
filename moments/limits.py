"""Grenzen van Moments. Waarden per album kunnen lager worden gezet; nooit hoger dan het harde plafond."""
from __future__ import annotations

# Plafonds die altijd gelden, ook als een album niets instelt.
DEFAULT_MAX_PER_GUEST = 10
DEFAULT_MAX_PER_ALBUM = 500
HARD_MAX_PER_GUEST = 50
HARD_MAX_PER_ALBUM = 2000

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
