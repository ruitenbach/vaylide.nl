# Overdracht naar een andere Claude-sessie (4 oktober 2026)

Alleen de actuele stand van zaken. Er is niets nieuws gebouwd na commit `c290a1c`.

## Repository

- Repository: `ruitenbach/vaylide.nl`
- Branch: `claude/vaylide-master-collectie`
- Laatste inhoudelijke commit: `c290a1c` (dit overdrachtsbestand komt als enige commit daarna)
- Bevat de huidige VAYLIDE-basis: 46 ontwerpen, Envelope Collection, zegelkeuze en monogram, Studio, checkout, toestemmingsopslag,
  bevestigingsmail, Mijn VAYLIDE, beheer en de mastercollectie A/B/C (`catalog/collectie.py`, `docs/COLLECTIE.md`).
- Tests: 587 geslaagd bij `c290a1c`.

## Mastercollectie

| Groep | Aantal | Betekenis |
|---|---|---|
| A | 11 | prominent, staat vooraan |
| B | 26 | secundair behouden |
| C | 9 | verborgen (niet zichtbaar in Beheer), technisch behouden; bestaande uitnodigingen blijven werken |

- Specials: Aurora Nocturne, Midnight Émeraude, Rosé Royale, Balzaal en Golden Noël. Midnight Émeraude en Rosé Royale hebben nog geen
  meerprijs (dus de prijs van het pakket).
- Winterlicht blijft A, maar is geen Special.
- Migratie `catalog/migrations/0006_collectie_abc.py` past bestaande databases eenmalig aan (C verbergen, twee nieuwe specials, volgorde).

## Bewust nog niet gedaan

- Liefde op papier V2 is niet samengevoegd (staat op de upstream-branch `claude/peaceful-pasteur-tbzswi` van `bootsman075-ops/vaylide.nl`).
- Royal Christmas, Winter White en Midnight Gala ontbreken nog (niet in Git gevonden, niet gebouwd).
- Het juridische concept artikel 9/10 (`docs/CONCEPT-ARTIKEL-9-10.md`) is nog niet definitief doorgevoerd.
- Instagram Reel en promofilmpje zijn marketinghulpmiddelen en horen niet bij de kaartencollectie.

## Render

| Onderdeel | Naam | Mag je aanraken? |
|---|---|---|
| Productie webservice | `vaylide` | **Nee, absoluut niet** |
| Productie database | `vaylide-db` | **Nee, absoluut niet** |
| Staging webservice | `vaylide-staging` | Ja |
| Staging database | `vaylide-staging-db` | Ja (alleen via de staging-service) |

Staging draait op dit moment **nog niet** op `claude/vaylide-master-collectie` (maar nog op `claude/envelop-collectie`).

## Volgende stap (alleen voor een sessie met browser- en Render-toegang)

1. Open uitsluitend `vaylide-staging` in het Render-dashboard (controleer de naam; het is niet `vaylide`).
2. Settings → Build & Deploy → Branch: wijzig naar `claude/vaylide-master-collectie` en sla op.
3. Deploy de nieuwste commit van die branch.
4. Controleer in de deploylog en de omgeving dat `vaylide-staging-db` wordt gebruikt (`DATABASE_URL`), nooit `vaylide-db`. Migratie `0006` mag alleen daar draaien.
5. Wacht tot staging op Live staat en geef de staging-URL aan de eigenaar. Niets naar productie zonder uitdrukkelijke toestemming.

Controles daarna (geen nieuwe testcampagne): homepage, collectiepagina (A vooraan, C niet zichtbaar), Specials toont de vijf hierboven, Envelop & zegel
werkt, één gewone kaart en één Special openen, de Studio opent en er staan geen consolefouten. De site staat achter het previewwachtwoord van staging
(gebruikersnaam `voorbeeld`); dat wachtwoord hoort niet in een gesprek of in Git.
