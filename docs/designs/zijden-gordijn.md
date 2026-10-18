# Zijden gordijn

## 1. Naam

Zijden gordijn

## 2. Slug

`zijden-gordijn`   (de map `designs/zijden-gordijn/v1/`, de demo-URL `/voorbeeld/zijden-gordijn/`)

## 3. Categorie

Gewone kaart met openingsfilm, indeling Luxe (bestaande Luxe-prijs per gelegenheid, geen eigen meerprijs; goedgekeurd door de eigenaar op 18 oktober 2026) · gelegenheden: bruiloft, verloving, jubileum · kleuren: Ivoor en goud. Groep C: verborgen.

## 4. Status

Lokaal klaar, ter beoordeling (18 oktober 2026), op de ontwikkelbranch `claude/project-thread-m2kme8`. Niet op staging, niet zichtbaar, niet bestelbaar. Zichtbaar maken wacht op bevestigde rechten van de film.

## 5. Concept / verhaal

Zijden gordijnen vol bloemen schuiven open naar een kasteel in het avondlicht. Eén van de vijf filmkaarten, zie [`../INTROKAARTEN.md`](../INTROKAARTEN.md).

## 6. Opening / animatie

Je ziet eerst gesloten ivoren zijden gordijnen met witte rozen en gouden borduursel. Na een tik schuiven ze open en kijk je door naar een terras met een fontein, kaarsen en een kasteel in het licht van de ondergaande zon. Daarna staan jullie namen in de lucht en loopt de uitnodiging door met aftellen, programma, locatie en aanmelden, in ivoor en goud. De opening is over te slaan en rustig bij minder beweging. De film is een gegenereerde scène zonder personen.

## 6a. Premium laag (18 oktober 2026, ter beoordeling)

enkele rozenblaadjes, warme lichtreflecties; zie `docs/INTROKAARTEN.md` en `tools/introkaarten/premium_laag.py` (de plekken staan daar). Bloesemmeer is het voorbeeld waarop dit is gebaseerd.

## 7. Pagina na de opening

Opbouw zoals Rozenboog: kop met het laatste beeld van de film, namen in de lucht, daarna aftellen, verhaal, programma, locatie en aanmelden, met uitsneden uit de film tussen de onderdelen. Effecten (uit `catalog/effects.py`): sfeer: goudstof, knal: blaadjes, viering: blaadjes, namen: schrijf, onthul: zacht, extra: kenburns, tik.

## 8. Assets en waar ze staan

| Asset | Pad in de repository | Herkomst | Opmerking |
|---|---|---|---|
| Film (MP4, H.264) | `designs/zijden-gordijn/v1/opening.mp4` | opnieuw gecodeerd uit het bronbestand | geen geluid, `+faststart` |
| Film (WebM, VP9) | `designs/zijden-gordijn/v1/opening.webm` | idem | extra formaat voor browsers zonder H.264 |
| Beelden | `designs/zijden-gordijn/v1/poster.webp`, `end.webp`, `cut-a…d.webp`, `band.webp`, `gal-1…4.webp` | stills uit de film | |
| Kaartbeeld | `static/img/designs/zijden-gordijn.webp` | uit het eindbeeld | |

Het bronbestand staat niet in Git maar in de gedeelde projectmap: Vertical_luxury_wedding_reveal… (curtains.mp4).

## 9. Externe AI/video-output

Aangeleverd door de eigenaar; de bron- en prompttekst is niet bekend, de bestandsnaam is de enige aanduiding. Het bronbestand heeft een metadata-label `AIGC` (`ProduceID` `R-pvZYHTo6Rsaw8or5VXzZjQ`, `ContentProducer` `001191330106MA2CFLDG4R10001`). Dat label bewijst geen gebruiksrechten. **Commerciële rechten: niet aantoonbaar bevestigd** (zie `docs/INTROKAARTEN.md`, "Rechten per videobestand").

## 10. Technische bouwinstructies

Gegenereerd door `tools/introkaarten/maak_introkaarten.py` uit het gedeelde sjabloon `tools/introkaarten/sjabloon/`. Registratie via `sync_designs` (in een bestaande database `--update-manifest`). Geen inline script of stijl (CSP). Wijzigen van een gebruikte kaart gaat via een v2.

## 11. Wat al afgerond is

- Kaart gebouwd en verborgen opgenomen, 18 oktober 2026.
- WebM als extra bron toegevoegd; afspelen, eindscène en overgang gecontroleerd in Chromium (mobiel en desktop, 6 scenario's), axe zonder bevindingen (`docs/CONTROLES.md`).
- Knoppen en plaatsregel op mobiel: blok `knop-ruimte` in `style.css` houdt de plaatsregel tussen de pauze- en muziekknop (18 oktober 2026; `docs/CONTROLES.md`).
- Link 'Aanmelden' rechtsboven in de kop, naar `#aanmelden`, alleen als aanmelden kan (blok `aanmeld-link`, 18 oktober 2026; `docs/CONTROLES.md`).

## 12. Wat nog moet gebeuren

- [ ] Rechten van de film bevestigen (dienst, account, commercieel gebruik).
- [ ] MP4 afspelen op echte telefoons (iOS Safari, Android Chrome), Safari en Firefox.
- [ ] Besluit van de eigenaar over zichtbaar maken.

## 13. Besluiten die niet opnieuw ter discussie hoeven

- Indeling Luxe, geen prijswijziging, kaart blijft verborgen en niet bestelbaar tot de rechten bevestigd zijn (eigenaar, 18 oktober 2026).

## 14. Laatste relevante commit

Zie `git log -- designs/zijden-gordijn`.

## 15. Volgende stap

De eigenaar levert per film de herkomst en de bevestiging van commercieel gebruik; daarna beslist de eigenaar over staging en zichtbaar maken.
