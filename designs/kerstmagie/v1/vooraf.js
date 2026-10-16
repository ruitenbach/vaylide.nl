/* Kerstmagie v1: draait vóór effects.js (staat daarom vooraan in de kop).
   Kerstmagie tekent zijn eigen sneeuw met diepte en meebewegend met het scrollen (snow.js). De sfeer in het manifest blijft
   'sneeuw' (voor de labels en de beschrijving op de website), maar de gedeelde effectenlaag hoeft die sneeuw dan niet nog
   eens te tekenen: we zetten haar sfeer uit voordat ze hem leest. De knal bij het openen en de knop 'Beweging' blijven van effects.js. */
document.documentElement.setAttribute("data-fx-sfeer", "geen");
