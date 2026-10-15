/* Kerstmarkt v1: het filmpje in de opening, de kaart op de plek van de kaart uit het filmpje, en de knop om de opening
   nog een keer te bekijken.
   - Na een tik op 'Open de kerstkaart' speelt het filmpje (zonder geluid) tot de kaart met de ster er staat. Het speelt
     iets sneller dan het origineel, zodat het precies eindigt als het openingsscherm vervaagt (4,55 s na de tik).
     Begint het later, dan speelt het nog iets sneller.
   - Begint het filmpje niet binnen 0,8 seconde, blijft het hangen of mag het niet spelen, dan verschijnt de kaart in een
     gloed: het eindbeeld vloeit over het eerste beeld (style.css).
   - Bij 'minder beweging' of 'Beweging uit' speelt er niets: invite.js opent dan rustig, direct op de geopende kaart.
   - De kaart in de kop begint precies op de kaart uit het filmpje: dit script rekent uit hoe de kaart (een rechthoek) op
     de vier hoeken van de kaart in het laatste filmbeeld past (--km-van, een perspectieftransformatie).
   Dit script draait vóór invite.js (het staat eerder in de pagina), zodat het filmpje al start voordat invite.js opent.
   Wijzig een uitgebrachte versie niet: maak een v2. */
(function () {
  "use strict";
  var html = document.documentElement;
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Na de tik vervaagt het openingsscherm op dit moment (gelijk aan data-fx-intro en --km-out in style.css).
  var FADE_AT = 4550;
  // De vier hoeken van de kaart in het laatste filmbeeld (720 × 1280): linksboven, rechtsboven, rechtsonder, linksonder.
  var FILM_CARD = [[305, 413], [547, 409], [537, 820], [296, 805]];

  /* De voorbeeldbalk: het beeld in de opening begint eronder, net als de kop, zodat ze precies op elkaar passen. */
  var bar = document.querySelector(".inv-banner");
  function setBar() { html.style.setProperty("--km-bar", (bar ? bar.offsetHeight : 0) + "px"); }
  setBar();

  /* Veel tekst op de kaart: de letters worden kleiner (nooit groter), zodat alles binnen de gouden rand blijft. */
  var box = document.querySelector("[data-km-fit]");
  function fit() {
    if (!box || !box.firstElementChild) return;
    var inner = box.firstElementChild;
    var scale = 1;
    box.style.setProperty("--km-fit", "1");
    for (var i = 0; i < 5; i++) {
      var room = box.clientHeight / Math.max(1, inner.offsetHeight);
      if (room >= 0.995) break;
      scale = Math.max(0.5, scale * room * 0.98);
      box.style.setProperty("--km-fit", scale.toFixed(3));
    }
  }

  /* De kaart in de kop op de plek van de kaart in het filmpje: een perspectieftransformatie van de rechthoek van de
     kaart naar de vier hoeken in het beeld (Heckbert, 'Fundamentals of Texture Mapping', 1989). */
  var frame = document.querySelector("[data-km-frame]");
  var card = document.querySelector("[data-km-card]");
  function setPose() {
    if (!frame || !card) return;
    var fw = frame.offsetWidth, fh = frame.offsetHeight, w = card.offsetWidth, h = card.offsetHeight;
    if (!fw || !fh || !w || !h) return;
    var q = FILM_CARD.map(function (p) { return [p[0] / 720 * fw - card.offsetLeft, p[1] / 1280 * fh - card.offsetTop]; });
    var x0 = q[0][0], y0 = q[0][1], x1 = q[1][0], y1 = q[1][1], x2 = q[2][0], y2 = q[2][1], x3 = q[3][0], y3 = q[3][1];
    var dx1 = x1 - x2, dx2 = x3 - x2, sx = x0 - x1 + x2 - x3;
    var dy1 = y1 - y2, dy2 = y3 - y2, sy = y0 - y1 + y2 - y3;
    var den = dx1 * dy2 - dx2 * dy1;
    if (!den) return;
    var g = (sx * dy2 - dx2 * sy) / den, k = (dx1 * sy - sx * dy1) / den;
    var a = x1 - x0 + g * x1, b = x3 - x0 + k * x3, d = y1 - y0 + g * y1, e = y3 - y0 + k * y3;
    var m = [a / w, d / w, 0, g / w, b / h, e / h, 0, k / h, 0, 0, 1, 0, x0, y0, 0, 1];
    card.style.setProperty("--km-van", "matrix3d(" + m.map(function (n) { return +n.toFixed(6); }).join(", ") + ")");
  }

  /* Het kaartje met de datum: de halve gaatjes op de hoogte van de stippellijn (die schuift mee met de tekst). */
  function setCut() {
    document.querySelectorAll(".km-pass").forEach(function (pass) {
      var more = pass.querySelector(".km-pass__more");
      if (more) pass.style.setProperty("--km-cut", (pass.clientTop + more.offsetTop + 1) + "px");
    });
  }

  function layout() { setBar(); fit(); setPose(); setCut(); }
  layout();
  var resizeTimer = null;
  window.addEventListener("resize", function () {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(layout, 120);
  });
  if (document.fonts) {
    // Na het laden van de letters kan de voorbeeldbalk een andere hoogte hebben, en de tekst op de kaart ook.
    if (document.fonts.ready) document.fonts.ready.then(layout);
    if (document.fonts.addEventListener) document.fonts.addEventListener("loadingdone", fit);
  }

  /* ---------- De opening ---------- */
  var cover = document.querySelector(".km-cover");
  var film = cover && cover.querySelector("[data-km-film]");

  /* De knop onderaan: de opening nog een keer bekijken (de pagina opnieuw, met het openingsscherm). */
  var again = document.querySelector("[data-km-again]");
  if (again && cover) {
    again.hidden = false;
    again.querySelector("button").addEventListener("click", function () {
      try { sessionStorage.removeItem("vierlief-open:" + location.pathname); } catch (e) { /* privémodus */ }
      window.scrollTo(0, 0);
      location.replace(location.pathname + location.search);
    });
  }

  if (!cover || !film) return;
  var started = false, tapped = 0, waitTimer = null;

  /* Het filmpje speelt toch niet (of hapert): dan de gloed met het eindbeeld (zie style.css). Komt dat laat,
     dan vloeit het eindbeeld snel over, zodat het er staat voordat het openingsscherm vervaagt. */
  function fade() {
    window.clearTimeout(waitTimer);
    if (!cover.classList.contains("km-cover--speelt")) return;
    if (tapped && Date.now() - tapped > 1500) cover.classList.add("km-cover--snel");
    cover.classList.remove("km-cover--speelt", "km-cover--film");
    if (!film.paused) film.pause();
  }

  film.muted = true;
  film.addEventListener("playing", function () {
    if (started || !cover.classList.contains("km-cover--speelt")) return;
    started = true;
    window.clearTimeout(waitTimer);
    // Zo snel dat het filmpje klaar is als het openingsscherm vervaagt (minstens gewone snelheid, hoogstens twee keer).
    var left = (FADE_AT - (Date.now() - tapped) - 60) / 1000;
    var rest = (film.duration || 5.54) - film.currentTime;
    film.playbackRate = Math.min(2, Math.max(1, left > 0 ? rest / left : 2));
    cover.classList.add("km-cover--film");
  });
  // Blijft het filmpje halverwege hangen (trage verbinding), dan verschijnt de kaart in de gloed.
  film.addEventListener("waiting", function () {
    if (started && html.classList.contains("is-opening")) fade();
  });

  cover.querySelectorAll("[data-open]").forEach(function (el) {
    el.addEventListener("click", function () {
      if (html.classList.contains("is-opening") || html.classList.contains("is-open")) return;
      if (reduceMotion || html.classList.contains("fx-paused")) return;
      cover.classList.add("km-cover--speelt");
      tapped = Date.now();
      // Nog niet (genoeg) geladen, zoals vaak op een iPhone, die een filmpje meestal pas na een tik laadt: begint het
      // niet binnen 0,8 seconde, dan de gloed. Is het al geladen, dan speelt het meteen.
      waitTimer = window.setTimeout(function () { if (!started) fade(); }, 800);
      try { film.currentTime = 0; } catch (e) { /* nog niet te spoelen */ }
      var attempt = film.play();
      if (attempt && attempt.catch) attempt.catch(fade);
    });
  });

  /* 'Beweging uit' tijdens het filmpje: meteen naar het laatste beeld (de kaart met de ster). */
  new MutationObserver(function () {
    if (film.paused || !html.classList.contains("fx-paused")) return;
    film.pause();
    try { film.currentTime = film.duration || film.currentTime; } catch (e) { /* laat staan */ }
  }).observe(html, { attributes: true, attributeFilter: ["class"] });
  // Zodra de kaart open is, is het filmpje niet meer nodig.
  document.addEventListener("invite:opened", function () { if (!film.paused) film.pause(); });
})();
