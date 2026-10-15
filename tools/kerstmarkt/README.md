# Kerstmarkt: de beelden uit het filmpje

De kerstkaart Kerstmarkt (`designs/kerstmarkt/v1/`) gebruikt het filmpje dat de eigenaar op 15 oktober 2026 stuurde (WhatsApp-video, 10 seconden, staand 720 × 1280, zonder geluid): je kijkt vanuit een reuzenrad over een besneeuwde kerstmarkt bij avond. Rond 2,5 seconden verschijnt een lichtstreep die uitgroeit tot een lege kaart met een gouden rand en een ster erboven; daarna zoomt het beeld langzaam in.

Op de kaart staat alleen **het begin**: van 0 tot 5,5 seconden (beeld 0 tot en met 132), het moment waarop de gloed rond de kaart weg is. Daarna neemt de echte kaart het over: hij ligt precies op de kaart uit het filmpje, komt naar voren en klapt open, met de groet en de naam van de klant erin. Het onderschrift op de kaart in het filmpje is onleesbaar (met AI gemaakt) en staat daarom niet op de kaart.

## Opnieuw maken

Bijvoorbeeld als er een scherpere of langere versie van het filmpje komt (ffmpeg en Pillow nodig):

```bash
.venv/bin/python tools/kerstmarkt/maak_film.py pad/naar/filmpje.mp4
```

Bij een ander filmpje klopt het laatste beeld misschien niet meer. Kies dan met `--eind` het beeld waarop de kaart er staat zonder gloed (bij 24 beelden per seconde is beeld 24 precies 1 seconde).

Daarna:

1. **De kaart op de kaart.** Het laatste filmbeeld (`kaart.webp`) is ook de kop. Meet in dat beeld de vier hoeken van de kaart (linksboven, rechtsboven, rechtsonder, linksonder, in beeldpunten van 720 × 1280) en zet ze in `FILM_CARD` in `designs/kerstmarkt/v1/kerstmarkt.js`. De ster en het stokje staan in `style.css` bij `.km-star` (breedte en verschuiving in procenten van de kaart). Zonder script geldt een benadering (`translate(…) scale(…)` bij `--km-van` in `style.css`).
2. **Controleer de overgang**: `node e2e/kerstmarkt.cjs http://127.0.0.1:8000 /tmp/kerstmarkt` (de drie paden van de opening, en hoe precies de kaart op de kaart uit het filmpje ligt).
3. **Tijden.** Is het filmpje langer of korter, pas dan `FADE_AT` in `kerstmarkt.js`, `data-duration` en `data-fx-intro` in `invitation.html` en `--km-out` in `style.css` samen aan. Het script laat het filmpje zo snel spelen (minstens gewone snelheid) dat het klaar is op `FADE_AT`.
4. **Het slot** (`slot.webp`) is een uitsnede van het eerste beeld (`SLOT_CROP` in `maak_film.py`). Verschuift de kerstboom, pas dan de twinkelende lichtjes aan (`.km-market__lights` in `style.css`, in procenten van het beeld).
5. **Kaartbeeld voor de collectie**: `node tools/kerstmarkt/kaartbeeld.cjs http://127.0.0.1:8000 /tmp/kerstmarkt.png`, en dan omzetten naar `static/img/designs/kerstmarkt.webp` (de regel staat bovenin het script).
6. Draai `manage.py test tests`.

Na de livegang gaat een nieuw filmpje in een nieuwe versie (`designs/kerstmarkt/v2/`), zodat verstuurde kaarten niet veranderen.

## Rechten

Het filmpje lijkt met AI gemaakt. Of het op de website mag worden gebruikt, bevestigt de eigenaar zelf.
