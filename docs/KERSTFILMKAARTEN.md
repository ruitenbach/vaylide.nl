# Kerstmarkt, Kerstpaleis, Kerstcoupé en Kerstbal

Vier nieuwe kerstkaarten met een eigen film als opening, overgenomen van een collega (15 oktober 2026). Alle vier staan op de ontwikkelbranch `claude/kerstontwerpen-integratie` (lokaal, niet gepusht) en zijn **Luxe, € 24,95 inclusief btw, 12 maanden online** (besluit van de eigenaar). De prijsstructuur zelf is niet aangepast: alleen vier regels in `INDELING` (`catalog/prijzen.py`).

| Kaart | Opening | Kleuren | Herkomst |
|---|---|---|---|
| Kerstmarkt (`kerstmarkt`) | Film vanuit een reuzenrad; kaart met ster klapt open | Avondblauw, Gondelrood, Dennengroen | zip Kerstmarkt: alleen `designs/kerstmarkt`, kaartbeeld, test, tool en e2e (de rest van die oudere sitekopie is niet overgenomen) |
| Kerstpaleis (`kerstpaleis`) | Film: de deuren van een paleis gaan open | Kerstrood, Dennengroen, Nachtblauw | losse voorbeeldkaart, omgezet naar een ontwerp met de gewone velden; de voorbeeldbalk, kleurkiezer en nep-aanmelding zijn vervallen |
| Kerstcoupé (`kerstcoupe`) | Film: fluwelen gordijnen gaan open op een bergdorp | Rood fluweel, Sneeuwnacht, Mahonie | patch, **niet toegepast** (paste niet op deze basis): de nieuwe bestanden zijn overgenomen en de regels in gedeelde bestanden met de hand toegevoegd |
| Kerstbal (`kerstbal`) | Film: een kerstbal gaat open, de kaart komt eruit | Kerstrood | losse voorbeeldpagina, omgezet naar een ontwerp. Eén kleur: de pagina noemt een tweede ("ivoor") maar bevat die niet, dus die is niet verzonnen |

## Wat er gewijzigd is buiten de ontwerpmappen

- `catalog/prijzen.py`: vier regels bij Luxe. `catalog/collectie.py`: de vier in groep B. `invitations/demo.py`: voorbeeldbeelden en gelegenheid.
- Tests: aantallen in `test_effects`, `test_collectie`, `test_prijsstructuur`; volgorde van de kerstlijst in `test_kerst` en `test_middernacht` (nieuwste eerst: de vier staan nu voor Gloria). Nieuw: `test_kerstmarkt`, `test_kerstpaleis`, `test_kerstcoupe`, `test_kerstbal` en een bestel- en publicatietest in `test_prijsstructuur`.
- Het gedeelde `invite.js` is niet aangepast. Kerstbal start zijn film met een eigen script (`designs/kerstbal/v1/kerstbal.js`).
- Volgorde: de vier hebben `sort_order` 41, 42, 43 en 44 en dezelfde `added_at`; omdat de collectie "nieuwste eerst" toont, staan ze bovenaan de kerstlijst. Wil je dat niet, dan kan `added_at` in de manifesten oudere tijden krijgen.

## Rechten

De films lijken met AI gemaakt. De zips zeggen dat het eigen materiaal is; de eigenaar bevestigt dat.
