/* Kerstmagie v1: de openingsfilm.
   Een tik in het midden start de film; als hij klaar is (of de gast op 'Overslaan' tikt) opent de uitnodiging
   via het gewone openingsscherm uit invite.js. Het filmbestand wordt pas geladen als het scherm echt getoond
   wordt, dus wie de uitnodiging al eerder opende, downloadt de film niet opnieuw.
   Gaat er iets mis (de film start niet, laadt te traag of geeft een fout), dan opent de uitnodiging gewoon. */
(function () {
  "use strict";

  var html = document.documentElement;
  var cover = document.querySelector("[data-cover]");
  if (!cover || !html.classList.contains("has-cover")) return;

  var video = cover.querySelector("[data-kl-video]");
  var play = cover.querySelector("[data-kl-play]");
  var finish = cover.querySelector("[data-kl-finish]");
  var skip = cover.querySelector("[data-kl-skip]");
  var watch = cover.querySelector("[data-kl-watch]");
  var hint = cover.querySelector("[data-kl-hint]");
  var status = cover.querySelector("[data-kl-status]");
  var center = cover.querySelector(".kl-cover__center");
  if (!video || !play || !finish) return;

  var reduceQuery = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  var started = false;
  var done = false;
  var giveUp = null;

  /* 'Minder beweging' in het systeem of de knop 'Beweging' op stil: dan geen film, tenzij de gast erom vraagt. */
  function calm() {
    return !!(reduceQuery && reduceQuery.matches) || html.classList.contains("fx-paused");
  }

  /* De film laadt pas nadat de pagina klaar is (eerst de afbeeldingen en letters), en bij 'databesparing'
     pas na de tik. Een tik die eerder komt, laadt hem meteen. */
  var connection = navigator.connection || {};
  var loaded = false;
  function load() {
    if (loaded || done) return;
    loaded = true;
    /* mp4 waar het kan (loopt het soepelst op telefoons), anders webm. */
    var canMp4 = video.canPlayType && video.canPlayType('video/mp4; codecs="avc1.640028"') !== "";
    video.preload = "auto";
    video.src = video.getAttribute(canMp4 ? "data-src-mp4" : "data-src-webm");
    video.load();
  }
  if (!connection.saveData) {
    var later = function () { window.setTimeout(load, 1200); };
    if (document.readyState === "complete") later(); else window.addEventListener("load", later);
  }

  function say(text) { if (status) status.textContent = text; }

  function open() {
    if (done) return;
    done = true;
    window.clearTimeout(giveUp);
    finish.click();
  }

  function begin(force) {
    if (started || done) return;
    if (calm() && !force) { open(); return; }
    started = true;
    load();
    cover.classList.add("is-loading");
    say("De film wordt geladen.");
    giveUp = window.setTimeout(open, 9000);

    var attempt;
    try { attempt = video.play(); } catch (e) { open(); return; }
    if (attempt && attempt.catch) attempt.catch(open);
  }

  video.addEventListener("playing", function () {
    if (done) return;
    window.clearTimeout(giveUp);
    cover.classList.remove("is-loading");
    cover.classList.add("is-playing");
    if (center) center.inert = true;
    if (watch) watch.hidden = true;
    if (skip) skip.hidden = false;
    say("De film speelt. Tik op Overslaan om direct naar de uitnodiging te gaan.");
  });
  /* Haperen midden in de film: wachten, maar niet eindeloos. */
  video.addEventListener("waiting", function () {
    if (done || !started) return;
    window.clearTimeout(giveUp);
    giveUp = window.setTimeout(open, 12000);
  });
  video.addEventListener("ended", open);
  video.addEventListener("error", function () { if (started) open(); });

  /* Een tik in het midden (of overal op het scherm) start de film. */
  cover.addEventListener("click", function (event) {
    if (event.target.closest("[data-kl-skip], [data-kl-finish], [data-kl-watch]")) return;
    begin(false);
  });
  if (watch) watch.addEventListener("click", function () { begin(true); });

  /* Bij 'Overslaan' en bij het openen op een andere manier stopt de film. */
  document.addEventListener("invite:opening", function () {
    done = true;
    window.clearTimeout(giveUp);
    video.pause();
    cover.classList.remove("is-loading");
  });
  document.addEventListener("invite:opened", function () {
    video.removeAttribute("src");
    video.load();
  });

  /* Rustige weergave: de knop opent direct, en er is een aparte knop om de film toch te bekijken. */
  function sync() {
    if (started || done) return;
    var quiet = calm();
    play.setAttribute("aria-label", quiet ? "Open de uitnodiging" : "Start de openingsfilm");
    if (hint) hint.textContent = quiet ? "Tik in het midden om te openen" : "Tik in het midden om te beginnen";
    if (watch) watch.hidden = !quiet;
  }
  sync();
  if (window.MutationObserver) new MutationObserver(sync).observe(html, { attributes: true, attributeFilter: ["class"] });
  if (reduceQuery) {
    if (reduceQuery.addEventListener) reduceQuery.addEventListener("change", sync);
    else if (reduceQuery.addListener) reduceQuery.addListener(sync);
  }
})();
