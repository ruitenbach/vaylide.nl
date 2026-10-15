// Kerstmarkt: de filmopening en de overgang naar de kaart.
// 1. De drie paden van de opening, met het filmpje vertraagd in de browser:
//    - vooraf geladen: het filmpje speelt meteen, iets sneller dan normaal, en is klaar als het openingsscherm vervaagt;
//    - pas na de tik geladen, snel (zoals een iPhone vaak doet): het filmpje speelt, nog iets sneller;
//    - te traag (2,5 s): na 0,8 seconde verschijnt de kaart in een gloed (het eindbeeld vloeit over het eerste beeld).
// 2. Ligt de kaart in de kop precies op de kaart in het laatste filmbeeld? Op 390 × 844 en 1366 × 900: schermafbeeldingen
//    van de kop zonder kaart (het filmbeeld), met de kaart in de stand van het filmpje, en ter vergelijking met de kaart
//    3 pixels verschoven. Gemeten wordt het deel van de beeldpunten in een band rond de rand van de kaart dat duidelijk
//    verschilt van het filmbeeld. De echte stand moet minder dan half zoveel verschil geven als de verschoven stand.
// Gebruik (vanuit de projectmap, server in testmodus): node e2e/kerstmarkt.cjs http://127.0.0.1:8000 /tmp/kerstmarkt
const { chromium } = require("playwright");
const fs = require("fs");
const [base, out = "/tmp/kerstmarkt"] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const FILM_CARD = [[305, 413], [547, 409], [537, 820], [296, 805]];
let failures = 0;
const check = (name, ok, detail) => { if (!ok) failures++; console.log(`${ok ? "ok    " : "FOUT  "} ${name}: ${detail}`); };

async function path(b, name, delayMs, preload) {
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const p = await ctx.newPage();
  let tapped = false;
  await p.route(/markt(\.[0-9a-f]+)?\.(webm|mp4)/, async (route) => {
    if (!preload && !tapped) { await new Promise((r) => { const t = setInterval(() => { if (tapped) { clearInterval(t); r(); } }, 20); }); }
    if (delayMs) await new Promise((r) => setTimeout(r, delayMs));
    route.continue();
  });
  await p.goto(`${base}/voorbeeld/kerstmarkt/`, { waitUntil: "domcontentloaded" });
  await p.waitForTimeout(preload ? 2500 : 800);
  tapped = true;
  await p.click(".km-open");
  const t0 = Date.now();
  const log = [];
  for (const t of [400, 1200, 2500, 4300]) {
    const w = t - (Date.now() - t0); if (w > 0) await p.waitForTimeout(w);
    log.push(await p.evaluate((t) => {
      const c = document.querySelector(".km-cover"), v = document.querySelector("[data-km-film]");
      const end = (+getComputedStyle(c.querySelector(".km-frame__end")).opacity).toFixed(2);
      return { t, speelt: c.classList.contains("km-cover--speelt"), film: c.classList.contains("km-cover--film"), video: +v.currentTime.toFixed(2), rate: +v.playbackRate.toFixed(2), end: +end };
    }, t));
    if (t === 2500) await p.screenshot({ path: `${out}/pad-${name}.png` });
  }
  await p.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 8000 });
  const opened = Date.now() - t0;
  await ctx.close();
  return { log, opened };
}

async function alignment(b, width, height) {
  const ctx = await b.newContext({ viewport: { width, height }, bypassCSP: true });
  const p = await ctx.newPage();
  await p.goto(`${base}/voorbeeld/kerstmarkt/`, { waitUntil: "networkidle" });
  await p.waitForTimeout(600);
  // De kop met de kaart in de stand van het filmpje (het openingsscherm weg, maar nog 'has-cover').
  await p.addStyleTag({ content: ".km-cover { display: none !important; } .fx-slot, .fx-toggle, .music, .km-scroll, .km-halo { visibility: hidden !important; }" });
  await p.waitForTimeout(300);
  const card = (await p.screenshot()).toString("base64");
  await p.addStyleTag({ content: ".km-card { translate: 3px 3px; }" });
  await p.waitForTimeout(200);
  const moved = (await p.screenshot()).toString("base64");
  await p.addStyleTag({ content: ".km-card { visibility: hidden !important; }" });
  await p.waitForTimeout(200);
  const film = (await p.screenshot()).toString("base64");
  const frame = await p.evaluate(() => { const r = document.querySelector("[data-km-frame]").getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; });
  const pts = FILM_CARD.map(([x, y]) => [frame.x + x / 720 * frame.w, frame.y + y / 1280 * frame.h]);
  // Vergelijk in de pagina: een band van 8 pixels rond de rand van de kaart in het filmbeeld.
  const measure = (card) => p.evaluate(async ({ card, film, pts }) => {
    const load = (src) => new Promise((r) => { const i = new Image(); i.onload = () => r(i); i.src = "data:image/png;base64," + src; });
    const [a, f] = await Promise.all([load(card), load(film)]);
    const cv = document.createElement("canvas"); cv.width = a.width; cv.height = a.height;
    const ctx = cv.getContext("2d");
    ctx.drawImage(a, 0, 0); const da = ctx.getImageData(0, 0, cv.width, cv.height).data;
    ctx.drawImage(f, 0, 0); const df = ctx.getImageData(0, 0, cv.width, cv.height).data;
    const dist = (px, py, [x1, y1], [x2, y2]) => { const dx = x2 - x1, dy = y2 - y1, t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy))); return Math.hypot(px - x1 - t * dx, py - y1 - t * dy); };
    const xs = pts.map((q) => q[0]), ys = pts.map((q) => q[1]);
    let n = 0, off = 0;
    for (let y = Math.floor(Math.min(...ys) - 8); y < Math.max(...ys) + 8; y++) {
      for (let x = Math.floor(Math.min(...xs) - 8); x < Math.max(...xs) + 8; x++) {
        const d = Math.min(...pts.map((q, i) => dist(x, y, q, pts[(i + 1) % 4])));
        if (d > 8) continue;
        const k = (y * cv.width + x) * 4;
        n++;
        if (Math.abs(da[k] - df[k]) + Math.abs(da[k + 1] - df[k + 1]) + Math.abs(da[k + 2] - df[k + 2]) > 150) off++;
      }
    }
    return { n, off, share: off / n };
  }, { card, film, pts });
  const result = await measure(card);
  result.moved = (await measure(moved)).share;
  fs.writeFileSync(`${out}/uitlijning-${width}-kaart.png`, Buffer.from(card, "base64"));
  fs.writeFileSync(`${out}/uitlijning-${width}-film.png`, Buffer.from(film, "base64"));
  await ctx.close();
  return result;
}

(async () => {
  const b = await chromium.launch();
  const a = await path(b, "vooraf-geladen", 0, true);
  check("Filmpje vooraf geladen: speelt", a.log[1].film && a.log[1].video > 0.8 && a.log[3].video > 4.8 && a.log[1].rate >= 1.1 && a.log[1].rate <= 1.4,
    `${JSON.stringify(a.log)}, geopend na ${a.opened} ms`);
  const b2 = await path(b, "na-de-tik-snel", 150, false);
  check("Filmpje pas na de tik geladen: speelt", b2.log[2].film && b2.log[3].video > 4.6, `${JSON.stringify(b2.log)}, geopend na ${b2.opened} ms`);
  const c = await path(b, "te-traag", 2500, false);
  check("Filmpje te traag: kaart verschijnt in een gloed", !c.log[1].speelt && !c.log[1].film && c.log[3].end > 0.95, `${JSON.stringify(c.log)}, geopend na ${c.opened} ms`);
  for (const [w, h] of [[390, 844], [1366, 900]]) {
    const r = await alignment(b, w, h);
    check(`Kaart ligt op de kaart uit het filmpje (${w} × ${h})`, r.share < r.moved / 2,
      `rond de rand ${(r.share * 100).toFixed(1)}% van ${r.n} beeldpunten duidelijk anders; 3 pixels verschoven: ${(r.moved * 100).toFixed(1)}%`);
  }
  await b.close();
  console.log(`\nControles: ${failures ? "met fouten" : "alles ok"}`);
  process.exitCode = failures ? 1 : 0;
})();
