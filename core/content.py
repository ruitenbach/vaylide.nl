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
HOME_KERST = ["winterlicht", "gloria", "kerstman", "sneeuwpop"]

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
