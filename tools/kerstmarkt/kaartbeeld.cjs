// Kerstmarkt: het kaartbeeld voor de collectie (static/img/designs/kerstmarkt.webp, 800 × 1000).
// De ster en de kaart zijn samen iets hoger dan 4:5 breed is. Daarom de geopende kop in een venster van 4:5 (640 × 800):
// het beeldvak (9:16) staat dan in het midden, met de vage kerstmarkt ernaast, zoals op een computer.
// Gebruik (vanuit de projectmap, ontwikkelserver op :8000):
//   node tools/kerstmarkt/kaartbeeld.cjs http://127.0.0.1:8000 /tmp/kerstmarkt.png
//   .venv/bin/python -c "from PIL import Image; Image.open('/tmp/kerstmarkt.png').convert('RGB').save('static/img/designs/kerstmarkt.webp', quality=80, method=6)"
const { chromium } = require("playwright");

(async () => {
  const [base, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 640, height: 800 }, deviceScaleFactor: 1.25, bypassCSP: true });
  const page = await context.newPage();
  await page.goto(`${base}/voorbeeld/kerstmarkt/#uitnodiging`, { waitUntil: "networkidle" });
  await page.addStyleTag({ content: ".inv-banner, .music, .fx-toggle, .km-scroll { display: none !important; } :root { --km-bar: 0px !important; } .inv-main:focus { outline: none !important; }" });
  await page.evaluate(async () => { await document.fonts.ready; window.dispatchEvent(new Event("resize")); window.scrollTo(0, 0); });
  // Wachten tot de sneeuw (effects.js) goed in beeld is, dan alles stil.
  await page.waitForTimeout(2600);
  await page.addStyleTag({ content: "*, *::before, *::after { animation-play-state: paused !important; }" });
  await page.screenshot({ path: out });
  await browser.close();
  console.log("ok", out);
})();
