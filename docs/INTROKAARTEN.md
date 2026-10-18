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
| `designs/<slug>/v1/opening.mp4` | de film, opnieuw gecodeerd voor het web: H.264 (High, level 3.1), geen geluid, `+faststart`, 1,4 tot 1,9 MB |
| `designs/<slug>/v1/opening.webm` | dezelfde film als extra formaat (VP9, geen geluid), 2,2 tot 2,9 MB, voor browsers zonder H.264; staat als tweede bron in het blok `film` (`"webm"`). MP4 blijft het hoofdformaat |
| `designs/<slug>/v1/poster.webp`, `end.webp` | eerste beeld (het gesloten beeld voor de tik) en laatste beeld (gelijk aan het laatste beeld van de film) |
| `designs/<slug>/v1/cut-a…d.webp`, `band.webp`, `gal-1…4.webp` | uitsneden uit de film tussen de onderdelen, voor de afsluiting en als voorbeeldbeelden in de galerij |
| `static/img/designs/<slug>.webp` | kaartbeeld voor de collectie (800 × 1000, uit het eindbeeld) |
| `tools/introkaarten/maak_introkaarten.py` | maakt alle bestanden hierboven uit de vijf bronfilms: `python tools/introkaarten/maak_introkaarten.py <map met curtains.mp4, blossom.mp4, fan.mp4, christmas.mp4, palace.mp4> [slug …]` (Python met Pillow en ffmpeg) |
| `tests/test_introkaarten.py` | manifest, verborgen, Luxe en prijs, media, tekstkleuren, voorbeeld alleen voor beheerders, CSP |

De bronfilms staan niet in Git (alleen in de gedeelde projectmap). De herkomst: `curtains.mp4` = *Vertical_luxury_wedding_reveal…*, `blossom.mp4` = *One_continuous_cinematic_vertical_10_second_nature_reveal…*, `fan.mp4` = *Premium_cinematic_vertical_wedding_reveal…*, `christmas.mp4` = *Premium_magical_Christmas_cinematic…*, `palace.mp4` = de film in de upload zonder bestandsnaam (gouden deuren en paleis).

## Aanpassen

De kaarten delen één opbouw. Een wijziging aan het sjabloon of de gegevens in `maak_introkaarten.py` en opnieuw genereren overschrijft de bestanden in `designs/<slug>/v1/`. Een kaart die al in gebruik is, wijzig je niet: maak een v2 (zie `docs/HANDLEIDING.md`).

## Rechten per videobestand (18 oktober 2026)

**Voor geen van de vijf films zijn de commerciële gebruiksrechten aantoonbaar bevestigd.** De kaarten blijven daarom verborgen (groep C) en alleen voor beheerders te bekijken, voor interne beoordeling.

Wat wel vaststaat, uit de bestanden zelf (`ffprobe`): alle vijf zijn 720 × 1280, 10 seconden, zonder geluid, en dragen een metadata-label `AIGC` (`Label: 1`, een aanduiding van door AI gegenereerde inhoud) met dezelfde `ContentProducer`-code `001191330106MA2CFLDG4R10001` en een eigen `ProduceID` per film. Dat label zegt dát de film door AI is gemaakt en door welke dienst die is geproduceerd; het zegt niets over wie de gebruiksrechten heeft of of commercieel gebruik is toegestaan, en het bewijst die rechten dus niet. De code hoort bij een dienst die ik niet kan herleiden tot Runway; de bevestiging van 16 oktober 2026 (eigen Runway-account, zie `docs/OVERDRACHT.md` punt 14) gaat over de films van Rozenboog en Kerstmagie en dekt deze vijf niet. Ik neem niet aan dat dezelfde dienst of voorwaarden gelden.

| Film (bronbestand in de projectmap) | Kaart | `ProduceID` in het label | Herkomst aantoonbaar | Commerciële rechten aantoonbaar |
|---|---|---|---|---|
| *Vertical_luxury_wedding_reveal…* (`curtains.mp4`) | Zijden gordijn | `R-pvZYHTo6Rsaw8or5VXzZjQ` | Aangeleverd door de eigenaar; dienst en account onbekend | Nee |
| *One_continuous_cinematic_vertical_10_second_nature_reveal…* (`blossom.mp4`; staat er twee keer, identiek) | Bloesemmeer | `R-HOI8UO04RtCj9ZiScOGD8Q` | Idem | Nee |
| *Premium_cinematic_vertical_wedding_reveal…* (`fan.mp4`) | Bloesemwaaier | `R-1XxXJActQEie8Bv5Xey1Gg` | Idem | Nee |
| *Premium_magical_Christmas_cinematic…* (`christmas.mp4`) | Kerstsprookje | `R-YNw_bsoxSvKHLxxVq-pt8Q` | Idem | Nee |
| upload zonder bestandsnaam, gouden deuren en paleis (`palace.mp4`) | Gouden poort | `R-Xs24VZRhRNu_HNmMEO0T7Q` | Idem | Nee |

Nodig per film, van de eigenaar: met welke dienst en op wiens account de film is gemaakt, en een bevestiging of schriftelijke voorwaarden (of een uitdrukkelijk akkoord van de eigenaar) dat commercieel gebruik in verkochte uitnodigingen is toegestaan. Pas daarna kan een kaart zichtbaar worden (zie "Wat is vastgelegd"). Het label staat niet meer in de films op de website: de web-versies zijn opnieuw gecodeerd en bevatten geen metadata; de bronbestanden staan alleen in de projectmap.

## Controle van de films (18 oktober 2026)

Zie `docs/CONTROLES.md`, "Vijf filmkaarten". Kort: de testbrowser van deze omgeving kan geen H.264 afspelen; het afspelen is daar daarom met de WebM gecontroleerd, de MP4 is met `ffprobe` en `ffmpeg` gecontroleerd (geldig, volledig decodeerbaar, `+faststart`, geen geluid) maar niet in een echte browser afgespeeld. Bij het eerste onderzoek bleek dat de film in die browser stil werd overgeslagen omdat er geen bruikbare bron was; dat is verholpen met de WebM-bron.
