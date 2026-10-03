/* VAYLIDE Envelope Collection: de GSAP-opening van Signature Ivory. Licht, zacht en rustig: geen filmische spanning, wel een envelop die
   zorgvuldig wordt geopend. Alleen voor .vx--signature; de andere stijlen blijven op static/js/envelop-collectie.js.

   Gebruik op een pagina: laad static/vendor/gsap/gsap.min.js, dan dit bestand, dan envelop-collectie.js (dat laat een envelop met
   data-vx-gsap met rust). Ontbreekt GSAP, dan doet dit bestand niets en opent envelop-collectie.js de envelop zoals voorheen.
   Na het openen komt, net als bij de klassieke engine, 'vx:opened' (bubbelt) en krijgt de envelop de klasse is-open; envelop.vxReset()
   zet alles terug.

   Wat er gebeurt (alles in één timeline, ongeveer 2,9 s na de tik):
   - Onzichtbaar opwarmen: voordat de envelop verschijnt loopt de timeline langs de drie zwaarste momenten (flap open, kaart eruit, eindstand),
     terwijl de envelop vrijwel doorzichtig is. Zo hoeft de browser de lichtfilters en lagen niet pas tijdens het openen te tekenen (dat gaf
     haperingen van 100 tot 130 ms). Daarna schuift de envelop zacht in beeld.
   - Rust: een nauwelijks merkbare zweving, een zachte lichtstreep over het papier, en met een muis een heel lichte kanteling.
   - Openen: het zegel geeft mee en vangt het licht, breekt, de flap draait open, de kaart komt eruit en schuift naar voren.
   Beweging gebruikt alleen transform en opacity. Elk onderdeel dat tijdens het openen van volgorde wisselt heeft een eigen laag. Bij 'minder beweging'
   (of als de gast de beweging stilzette) fadet de envelop kort uit en komt hij in de eindstand terug. */
(function () {
  "use strict";
  var gsap = window.gsap;
  var envs = document.querySelectorAll(".vx--signature[data-vx]");
  if (!gsap || !envs.length) return;
  var html = document.documentElement;
  var reduceMq = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var fineMq = window.matchMedia ? window.matchMedia("(hover: hover) and (pointer: fine)") : { matches: false };

  function calmNu() { return reduceMq.matches || html.classList.contains("fx-paused"); }

  Array.prototype.forEach.call(envs, function (env) {
    if (env.hasAttribute("data-vx-gsap")) return;
    env.setAttribute("data-vx-gsap", "");
    var q = gsap.utils.selector(env);
    var stage = q(".vx-stage")[0], envBody = q(".vx-env")[0], card = q(".vx-card")[0], flap = q(".vx-flap")[0], flapcast = q(".vx-flapcast")[0];
    var sealTop = q(".vx-sealpart--top")[0], sealBase = q(".vx-sealpart--base")[0], crack = q(".vx-seal-crack")[0];
    var hint = q(".vx-hint")[0], shadow = q(".vx-shadow")[0], sheen = q(".vx-sheen")[0], hit = q(".vx-seal-hit")[0];
    var parts = [sealTop, sealBase], pocketshade = q(".vx-card__pocketshade")[0];

    // Twee kleine hulpvlakken (geen filters): licht dat het zegel vangt en een zachte schaduw onder de kaart terwijl die opstijgt.
    var glimp = document.createElement("i");
    glimp.className = "vx-glimp";
    glimp.setAttribute("aria-hidden", "true");
    envBody.appendChild(glimp);
    var lift = document.createElement("i");
    lift.className = "vx-lift";
    lift.setAttribute("aria-hidden", "true");
    card.insertBefore(lift, card.firstChild);

    var tl = null, idle = null, sweep = null, opened = false, started = false, tiltOff = null;

    function drop() { return envBody.getBoundingClientRect().width * 0.7 * 0.16; }   // de envelop zakt een stukje als de kaart eruit is

    function build() {
      var d = drop();
      gsap.set(parts, { x: 0, y: 0, xPercent: -50, yPercent: -52 });
      gsap.set(glimp, { opacity: 0, scale: .5, xPercent: -50, yPercent: -50 });
      gsap.set(lift, { opacity: 0 });
      tl = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });
      // 1. het zegel geeft mee, vangt het licht en breekt
      tl.to(parts, { scale: .965, duration: .22 }, 0)
        .to(hint, { opacity: 0, duration: .3 }, 0)
        .call(function () { env.classList.add("is-pressed"); }, null, 0)
        .to(glimp, { opacity: .8, scale: 1.05, duration: .26, ease: "power1.out" }, .08)
        .to(glimp, { opacity: 0, scale: 1.5, duration: .5, ease: "sine.out" }, .34)
        .set(crack, { opacity: 1 }, .28)
        .call(function () { env.classList.add("is-cracked"); }, null, .28)
        .to(sealTop, { yPercent: -59, rotation: -3, scale: 1, duration: .32, ease: "power3.out" }, .28)
        .to(sealBase, { yPercent: -51.6, scale: 1, duration: .32, ease: "power3.out" }, .28)
        // 2. de flap draait open
        .call(function () { env.classList.add("is-opening"); }, null, .5)
        .to(flap, { rotationX: 180, duration: 1.05, ease: "power2.inOut" }, .5)
        .to(flapcast, { opacity: 1, duration: .45 }, .5)
        .set(flap, { zIndex: 1 }, 1.02)
        .call(function () { env.classList.add("is-flap-back"); }, null, 1.02)
        .to(flapcast, { opacity: .22, duration: .7, ease: "sine.inOut" }, 1.05)
        // 3. de kaart komt een stukje, dan helemaal eruit, dan naar voren
        .call(function () { env.classList.add("is-card-peek"); }, null, 1.3)
        .to(card, { yPercent: -27, duration: .4 }, 1.3)
        .to(pocketshade, { opacity: .55, duration: .4 }, 1.3)
        .to(lift, { opacity: .45, duration: .4 }, 1.3)
        .call(function () { env.classList.add("is-card-out"); }, null, 1.65)
        .to(card, { yPercent: -108, duration: .62, ease: "power2.inOut" }, 1.65)
        .to(pocketshade, { opacity: 0, duration: .4 }, 1.65)
        .to([envBody, shadow], { y: d, duration: .62, ease: "power2.inOut" }, 1.65)
        .to(lift, { opacity: .75, duration: .62, ease: "sine.inOut" }, 1.65)
        .set(card, { zIndex: 8 }, 2.27)
        .call(function () { env.classList.add("is-card-front"); }, null, 2.27)
        .to(card, { yPercent: -74, scale: 1.02, duration: .55, force3D: false }, 2.27)   // zonder eigen laag: tekst en papierrand blijven scherp
        .to(lift, { opacity: .55, duration: .55 }, 2.27);
      tl.eventCallback("onComplete", finish);
    }

    function finish() {
      if (opened) return;
      opened = true;
      env.classList.add("is-open");
      env.dispatchEvent(new CustomEvent("vx:opened", { bubbles: true }));
    }

    /* ------------------------------------------------------------------------------------ rust (zweving, lichtstreep, kanteling) */
    function startIdle() {
      if (calmNu() || idle) return;
      idle = gsap.timeline({ repeat: -1, yoyo: true }).to(stage, { y: -3, duration: 3.6, ease: "sine.inOut" }, 0)
        .to(shadow, { scale: .975, opacity: .86, duration: 3.6, ease: "sine.inOut" }, 0);
      if (sheen) {
        sweep = gsap.timeline({ repeat: -1, repeatDelay: 6.5, delay: 2.2 })
          .fromTo(sheen, { opacity: 0, backgroundPosition: "110% 0" }, { opacity: 1, duration: .8, ease: "sine.inOut" }, 0)
          .to(sheen, { backgroundPosition: "-10% 0", duration: 2.8, ease: "sine.inOut" }, 0)
          .to(sheen, { opacity: 0, duration: .9, ease: "sine.inOut" }, 1.9);
      }
      if (fineMq.matches && !tiltOff) {
        gsap.set(stage, { transformPerspective: 1100 });
        var ry = gsap.quickTo(stage, "rotationY", { duration: 1.1, ease: "power3.out" });
        var rx = gsap.quickTo(stage, "rotationX", { duration: 1.1, ease: "power3.out" });
        var move = function (e) {
          var b = stage.getBoundingClientRect();
          var nx = (e.clientX - (b.left + b.width / 2)) / Math.max(b.width, 1), ny = (e.clientY - (b.top + b.height / 2)) / Math.max(b.height, 1);
          ry(Math.max(-1, Math.min(1, nx)) * 3); rx(Math.max(-1, Math.min(1, ny)) * -2);
        };
        window.addEventListener("pointermove", move, { passive: true });
        tiltOff = function () { window.removeEventListener("pointermove", move); gsap.to(stage, { rotationY: 0, rotationX: 0, duration: .6, ease: "power2.out" }); tiltOff = null; };
      }
      // Buiten beeld of in een ander tabblad hoeft de zweving niet te lopen.
      if ("IntersectionObserver" in window && !env._vxIo) {
        env._vxIo = new IntersectionObserver(function (en) {
          var zichtbaar = en[0].isIntersecting && !document.hidden;
          [idle, sweep].forEach(function (t) { if (t) t.paused(!zichtbaar); });
        });
        env._vxIo.observe(env);
      }
    }
    function stopIdle(snel) {
      [idle, sweep].forEach(function (t) { if (t) t.kill(); });
      idle = sweep = null;
      if (tiltOff) tiltOff();
      if (sheen) gsap.to(sheen, { opacity: 0, duration: snel ? .1 : .3 });
      gsap.to(stage, { y: 0, duration: snel ? .2 : .5, ease: "power2.out" });
      gsap.to(shadow, { scale: 1, opacity: 1, duration: .5 });
    }

    /* ------------------------------------------------------------------------------------ opwarmen en verschijnen */
    function wacht(ms) { return new Promise(function (r) { window.setTimeout(r, ms); }); }
    function beeld() { return new Promise(function (r) { window.requestAnimationFrame(function () { r(); }); }); }
    function rustig(max) {   // klaar zodra drie beelden achter elkaar vlot zijn (of na max ms)
      return new Promise(function (res) {
        var vorig = performance.now(), begin = vorig, goed = 0;
        (function f(nu) {
          goed = nu - vorig < 24 ? goed + 1 : 0; vorig = nu;
          if (started || goed >= 3 || nu - begin > max) res(); else window.requestAnimationFrame(f);
        })(vorig);
      });
    }
    function stap(tijd, max) {
      return function () { if (started) return null; performance.mark("vx:opwarmen-stap"); tl.pause().time(tijd, true); return beeld().then(function () { return rustig(max); }); };
    }
    function verschijn() {
      gsap.fromTo(stage, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 1.05, ease: "power3.out", clearProps: "opacity", onComplete: startIdle });
      gsap.fromTo(hint, { opacity: 0 }, { opacity: 1, duration: .9, delay: .7, ease: "sine.out" });
    }
    function init() {
      build();
      env.vxOpen = open;
      env.vxTimeline = tl;   // voor de e2e-controles: de timeline op vaste tijden stilzetten
      env.vxReset = reset;
      if (calmNu()) { gsap.set(stage, { opacity: 1 }); return; }
      // De envelop is nu vrijwel doorzichtig (niet 0: een laag met opacity 0 wordt pas gerasterd als hij zichtbaar wordt).
      gsap.set(stage, { opacity: .01 });
      gsap.set(hint, { opacity: 0 });
      var fonts = document.fonts && document.fonts.ready ? Promise.race([document.fonts.ready, wacht(1500)]) : Promise.resolve();
      fonts.then(beeld).then(function () {
        performance.mark("vx:opwarmen-begin");
        return Promise.resolve().then(stap(1.25, 1800)).then(stap(2.1, 500)).then(stap(3.2, 500));
      }).then(function () {
        if (started) return;   // de gast tikte al tijdens het opwarmen: de opening loopt, niet terugzetten
        tl.pause().time(0, true);
        gsap.set(parts, { x: 0, y: 0, xPercent: -50, yPercent: -52 });
        performance.mark("vx:opwarmen-klaar");
        if (!started) verschijn();
      });
    }

    /* ------------------------------------------------------------------------------------ openen en terugzetten */
    function open() {
      if (started) return;
      started = true;
      stopIdle();
      if (!tl) build();
      if (calmNu()) {
        env.classList.add("is-rm");
        gsap.to(stage, { opacity: 0, duration: .3, onComplete: function () {
          tl.progress(1, true);
          ["is-pressed", "is-cracked", "is-opening", "is-flap-back", "is-card-peek", "is-card-out", "is-card-front"].forEach(function (c) { env.classList.add(c); });
          gsap.to(stage, { opacity: 1, duration: .4, onComplete: function () { finish(); } });
        } });
        return;
      }
      gsap.set(stage, { opacity: 1 });
      tl.timeScale(1).play(0);
    }
    function reset() {
      if (tl) tl.pause(0, true);
      ["is-rm", "is-pressed", "is-cracked", "is-opening", "is-flap-back", "is-card-peek", "is-card-out", "is-card-front", "is-open"].forEach(function (c) { env.classList.remove(c); });
      gsap.set([stage, hint], { clearProps: "opacity" });
      gsap.set(stage, { opacity: 1, y: 0 });
      gsap.set(hint, { opacity: 1 });
      gsap.set(parts, { x: 0, y: 0, xPercent: -50, yPercent: -52 });
      opened = false; started = false;
      startIdle();
      if (hit) hit.focus({ preventScroll: true });
    }

    Array.prototype.forEach.call(env.querySelectorAll("[data-vx-open]"), function (b) { b.addEventListener("click", open); });
    init();
  });
})();
