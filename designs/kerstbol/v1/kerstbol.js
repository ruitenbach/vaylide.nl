/* Kerstbol v1: de opening van het gesloten kerstcadeau als één scène in de kop.
   Een tik op het cadeau start één video (strik los, lint weg, deksel open, sneeuwbol omhoog, 10 s). Twee soorten fonkelingen: warm goud rond het
   gesloten cadeau en in de eerste fase, en vanaf 6,5 s witgouden kristal rond de sneeuwbol. Na het einde staat de groet in beeld.
   Het script maakt de deeltjes pas aan als ze nodig zijn en ruimt alles op (timers, deeltjes, vergrendeling) bij Opening overslaan, Opnieuw beleven
   en het verlaten van de pagina. Zonder dit script, bij 'minder beweging', bij stilgezette beweging, of als de opening al gezien is, staat het
   eindbeeld met de groet er direct, met een knop om de opening af te spelen. Er is één video; hij wordt hergebruikt voor opnieuw beleven. */
(function () {
  "use strict";
  var hero = document.querySelector("[data-kb]");
  if (!hero) return;
  var html = document.documentElement;
  var q = function (sel) { return hero.querySelector(sel); };
  var video = q("[data-kb-video]"), open = q("[data-kb-open]"), fallback = q("[data-kb-fallback]"), overslaan = q("[data-kb-skip]");
  var ambient = q("[data-kb-ambient]"), replay = q("[data-kb-replay]"), sparkles = q("[data-kb-sparkles]"), status = q("[data-kb-status]"), scroll = q("[data-kb-scroll]");
  var inhoud = document.querySelector(".kb-body");
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var heeftOpening = hero.hasAttribute("data-kb-opening") && !!open;
  var opslagSleutel = "vierlief-open:" + location.pathname;  // dezelfde sleutel als invite.js: één keer per sessie
  var FASE_TWEE = 6.5;                                        // seconden in de video waarop het goud overgaat in kristal
  var timers = [], bezig = false, afgelopen = false, afgespeeld = false, geblokkeerd = false, faseTwee = false, waarnemer = null;

  function rustig() { return reduceQuery.matches || html.classList.contains("fx-paused"); }
  function later(fn, ms) { timers.push(window.setTimeout(fn, ms)); }
  function stopTimers() { timers.forEach(window.clearTimeout); timers = []; }
  function zeg(tekst) { if (status) status.textContent = tekst; }
  function vergrendel(aan) {
    html.classList.toggle("kb-bezig", aan);
    if (inhoud) { if ("inert" in inhoud) inhoud.inert = aan; else if (aan) inhoud.setAttribute("aria-hidden", "true"); else inhoud.removeAttribute("aria-hidden"); }
  }
  function gezien() { try { return !!window.sessionStorage.getItem(opslagSleutel); } catch (e) { return false; } }
  function onthoud() { if (html.classList.contains("inv-embed")) return; try { window.sessionStorage.setItem(opslagSleutel, "1"); } catch (e) { /* privémodus */ } }
  function knopTekst() {
    if (!replay) return;
    replay.hidden = false;
    replay.textContent = (!heeftOpening || rustig() || geblokkeerd || !afgespeeld) ? "Speel de opening af ▷" : "Opnieuw beleven ↻";
  }

  /* ---------- de gloed naast de video (alleen op een breder scherm) ---------- */
  // De video is 9:16. Op een breed scherm staat hij over de volle hoogte; aan weerszijden tekent dit script een zeer klein, vervaagd beeld van de video zelf
  // (32 x 57 pixels, ongeveer 15 keer per seconde, alleen zolang de video speelt). Op een telefoon is het canvas verborgen en gebeurt er niets.
  var actx = ambient && ambient.getContext ? ambient.getContext("2d") : null, ambientBron = "poster", laatsteTeken = 0;
  function ambientZichtbaar() { return !!actx && window.getComputedStyle(ambient).display !== "none"; }
  function teken(bron) { try { actx.drawImage(bron, 0, 0, 32, 57); } catch (e) { /* nog geen beeld */ } }
  function tekenBeeld(naam, url) {
    ambientBron = naam;
    if (!ambientZichtbaar() || !url) return;
    var im = new Image();
    im.onload = function () { if (ambientBron === naam) teken(im); };
    im.src = url;
  }
  function ambientLus() {
    ambientBron = "video";
    if (!ambientZichtbaar() || !video.requestVideoFrameCallback) return;
    video.requestVideoFrameCallback(function kijk(nu) {
      if (video.paused || video.ended || ambientBron !== "video") return;
      if (nu - laatsteTeken > 60) { teken(video); laatsteTeken = nu; }
      video.requestVideoFrameCallback(kijk);
    });
  }
  function eindUrl() { var i = q(".kb-eindbeeld"); return i ? i.src : ""; }
  if (window.matchMedia) {
    var breed = window.matchMedia("(min-aspect-ratio: 3/5)");
    var herteken = function () {
      if (!breed.matches) return;
      if (ambientBron === "video") teken(video); else tekenBeeld(ambientBron, ambientBron === "eind" ? eindUrl() : video.poster);
    };
    if (breed.addEventListener) breed.addEventListener("change", herteken);
  }

  /* ---------- fonkelingen: 40 gouden, daarna 55 kristallen, alleen zolang ze nodig zijn ---------- */
  function maakGlint(i) {
    var goud = i < 40, j = goud ? i : i - 40, hoek = j * 2.399, rx = goud ? 34 : 28, ry = goud ? 17 : 20;
    var el = document.createElement("i");
    el.className = "kb-glint " + (goud ? "kb-glint--goud" : "kb-glint--kristal" + (i % 4 === 3 ? " kb-glint--ster" : ""));
    var x = 50 + Math.cos(hoek) * rx * (0.65 + (j % 5) * 0.07), y = (goud ? 65 : 43) + Math.sin(hoek) * ry * (0.65 + (j % 7) * 0.04);
    var s = el.style;
    s.setProperty("--x", x + "%"); s.setProperty("--y", y + "%"); s.setProperty("--size", (goud ? 4 + j % 7 : 2 + j % 4) + "px");
    s.setProperty("--duur", (2 + j % 7 * 0.23) + "s"); s.setProperty("--vertraging", (-j % 13 * 0.3) + "s");
    return el;
  }
  function glinten(van, tot) {
    if (!sparkles || rustig()) return;
    var stuk = document.createDocumentFragment();
    for (var i = van; i < tot; i++) stuk.appendChild(maakGlint(i));
    sparkles.appendChild(stuk);
  }
  function wisGlinten() { if (sparkles) sparkles.textContent = ""; }

  /* ---------- video ---------- */
  var geladen = false;
  function laadVoor() {  // alleen als de gast aanstalten maakt (aanraken, focus) en niet bij Data-besparing: dan pas bij de tik
    if (geladen || !video) return;
    var c = navigator.connection;
    if (c && (c.saveData || /(^|-)2g$/.test(c.effectiveType || ""))) return;
    geladen = true; video.preload = "auto";
  }
  function faseTweeStart() {
    if (faseTwee) return;
    faseTwee = true;
    hero.classList.add("kb-afterglow");
    wisGlinten();            // de gouden fonkelingen stoppen hier; geen achterblijvende animaties
    glinten(40, 95);
    later(wisGlinten, 9000); // de kristallen fonkelen tweemaal en worden daarna verwijderd
  }
  function opTijd() {
    if (video.currentTime > FASE_TWEE) faseTweeStart();
    if (!video.requestVideoFrameCallback && ambientBron === "video" && ambientZichtbaar()) teken(video);
  }
  function speel() {  // moet vanuit een tik of toets komen: de afspeelstart hoort bij het gebaar
    stopTimers(); faseTwee = false; hero.classList.remove("kb-afterglow");
    try { video.currentTime = 0; } catch (e) { /* nog geen metadata */ }
    var belofte = video.play();
    var gelukt = function () {
      geblokkeerd = false; afgespeeld = true; bezig = true;
      hero.classList.remove("kb-eind", "kb-finished", "kb-klaar");
      hero.classList.add("kb-playing");
      if (fallback) fallback.hidden = true;
      if (open) open.disabled = true;
      if (replay) replay.hidden = true;
      zeg("De opening speelt.");
      ambientLus();
    };
    var mislukt = function () {
      geblokkeerd = true; bezig = false;
      if (fallback) { fallback.hidden = false; fallback.focus({ preventScroll: true }); }
      zeg("De video kon niet vanzelf starten. Tik op Speel de opening af.");
      knopTekst();
    };
    if (belofte && belofte.then) belofte.then(gelukt, mislukt); else gelukt();
  }
  if (video) {
    video.addEventListener("timeupdate", opTijd);
    video.addEventListener("ended", einde);
    video.addEventListener("error", function () {
      bezig = false; geblokkeerd = true;
      if (fallback) { fallback.hidden = false; fallback.textContent = "Video laden mislukt — probeer opnieuw"; }
      zeg("De video kon niet worden geladen.");
    });
  }

  /* ---------- standen ---------- */
  function toonEind(metFocus) {  // het eindbeeld met de groet, zonder te wachten op de video
    stopTimers(); wisGlinten();
    if (video) { video.pause(); try { video.currentTime = 0; } catch (e) { /* geen metadata */ } }
    hero.classList.remove("kb-playing", "kb-afterglow");
    hero.classList.add("kb-eind", "kb-finished", "kb-klaar");
    afgelopen = true; bezig = false; faseTwee = false;
    if (open) open.disabled = true;
    if (fallback) fallback.hidden = true;
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    vergrendel(false);
    knopTekst();
    tekenBeeld("eind", eindUrl());
    if (metFocus && scroll) window.requestAnimationFrame(function () { scroll.focus({ preventScroll: true }); });
  }
  function einde() {
    if (video) video.pause();
    hero.classList.remove("kb-playing");
    hero.classList.add("kb-finished", "kb-klaar");
    afgelopen = true; bezig = false;
    wisGlinten();
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    if (ambientZichtbaar()) { teken(video); ambientBron = "eind"; }
    onthoud(); vergrendel(false); knopTekst();
    zeg("De kerstkaart is geopend. Scroll verder voor de rest van de kaart.");
    if (scroll) scroll.focus({ preventScroll: true });
  }
  function begin() {
    if (!open || open.disabled || afgelopen) return;
    if (rustig()) { overslaanNu(); return; }
    speel();
    if ("MutationObserver" in window) {  // de gast zet de beweging stil tijdens de opening
      waarnemer = new MutationObserver(function () { if (bezig && rustig()) overslaanNu(); });
      waarnemer.observe(html, { attributes: true, attributeFilter: ["class"] });
    }
  }
  function overslaanNu() {
    if (afgelopen) return;
    afgespeeld = false;
    toonEind(true); onthoud();
    zeg("Opening overgeslagen. De kerstkaart is geopend. Scroll verder voor de rest van de kaart.");
  }
  function opnieuw() {
    stopTimers(); wisGlinten();
    video.pause(); try { video.currentTime = 0; } catch (e) { /* geen metadata */ }
    hero.classList.add("kb-resetting");
    hero.classList.remove("kb-playing", "kb-afterglow", "kb-finished", "kb-klaar", "kb-eind");
    window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { hero.classList.remove("kb-resetting"); }); });
    bezig = false; afgelopen = false; afgespeeld = false; geblokkeerd = false; faseTwee = false;
    open.disabled = false; if (replay) replay.hidden = true; if (fallback) fallback.hidden = true;
    vergrendel(true);
    window.scrollTo({ top: 0, behavior: "instant" });
    glinten(0, 40);
    tekenBeeld("poster", video.poster);
    open.focus({ preventScroll: true });
    zeg("Het cadeau is weer dicht. Tik erop om het te openen.");
  }

  if (open) { open.addEventListener("click", begin); ["pointerdown", "focus", "touchstart"].forEach(function (naam) { open.addEventListener(naam, laadVoor, { once: true, passive: true }); }); }
  if (fallback) fallback.addEventListener("click", speel);
  if (overslaan) overslaan.addEventListener("click", overslaanNu);
  if (replay) replay.addEventListener("click", function () {
    if (heeftOpening && !rustig() && afgespeeld && !geblokkeerd) opnieuw(); else speel();
  });
  var skipLink = document.querySelector(".skip-link");
  if (skipLink) skipLink.addEventListener("click", function () { if (bezig || (heeftOpening && !afgelopen)) overslaanNu(); });
  window.addEventListener("pagehide", function () { stopTimers(); wisGlinten(); });

  /* ---------- de kaart eronder: sfeer en glans alleen in beeld ---------- */
  var banden = document.querySelectorAll(".kb-sec");
  if ("IntersectionObserver" in window && banden.length) {
    var kijker = new IntersectionObserver(function (items) {
      items.forEach(function (item) { item.target.classList.toggle("kb-zichtbaar", item.isIntersecting); });
    }, { rootMargin: "10% 0px 10% 0px" });
    banden.forEach(function (band) { kijker.observe(band); });
  } else {
    banden.forEach(function (band) { band.classList.add("kb-zichtbaar"); });
  }

  /* ---------- begin ---------- */
  function start() {
    if (!heeftOpening) { toonEind(false); hero.classList.add("kb-klaar"); knopTekst(); return; }
    var direct = /^#(aanmelden|aanmelden-formulier|uitnodiging)/.test(location.hash) || html.hasAttribute("data-live") ||
      html.hasAttribute("data-direct-open") || html.classList.contains("inv-embed");
    if (direct || gezien() || rustig()) { toonEind(false); return; }
    vergrendel(true);
    glinten(0, 40);          // warme gouden fonkelingen rond het gesloten cadeau
    tekenBeeld("poster", video.poster);
    if ("requestIdleCallback" in window) window.requestIdleCallback(laadVoor, { timeout: 4000 }); else window.setTimeout(laadVoor, 2500);
  }
  start();
})();
