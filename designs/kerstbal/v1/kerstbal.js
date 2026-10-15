/* Kerstbal v1: de film in de opening.
   Tot de gast tikt staat het eerste beeld (de dichte kerstbal) stil. Na een tik op de bal speelt het filmpje (zonder geluid):
   de bal gaat open en de kaart komt eruit. Dit script staat alleen in dit ontwerp en laat invite.js ongemoeid.
   Speelt het filmpje niet binnen anderhalve seconde (of mag het niet), dan vervaagt de dichte bal en komt de kaart toch naar voren.
   Bij 'minder beweging' of 'Beweging uit' speelt het filmpje niet: de kaart opent dan rustig.
   Wijzig een uitgebrachte versie niet: maak een v2. */
(function () {
  "use strict";
  var html = document.documentElement;
  var video = document.querySelector(".kb-cover .kb-video");
  if (!video) return;

  video.muted = true;
  try { video.load(); } catch (e) { /* oudere browser: laadt bij afspelen */ }

  function failed() {
    video.pause();
    html.classList.add("cover-video-failed");
  }

  document.addEventListener("invite:opening", function (event) {
    if (event.detail && event.detail.reduceMotion) return;
    var timer = window.setTimeout(failed, 1500);
    video.addEventListener("playing", function () { window.clearTimeout(timer); }, { once: true });
    try { video.currentTime = 0; } catch (e) { /* nog geen gegevens: begint toch bij 0 */ }
    var attempt = video.play();
    if (attempt && attempt.catch) attempt.catch(function () { window.clearTimeout(timer); failed(); });
  });
  // Zodra de kaart open is, is het filmpje niet meer nodig.
  document.addEventListener("invite:opened", function () { if (!video.paused) video.pause(); });
  // Tikt de gast tijdens het openen op 'Beweging', dan staat het filmpje meteen stil.
  new MutationObserver(function () {
    if (html.classList.contains("fx-paused") && !video.paused) video.pause();
  }).observe(html, { attributes: true, attributeFilter: ["class"] });
})();
