// Contrast van de tekst op het raam van Kerstcoupé tegen de foto erachter (met de nachtblauwe waas, zoals de gast hem ziet).
// De gewone toegankelijkheidscontrole slaat tekst op een beeld over ([data-tekst-op-beeld]); deze meet de echte pixels.
// Per regel (groet, wens, afzender, namen, ondertitel, 'Lees verder'): de tekstkleur tegen de 2% slechtste
// achtergrondpixels in het vak van die regel, zonder de schaduw rond de letters, met het licht van het lampje en de kaarsen
// op volle sterkte (slechtste geval) en zonder sneeuw. Eis: 4,5:1, en 3:1 voor grote tekst (vanaf 24 pixels).
// De laatste regel geeft de slechtste waarde gedeeld door de eis (1 of meer is goed).
// Gebruik (vanuit de projectmap, server in testmodus):
//   node e2e/coupe.cjs http://127.0.0.1:8000 [390x844,360x740,768x1024,1366x900] [pad,pad,...]
// Zonder paden: het voorbeeld. Geef ook de testuitnodigingen uit e2e/fixtures.py mee (lange namen, andere gelegenheden),
// bijvoorbeeld /u/familie-vandenbroucke-hoogeveen-xxxxx/.
const { chromium } = require("playwright");
const [base = "http://127.0.0.1:8000", sizes = "390x844,360x740,768x1024,1366x900", paths = ""] = process.argv.slice(2);
const pages = paths ? paths.split(",") : ["/voorbeeld/kerstcoupe/"];
const SELECTOR = ".kc-greet, .kc-wish, .kc-names, .kc-members, .kc-tagline, .kc-scroll";
(async () => {
  const browser = await chromium.launch();
  let worstAll = 99;
  for (const size of sizes.split(",")) {
    const [w, h] = size.split("x").map(Number);
    for (const url of pages) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, reducedMotion: "reduce", bypassCSP: true });
      const p = await ctx.newPage();
      await p.goto(base + url + (url.includes("#") ? "" : "#uitnodiging"), { waitUntil: "networkidle" });
      await p.evaluate(async () => { await document.fonts.ready; document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0); });
      // Licht op volle sterkte, geen sneeuw en geen knoppen in beeld.
      await p.addStyleTag({ content: ".kc-glow { opacity: .7 !important; animation: none !important; } .fx-slot, .fx-toggle, .music { display: none !important; }" });
      await p.waitForTimeout(400);
      const lines = await p.evaluate((sel) => [...document.querySelectorAll(sel)].map((el) => {
        const r = document.createRange();
        r.selectNodeContents(el);
        const rects = [...r.getClientRects()].filter((q) => q.width > 2).map((q) => [q.left, q.top, q.width, q.height]);
        const cs = getComputedStyle(el);
        const c = cs.color.match(/\d+(\.\d+)?/g).map(Number).slice(0, 3);
        const fs = parseFloat(cs.fontSize);
        return { cls: el.className.split(" ")[0].replace("kc-", ""), rects, color: c, large: fs >= 24 || (fs >= 18.66 && +cs.fontWeight >= 700) };
      }), SELECTOR);
      // De letters onzichtbaar maken, de waas en de achtergrond van 'Lees verder' blijven staan.
      await p.addStyleTag({ content: `${SELECTOR.split(",").map((s) => s.trim() + ", " + s.trim() + " *").join(", ")} { color: transparent !important; text-shadow: none !important; } .kc-scroll svg { visibility: hidden; }` });
      await p.waitForTimeout(150);
      const shot = await p.screenshot({ type: "png" });
      const res = await p.evaluate(async ([b64, lines]) => {
        const img = new Image();
        img.src = "data:image/png;base64," + b64;
        await img.decode();
        const c = document.createElement("canvas");
        c.width = img.width; c.height = img.height;
        const g = c.getContext("2d");
        g.drawImage(img, 0, 0);
        const lum = ([r, gg, b]) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(gg) + 0.0722 * f(b); };
        const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
        return lines.map((line) => {
          const ratios = [];
          for (const [x, y, rw, rh] of line.rects) {
            const X = Math.max(0, Math.round(x)), Y = Math.max(0, Math.round(y));
            const W = Math.min(img.width - X, Math.round(rw)), H = Math.min(img.height - Y, Math.round(rh));
            if (W < 1 || H < 1) continue;
            const d = g.getImageData(X, Y, W, H).data;
            for (let i = 0; i < d.length; i += 4) ratios.push(ratio(line.color, [d[i], d[i + 1], d[i + 2]]));
          }
          ratios.sort((a, b) => a - b);
          return { p2: ratios[Math.floor(ratios.length * 0.02)], min: ratios[0] };
        });
      }, [shot.toString("base64"), lines]);
      const out = [];
      lines.forEach((line, i) => {
        const { p2, min } = res[i];
        if (p2 === undefined) return;
        const need = line.large ? 3 : 4.5;
        worstAll = Math.min(worstAll, p2 / need);
        out.push(`${line.cls} ${p2.toFixed(2)} (min ${min.toFixed(2)}, nodig ${need})${p2 < need ? " <<<" : ""}`);
      });
      console.log(`${size} ${url.padEnd(44)} ${out.join(" | ")}`);
      await ctx.close();
    }
  }
  console.log("slechtste verhouding tegenover de eis (1 of meer is goed):", worstAll.toFixed(2));
  await browser.close();
})();
