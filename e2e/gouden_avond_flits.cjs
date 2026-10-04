// Gouden Avond: geen zwarte flits als de deuren de video onthullen. Neemt in rap tempo schermafbeeldingen van het portaal tussen 2,3 en 4,3 s na de tik en meet de gemiddelde helderheid.
const { chromium } = require("playwright");
const [base] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  for (const w of [390, 1366]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: w < 800 ? 844 : 768 } }); const page = await ctx.newPage();
    await page.goto(base + "/voorbeeld/gouden-avond/?gelegenheid=bruiloft", { waitUntil: "load" }); await page.waitForTimeout(2500);
    const box = await page.locator("[data-bc-portal]").boundingBox();
    await page.locator("[data-bc-sleutel]").click(); const t0 = Date.now();
    const maten = [];
    while (Date.now() - t0 < 4600) {
      const t = Date.now() - t0;
      if (t < 2200) { await page.waitForTimeout(100); continue; }
      const buf = await page.screenshot({ clip: { x: box.x + box.width * 0.3, y: box.y + box.height * 0.15, width: box.width * 0.4, height: box.height * 0.5 }, type: "jpeg", quality: 60 });
      const g = await page.evaluate(async (b64) => { const i = new Image(); i.src = "data:image/jpeg;base64," + b64; await i.decode(); const c = document.createElement("canvas"); c.width = 40; c.height = 40; const x = c.getContext("2d"); x.drawImage(i, 0, 0, 40, 40); const d = x.getImageData(0, 0, 40, 40).data; let s = 0; for (let k = 0; k < d.length; k += 4) s += 0.2126 * d[k] + 0.7152 * d[k + 1] + 0.0722 * d[k + 2]; return s / 1600; }, buf.toString("base64"));
      maten.push([t, Math.round(g)]);
    }
    console.log(w, "helderheid (0-255) per moment:", maten.map((m) => `${m[0]}ms:${m[1]}`).join("  "));
    console.log(w, "donkerste:", Math.min(...maten.map((m) => m[1])), " (zwart zou < 25 zijn)");
    await ctx.close();
  }
  await browser.close();
})();
