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

## Productie-uitrol met verborgen kaarten (18 oktober 2026, 23:00)

Uitdrukkelijk akkoord van de eigenaar (18 oktober 2026, 20:58): de vijf kaarten verborgen naar productie, los van de definitieve rechtencontrole. **Geen toestemming om ze zichtbaar of bestelbaar te maken.**

**Uitgevoerd:** gewone fast-forward (zonder force) van `claude/kerstkaarten-website-design-51mn9k` van 691ca1c naar 42e1dca, de eerder geteste commit. Web (`vaylide`) en taken (`vaylide-taken`) deployen van dezelfde branch.

**Echt gecontroleerd (Render-logboeken en alleen-lezen databasequery's, voor en na):**
- Web: deploy live, `/healthz` 200, geen foutmeldingen of waarschuwingen sinds de uitrol, "No migrations to apply". Taken: build geslaagd, run na de uitrol geslaagd.
- Productiedatabase: ontwerpen 58 → 63 (de vijf nieuwe), **actieve ontwerpen 49 → 49 met dezelfde lijst** (vergelijking via controlesom), de vijf nieuwe alle `is_active = false`, prijsregels 27 → 27 met dezelfde controlesom, pakketten en extra's gelijk, bestellingen 2 → 2 (laatste wijziging ongewijzigd), kortingscodes 1 → 1 met dezelfde controlesom.

**Niet gecontroleerd:** de publieke site (vaylide.nl) is vanuit de cloudomgeving niet bereikbaar; het 404-gedrag voor bezoekers en het ontbreken in zoeken en sitemap rusten dus op de tests en op `is_active = false`, niet op een live aanvraag. Eenmalig te controleren door de eigenaar of via een omgeving met toegang.

**Voorwaarden voor publieke vrijgave (nog open):**
1. Commerciële gebruiksrechten per film bevestigd (zie "Herkomst en Runway-voorwaarden"; de eigenaar wijst naar de Runway-pagina "Usage rights", die ik niet kon openen).
2. Controle op Safari/iOS en echte telefoons, inclusief de MP4 (H.264), die nergens is afgespeeld.
3. Bevestiging van Luxe als indeling door de eigenaar.
4. Nieuw, afzonderlijk akkoord voor activeren.

**Terugvalplan:** de vorige productiedeploy (691ca1c) weer live zetten via Render.

## Rechtenregistratie bijgewerkt: herkomstketen (18 oktober 2026, 21:17)

**Verklaring van de eigenaar** (bericht van 18 oktober 2026, 21:17, vervangt de eerdere, onvolledige verklaring van 20:50 en 20:58): de oorspronkelijke afbeeldingen van alle vijf kaarten zijn door ChatGPT gegenereerd; de eigenaar heeft ze daarna zelf met zijn eigen **Runway Pro-account** omgezet naar video's. Herkomstketen voor alle vijf: ChatGPT/OpenAI → eigen Runway Pro-account → Vaylide. Per film is dit dezelfde verklaring; een verschil per film is niet opgegeven.

| Kaart | Herkomstketen (verklaard door de eigenaar) | Herkomst aantoonbaar met bewijsstuk |
|---|---|---|
| Zijden gordijn | ChatGPT-afbeelding → Runway Pro → Vaylide | Nee, alleen verklaring |
| Bloesemmeer | idem | Nee, alleen verklaring |
| Bloesemwaaier | idem | Nee, alleen verklaring |
| Kerstsprookje | idem | Nee, alleen verklaring |
| Gouden poort | idem | Nee, alleen verklaring |

**Voorwaarden: wat ik heb kunnen nagaan.** De officiële pagina's van OpenAI en Runway zijn vanuit de cloudomgeving niet te openen (DNS-fout); ik heb ze dus niet zelf gelezen. Wat ik wel zag zijn zoekresultaten, deels als samenvatting van de officiële Runway-helppagina's en deels van secundaire bronnen:
- **Runway** (helppagina "Usage rights" en "Can I use the content I made in Runway for commercial purposes", zoals de zoekmachine ze samenvat): op elk plan (Free, Standard, Pro, Max, Unlimited) behoudt de gebruiker het eigendom en alle rechten op wat hij uploadt en genereert; de inhoud mag volgens die pagina's worden gebruikt zonder niet-commerciële beperkingen van Runway; vermelding van Runway is niet verplicht. Een Pro-plan valt daar dus onder.
- **OpenAI** (alleen secundaire bronnen, niet de eigen voorwaarden): "you own all Input and Output" en OpenAI draagt zijn rechten op de uitvoer over aan de gebruiker; commercieel gebruik van beelden is volgens die bronnen toegestaan, binnen het gebruiksbeleid. Eigendom is contractueel en geen garantie dat een beeld auteursrechtelijk beschermd is of vrij van rechten van derden.
- Beide partijen regelen alleen hun eigen deel: bij beeld naar video blijft de gebruiker zelf verantwoordelijk voor rechten op wat hij als invoer gebruikt. Dat is hier een eigen ChatGPT-beeld.

**Aanwijzingen voor extern bronmateriaal of afzonderlijke beperkingen.** Onderzocht in de code en de bestanden:
- Geen concrete aanwijzing gevonden: alle beelden op de kaarten (kop, uitsneden, galerij, eindbeeld) zijn stills uit de eigen films; er is geen stockfoto, geen geluidsspoor en geen extern adres in de kaarten; de gebruikte lettertypen zijn OFL op de eigen server (zie punt 14 in `docs/OVERDRACHT.md`).
- In drie stilstaande beelden per film (op miniatuurformaat) geen zichtbaar watermerk, logo of tekst. Dat is een steekproef, geen volledige beeldcontrole.
- De scènes zijn algemeen (gordijn met kasteel, bloesemmeer, waaier en pagode, kerststad, gouden poort met paleis). Er staan geen gezichten, merken of namen in. Het paleis van Gouden poort doet denken aan een bekend bouwwerk; dat is geen rechtenprobleem, maar wel een beeld dat de eigenaar kan willen nalopen.

**Onderscheid: aantoonbaar risico of ontbrekend bewijs**
- *Aantoonbaar risico (concrete aanwijzing, onverklaard):* de bronbestanden (de originele mp4's) dragen een AIGC-label met een `ContentProducer`-code die ik niet tot Runway of OpenAI kan herleiden (zie "Rechten per videobestand"). Het past niet vanzelf bij de herkomstketen. Het is geen bewijs van een beperking, maar het is wel een feit dat nog een verklaring nodig heeft (bijvoorbeeld een tussenstap via een andere dienst of een export). De bestanden op de website zijn opnieuw gecodeerd en dragen dit label niet meer.
- *Ontbrekende administratieve bewijsstukken:* (1) per film de generatie in het Runway-account (datum, plan Pro op dat moment, naam of prompt), (2) de ChatGPT-afbeelding waaruit de film is gemaakt, met datum, (3) een bewaarde kopie, met datum, van de Runway-pagina "Usage rights" en de OpenAI-voorwaarden zoals ze golden.

**Eindoordeel (alleen resterende blokkades voor publicatie)**
Volgens de voorwaarden zoals ik ze kon nagaan is commercieel gebruik van eigen Runway-generaties en ChatGPT-uitvoer in beginsel toegestaan, en de herkomstketen is door de eigenaar verklaard. De blokkade is daarmee **niet opgeheven**; wat resteert is dit:
1. Eén onverklaard feit: de `ContentProducer`-code in de bronbestanden (zie hierboven).
2. De bewijsstukken onder "ontbrekende administratieve bewijsstukken": zonder die stukken berust de herkomst op de verklaring alleen.
De tabel "Rechten per videobestand" blijft daarom op "Nee" staan; zij wordt bijgewerkt zodra de eigenaar de punten 1 en 2 aanlevert. Daarnaast blijven de technische en commerciële voorwaarden voor publieke vrijgave uit "Productie-uitrol met verborgen kaarten" gelden (Safari/iOS en telefoontest, bevestiging van Luxe, nieuw akkoord voor activeren). Dit is geen juridisch advies.

## Definitieve rechtenstatus (18 oktober 2026, 21:21)

Dit vervangt de eindoordelen van 20:50 en 21:17 waar die afwijken. Er is niets in code, ontwerpen of deployments veranderd.

**Officiële bronnen, door de eigenaar aangeleverd en door hem rechtstreeks laten controleren** (ik kon beide adressen vanuit de cloudomgeving niet openen en heb ze dus zelf niet gelezen; mijn eigen zoekresultaten gaven dezelfde strekking, zie hierboven):
- Runway, "Usage rights": https://help.runwayml.com/hc/en-us/articles/18927776141715-Usage-rights
- OpenAI, gebruiksvoorwaarden: https://openai.com/nl-NL/policies/terms-of-use/

**1. Algemene commerciële gebruiksrechten (volgens de voorwaarden):** door de eigenaar rechtstreeks gecontroleerd aan de officiële bronnen; commercieel gebruik van eigen uitvoer is in beginsel toegestaan. Niet door mij onafhankelijk gelezen. Geen juridisch advies.

**2. Herkomst, bevestigd door de eigenaar (18 oktober 2026, 21:21, herhaald):**
- De vijf oorspronkelijke afbeeldingen zijn met ChatGPT gegenereerd.
- De eigenaar maakte de vijf video's zelf via zijn eigen Runway Pro-account.
- Voor zover hem bekend is geen extern stockmateriaal gebruikt.
Mijn eigen controle van de bestanden en de code (zie "Rechtenregistratie bijgewerkt") vond geen aanwijzing voor stockmateriaal, geluid, extern adres of een zichtbaar watermerk (steekproef).

**3. Nog niet onafhankelijk geverifieerd:**
- De herkomstketen zelf: er is geen export of overzicht uit de accounts bijgevoegd.
- De generatiegegevens per film (datum, plan op dat moment, prompt of naam, bronafbeelding uit ChatGPT): **niet beschikbaar in het dossier**; hieronder geregistreerd als ontbrekend. Alleen de bestandsnamen van vier bronbestanden bevatten het begin van de prompt.
- De afwijkende AIGC-producentcode: **openstaand herkomstonderzoek**, niet beschouwd als bewijs dat commerciële rechten ontbreken. Alle vijf de bronbestanden dragen dezelfde `ContentProducer` en `ContentPropagator` (`001191330106MA2CFLDG4R10001`) en een eigen `ProduceID`. De opbouw van het label lijkt op de Chinese norm voor impliciete AI-labels (niet geverifieerd). Wie het label op het bestand zet, is niet vastgesteld. Een eenvoudige manier om dit later af te sluiten, zonder dat het nu nodig is: een van de generaties opnieuw uit het Runway-account downloaden en kijken of dat bestand hetzelfde label draagt.

**Originele bestanden bewaard** (ongewijzigd in de gedeelde projectmap `/mnt/project-files/`; de bestanden op de website zijn opnieuw gecodeerd en dragen het label niet):

| Kaart | Bronbestand | Grootte (bytes) | SHA-256 |
|---|---|---|---|
| Zijden gordijn | `uploads/hearth/17f76c22-da85-44c6-8dcb-6fa212ad4acc` | 28177231 | `1123cc42cc134bf2fd2dbfc16e4cfa16b91f14d42cce7157f5dde8d385078278` |
| Bloesemmeer | `One_continuous_cinematic_vertical_10_second_nature_reveal__absolutely_no_architecture_or_wedding_dec.mp4` (er staat een identieke kopie met " 2" in de naam naast) | 29120096 | `3c6c7a95f4a8df32f4d1ed79a0d1d51314522e948cef18b6f757609486a3284e` |
| Bloesemwaaier | `Premium_cinematic_vertical_wedding_reveal__one_uninterrupted_locked_off_shot__Start_exactly_with_the.mp4` (ook als `uploads/hearth/c3f63281-e0b5-4f57-9b14-6687a2880e24`) | 25051384 | `8090250b44d87c890bc73fd0baf43a0a93fe165cd42c406af3f3e5696139a621` |
| Kerstsprookje | `Premium_magical_Christmas_cinematic_vertical_10_second_reveal__At_first_the_ENTIRE_portrait_frame_is.mp4` | 36971633 | `18fa37066579aad87892578c7964432c69c88fcbb7664c8b530bbe8aff7709c0` |
| Gouden poort | `uploads/hearth/d81b1a19-cfc5-4870-b3b4-1498f550588a` | 26081875 | `821993e4ddcd27c18507da4b1114e498f17639b5df17a29872b215a59fbd1071` |

**Aanvullend bewijs:** op verzoek van de eigenaar nu niet gevraagd; er is geen concreet, relevant risico dat dat nodig maakt. De bewaarde generatiegegevens blijven wel een open gat in het dossier.

**Resterende blokkades voor publicatie, na deze status:** de openstaande vraag naar de producentcode is een onderzoekspunt; of dat nog een blokkade is, beslist de eigenaar. Verder gelden alleen de eerder vastgelegde technische en commerciële voorwaarden (Safari/iOS en telefoontest inclusief de MP4, bevestiging van Luxe, nieuw akkoord om te activeren). De tabel "Rechten per videobestand" blijft daarom nog op "Nee" tot de eigenaar de rechtenstatus als voldoende aanvaardt; dit is zijn besluit, niet een bevinding over ontbrekende rechten.

## Laatste technische vrijgavecontrole (18 oktober 2026, 21:40)

Uitgevoerd op verzoek van de eigenaar (18 oktober 2026, 21:33), na zijn goedkeuring van de rechtenregistratie (de afwijkende `ContentProducer`-code blijft een administratief aandachtspunt en is op zichzelf geen blokkade) en zijn voorkeur om alle vijf onder de bestaande indeling **Luxe** te houden, zonder prijswijzigingen. Geen code, ontwerpen of deployments gewijzigd; de kaarten blijven verborgen en niet bestelbaar tot een afzonderlijk akkoord.

**Echt uitgevoerd (lokale testserver met de kaarten daar zichtbaar gezet, Chromium met Playwright):**
- Film, alle vijf, 390 × 844 (touch), 1366 × 768 en met een traag netwerk (1,6 Mbps, 150 ms): de film start 0,24 tot 0,29 seconde na de tik, speelt de volle 10 seconden, de uitnodiging opent daarna, geen scriptfouten, geen horizontale overloop.
- Terugval, alle vijf: bij geblokkeerde videobestanden en bij een geweigerde `play()` opent de uitnodiging na ongeveer 1,1 seconde (de kaart met stilstaand beeld), zonder fouten. Met 'minder beweging' opent de kaart direct zonder film.
- Link Aanmelden, alle vijf, op 390 en 1366: zichtbaar na de film, raakbaar, bereikbaar met het toetsenbord, wijst naar `#aanmelden` en brengt het formulier in beeld; ook aanwezig met 'minder beweging'; de pagina is na de film niet meer inert.
- Pauzeknop en effecten, alle vijf, op 390 en 1366: de effectlaag tekent deeltjes (zichtbare pixels op het canvas), de pauzeknop zet de beweging stil (`fx-motion` uit, laag verborgen) en een tweede tik hervat; geen scriptfouten.
- Beschermde productie, alleen-lezen databasequery's op de productiedatabase na de uitrol: 63 ontwerpen, actieve ontwerpen 49 met dezelfde lijst (controlesom gelijk aan die van vóór de uitrol), alle vijf inactief, 27 prijsregels met dezelfde controlesom, pakketten, extra's en kortingscodes gelijk, 2 bestellingen met dezelfde laatste wijziging; geen fouten of waarschuwingen in de productielogboeken sinds de uitrol. Tests: 71 tests voor de kaarten, de collectie en de prijsstructuur geslaagd (404 voor bezoekers, niet in collectie, zoeken en sitemap, niet te kiezen in de bestelroute, prijzen ongewijzigd). De volledige suite (1391 tests) slaagde eerder, op de twee bekende falers door de lokale `.env` na.
- MP4 (H.264) statisch gecontroleerd met `ffprobe` en een controle van de bestandsopbouw, alle vijf: High-profiel niveau 3.1 (`avc1.64001F`, gelijk aan de `type`-aanduiding in de pagina), `yuv420p`, 720 × 1280, 30 beelden per seconde, 1,1 tot 1,6 Mbps, geen geluidsspoor, `moov` vóór `mdat` (begint te spelen zonder eerst alles te laden). De pagina zet de film op `muted` en `playsinline` en start hem na een tik.

**Niet uitgevoerd, en dus niet bevestigd:**
- iPhone Safari: er is geen echte iPhone en geen WebKit in de testomgeving (alleen Chromium). De MP4 is in geen enkele browser daadwerkelijk afgespeeld (de testbrowser heeft geen H.264; de film is met de WebM-versie getest). De H.264-gegevens hierboven zijn een bestandscontrole, geen afspeeltest, en een Chromium-test is niet gelijk aan een echte iPhone.
- Firefox, Android Chrome op echte toestellen, Low Power Mode op iOS.
- De publieke site (vaylide.nl) en de stagingsite zijn vanuit de cloudomgeving niet bereikbaar.

**Restrisico:** de MP4 op een echte iPhone, plus het gedrag van de tik-start onder Low Power Mode. Gevolgen zijn beperkt: de terugval is getest (zonder film opent de uitnodiging binnen ongeveer 1,1 seconde met het stilstaande beeld) en activeren is omkeerbaar in Beheer → Ontwerpen. Een echte controle is pas mogelijk als de kaarten zichtbaar zijn of met een tijdelijk beheeraccount (dat de eigenaar niet wil).

**Advies:** GO voor publieke activatie, onder de voorwaarde dat de eigenaar het restrisico aanvaardt en na het activeren direct de film op een eigen iPhone en Android controleert; bij een probleem zet hij het ontwerp in Beheer weer uit. Afzonderlijk akkoord van de eigenaar blijft nodig; er is niets zichtbaar of bestelbaar gemaakt.
