// Wat gaat er echt naar Microsoft als iemand in de Studio zijn kaart invult? Met het échte Clarity-script (lokale kopie van tag en
// clarity.js in de map van het tweede argument); alle verzoeken naar clarity.ms en bing.com worden onderschept, er gaat niets naar
// Microsoft. We vullen Gegevens en Praktische info met herkenbare testwaarden, pakken elk collect-pakket uit en zoeken die waarden.
// Clarity neemt ook de kaders met de live kaart mee; hun <title> schermt Clarity niet af (daarom heeft een voorbeeld in de Studio
// een neutrale titel, invitations/render.py: STUDIO_TITEL).
// Gebruik (server met VIERLIEF_CLARITY_ID): NODE_PATH=<playwright> node e2e/clarity_studio_pakketten.cjs <basis-url> <map> [chromium|firefox|webkit]
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
const GEHEIM = ["Annemieke", "Bartholomeus", "Geheimstraat", "Teststad", "Kasteel Testhof", "Geheime welkomsttekst",
                "Geheime Carla", "0612345678", "geheim.contact@example.com", "Geheime afsluiting"];

function uitpakken(buf) {
  if (!buf) return "";
  try { return zlib.gunzipSync(buf).toString(); } catch (e) { return buf.toString(); }
}

(async () => {
  const b = await TYPE.launch();
  const c = await b.newContext({ viewport: { width: 1366, height: 900 } });
  const p = await c.newPage();
  const pakketten = [];
  await c.route(/clarity\.ms|bing\.com/, (route) => {
    const u = route.request().url();
    if (/\/tag\//.test(u)) return route.fulfill({ status: 200, contentType: "application/javascript", body: TAG });
    if (/clarity\.js/.test(u)) return route.fulfill({ status: 200, contentType: "application/javascript", body: SCRIPT });
    if (/collect/.test(u)) pakketten.push(uitpakken(route.request().postDataBuffer()));
    return route.fulfill({ status: 204, body: "" });
  });

  await p.goto(BASIS + "/ontwerpen/", { waitUntil: "load" });
  await p.locator('[data-toestemming-keuze="ja"]').click();
  await p.goto(BASIS + "/maken/?ontwerp=ja-woord&gelegenheid=verloving&soort=uitnodiging&direct=1", { waitUntil: "load" });
  await p.waitForURL(/\/gegevens\//, { timeout: 15000 });
  const vul = async (n, w) => { await p.locator(`[name="${n}"]`).fill(w); await p.waitForTimeout(150); };
  await vul("name_partner_1", "Geheime Annemieke"); await vul("name_partner_2", "Geheime Bartholomeus");
  await vul("venue_name", "Kasteel Testhof"); await vul("address", "Geheimstraat 12, 1234 AB Teststad");
  await vul("welcome_text", "Geheime welkomsttekst voor de gasten");
  await p.waitForTimeout(2500);                                        // de live kaart ververst en Clarity verstuurt
  await p.locator("button[name=actie][value=volgende]").first().click();
  await p.waitForURL(/\/programma\//, { timeout: 15000 });
  await p.evaluate(() => document.querySelectorAll("details.studio-deel").forEach((d) => { d.open = true; }));
  await vul("contact_name", "Geheime Carla"); await vul("contact_phone", "0612345678");
  await vul("contact_email", "geheim.contact@example.com"); await vul("closing_text", "Geheime afsluiting");
  await p.waitForTimeout(2500);
  await p.locator("button[name=actie][value=volgende]").first().click();
  await p.waitForURL(/\/aanmelden\//, { timeout: 15000 });
  await p.waitForTimeout(3000);

  const alles = pakketten.join("\n");
  const kaderTitels = [...new Set([...alles.matchAll(/"([^"]{2,80} · (?:uitnodiging|wenskaart|kerstkaart|VAYLIDE))"/g)].map((m) => m[1]))];
  ok("Clarity verstuurde pakketten (met het kader van de live kaart)", pakketten.length > 3 && /inv-colophon|data-fx-slot/.test(alles), `${pakketten.length} pakketten`);
  const gevonden = GEHEIM.filter((g) => alles.includes(g));
  ok("geen enkele testwaarde leesbaar in de pakketten", gevonden.length === 0, gevonden.join(", "));
  ok("het kader van de live kaart heeft de neutrale titel", alles.includes('"Voorbeeld · VAYLIDE"') && !kaderTitels.some((t) => /Annemieke|Bartholomeus/.test(t)), kaderTitels.join(" | "));
  await b.close();
  console.log(fouten ? `${fouten} FOUT` : "ALLES OK");
  process.exit(fouten ? 1 : 0);
})().catch((e) => { console.log("TESTFOUT", String(e).slice(0, 300)); process.exit(2); });
