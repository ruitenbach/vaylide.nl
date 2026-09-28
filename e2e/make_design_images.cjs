// Maakt kaartafbeeldingen van de ontwerpen voor de collectie (800×1000).
// Gebruik (vanuit de projectmap, ontwikkelserver op :8000):
//   node e2e/make_design_images.cjs http://127.0.0.1:8000 static/img/designs [code ...]
// Zonder codes: alle ontwerpen in designs/. Van de eerste drie ontwerpen wordt het openingsscherm
// vastgelegd, van de Atelier-ontwerpen de geopende uitnodiging (daar zit de eigen kop met versiering),
// net als bij ontwerpen met "kaartbeeld": "open" in het manifest (Winterlicht: het kerstraam).
// Daarna de PNG's omzetten naar WebP en de PNG's verwijderen, bijvoorbeeld:
//   .venv/bin/python -c "import pathlib; from PIL import Image; [(Image.open(p).convert('RGB').save(p.with_suffix('.webp'), quality=80), p.unlink()) for p in pathlib.Path('static/img/designs').glob('*.png')]"
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

function designs() {
  const root = path.join(process.cwd(), "designs");
  const out = [];
  for (const slug of fs.readdirSync(root).sort()) {
    if (slug.startsWith("_")) continue;
    const versions = fs.readdirSync(path.join(root, slug)).filter((v) => /^v\d+$/.test(v)).sort((a, b) => parseInt(a.slice(1), 10) - parseInt(b.slice(1), 10));
    if (!versions.length) continue;
    const manifest = JSON.parse(fs.readFileSync(path.join(root, slug, versions[versions.length - 1], "manifest.json"), "utf8"));
    out.push({ slug, open: Boolean(manifest.atelier) || manifest.kaartbeeld === "open" });
  }
  return out;
}

(async () => {
  const [base, outDir, ...only] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  for (const { slug, open } of designs().filter((d) => !only.length || only.includes(d.slug))) {
    // Openingsscherm: 400×500 zoals bij de eerste ontwerpen; geopend: iets ruimer, zodat de kop in beeld is.
    const [w, h] = open ? [480, 600] : [400, 500];
    const context = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 800 / w, bypassCSP: true });
    const page = await context.newPage();
    await page.goto(`${base}/voorbeeld/${slug}/${open ? "#uitnodiging" : ""}`, { waitUntil: "networkidle" });
    await page.addStyleTag({ content: ":root { --inv-banner-h: 0px; } .inv-banner, .music, .fx-toggle, .wl-scroll { display: none !important; } *, *::before, *::after { animation-play-state: paused !important; }" });
    await page.evaluate(async () => { await document.fonts.ready; window.scrollTo(0, 0); });
    // Wachten tot de zwevende deeltjes (effects.js) goed in beeld zijn.
    await page.waitForTimeout(open ? 2200 : 1800);
    await page.screenshot({ path: `${outDir}/${slug}.png` });
    await context.close();
    console.log("ok", slug);
  }
  await browser.close();
})();
