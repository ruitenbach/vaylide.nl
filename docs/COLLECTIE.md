# De officiële VAYLIDE-collectie (A, B en C)

Stand: 4 oktober 2026, branch `claude/vaylide-master-collectie` (gebouwd op `claude/aurora-nocturne`). Deze indeling is een voorstel van
de eigenaar en is bewust klein gehouden: er zijn geen ontwerpen opnieuw gebouwd, aangepast of verwijderd.

## Wat A, B en C betekenen

| Groep | Betekenis | Aantal |
|---|---|---|
| **A** | Prominent tonen: staat vooraan in de collectie | 11 |
| **B** | Secundair behouden: staat na de A-ontwerpen | 26 |
| **C** | Technisch bewaren, voorlopig niet tonen | 9 |

De indeling staat op één plek: `catalog/collectie.py` (met de redenen per groep). Een nieuw ontwerp dat daar niet staat, is B.

- **A**: Aurora Nocturne, Midnight Émeraude, Rosé Royale, Balzaal, Golden Noël (de vijf Specials), Liefde op papier, Voor altijd, Avondgoud,
  Puur moment, Winterlicht en Gloria.
- **B**: Eerste dans, Aan tafel, Middernacht en 23 Atelier-ontwerpen (zie het bestand).
- **C**: Ho ho ho, Sneeuwpret, Wolkje, Stipjes, Door de jaren, Mijlpaal, Borrel, Congres en Lijnenspel.

## Hoe het in het platform werkt (zonder nieuwe functies)

Er is geen nieuwe databasekolom of schermonderdeel. De bestaande velden van een ontwerp doen het werk:

- **A vóór B**: via `sort_order`. Alle A-ontwerpen hebben een lager nummer dan alle B-ontwerpen en geen twee ontwerpen delen een nummer.
- **C niet tonen**: `is_active` staat uit (Beheer → Ontwerpen → "Zichtbaar en bestelbaar"). Het ontwerp staat dan niet in de collectie, de
  zoekfunctie of de Studio. De map, de versies en **alle bestaande uitnodigingen blijven gewoon werken**. Aanzetten in Beheer brengt het
  ontwerp meteen terug.
- **Specials**: `special` staat aan voor Aurora Nocturne, Midnight Émeraude, Rosé Royale, Balzaal en Golden Noël. Winterlicht is A maar
  bewust geen special. Specials staan onder Specials; een eigen meerprijs is een optie `special-<code>` in Beheer → Prijzen. Zonder die
  optie kost een special gewoon de prijs van het pakket (keuze van de eigenaar, zie `tests/test_specials.py`). Voor Midnight Émeraude en
  Rosé Royale is er nog geen meerprijs ingesteld; die verzin ik niet.

### Nieuwe en bestaande databases

- **Nieuwe database**: `catalog/seed.py` leest de manifesten (`sort_order`, `special`) en zet C-ontwerpen op niet zichtbaar.
- **Bestaande database** (zoals staging): migratie `catalog/migrations/0006_collectie_abc.py` past **één keer** de zichtbaarheid van C,
  de twee nieuwe specials en de nieuwe volgorde toe. Daarna beslist Beheer: opnieuw inlezen van de ontwerpen (`sync_designs`) zet een
  keuze van de eigenaar niet terug.

## Eenmalige opschoning van gegevens in deze ronde

- Dubbele `sort_order` opgelost: Aurora Nocturne en Rosé Royale (8) en Golden Noël en Gloria (39).
- Kaartbeelden toegevoegd voor Midnight Émeraude, Rosé Royale en Golden Noël (`static/img/designs/`, gemaakt met
  `e2e/make_design_images.cjs`, de geopende kaart).
- `envelope_mode` staat nu in elk manifest (`optional` voor 11 ontwerpen, `built_in` voor de andere 35). De Atelier-generator
  (`tools/atelier/`) schrijft het ook, zodat opnieuw genereren niets verandert. De tabel `ONTWERP_MODUS` in
  `catalog/envelop_collectie.py` blijft de terugval voor ontwerpversies die al in een database staan (daar wordt het manifest niet
  bijgewerkt); `tests/test_collectie.py` bewaakt dat beide overeenkomen.
- Homepage, kerstpodium: Ho ho ho en Sneeuwpret zijn C en vervangen door Golden Noël (`HOME_KERST` in `core/content.py`).

## Bewust voor later

- **Liefde op papier v2** (branch `peaceful-pasteur-tbzswi` in `bootsman075-ops/vaylide.nl`) is niet samengevoegd. Het moet opnieuw op de
  nieuwe basis worden gebouwd, met het persoonlijke zegel van Compleet, zonder groot VAYLIDE-logo op de envelop van iedere klant.
- **Royal Christmas, Winter White en Midnight Gala**: in Git niet gevonden en niet opnieuw gebouwd.
- **Instagram Reel en promofilmpje** (`tools/reel`, `tools/promo` op de upstream-branches): marketinghulpmiddelen, buiten de kaartencollectie.
- Geen GSAP-upgrade van andere kaarten, geen redesigns, geen nieuwe kaarten.
- Een visuele uitlichting van A (bijvoorbeeld een eigen sectie op de collectiepagina) bestaat nog niet; A staat nu alleen vooraan.
- De zakelijke lijn is dun (Gala, Strak zakelijk, Avondgoud, Puur moment).
