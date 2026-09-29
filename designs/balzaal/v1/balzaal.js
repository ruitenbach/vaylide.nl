/* Balzaal v1: subtiele diepte. Met de muis schuiven zaal, paar en bloemen elk een klein beetje anders mee (--dx, --dy).
   Alleen met een muis, en niet bij 'minder beweging' of als de gast de beweging heeft stilgezet. Zonder dit script staat
   alles gewoon stil en is de uitnodiging volledig leesbaar. */
(function () {
  "use strict";
  var hero = document.querySelector("[data-bz-diepte]");
  if (!hero || !window.matchMedia) return;
  if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var frame = 0, x = 0, y = 0;
  function apply() {
    frame = 0;
    var still = reduce.matches || !document.documentElement.classList.contains("fx-motion");
    hero.style.setProperty("--dx", still ? "0" : x.toFixed(3));
    hero.style.setProperty("--dy", still ? "0" : y.toFixed(3));
  }
  hero.addEventListener("pointermove", function (e) {
    var r = hero.getBoundingClientRect();
    x = Math.max(-1, Math.min(1, (e.clientX - r.left) / r.width * 2 - 1));
    y = Math.max(-1, Math.min(1, (e.clientY - r.top) / r.height * 2 - 1));
    if (!frame) frame = window.requestAnimationFrame(apply);
  });
  hero.addEventListener("pointerleave", function () { x = 0; y = 0; if (!frame) frame = window.requestAnimationFrame(apply); });
})();
