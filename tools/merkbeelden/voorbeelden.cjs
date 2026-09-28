// Maakt de tegels per gelegenheid en de voorbeeldkaart van de homepage uit de echte
// voorbeelduitnodigingen (fictieve evenementen). Start eerst de ontwikkelserver.
// Gebruik: node tools/merkbeelden/voorbeelden.cjs [basis-url] [kerst]   (standaard http://127.0.0.1:8000)
// Met 'kerst' alleen de kerstbeelden (tegel-kerst.webp en de brede gelegenheid-kerst.webp, op een lichte achtergrond).
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE = process.argv[2] || "http://127.0.0.1:8000";
const ONLY_KERST = process.argv[3] === "kerst";
const OUT = path.resolve(__dirname, "../../static/img/site");
// gelegenheid, ontwerp, kleur, openen?
// Per gelegenheid een licht ontwerp dat ervoor gemaakt is (geen donkere kaarten op de homepage).
const TILES = [
  ["bruiloft", "eucalyptus", "salie", true],
  ["verloving", "ja-woord", "champagne", true],
  ["verjaardag", "ballonfeest", "pastel", true],
  ["jubileum", "lauwerkrans", "goud", true],
  ["babyshower", "stipjes", "roze", true],
  ["zakelijk", "borrel", "koraal", true],
];
const HIDE = ".lp-cover__hint,.lp-cover__music,.ag-cover__hint,.ag-cover__music,.pm-open,.a-cover__hint,.a-cover__music,.music{display:none!important}";

async function toWebp(page, png, width, height, quality) {
  const data = await page.evaluate(async ([b64, w, h, q]) => {
    const img = new Image();
    img.src = "data:image/png;base64," + b64;
    await img.decode();
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    const ctx = c.getContext("2d");
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(img, 0, 0, w, h);
    return c.toDataURL("image/webp", q);
  }, [png.toString("base64"), width, height, quality]);
  return Buffer.from(data.split(",")[1], "base64");
}

async function shoot(context, url, open, size) {
  const page = await context.newPage();
  await page.goto(url, { waitUntil: "networkidle" });
  if (open === "telefoon") {
    // Voorvertoning van het live voorbeeld: precies zoals het in de telefoon staat, dus niets verbergen.
    await page.waitForTimeout(800);
    const png = await page.screenshot({ type: "png" });
    const webp = await toWebp(page, png, 540, 1152, 0.8);
    await page.close();
    return webp;
  }
  if (open) {
    await page.evaluate(() => document.querySelector("[data-open]").click());
    await page.waitForTimeout(2500);
    // Na het openen krijgt de kop de focus (voor toetsenbord en schermlezer); geen focusrand in de afbeelding.
    await page.evaluate(() => { window.scrollTo(0, 0); if (document.activeElement) document.activeElement.blur(); });
  }
  await page.addStyleTag({ content: HIDE });
  await page.waitForTimeout(500);
  const png = await page.screenshot({ type: "png" });
  size = size || (open === "kaart" ? [500, 800, 0.82] : open === "telefoon" ? [540, 1152, 0.8] : [560, 350, 0.8]);
  const webp = await toWebp(page, png, ...size);
  await page.close();
  return webp;
}

(async () => {
  const browser = await chromium.launch();
  // CSP van de voorbeeldpagina's staat geen extra stijlregels toe; alleen voor deze schermafbeeldingen uitgezet.
  const wide = await browser.newContext({ viewport: { width: 720, height: 450 }, reducedMotion: "reduce", bypassCSP: true });
  for (const [occasion, slug, palette, open] of ONLY_KERST ? [] : TILES) {
    const file = path.join(OUT, `gelegenheid-${occasion}.webp`);
    fs.writeFileSync(file, await shoot(wide, `${BASE}/voorbeeld/${slug}/?gelegenheid=${occasion}&kleur=${palette}&embed=1`, open));
    console.log(path.relative(process.cwd(), file), fs.statSync(file).size, "bytes");
  }
  // Staande themakaarten voor de homepage (boogvorm, 400 x 500), Kerst voorop met de geopende kerstkaart.
  const staand = await browser.newContext({ viewport: { width: 400, height: 500 }, deviceScaleFactor: 1.5, reducedMotion: "reduce", bypassCSP: true });
  for (const [occasion, slug, palette, open] of ONLY_KERST ? [["kerst", "winterlicht", "hulst", true]] : [["kerst", "winterlicht", "hulst", true], ...TILES]) {
    const file = path.join(OUT, `tegel-${occasion}.webp`);
    fs.writeFileSync(file, await shoot(staand, `${BASE}/voorbeeld/${slug}/?gelegenheid=${occasion}&kleur=${palette}&embed=1`, open, [400, 500, 0.8]));
    console.log(path.relative(process.cwd(), file), fs.statSync(file).size, "bytes");
  }
  await staand.close();
  // Kerst: een brede tegel (onder de zes gewone) met de envelop en de geopende kerstkaart naast elkaar.
  const kerst = await browser.newContext({ viewport: { width: 390, height: 720 }, deviceScaleFactor: 2, reducedMotion: "reduce", bypassCSP: true });
  const shotKerst = async (kleur, open) => {
    const page = await kerst.newPage();
    await page.goto(`${BASE}/voorbeeld/winterlicht/?kleur=${kleur}&embed=1`, { waitUntil: "networkidle" });
    if (open) {
      await page.evaluate(() => document.querySelector("[data-open]").click());
      await page.waitForTimeout(1200);
      await page.evaluate(() => { window.scrollTo(0, 0); if (document.activeElement) document.activeElement.blur(); });
    }
    await page.addStyleTag({ content: HIDE + ".wl-cover__text,.wl-scroll,.fx-toggle{display:none!important}" });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(600);
    const png = await page.screenshot({ type: "png" });
    await page.close();
    return png.toString("base64");
  };
  const envelop = await shotKerst("hulst", false);
  const kaartKerst = await shotKerst("winternacht", true);
  const helper = await kerst.newPage();
  const tile = await helper.evaluate(async ([a, b]) => {
    const load = async (b64) => { const i = new Image(); i.src = "data:image/png;base64," + b64; await i.decode(); return i; };
    const [env, card] = [await load(a), await load(b)];
    const c = document.createElement("canvas");
    c.width = 1200; c.height = 520;
    const g = c.getContext("2d");
    const bg = g.createLinearGradient(0, 0, 1200, 520);
    bg.addColorStop(0, "#FBF1E4"); bg.addColorStop(0.55, "#F3DFC8"); bg.addColorStop(1, "#E9CDB0");
    g.fillStyle = bg; g.fillRect(0, 0, 1200, 520);
    let s = 7;
    const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
    for (let i = 0; i < 60; i++) {
      const x = rnd() * 1200, y = rnd() * 520, r = 6 + rnd() * 26;
      const rg = g.createRadialGradient(x, y, 0, x, y, r);
      rg.addColorStop(0, `rgba(214,${150 + Math.round(rnd() * 40)},80,${0.16 + rnd() * 0.22})`);
      rg.addColorStop(1, "rgba(255,190,120,0)");
      g.fillStyle = rg; g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
    }
    const glow = g.createRadialGradient(600, 260, 20, 600, 260, 520);
    glow.addColorStop(0, "rgba(255,200,130,0.22)"); glow.addColorStop(1, "rgba(255,200,130,0)");
    g.fillStyle = glow; g.fillRect(0, 0, 1200, 520);
    const place = (img, cx, cy, h, angle) => {
      const w = h * img.naturalWidth / img.naturalHeight;
      g.save();
      g.translate(cx, cy);
      g.rotate(angle);
      g.shadowColor = "rgba(90,50,20,0.4)"; g.shadowBlur = 40; g.shadowOffsetY = 18;
      g.fillStyle = "#000"; g.fillRect(-w / 2, -h / 2, w, h);
      g.shadowColor = "transparent";
      g.drawImage(img, -w / 2, -h / 2, w, h);
      g.restore();
    };
    place(env, 470, 262, 470, -0.07);
    place(card, 730, 258, 480, 0.05);
    return c.toDataURL("image/webp", 0.82);
  }, [envelop, kaartKerst]);
  await helper.close();
  const kerstFile = path.join(OUT, "gelegenheid-kerst.webp");
  fs.writeFileSync(kerstFile, Buffer.from(tile.split(",")[1], "base64"));
  console.log(path.relative(process.cwd(), kerstFile), fs.statSync(kerstFile).size, "bytes");
  await kerst.close();
  if (ONLY_KERST) { await browser.close(); return; }
  const tall = await browser.newContext({ viewport: { width: 400, height: 640 }, deviceScaleFactor: 1.5, reducedMotion: "reduce", bypassCSP: true });
  const card = path.join(OUT, "kaart-voorbeeld.webp");
  fs.writeFileSync(card, await shoot(tall, `${BASE}/voorbeeld/liefde-op-papier/?gelegenheid=bruiloft&kleur=salie&embed=1`, "kaart"));
  console.log(path.relative(process.cwd(), card), fs.statSync(card).size, "bytes");
  // Scherm van de telefoon op de homepage (270 x 576 beeldpunten), als voorvertoning tot het live voorbeeld laadt.
  const phone = await browser.newContext({ viewport: { width: 270, height: 576 }, deviceScaleFactor: 2, reducedMotion: "reduce" });
  const poster = path.join(OUT, "telefoon-voorbeeld.webp");
  fs.writeFileSync(poster, await shoot(phone, `${BASE}/voorbeeld/liefde-op-papier/?gelegenheid=bruiloft&kleur=blush&embed=1`, "telefoon"));
  console.log(path.relative(process.cwd(), poster), fs.statSync(poster).size, "bytes");
  await browser.close();
})();
