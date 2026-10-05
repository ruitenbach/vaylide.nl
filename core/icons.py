"""Eigen lijniconen (24 x 24, lijndikte via CSS) voor de website.

Zelf getekend; geen iconenbibliotheek nodig. Gebruik in templates: {% icon "zoeken" %}.
"""

ICONS = {
    "zoeken": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "tas": '<path d="M5.5 8.5h13l-1 11.5h-11l-1-11.5Z"/><path d="M9 8.5V7a3 3 0 0 1 6 0v1.5"/>',
    "pijl": '<path d="M5 12h14"/><path d="m13.5 6.5 5.5 5.5-5.5 5.5"/>',
    "afspelen": '<path d="M9.5 7.8v8.4l6.8-4.2-6.8-4.2Z" fill="currentColor" stroke="none"/>',
    "vink": '<circle cx="12" cy="12" r="8.5"/><path d="m8.6 12.3 2.3 2.3 4.6-4.8"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "kaarten": '<rect x="4" y="6.5" width="9.5" height="13" rx="1.5"/><path d="M8.5 6.5V5.5A1.5 1.5 0 0 1 10 4h8.5A1.5 1.5 0 0 1 20 5.5v10a1.5 1.5 0 0 1-1.5 1.5h-5"/>',
    "potlood": '<path d="M15.5 4.5 19.5 8.5 9 19H5v-4L15.5 4.5Z"/><path d="m13.5 6.5 4 4"/>',
    "oog": '<path d="M2.5 12s3.5-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.5 6.5-9.5 6.5S2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/>',
    "versturen": '<path d="M20.5 3.5 10.5 13.5"/><path d="M20.5 3.5 14 20.5l-3.5-7-7-3.5 17-6.5Z"/>',
    "wekker": '<circle cx="12" cy="13" r="7.2"/><path d="M12 9.5V13l2.4 1.8"/><path d="m4.5 5.8 2.6-2.2M19.5 5.8l-2.6-2.2"/>',
    "locatie": '<path d="M12 21s-6.5-5.7-6.5-11a6.5 6.5 0 0 1 13 0c0 5.3-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/>',
    "gasten": '<circle cx="9" cy="8.5" r="3.2"/><path d="M3.5 19.5c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5"/><path d="M15.5 5.6a3 3 0 0 1 0 5.8"/><path d="M17.6 14.8c1.7.7 2.6 2.2 2.9 4.7"/>',
    "programma": '<path d="M9 6.5h11M9 12h11M9 17.5h11"/><circle cx="5" cy="6.5" r="1"/><circle cx="5" cy="12" r="1"/><circle cx="5" cy="17.5" r="1"/>',
    "fotos": '<rect x="3.5" y="5" width="17" height="14" rx="2"/><circle cx="9" cy="10" r="1.7"/><path d="m20.5 15.5-4.8-4.8L7 19"/>',
    "kleuren": '<path d="M12 3.5a8.5 8.5 0 1 0 0 17c1.3 0 1.9-1 1.3-2.1-.7-1.3.2-2.9 1.7-2.9h2.3a3.2 3.2 0 0 0 3.2-3.2C20.5 7.3 16.7 3.5 12 3.5Z"/><circle cx="7.6" cy="11.2" r="1"/><circle cx="9.6" cy="7.4" r="1"/><circle cx="14.2" cy="7" r="1"/>',
    "muziek": '<path d="M9 17.5V6l10-2v11.5"/><circle cx="6.5" cy="17.5" r="2.5"/><circle cx="16.5" cy="15.5" r="2.5"/>',
    "agenda": '<rect x="4" y="5.5" width="16" height="14.5" rx="2"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/>',
    "delen": '<circle cx="17.5" cy="5.5" r="2.3"/><circle cx="6.5" cy="12" r="2.3"/><circle cx="17.5" cy="18.5" r="2.3"/><path d="m8.5 10.8 7-4.1M8.5 13.2l7 4.1"/>',
    "slot": '<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/>',
    "envelop": '<rect x="3.5" y="6" width="17" height="12.5" rx="1.5"/><path d="m4 7 8 6.2L20 7"/>',
    "hart": '<path d="M12 19.5s-7.5-4.4-7.5-10A4.3 4.3 0 0 1 12 7.1a4.3 4.3 0 0 1 7.5 2.4c0 5.6-7.5 10-7.5 10Z"/>',
}
