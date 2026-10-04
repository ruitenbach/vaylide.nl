# Ontwerpreferenties (prompts en bronnen van externe tools)

Hier bewaren we wat bij een ontwerp hoort maar niet in `designs/<slug>/v1/` thuishoort: prompts en instructies voor externe AI- of videotools,
referentiebeelden, moodboards en korte notities over wat is goedgekeurd of verworpen.

## Indeling (richtlijn; een map met alleen een paar lichte bestanden mag plat blijven)

```
tools/design-references/<slug>/
  README.md        wat staat hier, welke tool, welke datum
  prompts/         prompts en instructies (tekstbestanden)
  referenties/     kleine referentiebeelden (liefst klein; geen auteursrechtelijk beschermd materiaal zonder toestemming)
```

## Afspraken

- Maak de map pas aan als er iets te bewaren is. Nu aanwezig: `kerstbol/` en `kerstkaart/` (zie hun `README.md`).
- Licht en draagbaar: een referentie hoort enkele MB's te zijn, zodat een toekomstige (cloud-)sessie niet afhankelijk is van de lokale mappen van de eigenaar.
- **Geen grote bestanden in Git** (video's, masters, grote PNG's). Zet die in de eigen opslag en noem in het ontwerpdocument (`docs/designs/<slug>.md`, onderdelen 8 en 9) waar ze staan. Wat een ontwerp echt nodig heeft om te draaien, gaat in `designs/<slug>/v1/` en in verkleinde vorm.
- Geen sleutels, wachtwoorden of inloggegevens van externe diensten in deze map.
- Wat hier staat, wordt genoemd in het ontwerpdocument; de plek en de herkomst zijn daar leidend.
