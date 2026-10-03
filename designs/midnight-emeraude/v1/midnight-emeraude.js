/* Midnight Émeraude v1: alle beweging van dit ontwerp, gebouwd met GSAP (static/vendor/gsap/: gsap, ScrollTrigger, MotionPathPlugin, SplitText).
   De opmaak staat in style.css en bevat zelf geen animaties: zonder GSAP, bij 'minder beweging' of als de gast de beweging stilzet,
   blijft alles gewoon staan en is alles bruikbaar (tik op het zegel en de uitnodiging opent).

   Opbouw
   - Eén master-timeline voor de opening: in het donker komt champagnegoud licht, de envelop komt uit de duisternis en het zegel vangt
     het licht (loopt vanzelf; wacht dan op een tik: addPause 'tik'). Na de tik breekt het zegel, gaat de flap open, komt de kaart
     eruit en rijdt de camera de kaart in. De kaart zakt weg in de avond en wordt de wereld erachter: onscherpe bladeren en kristallen
     vliegen langs de camera, het landgoed gaat branden, de ringen vangen het licht en de namen verschijnen. De lichtvonk uit het zegel
     reist met MotionPath naar de ringen. De hele film is één timeline (de kopfilm zit er als geneste timeline in).
   - ScrollTrigger: parallax in de kop (elke laag een eigen snelheid), regels die uit een masker omhoog komen (SplitText), zachte
     onthullingen, een gouden draad die zich tekent met een lichtvonk erlangs (MotionPath, scrub), het programma, het boogvenster.
   - Rustlussen (sterren, glans op het water, de ringen) staan stil zodra de kop niet in beeld is.
   - Alles zit in gsap.context en gsap.matchMedia: bij 'minder beweging' of Beweging-uit wordt het teruggedraaid naar de rustige eindstand.
   Twee lagen per beeld: .me-l krijgt de beweging van de opening, .me-p de parallax bij het scrollen, zodat ze elkaar nooit in de weg zitten. */
(function () {
  "use strict";
  var html = document.documentElement;
  if (!window.gsap) { html.classList.add("me-ready"); return; }  // GSAP niet geladen: vaste eindstand
  var gsap = window.gsap;
  var plugins = [window.ScrollTrigger, window.MotionPathPlugin, window.SplitText].filter(Boolean);
  gsap.registerPlugin.apply(gsap, plugins);
  var ST = window.ScrollTrigger, SplitText = window.SplitText;

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function boot() {
    performance.mark("me:boot-begin");
    var cover = $(".me-cover");
    var hero = $("#me-hero");
    if (!hero) { html.classList.add("me-ready"); return; }
    html.classList.add("me-ready");
    var vonk = $(".me-vonk");
    var mm = gsap.matchMedia();
    var ctxOpen = null, ctxScroll = null;
    var master = null, waiting = false, filmDone = false;
    var lastW = window.innerWidth, lastH = window.innerHeight;

    /* Beelden alvast uitpakken, zodat het eerste tekenen (de kop die verschijnt, een hoofdstuk dat in beeld komt) niet haperd.
       De kop eerst; de rest van de pagina pas als de browser even niets te doen heeft. */
    function decodeer(lijst) { return Promise.all(lijst.map(function (img) { return img.decode ? img.decode().catch(function () {}) : null; })); }
    var heroDecoded = decodeer($$("img", hero));
    var idle = window.requestIdleCallback || function (f) { return window.setTimeout(f, 1500); };
    idle(function () { decodeer($$(".me-body img")); });

    function paused() { return html.classList.contains("fx-paused"); }
    function coverOn() { return !!cover && html.classList.contains("has-cover") && !cover.hidden; }

    /* ------------------------------------------------------------------ de kopfilm (op de kaart zelf) */
    function heroFilm() {
      var h = gsap.timeline({ defaults: { ease: "power2.out" } });
      var stars = $$(".me-hero .me-ster");
      h.from(stars, { opacity: 0, duration: 1.4, stagger: { amount: 2.2, from: "random" }, ease: "sine.inOut" }, 0)
        // de wereld komt op ons af: de camera rijdt vooruit
        .fromTo(".me-l--wereld", { scale: .8, transformOrigin: "50% 86%" }, { scale: 1, duration: 3.8, ease: "power2.out" }, 0)
        .fromTo(".me-wereld--licht", { opacity: 0 }, { opacity: 1, duration: 2, ease: "sine.inOut" }, .9)
        .from(".me-water", { opacity: 0, duration: 1.6 }, 1.4)
        .fromTo(".me-l--stralen", { opacity: 0, scale: .82, transformOrigin: "50% 100%" }, { opacity: 1, scale: 1, duration: 2.6 }, .5)
        // onscherpe bladeren en bloemen vliegen langs de camera (groter en naar buiten, tot hun rustplek)
        .fromTo(".me-l--voor-l", { xPercent: 36, scale: .52, opacity: 0, transformOrigin: "0% 100%" }, { xPercent: 0, scale: 1, opacity: 1, duration: 3.6, ease: "power3.out" }, 0)
        .fromTo(".me-l--voor-r", { xPercent: -36, scale: .52, opacity: 0, transformOrigin: "100% 100%" }, { xPercent: 0, scale: 1, opacity: 1, duration: 3.6, ease: "power3.out" }, .08)
        .fromTo(".me-l--kristal", { opacity: 0, scale: 1.3, yPercent: -7, transformOrigin: "50% 0%" }, { opacity: 1, scale: 1, yPercent: 0, duration: 3.2 }, .25)
        // de gouden ringen: uit het donker, met het licht dat uit het zegel kwam
        .fromTo(".me-ringw", { opacity: 0, scale: .5, rotationY: 52, transformPerspective: 900, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, rotationY: 0, duration: 2.4, ease: "expo.out" }, 1.3)
        .from(".me-glans", { scale: 0, rotation: -100, opacity: 0, duration: 1, stagger: .28, ease: "back.out(2.2)", transformOrigin: "50% 50%" }, 2.5)
        // de namen
        .from(".me-kicker", { opacity: 0, y: 14, duration: 1.1 }, 2.1)
        .from(".me-naam__in", { yPercent: 118, duration: 1.5, stagger: .3, ease: "expo.out" }, 2.3)
        .from(".me-amp", { opacity: 0, scale: .55, rotation: -14, duration: 1.2, ease: "back.out(1.7)", transformOrigin: "50% 60%" }, 2.7)
        .fromTo(".me-naam__in", { backgroundPosition: "100% 0" }, { backgroundPosition: "0% 0", duration: 2.2, ease: "power1.inOut" }, 3)
        .fromTo(".me-lint", { scaleX: 0, opacity: 0 }, { scaleX: 1, opacity: 1, duration: 1.1, ease: "power3.out", transformOrigin: "50% 50%" }, 3.1)
        .from(".me-tagline", { opacity: 0, y: 12, duration: 1.1 }, 3.5)
        .from(".me-scroll", { opacity: 0, y: -8, duration: .9 }, 4);
      return h;
    }

    /* Rustlussen van de kop: stoppen zodra de kop uit beeld is. */
    function heroIdle() {
      var idle = gsap.timeline({ paused: true });
      var rnd = gsap.utils.random;
      $$(".me-hero .me-ster").sort(function () { return Math.random() - .5; }).slice(0, 8).forEach(function (s) {
        idle.to(s, { opacity: rnd(.2, .45), duration: rnd(1.4, 2.8), repeat: -1, yoyo: true, ease: "sine.inOut" }, rnd(0, 2));
      });
      idle.fromTo(".me-water__glinster", { xPercent: -60 }, { xPercent: 240, duration: 9, repeat: -1, ease: "none" }, 0)
        .to(".me-ringw", { y: -7, rotationY: 7, duration: 4.2, repeat: -1, yoyo: true, ease: "sine.inOut" }, 0)
        .to(".me-glans", { scale: .55, opacity: .5, duration: 1.7, repeat: -1, yoyo: true, ease: "sine.inOut", stagger: { each: .6, repeat: -1, yoyo: true } }, 0)
        .to(".me-scroll svg", { y: 5, duration: 1.3, repeat: -1, yoyo: true, ease: "sine.inOut" }, 0);
      var trig = ST.create({
        trigger: hero, start: "top bottom", end: "bottom top",
        onToggle: function (self) { if (!filmDone) return; if (self.isActive) idle.play(); else idle.pause(); }
      });
      return { idle: idle, trig: trig };
    }

    /* Diepte met de aanwijzer (alleen met een muis): elke laag beweegt een eigen, klein stukje mee; ver weg minder, vooraan meer. */
    var ctxPoint = null;
    function pointerDiepte() {
      if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
      ctxPoint = gsap.context(function () {
        var lagen = [[".me-l--lucht", -5], [".me-l--stralen", -8], [".me-l--wereld", -14], [".me-l--kristal", 20], [".me-l--voor-l", 34], [".me-l--voor-r", 34]];
        var zet = lagen.map(function (l) {
          return { d: l[1], x: gsap.quickTo(l[0], "x", { duration: 1.4, ease: "power3.out" }), y: gsap.quickTo(l[0], "y", { duration: 1.4, ease: "power3.out" }) };
        });
        function beweeg(e) {
          if (window.scrollY > window.innerHeight) return;
          var nx = e.clientX / window.innerWidth - .5, ny = e.clientY / window.innerHeight - .5;
          zet.forEach(function (z) { z.x(nx * 2 * z.d); z.y(ny * 2 * z.d * .6); });
        }
        window.addEventListener("pointermove", beweeg, { passive: true });
        return function () { window.removeEventListener("pointermove", beweeg); };
      }, hero);
    }

    function startIdle() {
      filmDone = true;
      if (refreshNaFilm) { refreshNaFilm = false; ST.refresh(); }
      var s = heroIdle();
      if (s.trig.isActive) s.idle.play();
      pointerDiepte();
    }

    /* ------------------------------------------------------------------ de opening (master-timeline) */
    function buildOpening() {
      performance.mark("me:opening-bouw-begin");
      ctxOpen = gsap.context(function () {
        var envEl = $(".vx", cover);
        var q = gsap.utils.selector(envEl);
        var stage = q(".vx-stage")[0], card = q(".vx-card")[0], flap = q(".vx-flap")[0], flapcast = q(".vx-flapcast")[0], envBody = q(".vx-env")[0];
        var sealTop = q(".vx-sealpart--top")[0], sealBase = q(".vx-sealpart--base")[0], crack = q(".vx-seal-crack")[0];
        var parts = [sealTop, sealBase], glimp = $(".me-glimp", cover);
        var licht = $(".me-cover__licht", cover), aan = $(".me-cover__aan", cover), music = $(".me-cover__music", cover);
        var hint = q(".vx-hint")[0], shadow = q(".vx-shadow")[0];

        // Plekken meten voordat er iets verschuift: het zegel (begin van de vonk), de ringen (einde) en de kaart (de camerarit).
        var vw = window.innerWidth, vh = window.innerHeight;
        var sr = sealTop.getBoundingClientRect(), rr = $(".me-ringw").getBoundingClientRect();
        var sx = sr.left + sr.width / 2, sy = sr.top + sr.height / 2, rx = rr.left + rr.width / 2, ry = rr.top + rr.height * .42;
        var cr = card.getBoundingClientRect(), st = stage.getBoundingClientRect(), er = envEl.getBoundingClientRect();
        var drop = envBody.getBoundingClientRect().width * .7 * .16;     // de envelop zakt een stukje als de kaart eruit is (zoals in de collectie)
        var ccx = cr.left + cr.width / 2, ccy = cr.top + cr.height / 2 - cr.height * .74 + drop;   // waar de kaart uiteindelijk staat
        // Liggend scherm: tot de kaart het beeld vult. Staand scherm: de kaart is liggend en zou dan veel breder dan het scherm worden (tekst
        // door midden); daar rijdt de camera tot de kaart ruim de breedte vult, en lost de rest op in de wereld erachter.
        var push = vw >= vh ? Math.min(3.6, Math.max(vw / (cr.width * 1.02), vh / (cr.height * 1.02)) * 1.2) : Math.min(4, vw / (cr.width * 1.02) * 1.32);

        /* Scherpe camerarit: een kopie van de kaart (zelfde papier, zelfde tekst) staat klaar op de plek waar de kaart eindigt. Zodra de
           kaart helemaal uit de envelop is, neemt de kopie het over en schaalt mee. Omdat hij zonder eigen laag wordt getekend (force3D uit),
           tekent de browser tekst, papier en rand bij elke schaal opnieuw scherp, in plaats van een klein plaatje op te rekken. */
        var kopie = card.cloneNode(true);
        kopie.removeAttribute("id");
        Object.assign(kopie.style, { position: "absolute", left: (ccx - cr.width / 2 - er.left) + "px", top: (ccy - cr.height / 2 - er.top) + "px", width: cr.width + "px",
          height: cr.height + "px", right: "auto", bottom: "auto", margin: "0", zIndex: "30", visibility: "hidden", transform: "none", filter: "none", transition: "none" });
        envEl.appendChild(kopie);
        var kbody = $(".vx-card__body", kopie);

        // Beginstand: donker. Alles wat de opening bestuurt, krijgt zijn eigen stand van GSAP; de CSS van de collectie blijft de rust.
        gsap.set(parts, { x: 0, y: 0, xPercent: -50, yPercent: -52 });
        gsap.set(licht, { opacity: 0, scale: .4 });
        gsap.set(stage, { opacity: .01, y: 40 });   // niet 0: een laag met opacity 0 wordt pas gerasterd als hij zichtbaar wordt (dat gaf een haper bij het oplichten)
        gsap.set([aan, hint, music], { opacity: 0 });
        gsap.set(vonk, { x: sx, y: sy, opacity: 0, scale: .3 });
        gsap.set(glimp, { x: sx, y: sy, opacity: 0, scale: .3 });
        gsap.set(".vx-flap__svg", { filter: "none" });  // lichtfilters op de draaiende flap zijn te zwaar: de flap draait zonder slagschaduw

        var idleWait = null;
        var tl = master = gsap.timeline({ defaults: { ease: "power2.out" } });
        // 1. uit het donker (loopt vanzelf, ongeveer 3 s): champagnegoud licht, de envelop komt op, het zegel vangt het licht
        tl.to(licht, { opacity: 1, scale: 1, duration: 1.9, ease: "power1.out" }, .15)
          .to(stage, { opacity: 1, y: 0, duration: 1.7 }, .6)
          .to(aan, { opacity: 1, duration: 1.1 }, 1.3)
          .to(glimp, { opacity: .7, scale: 1.05, x: sx + 6, y: sy + 4, duration: .8, ease: "sine.inOut" }, 2)
          .to(glimp, { opacity: 0, scale: 1.4, duration: .7, ease: "sine.out" }, 2.8)
          .to([hint, music], { opacity: 1, duration: .8 }, 2.4)
          .addLabel("tik", 3.3)
          .call(function () { waiting = true; if (idleWait) idleWait.kill(); idleWait = gsap.to(licht, { scale: 1.05, duration: 3.2, repeat: -1, yoyo: true, ease: "sine.inOut" }); }, null, "tik-=.05")
          .addPause("tik");

        // 2. na de tik: het zegel geeft mee, vangt het licht en breekt
        tl.to(parts, { scale: .965, duration: .25 }, "tik")
          .to([hint, music, aan], { opacity: 0, duration: .4 }, "tik")
          .fromTo(glimp, { opacity: 0, scale: .5, x: sx - 4, y: sy - 3 }, { opacity: .7, scale: 1, x: sx + 6, y: sy + 3, duration: .25, ease: "power1.out" }, "tik+=.08")
          .to(glimp, { opacity: 0, scale: 1.4, duration: .45 }, "tik+=.33")
          .set(crack, { opacity: 1 }, "tik+=.3")
          .to(sealTop, { yPercent: -59, rotation: -3, scale: 1, duration: .32, ease: "power3.out" }, "tik+=.3")
          .to(sealBase, { yPercent: -51.6, scale: 1, duration: .32, ease: "power3.out" }, "tik+=.3")
          // de lichtvonk verlaat het zegel en zoekt de ringen (MotionPath), over de hele opening
          .to(vonk, { opacity: 1, scale: 1, duration: .5 }, "tik+=.42")
          .to(vonk, {
            motionPath: { path: [{ x: sx, y: sy }, { x: sx + (rx - sx) * .18, y: Math.min(sy, ry) - vh * .2 }, { x: sx + (rx - sx) * .62, y: Math.min(sy, ry) - vh * .08 }, { x: rx, y: ry }], curviness: 1.4 },
            duration: 3.95, ease: "power1.inOut"
          }, "tik+=.42")
          .to(vonk, { scale: 1.5, duration: .3, yoyo: true, repeat: 1, ease: "sine.inOut" }, "tik+=2.2")
          // 3. de flap gaat open (3D)
          .to(flap, { rotationX: 180, duration: 1.05, ease: "power2.inOut" }, "tik+=.6")
          .set(flap, { zIndex: 1 }, "tik+=1.1")
          .to(flapcast, { opacity: 1, duration: .45 }, "tik+=.6")
          .to(flapcast, { opacity: .22, duration: .7, ease: "sine.inOut" }, "tik+=1.1")
          // 4. de kaart: een stukje, dan helemaal eruit, dan naar voren
          .to(card, { yPercent: -27, duration: .36 }, "tik+=1.45")
          .to(card, { yPercent: -108, duration: .6, ease: "power2.inOut" }, "tik+=1.8")
          .to([envBody, shadow], { y: drop, duration: .6, ease: "power2.inOut" }, "tik+=1.8")
          .set(card, { zIndex: 8 }, "tik+=2.4")
          .to(card, { yPercent: -74, scale: 1.02, duration: .45 }, "tik+=2.4")
          // 5. de camera rijdt de kaart in. De scherpe kopie neemt het over en schaalt samen met de envelop (die achterblijft en
          //    onscherp wordt: een natuurlijke scherptediepte); daarna lost de kaart op in de wereld erachter.
          .set(kopie, { visibility: "visible", scale: 1.02, transformOrigin: "50% 50%" }, "tik+=2.85")
          .set(stage, { transformOrigin: (ccx - st.left) + "px " + (ccy - st.top) + "px" }, "tik+=2.85")
          .to([stage, kopie], { scale: push, x: vw / 2 - ccx, y: vh / 2 - ccy, duration: 1.55, ease: "power3.inOut", force3D: false }, "tik+=2.9")
          .set(stage, { visibility: "hidden" }, "tik+=3.75")
          .to(kbody, { opacity: 0, duration: .5, ease: "sine.in" }, "tik+=3.45")
          .to(licht, { opacity: .6, scale: 1.2, duration: 1, ease: "sine.inOut" }, "tik+=3.3")
          .to(cover, { opacity: 0, duration: .6, ease: "power2.in" }, "tik+=3.95")
          .set(cover, { display: "none" }, "tik+=4.62")   // al weg voordat invite.js het scherm sluit: dat spaart daar een herberekening van de hele pagina
          .set(vonk, { autoAlpha: 0 }, "tik+=4.8")
          .add(heroFilm().timeScale(1.3).eventCallback("onComplete", startIdle), "tik+=3.4");
        window.vaylideMidnight = { master: tl };
        // een tik tijdens het begin: de rest van de intro gaat snel, dan begint de opening
        var warm = { klaar: false, stop: false };
        onOpening = function () {
          if (!warm.klaar) { warm.stop = true; return; }   // tik tijdens het opwarmen: opwarmen stopt en de opening begint zo snel mogelijk
          start();
        };
        function start() {
          if (idleWait) idleWait.kill();
          if (tl.time() < tl.labels.tik - 0.01) {
            tl.tweenTo("tik", { duration: .6, ease: "power1.in", onComplete: function () { tl.play(); } });
          } else {
            tl.play();
          }
        }

        /* Opwarmen onder een kort openingsmoment. De eerste keer dat de browser iets tekent, moet hij het rasteren en naar de grafische kaart
           sturen: de filters in de envelop (reliëf, lak), de binnenkant van de flap, de grote kaart en de hele kop. Gebeurde dat pas op het
           moment dat ze in beeld komen, dan haperde het beeld precies daar (100 tot 500 ms). Daarom loopt de tijdlijn vóór de intro langs de
           vier zwaarste momenten, terwijl een vlak van vrijwel pure nacht (opacity .995, dus geen volledige bedekking: dan zou de browser de
           lagen eronder juist overslaan) alles bedekt. Daarna gaat de tijdlijn terug naar het begin. Omdat dat 2 tot 3 s kan duren (de
           grafische kaart staat dan soms even stil), staat daar een bewust, rustig openingsmoment boven: een klein Vaylide-merkteken in een zachte
           champagne gloed, met een gouden lijntje waar een lichtpuntje langs glijdt. Het merkteken staat vanaf het eerste beeld vast
           (geen fade-in, want dat zou juist bevriezen), beweegt alleen zacht en gaat daarna over in de intro. Het is aria-hidden, de
           uitnodiging zelf blijft inert, en bij 'minder beweging' of een al geopende kaart wordt dit niet gebouwd of getoond. */
        var schild = document.createElement("i");
        schild.className = "me-warm";
        schild.setAttribute("aria-hidden", "true");
        document.body.appendChild(schild);
        var merk = $(".me-open");
        var merkLus = null;
        function toonMerk() {
          if (!merk) return;
          merk.classList.add("is-aan");
          merkLus = gsap.timeline();
          merkLus.to($(".me-open__gloed", merk), { opacity: .72, duration: 1.8, yoyo: true, repeat: -1, ease: "sine.inOut" }, 0)
            .to($(".me-open__v", merk), { opacity: .78, duration: 1.8, yoyo: true, repeat: -1, ease: "sine.inOut" }, 0)
            .add(gsap.timeline({ repeat: -1, repeatDelay: .5 })
              .fromTo($(".me-open__glans", merk), { x: -34, opacity: 0 }, { x: 150, duration: 1.5, ease: "sine.inOut" }, 0)
              .to($(".me-open__glans", merk), { opacity: 1, duration: .45, yoyo: true, repeat: 1, ease: "sine.inOut" }, 0), 0);
        }
        function verbergMerk(zacht) {
          if (!merk || !merk.classList.contains("is-aan")) return;
          var klaar = function () { if (merkLus) merkLus.kill(); merkLus = null; merk.classList.remove("is-aan"); gsap.set(merk, { clearProps: "opacity" }); };
          if (zacht) gsap.to(merk, { opacity: 0, duration: .8, ease: "sine.inOut", onComplete: klaar }); else klaar();
        }
        window.setTimeout(function () { verbergMerk(false); }, 12000);   // vangnet: het merkteken blijft nooit staan
        tl.pause(0);
        function wacht(ms) { return new Promise(function (r) { window.setTimeout(r, ms); }); }
        function beeld() { return new Promise(function (r) { window.requestAnimationFrame(function () { r(); }); }); }
        function rustig(max) {   // klaar zodra drie beelden achter elkaar vlot zijn (of na max ms)
          return new Promise(function (res) {
            var vorig = performance.now(), begin = vorig, goed = 0;
            (function f(nu) {
              goed = nu - vorig < 24 ? goed + 1 : 0; vorig = nu;
              if (warm.stop || goed >= 3 || nu - begin > max) res(); else window.requestAnimationFrame(f);
            })(vorig);
          });
        }
        function stap(tijd, max) {
          return function () { if (warm.stop) return null; performance.mark("me:opwarmen-stap"); tl.pause().time(tijd, true); return beeld().then(function () { return rustig(max); }); };
        }
        var t = tl.labels.tik;
        toonMerk();
        var getoond = performance.now();
        performance.mark("me:opwarmen-begin");
        // Het merkteken moet eerst echt getekend zijn voordat het zware werk begint; dan blijft het staan terwijl de kaart even stilvalt.
        beeld().then(function () {
          // De eerste stap duurt het langst (de envelop met zijn filters); op een traag apparaat nemen we niet langer dan 2,4 s, de rest
          // gebeurt dan alsnog tijdens de intro. De kop komt als laatste, zodra de beelden uitgepakt zijn.
          return Promise.resolve().then(stap(t + 1.25, 2400)).then(stap(t + 2.95, 600)).then(stap(t + 4.3, 600))
            .then(function () { return Promise.race([heroDecoded, wacht(2500)]); }).then(stap(t + 6.3, 600));
        }).then(function () {
          // Het merkteken is minstens even lang te zien (anders flitst het), en gaat dan zacht over in de intro.
          return wacht(Math.max(0, 900 - (performance.now() - getoond)));
        }).then(function () {
          tl.pause().time(0, true);
          if (schild.parentNode) schild.parentNode.removeChild(schild);
          warm.klaar = true;
          performance.mark("me:opwarmen-klaar");
          verbergMerk(!warm.stop);
          if (warm.stop) start(); else tl.play();
        });
        performance.mark("me:opening-bouw-klaar");
        return function () { warm.stop = true; verbergMerk(false); if (schild.parentNode) schild.parentNode.removeChild(schild); if (kopie.parentNode) kopie.parentNode.removeChild(kopie); };   // de kopie en het vlak horen bij de film
      }, document.body);
    }
    var onOpening = null;

    /* Zonder envelop (al geopend, of rechtstreeks): alleen de kopfilm, iets rustiger. */
    function buildDirect() {
      ctxOpen = gsap.context(function () {
        var h = heroFilm().eventCallback("onComplete", startIdle);
        h.timeScale(1.5);
        window.vaylideMidnight = { master: h };
      }, document.body);
    }

    document.addEventListener("invite:opening", function (e) {
      if (e.detail && e.detail.reduceMotion) return;  // rustig: geen film
      if (onOpening) { onOpening(); onOpening = null; waiting = false; }
    });
    /* Na het openen meten de scrollhoofdstukken één keer opnieuw, maar niet midden in de film (dat kostte één haperend beeld van ongeveer
       80 ms op het moment dat de namen verschijnen): als de film nog loopt, gebeurt het zodra hij klaar is. */
    var refreshNaFilm = false;
    document.addEventListener("invite:opened", function () { if (master && !filmDone && master.isActive()) refreshNaFilm = true; else ST.refresh(); });
    window.addEventListener("load", function () { ST.refresh(); });

    /* ------------------------------------------------------------------ scrollen */
    function buildScroll() {
      performance.mark("me:scroll-bouw-begin");
      ctxScroll = gsap.context(function () {
        var tr = function (extra) { return Object.assign({ trigger: hero, start: "top top", end: "bottom top", scrub: true }, extra || {}); };

        // De kop: elke laag zijn eigen snelheid (echte parallax); de tekst blijft rustiger en dooft aan het eind.
        gsap.timeline({ defaults: { ease: "none" }, scrollTrigger: tr() })
          .to(".me-l--lucht .me-p", { yPercent: 6 }, 0)
          .to(".me-l--stralen .me-p", { yPercent: 9 }, 0)
          .to(".me-l--wereld .me-p", { yPercent: 15 }, 0)
          .to(".me-l--kristal .me-p", { yPercent: -24 }, 0)
          .to(".me-l--voor-l .me-p", { yPercent: -34, scale: 1.14, transformOrigin: "0% 100%" }, 0)
          .to(".me-l--voor-r .me-p", { yPercent: -34, scale: 1.14, transformOrigin: "100% 100%" }, 0)
          .to(".me-hero__tekst", { yPercent: 16, opacity: .15 }, 0);

        // Onthullingen: zachte opkomst per groep.
        gsap.set(".me-fade", { opacity: 0, y: 24 });
        ST.batch(".me-fade", {
          start: "top 87%", once: true,
          onEnter: function (batch) { gsap.to(batch, { opacity: 1, y: 0, duration: .95, ease: "power3.out", stagger: .1, overwrite: "auto" }); }
        });

        performance.mark("me:splittext-begin");
        // Koppen en tekst: regels komen uit een masker omhoog (SplitText); aria-label blijft de volledige tekst.
        $$(".me-split").forEach(function (host) {
          var ps = $$(":scope > p", host);
          (ps.length ? ps : [host]).forEach(function (el, i) {
            SplitText.create(el, {
              type: "lines", mask: "lines", linesClass: "me-regel", autoSplit: true,
              aria: el.matches("p") ? "none" : "auto",  // aria-label mag niet op een alinea; een kop houdt wel zijn volledige tekst
              onSplit: function (self) {
                return gsap.from(self.lines, {
                  yPercent: 112, duration: .95, ease: "power4.out", stagger: .075, delay: i * .06,
                  scrollTrigger: { trigger: el, start: "top 86%", once: true }
                });
              }
            });
          });
        });

        performance.mark("me:splittext-klaar");
        // De gouden draad: hij tekent zich bij het scrollen en een lichtvonk reist erlangs (MotionPath).
        $$(".me-draad").forEach(function (svg) {
          var pad = $(".me-draad__pad", svg), spark = $(".me-draad__vonk", svg), ringen = $(".me-draad__ringen", svg), steen = $(".me-draad__steen", svg);
          pad.setAttribute("pathLength", "1");
          gsap.set(pad, { strokeDasharray: 1, strokeDashoffset: 1 });
          gsap.set(spark, { opacity: 0 });
          gsap.timeline({ defaults: { ease: "none" }, scrollTrigger: { trigger: svg, start: "top 96%", end: "bottom 50%", scrub: .5 } })
            .to(pad, { strokeDashoffset: 0, duration: 1 }, 0)
            .to(spark, { motionPath: { path: pad, align: pad, alignOrigin: [.5, .5] }, duration: 1 }, 0)
            .to(spark, { opacity: 1, duration: .12 }, 0)
            .to(spark, { opacity: 0, duration: .15 }, .85)
            .from([ringen, steen], { scale: 0, opacity: 0, transformOrigin: "50% 50%", duration: .3, ease: "back.out(2)" }, .42);
        });

        // Donker bladwerk langs de rand beweegt traag mee: de wereld van de kop loopt door.
        $$(".me-blad").forEach(function (b) {
          var flip = b.classList.contains("me-blad--r");
          gsap.fromTo(b, { yPercent: -6, rotation: flip ? 2.5 : -2.5, scaleX: flip ? -1 : 1, transformOrigin: "50% 100%" },
            { yPercent: 6, rotation: flip ? -2.5 : 2.5, ease: "none", scrollTrigger: { trigger: b.parentNode, start: "top bottom", end: "bottom top", scrub: true } });
        });
        $$(".me-nachtsterren").forEach(function (s) {
          gsap.fromTo(s, { yPercent: 4, scale: 1.1 }, { yPercent: -4, ease: "none", scrollTrigger: { trigger: s.parentNode, start: "top bottom", end: "bottom top", scrub: true } });
        });

        // Datum: het grote cijfer komt als een filmtitel naar voren.
        $$(".me-dag__getal").forEach(function (g) {
          gsap.fromTo(g, { scale: .78, opacity: 0, yPercent: 12 }, { scale: 1, opacity: 1, yPercent: 0, ease: "power1.out", scrollTrigger: { trigger: g, start: "top 94%", end: "top 52%", scrub: .6 } });
        });

        // Programma: de gouden lijn groeit mee, de ringetjes verschijnen één voor één.
        $$(".me-prog").forEach(function (list) {
          gsap.fromTo($(".me-prog__lijn", list), { scaleY: 0 }, { scaleY: 1, ease: "none", scrollTrigger: { trigger: list, start: "top 75%", end: "bottom 70%", scrub: .5 } });
        });
        ST.batch(".me-prog__ring", {
          start: "top 90%", once: true,
          onEnter: function (b) { gsap.from(b, { scale: 0, duration: .8, ease: "back.out(2.4)", stagger: .14 }); }
        });

        // Locatie: kijk door het boogvenster; het landgoed beweegt erachter.
        $$(".me-venster").forEach(function (v) {
          gsap.fromTo($(".me-venster__beeld", v), { yPercent: 7, scale: 1.14 }, { yPercent: -7, scale: 1, ease: "none", scrollTrigger: { trigger: v, start: "top bottom", end: "bottom top", scrub: true } });
          gsap.from(v, { scale: .93, opacity: 0, duration: 1.4, ease: "power3.out", scrollTrigger: { trigger: v, start: "top 86%", once: true } });
        });

        // Dresscode: de satijnen linten zwaaien even uit.
        ST.batch(".me-lintje", {
          start: "top 92%", once: true,
          onEnter: function (b) { gsap.fromTo(b, { rotation: 9, transformOrigin: "50% 0%" }, { rotation: 0, duration: 2.2, ease: "elastic.out(1, .4)", stagger: .14 }); }
        });

        // Slot: terug in de avond, met het landgoed en de ringen.
        $$(".me-slot").forEach(function (s) {
          gsap.fromTo($(".me-slot__beeld", s), { yPercent: 9, scale: 1.08 }, { yPercent: -3, scale: 1, ease: "none", scrollTrigger: { trigger: s, start: "top bottom", end: "center center", scrub: true } });
          gsap.from($(".me-slot__ring", s), { y: 46, scale: .8, opacity: 0, rotationY: -34, transformPerspective: 800, duration: 2, ease: "expo.out", scrollTrigger: { trigger: s, start: "top 62%", once: true } });
          gsap.from($(".me-slot__namen", s), { opacity: 0, yPercent: 30, scale: .92, duration: 1.6, ease: "power3.out", scrollTrigger: { trigger: $(".me-slot__namen", s), start: "top 90%", once: true } });
        });
      }, document.body);
      performance.mark("me:scroll-bouw-klaar");
    }

    /* ------------------------------------------------------------------ opbouwen en opruimen */
    function build(withOpening) {
      if (withOpening) {
        if (coverOn()) buildOpening(); else buildDirect();
      }
      buildScroll();
    }
    function teardown() {
      if (ctxOpen) { ctxOpen.revert(); ctxOpen = null; }
      if (ctxScroll) { ctxScroll.revert(); ctxScroll = null; }
      if (ctxPoint) { ctxPoint.revert(); ctxPoint = null; }
      if (vonk) { gsap.set(vonk, { clearProps: "all" }); }
      master = null; onOpening = null; waiting = false; filmDone = false;
    }

    mm.add("(prefers-reduced-motion: no-preference)", function () {
      if (!paused()) build(true);
      // 'Beweging' uit: terug naar de rustige eindstand. Weer aan: alleen de scrollbewegingen (de opening is dan voorbij of rustig).
      var obs = new MutationObserver(function () {
        if (paused()) { teardown(); }
        else if (!ctxScroll) { build(coverOn()); }
      });
      obs.observe(html, { attributes: true, attributeFilter: ["class"] });
      var rt = 0;
      function onResize() {
        window.clearTimeout(rt);
        rt = window.setTimeout(function () {
          var big = Math.abs(window.innerWidth - lastW) > 2 || Math.abs(window.innerHeight - lastH) > 90;
          lastW = window.innerWidth; lastH = window.innerHeight;
          // Alleen opnieuw meten als de film nog niet is begonnen (de metingen voor de vonk en de camerarit hangen aan het scherm).
          if (big && waiting && ctxOpen && !paused()) { ctxOpen.revert(); ctxOpen = null; onOpening = null; waiting = false; buildOpening(); }
        }, 250);
      }
      window.addEventListener("resize", onResize);
      return function () {
        obs.disconnect();
        window.removeEventListener("resize", onResize);
        window.clearTimeout(rt);
        teardown();
      };
    });
  }

  // Pas na DOMContentLoaded: dan heeft invite.js (laadt na dit script) het openingsscherm al klaargezet (klasse has-cover).
  if (document.readyState === "complete") boot();
  else document.addEventListener("DOMContentLoaded", boot);
})();
