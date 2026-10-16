/* Kerstmagie v1: de datum onder een ijslaag.
   De datum staat gewoon in de pagina (ook voor schermlezers). Dit script legt er een laag ijs overheen, een stukje van het
   sneeuwkristal uit de film, die de bezoeker met een veeg of tik wegkrast. Na ongeveer de helft smelt de rest vanzelf weg.
   Altijd een uitweg: de knop 'Onthul de datum' (ook met toetsenbord), en geen laag bij geen JavaScript, bij 'minder beweging',
   als de knop 'Beweging' op stil staat, als het tekenen niet lukt, of als de datum in deze sessie al onthuld is. */
(function () {
  "use strict";

  var html = document.documentElement;
  var block = document.querySelector("[data-kl-date]");
  if (!block) return;

  var key = "vierlief-kras:" + location.pathname;
  var seen = false;
  try { seen = !!sessionStorage.getItem(key); } catch (e) { /* privémodus */ }
  if (seen || !html.classList.contains("fx-motion")) return;

  var canvas, ctx, wrap, hint, button, w = 0, h = 0, dpr = 1, down = false, last = null, touched = false, gone = false, checkTimer = 0;
  var RADIUS = 21;          /* straal van de kwast in beeldpunten */
  var REVEAL_AT = 0.5;      /* zodra dit deel weg is, smelt de rest */

  function remember() { try { sessionStorage.setItem(key, "1"); } catch (e) { /* privémodus */ } }

  /* Het ijs: lichte koele kleuren, kristalstructuur uit de film, fijne korrel en haarscheurtjes. */
  function paint(image) {
    var g = ctx;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.globalCompositeOperation = "source-over";
    g.clearRect(0, 0, w, h);
    var base = g.createLinearGradient(0, 0, w, h);
    base.addColorStop(0, "#E6F1FC"); base.addColorStop(0.5, "#C9DEF2"); base.addColorStop(1, "#E2EFFB");
    g.fillStyle = base;
    g.fillRect(0, 0, w, h);
    if (image && image.complete && image.naturalWidth) {
      var s = Math.max(w / image.naturalWidth, h / image.naturalHeight) * 1.1;
      g.globalCompositeOperation = "multiply";
      g.globalAlpha = 0.45;
      g.drawImage(image, (w - image.naturalWidth * s) / 2, (h - image.naturalHeight * s) / 2, image.naturalWidth * s, image.naturalHeight * s);
      g.globalAlpha = 1;
      g.globalCompositeOperation = "source-over";
      g.fillStyle = "rgba(246,251,255,.55)";              /* licht de donkere plekken van het beeld op: ijs, geen vuil */
      g.fillRect(0, 0, w, h);
    }
    var i, x, y, r;
    for (i = 0; i < Math.round(w * h / 90); i++) {            /* fijne korrel */
      x = Math.random() * w; y = Math.random() * h; r = 0.4 + Math.random() * 1.1;
      g.fillStyle = Math.random() < 0.7 ? "rgba(255,255,255,.55)" : "rgba(150,190,228,.22)";
      g.beginPath(); g.arc(x, y, r, 0, 6.2832); g.fill();
    }
    g.strokeStyle = "rgba(255,255,255,.55)"; g.lineWidth = 0.7; g.lineCap = "round";
    for (i = 0; i < 6; i++) {                                  /* haarscheurtjes */
      x = Math.random() * w; y = Math.random() * h;
      g.beginPath(); g.moveTo(x, y);
      for (var k = 0; k < 4; k++) { x += (Math.random() - 0.5) * 46; y += (Math.random() - 0.5) * 24; g.lineTo(x, y); }
      g.stroke();
    }
    var top = g.createLinearGradient(0, 0, 0, h);              /* glans bovenaan, een zachte schaduw onderaan */
    top.addColorStop(0, "rgba(255,255,255,.55)"); top.addColorStop(0.4, "rgba(255,255,255,0)"); top.addColorStop(1, "rgba(120,160,205,.2)");
    g.fillStyle = top; g.fillRect(0, 0, w, h);
    g.strokeStyle = "rgba(255,255,255,.85)"; g.lineWidth = 1.2; g.strokeRect(0.6, 0.6, w - 1.2, h - 1.2);
  }

  function build() {
    var rect = block.getBoundingClientRect();
    w = Math.max(60, Math.round(block.offsetWidth || rect.width)); h = Math.max(40, Math.round(block.offsetHeight || rect.height));
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    var image = new Image();
    image.onload = function () { if (!touched && !gone) paint(image); };
    image.src = block.getAttribute("data-kl-vlok") || "";
    paint(null);
  }

  function point(e) {
    var r = canvas.getBoundingClientRect();
    return { x: (e.clientX - r.left) * (w / r.width), y: (e.clientY - r.top) * (h / r.height) };
  }
  /* Een veeg is een rij zachte stempels: de rand van de kwast loopt uit, geen harde streep. */
  function stamp(x, y) {
    var g = ctx, grad = g.createRadialGradient(x, y, 0, x, y, RADIUS);
    grad.addColorStop(0, "rgba(0,0,0,1)"); grad.addColorStop(0.45, "rgba(0,0,0,.9)"); grad.addColorStop(1, "rgba(0,0,0,0)");
    g.globalCompositeOperation = "destination-out";
    g.fillStyle = grad;
    g.beginPath(); g.arc(x, y, RADIUS, 0, 6.2832); g.fill();
  }
  function stroke(a, b) {
    var dx = b.x - a.x, dy = b.y - a.y, dist = Math.sqrt(dx * dx + dy * dy), step = RADIUS * 0.3, n = Math.max(1, Math.ceil(dist / step));
    for (var i = 1; i <= n; i++) stamp(a.x + dx * i / n, a.y + dy * i / n);
  }

  /* Hoeveel is weggekrast? Meten op een klein afbeeldinkje. */
  function cleared() {
    var probe = cleared.probe || (cleared.probe = document.createElement("canvas"));
    probe.width = 48; probe.height = 20;
    var g = probe.getContext("2d");
    g.clearRect(0, 0, 48, 20);
    g.drawImage(canvas, 0, 0, 48, 20);
    var data = g.getImageData(0, 0, 48, 20).data, n = 0;
    for (var i = 3; i < data.length; i += 4) if (data[i] < 60) n++;
    return n / (48 * 20);
  }
  function check() {
    checkTimer = 0;
    if (!gone && cleared() >= REVEAL_AT) reveal(false);
  }

  function reveal(focus) {
    if (gone) return;
    gone = true; remember();
    wrap.classList.add("is-melting");
    window.setTimeout(function () { if (wrap.parentNode) wrap.parentNode.removeChild(wrap); block.classList.remove("kl-date--frost"); }, 1000);
    if (focus) { block.setAttribute("tabindex", "-1"); block.focus({ preventScroll: true }); }
    document.dispatchEvent(new CustomEvent("kerstmagie:datum"));
  }

  try {
    block.classList.add("kl-date--frost");
    wrap = document.createElement("div");
    wrap.className = "kl-frost";
    wrap.setAttribute("data-tekst-op-beeld", "");   /* de tekst staat op het ijs: e2e/kerstmagie-kaart.cjs meet het contrast op de echte pixels */
    canvas = document.createElement("canvas");
    canvas.className = "kl-frost__ice";
    canvas.setAttribute("aria-hidden", "true");
    ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("geen canvas");
    hint = document.createElement("span");
    hint.className = "kl-frost__hint";
    hint.setAttribute("aria-hidden", "true");
    hint.textContent = "Kras het ijs weg";
    button = document.createElement("button");
    button.type = "button";
    button.className = "kl-frost__btn";
    button.textContent = "Onthul de datum";
    wrap.appendChild(canvas); wrap.appendChild(hint); wrap.appendChild(button);
    block.appendChild(wrap);
    build();

    canvas.addEventListener("pointerdown", function (e) {
      if (gone) return;
      down = true; touched = true; hint.classList.add("is-hidden");
      try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* oudere browser */ }
      last = point(e); stamp(last.x, last.y);
      e.preventDefault();
    });
    canvas.addEventListener("pointermove", function (e) {
      if (!down || gone) return;
      var p = point(e); stroke(last, p); last = p;
      if (!checkTimer) checkTimer = window.setTimeout(check, 140);
    });
    function up() { if (!down) return; down = false; last = null; window.clearTimeout(checkTimer); checkTimer = 0; check(); }
    canvas.addEventListener("pointerup", up);
    canvas.addEventListener("pointercancel", up);
    button.addEventListener("click", function () { reveal(true); });

    /* Het blok kan van maat veranderen (letters die laden, een ander scherm): tot de eerste veeg tekenen we het ijs opnieuw. */
    if (window.ResizeObserver) new ResizeObserver(function () {
      if (gone || touched) return;
      if (Math.abs(block.offsetWidth - w) > 2 || Math.abs(block.offsetHeight - h) > 2) build();
    }).observe(block);

    /* Staat de beweging op stil of uit (knop 'Beweging', 'minder beweging'), dan hoort de datum er gewoon te staan. */
    if (window.MutationObserver) new MutationObserver(function () {
      if (!html.classList.contains("fx-motion")) reveal(false);
    }).observe(html, { attributes: true, attributeFilter: ["class"] });
  } catch (error) {
    if (wrap && wrap.parentNode) wrap.parentNode.removeChild(wrap);
    block.classList.remove("kl-date--frost");
  }
})();
