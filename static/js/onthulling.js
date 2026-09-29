/* De onthulling na een geslaagde betaling: de show (envelop, kaart, titel) via CSS-klasse .is-spelen, plus
   gouden confetti, vuurwerk en goudstof op een canvas. Bij 'minder beweging' geen show: alles staat al in de
   eindstand (zie onthulling.css). Zonder JavaScript ook. */
(function () {
  "use strict";
  var stage = document.querySelector("[data-onthulling]");
  if (!stage) return;

  /* Link kopiëren (alleen met JavaScript zichtbaar) */
  var copy = stage.querySelector("[data-kopieer]");
  if (copy && navigator.clipboard) {
    copy.hidden = false;
    copy.addEventListener("click", function () {
      navigator.clipboard.writeText(copy.getAttribute("data-kopieer")).then(function () {
        copy.textContent = "Gekopieerd!";
        window.setTimeout(function () { copy.textContent = "Link kopiëren"; }, 2200);
      });
    });
  }
  stage.querySelectorAll("[data-select-all]").forEach(function (input) {
    input.addEventListener("focus", function () { input.select(); });
  });

  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;

  var canvas = stage.querySelector("[data-confetti]");
  var ctx = canvas && canvas.getContext ? canvas.getContext("2d") : null;
  var again = stage.querySelector("[data-onthulling-opnieuw]");
  var COLORS = ["#E9C877", "#FFE9A8", "#C9A45C", "#FFF6DA", "#F2B8B5", "#FFFFFF", "#D8A7C0"];
  var parts = [], sparks = [], timers = [], raf = 0, width = 0, height = 0, dpr = 1, dustUntil = 0;

  function size() {
    if (!canvas) return;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = stage.clientWidth;
    height = stage.clientHeight;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function rand(a, b) { return a + Math.random() * (b - a); }
  function pick(list) { return list[(Math.random() * list.length) | 0]; }

  // Een uitbarsting confetti vanuit een punt (bijv. de envelop), omhoog en opzij.
  function burst(x, y, count, power) {
    for (var i = 0; i < count; i++) {
      var angle = rand(-Math.PI * 0.95, -Math.PI * 0.05);
      var speed = rand(power * 0.45, power);
      parts.push({
        x: x, y: y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
        w: rand(6, 11), h: rand(9, 16), rot: rand(0, Math.PI * 2), vr: rand(-0.25, 0.25),
        flip: rand(0, Math.PI * 2), vf: rand(0.08, 0.22), color: pick(COLORS),
        shape: Math.random() < 0.18 ? "ster" : (Math.random() < 0.3 ? "rond" : "strook"), life: 0, max: rand(240, 380)
      });
    }
  }

  // Vuurwerk: een ring van vonken met een staart.
  function firework(x, y) {
    var n = 46, color = pick(["#FFE9A8", "#E9C877", "#FFF6DA", "#F2B8B5"]);
    for (var i = 0; i < n; i++) {
      var a = (i / n) * Math.PI * 2, s = rand(2.2, 4.2);
      sparks.push({ x: x, y: y, px: x, py: y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: 0, max: rand(55, 80), color: color });
    }
  }

  function dust() {
    if (performance.now() > dustUntil || parts.length > 260) return;
    parts.push({ x: rand(0, width), y: -10, vx: rand(-0.3, 0.3), vy: rand(0.6, 1.4), w: rand(2, 4), h: rand(2, 4), rot: 0, vr: 0,
                 flip: 0, vf: 0, color: pick(["#FFE9A8", "#E9C877", "#FFFFFF"]), shape: "rond", life: 0, max: 600, stof: true });
  }

  function star(r) {
    ctx.beginPath();
    for (var i = 0; i < 10; i++) {
      var rr = i % 2 ? r * 0.45 : r, a = (i / 10) * Math.PI * 2 - Math.PI / 2;
      ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
    }
    ctx.closePath();
    ctx.fill();
  }

  function frame() {
    ctx.clearRect(0, 0, width, height);
    if (Math.random() < 0.5) dust();
    for (var i = parts.length - 1; i >= 0; i--) {
      var p = parts[i];
      p.life++;
      if (!p.stof) { p.vx *= 0.985; p.vy = p.vy * 0.985 + 0.16; p.vx += Math.sin(p.life / 12 + p.flip) * 0.04; }
      p.x += p.vx; p.y += p.vy; p.rot += p.vr; p.flip += p.vf;
      if (p.y > height + 30 || p.life > p.max) { parts.splice(i, 1); continue; }
      var fade = Math.min(1, (p.max - p.life) / 40);
      ctx.save();
      ctx.globalAlpha = p.stof ? 0.7 * fade : fade;
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.fillStyle = p.color;
      if (p.shape === "ster") { ctx.shadowColor = "#FFE9A8"; ctx.shadowBlur = 8; star(p.w * 0.8); }
      else if (p.shape === "rond") { ctx.beginPath(); ctx.arc(0, 0, p.w / 2, 0, Math.PI * 2); ctx.fill(); }
      else { ctx.scale(1, Math.cos(p.flip)); ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); }
      ctx.restore();
    }
    ctx.lineCap = "round";
    for (var j = sparks.length - 1; j >= 0; j--) {
      var s = sparks[j];
      s.life++;
      s.px = s.x; s.py = s.y;
      s.vx *= 0.96; s.vy = s.vy * 0.96 + 0.05;
      s.x += s.vx; s.y += s.vy;
      if (s.life > s.max) { sparks.splice(j, 1); continue; }
      ctx.globalAlpha = 1 - s.life / s.max;
      ctx.strokeStyle = s.color;
      ctx.shadowColor = s.color;
      ctx.shadowBlur = 10;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(s.px - s.vx * 3, s.py - s.vy * 3);
      ctx.lineTo(s.x, s.y);
      ctx.stroke();
    }
    ctx.shadowBlur = 0;
    ctx.globalAlpha = 1;
    if (parts.length || sparks.length || performance.now() < dustUntil) raf = window.requestAnimationFrame(frame);
    else { raf = 0; ctx.clearRect(0, 0, width, height); }
  }

  function run() { if (!raf && ctx) raf = window.requestAnimationFrame(frame); }
  function later(ms, fn) { timers.push(window.setTimeout(fn, ms)); }

  function podiumPoint() {
    var podium = stage.querySelector(".onthulling__podium");
    var a = podium.getBoundingClientRect(), b = stage.getBoundingClientRect();
    return { x: a.left - b.left + a.width / 2, y: a.top - b.top + a.height * 0.55 };
  }

  function play() {
    timers.forEach(window.clearTimeout);
    timers = [];
    parts = [];
    sparks = [];
    stage.classList.remove("is-spelen");
    void stage.offsetWidth;  // de CSS-animaties opnieuw laten beginnen
    stage.classList.add("is-spelen");
    if (!ctx) return;
    size();
    dustUntil = performance.now() + 14000;
    run();
    // Op het moment dat de kaart uit de envelop komt: confetti, daarna vuurwerk.
    later(1650, function () { var p = podiumPoint(); burst(p.x, p.y, 170, 15); run(); });
    later(2300, function () { burst(width * 0.08, height * 0.95, 70, 17); burst(width * 0.92, height * 0.95, 70, 17); run(); });
    [2800, 3400, 4100, 4900, 5600].forEach(function (t, i) {
      later(t, function () { firework(rand(width * 0.15, width * 0.85), rand(height * 0.12, height * 0.45)); run(); if (i === 1) { var p = podiumPoint(); burst(p.x, p.y, 60, 11); } });
    });
    if (again) later(5200, function () { again.hidden = false; });
  }

  window.addEventListener("resize", function () { if (raf) size(); });
  document.addEventListener("visibilitychange", function () {
    if (document.hidden && raf) { window.cancelAnimationFrame(raf); raf = 0; }
    else if (!document.hidden) run();
  });
  if (again) again.addEventListener("click", function () { again.hidden = true; play(); });
  play();
})();
