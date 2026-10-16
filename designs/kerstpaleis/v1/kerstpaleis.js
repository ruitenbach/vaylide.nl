/* Kerstpaleis v1: de film in de opening.
   Tot de gast tikt, staat het eerste beeld (de dichte deuren) stil. Na 'Open de deuren' speelt het filmpje:
   de deuren gaan open naar gouden licht. Daarna laat het platform het openingsscherm vervagen (data-duration),
   zodat de kaart eronder tevoorschijn komt, net als in de film.
   Bij 'minder beweging' of 'Beweging uit' speelt het filmpje niet: de kaart verschijnt dan direct.
   Zonder dit script of zonder filmpje werkt alles ook: dan blijft het eerste beeld staan tot de kaart verschijnt.
   Wijzig een uitgebrachte versie niet: maak een v2. */
/* De kaart vult precies het scherm: de voorbeeldbalk bovenaan gaat eraf, zodat de scrollaanwijzing in beeld blijft. */
(function () {
  "use strict";
  var bar = document.querySelector(".inv-banner");
  if (!bar) return;
  function set() { document.documentElement.style.setProperty("--kp-bar", bar.offsetHeight + "px"); }
  set();
  if (window.ResizeObserver) new ResizeObserver(set).observe(bar);
})();

(function () {
  "use strict";
  var cover = document.querySelector(".kp-cover");
  var film = cover && cover.querySelector("[data-kp-film]");
  if (!film) return;
  var html = document.documentElement;

  film.muted = true;
  function ready() { cover.classList.add("kp-cover--film"); }
  if (film.readyState >= 2) ready();
  else film.addEventListener("loadeddata", ready);

  document.addEventListener("invite:opening", function (event) {
    if (event.detail && event.detail.reduceMotion) return;
    cover.classList.add("kp-cover--playing");
    var attempt = film.play();
    if (attempt && attempt.catch) attempt.catch(function () { cover.classList.remove("kp-cover--playing"); });
  });
  // Zodra de kaart open is, is het filmpje niet meer nodig.
  document.addEventListener("invite:opened", function () { if (!film.paused) film.pause(); });
  // Tikt de gast tijdens het openen op 'Beweging', dan staat het filmpje meteen stil.
  new MutationObserver(function () {
    if (html.classList.contains("fx-paused") && !film.paused) film.pause();
  }).observe(html, { attributes: true, attributeFilter: ["class"] });
})();
