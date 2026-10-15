# Kerstcoupé: de beelden uit het filmpje

De kerstkaart Kerstcoupé (`designs/kerstcoupe/v1/`) gebruikt het filmpje dat de eigenaar op 15 oktober 2026 stuurde: een treincoupé bij avond, waarin rode fluwelen gordijnen opengaan en een besneeuwd bergdorp onder de maan laten zien. In het filmpje verschijnt daarna "Fijne kerstdagen en een schitterend nieuwjaar" met VAYLIDE eronder.

Op de kaart staat alleen het stuk **zonder tekst**: van 1,0 tot 4,9 seconden, als de gordijnen opengaan. De groet op het raam maakt de kaart zelf, met de naam van de klant op de plek waar in het filmpje VAYLIDE staat. Zo kan elke klant de kaart gebruiken.

## Opnieuw maken

Bijvoorbeeld als er een scherpere of langere versie van het filmpje komt (ffmpeg en Pillow nodig):

```bash
.venv/bin/python tools/kerstcoupe/maak_film.py pad/naar/filmpje.mp4
```

Bij een ander filmpje kloppen de beeldnummers misschien niet meer. Kies dan met `--begin` het eerste beeld waarin de gordijnen nog dicht zijn en met `--eind` het laatste beeld voordat er tekst verschijnt (bij 24 beelden per seconde is beeld 24 precies 1 seconde).

Daarna:

1. Controleer de overgang: het laatste filmbeeld (`open.webp`) is ook de kop van de kaart. De camera moet stilstaan, anders verspringt het beeld als de opening verdwijnt.
2. Komt het raam op een andere plek, pas dan in `style.css` de plaats van het glas (`.kc-glass`), de stoom (`.kc-steam`), het licht (`.kc-glow--lamp` en `.kc-glow--kaars`) en de tekst (`.kc-hero__text`) aan, in procenten van het beeld.
3. Meet het contrast van de tekst op het raam: `node e2e/coupe.cjs http://127.0.0.1:8000`.
4. Maak het kaartbeeld voor de collectie opnieuw: `node e2e/make_design_images.cjs http://127.0.0.1:8000 /tmp/kaart kerstcoupe` en zet het om naar `static/img/designs/kerstcoupe.webp` (800 × 1000).
5. Controleer de opening met `node e2e/coupe-opening.cjs http://127.0.0.1:8000 /tmp/coupe` (het filmpje vooraf geladen, pas na de tik, en te traag).
6. Draai `manage.py test tests`.

Na de livegang gaat een nieuw filmpje in een nieuwe versie (`designs/kerstcoupe/v2/`), zodat verstuurde kaarten niet veranderen.

## Rechten

Het filmpje lijkt met AI gemaakt. Of het op de website mag worden gebruikt, bevestigt de eigenaar zelf.
