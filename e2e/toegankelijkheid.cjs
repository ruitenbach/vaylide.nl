// Toegankelijkheid van alle uitnodigingsontwerpen, in elke kleurvariant: dicht (openingsscherm) en geopend.
// - axe-core (WCAG 2.0/2.1, niveau A en AA);
// - contrast van tekst, ook op kleurverlopen (dat kan axe niet beoordelen), tegen de slechtste kleur in het verloop;
// - op het openingsscherm ook de decoratieve tekst die voor schermlezers verborgen is (die moet wel leesbaar zijn).
// Gebruik (vanuit de projectmap, server in testmodus):
//   npm install --no-save axe-core@4          (eenmalig; Playwright en Chromium zijn al nodig voor e2e/controle2.cjs)
//   node e2e/toegankelijkheid.cjs http://127.0.0.1:8000 /tmp/toegankelijkheid.json [code ...]
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [base, outFile, ...only] = process.argv.slice(2);
const axeSrc = fs.readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

function designs() {
  const root = path.join(process.cwd(), "designs");
  const out = {};
  for (const slug of fs.readdirSync(root).sort()) {
    if (slug.startsWith("_") || (only.length && !only.includes(slug))) continue;
    const versions = fs.readdirSync(path.join(root, slug)).filter((v) => /^v\d+$/.test(v)).sort((a, b) => parseInt(a.slice(1), 10) - parseInt(b.slice(1), 10));
    if (!versions.length) continue;
    const manifest = JSON.parse(fs.readFileSync(path.join(root, slug, versions[versions.length - 1], "manifest.json"), "utf8"));
    out[slug] = manifest.palettes.map((p) => p.key);
  }
  return out;
}

// Contrastcontrole in de pagina. Met decoratief=true telt ook tekst mee die aria-hidden is.
function check(decoratief) {
  const parse = (c) => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lum = ({ r, g, b }) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
  const blend = (fg, bg) => ({ r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 });
  const out = [];
  const onPhoto = [];
  for (const el of document.querySelectorAll("body *")) {
    const direct = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 1);
    if (!direct) continue;
    // Tekst op een getekend beeld (zoals het kerstraam van Winterlicht): die meet e2e/kerstraam.cjs op de echte pixels.
    if (el.closest("[data-tekst-op-beeld]")) { onPhoto.push(el.textContent.trim().replace(/\s+/g, " ").slice(0, 50)); continue; }
    if (el.closest(decoratief ? "script, style, noscript, .visually-hidden" : "script, style, noscript, [aria-hidden='true'], .visually-hidden")) continue;
    if (typeof el.checkVisibility === "function" && !el.checkVisibility({ opacityProperty: true, visibilityProperty: true })) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const cs = getComputedStyle(el);
    let fg = parse(cs.color);
    if (!fg || fg.a === 0) continue;
    const candidates = [];
    // Verloop dat in de letters zelf zit (background-clip: text, zoals de glans bij 'folie'):
    // die kleuren zijn tekstkleuren, geen achtergrond. Elke kleur moet genoeg contrast hebben.
    const fgs = [];
    let solid = null, photo = false;
    let stack = [];
    for (let n = el; n; n = n.parentElement) {
      const s = getComputedStyle(n);
      const bi = s.backgroundImage;
      if (bi && bi !== "none" && (s.backgroundClip === "text" || s.webkitBackgroundClip === "text")) {
        for (const m of bi.matchAll(/rgba?\([^)]+\)/g)) { const c = parse(m[0]); if (c && c.a >= 0.5) fgs.push(c); }
        continue;
      }
      if (bi && bi !== "none") {
        if (bi.includes("gradient")) {
          const stops = [...bi.matchAll(/rgba?\([^)]+\)/g)].map((m) => parse(m[0])).filter(Boolean);
          for (const c of stops) if (c.a >= 0.5) candidates.push(c);
          // Volledig dekkend verloop: wat eronder ligt is niet zichtbaar.
          if (stops.length && stops.every((c) => c.a >= 0.95) && !bi.includes("url(")) { solid = stops[0]; break; }
        } else if (n !== document.body && n !== document.documentElement) { photo = true; }
      }
      const bc = parse(s.backgroundColor);
      if (bc && bc.a >= 0.95) { solid = bc; break; }
      if (bc && bc.a > 0) stack.push(bc);
      // Tekst boven een foto (img als broer of zus in een positioneerd kader)
      if (n !== el && n.querySelector(":scope > img, :scope > picture, :scope > .ph, :scope > figure") && getComputedStyle(n).position !== "static") {
        const txtPos = getComputedStyle(el).position;
        if (n.querySelector(":scope > img, :scope > picture") && (s.position === "relative" || s.position === "absolute")) { /* mogelijk op foto */ }
      }
    }
    if (!solid) solid = { r: 255, g: 255, b: 255, a: 1 };
    // Halfdoorzichtige lagen samenvoegen boven de effen kleur.
    let bg = solid;
    for (const layer of stack.reverse()) bg = blend(layer, bg);
    const all = [bg, ...candidates.map((c) => (c.a < 1 ? blend(c, bg) : c))];
    let fgFinal = fg.a < 1 ? blend(fg, bg) : fg;
    let worst = Infinity, worstBg = null;
    for (const f of [fg, ...fgs]) {
      const ff = f.a < 1 ? blend(f, bg) : f;
      for (const c of all) { const q = ratio(ff, c); if (q < worst) { worst = q; worstBg = c; fgFinal = ff; } }
    }
    const size = parseFloat(cs.fontSize), weight = parseInt(cs.fontWeight, 10);
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const need = large ? 3 : 4.5;
    const text = el.textContent.trim().replace(/\s+/g, " ").slice(0, 50);
    const rgb = (c) => `rgb(${Math.round(c.r)},${Math.round(c.g)},${Math.round(c.b)})`;
    if (photo) { onPhoto.push(text); continue; }
    if (worst < need) out.push({ text, cls: (el.className || "").toString().slice(0, 40), fg: rgb(fgFinal), bg: rgb(worstBg), ratio: Math.round(worst * 100) / 100, need, size });
  }
  return { fails: out, onPhoto: [...new Set(onPhoto)].slice(0, 12) };
}

const results = [];
async function run(page, name, url, open) {
  await page.goto(base + url, { waitUntil: "networkidle" });
  // Na het openen wachten tot de entree van de kop klaar is (effects.js zet dan 'fx-done').
  // Na 3,3 s zijn de meeste openingen klaar; een opening als film (Rozenboog) duurt ruim 11 s.
  if (open && await page.$("[data-open]")) { await page.evaluate(() => document.querySelector("[data-open]").click()); await page.waitForTimeout(3300); await page.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 20000 }).catch(() => {}); await page.waitForFunction(() => !document.documentElement.classList.contains("fx") || document.documentElement.classList.contains("fx-done"), null, { timeout: 10000 }).catch(() => {}); await page.waitForTimeout(300); }
  await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 400) { window.scrollTo({ top: y, behavior: "instant" }); await new Promise((r) => setTimeout(r, 30)); } window.scrollTo(0, 0); });
  await page.waitForTimeout(700);
  // Wachten tot eenmalige animaties (onthullen, na elkaar invloeien) klaar zijn; doorlopende tellen niet mee.
  await page.waitForFunction(() => document.getAnimations().every((a) => a.playState !== "running" || a.effect.getTiming().iterations === Infinity), null, { timeout: 6000 }).catch(() => {});
  await page.evaluate(axeSrc);
  const violations = await page.evaluate(async () => {
    const res = await axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] } });
    return res.violations.map((v) => ({ id: v.id, count: v.nodes.length, nodes: v.nodes.slice(0, 4).map((n) => n.target.join(" ")) }));
  });
  const contrast = await page.evaluate(check, !open);
  results.push({ name, url, violations, contrast: contrast.fails });
  const bad = violations.length || contrast.fails.length;
  console.log(`${bad ? "LET OP" : "ok"} ${name}${violations.length ? " axe: " + violations.map((v) => `${v.id}(${v.count}) ${v.nodes.join(" ; ")}`).join(" | ") : ""}${contrast.fails.length ? " contrast: " + contrast.fails.map((f) => `"${f.text}" ${f.fg} op ${f.bg} = ${f.ratio} (nodig ${f.need})`).join("; ") : ""}`);
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ bypassCSP: true, viewport: { width: 390, height: 844 } });
  await ctx.addInitScript(() => { try { sessionStorage.clear(); } catch (e) { /* privémodus */ } });
  const page = await ctx.newPage();
  for (const [slug, keys] of Object.entries(designs())) {
    for (const k of keys) {
      await run(page, `${slug}-${k}-dicht`, `/voorbeeld/${slug}/?kleur=${k}`, false);
      await run(page, `${slug}-${k}-open`, `/voorbeeld/${slug}/?kleur=${k}`, true);
    }
  }
  fs.writeFileSync(outFile, JSON.stringify(results, null, 2));
  console.log(`\nPagina's: ${results.length}, met bevindingen: ${results.filter((r) => r.violations.length || r.contrast.length).length}`);
  await browser.close();
})();
