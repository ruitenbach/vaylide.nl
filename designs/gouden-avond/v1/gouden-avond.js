/* Gouden Avond v1: de opening (sleutel, deuren, dansvideo, feest) als één scène in de kop.
   Volgorde en tijden zijn die van het goedgekeurde prototype (ms na de tik op de sleutel):
     0 sleutel lijnt uit · 850 getande uiteinde gaat het slot in · 1350 sleutel draait om · 2200 sleutel verdwijnt · 2500 deuren slaan open
     2900 feest (hartjes, confetti, lichtpuntjes: 145 deeltjes) · 3050 dansvideo start · 6500 namen en datum.
   Wat de browser tekent (deuren, sleutel, deeltjes) staat in style.css als overgangen en animaties op transform en opacity; dit script zet alleen de
   klassen op het juiste moment en ruimt alles op: bij Opening overslaan, bij Opnieuw beleven en bij het verlaten van de pagina worden alle timers
   gestopt en de deeltjes verwijderd. Hartjes en confetti spreiden uit en vervagen (ze vallen niet). Zonder dit script, bij 'minder beweging', bij
   stilgezette beweging of als de opening al gezien is, staat de scène open (poster, namen, datum) met een knop om de dans af te spelen. */
(function () {
  "use strict";
  var hero = document.querySelector("[data-bc]");
  if (!hero) return;
  var html = document.documentElement;
  var q = function (sel) { return hero.querySelector(sel); };
  var video = q("[data-bc-video]"), sleutel = q("[data-bc-sleutel]"), overslaan = q("[data-bc-skip]"), bekijk = q("[data-bc-bekijk]");
  var replay = q("[data-bc-replay]"), feest = q("[data-bc-feest]"), status = q("[data-bc-status]");
  var inhoud = document.querySelector(".bc-body");
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var heeftOpening = hero.hasAttribute("data-bc-opening");
  var opslagSleutel = "vierlief-open:" + location.pathname;  // dezelfde sleutel als invite.js: één keer per sessie
  var STAND = ["bc-aligning", "bc-inserting", "bc-turning", "bc-unlocked", "bc-opened", "bc-text-visible", "bc-klaar"];
  var timers = [], frame = 0, feestAan = false, bezig = false, afgelopen = false, afgespeeld = false, geblokkeerd = false, waarnemer = null;

  function rustig() { return reduceQuery.matches || html.classList.contains("fx-paused"); }
  function later(fn, ms) { timers.push(window.setTimeout(fn, ms)); }
  function stopTimers() { timers.forEach(window.clearTimeout); timers = []; }
  function zeg(tekst) { if (status) status.textContent = tekst; }
  function vergrendel(aan) {
    html.classList.toggle("bc-bezig", aan);
    if (inhoud) { if ("inert" in inhoud) inhoud.inert = aan; else if (aan) inhoud.setAttribute("aria-hidden", "true"); else inhoud.removeAttribute("aria-hidden"); }
  }
  function gezien() { try { return !!window.sessionStorage.getItem(opslagSleutel); } catch (e) { return false; } }
  function onthoud() { if (html.classList.contains("inv-embed")) return; try { window.sessionStorage.setItem(opslagSleutel, "1"); } catch (e) { /* privémodus */ } }
  function vervolgknop() {
    if (!replay) return;
    replay.hidden = false;
    replay.textContent = (!afgespeeld || geblokkeerd || rustig() || !sleutel) ? "Speel de scène af ▷" : "Opnieuw beleven ↺";
  }

  /* ---------- feest: 145 deeltjes, alleen zolang het feest duurt ---------- */
  var PALET = ["#e4c58b", "#fff1d4", "#b98d4d", "#f8e7c5", "#d7b16c"];
  var HART = "M12 21S2 14.8 2 8.1C2 2.8 8.7 1.7 12 6C15.3 1.7 22 2.8 22 8.1C22 14.8 12 21 12 21Z";
  var STER = "m12 1 2.8 7.6L23 12l-8.2 3.4L12 23l-2.8-7.6L1 12l8.2-3.4Z";
  function vorm(pad) {
    var ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg"), p = document.createElementNS(ns, "path");
    svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("aria-hidden", "true"); svg.setAttribute("focusable", "false");
    p.setAttribute("d", pad); svg.appendChild(p);
    return svg;
  }
  function bouwFeest() {
    var stuk = document.createDocumentFragment();
    for (var i = 0; i < 145; i++) {
      var type = i % 3 === 0 ? "confetti" : i % 4 === 0 ? "star" : "heart";
      var el = document.createElement("span");
      el.className = "bc-spark bc-spark--" + (type === "star" ? "star" : type);
      if (type === "heart") el.appendChild(vorm(HART)); else if (type === "star") el.appendChild(vorm(STER));
      var kant = i % 2 ? 1 : -1, bereik = 45 + (i * 31 % 170), hoogte = 80 + (i * 43 % 245), maat = 7 + (i * 7 % 12);
      var s = el.style;
      s.setProperty("--size", maat + "px"); s.setProperty("--tone", PALET[i % PALET.length]);
      s.setProperty("--dx", kant * bereik + "px"); s.setProperty("--dy", -hoogte + "px");
      s.setProperty("--endx", kant * (bereik + 12) + "px"); s.setProperty("--endy", (-hoogte - 12) + "px");
      s.setProperty("--spin", kant * (60 + i * 17 % 150) + "deg"); s.setProperty("--endspin", kant * (170 + i * 29 % 290) + "deg");
      s.setProperty("--duration", (4.2 + i % 9 * 0.22) + "s"); s.setProperty("--delay", i % 20 * 0.075 + "s");
      if (type === "star") {
        s.setProperty("--glintx", (8 + i * 37 % 84) + "%"); s.setProperty("--glinty", (8 + i * 23 % 76) + "%");
        s.setProperty("--glintsize", (4 + i % 5) + "px"); s.setProperty("--glintdelay", (i % 12 * 0.13) + "s");
      }
      stuk.appendChild(el);
    }
    feest.appendChild(stuk);
  }
  function stopFeest() {
    if (!feest) return;
    if (frame) { window.cancelAnimationFrame(frame); frame = 0; }
    feest.textContent = "";
    feestAan = false;
  }
  function klaarzettenFeest() {  // de deeltjes worden alvast opgebouwd (onzichtbaar) terwijl de sleutel draait; bij 2,9 s hoeft alleen de klas erop
    if (!feest || feest.firstChild || rustig()) return;
    bouwFeest();
  }
  function startFeest() {
    if (!feest || feestAan || rustig()) return;
    if (!feest.firstChild) bouwFeest();
    feestAan = true;
    // In porties van 29 over vijf beelden: alle 145 tegelijk laten starten kost op een trage telefoon één beeld van 40 ms stijlwerk.
    var deeltjes = feest.children, porties = 5, per = Math.ceil(deeltjes.length / porties), n = 0;
    (function portie() {
      if (!feestAan) return;
      for (var i = n * per; i < Math.min(deeltjes.length, (n + 1) * per); i++) deeltjes[i].classList.add("bc-spark--aan");
      if (++n < porties) frame = window.requestAnimationFrame(portie);
    })();
    later(stopFeest, 7800);
  }

  /* ---------- dansvideo ---------- */
  function opwarmen() {  // achter de gesloten deuren: decoder en eerste beeld klaarzetten, zodat de start bij 3,05 s geen haperende frame kost
    if (!video || !video.play) return;
    var belofte = video.play();
    if (belofte && belofte.then) belofte.then(function () { video.pause(); try { video.currentTime = 0; } catch (e) { /* geen metadata */ } }, function () { /* geblokkeerd: dan speelt de knop later */ });
  }
  function speel() {
    if (!video) return;
    try { video.currentTime = 0; } catch (e) { /* nog geen metadata */ }
    var belofte = video.play();
    if (belofte && belofte.then) {
      belofte.then(function () { afgespeeld = true; geblokkeerd = false; vervolgknop(); }, function () { geblokkeerd = true; vervolgknop(); });
    } else { afgespeeld = true; vervolgknop(); }
  }
  if (video) video.addEventListener("ended", function () { video.pause(); vervolgknop(); });

  /* ---------- stand van de scène ---------- */
  function zetStand(namen) {
    hero.classList.add("bc-resetting");
    STAND.forEach(function (n) { hero.classList.toggle(n, namen.indexOf(n) >= 0); });
    window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { hero.classList.remove("bc-resetting"); }); });
  }
  function slotStand() { return ["bc-opened", "bc-unlocked", "bc-text-visible", "bc-klaar"]; }

  function afronden(metFocus) {
    afgelopen = true; bezig = false;
    hero.classList.add("bc-klaar");
    hero.classList.add("bc-text-visible");
    onthoud();
    if (waarnemer) { waarnemer.disconnect(); waarnemer = null; }
    vervolgknop();
    zeg("De uitnodiging is geopend. Scroll voor het programma en het aanmelden.");
    // De uitnodiging eronder (honderden elementen) gaat in een eigen beeld van het slot af, niet in hetzelfde beeld als de namen die verschijnen.
    window.requestAnimationFrame(function () {
      vergrendel(false);
      if (metFocus && bekijk) window.requestAnimationFrame(function () { bekijk.focus({ preventScroll: true }); });
    });
  }
  function direct() {  // open scène zonder opening
    zetStand(slotStand());
    afgelopen = true; bezig = false;
    vergrendel(false);
    vervolgknop();
  }
  function begin() {
    if (bezig || afgelopen) return;
    if (rustig()) { overslaanNu(); return; }
    bezig = true;
    if (window.scrollY > 0) window.scrollTo({ top: 0, behavior: "instant" });  // de scène hoort volledig in beeld te staan (bijvoorbeeld na een sprong via de toetsenbordfocus)
    sleutel.disabled = true;
    hero.classList.add("bc-aligning");
    zeg("De sleutel draait in het slot.");
    later(klaarzettenFeest, 1000);
    later(opwarmen, 150);
    if (overslaan) overslaan.focus({ preventScroll: true });
    later(function () { hero.classList.add("bc-inserting"); }, 850);
    later(function () { hero.classList.add("bc-turning"); }, 1350);
    later(function () { hero.classList.add("bc-unlocked"); }, 2200);
    later(function () { hero.classList.add("bc-opened"); zeg("De deuren gaan open."); }, 2500);
    later(startFeest, 2900);
    later(speel, 3050);
    later(function () { afronden(true); }, 6500);
    if ("MutationObserver" in window) {  // de gast zet de beweging stil tijdens de opening
      waarnemer = new MutationObserver(function () { if (bezig && rustig()) overslaanNu(); });
      waarnemer.observe(html, { attributes: true, attributeFilter: ["class"] });
    }
  }
  function overslaanNu() {
    if (afgelopen) return;
    stopTimers();
    stopFeest();
    if (video) { video.pause(); try { video.currentTime = 0; } catch (e) { /* geen metadata */ } }
    afgespeeld = false;
    if (sleutel) sleutel.disabled = true;
    zetStand(slotStand());
    afronden(true);
    zeg("Opening overgeslagen. De uitnodiging is geopend. Scroll voor het programma en het aanmelden.");
  }
  function opnieuw() {
    stopTimers();
    stopFeest();
    if (video) { video.pause(); try { video.currentTime = 0; } catch (e) { /* geen metadata */ } }
    zetStand([]);
    bezig = false; afgelopen = false; afgespeeld = false; geblokkeerd = false;
    sleutel.disabled = false;
    replay.hidden = true;
    vergrendel(true);
    window.scrollTo(0, 0);
    sleutel.focus({ preventScroll: true });
    zeg("De deuren zijn weer dicht. Tik op de sleutel om te openen.");
  }

  if (sleutel) sleutel.addEventListener("click", begin);
  if (overslaan) overslaan.addEventListener("click", overslaanNu);
  if (replay) replay.addEventListener("click", function () {
    if (!sleutel || rustig() || geblokkeerd || !afgespeeld) speel(); else opnieuw();
  });
  if (bekijk) bekijk.addEventListener("click", function () {
    var doel = document.getElementById("bc-verder");
    if (doel) doel.scrollIntoView({ behavior: rustig() ? "auto" : "smooth", block: "start" });
  });
  var skipLink = document.querySelector(".skip-link");
  if (skipLink) skipLink.addEventListener("click", function () { if (bezig) overslaanNu(); });
  window.addEventListener("pagehide", function () { stopTimers(); stopFeest(); });

  /* ---------- de uitnodiging eronder: bewegen alleen in beeld ---------- */
  // Stralenkrans en goudglans lopen alleen in een band die zichtbaar is (klas bc-zichtbaar); de achtergrondfoto's schuiven iets mee bij het scrollen.
  var banden = document.querySelectorAll(".bc-sec");
  if ("IntersectionObserver" in window && banden.length) {
    var kijker = new IntersectionObserver(function (items) {
      items.forEach(function (item) { item.target.classList.toggle("bc-zichtbaar", item.isIntersecting); });
    }, { rootMargin: "10% 0px 10% 0px" });
    banden.forEach(function (band) { kijker.observe(band); });
  } else {
    banden.forEach(function (band) { band.classList.add("bc-zichtbaar"); });
  }
  function parallax() {
    var g = window.gsap, st = window.ScrollTrigger;
    if (!g || !st || rustig() || !html.classList.contains("fx-motion")) return;
    g.registerPlugin(st);
    document.querySelectorAll("[data-bc-parallax]").forEach(function (foto) {
      g.fromTo(foto, { yPercent: -6 }, { yPercent: 6, ease: "none", scrollTrigger: { trigger: foto.parentNode, start: "top bottom", end: "bottom top", scrub: true } });
    });
  }
  if (document.readyState === "complete") parallax(); else window.addEventListener("load", parallax, { once: true });

  /* ---------- begin ---------- */
  function start() {
    if (!heeftOpening || !sleutel) { direct(); return; }
    var direct_open = /^#(aanmelden|aanmelden-formulier|uitnodiging)/.test(location.hash) || html.hasAttribute("data-live") ||
      html.hasAttribute("data-direct-open") || html.classList.contains("inv-embed");
    if (direct_open || gezien() || rustig()) { direct(); return; }
    vergrendel(true);
    if (video) video.preload = "auto";  // de dans moet klaar zijn als de deuren opengaan
  }
  start();
})();
