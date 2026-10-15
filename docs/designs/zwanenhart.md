# Zwanenhart

## 1. Naam
Zwanenhart

## 2. Slug
`zwanenhart` (`designs/zwanenhart/v1/`)

## 3. Categorie
Special (groep A in `catalog/collectie.py`, `special: true`). Trouwkaart: Special € 89,95 incl. btw, 12 maanden online (besluit van de eigenaar, 15 oktober 2026; bestaand bedrag in `catalog/prijzen.py`). De gelegenheden verloving en jubileum horen er ook bij en krijgen daar het bestaande Special-bedrag (€ 69,00); er is geen nieuw prijspunt.

## 4. Status
Lokaal geïntegreerd op de kerstontwerpen-branch en getest; nog niet gecommit, niet op staging of live.

## 5. Concept / verhaal
Een ivoren envelop met reliëfbloemen en een gouden lakzegel. Na een tik gloeit het zegel, de envelop opent en uit het licht verschijnen twee witte zwanen op een meer met bloesem. Ze buigen naar elkaar toe tot hun halzen een hart vormen.

## 6. Opening / animatie
Film van 6,5 s (720x1280, H.264, zonder geluid), alleen na een tik. De namen verschijnen op 5,8 s. Opening over te slaan; bij 'minder beweging', stilgezette beweging of een tweede bezoek staat direct het eindbeeld. Start de film niet binnen 6 s, dan volgt het eindbeeld.

## 7. Pagina na de opening
Namen, datum, aftellen, verhaal, galerij, programma, locatie, dresscode, praktisch, aanmelden, contact, afsluiting, muziek. Eén kleurvariant: Ivoor en champagnegoud.

## 8. Assets en waar ze staan
`designs/zwanenhart/v1/media/` (film, posters, beelden), `static/img/designs/zwanenhart.webp` (kaartbeeld). De twee originele Runway-video's staan niet in de repo (alleen nodig om de film opnieuw te maken).

## 9. Externe AI/video-output
De film is gegenereerd (Runway) en gemonteerd met ffmpeg; zonder personen. Rechten bevestigt de eigenaar.

## 10. Technische bouwinstructies
Zie `designs/zwanenhart/v1/zwanenhart.js` en de tests in `tests/test_zwanenhart.py`. De film heeft alleen een mp4-bron; de sandbox speelt geen H.264, dus in de browsertest wordt een VP9-kopie gebruikt (`e2e/zwanenhart_functies.cjs`).

## 11. Wat al afgerond is
Ontwerp, tests, indeling (Special), collectie (A), sort_order 14, demo-gegevens, bestelroute met € 89,95.

## 12. Wat nog moet gebeuren
Echte telefoon, Safari, Firefox en H.264 in Chrome/Edge op Windows; `e2e/effecten.cjs` voor dit ontwerp.

## 13. Besluiten die niet opnieuw ter discussie hoeven
Special, € 89,95 voor een trouwkaart, 12 maanden.

## 14. Laatste relevante commit
Nog niet gecommit.

## 15. Volgende stap
Beoordelen door de eigenaar, daarna commit en staging.
