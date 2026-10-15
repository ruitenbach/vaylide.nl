/* Zwanenhart v1: de opening (envelop, licht, zwanen, namen) als één scène in de kop.
   Volgorde: eerste beeld van de film (de gesloten envelop met het gouden zegel) als poster met de knop "Tik om de envelop te openen" → de gast tikt → de film speelt
   (6,5 s: het zegel gloeit, de envelop opent, uit het licht verschijnen twee zwanen die naar elkaar toe buigen tot hun snavelpunten elkaar net raken) → op 5,8 s,
   als de overgang bijna klaar is, verschijnen de namen
   en de datum en komt de pagina vrij → aan het eind blijft het laatste beeld staan. De film speelt alleen na een tik (dus ook als de browser automatisch afspelen
   blokkeert) en nooit vanzelf opnieuw. Terugval: weigert de browser het afspelen, laadt de film niet of start hij niet binnen enkele seconden, dan staat direct het
   eindbeeld met de namen en is de pagina bruikbaar. Zonder dit script, bij 'minder beweging', bij stilgezette beweging of als de opening al gezien is, staat direct
   het eindbeeld met de namen. Als de namen verschijnen, volgt de knal uit het manifest (vonken en goud). Opbouw gelijk aan witte-roos.js. */
(function () {
  "use strict";
  var hero = document.querySelector("[data-zh]");
  if (!hero) return;
  var html = document.documentElement;
  var q = function (sel) { return hero.querySelector(sel); };
  var video = q("[data-zh-video]"), open = q("[data-zh-open]"), overslaan = q("[data-zh-skip]"), bekijk = q("[data-zh-bekijk]"), nogmaals = q("[data-zh-again]");
  var status = q("[data-zh-status]");
  var inhoud = document.querySelector(".zh-body");
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var heeftOpening = hero.hasAttribute("data-zh-opening");
  var opslagSleutel = "vierlief-open:" + location.pathname;  // dezelfde sleutel als invite.js: één keer per sessie
  var TEKST_OP = 5.8;                                          // seconde in de film waarop de namen verschijnen (de zwanen zijn bijna bij elkaar; de film stopt op 6,5 s, als de snavels elkaar raken)
  var STARTTIJD = 6000;                                        // zo lang (ms) mag de film na een tik nodig hebben om te starten; daarna het eindbeeld
  var STAND = ["zh-gate", "zh-laadt", "zh-speelt", "zh-tekst", "zh-klaar"];
  var bezig = false, afgelopen = false, waarnemer = null, wachter = null;

  function rustig() { return reduceQuery.matches || html.classList.contains("fx-paused"); }
  function zeg(tekst) { if (status) status.textContent = tekst; }
  function vergrendel(aan) {
    html.classList.toggle("zh-bezig", aan);
    if (inhoud) { if ("inert" in inhoud) inhoud.inert = aan; else if (aan) inhoud.setAttribute("aria-hidden", "true"); else inhoud.removeAttribute("aria-hidden"); }
  }
  function gezien() { try { return !!window.sessionStorage.getItem(opslagSleutel); } catch (e) { return false; } }
  function onthoud() { if (html.classList.contains("inv-embed")) return; try { window.sessionStorage.setItem(opslagSleutel, "1"); } catch (e) { /* privémodus */ } }
  function zetStand(namen) { STAND.forEach(function (n) { hero.classList.toggle(n, namen.indexOf(n) >= 0); }); }
  function stopWachter() { if (wachter) { window.clearTimeout(wachter); wachter = null; } }

  function rewind() { if (!video) return; video.pause(); try { video.currentTime = 0; } catch (e) { /* nog geen metadata */ } }

  function afronden(metFocus, melding) {
    afgelopen = true; bezig = false;
    stopWachter();
    zetStand(["zh-klaar"]);
    onthoud();
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    zeg(melding || "De uitnodiging is geopend. Scroll voor het programma en het aanmelden.");
    window.requestAnimationFrame(function () {
      vergrendel(false);
      if (metFocus && bekijk) window.requestAnimationFrame(function () { bekijk.focus({ preventScroll: true }); });
    });
  }
  function direct() {  // eindbeeld zonder opening
    zetStand(["zh-klaar"]);
    afgelopen = true; bezig = false;
    vergrendel(false);
  }
  function vonken() {  // de knal uit het manifest (effects.js): een regen van vonken en goud op het moment dat de namen verschijnen
    if (rustig() || typeof window.CustomEvent !== "function") return;
    document.dispatchEvent(new CustomEvent("invite:opening"));
  }
  function tekstTonen() {  // de namen komen in beeld en de pagina komt vrij terwijl de zwanen de laatste centimeters naar elkaar toe buigen
    if (!bezig || hero.classList.contains("zh-tekst")) return;
    hero.classList.add("zh-tekst");
    vonken();
    onthoud();
    vergrendel(false);
    zeg("De uitnodiging is geopend. Scroll voor het programma en het aanmelden.");
  }
  function terugval() {  // de film kan niet spelen: direct het eindbeeld, de uitnodiging blijft volledig bruikbaar
    if (!bezig) return;
    rewind();
    afronden(true, "De film kan hier niet worden afgespeeld. De uitnodiging is geopend.");
  }

  function speel() {
    if (!video) { afronden(false); return; }
    rewind();
    zetStand(["zh-laadt"]);
    stopWachter();
    wachter = window.setTimeout(terugval, STARTTIJD);
    var belofte;
    try { belofte = video.play(); } catch (e) { terugval(); return; }
    if (belofte && belofte.then) belofte.then(null, terugval);
  }
  if (video) {
    video.addEventListener("playing", function () { if (!bezig) return; stopWachter(); hero.classList.remove("zh-laadt"); hero.classList.add("zh-speelt"); });
    video.addEventListener("timeupdate", function () { if (bezig && video.currentTime >= TEKST_OP) tekstTonen(); });
    video.addEventListener("ended", function () { video.pause(); if (bezig) { tekstTonen(); afronden(true); } else zetStand(["zh-klaar"]); });  // de film is kort: kwam de laatste timeupdate vóór TEKST_OP, dan alsnog namen en vonken
    video.addEventListener("error", terugval);
    var bron = video.querySelector("source");
    if (bron) bron.addEventListener("error", terugval);
  }

  function begin() {
    if (bezig || afgelopen) return;
    if (rustig()) { overslaanNu(); return; }
    bezig = true;
    if (window.scrollY > 0) window.scrollTo({ top: 0, behavior: "instant" });
    if (open) open.disabled = true;
    zeg("De opening speelt.");
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
    if (open) open.disabled = true;
    afronden(true, "Opening overgeslagen. De uitnodiging is geopend. Scroll voor het programma en het aanmelden.");
  }
  function opnieuw() {
    if (rustig()) { zeg("De beweging staat uit. Zet de beweging aan om de opening af te spelen."); return; }
    rewind();
    bezig = true; afgelopen = false;
    hero.classList.remove("zh-tekst");
    window.scrollTo(0, 0);
    vergrendel(true);
    if (overslaan) overslaan.focus({ preventScroll: true });
    zeg("De opening speelt opnieuw.");
    speel();
  }

  if (open) open.addEventListener("click", begin);
  if (overslaan) overslaan.addEventListener("click", overslaanNu);
  if (nogmaals) nogmaals.addEventListener("click", opnieuw);
  if (bekijk) bekijk.addEventListener("click", function () {
    var doel = document.getElementById("zh-verder");
    if (doel) doel.scrollIntoView({ behavior: rustig() ? "auto" : "smooth", block: "start" });
  });
  var skipLink = document.querySelector(".skip-link");
  if (skipLink) skipLink.addEventListener("click", function () { if (bezig) overslaanNu(); });
  window.addEventListener("pagehide", function () { if (video) video.pause(); });

  /* ---------- begin ---------- */
  function start() {
    if (!heeftOpening || !open) { direct(); return; }
    var direct_open = /^#(aanmelden|aanmelden-formulier|uitnodiging)/.test(location.hash) || html.hasAttribute("data-live") ||
      html.hasAttribute("data-direct-open") || html.classList.contains("inv-embed");
    if (direct_open || gezien() || rustig()) { direct(); return; }
    zetStand(["zh-gate"]);
    vergrendel(true);
    if (video) video.preload = "auto";  // de film moet klaar zijn als de gast tikt
  }
  start();
})();
