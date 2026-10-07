/* Kerststad v1: de opening van de peperkoekstad als één scène in de kop.
   Het eerste beeld is extreem dichtbij: de ronde gouden badge met de officiële VAYLIDE-V. De V is het klikpunt (een zachte lichtring en de tekst "Tik op de V om te openen").
   Eén tik speelt de volledige video één keer, van 0 s tot het einde. Daarna valt de kaart niet stil: de laatste scène loopt door als levende eindloop, van lusStart (16,0 s) tot het einde en weer
   terug, met sneeuw, twinkelende lichtjes en bewegende figuurtjes uit de video zelf. De opening start daarna nooit meer vanzelf; alleen "Opnieuw beleven" (een tik) begint opnieuw.
   De sprong aan het eind van de lus is een kruisverloop: een stilstaand beeld van het laatste frame wordt in 1,4 s doorzichtig terwijl de video vanaf lusStart verder speelt. De video zelf wordt
   niet bewerkt. Er is één video; de lus pauzeert buiten beeld en in een verborgen tabblad. Zonder dit script, bij 'minder beweging', bij stilgezette beweging of in de Studio staat het eindbeeld met
   de groet er direct, met een knop om de opening af te spelen (eenmalig, zonder lus). */
(function () {
  "use strict";
  var hero = document.querySelector("[data-ks]");
  if (!hero) return;
  var html = document.documentElement;
  var q = function (sel) { return hero.querySelector(sel); };
  var video = q("[data-ks-video]"), open = q("[data-ks-open]"), fallback = q("[data-ks-fallback]"), overslaan = q("[data-ks-skip]");
  var spiegel = q("[data-ks-spiegel]"), replay = q("[data-ks-replay]"), status = q("[data-ks-status]"), scroll = q("[data-ks-scroll]");
  var inhoud = document.querySelector(".ks-body");
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var heeftOpening = hero.hasAttribute("data-ks-opening") && !!open;
  var opslagSleutel = "vierlief-open:" + location.pathname;  // dezelfde sleutel als invite.js: één keer per sessie
  var lusStart = parseFloat(video && video.getAttribute("data-ks-lus")) || 16;    // seconde in de gekozen video waar de levende eindloop begint (per bron anders: data-ks-lus / data-ks-lus-desktop)
  var breedQuery = window.matchMedia ? window.matchMedia("(min-aspect-ratio: 6/5)") : { matches: false };
  var mobielBron = video && video.querySelector("source") ? video.querySelector("source").getAttribute("src") : "";
  var formaat = "smal";
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


  /* ---------- video ---------- */
  var geladen = false;
  function laadVoor() {  // alleen als de gast aanstalten maakt (aanraken, focus) en niet bij Data-besparing: dan pas bij de tik
    if (geladen || !video) return;
    var c = navigator.connection;
    if (c && (c.saveData || /(^|-)2g$/.test(c.effectiveType || ""))) return;
    geladen = true; video.preload = "auto";
  }
  // Twee bronnen: staand 9:16 (telefoon, staande tablet) en liggend 16:9 (brede schermen). De bron wordt gekozen vóór het afspelen begint en blijft daarna staan: tijdens de opening of de
  // eindloop wisselt er nooit van bron, ook niet als het scherm draait of het venster verandert. Pas bij een nieuwe start (tik, overslaan, opnieuw beleven) kan een andere bron worden gekozen.
  function kiesBron() {
    if (!video || bezig || lusAan) return;
    var desktop = video.getAttribute("data-ks-bron-desktop");
    var nieuw = breedQuery.matches && desktop ? "breed" : "smal";
    if (nieuw === formaat) return;
    formaat = nieuw;
    hero.setAttribute("data-ks-formaat", nieuw);
    lusStart = parseFloat(video.getAttribute(nieuw === "breed" ? "data-ks-lus-desktop" : "data-ks-lus")) || 16;
    video.setAttribute("src", nieuw === "breed" ? desktop : mobielBron);
  }
  if (breedQuery.addEventListener) breedQuery.addEventListener("change", function () { if (!bezig && !lusAan && !afgelopen) kiesBron(); });

  function zoekNaar(t) { try { video.currentTime = t; } catch (e) { /* nog geen metadata */ } }
  function afspelen() {
    var belofte = video.play();
    return belofte && belofte.then ? belofte : Promise.resolve();
  }

  function kanZoeken() {  // een server zonder Range-verzoeken geeft een video die niet kan springen: dan geen eindloop (anders begint hij weer bij 0)
    try { var z = video.seekable; return z.length > 0 && z.end(z.length - 1) >= lusStart + 0.5; } catch (e) { return false; }
  }
  function springNaarLus(klaar) {  // naar lusStart springen; lukt dat niet binnen 6 s, dan het stilstaande eindbeeld
    var wacht = window.setTimeout(function () { video.removeEventListener("seeked", gedaan); toonStatisch(false); }, 6000);
    var gedaan = function () {
      video.removeEventListener("seeked", gedaan); window.clearTimeout(wacht);
      if (Math.abs(video.currentTime - lusStart) > 1) { toonStatisch(false); return; }
      klaar();
    };
    video.addEventListener("seeked", gedaan);
    zoekNaar(lusStart);
  }

  // De levende eindloop: aan het eind van de video het laatste beeld stilzetten, naar lusStart springen en dat beeld in 1,4 s laten verdwijnen.
  function spring() {
    if (!lusAan) return;
    if (!kanZoeken()) { toonStatisch(false); return; }
    if (spiegel && video.videoWidth) {   // het stilstaande beeld krijgt de beeldverhouding van de gekozen bron (staand of liggend), anders zou het scheef staan
      var schaal = Math.min(1, 960 / Math.max(video.videoWidth, video.videoHeight));
      spiegel.width = Math.round(video.videoWidth * schaal); spiegel.height = Math.round(video.videoHeight * schaal);
      try { spiegel.getContext("2d").drawImage(video, 0, 0, spiegel.width, spiegel.height); zetSprong(true); } catch (e) { /* geen beeld: dan zonder kruisverloop */ }
    }
    springNaarLus(function () {
      afspelen().then(function () {
        window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { zetSprong(false); }); });
      }, function () { toonStatisch(false); });
    });
  }

  function naarLus(vanaf) {  // de scène staat open; de video loopt vanaf lusStart door (vanaf=true: eerst naar die plek springen)
    if (vanaf) kiesBron();
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
    lusAan = false; zetSprong(false); kiesBron();
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
    lusAan = false; bezig = false; kiesBron();
    video.pause(); zoekNaar(0); zetSprong(false);
    hero.classList.add("ks-resetting");
    hero.classList.remove("ks-playing", "ks-finished", "ks-klaar", "ks-eind", "ks-lus");
    window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { hero.classList.remove("ks-resetting"); }); });
    bezig = false; afgelopen = false; afgespeeld = false; geblokkeerd = false; lusAan = false;
    open.disabled = false; if (replay) replay.hidden = true; if (fallback) fallback.hidden = true;
    vergrendel(true);
    window.scrollTo({ top: 0, behavior: "instant" });
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
    kiesBron();
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
    if ("requestIdleCallback" in window) window.requestIdleCallback(laadVoor, { timeout: 4000 }); else window.setTimeout(laadVoor, 2500);
  }
  start();
})();
