/* Kerstcoupé v1: het filmpje van de gordijnen in de opening, en de groet op het raam passend maken.
   - Na een tik op 'Open de gordijnen' speelt het filmpje (zonder geluid). Het laatste beeld is hetzelfde als de kop,
     dus als het openingsscherm vervaagt, loopt het naadloos over in de groet op het raam.
   - Begint het filmpje niet binnen 0,8 seconde, blijft het hangen of mag het niet spelen, dan gaan de gordijnen
     open met een overvloeier naar het open raam.
   - Bij 'minder beweging' of 'Beweging uit' speelt er niets: invite.js opent dan rustig, direct op het open raam.
   Dit script draait vóór invite.js (het staat eerder in de pagina), zodat de tijden van de opening al kloppen
   op het moment dat invite.js ze leest. Zonder dit script opent de kaart met de overvloeier (style.css).
   Wijzig een uitgebrachte versie niet: maak een v2. */
(function () {
  "use strict";
  var html = document.documentElement;
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* De voorbeeldbalk: het beeld in de opening begint eronder, net als de kop, zodat ze precies op elkaar passen. */
  var bar = document.querySelector(".inv-banner");
  function setBar() { html.style.setProperty("--kc-bar", (bar ? bar.offsetHeight : 0) + "px"); }
  setBar();

  /* Veel tekst op het raam: de letters worden kleiner (nooit groter), zodat alles op het glas blijft. */
  var box = document.querySelector("[data-kc-fit]");
  function fit() {
    if (!box || !box.firstElementChild) return;
    var inner = box.firstElementChild;
    var scale = 1;
    box.style.setProperty("--kc-fit", "1");
    // Alleen de hoogte telt: de regels lopen in de breedte gewoon door naar een volgende regel.
    // (offsetHeight, niet scrollHeight: de waas achter de letters steekt bewust buiten het tekstvak uit.)
    for (var i = 0; i < 4; i++) {
      var room = box.clientHeight / Math.max(1, inner.offsetHeight);
      if (room >= 0.995) break;
      scale = Math.max(0.55, scale * room * 0.98);
      box.style.setProperty("--kc-fit", scale.toFixed(3));
    }
  }
  fit();
  var resizeTimer = null;
  window.addEventListener("resize", function () {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(function () { setBar(); fit(); }, 120);
  });
  if (document.fonts) {
    // Na het laden van de letters kan de voorbeeldbalk een andere hoogte hebben, en de tekst op het raam ook.
    if (document.fonts.ready) document.fonts.ready.then(function () { setBar(); fit(); });
    if (document.fonts.addEventListener) document.fonts.addEventListener("loadingdone", fit);
  }

  /* ---------- De opening ---------- */
  var cover = document.querySelector(".kc-cover");
  var film = cover && cover.querySelector("[data-kc-film]");
  if (!cover) return;
  var started = false, waitTimer = null;

  function timing(duration, intro, out) {
    cover.setAttribute("data-duration", String(duration));
    cover.setAttribute("data-fx-intro", String(intro));
    cover.style.setProperty("--kc-out", out + "ms");
  }
  /* Het filmpje speelt toch niet (of hapert): dan de overvloeier naar het open raam (zie style.css). */
  function fade() {
    window.clearTimeout(waitTimer);
    cover.classList.remove("kc-cover--speelt");
  }

  if (film) {
    film.muted = true;
    film.addEventListener("playing", function () {
      started = true;
      window.clearTimeout(waitTimer);
      cover.classList.add("kc-cover--film");
    });
    // Blijft het filmpje halverwege hangen (trage verbinding), dan vloeit het open raam eroverheen.
    film.addEventListener("waiting", function () {
      if (started && html.classList.contains("is-opening")) fade();
    });
  }

  cover.querySelectorAll("[data-open]").forEach(function (el) {
    el.addEventListener("click", function () {
      if (html.classList.contains("is-opening") || html.classList.contains("is-open")) return;
      if (reduceMotion || html.classList.contains("fx-paused") || !film) return;
      // (De standaardtijden in invitation.html horen bij de overvloeier.)
      cover.classList.add("kc-cover--speelt");
      timing(4300, 3700, 3800);
      // Nog niet (helemaal) geladen, zoals vaak op een iPhone, die een filmpje meestal pas na een tik laadt: begint het
      // niet binnen 0,8 seconde, dan de overvloeier. Is het al helemaal geladen, dan speelt het meteen.
      if (film.readyState < 4) waitTimer = window.setTimeout(function () { if (!started) fade(); }, 800);
      try { film.currentTime = 0; } catch (e) { /* nog niet te spoelen */ }
      var attempt = film.play();
      if (attempt && attempt.catch) attempt.catch(fade);
    });
  });

  /* 'Beweging uit' tijdens het filmpje: meteen naar het open raam (het laatste beeld). */
  function calmFilm() {
    if (!film || film.paused || !html.classList.contains("fx-paused")) return;
    film.pause();
    try { film.currentTime = film.duration || film.currentTime; } catch (e) { /* laat staan */ }
  }
  new MutationObserver(calmFilm).observe(html, { attributes: true, attributeFilter: ["class"] });
})();
