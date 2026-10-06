"""Stappen van het samenstellen."""

STEPS = [
    ("gelegenheid", "Gelegenheid"),
    ("ontwerp", "Ontwerp"),
    ("envelop", "Envelop & zegel"),
    ("gegevens", "Gegevens"),
    ("programma", "Programma & info"),
    ("aanmelden", "Aanmelden"),
    ("fotos", "Foto's & verhaal"),
    ("stijl", "Stijl & onderdelen"),
    ("voorbeeld", "Voorbeeld"),
    ("bestellen", "Bestellen"),
]
STEP_KEYS = [key for key, _ in STEPS]
STEP_LABELS = dict(STEPS)
FORM_STEPS = ["ontwerp", "envelop", "gegevens", "programma", "aanmelden", "fotos", "stijl"]


# Bij een wenskaart is er niets aan te melden en kiest de klant geen envelop (het ontwerp heeft zijn eigen opening): de route blijft kort.
# Van 'Programma & info' blijft alleen de afsluitende tekst over.
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
    items = []
    labels = {**STEP_LABELS, **(labels or {})}
    keys = [k for k in STEP_KEYS if not (paid and k == "bestellen") and k not in skip]
    current_index = keys.index(current) if current in keys else 0
    for index, key in enumerate(keys):
        items.append(
            {
                "key": key,
                "label": labels[key],
                "number": index + 1,
                "state": "done" if index < current_index else ("current" if index == current_index else "todo"),
                "linkable": key not in ("gelegenheid",),
            }
        )
    return items
