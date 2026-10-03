"""Effecten per ontwerp: sfeer, knal bij openen, viering na aanmelden, namen en onthullen.

Een ontwerp zet in manifest.json een blok "effects" met per onderdeel een van deze keuzes.
Het gedrag staat in invitations/static/invitations/effects.js en effects.css. Alles is
decoratief: zonder JavaScript of bij 'minder beweging' blijft de uitnodiging gewoon leesbaar.
"""

EFFECT_OPTIONS = {
    # Zwevende deeltjes op de achtergrond (en op het openingsscherm).
    "sfeer": ["geen", "blaadjes", "bloesem", "bladeren", "lauwerblaadjes", "pluisjes", "confetti", "harten", "ballonnen", "bellen",
              "champagne", "bokeh", "stippen", "stofjes", "zonlicht", "neon", "geometrie", "wolkjes", "goudstof",
              "glitter", "sterren", "netwerk", "raster", "film", "cadeautjes", "sneeuw"],
    # Uitbarsting op het moment dat de uitnodiging opengaat.
    "knal": ["geen", "blaadjes", "bloesem", "bladeren", "lauwerblaadjes", "pluisjes", "confetti", "kanon", "vonken", "sterren", "harten",
             "bellen", "ballonnen", "lijnen", "neon", "flits", "champagne", "stippen", "netwerk", "bokeh", "cadeautjes", "sneeuw"],
    # Hoe de namen verschijnen na het openen.
    "namen": ["zacht", "schrijf", "folie", "gloed", "pop"],
    # Hoe secties verschijnen bij het scrollen.
    "onthul": ["omhoog", "zacht", "zoom", "kanteling", "wissel"],
}
# Het feestje als een gast laat weten dat hij komt: dezelfde keuzes als de knal.
EFFECT_OPTIONS["viering"] = EFFECT_OPTIONS["knal"]

EFFECT_EXTRAS = {
    "kenburns": "Foto's zoomen langzaam in",
    "kantel": "Het openingsscherm kantelt mee met de muis",
    "tik": "Een tik op de uitnodiging geeft een klein vonkje",
    "stralen": "Draaiende lichtstralen achter de kop",
    "disco": "Draaiende lichtspikkels achter de kop",
    "aura": "Zachte kleurvlekken die langzaam over de achtergrond bewegen",
}

EFFECT_LABELS = {
    "blaadjes": "Bloemblaadjes", "bloesem": "Bloesem", "bladeren": "Blaadjes", "lauwerblaadjes": "Lauwerblaadjes", "pluisjes": "Pluimen", "confetti": "Confetti",
    "kanon": "Confettikanonnen", "harten": "Hartjes", "ballonnen": "Ballonnen", "bellen": "Zeepbellen",
    "champagne": "Champagnebubbels", "bokeh": "Zachte lichtjes", "stippen": "Stippen", "stofjes": "Stofjes in het licht",
    "zonlicht": "Zonnestofjes", "neon": "Neonvormen", "geometrie": "Lijnvormen", "wolkjes": "Wolkjes",
    "goudstof": "Goudstof", "glitter": "Glitter", "sterren": "Sterrenhemel", "netwerk": "Netwerk", "raster": "Lichtgolf",
    "film": "Filmkorrel", "vonken": "Vonken en glanzende confetti", "lijnen": "Lichtlijnen", "flits": "Flits",
    "cadeautjes": "Cadeautjes", "sneeuw": "Sneeuw", "geen": "Geen",
}

# Voor de website: wat een gast ziet (kleine letters, midden in een zin).
SFEER_TEXT = {
    "blaadjes": "dwarrelende bloemblaadjes", "bloesem": "dwarrelende bloesem", "bladeren": "vallende blaadjes",
    "lauwerblaadjes": "vallende lauwerblaadjes", "pluisjes": "zwevende pluimen", "confetti": "vallende confetti",
    "harten": "opstijgende hartjes", "ballonnen": "opstijgende ballonnen", "bellen": "zwevende zeepbellen",
    "champagne": "opborrelende champagnebubbels", "bokeh": "zachte zwevende lichtjes", "stippen": "zwevende stippen",
    "stofjes": "stofjes in het licht", "zonlicht": "zonnestofjes", "neon": "gloeiende neonvormen",
    "geometrie": "zwevende lijnvormen", "wolkjes": "drijvende wolkjes", "goudstof": "fonkelend goudstof",
    "glitter": "fonkelende glitter", "sterren": "een fonkelende sterrenhemel met vallende sterren",
    "netwerk": "een bewegend netwerk van lijnen", "raster": "een lichtgolf over een puntjesraster",
    "film": "filmkorrel en krasjes als bij een oude projector", "cadeautjes": "vallende cadeautjes",
    "sneeuw": "zacht vallende sneeuw",
}
KNAL_TEXT = {
    "blaadjes": "een regen van bloemblaadjes", "bloesem": "een wolk bloesem", "bladeren": "opwaaiende blaadjes",
    "lauwerblaadjes": "opwaaiende lauwerblaadjes", "pluisjes": "opwaaiende pluimen", "confetti": "een explosie van confetti",
    "kanon": "twee confettikanonnen", "vonken": "vonken en glanzende confetti", "sterren": "een wolk sterrenstof",
    "harten": "een wolk hartjes", "bellen": "een bos zeepbellen", "ballonnen": "een lucht vol ballonnen",
    "lijnen": "stralende lichtlijnen", "neon": "neonvonken", "flits": "een cameraflits", "champagne": "een champagneknal",
    "stippen": "een regen van stippen", "netwerk": "een netwerk dat uitwaaiert", "bokeh": "zachte lichtjes",
    "cadeautjes": "een plof en een fontein van cadeautjes",
    "sneeuw": "een wolk sneeuwvlokjes en gouden sterretjes",
}


def effects_errors(config) -> list[str]:
    """Geeft een lijst met fouten in het effects-blok (leeg als alles klopt)."""
    if not isinstance(config, dict):
        return ["'effects' moet een blok met instellingen zijn."]
    errors = []
    for key, options in EFFECT_OPTIONS.items():
        value = config.get(key)
        if value not in options:
            errors.append(f"effects.{key} = {value!r}; kies uit: {', '.join(options)}")
    extra = config.get("extra", [])
    if not isinstance(extra, list):
        errors.append("effects.extra moet een lijst zijn.")
    else:
        unknown = [e for e in extra if e not in EFFECT_EXTRAS]
        if unknown:
            errors.append(f"effects.extra kent {', '.join(map(str, unknown))} niet; kies uit: {', '.join(EFFECT_EXTRAS)}")
    return errors


def effect_view(config) -> dict:
    """Instellingen voor het sjabloon: data-attributen en klassen op <html>. Leeg zonder effects-blok."""
    if not isinstance(config, dict) or effects_errors(config):
        return {}
    extra = config.get("extra", [])
    classes = ["fx", f"fx-namen-{config['namen']}", f"fx-onthul-{config['onthul']}"]
    classes += [f"fx-{e}" for e in extra if e != "tik"]
    return {
        "sfeer": config["sfeer"],
        "knal": config["knal"],
        "viering": config["viering"],
        "namen": config["namen"],
        "onthul": config["onthul"],
        "tik": "tik" in extra,
        "extra": extra,
        "classes": " ".join(classes),
    }


def _mix(a: str, b: str, t: float) -> str:
    ha, hb = a.lstrip("#"), b.lstrip("#")
    ca = [int(ha[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(hb[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


def shine_color(fg: str, bg: str, accent: str) -> str:
    """Kleur van de lichtstreep bij 'folie' (namen): altijd minstens 3,2:1 op de achtergrond.

    Namen in de tekstkleur krijgen een glans in de accentkleur (goud op crème, goud op zwart).
    Namen die zelf al de accentkleur hebben, krijgen een lichtere tint: op een donkere
    achtergrond altijd, op een lichte zolang het contrast het toelaat.
    """
    from .atelier import _luminance, contrast

    if fg.upper() != accent.upper() and contrast(accent, bg) >= 3.2:
        return accent.upper()
    if _luminance(bg) < _luminance(fg):
        return _mix(fg, "#FFFFFF", 0.6)
    for t in (0.45, 0.35, 0.25, 0.15):
        candidate = _mix(fg, "#FFFFFF", t)
        if contrast(candidate, bg) >= 3.2:
            return candidate
    return fg.upper()


def effect_summary(config) -> str:
    """Eén zin voor de ontwerppagina, bijvoorbeeld: 'Dwarrelende bloemblaadjes en bij het openen een regen van bloemblaadjes.'"""
    if not isinstance(config, dict) or effects_errors(config):
        return ""
    # Een ontwerp met een eigen filmische opening (zonder deeltjes) mag zelf zeggen wat je ziet: "samenvatting" in het effects-blok.
    eigen = config.get("samenvatting")
    if isinstance(eigen, str) and eigen.strip():
        return eigen.strip()
    sfeer = SFEER_TEXT.get(config["sfeer"], "")
    knal = KNAL_TEXT.get(config["knal"], "")
    if sfeer and knal:
        text = f"{sfeer} en bij het openen {knal}"
    elif sfeer or knal:
        text = sfeer or f"bij het openen {knal}"
    else:
        return ""
    return text[0].upper() + text[1:] + "."


def effect_card_label(config, opening_label: str = "") -> str:
    """Kort kenmerk voor een ontwerpkaart, bijvoorbeeld 'bloemblaadjes'.

    Leeg als het hetzelfde zou zeggen als de naam van de opening ("Confetti · confetti").
    """
    if isinstance(config, dict) and isinstance(config.get("kaartlabel"), str) and config["kaartlabel"].strip():
        return config["kaartlabel"].strip().lower()   # eigen label, zie effect_summary
    if not isinstance(config, dict) or config.get("sfeer") in (None, "geen"):
        return ""
    label = EFFECT_LABELS.get(config["sfeer"], "").lower()
    return "" if label == opening_label.strip().lower() else label
