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


  /* ---------- de levende laag: de V op de gevel en de figuurtjes op het plein, bij beide bronnen ---------- */
  // Alles staat in beeldcoördinaten van het referentiebeeld van de gekozen bron (16,0 s; liggend 960 x 540, staand 540 x 960) en gaat met de gemeten camerabeweging mee (kerststad-spoor.js). De V volgt de
  // gevel van het huis naast de kerk, de figuurtjes de grond van het plein. Bij de sprong van de eindloop (en bij het oplossen van het eindbeeld) schuift alles mee met het kruisverloop. De figuurtjes
  // lopen op hun eigen klok, niet op de tijd van de video, zodat hun beweging bij elke sprong van de lus gewoon doorloopt. De video's zelf zijn niet bewerkt.
  var laag = q("[data-ks-laag]"), vEl = q("[data-ks-v]"), eindEl = q("[data-ks-eindbeeld]");
  var SPOOR = window.KERSTSTAD_SPOOR, figuren = [], laagLus = 0, laatsteNu = 0, T_EIND = 19.95;
  var LAAG = {   // per bron: de plek van de V (het midden van de krans onder het hartje), zijn breedte, het begin van de avondscène en de diepteschaal van de figuurtjes
    breed: { vAnker: [319, 234.5], vBreedte: 30, tV: 12.5, tFig: 14.0, diepteY: 340, diepteK: 0.0035 },
    smal: { vAnker: [159, 375], vBreedte: 44, tV: 12.5, tFig: 14.2, diepteY: 500, diepteK: 0.003 }
  };
  function klem(x, a, b) { return Math.max(a, Math.min(b, x)); }
  function zacht(x) { x = klem(x, 0, 1); return x * x * (3 - 2 * x); }
  function menging(a, b, p) { return a + (b - a) * p; }
  function spoorOp(fm, naam, t) {
    var rij = SPOOR[fm][naam], x = klem((t - SPOOR.van) / SPOOR.stap, 0, rij.length - 1), i = Math.min(rij.length - 2, Math.floor(x)), f = x - i, m = [];
    for (var j = 0; j < 6; j++) m.push(menging(rij[i][j], rij[i + 1][j], f));
    return m;
  }
  function pas(m, x, y) { return [m[0] * x + m[1] * y + m[2], m[3] * x + m[4] * y + m[5]]; }
  function leesPad(tekst) {
    if (!tekst) return null;
    return tekst.split(" ").map(function (p) { var d = p.split(","); return [parseFloat(d[0]), parseFloat(d[1])]; });
  }
  if (laag) {
    figuren = [].slice.call(laag.querySelectorAll("[data-ks-fig]")).map(function (el) {
      var pad = { breed: leesPad(el.getAttribute("data-pad")), smal: leesPad(el.getAttribute("data-pad-smal")) };
      var lengte = {};
      ["breed", "smal"].forEach(function (fm) { var p = pad[fm]; lengte[fm] = p && p.length > 1 ? Math.hypot(p[1][0] - p[0][0], p[1][1] - p[0][1]) : 0; });
      return { el: el, draai: el.querySelector(".ks-fig__draai"), pad: pad, lengte: lengte, v: parseFloat(el.getAttribute("data-snelheid")) || 6, gedrag: el.getAttribute("data-gedrag"),
               fase: parseFloat(el.getAttribute("data-fase")) || 0, hoogte: { breed: parseFloat(el.getAttribute("data-hoogte")) || 28, smal: parseFloat(el.getAttribute("data-hoogte-smal")) || 38 }, kijk: 1, stil: false };
    });
  }
  function figuurStand(f, nu, fm) {  // positie (referentiebeeld), kijkrichting en of hij loopt
    var pad = f.pad[fm];
    if (pad.length < 2) {
      var wissel = Math.floor((nu + f.fase * 10) / 7) % 2;     // de zwaaier draait zich af en toe om
      return { x: pad[0][0], y: pad[0][1], kijk: wissel ? -1 : 1, loopt: false, hop: 0 };
    }
    var pauze = 1.6, duur = f.lengte[fm] / f.v, cyclus = 2 * (duur + pauze), u = ((nu + f.fase * cyclus) % cyclus + cyclus) % cyclus, p, kijk, loopt = true;
    if (u < duur) { p = u / duur; kijk = 1; }
    else if (u < duur + pauze) { p = 1; kijk = -1; loopt = false; }
    else if (u < 2 * duur + pauze) { p = 1 - (u - duur - pauze) / duur; kijk = -1; }
    else { p = 0; kijk = 1; loopt = false; }
    var x = menging(pad[0][0], pad[1][0], p), y = menging(pad[0][1], pad[1][1], p);
    return { x: x, y: y, kijk: kijk, loopt: loopt, hop: f.gedrag === "kind" && loopt ? Math.abs(Math.sin(nu * 6.3 + f.fase * 5)) * 2.6 : 0 };
  }
  function laagStap(nu) {
    laagLus = window.requestAnimationFrame(laagStap);
    var klas = hero.classList;
    if (!(klas.contains("ks-playing") || klas.contains("ks-lus") || klas.contains("ks-eind") || klas.contains("ks-finished")) || document.hidden || !inBeeld) return;
    var fm = formaat, C = LAAG[fm], S = SPOOR[fm];
    var dt = Math.min(0.1, (nu - laatsteNu) / 1000 || 0.016); laatsteNu = nu;
    var scene = laag.parentNode, W = scene.clientWidth, H = scene.clientHeight;
    var beeldverhouding = S.w / S.h, Wd = Math.max(W, H * beeldverhouding), k = Wd / S.w, offX = (W - Wd) / 2, offY = (H - Wd / beeldverhouding) / 2;
    var opSpiegel = spiegel ? parseFloat(getComputedStyle(spiegel).opacity) || 0 : 0, opEind = eindEl ? parseFloat(getComputedStyle(eindEl).opacity) || 0 : 0;
    var op = Math.max(opSpiegel, opEind);
    var tOnder = opEind > 0.99 ? T_EIND : (video.currentTime || 0);
    var aV = menging(zacht((tOnder - C.tV) / 1.0), 1, op), aF = menging(zacht((tOnder - C.tFig) / 1.0), 1, opSpiegel) * (1 - opEind);
    function plaats(naam, tijd, x, y) { var m = spoorOp(fm, naam, tijd), a = pas(m, x, y); return { x: a[0], y: a[1], s: Math.sqrt(Math.abs(m[0] * m[4] - m[1] * m[3])) }; }
    function gemengd(naam, x, y) {  // positie nu, zacht overgaand naar het eindbeeld tijdens het kruisverloop
      var a = plaats(naam, tOnder, x, y);
      if (op < 0.001) return a;
      var b = plaats(naam, T_EIND, x, y);
      return { x: menging(a.x, b.x, op), y: menging(a.y, b.y, op), s: menging(a.s, b.s, op) };
    }
    var g = gemengd("gevel", C.vAnker[0], C.vAnker[1]), vb = C.vBreedte * g.s * k;
    vEl.style.opacity = aV.toFixed(3);
    vEl.style.transform = "translate(" + (offX + g.x * k - 50).toFixed(2) + "px," + (offY + g.y * k - 45).toFixed(2) + "px) scale(" + (vb / 100).toFixed(4) + ")";
    laag.style.setProperty("--ks-fig-licht", menging(0.94, 0.8, zacht((tOnder - 13.5) / 3)).toFixed(3));
    for (var i = 0; i < figuren.length; i++) {
      var f = figuren[i];
      if (!f.pad[fm]) { f.el.style.opacity = "0"; continue; }
      var st = figuurStand(f, nu / 1000, fm), p = gemengd("plein", st.x, st.y);
      var maat = (f.hoogte[fm] * 1.1 / 60) * (1 + (st.y - C.diepteY) * C.diepteK) * p.s * k;
      f.kijk += (st.kijk - f.kijk) * Math.min(1, dt * 7);                // omdraaien via een korte vernauwing
      f.el.style.opacity = aF.toFixed(3);
      f.el.style.transform = "translate(" + (offX + p.x * k - 22).toFixed(2) + "px," + (offY + p.y * k - 56 - st.hop * k).toFixed(2) + "px) scale(" + maat.toFixed(4) + ")";
      f.el.style.zIndex = Math.round(p.y);
      f.draai.style.transform = "scaleX(" + f.kijk.toFixed(3) + ")";
      var stil = !st.loopt && f.gedrag !== "zwaai";
      if (stil !== f.stil) { f.stil = stil; f.el.classList.toggle("ks-fig--stil", stil); }
    }
  }
  function zetLaag() {  // de laag draait bij beide bronnen zodra de kaart start
    if (laag && SPOOR && !laagLus) laagLus = window.requestAnimationFrame(laagStap);
  }

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
    zetLaag();
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
    zetLaag();
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
