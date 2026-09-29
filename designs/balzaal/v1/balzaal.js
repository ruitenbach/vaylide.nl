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

/* De dans: speelt na het openen (niet bij 'minder beweging' of stilgezette beweging), met een knop om te pauzeren.
   Zonder videobestand of zonder JavaScript blijft de stilstaande scène staan. */
(function () {
  "use strict";
  var box = document.querySelector("[data-bz-dans]");
  var knop = document.querySelector("[data-bz-dans-knop]");
  if (!box || !knop) return;
  var video = box.querySelector("video");
  var label = knop.querySelector("[data-bz-dans-label]");
  var html = document.documentElement;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  knop.hidden = false;
  function show(playing) {
    knop.setAttribute("aria-pressed", playing ? "true" : "false");
    label.textContent = playing ? "Dans pauzeren" : "Dans afspelen";
  }
  function play() {
    video.preload = "auto";
    var p = video.play();
    if (p && p.catch) p.catch(function () { show(false); });
  }
  video.addEventListener("play", function () { show(true); });
  video.addEventListener("pause", function () { show(false); });
  knop.addEventListener("click", function () { if (video.paused) play(); else video.pause(); });
  function autostart() {
    if (reduce || html.classList.contains("fx-paused")) return;
    window.setTimeout(play, 600);
  }
  if (html.classList.contains("is-open") || !html.classList.contains("has-cover")) autostart();
  else document.addEventListener("invite:opening", function () { window.setTimeout(autostart, 1800); }, { once: true });
  // Beweging stilgezet met de knop 'Beweging': de dans pauzeert ook.
  new MutationObserver(function () { if (html.classList.contains("fx-paused") && !video.paused) video.pause(); })
    .observe(html, { attributes: true, attributeFilter: ["class"] });
})();
