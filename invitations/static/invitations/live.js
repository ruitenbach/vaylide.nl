/* De live kaart in de editor: foto's markeren en naar het deel scrollen waar de klant aan werkt.
   Alleen geladen in die weergave (html[data-live]); gasten krijgen dit nooit. */
(function () {
  "use strict";
  var html = document.documentElement;
  var part = html.getAttribute("data-live");
  var params = new URLSearchParams(location.search);
  var labels = { hoofdfoto: "Hoofdfoto", galerij: "Fotogalerij" };

  /* De live kaart in de Studio staat stil voor de muis: geen kantelen, parallax of meebewegen met de aanwijzer, ook niet als het ontwerp dat
     wel doet. Alles anders blijft live (animaties, effecten, tikken en klikken). De gepubliceerde kaart en het voorbeeld (/maken/<id>/voorbeeld)
     laden dit bestand niet en houden hun beweging. Een luisteraar in de vangstfase op window loopt vóór alle andere. */
  function negeerAanwijzer(e) { e.stopImmediatePropagation(); }
  window.addEventListener("pointermove", negeerAanwijzer, true);
  window.addEventListener("mousemove", negeerAanwijzer, true);

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
