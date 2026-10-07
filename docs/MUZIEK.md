# Muziek bij een uitnodiging

Stand 9 oktober 2026. Er staan **geen muziekbestanden** in de repository, behalve de eigen track van Kerststad (`designs/kerststad/v1/media/muziek.mp3`).

## Hoe muziek nu gekoppeld is

| Situatie | Wat speelt er | Waar |
|---|---|---|
| Voorbeeld van een ontwerp (`/voorbeeld/<slug>/`) | een **speeldoosje**, live gesynthetiseerd in de browser (geen bestand); de melodie staat per ontwerp in `manifest.json` → `demo_melody` | `invitations/static/invitations/invite.js` (`MELODIES`) |
| Echte uitnodiging, klant uploadt eigen mp3/m4a | het bestand van de klant (betaalde extra "Muziek", functie `music`) | Studio, stap Foto's → `content.music.asset` |
| Ontwerp met een eigen track in het manifest | die track (alleen Kerststad) | `manifest.json` → `music`, zie hieronder |

Melodieën van de voorbeelden: `we-wish-you` (Golden Noël, Kerstbol, Kerstkaart, Aan tafel, Kerststad als terugval), `stille-nacht` (Winterlicht), `carol-of-the-bells` (Middernacht), `gloria` (Gloria) en `canon` (de bruiloftsontwerpen). Alle zijn publiek domein en eigen synthese.

## Een eigen track per ontwerp

```json
"music": { "src": "designs/<slug>/v1/media/muziek.mp3", "title": "Naam van het nummer", "volume": 0.45 }
```

- `src`: pad onder `static/`. `volume`: 0,05 tot 1; de muziek begint met een zachte inzet van 2 s.
- Het element heeft `loop` en `preload="none"`; er is geen autoplay. De knop is de bestaande muziekknop.
- Een klant met eigen muziek (`content.music.asset`) gaat voor; zonder `music` in het manifest verandert er niets.
- **De keuze van de klant** staat expliciet in `content.music.source`: `design` (de track van het ontwerp, inbegrepen), `none` (geen muziek) of `custom` (eigen upload, de betaalde extra "Muziek"). Een lege bron betekent "niet gekozen": dan geldt alleen een eigen upload, zoals altijd. Er wordt niets afgeleid uit ontbrekende velden.
- Een nieuw concept bij een ontwerp met een eigen track begint met `source = design` en het onderdeel Muziek aan (`muziek_bij_ontwerp` in `invitations/content.py`, ook bij wisselen van ontwerp; bestaande klantmuziek en bestaande keuzes blijven ongemoeid).
- **Studio** (stap Foto's, Muziek): bij zo'n ontwerp drie keuzes met een prijslabel: *Muziek van dit ontwerp* (inbegrepen), *Geen muziek* en *Eigen muziek uploaden* (extra optie, gaat altijd voor). Bij `design` en `none` blijft een eerder geüploade eigen muziek bewaard, speelt niet en kost niets. Ontwerpen zonder track houden de oude muziekstap.
- **Prijs** (`required_features`): alleen `custom` met een bestand (of een oude kaart met upload en lege bron) vraagt de extra "Muziek"; Essentieel € 39 → € 48, Compleet € 69 blijft € 69.
- Voorbeeld en echte kaart gebruiken dezelfde `build_view`, dus de Studio-preview en de gepubliceerde kaart gedragen zich gelijk.
- `sync_designs` werkt bij bestaande ontwerpversies alleen de sleutel `music` bij; de rest van het vastgelegde manifest blijft.
- De hotlinkblokkade dekt ook `.mp3` onder `/static/designs/`.
