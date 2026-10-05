"""De officiële VAYLIDE-profielen op sociale media: één bron voor de voettekst en voor `sameAs` in de gestructureerde gegevens.

Alleen echte, door de eigenaar opgegeven profielen. Een profiel erbij of eraf: hier aanpassen, dan volgen voettekst en zoekmachinegegevens vanzelf.
"""
from __future__ import annotations

# (iconsleutel in core/icons.py, naam, volledige link), in de volgorde van de voettekst.
PROFIELEN = (
    ("instagram", "Instagram", "https://www.instagram.com/vaylidenl/"),
    ("facebook", "Facebook", "https://www.facebook.com/profile.php?id=61594950397795"),
    ("tiktok", "TikTok", "https://www.tiktok.com/@vaylidenl"),
    ("linkedin", "LinkedIn", "https://www.linkedin.com/company/vaylide/"),
)


def social_links() -> list[dict]:
    return [{"icon": icon, "label": label, "url": url} for icon, label, url in PROFIELEN]


def same_as() -> list[str]:
    return [url for _icon, _label, url in PROFIELEN]
