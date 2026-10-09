"""De officiële VAYLIDE-collectie: welke ontwerpen prominent, secundair of voorlopig niet getoond worden.

A  prominent tonen: staat vooraan in de collectie (lage volgorde).
B  secundair behouden: staat na de A-ontwerpen.
C  technisch bewaren, voorlopig niet tonen: de map, de versies en alle bestaande uitnodigingen blijven; het ontwerp staat in de
   catalogus op 'niet zichtbaar' (Beheer → Ontwerpen → 'Zichtbaar en bestelbaar'). Zet je dat daar weer aan, dan is het ontwerp
   meteen terug (en komt het bij B).

Er wordt niets verwijderd. Een nieuw ontwerp dat hier niet staat, is B. De indeling is een voorstel van de eigenaar en kan hier
(en in Beheer) worden aangepast; zie docs/COLLECTIE.md. Nieuwe databases krijgen de waarden via de manifesten en catalog/seed.py;
bestaande databases krijgen ze één keer via migratie 0006 (daarna beslist Beheer).
"""
from __future__ import annotations

from functools import lru_cache

A = (
    "aurora-nocturne", "midnight-emeraude", "rose-royale", "balzaal", "golden-noel", "gouden-avond", "strandboog", "kerstbol", "kerstkaart", "kerststad",      # specials
    "liefde-op-papier", "voor-altijd", "avondgoud", "puur-moment",                         # bruiloft en alle gelegenheden
    "winterlicht", "gloria",                                                               # kerst
)
B = (
    "eerste-dans", "aan-tafel", "middernacht",
    "eucalyptus", "rozentuin", "pampas", "zuiden", "lentebloesem", "monogram", "ja-woord", "gatsby", "sterrennacht", "polaroid",
    "lauwerkrans", "zilveren-feest", "gouden-jaren", "robijn",
    "confetti", "glitter", "neon", "tropisch", "ballonfeest", "regenboog", "maanlicht",
    "gala", "strak",
)
C = (
    "kerstman", "sneeuwpop",                                            # cartoon-uitstraling, past niet bij het premium-niveau
    "wolkje", "stipjes", "door-de-jaren", "mijlpaal",                  # lijken sterk op een beter ontwerp (ballonfeest, regenboog, polaroid, gouden-jaren)
    "borrel", "congres", "lijnenspel",                                  # kaartbeeld met leeg vlak; nog niet premium genoeg
)

# Specials: bijzondere ontwerpen onder Specials, met een eigen meerprijs (catalog/specials.py). Winterlicht is bewust geen special.
SPECIALS = ("aurora-nocturne", "midnight-emeraude", "rose-royale", "balzaal", "golden-noel", "gouden-avond", "strandboog", "kerstbol", "kerstkaart", "kerststad")
NIEUWE_SPECIALS = ("midnight-emeraude", "rose-royale")      # kregen de vlag pas bij de samenstelling van de collectie (migratie 0006)

# Volgorde (sort_order) van de ontwerpen waarvan het nummer voor de collectie is veranderd. Alle andere ontwerpen houden hun nummer.
# A staat vóór B; geen twee ontwerpen hebben hetzelfde nummer (tests/test_collectie.py bewaakt dit en de overeenkomst met de manifesten).
SORT_ORDER = {
    "aurora-nocturne": 1, "midnight-emeraude": 2, "rose-royale": 3, "balzaal": 4, "golden-noel": 6, "kerstbol": 7, "kerstkaart": 8, "gouden-avond": 9, "strandboog": 12,
    "eerste-dans": 100, "aan-tafel": 101, "middernacht": 102,
}


# Wanneer een ontwerp is toegevoegd: `added_at` in het manifest (ISO-tijd, vast per ontwerp, in de code). Dit is de enige bron voor 'nieuwste eerst' (zie
# `catalog.occasions.collectie_volgorde`) en hangt dus niet af van de database: staging, production en een nieuwe database geven dezelfde volgorde, en
# `sync_designs`, deployen of opnieuw registreren veranderen niets. Een nieuw ontwerp krijgt in zijn manifest de tijd van toevoegen (tests/test_collectie.py bewaakt dat).
@lru_cache(maxsize=1)
def toegevoegd() -> dict:
    """slug -> tijdstip (met tijdzone) uit de manifesten; bij meerdere versies telt de vroegste. Een ontbrekende of ongeldige `added_at` is een duidelijke fout
    (DesignError), geen stille terugval: ook `sync_designs` en de tests laten het dan falen."""
    from .seed import design_manifests, parse_added_at

    gevonden: dict = {}
    for pad, data in design_manifests():
        moment = parse_added_at(data["added_at"], f"{pad.parent.parent.name}/{pad.parent.name}/manifest.json")
        slug = data["slug"]
        if slug not in gevonden or moment < gevonden[slug]:
            gevonden[slug] = moment
    return gevonden


def groep(slug: str) -> str:
    if slug in A:
        return "A"
    if slug in C:
        return "C"
    return "B"


def zichtbaar(slug: str) -> bool:
    """Alleen C staat voorlopig niet in de collectie."""
    return groep(slug) != "C"


def pas_toe(template_model) -> int:
    """Zet de collectie-instellingen op bestaande ontwerpen in de catalogus (zichtbaarheid, specials, volgorde).

    Wordt eenmalig gebruikt door migratie 0006. Verwijdert niets. Geeft het aantal ontwerpen terug dat is aangepast.
    """
    aangepast = 0
    for template in template_model.objects.all():
        wijzigingen = {}
        if not zichtbaar(template.slug) and template.is_active:
            wijzigingen["is_active"] = False
        if template.slug in NIEUWE_SPECIALS and not template.special:
            wijzigingen["special"] = True
        if template.slug in SORT_ORDER and template.sort_order != SORT_ORDER[template.slug]:
            wijzigingen["sort_order"] = SORT_ORDER[template.slug]
        if wijzigingen:
            template_model.objects.filter(pk=template.pk).update(**wijzigingen)
            aangepast += 1
    return aangepast
