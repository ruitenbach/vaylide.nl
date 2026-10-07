/* Kerststad v1: de opening van de peperkoekstad als één scène in de kop.
   Het eerste beeld is extreem dichtbij: de ronde gouden badge met de officiële VAYLIDE-V. De V is het klikpunt (een zachte lichtring en de tekst "Tik op de V om te openen").
   Eén tik speelt de opening één keer. Daarna valt de kaart niet stil: de laatste scène loopt door als levende eindloop. Die eindloop is een aparte, kleine clip (loop.mp4 / loop-desktop.mp4,
   dezelfde beelden vanaf lusStart tot het einde van de film) die ook nog eens in twee exemplaren (A en B) klaarstaat: er wordt nooit meer in de grote openingsvideo teruggesprongen.
   De opening gaat bij lusStart zonder zichtbare naad over in clip A (dezelfde beelden; A komt in 0,8 s boven de nog doorlopende opening), en aan het eind van elke ronde komt het andere
   exemplaar met een kruisverloop van 0,8 s boven het eerste. Het exemplaar dat net is weggevallen springt achter de schermen terug naar het begin en staat dan weer klaar.
   De opening start daarna nooit meer vanzelf; alleen "Opnieuw beleven" (een tik) begint opnieuw. De video's zelf zijn niet bewerkt. De lus pauzeert buiten beeld en in een verborgen tabblad.
   Zonder dit script, bij 'minder beweging', bij stilgezette beweging of in de Studio staat het eindbeeld met de groet er direct, met een knop om de opening af te spelen (eenmalig, zonder lus). */
(function () {
  "use strict";
  var hero = document.querySelector("[data-ks]");
  if (!hero) return;
  var html = document.documentElement;
  var q = function (sel) { return hero.querySelector(sel); };
  var video = q("[data-ks-video]"), open = q("[data-ks-open]"), fallback = q("[data-ks-fallback]"), overslaan = q("[data-ks-skip]");
  var scene = q("[data-ks-scene]"), replay = q("[data-ks-replay]"), status = q("[data-ks-status]"), scroll = q("[data-ks-scroll]");
  var inhoud = document.querySelector(".ks-body");
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var heeftOpening = hero.hasAttribute("data-ks-opening") && !!open;
  var opslagSleutel = "vierlief-open:" + location.pathname;  // dezelfde sleutel als invite.js: één keer per sessie
  var lusStart = parseFloat(video && video.getAttribute("data-ks-lus")) || 16.5;  // seconde in de opening waar hij overgaat in de loopclip (= het eerste beeld van de clip; per bron: data-ks-lus / data-ks-lus-desktop)
  var LOOP_FADE = 0.8, LOOP_VOOR = 0.15;                                          // kruisverloop in seconden (zelfde waarde als de CSS-overgang van .ks-loop) en hoeveel eerder het volgende exemplaar start
  var breedQuery = window.matchMedia ? window.matchMedia("(min-aspect-ratio: 6/5)") : { matches: false };
  var mobielBron = video && video.querySelector("source") ? video.querySelector("source").getAttribute("src") : "";
  var formaat = "smal";
  var laadFout = false, bezig = false, afgelopen = false, afgespeeld = false, geblokkeerd = false, lusAan = false, hervatNaRust = false, inBeeld = true, waarnemer = null;
  var loopEls = null, loopActief = 0, loopAan = false, loopWissel = false, loopRaf = 0, loopTimer = 0;

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

  /* ---------- video ---------- */
  var geladen = false;
  function laadVoor() {  // alleen als de gast aanstalten maakt (aanraken, focus) en niet bij Data-besparing: dan pas bij de tik
    if (geladen || !video) return;
    var c = navigator.connection;
    if (c && (c.saveData || /(^|-)2g$/.test(c.effectiveType || ""))) return;
    geladen = true; video.preload = "auto";
    maakLoop();   // de kleine loopclip (1 tot 4 MB) laadt al mee: hij staat klaar vóór de opening er is
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
    lusStart = parseFloat(video.getAttribute(nieuw === "breed" ? "data-ks-lus-desktop" : "data-ks-lus")) || 16.5;
    video.setAttribute("src", nieuw === "breed" ? desktop : mobielBron);
    zetLoopBron();
  }
  if (breedQuery.addEventListener) breedQuery.addEventListener("change", function () { if (!bezig && !lusAan && !afgelopen) kiesBron(); });

  function zoekNaar(t) { try { video.currentTime = t; } catch (e) { /* nog geen metadata */ } }
  function afspelen() {
    var belofte = video.play();
    return belofte && belofte.then ? belofte : Promise.resolve();
  }

  /* ---------- de levende eindloop: een aparte kleine clip in twee exemplaren (A/B), nooit terugspringen in de opening ---------- */
  function loopUrl() { return video.getAttribute(formaat === "breed" ? "data-ks-loop-desktop" : "data-ks-loop") || ""; }
  function zetLoopBron() {
    if (!loopEls) return;
    var url = loopUrl();
    loopEls.forEach(function (v) { if (url && v.getAttribute("src") !== url) { v.setAttribute("src", url); v.load(); } });
  }
  function maakLoop() {
    if (loopEls || !scene || !video || !loopUrl()) return loopEls;
    loopEls = [0, 1].map(function () {
      var v = document.createElement("video");
      v.className = "ks-loop"; v.muted = true; v.defaultMuted = true; v.loop = false; v.preload = "auto";
      ["muted", "playsinline", "webkit-playsinline", "disablepictureinpicture", "disableremoteplayback"].forEach(function (naam) { v.setAttribute(naam, ""); });
      v.setAttribute("controlslist", "nodownload noplaybackrate"); v.setAttribute("aria-hidden", "true"); v.setAttribute("tabindex", "-1");
      v.addEventListener("error", function () { if (loopAan) toonStatisch(false); });
      v.addEventListener("ended", function () { if (loopAan && v === loopEls[loopActief]) wissel(); });   // vangnet: als de klok het moment miste
      video.parentNode.insertBefore(v, video.nextSibling);
      return v;
    });
    zetLoopBron();
    return loopEls;
  }
  function metKlaar(v, ok, fout) {   // wacht (hooguit 6 s) tot een clip genoeg heeft om door te spelen
    if (v.readyState >= 3) { ok(); return; }
    var klaar = function () { v.removeEventListener("canplay", klaar); window.clearTimeout(t); ok(); };
    var t = window.setTimeout(function () { v.removeEventListener("canplay", klaar); fout(); }, 6000);
    v.addEventListener("canplay", klaar);
  }
  function primeer(v) {   // iOS laadt een clip pas na play(): het klaarstaande exemplaar krijgt zo zijn eerste beeld
    if (v.readyState >= 2) return;
    var b = v.play();
    if (b && b.then) b.then(function () { v.pause(); try { v.currentTime = 0; } catch (e) { /* nog geen metadata */ } }, function () { /* later opnieuw */ });
  }
  function startLoop() {   // clip A begint op zijn eerste beeld en komt in 0,8 s boven de opening (of boven het eindbeeld)
    if (loopAan) return;
    if (!maakLoop()) { toonStatisch(false); return; }
    var a = loopEls[0];
    loopActief = 0; loopWissel = false; loopAan = true; lusAan = true;
    loopEls.forEach(function (v) { v.classList.remove("ks-zicht", "ks-boven"); });
    metKlaar(a, function () {
      if (!loopAan) return;
      if (a.currentTime > 0.05) { try { a.currentTime = 0; } catch (e) { /* nog geen metadata */ } }
      a.classList.add("ks-boven");
      var b = a.play();
      (b && b.then ? b : Promise.resolve()).then(function () {
        if (!loopAan) return;
        a.classList.add("ks-zicht");
        hero.classList.remove("ks-eind");
        primeer(loopEls[1]);
        window.clearTimeout(loopTimer);
        loopTimer = window.setTimeout(function () { if (loopAan && !video.paused && !video.ended) video.pause(); }, LOOP_FADE * 1000 + 150);   // de opening eronder is nu volledig bedekt: stilzetten spaart de telefoon
      }, function () { toonStatisch(false); });
      loopWacht();
    }, function () { toonStatisch(false); });
  }
  function wissel() {   // het andere exemplaar (staat al op zijn eerste beeld) komt boven het huidige en neemt het over
    if (!loopAan || loopWissel) return;
    var x = loopEls[loopActief], y = loopEls[1 - loopActief];
    loopWissel = true;
    var los = function () {
      y.classList.add("ks-boven"); x.classList.remove("ks-boven");
      var b = y.play();
      (b && b.then ? b : Promise.resolve()).then(function () { y.classList.add("ks-zicht"); }, function () { /* hervat na een pauze */ });
      window.clearTimeout(loopTimer);
      loopTimer = window.setTimeout(function () {
        x.classList.remove("ks-zicht"); x.pause();
        try { x.currentTime = 0; } catch (e) { /* nog geen metadata */ }   // achter de schermen terug naar het begin: staat weer klaar
        loopActief = 1 - loopActief; loopWissel = false;
      }, LOOP_FADE * 1000 + 120);
    };
    if (y.readyState >= 2) los(); else y.addEventListener("loadeddata", los, { once: true });
  }
  function loopWacht() {   // per beeld kijken of het volgende exemplaar moet starten
    window.cancelAnimationFrame(loopRaf);
    var stap = function () {
      loopRaf = window.requestAnimationFrame(stap);
      if (!loopAan || document.hidden) return;
      var x = loopEls[loopActief];
      // de film eindigt waar clip A eindigt (de opening zelf is vanaf de overgang stilgezet): dan komen groet, bijschrift en focus, net nadat het kruisverloop naar B klaar is
      if (bezig && x.duration && x.currentTime >= x.duration - 0.2) einde();
      if (loopWissel) return;
      if (x.duration && !x.paused && x.currentTime >= x.duration - LOOP_FADE - LOOP_VOOR) wissel();
    };
    loopRaf = window.requestAnimationFrame(stap);
  }
  function stopLoop() {
    loopAan = false; lusAan = false; loopWissel = false;
    window.cancelAnimationFrame(loopRaf); window.clearTimeout(loopTimer);
    if (!loopEls) return;
    loopEls.forEach(function (v) {
      v.classList.remove("ks-zicht", "ks-boven"); v.pause();
      try { if (v.currentTime > 0) v.currentTime = 0; } catch (e) { /* nog geen metadata */ }
    });
  }

  function naarLus(vanaf) {  // de scène staat open; vanaf=true: de loopclip komt boven het eindbeeld (overslaan, tweede bezoek, beweging weer aan)
    if (vanaf) kiesBron();
    afgelopen = true; bezig = false;
    hervatNaRust = false;
    hero.classList.remove("ks-playing");
    hero.classList.add("ks-finished", "ks-klaar", "ks-lus");
    if (open) open.disabled = true;
    if (fallback) fallback.hidden = true;
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    vergrendel(false);
    knopTekst();
    if (vanaf) {
      video.pause();
      hero.classList.add("ks-eind");     // het eindbeeld blijft staan tot de clip speelt en lost dan op in de eindloop
      startLoop();
    }
  }

  function einde() {  // de film is uit: alleen de eindloop draait nog
    if (afgelopen) return;
    afgelopen = true; bezig = false;
    onthoud();
    video.pause();
    if (rustig()) { toonStatisch(true); return; }
    naarLus(false);
    if (!loopAan) startLoop();    // vangnet: als de overgang tijdens de opening niet lukte, komt de clip nu (met een kruisverloop)
    zeg("De kerstkaart is geopend. Scroll verder voor de rest van de kaart.");
    if (scroll) scroll.focus({ preventScroll: true });
  }

  function volgOpening() {   // op lusStart (iets eerder, de clip heeft even nodig) gaat de opening zonder naad over in loopclip A
    if (!video.requestVideoFrameCallback) return;
    var cb = function (nu, meta) {
      if (!bezig || loopAan) return;
      if (meta.mediaTime >= lusStart - 0.08) { startLoop(); return; }
      video.requestVideoFrameCallback(cb);
    };
    video.requestVideoFrameCallback(cb);
  }
  function speel() {  // moet vanuit een tik of toets komen: de afspeelstart hoort bij het gebaar
    stopLoop(); kiesBron(); maakLoop();
    hero.classList.remove("ks-eind", "ks-finished", "ks-klaar", "ks-lus");
    zoekNaar(0);
    afspelen().then(function () {
      geblokkeerd = false; afgespeeld = true; bezig = true; afgelopen = false;
      hero.classList.add("ks-playing");
      volgOpening();
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
    video.addEventListener("timeupdate", function () { if (bezig && !loopAan && !video.requestVideoFrameCallback && video.currentTime >= lusStart - 0.1) startLoop(); });
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
    stopLoop();
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
    stopLoop(); bezig = false; kiesBron();
    video.pause(); zoekNaar(0);
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
  function hervat() {
    if (!loopAan || !inBeeld || document.hidden || rustig()) return;
    loopEls.forEach(function (v, i) { if (v.classList.contains("ks-zicht") || (loopWissel && i !== loopActief)) { var b = v.play(); if (b && b.catch) b.catch(function () { /* tik nodig */ }); } });
  }
  function pauzeer() { if (loopAan) loopEls.forEach(function (v) { v.pause(); }); }
  document.addEventListener("visibilitychange", function () { if (document.hidden) pauzeer(); else hervat(); });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (items) {
      inBeeld = items[items.length - 1].isIntersecting;
      if (inBeeld) hervat(); else pauzeer();
    }, { threshold: 0.05 }).observe(hero);
  }
  if ("MutationObserver" in window) {   // de gast zet de beweging stil of weer aan terwijl de eindloop draait
    new MutationObserver(function () {
      if (rustig() && loopAan) { hervatNaRust = true; toonStatisch(false); }
      else if (!rustig() && hervatNaRust && !reduceQuery.matches) { hervatNaRust = false; naarLus(true); }
    }).observe(html, { attributes: true, attributeFilter: ["class"] });
  }
  window.addEventListener("pagehide", function () { if (video) video.pause(); pauzeer(); });

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
      toonStatisch(false);
      naarLus(true);
      return;
    }
    if (studioStil || direct || rustig()) { toonStatisch(false); return; }
    if (!html.hasAttribute("data-live") && gezien()) {   // al gezien in deze sessie: de opening start niet opnieuw, de levende eindloop wel
      toonStatisch(false);
      var c = navigator.connection;
      if (!(c && c.saveData)) naarLus(true);   // alleen de kleine loopclip wordt geladen, niet de grote opening
      return;
    }
    vergrendel(true);
    if ("requestIdleCallback" in window) window.requestIdleCallback(laadVoor, { timeout: 4000 }); else window.setTimeout(laadVoor, 2500);
  }
  start();
})();
