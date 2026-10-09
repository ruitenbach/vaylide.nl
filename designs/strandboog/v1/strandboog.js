/* Strandboog v1: de opening (ringdoosje, filmscène, namen) als één scène in de kop.
   Volgorde: poster van het gesloten doosje met de knop "Tik om het doosje te openen" → de gast tikt → de filmscène speelt (±18 s: doosje gaat open, bloemenboog
   aan zee, bloemenmeisje, duiven, de boog in het avondlicht) → op 13,7 s verschijnen de namen en de datum en komt de pagina vrij → aan het eind blijft het
   eindbeeld staan. De video speelt alleen na een tik (dus ook als de browser automatisch afspelen blokkeert) en nooit vanzelf opnieuw. Zonder dit script, bij 'minder beweging',
   bij stilgezette beweging of als de opening al gezien is, staat direct het eindbeeld met de namen, met een knop om de scène af te spelen. */
(function () {
  "use strict";
  var hero = document.querySelector("[data-sb]");
  if (!hero) return;
  var html = document.documentElement;
  var q = function (sel) { return hero.querySelector(sel); };
  var video = q("[data-sb-video]"), open = q("[data-sb-open]"), overslaan = q("[data-sb-skip]"), bekijk = q("[data-sb-bekijk]");
  var replay = q("[data-sb-replay]"), status = q("[data-sb-status]");
  var inhoud = document.querySelector(".sb-body");
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var heeftOpening = hero.hasAttribute("data-sb-opening");
  var opslagSleutel = "vierlief-open:" + location.pathname;  // dezelfde sleutel als invite.js: één keer per sessie
  var TEKST_OP = 13.7;                                         // seconde in de video waarop de namen verschijnen (de boog in het avondlicht)
  var STAND = ["sb-gate", "sb-speelt", "sb-tekst", "sb-klaar"];
  var bezig = false, afgelopen = false, afgespeeld = false, geblokkeerd = false, waarnemer = null;

  function rustig() { return reduceQuery.matches || html.classList.contains("fx-paused"); }
  function zeg(tekst) { if (status) status.textContent = tekst; }
  function vergrendel(aan) {
    html.classList.toggle("sb-bezig", aan);
    if (inhoud) { if ("inert" in inhoud) inhoud.inert = aan; else if (aan) inhoud.setAttribute("aria-hidden", "true"); else inhoud.removeAttribute("aria-hidden"); }
  }
  function gezien() { try { return !!window.sessionStorage.getItem(opslagSleutel); } catch (e) { return false; } }
  function onthoud() { if (html.classList.contains("inv-embed")) return; try { window.sessionStorage.setItem(opslagSleutel, "1"); } catch (e) { /* privémodus */ } }
  function zetStand(namen) { STAND.forEach(function (n) { hero.classList.toggle(n, namen.indexOf(n) >= 0); }); }
  function vervolgknop() {
    if (!replay) return;
    replay.hidden = false;
    replay.textContent = (!afgespeeld || geblokkeerd || rustig()) ? "Speel de scène af ▷" : "Opnieuw beleven ↺";
  }
  function rewind() { if (!video) return; video.pause(); try { video.currentTime = 0; } catch (e) { /* nog geen metadata */ } }

  function afronden(metFocus) {
    afgelopen = true; bezig = false;
    zetStand(["sb-klaar"]);
    onthoud();
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    vervolgknop();
    zeg("De uitnodiging is geopend. Scroll voor het programma en het aanmelden.");
    window.requestAnimationFrame(function () {
      vergrendel(false);
      if (metFocus && bekijk) window.requestAnimationFrame(function () { bekijk.focus({ preventScroll: true }); });
    });
  }
  function direct() {  // eindbeeld zonder opening
    zetStand(["sb-klaar"]);
    afgelopen = true; bezig = false;
    vergrendel(false);
    vervolgknop();
  }
  function tekstTonen() {  // de namen komen in beeld en de pagina komt vrij terwijl de laatste seconden nog spelen
    if (!bezig || hero.classList.contains("sb-tekst")) return;
    hero.classList.add("sb-tekst");
    onthoud();
    vergrendel(false);
    zeg("De uitnodiging is geopend. Scroll voor het programma en het aanmelden.");
  }

  function speel() {
    if (!video) { afronden(false); return; }
    rewind();
    zetStand(["sb-speelt"]);
    var belofte = video.play();
    var gelukt = function () { afgespeeld = true; geblokkeerd = false; };
    var mislukt = function () { geblokkeerd = true; afronden(false); };
    if (belofte && belofte.then) belofte.then(gelukt, mislukt); else gelukt();
  }
  if (video) {
    video.addEventListener("timeupdate", function () { if (bezig && video.currentTime >= TEKST_OP) tekstTonen(); });
    video.addEventListener("ended", function () { video.pause(); if (bezig) afronden(true); else { zetStand(["sb-klaar"]); vervolgknop(); } });
    video.addEventListener("error", function () { if (bezig) { geblokkeerd = true; afronden(false); } });
  }

  function begin() {
    if (bezig || afgelopen) return;
    if (rustig()) { overslaanNu(); return; }
    bezig = true;
    if (window.scrollY > 0) window.scrollTo({ top: 0, behavior: "instant" });
    if (open) open.disabled = true;
    zeg("Het doosje gaat open.");
    if (overslaan) overslaan.focus({ preventScroll: true });
    speel();
    if ("MutationObserver" in window) {  // de gast zet de beweging stil tijdens de opening
      waarnemer = new MutationObserver(function () { if (bezig && rustig()) overslaanNu(); });
      waarnemer.observe(html, { attributes: true, attributeFilter: ["class"] });
    }
  }
  function overslaanNu() {
    if (afgelopen) return;
    rewind();
    afgespeeld = false;
    if (open) open.disabled = true;
    afronden(true);
    zeg("Opening overgeslagen. De uitnodiging is geopend. Scroll voor het programma en het aanmelden.");
  }
  function opnieuw() {
    rewind();
    bezig = true; afgelopen = false; afgespeeld = false; geblokkeerd = false;
    replay.hidden = true;
    hero.classList.remove("sb-tekst");
    window.scrollTo(0, 0);
    vergrendel(true);
    if (overslaan) overslaan.focus({ preventScroll: true });
    zeg("De scène speelt opnieuw.");
    speel();
  }

  if (open) open.addEventListener("click", begin);
  if (overslaan) overslaan.addEventListener("click", overslaanNu);
  if (replay) replay.addEventListener("click", function () { if (rustig() || geblokkeerd || !afgespeeld) { bezig = true; afgelopen = false; hero.classList.remove("sb-tekst"); replay.hidden = true; speel(); } else opnieuw(); });
  if (bekijk) bekijk.addEventListener("click", function () {
    var doel = document.getElementById("sb-verder");
    if (doel) doel.scrollIntoView({ behavior: rustig() ? "auto" : "smooth", block: "start" });
  });
  var skipLink = document.querySelector(".skip-link");
  if (skipLink) skipLink.addEventListener("click", function () { if (bezig) overslaanNu(); });
  window.addEventListener("pagehide", function () { if (video) video.pause(); });

  /* ---------- de uitnodiging eronder: achtergrondfoto's schuiven iets mee (alleen met beweging) ---------- */
  function parallax() {
    var g = window.gsap, st = window.ScrollTrigger;
    if (!g || !st || rustig() || !html.classList.contains("fx-motion")) return;
    g.registerPlugin(st);
    document.querySelectorAll("[data-sb-parallax]").forEach(function (foto) {
      g.fromTo(foto, { yPercent: -6 }, { yPercent: 6, ease: "none", scrollTrigger: { trigger: foto.parentNode, start: "top bottom", end: "bottom top", scrub: true } });
    });
  }
  if (document.readyState === "complete") parallax(); else window.addEventListener("load", parallax, { once: true });

  /* ---------- begin ---------- */
  function start() {
    if (!heeftOpening || !open) { direct(); return; }
    var direct_open = /^#(aanmelden|aanmelden-formulier|uitnodiging)/.test(location.hash) || html.hasAttribute("data-live") ||
      html.hasAttribute("data-direct-open") || html.classList.contains("inv-embed");
    if (direct_open || gezien() || rustig()) { direct(); return; }
    zetStand(["sb-gate"]);
    vergrendel(true);
    if (video) video.preload = "auto";  // de film moet klaar zijn als de gast tikt
  }
  start();
})();
