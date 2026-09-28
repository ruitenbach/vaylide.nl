"""Keuzes voor de Atelier-ontwerpen (gedeelde opbouw in designs/_atelier/v1/).

Een Atelier-ontwerp zet in manifest.json een blok "atelier" met per onderdeel een van
deze keuzes. De sjablonen en de opmaak staan in designs/_atelier/v1/.
"""

ATELIER_OPTIONS = {
    "opening": ["envelop", "vouwkaart", "gordijn", "lint", "sluier", "confetti", "ballonnen", "sterren", "schuif", "polaroid", "cadeau"],
    "hero": ["klassiek", "gesplitst", "kader", "redactioneel", "monogram", "polaroid", "volbeeld", "band", "getal"],
    "sections": ["lijnen", "kaarten", "genummerd", "tweekolom", "midden", "tijdlijn"],
    "heading": ["lijn", "ornament", "script", "kapitaal", "groot"],
    "names": ["display", "script", "kapitaal", "cursief", "stapel"],
    "date": ["blok", "lijn", "cirkel", "cijfers", "kalender"],
    "photo": ["boog", "cirkel", "rond", "recht", "polaroid"],
    "texture": ["geen", "papier", "stippen", "linnen", "ruit", "sterren", "confetti"],
    "ornament": ["geen", "eucalyptus", "botanisch", "bloemen", "pampas", "palm", "lauwerkrans", "deco", "geometrisch",
                 "sterren", "confetti", "ballonnen", "harten", "zon", "golven", "wolken", "regenboog", "ringen", "lijnen",
                 "fonkel", "stippen", "kerstman", "sneeuwpop"],
}

OPENING_LABELS = {
    "envelop": "Envelop met zegel",
    "vouwkaart": "Vouwkaart",
    "gordijn": "Gordijn",
    "lint": "Cadeaulint",
    "sluier": "Zachte sluier",
    "confetti": "Confetti",
    "ballonnen": "Ballonnen",
    "sterren": "Sterrenhemel",
    "schuif": "Schuifpaneel",
    "polaroid": "Polaroid",
    "cadeau": "Cadeau om uit te pakken",
}


def atelier_errors(config) -> list[str]:
    """Geeft een lijst met fouten in het atelier-blok (leeg als alles klopt)."""
    if not isinstance(config, dict):
        return ["'atelier' moet een blok met instellingen zijn."]
    errors = []
    for key, options in ATELIER_OPTIONS.items():
        value = config.get(key)
        if value not in options:
            errors.append(f"atelier.{key} = {value!r}; kies uit: {', '.join(options)}")
    return errors


# Kleurnamen in de ontwerpbeschrijving en de CSS-variabelen in manifest.json.
ATELIER_VARS = {
    "bg": "--a-bg", "surface": "--a-surface", "ink": "--a-ink", "muted": "--a-muted", "accent": "--a-accent",
    "accent_ink": "--a-accent-ink", "accent_text": "--a-accent-text", "line": "--a-line", "c2": "--a-c2", "c3": "--a-c3",
    "cover_bg": "--a-cover-bg", "cover_ink": "--a-cover-ink", "cover_card": "--a-cover-card", "cover_btn": "--a-cover-btn",
    "cover_btn_ink": "--a-cover-btn-ink", "cover_accent": "--a-cover-accent", "env": "--a-env", "seal": "--a-seal",
    "curtain": "--a-curtain", "ribbon": "--a-ribbon", "wrap": "--a-wrap", "band": "--a-band", "band_ink": "--a-band-ink", "hero_ink": "--a-hero-ink",
    "hero_accent": "--a-hero-accent", "moon": "--a-moon", "orn": "--a-orn", "scheme": "--a-scheme",
}


def palette_colors(palette: dict) -> dict:
    """Kleuren van een kleurvariant uit manifest.json, met de namen uit ATELIER_VARS."""
    by_var = {var: key for key, var in ATELIER_VARS.items()}
    return {by_var[var]: value for var, value in (palette.get("vars") or {}).items() if var in by_var}


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def channel(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a: str, b: str) -> float:
    """Contrastverhouding volgens WCAG 2.1 (1 tot 21)."""
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def palette_problems(c: dict, atelier: dict | None = None) -> list[str]:
    """Tekstparen van een kleurvariant die onder 4,5:1 blijven (WCAG 2.1 AA voor gewone tekst)."""
    text = c.get("accent_text", c["accent"])
    pairs = [
        ("tekst op achtergrond", c["ink"], c["bg"]),
        ("tekst op kaart", c["ink"], c["surface"]),
        ("gedempte tekst op achtergrond", c["muted"], c["bg"]),
        ("gedempte tekst op kaart", c["muted"], c["surface"]),
        ("accenttekst op achtergrond", text, c["bg"]),
        ("accenttekst op kaart", text, c["surface"]),
        ("knoptekst op accent", c["accent_ink"], c["accent"]),
        ("tekst op openingsscherm", c.get("cover_ink", c["ink"]), c.get("cover_bg", c["bg"])),
    ]
    if "cover_btn" in c or "cover_btn_ink" in c:
        pairs.append(("knop op openingsscherm", c.get("cover_btn_ink", c["accent_ink"]), c.get("cover_btn", c["accent"])))
    if "band" in c or (atelier or {}).get("hero") == "band":
        pairs.append(("tekst op band", c.get("band_ink", c["accent_ink"]), c.get("band", c["accent"])))
    if "cover_card" in c:
        pairs.append(("tekst op kaart in opening", c["ink"], c["cover_card"]))
    return [f"{name}: {fg} op {bg} = {contrast(fg, bg):.2f}:1 (minimaal 4,5)" for name, fg, bg in pairs if contrast(fg, bg) < 4.5]
