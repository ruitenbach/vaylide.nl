# Algemene voorwaarden verwerken (concept 29 september 2026)

Werk op de **lokale branch `claude/algemene-voorwaarden`**. Niet gepusht: de branch
`claude/kerstkaarten-website-design-51mn9k` gaat automatisch naar Render, en publiceren gebeurt pas na akkoord van de
eigenaar. De tekst is een **concept**. Hij is niet juridisch beoordeeld en de site zegt dat ook zo.

## Wat er gebouwd is

| Onderdeel | Waar |
|---|---|
| Volledige concepttekst (artikel 1 t/m 16 en het modelformulier) als versie `2026-09-29` | `core/templates/core/voorwaarden/2026-09-29.html`, `core/voorwaarden.py` |
| Pagina `/voorwaarden/`, oudere versies op `/voorwaarden/versie/<versie>/`, downloaden als HTML-bestand, en afdrukken of opslaan als pdf | `core/views.py`, `core/templates/core/terms.html`, `terms_download.html` |
| Bedrijfsgegevens uit de instellingen, ontbrekende gegevens als geel invulveld | `core/company.py`, filter `invul` in `core/templatetags/vl.py` |
| "Contact & bedrijfsgegevens", bereikbaar via de footer | `core/templates/core/contact.html`, `templates/partials/footer.html` |
| Looptijd in kalendermaanden vanaf de bevestigde betaling, één keer vastgelegd als `Order.ends_at` | `invitations/availability.py`, `orders/fulfilment.py` |
| Bij bestellen twee losse vinkjes, standaard uit: de voorwaarden (met versie en download), en de toestemming voor directe levering met de erkenning over het herroepingsrecht | `studio/forms.py`, `studio/templates/studio/step_bestellen.html` |
| Op de bestelling vastgelegd: versie van de voorwaarden, tijdstip en letterlijke tekst van de toestemming | `orders/models.py` (`terms_version`, `delivery_consent_at`, `delivery_consent_text`) |
| Bewaarbare bestelbevestiging (zie hieronder) | `processing/templates/emails/order_confirmation.txt`, `processing/emails.py` |
| Herroepingsfunctie "Hier de overeenkomst ontbinden" / "Ontbinding bevestigen", met ontvangstbevestiging en een lijst in het beheer | `orders/views.py` (`withdraw`), model `Withdrawal`, `beheer` → Herroepingen |
| Beveiliging: in live-modus start de site niet zonder juridische naam en vestigingsadres | `config/settings.py` |

**De bestelbevestiging bevat:**
- de bedrijfsgegevens;
- het pakket, de regels en de prijs;
- de aankoopdatum en "Online tot en met";
- de toestemming voor directe levering (tijdstip en tekst);
- de versie van de voorwaarden met een link, en de voorwaarden als bijlage;
- de link naar de herroepingsfunctie.

## Looptijd (artikel 6): hoe het technisch werkt

- **Aankoopdatum:** `Order.paid_at`, het moment waarop de betaalprovider de betaling bevestigt.
- **Einddatum:** dezelfde kalenderdag 6 of 12 maanden later (plus eventueel "Langer online"), tot 23:59:59 in Nederlandse
  tijd. Bestaat die dag niet, dan telt de laatste dag van de maand: 31 januari + 1 maand = 28 of 29 februari.
- **Vastgelegd:** de einddatum wordt één keer vastgelegd, op `Order.ends_at`, bij de eerste verwerking van de betaling.
  Een herhaalde betaalmelding, later publiceren of een wijziging verschuift hem niet.
- **Bestaande bestellingen** houden hun eerder beloofde datum; er is niets met terugwerkende kracht herberekend. Oude
  bestellingen gebruikten ongeveer 30,44 dagen per maand, gerekend vanaf de publicatie.
- **Waar je de einddatum ziet:** in de bestelbevestiging, op de bedankpagina en in Mijn VAYLIDE. Bij Bestellen staat de
  einddatum als je vandaag betaalt, met een waarschuwing als die vóór de evenementdatum valt. Dat is geen verplichte
  upgrade.
- **Verlopen:** de nachtelijke taak `apply_retention` zet uitnodigingen na de einddatum op "Verlopen". Ze zijn dan niet
  meer bereikbaar. Dat bestond al.
- **Verlopen is niet verwijderen:** aanmeldingen gaan pas een instelbaar aantal dagen later weg. Zie de privacyverklaring.

## Ontbrekende bedrijfsgegevens en besluiten van de eigenaar

1. **Juridische naam met rechtsvorm:** in Render zetten als `VIERLIEF_JURIDISCHE_NAAM`.
2. **Vestigingsadres (woonadres):** in Render zetten als `VIERLIEF_ADRES`, regels scheiden met `|`. Zonder deze twee
   start de site niet in live-modus.
3. **Contactadres:** voorlopig info@vantorstudio.nl. Dat staat nu als standaard in de code en in je lokale `.env`.
   **Op Render wordt `VIERLIEF_CONTACT_EMAIL` apart ingesteld: pas het daar zelf aan.**
4. **Telefoonnummer:** bewust weggelaten, op keuze van de eigenaar. Zie de juridische punten.
5. **Prijsverdeling tussen kaart (digitale inhoud) en online beschikbaarheid (dienst):** niet verzonnen. Die is nodig als
   iemand de dienst herroept na de start (artikel 9.3 en 9.4).
6. **Beleid bij herroepen:**
   - de site registreert het verzoek en stuurt een bevestiging;
   - beoordelen, eventueel offline halen en terugbetalen (binnen 14 dagen, via Mollie) doet de eigenaar;
   - er is niets automatisch aan geldstromen veranderd.

## Verschillen tussen de tekst en wat technisch werkt

- **Artikel 3, technische vereisten:** de site noemt nergens vóór aankoop welke technische vereisten er gelden (bijvoorbeeld
  een recente browser). Nog toe te voegen.
- **Artikel 6, eigen inhoud terugkrijgen:** er is een export van de gastenlijst. Er is geen export van de eigen inhoud,
  zoals geüploade foto's en teksten.
- **Artikel 9.2 en 9.4, directe levering:**
  - het vinkje voor directe levering is **verplicht** om te bestellen, want de kaart wordt direct na betaling gepubliceerd;
  - bij Bestellen staat alleen een korte zin over de regels per onderdeel ("Voor de online beschikbaarheid (een dienst)
    gelden aparte regels"); een volledige uitleg vóór aankoop ontbreekt nog.
- **Artikel 10:** de herroepingsfunctie werkt voor registratie en ontvangstbevestiging. Toegang beëindigen en terugbetalen
  zijn handwerk.
- **Artikel 12:** controleer of de AI-hulp bij teksten en de functie eigen gezichten vooraf genoeg uitleg geven over de
  gegevensverwerking.
- **Artikel 15, klachten binnen veertien dagen:** een belofte die de eigenaar zelf moet waarmaken; de site bewaakt dat niet.
- **Privacyverklaring vergeleken** (inmiddels uitgewerkt op de branch `claude/privacyverklaring`, zie `docs/PRIVACY.md`):
  - "Wie zijn wij" noemt geen juridische naam en geen adres;
  - de nieuwsbrief (toestemming en afmelden), de herroepingsgegevens en eventuele verwerking door Google (eigen gezichten,
    staat uit) worden nog niet genoemd;
  - de bewaartermijnen zijn niet aangepast.
- **Oude teksten vervangen:**
  - de oude voorwaarden (8 korte artikelen) en het oude vinkje ("wil dat mijn uitnodiging direct na betaling wordt
    gepubliceerd") zijn vervangen;
  - de oude melding "maanden online vanaf publicatie" is aangepast naar "vanaf de aankoopdatum".

## Juridisch te beoordelen

1. **Herroepingsfunctie (art. 6:230oa BW, verplicht sinds 19 juni 2026):**
   - teksten: "Hier de overeenkomst ontbinden" en "Ontbinding bevestigen";
   - gevraagd wordt naam, bestelnummer of omschrijving, en e-mail;
   - de ontvangstbevestiging gaat per e-mail, met inhoud en datum en tijd;
   - de functie is altijd bereikbaar via de footer en de contactpagina.
   - Laten toetsen of dit aan de wet voldoet.
2. **Vervallen van het herroepingsrecht bij digitale inhoud:** met een afzonderlijk vinkje, bevestigd in de e-mail. Te
   toetsen:
   - de precieze tekst;
   - of de toestemming een voorwaarde voor bestellen mag zijn;
   - hoe dit samengaat met de online beschikbaarheid als dienst (artikel 9.3 en 9.4).
3. **Bedrijfsgegevens:**
   - het vestigingsadres is een woonadres;
   - er staat geen telefoonnummer, terwijl de wet om contactgegevens vraagt.
   - Laten beoordelen wat verplicht op de site en in de bevestiging moet.
4. **Contactadres:** een e-mailadres op een ander domein (vantorstudio.nl) als contact- en afzenderadres. Let op de
   bezorging (SPF, DKIM, DMARC) zodra e-mail echt verstuurd wordt.
5. **De concepttekst in het algemeen:** de tevredenheidsbelofte (artikel 7), de aansprakelijkheid (artikel 15) en het
   toepasselijk recht (artikel 16).

Bronnen (september 2026):
- [Thuiswinkel.org: de herroepingsfunctie](https://www.thuiswinkel.org/kennisbank/kennisartikelen/de-herroepingsfunctie-op-weg-naar-implementatie-in-nederland/)
- [Thuiswinkel.org: uitzonderingen op het herroepingsrecht](https://www.thuiswinkel.org/kennisbank/kennisartikelen/uitzonderingen-op-het-herroepingsrecht/)
- [ICTRecht: herroepingsrecht bij digitale inhoud](https://www.ictrecht.nl/blog/herroepingsrecht-op-digitale-inhoud-kun-je-dat-uitsluiten)

Deze bronnen zijn geen officiële overheidsbronnen. Een jurist moet de tekst van de wet zelf (art. 6:230oa BW) en de
uitleg van de ACM nog raadplegen.

## Getest

Zie `docs/CONTROLES.md`, onder "Algemene voorwaarden".
