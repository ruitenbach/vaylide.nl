// Tekent de beelden van Aurora Nocturne met art.js in Chromium en schrijft ze naar designs/aurora-nocturne/v1/img/<thema>/.
// Gebruik (vanuit de projectmap):
//   node tools/aurora_nocturne/render.cjs                    alle vier de thema's (nacht, parel, roze, salie)
//   node tools/aurora_nocturne/render.cjs parel              alleen dit thema
//   node tools/aurora_nocturne/render.cjs parel preview      alleen de voorbeeldbeelden (donker en verlicht) in een tijdelijke map
// De korrel (papier van de envelop) is voor alle thema's gelijk en staat in img/korrel.webp.
// Voorbeeldbeelden komen in $AN_PREVIEW (standaard /tmp/aurora-preview), niet in de repository.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const IMG = path.join(ROOT, "designs", "aurora-nocturne", "v1", "img");
const PREVIEW = process.env.AN_PREVIEW || "/tmp/aurora-preview";
const THEMAS = ["nacht", "parel", "roze", "salie"];
const arg1 = process.argv[2] || "alles";
const gekozen = THEMAS.includes(arg1) ? [arg1] : THEMAS;
const preview = process.argv.includes("preview");

(async () => {
  fs.mkdirSync(PREVIEW, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 800, height: 600 } });
  page.on("pageerror", (e) => console.error("pageerror:", e.message));
  page.on("console", (m) => { if (m.type() === "error") console.error("console:", m.text()); });
  await page.setContent("<!doctype html><meta charset=utf-8><body></body>");
  await page.addScriptTag({ path: path.join(__dirname, "art.js") });

  const spec = {
    lucht: ["lucht", 0.8], auroraA: ["aurora-a", 0.75], auroraB: ["aurora-b", 0.75], ver: ["ver", 0.82], mist: ["mist", 0.55], paviljoen: ["paviljoen", 0.8],
    entree: ["licht-entree", 0.8], zij: ["licht-zij", 0.8], kroon: ["licht-kroon", 0.8], lampjes: ["licht-lampjes", 0.8], kaarsen: ["licht-kaarsen", 0.8],
    voorL: ["voor-l", 0.82], voorR: ["voor-r", 0.82], hoek: ["hoek", 0.82], slinger: ["slinger", 0.82],
  };
  for (const thema of gekozen) {
    const prev = await page.evaluate((thema) => {
      const A = window.AN, L = {};
      A.setTheme(thema);
      L.lucht = A.drawLucht(2400, 1350);
      L.auroraA = A.drawAurora(800, 450, "a");
      L.auroraB = A.drawAurora(800, 450, "b");
      L.ver = A.drawVer(2400, 1350);
      L.mist = A.drawMist(1200, 260);
      L.paviljoen = A.drawPaviljoen(true);
      L.entree = A.lichtEntree(); L.zij = A.lichtZij(); L.kroon = A.lichtKroon(); L.lampjes = A.lichtLampjes(); L.kaarsen = A.lichtKaarsen();
      L.voorL = A.drawVoor(600, 760, -1);
      L.voorR = A.drawVoor(600, 760, 1);
      L.hoek = A.drawHoek(560);
      L.slinger = A.drawSlinger(1400, 300);
      window.__L = L;
      return {
        donker: A.composePreview(L, 1600, 900, false).toDataURL("image/png"),
        licht: A.composePreview(L, 1600, 900, true).toDataURL("image/png"),
        hoek: L.hoek.toDataURL("image/png"),
        slinger: L.slinger.toDataURL("image/png"),
      };
    }, thema);
    for (const [k, v] of Object.entries(prev)) fs.writeFileSync(path.join(PREVIEW, `voorbeeld-${thema}-${k}.png`), Buffer.from(v.split(",")[1], "base64"));
    if (preview) { console.log(thema, "voorbeelden in", PREVIEW); continue; }
    const out = path.join(IMG, thema);
    fs.mkdirSync(out, { recursive: true });
    let totaal = 0;
    for (const [key, [name, q]] of Object.entries(spec)) {
      const data = await page.evaluate(([k, q]) => window.__L[k].toDataURL("image/webp", q), [key, q]);
      const buf = Buffer.from(data.split(",")[1], "base64");
      fs.writeFileSync(path.join(out, name + ".webp"), buf);
      totaal += buf.length;
      console.log(thema.padEnd(6), name.padEnd(14), Math.round(buf.length / 1024) + " KB");
    }
    console.log(thema.padEnd(6), "samen".padEnd(14), Math.round(totaal / 1024) + " KB");
  }
  if (!preview) {
    const korrel = await page.evaluate(() => window.AN.drawKorrel(112).toDataURL("image/webp", 0.9));
    fs.writeFileSync(path.join(IMG, "korrel.webp"), Buffer.from(korrel.split(",")[1], "base64"));
  }
  await browser.close();
})();
