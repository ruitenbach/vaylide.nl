// Kerstmagie: sneeuw tijdens het scrollen en de datum onder ijs (designs/kerstmagie/v1/snow.js en kras.js).
// Controleert: de sneeuw loopt na het openen en tijdens het scrollen door, ligt onder de tekst en boven de beelden, volgt de knop
// 'Beweging' en 'minder beweging'; de datum is leesbaar zonder JavaScript, bij minder beweging en als het tekenen mislukt;
// krassen, de knop 'Onthul de datum' (ook met toetsenbord) en onthouden per sessie; en de belasting op een vertraagde processor.
// Gebruik (vanuit de projectmap, server in testmodus): node e2e/kerstmagie-kaart.cjs http://127.0.0.1:8000
const { chromium } = require("playwright");
const zlib = require("zlib");

const base = process.argv[2] || "http://127.0.0.1:8000";
const URL = `${base}/voorbeeld/kerstmagie/?gelegenheid=kerst#uitnodiging`;
let bad = 0;
const check = (name, ok, detail) => { if (!ok) bad++; console.log(`${ok ? "ok    " : "FOUT  "} ${name}: ${detail}`); };
const ink = (p, sel) => p.evaluate((s) => { const c = document.querySelector(s); if (!c) return -1; const g = c.getContext("2d"), d = g.getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 20) n++; return n; }, sel);
const snapshot = (p, sel) => p.evaluate((s) => document.querySelector(s).toDataURL(), sel);
const dateVisible = (p) => p.evaluate(() => { const d = document.querySelector("[data-kl-date]"); const f = document.querySelector(".kl-frost"); return !!d && getComputedStyle(d).visibility !== "hidden" && (!f || getComputedStyle(f).display === "none"); });


// Kleine PNG-lezer voor een schermafbeelding van Playwright (8 bit, zonder interlace).
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
      else if (f === 4) { const q = a + b - c, pa = Math.abs(q - a), pb = Math.abs(q - b), pc = Math.abs(q - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      px[y * stride + x] = v & 255;
    }
  }
  return { width, height, bpp, px };
}
const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
const lum = (r, g, b) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);

(async () => {
  const browser = await chromium.launch();
  const open = async (opts = {}, init) => {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, bypassCSP: true, ...opts });
    const p = await ctx.newPage();
    if (init) await p.addInitScript(init);
    const errors = []; p.on("pageerror", (e) => errors.push(String(e)));
    await p.goto(URL, { waitUntil: "load" }); await p.waitForTimeout(3200);
    return { ctx, p, errors };
  };

  // 1. Sneeuw
  { const { ctx, p, errors } = await open();
    const a = await ink(p, ".kl-snow--page");
    check("Sneeuw loopt na het openen", a > 50, `getekende punten: ${a}`);
    const layers = await p.evaluate(() => {
      const c = document.querySelector(".kl-snow--page"), cs = getComputedStyle(c), h1 = getComputedStyle(document.querySelector(".kl-hero__top")), sec = getComputedStyle(document.querySelector(".kl-section, .kl-duo__text")), img = getComputedStyle(document.querySelector(".kl-hero__bg"));
      const r = document.querySelector(".kl-names").getBoundingClientRect();
      return { snow: +cs.zIndex, tekst: +h1.zIndex, sectie: +sec.zIndex, beeld: +img.zIndex || 0, events: cs.pointerEvents, boven: document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2).closest(".kl-names") !== null };
    });
    check("Sneeuw ligt boven de beelden en onder de tekst", layers.beeld < layers.snow && layers.snow < layers.tekst && layers.snow < layers.sectie && layers.events === "none" && layers.boven, JSON.stringify(layers));
    const H = await p.evaluate(() => document.documentElement.scrollHeight);
    let all = true, notes = [];
    for (const f of [0.25, 0.5, 0.75, 1]) { await p.evaluate((y) => scrollTo(0, y), Math.round((H - 844) * f)); await p.waitForTimeout(700); const n = await ink(p, ".kl-snow--page"); notes.push(n); if (n < 50) all = false; }
    check("Sneeuw loopt door tijdens het scrollen", all, `getekende punten op 25/50/75/100%: ${notes.join(", ")}`);
    const s1 = await snapshot(p, ".kl-snow--page"); await p.waitForTimeout(500); const s2 = await snapshot(p, ".kl-snow--page");
    check("Sneeuw beweegt", s1 !== s2, "twee opnames verschillen");
    await p.click("[data-fx-toggle]"); await p.waitForTimeout(400);
    const f1 = await snapshot(p, ".kl-snow--page"); await p.waitForTimeout(700); const f2 = await snapshot(p, ".kl-snow--page");
    check("Knop 'Beweging' zet de sneeuw stil (blijft staan)", f1 === f2 && (await ink(p, ".kl-snow--page")) > 50, "beeld ongewijzigd en nog zichtbaar");
    await p.click("[data-fx-toggle]"); await p.waitForTimeout(700);
    const g1 = await snapshot(p, ".kl-snow--page"); await p.waitForTimeout(400); const g2 = await snapshot(p, ".kl-snow--page");
    check("Sneeuw loopt weer na aanzetten", g1 !== g2, "beeld verandert weer");
    check("Geen fouten in de console", errors.length === 0, errors.join("; ") || "geen");
    await ctx.close(); }

  // 2. Minder beweging: geen sneeuw, datum zichtbaar, geen ijslaag
  { const { ctx, p } = await open({ reducedMotion: "reduce" });
    const n = await ink(p, ".kl-snow--page");
    check("Minder beweging: geen sneeuw", n <= 0, `getekende punten: ${n}`);
    check("Minder beweging: datum zonder ijslaag", (await p.locator(".kl-frost").count()) === 0 && (await dateVisible(p)), "geen ijslaag, datum zichtbaar");
    await ctx.close(); }

  // 3. Zonder JavaScript
  { const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false }); const p = await ctx.newPage();
    await p.goto(URL, { waitUntil: "load" });
    const r = await p.evaluate(() => ({ frost: document.querySelectorAll(".kl-frost, .kl-snow").length, tekst: document.querySelector(".kl-date__day").textContent.trim(), zicht: getComputedStyle(document.querySelector(".kl-date")).visibility }));
    check("Zonder JavaScript: datum gewoon zichtbaar, geen ijslaag", r.frost === 0 && r.tekst.length > 0 && r.zicht === "visible", JSON.stringify(r));
    await ctx.close(); }

  // 4. Tekenen mislukt: geen ijslaag
  { const { ctx, p } = await open({}, () => { const o = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function () { return null; }; });
    check("Als het tekenen niet lukt: datum zichtbaar", (await p.locator(".kl-frost").count()) === 0 && (await dateVisible(p)), "geen ijslaag");
    await ctx.close(); }

  // 5. Krassen, toetsenbord, onthouden
  { const { ctx, p } = await open();
    const frost = await p.locator(".kl-frost").count();
    check("Datum begint onder een ijslaag", frost === 1, `ijslagen: ${frost}`);
    const box = await p.locator(".kl-date").boundingBox(), y = box.y + box.height * 0.45;
    await p.mouse.move(box.x + 12, y); await p.mouse.down();
    for (let x = 12; x < box.width * 0.3; x += 6) await p.mouse.move(box.x + x, y);
    await p.mouse.up(); await p.waitForTimeout(250);
    const part = await p.evaluate(() => { const c = document.querySelector(".kl-frost__ice"); const g = c.getContext("2d"); const px = g.getImageData(Math.round(c.width * 0.1), Math.round(c.height * 0.45), 1, 1).data[3]; const far = g.getImageData(Math.round(c.width * 0.8), Math.round(c.height * 0.45), 1, 1).data[3]; return { weg: px, rest: far, hint: document.querySelector(".kl-frost__hint").classList.contains("is-hidden") }; });
    check("Na een veeg is dat stuk weg, de rest blijft staan", part.weg < 40 && part.rest > 200 && part.hint, JSON.stringify(part));
    await p.mouse.move(box.x + box.width * 0.3, y - 12); await p.mouse.down();
    for (let x = box.width * 0.3; x < box.width * 0.95; x += 6) await p.mouse.move(box.x + x, y - 12);
    await p.mouse.move(box.x + box.width * 0.95, y + 14); for (let x = box.width * 0.95; x > 8; x -= 6) await p.mouse.move(box.x + x, y + 14);
    await p.mouse.up(); await p.waitForTimeout(1500);
    check("Na genoeg krassen smelt de rest weg", (await p.locator(".kl-frost").count()) === 0, "ijslaag verwijderd");
    await p.reload({ waitUntil: "load" }); await p.waitForTimeout(2500);
    check("Herladen in dezelfde sessie: datum direct zichtbaar", (await p.locator(".kl-frost").count()) === 0, "geen ijslaag");
    await ctx.close(); }
  { const { ctx, p } = await open();
    await p.keyboard.press("Tab"); let hit = false;
    for (let i = 0; i < 40 && !hit; i++) { hit = await p.evaluate(() => document.activeElement && document.activeElement.classList.contains("kl-frost__btn")); if (!hit) await p.keyboard.press("Tab"); }
    check("De knop 'Onthul de datum' is met Tab te bereiken", hit, hit ? "focus op de knop" : "niet gevonden");
    await p.keyboard.press("Enter"); await p.waitForTimeout(1400);
    check("Enter onthult de datum", (await p.locator(".kl-frost").count()) === 0 && (await dateVisible(p)), "ijslaag weg, focus op de datum");
    await ctx.close(); }
  { const { ctx, p } = await open();
    await p.click("[data-fx-toggle]"); await p.waitForTimeout(1400);
    check("Knop 'Beweging' op stil: de ijslaag verdwijnt en de datum staat er", (await p.locator(".kl-frost").count()) === 0, "datum zichtbaar");
    await ctx.close(); }

  // 5b. Openingsscherm: sneeuw over de film, daarna over naar de kaart
  { const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, bypassCSP: true }); const p = await ctx.newPage();
    await p.goto(`${base}/voorbeeld/kerstmagie/?gelegenheid=kerst`, { waitUntil: "load" }); await p.waitForTimeout(2500);
    const n = await ink(p, ".kl-snow--cover");
    check("Sneeuw op het openingsscherm", n > 20, `getekende punten: ${n}`);
    const zc = await p.evaluate(() => ({ snow: +getComputedStyle(document.querySelector(".kl-snow--cover")).zIndex, tekst: +getComputedStyle(document.querySelector(".kl-cover__center")).zIndex }));
    check("Sneeuw op het openingsscherm ligt onder de knop en tekst", zc.snow < zc.tekst, JSON.stringify(zc));
    await p.click("[data-kl-finish]", { force: true }); await p.waitForTimeout(3500);
    check("Na het openen loopt de sneeuw op de kaart", (await ink(p, ".kl-snow--page")) > 20 && (await ink(p, ".kl-snow--cover")) <= 0, "kaart ja, openingsscherm nee");
    await ctx.close(); }

  // 5c. Tekst op het ijs (kopregel 'Kras het ijs weg' en de knop) op de echte pixels, op drie schermformaten
  for (const [name, w, h] of [["360", 360, 640], ["390", 390, 844], ["1366", 1366, 768]]) {
    const { ctx, p } = await open({ viewport: { width: w, height: h } });
    await p.evaluate(() => document.querySelectorAll(".kl-snow,.inv-banner,.fx-toggle,.music").forEach((e) => (e.style.display = "none")));
    for (const [sel, label] of [[".kl-frost__hint", "hint"], [".kl-frost__btn", "knop"]]) {
      await p.evaluate((q) => { const e = document.querySelector(q); e.style.color = "transparent"; e.style.textDecorationColor = "transparent"; e.style.transition = "none"; document.querySelector(".kl-frost__hint").style.opacity = q.includes("hint") ? "1" : ""; }, sel);
    }
    await p.evaluate(() => document.querySelectorAll(".kl-frost__hint,.kl-frost__btn").forEach((e) => { const r = document.createRange(); r.selectNodeContents(e); const b = r.getBoundingClientRect(); e.dataset.b = [b.x, b.y, b.width, b.height].join(","); }));
    const shot = readPng(await p.screenshot());
    for (const [sel, label] of [[".kl-frost__hint", "hint"], [".kl-frost__btn", "knop"]]) {
      const [bx, by, bw, bh] = (await p.evaluate((q) => document.querySelector(q).dataset.b, sel)).split(",").map(Number);
      const yf = lum(8, 23, 58); let worst = Infinity;
      for (let y = Math.max(0, Math.floor(by)); y < Math.min(shot.height, Math.ceil(by + bh)); y++) for (let x = Math.max(0, Math.floor(bx)); x < Math.min(shot.width, Math.ceil(bx + bw)); x++) { const i = (y * shot.width + x) * shot.bpp, yb = lum(shot.px[i], shot.px[i + 1], shot.px[i + 2]); worst = Math.min(worst, (Math.max(yb, yf) + 0.05) / (Math.min(yb, yf) + 0.05)); }
      check(`Tekst op het ijs (${label}) leesbaar op ${name}`, worst >= 4.5, `slechtste pixel ${worst.toFixed(1)}:1 (minimaal 4,5:1)`);
    }
    await ctx.close();
  }

  // 6. Belasting: beelden per seconde op een vier keer vertraagde processor, met en zonder sneeuw, tijdens het scrollen
  { const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, deviceScaleFactor: 2, bypassCSP: true }); const p = await ctx.newPage();
    await p.goto(URL, { waitUntil: "load" }); await p.waitForTimeout(3200);
    const client = await ctx.newCDPSession(p); await client.send("Emulation.setCPUThrottlingRate", { rate: 4 });
    const meet = async () => p.evaluate(async () => new Promise((done) => { let n = 0, t0 = performance.now(), worst = 0, last = t0; const h = document.documentElement.scrollHeight - innerHeight; const loop = (t) => { n++; worst = Math.max(worst, t - last); last = t; scrollTo(0, ((t - t0) / 3000) * h * 0.5); if (t - t0 < 3000) requestAnimationFrame(loop); else done({ fps: Math.round(n / ((t - t0) / 1000)), worst: Math.round(worst) }); }; requestAnimationFrame(loop); }));
    const met = await meet();
    await p.click("[data-fx-toggle]"); await p.evaluate(() => scrollTo(0, 0)); await p.waitForTimeout(500);
    const zonder = await meet();
    console.log(`info   belasting op 4x vertraagde processor, scrollend: met sneeuw ${met.fps} beelden/s (langste beeld ${met.worst} ms), zonder sneeuw ${zonder.fps} beelden/s (${zonder.worst} ms)`);
    check("Sneeuw kost weinig beelden per seconde", met.fps >= zonder.fps * 0.8 || met.fps >= 30, `${met.fps} tegen ${zonder.fps}`);
    await ctx.close(); }

  await browser.close();
  console.log(bad ? `${bad} controle(s) mislukt` : "Alle controles geslaagd");
  process.exit(bad ? 1 : 0);
})();
