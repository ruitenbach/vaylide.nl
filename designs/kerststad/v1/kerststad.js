/* Kerststad v1: de opening van de peperkoekstad als één scène in de kop.
   Het eerste beeld is extreem dichtbij: de ronde gouden badge met de officiële VAYLIDE-V. De V is het klikpunt (een zachte lichtring en de tekst "Tik op de V om te openen").
   Eén tik speelt de opening één keer, van 0 s tot het einde. Daarna valt de kaart niet stil: de laatste scène loopt door als levende eindloop.
   De eindloop is bij voorkeur een aparte, kleine clip (loop.mp4 / loop-desktop.mp4: dezelfde beelden vanaf lusStart tot het einde van de film) in twee exemplaren (A en B):
   bij lusStart gaat de opening zonder naad over in clip A, en aan het eind van elke ronde komt het andere exemplaar, dat al klaarstaat, met een kruisverloop van 0,8 s boven het eerste.
   Er wordt dan nooit meer in de grote openingsvideo teruggesprongen. Alles rond die clips is een extraatje met terugval: lukt het starten van clip A niet (te traag, niet toegestaan,
   niet ondersteund), dan doet de kaart wat hij deed vóór de clips: de opening speelt uit en de eindloop is een sprong terug naar lusStart met een kruisverloop (spring()).
   De opening start daarna nooit meer vanzelf; alleen "Opnieuw beleven" (een tik) begint opnieuw. De video's zelf zijn niet bewerkt. De lus pauzeert buiten beeld en in een verborgen tabblad.
   Zonder dit script, bij 'minder beweging', bij stilgezette beweging of in de Studio staat het eindbeeld met de groet er direct, met een knop om de opening af te spelen (eenmalig, zonder lus). */
(function () {
  "use strict";
  var hero = document.querySelector("[data-ks]");
  if (!hero) return;
  var html = document.documentElement;
  var q = function (sel) { return hero.querySelector(sel); };
  var video = q("[data-ks-video]"), open = q("[data-ks-open]"), fallback = q("[data-ks-fallback]"), overslaan = q("[data-ks-skip]");
  var spiegel = q("[data-ks-spiegel]"), replay = q("[data-ks-replay]"), status = q("[data-ks-status]"), scroll = q("[data-ks-scroll]");
  var inhoud = document.querySelector(".ks-body");
  var scene = q("[data-ks-scene]"), hint = q("[data-ks-hint]");
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var heeftOpening = hero.hasAttribute("data-ks-opening") && !!open;
  var opslagSleutel = "vierlief-open:" + location.pathname;  // dezelfde sleutel als invite.js: één keer per sessie
  var lusStart = parseFloat(video && video.getAttribute("data-ks-lus")) || 16.5;  // seconde in de opening waar hij overgaat in de loopclip (= het eerste beeld van de clip; per bron: data-ks-lus / data-ks-lus-desktop)
  var breedQuery = window.matchMedia ? window.matchMedia("(min-aspect-ratio: 6/5)") : { matches: false };
  var mobielBron = video ? (video.getAttribute("data-ks-bron") || "") : "";   // zonder <source>: de pagina haalt alleen de gekozen opening binnen, op desktop dus niet ook de mobiele
  var formaat = "";
  var LOOP_FADE = 0.8, LOOP_VOOR = 0.15;                                          // kruisverloop in seconden (zelfde waarde als de CSS-overgang van .ks-loop) en hoeveel eerder het volgende exemplaar start
  var laadFout = false, bezig = false, afgelopen = false, afgespeeld = false, geblokkeerd = false, lusAan = false, hervatNaRust = false, inBeeld = true, waarnemer = null;
  var loopKapot = false;   // waar: de loopclips hebben gefaald in deze ronde; dan gaat de kaart bij elk eind direct naar de oude eindloop, zonder opnieuw te wachten
  var oudeLus = false;   // alleen waar: de oude eindloop (de grote video springt terug) draait; dan, en alleen dan, bedient hervat()/pauzeer() de grote video
  var loopEls = null, loopActief = 0, loopAan = false, loopWissel = false, loopRaf = 0, loopTimer = 0, pauzeTimer = 0, openingStil = false, loopVoortgang = null;
  function veilig(fn) { try { return fn(); } catch (e) { return undefined; } }   // de loopclips zijn een extraatje: een fout daarin mag de V of de opening nooit raken

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
    veilig(maakLoop);   // de kleine loopclip (1 tot 4 MB) laadt al mee
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
    veilig(zetLoopBron);
  }
  if (breedQuery.addEventListener) breedQuery.addEventListener("change", function () { if (!bezig && !lusAan && !afgelopen) kiesBron(); });

  function zoekNaar(t) { try { video.currentTime = t; } catch (e) { /* nog geen metadata */ } }
  function afspelen() {
    var belofte = video.play();
    return belofte && belofte.then ? belofte : Promise.resolve();
  }

  /* ---------- de aparte eindloop: twee exemplaren (A/B) van een kleine clip; elke fout hierin leidt tot de oude eindloop ---------- */
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
      v.addEventListener("error", function () { veilig(loopMislukt); });   // een clip mislukt: terug naar de oude eindloop
      v.addEventListener("ended", function () { if (loopAan && v === loopEls[loopActief]) veilig(wissel); });   // vangnet: als de klok het moment miste
      video.parentNode.insertBefore(v, video.nextSibling);
      return v;
    });
    zetLoopBron();
    return loopEls;
  }
  function loopMislukt() {   // de clips doen het niet (meer): de opening speelt gewoon uit en de kaart eindigt nooit met alleen een stil eindbeeld, maar met de oude eindloop
    if (!loopAan) return;
    loopKapot = true;
    stopLoop();
    if (bezig) { if (video.paused) afspelen().then(null, function () { toonStatisch(false); }); return; }   // einde() volgt vanzelf en zet de oude sprong in
    if (lusAan) spring();
  }
  function primeer(v) {   // iOS laadt een clip pas na play(): het klaarstaande exemplaar krijgt zo zijn eerste beeld
    if (v.readyState >= 2) return;
    var b = v.play();
    if (b && b.then) b.then(function () { v.pause(); try { v.currentTime = 0; } catch (e) { /* nog geen metadata */ } }, function () { /* later opnieuw */ });
  }
  function loopStart() {   // belofte: true als clip A echt speelt (en in 0,8 s boven het beeld komt), anders false binnen 4 s; er wordt niets stuk gemaakt
    return new Promise(function (klaar) {
      var af = false;
      var mislukt = function () { if (af) return; af = true; window.clearTimeout(t); stopLoop(); klaar(false); };
      var t = window.setTimeout(mislukt, 4000);
      try {
        if (loopAan) { af = true; window.clearTimeout(t); klaar(true); return; }
        if (!maakLoop()) { mislukt(); return; }
        var a = loopEls[0];
        loopActief = 0; loopWissel = false;
        loopEls.forEach(function (v) { v.classList.remove("ks-zicht", "ks-boven"); });
        if (a.currentTime > 0.05) { try { a.currentTime = 0; } catch (e) { /* nog geen metadata */ } }
        a.classList.add("ks-boven");
        var b = a.play();   // play() laadt de clip zelf als de browser dat nog niet deed (iOS); de belofte is klaar zodra het echt speelt
        (b && b.then ? b : Promise.resolve()).then(function () {
          if (af) return;
          af = true; window.clearTimeout(t);
          loopAan = true;
          a.classList.add("ks-zicht");
          if (bezig) {   // de opening eronder is na het kruisverloop volledig bedekt: stilzetten (de film eindigt waar clip A eindigt, zie loopWacht)
            window.clearTimeout(pauzeTimer);
            pauzeTimer = window.setTimeout(function () { if (loopAan && bezig && !video.paused) { video.pause(); openingStil = true; } }, LOOP_FADE * 1000 + 150);
          }
          veilig(function () { primeer(loopEls[1]); });
          veilig(loopWacht);
          klaar(true);
        }, mislukt);
      } catch (e) { mislukt(); }
    });
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
      if (bezig && openingStil && x.duration && x.currentTime >= x.duration - 0.2) { veilig(einde); }   // de film is uit: groet, bijschrift en focus
      // stilstand: speelt het exemplaar wel maar loopt de tijd 3 s niet door, dan is de clip vastgelopen: oude eindloop
      var nu = window.performance.now();
      if (!loopVoortgang || loopVoortgang.el !== x || loopVoortgang.t !== x.currentTime || x.paused || !inBeeld) loopVoortgang = { el: x, t: x.currentTime, nu: nu };
      else if (nu - loopVoortgang.nu > 3000) { loopVoortgang = null; veilig(loopMislukt); return; }
      if (loopWissel) return;
      if (x.duration && !x.paused && x.currentTime >= x.duration - LOOP_FADE - LOOP_VOOR) veilig(wissel);
    };
    loopRaf = window.requestAnimationFrame(stap);
  }
  function stopLoop() {
    loopAan = false; loopWissel = false; openingStil = false; loopVoortgang = null;
    window.cancelAnimationFrame(loopRaf); window.clearTimeout(loopTimer); window.clearTimeout(pauzeTimer);
    if (!loopEls) return;
    loopEls.forEach(function (v) {
      v.classList.remove("ks-zicht", "ks-boven"); v.pause();
      try { if (v.currentTime > 0) v.currentTime = 0; } catch (e) { /* nog geen metadata */ }
    });
  }
  function volgOpening() {   // op lusStart (iets eerder, de clip heeft even nodig) probeert de opening over te gaan in loopclip A; lukt dat niet, dan speelt hij gewoon uit
    if (!video.requestVideoFrameCallback) return;   // zonder dit (oudere browsers) volgt de overgang via timeupdate, zie onderaan
    var cb = function (nu, meta) {
      if (!bezig || loopAan) return;
      if (meta.mediaTime >= lusStart - 0.08) { loopStart(); return; }
      video.requestVideoFrameCallback(cb);
    };
    video.requestVideoFrameCallback(cb);
  }

  function kanZoeken() {  // een server zonder Range-verzoeken geeft een video die niet kan springen: dan geen eindloop (anders begint hij weer bij 0)
    try { var z = video.seekable; return z.length > 0 && z.end(z.length - 1) >= lusStart + 0.5; } catch (e) { return false; }
  }
  function springNaarLus(klaar) {  // naar lusStart springen (pas als de metadata er is: WebKit negeert een sprong ervoor); lukt dat niet binnen 8 s, dan het stilstaande eindbeeld
    var opnieuw_ = false;
    var ruim = function () { window.clearTimeout(wacht); video.removeEventListener("seeked", gedaan); video.removeEventListener("loadedmetadata", spring_); };
    var wacht = window.setTimeout(function () { ruim(); toonStatisch(false); }, 8000);
    var gedaan = function () {
      if (Math.abs(video.currentTime - lusStart) > 1) {   // een eerdere, nog openstaande sprong (naar 0) meldt zich: één keer opnieuw naar lusStart, anders opgeven
        if (!opnieuw_) { opnieuw_ = true; zoekNaar(lusStart); return; }
        ruim(); toonStatisch(false); return;
      }
      ruim(); klaar();
    };
    var spring_ = function () { video.removeEventListener("loadedmetadata", spring_); video.addEventListener("seeked", gedaan); zoekNaar(lusStart); };
    if (video.readyState >= 1) spring_(); else video.addEventListener("loadedmetadata", spring_);
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
        oudeLus = true;
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
      hero.classList.add("ks-eind");     // het eindbeeld blijft staan tot de eindloop speelt en lost dan op
      var oudeLoop = function () {       // terugval: de oude eindloop (de grote video springt naar lusStart)
        if (!geladen) { video.preload = "auto"; geladen = true; }
        springNaarLus(function () { afspelen().then(function () { oudeLus = true; hero.classList.remove("ks-eind"); }, function () { toonStatisch(false); }); });
      };
      if (loopKapot) oudeLoop(); else loopStart().then(function (ok) { if (ok) hero.classList.remove("ks-eind"); else { loopKapot = true; oudeLoop(); } });
    }
  }

  function einde() {  // de film is uit (de opening zelf, of clip A bij zijn eind): één keer afhandelen
    if (afgelopen && !bezig && !oudeLus) return;   // één keer afhandelen; de oude eindloop mag wel bij elk eind van de video opnieuw
    afgelopen = true; bezig = false;
    onthoud();
    if (rustig()) { toonStatisch(true); return; }
    naarLus(false);
    if (!loopAan) {   // draait de loopclip nog niet, dan nu proberen; lukt dat niet, dan de oude sprong terug (en de volgende rondes direct)
      if (loopKapot) spring(); else loopStart().then(function (ok) { if (!ok) { loopKapot = true; spring(); } });
    }
    zeg("De kerstkaart is geopend. Scroll verder voor de rest van de kaart.");
    if (scroll) scroll.focus({ preventScroll: true });
  }

  function laadt(aan) {   // de tik krijgt direct zichtbare reactie, ook als de opening nog laadt: de kaart staat dan al in "opening start"
    hero.classList.toggle("ks-laadt", aan);
    if (!hint) return;
    if (aan) { if (!hint.hasAttribute("data-tekst")) hint.setAttribute("data-tekst", hint.textContent); hint.textContent = "EVEN LADEN…"; }
    else if (hint.hasAttribute("data-tekst")) { hint.textContent = hint.getAttribute("data-tekst"); hint.removeAttribute("data-tekst"); }
  }
  function speel() {  // moet vanuit een tik of toets komen: de afspeelstart hoort bij het gebaar
    veilig(stopLoop); oudeLus = false; loopKapot = false; lusAan = false; zetSprong(false); kiesBron(); veilig(maakLoop);
    hero.classList.remove("ks-eind", "ks-finished", "ks-klaar", "ks-lus");
    laadt(true); if (open) open.disabled = true; zeg("De opening wordt geladen.");
    zoekNaar(0);
    afspelen().then(function () {
      geblokkeerd = false; afgespeeld = true; bezig = true; afgelopen = false;
      laadt(false);
      hero.classList.add("ks-playing");
      veilig(volgOpening);
      if (fallback) fallback.hidden = true;
      if (open) open.disabled = true;
      if (replay) replay.hidden = true;
      vergrendel(true);
      zeg("De opening speelt.");
    }, function () {
      geblokkeerd = true; bezig = false;
      laadt(false); if (open) open.disabled = false;
      if (fallback) { fallback.hidden = false; fallback.focus({ preventScroll: true }); }
      zeg("De video kon niet vanzelf starten. Tik op Speel de opening af.");
      knopTekst();
    });
  }
  if (video) {
    video.addEventListener("ended", einde);
    video.addEventListener("timeupdate", function () { if (bezig && !loopAan && !video.requestVideoFrameCallback && video.currentTime >= lusStart - 0.1) veilig(loopStart); });
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
    veilig(stopLoop); oudeLus = false; laadt(false);
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
    veilig(stopLoop); oudeLus = false; laadt(false); lusAan = false; bezig = false; kiesBron();
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
  function hervat() {
    if (loopAan) {
      if (!inBeeld || document.hidden || rustig()) return;
      loopEls.forEach(function (v, i) { if (v.classList.contains("ks-zicht") || (loopWissel && i !== loopActief)) { var b = v.play(); if (b && b.catch) b.catch(function () { /* tik nodig */ }); } });
      return;
    }
    if (oudeLus && inBeeld && !document.hidden && !rustig() && video.paused && !video.seeking) afspelen().then(null, function () { toonStatisch(false); });
  }
  function pauzeer() {
    if (loopAan) { loopEls.forEach(function (v) { v.pause(); }); return; }
    if (oudeLus && !video.paused) video.pause();
  }
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
  window.addEventListener("pagehide", function () { if (video) video.pause(); veilig(pauzeer); });

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
      if (!(c && c.saveData)) naarLus(true);
      return;
    }
    vergrendel(true);
    if ("requestIdleCallback" in window) window.requestIdleCallback(laadVoor, { timeout: 4000 }); else window.setTimeout(laadVoor, 2500);
  }
  start();
})();
