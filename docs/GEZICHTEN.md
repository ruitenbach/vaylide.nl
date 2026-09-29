# Onze eigen gezichten (Balzaal) — gebouwd, staat UIT

De klant kan een foto van de bruid en van de bruidegom uploaden. Een beeld-API maakt daarmee een persoonlijke versie
van het bruidspaar in de balzaal. De klant ziet het voorbeeld eerst zelf, keurt het goed vóór het afrekenen, en na
betaling staat precies die versie op de kaart. **De functie staat standaard uit en is nog niet openbaar.**

## Wat er gebouwd is

| Onderdeel | Waar |
|---|---|
| Pagina in de editor (stap Stijl → "Onze eigen gezichten") | `gezichten/views.py`, `gezichten/templates/gezichten/gezichten.html`, `static/js/gezichten.js` |
| Uploaden, toestemming, pogingen, goedkeuren, verwijderen | `gezichten/services.py`, model `FaceRequest` |
| Koppeling met de beeld-API (Gemini) en een nagebootste testbewerking | `gezichten/provider.py` |
| Op de kaart: de goedgekeurde versie als hele scène (zaal met paar), de bloemen ervoor | `designs/balzaal/v1/invitation.html` |
| Prijs: content met een eigen versie vraagt de functie `gezichten` → extra optie wordt automatisch meegeteld | `catalog/features.py`, `invitations/content.py` |

Werking in het kort:

- **Uploaden:** type en grootte worden gecontroleerd. Een foto mag tot 10 MB zijn en moet minimaal 400 pixels meten.
  De foto wordt opnieuw opgeslagen zonder EXIF of GPS. Toestemming is verplicht en wordt met tekst en tijdstip
  vastgelegd.
- **Opslag:** foto's en voorbeelden staan in een niet-openbare map. Alleen de eigenaar en het Vaylide-team zien ze;
  anderen krijgen 404. Na goedkeuring komt alleen de goedgekeurde afbeelding bij de uitnodiging, en die is pas na
  publicatie openbaar.
- **Voorbeeld maken:** elke poging is één taak met een unieke sleutel. Een herhaalde taak maakt geen tweede beeld en
  kost dus niets extra. Bij drukte probeert de wachtrij het één keer opnieuw. Een mislukte poging telt niet mee.
  Standaard zijn er 3 pogingen (`VIERLIEF_FACES_ATTEMPTS`); extra pogingen kent het beheer toe (veld `extra_attempts`).
- **Achtergrond:** de generatie loopt op de achtergrond, omdat ze langer kan duren dan een webverzoek. De pagina
  ververst vanzelf.
- **Na betaling:** alles ligt vast. Er komt geen nieuwe generatie of andere goedkeuring meer. Gepubliceerd wordt
  precies de goedgekeurde versie.
- **Verwijderen:** de klant kan de foto's en voorbeelden altijd verwijderen. Vóór betaling verdwijnt dan ook de eigen
  versie van de kaart. Na betaling ruimt de nachtelijke taak de losse foto's zelf op; de goedgekeurde versie blijft
  op de kaart.
- **Eén of twee foto's:** er zijn nu altijd twee foto's nodig (`ALLOW_SINGLE = False`). Met één foto de andere persoon
  laten staan kan pas nadat met de echte API is getest dat dat betrouwbaar gaat.

## Beeld-API: onderzoek en kosten (september 2026)

| API | Geschikt? | Kosten per generatie (1 scène + 2 gezichtsfoto's) |
|---|---|---|
| **Google Gemini 3 Pro Image ("Nano Banana Pro")** (gekozen standaard, `gemini-3-pro-image`) | Sterk in het behouden van personen en compositie; meerdere referentiebeelden (tot 4 personen) | uitvoer 2K ≈ **$0,134** + invoer ≈ $0,004 → **ca. $0,14 (€0,13)** |
| Google Gemini 3.1 Flash Image (`gemini-3.1-flash-image`) | Sneller en goedkoper, iets minder nauwkeurig | 2K ≈ **$0,10**; 1K ≈ $0,07 |
| OpenAI gpt-image-2 (bewerken met referentiebeelden) | Goed alternatief | hoge kwaliteit 1024×1536 ≈ **$0,17–0,21** incl. invoerbeelden |

Bronnen: [Gemini API-prijzen](https://ai.google.dev/gemini-api/docs/pricing),
[Gemini beeldgeneratie](https://ai.google.dev/gemini-api/docs/image-generation),
[OpenAI gpt-image-1.5](https://developers.openai.com/api/docs/models/gpt-image-1.5),
[OpenAI prijzen](https://developers.openai.com/api/docs/pricing).
Prijzen zonder btw, in dollars. Controleer ze vóór het aanzetten.

Per klant, met maximaal 3 pogingen: **ca. €0,40** aan API-kosten (Nano Banana Pro). Mislukte pogingen tellen voor de
klant niet mee, maar kunnen bij de API soms wel iets kosten.

Privacy bij Gemini (betaalde API):

- Klantgegevens worden niet gebruikt om de modellen te verbeteren.
- Google bewaart prompts en beelden 55 dagen om misbruik op te sporen.
- In de EER gelden altijd de voorwaarden voor betaalde diensten.

Dit moet in de privacyverklaring en de verwerkersovereenkomst komen (zie `docs/INVULLIJST.md`).

## Prijsvoorstel (beslissing van de eigenaar)

Voorstel: een extra optie **"Eigen gezichten op het bruidspaar"** voor **€ 12,50 tot € 14,95** (incl. btw), met 3
pogingen. Dat dekt ruim de API-kosten (ca. € 0,40), het risico op extra ondersteuning, en afkeur door het model. Een
extra set van 3 pogingen zou € 4,95 kunnen kosten (nu nog via het beheer toe te kennen). **Er is geen prijs ingesteld.**

## Aanzetten (pas na akkoord)

1. **Privacy:** privacytekst en verwerkersovereenkomst met Google laten beoordelen.
2. **Beheer:** in Beheer → Prijzen een extra optie maken met functie `gezichten` en de gekozen prijs.
3. **Sleutel in Render:** `GEMINI_API_KEY` = een sleutel van een betaald Google AI-project, alleen in Render.
4. **Aanzetten in Render:** `VIERLIEF_FACES_ENABLED` = `true`. Kies eventueel met `VIERLIEF_FACES_MODEL` een ander
   model.
5. **Kwaliteit testen:** eerst met eigen, toegestane foto's op de afgeschermde testversie.

Zonder één van die stappen blijft de knop onzichtbaar.

Lokaal testen zonder kosten: `VIERLIEF_FACES_ENABLED=true VIERLIEF_FACES_PROVIDER=test` (alleen in testmodus). Die zet
alleen de balk "Testvoorbeeld" op de scène; er wordt niets echt bewerkt.
