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

## Premium laag, voorbeeld op Bloesemmeer (18 oktober 2026, ter goedkeuring)

Op verzoek van de eigenaar is eerst alleen **Bloesemmeer** verfijnd, om te beoordelen voor de andere vier hetzelfde krijgen. De openingsfilm, het ontwerp en de bestaande animaties zijn niet aangepast. Wat er bij is gekomen (alleen in `designs/bloesemmeer/v1/`, behalve de keuze `scrollwind`):

- **Licht op het water**: drie lagen kleine, langgerekte lichtjes met eigen maat, tempo en fase, plus een smalle zonnebaan die langzaam in- en uitademt (`.fk-water`), over het water van het eindbeeld.
- **Nevel op twee dieptes** (`.fk-mist`): zachte, langzaam verschuivende banden bij de dalen en bij de waterval.
- **Diepte bij het scrollen**: nevel en water schuiven iets sneller omhoog dan het beeld (scrollgestuurde CSS-animatie, alleen waar de browser die kent).
- **Bloesemblaadjes over de kop**: de bestaande sfeer *Bloesem* valt nu ook over het beeld van de kop (een eigen laag die alleen loopt terwijl de kop in beeld is), achter de namen en de datum. De kleuren `--fx-1` tot `--fx-3` zijn iets dieper roze, zodat de blaadjes op de lichte lucht te zien zijn.
- **Blaadjes reageren op scrollen** (`scrollwind`, nieuwe optionele keuze in `catalog/effects.py` en `effects.js`): scrollen duwt de blaadjes zacht opzij (hoogstens 16 px/s) en verschuift ze licht mee, grote blaadjes iets meer dan kleine. Alleen ontwerpen die `scrollwind` kiezen merken er iets van; alle andere ontwerpen zijn ongewijzigd.

Alles is decoratief (`aria-hidden`, niet aanklikbaar), staat achter de tekst, beweegt alleen onder `.fx-motion` (dus niet bij 'minder beweging' of na stilzetten met de knop *Beweging*) en gebruikt alleen `transform` en `opacity` (geen filter of overvloeimodus). Zichtbaar na het openen van de uitnodiging, met een rustige inblending. De kaart blijft verborgen en niet bestelbaar.

### Doorgetrokken naar de andere vier kaarten (18 oktober 2026, ter beoordeling)

Na akkoord op de aanpak kregen de andere vier kaarten dezelfde techniek, met een eigen identiteit; Bloesemmeer is daarbij niet meer aangeraakt. De plekken zijn percentages van het eindbeeld en staan in `tools/introkaarten/premium_laag.py` (herhaalbaar: `python tools/introkaarten/premium_laag.py [slug …]`, daarna `manage.py sync_designs --update-manifest`; vervangt alleen wat tussen de markeringen `premium-laag begin/einde` staat).

| Kaart | Identiteit | Blaadjes of sneeuw (sfeer, `--fx-density`) |
|---|---|---|
| Zijden gordijn | warme zonsondergang op het terras: ademende gloed van zon, fontein, kaarsen en ramen, zachte glinstering op het terras, lichte nevel | enkele rozenblaadjes (*Bloemblaadjes*, roze en ivoor, 0,3) |
| Bloesemwaaier | lantaarntuin: negen lantaarns en de zon die zacht ademen, nevel bij de waterval, lichtjes en zonnebaan op het water | dwarrelende bloesem (*Bloesem*, 0,8) |
| Kerstsprookje | kerstplein: warme gouden lichtpuntjes in de boom, lantaarns en carrousel, lichte winternevel, glans op het ijs; geen bloesem of rozen | fijne sneeuw (*Sneeuw*, 0,6) |
| Gouden poort | architectuur en luxe: een lichtbaan die eens per 18 seconden over de gouden bogen en de koepel trekt, glans op de lantaarns en de waterpartij, enkele lichtpuntjes op de koepel | heel spaarzame champagnekleurige blaadjes (*Bloemblaadjes*, 0,18) |

Nieuw in de gedeelde `effects.js`, beide opt-in en zonder invloed op andere ontwerpen: `scrollwind` (zie hierboven) en de stijlvariabele `--fx-density` (0 tot 1: minder deeltjes dan de standaard van de sfeer). De kleuren `--fx-1` tot `--fx-3` zijn bij Zijden gordijn en Gouden poort aangepast (roze en ivoor, champagne), zodat de blaadjes bij de kaart passen.

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

## Knoppen en plaatsregel op mobiel (18 oktober 2026)

De pauze- en muziekknop zweven in de hoeken van het scherm. Het blok `knop-ruimte` onderaan `style.css` (en in het sjabloon) houdt de regel met tijd en plaats op schermen tot 480 px tussen de knoppen. Zie `docs/CONTROLES.md`. Dezelfde regel staat ook in `designs/rozenboog/v1/style.css` (`.rb-meta`).

## Link Aanmelden in de kop (18 oktober 2026)

Een kleine link `Aanmelden` (`.fk-aanmeld`, bij Rozenboog `.rb-aanmeld`) staat rechtsboven in de kop en wijst naar `#aanmelden`. Hij verschijnt alleen als aanmelden kan (`v.show.rsvp and not v.rsvp.closed_reason`) en pas na de film, omdat de uitnodiging tot dan inert is. Stijl: blok `aanmeld-link` in `style.css` en het sjabloon. Zie `docs/CONTROLES.md`.

## Afronding van de ontwikkelronde van de vijf filmkaarten (18 oktober 2026)

Stand: ontwikkelcommit `42e1dca` staat op de stagingtak `claude/vaylide-master-collectie` en is daar live (deploy van 20:22 UTC). De ontwikkelbranch `claude/project-thread-m2kme8` heeft daarna alleen documentatie erbij. Productie is niet aangeraakt.

**Echt uitgevoerd en geslaagd**
- Tests: `manage.py test tests` (1391 tests) na de laatste codewijziging; alleen de twee bekende falers door de lokale `.env` (`VIERLIEF_CONTACT_EMAIL`, tests `test_voorwaarden_nieuw`), die niets met deze kaarten te maken hebben. Na afronding opnieuw de tests voor de kaarten, collectie, prijsstructuur, film en effecten: 108 tests, geslaagd.
- axe (`e2e/toegankelijkheid.cjs`, dicht en open): 0 bevindingen voor alle zes kaarten (de vijf plus Rozenboog).
- Chromium: film, eindbeeld, effectlaag, pauzeknop, minder beweging, vier schermbreedtes, knoppen naast de plaatsregel, link Aanmelden (plaatsing, toetsenbord, inert tijdens de film), vloeiendheid met vertraagde processor. Details per onderdeel: eerdere secties in dit document.
- Staging, alleen-lezen: deploy live, geen fouten of waarschuwingen in de logs, `/healthz` 200, geen migraties; stagingdatabase: 63 ontwerpen waarvan 47 actief, de vijf kaarten inactief, geen medewerkersaccount.

**Bewust overgeslagen (besluit van de eigenaar, 18 oktober 2026)**
- Handmatige controle op de eigen telefoon op staging (Safari, Android Chrome); daarvoor is geen tijdelijk beheeraccount aangemaakt.
- Browsercontrole op de stagingsite zelf: de cloudomgeving bereikt die niet; niet verder uitgezocht.
- Safari en Firefox in de testomgeving, echte telefoons, de MP4 op echte apparaten (testbrowser heeft geen H.264; WebM en `ffprobe` zijn gebruikt).

**Verborgen en niet bestelbaar**: groep C in `catalog/collectie.py`; in de stagingdatabase `is_active = false` voor alle vijf (gelezen op 18 oktober 2026, na de laatste deploy); tests: 404 voor bezoekers en klanten, niet in collectie, zoeken en sitemap, niet te kiezen in de bestelroute (ook niet voor beheerders), geen wijziging in prijzen. Prijzen, betalingen en bestaande ontwerpen zijn niet gewijzigd.

**Nog open, bij de eigenaar**: de commerciële gebruiksrechten per film (zie "Rechten per videobestand": voor alle vijf nog niet bevestigd) en de controle op echte telefoons. Geen publieke activatie, verkoop of productie-uitrol zonder nieuw akkoord.

## Herkomst en Runway-voorwaarden (18 oktober 2026, 20:50)

**Verklaring van de eigenaar** (bericht van 18 oktober 2026, 20:50): alle vijf openingsvideo's zijn door hemzelf gemaakt met zijn eigen Runway-account. Dit is een mondelinge verklaring; er is nog geen bewijs uit het account bijgevoegd (plan, datum van de generatie, exportoverzicht).

**Wat ik wel en niet kon controleren**
- De officiële voorwaarden van Runway waren niet te openen: de cloudomgeving bereikte runwayml.com en de helppagina's niet (DNS-fout). Ik claim dus niet de voorwaarden zelf gelezen te hebben.
- Wat wel te vinden was (zoekresultaten, alleen secundaire bronnen en deels tegenstrijdig): Runway claimt geen eigendom van uitvoer; volgens sommige bronnen is commercieel gebruik alleen toegestaan met een betaald abonnement en is de uitvoer van het gratis plan watermerk en bedoeld voor persoonlijk gebruik, volgens andere beperkt Runway commercieel gebruik niet. Dat is geen basis voor een rechtenbesluit.
- De bestanden zelf dragen een `AIGC`-label met een `ContentProducer`-code die ik niet tot Runway kan herleiden (zie "Rechten per videobestand"). Dat past niet vanzelf bij de verklaring van de eigenaar en is niet uitgelegd. Het is geen bewijs tegen de verklaring, maar het is wel een open vraag.

**Besluit:** commercieel gebruik is **niet voldoende bevestigd**; de rechtenblokkade is daarom **niet opgeheven**. Alle vijf blijven "Nee" in de tabel hierboven; de kaarten blijven verborgen (groep C).

**Wat de blokkade kan opheffen** (door de eigenaar aan te leveren):
1. Uit het Runway-account: per film het abonnement (plan) op het moment van genereren en het overzicht van de generatie (naam of prompt, datum), bijvoorbeeld als schermafbeelding.
2. De versie en datum van de Runway-voorwaarden die toen golden, met de passage over commercieel gebruik van uitvoer (of een bevestiging dat het plan commercieel gebruik toestaat).
3. Een verklaring waarom de bestanden een `ContentProducer`-code dragen die niet van Runway lijkt te zijn (bijvoorbeeld omdat de film via een andere dienst of een export is gelopen).
Daarna werk ik de tabel per film bij.
