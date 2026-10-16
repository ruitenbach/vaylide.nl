/* Kerstmagie v1: rustige sneeuw met diepte, op het openingsscherm en tijdens het scrollen door de kaart.
   - Drie lagen: kleine verre sneeuw, zachte vlokken ertussen en een paar vage voorgrondvlokken.
   - Het scrollen werkt door op de beweging van de vlokken (verder weg beweegt minder mee): dat geeft diepte.
   - De sneeuw ligt boven de beelden en onder de tekst (zie style.css), valt dus nooit over tekst of formulier.
   - Volgt de knop 'Beweging' en 'minder beweging': html.fx-motion = lopen, html.fx-paused = stilgezet (blijft staan),
     anders (minder beweging) geen sneeuw.
   - Zuinig: sprites worden één keer getekend, de resolutie is begrensd, op een telefoon maximaal 40 beelden per seconde
     en minder vlokken, en tijdens een verborgen tabblad staat alles stil. */
(function () {
  "use strict";

  var html = document.documentElement;
  var TAU = Math.PI * 2;
  var small = Math.min(window.innerWidth, window.innerHeight) < 700;
  var lowPower = (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) || (navigator.deviceMemory && navigator.deviceMemory <= 3);

  function rnd(a, b) { return a + Math.random() * (b - a); }

  /* Zachte ronde vlok: één keer tekenen, daarna alleen kopiëren. */
  function dotSprite(softness) {
    var n = 64, c = document.createElement("canvas");
    c.width = c.height = n;
    var g = c.getContext("2d"), grad = g.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2);
    grad.addColorStop(0, "rgba(246,251,255,1)");
    grad.addColorStop(softness, "rgba(238,246,255,.55)");
    grad.addColorStop(1, "rgba(238,246,255,0)");
    g.fillStyle = grad;
    g.fillRect(0, 0, n, n);
    return c;
  }
  /* Klein kristal met zes armen en zijtakjes, voor een enkele vlok. */
  function crystalSprite() {
    var n = 64, c = document.createElement("canvas");
    c.width = c.height = n;
    var g = c.getContext("2d");
    g.translate(n / 2, n / 2);
    g.strokeStyle = "rgba(244,250,255,.95)";
    g.lineCap = "round";
    g.lineWidth = 2.4;
    for (var i = 0; i < 6; i++) {
      g.save(); g.rotate(i * TAU / 6); g.beginPath();
      g.moveTo(0, 0); g.lineTo(26, 0); g.moveTo(15, 0); g.lineTo(21, 6); g.moveTo(15, 0); g.lineTo(21, -6);
      g.stroke(); g.restore();
    }
    return c;
  }
  var SPRITES = { far: dotSprite(0.5), mid: dotSprite(0.38), near: dotSprite(0.05), crystal: crystalSprite() };

  /* Lagen: aandeel, straal, snelheid, dekking, hoe sterk het scrollen meetelt, zwaai. */
  var LAYERS = [
    { key: "far", share: 0.6, r: [0.9, 1.7], v: [10, 17], a: [0.34, 0.58], scroll: 0.08, sway: [3, 9] },
    { key: "mid", share: 0.32, r: [2, 3.4], v: [18, 28], a: [0.5, 0.85], scroll: 0.22, sway: [8, 22] },
    { key: "near", share: 0.08, r: [6, 10], v: [34, 48], a: [0.1, 0.2], scroll: 0.5, sway: [10, 26] }
  ];

  function Snow(host, options) {
    this.host = host;
    this.fixed = options.fixed;
    this.canvas = document.createElement("canvas");
    this.canvas.className = "kl-snow " + (options.className || "");
    this.canvas.setAttribute("aria-hidden", "true");
    host.insertBefore(this.canvas, host.firstChild);
    this.ctx = this.canvas.getContext("2d");
    this.list = [];
    this.w = 0; this.h = 0; this.dpr = 1;
    this.running = false; this.frozen = false; this.raf = 0; this.last = 0; this.lastDraw = 0; this.t = 0;
    this.scrollY = window.pageYOffset || 0;
    this.fps = small || lowPower ? 40 : 60;
    this.resize();
  }
  Snow.prototype.resize = function () {
    var w = this.fixed ? window.innerWidth : this.host.clientWidth, h = this.fixed ? window.innerHeight : this.host.clientHeight;
    var dpr = Math.min(window.devicePixelRatio || 1, small ? 1.25 : 1.5);
    if (w === this.w && h === this.h && dpr === this.dpr) return;
    this.w = w; this.h = h; this.dpr = dpr;
    this.canvas.width = Math.max(1, Math.round(w * dpr));
    this.canvas.height = Math.max(1, Math.round(h * dpr));
    this.canvas.style.width = w + "px";
    this.canvas.style.height = h + "px";
    this.fill();
  };
  Snow.prototype.fill = function () {
    var area = this.w * this.h, n = Math.round(area / 13500);
    n = Math.max(16, Math.min(small ? 38 : 72, n));
    if (lowPower) n = Math.round(n * 0.7);
    this.list = [];
    for (var li = 0; li < LAYERS.length; li++) {
      var L = LAYERS[li], count = Math.max(li === 2 ? 3 : 1, Math.round(n * L.share));
      for (var i = 0; i < count; i++) this.list.push(this.make(L, false));
    }
  };
  Snow.prototype.make = function (L, top) {
    return {
      L: L, x: rnd(0, this.w), y: top ? -rnd(8, 40) : rnd(0, this.h), r: rnd(L.r[0], L.r[1]), v: rnd(L.v[0], L.v[1]), a: rnd(L.a[0], L.a[1]),
      sw: rnd(L.sway[0], L.sway[1]), f: rnd(0.15, 0.5), p: rnd(0, TAU),
      crystal: L.key === "mid" && Math.random() < 0.07, rot: rnd(0, TAU), spin: rnd(-0.25, 0.25)
    };
  };
  Snow.prototype.draw = function (dt, scrollDelta) {
    var g = this.ctx, w = this.w, h = this.h, i, p, x;
    g.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    g.clearRect(0, 0, w, h);
    var gust = Math.sin(this.t * 0.12) * 3;      /* een lichte, wisselende wind */
    for (i = 0; i < this.list.length; i++) {
      p = this.list[i];
      if (dt) {
        p.y += p.v * dt - scrollDelta * p.L.scroll;
        p.x += (4 + gust) * (0.4 + p.L.scroll) * dt;
        p.rot += p.spin * dt;
        if (p.y > h + 20) { this.list[i] = p = this.make(p.L, true); }
        else if (p.y < -30) { p.y = h + 10; p.x = rnd(0, w); }
        if (p.x > w + 20) p.x = -10;
      }
      x = p.x + Math.sin(this.t * p.f + p.p) * p.sw;
      g.globalAlpha = p.a;
      if (p.crystal) {
        g.save(); g.translate(x, p.y); g.rotate(p.rot);
        g.drawImage(SPRITES.crystal, -7, -7, 14, 14);
        g.restore();
      } else {
        g.drawImage(SPRITES[p.L.key], x - p.r, p.y - p.r, p.r * 2, p.r * 2);
      }
    }
    g.globalAlpha = 1;
  };
  Snow.prototype.frame = function (now) {
    if (!this.running) return;
    this.raf = window.requestAnimationFrame(this.frame.bind(this));
    if (now - this.lastDraw < 1000 / this.fps - 2) return;
    var dt = Math.min(0.05, (now - (this.last || now)) / 1000);
    this.last = now; this.lastDraw = now; this.t += dt;
    var y = window.pageYOffset || 0, d = this.fixed ? Math.max(-120, Math.min(120, y - this.scrollY)) : 0;
    this.scrollY = y;
    this.draw(dt, d);
  };
  Snow.prototype.start = function () {
    if (this.running || document.hidden) return;
    this.running = true; this.frozen = false; this.last = 0; this.scrollY = window.pageYOffset || 0;
    this.canvas.classList.add("is-on");
    this.raf = window.requestAnimationFrame(this.frame.bind(this));
  };
  /* Stilgezet met de knop 'Beweging': het beeld blijft staan zoals het is. */
  Snow.prototype.freeze = function () {
    var was = this.running;
    this.running = false;
    window.cancelAnimationFrame(this.raf);
    if (!was && !this.frozen) { this.draw(0, 0); }
    this.frozen = true;
    this.canvas.classList.add("is-on");
  };
  Snow.prototype.stop = function () {
    this.running = false; this.frozen = false;
    window.cancelAnimationFrame(this.raf);
    this.canvas.classList.remove("is-on");
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  };

  /* Zet de sneeuw aan, stil of uit, afhankelijk van de knop 'Beweging' en 'minder beweging' (klassen van effects.js). */
  function follow(snow, wanted) {
    function apply() {
      if (!wanted()) { snow.stop(); return; }
      if (html.classList.contains("fx-motion")) snow.start();
      else if (html.classList.contains("fx-paused")) snow.freeze();
      else snow.stop();
    }
    apply();
    if (window.MutationObserver) new MutationObserver(apply).observe(html, { attributes: true, attributeFilter: ["class"] });
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { if (snow.running) { snow.running = false; window.cancelAnimationFrame(snow.raf); snow.pausedByTab = true; } }
      else if (snow.pausedByTab) { snow.pausedByTab = false; apply(); }
    });
    var timer = 0;
    window.addEventListener("resize", function () { window.clearTimeout(timer); timer = window.setTimeout(function () { snow.resize(); if (snow.frozen) snow.draw(0, 0); }, 150); });
  }

  /* Openingsscherm: sneeuw over de film en onder de knop en tekst. */
  var cover = document.querySelector("[data-cover]");
  if (cover && html.classList.contains("has-cover")) {
    var coverSnow = new Snow(cover, { fixed: false, className: "kl-snow--cover" });
    follow(coverSnow, function () { return html.classList.contains("has-cover") && !html.classList.contains("is-opening"); });
    document.addEventListener("invite:opening", function () { window.setTimeout(function () { coverSnow.stop(); }, 1500); });
  }

  /* De kaart: één vaste laag over het scherm. Begint zodra de kaart verschijnt. */
  var page = new Snow(document.body, { fixed: true, className: "kl-snow--page" });
  follow(page, function () { return !html.classList.contains("has-cover") || html.classList.contains("is-opening"); });
})();
