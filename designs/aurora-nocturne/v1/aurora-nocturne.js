/* Aurora Nocturne v1: alle beweging van dit ontwerp, gebouwd met GSAP (static/vendor/gsap/: gsap en ScrollTrigger).
   De opmaak (style.css) bevat zelf geen animaties van de opening: zonder GSAP, bij 'minder beweging' of als de gast de beweging stilzet,
   staat alles in de eindstand en werkt alles (tik op het zegel of op "Open uitnodiging": de uitnodiging opent).

   Opbouw
   - Scène 1 (duisternis) speelt vanzelf en wacht dan op een tik: de envelop komt uit het donker doordat licht over het papier glijdt.
   - Eén master-timeline 'film' (tijd 0 = de tik): scène 2 het zegel (drukt, spant, breekt), scène 3 de envelop (één klep met massa en
     schaduwen), scène 4 het lichtportaal (een gat in het donker dat groeit; erachter de paviljoenscène), daarna de camera, de lampencascade
     en de naam-voor-naam onthulling. Tijden staan als getal bij de tween, niet als tientallen losse CSS-vertragingen.
   - Het portaal is één clip-path met een gat (path, evenodd) dat per beeld wordt bijgewerkt, plus een rand van licht (drie SVG-lijnen).
   - De kop heeft per laag een camera (.an-l, GSAP) en een parallax bij het scrollen (.an-p, ScrollTrigger), zodat die elkaar niet in de weg zitten.
   - Rust: CSS-lussen op een paar losse lagen (style.css, alleen met beweging aan) en één stofcanvas met een handvol deeltjes op 16 beelden per seconde (de deeltjes bewegen zo langzaam dat meer niets toevoegt).
   - Alles zit in gsap.context en gsap.matchMedia: bij 'minder beweging' of Beweging-uit wordt het teruggedraaid naar de rustige eindstand. */
(function () {
  "use strict";
  var html = document.documentElement;
  if (!window.gsap) { klasse("an-rust", true); return; }   // GSAP niet geladen: vaste eindstand
  var gsap = window.gsap;
  if (window.ScrollTrigger) gsap.registerPlugin(window.ScrollTrigger);
  var ST = window.ScrollTrigger;

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function paused() { return html.classList.contains("fx-paused"); }
  /* classList.add/remove schrijven het attribuut ook als er niets verandert; dat zou onze MutationObserver weer afvuren (oneindige lus). */
  function klasse(naam, aan) { if (html.classList.contains(naam) !== !!aan) html.classList[aan ? "add" : "remove"](naam); }

  /* ---------------------------------------------------------------- stof: één canvas voor het openingsscherm én de kop */
  var Stof = (function () {
    var canvas = null, ctx = null, W = 0, H = 0, parts = [], running = false, acc = 0, last = 0, t = 0, sprite = null, lampion = null, seen = true;
    function sprites() {
      var s = document.createElement("canvas"); s.width = s.height = 32;
      var g = s.getContext("2d"), gr = g.createRadialGradient(16, 16, 0, 16, 16, 16);
      // De kleur van het stof komt uit het gekozen palet (champagne in de nacht, wit met een zweem goud in de lichte ochtenden).
      var cs = window.getComputedStyle(document.body), kern = cs.getPropertyValue("--an-stof").trim() || "255,244,214", rand = cs.getPropertyValue("--an-stof-2").trim() || "240,222,176";
      gr.addColorStop(0, "rgba(" + kern + ",1)"); gr.addColorStop(0.35, "rgba(" + rand + ",.55)"); gr.addColorStop(1, "rgba(" + rand + ",0)");
      g.fillStyle = gr; g.fillRect(0, 0, 32, 32);
      return s;
    }
    /* Een lampion: een warm papieren lichtje met een gloed. Kleur uit het palet (--an-lampion). */
    function lampionSprite() {
      var cs = window.getComputedStyle(document.body), k = cs.getPropertyValue("--an-lampion").trim() || "255,214,150";
      var s = document.createElement("canvas"); s.width = 64; s.height = 88;
      var g = s.getContext("2d"), halo = g.createRadialGradient(32, 40, 0, 32, 40, 32);
      halo.addColorStop(0, "rgba(" + k + ",.5)"); halo.addColorStop(0.5, "rgba(" + k + ",.16)"); halo.addColorStop(1, "rgba(" + k + ",0)");
      g.fillStyle = halo; g.fillRect(0, 0, 64, 88);
      var body = g.createLinearGradient(0, 22, 0, 62);
      body.addColorStop(0, "rgba(255,246,222,1)"); body.addColorStop(0.45, "rgba(" + k + ",1)"); body.addColorStop(1, "rgba(" + k + ",.78)");
      g.beginPath(); g.moveTo(24, 24); g.bezierCurveTo(14, 34, 14, 52, 25, 62); g.lineTo(39, 62); g.bezierCurveTo(50, 52, 50, 34, 40, 24); g.closePath();
      g.fillStyle = body; g.fill();
      g.strokeStyle = "rgba(120,70,20,.35)"; g.lineWidth = 1; g.stroke();
      g.strokeStyle = "rgba(150,90,30,.28)"; g.beginPath(); g.moveTo(32, 24); g.lineTo(32, 62); g.moveTo(24, 26); g.quadraticCurveTo(19, 44, 26, 62); g.moveTo(40, 26); g.quadraticCurveTo(45, 44, 38, 62); g.stroke();
      g.fillStyle = "rgba(110,66,24,.85)"; g.fillRect(24, 21, 16, 4); g.fillRect(26, 62, 12, 3);
      var vl = g.createRadialGradient(32, 50, 0, 32, 50, 10); vl.addColorStop(0, "rgba(255,255,240,.9)"); vl.addColorStop(1, "rgba(255,255,240,0)");
      g.fillStyle = vl; g.fillRect(20, 38, 24, 24);
      return s;
    }
    function size() {
      if (!canvas) return;
      var w = canvas.clientWidth || window.innerWidth, h = canvas.clientHeight || window.innerHeight;
      if (w === W && h === H) return;
      W = w; H = h; canvas.width = W; canvas.height = H;
      var n = W < 600 ? 16 : 26, nl = W < 600 ? 8 : 12;
      parts = parts.filter(function (p) { return !p.lamp; });
      while (parts.length < n) parts.push(spawn(true));
      parts.length = n;
      // lampionnen alleen in de kop (boven het paviljoen), niet op het openingsscherm
      if (canvas.parentNode && canvas.parentNode.classList.contains("an-stofhaven")) for (var q = 0; q < nl; q++) parts.push(spawnLamp(true));
    }
    function spawn(first) {
      var big = Math.random() < 0.14;
      return {
        x: Math.random() * (W || 400), y: first ? Math.random() * (H || 800) : (H || 800) + 10,
        r: big ? 5 + Math.random() * 5 : 0.9 + Math.random() * 1.6, a: big ? 0.05 + Math.random() * 0.06 : 0.22 + Math.random() * 0.4,
        vx: (Math.random() - 0.5) * 6, vy: -(2.5 + Math.random() * 7) * (big ? 0.6 : 1), ph: Math.random() * 6.28, f: 0.4 + Math.random() * 1.2
      };
    }
    function spawnLamp(first) {
      var h = (W < 600 ? 40 : 54) * (0.65 + Math.random() * 0.8);
      return { lamp: true, x: W * (0.06 + Math.random() * 0.88), y: first ? (H || 800) * (0.2 + Math.random() * 0.8) : (H || 800) + h, h: h,
        vx: (Math.random() - 0.5) * 5, vy: -(5 + Math.random() * 7), ph: Math.random() * 6.28, f: 0.5 + Math.random() * 0.9, a: 0.75 + Math.random() * 0.25 };
    }
    function frame(now) {
      if (!running) return;
      window.requestAnimationFrame(frame);
      var dt = Math.min(0.1, (now - last) / 1000); last = now; acc += dt;
      if (acc < 1 / 16) return;
      dt = acc; acc = 0; t += dt;
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.x += (p.vx + Math.sin(t * 0.3 + p.ph) * (p.lamp ? 6 : 2.2)) * dt; p.y += p.vy * dt;
        if (p.lamp) {
          if (p.y < -p.h || p.x < -30 || p.x > W + 30) { parts[i] = p = spawnLamp(false); }
          // zacht in beeld en weer uit beeld: onderaan en in de bovenste vijfde
          var door = Math.min(1, Math.max(0, p.y / (H * 0.3))) * Math.min(1, Math.max(0, ((H || 800) + p.h - p.y) / (H * 0.12)));
          ctx.globalAlpha = p.a * door * (0.88 + 0.12 * Math.sin(t * p.f * 3 + p.ph));
          ctx.drawImage(lampion, p.x - p.h * 0.36, p.y - p.h * 0.5, p.h * 0.73, p.h);
          continue;
        }
        if (p.y < -12 || p.x < -12 || p.x > W + 12) { parts[i] = p = spawn(false); }
        var tw = 0.62 + 0.38 * Math.sin(t * p.f + p.ph);
        ctx.globalAlpha = p.a * tw;
        var d = p.r * 2.6;
        ctx.drawImage(sprite, p.x - d / 2, p.y - d / 2, d, d);
      }
      ctx.globalAlpha = 1;
    }
    return {
      init: function (c) { canvas = c; if (!canvas) return; ctx = canvas.getContext("2d"); sprite = sprites(); lampion = lampionSprite(); size(); window.addEventListener("resize", size); },
      move: function (host) { if (canvas && host && canvas.parentNode !== host) { host.appendChild(canvas); W = H = 0; size(); } },
      visible: function (v) { seen = v; if (v) this.start(); else this.stop(); },
      start: function () {
        if (!canvas || running || !seen || paused() || document.hidden || !html.classList.contains("fx-motion")) return;
        running = true; last = performance.now(); canvas.style.display = ""; window.requestAnimationFrame(frame);
      },
      stop: function () { running = false; },
      hide: function () { running = false; if (canvas) { ctx.clearRect(0, 0, W, H); canvas.style.display = "none"; } }
    };
  })();


  /* De tekst bepaalt hoe groot het paviljoen onder de kop mag zijn: de top (de torenspits) blijft onder de laatste tekstregel. Zonder dit
     script staat het paviljoen op de gewone maat. */
  function pasPaviljoenAan() {
    var hero = $("#an-hero"), tekst = hero && $(".an-hero__tekst", hero);
    if (!tekst) return;
    var r = hero.getBoundingClientRect(), t = tekst.getBoundingClientRect();
    var nodig = r.height - (t.bottom - r.top) - 12;       // ruimte onder de laatste regel
    // plaathoogte H: top + 4% van H (torenspits) moet onder de tekst liggen, en 6% van H zakt onder de rand
    hero.style.setProperty("--an-ph-max", Math.max(r.height * 0.34, nodig / 0.9).toFixed(0) + "px");
  }

  function boot() {
    var cover = $(".an-cover");
    var hero = $("#an-hero");
    if (!hero) { klasse("an-rust", true); return; }
    var mm = gsap.matchMedia();
    var ctx = null, ctxScroll = null, film = null, intro = null, idleLoops = [], waiting = false, terug = false;   // terug: de film wordt teruggedraaid, dan doen callbacks niets
    var GAT = { on: false, a: 1, b: 18, k: 0, W: 0, H: 0 };
    var gatEl = $(".an-gat"), rand = $(".an-rand"), marker = $(".an-env__open");
    var randPaden = $$(".an-rand path");

    function coverOn() { return !!cover && html.classList.contains("has-cover") && !cover.hidden; }

    pasPaviljoenAan();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(pasPaviljoenAan);
    window.addEventListener("load", pasPaviljoenAan);
    window.addEventListener("resize", pasPaviljoenAan);
    Stof.init($(".an-stof"));
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (e) {
        var inzicht = e[e.length - 1].isIntersecting;
        hero.classList.toggle("an-weg", !inzicht);
        if (!coverOn()) Stof.visible(inzicht);
      }, { threshold: 0.02 }).observe(hero);
    }
    document.addEventListener("visibilitychange", function () { if (document.hidden) Stof.stop(); else Stof.start(); });

    /* ------------------------------------------------------------------ het portaal: een gat in het donker */
    function boog(cx, cy, a, b) {
      var rt = Math.min(a, b), rb = Math.min(a, b, 8), x0 = cx - a, x1 = cx + a, y0 = cy - b, y1 = cy + b;
      function f(n) { return Math.round(n * 10) / 10; }
      return "M" + f(x0) + " " + f(y0 + rt) + "A" + f(rt) + " " + f(rt) + " 0 0 1 " + f(x0 + rt) + " " + f(y0) + "H" + f(x1 - rt) +
        "A" + f(rt) + " " + f(rt) + " 0 0 1 " + f(x1) + " " + f(y0 + rt) + "V" + f(y1 - rb) + "A" + f(rb) + " " + f(rb) + " 0 0 1 " + f(x1 - rb) + " " + f(y1) +
        "H" + f(x0 + rb) + "A" + f(rb) + " " + f(rb) + " 0 0 1 " + f(x0) + " " + f(y1 - rb) + "Z";
    }
    function renderGat() {
      if (!GAT.on) {
        gatEl.style.clipPath = ""; gatEl.style.webkitClipPath = "";
        return;
      }
      var W = GAT.W, H = GAT.H, m = marker.getBoundingClientRect();
      var cx = m.left + (W / 2 - m.left) * GAT.k, cy = m.top + (H / 2 - m.top) * GAT.k;
      var d = boog(cx, cy, GAT.a, GAT.b);
      var clip = 'path(evenodd, "M0 0H' + W + 'V' + H + 'H0Z' + d + '")';
      gatEl.style.clipPath = clip; gatEl.style.webkitClipPath = clip;
      for (var i = 0; i < randPaden.length; i++) randPaden[i].setAttribute("d", d);
    }

    /* ------------------------------------------------------------------ scène 1: duisternis (loopt vanzelf, wacht dan op een tik) */
    function buildIntro() {
      var glans = $(".an-env__glans"), stage = $(".an-env"), acties = $$(".an-open");
      gsap.set(stage, { opacity: 0, y: 10 });
      gsap.set(acties, { opacity: 0, y: 6 });
      gsap.set(".an-stof", { opacity: 0 });
      // de versiering rond de envelop: bloemen groeien uit de hoeken, bogen tekenen zich, een waaier van licht gaat open
      gsap.set(".an-hoek img", { opacity: 0, scale: 0.78, rotation: -5 });
      gsap.set(".an-bogen path", { strokeDasharray: 1, strokeDashoffset: 1 });
      gsap.set(".an-ster", { opacity: 0, scale: 0.4, transformOrigin: "50% 50%" });
      gsap.set(".an-stralen", { opacity: 0, scale: 0.6 });
      gsap.set(".an-fonkel", { opacity: 0 });
      gsap.set([".an-uitn", ".an-dag"], { opacity: 0, y: 10 });
      intro = gsap.timeline({ defaults: { ease: "sine.inOut" } });
      intro.to(".an-hoek img", { opacity: 1, scale: 1, rotation: 0, duration: 2.2, ease: "power3.out", stagger: 0.14 }, 0.05)
        .to(".an-bogen path:not(.an-ster)", { strokeDashoffset: 0, duration: 2.0, ease: "power2.inOut", stagger: 0.18 }, 0.25)
        .to(".an-ster", { opacity: 1, scale: 1, duration: 0.9, ease: "back.out(2.4)", stagger: 0.12 }, 1.2)
        .to(".an-stralen", { opacity: 1, scale: 1, duration: 2.6, ease: "power2.out" }, 0.3)
        .to(".an-fonkel", { opacity: 0.6, duration: 0.8, stagger: { each: 0.08, from: "random" } }, 0.9)
        .to([".an-uitn", ".an-dag"], { opacity: 1, y: 0, duration: 1.2, ease: "power2.out", stagger: 0.2 }, 0.7);
      intro.to(stage, { opacity: 1, y: 0, duration: 1.5, ease: "sine.out" }, 0.1)
        .fromTo(glans, { "--gx": "0%" }, { "--gx": "330%", duration: 2.2, ease: "power1.inOut" }, 0.15)
        .to(".an-stof", { opacity: 1, duration: 1.4 }, 0.3)
        .to(acties, { opacity: 1, y: 0, duration: 0.9, ease: "power2.out", stagger: 0.12 }, 1.0)
        .call(function () { if (terug) return; waiting = true; startIdle(); }, null, 1.6);
      Stof.start();
    }
    function startIdle() {
      var glans = $(".an-env__glans");
      idleLoops.push(gsap.fromTo(".an-bogen", { scale: 1 }, { scale: 1.015, duration: 5, ease: "sine.inOut", yoyo: true, repeat: -1, transformOrigin: "50% 60%" }));
      $$(".an-hoek img").forEach(function (img, i) {
        idleLoops.push(gsap.to(img, { rotation: i % 2 ? -1.6 : 1.6, scale: 1.015, duration: 4.5 + i * 0.7, ease: "sine.inOut", yoyo: true, repeat: -1 }));
      });
      $$(".an-fonkel").forEach(function (f, i) {
        idleLoops.push(gsap.fromTo(f, { opacity: 0.15, scale: 0.6 }, { opacity: 1, scale: 1.25, duration: 1.1 + (i % 5) * 0.35, ease: "sine.inOut", yoyo: true, repeat: -1, delay: (i % 7) * 0.3 }));
      });
      idleLoops.push(gsap.fromTo(glans, { "--gx": "0%" }, { "--gx": "330%", duration: 2.4, ease: "power1.inOut", repeat: -1, repeatDelay: 5.5, delay: 3.5 }));
      // een rustige glans over het zegel
      idleLoops.push(gsap.timeline({ repeat: -1, repeatDelay: 4.2, delay: 2.2 })
        .set("#an-glint", { attr: { cx: 14 } })
        .to("#an-glint", { attr: { opacity: 1 }, duration: 0.25 }, 0)
        .to("#an-glint", { attr: { cx: 86 }, duration: 1.1, ease: "power1.inOut" }, 0)
        .to("#an-glint", { attr: { opacity: 0 }, duration: 0.3 }, 0.85));
    }
    function stopIdle() { idleLoops.forEach(function (l) { l.kill(); }); idleLoops = []; gsap.set("#an-glint", { attr: { opacity: 0 } }); }

    /* ------------------------------------------------------------------ de film (tijd 0 = de tik) */
    function buildFilm() {
      var W = window.innerWidth, H = window.innerHeight;
      var flap = $(".an-flap"), stage = $(".an-env");
      GAT.W = W; GAT.H = H;
      function envW() { return stage.offsetWidth || 280; }
      var tl = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });
      var A = ".an-hero ";

      // Beginstanden van de kop: donker, nog geen lampen, geen tekst; de wereld ligt onder een sluier van licht.
      gsap.set(A + ".an-licht", { opacity: 0 });
      gsap.set(A + ".an-stralen-h", { opacity: 0 });
      gsap.set(A + ".an-hero__licht", { opacity: 1 });
      gsap.set([".an-kicker", ".an-datum", ".an-tagline", ".an-sub", ".an-scroll"], { opacity: 0 });
      gsap.set(".an-naam__in", { opacity: 0 });
      gsap.set(".an-amp__in", { opacity: 0 });
      gsap.set(".an-hh img", { opacity: 0 });
      gsap.set(flap, { transformPerspective: 820, transformOrigin: "50% 0%" });
      gsap.set(".an-stage", { transformOrigin: "50% 15%" });

      /* ---- scène 2: het zegel (0 - 0.85). Het reageert alsof er energie achter zit; het breekt, het ontploft niet. */
      tl.to(".an-open", { opacity: 0, y: 8, duration: 0.3, ease: "power1.in" }, 0)
        .to([".an-uitn", ".an-dag"], { opacity: 0, y: -6, duration: 0.5, ease: "power1.in" }, 0.1)
        .to(".an-fonkel", { opacity: 0, duration: 0.6 }, 0.1)
        .to(".an-bogen", { opacity: 0, scale: 1.3, duration: 0.9, ease: "power2.in", transformOrigin: "50% 50%" }, 0.5)
        .to(".an-stralen", { opacity: 0, scale: 1.3, duration: 0.9, ease: "power2.in" }, 0.5)
        .to(".an-hoek img", { scale: 1.5, opacity: 0, duration: 1.0, ease: "power2.in", stagger: 0.04 }, 0.6)
        .call(function () { if (!terug) stopIdle(); }, null, 0)
        .to(".an-env", { y: 2, scale: 0.994, duration: 0.24, ease: "power2.out" }, 0.0)                // drukbeweging
        .to(".an-zegel", { scale: 0.972, duration: 0.24, ease: "power2.out" }, 0.0)
        .set("#an-ringlicht", { attr: { opacity: 1 } }, 0.1)
        .fromTo("#an-ringlicht", { attr: { "stroke-dashoffset": 0 } }, { attr: { "stroke-dashoffset": -100 }, duration: 0.62, ease: "power1.inOut" }, 0.1)   // gouden lichtlijn door het reliëf
        .fromTo("#an-glint", { attr: { cx: 14, opacity: 0 } }, { attr: { cx: 86, opacity: 1 }, duration: 0.5, ease: "power1.inOut" }, 0.2)                   // minieme reflectie
        .to("#an-glint", { attr: { opacity: 0 }, duration: 0.2 }, 0.58)
        .fromTo(".an-zegel", { x: 0 }, { x: 0.8, duration: 0.05, repeat: 7, yoyo: true, ease: "none" }, 0.28)                                              // spanning in het materiaal
        .to(".an-zegel", { x: 0, duration: 0.05 }, 0.7)
        // de breuk
        .to(".an-zegel--boven", { rotation: -5, y: -3.5, x: -1.2, scale: 1, duration: 0.42, ease: "power3.out" }, 0.74)
        .to(".an-zegel--onder", { y: 2, rotation: 1.2, scale: 1, duration: 0.42, ease: "power3.out" }, 0.74)
        .to(".an-env", { y: 0, scale: 1, duration: 0.5, ease: "back.out(2.2)" }, 0.74)                                                                    // de spanning valt weg
        .set("#an-ringlicht", { attr: { opacity: 0 } }, 0.78);
      // brokjes goud vallen uit de breuk
      $$(".an-chips i").forEach(function (chip, i) {
        var dx = (i - 2) * 11 + (Math.random() - 0.5) * 8;
        tl.fromTo(chip, { x: 0, y: 0, opacity: 0, rotation: 0 }, { x: dx, y: 34 + Math.random() * 40, rotation: (Math.random() - 0.5) * 420, opacity: 0.95, duration: 0.34, ease: "power1.out" }, 0.76 + i * 0.03)
          .to(chip, { y: "+=" + (60 + i * 8), opacity: 0, duration: 0.5, ease: "power2.in" }, 1.1 + i * 0.03);
      });
      // de aurora-achtige lichtlijn loopt vanuit het midden langs de vouw
      tl.set(".an-scheur path", { opacity: 1 }, 0.76)
        .fromTo(".an-scheur path", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.7, ease: "power2.out" }, 0.78)
        .to(".an-scheur__glans", { opacity: 0.0, duration: 0.5, ease: "sine.in" }, 1.7)
        .to(".an-scheur__kern", { opacity: 0, duration: 0.4, ease: "sine.in" }, 1.8);

      /* ---- scène 3: de envelop gaat open (0.8 - 2.5): één klep met massa, schaduwen en traagheid. */
      tl.to(flap, { rotationX: 12, duration: 0.42, ease: "power2.in" }, 0.84)                                // de klep komt zwaar los
        .to(flap, { rotationX: 98, duration: 0.62, ease: "power1.inOut" }, 1.26)                              // en zwaait naar de camera
        .to(flap, { rotationX: 176, duration: 0.62, ease: "power3.out" }, 1.86)                               // valt over
        .to(flap, { rotationX: 171, duration: 0.34, ease: "sine.inOut" }, 2.48)                               // en komt tot rust
        .to(".an-flap__voor .an-flap__tint", { opacity: 0.55, duration: 0.9, ease: "sine.in" }, 0.9)         // de voorkant draait weg uit het licht
        .to(".an-env__vschaduw", { opacity: 0, y: 16, scaleY: 1.5, duration: 0.9, ease: "power1.out" }, 0.9)  // de schaduw onder de klep trekt weg
        .to(".an-env__binnenlicht", { opacity: 1, duration: 1.0, ease: "sine.inOut" }, 1.1)                   // binnenin gaat licht aan
        .to(".an-flap__achter .an-flap__licht", { opacity: 1, duration: 0.9, ease: "sine.inOut" }, 1.7)       // dat valt op de voering van de klep
        .to(".an-env__flapschaduw", { opacity: 0.8, duration: 0.5, ease: "sine.out" }, 2.0)                   // en de klep werpt een schaduw op het blad erachter
        .to(".an-stage", { scale: 1.04, duration: 0.72, ease: "sine.inOut" }, 0.9);                          // de camera schuift langzaam naar binnen

      /* ---- scène 4: het lichtportaal (1.55 - 2.9): een smalle opening van licht die groeit; de camera gaat erdoorheen. */
      tl.call(function () {
        if (terug) return;
        var m = marker.getBoundingClientRect();
        var dy = window.innerHeight / 2 - (m.top + 1);
        GAT.W = window.innerWidth; GAT.H = window.innerHeight;
        film.__dy = dy;
      }, null, 1.5);
      tl.to(rand, { opacity: 1, duration: 0.3, ease: "sine.out" }, 1.52)
        .call(function () { if (terug) return; GAT.on = true; GAT.a = 1; GAT.b = 16; GAT.k = 0; renderGat(); }, null, 1.52)
        .to(GAT, { b: function () { return Math.max(48, Math.min(120, stage.offsetHeight * 0.31)); }, a: 3, duration: 0.56, ease: "power2.out", onUpdate: renderGat }, 1.54)                         // een blad van licht
        .to(".an-stage", { y: function () { return film.__dy || 0; }, scale: function () { return Math.min(3, Math.max(2.5, 600 / envW())); }, duration: 1.4, ease: "power2.inOut", onUpdate: renderGat }, 1.62)                             // de camera schuift de envelop in
        .to(GAT, { a: function () { return GAT.W * 0.75; }, b: function () { return GAT.H * 0.9; }, k: 1, duration: 1.2, ease: "power2.inOut", onUpdate: renderGat }, 1.95) // het portaal opent
        .to(".an-zegel--onder", { opacity: 0, duration: 0.4, ease: "sine.in" }, 2.1)
        .to(rand, { opacity: 0, duration: 0.45, ease: "sine.in" }, 2.55)
        .call(function () { if (terug) return; GAT.on = false; renderGat(); }, null, 3.05);

      /* ---- de wereld erachter: sluier van licht die optrekt, camera die 3 tot 5% terugtrekt, subtiele parallax tussen de dieptelagen. */
      tl.to(A + ".an-hero__licht", { opacity: 0, duration: 2.1, ease: "sine.inOut" }, 1.7)
        .fromTo(A + ".an-l--lucht", { scale: 1.025, transformOrigin: "50% 70%" }, { scale: 1, duration: 3.3, ease: "power2.out" }, 1.55)
        .fromTo(A + ".an-l--ver", { scale: 1.035, transformOrigin: "50% 74%" }, { scale: 1, duration: 3.3, ease: "power2.out" }, 1.55)
        .fromTo(A + ".an-l--mist-a", { scale: 1.04, transformOrigin: "50% 90%" }, { scale: 1, duration: 3.3, ease: "power2.out" }, 1.55)
        .fromTo(A + ".an-l--pav", { scale: 1.05, transformOrigin: "50% 92%" }, { scale: 1, duration: 3.3, ease: "power2.out" }, 1.55)
        .fromTo(A + ".an-l--mist-b", { scale: 1.07, transformOrigin: "50% 100%" }, { scale: 1, duration: 3.3, ease: "power2.out" }, 1.55)
        .fromTo(A + ".an-l--voor-l", { scale: 1.1, transformOrigin: "0% 100%" }, { scale: 1, duration: 3.3, ease: "power2.out" }, 1.55)
        .fromTo(A + ".an-l--voor-r", { scale: 1.1, transformOrigin: "100% 100%" }, { scale: 1, duration: 3.3, ease: "power2.out" }, 1.55);

      /* ---- het lichtmoment: de lampen gaan niet tegelijk aan, maar in een korte cascade (ongeveer 0,8 s tussen de eerste en de laatste). */
      var C = 2.75;
      tl.to(A + ".an-licht--entree", { opacity: 1, duration: 0.6, ease: "sine.inOut" }, C)
        .to(A + ".an-licht--zij", { opacity: 1, duration: 0.6, ease: "sine.inOut" }, C + 0.22)
        .fromTo(A + ".an-licht--kroon", { opacity: 0 }, { opacity: 1, duration: 0.75, ease: "power2.out" }, C + 0.4)
        .fromTo(A + ".an-licht--lampjes", { opacity: 0, clipPath: "inset(0 50% 0 50%)" }, { opacity: 1, clipPath: "inset(0 0% 0 0%)", duration: 0.7, ease: "power1.inOut", clearProps: "clipPath" }, C + 0.68)
        .to(A + ".an-licht--kaarsen", { opacity: 1, duration: 0.5, ease: "sine.inOut" }, C + 0.8)
        .to(A + ".an-stralen-h", { opacity: 1, duration: 2.6, ease: "sine.out", clearProps: "opacity" }, C + 0.5);

      /* ---- de tekst: pas als de omgeving grotendeels zichtbaar is, naam voor naam. */
      var T = 3.05, namen = $$(".an-naam__in");
      tl.fromTo(".an-hh img", { opacity: 0, scale: 1.18, rotation: -4 }, { opacity: 1, scale: 1, rotation: 0, duration: 2.4, ease: "power3.out", stagger: 0.18, clearProps: "scale,rotation" }, T - 0.4);
      tl.fromTo(".an-kicker", { opacity: 0, y: 8, letterSpacing: "0.7em" }, { opacity: 1, y: 0, letterSpacing: "0.46em", duration: 1.1, ease: "power2.out", clearProps: "letterSpacing" }, T)
        .fromTo(namen[0], { opacity: 0, y: 12, clipPath: "inset(0% 0% 100% 0%)", letterSpacing: "0.46em" }, { opacity: 1, y: 0, clipPath: "inset(-20% -20% -20% -20%)", letterSpacing: "0.2em", duration: 1.3, ease: "power3.out", clearProps: "clipPath,letterSpacing" }, T + 0.2);
      namen.slice(1).forEach(function (naam) {
        tl.fromTo(naam, { opacity: 0, y: 12, clipPath: "inset(0% 0% 100% 0%)", letterSpacing: "0.46em" }, { opacity: 1, y: 0, clipPath: "inset(-20% -20% -20% -20%)", letterSpacing: "0.2em", duration: 1.3, ease: "power3.out", clearProps: "clipPath,letterSpacing" }, T + 0.85);
      });
      tl.fromTo(".an-amp__in", { opacity: 0, y: 8, scale: 0.86 }, { opacity: 1, y: 0, scale: 1, duration: 0.9, ease: "power2.out", clearProps: "scale" }, T + 0.62)
        .fromTo(".an-datum", { opacity: 0 }, { opacity: 1, duration: 0.9, ease: "sine.inOut" }, T + 1.3)
        .fromTo(".an-datum i:first-child", { scaleX: 0, transformOrigin: "100% 50%" }, { scaleX: 1, duration: 0.9, ease: "power2.out", clearProps: "transform" }, T + 1.3)
        .fromTo(".an-datum i:last-child", { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: 0.9, ease: "power2.out", clearProps: "transform" }, T + 1.3)
        .fromTo(".an-sub, .an-tagline", { opacity: 0, y: 6 }, { opacity: 1, y: 0, duration: 0.8 }, T + 1.5)
        .fromTo(".an-scroll", { opacity: 0 }, { opacity: 0.9, duration: 0.8, ease: "sine.inOut" }, T + 1.7)
        .call(function () { if (terug) return; Stof.move($(".an-stofhaven")); Stof.start(); klasse("an-rust", true); }, null, T + 2.5);
      tl.eventCallback("onComplete", function () {
        if (terug) return;
        gsap.set([".an-kicker", ".an-datum", ".an-tagline", ".an-sub", ".an-naam__in", ".an-amp__in", ".an-hh img"], { clearProps: "opacity,transform,y" });
        klasse("an-rust", true);
      });
      return tl;
    }

    /* Zonder envelop (al geopend, of rechtstreeks): alleen de wereld die tot rust komt, rustiger en korter. */
    function buildDirect() {
      var tl = gsap.timeline({ defaults: { ease: "power2.out" } });
      var A = ".an-hero ";
      gsap.set(A + ".an-licht", { opacity: 0 });
      gsap.set(A + ".an-stralen-h", { opacity: 0 });
      gsap.set([".an-kicker", ".an-datum", ".an-tagline", ".an-sub", ".an-scroll"], { opacity: 0 });
      gsap.set(".an-naam__in", { opacity: 0, y: 10 });
      gsap.set(".an-amp__in", { opacity: 0 });
      gsap.set(".an-hh img", { opacity: 0 });
      tl.fromTo(".an-hh img", { opacity: 0, scale: 1.12 }, { opacity: 1, scale: 1, duration: 1.8, stagger: 0.12, clearProps: "scale" }, 0.3)
        .fromTo(A + ".an-l--pav", { scale: 1.03, transformOrigin: "50% 92%" }, { scale: 1, duration: 2.2 }, 0)
        .fromTo(A + ".an-l--voor-l", { scale: 1.06, transformOrigin: "0% 100%" }, { scale: 1, duration: 2.2 }, 0)
        .fromTo(A + ".an-l--voor-r", { scale: 1.06, transformOrigin: "100% 100%" }, { scale: 1, duration: 2.2 }, 0)
        .to(A + ".an-licht--entree", { opacity: 1, duration: 0.5 }, 0.2)
        .to(A + ".an-licht--zij", { opacity: 1, duration: 0.5 }, 0.35)
        .to(A + ".an-licht--kroon", { opacity: 1, duration: 0.6 }, 0.5)
        .to(A + ".an-licht--lampjes", { opacity: 1, duration: 0.6 }, 0.7)
        .to(A + ".an-licht--kaarsen", { opacity: 1, duration: 0.5 }, 0.8)
        .to(A + ".an-stralen-h", { opacity: 1, duration: 2, clearProps: "opacity" }, 0.9)
        .to([".an-kicker", ".an-naam__in", ".an-amp__in", ".an-datum", ".an-sub", ".an-tagline", ".an-scroll"], { opacity: 1, y: 0, duration: 0.9, stagger: 0.14, ease: "sine.out" }, 0.9)
        .call(function () { if (terug) return; Stof.move($(".an-stofhaven")); Stof.start(); klasse("an-rust", true); }, null, 1.6)
        .eventCallback("onComplete", function () { gsap.set([".an-kicker", ".an-datum", ".an-tagline", ".an-sub", ".an-naam__in", ".an-amp__in", ".an-scroll", ".an-hh img"], { clearProps: "opacity,transform,y" }); });
      return tl;
    }

    /* ------------------------------------------------------------------ scrollen: een zeer subtiele parallax */
    function buildScroll() {
      if (!ST) return;
      ctxScroll = gsap.context(function () {
        var diepte = { ".an-l--lucht": 1.5, ".an-l--ver": 3, ".an-l--mist-a": 4.5, ".an-l--pav": 6, ".an-l--mist-b": 8, ".an-l--voor-l": 12, ".an-l--voor-r": 12 };
        Object.keys(diepte).forEach(function (sel) {
          gsap.to(sel + " .an-p", { yPercent: diepte[sel], ease: "none", scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: true } });
        });
      }, document.body);
    }

    /* ------------------------------------------------------------------ opbouwen en opruimen */
    function build() {
      if (coverOn()) {
        ctx = gsap.context(function () {
          klasse("an-gsap", true);
          buildIntro();
          film = buildFilm();
          window.vaylideAurora = { film: film, intro: intro, gat: GAT };
        }, document.body);
      } else {
        ctx = gsap.context(function () { buildDirect(); }, document.body);
      }
      buildScroll();
    }
    function teardown() {
      terug = true;
      if (ctx) { ctx.revert(); ctx = null; }
      if (ctxScroll) { ctxScroll.revert(); ctxScroll = null; }
      terug = false;
      idleLoops.forEach(function (l) { l.kill(); }); idleLoops = [];
      GAT.on = false; if (gatEl) renderGat();
      klasse("an-gsap", false);
      klasse("an-rust", true);
      waiting = false; film = null; intro = null;
      if (hero) Stof.move($(".an-stofhaven"));
    }

    document.addEventListener("invite:opening", function (e) {
      if (e.detail && e.detail.reduceMotion) return;   // rustig: geen film
      if (!film) return;
      stopIdle();
      if (intro) intro.progress(1);
      film.play(0);
    });
    document.addEventListener("invite:opened", function () {
      Stof.move($(".an-stofhaven"));
      if (film && film.isActive()) Stof.start();
      else Stof.visible(true);
      if (ST) ST.refresh();
    });

    mm.add("(prefers-reduced-motion: no-preference)", function () {
      if (!paused()) build();
      else { Stof.hide(); klasse("an-rust", true); }
      var obs = new MutationObserver(function () {
        if (paused()) { teardown(); Stof.hide(); }
        else if (!ctx && html.classList.contains("fx-motion")) { build(); }
      });
      obs.observe(html, { attributes: true, attributeFilter: ["class"] });
      var rt = 0;
      function onResize() {
        window.clearTimeout(rt);
        rt = window.setTimeout(function () { if (film && waiting && !film.isActive()) { GAT.W = window.innerWidth; GAT.H = window.innerHeight; } if (ST) ST.refresh(); }, 250);
      }
      window.addEventListener("resize", onResize);
      return function () { obs.disconnect(); window.removeEventListener("resize", onResize); window.clearTimeout(rt); teardown(); };
    });
    // 'Minder beweging': geen stof, geen film.
    mm.add("(prefers-reduced-motion: reduce)", function () { Stof.hide(); klasse("an-rust", true); });
  }

  // Pas na DOMContentLoaded: dan heeft invite.js (laadt na dit script) het openingsscherm al klaargezet (klasse has-cover).
  if (document.readyState === "complete") boot();
  else document.addEventListener("DOMContentLoaded", boot);
})();
