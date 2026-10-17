# Vijf filmkaarten: Zijden gordijn, Bloesemmeer, Bloesemwaaier, Kerstsprookje, Gouden poort

Vijf nieuwe kaarten met een eigen openingsfilm (18 oktober 2026). De films zijn door de eigenaar aangeleverd (staand 720 × 1280, 10 seconden, 30 beelden per seconde, zonder geluid, gegenereerde scènes zonder personen). Elke kaart is opgebouwd zoals Rozenboog: de film is de opening, de kop toont het laatste beeld van de film met de namen in de lucht en de datum vrij in het licht eronder, en de uitnodiging loopt door in dezelfde wereld met uitsneden uit de film tussen de onderdelen.

| Kaart (`slug`) | Film | Gelegenheden | Kleuren | Namen |
|---|---|---|---|---|
| Zijden gordijn (`zijden-gordijn`) | Ivoren zijden gordijnen met witte rozen schuiven open naar een terras met fontein en een kasteel bij zonsondergang | bruiloft, verloving, jubileum | Ivoor en goud | Pinyon Script |
| Bloesemmeer (`bloesemmeer`) | Een wand van kersenbloesem opent naar een bergmeer met waterval en opkomende zon (geen gebouwen) | bruiloft, verloving, verjaardag, babyshower | Bloesemroze | Parisienne |
| Bloesemwaaier (`bloesemwaaier`) | Een ivoren waaier met bloesem klapt dicht en onthult een lantaarntuin met houten brug en waterval | bruiloft, verloving, jubileum, verjaardag | Zonsondergang | Great Vibes |
| Kerstsprookje (`kerstsprookje`) | Besneeuwde dennen vol gouden lichtjes schuiven open naar een kerstplein met een hoge kerstboom onder de sterren | kerst | Nachtblauw en goud (donker) | Great Vibes |
| Gouden poort (`gouden-poort`) | Gouden deuren met sterpatroon gaan open naar een paleistuin met koepel, palmen en waterpartij | bruiloft, verloving, jubileum, verjaardag | Champagne en goud | Gilda Display |

Welke video bij welke kaart hoort, en de gelegenheid en naam, zijn een voorstel van mij (Claude): de eigenaar kan ze in de manifesten (`designs/<slug>/v1/manifest.json`) aanpassen. Tekst en lettertype van de rest staan in de bestaande bestanden (`Cormorant Garamond` en `Figtree`).

## Wat is vastgelegd

- **Verborgen (groep C)** in `catalog/collectie.py`, zoals Rozenboog en Kerstmagie: de ontwerpen staan in de catalogus, maar zijn niet zichtbaar in de collectie, niet te kiezen en niet bestelbaar; ingelogde beheerders kunnen het voorbeeld bekijken (`/voorbeeld/<slug>/?gelegenheid=…`), alle anderen krijgen een 404. Reden: de rechten op de films zijn nog niet bevestigd. Zichtbaar maken: verplaats de slugs van C naar B in `catalog/collectie.py` (voor nieuwe databases), zet in Beheer → Ontwerpen *Zichtbaar en bestelbaar* aan (bestaande databases, zoals staging), en pas de aantallen in `test_collectie`, `test_prijsstructuur` en `test_effects` aan. Niet doen zonder akkoord van de eigenaar.
- **Indeling Luxe** in `catalog/prijzen.py` (voorstel naar analogie van Rozenboog en de kerstfilms). Er is geen prijs gewijzigd of toegevoegd: een kaart kost de bestaande Luxe-prijs van de gelegenheid (kerst € 24,95, verjaardag € 34,95, bruiloft € 59,95, jubileum en verloving € 39,95, babyshower € 34,95). De eigenaar bevestigt Luxe of kiest Special; Special vraagt de special-vlag en een eigen meerprijs.
- **Geen envelop**: `envelope_mode: built_in`, de eigen filmopening; er is geen stap *Envelop en zegel*.
- **Opening**: een tik op *Open de uitnodiging* start de film (nooit vanzelf); de film speelt na de tik. Bij minder beweging, stilgezette beweging, een directe link naar de aanmelding en in het kleine voorbeeld opent de kaart direct op het eindbeeld. Dit is de gedeelde filmopening in `invite.js`; er is niets aan gedeelde bestanden veranderd.
- **Effecten** (bestaande keuzes uit `catalog/effects.py`): Zijden gordijn goudstof met bloemblaadjes; Bloesemmeer en Bloesemwaaier bloesem; Kerstsprookje sneeuw met sterren; Gouden poort goudstof met vonken. De kleuren van de deeltjes staan in het manifest (`--fx-1` tot `--fx-4`).

## Bestanden

| Bestand | Wat |
|---|---|
| `designs/<slug>/v1/manifest.json` | gegevens, palet, effecten, blok `film` |
| `designs/<slug>/v1/invitation.html`, `style.css` | gegenereerd uit het gedeelde sjabloon `tools/introkaarten/sjabloon/` (een kopie van Rozenboog zonder rozen- en terrasdetails), met de kleuren in het manifest en de plek van de namen onderaan `style.css` (`--fk-sky-*`) |
| `designs/<slug>/v1/opening.mp4` | de film, opnieuw gecodeerd voor het web: H.264, geen geluid, `+faststart`, 1,4 tot 1,9 MB |
| `designs/<slug>/v1/poster.webp`, `end.webp` | eerste beeld (het gesloten beeld voor de tik) en laatste beeld (gelijk aan het laatste beeld van de film) |
| `designs/<slug>/v1/cut-a…d.webp`, `band.webp`, `gal-1…4.webp` | uitsneden uit de film tussen de onderdelen, voor de afsluiting en als voorbeeldbeelden in de galerij |
| `static/img/designs/<slug>.webp` | kaartbeeld voor de collectie (800 × 1000, uit het eindbeeld) |
| `tools/introkaarten/maak_introkaarten.py` | maakt alle bestanden hierboven uit de vijf bronfilms: `python tools/introkaarten/maak_introkaarten.py <map met curtains.mp4, blossom.mp4, fan.mp4, christmas.mp4, palace.mp4> [slug …]` (Python met Pillow en ffmpeg) |
| `tests/test_introkaarten.py` | manifest, verborgen, Luxe en prijs, media, tekstkleuren, voorbeeld alleen voor beheerders, CSP |

De bronfilms staan niet in Git (alleen in de gedeelde projectmap). De herkomst: `curtains.mp4` = *Vertical_luxury_wedding_reveal…*, `blossom.mp4` = *One_continuous_cinematic_vertical_10_second_nature_reveal…*, `fan.mp4` = *Premium_cinematic_vertical_wedding_reveal…*, `christmas.mp4` = *Premium_magical_Christmas_cinematic…*, `palace.mp4` = de film in de upload zonder bestandsnaam (gouden deuren en paleis).

## Aanpassen

De kaarten delen één opbouw. Een wijziging aan het sjabloon of de gegevens in `maak_introkaarten.py` en opnieuw genereren overschrijft de bestanden in `designs/<slug>/v1/`. Een kaart die al in gebruik is, wijzig je niet: maak een v2 (zie `docs/HANDLEIDING.md`).

## Rechten

De films lijken met AI gemaakt. De eigenaar bevestigt dat ze eigen materiaal zijn en commercieel gebruikt mogen worden (zoals bij Kerstmagie en Rozenboog bevestigd voor een eigen Runway-account); tot die bevestiging blijven de kaarten verborgen.
