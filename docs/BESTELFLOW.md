# De bestelroute in vier stappen

Stand: 8 oktober 2026, branch `claude/flow-vereenvoudiging` (vanaf `1383190`, de stand op production). Nog niet op staging of production.

De klant ziet vier fasen: **1 Kies kaart → 2 Personaliseer → 3 Controleer → 4 Bestel**. Code: `studio/steps.py` (fasen, onderdelen,
volgorde), `studio/views.py`, `studio/templates/studio/`, `static/js/studio.js`.

## Kies kaart

- Elke kaart op `/maken/` is een verzendknop (`name="template"`): een tik bewaart de keuze, maakt het concept en brengt de klant direct naar
  Personaliseren (Gegevens). Geen keuzerondjes, geen knop onderaan en geen pakketkeuze meer; het pakket kies je bij Bestel
  (een meegegeven `pakket` bij het starten blijft werken).
- Komt de klant van een ontwerppagina (`/ontwerpen/<naam>/`, voorbeeld) via "Kies dit ontwerp" of "Maak jouw uitnodiging", dan staat in de
  link `direct=1`: de pagina toont "Gekozen ontwerp ✓" en start de kaart meteen (één keer per tabblad, zodat 'terug' geen lus wordt). Zonder
  JavaScript staat er één knop "Verder met personaliseren". De rest van de collectie zit achter "Wijzigen".
- Gelegenheid en soort (uitnodiging of wenskaart) zijn chips boven de kaarten. Een wenskaart toont zijn prijs in de keuze.
- "Wijzigen" in Personaliseren (`/maken/<id>/ontwerp/?terug=<onderdeel>`) kiest een ander ontwerp met dezelfde tik; de invoer blijft bewaard en
  de klant komt terug waar hij was. Gegevens blijven ook als de gelegenheid wisselt.

## Personaliseer

Onderdelen in een balk boven het formulier: Gegevens, Praktische info, Aanmelden, Foto's & verhaal, Envelop & zegel (alleen bij een ontwerp met die
keuze) en Stijl. Een wenskaart slaat Aanmelden en Envelop over en heeft Afsluiting, Foto en Stijl.

- **Niets is verplicht.** Een leeg veld laat het onderdeel van de kaart weg; ontbrekende gegevens zijn een tip bij Controleer, geen blokkade
  (`publish_issues` in `invitations/content.py`). Alleen tegenstrijdige gegevens blokkeren nog: een datum in het verleden en een
  aanmelddeadline na het evenement.
- **Wisselen bewaart.** Een klik op een onderdeel in de balk, op een fase in de voortgang of op Wijzigen stuurt eerst het formulier mee
  (`actie=ga`, `naar=<stap>`), bewaart en gaat daarna naar de gekozen stap. Zonder wijzigingen is het een gewone link. Fouten in een veld
  houden de klant op de pagina.
- **Knoppen** (`_actions.html`): "Volgende: <onderdeel>" (bij het laatste onderdeel "Verder naar controle"), "Bekijk mijn kaart" (direct naar
  Controleer) en "Opslaan". Op een telefoon staan ze vast onderaan in beeld.
- **Praktische info** is één onderdeel: programma, dresscode, tips voor gasten, contactpersoon en afsluiting als opvouwbare blokken (ingevuld =
  open). De schakelaars voor die onderdelen bij Stijl zijn weg: ingevuld = zichtbaar, leeg = verborgen (`ProgramForm.apply` zet de schakelaar
  aan, ook bij oudere concepten). Bij Stijl blijven afteller, verhaal, galerij en muziek.
- **Aanmelden:** bij een **bruiloft** bestaat de aanmelddeadline ("Aanmelden kan tot en met") niet meer; bij andere gelegenheden is hij optioneel.
  Het aantal personen per aanmelding (standaard 2, leeg = 2) bepaalt of gasten "Met hoeveel personen kom je?" zien.
- **Live kaart** blijft naast het formulier (breed scherm) of achter "Bekijk je kaart" (telefoon) en toont wat je typt, nog vóór het opslaan.

## Controleer en Bestel

Controleer toont de kaart (telefoon of computer), de tips en "Iets aanpassen?" als chips; de vervolgknop "Verder naar bestellen" blijft op een
telefoon onderaan in beeld. Bestel is ongewijzigd (pakket, extra's, voorwaarden, betalen) met kortere teksten; de juridische teksten uit
`core/voorwaarden.py` zijn niet aangepast.

## Aanmelden met aantal personen (gast → maker)

De gast kiest "Met hoeveel personen kom je?" (1 tot het ingestelde maximum, alleen als het maximum boven 1 ligt). Het aantal staat op de
aanmelding (`GuestResponse.party_size`), de bevestiging noemt het ("Aangemeld met 3 personen."), en de maker ziet het in Mijn VAYLIDE (samenvatting
"Aanwezig · 3 personen", gastenoverzicht met kolom Personen en het totaal, csv "Aantal personen"). Een afwezige gast telt 0. Tests:
`tests/test_rsvp_personen.py`, `e2e/rsvp_personen.cjs`.

## Nieuwste ontwerpen eerst

Eén regel voor alle plekken waar ontwerpen staan: **Specials eerst, daarna de gewone ontwerpen, overal het nieuwst toegevoegde ontwerp links of
bovenaan.** Eén functie: `catalog/occasions.py: collectie_volgorde`, gebruikt door de Collectie, Inspiratie (Specials en de 6 nieuwste ontwerpen,
boven de teksten), de ontwerpkeuze in de Studio en 'Meer voor…' op de ontwerppagina. Alleen actieve ontwerpen met een versie worden getoond.

"Nieuwst" komt uit de code, niet uit de database: elk manifest heeft een vaste `added_at` (ISO-tijd met tijdzone, bijv. `2026-10-07T07:59:37Z`),
gelezen door `catalog/collectie.py: toegevoegd()`. `Template.created_at` (de registratietijd in een specifieke database) doet niet mee; staging,
production en een nieuwe database geven dus dezelfde volgorde, ook na `sync_designs` of een nieuwe deploy. Bij gelijke tijd beslist `sort_order`.
**Een nieuw ontwerp krijgt in zijn manifest een `added_at` met de tijd van toevoegen**; `tests/test_flow_eenvoudig.py` (`VasteToevoegdatumTests`) laat
de tests falen als die ontbreekt. De waarden van de bestaande ontwerpen komen uit de git-geschiedenis (de commit waarin het ontwerp is toegevoegd).
Gevolg: de A/B-indeling uit `catalog/collectie.py` bepaalt de volgorde alleen nog voor ontwerpen die op hetzelfde moment zijn toegevoegd.

## Controles

- `tests/test_flow_eenvoudig.py`, `tests/test_rsvp_personen.py` en de bijgewerkte tests (optionele velden, nieuwe stappen).
- `e2e/flow_eenvoudig.cjs` (Chromium, WebKit en Firefox, 390 en 1366 px): zeven gelegenheden kaart → personaliseren, velden overslaan,
  wisselen, later invullen, ander ontwerp, live kaart, bestellen bereikbaar (niet betalen).
- `e2e/rsvp_personen.cjs` met `e2e/rsvp_setup.py`: aanmelden als gast met 3 personen en het overzicht van de maker.
