"""Vaste teksten van de commerciële website (op één plek aan te passen).

Let op: geen verzonnen reviews, klantenaantallen of beloftes over levertijden.
"""

# Homepage: vier stappen met icoon (icoonnamen uit core/icons.py).
STEPS_SHORT = [
    ("kaarten", "Kies een ontwerp", "Uit onze collectie, voor elke gelegenheid."),
    ("potlood", "Vul je gegevens in", "Tekst, foto's, datum en extra opties."),
    ("oog", "Bekijk en pas aan", "Zie direct een voorbeeld van jouw uitnodiging."),
    ("versturen", "Delen maar", "Na je betaling een eigen link en QR-code."),
]

HERO_CHECKS = ["Snel en eenvoudig", "Stijlvolle ontwerpen", "Automatisch online", "RSVP & gastenlijst"]

# Homepage: drie uitgelichte ontwerpen (codes), de kerstkaart eerst. Alleen lichte ontwerpen: geen donkere of zwarte
# voorbeeldkaarten op de homepage. Ontbreekt er een, dan vullen de eerste uit de collectie aan.
HOME_DESIGNS = ["winterlicht", "liefde-op-papier", "confetti"]

# Homepage, kerstpodium: lichte kerstontwerpen die in 3D zweven (kaartbeelden uit static/img/designs/).
HOME_KERST = ["winterlicht", "gloria", "golden-noel", "kerstbol", "kerstkaart"]    # Ho ho ho en Sneeuwpret zijn C (catalog/collectie.py) en staan voorlopig niet in de collectie

# Donker paneel op de homepage: onderdelen die elke uitnodiging kan hebben.
HOME_FEATURES = [
    ("wekker", "Afteller"),
    ("locatie", "Locatie"),
    ("gasten", "Gastenlijst"),
    ("programma", "Programma"),
    ("fotos", "Foto's"),
    ("kleuren", "Kleurkeuze"),
]

# Tegels per gelegenheid; het beeld is een weergave van een echt (licht) voorbeeld. Kerst staat voorop.
OCCASION_TILES = [
    ("kerst", "Kerst"),
    ("bruiloft", "Bruiloft"),
    ("verloving", "Verloving"),
    ("verjaardag", "Verjaardag"),
    ("jubileum", "Jubileum"),
    ("babyshower", "Babyshower"),
    ("zakelijk", "Zakelijk"),
]
# Korte uitleg bij een tegel (nu alleen Kerst; op de homepage staat die in het kerstpodium).
OCCASION_TILE_NOTES = {
    "kerst": "Een warme digitale kerstkaart, als uitnodiging voor het kerstdiner of als wenskaart.",
}

# Zo werkt het: zes stappen (icoonnamen uit core/icons.py).
STEPS = [
    ("kaarten", "Kies een ontwerp", "Probeer het werkende voorbeeld op je eigen telefoon."),
    ("potlood", "Vul je gegevens in", "Alleen de vragen die bij jouw gelegenheid horen."),
    ("fotos", "Voeg foto's toe", "Je kiest zelf welk deel in beeld komt."),
    ("oog", "Bekijk je voorbeeld", "Op telefoon en computer; pas aan wat je wilt."),
    ("tas", "Betaal online", "Na een bevestigde betaling wordt je uitnodiging automatisch gepubliceerd."),
    ("delen", "Deel en volg aanmeldingen", "Via link of QR-code. Antwoorden zie je in Mijn VAYLIDE."),
]

FEATURES = [
    ("envelop", "Openingsanimatie", "Envelop, gouden deur of doorschijnend vel. Openen met één tik."),
    ("wekker", "Afteller", "In de juiste tijdzone."),
    ("programma", "Programma", "Van ontvangst tot feest op een tijdlijn."),
    ("locatie", "Locatie en route", "Met een knop naar de kaart."),
    ("gasten", "Aanmelden zonder account", "Aanwezig en met hoeveel personen. Extra vragen uit een vaste lijst met Compleet of als extra optie."),
    ("agenda", "In de agenda", "Google, Apple en Outlook."),
    ("delen", "Delen", "Via WhatsApp, een link of een QR-code."),
    ("muziek", "Muziek", "Start pas als de gast erop tikt."),
    ("slot", "Privé", "Niet vindbaar in zoekmachines. Alleen jij ziet de gastenlijst."),
]

# 'Wat je gasten krijgen' (Zo werkt het) in drie rustige groepen; de onderdelen komen uit FEATURES (op icoon).
FEATURE_GROUPS = [
    ("Openen en beleven", "Wat je gasten zien als ze de link openen.", ["envelop", "muziek", "wekker"]),
    ("Alles bij de hand", "De praktische informatie op één plek.", ["programma", "locatie", "agenda"]),
    ("Reageren en delen", "Eenvoudig voor je gasten, overzichtelijk voor jou.", ["gasten", "delen", "slot"]),
]

FAQ = [
    ("Hoe werkt een digitale uitnodiging van VAYLIDE?",
     "Je kiest een ontwerp, vult de gegevens van je evenement in en bekijkt meteen een persoonlijk voorbeeld. "
     "Na de betaling wordt je uitnodiging automatisch gepubliceerd op een eigen link. Die deel je via WhatsApp, e-mail of met een QR-code."),
    ("Heb ik een account nodig?",
     "Je kunt direct beginnen zonder account. Om je ontwerp te bewaren en te bestellen bevestig je je e-mailadres met een code. "
     "Daarmee log je later weer in, ook op een ander apparaat. Een wachtwoord is niet nodig."),
    ("Moeten mijn gasten een account aanmaken?",
     "Nee. Gasten openen de link en geven aan of ze komen, eventueel met hoeveel personen. Ze kunnen hun antwoord later zelf wijzigen."),
    ("Kan ik na het publiceren nog iets aanpassen?",
     "Ja. Je wijzigt de gegevens in Mijn VAYLIDE, bekijkt een voorbeeld en publiceert opnieuw. De link en de QR-code blijven hetzelfde."),
    ("Wie kan de aanmeldingen zien?",
     "Alleen jij, in Mijn VAYLIDE. Gasten zien elkaars antwoorden niet. Je kunt de gastenlijst exporteren naar een bestand voor Excel of Numbers."),
    ("Wordt mijn uitnodiging gevonden via Google?",
     "Nee. Uitnodigingen zijn alleen bereikbaar via de link en we vragen zoekmachines om ze niet op te nemen."),
    ("Kan ik muziek toevoegen?",
     "Ja, met het pakket Compleet of als extra optie. De muziek start pas als een gast er zelf op tikt. "
     "Gebruik alleen muziek waarvoor je toestemming hebt."),
    ("Welke foto's kan ik gebruiken?",
     "JPG, PNG of WebP tot 12 MB per foto. Je kiest zelf welk deel van de foto in beeld komt. "
     "Locatiegegevens en andere verborgen informatie in foto's halen we automatisch weg."),
    ("Hoe betaal ik?",
     "Je betaalt online bij het afronden van je bestelling. Welke betaalmethoden beschikbaar zijn, zoals iDEAL, zie je bij het afrekenen."),
    ("Wanneer staat mijn uitnodiging online?",
     "Zodra de betaalprovider je betaling heeft bevestigd, wordt je uitnodiging automatisch gepubliceerd. "
     "Je ziet de link direct in Mijn VAYLIDE en ontvangt hem ook per e-mail."),
    ("Hoe lang blijft mijn uitnodiging online?",
     "Essentieel 6 maanden en Compleet 12 maanden, gerekend vanaf de aankoopdatum: de dag waarop je betaling is bevestigd. "
     "Later publiceren of je evenement verplaatsen verschuift die einddatum niet. De einddatum staat in je bestelbevestiging en "
     "bij je uitnodiging in Mijn VAYLIDE. Er is geen automatische verlenging; langer online is als extra optie mogelijk."),
    ("Ik heb een bijzondere wens. Kan dat?",
     "Gebruik 'Extra wensen of hulp nodig?' tijdens het samenstellen of in Mijn VAYLIDE. We bekijken je vraag persoonlijk. "
     "Kost het iets extra, dan krijg je eerst een voorstel; we beginnen pas na jouw akkoord."),
    ("Wat gebeurt er met de gegevens na afloop?",
     "Na de beschikbaarheidsperiode gaat de uitnodiging offline en worden de gastgegevens na een vaste termijn verwijderd. "
     "Je kunt je uitnodiging, de aanmeldingen en je account ook zelf eerder verwijderen."),
]

# Homepage: een korte selectie veelgestelde vragen (vragen uit FAQ, plus één over delen). Alleen functies die er zijn.
HOME_FAQ_QUESTIONS = [
    "Hoe werkt een digitale uitnodiging van VAYLIDE?",
    "Kan ik na het publiceren nog iets aanpassen?",
    "Hoe betaal ik?",
    "Wanneer staat mijn uitnodiging online?",
    "Moeten mijn gasten een account aanmaken?",
    "Wie kan de aanmeldingen zien?",
]
HOME_FAQ_EXTRA = [
    ("Hoe deel ik mijn uitnodiging met gasten?",
     "Na de betaling krijg je een eigen link en een QR-code. Die deel je via WhatsApp of e-mail, of je zet de QR-code "
     "op een kaartje. Gasten openen de uitnodiging in hun browser, zonder app."),
]

# Inspiratie: voorbeeldteksten om over te nemen (geen echte klanten of reviews).
TEXT_SAMPLES = [
    ("bruiloft", "Bruiloft", "Wij gaan trouwen! We zouden het heel bijzonder vinden om deze dag met jou te vieren."),
    ("verloving", "Verloving", "Ze zei ja! Dat willen we graag samen met jou vieren, met een glas en goed eten."),
    ("verjaardag", "Verjaardag", "Dertig wordt gevierd met muziek, bubbels en de mensen die ertoe doen. Kom je ook?"),
    ("jubileum", "Jubileum", "Veertig jaar samen: dat vieren we graag met familie, vrienden en buren."),
    ("babyshower", "Babyshower", "Er is iets kleins op komst! Vier het met ons met taart, thee en spelletjes."),
    ("zakelijk", "Zakelijk", "Graag nodigen wij u uit om samen met ons team dit bijzondere moment te vieren."),
    ("kerst", "Kerst", "Wat een jaar was het! We vieren kerst graag met de mensen die ons het dierbaarst zijn. Schuif je aan bij ons kerstdiner?"),
]

TIPS = [
    ("agenda", "Kies een aanmelddatum", "Een paar weken voor de dag. Dan weet je op tijd met hoeveel gasten je rekent."),
    ("programma", "Zet het programma erin", "Gasten zien meteen wanneer de ceremonie, het diner of het feest begint."),
    ("gasten", "Extra vragen", "Kies uit vaste vragen, bijvoorbeeld over vervoer of overnachten. Met Compleet of als extra optie."),
    ("kleuren", "Geef een dresscode mee", "Met een paar kleuren erbij weten gasten precies wat je bedoelt."),
    ("fotos", "Kies rustige foto's", "Je bepaalt zelf welk deel in beeld komt, zodat tekst goed leesbaar blijft."),
    ("delen", "Deel op jouw manier", "Stuur de link via WhatsApp of e-mail, of zet de QR-code op een kaart."),
]

# Over ons: aanvulling op de tekst van de eigenaar. Alleen wat Vaylide echt doet; geen duurzaamheidsclaims.
ABOUT_POINTS = [
    ("wekker", "Snel beschikbaar",
     "Geen wachttijd voor drukwerk of bezorging. Zodra je betaling is bevestigd, staat je uitnodiging online en kun je hem direct delen."),
    ("potlood", "Eenvoudig te maken",
     "Je stelt je uitnodiging zelf samen, in je eigen tempo en met een voorbeeld dat meteen meekijkt. Je gasten hebben geen account of app nodig."),
    ("kaarten", "Voor particulieren en bedrijven",
     "Van bruiloft, verjaardag of kerstdiner tot relatiedag, jubileum of personeelsfeest. Bij zakelijke evenementen spreekt de uitnodiging je gasten aan met 'u'."),
    ("envelop", "Digitaal in plaats van extra drukwerk",
     "Een wijziging publiceer je op dezelfde link, en programma, route en aanmelden staan bij elkaar. Wil je toch iets op papier, dan print je de QR-code op een kaartje."),
]

# Over ons: waar Vaylide op let.
VALUES = [
    ("hart", "Persoonlijk", "Je uitnodiging vertelt jullie verhaal, met eigen tekst, foto's en programma."),
    ("potlood", "Eenvoudig", "Je maakt hem zelf, in je eigen tempo. Gasten hebben geen account nodig."),
    ("slot", "Privé", "Niet vindbaar in zoekmachines. Alleen jij ziet de aanmeldingen."),
    ("vink", "Duidelijk geprijsd", "Eén keer betalen, geen kosten per gast. Bijzondere wensen alleen na jouw akkoord."),
]


# SEO-landingspagina /digitale-trouwkaarten/ (core/templates/core/trouwkaarten.html). Alleen ontwerpen die er zijn en bij de bruiloft horen
# (ontbrekende worden overgeslagen). Het kopbeeld toont drie echte kaartbeelden; daaronder staat de keuze.
TROUW_KOP = ["balzaal", "strandboog", "midnight-emeraude"]
TROUW_UITGELICHT = ["gouden-avond", "rose-royale", "aurora-nocturne", "eerste-dans", "voor-altijd", "liefde-op-papier", "rozentuin", "eucalyptus"]

TROUW_VOORDELEN = [
    ("envelop", "Een opening die indruk maakt",
     "Je gasten tikken op het zegel, de envelop of de deuren gaan open en jullie kaart verschijnt. Het voelt als echte post, maar dan met beweging."),
    ("gasten", "Aanmeldingen op één plek",
     "Gasten geven met één tik door of ze komen en met hoeveel personen, zonder account. Jij ziet de lijst in Mijn VAYLIDE en exporteert hem voor Excel of Numbers."),
    ("potlood", "Wijzigen zonder opnieuw te versturen",
     "Verandert de tijd of de locatie? Pas de kaart aan en publiceer opnieuw. De link en de QR-code blijven hetzelfde, dus niemand hoeft iets nieuws te ontvangen."),
]

TROUW_FAQ = [
    ("Wat is een digitale trouwkaart?",
     "Een trouwkaart die je gasten als link openen op hun telefoon of computer, in plaats van een kaart in de brievenbus. "
     "Bij VAYLIDE heeft elke kaart een eigen opening, zoals een envelop met lakzegel, en staan datum, programma, route en aanmelden op één plek."),
    ("Kunnen gasten zich aanmelden zonder account?",
     "Ja. Gasten openen de link en geven aan of ze komen, eventueel met hoeveel personen. Ze hoeven geen account aan te maken en kunnen hun antwoord later zelf wijzigen."),
    ("Hoe deel ik de trouwkaart met mijn gasten?",
     "Na je betaling krijg je een eigen link en een QR-code. Die deel je via WhatsApp of e-mail, of je zet de QR-code op een kaartje. "
     "Gasten openen de kaart in hun browser, zonder app."),
    ("Kan ik de kaart nog aanpassen als hij al gedeeld is?",
     "Ja. Je wijzigt de gegevens in Mijn VAYLIDE, bekijkt een voorbeeld en publiceert opnieuw. De link en de QR-code blijven hetzelfde."),
    ("Wat kost een digitale trouwkaart?",
     "Je betaalt eenmalig, zonder kosten per gast. Essentieel kost {essentieel} en Compleet {compleet}. "
     "Specials hebben een eigen meerprijs, die je vóór het afrekenen ziet. Ontwerpen en bekijken is gratis; je betaalt pas bij het publiceren."),
    ("Hoe lang blijft de trouwkaart online?",
     "Essentieel 6 maanden en Compleet 12 maanden, gerekend vanaf de aankoopdatum: de dag waarop je betaling is bevestigd. "
     "Langer online is als extra optie mogelijk; er is geen automatische verlenging."),
    ("Kan ik foto's en muziek toevoegen?",
     "Ja, met het pakket Compleet of als extra optie: een fotogalerij met maximaal 12 foto's en eigen muziek. "
     "De muziek start pas als een gast er zelf op tikt."),
    ("Is mijn trouwkaart te vinden via Google?",
     "Nee. Een trouwkaart is alleen bereikbaar via de link en we vragen zoekmachines om hem niet op te nemen. Alleen jij ziet de gastenlijst."),
]


# SEO-landingspagina /digitale-kerstkaarten/ (core/templates/core/kerstkaarten.html). Warme, lichte kaarten voorop; alleen ontwerpen die er zijn
# (ontbrekende worden overgeslagen). De openingen en effecten komen uit de manifesten van de ontwerpen.
KERST_KOP = ["golden-noel", "gloria", "kerstbol", "winterlicht", "middernacht"]
KERST_ONTWERPEN = ["kerstbol", "golden-noel", "gloria", "winterlicht", "middernacht", "aan-tafel", "kerststad", "kerstkaart"]
KERST_FAMILIE = "winterlicht"
KERST_ZAKELIJK = ["middernacht", "gloria"]

KERST_BELEVING = [
    ("envelop", "Een bijzondere opening",
     "Je ontvanger tikt en de kaart gaat open: een envelop met lakzegel, engelenvleugels, een glazen kerstbal of een gesloten cadeau met sneeuwbol."),
    ("kleuren", "Beweging en sfeer",
     "Sneeuw, goudstof, kaarslicht en fonkelende sterren. De kaart beweegt zacht mee, zonder dat het druk wordt."),
    ("muziek", "Een geluid dat erbij hoort",
     "Kerststad heeft een eigen muziekje, een uitnodiging kan eigen muziek krijgen. Het geluid start nooit vanzelf: pas als de ontvanger erop tikt."),
]

KERST_DELEN = [
    ("chat", "Via WhatsApp", "Plak de link in een gesprek of groep. Ontvangers openen de kaart in hun browser."),
    ("link", "Als link", "Na je betaling krijg je een eigen link. Stuur hem per e-mail of sms, of zet hem in een nieuwsbrief of intranetbericht."),
    ("qr", "Met een QR-code", "Ook een QR-code is inbegrepen: handig op een kaartje bij een cadeau, op een scherm of in een brief."),
]

KERST_FAQ = [
    ("Wat is een digitale kerstkaart?",
     "Een kerstkaart die je niet per post verstuurt maar als link deelt. De ontvanger opent hem op telefoon of computer en ziet jullie kaart met een eigen opening, "
     "beweging en sfeer, bijvoorbeeld een envelop met lakzegel, engelenvleugels of een glazen kerstbal."),
    ("Hoe verstuur je een digitale kerstkaart?",
     "Na je betaling krijg je een eigen link en een QR-code. Die deel je zelf: via WhatsApp, e-mail of sms, of je zet de QR-code op een kaartje of in een brief. "
     "VAYLIDE verstuurt de kaart dus niet voor je; jij bepaalt wie hem krijgt."),
    ("Kan ik een kerstkaart via WhatsApp versturen?",
     "Ja. Plak de link in een gesprek of groep. Ontvangers tikken erop en de kaart opent in hun browser, zonder app."),
    ("Kan ik mijn eigen tekst en foto's toevoegen?",
     "Ja. Je vult zelf de afzender en je boodschap in en voegt eventueel een foto toe, en je ziet direct het voorbeeld. "
     "Bij een kerstuitnodiging met Compleet komt daar een fotogalerij van maximaal 12 foto's bij."),
    ("Kunnen bedrijven VAYLIDE gebruiken voor een zakelijke kerstgroet?",
     "Ja. Als afzender vul je een bedrijfsnaam of teamnaam in en je deelt dezelfde link met klanten, medewerkers of relaties. "
     "Wil je je eigen logo of huisstijl in de kaart, dan kan dat op aanvraag: je krijgt eerst een voorstel met prijs."),
    ("Hebben ontvangers een app nodig?",
     "Nee. Ontvangers openen de link in hun browser. Ze hoeven geen app te installeren en geen account aan te maken."),
    ("Kan ik de kerstkaart eerst bekijken?",
     "Ja. Ontwerpen en bekijken is gratis: van elk ontwerp staat een werkend voorbeeld online en in de Studio zie je direct jouw kaart. Je betaalt pas bij het publiceren."),
    ("Wat kost een digitale kerstkaart?",
     "Een kerstwenskaart, alleen een groet, kost {wens} en {wens_special} in een Special-ontwerp, beide inclusief btw en eenmalig. "
     "Wil je ook een datum, programma, locatie en aanmelden, bijvoorbeeld voor een kerstdiner of kerstborrel, dan kies je Essentieel ({essentieel}) of Compleet ({compleet})."),
    ("Kan er muziek bij een digitale kerstkaart?",
     "Kerststad heeft een eigen muziekje. Bij een kerstuitnodiging kun je eigen muziek toevoegen met Compleet of als extra optie. "
     "De muziek start nooit vanzelf: pas als de ontvanger erop tikt. Een wenskaart heeft geen muziek."),
]

