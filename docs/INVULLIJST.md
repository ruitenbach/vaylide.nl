# Invullijst vóór de livegang (29 september 2026)

Alleen feiten en keuzes die de eigenaar moet aanleveren. Er zijn geen bedrijfsgegevens verzonnen; waar ze
ontbreken staat dat hieronder. Juridische teksten die beoordeeld moeten worden staan onder "Juridisch
beoordelen" (⚖).

## Bedrijfsgegevens (nu nergens op de site)

- [ ] Handelsnaam en rechtsvorm (eenmanszaak, vof, bv …)
- [ ] KvK-nummer
- [ ] Vestigingsadres (of een correspondentieadres, als dat mag)
- [ ] Btw-identificatienummer, of: valt het bedrijf onder de kleineondernemersregeling (KOR)?
- [ ] E-mailadres voor klanten op het eigen domein (nu `VIERLIEF_CONTACT_EMAIL` in Render) en voor meldingen (`VIERLIEF_OWNER_EMAIL`)
- [ ] Telefoonnummer (⚖ laten beoordelen of dit verplicht op de site moet)
- Waar het komt: voettekst of contactpagina, privacyverklaring ("Wie zijn wij") en voorwaarden.

## Prijzen en betalen

- [ ] Bevestig de prijzen: Essentieel € 39 (6 maanden online), Compleet € 69 (12 maanden online), extra opties
      € 6–12 (zie Beheer → Prijzen). Er zijn geen prijzen gewijzigd.
- [ ] "Alle prijzen zijn inclusief btw" (prijzenpagina): klopt dit? Bij de KOR wordt er geen btw gerekend.
- [ ] Zet in Beheer → Instellingen "Voorlopige prijzen" uit zodra de prijzen definitief zijn.
- [ ] Facturen: de site maakt geen btw-facturen; de bevestigingsmail is geen factuur. Hoe factureer je?
- [ ] Terugbetalen: bij een dubbele betaling of een afwijkend bedrag zet de site de bestelling op
      "aandacht nodig" (Beheer → Verwerking → Vastgelopen bestellingen). Terugbetalen gebeurt in Mollie. Wat is je beleid?
- [ ] Mollie: account bevestigd, iDEAL en PayPal aangezet, testsleutel in Render (zie `docs/MOLLIE_TEST.md`).

## ⚖ Juridisch beoordelen

1. **Voorwaarden, artikel 2**: "Door je uitnodiging vóór de betaling te controleren en direct na betaling te
   laten publiceren, vraag je ons uitdrukkelijk om direct te leveren." Plus het vinkje bij bestellen: "Ik ga
   akkoord met de voorwaarden en wil dat mijn uitnodiging direct na betaling wordt gepubliceerd." Is dit
   genoeg voor het vervallen van de bedenktijd bij digitale inhoud, of moet de klant uitdrukkelijk verklaren
   dat hij daarmee zijn herroepingsrecht verliest (en moet dat in de bevestigingsmail staan)?
2. **Voorwaarden, artikelen 3 en 4 (nieuw, feitelijk)**: levering (link en QR-code in Mijn Vaylide en per
   e-mail) en afbreken (niets afgeschreven, ontwerp bewaard; zelf verwijderen in Mijn Vaylide). Er staat
   bewust niets over terugbetalen: dat is een keuze van de eigenaar.
3. **Voorwaarden, artikel 8 (Beschikbaarheid)** en een eventuele beperking van aansprakelijkheid.
4. **Privacyverklaring**: verwerkingsverantwoordelijke (bedrijfsgegevens), grondslagen per doel, recht om
   te klagen bij de Autoriteit Persoonsgegevens, de lijst van verwerkers (hosting Render in Frankfurt,
   betalingen Mollie, de e-mailprovider, en Anthropic als de AI-hulp aanstaat: doorgifte buiten de EU?), en
   verwerkersovereenkomsten met die partijen.
5. **Gastgegevens**: de klant nodigt gasten uit en Vaylide bewaart hun antwoorden. Wie is
   verwerkingsverantwoordelijke voor de gastgegevens, en wat moet daarover in de voorwaarden?
6. **Bewaartermijnen** (nu: aanmeldingen 90 dagen na het einde van de beschikbaarheid, ontwerpen zonder
   e-mailadres 30 dagen, nooit bestelde ontwerpen 365 dagen). Aan te passen in Beheer → Instellingen.
7. **Over ons en de homepage**: geen onbewezen claims (geen duurzaamheid, reviews of klantenaantallen). Laat
   meelezen of "Digitaal in plaats van extra drukwerk" en "Snel beschikbaar" zo mogen blijven.

## Keuzes voor aansluitingen

- [ ] **E-mail (SMTP)**: welke aanbieder, welk afzendadres (bijv. `hallo@vaylide.nl`)? Daarna MX, SPF, DKIM en DMARC in de DNS.
- [ ] **Tweede back-uplocatie**: welke S3-compatibele aanbieder in de EU (bijv. Hetzner Object Storage,
      Scaleway, OVHcloud, Backblaze B2 in Amsterdam), en wie maakt de bucket en het sleutelpaar aan? Daarna de
      zeven waarden uit `docs/BACKUP.md` in Render, en de versleutelingssleutel ook op een veilige plek buiten de server.
- [ ] **AI-hulp**: aanzetten (Anthropic-sleutel, kosten per gebruik, vermelding in de privacyverklaring) of uit laten.
- [ ] **Domein**: wanneer omzetten, en staat er nu iets op de hosting bij Vimexx dat moet blijven? Zie `docs/DOMEIN.md`.
- [ ] **TikTok**: link naar het account (Instagram staat er al: `https://www.instagram.com/vaylidenl/`).
- [ ] **Render-abonnement**: welke back-ups van de database krijg je bij het gekozen abonnement (dagelijks, herstel naar een tijdstip)?
