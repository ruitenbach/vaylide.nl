/* Kerstkaart v1: de opening van het chocoladehuis als één scène in de kop.
   Eerst staat het gesloten huis met een gouden deurklopper in beeld. Een tik op de klopper geeft drie klopjes (de ring van de klopper beweegt echt, met een zacht
   klopgeluid en een lichtflits in het raam), daarna start één video (deur open, elfjes, het huis lost op, een lolly, zwaaiende elfjes, 15 s). Na het einde staat de
   groet in beeld. De video start nooit vanzelf: de afspeelstart hoort bij de tik.
   Het script maakt de gouden vonken pas aan als ze nodig zijn en ruimt alles op (timers, deeltjes, geluid, vergrendeling) bij Opening overslaan, Opnieuw beleven en
   het verlaten van de pagina. Zonder dit script, bij 'minder beweging', bij stilgezette beweging, of als de opening al gezien is, staat het eindbeeld met de groet
   er direct, met een knop om de opening af te spelen. Er is één video; hij wordt hergebruikt voor opnieuw beleven. */
(function () {
  "use strict";
  var hero = document.querySelector("[data-kk]");
  if (!hero) return;
  var html = document.documentElement;
  var q = function (sel) { return hero.querySelector(sel); };
  var video = q("[data-kk-video]"), open = q("[data-kk-open]"), fallback = q("[data-kk-fallback]"), overslaan = q("[data-kk-skip]"), deur = q("[data-kk-deur]");
  var ambient = q("[data-kk-ambient]"), replay = q("[data-kk-replay]"), sparkles = q("[data-kk-sparkles]"), status = q("[data-kk-status]"), scroll = q("[data-kk-scroll]");
  var inhoud = document.querySelector(".kk-body");
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var heeftOpening = hero.hasAttribute("data-kk-opening") && !!open;
  var opslagSleutel = "vierlief-open:" + location.pathname;  // dezelfde sleutel als invite.js: één keer per sessie
  var KLOP_TIJDEN = [0, 430, 800];                            // ms van de drie klopjes
  var NA_KLOPPEN = 750;                                       // ms rust na het laatste klopje, daarna start de video
  var timers = [], primen = false, bezig = false, afgelopen = false, afgespeeld = false, geblokkeerd = false, klopt = false, waarnemer = null, audio = null;

  function rustig() { return reduceQuery.matches || html.classList.contains("fx-paused"); }
  function later(fn, ms) { timers.push(window.setTimeout(fn, ms)); }
  function stopTimers() { timers.forEach(window.clearTimeout); timers = []; }
  function zeg(tekst) { if (status) status.textContent = tekst; }
  function vergrendel(aan) {
    html.classList.toggle("kk-bezig", aan);
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
  function tekenBeeld(naam, el) {
    ambientBron = naam;
    if (!ambientZichtbaar() || !el) return;
    if (el.complete && el.naturalWidth) { teken(el); return; }
    el.addEventListener("load", function () { if (ambientBron === naam) teken(el); }, { once: true });
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
  var posterEl = q(".kk-poster"), eindEl = q(".kk-eindbeeld");
  if (window.matchMedia) {
    var breed = window.matchMedia("(min-aspect-ratio: 3/5)");
    var herteken = function () {
      if (!breed.matches) return;
      if (ambientBron === "video") teken(video); else tekenBeeld(ambientBron, ambientBron === "eind" ? eindEl : posterEl);
    };
    if (breed.addEventListener) breed.addEventListener("change", herteken);
  }

  /* ---------- gouden vonken: rond de klopper bij een klopje, een paar bij het wachten ---------- */
  function vonk(x, y, dx, dy, grootte, duur) {
    var el = document.createElement("i");
    el.className = "kk-vonk";
    var s = el.style;
    s.setProperty("--x", x + "%"); s.setProperty("--y", y + "%"); s.setProperty("--dx", dx + "px"); s.setProperty("--dy", dy + "px");
    s.setProperty("--size", grootte + "px"); s.setProperty("--duur", duur + "ms");
    el.addEventListener("animationend", function () { if (el.parentNode) el.parentNode.removeChild(el); });
    return el;
  }
  function vonken(aantal) {  // een korte, kleine uitbarsting vanaf de klopper (51,5 % en 61,7 % van het beeld)
    if (!sparkles || rustig()) return;
    var stuk = document.createDocumentFragment();
    for (var i = 0; i < aantal; i++) {
      var hoek = (i / aantal) * 6.283 + Math.random() * 0.5, afstand = 26 + Math.random() * 34;
      stuk.appendChild(vonk(51.5, 61.7, Math.cos(hoek) * afstand, Math.sin(hoek) * afstand - 8, 3 + Math.round(Math.random() * 4), 560 + Math.round(Math.random() * 420)));
    }
    sparkles.appendChild(stuk);
  }
  function wisVonken() { if (sparkles) sparkles.textContent = ""; }

  /* ---------- het klopgeluid: gesynthetiseerd, zacht (hout met een vleugje koper), alleen na een tik ---------- */
  function geluid() {
    if (rustig()) return;
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      if (!audio) audio = new Ctx();
      if (audio.state === "suspended" && audio.resume) audio.resume();
      var nu = audio.currentTime, uit = audio.destination;
      var master = audio.createGain(); master.gain.value = 0.32; master.connect(uit);
      // houten dof geluid: een dalende sinus
      var o = audio.createOscillator(), g = audio.createGain();
      o.type = "sine"; o.frequency.setValueAtTime(190, nu); o.frequency.exponentialRampToValueAtTime(62, nu + 0.11);
      g.gain.setValueAtTime(0.0001, nu); g.gain.exponentialRampToValueAtTime(0.9, nu + 0.006); g.gain.exponentialRampToValueAtTime(0.0001, nu + 0.16);
      o.connect(g); g.connect(master); o.start(nu); o.stop(nu + 0.2);
      // de tik van de ring: een kort, gefilterd ruisje
      var lengte = Math.floor(audio.sampleRate * 0.05), buf = audio.createBuffer(1, lengte, audio.sampleRate), d = buf.getChannelData(0);
      for (var i = 0; i < lengte; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / lengte, 3);
      var ruis = audio.createBufferSource(), filter = audio.createBiquadFilter(), gr = audio.createGain();
      ruis.buffer = buf; filter.type = "bandpass"; filter.frequency.value = 1900; filter.Q.value = 1.1; gr.gain.value = 0.55;
      ruis.connect(filter); filter.connect(gr); gr.connect(master); ruis.start(nu);
      // een heel zacht koperen naklank
      var k = audio.createOscillator(), gk = audio.createGain();
      k.type = "triangle"; k.frequency.value = 1180;
      gk.gain.setValueAtTime(0.0001, nu); gk.gain.exponentialRampToValueAtTime(0.07, nu + 0.004); gk.gain.exponentialRampToValueAtTime(0.0001, nu + 0.2);
      k.connect(gk); gk.connect(master); k.start(nu); k.stop(nu + 0.24);
    } catch (e) { /* geen geluid: de rest werkt gewoon */ }
  }
  function sluitGeluid() { if (audio && audio.close) { try { audio.close(); } catch (e) { /* al gesloten */ } } audio = null; }

  /* ---------- het kloppen ---------- */
  function klop() {  // één klopje: de ring beweegt, het raam licht op, er vliegen vonken, er klinkt een tik
    if (!deur) return;
    deur.classList.remove("kk-klop"); void deur.offsetWidth; deur.classList.add("kk-klop");
    hero.classList.remove("kk-dreun"); void hero.offsetWidth; hero.classList.add("kk-dreun");
    vonken(7);
    geluid();
  }
  function klopKlopKlop(daarna) {
    klopt = true; hero.classList.add("kk-kloppen");
    KLOP_TIJDEN.forEach(function (ms) { later(klop, ms); });
    later(function () { klopt = false; hero.classList.remove("kk-kloppen", "kk-dreun"); if (deur) deur.classList.remove("kk-klop"); daarna(); }, KLOP_TIJDEN[KLOP_TIJDEN.length - 1] + NA_KLOPPEN);
  }

  /* ---------- video ---------- */
  var geladen = false;
  function laadVoor() {  // alleen als de gast aanstalten maakt (aanraken, focus) en niet bij Data-besparing: dan pas bij de tik
    if (geladen || !video) return;
    var c = navigator.connection;
    if (c && (c.saveData || /(^|-)2g$/.test(c.effectiveType || ""))) return;
    geladen = true; video.preload = "auto";
    try { video.load(); } catch (e) { /* oudere browser */ }
  }
  function opTijd() {
    if (!video.requestVideoFrameCallback && ambientBron === "video" && ambientZichtbaar()) teken(video);
  }
  function toonVideo() {  // het eerste beeld van de video is gelijk aan het startbeeld met de klopper in rust: de overgang is naadloos
    hero.classList.remove("kk-eind", "kk-finished", "kk-klaar");
    hero.classList.add("kk-playing");
  }
  function speel() {  // moet vanuit een tik of toets komen (of kort daarna): de afspeelstart hoort bij het gebaar
    stopTimers(); wisVonken(); primen = false;
    laadVoor();
    try { video.currentTime = 0; } catch (e) { /* nog geen metadata */ }
    var belofte = video.play();
    var gelukt = function () {
      geblokkeerd = false; afgespeeld = true; bezig = true;
      if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(toonVideo); else window.setTimeout(toonVideo, 120);
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
    stopTimers(); wisVonken(); sluitGeluid();
    if (video) { video.pause(); try { video.currentTime = 0; } catch (e) { /* geen metadata */ } }
    hero.classList.remove("kk-playing", "kk-kloppen", "kk-dreun");
    hero.classList.add("kk-eind", "kk-finished", "kk-klaar");
    afgelopen = true; bezig = false; klopt = false;
    if (open) open.disabled = true;
    if (fallback) fallback.hidden = true;
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    vergrendel(false);
    knopTekst();
    tekenBeeld("eind", eindEl);
    if (metFocus && scroll) window.requestAnimationFrame(function () { scroll.focus({ preventScroll: true }); });
  }
  function einde() {
    if (video) video.pause();
    hero.classList.remove("kk-playing");
    hero.classList.add("kk-finished", "kk-klaar");
    afgelopen = true; bezig = false;
    wisVonken(); sluitGeluid();
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    if (ambientZichtbaar()) { teken(video); ambientBron = "eind"; }
    onthoud(); vergrendel(false); knopTekst();
    zeg("De kerstkaart is geopend. Scroll verder voor de rest van de kaart.");
    if (scroll) scroll.focus({ preventScroll: true });
  }
  function begin() {
    if (!open || open.disabled || afgelopen || klopt || bezig) return;
    if (rustig()) { overslaanNu(); return; }
    open.disabled = true;
    laadVoor();
    // Op sommige telefoons mag een stille video alleen starten kort na een tik: probeer de afspeelstart vast te leggen en zet hem meteen weer stil.
    primen = true;
    try { var p = video.play(); if (p && p.then) p.then(function () { if (!primen) return; video.pause(); try { video.currentTime = 0; } catch (e) { /* geen metadata */ } }, function () { /* later opnieuw */ }); } catch (e) { /* geen video */ }
    zeg("Er wordt drie keer aangeklopt.");
    klopKlopKlop(speel);
    if ("MutationObserver" in window) {  // de gast zet de beweging stil tijdens de opening
      waarnemer = new MutationObserver(function () { if ((bezig || klopt) && rustig()) overslaanNu(); });
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
    stopTimers(); wisVonken();
    video.pause(); try { video.currentTime = 0; } catch (e) { /* geen metadata */ }
    hero.classList.add("kk-resetting");
    hero.classList.remove("kk-playing", "kk-finished", "kk-klaar", "kk-eind", "kk-kloppen", "kk-dreun");
    window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { hero.classList.remove("kk-resetting"); }); });
    bezig = false; afgelopen = false; afgespeeld = false; geblokkeerd = false; klopt = false;
    open.disabled = false; if (replay) replay.hidden = true; if (fallback) fallback.hidden = true;
    vergrendel(true);
    window.scrollTo({ top: 0, behavior: "instant" });
    tekenBeeld("poster", posterEl);
    open.focus({ preventScroll: true });
    zeg("De deur is weer dicht. Tik op de deurklopper om aan te kloppen.");
  }

  if (open) { open.addEventListener("click", begin); ["pointerdown", "focus", "touchstart"].forEach(function (naam) { open.addEventListener(naam, laadVoor, { once: true, passive: true }); }); }
  if (fallback) fallback.addEventListener("click", function () { speel(); });
  if (overslaan) overslaan.addEventListener("click", overslaanNu);
  if (replay) replay.addEventListener("click", function () {
    if (heeftOpening && !rustig() && afgespeeld && !geblokkeerd) opnieuw(); else speel();
  });
  var skipLink = document.querySelector(".skip-link");
  if (skipLink) skipLink.addEventListener("click", function () { if (bezig || klopt || (heeftOpening && !afgelopen)) overslaanNu(); });
  window.addEventListener("pagehide", function () { stopTimers(); wisVonken(); sluitGeluid(); });

  /* ---------- de kaart eronder: sfeer en glans alleen in beeld ---------- */
  var banden = document.querySelectorAll(".kk-sec");
  if ("IntersectionObserver" in window && banden.length) {
    var kijker = new IntersectionObserver(function (items) {
      items.forEach(function (item) { item.target.classList.toggle("kk-zichtbaar", item.isIntersecting); });
    }, { rootMargin: "10% 0px 10% 0px" });
    banden.forEach(function (band) { kijker.observe(band); });
  } else {
    banden.forEach(function (band) { band.classList.add("kk-zichtbaar"); });
  }

  /* ---------- begin ---------- */
  function start() {
    if (!heeftOpening) { toonEind(false); hero.classList.add("kk-klaar"); knopTekst(); return; }
    var direct = /^#(aanmelden|aanmelden-formulier|uitnodiging)/.test(location.hash) || html.hasAttribute("data-live") ||
      html.hasAttribute("data-direct-open") || html.classList.contains("inv-embed");
    if (direct || gezien() || rustig()) { toonEind(false); return; }
    vergrendel(true);
    tekenBeeld("poster", posterEl);
    if ("requestIdleCallback" in window) window.requestIdleCallback(laadVoor, { timeout: 4000 }); else window.setTimeout(laadVoor, 2500);
  }
  start();
})();
