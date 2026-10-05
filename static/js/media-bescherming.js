/* VAYLIDE: eigen beelden en video's niet met één klik kunnen opslaan.
 *
 * Alleen media-elementen: tekst blijft selecteerbaar en kopieerbaar, aanraken, klikken en scrollen blijven gewoon werken.
 * Wat het doet: geen contextmenu op beschermde media, geen slepen, geen downloadknop in de videospeler.
 * Wat het niet kan (en niet doet): screenshots of schermopnames tegenhouden, of voorkomen dat iemand het bestand
 * uit het netwerkverkeer haalt. Dit is een drempel tegen "opslaan als", geen DRM.
 *
 * Beschermd: <img>, <video> en <svg><image> uit /static/ (onze eigen bestanden) en alles binnen [data-media-beschermd].
 * Buiten schot: alles binnen [data-media-vrij] en afbeeldingen die niet uit /static/ komen (zoals de QR-code en foto's van klanten).
 */
(function () {
  "use strict";

  var MEDIA = "img, video, svg image";

  function pad(waarde) {
    try { return new URL(waarde, location.href); } catch (e) { return null; }
  }

  function beschermd(el) {
    if (!el || !el.closest || !el.matches(MEDIA)) return false;
    if (el.closest("[data-media-vrij]")) return false;
    if (el.closest("[data-media-beschermd]")) return true;
    if (el.tagName === "VIDEO") return true;
    var bron = el.currentSrc || el.getAttribute("src") || el.getAttribute("href") || el.getAttribute("xlink:href") || "";
    var url = pad(bron);
    return !!url && url.origin === location.origin && url.pathname.indexOf("/static/") === 0;
  }

  function doelwit(ev) {
    var t = ev.target;
    return t && t.nodeType === 1 ? t.closest(MEDIA) : null;
  }

  function weiger(ev) {
    var el = doelwit(ev);
    if (el && beschermd(el)) ev.preventDefault();
  }

  document.addEventListener("contextmenu", weiger);
  document.addEventListener("dragstart", weiger);

  function bescherm(el) {
    if (!beschermd(el)) return;
    if (el.tagName === "IMG") {
      el.setAttribute("draggable", "false");
    } else if (el.tagName === "VIDEO") {
      el.setAttribute("controlslist", "nodownload noplaybackrate");
      el.setAttribute("disablepictureinpicture", "");
      el.setAttribute("disableremoteplayback", "");
      el.removeAttribute("download");
    }
  }

  function bescherm_alles(wortel) {
    if (wortel.nodeType !== 1) return;
    if (wortel.matches(MEDIA)) bescherm(wortel);
    var kinderen = wortel.querySelectorAll ? wortel.querySelectorAll(MEDIA) : [];
    for (var i = 0; i < kinderen.length; i++) bescherm(kinderen[i]);
  }

  function start() {
    bescherm_alles(document.documentElement);
    if (!("MutationObserver" in window)) return;
    new MutationObserver(function (lijst) {
      for (var i = 0; i < lijst.length; i++) {
        var nieuw = lijst[i].addedNodes;
        for (var j = 0; j < nieuw.length; j++) bescherm_alles(nieuw[j]);
      }
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
