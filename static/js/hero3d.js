/* Vaylide: de 3D-wereld op de homepage en de sprankelende koppen op de andere pagina's.
   - De voorbeeldkaart in de kop draait om met een tik, klik of Enter (werkt ook bij 'minder beweging'); op de computer ook bij aanwijzen (CSS).
   - De voorbeeldkaart en de gouden kaart kantelen mee met de muis; zonder muis (telefoon) bewegen ze vanzelf rustig heen en weer.
   - Gouden sterretjes twinkelen door de hele kop, ook achter de tekst; bewegen over de kop laat een spoortje glitter achter.
   - [data-sparkles]: een sectie met zacht zwevende sterretjes (kerstpodium, paginakoppen).
   - [data-tilt3d]: een waaier kaarten die meekantelt met de muis.
   Beweging nooit bij 'minder beweging'. Tekenlussen stoppen als de sectie uit beeld is of het tabblad verborgen. */
(function () {
  "use strict";

  // Voorbeeldkaart: omdraaien en terug. Staat los van de beweging, zodat hij altijd werkt.
  document.querySelectorAll("[data-flipkaart]").forEach(function (kaart) {
    var knop = kaart.querySelector(".flipkaart__knop");
    if (!knop) return;
    knop.addEventListener("click", function () {
      var open = !kaart.classList.contains("is-open");
      kaart.classList.toggle("is-open", open);
      knop.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });

  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;
  var finePointer = window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  function rand(a, b) { return a + Math.random() * (b - a); }

  // Vooral goud, af en toe wit.
  var GOUD = ["214, 162, 72", "236, 190, 96", "196, 140, 52", "255, 222, 150", "255, 255, 255"];
  var WARM = ["255, 226, 160", "255, 240, 205", "246, 200, 120", "255, 255, 255"];

  // Sterretje met vier punten en een zachte gloed.
  function drawSparkle(ctx, s, alpha) {
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

  /* Een sterretjesveld op een canvas dat een hele sectie bedekt. opts.tick(t, dt, veld) mag extra sterretjes maken. */
  function sterrenveld(section, canvas, opts) {
    if (!canvas || !canvas.getContext) return null;
    var ctx = canvas.getContext("2d");
    var veld = { sparkles: [], width: 0, height: 0, running: false, visible: true, ctx: ctx };
    var dpr = 1, lastTime = 0;
    veld.spawn = function (x, y, o) {
      if (veld.sparkles.length > (opts.max || 120)) return;
      o = o || {};
      veld.sparkles.push({
        x: x, y: y,
        vx: rand(-8, 8), vy: o.vy != null ? o.vy : rand(-14, -4),
        size: o.size || rand(4.5, 10), life: 0, max: o.max || rand(1.2, 2.6),
        rot: rand(0, Math.PI), spin: rand(-1.2, 1.2),
        color: (opts.colors || GOUD)[Math.floor(Math.random() * (opts.colors || GOUD).length)]
      });
    };
    function resize() {
      var r = section.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      veld.width = r.width; veld.height = r.height;
      canvas.width = Math.round(r.width * dpr);
      canvas.height = Math.round(r.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function frame(t) {
      if (!veld.running) return;
      var dt = Math.min(0.05, (t - (lastTime || t)) / 1000);
      lastTime = t;
      opts.tick(t, dt, veld);
      ctx.clearRect(0, 0, veld.width, veld.height);
      for (var i = veld.sparkles.length - 1; i >= 0; i--) {
        var p = veld.sparkles[i];
        p.life += dt;
        if (p.life >= p.max) { veld.sparkles.splice(i, 1); continue; }
        p.x += p.vx * dt; p.y += p.vy * dt; p.rot += p.spin * dt;
        var f = p.life / p.max;
        var alpha = Math.sin(Math.PI * f) * (0.75 + 0.25 * Math.sin(p.life * 14)); // opkomen, twinkelen, vervagen
        drawSparkle(ctx, p, Math.max(0, alpha));
      }
      requestAnimationFrame(frame);
    }
    veld.start = function () {
      if (veld.running || !veld.visible || document.hidden) return;
      veld.running = true; lastTime = 0;
      requestAnimationFrame(frame);
    };
    veld.stop = function () { veld.running = false; };
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        veld.visible = entries[0].isIntersecting;
        if (veld.visible) veld.start(); else veld.stop();
      }).observe(section);
    }
    document.addEventListener("visibilitychange", function () { if (document.hidden) veld.stop(); else veld.start(); });
    window.addEventListener("resize", resize);
    resize();
    veld.start();
    return veld;
  }

  // ---------- De kop op de homepage ----------
  var hero = document.querySelector("[data-hero3d]");
  if (hero) (function () {
    var stage = hero.querySelector(".card-stage");
    var media = hero.querySelector(".hero__media");
    var canvas = hero.querySelector(".hero__sparkles");
    if (!stage || !media) return;
    var MAX_TILT = 12; // graden
    var target = { rx: 0, ry: 0, gx: 30, gy: 20, px: 0, py: 0 };
    var now = { rx: 0, ry: 0, gx: 30, gy: 20, px: 0, py: 0 };
    var pointer = null, lastPointerAt = 0, trailDist = 0, spawnClock = 0, ambientClock = 0;

    var veld = sterrenveld(hero, canvas, {
      max: 130,
      tick: function (t, dt, v) {
        // Zonder muis bewegen de kaarten vanzelf rustig heen en weer.
        if (!pointer || t - lastPointerAt > 2500) {
          var s = t / 1000;
          target.ry = Math.sin(s * 0.6) * 9;
          target.rx = Math.cos(s * 0.45) * 4;
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

        // Sterretjes rond de kaarten (ongeveer twaalf per seconde) en verspreid door de hele kop (ongeveer vijf per seconde).
        var h = hero.getBoundingClientRect();
        var c = stage.getBoundingClientRect();
        spawnClock += dt;
        while (spawnClock > 0.085) {
          spawnClock -= 0.085;
          v.spawn(c.left - h.left + rand(-0.4, 1.3) * c.width, c.top - h.top + rand(-0.5, 1.15) * c.height);
        }
        ambientClock += dt;
        while (ambientClock > 0.2) {
          ambientClock -= 0.2;
          v.spawn(rand(0, v.width), rand(0, v.height), { size: rand(3, 6.5), max: rand(1.8, 3.4), vy: rand(-8, -2) });
        }
      }
    });
    if (!veld) return;

    hero.addEventListener("pointermove", function (e) {
      if (e.pointerType === "touch") return;
      var c = stage.getBoundingClientRect();
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
      var p = { x: e.clientX - h.left, y: e.clientY - h.top };
      // Spoortje glitter: een sterretje per ~14 pixels beweging (de afstand telt op over kleine bewegingen).
      if (pointer) {
        trailDist += Math.hypot(p.x - pointer.x, p.y - pointer.y);
        var n = 0;
        while (trailDist > 14 && n < 4) { trailDist -= 14; n++; veld.spawn(p.x + rand(-8, 8), p.y + rand(-8, 8), { size: rand(4, 7.5), max: rand(0.6, 1.1), vy: rand(-18, 4) }); }
        if (trailDist > 14) trailDist = 0;
      }
      pointer = p;
      lastPointerAt = performance.now();
      stage.classList.add("is-actief");
      veld.start();
    });
    hero.addEventListener("pointerleave", function () {
      pointer = null;
      stage.classList.remove("is-actief");
    });
  })();

  // ---------- Secties met zwevende sterretjes (kerstpodium, paginakoppen) ----------
  document.querySelectorAll("[data-sparkles]").forEach(function (section) {
    var canvas = section.querySelector("canvas");
    var warm = section.classList.contains("kerstpodium");
    var clock = 0;
    sterrenveld(section, canvas, {
      max: 90,
      colors: warm ? WARM : GOUD,
      tick: function (t, dt, v) {
        clock += dt;
        var every = warm ? 0.09 : 0.16;
        while (clock > every) {
          clock -= every;
          v.spawn(rand(0, v.width), rand(0, v.height), { size: rand(3, warm ? 8 : 6.5), max: rand(1.6, 3.2), vy: rand(-10, -2) });
        }
      }
    });
  });

  // ---------- Waaier van kaarten die meekantelt ----------
  if (finePointer) {
    document.querySelectorAll("[data-tilt3d]").forEach(function (el) {
      var area = el.parentElement || el;
      area.addEventListener("pointermove", function (e) {
        var r = el.getBoundingClientRect();
        var x = Math.max(-1, Math.min(1, (e.clientX - (r.left + r.width / 2)) / (r.width / 2)));
        var y = Math.max(-1, Math.min(1, (e.clientY - (r.top + r.height / 2)) / (r.height / 2)));
        el.style.setProperty("--tx", (x * 12).toFixed(2) + "deg");
        el.style.setProperty("--ty", (-y * 8).toFixed(2) + "deg");
      });
      area.addEventListener("pointerleave", function () {
        el.style.removeProperty("--tx");
        el.style.removeProperty("--ty");
      });
    });
  }
})();
