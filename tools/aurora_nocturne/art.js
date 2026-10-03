/* Aurora Nocturne: alle beelden worden met code op een canvas getekend (geen foto's, geen stockbeelden, geen AI-beelden).
   Wordt geladen door render.cjs in Chromium. Vaste toevalsgetallen (rng) per onderdeel: een nieuwe run geeft hetzelfde beeld.

   Opbouw van de scène (achter naar voor, zie designs/aurora-nocturne/v1/invitation.html):
     lucht · aurora (2 linten) · ver (heuvels, bos, meer) · mist · paviljoen (donker) · lichtkaarten (entree, zij, kroon, lampjes, kaarsen) · voorgrond
   De lichtkaarten zijn volledig doorzichtig behalve het licht zelf: het ontwerp zet er alleen de opacity van aan of uit,
   dus de lampen gaan in een cascade aan zonder tientallen losse elementen. */
"use strict";

var TAU = Math.PI * 2;

function rng(seed) {
  var s = seed >>> 0;
  return function () {
    s = (s + 0x6D2B79F5) >>> 0;
    var t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function cv(w, h) { var c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
function lin(g, x0, y0, x1, y1, stops) { var gr = g.createLinearGradient(x0, y0, x1, y1); stops.forEach(function (s) { gr.addColorStop(s[0], s[1]); }); return gr; }
function rad(g, x0, y0, r0, x1, y1, r1, stops) { var gr = g.createRadialGradient(x0, y0, r0, x1, y1, r1); stops.forEach(function (s) { gr.addColorStop(s[0], s[1]); }); return gr; }
function lerp(a, b, t) { return a + (b - a) * t; }
function smooth(t) { return t * t * (3 - 2 * t); }

/* Gladde ruis in één dimensie (waarden tussen 0 en 1), voor bergruggen, aurora en mist. */
function noise1(seed) {
  var r = rng(seed), v = [];
  for (var i = 0; i < 256; i++) v.push(r());
  return function (x) {
    var i = Math.floor(x), f = x - i;
    var a = v[((i % 256) + 256) % 256], b = v[(((i + 1) % 256) + 256) % 256];
    return lerp(a, b, smooth(f));
  };
}
function fbm(n, x, oct) {
  var amp = 0.5, sum = 0, tot = 0, f = 1;
  for (var o = 0; o < (oct || 4); o++) { sum += n(x * f) * amp; tot += amp; amp *= 0.5; f *= 2.03; }
  return sum / tot;
}

/* Fijne korrel tegen banden in verlopen (alleen op dekkende vlakken). */
function dither(c, amount, seed) {
  var g = c.getContext("2d"), d = g.getImageData(0, 0, c.width, c.height), a = d.data, r = rng(seed);
  for (var i = 0; i < a.length; i += 4) {
    var n = (r() - 0.5) * amount;
    a[i] += n; a[i + 1] += n; a[i + 2] += n;
  }
  g.putImageData(d, 0, 0);
}

/* =================================================================== kleuren */
var PAL = {
  nacht0: "#01030a", nacht1: "#040918", nacht2: "#081633", nacht3: "#0d2a52", glimp: "#1b4a6b",
  frame: "#04070f", frame2: "#0a1222",
  ivoor: [240, 234, 218], champagne: [236, 214, 160], warm: [255, 238, 200], amber: [226, 172, 98],
  groen: [110, 232, 190], ijs: [150, 206, 255], teal: [70, 200, 200]
};
function rgba(c, a) { return "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a + ")"; }

/* =================================================================== thema's
   Vier kleurwerelden met dezelfde tekening: nacht (het origineel) en drie lichte ochtenden: parel, roze en salie.
   Alles wat een kleur heeft staat hier; de functies hieronder tekenen met T. Kies met setTheme(naam) (render.cjs doet dat per map). */
var THEMES = {
  nacht: {
    light: false, frame: "#04070f", frame2: "#0a1222",
    sky: [[0, "#000106"], [0.34, "#01040c"], [0.58, "#040b1b"], [0.74, "#0b2538"], [0.8, "#07182a"], [1, "#000106"]],
    glow: [[0, "rgba(60,140,150,0.20)"], [0.4, "rgba(30,90,120,0.09)"], [1, "rgba(0,0,0,0)"]],
    star: "225,236,255", cirrus: null,
    aurA: [[150, 206, 255], [70, 200, 200], [110, 232, 190]], aurB: [[150, 206, 255], [150, 206, 255], [70, 200, 200]], aurK: [1, 1], aurComp: "lighter",
    ridge1: ["#0a2236", "#071a2c"], ridge2: ["#06121f", "#050e1b"], vmist: "100,150,175", vmistA: 0.11, forest: "#02070d",
    lake: [[0, "#071b2b"], [0.16, "#040f1c"], [0.55, "#01060d"], [1, "#000106"]], streak: "120,180,215", streakK: 1,
    mist: "96,130,162", mistK: 1,
    glass: ["rgba(28,62,100,0.96)", "rgba(11,26,46,0.97)", "rgba(5,11,20,0.98)"],
    rim: "160,200,235", rim2: "170,205,240", rimK: 1, hallGlow: ["rgba(80,200,190,0.16)", "rgba(80,160,220,0.05)"], streakGlass: "200,230,255",
    chandIn: ["rgba(120,150,190,0.20)", "rgba(160,190,225,0.30)"], door: "rgba(2,5,10,0.55)", lampGlass: "rgba(60,90,120,0.55)",
    slab: ["#0d1829", "#0a1422", "#050a14"], steps: ["#08111f", "#0b1627"],
    urn: "#0a1424", urnRim: "#0e1a2d", urnHl: "170,205,240", bloomShade: "8,14,26", leaf: "rgba(20,44,40,0.9)", flowerIn: "rgba(60,90,80,0.2)",
    shade: "8,14,26", grass: "2,6,12", grassRim: "150,190,225", plane: "#06142a"
  },
  /* Parelmoer: parelwit, ijsblauw en een zweem champagne bij de horizon. */
  parel: {
    light: true, frame: "#3c4553", frame2: "#566071",
    sky: [[0, "#c6d6e8"], [0.3, "#dbe5ef"], [0.55, "#eef0f1"], [0.7, "#f8eedd"], [0.76, "#f7e4c6"], [0.8, "#e8dcc9"], [1, "#c9ced2"]],
    glow: [[0, "rgba(255,226,170,0.78)"], [0.4, "rgba(255,236,206,0.34)"], [1, "rgba(255,246,230,0)"]],
    star: null, cirrus: "255,255,255", cirrus2: "246,214,160",
    aurA: [[200, 224, 244], [176, 224, 208], [226, 214, 170]], aurB: [[214, 206, 240], [214, 206, 240], [240, 214, 170]], aurK: [1.5, 1.7], aurComp: "source-over",
    ridge1: ["#cfd9e4", "#c0ccda"], ridge2: ["#b3c2d2", "#a6b7c9"], vmist: "255,248,238", vmistA: 0.28, forest: "#7189a0",
    lake: [[0, "#e9e3d8"], [0.16, "#cfd8e0"], [0.55, "#aebdca"], [1, "#98aab9"]], streak: "255,255,255", streakK: 3.5,
    mist: "255,252,246", mistK: 1.0,
    glass: ["rgba(200,216,232,0.96)", "rgba(142,164,190,0.97)", "rgba(92,112,138,0.98)"],
    rim: "255,255,255", rim2: "255,255,255", rimK: 2, hallGlow: ["rgba(255,255,255,0.34)", "rgba(210,226,244,0.12)"], streakGlass: "255,255,255",
    chandIn: ["rgba(70,84,108,0.30)", "rgba(255,255,255,0.45)"], door: "rgba(34,44,60,0.55)", lampGlass: "rgba(230,238,246,0.6)",
    slab: ["#e3dfd8", "#d3d0ca", "#b4b4b2"], steps: ["#cfccc5", "#dcd9d2"],
    urn: "#8f97a6", urnRim: "#a6adba", urnHl: "255,255,255", bloomShade: "70,80,104", leaf: "rgba(78,110,96,0.9)", flowerIn: "rgba(90,120,110,0.25)",
    shade: "34,44,64", grass: "68,86,92", grassRim: "255,255,255", plane: "#c4d2e2"
  },
  /* Rozenmorgen: een roze dageraad met mauve heuvels en een pruimkleurig frame. */
  roze: {
    light: true, frame: "#4a3748", frame2: "#66505f",
    sky: [[0, "#e3c8d6"], [0.3, "#efd6dc"], [0.55, "#f7e4e0"], [0.7, "#fbe8d8"], [0.76, "#fadcc0"], [0.8, "#ecd3c4"], [1, "#d3bfc6"]],
    glow: [[0, "rgba(255,214,176,0.80)"], [0.4, "rgba(255,226,200,0.34)"], [1, "rgba(255,240,228,0)"]],
    star: null, cirrus: "255,250,246", cirrus2: "248,196,176",
    aurA: [[240, 204, 220], [248, 190, 176], [244, 214, 168]], aurB: [[222, 196, 232], [222, 196, 232], [248, 200, 180]], aurK: [1.5, 1.7], aurComp: "source-over",
    ridge1: ["#e3cbd6", "#d6bbc9"], ridge2: ["#c9a9ba", "#bb9aae"], vmist: "255,244,238", vmistA: 0.28, forest: "#8d6f84",
    lake: [[0, "#f0ddd6"], [0.16, "#dcc3cb"], [0.55, "#bf9fb0"], [1, "#a98a9d"]], streak: "255,246,240", streakK: 3.5,
    mist: "255,246,242", mistK: 1.0,
    glass: ["rgba(228,200,214,0.96)", "rgba(172,138,160,0.97)", "rgba(118,88,112,0.98)"],
    rim: "255,255,255", rim2: "255,250,246", rimK: 2, hallGlow: ["rgba(255,248,244,0.34)", "rgba(246,214,226,0.14)"], streakGlass: "255,250,248",
    chandIn: ["rgba(96,66,90,0.30)", "rgba(255,252,250,0.45)"], door: "rgba(56,36,56,0.55)", lampGlass: "rgba(246,226,232,0.6)",
    slab: ["#eadfdb", "#dccfcc", "#bfb1b3"], steps: ["#d8cac8", "#e4d8d4"],
    urn: "#9c8494", urnRim: "#b09aa8", urnHl: "255,250,248", bloomShade: "96,64,88", leaf: "rgba(96,112,92,0.9)", flowerIn: "rgba(120,100,110,0.25)",
    shade: "54,34,52", grass: "92,66,82", grassRim: "255,248,244", plane: "#dcc4d0"
  },
  /* Saliemist: zacht groen en zeeglas, met een bosgroen frame. */
  salie: {
    light: true, frame: "#2f4741", frame2: "#4b6159",
    sky: [[0, "#c9dfdd"], [0.3, "#dbe9e5"], [0.55, "#ecf1ea"], [0.7, "#f6f2e2"], [0.76, "#f5ead0"], [0.8, "#e4e2cf"], [1, "#c3cfc9"]],
    glow: [[0, "rgba(255,230,176,0.76)"], [0.4, "rgba(255,240,208,0.32)"], [1, "rgba(255,248,232,0)"]],
    star: null, cirrus: "255,255,252", cirrus2: "244,222,168",
    aurA: [[184, 228, 214], [160, 220, 200], [230, 226, 168]], aurB: [[176, 214, 236], [176, 214, 236], [160, 220, 200]], aurK: [1.5, 1.7], aurComp: "source-over",
    ridge1: ["#cddcd5", "#bdd0c7"], ridge2: ["#a9c1b6", "#9bb5a9"], vmist: "250,252,244", vmistA: 0.28, forest: "#587a6d",
    lake: [[0, "#e4e8dc"], [0.16, "#cbd9d3"], [0.55, "#a2bbb3"], [1, "#8ba8a0"]], streak: "252,255,250", streakK: 3.5,
    mist: "250,253,247", mistK: 1.0,
    glass: ["rgba(198,224,222,0.96)", "rgba(132,170,168,0.97)", "rgba(84,120,118,0.98)"],
    rim: "255,255,255", rim2: "255,255,250", rimK: 2, hallGlow: ["rgba(255,255,252,0.34)", "rgba(206,234,226,0.14)"], streakGlass: "255,255,252",
    chandIn: ["rgba(52,84,76,0.30)", "rgba(255,255,252,0.45)"], door: "rgba(26,48,44,0.55)", lampGlass: "rgba(228,244,238,0.6)",
    slab: ["#e1e2d8", "#d1d3c8", "#b0b6ae"], steps: ["#cdd0c4", "#dadcd1"],
    urn: "#86a095", urnRim: "#9db4aa", urnHl: "255,255,250", bloomShade: "52,84,76", leaf: "rgba(70,112,88,0.9)", flowerIn: "rgba(90,130,110,0.25)",
    shade: "28,48,44", grass: "56,84,72", grassRim: "255,255,250", plane: "#c2d6d2"
  }
};
var T = THEMES.nacht; T.name = "nacht";
function setTheme(name) {
  if (!THEMES[name]) throw new Error("onbekend thema: " + name);
  T = THEMES[name]; T.name = name; PAL.frame = T.frame; PAL.frame2 = T.frame2;
}
function rimA(a, k) { return "rgba(" + (k || T.rim) + "," + Math.min(1, a * T.rimK) + ")"; }

/* =================================================================== lucht (dekkend, 2400 x 1350) */
function drawLucht(W, H) {
  var c = cv(W, H), g = c.getContext("2d");
  g.fillStyle = lin(g, 0, 0, 0, H, T.sky);
  g.fillRect(0, 0, W, H);
  // Zachte gloed aan de horizon, midden achter het paviljoen.
  g.fillStyle = rad(g, W * 0.5, H * 0.76, 0, W * 0.5, H * 0.76, W * 0.55, T.glow);
  g.fillRect(0, 0, W, H);
  if (T.light) { cirrus(g, W, H); dither(c, 3.2, 5); return c; }
  // Sterren: weinig en klein, geen sterren vlak boven de horizon.
  var r = rng(11);
  for (var i = 0; i < 520; i++) {
    var x = r() * W, y = Math.pow(r(), 1.5) * H * 0.7;
    var big = r() < 0.012;
    var rad0 = big ? 1.0 + r() * 0.5 : 0.4 + r() * 0.7;
    var a = (big ? 0.7 : 0.18 + r() * 0.45) * (1 - y / (H * 0.78));
    if (big) {
      g.fillStyle = rad(g, x, y, 0, x, y, 5, [[0, "rgba(220,235,255," + (a * 0.5) + ")"], [1, "rgba(220,235,255,0)"]]);
      g.fillRect(x - 5, y - 5, 10, 10);
    }
    g.fillStyle = "rgba(225,236,255," + a + ")";
    g.beginPath(); g.arc(x, y, rad0, 0, TAU); g.fill();
  }
  dither(c, 3.2, 5);
  return c;
}

/* Lichte thema's: hoge, ijle sluierwolken in plaats van sterren (zacht, langgerekt, vlak boven de horizon bijna weg). */
function cirrus(g, W, H) {
  var r = rng(11);
  for (var i = 0; i < 52; i++) {
    var x = r() * W, y = Math.pow(r(), 1.25) * H * 0.62, w = 160 + r() * 560, h = 5 + r() * 15;
    var a = (0.12 + r() * 0.26) * (1 - y / (H * 0.74)), tint = r() < 0.28 ? T.cirrus2 : T.cirrus;
    g.save(); g.translate(x, y); g.rotate((r() - 0.5) * 0.07); g.scale(w, h);
    g.fillStyle = rad(g, 0, 0, 0, 0, 0, 1, [[0, "rgba(" + tint + "," + a + ")"], [0.55, "rgba(" + tint + "," + (a * 0.4) + ")"], [1, "rgba(" + tint + ",0)"]]);
    g.fillRect(-1, -1, 2, 2);
    g.restore();
  }
}

/* =================================================================== aurora (doorzichtig, laag detail: wordt groter getoond) */
function drawAurora(W, H, kind) {
  var c = cv(W, H), g = c.getContext("2d");
  var n = noise1(kind === "a" ? 31 : 77), n2 = noise1(kind === "a" ? 5 : 9);
  g.globalCompositeOperation = T.aurComp;
  var base = kind === "a" ? H * 0.5 : H * 0.42;
  var step = 2;
  for (var x = 0; x < W; x += step) {
    var u = x / W;
    var sway = Math.sin(u * TAU * (kind === "a" ? 0.9 : 1.4) + (kind === "a" ? 0.4 : 2.2)) * H * 0.07 + (fbm(n, u * 3.2, 3) - 0.5) * H * 0.2;
    var yb = base + sway;
    var hh = H * (kind === "a" ? 0.34 : 0.26) * (0.35 + 0.9 * fbm(n2, u * 5.5 + 3, 3));
    var edge = Math.sin(u * Math.PI);
    var ray = 0.55 + 0.45 * n2(u * 90 + 7);                  // fijne straalstructuur
    var a = (kind === "a" ? 0.21 * T.aurK[0] : 0.13 * T.aurK[1]) * edge * ray;
    var gr = g.createLinearGradient(0, yb - hh, 0, yb + H * 0.035);
    var AC = kind === "a" ? T.aurA : T.aurB;
    if (kind === "a") {
      gr.addColorStop(0, rgba(AC[0], 0));
      gr.addColorStop(0.45, rgba(AC[1], a * 0.55));
      gr.addColorStop(0.85, rgba(AC[2], a));
      gr.addColorStop(1, rgba(AC[2], 0));
    } else {
      gr.addColorStop(0, rgba(AC[0], 0));
      gr.addColorStop(0.55, rgba(AC[1], a * 0.7));
      gr.addColorStop(0.9, rgba(AC[2], a));
      gr.addColorStop(1, rgba(AC[2], 0));
    }
    g.fillStyle = gr;
    g.fillRect(x, yb - hh, step + 0.6, hh + H * 0.035);
  }
  // Zacht maken: een aurora heeft geen harde randen.
  var b = cv(W, H), bg = b.getContext("2d");
  bg.filter = "blur(" + Math.round(W / 220) + "px)";
  bg.drawImage(c, 0, 0);
  return b;
}

/* =================================================================== ver: heuvels, bos en meer (doorzichtig, 2400 x 1350) */
function ridge(g, W, y0, amp, seed, color, freq, spikes) {
  var n = noise1(seed), r = rng(seed + 3);
  g.beginPath(); g.moveTo(0, g.canvas.height);
  for (var x = 0; x <= W; x += 3) {
    var y = y0 - (fbm(n, x / W * freq, 4) - 0.35) * amp;
    if (spikes) {
      // Dennen: kleine spitse pieken die op de rug staan.
      var k = Math.floor(x / spikes), f = (x % spikes) / spikes;
      var h = (0.4 + 0.6 * rng(k * 9 + seed)()) * amp * 0.34;
      y -= Math.max(0, 1 - Math.abs(f - 0.5) * 2.1) * h;
    }
    g.lineTo(x, y);
  }
  g.lineTo(W, g.canvas.height); g.closePath();
  g.fillStyle = color; g.fill();
}
/* Een dichte, onregelmatige bosrand: honderden kleine bomen, geen regelmatige zaagtand. */
function forest(g, W, y0, seed, color, hMax) {
  var r = rng(seed), n = noise1(seed + 1);
  g.fillStyle = color;
  g.fillRect(0, y0 - 2, W, g.canvas.height - y0 + 2);
  for (var x = -20; x < W + 20; x += 3 + r() * 5) {
    var cluster = 0.35 + 0.65 * fbm(n, x / W * 9, 3);
    var h = hMax * (0.25 + 0.75 * r()) * cluster, w = h * (0.28 + 0.2 * r());
    g.beginPath();
    g.moveTo(x - w, y0 + 2);
    g.quadraticCurveTo(x - w * 0.35, y0 - h * 0.55, x + (r() - 0.5) * 2, y0 - h);
    g.quadraticCurveTo(x + w * 0.35, y0 - h * 0.55, x + w, y0 + 2);
    g.closePath(); g.fill();
  }
}
function drawVer(W, H) {
  var c = cv(W, H), g = c.getContext("2d");
  var hor = H * 0.742;                       // waterlijn / voet van de verre oever
  // Verre rug, met een koele rand van de horizonlucht.
  ridge(g, W, hor - H * 0.045, H * 0.07, 21, lin(g, 0, hor - H * 0.11, 0, hor, [[0, T.ridge1[0]], [1, T.ridge1[1]]]), 3.2, 0);
  ridge(g, W, hor - H * 0.02, H * 0.06, 33, lin(g, 0, hor - H * 0.08, 0, hor, [[0, T.ridge2[0]], [1, T.ridge2[1]]]), 4.1, 0);
  // Mist tussen de ruggen.
  g.fillStyle = lin(g, 0, hor - H * 0.07, 0, hor + H * 0.01, [[0, "rgba(" + T.vmist + ",0)"], [1, "rgba(" + T.vmist + "," + T.vmistA + ")"]]);
  g.fillRect(0, hor - H * 0.07, W, H * 0.08);
  // Bosrand: donkere dennen.
  forest(g, W, hor + H * 0.004, 47, T.forest, H * 0.036);
  // Het meer: dekkend donker, met de weerspiegeling van de horizon.
  var lake = lin(g, 0, hor, 0, H, T.lake);
  g.fillStyle = lake; g.fillRect(0, hor, W, H - hor);
  // Spiegeling van de oever: omgekeerd, zacht, met rimpels.
  var m = cv(W, Math.round(H * 0.2)), mg = m.getContext("2d");
  mg.save(); mg.translate(0, m.height); mg.scale(1, -1);
  mg.drawImage(c, 0, hor - m.height, W, m.height, 0, 0, W, m.height);
  mg.restore();
  mg.globalCompositeOperation = "destination-in";
  mg.fillStyle = lin(mg, 0, 0, 0, m.height, [[0, "rgba(0,0,0,0.55)"], [1, "rgba(0,0,0,0)"]]);
  mg.fillRect(0, 0, W, m.height);
  var rip = cv(W, m.height), rg = rip.getContext("2d"), rr = rng(61);
  for (var y = 0; y < m.height; y += 2) {
    var dx = Math.sin(y * 0.19 + rr() * 0.8) * (2 + y * 0.03);
    rg.drawImage(m, 0, y, W, 2, dx, y, W, 2);
  }
  g.globalAlpha = 0.9; g.drawImage(rip, 0, hor + 2); g.globalAlpha = 1;
  // Lange, zachte lichtstrepen op het water (koele hemelreflectie).
  var rs = rng(77);
  for (var i = 0; i < 70; i++) {
    var xx = rs() * W, yy = hor + 8 + Math.pow(rs(), 1.6) * (H - hor) * 0.5, ww = 80 + rs() * 380;
    g.fillStyle = lin(g, xx, 0, xx + ww, 0, [[0, "rgba(" + T.streak + ",0)"], [0.5, "rgba(" + T.streak + "," + ((0.025 + rs() * 0.03) * T.streakK) + ")"], [1, "rgba(" + T.streak + ",0)"]]);
    g.fillRect(xx, yy, ww, 1.5);
  }
  return c;
}

/* =================================================================== mist (doorzichtig, breed) */
function drawMist(W, H) {
  var c = cv(W, H), g = c.getContext("2d"), r = rng(91);
  for (var i = 0; i < 260; i++) {
    var x = r() * W, y = H * (0.3 + 0.45 * r()), rr = 110 + r() * 240;
    var a = (0.008 + r() * 0.016) * T.mistK;
    [-W, 0, W].forEach(function (o) {
      g.fillStyle = rad(g, x + o, y, 0, x + o, y, rr, [[0, "rgba(" + T.mist + "," + a + ")"], [1, "rgba(" + T.mist + ",0)"]]);
      g.fillRect(x + o - rr, y - rr, rr * 2, rr * 2);
    });
  }
  g.globalCompositeOperation = "destination-in";
  g.fillStyle = lin(g, 0, 0, 0, H, [[0, "rgba(0,0,0,0)"], [0.28, "rgba(0,0,0,1)"], [0.7, "rgba(0,0,0,1)"], [1, "rgba(0,0,0,0)"]]);
  g.fillRect(0, 0, W, H);
  g.fillStyle = lin(g, 0, 0, W, 0, [[0, "rgba(0,0,0,0)"], [0.14, "rgba(0,0,0,1)"], [0.86, "rgba(0,0,0,1)"], [1, "rgba(0,0,0,0)"]]);
  g.fillRect(0, 0, W, H);
  return c;
}

/* =================================================================== het paviljoen (vlak van 1080 x 1100) */
var PV = {
  W: 1080, H: 1100, cx: 540, base: 800,
  hw: 420, T: 15                    // breedte van de hal, dikte van het frame
};
PV.hs = Math.round(PV.hw * 0.85);   // muurhoogte tot de aanzet van de boog
PV.R = PV.hw / 2;
PV.spring = PV.base - PV.hs;
PV.top = PV.spring - PV.R;          // top van de boog
PV.x0 = PV.cx - PV.hw / 2; PV.x1 = PV.cx + PV.hw / 2;
PV.ww = Math.round(PV.hw * 0.55);   // breedte van een vleugel
PV.wingTop = PV.base - Math.round((PV.hs + PV.R) * 0.56);
PV.slabY = PV.base + 46;            // onderrand van het terras

/* Het glasvlak van de hal: een boog met een rechthoek eronder. */
function hallPath(g, inset) {
  var T = inset || 0;
  g.beginPath();
  g.moveTo(PV.x0 + T, PV.base - T);
  g.lineTo(PV.x0 + T, PV.spring);
  g.arc(PV.cx, PV.spring, PV.R - T, Math.PI, 0, false);
  g.lineTo(PV.x1 - T, PV.base - T);
  g.closePath();
}
/* Rijen en kolommen van de hal. Zes kolommen, een waaier in de boog. */
var HALL = { cols: 6 };
function hallBars(g, color, wMain, wFine) {
  var inner = PV.hw - PV.T * 2, cw = inner / HALL.cols;
  g.save(); hallPath(g, PV.T); g.clip();
  g.strokeStyle = color; g.lineCap = "butt";
  // verticale roedes
  g.lineWidth = wMain;
  for (var i = 1; i < HALL.cols; i++) { var x = PV.x0 + PV.T + i * cw; g.beginPath(); g.moveTo(x, PV.base); g.lineTo(x, PV.spring); g.stroke(); }
  // dwarsroedes
  var rows = [PV.base - 150, PV.base - 300, PV.spring];
  rows.forEach(function (y) { g.lineWidth = wFine * 1.4; g.beginPath(); g.moveTo(PV.x0, y); g.lineTo(PV.x1, y); g.stroke(); });
  // de waaier in de boog
  g.lineWidth = wFine * 1.1;
  for (var k = 1; k < 6; k++) {
    var a = Math.PI + k * (Math.PI / 6);
    if (k === 3) continue;
    g.beginPath(); g.moveTo(PV.cx, PV.spring); g.lineTo(PV.cx + Math.cos(a) * PV.R, PV.spring + Math.sin(a) * PV.R); g.stroke();
  }
  g.lineWidth = wFine * 1.2;
  [0.34, 0.66].forEach(function (f) { g.beginPath(); g.arc(PV.cx, PV.spring, PV.R * f, Math.PI, 0); g.stroke(); });
  g.restore();
}
/* Een vleugel: een glazen doos met een plat dak. Geeft de glasvlakken terug (voor de lichtkaarten). */
function wingRect(side) {
  var x0 = side < 0 ? PV.x0 - PV.ww : PV.x1, x1 = x0 + PV.ww;
  return { x0: x0, x1: x1, top: PV.wingTop, base: PV.base };
}
function wingGlass(side) {
  var w = wingRect(side), T = 13, panes = [];
  var cols = 3, rows = 2;
  var iw = (w.x1 - w.x0 - T * 2 - 14), ih = (w.base - w.top - T * 2 - 26);
  var px = w.x0 + T + (side < 0 ? 0 : 14), py = w.top + T + 22;
  var cw = iw / cols, ch = ih / rows;
  for (var cI = 0; cI < cols; cI++) for (var rI = 0; rI < rows; rI++) {
    panes.push({ x: px + cI * cw + 3, y: py + rI * ch + 3, w: cw - 6, h: ch - 6, c: cI, r: rI });
  }
  return panes;
}

function glassFill(g, x, y, w, h, tint) {
  g.fillStyle = lin(g, 0, y, 0, y + h, [[0, T.glass[0]], [0.5, T.glass[1]], [1, T.glass[2]]]);
  g.fillRect(x, y, w, h);
}

function drawPaviljoen(withReflection) {
  var c = cv(PV.W, PV.H), g = c.getContext("2d");
  var cx = PV.cx, base = PV.base;

  // ---- achter de hal: lantaarn (koepel) met torenspits
  var drumW = PV.hw * 0.2, drumH = PV.hw * 0.15, dTop = PV.top - drumH + 4;
  g.fillStyle = PAL.frame;
  g.fillRect(cx - drumW / 2 - 4, dTop, drumW + 8, drumH + 6);
  g.beginPath(); g.moveTo(cx - drumW / 2 - 8, dTop + 2); g.quadraticCurveTo(cx, dTop - drumW * 0.62, cx + drumW / 2 + 8, dTop + 2); g.closePath(); g.fill();
  g.fillRect(cx - 1.4, dTop - drumW * 0.62 - PV.hw * 0.14, 2.8, PV.hw * 0.15);        // spits
  g.beginPath(); g.arc(cx, dTop - drumW * 0.62 - PV.hw * 0.14, 3.6, 0, TAU); g.fill();
  // glas van de lantaarn
  g.save(); g.beginPath(); g.rect(cx - drumW / 2, dTop + 6, drumW, drumH - 4); g.clip();
  glassFill(g, cx - drumW / 2, dTop + 6, drumW, drumH);
  g.restore();
  g.strokeStyle = PAL.frame; g.lineWidth = 3;
  for (var i = 1; i < 4; i++) { var xx = cx - drumW / 2 + i * drumW / 4; g.beginPath(); g.moveTo(xx, dTop + 6); g.lineTo(xx, dTop + drumH); g.stroke(); }

  // ---- vleugels
  [-1, 1].forEach(function (side) {
    var w = wingRect(side), T = 13;
    g.fillStyle = PAL.frame;
    g.fillRect(w.x0, w.top, w.x1 - w.x0, w.base - w.top);
    // kroonlijst en dakrand
    g.fillStyle = PAL.frame2; g.fillRect(w.x0 - 6, w.top - 8, w.x1 - w.x0 + 12, 12);
    g.fillStyle = rimA(0.24); g.fillRect(w.x0 - 6, w.top - 8, w.x1 - w.x0 + 12, 1.3);
    // glasvakken
    wingGlass(side).forEach(function (p) {
      glassFill(g, p.x, p.y, p.w, p.h);
    });
  });

  // ---- de hal: frame, glas, roeden
  hallPath(g, 0); g.fillStyle = PAL.frame; g.fill();
  g.save(); hallPath(g, PV.T); g.clip();
  glassFill(g, PV.x0, PV.top, PV.hw, PV.hw * 1.4);
  // hemelreflectie: een koele schuine gloed in de bovenhelft en twee lange glansstroken
  g.fillStyle = lin(g, PV.x0, PV.top, PV.x1, PV.spring + 100, [[0, T.hallGlow[0]], [0.5, T.hallGlow[1]], [1, "rgba(0,0,0,0)"]]);
  g.fillRect(PV.x0, PV.top, PV.hw, PV.hw);
  [[0.18, 70, 0.05], [0.58, 34, 0.04]].forEach(function (s) {
    g.save(); g.translate(PV.x0 + PV.hw * s[0], PV.top); g.rotate(0.26);
    g.fillStyle = lin(g, 0, 0, s[1], 0, [[0, "rgba(" + T.streakGlass + ",0)"], [0.5, "rgba(" + T.streakGlass + "," + (s[2] * T.rimK) + ")"], [1, "rgba(" + T.streakGlass + ",0)"]]);
    g.fillRect(0, -40, s[1], PV.hw * 1.6);
    g.restore();
  });
  // een heel zwakke binnenwereld: kroonluchter en bloemstukken (alleen te zien als silhouet)
  chandelier(g, cx, PV.spring - PV.R * 0.42, 0.9, T.chandIn[0], T.chandIn[1]);
  flowersInside(g, 0.14);
  g.restore();
  hallBars(g, PAL.frame, 6, 3.6);
  // lichte rand (maanlicht) op de buitenkant van de boog
  g.save(); hallPath(g, 0); g.clip();
  g.strokeStyle = rimA(0.30, T.rim2); g.lineWidth = 2;
  g.beginPath(); g.arc(cx, PV.spring, PV.R - 1, Math.PI * 1.02, Math.PI * 1.62); g.stroke();
  g.restore();
  // deur: twee deurvleugels met stijlen
  g.fillStyle = T.door; g.fillRect(cx - 78, base - 300, 156, 286);
  g.strokeStyle = PAL.frame; g.lineWidth = 7; g.strokeRect(cx - 78, base - 300, 156, 286);
  g.lineWidth = 5; g.beginPath(); g.moveTo(cx, base - 300); g.lineTo(cx, base - PV.T); g.stroke();
  g.fillStyle = "rgba(210,190,140,0.55)"; g.fillRect(cx - 14, base - 150, 4, 22); g.fillRect(cx + 10, base - 150, 4, 22);

  // ---- vleugels: roeden en lichte rand
  [-1, 1].forEach(function (side) {
    var w = wingRect(side);
    g.strokeStyle = PAL.frame; g.lineWidth = 6;
    // kozijnen tussen de vakken
    wingGlass(side).forEach(function (p) {
      g.strokeStyle = PAL.frame; g.lineWidth = 7; g.strokeRect(p.x, p.y, p.w, p.h);
    });
    g.fillStyle = rimA(0.16); g.fillRect(side < 0 ? w.x0 : w.x1 - 1.5, w.top, 1.5, w.base - w.top);
  });
  // pilasters tussen hal en vleugels
  g.fillStyle = PAL.frame2;
  [PV.x0 - 14, PV.x1 - 2].forEach(function (x) { g.fillRect(x, PV.wingTop - 28, 16, base - PV.wingTop + 28); });
  g.fillStyle = rimA(0.22); g.fillRect(PV.x0 - 14, PV.wingTop - 28, 1.4, base - PV.wingTop + 28);

  // ---- terras en trap
  var slab = lin(g, 0, base, 0, PV.slabY, [[0, T.slab[0]], [0.08, T.slab[1]], [1, T.slab[2]]]);
  g.fillStyle = slab; g.fillRect(48, base, PV.W - 96, PV.slabY - base);
  g.fillStyle = rimA(0.30, T.rim2); g.fillRect(48, base, PV.W - 96, 1.6);
  // de trap voor de deur (drie treden)
  [[0.36, 0, 16], [0.43, 16, 17], [0.5, 33, 18]].forEach(function (s, idx) {
    var w = PV.hw * s[0], y = base + s[1] + 2;
    g.fillStyle = idx % 2 ? T.steps[0] : T.steps[1]; g.fillRect(cx - w / 2, y, w, s[2]);
    g.fillStyle = rimA(0.26 - idx * 0.05, T.rim2); g.fillRect(cx - w / 2, y, w, 1.4);
  });

  // ---- urnen met bloemen en lantaarns
  [-1, 1].forEach(function (s) {
    urn(g, cx + s * PV.hw * 0.40, base + 2, s);
    lampPost(g, cx + s * (PV.hw / 2 + PV.ww * 0.78), base + 2, 0.86);
  });
  lampPost(g, cx - PV.hw * 0.62, base + 2, 0.7);
  lampPost(g, cx + PV.hw * 0.62, base + 2, 0.7);

  // ---- weerspiegeling in het water onder het terras
  if (withReflection) reflect(c, PV.slabY, 0.36, 250, 9);
  return c;
}

function chandelier(g, cx, y, s, line, glint) {
  g.save(); g.translate(cx, y); g.scale(s, s);
  g.strokeStyle = line; g.lineWidth = 1.8;
  g.beginPath(); g.moveTo(0, -150); g.lineTo(0, -40); g.stroke();
  [[0, 34, 110], [0, 62, 78], [0, 92, 46]].forEach(function (t) {
    g.beginPath(); g.ellipse(0, t[0] + 0, t[2] / 2, 10, 0, 0, TAU); g.stroke();
  });
  g.beginPath(); g.moveTo(-55, -2); g.quadraticCurveTo(0, 30, 55, -2); g.stroke();
  g.beginPath(); g.moveTo(-38, 22); g.quadraticCurveTo(0, 54, 38, 22); g.stroke();
  g.fillStyle = glint;
  var r = rng(4);
  for (var i = 0; i < 46; i++) { var a = r() * TAU, d = Math.sqrt(r()) * 56; g.fillRect(Math.cos(a) * d - 1, 4 + Math.sin(a) * d * 0.62 - 1, 2, 3 + r() * 6); }
  g.restore();
}
function flowersInside(g, alpha) {
  var r = rng(15);
  [[PV.cx - 168, PV.base - 20], [PV.cx + 168, PV.base - 20]].forEach(function (p) {
    for (var i = 0; i < 40; i++) {
      var x = p.x + (r() - 0.5) * 70, y = p.y - 100 - Math.pow(r(), 0.8) * 140, rr = 7 + r() * 11;
      g.fillStyle = "rgba(220,225,230," + (alpha * (0.5 + r() * 0.8)) + ")";
      g.beginPath(); g.arc(x, y, rr, 0, TAU); g.fill();
    }
    g.fillStyle = T.flowerIn; g.fillRect(p.x - 2, p.y - 100, 4, 100);
  });
}
function urn(g, x, y, side) {
  g.save(); g.translate(x, y);
  // zuil en vaas
  g.fillStyle = T.urn;
  g.beginPath(); g.moveTo(-26, 0); g.lineTo(-22, -26); g.lineTo(22, -26); g.lineTo(26, 0); g.closePath(); g.fill();
  g.beginPath(); g.moveTo(-18, -26); g.bezierCurveTo(-30, -56, -40, -86, -34, -104); g.lineTo(34, -104); g.bezierCurveTo(40, -86, 30, -56, 18, -26); g.closePath(); g.fill();
  g.fillStyle = T.urnRim; g.fillRect(-40, -112, 80, 11);
  g.fillStyle = rimA(0.30, T.urnHl); g.fillRect(-40, -112, 80, 1.3);
  g.fillStyle = rimA(0.18, T.urnHl); g.beginPath(); g.moveTo(-31, -100); g.bezierCurveTo(-37, -84, -28, -58, -16, -30); g.lineTo(-14, -30); g.bezierCurveTo(-26, -58, -33, -84, -28, -100); g.closePath(); g.fill();
  // bloemen: ivoor, zacht verlicht van links
  var r = rng(side > 0 ? 71 : 29);
  var blooms = [];
  for (var i = 0; i < 46; i++) {
    var a = r() * Math.PI, d = Math.pow(r(), 0.7) * 54;
    blooms.push({ x: Math.cos(a) * d * 0.95, y: -118 - Math.sin(a) * d * 1.1, r: 6.5 + r() * 9, t: r() });
  }
  blooms.sort(function (p, q) { return p.y - q.y; });
  blooms.forEach(function (b) {
    var shade = 0.55 + 0.45 * (1 - (b.x + 54) / 108);
    g.fillStyle = "rgba(" + Math.round(150 + 90 * shade) + "," + Math.round(160 + 74 * shade) + "," + Math.round(170 + 50 * shade) + "," + (0.5 + 0.4 * b.t) + ")";
    g.beginPath(); g.arc(b.x, b.y, b.r, 0, TAU); g.fill();
    g.fillStyle = "rgba(" + T.bloomShade + ",0.35)"; g.beginPath(); g.arc(b.x + b.r * 0.2, b.y + b.r * 0.25, b.r * 0.55, 0, TAU); g.fill();
  });
  // een paar bladeren
  g.strokeStyle = T.leaf; g.lineWidth = 2;
  for (var k = 0; k < 7; k++) { var aa = Math.PI * (0.1 + 0.8 * k / 6); g.beginPath(); g.moveTo(0, -112); g.quadraticCurveTo(Math.cos(aa) * 40, -112 - Math.sin(aa) * 30, Math.cos(aa) * 66, -108 - Math.sin(aa) * 6); g.stroke(); }
  g.restore();
}
function lampPost(g, x, y, s) {
  g.save(); g.translate(x, y); g.scale(s, s);
  g.fillStyle = PAL.frame;
  g.fillRect(-2, -172, 4, 172);
  g.fillRect(-9, -8, 18, 8);
  g.fillRect(-6, -14, 12, 6);
  g.beginPath(); g.moveTo(-12, -214); g.lineTo(12, -214); g.lineTo(9, -174); g.lineTo(-9, -174); g.closePath(); g.fill();
  g.beginPath(); g.moveTo(-14, -214); g.lineTo(0, -230); g.lineTo(14, -214); g.closePath(); g.fill();
  g.fillRect(-1, -240, 2, 12);
  g.fillStyle = T.lampGlass; g.fillRect(-8, -210, 16, 32);
  g.fillStyle = rimA(0.25, T.rim2); g.fillRect(-12, -214, 1.2, 40);
  g.restore();
}

/* Spiegeling in water of nat steen: omgekeerd, zacht, met rimpels, verdwijnt met de afstand. */
function reflect(c, y0, strength, depth, seed) {
  var W = c.width, g = c.getContext("2d");
  var m = cv(W, depth), mg = m.getContext("2d");
  mg.save(); mg.translate(0, depth); mg.scale(1, -0.82);
  mg.drawImage(c, 0, y0 - depth / 0.82, W, depth / 0.82, 0, 0, W, depth / 0.82);
  mg.restore();
  var rip = cv(W, depth), rg = rip.getContext("2d"), rr = rng(seed);
  for (var y = 0; y < depth; y += 2) {
    var dx = Math.sin(y * 0.045 + seed) * (0.5 + y * 0.012) + (rr() - 0.5) * (0.6 + y * 0.01);
    rg.drawImage(m, 0, y, W, 2, dx, y, W, 2);
  }
  var soft = cv(W, depth), sg = soft.getContext("2d");
  sg.filter = "blur(3.2px)"; sg.drawImage(rip, 0, 0);
  sg.filter = "none";
  sg.globalCompositeOperation = "destination-in";
  sg.fillStyle = lin(sg, 0, 0, 0, depth, [[0, "rgba(0,0,0,1)"], [0.55, "rgba(0,0,0,0.35)"], [1, "rgba(0,0,0,0)"]]);
  sg.fillRect(0, 0, W, depth);
  g.globalAlpha = strength; g.drawImage(soft, 0, y0 + 2); g.globalAlpha = 1;
}

/* =================================================================== lichtkaarten */
var WARM = { core: [255, 236, 190], mid: [232, 196, 136], edge: [196, 140, 80] };
/* Champagnelicht in een ruit: donkerder bovenin (plafond), warm en helder onderin (tafels, kaarsen). Nooit egaal wit. */
function warmFill(g, x, y, w, h, k) {
  g.fillStyle = lin(g, 0, y, 0, y + h, [[0, rgba(WARM.edge, 0.50 * k)], [0.45, rgba(WARM.mid, 0.72 * k)], [1, rgba(WARM.core, 0.90 * k)]]);
  g.fillRect(x, y, w, h);
  // zachte horizontale variatie: het licht komt van binnen, de randen blijven iets donkerder
  g.fillStyle = lin(g, x, 0, x + w, 0, [[0, "rgba(" + T.shade + ",0.22)"], [0.3, "rgba(" + T.shade + ",0)"], [0.7, "rgba(" + T.shade + ",0)"], [1, "rgba(" + T.shade + ",0.22)"]]);
  g.fillRect(x, y, w, h);
}
/* Halo: een brede, zachte gloed rond het licht, zodat het glas in de lucht "uitloopt". */
function halo(target, src, blurPx, alpha) {
  var g = target.getContext("2d"), b = cv(src.width, src.height), bg = b.getContext("2d");
  bg.filter = "blur(" + blurPx + "px)"; bg.drawImage(src, 0, 0);
  g.globalCompositeOperation = "lighter"; g.globalAlpha = alpha; g.drawImage(b, 0, 0);
  g.globalAlpha = 1; g.globalCompositeOperation = "source-over";
}
/* Weerspiegeling van het licht in het natte terras en het water. */
function reflectLight(c, strength) { reflect(c, PV.slabY, strength, 270, 14); }

function newLayer() { var c = cv(PV.W, PV.H); return { c: c, g: c.getContext("2d") }; }

/* Licht van de zijramen */
function lichtZij() {
  var L = newLayer(), g = L.g, r = rng(103);
  var core = cv(PV.W, PV.H), cg = core.getContext("2d");
  [-1, 1].forEach(function (side) {
    wingGlass(side).forEach(function (p) {
      var k = 0.78 + 0.22 * r();
      warmFill(cg, p.x, p.y, p.w, p.h, k);
      // zachte lichtval: boven iets donkerder (plafond), onderin warm
      cg.fillStyle = lin(cg, 0, p.y, 0, p.y + p.h * 0.5, [[0, "rgba(" + T.shade + ",0.28)"], [1, "rgba(" + T.shade + ",0)"]]);
      cg.fillRect(p.x, p.y, p.w, p.h * 0.5);
      // silhouetten van bloemen en meubels voor diepte

    });
  });
  g.drawImage(core, 0, 0);
  halo(L.c, core, 24, 0.30); halo(L.c, core, 64, 0.18);
  // de roeden blijven donker
  g.save();
  [-1, 1].forEach(function (side) { wingGlass(side).forEach(function (p) { g.strokeStyle = PAL.frame; g.lineWidth = 7; g.strokeRect(p.x, p.y, p.w, p.h); g.lineWidth = 4; g.beginPath(); g.moveTo(p.x + p.w / 2, p.y); g.lineTo(p.x + p.w / 2, p.y + p.h); g.stroke(); }); });
  g.restore();
  reflectLight(L.c, 0.5);
  return L.c;
}
/* Licht van de ingang: deur, trap, urnen */
function lichtEntree() {
  var L = newLayer(), g = L.g, cx = PV.cx, base = PV.base;
  var core = cv(PV.W, PV.H), cg = core.getContext("2d");
  warmFill(cg, cx - 71, base - 294, 142, 276, 0.92);
  // diepte: een lage, warme gloed (de zaal erachter) en twee donkere silhouetten van gasten-aan-tafel
  cg.fillStyle = rad(cg, cx, base - 120, 0, cx, base - 120, 150, [[0, "rgba(255,240,205,0.40)"], [1, "rgba(255,240,205,0)"]]);
  cg.fillRect(cx - 78, base - 300, 156, 286);

  g.drawImage(core, 0, 0);
  halo(L.c, core, 20, 0.34); halo(L.c, core, 60, 0.20);
  g.strokeStyle = PAL.frame; g.lineWidth = 7; g.strokeRect(cx - 78, base - 300, 156, 286);
  g.lineWidth = 5; g.beginPath(); g.moveTo(cx, base - 300); g.lineTo(cx, base - PV.T); g.stroke();
  // het licht valt de trap af
  g.globalCompositeOperation = "lighter";
  g.fillStyle = lin(g, 0, base, 0, base + 70, [[0, rgba(WARM.mid, 0.55)], [1, rgba(WARM.mid, 0)]]);
  g.beginPath(); g.moveTo(cx - 80, base); g.lineTo(cx + 80, base); g.lineTo(cx + 120, base + 70); g.lineTo(cx - 120, base + 70); g.closePath(); g.fill();
  // opwaarts licht op de bloemen in de urnen
  [-1, 1].forEach(function (s) {
    var ux = cx + s * PV.hw * 0.40;
    g.fillStyle = rad(g, ux, base - 96, 0, ux, base - 96, 95, [[0, "rgba(255,226,170,0.28)"], [1, "rgba(255,226,170,0)"]]);
    g.fillRect(ux - 100, base - 200, 200, 200);
  });
  g.globalCompositeOperation = "source-over";
  reflectLight(L.c, 0.62);
  return L.c;
}
/* Licht van de hal: de grote boog met de kroonluchter */
function lichtKroon() {
  var L = newLayer(), g = L.g, cx = PV.cx;
  var core = cv(PV.W, PV.H), cg = core.getContext("2d");
  cg.save(); hallPath(cg, PV.T); cg.clip();
  // alleen het deel boven de deur
  cg.beginPath(); cg.rect(PV.x0, PV.top, PV.hw, PV.base - 300 - PV.top); cg.clip();
  cg.fillStyle = lin(cg, 0, PV.top, 0, PV.base - 300, [[0, rgba(WARM.edge, 0.42)], [0.5, rgba(WARM.mid, 0.66)], [1, rgba(WARM.core, 0.80)]]);
  cg.fillRect(PV.x0, PV.top, PV.hw, PV.hw * 1.5);
  cg.fillStyle = rad(cg, cx, PV.spring - PV.R * 0.38, 0, cx, PV.spring - PV.R * 0.38, PV.R * 1.0, [[0, "rgba(255,246,222,0.62)"], [0.4, "rgba(255,236,196,0.26)"], [1, "rgba(255,236,196,0)"]]);
  cg.fillRect(PV.x0, PV.top, PV.hw, PV.hw * 1.5);
  // facetten: elke waaiersector een tikje anders, zoals echt glas
  var rf = rng(12);
  for (var q = 0; q < 6; q++) {
    cg.fillStyle = "rgba(" + T.shade + "," + (0.06 + rf() * 0.12) + ")";
    cg.beginPath(); cg.moveTo(cx, PV.spring); cg.arc(cx, PV.spring, PV.R, Math.PI + q * Math.PI / 6, Math.PI + (q + 1) * Math.PI / 6); cg.closePath(); cg.fill();
  }
  cg.restore();
  g.drawImage(core, 0, 0);
  halo(L.c, core, 28, 0.34); halo(L.c, core, 84, 0.24);
  // kroonluchter: helder silhouet met kristallen
  g.save(); hallPath(g, PV.T); g.clip();
  chandelier(g, cx, PV.spring - PV.R * 0.40, 1.12, "rgba(80,50,18,0.62)", "rgba(255,250,232,0.95)");
  g.restore();
  // roeden blijven donker
  hallBars(g, PAL.frame, 6, 3.6);
  // de deur-ruimte blijft bij 'entree': hier wissen we alles onder de transom
  g.globalCompositeOperation = "destination-out";
  g.fillRect(PV.x0, PV.base - 300, PV.hw, 300);
  g.globalCompositeOperation = "source-over";
  // lantaarn op het dak
  var drumW = PV.hw * 0.2, drumH = PV.hw * 0.15, dTop = PV.top - drumH + 4;
  var ln = cv(PV.W, PV.H), lg = ln.getContext("2d");
  lg.fillStyle = lin(lg, 0, dTop, 0, dTop + drumH, [[0, rgba(WARM.core, 0.9)], [1, rgba(WARM.mid, 0.8)]]);
  lg.fillRect(cx - drumW / 2, dTop + 6, drumW, drumH - 4);
  g.drawImage(ln, 0, 0); halo(L.c, ln, 14, 0.7);
  g.strokeStyle = PAL.frame; g.lineWidth = 3;
  for (var i = 1; i < 4; i++) { var xx = cx - drumW / 2 + i * drumW / 4; g.beginPath(); g.moveTo(xx, dTop + 6); g.lineTo(xx, dTop + drumH); g.stroke(); }
  // een zeer zacht lichtschijnsel omhoog, door het glazen dak
  g.globalCompositeOperation = "lighter";
  g.fillStyle = rad(g, cx, PV.top - 20, 0, cx, PV.top - 20, 250, [[0, "rgba(255,230,170,0.20)"], [1, "rgba(255,230,170,0)"]]);
  g.fillRect(cx - 260, PV.top - 280, 520, 540);
  g.globalCompositeOperation = "source-over";
  reflectLight(L.c, 0.46);
  return L.c;
}
/* Kleine decoratieve lampjes: rand van de daken, de boog en de lantaarns */
function lichtLampjes() {
  var L = newLayer(), g = L.g, pts = [];
  // langs de boog van de hal
  for (var i = 0; i <= 26; i++) { var a = Math.PI + i * Math.PI / 26; pts.push([PV.cx + Math.cos(a) * (PV.R + 7), PV.spring + Math.sin(a) * (PV.R + 7), 1]); }
  // langs de dakrand van beide vleugels
  [-1, 1].forEach(function (side) {
    var w = wingRect(side), n = 9;
    for (var k = 0; k < n; k++) { pts.push([w.x0 - 2 + (w.x1 - w.x0 + 4) * k / (n - 1), w.top - 12, 0.85]); }
  });
  // lantaarns
  [[PV.cx - (PV.hw / 2 + PV.ww * 0.78), 0.86], [PV.cx + (PV.hw / 2 + PV.ww * 0.78), 0.86], [PV.cx - PV.hw * 0.62, 0.7], [PV.cx + PV.hw * 0.62, 0.7]].forEach(function (p) {
    pts.push([p[0], PV.base - 194 * p[1] + 2, 2.3 * p[1]]);
  });
  var core = cv(PV.W, PV.H), cg = core.getContext("2d");
  pts.forEach(function (p) {
    cg.fillStyle = rgba(WARM.core, 0.98); cg.beginPath(); cg.arc(p[0], p[1], 2.3 * p[2], 0, TAU); cg.fill();
  });
  g.drawImage(core, 0, 0);
  halo(L.c, core, 7, 1); halo(L.c, core, 22, 0.8);
  // lantaarnlicht op de grond
  g.globalCompositeOperation = "lighter";
  [[PV.cx - (PV.hw / 2 + PV.ww * 0.78)], [PV.cx + (PV.hw / 2 + PV.ww * 0.78)]].forEach(function (p) {
    g.fillStyle = rad(g, p[0], PV.base - 160, 0, p[0], PV.base - 160, 70, [[0, "rgba(255,222,160,0.34)"], [1, "rgba(255,222,160,0)"]]);
    g.fillRect(p[0] - 80, PV.base - 240, 160, 160);
  });
  g.globalCompositeOperation = "source-over";
  reflectLight(L.c, 0.4);
  return L.c;
}
/* Kaarsen op het terras en bij de deur */
function lichtKaarsen() {
  var L = newLayer(), g = L.g, base = PV.base, cx = PV.cx;
  var spots = [[cx - 120, base - 3, 1], [cx - 98, base - 3, 0.8], [cx + 98, base - 3, 0.8], [cx + 120, base - 3, 1], [cx - 214, base - 3, 0.9], [cx + 214, base - 3, 0.9], [cx - 60, base + 16, 0.7], [cx + 60, base + 16, 0.7]];
  var core = cv(PV.W, PV.H), cg = core.getContext("2d");
  spots.forEach(function (s) {
    var x = s[0], y = s[1], k = s[2];
    cg.fillStyle = "rgba(235,225,205,0.95)"; cg.fillRect(x - 4 * k, y - 26 * k, 8 * k, 26 * k);       // kaars
    cg.fillStyle = "rgba(6,12,22,0.5)"; cg.fillRect(x + 1 * k, y - 26 * k, 3 * k, 26 * k);
    cg.fillStyle = rad(cg, x, y - 34 * k, 0, x, y - 34 * k, 9 * k, [[0, "rgba(255,255,255,1)"], [0.4, "rgba(255,236,184,1)"], [1, "rgba(255,170,70,0)"]]);
    cg.beginPath(); cg.ellipse(x, y - 34 * k, 3.6 * k, 8.4 * k, 0, 0, TAU); cg.fill();
  });
  g.drawImage(core, 0, 0);
  g.globalCompositeOperation = "lighter";
  spots.forEach(function (s) { g.fillStyle = rad(g, s[0], s[1] - 34 * s[2], 0, s[0], s[1] - 34 * s[2], 50 * s[2], [[0, "rgba(255,210,140,0.36)"], [1, "rgba(255,210,140,0)"]]); g.fillRect(s[0] - 55, s[1] - 90, 110, 110); });
  g.globalCompositeOperation = "source-over";
  reflectLight(L.c, 0.4);
  return L.c;
}

/* =================================================================== voorgrond: hoog gras en een enkel onscherp bloemhoofd, in de hoeken */
function drawVoor(W, H, side) {
  var c = cv(W, H), g = c.getContext("2d"), r = rng(side < 0 ? 201 : 303);
  var s = side < 0 ? 1 : -1, bx = side < 0 ? 0 : W;
  function blades(count, hMin, hMax, wMax, blur, alpha, spread) {
    var layer = cv(W, H), lg = layer.getContext("2d");
    for (var i = 0; i < count; i++) {
      var x = bx + s * Math.pow(r(), 1.5) * W * spread, h0 = H * (hMin + r() * (hMax - hMin)), lean = s * (r() * 0.9 - 0.15) * 90;
      var base = H + 6, tipX = x + lean, tipY = H - h0, cxp = x + lean * 0.25, cyp = H - h0 * 0.55;
      var w0 = 1.6 + r() * wMax;
      lg.fillStyle = "rgba(" + T.grass + "," + alpha + ")";
      lg.beginPath();
      lg.moveTo(x - w0, base); lg.quadraticCurveTo(cxp - w0 * 0.5, cyp, tipX, tipY); lg.quadraticCurveTo(cxp + w0 * 0.5, cyp, x + w0, base);
      lg.closePath(); lg.fill();
      // een zweem maanlicht langs de rand
      lg.strokeStyle = "rgba(" + T.grassRim + "," + (0.10 * alpha * T.rimK) + ")"; lg.lineWidth = 0.9;
      lg.beginPath(); lg.moveTo(x - w0, base); lg.quadraticCurveTo(cxp - w0 * 0.5, cyp, tipX, tipY); lg.stroke();
    }
    g.save(); if (blur) g.filter = "blur(" + blur + "px)"; g.drawImage(layer, 0, 0); g.restore();
  }
  blades(70, 0.10, 0.42, 3.2, 0, 0.92, 0.5);          // scherp, achter
  blades(26, 0.18, 0.62, 5.5, 2.2, 0.92, 0.36);       // iets onscherp
  blades(10, 0.30, 0.90, 11, 7, 0.88, 0.2);           // heel onscherp, vooraan
  // randen: laat alles zacht uitlopen naar het donker, ook aan de binnenkant
  g.globalCompositeOperation = "destination-in";
  var m = cv(W, H), mg = m.getContext("2d");
  mg.fillStyle = lin(mg, side < 0 ? 0 : W, 0, side < 0 ? W : 0, 0, [[0, "rgba(0,0,0,1)"], [0.6, "rgba(0,0,0,1)"], [1, "rgba(0,0,0,0)"]]);
  mg.fillRect(0, 0, W, H);
  g.drawImage(m, 0, 0);
  g.globalCompositeOperation = "source-over";
  return c;
}

/* =================================================================== voorbeeld (alle lagen op elkaar, om te beoordelen) */
function composePreview(layers, W, H, lit) {
  var c = cv(W, H), g = c.getContext("2d");
  var s = W / 2400;
  g.drawImage(layers.lucht, 0, 0, W, H);
  g.globalAlpha = 0.9; g.drawImage(layers.auroraA, 0, 0, W, H); g.globalAlpha = 0.8; g.drawImage(layers.auroraB, 0, 0, W, H); g.globalAlpha = 1;
  g.drawImage(layers.ver, 0, 0, W, H);
  g.drawImage(layers.mist, 0, H * 0.58, W, H * 0.3);
  // paviljoen: onderaan in het midden, hoogte 62% van de hoogte
  var ph = H * 0.62, pw = ph * PV.W / PV.H, px = (W - pw) / 2, py = H - ph;
  g.drawImage(layers.paviljoen, px, py, pw, ph);
  if (lit) ["entree", "zij", "kroon", "lampjes", "kaarsen"].forEach(function (k) { g.drawImage(layers[k], px, py, pw, ph); });
  g.drawImage(layers.mist, -W * 0.2, H * 0.72, W * 1.2, H * 0.28);
  var vh = H * 0.5, vw = vh * layers.voorL.width / layers.voorL.height;
  g.drawImage(layers.voorL, 0, H - vh, vw, vh);
  g.drawImage(layers.voorR, W - vw, H - vh, vw, vh);
  return c;
}

function composePlane(layers, lit) {
  var c = cv(PV.W, PV.H), g = c.getContext("2d");
  g.fillStyle = T.plane; g.fillRect(0, 0, PV.W, PV.H);
  g.drawImage(layers.paviljoen, 0, 0);
  if (lit) lit.forEach(function (k) { g.drawImage(layers[k], 0, 0); });
  return c;
}

/* Fluweelkorrel: een naadloze tegel met fijne lichte en donkere puntjes en korte vezels (voor het papier van de envelop). */
function drawKorrel(S) {
  var c = cv(S, S), g = c.getContext("2d"), d = g.createImageData(S, S), a = d.data, r = rng(2024);
  for (var i = 0; i < a.length; i += 4) {
    var v = r();
    if (v < 0.5) { a[i] = a[i + 1] = a[i + 2] = 255; a[i + 3] = Math.round(r() * 20); }
    else { a[i] = a[i + 1] = a[i + 2] = 0; a[i + 3] = Math.round(r() * 34); }
  }
  g.putImageData(d, 0, 0);
  g.lineCap = "round";
  for (var k = 0; k < S * 0.9; k++) {
    var x = r() * S, y = r() * S, l = 2 + r() * 5, an = r() * TAU;
    g.strokeStyle = r() < 0.5 ? "rgba(190,215,255," + (0.03 + r() * 0.05) + ")" : "rgba(0,0,0," + (0.05 + r() * 0.07) + ")";
    g.lineWidth = 0.6 + r() * 0.5;
    [[0, 0], [S, 0], [0, S], [S, S], [-S, 0], [0, -S]].forEach(function (o) {
      g.beginPath(); g.moveTo(x + o[0], y + o[1]); g.lineTo(x + o[0] + Math.cos(an) * l, y + o[1] + Math.sin(an) * l); g.stroke();
    });
  }
  return c;
}

/* =================================================================== bloemen: een hoek met takken en bloemen, en een hangende slinger */
var DEG = Math.PI / 180;
var FLORA = {
  nacht: {
    leaf: ["#1f5a66", "#0e303a"], leafLight: "rgba(150,210,200,0.18)", vein: "rgba(190,230,220,0.38)", stem: "#17434d",
    bloom: [["#fbf5e6", "#eadcbc", "#c7ae7a"], ["#f1e6cf", "#dcc795", "#b79c5b"], ["#dbe8f3", "#b8d0e4", "#86a9c6"], ["#fff9ee", "#efe2c4", "#d3bd8a"]],
    petalEdge: "rgba(90,70,30,0.24)", heart: ["#ecca7c", "#a98334"], berry: ["#f4d890", "#a98334"], gyp: "rgba(250,246,236,0.96)", gold: "#d9c38c", shadow: "rgba(0,0,0,0.6)", light: "255,226,160"
  },
  parel: {
    leaf: ["#9fc0b4", "#628a7c"], leafLight: "rgba(255,255,255,0.24)", vein: "rgba(255,255,255,0.5)", stem: "#6f9486",
    bloom: [["#ffffff", "#f1eef6", "#d3cde2"], ["#fff8ea", "#f2e2bd", "#d9bf86"], ["#e9f1fa", "#c5d9ee", "#93b5d6"], ["#fdfcff", "#e7e3f2", "#c4bcd8"]],
    petalEdge: "rgba(90,100,130,0.24)", heart: ["#ebca7c", "#b8892e"], berry: ["#f1d79a", "#b8892e"], gyp: "rgba(176,188,208,0.98)", gold: "#c9a65a", shadow: "rgba(60,70,100,0.4)", light: "255,230,170"
  },
  roze: {
    leaf: ["#abc1a4", "#6d8967"], leafLight: "rgba(255,255,255,0.22)", vein: "rgba(255,255,255,0.5)", stem: "#7f9a78",
    bloom: [["#fff1ee", "#f6c9cf", "#e19aa8"], ["#fff6ea", "#f9d3b8", "#e8a98c"], ["#fdeaf1", "#f1b9cd", "#d98aa6"], ["#fffaf3", "#f4e0cf", "#dcb9a0"]],
    petalEdge: "rgba(120,60,80,0.24)", heart: ["#f1c47c", "#b8743e"], berry: ["#f4cca4", "#b8743e"], gyp: "rgba(226,164,168,0.95)", gold: "#d9ae82", shadow: "rgba(110,60,80,0.4)", light: "255,214,180"
  },
  salie: {
    leaf: ["#88ab91", "#4f7860"], leafLight: "rgba(255,255,255,0.22)", vein: "rgba(255,255,255,0.5)", stem: "#5f8670",
    bloom: [["#fffef4", "#f2eed2", "#cfc690"], ["#fff9df", "#f3e4a6", "#d6bd62"], ["#ffffff", "#eef3ea", "#bfd0bf"], ["#fbf8e6", "#e7e2bb", "#c2b97e"]],
    petalEdge: "rgba(70,90,50,0.24)", heart: ["#e5c76c", "#a88a2c"], berry: ["#f0d98e", "#a88a2c"], gyp: "rgba(160,190,160,0.98)", gold: "#c8b46a", shadow: "rgba(40,70,56,0.4)", light: "255,232,168"
  }
};
function F() { return FLORA[T.name]; }

function leafPath(g, len, wid) {
  g.beginPath(); g.moveTo(0, 0);
  g.bezierCurveTo(len * 0.22, -wid * 1.05, len * 0.7, -wid * 0.85, len, 0);
  g.bezierCurveTo(len * 0.7, wid * 0.85, len * 0.22, wid * 1.05, 0, 0); g.closePath();
}
function pointedLeaf(g, x, y, ang, len, wid) {
  var f = F();
  g.save(); g.translate(x, y); g.rotate(ang);
  leafPath(g, len, wid); g.fillStyle = lin(g, 0, -wid, 0, wid, [[0, f.leaf[0]], [1, f.leaf[1]]]); g.fill();
  g.save(); leafPath(g, len, wid); g.clip(); g.fillStyle = f.leafLight; g.fillRect(0, -wid * 1.1, len, wid * 1.1); g.restore();
  g.strokeStyle = f.vein; g.lineWidth = Math.max(0.7, wid * 0.07); g.beginPath(); g.moveTo(len * 0.04, 0); g.quadraticCurveTo(len * 0.5, -wid * 0.1, len * 0.94, 0); g.stroke();
  g.restore();
}
function roundLeaf(g, x, y, ang, len, wid) {
  var f = F();
  g.save(); g.translate(x, y); g.rotate(ang);
  g.beginPath(); g.ellipse(len * 0.5, 0, len * 0.5, wid, 0, 0, TAU);
  g.fillStyle = rad(g, len * 0.38, -wid * 0.3, 0, len * 0.5, 0, len * 0.62, [[0, f.leaf[0]], [1, f.leaf[1]]]); g.fill();
  g.strokeStyle = f.vein; g.lineWidth = 0.8; g.globalAlpha = 0.6; g.beginPath(); g.moveTo(len * 0.04, 0); g.lineTo(len * 0.9, 0); g.stroke(); g.globalAlpha = 1;
  g.restore();
}
/* Een tak: een zachte boog met bladeren links en rechts, kleiner naar de top. kind 0: spitse bladeren, 1: ronde (eucalyptus). */
function tak(g, x0, y0, ang, length, kind, r, thick) {
  var f = F(), bend = (r() - 0.5) * length * 0.35;
  var nx = -Math.sin(ang), ny = Math.cos(ang);
  var ex = x0 + Math.cos(ang) * length, ey = y0 + Math.sin(ang) * length;
  var cx = (x0 + ex) / 2 + nx * bend, cy = (y0 + ey) / 2 + ny * bend;
  function P(t) { var u = 1 - t; return [u * u * x0 + 2 * u * t * cx + t * t * ex, u * u * y0 + 2 * u * t * cy + t * t * ey]; }
  function A(t) { var u = 1 - t; var dx = 2 * u * (cx - x0) + 2 * t * (ex - cx), dy = 2 * u * (cy - y0) + 2 * t * (ey - cy); return Math.atan2(dy, dx); }
  g.strokeStyle = f.stem; g.lineCap = "round"; g.lineWidth = thick || 3.4;
  g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo(cx, cy, ex, ey); g.stroke();
  var n = Math.round(length / (kind ? 26 : 30));
  for (var i = 1; i <= n; i++) {
    var t = i / (n + 1), p = P(t), a = A(t), s = 1 - t * 0.62;
    var len = (kind ? 40 : 66) * s * (0.85 + r() * 0.3), wid = (kind ? 21 : 15) * s;
    [-1, 1].forEach(function (side) {
      var aa = a + side * (0.62 + r() * 0.35);
      if (kind) roundLeaf(g, p[0], p[1], aa, len, wid); else pointedLeaf(g, p[0], p[1], aa, len, wid);
    });
  }
  var e = P(1), ae = A(1);
  if (kind) roundLeaf(g, e[0], e[1], ae, 34, 17); else pointedLeaf(g, e[0], e[1], ae, 60, 13);
  return { end: e, P: P, A: A };
}
function bloem(g, x, y, R, kind, r) {
  var f = F(), cols = f.bloom[kind % f.bloom.length];
  g.save(); g.translate(x, y); g.rotate(r() * TAU);
  var rings = 5, counts = [7, 6, 6, 5, 5];
  for (var k = 0; k < rings; k++) {
    var fr = 1 - k * 0.17, rr = R * fr, n = counts[k], off = r() * TAU;
    if (k === 0) { g.shadowColor = f.shadow; g.shadowBlur = R * 0.34; g.shadowOffsetY = R * 0.08; }
    for (var i = 0; i < n; i++) {
      var a = off + i * TAU / n + (r() - 0.5) * 0.22, pw = rr * (0.62 + 0.12 * r());
      g.save(); g.rotate(a);
      g.beginPath(); g.moveTo(0, 0); g.bezierCurveTo(rr * 0.12, -pw * 1.05, rr * 0.98, -pw * 0.95, rr, 0); g.bezierCurveTo(rr * 0.98, pw * 0.95, rr * 0.12, pw * 1.05, 0, 0); g.closePath();
      g.fillStyle = rad(g, rr * 0.1, 0, 0, rr * 0.1, 0, rr * 1.06, [[0, cols[2]], [0.5, cols[1]], [1, cols[0]]]); g.fill();
      g.shadowColor = "rgba(0,0,0,0)"; g.shadowBlur = 0; g.shadowOffsetY = 0;
      g.strokeStyle = f.petalEdge; g.lineWidth = 0.9; g.stroke();
      g.restore();
    }
  }
  g.fillStyle = rad(g, 0, 0, 0, 0, 0, R * 0.2, [[0, f.heart[0]], [1, f.heart[1]]]); g.beginPath(); g.arc(0, 0, R * 0.17, 0, TAU); g.fill();
  g.restore();
}
function knop(g, x, y, R, ang, kind) {
  var f = F(), cols = f.bloom[kind % f.bloom.length];
  g.save(); g.translate(x, y); g.rotate(ang);
  g.fillStyle = f.leaf[1]; g.beginPath(); g.ellipse(-R * 0.1, 0, R * 0.7, R * 0.42, 0, 0, TAU); g.fill();
  g.fillStyle = rad(g, R * 0.2, -R * 0.2, 0, 0, 0, R * 1.2, [[0, cols[0]], [1, cols[2]]]);
  g.beginPath(); g.ellipse(R * 0.25, 0, R * 0.85, R * 0.62, 0, 0, TAU); g.fill();
  g.strokeStyle = f.petalEdge; g.lineWidth = 0.8; g.stroke();
  g.restore();
}
function bessen(g, x, y, ang, len, r) {
  var f = F();
  g.strokeStyle = f.stem; g.lineWidth = 1.8; g.lineCap = "round";
  var ex = x + Math.cos(ang) * len, ey = y + Math.sin(ang) * len;
  g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo((x + ex) / 2 - Math.sin(ang) * len * 0.12, (y + ey) / 2 + Math.cos(ang) * len * 0.12, ex, ey); g.stroke();
  for (var i = 0; i < 5; i++) {
    var bx = ex + (r() - 0.5) * 34 + Math.cos(ang) * i * 4, by = ey + (r() - 0.5) * 34 + Math.sin(ang) * i * 4, br = 5.5 + r() * 3.2;
    g.fillStyle = rad(g, bx - br * 0.3, by - br * 0.3, 0, bx, by, br * 1.1, [[0, f.berry[0]], [1, f.berry[1]]]);
    g.beginPath(); g.arc(bx, by, br, 0, TAU); g.fill();
    g.fillStyle = "rgba(255,255,255,0.55)"; g.beginPath(); g.arc(bx - br * 0.32, by - br * 0.34, br * 0.25, 0, TAU); g.fill();
  }
}
/* Gipskruid: ijle takjes met witte stipjes. */
function gips(g, x, y, ang, len, r) {
  var f = F();
  g.strokeStyle = f.gyp; g.globalAlpha = 0.75; g.lineWidth = 1.1; g.lineCap = "round";
  function twig(x1, y1, a, l, depth) {
    var x2 = x1 + Math.cos(a) * l, y2 = y1 + Math.sin(a) * l;
    g.beginPath(); g.moveTo(x1, y1); g.quadraticCurveTo((x1 + x2) / 2 + (r() - 0.5) * l * 0.2, (y1 + y2) / 2 + (r() - 0.5) * l * 0.2, x2, y2); g.stroke();
    if (depth > 0) { twig(x2, y2, a - 0.5 - r() * 0.3, l * 0.6, depth - 1); twig(x2, y2, a + 0.5 + r() * 0.3, l * 0.6, depth - 1); twig(x2, y2, a + (r() - 0.5) * 0.3, l * 0.55, depth - 1); }
    else { g.globalAlpha = 1; g.fillStyle = f.gyp; for (var i = 0; i < 3; i++) { g.beginPath(); g.arc(x2 + (r() - 0.5) * 9, y2 + (r() - 0.5) * 9, 1.6 + r() * 1.8, 0, TAU); g.fill(); } g.globalAlpha = 0.75; }
  }
  twig(x, y, ang, len * 0.4, 3);
  g.globalAlpha = 1;
}
/* Een dun gouden koord met kraaltjes langs een boog. */
function koord(g, pts, beads) {
  var f = F();
  g.strokeStyle = f.gold; g.lineWidth = 1.6; g.globalAlpha = 0.9;
  g.beginPath(); g.moveTo(pts[0], pts[1]); g.quadraticCurveTo(pts[2], pts[3], pts[4], pts[5]); g.stroke();
  for (var i = 1; i < beads; i++) {
    var t = i / beads, u = 1 - t, x = u * u * pts[0] + 2 * u * t * pts[2] + t * t * pts[4], y = u * u * pts[1] + 2 * u * t * pts[3] + t * t * pts[5];
    g.fillStyle = rad(g, x - 1, y - 1, 0, x, y, 4, [[0, "#fff6d8"], [1, f.gold]]); g.beginPath(); g.arc(x, y, 2.6 + (i % 3 === 0 ? 1.4 : 0), 0, TAU); g.fill();
  }
  g.globalAlpha = 1;
}

/* De hoek: hangt links boven aan; het script spiegelt en draait hem voor de andere hoeken. */
function drawHoek(S) {
  var c = cv(S, S), g = c.getContext("2d"), r = rng(77), k = S / 560;
  g.scale(k, k);
  // dunne takken eerst (achteraan), lange boog van ver naar dichtbij
  tak(g, -8, -8, 12 * DEG, 540, 1, r, 3.6);
  tak(g, -8, -8, 80 * DEG, 470, 0, r, 3.6);
  tak(g, -8, -8, 36 * DEG, 500, 0, r, 4.2);
  tak(g, -8, -8, 58 * DEG, 420, 1, r, 3.6);
  tak(g, -8, -8, 24 * DEG, 360, 1, r, 3.2);
  [[20, 470], [44, 430], [68, 400], [86, 340]].forEach(function (a) { gips(g, -4, -4, a[0] * DEG, a[1], r); });
  koord(g, [10, 400, 150, 150, 410, 14], 16);
  koord(g, [4, 250, 80, 90, 250, 6], 10);
  // knoppen en bessen
  [[300, 120, 21, 60], [430, 80, 17, 20], [120, 330, 22, 100], [70, 450, 16, 70], [330, 250, 16, 40], [210, 400, 17, 80]].forEach(function (b, i) { knop(g, b[0], b[1], b[2], b[3] * DEG, i); });
  [[360, 190, 40], [190, 360, 70], [470, 150, 20], [140, 470, 85]].forEach(function (b) { bessen(g, b[0], b[1], b[2] * DEG, 40, r); });
  // bloemen: klein naar groot
  bloem(g, 380, 56, 38, 1, r); bloem(g, 52, 392, 40, 2, r); bloem(g, 262, 168, 44, 3, r); bloem(g, 160, 262, 46, 1, r);
  bloem(g, 268, 60, 66, 2, r); bloem(g, 62, 270, 68, 3, r);
  bloem(g, 150, 168, 78, 0, r); bloem(g, 70, 70, 96, 1, r); bloem(g, 100, 130, 70, 0, r);
  return c;
}

/* De slinger: hangt aan twee kanten (links en rechts op de rand), met bloemen, takjes, bessen en kleine lampjes. */
function drawSlinger(W, H) {
  var c = cv(W, H), g = c.getContext("2d"), r = rng(31), f = F(), k = W / 1400;
  g.scale(k, k);
  var x0 = -10, y0 = 30, x1 = 1410, y1 = 30, cxp = 700, cyp = 270;       // bezier-boog met doorhang
  function P(t) { var u = 1 - t; return [u * u * x0 + 2 * u * t * cxp + t * t * x1, u * u * y0 + 2 * u * t * cyp + t * t * y1]; }
  function A(t) { var u = 1 - t, dx = 2 * u * (cxp - x0) + 2 * t * (x1 - cxp), dy = 2 * u * (cyp - y0) + 2 * t * (y1 - cyp); return Math.atan2(dy, dx); }
  g.strokeStyle = f.stem; g.lineWidth = 4; g.lineCap = "round";
  g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo(cxp, cyp, x1, y1); g.stroke();
  // bladeren langs de hele slinger
  for (var i = 1; i < 70; i++) {
    var t = i / 70, p = P(t), a = A(t);
    [-1, 1].forEach(function (side) {
      var aa = a + side * (0.55 + r() * 0.5), len = 40 + r() * 34, wid = 12 + r() * 6;
      if (i % 3 === 0) roundLeaf(g, p[0], p[1], aa, len * 0.7, wid * 1.3); else pointedLeaf(g, p[0], p[1], aa, len, wid);
    });
  }
  // gouden koord langs de slinger, iets onder de bladeren
  var gp = [x0, y0 + 12, cxp, cyp + 24, x1, y1 + 12];
  koord(g, gp, 40);
  // bloemen op vaste plekken, groot in het midden
  [[0.5, 74, 0], [0.36, 56, 1], [0.64, 56, 2], [0.22, 44, 3], [0.78, 44, 0], [0.09, 38, 1], [0.91, 38, 2]].forEach(function (b) {
    var p = P(b[0]);
    bessen(g, p[0] + 40, p[1] + 8, A(b[0]) + 0.5, 40, r);
    bloem(g, p[0], p[1] + 6, b[1], b[2], r);
    bloem(g, p[0] - b[1] * 0.9, p[1] - 4, b[1] * 0.56, (b[2] + 1) % 4, r);
    bloem(g, p[0] + b[1] * 0.85, p[1] - 2, b[1] * 0.5, (b[2] + 2) % 4, r);
  });
  // kleine lampjes die onder de slinger hangen
  [0.14, 0.29, 0.43, 0.57, 0.71, 0.86].forEach(function (t, i) {
    var p = P(t), l = 34 + (i % 2) * 22;
    g.strokeStyle = f.gold; g.lineWidth = 1; g.beginPath(); g.moveTo(p[0], p[1] + 8); g.lineTo(p[0], p[1] + 8 + l); g.stroke();
    var y = p[1] + 8 + l;
    g.save(); g.globalCompositeOperation = "source-over";
    g.fillStyle = rad(g, p[0], y, 0, p[0], y, 30, [[0, "rgba(" + f.light + ",0.55)"], [1, "rgba(" + f.light + ",0)"]]); g.fillRect(p[0] - 30, y - 30, 60, 60);
    g.fillStyle = rad(g, p[0] - 1, y - 1, 0, p[0], y, 7, [[0, "#fffdf2"], [0.5, "rgba(" + f.light + ",1)"], [1, "rgba(" + f.light + ",0.9)"]]); g.beginPath(); g.arc(p[0], y, 6, 0, TAU); g.fill();
    g.restore();
  });
  return c;
}

window.AN = {drawHoek: drawHoek, drawSlinger: drawSlinger, setTheme: setTheme, THEMES: THEMES, drawKorrel: drawKorrel, composePlane: composePlane,
  PV: PV, drawLucht: drawLucht, drawAurora: drawAurora, drawVer: drawVer, drawMist: drawMist, drawPaviljoen: drawPaviljoen,
  lichtZij: lichtZij, lichtEntree: lichtEntree, lichtKroon: lichtKroon, lichtLampjes: lichtLampjes, lichtKaarsen: lichtKaarsen,
  drawVoor: drawVoor, composePreview: composePreview
};
