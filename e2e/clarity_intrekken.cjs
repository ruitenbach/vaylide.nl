// Intrekken van toestemming met het échte Clarity-script: een lokale kopie van de tag en clarity.js (map als tweede argument). Alle
// verzoeken naar clarity.ms en bing.com worden onderschept; er gaat niets naar Microsoft. Uit elk collect-verzoek lezen we het bezoekers- en
// sessie-ID (envelop e[5] en e[6]). Na Weigeren mag er geen enkel verzoek meer naar Clarity gaan: geen laatste pakket en geen nieuwe sessie.
// Clarity plant na consentv2 'denied' zelf een herstart zonder cookies, met een nieuw ID (clarity-js, data/metadata.ts: consentv2).
// Gebruik (server met VIERLIEF_CLARITY_ID): NODE_PATH=<playwright> node e2e/clarity_intrekken.cjs <basis-url> <map> [chromium|firefox|webkit]
// De map vul je met: curl https://www.clarity.ms/tag/<id> > tag.js, en clarity.js van het adres dat in die tag staat.
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");
const { chromium, firefox, webkit } = require("playwright");
const BASIS = process.argv[2] || "http://127.0.0.1:8010";
const MAP = process.argv[3];
const NAAM = process.argv[4] || "chromium";
const TYPE = { chromium, firefox, webkit }[NAAM];
const TAG = fs.readFileSync(path.join(MAP, "tag.js"), "utf8");
const SCRIPT = fs.readFileSync(path.join(MAP, "clarity.js"), "utf8");
let fouten = 0; const ok = (n, w, e) => { if (!w) fouten++; console.log(`${w ? "OK  " : "FOUT"} [${NAAM}] ${n}${e ? " | " + e : ""}`); };

function envelop(buf) {
  if (!buf) return null;
  let tekst; try { tekst = zlib.gunzipSync(buf).toString(); } catch (e) { tekst = buf.toString(); }
  try { const j = JSON.parse(tekst); return j.e ? `${j.e[5]}/${j.e[6]}` : null; } catch (e) { return null; }
}

(async () => {
  const b = await TYPE.launch();
  const c = await b.newContext({ viewport: { width: 1366, height: 768 } });
  const p = await c.newPage();
  const verkeer = [];                     // [moment, soort, url, id]
  let geweigerd = Infinity;
  await c.route(/clarity\.ms|bing\.com/, (route) => {
    const r = route.request(); const u = r.url(); const t = Date.now();
    if (/\/tag\//.test(u)) { verkeer.push([t, "tag", u]); return route.fulfill({ status: 200, contentType: "application/javascript", body: TAG }); }
    if (/clarity\.js/.test(u)) { verkeer.push([t, "script", u]); return route.fulfill({ status: 200, contentType: "application/javascript", body: SCRIPT }); }
    verkeer.push([t, /collect/.test(u) ? "collect" : "anders", u, envelop(r.postDataBuffer())]);
    return route.fulfill({ status: 204, body: "" });
  });
  const blokkades = [];                   // pogingen die de browser zelf tegenhield (CSP)
  p.on("console", (m) => { if (/clarity\.ms/.test(m.text()) && /Content.Security.Policy|Content-Security-Policy/i.test(m.text())) blokkades.push([Date.now(), m.text().slice(0, 140)]); });
  const fout = []; p.on("pageerror", (e) => fout.push(String(e).slice(0, 140)));
  const na = (soort) => verkeer.filter((v) => v[0] >= geweigerd && (!soort || v[1] === soort));

  // 1. Accepteren en twee pagina's bezoeken: één bezoeker, één sessie.
  await p.goto(BASIS + "/ontwerpen/", { waitUntil: "load" });
  await p.locator('[data-toestemming-keuze="ja"]').click();
  await p.waitForTimeout(4000);
  await p.goto(BASIS + "/prijzen/", { waitUntil: "load" });
  await p.waitForTimeout(4000);
  const ids = [...new Set(verkeer.filter((v) => v[1] === "collect" && v[3]).map((v) => v[3]))];
  ok("met toestemming: Clarity meet, met één bezoeker en één sessie", verkeer.some((v) => v[1] === "collect") && ids.length === 1, ids.join(", "));
  const voor = (await c.cookies()).map((x) => x.name);
  ok("met toestemming: _clck en _clsk gezet", voor.includes("_clck") && voor.includes("_clsk"), voor.join(","));

  // 2. Intrekken via Cookie-instellingen → Weigeren.
  await p.locator("[data-cookie-instellingen]").first().click();
  geweigerd = Date.now();
  await Promise.all([p.waitForEvent("load", { timeout: 15000 }).catch(() => null), p.locator('[data-toestemming-keuze="nee"]').click()]);
  await p.waitForTimeout(5000);                                        // ruim langer dan Clarity's herstart (250 ms) en uploadvertraging (1 s)
  const nieuw = na("collect").map((v) => v[3] || "?");
  ok("na intrekken: geen enkel collect-verzoek meer (geen laatste pakket, geen nieuwe sessie)", nieuw.length === 0, nieuw.length ? `${nieuw.length}× met ${[...new Set(nieuw)].join(", ")} (was ${ids.join(", ")})` : "");
  ok("na intrekken: ook geen ander verzoek naar clarity.ms of bing.com", na().length === 0, na().map((v) => v[1] + " " + v[2].slice(0, 60)).join(" | "));
  // Wat de pagina kan lezen en wat naar de server gaat. (WebKit op Windows bewaart op een IP-adres ook onzichtbare kopieën met een
  // onmogelijk domein zoals .0.1; die leest geen pagina en ze gaan niet mee. Op een echte domeinnaam gebeurt dat niet.)
  const leesbaar = await p.evaluate(() => document.cookie);
  ok("na intrekken: _clck en _clsk weg, keuze 'nee' bewaard", !/(^|;\s*)_cl(ck|sk)=/.test(leesbaar) && /vaylide_analytics=nee/.test(leesbaar), leesbaar);
  ok("na intrekken: Clarity niet meer op de herladen pagina", (await p.evaluate(() => !window.__vaylideClarity && !document.querySelector('script[src*="clarity.ms"]'))));

  // 3. Volgende pagina: niets, en de Clarity-cookies gaan ook niet meer mee naar de server.
  const [verzoek] = await Promise.all([p.waitForRequest((r) => r.url().startsWith(BASIS + "/ontwerpen/")), p.goto(BASIS + "/ontwerpen/", { waitUntil: "load" })]);
  const kop = (await verzoek.allHeaders()).cookie || "";
  await p.waitForTimeout(2500);
  ok("volgende pagina na intrekken: geen verzoek naar Clarity, geen _clck/_clsk in de Cookie-kop", na().length === 0 && !/_cl(ck|sk)=/.test(kop), kop);
  ok("geen JS-fouten", fout.length === 0, fout.join(" | "));
  console.log(`info [${NAAM}] pogingen die de browser blokkeerde: ${blokkades.length}${blokkades.length ? " | " + blokkades.map((x) => x[1]).join(" | ") : ""}`);
  await b.close();
  console.log(fouten ? `${fouten} FOUT` : "ALLES OK");
  process.exit(fouten ? 1 : 0);
})();
