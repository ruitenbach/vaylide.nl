"""Stappen van het samenstellen."""

STEPS = [
    ("gelegenheid", "Gelegenheid"),
    ("ontwerp", "Ontwerp"),
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
FORM_STEPS = ["ontwerp", "gegevens", "programma", "aanmelden", "fotos", "stijl"]


# Bij een wenskaart (Kerst zonder evenement) is er niets aan te melden, en van 'Programma & info' blijft alleen de
# afsluitende tekst over.
WENSKAART_SKIP = frozenset({"aanmelden"})
WENSKAART_LABELS = {"programma": "Afsluiting"}


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
