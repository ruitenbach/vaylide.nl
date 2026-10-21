/* 3D-kaartencarrousel voor de homepage (alleen als Beheer minstens vijf geschikte ontwerpen uitlicht). CSS 3D-transforms, Pointer Events, geen bibliotheek.
   - Slepen of vegen draait de ring; een tik op een zijkaart selecteert die eerst, een tik op de middelste opent het ontwerp.
   - touch-action: pan-y laat verticaal scrollen aan de browser; pas bij een duidelijk horizontale beweging neemt de carrousel over.
   - Bij 'minder beweging' geen traagheid en geen glijden; zonder 3D een gewone rij met scroll-snap. */
(function () {
  "use strict";
  var root = document.querySelector("[data-carrousel]");
  if (!root) return;
  var stage = root.querySelector(".cv__stage"), ring = root.querySelector(".cv__ring");
  var cards = Array.prototype.slice.call(ring.children), N = cards.length;
  if (!N) return;
  var naamEl = root.querySelector(".cv__naam"), subEl = root.querySelector(".cv__sub"), dotsEl = root.querySelector(".cv__dots");
  var statusEl = root.querySelector(".cv__status"), openEl = root.querySelector('[data-cv="open"]');
  var reduceMq = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  var flat = !(window.CSS && CSS.supports && CSS.supports("transform-style", "preserve-3d"));
  var tpos = 0, lerping = false, pos = 0, sel = -1, geo = null, raf = 0, anim = null, suppress = false, p0 = null, dots = [];

  cards.forEach(function (c, i) {
    var dm = document.createElement("span"); dm.className = "cv__dim"; dm.setAttribute("aria-hidden", "true"); c.appendChild(dm); c.dimEl = dm;
    var b = document.createElement("button");
    b.type = "button"; b.setAttribute("aria-label", "Ga naar " + c.getAttribute("data-naam"));
    b.addEventListener("click", function () { naar(i); });
    dotsEl.appendChild(b); dots.push(b);
    c.querySelector("a").addEventListener("click", function (e) {
      if (suppress) { e.preventDefault(); return; }
      if (flat) return;
      if (i !== current()) { e.preventDefault(); naar(i); }
    });
  });
  function current() { return ((Math.round(pos) % N) + N) % N; }
  function wrapO(o) { return ((o + N / 2) % N + N) % N - N / 2; }

  function meet() {
    var w = stage.clientWidth, groot = w >= 900;
    // Mobiel: kleinere middelste kaart en buurkaarten die duidelijk half in beeld staan, zodat veegbaar meteen te zien is.
    var cw = groot ? Math.min(300, w * 0.22) : Math.min(190, w * 0.47);
    geo = { cw: cw, stap: groot ? 21 : 30, R: groot ? Math.max(560, w * 0.56) : cw * 1.9, k: groot ? 0.1 : 0.1, dim: groot ? 0.18 : 0.1 };
    root.style.setProperty("--cw", cw + "px");
    root.style.setProperty("--stage-h", Math.round(cw * 1.25 + 34) + "px");
    root.classList.toggle("cv--plat", flat);
    if (flat) root.style.setProperty("--cw", Math.min(180, w * 0.44) + "px");
  }
  function teken() {
    if (!geo || flat) return;
    for (var i = 0; i < N; i++) {
      var o = wrapO(i - pos), a = Math.abs(o), th = o * geo.stap, rad = th * Math.PI / 180;
      var el = cards[i];
      el.style.transform = "translate3d(" + (Math.sin(rad) * geo.R).toFixed(1) + "px," + (a * a * geo.cw * 0.012).toFixed(1) + "px," + ((Math.cos(rad) - 1) * geo.R).toFixed(1) + "px) rotateY(" + th.toFixed(2) + "deg) scale(" + Math.max(0.5, 1 - geo.k * a).toFixed(3) + ")";
      el.style.opacity = a <= 2.3 ? 1 : Math.max(0, 1 - (a - 2.3) * 1.7).toFixed(2);
      el.style.zIndex = String(100 - Math.round(a * 10));
      el.dimEl.style.opacity = Math.min(0.4, a * geo.dim).toFixed(2);
      el.style.pointerEvents = a > 2.6 ? "none" : "auto";
      el.classList.toggle("is-weg", a > 2.7);
    }
    var s = current();
    if (s !== sel) kies(s);
  }
  function kies(s) {
    sel = s;
    var c = cards[s];
    naamEl.textContent = c.getAttribute("data-naam");
    subEl.textContent = c.getAttribute("data-sub");
    openEl.href = c.getAttribute("data-href");
    openEl.setAttribute("aria-label", "Bekijk het ontwerp " + c.getAttribute("data-naam"));
    cards.forEach(function (k, i) {
      var is = i === s;
      k.classList.toggle("is-sel", is);
      if (is) k.removeAttribute("aria-hidden"); else k.setAttribute("aria-hidden", "true");
      k.querySelector("a").tabIndex = is ? 0 : -1;
    });
    dots.forEach(function (d, i) { if (i === s) d.setAttribute("aria-current", "true"); else d.removeAttribute("aria-current"); });
    statusEl.textContent = c.getAttribute("data-naam") + ", ontwerp " + (s + 1) + " van " + N;
  }
  function vlak() { if (!raf) raf = requestAnimationFrame(function () { raf = 0; teken(); }); }
  function lerpStart() {
    if (lerping) return; lerping = true; anim = null;
    (function tik() {
      if (!lerping) return;
      pos += (tpos - pos) * 0.28; teken();
      if (p0 && p0.drag || Math.abs(tpos - pos) > 0.002) requestAnimationFrame(tik); else lerping = false;
    })();
  }
  function glij(doel, kort, traag) {
    lerping = false;
    if (reduceMq.matches) { pos = doel; teken(); return; }
    var van = pos, t0 = performance.now(), dur = (kort ? 380 : 560) + Math.min(Math.abs(doel - pos), 3) * 120, my = anim = {};
    (function stap(t) {
      if (anim !== my) return;
      var p = Math.max(0, Math.min(1, (t - t0) / dur)), e = 1 - Math.pow(1 - p, 4);
      pos = van + (doel - van) * e; teken();
      if (p < 1) requestAnimationFrame(stap);
    })(t0);
  }
  function naar(i, kort) { glij(Math.round(pos) + wrapO(i - Math.round(pos)), kort); }
  function stuur(d) { glij(Math.round(pos) + d, true); }

  stage.addEventListener("pointerdown", function (e) {
    if (flat || (e.pointerType === "mouse" && e.button !== 0)) return;
    anim = null;
    p0 = { id: e.pointerId, x: e.clientX, y: e.clientY, pos: pos, lx: e.clientX, lt: performance.now(), v: 0, drag: false };
  });
  stage.addEventListener("pointermove", function (e) {
    if (!p0 || e.pointerId !== p0.id) return;
    var dx = e.clientX - p0.x, dy = e.clientY - p0.y;
    if (!p0.drag) {
      if (Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(dy)) {
        p0.drag = true; stage.classList.add("is-drag");
        if (e.pointerType === "mouse") { try { stage.setPointerCapture(e.pointerId); } catch (x) {} }
      } else return;
    }
    tpos = p0.pos - dx / (geo.cw * 0.62);
    lerpStart();
    var nu = performance.now(), dt = nu - p0.lt;
    if (dt > 0) p0.v = 0.8 * p0.v + 0.2 * ((e.clientX - p0.lx) / dt);
    p0.lx = e.clientX; p0.lt = nu;
    vlak();
  });
  function los(e) {
    if (!p0 || (e && e.pointerId !== p0.id)) return;
    var was = p0.drag, v = p0.v; p0 = null; lerping = false;
    stage.classList.remove("is-drag");
    if (!was) { if (Math.abs(pos - Math.round(pos)) > 0.002) glij(Math.round(pos), true); return; }     // een tik tijdens een beweging zet de ring weer recht
    suppress = true; setTimeout(function () { suppress = false; }, 80);
    var extra = reduceMq.matches ? 0 : -v * 220 / (geo.cw * 0.62);
    glij(Math.round(tpos + Math.max(-2, Math.min(2, extra))), false, 1);
  }
  stage.addEventListener("pointerup", los);
  stage.addEventListener("pointercancel", los);
  stage.addEventListener("lostpointercapture", function (e) { if (e.pointerType === "mouse" && p0 && p0.drag) los(e); });
  stage.addEventListener("dragstart", function (e) { e.preventDefault(); });
  stage.addEventListener("keydown", function (e) {
    if (e.key === "ArrowRight") { e.preventDefault(); stuur(1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); stuur(-1); }
    else if (e.key === "Home") { e.preventDefault(); naar(0); }
    else if (e.key === "End") { e.preventDefault(); naar(N - 1); }
  });
  root.querySelector('[data-cv="prev"]').addEventListener("click", function () { stuur(-1); });
  root.querySelector('[data-cv="next"]').addEventListener("click", function () { stuur(1); });
  // Zweven en een zacht meebewegend perspectief: alleen als beweging is toegestaan; pauze als de ring uit beeld is of het tabblad verborgen.
  var po = 0, poT = 0, poRaf = 0, zichtbaar = true;
  function zweef() { root.classList.toggle("fx-zweef", !reduceMq.matches && !flat); }
  function rust() { root.classList.toggle("is-rust", !zichtbaar || document.hidden); }
  zweef(); if (reduceMq.addEventListener) reduceMq.addEventListener("change", zweef);
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { zichtbaar = en[0].isIntersecting; rust(); }).observe(stage);
  document.addEventListener("visibilitychange", rust);
  if (window.matchMedia && matchMedia("(hover: hover) and (pointer: fine)").matches) {
    root.addEventListener("pointermove", function (e) {
      if (reduceMq.matches || p0) return;
      var r = stage.getBoundingClientRect(); poT = Math.max(-1, Math.min(1, (e.clientX - r.left) / r.width * 2 - 1));
      if (!poRaf) poRaf = requestAnimationFrame(function tik() { po += (poT - po) * 0.06; stage.style.setProperty("--po", po.toFixed(3)); if (Math.abs(poT - po) > 0.004) poRaf = requestAnimationFrame(tik); else poRaf = 0; });
    });
    root.addEventListener("pointerleave", function () { poT = 0; if (!poRaf) poRaf = requestAnimationFrame(function tik() { po += (poT - po) * 0.06; stage.style.setProperty("--po", po.toFixed(3)); if (Math.abs(po) > 0.004) poRaf = requestAnimationFrame(tik); else poRaf = 0; }); });
  }
  var rt = 0;
  window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { meet(); teken(); }, 80); });
  // Bewegingshint bij de eerste weergave: de ring beweegt één keer even mee en een korte regel zegt wat kan. Niet bij 'minder beweging' (dan alleen de regel).
  var hintEl = root.querySelector(".cv__hint"), hintKlaar = false;
  function hintUit() { hintKlaar = true; hintEl.classList.remove("is-aan"); }
  function hint() {
    if (hintKlaar || p0) return; hintKlaar = true;
    var grof = window.matchMedia && matchMedia("(pointer: coarse)").matches;
    hintEl.textContent = grof ? "‹  Veeg voor meer ontwerpen  ›" : "‹  Sleep voor meer ontwerpen  ›";
    hintEl.classList.add("is-aan");
    setTimeout(function () { hintEl.classList.remove("is-aan"); }, 6000);
    if (reduceMq.matches || flat) return;
    var my = anim = {}, t0 = performance.now();
    (function stap(t) {
      if (anim !== my) return;
      var u = Math.max(0, Math.min(1, (t - t0) / 1900));      // de eerste beeldtijd kan iets voor t0 liggen: nooit een negatief getal in de macht
      pos = 0.3 * Math.sin(Math.PI * Math.pow(u, 0.8)) * (1 - 0.15 * u); teken();
      if (u < 1) requestAnimationFrame(stap); else { pos = 0; teken(); }
    })(t0);
  }
  stage.addEventListener("pointerdown", hintUit, true);
  stage.addEventListener("keydown", hintUit, true);
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (en) {
      if (en[0].isIntersecting) { io.disconnect(); setTimeout(hint, 1300); }
    }, { threshold: 0.6 });
    io.observe(stage);
  }
  meet(); teken();
})();
