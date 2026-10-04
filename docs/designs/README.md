# Ontwerpen: één vaste bron

Vanaf 4 oktober 2026 staat de informatie over elk VAYLIDE-ontwerp in de repository, niet meer alleen in losse ChatGPT- of Claude-sessies.
Per ontwerp bestaat er **één document**: `docs/designs/<slug>.md`, gemaakt van [`_sjabloon.md`](_sjabloon.md) (15 vaste onderdelen).

## Afspraken

- **Eén bestand per ontwerp**, genoemd naar de slug (bijvoorbeeld `kerstkaart.md`, `kerstbol.md`). Het document is leidend; staat er iets anders in een losse sessie, dan geldt dit document.
- **Niet verzinnen.** Een onderdeel dat nog niet bekend is, blijft leeg met "nog niet bepaald". Inhoud komt van de eigenaar of uit een goedgekeurd besluit, niet uit andere ontwerpen afgeleid.
- **Bijhouden bij elke wijziging aan het ontwerp:** status (onderdeel 4), afgerond en openstaand (11 en 12), laatste commit (14) en volgende stap (15).
- **Besluiten** (onderdeel 13) worden niet opnieuw besproken, tenzij de eigenaar dat zegt.
- **Assets en bronnen** (onderdelen 8 en 9): grote bestanden en masters staan niet in Git; het document zegt waar ze wel staan. Prompts en referenties van externe AI- en videotools bewaren we in [`tools/design-references/`](../../tools/design-references/README.md).
- Het ontwerp zelf blijft in `designs/<slug>/v1/` (zie `docs/HANDLEIDING.md`); een uitgebrachte versie wijzig je niet, je maakt een v2. Technische documentatie van een ontwerp die al in een eigen bestand staat (zoals `docs/GOUDEN-AVOND.md`) blijft bestaan en wordt vanuit het ontwerpdocument genoemd.

## Overzicht

| Ontwerp | Slug | Document | Status |
|---|---|---|---|
| Kerstkaart | `kerstkaart` | [kerstkaart.md](kerstkaart.md) | on hold: concept; preview-video en storyboard als referentie in `tools/design-references/kerstkaart/`, nog niet ingebouwd |
| Kerstbol | `kerstbol` (definitief) | [kerstbol.md](kerstbol.md) | on hold: goedgekeurd prototype en assets als referentie in `tools/design-references/kerstbol/`, nog niet ingebouwd |

Voeg een regel toe zodra er een ontwerpdocument is. Bestaande ontwerpen worden hier pas ingevuld als de eigenaar daarom vraagt.
