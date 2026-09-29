/* De live kaart in de editor: foto's markeren en naar het deel scrollen waar de klant aan werkt.
   Alleen geladen in die weergave (html[data-live]); gasten krijgen dit nooit. */
(function () {
  "use strict";
  var html = document.documentElement;
  var part = html.getAttribute("data-live");
  var params = new URLSearchParams(location.search);
  var labels = { hoofdfoto: "Hoofdfoto", galerij: "Fotogalerij" };

  if (part === "fotos") {
    document.querySelectorAll("[data-foto]").forEach(function (img) {
      var box = img.closest(".ph") || img.parentElement;
      box.classList.add("live-mark");
      box.setAttribute("data-live-label", labels[img.getAttribute("data-foto")] || "Foto");
    });
  }

  function target() {
    if (part === "fotos") return document.querySelector("[data-foto]") || document.querySelector("[id$='story-title']");
    if (part === "aanmelden") return document.getElementById("aanmelden");
    if (part === "programma") return document.querySelector("[id$='program-title']");
    return null;
  }

  // Direct springen (de kaarten scrollen normaal 'zacht'); scrollIntoView zou ook de editorpagina zelf verschuiven.
  function jump(top) { window.scrollTo({ top: Math.max(0, top), behavior: "instant" }); }
  function place() {
    var y = params.get("y");
    if (y !== null) { jump(parseInt(y, 10) || 0); return; }
    var el = target();
    if (!el) return;
    var box = el.getBoundingClientRect();
    jump(window.scrollY + box.top - Math.max(0, (window.innerHeight - box.height) / 2));
  }
  if (document.readyState === "complete") place(); else window.addEventListener("load", place);
})();
