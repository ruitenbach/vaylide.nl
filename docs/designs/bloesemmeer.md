# Bloesemmeer

## 1. Naam

Bloesemmeer

## 2. Slug

`bloesemmeer`   (de map `designs/bloesemmeer/v1/`, de demo-URL `/voorbeeld/bloesemmeer/`)

## 3. Categorie

Gewone kaart met openingsfilm, indeling Luxe (bestaande Luxe-prijs per gelegenheid, geen eigen meerprijs; goedgekeurd door de eigenaar op 18 oktober 2026) · gelegenheden: bruiloft, verloving, verjaardag, babyshower · kleuren: Bloesemroze. Groep C: verborgen.

## 4. Status

Lokaal klaar, ter beoordeling (18 oktober 2026), op de ontwikkelbranch `claude/project-thread-m2kme8`. Niet op staging, niet zichtbaar, niet bestelbaar. Zichtbaar maken wacht op bevestigde rechten van de film.

## 5. Concept / verhaal

Een wand van kersenbloesem opent naar een bergmeer met een waterval in het zonlicht. Eén van de vijf filmkaarten, zie [`../INTROKAARTEN.md`](../INTROKAARTEN.md).

## 6. Opening / animatie

Je ziet eerst een wand van roze kersenbloesem. Na een tik gaat die langzaam open en kijk je uit over een helder meer met een waterval tussen de bergen, terwijl de zon opkomt achter de takken. Daarna staan jullie namen in de lucht en loopt de uitnodiging door met aftellen, programma, locatie en aanmelden, in zachtroze en goud. De opening is over te slaan en rustig bij minder beweging. De film is een gegenereerde scène zonder personen en zonder gebouwen.

## 6a. Premium laag (voorbeeld, 18 oktober 2026, ter goedkeuring)

Licht op het water, nevel op twee dieptes, bloesemblaadjes over de kop en scrollreactie van de blaadjes; zie `docs/INTROKAARTEN.md`. Alleen op deze kaart; de andere vier wachten op akkoord van de eigenaar.

## 7. Pagina na de opening

Opbouw zoals Rozenboog: kop met het laatste beeld van de film, namen in de lucht, daarna aftellen, verhaal, programma, locatie en aanmelden, met uitsneden uit de film tussen de onderdelen. Effecten (uit `catalog/effects.py`): sfeer: bloesem, knal: bloesem, viering: bloesem, namen: zacht, onthul: zacht, extra: kenburns, tik.

## 8. Assets en waar ze staan

| Asset | Pad in de repository | Herkomst | Opmerking |
|---|---|---|---|
| Film (MP4, H.264) | `designs/bloesemmeer/v1/opening.mp4` | opnieuw gecodeerd uit het bronbestand | geen geluid, `+faststart` |
| Film (WebM, VP9) | `designs/bloesemmeer/v1/opening.webm` | idem | extra formaat voor browsers zonder H.264 |
| Beelden | `designs/bloesemmeer/v1/poster.webp`, `end.webp`, `cut-a…d.webp`, `band.webp`, `gal-1…4.webp` | stills uit de film | |
| Kaartbeeld | `static/img/designs/bloesemmeer.webp` | uit het eindbeeld | |

Het bronbestand staat niet in Git maar in de gedeelde projectmap: One_continuous_cinematic_vertical_10_second_nature_reveal… (blossom.mp4).

## 9. Externe AI/video-output

Aangeleverd door de eigenaar; de bron- en prompttekst is niet bekend, de bestandsnaam is de enige aanduiding. Het bronbestand heeft een metadata-label `AIGC` (`ProduceID` `R-HOI8UO04RtCj9ZiScOGD8Q`, `ContentProducer` `001191330106MA2CFLDG4R10001`). Dat label bewijst geen gebruiksrechten. **Commerciële rechten: niet aantoonbaar bevestigd** (zie `docs/INTROKAARTEN.md`, "Rechten per videobestand").

## 10. Technische bouwinstructies

Gegenereerd door `tools/introkaarten/maak_introkaarten.py` uit het gedeelde sjabloon `tools/introkaarten/sjabloon/`. Registratie via `sync_designs` (in een bestaande database `--update-manifest`). Geen inline script of stijl (CSP). Wijzigen van een gebruikte kaart gaat via een v2.

## 11. Wat al afgerond is

- Kaart gebouwd en verborgen opgenomen, 18 oktober 2026.
- WebM als extra bron toegevoegd; afspelen, eindscène en overgang gecontroleerd in Chromium (mobiel en desktop, 6 scenario's), axe zonder bevindingen (`docs/CONTROLES.md`).
- Knoppen en plaatsregel op mobiel: blok `knop-ruimte` in `style.css` houdt de plaatsregel tussen de pauze- en muziekknop (18 oktober 2026; `docs/CONTROLES.md`).

## 12. Wat nog moet gebeuren

- [ ] Akkoord van de eigenaar op de premium laag, daarna eventueel naar de andere vier kaarten.
- [ ] Rechten van de film bevestigen (dienst, account, commercieel gebruik).
- [ ] MP4 afspelen op echte telefoons (iOS Safari, Android Chrome), Safari en Firefox.
- [ ] Besluit van de eigenaar over zichtbaar maken.

## 13. Besluiten die niet opnieuw ter discussie hoeven

- Indeling Luxe, geen prijswijziging, kaart blijft verborgen en niet bestelbaar tot de rechten bevestigd zijn (eigenaar, 18 oktober 2026).

## 14. Laatste relevante commit

Zie `git log -- designs/bloesemmeer`.

## 15. Volgende stap

De eigenaar levert per film de herkomst en de bevestiging van commercieel gebruik; daarna beslist de eigenaar over staging en zichtbaar maken.
