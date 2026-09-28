/* Vaylide homepage: de kaart in de kop in 3D, met glans en gouden sterretjes.
   - De kaart kantelt mee met de muis; zonder muis (telefoon) draait hij vanzelf rustig heen en weer.
   - De lichtglans volgt de muis en de achtergrondfoto schuift een klein beetje tegengesteld mee.
   - Gouden sterretjes twinkelen rond de kaart; bewegen over de kop laat een spoortje glitter achter.
   Niets hiervan bij 'minder beweging'. De tekenlus stopt als de kop uit beeld is of het tabblad verborgen. */
(function () {
  "use strict";
  var hero = document.querySelector("[data-hero3d]");
  if (!hero) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;
  var stage = hero.querySelector(".card-stage");
  var media = hero.querySelector(".hero__media");
  var canvas = hero.querySelector(".hero__sparkles");
  if (!stage || !media || !canvas || !canvas.getContext) return;
  var ctx = canvas.getContext("2d");

  var MAX_TILT = 14; // graden
  var target = { rx: 0, ry: 0, gx: 30, gy: 20, px: 0, py: 0 };
  var now = { rx: 0, ry: 0, gx: 30, gy: 20, px: 0, py: 0 };
  var pointer = null; // laatste muispositie binnen de kop (in pixels van het canvas)
  var lastPointerAt = 0;
  var trailDist = 0;
  var visible = true;
  var running = false;
  var dpr = 1, width = 0, height = 0;
  var sparkles = [];
  var spawnClock = 0;
  var lastTime = 0;

  function resize() {
    var r = media.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = r.width; height = r.height;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function cardBox() {
    var m = media.getBoundingClientRect();
    var c = stage.getBoundingClientRect();
    return { x: c.left - m.left, y: c.top - m.top, w: c.width, h: c.height };
  }

  hero.addEventListener("pointermove", function (e) {
    if (e.pointerType === "touch") return;
    var c = stage.getBoundingClientRect();
    var m = media.getBoundingClientRect();
    var h = hero.getBoundingClientRect();
    // Kantelen ten opzichte van het midden van de kaart, begrensd.
    var dx = (e.clientX - (c.left + c.width / 2)) / (h.width / 2);
    var dy = (e.clientY - (c.top + c.height / 2)) / (h.height / 2);
    dx = Math.max(-1, Math.min(1, dx)); dy = Math.max(-1, Math.min(1, dy));
    target.ry = dx * MAX_TILT;
    target.rx = -dy * MAX_TILT * 0.8;
    target.gx = Math.max(0, Math.min(100, ((e.clientX - c.left) / c.width) * 100));
    target.gy = Math.max(0, Math.min(100, ((e.clientY - c.top) / c.height) * 100));
    target.px = dx; target.py = dy;
    var p = { x: e.clientX - m.left, y: e.clientY - m.top };
    // Spoortje glitter: een sterretje per ~14 pixels beweging (de afstand telt op over kleine bewegingen).
    if (pointer) {
      trailDist += Math.hypot(p.x - pointer.x, p.y - pointer.y);
      var n = 0;
      while (trailDist > 14 && n < 4) { trailDist -= 14; n++; spawn(p.x + rand(-8, 8), p.y + rand(-8, 8), true); }
      if (trailDist > 14) trailDist = 0;
    }
    pointer = p;
    lastPointerAt = performance.now();
    stage.classList.add("is-actief");
    start();
  });
  hero.addEventListener("pointerleave", function () {
    pointer = null;
    stage.classList.remove("is-actief");
  });

  function rand(a, b) { return a + Math.random() * (b - a); }

  // Vooral goud (zichtbaar op de lichte foto), af en toe wit.
  var KLEUREN = ["214, 162, 72", "236, 190, 96", "196, 140, 52", "255, 222, 150", "255, 255, 255"];
  function spawn(x, y, trail) {
    if (sparkles.length > 110) return;
    sparkles.push({
      x: x, y: y,
      vx: rand(-8, 8), vy: trail ? rand(-18, 4) : rand(-14, -4),
      size: trail ? rand(4, 7.5) : rand(4.5, 11),
      life: 0, max: trail ? rand(0.6, 1.1) : rand(1.2, 2.6),
      rot: rand(0, Math.PI), spin: rand(-1.2, 1.2),
      color: KLEUREN[Math.floor(Math.random() * KLEUREN.length)]
    });
  }

  // Sterretje met vier punten en een zachte gloed.
  function drawSparkle(s, alpha) {
    var r = s.size;
    ctx.save();
    ctx.translate(s.x, s.y);
    ctx.rotate(s.rot);
    var glow = ctx.createRadialGradient(0, 0, 0, 0, 0, r * 2.4);
    glow.addColorStop(0, "rgba(" + s.color + "," + (0.55 * alpha) + ")");
    glow.addColorStop(1, "rgba(" + s.color + ",0)");
    ctx.fillStyle = glow;
    ctx.beginPath(); ctx.arc(0, 0, r * 2.4, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "rgba(" + s.color + "," + alpha + ")";
    ctx.beginPath();
    ctx.moveTo(0, -r); ctx.quadraticCurveTo(r * 0.12, -r * 0.12, r, 0);
    ctx.quadraticCurveTo(r * 0.12, r * 0.12, 0, r); ctx.quadraticCurveTo(-r * 0.12, r * 0.12, -r, 0);
    ctx.quadraticCurveTo(-r * 0.12, -r * 0.12, 0, -r);
    ctx.fill();
    ctx.restore();
  }

  function frame(t) {
    if (!running) return;
    var dt = Math.min(0.05, (t - (lastTime || t)) / 1000);
    lastTime = t;

    // Zonder muis draait de kaart vanzelf rustig heen en weer.
    if (!pointer || t - lastPointerAt > 2500) {
      var s = t / 1000;
      target.ry = Math.sin(s * 0.6) * 10;
      target.rx = Math.cos(s * 0.45) * 5;
      target.gx = 50 + Math.sin(s * 0.6) * 40;
      target.gy = 30 + Math.cos(s * 0.45) * 20;
      target.px = Math.sin(s * 0.6) * 0.6;
      target.py = Math.cos(s * 0.45) * 0.4;
    }
    var k = 1 - Math.pow(0.001, dt); // soepel naar het doel
    ["rx", "ry", "gx", "gy", "px", "py"].forEach(function (key) { now[key] += (target[key] - now[key]) * k; });
    stage.style.setProperty("--rx", now.rx.toFixed(2) + "deg");
    stage.style.setProperty("--ry", now.ry.toFixed(2) + "deg");
    stage.style.setProperty("--gx", now.gx.toFixed(1) + "%");
    stage.style.setProperty("--gy", now.gy.toFixed(1) + "%");
    stage.style.setProperty("--px", now.px.toFixed(3));
    stage.style.setProperty("--py", now.py.toFixed(3));
    media.style.setProperty("--hx", now.px.toFixed(3));
    media.style.setProperty("--hy", now.py.toFixed(3));

    // Nieuwe sterretjes rond de kaart, ongeveer veertien per seconde.
    spawnClock += dt;
    var box = cardBox();
    while (spawnClock > 0.07) {
      spawnClock -= 0.07;
      var edge = Math.random();
      spawn(box.x + rand(-0.25, 1.25) * box.w, box.y + (edge < 0.7 ? rand(-0.15, 1.1) : rand(0.9, 1.15)) * box.h, false);
    }

    ctx.clearRect(0, 0, width, height);
    for (var i = sparkles.length - 1; i >= 0; i--) {
      var p = sparkles[i];
      p.life += dt;
      if (p.life >= p.max) { sparkles.splice(i, 1); continue; }
      p.x += p.vx * dt; p.y += p.vy * dt; p.rot += p.spin * dt;
      var f = p.life / p.max;
      var alpha = Math.sin(Math.PI * f) * (0.75 + 0.25 * Math.sin(p.life * 14)); // opkomen, twinkelen, vervagen
      drawSparkle(p, Math.max(0, alpha));
    }
    requestAnimationFrame(frame);
  }

  function start() {
    if (running || !visible || document.hidden) return;
    running = true;
    lastTime = 0;
    requestAnimationFrame(frame);
  }
  function stop() { running = false; }

  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting;
      if (visible) start(); else stop();
    }).observe(hero);
  }
  document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else start(); });
  window.addEventListener("resize", resize);
  resize();
  start();
})();
