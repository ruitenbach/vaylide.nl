// Contrast van de tekst op het openingsscherm van Kerstmagie, gemeten op de echte pixels (de tekst staat op de film,
// dus e2e/toegankelijkheid.cjs laat hem over aan deze controle: data-tekst-op-beeld).
// Per schermformaat wordt de tekst onzichtbaar gemaakt, het beeld vastgelegd en voor elke pixel onder de letters het
// contrast met de tekstkleur berekend. Eis: minimaal 4,5:1 voor de slechtste pixel.
// Gebruik (vanuit de projectmap, server in testmodus): node e2e/kerstmagie-contrast.cjs http://127.0.0.1:8000 [uitvoermap]
const { chromium } = require("playwright");
const fs = require("fs");
const zlib = require("zlib");

const [base = "http://127.0.0.1:8000", outDir = "/tmp/kerstmagie-contrast"] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });

// Kleine PNG-lezer (8 bit RGB of RGBA, zonder interlace): genoeg voor een schermafbeelding van Playwright.
function readPng(buf) {
  let pos = 8, width, height, bpp, idat = [];
  while (pos < buf.length) {
    const len = buf.readUInt32BE(pos), type = buf.toString("ascii", pos + 4, pos + 8), data = buf.subarray(pos + 8, pos + 8 + len);
    if (type === "IHDR") { width = data.readUInt32BE(0); height = data.readUInt32BE(4); bpp = data[9] === 6 ? 4 : 3; }
    if (type === "IDAT") idat.push(data);
    pos += 12 + len;
  }
  const raw = zlib.inflateSync(Buffer.concat(idat)), stride = width * bpp, px = Buffer.alloc(height * stride);
  for (let y = 0; y < height; y++) {
    const f = raw[y * (stride + 1)], row = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? px[y * stride + x - bpp] : 0, b = y ? px[(y - 1) * stride + x] : 0, c = x >= bpp && y ? px[(y - 1) * stride + x - bpp] : 0;
      let v = row[x];
      if (f === 1) v += a; else if (f === 2) v += b; else if (f === 3) v += (a + b) >> 1;
      else if (f === 4) { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      px[y * stride + x] = v & 255;
    }
  }
  return { width, height, bpp, px };
}
const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
const lum = (r, g, b) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);

(async () => {
  const browser = await chromium.launch();
  let failed = 0;
  for (const [name, w, h] of [["360x640", 360, 640], ["390x844", 390, 844], ["768x1024", 768, 1024], ["1366x768", 1366, 768]]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const p = await ctx.newPage();
    await p.goto(`${base}/voorbeeld/kerstmagie/?gelegenheid=kerst`, { waitUntil: "load" });
    await p.waitForTimeout(2200);
    const fg = await p.evaluate(() => getComputedStyle(document.querySelector(".kl-cover__title")).color.match(/\d+/g).slice(0, 3).map(Number));
    await p.evaluate(() => { document.querySelectorAll(".fx-slot, .inv-banner").forEach((e) => (e.style.display = "none")); document.querySelectorAll(".kl-cover__kicker, .kl-cover__title, .kl-cover__hint").forEach((e) => (e.style.color = "transparent")); });
    await p.waitForTimeout(300);
    const boxes = {};
    for (const c of ["kicker", "title", "hint"]) boxes[c] = await p.locator(".kl-cover__" + c).boundingBox();
    const shot = await p.screenshot({ path: `${outDir}/meetbeeld-${name}.png` });
    const img = readPng(shot), yf = lum(...fg);
    for (const [c, b] of Object.entries(boxes)) {
      let worst = Infinity;
      for (let y = Math.floor(b.y); y < Math.ceil(b.y + b.height); y++) for (let x = Math.floor(b.x); x < Math.ceil(b.x + b.width); x++) {
        const i = (y * img.width + x) * img.bpp, q = (Math.max(lum(img.px[i], img.px[i + 1], img.px[i + 2]), yf) + 0.05) / (Math.min(lum(img.px[i], img.px[i + 1], img.px[i + 2]), yf) + 0.05);
        if (q < worst) worst = q;
      }
      const ok = worst >= 4.5; if (!ok) failed++;
      console.log(`${ok ? "ok    " : "FOUT  "} ${name} ${c}: slechtste pixel ${worst.toFixed(1)}:1 (minimaal 4,5:1)`);
    }
    await ctx.close();
  }
  await browser.close();
  console.log(failed ? `${failed} meting(en) onder 4,5:1` : "Alle metingen halen 4,5:1");
  process.exit(failed ? 1 : 0);
})();
