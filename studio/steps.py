"""Stappen van het samenstellen.

De klant ziet vier fasen: 1 Kies kaart, 2 Personaliseer, 3 Controleer, 4 Bestel. Fase 2 bestaat uit onderdelen (Gegevens, Praktische
info, Aanmelden, Foto's, Envelop, Stijl) die in een balk boven het formulier staan; ze zijn allemaal optioneel en wisselen bewaart wat er staat.
"""

STEPS = [
    ("gelegenheid", "Gelegenheid"),
    ("ontwerp", "Ontwerp"),
    ("gegevens", "Gegevens"),
    ("programma", "Praktische info"),
    ("aanmelden", "Aanmelden"),
    ("fotos", "Foto's & verhaal"),
    ("envelop", "Envelop & zegel"),
    ("stijl", "Stijl"),
    ("voorbeeld", "Controle"),
    ("bestellen", "Bestellen"),
]
STEP_KEYS = [key for key, _ in STEPS]
STEP_LABELS = dict(STEPS)
FORM_STEPS = ["ontwerp", "gegevens", "programma", "aanmelden", "fotos", "envelop", "stijl"]

# De onderdelen van fase 2 (Personaliseer), in de volgorde van de balk en van 'Volgende'.
PERSONALISEER = ["gegevens", "programma", "aanmelden", "fotos", "envelop", "stijl"]

# De vier fasen die de klant ziet: (sleutel, label, stap waar de fase begint).
FASEN = [
    ("kaart", "Kies kaart", "ontwerp"),
    ("personaliseer", "Personaliseer", "gegevens"),
    ("controle", "Controleer", "voorbeeld"),
    ("bestel", "Bestel", "bestellen"),
]
FASE_VAN = {"gelegenheid": "kaart", "ontwerp": "kaart", "voorbeeld": "controle", "bestellen": "bestel",
            **{key: "personaliseer" for key in PERSONALISEER}}


# Bij een wenskaart is er niets aan te melden en kiest de klant geen envelop (het ontwerp heeft zijn eigen opening): de route blijft kort.
# Van 'Praktische info' blijft alleen de afsluitende tekst over.
WENSKAART_SKIP = frozenset({"aanmelden", "envelop"})

# Bij een ontwerp zonder keuze uit de Envelope Collection (envelope_mode is niet "optional") bestaat de stap Envelop & zegel niet.
ENVELOP_SKIP = frozenset({"envelop"})
WENSKAART_LABELS = {"programma": "Afsluiting", "fotos": "Foto", "stijl": "Stijl"}


def heeft_envelopstap(inv) -> bool:
    """De stap Envelop & zegel bestaat alleen bij een ontwerp met de keuze uit de Envelope Collection (envelope_mode optional) en
    als er voor de gelegenheid een uitgewerkte envelop is. Eén plek voor de Studio en Mijn VAYLIDE."""
    from catalog import envelop_collectie

    return envelop_collectie.modus(inv.template_version) == "optional" and bool(envelop_collectie.beschikbaar(inv.occasion))


def next_step(step: str, *, paid: bool = False, skip=frozenset()) -> str:
    keys = [k for k in STEP_KEYS if k != "gelegenheid" and not (paid and k == "bestellen")]
    index = keys.index(step) if step in keys else 0
    # De eerstvolgende stap die niet wordt overgeslagen (ook vanaf een overgeslagen stap).
    for key in keys[index + 1:]:
        if key not in skip:
            return key
    return keys[-1]


def previous_step(step: str, *, skip=frozenset()) -> str:
    keys = [k for k in STEP_KEYS if k != "gelegenheid"]
    index = keys.index(step) if step in keys else 0
    for key in reversed(keys[:index]):
        if key not in skip:
            return key
    return keys[0]


def progress(current: str, *, paid: bool = False, skip=frozenset(), labels=None) -> list[dict]:
    """De vier fasen met hun stand (done, current, todo). Na betaling bestaat de fase Bestel niet meer."""
    fasen = [f for f in FASEN if not (paid and f[0] == "bestel")]
    huidig = FASE_VAN.get(current, "kaart")
    current_index = next((i for i, f in enumerate(fasen) if f[0] == huidig), 0)
    return [
        {
            "key": key,
            "label": label,
            "step": stap,
            "number": index + 1,
            "state": "done" if index < current_index else ("current" if index == current_index else "todo"),
            "linkable": True,
        }
        for index, (key, label, stap) in enumerate(fasen)
    ]


def substeps(current: str, *, skip=frozenset(), labels=None) -> list[dict]:
    """De onderdelen van fase 2 voor de balk boven het formulier. Leeg buiten fase 2."""
    if current not in PERSONALISEER:
        return []
    labels = {**STEP_LABELS, **(labels or {})}
    return [
        {"key": key, "label": labels[key], "current": key == current}
        for key in PERSONALISEER
        if key not in skip
    ]
