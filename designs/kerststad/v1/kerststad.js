/* Kerststad v1: de opening van de peperkoekstad als één scène in de kop.
   Het eerste beeld is extreem dichtbij: de ronde gouden badge met de officiële VAYLIDE-V. De V is het klikpunt (een zachte lichtring en de tekst "Tik op de V om te openen").
   Eén tik speelt de volledige video één keer, van 0 s tot het einde. Daarna valt de kaart niet stil: de laatste scène loopt door als levende eindloop, van LUS_START (16,0 s) tot het einde en weer
   terug, met sneeuw, twinkelende lichtjes en bewegende figuurtjes uit de video zelf. De opening start daarna nooit meer vanzelf; alleen "Opnieuw beleven" (een tik) begint opnieuw.
   De sprong aan het eind van de lus is een kruisverloop: een stilstaand beeld van het laatste frame wordt in 1,4 s doorzichtig terwijl de video vanaf LUS_START verder speelt. De video zelf wordt
   niet bewerkt. Er is één video; de lus pauzeert buiten beeld en in een verborgen tabblad. Zonder dit script, bij 'minder beweging', bij stilgezette beweging of in de Studio staat het eindbeeld met
   de groet er direct, met een knop om de opening af te spelen (eenmalig, zonder lus). */
(function () {
  "use strict";
  var hero = document.querySelector("[data-ks]");
  if (!hero) return;
  var html = document.documentElement;
  var q = function (sel) { return hero.querySelector(sel); };
  var video = q("[data-ks-video]"), open = q("[data-ks-open]"), fallback = q("[data-ks-fallback]"), overslaan = q("[data-ks-skip]");
  var ambient = q("[data-ks-ambient]"), spiegel = q("[data-ks-spiegel]"), replay = q("[data-ks-replay]"), status = q("[data-ks-status]"), scroll = q("[data-ks-scroll]");
  var inhoud = document.querySelector(".ks-body");
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var heeftOpening = hero.hasAttribute("data-ks-opening") && !!open;
  var opslagSleutel = "vierlief-open:" + location.pathname;  // dezelfde sleutel als invite.js: één keer per sessie
  var LUS_START = parseFloat(video && video.getAttribute("data-ks-lus")) || 16;   // seconde in de video waar de levende eindloop begint
  var laadFout = false, bezig = false, afgelopen = false, afgespeeld = false, geblokkeerd = false, lusAan = false, hervatNaRust = false, inBeeld = true, waarnemer = null;

  function rustig() { return reduceQuery.matches || html.classList.contains("fx-paused"); }
  function zeg(tekst) { if (status) status.textContent = tekst; }
  function vergrendel(aan) {
    html.classList.toggle("ks-bezig", aan);
    if (inhoud) { if ("inert" in inhoud) inhoud.inert = aan; else if (aan) inhoud.setAttribute("aria-hidden", "true"); else inhoud.removeAttribute("aria-hidden"); }
  }
  function gezien() { try { return !!window.sessionStorage.getItem(opslagSleutel); } catch (e) { return false; } }
  function onthoud() { if (html.classList.contains("inv-embed")) return; try { window.sessionStorage.setItem(opslagSleutel, "1"); } catch (e) { /* privémodus */ } }
  function knopTekst() {
    if (!replay) return;
    replay.hidden = false;
    replay.textContent = (!heeftOpening || rustig() || geblokkeerd || !afgespeeld) ? "Speel de opening af ▷" : "Opnieuw beleven ↻";
  }
  function zetSprong(aan) { if (spiegel) spiegel.classList.toggle("ks-aan", aan); }

  /* ---------- de gloed naast de video (alleen op een breder scherm) ---------- */
  // De video is 9:16. Op een breed scherm staat hij over de volle hoogte; aan weerszijden tekent dit script een zeer klein, vervaagd beeld van de video zelf
  // (32 x 57 pixels, ongeveer 15 keer per seconde, alleen zolang de video speelt). Op een telefoon is het canvas verborgen en gebeurt er niets.
  var actx = ambient && ambient.getContext ? ambient.getContext("2d") : null, ambientBron = "poster", laatsteTeken = 0, ambientBezig = false;
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
    if (ambientBezig || !ambientZichtbaar() || !video.requestVideoFrameCallback) return;
    ambientBezig = true;
    video.requestVideoFrameCallback(function kijk(nu) {
      if (video.paused || video.ended || ambientBron !== "video") { ambientBezig = false; return; }
      if (nu - laatsteTeken > 60) { teken(video); laatsteTeken = nu; }
      video.requestVideoFrameCallback(kijk);
    });
  }
  function eindUrl() { var i = q(".ks-eindbeeld"); return i ? i.src : ""; }
  if (window.matchMedia) {
    var breed = window.matchMedia("(min-aspect-ratio: 3/5)");
    var herteken = function () {
      if (!breed.matches) return;
      if (ambientBron === "video") teken(video); else tekenBeeld(ambientBron, ambientBron === "eind" ? eindUrl() : video.poster);
    };
    if (breed.addEventListener) breed.addEventListener("change", herteken);
  }

  /* ---------- video ---------- */
  var geladen = false;
  function laadVoor() {  // alleen als de gast aanstalten maakt (aanraken, focus) en niet bij Data-besparing: dan pas bij de tik
    if (geladen || !video) return;
    var c = navigator.connection;
    if (c && (c.saveData || /(^|-)2g$/.test(c.effectiveType || ""))) return;
    geladen = true; video.preload = "auto";
  }
  function zoekNaar(t) { try { video.currentTime = t; } catch (e) { /* nog geen metadata */ } }
  function afspelen() {
    var belofte = video.play();
    return belofte && belofte.then ? belofte : Promise.resolve();
  }

  function kanZoeken() {  // een server zonder Range-verzoeken geeft een video die niet kan springen: dan geen eindloop (anders begint hij weer bij 0)
    try { var z = video.seekable; return z.length > 0 && z.end(z.length - 1) >= LUS_START + 0.5; } catch (e) { return false; }
  }
  function springNaarLus(klaar) {  // naar LUS_START springen; lukt dat niet binnen 6 s, dan het stilstaande eindbeeld
    var wacht = window.setTimeout(function () { video.removeEventListener("seeked", gedaan); toonStatisch(false); }, 6000);
    var gedaan = function () {
      video.removeEventListener("seeked", gedaan); window.clearTimeout(wacht);
      if (Math.abs(video.currentTime - LUS_START) > 1) { toonStatisch(false); return; }
      klaar();
    };
    video.addEventListener("seeked", gedaan);
    zoekNaar(LUS_START);
  }

  // De levende eindloop: aan het eind van de video het laatste beeld stilzetten, naar LUS_START springen en dat beeld in 1,4 s laten verdwijnen.
  function spring() {
    if (!lusAan) return;
    if (!kanZoeken()) { toonStatisch(false); return; }
    var w = spiegel ? spiegel.width : 0, h = spiegel ? spiegel.height : 0;
    if (spiegel) { try { spiegel.getContext("2d").drawImage(video, 0, 0, w, h); zetSprong(true); } catch (e) { /* geen beeld: dan zonder kruisverloop */ } }
    springNaarLus(function () {
      afspelen().then(function () {
        window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { zetSprong(false); }); });
      }, function () { toonStatisch(false); });
    });
  }

  function naarLus(vanaf) {  // de scène staat open; de video loopt vanaf LUS_START door (vanaf=true: eerst naar die plek springen)
    lusAan = true; afgelopen = true; bezig = false;
    hervatNaRust = false;
    hero.classList.remove("ks-playing");
    hero.classList.add("ks-finished", "ks-klaar", "ks-lus");
    if (open) open.disabled = true;
    if (fallback) fallback.hidden = true;
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    vergrendel(false);
    knopTekst();
    if (vanaf) {
      hero.classList.add("ks-eind");     // het eindbeeld blijft staan tot de video speelt en lost dan op in de eindloop
      springNaarLus(function () { afspelen().then(function () { hero.classList.remove("ks-eind"); }, function () { toonStatisch(false); }); });
    }
  }

  function einde() {  // de volledige video is één keer afgespeeld
    afgelopen = true; bezig = false;
    onthoud();
    if (rustig()) { toonStatisch(true); return; }
    naarLus(false);
    spring();
    zeg("De kerstkaart is geopend. Scroll verder voor de rest van de kaart.");
    if (scroll) scroll.focus({ preventScroll: true });
  }

  function speel() {  // moet vanuit een tik of toets komen: de afspeelstart hoort bij het gebaar
    lusAan = false; zetSprong(false);
    hero.classList.remove("ks-eind", "ks-finished", "ks-klaar", "ks-lus");
    zoekNaar(0);
    afspelen().then(function () {
      geblokkeerd = false; afgespeeld = true; bezig = true; afgelopen = false;
      hero.classList.add("ks-playing");
      if (fallback) fallback.hidden = true;
      if (open) open.disabled = true;
      if (replay) replay.hidden = true;
      vergrendel(true);
      zeg("De opening speelt.");
    }, function () {
      geblokkeerd = true; bezig = false;
      if (fallback) { fallback.hidden = false; fallback.focus({ preventScroll: true }); }
      zeg("De video kon niet vanzelf starten. Tik op Speel de opening af.");
      knopTekst();
    });
  }
  if (video) {
    video.addEventListener("playing", ambientLus);
    video.addEventListener("ended", einde);
    video.addEventListener("error", function () {
      bezig = false; geblokkeerd = true; laadFout = true;
      toonStatisch(false);
      if (fallback) { fallback.hidden = false; fallback.textContent = "Video laden mislukt — probeer opnieuw"; }
      zeg("De video kon niet worden geladen.");
    });
  }

  /* ---------- standen ---------- */
  function toonStatisch(metFocus) {  // het eindbeeld met de groet, zonder te wachten op de video
    if (video) { video.pause(); zoekNaar(0); }
    zetSprong(false);
    lusAan = false;
    hero.classList.remove("ks-playing", "ks-lus");
    hero.classList.add("ks-eind", "ks-finished", "ks-klaar");
    afgelopen = true; bezig = false;
    if (open) open.disabled = true;
    if (fallback && !laadFout) fallback.hidden = true;
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    vergrendel(false);
    knopTekst();
    tekenBeeld("eind", eindUrl());
    if (metFocus && scroll) window.requestAnimationFrame(function () { scroll.focus({ preventScroll: true }); });
  }
  function overslaanNu() {  // de gast slaat de opening over: direct naar de levende eindloop (de tik is het gebaar dat afspelen toestaat)
    if (afgelopen) return;
    afgespeeld = false;
    onthoud();
    if (rustig()) toonStatisch(true); else naarLus(true);
    zeg("Opening overgeslagen. De kerstkaart is geopend. Scroll verder voor de rest van de kaart.");
    if (scroll) window.requestAnimationFrame(function () { scroll.focus({ preventScroll: true }); });
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
  function opnieuw() {  // terug naar de gesloten badge: de gast moet opnieuw tikken
    video.pause(); zoekNaar(0); zetSprong(false);
    hero.classList.add("ks-resetting");
    hero.classList.remove("ks-playing", "ks-finished", "ks-klaar", "ks-eind", "ks-lus");
    window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { hero.classList.remove("ks-resetting"); }); });
    bezig = false; afgelopen = false; afgespeeld = false; geblokkeerd = false; lusAan = false;
    open.disabled = false; if (replay) replay.hidden = true; if (fallback) fallback.hidden = true;
    vergrendel(true);
    window.scrollTo({ top: 0, behavior: "instant" });
    tekenBeeld("poster", video.poster);
    open.focus({ preventScroll: true });
    zeg("De kerststad is weer dicht. Tik op de V om hem te openen.");
  }

  if (open) { open.addEventListener("click", begin); ["pointerdown", "focus", "touchstart"].forEach(function (naam) { open.addEventListener(naam, laadVoor, { once: true, passive: true }); }); }
  if (fallback) fallback.addEventListener("click", speel);
  if (overslaan) overslaan.addEventListener("click", overslaanNu);
  if (replay) replay.addEventListener("click", function () {
    if (heeftOpening && !rustig() && afgespeeld && !geblokkeerd) opnieuw(); else speel();
  });
  var skipLink = document.querySelector(".skip-link");
  if (skipLink) skipLink.addEventListener("click", function () { if (bezig || (heeftOpening && !afgelopen)) overslaanNu(); });

  /* ---------- de eindloop pauzeert buiten beeld, in een verborgen tabblad en bij stilgezette beweging ---------- */
  function hervat() { if (lusAan && inBeeld && !document.hidden && !rustig() && video.paused && !video.seeking) afspelen().then(null, function () { toonStatisch(false); }); }
  function pauzeer() { if (lusAan && !video.paused) video.pause(); }
  document.addEventListener("visibilitychange", function () { if (document.hidden) pauzeer(); else hervat(); });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (items) {
      inBeeld = items[items.length - 1].isIntersecting;
      if (inBeeld) hervat(); else pauzeer();
    }, { threshold: 0.05 }).observe(hero);
  }
  if ("MutationObserver" in window) {   // de gast zet de beweging stil of weer aan terwijl de eindloop draait
    new MutationObserver(function () {
      if (rustig() && lusAan) { hervatNaRust = true; toonStatisch(false); }
      else if (!rustig() && hervatNaRust && !reduceQuery.matches) { hervatNaRust = false; naarLus(true); }
    }).observe(html, { attributes: true, attributeFilter: ["class"] });
  }
  window.addEventListener("pagehide", function () { if (video) video.pause(); });

  /* ---------- de kaart eronder: sfeer en glans alleen in beeld ---------- */
  var banden = document.querySelectorAll(".ks-sec");
  if ("IntersectionObserver" in window && banden.length) {
    var kijker = new IntersectionObserver(function (items) {
      items.forEach(function (item) { item.target.classList.toggle("ks-zichtbaar", item.isIntersecting); });
    }, { rootMargin: "10% 0px 10% 0px" });
    banden.forEach(function (band) { kijker.observe(band); });
  } else {
    banden.forEach(function (band) { band.classList.add("ks-zichtbaar"); });
  }

  /* ---------- begin ---------- */
  function start() {
    var live = html.getAttribute("data-live");
    // Net als Kerstbol: het voorbeeldframe op de ontwerppagina en de live kaart bij Stijl en Envelop laten de dichte opening zien en klikbaar; de live kaart bij de andere stappen en de bedankpagina
    // (data-direct-open) tonen het eindbeeld zonder beweging, zodat de Studio rustig blijft.
    var studioStil = html.hasAttribute("data-live") && ["stijl", "envelop"].indexOf(live) < 0;
    var direct = /^#(aanmelden|aanmelden-formulier|uitnodiging)/.test(location.hash) || html.hasAttribute("data-direct-open");
    if (!heeftOpening) {                 // zonder opening: direct de levende eindloop (of het eindbeeld als automatisch starten niet mag)
      if (studioStil || rustig()) { toonStatisch(false); return; }
      toonStatisch(false); laadVoor(); video.preload = "auto";
      naarLus(true);
      return;
    }
    if (studioStil || direct || rustig()) { toonStatisch(false); return; }
    if (!html.hasAttribute("data-live") && gezien()) {   // al gezien in deze sessie: de opening start niet opnieuw, de levende eindloop wel
      video.preload = "auto"; geladen = true;
      toonStatisch(false);
      var c = navigator.connection;
      if (!(c && c.saveData)) naarLus(true);
      return;
    }
    vergrendel(true);
    tekenBeeld("poster", video.poster);
    if ("requestIdleCallback" in window) window.requestIdleCallback(laadVoor, { timeout: 4000 }); else window.setTimeout(laadVoor, 2500);
  }
  start();
})();
