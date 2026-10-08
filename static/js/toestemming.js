/* Toestemming voor bezoekersanalyse (Microsoft Clarity). Alleen geladen als VIERLIEF_CLARITY_ID is ingesteld (templates/base.html).
   - Zonder keuze of na Weigeren laadt Clarity niet: geen script, geen cookies, ook geen cookieloze meting.
   - Na Accepteren laadt Clarity één keer, asynchroon, en krijgt het via consentv2: analytics_Storage granted, ad_Storage denied.
   - Intrekken (via Cookie-instellingen): consentv2 met beide op denied als Clarity al geladen was (Clarity wist dan zijn cookies en
     beëindigt de sessie), de Clarity-cookies wissen we zelf ook, en de pagina laadt opnieuw zonder Clarity.
   De keuze staat in de noodzakelijke cookie vaylide_analytics (12 maanden). Zie core/analytics.py en docs/CLARITY.md. */
(function () {
  "use strict";
  var banner = document.querySelector("[data-toestemming]");
  if (!banner) return;
  var COOKIE = "vaylide_analytics";
  var JAAR = 365 * 24 * 60 * 60;
  var id = banner.getAttribute("data-clarity-id") || "";
  var hier = banner.getAttribute("data-clarity-hier") === "1";      // mag Clarity op deze pagina draaien?

  function keuze() {
    var m = document.cookie.match(/(?:^|;\s*)vaylide_analytics=(ja|nee)(?:;|$)/);
    return m ? m[1] : "";
  }
  function bewaar(waarde) {
    document.cookie = COOKIE + "=" + waarde + "; Max-Age=" + JAAR + "; Path=/; SameSite=Lax" + (location.protocol === "https:" ? "; Secure" : "");
  }
  function heeft(naam) { return new RegExp("(?:^|;\\s*)" + naam + "=").test(document.cookie); }
  function wisClarityCookies() {
    // _clck en _clsk staan op deze site (eventueel op het hoofddomein). Alleen wissen wat er echt staat, eerst zonder domein, dan per domein;
    // cookies van Microsoft op clarity.ms of bing.com kan deze site niet wissen (Clarity ruimt die zelf op bij 'denied').
    var host = location.hostname, pogingen = [""];
    if (!/^[\d.]+$/.test(host) && host.indexOf(":") < 0) {
      var delen = host.split(".");
      for (var i = 0; i < delen.length - 1; i++) pogingen.push("." + delen.slice(i).join("."));
    }
    ["_clck", "_clsk"].forEach(function (naam) {
      for (var j = 0; j < pogingen.length && heeft(naam); j++) {
        document.cookie = naam + "=; Max-Age=0; Path=/" + (pogingen[j] ? "; Domain=" + pogingen[j] : "");
      }
    });
  }
  function maskeer() {
    // Extra zekerheid naast de attributen in de templates: alles waar een klant of gast iets in kan typen of kiezen, meldingen en kaartframes.
    document.querySelectorAll("form, input, textarea, select, iframe, [data-gevoelig], .flash-wrap").forEach(function (el) {
      el.setAttribute("data-clarity-mask", "True");
    });
  }
  function laadClarity() {
    if (!id || !hier || window.__vaylideClarity) return;      // maximaal één keer per pagina
    window.__vaylideClarity = true;
    maskeer();
    window.clarity = window.clarity || function () { (window.clarity.q = window.clarity.q || []).push(arguments); };
    // De toestemming gaat vóór het eerste gegeven mee: Clarity verwerkt de wachtrij op volgorde.
    window.clarity("consentv2", { ad_Storage: "denied", analytics_Storage: "granted" });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.clarity.ms/tag/" + encodeURIComponent(id);
    document.head.appendChild(s);
  }
  function toon(open) {
    banner.hidden = !open;
    var huidige = keuze();
    banner.querySelectorAll("[data-toestemming-keuze]").forEach(function (knop) {
      knop.setAttribute("aria-pressed", knop.getAttribute("data-toestemming-keuze") === huidige ? "true" : "false");
    });
    var status = banner.querySelector("[data-toestemming-status]");
    if (status) status.textContent = huidige === "ja" ? "Je gaf toestemming." : huidige === "nee" ? "Je weigerde de meting." : "";
    if (open) { var eerste = banner.querySelector("[data-toestemming-keuze]"); if (eerste && huidige) eerste.focus({ preventScroll: true }); }
  }

  banner.querySelectorAll("[data-toestemming-keuze]").forEach(function (knop) {
    knop.addEventListener("click", function () {
      var nieuw = knop.getAttribute("data-toestemming-keuze");
      var was = keuze();
      bewaar(nieuw);
      toon(false);
      if (nieuw === "ja") { laadClarity(); return; }
      // Weigeren of intrekken
      wisClarityCookies();
      if (window.__vaylideClarity && typeof window.clarity === "function") {
        window.clarity("consentv2", { ad_Storage: "denied", analytics_Storage: "denied" });
        // Een geladen script kan niet worden verwijderd: de pagina opnieuw laden stopt elke verdere meting.
        window.setTimeout(function () { wisClarityCookies(); location.reload(); }, 400);
      } else if (was === "ja") {
        wisClarityCookies();
      }
    });
  });
  document.querySelectorAll("[data-cookie-instellingen]").forEach(function (link) {
    link.hidden = false;
    link.addEventListener("click", function (e) { e.preventDefault(); toon(true); });
  });

  var nu = keuze();
  if (nu === "ja") laadClarity();
  else if (nu === "nee") wisClarityCookies();
  else if (hier) toon(true);                                // alleen vragen waar Clarity ook echt zou draaien
})();
