/* Vaylide: effecten op de uitnodigingen.
   - sfeer: zwevende deeltjes op de achtergrond (blaadjes, goudstof, sterren, bubbels, ...);
   - knal: een uitbarsting op het moment dat de uitnodiging opengaat;
   - viering: een feestje als een gast laat weten dat hij komt;
   - kleinere effecten: versieringen die zichzelf tekenen, getallen die optellen, kantelen
     met de muis en vonkjes bij een tik.
   Welk effect een ontwerp krijgt, staat in manifest.json ("effects", zie catalog/effects.py).
   Alles is decoratief (aria-hidden); zonder dit script blijft de inhoud gewoon leesbaar.
   Geen beweging bij 'minder beweging' in het systeem. De knop 'Beweging' zet alles stil
   en onthoudt die keuze op dit apparaat (WCAG 2.2.2). */
(function () {
  "use strict";

  var html = document.documentElement;
  var body = document.body;
  if (!body || !html.classList.contains("fx") || !window.requestAnimationFrame) return;

  var TAU = Math.PI * 2;
  var WHITE = [255, 255, 255];
  var BLACK = [0, 0, 0];
  var PREF_KEY = "vierlief-beweging";

  var settings = {
    sfeer: html.getAttribute("data-fx-sfeer") || "geen",
    knal: html.getAttribute("data-fx-knal") || "geen",
    viering: html.getAttribute("data-fx-viering") || "geen",
    tik: html.hasAttribute("data-fx-tik"),
    kantel: html.classList.contains("fx-kantel"),
    scrollwind: html.classList.contains("fx-scrollwind")
  };
  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  var fineQuery = window.matchMedia ? window.matchMedia("(hover: hover) and (pointer: fine)") : null;
  /* Eenvoudige toestellen (weinig rekenkernen of geheugen): minder deeltjes vanaf het begin. */
  var lowPower = (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) || (navigator.deviceMemory && navigator.deviceMemory <= 3);
  var state = {
    reduced: !!(reduceQuery && reduceQuery.matches),
    paused: readPref() === "stil",
    pageOn: false
  };

  function motionOn() { return !state.reduced && !state.paused; }

  function readPref() {
    try { return window.localStorage.getItem(PREF_KEY); } catch (e) { return null; }
  }
  function writePref(value) {
    try {
      if (value) window.localStorage.setItem(PREF_KEY, value);
      else window.localStorage.removeItem(PREF_KEY);
    } catch (e) { /* privémodus of geblokkeerde opslag: dan alleen voor deze pagina */ }
  }

  /* ---------------------------------------------------------------- hulpjes */
  function rand(a, b) { return a + Math.random() * (b - a); }
  function range(r) { return rand(r[0], r[1]); }
  function pick(list) { return list[Math.floor(Math.random() * list.length)]; }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  function pickWeighted(list) {
    var total = 0, i;
    for (i = 0; i < list.length; i++) total += list[i][1];
    var r = Math.random() * total;
    for (i = 0; i < list.length; i++) { r -= list[i][1]; if (r <= 0) return list[i][0]; }
    return list[list.length - 1][0];
  }

  /* Kleuren: het canvas zet elke geldige CSS-kleur om naar #rrggbb of rgba(). */
  var probe = document.createElement("canvas").getContext("2d");
  function rgb(value, fallback) {
    value = (value || "").trim();
    if (!value || !probe) return fallback;
    probe.fillStyle = "#010203";
    probe.fillStyle = value;
    var out = String(probe.fillStyle);
    if (out === "#010203" && value.toLowerCase() !== "#010203") return fallback;
    if (out.charAt(0) === "#") {
      return [parseInt(out.substr(1, 2), 16), parseInt(out.substr(3, 2), 16), parseInt(out.substr(5, 2), 16)];
    }
    var m = out.match(/[\d.]+/g);
    return m && m.length >= 3 ? [+m[0], +m[1], +m[2]] : fallback;
  }
  function mix(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  function css(c, alpha) {
    return "rgba(" + Math.round(c[0]) + "," + Math.round(c[1]) + "," + Math.round(c[2]) + "," + (alpha == null ? 1 : alpha) + ")";
  }
  function luminance(c) {
    function ch(v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2]);
  }

  function ratio(a, b) {
    var la = luminance(a), lb = luminance(b);
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
  }

  /* Kleuren van een ontwerp, gelezen uit --fx-1 t/m --fx-4 en --fx-bg (per kleurvariant).
     Een kleur die bijna gelijk is aan de achtergrond, wordt lichter of donkerder gemaakt. */
  function paletteFor(el) {
    var cs = window.getComputedStyle(el || body);
    var bodyBg = rgb(window.getComputedStyle(body).backgroundColor, [250, 247, 242]);
    var bg = rgb(cs.getPropertyValue("--fx-bg"), bodyBg);
    var dark = luminance(bg) < 0.26;
    function visible(c) { return ratio(c, bg) < 1.7 ? mix(c, dark ? WHITE : BLACK, dark ? 0.62 : 0.35) : c; }
    var c1 = visible(rgb(cs.getPropertyValue("--fx-1"), dark ? [226, 196, 140] : [142, 106, 59]));
    var c2 = visible(rgb(cs.getPropertyValue("--fx-2"), mix(c1, WHITE, 0.5)));
    var c3 = visible(rgb(cs.getPropertyValue("--fx-3"), mix(c1, WHITE, 0.3)));
    var c4 = rgb(cs.getPropertyValue("--fx-4"), mix(c1, WHITE, dark ? 0.62 : 0.78));
    return { bg: bg, dark: dark, c1: c1, c2: c2, c3: c3, c4: c4 };
  }

  /* Kleurreeksen per soort deeltje. */
  var COLORS = {
    bloem: function (p) { return [p.c2, mix(p.c2, p.c1, 0.35), mix(p.c1, WHITE, 0.2), mix(p.c2, WHITE, 0.3)]; },
    bloesem: function (p) { return [mix(p.c2, WHITE, 0.35), mix(p.c2, WHITE, 0.6), mix(p.c1, WHITE, 0.55), mix(p.c2, p.c1, 0.2)]; },
    blad: function (p) { return [p.c1, mix(p.c1, p.c3, 0.45), mix(p.c1, WHITE, 0.3), p.dark ? mix(p.c1, WHITE, 0.5) : mix(p.c1, BLACK, 0.12)]; },
    pluis: function (p) {
      var straw = [226, 196, 150];
      return [mix(p.c2, straw, 0.45), mix(mix(p.c1, WHITE, 0.45), straw, 0.35), mix(p.c3, straw, 0.5)];
    },
    feest: function (p) {
      var list = [p.c1, p.c2, p.c3, mix(p.c1, WHITE, 0.45)];
      return p.dark ? list.map(function (c) { return mix(c, WHITE, 0.15); }) : list;
    },
    hart: function (p) {
      var rose = [212, 84, 116];
      return [mix(p.c1, rose, 0.35), mix(p.c2, rose, 0.3), mix(mix(p.c1, p.c2, 0.5), rose, 0.3), mix(mix(p.c1, WHITE, 0.3), rose, 0.25)];
    },
    bel: function (p) { return [p.c2, p.c3, p.c1]; },
    bubbel: function (p) { return p.dark ? [mix(p.c1, WHITE, 0.55), mix(p.c4, WHITE, 0.3)] : [mix(p.c1, BLACK, 0.05), mix(p.c1, WHITE, 0.2)]; },
    licht: function (p) { return [mix(p.c2, WHITE, 0.25), mix(p.c3, WHITE, 0.25), mix(p.c1, WHITE, 0.45), p.c4]; },
    stof: function (p) { return p.dark ? [mix(p.c1, WHITE, 0.6), p.c4] : [mix(p.c1, BLACK, 0.05), mix(p.c1, p.bg, 0.3)]; },
    zon: function (p) { return [mix(p.c1, [255, 214, 150], 0.55), mix(p.c2, WHITE, 0.25), mix(p.c1, WHITE, 0.4)]; },
    neon: function (p) { return [p.c1, p.c2, p.c3]; },
    geo: function (p) { return p.dark ? [mix(p.c1, WHITE, 0.2), mix(p.c2, WHITE, 0.3)] : [p.c1, mix(p.c1, p.c2, 0.4)]; },
    wolk: function (p) { return [mix(p.bg, WHITE, 0.85), mix(p.c2, WHITE, 0.75), WHITE]; },
    goud: function (p) {
      return p.dark ? [mix(p.c1, WHITE, 0.3), mix(p.c1, WHITE, 0.6), [255, 247, 226]]
        : [p.c1, mix(p.c1, BLACK, 0.12), mix(p.c1, WHITE, 0.2)];
    },
    ster: function (p) { return [[255, 246, 222], [226, 234, 255], mix(p.c4, WHITE, 0.4)]; },
    /* Cadeautjes: papier en lint als paar (zes getallen). Tinten uit de accentkleur plus goud of wit,
       zodat ze bij de kleurvariant passen; het lint is altijd duidelijk anders dan het papier. */
    cadeau: function (p) {
      function lint(box, want) {
        if (ratio(box, want) >= 1.6) return want;
        return luminance(box) > 0.4 ? mix(box, BLACK, 0.45) : mix(box, WHITE, 0.78);
      }
      var boxes, ribbons;
      if (p.dark) {
        boxes = [p.c1, mix(p.c1, WHITE, 0.55), mix(p.bg, WHITE, 0.16), mix(p.c1, WHITE, 0.82)];
        ribbons = [mix(p.bg, BLACK, 0.4), p.c1, p.c1, p.c1];
      } else {
        boxes = [p.c1, mix(p.c1, WHITE, 0.42), mix(p.c1, WHITE, 0.88), [216, 172, 76]];
        ribbons = [mix(p.c1, WHITE, 0.9), p.c1, p.c1, p.c1];
      }
      return boxes.map(function (b, i) { return b.concat(lint(b, ribbons[i])); });
    },
    film: function (p) { return p.dark ? [WHITE] : [mix(p.c1, BLACK, 0.55)]; },
    /* Sneeuw: op een donkere achtergrond wit en ijsblauw; op een lichte achtergrond is wit onzichtbaar,
       dan worden het vlokjes in goud en zilverblauw. */
    sneeuwzacht: function (p) { return p.dark ? [WHITE, [238, 244, 255], [255, 251, 242]] : [mix(p.c1, WHITE, 0.12), [170, 186, 210], mix(p.c1, BLACK, 0.06)]; },
    sneeuw: function (p) { return p.dark ? [WHITE, [226, 236, 255], mix(p.c4, WHITE, 0.5)] : [p.c1, mix(p.c1, BLACK, 0.12), [150, 168, 196]]; }
  };

  /* ---------------------------------------------------------------- sprites
     Elk deeltje wordt één keer op een klein canvas getekend (2x scherp) en daarna alleen
     nog verplaatst, gedraaid en geschaald. Tekenen gebeurt in eenheden: 1 = de maat van het deeltje. */
  var SPRITES = {
    petal: { w: 0.8, h: 1, draw: function (g, c) {
      var grad = g.createLinearGradient(0, 0.5, 0, -0.5);
      grad.addColorStop(0, css(mix(c, WHITE, 0.55)));
      grad.addColorStop(0.55, css(c));
      grad.addColorStop(1, css(mix(c, BLACK, 0.06)));
      g.fillStyle = grad;
      g.beginPath();
      g.moveTo(0, 0.5);
      g.bezierCurveTo(-0.47, 0.28, -0.46, -0.34, -0.14, -0.46);
      g.quadraticCurveTo(0, -0.37, 0.14, -0.46);
      g.bezierCurveTo(0.46, -0.34, 0.47, 0.28, 0, 0.5);
      g.fill();
      g.strokeStyle = css(mix(c, WHITE, 0.55), 0.5);
      g.lineWidth = 0.024;
      g.beginPath(); g.moveTo(0, 0.44); g.quadraticCurveTo(0.04, 0.02, 0, -0.34); g.stroke();
    } },
    blossom: { w: 1, h: 1, draw: function (g, c) {
      for (var i = 0; i < 5; i++) {
        g.save();
        g.rotate(i * TAU / 5);
        var grad = g.createLinearGradient(0, 0, 0, -0.5);
        grad.addColorStop(0, css(mix(c, BLACK, 0.04)));
        grad.addColorStop(1, css(mix(c, WHITE, 0.55)));
        g.fillStyle = grad;
        g.beginPath();
        g.moveTo(0, 0);
        g.bezierCurveTo(-0.22, -0.1, -0.25, -0.4, -0.09, -0.48);
        g.quadraticCurveTo(0, -0.42, 0.09, -0.48);
        g.bezierCurveTo(0.25, -0.4, 0.22, -0.1, 0, 0);
        g.fill();
        g.restore();
      }
      g.fillStyle = css(mix(c, BLACK, 0.3));
      g.beginPath(); g.arc(0, 0, 0.08, 0, TAU); g.fill();
      g.fillStyle = "rgba(250,214,120,0.95)";
      for (var j = 0; j < 7; j++) {
        var a = j * TAU / 7;
        g.beginPath(); g.arc(Math.cos(a) * 0.15, Math.sin(a) * 0.15, 0.028, 0, TAU); g.fill();
      }
    } },
    leafRound: { w: 0.92, h: 1.05, draw: function (g, c) {
      var grad = g.createLinearGradient(-0.4, -0.4, 0.4, 0.4);
      grad.addColorStop(0, css(mix(c, WHITE, 0.38)));
      grad.addColorStop(1, css(c));
      g.fillStyle = grad;
      g.beginPath(); g.ellipse(0, 0, 0.43, 0.45, 0, 0, TAU); g.fill();
      g.strokeStyle = css(mix(c, WHITE, 0.5), 0.55);
      g.lineWidth = 0.03;
      g.beginPath(); g.moveTo(0, 0.44); g.quadraticCurveTo(0.03, 0, 0, -0.34); g.stroke();
      g.strokeStyle = css(mix(c, BLACK, 0.25));
      g.lineWidth = 0.045;
      g.beginPath(); g.moveTo(0, 0.44); g.lineTo(0.02, 0.52); g.stroke();
    } },
    leafLong: { w: 0.46, h: 1, draw: function (g, c) {
      var grad = g.createLinearGradient(-0.2, 0, 0.2, 0);
      grad.addColorStop(0, css(mix(c, WHITE, 0.32)));
      grad.addColorStop(1, css(mix(c, BLACK, 0.06)));
      g.fillStyle = grad;
      g.beginPath();
      g.moveTo(0, -0.5);
      g.quadraticCurveTo(0.24, -0.06, 0, 0.5);
      g.quadraticCurveTo(-0.24, -0.06, 0, -0.5);
      g.fill();
      g.strokeStyle = css(mix(c, WHITE, 0.55), 0.6);
      g.lineWidth = 0.022;
      g.beginPath(); g.moveTo(0, 0.48); g.lineTo(0, -0.44); g.stroke();
    } },
    fluff: { w: 0.62, h: 1.05, draw: function (g, c) {
      g.lineCap = "round";
      g.lineWidth = 0.016;
      for (var i = 0; i < 70; i++) {
        var t = i / 63;
        var y = 0.46 - t * 0.92;
        var len = 0.06 + 0.2 * Math.sin(t * Math.PI) + Math.random() * 0.04;
        var side = i % 2 ? 1 : -1;
        g.strokeStyle = css(mix(c, WHITE, Math.random() * 0.3), 0.55 + Math.random() * 0.35);
        g.beginPath();
        g.moveTo(0.02 * Math.sin(t * 3), y);
        g.quadraticCurveTo(side * len * 0.5, y - 0.02, side * len, y - 0.07 - Math.random() * 0.05);
        g.stroke();
      }
      g.strokeStyle = css(mix(c, BLACK, 0.2), 0.5);
      g.lineWidth = 0.014;
      g.beginPath(); g.moveTo(0, 0.5); g.quadraticCurveTo(0.03, 0, 0, -0.48); g.stroke();
    } },
    rect: { w: 0.62, h: 1, draw: function (g, c) {
      g.fillStyle = css(c);
      g.fillRect(-0.31, -0.5, 0.62, 1);
      g.fillStyle = css(WHITE, 0.18);
      g.fillRect(-0.31, -0.5, 0.2, 1);
    } },
    circle: { w: 0.8, h: 0.8, draw: function (g, c) {
      g.fillStyle = css(c);
      g.beginPath(); g.arc(0, 0, 0.4, 0, TAU); g.fill();
    } },
    ribbon: { w: 0.42, h: 1.7, draw: function (g, c) {
      g.strokeStyle = css(c);
      g.lineWidth = 0.13;
      g.lineCap = "round";
      g.beginPath();
      for (var i = 0; i <= 24; i++) {
        var t = i / 24;
        var x = Math.sin(t * TAU * 1.25) * 0.13;
        var y = -0.78 + t * 1.56;
        if (i) g.lineTo(x, y); else g.moveTo(x, y);
      }
      g.stroke();
    } },
    tri: { w: 0.9, h: 0.8, draw: function (g, c) {
      g.fillStyle = css(c);
      g.beginPath(); g.moveTo(0, -0.38); g.lineTo(0.42, 0.36); g.lineTo(-0.42, 0.36); g.closePath(); g.fill();
    } },
    heart: { w: 1, h: 0.92, draw: function (g, c) {
      var grad = g.createRadialGradient(-0.18, -0.22, 0.02, 0, 0, 0.62);
      grad.addColorStop(0, css(mix(c, WHITE, 0.5)));
      grad.addColorStop(0.5, css(c));
      grad.addColorStop(1, css(mix(c, BLACK, 0.15)));
      g.fillStyle = grad;
      g.beginPath();
      g.moveTo(0, 0.42);
      g.bezierCurveTo(-0.08, 0.34, -0.5, 0.1, -0.5, -0.14);
      g.bezierCurveTo(-0.5, -0.34, -0.34, -0.46, -0.2, -0.46);
      g.bezierCurveTo(-0.08, -0.46, 0, -0.36, 0, -0.28);
      g.bezierCurveTo(0, -0.36, 0.08, -0.46, 0.2, -0.46);
      g.bezierCurveTo(0.34, -0.46, 0.5, -0.34, 0.5, -0.14);
      g.bezierCurveTo(0.5, 0.1, 0.08, 0.34, 0, 0.42);
      g.fill();
      g.fillStyle = "rgba(255,255,255,0.4)";
      g.beginPath(); g.ellipse(-0.24, -0.25, 0.09, 0.05, -0.7, 0, TAU); g.fill();
    } },
    bubble: { w: 1, h: 1, draw: function (g, c, px, dark) {
      var r = 0.47;
      var fill = g.createRadialGradient(0, 0, r * 0.5, 0, 0, r);
      fill.addColorStop(0, css(c, 0));
      fill.addColorStop(0.78, css(mix(c, WHITE, 0.35), dark ? 0.14 : 0.16));
      fill.addColorStop(1, css(mix(c, WHITE, 0.1), dark ? 0.45 : 0.5));
      g.fillStyle = fill;
      g.beginPath(); g.arc(0, 0, r, 0, TAU); g.fill();
      if (g.createConicGradient) {
        var rim = g.createConicGradient(0.6, 0, 0);
        rim.addColorStop(0, "rgba(240,120,190,0.8)");
        rim.addColorStop(0.25, "rgba(110,180,250,0.8)");
        rim.addColorStop(0.5, "rgba(120,220,170,0.75)");
        rim.addColorStop(0.75, "rgba(245,200,100,0.8)");
        rim.addColorStop(1, "rgba(240,120,190,0.8)");
        g.strokeStyle = rim;
      } else {
        g.strokeStyle = css(mix(c, WHITE, 0.3), 0.6);
      }
      g.lineWidth = 0.05;
      g.beginPath(); g.arc(0, 0, r - 0.025, 0, TAU); g.stroke();
      if (!dark) {
        g.strokeStyle = css(mix(c, BLACK, 0.3), 0.32);
        g.lineWidth = 0.016;
        g.beginPath(); g.arc(0, 0, r, 0, TAU); g.stroke();
      }
      g.fillStyle = "rgba(255,255,255,0.9)";
      g.beginPath(); g.ellipse(-0.19, -0.23, 0.1, 0.05, -0.7, 0, TAU); g.fill();
      g.fillStyle = "rgba(255,255,255,0.5)";
      g.beginPath(); g.arc(0.21, 0.2, 0.03, 0, TAU); g.fill();
    } },
    fizz: { w: 1, h: 1, draw: function (g, c) {
      g.fillStyle = css(c, 0.16);
      g.beginPath(); g.arc(0, 0, 0.42, 0, TAU); g.fill();
      g.strokeStyle = css(c, 0.85);
      g.lineWidth = 0.12;
      g.beginPath(); g.arc(0, 0, 0.4, 0, TAU); g.stroke();
      g.fillStyle = "rgba(255,255,255,0.85)";
      g.beginPath(); g.arc(-0.14, -0.14, 0.1, 0, TAU); g.fill();
    } },
    glint: { w: 1, h: 1, glow: true, draw: function (g, c) {
      g.fillStyle = css(c);
      g.beginPath();
      g.moveTo(0, -0.5);
      g.quadraticCurveTo(0.035, -0.035, 0.5, 0);
      g.quadraticCurveTo(0.035, 0.035, 0, 0.5);
      g.quadraticCurveTo(-0.035, 0.035, -0.5, 0);
      g.quadraticCurveTo(-0.035, -0.035, 0, -0.5);
      g.fill();
      var core = g.createRadialGradient(0, 0, 0, 0, 0, 0.2);
      core.addColorStop(0, "rgba(255,255,255,0.95)");
      core.addColorStop(1, css(c, 0));
      g.fillStyle = core;
      g.beginPath(); g.arc(0, 0, 0.2, 0, TAU); g.fill();
    } },
    speck: { w: 1, h: 1, draw: function (g, c) {
      var grad = g.createRadialGradient(0, 0, 0, 0, 0, 0.5);
      grad.addColorStop(0, css(c, 1));
      grad.addColorStop(0.45, css(c, 0.75));
      grad.addColorStop(1, css(c, 0));
      g.fillStyle = grad;
      g.beginPath(); g.arc(0, 0, 0.5, 0, TAU); g.fill();
    } },
    orb: { w: 1, h: 1, draw: function (g, c) {
      var grad = g.createRadialGradient(0, 0, 0, 0, 0, 0.5);
      grad.addColorStop(0, css(c, 0.5));
      grad.addColorStop(0.72, css(c, 0.34));
      grad.addColorStop(0.9, css(mix(c, WHITE, 0.3), 0.42));
      grad.addColorStop(1, css(c, 0));
      g.fillStyle = grad;
      g.beginPath(); g.arc(0, 0, 0.5, 0, TAU); g.fill();
    } },
    flake: { w: 1, h: 1, draw: function (g, c) {
      var grad = g.createRadialGradient(0, 0, 0, 0, 0, 0.5);
      grad.addColorStop(0, css(c, 1));
      grad.addColorStop(0.5, css(c, 0.82));
      grad.addColorStop(1, css(c, 0));
      g.fillStyle = grad;
      g.beginPath(); g.arc(0, 0, 0.5, 0, TAU); g.fill();
    } },
    crystal: { w: 1, h: 1, line: true, path: function (g) {
      for (var i = 0; i < 6; i++) {
        var a = i * Math.PI / 3, ca = Math.cos(a), sa = Math.sin(a);
        g.moveTo(0, 0); g.lineTo(ca * 0.46, sa * 0.46);
        for (var k = 0; k < 2; k++) {
          var u = k ? 0.33 : 0.2, l = k ? 0.09 : 0.13, bx = ca * u, by = sa * u;
          g.moveTo(bx, by); g.lineTo(bx + Math.cos(a + 0.8) * l, by + Math.sin(a + 0.8) * l);
          g.moveTo(bx, by); g.lineTo(bx + Math.cos(a - 0.8) * l, by + Math.sin(a - 0.8) * l);
        }
      }
    } },
    dot: { w: 1, h: 1, draw: function (g, c) {
      g.fillStyle = css(c);
      g.beginPath(); g.arc(0, 0, 0.46, 0, TAU); g.fill();
      g.fillStyle = "rgba(255,255,255,0.28)";
      g.beginPath(); g.arc(-0.15, -0.16, 0.13, 0, TAU); g.fill();
    } },
    /* Neonbuizen: gloed plus een lichte kern. */
    nRing: { w: 1, h: 1, neon: true, path: function (g) { g.arc(0, 0, 0.36, 0, TAU); } },
    nTriangle: { w: 1, h: 1, neon: true, path: function (g) { g.moveTo(0, -0.36); g.lineTo(0.36, 0.3); g.lineTo(-0.36, 0.3); g.closePath(); } },
    nZigzag: { w: 1, h: 0.6, neon: true, path: function (g) { g.moveTo(-0.42, 0.12); g.lineTo(-0.21, -0.12); g.lineTo(0, 0.12); g.lineTo(0.21, -0.12); g.lineTo(0.42, 0.12); } },
    nPlus: { w: 1, h: 1, neon: true, path: function (g) { g.moveTo(0, -0.3); g.lineTo(0, 0.3); g.moveTo(-0.3, 0); g.lineTo(0.3, 0); } },
    nWave: { w: 1, h: 0.5, neon: true, path: function (g) {
      for (var i = 0; i <= 20; i++) { var t = i / 20; var x = -0.42 + t * 0.84; var y = Math.sin(t * TAU) * 0.1; if (i) g.lineTo(x, y); else g.moveTo(x, y); }
    } },
    /* Dunne lijnvormen */
    oRing: { w: 1, h: 1, line: true, path: function (g) { g.arc(0, 0, 0.44, 0, TAU); } },
    oDiamond: { w: 1, h: 1, line: true, path: function (g) { g.moveTo(0, -0.45); g.lineTo(0.45, 0); g.lineTo(0, 0.45); g.lineTo(-0.45, 0); g.closePath(); } },
    oSquare: { w: 1, h: 1, line: true, path: function (g) { g.rect(-0.34, -0.34, 0.68, 0.68); } },
    oTriangle: { w: 1, h: 1, line: true, path: function (g) { g.moveTo(0, -0.42); g.lineTo(0.42, 0.34); g.lineTo(-0.42, 0.34); g.closePath(); } },
    oLine: { w: 1, h: 0.2, line: true, path: function (g) { g.moveTo(-0.46, 0); g.lineTo(0.46, 0); } },
    oArc: { w: 1, h: 0.6, line: true, path: function (g) { g.arc(0, 0.22, 0.44, Math.PI * 1.1, Math.PI * 1.9); } },
    cloud: { w: 2.1, h: 1.05, draw: function (g, c) {
      var parts = [[-0.62, 0.14, 0.3], [-0.26, -0.08, 0.38], [0.16, -0.18, 0.4], [0.55, 0.02, 0.32], [0.84, 0.2, 0.2], [0, 0.2, 0.36], [-0.88, 0.26, 0.18]];
      g.fillStyle = css(c);
      g.beginPath();
      parts.forEach(function (p) { g.moveTo(p[0] + p[2], p[1]); g.arc(p[0], p[1], p[2], 0, TAU); });
      g.fill();
      var shade = g.createLinearGradient(0, -0.3, 0, 0.5);
      shade.addColorStop(0, "rgba(255,255,255,0)");
      shade.addColorStop(1, css(mix(c, BLACK, 0.08), 0.18));
      g.fillStyle = shade;
      g.fill();
    } },
    gift: { w: 1, h: 1.1, draw: function (g, c) {
      var box = [c[0], c[1], c[2]];
      var rib = c.length > 5 ? [c[3], c[4], c[5]] : (luminance(box) > 0.4 ? mix(box, BLACK, 0.45) : mix(box, WHITE, 0.75));
      function rr(x, y, w, h, r) {
        g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
        g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
      }
      /* Doos met een zacht verloop en stippen op het papier. */
      var body = g.createLinearGradient(0, -0.1, 0, 0.5);
      body.addColorStop(0, css(mix(box, WHITE, 0.12)));
      body.addColorStop(1, css(mix(box, BLACK, 0.16)));
      g.fillStyle = body;
      rr(-0.38, -0.08, 0.76, 0.56, 0.05); g.fill();
      g.fillStyle = css(luminance(box) > 0.55 ? mix(box, BLACK, 0.12) : mix(box, WHITE, 0.5), 0.75);
      [[-0.25, 0.06], [0.23, 0.1], [-0.19, 0.33], [0.27, 0.36], [-0.31, 0.2], [0.17, 0.24]].forEach(function (d) {
        g.beginPath(); g.arc(d[0], d[1], 0.028, 0, TAU); g.fill();
      });
      /* Deksel met schaduwrand. */
      g.fillStyle = css(mix(box, BLACK, 0.3), 0.35);
      g.fillRect(-0.38, -0.08, 0.76, 0.05);
      var lid = g.createLinearGradient(0, -0.26, 0, -0.08);
      lid.addColorStop(0, css(mix(box, WHITE, 0.24)));
      lid.addColorStop(1, css(mix(box, WHITE, 0.04)));
      g.fillStyle = lid;
      rr(-0.44, -0.26, 0.88, 0.19, 0.045); g.fill();
      /* Lint over deksel en doos. */
      g.fillStyle = css(rib);
      g.fillRect(-0.075, -0.26, 0.15, 0.74);
      g.fillStyle = css(mix(rib, WHITE, 0.35), 0.55);
      g.fillRect(-0.075, -0.26, 0.04, 0.74);
      /* Strik: twee lussen met een donkere binnenkant en een knoop. */
      g.fillStyle = css(rib);
      g.beginPath(); g.ellipse(-0.15, -0.34, 0.15, 0.09, -0.42, 0, TAU); g.fill();
      g.beginPath(); g.ellipse(0.15, -0.34, 0.15, 0.09, 0.42, 0, TAU); g.fill();
      g.fillStyle = css(mix(rib, BLACK, 0.3));
      g.beginPath(); g.ellipse(-0.14, -0.34, 0.065, 0.032, -0.42, 0, TAU); g.fill();
      g.beginPath(); g.ellipse(0.14, -0.34, 0.065, 0.032, 0.42, 0, TAU); g.fill();
      g.fillStyle = css(mix(rib, BLACK, 0.12));
      g.beginPath(); g.arc(0, -0.285, 0.06, 0, TAU); g.fill();
      /* Glans linksboven op het deksel. */
      g.fillStyle = "rgba(255,255,255,0.28)";
      g.fillRect(-0.4, -0.235, 0.22, 0.035);
    } },
    balloon: { w: 0.8, h: 1.05, draw: function (g, c) {
      var grad = g.createRadialGradient(-0.13, -0.24, 0.02, 0, -0.08, 0.52);
      grad.addColorStop(0, css(mix(c, WHITE, 0.6)));
      grad.addColorStop(0.35, css(c));
      grad.addColorStop(1, css(mix(c, BLACK, 0.2)));
      g.fillStyle = grad;
      g.beginPath(); g.ellipse(0, -0.08, 0.37, 0.44, 0, 0, TAU); g.fill();
      g.fillStyle = css(mix(c, BLACK, 0.18));
      g.beginPath(); g.moveTo(-0.06, 0.44); g.lineTo(0.06, 0.44); g.lineTo(0, 0.35); g.closePath(); g.fill();
      g.fillStyle = "rgba(255,255,255,0.5)";
      g.beginPath(); g.ellipse(-0.16, -0.26, 0.06, 0.13, -0.45, 0, TAU); g.fill();
    } }
  };

  var spriteCache = {};
  function getSprite(kind, color, size, dark) {
    var def = SPRITES[kind];
    var px = Math.max(3, Math.round(size)) * 2;
    var glow = def.neon ? 9 : (def.glow && dark ? 6 : 0);
    var key = kind + "|" + Math.round(color[0]) + "," + Math.round(color[1]) + "," + Math.round(color[2]) +
      (color.length > 5 ? "," + Math.round(color[3]) + "," + Math.round(color[4]) + "," + Math.round(color[5]) : "") + "|" + px + "|" + (dark ? 1 : 0);
    var hit = spriteCache[key];
    if (hit) return hit;
    var pad = glow ? glow * 2 + 2 : 2;
    var cw = Math.ceil(px * def.w) + pad * 2;
    var ch = Math.ceil(px * def.h) + pad * 2;
    var canvas = document.createElement("canvas");
    canvas.width = cw;
    canvas.height = ch;
    var g = canvas.getContext("2d");
    g.translate(cw / 2, ch / 2);
    g.scale(px, px);
    if (def.neon) {
      g.lineCap = g.lineJoin = "round";
      g.shadowColor = css(color);
      g.shadowBlur = glow * 2;
      g.strokeStyle = css(color);
      g.lineWidth = 0.075;
      g.beginPath(); def.path(g); g.stroke();
      g.shadowBlur = 0;
      g.strokeStyle = css(mix(color, WHITE, 0.65));
      g.lineWidth = 0.028;
      g.beginPath(); def.path(g); g.stroke();
    } else if (def.line) {
      g.lineCap = g.lineJoin = "round";
      g.strokeStyle = css(color);
      g.lineWidth = 2.6 / px;
      g.beginPath(); def.path(g); g.stroke();
    } else {
      if (glow) { g.shadowColor = css(color, 0.9); g.shadowBlur = glow * 2; }
      def.draw(g, color, px, dark);
    }
    hit = { img: canvas, w: cw / 2, h: ch / 2 };
    spriteCache[key] = hit;
    return hit;
  }

  function drawSprite(ctx, sp, x, y, rot, sx, sy, alpha, dpr) {
    var c = Math.cos(rot), s = Math.sin(rot);
    ctx.setTransform(c * sx * dpr, s * sx * dpr, -s * sy * dpr, c * sy * dpr, x * dpr, y * dpr);
    ctx.globalAlpha = alpha;
    ctx.drawImage(sp.img, -sp.w / 2, -sp.h / 2, sp.w, sp.h);
  }

  /* ---------------------------------------------------------------- tekenvlak */
  /* De maat van een tekenvlak wordt alleen opnieuw gelezen als die veranderd kan zijn (ResizeObserver,
     of een resize van het venster). Bij elk beeld clientWidth lezen dwingt de browser om de hele opmaak
     opnieuw te berekenen terwijl er CSS-animaties lopen; dat kostte op een trage telefoon honderden ms. */
  var stages = [];
  var sizeObserver = window.ResizeObserver ? new window.ResizeObserver(function (entries) {
    for (var i = 0; i < entries.length; i++) {
      for (var j = 0; j < stages.length; j++) if (stages[j].host === entries[i].target) stages[j].dirty = true;
    }
  }) : null;
  function Stage(host, fixed, maxDpr) {
    this.host = host;
    this.fixed = fixed;
    this.maxDpr = maxDpr;
    this.canvas = document.createElement("canvas");
    this.canvas.className = "fx-canvas";
    this.canvas.setAttribute("aria-hidden", "true");
    host.appendChild(this.canvas);
    this.ctx = this.canvas.getContext("2d");
    this.w = 0; this.h = 0; this.dpr = 1;
    this.dirty = true;
    stages.push(this);
    if (sizeObserver) sizeObserver.observe(host);
  }
  Stage.prototype.resize = function () {
    if (!this.dirty) return false;
    this.dirty = false;
    var w = this.host.clientWidth || window.innerWidth;
    var h = this.host.clientHeight || window.innerHeight;
    var dpr = Math.min(window.devicePixelRatio || 1, this.maxDpr);
    if (w === this.w && h === this.h && dpr === this.dpr) return false;
    this.w = w; this.h = h; this.dpr = dpr;
    this.canvas.width = Math.max(1, Math.round(w * dpr));
    this.canvas.height = Math.max(1, Math.round(h * dpr));
    return true;
  };
  Stage.prototype.clear = function () {
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.globalAlpha = 1;
    this.ctx.globalCompositeOperation = "source-over";
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  };

  /* ---------------------------------------------------------------- sfeer: soorten */
  var AMBIENT = {
    blaadjes: { type: "drift", sprites: [["petal", 1]], colors: "bloem", density: 5.5, min: 12, max: 30, size: [11, 19], speed: [24, 50], dir: "down", sway: [16, 40], swayFreq: [0.35, 0.8], spin: [-1.1, 1.1], flip: [1, 2.8], alpha: [0.72, 0.95] },
    bloesem: { type: "drift", sprites: [["blossom", 0.45], ["petal", 0.55]], colors: "bloesem", density: 6, min: 14, max: 32, size: [11, 19], speed: [22, 46], dir: "down", sway: [14, 36], swayFreq: [0.4, 0.9], spin: [-1.3, 1.3], flip: [1, 3], alpha: [0.75, 0.98] },
    bladeren: { type: "drift", sprites: [["leafRound", 0.6], ["leafLong", 0.4]], colors: "blad", density: 4.5, min: 10, max: 24, size: [12, 21], speed: [22, 44], dir: "down", sway: [18, 44], swayFreq: [0.3, 0.7], spin: [-1, 1], flip: [0.8, 2.4], alpha: [0.7, 0.92] },
    lauwerblaadjes: { type: "drift", sprites: [["leafLong", 1]], colors: "blad", density: 4.5, min: 10, max: 24, size: [14, 24], speed: [22, 44], dir: "down", sway: [18, 44], swayFreq: [0.3, 0.7], spin: [-1, 1], flip: [0.8, 2.4], alpha: [0.7, 0.92] },
    pluisjes: { type: "drift", sprites: [["fluff", 1]], colors: "pluis", density: 2, min: 6, max: 13, size: [34, 66], speed: [10, 22], dir: "right", drop: [3, 10], sway: [8, 22], swayFreq: [0.2, 0.45], spin: [-0.25, 0.25], alpha: [0.4, 0.7] },
    confetti: { type: "drift", sprites: [["rect", 0.45], ["circle", 0.2], ["ribbon", 0.2], ["tri", 0.15]], colors: "feest", density: 6.5, min: 14, max: 36, size: [7, 12], speed: [34, 70], dir: "down", sway: [10, 26], swayFreq: [0.5, 1.2], spin: [-3, 3], flip: [2, 6], alpha: [0.85, 1], back: true },
    harten: { type: "drift", sprites: [["heart", 1]], colors: "hart", density: 3.6, min: 8, max: 20, size: [10, 22], speed: [16, 36], dir: "up", sway: [12, 30], swayFreq: [0.3, 0.7], spin: [-0.35, 0.35], alpha: [0.5, 0.88] },
    ballonnen: { type: "drift", sprites: [["balloon", 1]], colors: "feest", density: 1.4, min: 5, max: 10, size: [26, 44], speed: [24, 44], dir: "up", sway: [6, 16], swayFreq: [0.25, 0.55], spin: [-0.12, 0.12], alpha: [0.88, 1], string: true },
    bellen: { type: "drift", sprites: [["bubble", 1]], colors: "bel", density: 2.4, min: 7, max: 15, size: [14, 44], speed: [14, 34], dir: "up", sway: [10, 26], swayFreq: [0.3, 0.7], wobble: true, alpha: [0.7, 1] },
    champagne: { type: "drift", sprites: [["fizz", 1]], colors: "bubbel", density: 9, min: 24, max: 60, size: [3, 9], speed: [30, 80], dir: "up", sway: [2, 7], swayFreq: [1.4, 3], alpha: [0.35, 0.8] },
    bokeh: { type: "drift", sprites: [["orb", 1]], colors: "licht", density: 1.7, min: 7, max: 14, size: [44, 130], speed: [4, 13], dir: "any", alpha: [0.2, 0.45], pulse: [0.12, 0.3] },
    stippen: { type: "drift", sprites: [["dot", 1]], colors: "feest", density: 3.2, min: 9, max: 22, size: [7, 22], speed: [7, 18], dir: "any", sway: [3, 9], swayFreq: [0.3, 0.8], alpha: [0.5, 0.9] },
    stofjes: { type: "drift", sprites: [["speck", 1]], colors: "stof", density: 8, min: 18, max: 56, size: [2, 4.5], speed: [3, 10], dir: "any", alpha: [0.18, 0.45], pulse: [0.2, 0.6] },
    zonlicht: { type: "drift", sprites: [["speck", 1]], colors: "zon", density: 6.5, min: 16, max: 44, size: [3, 8], speed: [5, 14], dir: "up", sway: [6, 16], swayFreq: [0.2, 0.5], alpha: [0.28, 0.66], pulse: [0.3, 0.8] },
    neon: { type: "drift", sprites: [["nRing", 1], ["nTriangle", 1], ["nZigzag", 1], ["nPlus", 1], ["nWave", 1]], colors: "neon", density: 2, min: 8, max: 16, size: [20, 42], speed: [6, 16], dir: "any", spin: [-0.4, 0.4], alpha: [0.55, 0.92], pulse: [0.2, 0.5], blend: true },
    geometrie: { type: "drift", sprites: [["oRing", 1], ["oDiamond", 1], ["oSquare", 1], ["oTriangle", 1], ["oLine", 1], ["oArc", 1]], colors: "geo", density: 2.4, min: 8, max: 18, size: [16, 56], speed: [5, 14], dir: "any", spin: [-0.3, 0.3], alpha: [0.2, 0.42] },
    wolkjes: { type: "multi", layers: [
      { type: "drift", sprites: [["cloud", 1]], colors: "wolk", density: 0.8, min: 4, max: 8, size: [44, 88], speed: [6, 16], dir: "right", sway: [2, 6], swayFreq: [0.1, 0.25], alpha: [0.65, 0.95] },
      { type: "field", colors: "feest", specks: { density: 0 }, flares: { rate: 0.9, size: [8, 14], life: [1.2, 2] } }
    ] },
    cadeautjes: { type: "multi", layers: [
      { type: "drift", sprites: [["gift", 1]], colors: "cadeau", density: 1.5, min: 5, max: 11, size: [17, 30], speed: [24, 46], dir: "down", sway: [10, 24], swayFreq: [0.3, 0.65], spin: [-0.7, 0.7], alpha: [0.92, 1] },
      { type: "drift", sprites: [["rect", 0.5], ["circle", 0.3], ["ribbon", 0.2]], colors: "feest", density: 2.4, min: 6, max: 16, size: [6, 10], speed: [30, 60], dir: "down", sway: [8, 20], swayFreq: [0.5, 1.1], spin: [-3, 3], flip: [2, 6], alpha: [0.8, 1], back: true }
    ] },
    sneeuw: { type: "multi", layers: [
      { type: "drift", sprites: [["flake", 1]], colors: "sneeuwzacht", density: 8, min: 22, max: 80, size: [3, 8.5], speed: [18, 46], dir: "down", sway: [5, 20], swayFreq: [0.18, 0.5], alpha: [0.55, 0.95] },
      { type: "drift", sprites: [["crystal", 1]], colors: "sneeuw", density: 0.8, min: 3, max: 9, size: [11, 20], speed: [15, 28], dir: "down", sway: [10, 26], swayFreq: [0.2, 0.45], spin: [-0.6, 0.6], alpha: [0.55, 0.9] }
    ] },
    goudstof: { type: "field", colors: "goud", specks: { density: 10, min: 24, max: 70, size: [1.4, 3.4], drift: [3, 11], alpha: [0.35, 0.95], twinkle: [0.6, 1.8] }, flares: { rate: 1.1, size: [9, 18], life: [0.9, 1.6] } },
    glitter: { type: "field", colors: "goud", specks: { density: 22, min: 50, max: 140, size: [1.2, 3.8], drift: [4, 14], alpha: [0.35, 1], twinkle: [1, 3] }, flares: { rate: 3.4, size: [10, 24], life: [0.8, 1.4] } },
    sterren: { type: "field", colors: "ster", stars: true, specks: { density: 34, min: 60, max: 220, size: [1, 3], drift: [1.5, 5], alpha: [0.35, 1], twinkle: [0.4, 1.6] }, flares: { rate: 0.45, size: [8, 16], life: [1.4, 2.4] }, shooting: [2.5, 6.5] },
    netwerk: { type: "network", colors: "geo" },
    raster: { type: "grid", colors: "geo" },
    film: { type: "film", colors: "film" }
  };

  /* Drijvende deeltjes: vallen, stijgen, waaien of zweven. */
  function DriftSystem(cfg) { this.cfg = cfg; this.list = []; }
  DriftSystem.prototype.target = function (scene) {
    var c = this.cfg;
    var n = c.density * scene.stage.w * scene.stage.h / 100000;
    return Math.round(clamp(n, c.min, c.max) * scene.quality * scene.density);
  };
  DriftSystem.prototype.spawn = function (scene, p, initial) {
    var c = this.cfg, st = scene.stage;
    var colors = scene.colors[c.colors];
    p.kind = pickWeighted(c.sprites);
    p.color = pick(colors);
    p.size = range(c.size);
    var depth = (p.size - c.size[0]) / Math.max(1, c.size[1] - c.size[0]);
    var speed = rand(c.speed[0], c.speed[1]) * (0.75 + depth * 0.5);
    p.vx = 0; p.vy = 0;
    var m = p.size * 1.6;
    if (c.dir === "down") { p.vy = speed; p.x = rand(-m, st.w + m); p.y = initial ? rand(-m, st.h) : -m - rand(0, 40); }
    else if (c.dir === "up") { p.vy = -speed; p.x = rand(-m, st.w + m); p.y = initial ? rand(0, st.h + m) : st.h + m + rand(0, 40); }
    else if (c.dir === "right") { p.vx = speed; p.vy = c.drop ? range(c.drop) : 0; p.x = initial ? rand(-m, st.w) : -m - rand(0, 60); p.y = rand(-m, st.h * 0.9); }
    else { var a = rand(0, TAU); p.vx = Math.cos(a) * speed; p.vy = Math.sin(a) * speed; p.x = rand(0, st.w); p.y = rand(0, st.h); }
    p.sa = c.sway ? range(c.sway) : 0;
    p.sf = c.swayFreq ? range(c.swayFreq) * TAU : 0;
    p.ph = rand(0, TAU);
    p.rot = rand(0, TAU);
    p.spin = c.spin ? range(c.spin) : 0;
    p.flip = rand(0, TAU);
    p.fs = c.flip ? range(c.flip) : 0;
    p.alpha = range(c.alpha);
    p.pulse = c.pulse ? range(c.pulse) * TAU : 0;
    p.t = 0;
    p.fade = initial ? 1 : 0;
    return p;
  };
  DriftSystem.prototype.step = function (scene, dt) {
    var list = this.list, target = this.target(scene), i;
    while (list.length < target) list.push(this.spawn(scene, {}, scene.fresh));
    if (list.length > target) list.length = target;
    var st = scene.stage, c = this.cfg, wind = scene.wind;
    for (i = 0; i < list.length; i++) {
      var p = list[i];
      p.t += dt;
      p.x += (p.vx + (c.dir === "any" ? 0 : wind * (0.4 + p.size / 40))) * dt;
      p.y += p.vy * dt;
      if (scene.shift) p.y -= scene.shift * (0.04 + p.size / 260);
      p.rot += p.spin * dt;
      p.flip += p.fs * dt;
      if (p.fade < 1) p.fade = Math.min(1, p.fade + dt * 0.8);
      var m = p.size * 2 + p.sa;
      if (c.dir === "any") {
        if (p.x < -m) p.x = st.w + m; else if (p.x > st.w + m) p.x = -m;
        if (p.y < -m) p.y = st.h + m; else if (p.y > st.h + m) p.y = -m;
      } else if (p.y > st.h + m || p.y < -m - 60 || p.x > st.w + m + 60 || p.x < -m - 60) {
        this.spawn(scene, p, false);
      }
    }
  };
  DriftSystem.prototype.draw = function (scene) {
    var ctx = scene.stage.ctx, dpr = scene.stage.dpr, c = this.cfg, dark = scene.pal.dark;
    if (c.blend && dark) ctx.globalCompositeOperation = "lighter";
    for (var i = 0; i < this.list.length; i++) {
      var p = this.list[i];
      var x = p.x + (p.sf ? Math.sin(p.t * p.sf + p.ph) * p.sa : 0);
      var sy = c.flip ? Math.cos(p.flip) : 1;
      var sx = 1;
      if (c.wobble) { var w = Math.sin(p.t * 2.2 + p.ph) * 0.05; sx = 1 + w; sy = 1 - w; }
      var a = p.alpha * p.fade;
      if (p.pulse) a *= 0.72 + 0.28 * Math.sin(p.t * p.pulse + p.ph);
      var color = c.back && sy < 0 ? mix(p.color, BLACK, 0.22) : p.color;
      var sp = getSprite(p.kind, color, p.size, dark);
      if (c.string) {
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.globalAlpha = a * 0.55;
        ctx.strokeStyle = css(dark ? mix(p.color, WHITE, 0.5) : mix(p.color, BLACK, 0.35));
        ctx.lineWidth = 1;
        var by = p.y + p.size * 0.46, sway = Math.sin(p.t * 1.4 + p.ph) * p.size * 0.3;
        ctx.beginPath();
        ctx.moveTo(x, by);
        ctx.bezierCurveTo(x + sway, by + p.size * 0.6, x - sway, by + p.size * 1.1, x + sway * 0.6, by + p.size * 1.7);
        ctx.stroke();
        drawSprite(ctx, sp, x, p.y, Math.sin(p.t * 0.8 + p.ph) * 0.08, 1, 1, a, dpr);
      } else {
        drawSprite(ctx, sp, x, p.y, p.rot, sx, sy, a, dpr);
      }
    }
    ctx.globalCompositeOperation = "source-over";
  };

  /* Veld met glinsteringen: stofjes die fonkelen, af en toe een ster, soms een vallende ster. */
  function FieldSystem(cfg) { this.cfg = cfg; this.specks = []; this.flares = []; this.shots = []; this.nextShot = cfg.shooting ? range(cfg.shooting) * 0.5 : 0; }
  FieldSystem.prototype.target = function (scene) {
    var s = this.cfg.specks;
    if (!s || !s.density) return 0;
    return Math.round(clamp(s.density * scene.stage.w * scene.stage.h / 100000, s.min, s.max) * scene.quality);
  };
  FieldSystem.prototype.step = function (scene, dt) {
    var c = this.cfg, st = scene.stage, colors = scene.colors[c.colors], i;
    var target = this.target(scene);
    while (this.specks.length < target) {
      var a = rand(0, TAU), sp = c.specks.drift ? range(c.specks.drift) : 0;
      this.specks.push({ x: rand(0, st.w), y: rand(0, st.h), vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - (c.stars ? 0 : sp * 0.4),
        s: range(c.specks.size), a: range(c.specks.alpha), ph: rand(0, TAU), f: range(c.specks.twinkle) * TAU, color: pick(colors), t: 0 });
    }
    if (this.specks.length > target) this.specks.length = target;
    for (i = 0; i < this.specks.length; i++) {
      var p = this.specks[i];
      p.t += dt;
      p.x += (p.vx + (c.stars ? -2 : 0)) * dt;
      p.y += p.vy * dt;
      if (p.x < -4) p.x = st.w + 4; else if (p.x > st.w + 4) p.x = -4;
      if (p.y < -4) p.y = st.h + 4; else if (p.y > st.h + 4) p.y = -4;
    }
    if (c.flares && Math.random() < c.flares.rate * scene.quality * dt * Math.min(2.2, st.w * st.h / 330000)) {
      this.flares.push({ x: rand(st.w * 0.04, st.w * 0.96), y: rand(st.h * 0.04, st.h * 0.96), s: range(c.flares.size), life: range(c.flares.life), t: 0, rot: rand(-0.3, 0.3), color: pick(colors) });
    }
    for (i = this.flares.length - 1; i >= 0; i--) {
      this.flares[i].t += dt;
      if (this.flares[i].t >= this.flares[i].life) this.flares.splice(i, 1);
    }
    if (c.shooting) {
      this.nextShot -= dt;
      if (this.nextShot <= 0) {
        this.nextShot = range(c.shooting);
        var ang = rand(0.52, 0.85) * Math.PI;
        this.shots.push({ x: rand(st.w * 0.35, st.w * 1.05), y: rand(-10, st.h * 0.35), vx: Math.cos(ang) * 780, vy: Math.sin(ang) * 780, t: 0, life: rand(0.55, 0.85) });
      }
      for (i = this.shots.length - 1; i >= 0; i--) {
        var s = this.shots[i];
        s.t += dt; s.x += s.vx * dt; s.y += s.vy * dt;
        if (s.t >= s.life) this.shots.splice(i, 1);
      }
    }
  };
  FieldSystem.prototype.draw = function (scene) {
    var ctx = scene.stage.ctx, dpr = scene.stage.dpr, dark = scene.pal.dark, i;
    if (dark) ctx.globalCompositeOperation = "lighter";
    for (i = 0; i < this.specks.length; i++) {
      var p = this.specks[i];
      var tw = 0.5 + 0.5 * Math.sin(p.t * p.f + p.ph);
      var a = p.a * (this.cfg.stars ? 0.45 + 0.55 * tw : 0.25 + 0.75 * tw * tw);
      drawSprite(ctx, getSprite("speck", p.color, p.s * 2.2, dark), p.x, p.y, 0, 1, 1, a * scene.fade, dpr);
    }
    for (i = 0; i < this.flares.length; i++) {
      var f = this.flares[i];
      var k = Math.sin(Math.PI * f.t / f.life);
      drawSprite(ctx, getSprite("glint", f.color, f.s, dark), f.x, f.y, f.rot + f.t * 0.6, k, k, Math.min(1, k * 1.2) * scene.fade, dpr);
    }
    for (i = 0; i < this.shots.length; i++) {
      var s = this.shots[i];
      var fade = Math.sin(Math.PI * s.t / s.life);
      var tx = s.x - s.vx * 0.16, ty = s.y - s.vy * 0.16;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalAlpha = fade * scene.fade;
      var grad = ctx.createLinearGradient(s.x, s.y, tx, ty);
      grad.addColorStop(0, "rgba(255,255,255,0.95)");
      grad.addColorStop(1, "rgba(255,255,255,0)");
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.6;
      ctx.lineCap = "round";
      ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(tx, ty); ctx.stroke();
      drawSprite(ctx, getSprite("speck", WHITE, 7, dark), s.x, s.y, 0, 1, 1, fade * scene.fade, dpr);
    }
    ctx.globalCompositeOperation = "source-over";
  };

  /* Netwerk: punten die bewegen en lijnen trekken naar punten dichtbij. */
  function NetworkSystem(cfg) { this.cfg = cfg; this.nodes = []; this.packets = []; this.nextPacket = 0.5; }
  NetworkSystem.prototype.step = function (scene, dt) {
    var st = scene.stage, i;
    var target = Math.round(clamp(2.3 * st.w * st.h / 100000, 14, 58) * scene.quality);
    while (this.nodes.length < target) {
      var a = rand(0, TAU), sp = rand(8, 20);
      this.nodes.push({ x: rand(0, st.w), y: rand(0, st.h), vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, r: rand(1.4, 2.6) });
    }
    if (this.nodes.length > target) this.nodes.length = target;
    for (i = 0; i < this.nodes.length; i++) {
      var n = this.nodes[i];
      n.x += n.vx * dt; n.y += n.vy * dt;
      if (n.x < 0 || n.x > st.w) { n.vx *= -1; n.x = clamp(n.x, 0, st.w); }
      if (n.y < 0 || n.y > st.h) { n.vy *= -1; n.y = clamp(n.y, 0, st.h); }
    }
    this.link = st.w < 700 ? 110 : 150;
    this.nextPacket -= dt;
    if (this.nextPacket <= 0 && this.nodes.length > 2) {
      this.nextPacket = rand(0.4, 0.9);
      var from = pick(this.nodes), best = null, bd = 1e9;
      for (i = 0; i < this.nodes.length; i++) {
        var o = this.nodes[i];
        if (o === from) continue;
        var d = Math.hypot(o.x - from.x, o.y - from.y);
        if (d < this.link && d < bd && Math.random() < 0.7) { bd = d; best = o; }
      }
      if (best) this.packets.push({ a: from, b: best, t: 0, life: rand(0.6, 1.1) });
    }
    for (i = this.packets.length - 1; i >= 0; i--) {
      this.packets[i].t += dt;
      if (this.packets[i].t >= this.packets[i].life) this.packets.splice(i, 1);
    }
  };
  NetworkSystem.prototype.draw = function (scene) {
    var ctx = scene.stage.ctx, dpr = scene.stage.dpr, nodes = this.nodes, link = this.link;
    var color = scene.colors.geo[0], i, j;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.strokeStyle = css(color);
    ctx.lineWidth = 1;
    for (i = 0; i < nodes.length; i++) {
      for (j = i + 1; j < nodes.length; j++) {
        var dx = nodes[i].x - nodes[j].x, dy = nodes[i].y - nodes[j].y;
        if (dx > link || dx < -link || dy > link || dy < -link) continue;
        var d = Math.sqrt(dx * dx + dy * dy);
        if (d >= link) continue;
        ctx.globalAlpha = (1 - d / link) * 0.32 * scene.fade;
        ctx.beginPath(); ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[j].x, nodes[j].y); ctx.stroke();
      }
    }
    ctx.fillStyle = css(color);
    ctx.globalAlpha = 0.55 * scene.fade;
    ctx.beginPath();
    for (i = 0; i < nodes.length; i++) { ctx.moveTo(nodes[i].x + nodes[i].r, nodes[i].y); ctx.arc(nodes[i].x, nodes[i].y, nodes[i].r, 0, TAU); }
    ctx.fill();
    for (i = 0; i < this.packets.length; i++) {
      var p = this.packets[i], k = p.t / p.life;
      var x = p.a.x + (p.b.x - p.a.x) * k, y = p.a.y + (p.b.y - p.a.y) * k;
      drawSprite(ctx, getSprite("speck", scene.colors.geo[1] || color, 9, scene.pal.dark), x, y, 0, 1, 1, Math.sin(Math.PI * k) * scene.fade, dpr);
    }
  };

  /* Raster: een veld van puntjes waar rustig een lichtgolf overheen gaat. */
  function GridSystem(cfg) { this.cfg = cfg; this.t = 0; this.ripples = []; this.nextRipple = 1.2; }
  GridSystem.prototype.step = function (scene, dt) {
    this.t += dt;
    this.nextRipple -= dt;
    if (this.nextRipple <= 0) {
      this.nextRipple = rand(2.2, 4.5);
      this.ripples.push({ x: rand(0, scene.stage.w), y: rand(0, scene.stage.h), t: 0 });
    }
    for (var i = this.ripples.length - 1; i >= 0; i--) {
      this.ripples[i].t += dt;
      if (this.ripples[i].t > 4) this.ripples.splice(i, 1);
    }
  };
  GridSystem.prototype.draw = function (scene) {
    var st = scene.stage, ctx = st.ctx, dpr = st.dpr, gap = st.w < 700 ? 24 : 28;
    var color = scene.colors.geo[0], t = this.t, levels = [], L = 7, i;
    for (i = 0; i < L; i++) levels.push([]);
    var ox = (st.w % gap) / 2, oy = (st.h % gap) / 2;
    for (var y = oy; y <= st.h; y += gap) {
      for (var x = ox; x <= st.w; x += gap) {
        var wave = Math.sin((x * 0.6 + y) * 0.012 - t * 1.1);
        var v = wave > 0 ? Math.pow(wave, 8) : 0;
        for (i = 0; i < this.ripples.length; i++) {
          var r = this.ripples[i], d = Math.hypot(x - r.x, y - r.y) - r.t * 170;
          v += Math.exp(-d * d / 1400) * (1 - r.t / 4) * 0.9;
        }
        levels[Math.min(L - 1, Math.floor(v * L))].push(x, y);
      }
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = css(color);
    for (i = 0; i < L; i++) {
      var pts = levels[i];
      if (!pts.length) continue;
      ctx.globalAlpha = (0.1 + i * 0.1) * scene.fade;
      var s = 1.1 + i * 0.22;
      ctx.beginPath();
      for (var k = 0; k < pts.length; k += 2) ctx.rect(pts[k] - s, pts[k + 1] - s, s * 2, s * 2);
      ctx.fill();
    }
  };

  /* Film: korrel, stofjes en af en toe een krasje, zoals bij een oude projector. */
  function FilmSystem(cfg) { this.cfg = cfg; this.tiles = null; this.acc = 0; this.scratch = null; this.nextScratch = 1.5; this.dust = []; }
  FilmSystem.prototype.makeTiles = function (scene) {
    var color = scene.colors.film[0], dark = scene.pal.dark;
    this.tiles = [];
    for (var n = 0; n < 3; n++) {
      var c = document.createElement("canvas");
      c.width = c.height = 128;
      var g = c.getContext("2d"), img = g.createImageData(128, 128);
      for (var i = 0; i < img.data.length; i += 4) {
        var v = Math.random();
        img.data[i] = color[0]; img.data[i + 1] = color[1]; img.data[i + 2] = color[2];
        img.data[i + 3] = v > 0.55 ? Math.round((v - 0.55) * (dark ? 70 : 85)) : 0;
      }
      g.putImageData(img, 0, 0);
      this.tiles.push(scene.stage.ctx.createPattern(c, "repeat"));
    }
  };
  FilmSystem.prototype.step = function (scene, dt) {
    if (!this.tiles) this.makeTiles(scene);
    this.acc += dt;
    this.nextScratch -= dt;
    if (!this.scratch && this.nextScratch <= 0) {
      this.scratch = { x: rand(0.1, 0.9) * scene.stage.w, t: 0, life: rand(0.5, 1.4) };
      this.nextScratch = rand(2, 6);
    }
    if (this.scratch) { this.scratch.t += dt; if (this.scratch.t > this.scratch.life) this.scratch = null; }
  };
  FilmSystem.prototype.frameDue = function () {
    if (this.acc < 1 / 12) return false;
    this.acc = 0;
    return true;
  };
  FilmSystem.prototype.draw = function (scene) {
    var st = scene.stage, ctx = st.ctx, dpr = st.dpr, color = scene.colors.film[0];
    ctx.setTransform(dpr, 0, 0, dpr, rand(-64, 0) * dpr, rand(-64, 0) * dpr);
    ctx.globalAlpha = scene.fade;
    ctx.fillStyle = pick(this.tiles);
    ctx.fillRect(0, 0, st.w + 64, st.h + 64);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = css(color);
    var n = Math.random() < 0.6 ? Math.floor(rand(1, 4)) : 0;
    for (var i = 0; i < n; i++) {
      ctx.globalAlpha = rand(0.12, 0.3) * scene.fade;
      ctx.beginPath(); ctx.arc(rand(0, st.w), rand(0, st.h), rand(0.6, 2.2), 0, TAU); ctx.fill();
    }
    if (Math.random() < 0.08) {
      ctx.strokeStyle = css(color);
      ctx.globalAlpha = 0.18 * scene.fade;
      ctx.lineWidth = 0.8;
      var hx = rand(0, st.w), hy = rand(0, st.h);
      ctx.beginPath(); ctx.moveTo(hx, hy); ctx.quadraticCurveTo(hx + rand(-12, 12), hy + rand(4, 12), hx + rand(-16, 16), hy + rand(10, 24)); ctx.stroke();
    }
    if (this.scratch) {
      ctx.strokeStyle = css(color);
      ctx.globalAlpha = 0.16 * Math.sin(Math.PI * this.scratch.t / this.scratch.life) * scene.fade;
      ctx.lineWidth = 1;
      var x = this.scratch.x + rand(-1.5, 1.5);
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + rand(-4, 4), st.h); ctx.stroke();
    }
  };

  function makeSystem(cfg) {
    if (cfg.type === "drift") return new DriftSystem(cfg);
    if (cfg.type === "field") return new FieldSystem(cfg);
    if (cfg.type === "network") return new NetworkSystem(cfg);
    if (cfg.type === "grid") return new GridSystem(cfg);
    if (cfg.type === "film") return new FilmSystem(cfg);
    return null;
  }

  /* ---------------------------------------------------------------- sfeer: een scène per vlak */
  function Scene(slot, name) {
    var cfg = AMBIENT[name];
    this.slot = slot;
    this.name = name;
    /* Het openingsscherm scherp; achter de tekst mag het iets zachter (scheelt veel rekenwerk). */
    this.stage = new Stage(slot, slot.classList.contains("fx-slot--page"), slot.getAttribute("data-fx-slot") === "cover" ? 1.5 : 1);
    this.systems = (cfg.type === "multi" ? cfg.layers : [cfg]).map(makeSystem).filter(Boolean);
    this.quality = lowPower ? 0.7 : 1;
    /* Een ontwerp kan met --fx-density (0 tot 1, in de stijl) minder deeltjes vragen: "enkele blaadjes" in plaats van een bui. */
    var dens = parseFloat(window.getComputedStyle(slot).getPropertyValue("--fx-density"));
    this.density = dens > 0 && dens < 1 ? dens : 1;
    this.acc = 1;
    this.fresh = true;
    this.fade = 1;
    this.wind = 0;
    this.sdy = 0;
    this.sv = 0;
    this.shift = 0;
    this.t = 0;
    this.active = false;
    this.visible = true;
    this.pal = null;
    this.colors = null;
  }
  Scene.prototype.refresh = function () {
    this.pal = paletteFor(this.slot);
    var colors = {};
    for (var key in COLORS) colors[key] = COLORS[key](this.pal);
    this.colors = colors;
  };
  Scene.prototype.frame = function (dt) {
    /* Rustig zwevende deeltjes zien er met 30 beelden per seconde net zo vloeiend uit en kosten de helft. */
    this.acc += dt;
    if (this.acc < 1 / 31) return;
    dt = Math.min(0.1, this.acc);
    this.acc = 0;
    if (this.stage.resize() || !this.pal) this.refresh();
    this.t += dt;
    this.wind = Math.sin(this.t * 0.23) * 10 + Math.sin(this.t * 0.07) * 6;
    if (settings.scrollwind) {
      /* Scrollen duwt de deeltjes zacht opzij en verschuift ze licht mee: grote blaadjes iets meer dan kleine (diepte). */
      this.sv += (this.sdy / dt - this.sv) * 0.12;
      this.wind += clamp(this.sv * 0.02, -16, 16);
      this.shift = this.sdy;
      this.sdy = 0;
    }
    var due = true, i;
    for (i = 0; i < this.systems.length; i++) {
      this.systems[i].step(this, dt);
      if (this.systems[i].frameDue && !this.systems[i].frameDue()) due = false;
    }
    this.fresh = false;
    if (!due) return;
    this.stage.clear();
    for (i = 0; i < this.systems.length; i++) this.systems[i].draw(this);
  };
  Scene.prototype.setActive = function (on) {
    if (on === this.active) return;
    this.active = on;
    this.slot.classList.toggle("is-running", on);
    if (on) wake();
  };

  /* ---------------------------------------------------------------- knal en viering */
  var burst = { stage: null, list: [], pal: null, colors: null, flash: null };

  function burstStage() {
    if (!burst.stage) {
      var host = document.createElement("div");
      host.className = "fx-burst";
      host.setAttribute("aria-hidden", "true");
      body.appendChild(host);
      burst.stage = new Stage(host, true, 1.5);
    }
    burst.stage.resize();
    return burst.stage;
  }

  function burstColors(from) {
    var pal = paletteFor(from || body), colors = {};
    for (var key in COLORS) colors[key] = COLORS[key](pal);
    burst.pal = pal;
    burst.colors = colors;
    return colors;
  }

  function addParticle(opts) {
    var p = {
      kind: opts.kind || "sprite", sprite: opts.sprite, color: opts.color, size: opts.size || 10,
      x: opts.x, y: opts.y, vx: opts.vx || 0, vy: opts.vy || 0, g: opts.g || 0, drag: opts.drag == null ? 0.5 : opts.drag,
      rot: opts.rot == null ? rand(0, TAU) : opts.rot, spin: opts.spin || 0, flip: rand(0, TAU), fs: opts.fs || 0,
      sa: opts.sa || 0, sf: opts.sf || 0, ph: rand(0, TAU), life: opts.life || 2, age: -(opts.delay || 0),
      grow: opts.grow || 0, pop: !!opts.pop, back: !!opts.back, glow: !!opts.glow, width: opts.width || 1.6,
      ox: opts.x, oy: opts.y, angle: opts.angle || 0, speed: opts.speed || 0, fadeIn: opts.fadeIn || 0.06
    };
    burst.list.push(p);
    return p;
  }

  /* Deeltjes die vanuit een punt wegspringen. */
  function spray(x, y, n, o) {
    var colors = burst.colors[o.colors];
    for (var i = 0; i < n; i++) {
      var ang = o.angle ? range(o.angle) : rand(0, TAU);
      var sp = range(o.speed);
      addParticle({
        sprite: o.sprites ? pickWeighted(o.sprites) : o.sprite, color: pick(colors), size: range(o.size),
        x: x + rand(-4, 4), y: y + rand(-4, 4), vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp,
        g: o.g, drag: o.drag, spin: o.spin ? range(o.spin) : 0, fs: o.flip ? range(o.flip) : 0,
        sa: o.sway ? range(o.sway) : 0, sf: o.sway ? rand(1.5, 3.5) : 0, life: range(o.life),
        delay: o.stagger ? rand(0, o.stagger) : 0, pop: o.pop, back: o.back, grow: o.grow
      });
    }
  }

  var UP = [-Math.PI * 0.95, -Math.PI * 0.05];
  var BURSTS = {
    blaadjes: function (x, y, k) { spray(x, y, 62 * k, { sprite: "petal", colors: "bloem", size: [11, 22], speed: [220, 820], angle: [-Math.PI * 1.02, 0.02], g: 170, drag: 0.28, spin: [-4, 4], flip: [2, 6], sway: [20, 50], life: [2.6, 3.8] }); },
    bloesem: function (x, y, k) { spray(x, y, 66 * k, { sprites: [["blossom", 0.5], ["petal", 0.5]], colors: "bloesem", size: [9, 18], speed: [220, 820], angle: [-Math.PI * 1.02, 0.02], g: 170, drag: 0.28, spin: [-4, 4], flip: [2, 6], sway: [20, 50], life: [2.6, 3.8] }); },
    lauwerblaadjes: function (x, y, k) { spray(x, y, 52 * k, { sprite: "leafLong", colors: "blad", size: [14, 26], speed: [220, 780], angle: [-Math.PI * 1.02, 0.02], g: 160, drag: 0.28, spin: [-4, 4], flip: [2, 5], sway: [20, 50], life: [2.6, 3.8] }); },
    bladeren: function (x, y, k) { spray(x, y, 52 * k, { sprites: [["leafRound", 0.6], ["leafLong", 0.4]], colors: "blad", size: [12, 23], speed: [220, 780], angle: [-Math.PI * 1.02, 0.02], g: 160, drag: 0.28, spin: [-4, 4], flip: [2, 5], sway: [20, 50], life: [2.6, 3.8] }); },
    pluisjes: function (x, y, k) { spray(x, y, 16 * k, { sprite: "fluff", colors: "pluis", size: [30, 56], speed: [60, 260], angle: UP, g: -10, drag: 0.35, spin: [-1, 1], sway: [20, 40], life: [2.6, 3.8] }); },
    confetti: function (x, y, k) { spray(x, y, 110 * k, { sprites: [["rect", 0.5], ["circle", 0.2], ["ribbon", 0.2], ["tri", 0.1]], colors: "feest", size: [7, 13], speed: [240, 900], angle: [-Math.PI * 1.05, 0.05], g: 520, drag: 0.3, spin: [-8, 8], flip: [4, 12], life: [2.2, 3.4], back: true }); },
    kanon: function (x, y, k) {
      var st = burst.stage, v = st.h;
      [[0, st.h, -Math.PI * 0.36], [st.w, st.h, -Math.PI * 0.64]].forEach(function (c) {
        spray(c[0], c[1] + 10, 80 * k, { sprites: [["rect", 0.5], ["circle", 0.18], ["ribbon", 0.22], ["tri", 0.1]], colors: "feest", size: [7, 13],
          speed: [v * 1.05, v * 1.9], angle: [c[2] - 0.22, c[2] + 0.22], g: v * 1.15, drag: 0.4, spin: [-9, 9], flip: [4, 12], life: [2.6, 3.8], back: true, stagger: 0.25 });
      });
    },
    vonken: function (x, y, k) {
      var colors = burst.colors.goud;
      for (var i = 0; i < 64 * k; i++) {
        var a = rand(0, TAU), sp = rand(260, 860);
        addParticle({ kind: "spark", color: pick(colors), x: x, y: y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 120, g: 380, drag: 0.12, life: rand(0.8, 1.5), width: rand(1.2, 2.4) });
      }
      spray(x, y, 40 * k, { sprites: [["rect", 0.6], ["ribbon", 0.4]], colors: "goud", size: [7, 13], speed: [200, 700], angle: [-Math.PI * 1.05, 0.05], g: 420, drag: 0.32, spin: [-8, 8], flip: [5, 12], life: [2.2, 3.2], back: true });
      spray(x, y, 14 * k, { sprite: "glint", colors: "goud", size: [10, 20], speed: [80, 320], g: 0, drag: 0.2, spin: [-2, 2], life: [0.9, 1.5], pop: true });
    },
    sterren: function (x, y, k) {
      spray(x, y, 26 * k, { sprite: "glint", colors: burst.pal.dark ? "ster" : "goud", size: [9, 22], speed: [60, 420], g: 0, drag: 0.18, spin: [-2, 2], life: [1.2, 2.2], pop: true });
      spray(x, y, 60 * k, { sprite: "speck", colors: burst.pal.dark ? "ster" : "goud", size: [4, 9], speed: [40, 520], g: 30, drag: 0.2, life: [1, 2.2] });
    },
    harten: function (x, y, k) { spray(x, y, 34 * k, { sprite: "heart", colors: "hart", size: [12, 26], speed: [120, 440], angle: UP, g: -40, drag: 0.3, spin: [-1.5, 1.5], sway: [10, 30], life: [1.8, 2.8], pop: true }); },
    bellen: function (x, y, k) { spray(x, y, 26 * k, { sprite: "bubble", colors: "bel", size: [14, 40], speed: [80, 300], angle: UP, g: -60, drag: 0.4, sway: [10, 30], life: [1.8, 3], pop: true }); },
    ballonnen: function (x, y, k) {
      var st = burst.stage, colors = burst.colors.feest;
      for (var i = 0; i < 12 * k; i++) {
        addParticle({ sprite: "balloon", color: pick(colors), size: rand(30, 52), x: rand(st.w * 0.05, st.w * 0.95), y: st.h + rand(40, 180),
          vx: rand(-20, 20), vy: -rand(st.h * 0.55, st.h * 0.95), g: 0, drag: 1, rot: 0, sa: rand(10, 24), sf: rand(1, 2), life: 3.2, delay: rand(0, 0.5) });
      }
      BURSTS.confetti(x, y, k * 0.35);
    },
    lijnen: function (x, y, k) {
      var colors = burst.colors.geo, n = Math.round(40 * Math.max(k, 0.3));
      for (var i = 0; i < n; i++) {
        var a = i / n * TAU + rand(-0.04, 0.04);
        addParticle({ kind: "ray", color: pick(colors), x: x, y: y, angle: a, speed: rand(340, 720), life: rand(0.9, 1.3), width: 1 });
      }
      addParticle({ kind: "ring", color: colors[0], x: x, y: y, speed: 420, life: 1.2, width: 1.2 });
      addParticle({ kind: "ring", color: colors[0], x: x, y: y, speed: 260, life: 1.4, width: 1, delay: 0.15 });
    },
    neon: function (x, y, k) {
      var colors = burst.colors.neon;
      for (var i = 0; i < 56 * k; i++) {
        var a = rand(0, TAU), sp = rand(200, 760);
        addParticle({ kind: "spark", color: pick(colors), x: x, y: y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 160, drag: 0.15, life: rand(0.8, 1.4), width: rand(1.6, 2.6), glow: true });
      }
      spray(x, y, 12 * k, { sprites: [["nRing", 1], ["nTriangle", 1], ["nZigzag", 1], ["nPlus", 1]], colors: "neon", size: [18, 34], speed: [120, 420], g: 60, drag: 0.3, spin: [-3, 3], life: [1.2, 2], pop: true });
    },
    flits: function (x, y, k) {
      flash();
      spray(x, y, 30 * k, { sprites: [["rect", 0.5], ["circle", 0.3], ["heart", 0.2]], colors: "feest", size: [7, 14], speed: [160, 560], angle: UP, g: 380, drag: 0.3, spin: [-6, 6], flip: [3, 9], life: [1.8, 2.8], back: true, delay: 0.1 });
    },
    champagne: function (x, y, k) {
      spray(x, y, 120 * k, { sprite: "fizz", colors: "bubbel", size: [4, 12], speed: [240, 820], angle: [-Math.PI * 0.64, -Math.PI * 0.36], g: -40, drag: 0.35, sway: [4, 14], life: [1.6, 2.8] });
      spray(x, y, 30 * k, { sprite: "speck", colors: "goud", size: [4, 8], speed: [120, 500], angle: UP, g: 200, drag: 0.3, life: [0.9, 1.6] });
    },
    stippen: function (x, y, k) { spray(x, y, 80 * k, { sprite: "dot", colors: "feest", size: [6, 18], speed: [220, 820], angle: [-Math.PI * 1.05, 0.05], g: 560, drag: 0.32, life: [2, 3], pop: true }); },
    netwerk: function (x, y, k) {
      var colors = burst.colors.geo;
      for (var i = 0; i < 30 * k; i++) {
        var a = rand(0, TAU), sp = rand(120, 520);
        addParticle({ kind: "node", color: pick(colors), x: x, y: y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, drag: 0.2, life: rand(1.2, 1.8), width: rand(2, 3.4) });
      }
    },
    bokeh: function (x, y, k) { spray(x, y, 18 * k, { sprite: "orb", colors: "licht", size: [30, 90], speed: [40, 220], g: -10, drag: 0.4, life: [1.6, 2.6], grow: 0.8 }); },
    sneeuw: function (x, y, k) {
      spray(x, y, 70 * k, { sprite: "flake", colors: "sneeuwzacht", size: [4, 11], speed: [120, 640], g: 70, drag: 0.22, sway: [6, 18], life: [1.8, 3.2] });
      spray(x, y, 16 * k, { sprite: "crystal", colors: "sneeuw", size: [12, 24], speed: [100, 470], g: 30, drag: 0.25, spin: [-2, 2], life: [1.6, 2.8], pop: true });
      spray(x, y, 16 * k, { sprite: "glint", colors: "goud", size: [10, 22], speed: [60, 360], g: 0, drag: 0.2, spin: [-2, 2], life: [0.9, 1.6], pop: true });
    },
    /* Plof: een drukgolf, dan springen de cadeautjes er in een boog uit, met confetti en glinsters. */
    cadeautjes: function (x, y, k) {
      var colors = burst.colors.cadeau, big = k >= 0.5;
      addParticle({ kind: "ring", color: burst.colors.goud[0], x: x, y: y, speed: big ? 100 : 36, life: 0.36, width: big ? 3.5 : 2 });
      for (var i = 0; i < Math.max(1, Math.round(15 * k)); i++) {
        var a = rand(-Math.PI * 0.82, -Math.PI * 0.18), sp = big ? rand(560, 1040) : rand(260, 520);
        addParticle({ sprite: "gift", color: pick(colors), size: big ? rand(20, 36) : rand(13, 20), x: x + rand(-12, 12), y: y + rand(-6, 6),
          vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 1150, drag: 0.5, rot: rand(-0.3, 0.3), spin: rand(-4.5, 4.5),
          life: rand(2.3, 3.1), pop: true, delay: rand(0, 0.14) });
      }
      spray(x, y, 70 * k, { sprites: [["rect", 0.45], ["circle", 0.25], ["ribbon", 0.3]], colors: "feest", size: [6, 12], speed: [260, 920], angle: [-Math.PI * 0.96, -Math.PI * 0.04], g: 620, drag: 0.3, spin: [-8, 8], flip: [4, 12], life: [2, 3.2], back: true });
      spray(x, y, 12 * k, { sprite: "glint", colors: "goud", size: [10, 22], speed: [60, 320], g: 0, drag: 0.2, spin: [-2, 2], life: [0.8, 1.3], pop: true });
    }
  };

  function fire(name, x, y, from, scale) {
    if (!BURSTS[name] || !motionOn()) return;
    burstStage();
    burstColors(from);
    BURSTS[name](x, y, scale || 1);
    wake();
  }

  function flash() {
    var el = document.createElement("div");
    el.className = "fx-flash";
    el.setAttribute("aria-hidden", "true");
    body.appendChild(el);
    if (el.animate) {
      el.animate([{ opacity: 0 }, { opacity: 0.85, offset: 0.12 }, { opacity: 0 }], { duration: 650, easing: "ease-out" }).onfinish = function () { el.remove(); };
    } else {
      window.setTimeout(function () { el.remove(); }, 700);
    }
  }

  function stepBurst(dt) {
    var st = burst.stage, list = burst.list, ctx = st.ctx, dpr = st.dpr;
    st.resize();
    st.clear();
    var dark = burst.pal.dark;
    for (var i = list.length - 1; i >= 0; i--) {
      var p = list[i];
      p.age += dt;
      if (p.age < 0) continue;
      if (p.age >= p.life) { list.splice(i, 1); continue; }
      var drag = Math.pow(p.drag, dt);
      p.vx *= drag; p.vy *= drag;
      p.vy += p.g * dt;
      p.x += p.vx * dt; p.y += p.vy * dt;
      p.rot += p.spin * dt;
      p.flip += p.fs * dt;
      var lifeK = p.age / p.life;
      var a = Math.min(1, p.age / p.fadeIn) * (lifeK > 0.62 ? 1 - (lifeK - 0.62) / 0.38 : 1);
      if (p.kind === "spark") {
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.globalCompositeOperation = dark ? "lighter" : "source-over";
        ctx.globalAlpha = a;
        ctx.strokeStyle = css(p.color);
        ctx.lineWidth = p.width;
        ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - p.vx * 0.045, p.y - p.vy * 0.045); ctx.stroke();
        if (p.glow) {
          ctx.globalAlpha = a * 0.28;
          ctx.lineWidth = p.width * 3.2;
          ctx.stroke();
        }
        ctx.globalCompositeOperation = "source-over";
      } else if (p.kind === "ray") {
        var r2 = p.speed * Math.pow(lifeK, 0.6), r1 = r2 * clamp(lifeK * 1.6, 0, 0.92);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.globalAlpha = a * 0.75;
        ctx.strokeStyle = css(p.color);
        ctx.lineWidth = p.width;
        ctx.beginPath();
        ctx.moveTo(p.ox + Math.cos(p.angle) * r1, p.oy + Math.sin(p.angle) * r1);
        ctx.lineTo(p.ox + Math.cos(p.angle) * r2, p.oy + Math.sin(p.angle) * r2);
        ctx.stroke();
      } else if (p.kind === "ring") {
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.globalAlpha = a * 0.6;
        ctx.strokeStyle = css(p.color);
        ctx.lineWidth = p.width;
        ctx.beginPath(); ctx.arc(p.ox, p.oy, Math.max(0.1, p.speed * Math.pow(lifeK, 0.55)), 0, TAU); ctx.stroke();
      } else if (p.kind === "node") {
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.globalAlpha = a * 0.35;
        ctx.strokeStyle = css(p.color);
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(p.ox, p.oy); ctx.lineTo(p.x, p.y); ctx.stroke();
        ctx.globalAlpha = a;
        ctx.fillStyle = css(p.color);
        ctx.beginPath(); ctx.arc(p.x, p.y, p.width, 0, TAU); ctx.fill();
      } else {
        var s = 1;
        if (p.pop) s = p.age < 0.25 ? 0.3 + 0.8 * Math.sin(p.age / 0.25 * Math.PI * 0.62) : 1;
        if (p.grow) s *= 1 + p.grow * lifeK;
        var sy = p.fs ? Math.cos(p.flip) : 1;
        var color = p.back && sy < 0 ? mix(p.color, BLACK, 0.22) : p.color;
        var x = p.x + (p.sf ? Math.sin(p.age * p.sf + p.ph) * p.sa : 0);
        if (p.sprite === "balloon") {
          ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          ctx.globalAlpha = a * 0.5;
          ctx.strokeStyle = css(mix(p.color, BLACK, 0.3));
          ctx.lineWidth = 1;
          var by = p.y + p.size * 0.46;
          ctx.beginPath(); ctx.moveTo(x, by); ctx.quadraticCurveTo(x + Math.sin(p.age * 3) * 8, by + p.size * 0.8, x, by + p.size * 1.6); ctx.stroke();
        }
        if (dark && (p.sprite === "glint" || p.sprite === "speck")) ctx.globalCompositeOperation = "lighter";
        drawSprite(ctx, getSprite(p.sprite, color, p.size, dark), x, p.y, p.rot, s, s * sy, a, dpr);
        ctx.globalCompositeOperation = "source-over";
      }
    }
    return list.length > 0;
  }

  /* ---------------------------------------------------------------- lus */
  var scenes = [];
  var running = false;
  var lastTime = 0;
  var slowFrames = 0;
  var tilt = { els: [], tx: 0, ty: 0, x: 0, y: 0, active: false };

  if (settings.scrollwind) {
    var lastScrollY = window.pageYOffset || 0;
    window.addEventListener("scroll", function () {
      var y = window.pageYOffset || 0, d = clamp(y - lastScrollY, -400, 400);
      lastScrollY = y;
      for (var i = 0; i < scenes.length; i++) scenes[i].sdy += d;
    }, { passive: true });
  }

  function wake() {
    if (running) return;
    running = true;
    lastTime = performance.now();
    window.requestAnimationFrame(loop);
  }

  function loop(now) {
    var raw = (now - lastTime) / 1000;
    lastTime = now;
    var dt = Math.min(0.05, Math.max(0.001, raw));
    var busy = false, i;
    if (motionOn()) {
      /* Trage apparaten: minder deeltjes als het beeld stottert. */
      if (raw > 0.028 && raw < 0.2) slowFrames++; else if (slowFrames > 0) slowFrames -= 0.5;
      if (slowFrames > 45) {
        slowFrames = 0;
        scenes.forEach(function (s) { s.quality = Math.max(0.35, s.quality * 0.75); });
      }
      for (i = 0; i < scenes.length; i++) {
        var s = scenes[i];
        if (s.active && s.visible) { s.frame(dt); busy = true; }
      }
      if (burst.list.length) busy = stepBurst(dt) || busy;
      if (tilt.active) busy = stepTilt() || busy;
    }
    if (busy) window.requestAnimationFrame(loop);
    else running = false;
  }

  /* ---------------------------------------------------------------- kantelen met de muis */
  function stepTilt() {
    tilt.x += (tilt.tx - tilt.x) * 0.1;
    tilt.y += (tilt.ty - tilt.y) * 0.1;
    var mag = Math.min(1, Math.sqrt(tilt.x * tilt.x + tilt.y * tilt.y));
    var angle = (mag * 7).toFixed(2) + "deg";
    var value = mag < 0.002 ? "0deg" : (-tilt.y / (mag || 1)).toFixed(3) + " " + (tilt.x / (mag || 1)).toFixed(3) + " 0 " + angle;
    for (var i = 0; i < tilt.els.length; i++) tilt.els[i].style.setProperty("--fx-rot", value);
    return Math.abs(tilt.tx - tilt.x) > 0.001 || Math.abs(tilt.ty - tilt.y) > 0.001;
  }

  function setupTilt() {
    if (!settings.kantel || !fineQuery || !fineQuery.matches) return;
    tilt.els = Array.prototype.slice.call(document.querySelectorAll("[data-fx-tilt]"));
    if (!tilt.els.length) return;
    tilt.active = true;
    document.addEventListener("pointermove", function (e) {
      if (e.pointerType && e.pointerType !== "mouse") return;
      /* Browsers sturen na een wijziging in de opmaak soms een 'nep'-beweging zonder verplaatsing. */
      if (!e.movementX && !e.movementY) return;
      tilt.tx = clamp((e.clientX / window.innerWidth - 0.5) * 2, -1, 1);
      tilt.ty = clamp((e.clientY / window.innerHeight - 0.5) * 2, -1, 1);
      if (motionOn()) wake();
    }, { passive: true });
    document.documentElement.addEventListener("mouseleave", function () { tilt.tx = 0; tilt.ty = 0; if (motionOn()) wake(); });
  }

  /* ---------------------------------------------------------------- versieringen tekenen */
  var drawObserver = null;
  function prepareDrawings() {
    var svgs = document.querySelectorAll(".a-orn__svg, [data-fx-draw]");
    svgs.forEach(function (svg) {
      if (svg.closest("[data-cover]")) return;
      var strokes = 0;
      svg.querySelectorAll("path, line, polyline, polygon, circle, ellipse, rect").forEach(function (el) {
        var cs = window.getComputedStyle(el);
        var hasStroke = cs.stroke && cs.stroke !== "none" && parseFloat(cs.strokeWidth) > 0;
        if (hasStroke && cs.strokeDasharray === "none" && el.getTotalLength) {
          var len = 0;
          try { len = el.getTotalLength(); } catch (e) { len = 0; }
          if (len > 0) {
            el.style.setProperty("--fx-len", (Math.ceil(len) + 1) + "px");
            el.classList.add("fx-stroke");
            strokes++;
            return;
          }
        }
        if (cs.fill && cs.fill !== "none") el.classList.add("fx-fill");
      });
      if (strokes) svg.classList.add("fx-drawable");
    });
    if (!("IntersectionObserver" in window)) {
      document.querySelectorAll(".fx-drawable").forEach(function (el) { el.classList.add("is-drawn"); });
      return;
    }
    drawObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.add("is-drawn"); drawObserver.unobserve(entry.target); }
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.2 });
  }
  function observeDrawings(immediateInView) {
    document.querySelectorAll(".fx-drawable:not(.is-drawn)").forEach(function (el) {
      if (immediateInView) {
        var r = el.getBoundingClientRect();
        if (r.bottom > 0 && r.top < window.innerHeight) { el.classList.add("is-drawn", "is-instant"); return; }
      }
      if (drawObserver) drawObserver.observe(el);
      else el.classList.add("is-drawn");
    });
  }

  /* ---------------------------------------------------------------- getallen optellen */
  function countUp() {
    document.querySelectorAll(".a-number, [data-fx-count]").forEach(function (el) {
      var text = el.textContent.trim();
      if (!/^\d{1,3}$/.test(text)) return;
      var target = parseInt(text, 10);
      if (target < 2) return;
      var start = null, duration = 1500 + Math.min(target, 100) * 6, delay = 250;
      el.classList.add("is-counting");
      el.textContent = "0";
      function step(now) {
        if (start === null) start = now + delay;
        var k = clamp((now - start) / duration, 0, 1);
        var eased = 1 - Math.pow(1 - k, 3);
        el.textContent = String(Math.round(target * eased));
        if (k < 1 && motionOn()) window.requestAnimationFrame(step);
        else { el.textContent = text; el.classList.remove("is-counting"); }
      }
      window.requestAnimationFrame(step);
    });
  }

  /* ---------------------------------------------------------------- onderdelen na elkaar */
  function staggerChildren() {
    var lists = document.querySelectorAll(["a-program__list", "a-practical__list", "a-gallery__grid", "a-swatches", "cd", "inv-actions"]
      .map(function (name) { return "[data-reveal] ." + name; }).concat("[data-fx-stagger]").join(", "));
    lists.forEach(function (list) {
      Array.prototype.forEach.call(list.children, function (child, i) {
        child.style.setProperty("--fx-i", String(Math.min(i, 12)));
      });
    });
  }

  /* ---------------------------------------------------------------- vlakken */
  function setupScenes() {
    if (!AMBIENT[settings.sfeer]) return;
    document.querySelectorAll("[data-fx-slot]").forEach(function (slot) {
      var scene = new Scene(slot, settings.sfeer);
      scene.kind = slot.getAttribute("data-fx-slot");
      scenes.push(scene);
    });
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          scenes.forEach(function (s) {
            if (s.slot === entry.target) { s.visible = entry.isIntersecting; if (s.visible && s.active) wake(); }
          });
        });
      }, { rootMargin: "80px 0px" });
      scenes.forEach(function (s) { io.observe(s.slot); });
    }
  }

  function applyScenes() {
    var coverShown = html.classList.contains("has-cover") || html.classList.contains("is-opening");
    scenes.forEach(function (s) {
      var on = motionOn();
      if (s.kind === "cover") on = on && coverShown;
      else on = on && state.pageOn;
      if (!on && s.active) { s.stage.clear(); }
      s.setActive(on);
    });
  }

  /* ---------------------------------------------------------------- knop 'Beweging' */
  var toggle = document.querySelector("[data-fx-toggle]");
  function applyMotion() {
    var on = motionOn();
    html.classList.toggle("fx-motion", on);
    html.classList.toggle("fx-paused", state.paused && !state.reduced);
    if (toggle) {
      toggle.hidden = state.reduced;
      toggle.setAttribute("aria-pressed", state.paused ? "true" : "false");
    }
    if (!on) {
      burst.list.length = 0;
      if (burst.stage) burst.stage.clear();
      document.querySelectorAll(".fx-drawable:not(.is-drawn)").forEach(function (el) { el.classList.add("is-drawn", "is-instant"); });
    }
    applyScenes();
  }
  if (toggle) {
    toggle.addEventListener("click", function () {
      state.paused = !state.paused;
      writePref(state.paused ? "stil" : "");
      applyMotion();
    });
  }
  if (reduceQuery) {
    var onReduce = function (e) { state.reduced = e.matches; applyMotion(); };
    if (reduceQuery.addEventListener) reduceQuery.addEventListener("change", onReduce);
    else if (reduceQuery.addListener) reduceQuery.addListener(onReduce);
  }

  /* ---------------------------------------------------------------- openen, aanmelden, tikken */
  function centerOf(el) {
    if (!el) return { x: window.innerWidth / 2, y: window.innerHeight * 0.45 };
    var r = el.getBoundingClientRect();
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }

  function startPage(withIntro) {
    if (state.pageOn) return;
    state.pageOn = true;
    staggerChildren();
    if (withIntro && motionOn()) {
      html.classList.add("fx-start");
      countUp();
      window.setTimeout(function () { html.classList.add("fx-done"); }, 4200);
    } else {
      html.classList.add("fx-done");
    }
    observeDrawings(!withIntro);
    applyScenes();
  }

  document.addEventListener("invite:opening", function (event) {
    html.classList.add("fx-opening");
    if (!motionOn()) return;
    /* Opening als film: de knal en de kop wachten tot de film klaar is (invite:reveal). */
    if (event.detail && event.detail.film) return;
    var cover = document.querySelector("[data-cover]");
    var origin = centerOf(cover && (cover.querySelector("[data-fx-origin]") || cover.querySelector("[data-open]")));
    var delay = parseInt((cover && cover.getAttribute("data-fx-delay")) || "0", 10);
    var duration = parseInt((cover && cover.getAttribute("data-duration")) || "2200", 10);
    window.setTimeout(function () { fire(settings.knal, origin.x, origin.y, cover, 1); }, delay);
    /* De kop begint al terwijl het openingsscherm vervaagt: geen leeg moment ertussen. */
    var introAt = parseInt((cover && cover.getAttribute("data-fx-intro")) || String(duration - 650), 10);
    window.setTimeout(function () { if (html.classList.contains("is-opening")) startPage(true); }, Math.max(0, introAt));
  });

  document.addEventListener("invite:reveal", function () {
    if (!motionOn()) return;
    var cover = document.querySelector("[data-cover]");
    var origin = centerOf(document.querySelector("[data-fx-reveal-origin]") || (cover && cover.querySelector("[data-fx-origin]")));
    fire(settings.knal, origin.x, origin.y, cover, 1);
    startPage(true);
  });

  document.addEventListener("invite:opened", function (event) {
    var instant = !!(event.detail && event.detail.instant);
    startPage(!instant);
    applyScenes();
  });

  document.addEventListener("invite:rsvp", function (event) {
    var detail = event.detail || {};
    if (!detail.attending || !motionOn()) return;
    var target = detail.target && detail.target.isConnected ? detail.target : document.getElementById("aanmelden");
    var r = target ? target.getBoundingClientRect() : null;
    var x = r ? r.left + r.width / 2 : window.innerWidth / 2;
    var y = r ? clamp(r.top + Math.min(r.height / 2, 140), 80, window.innerHeight - 80) : window.innerHeight / 2;
    fire(settings.viering !== "geen" ? settings.viering : settings.knal, x, y, body, 1);
  });

  if (settings.tik) {
    document.addEventListener("click", function (event) {
      if (!motionOn() || !event.detail || event.clientX === undefined) return;
      if (event.target.closest("input, textarea, select, label, option, [data-open], [data-fx-toggle]")) return;
      if (html.classList.contains("is-opening")) return;
      var from = event.target.closest("[data-cover]") || body;
      fire(settings.knal !== "geen" ? settings.knal : "sterren", event.clientX, event.clientY, from, 0.16);
    });
  }

  var resizeTimer = null;
  window.addEventListener("resize", function () {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(function () {
      for (var i = 0; i < stages.length; i++) stages[i].dirty = true;
      wake();
    }, 120);
  });

  /* ---------------------------------------------------------------- start */
  setupScenes();
  prepareDrawings();
  setupTilt();
  applyMotion();
  var coverVisible = html.classList.contains("has-cover");
  if (!coverVisible) startPage(false);
  else applyScenes();
})();
