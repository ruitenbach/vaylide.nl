/* Moments, gastpagina (demonstratie). Alles gebeurt in de browser: er is geen verzoek naar de server en niets wordt bewaard.
   De gekozen bestanden worden alleen getoond (blob-adressen) en bij het verlaten van de pagina vergeten. */
(function () {
  "use strict";
  var root = document.getElementById("moments-root");
  if (!root) return;
  var d = root.dataset;
  var photosMax = parseInt(d.photosMax, 10) || 0;
  var videoSeconds = parseInt(d.videoSeconds, 10) || 0;

  function fill(template, values) {
    return (template || "").replace(/\{(\w+)\}/g, function (m, k) { return k in values ? values[k] : m; });
  }

  /* ----- begroeting ----- */
  var nameInput = root.querySelector("[data-greeting-input]");
  var greeting = root.querySelector("[data-greeting]");
  if (nameInput && greeting) {
    nameInput.addEventListener("input", function () {
      var name = nameInput.value.trim();
      greeting.textContent = name ? fill(nameInput.dataset.greetingTemplate, { name: name }) : nameInput.dataset.greetingDefault;
    });
  }

  /* ----- foto's ----- */
  var grid = root.querySelector("[data-photo-grid]");
  var counter = root.querySelector("[data-photo-counter]");
  var msg = root.querySelector("[data-photo-msg]");
  var hint = root.querySelector("[data-photo-hint]");
  var inputs = root.querySelectorAll("[data-photo-input]");
  var photos = [];

  function say(el, text, ok) {
    if (!el) return;
    el.hidden = !text;
    el.textContent = text || "";
    el.classList.toggle("mm-msg--ok", !!ok);
  }

  function renderCounter() {
    if (counter) counter.textContent = fill(d.txtCounter, { n: photos.length, max: photosMax });
    var full = photos.length >= photosMax;
    inputs.forEach(function (i) { i.disabled = full; });
    if (full) say(msg, d.txtFull, true);
  }

  function addPhotos(fileList) {
    var room = photosMax - photos.length;
    var files = Array.prototype.slice.call(fileList);
    var images = files.filter(function (f) { return /^image\//.test(f.type); });
    var problem = "";
    if (images.length < files.length) problem = d.txtNotPhoto;
    if (images.length > room) { problem = fill(d.txtRoomPhotos, { n: Math.max(room, 0) }); images = images.slice(0, Math.max(room, 0)); }
    if (!photos.length && hint) {
      grid.querySelectorAll(".mm-thumb--example").forEach(function (li) { li.remove(); });
      hint.hidden = true;
    }
    images.forEach(function (file) {
      var url = URL.createObjectURL(file);
      var li = document.createElement("li");
      li.className = "mm-thumb";
      var img = document.createElement("img");
      img.src = url; img.alt = ""; img.width = 400; img.height = 400;
      var btn = document.createElement("button");
      btn.type = "button"; btn.className = "mm-remove";
      btn.setAttribute("aria-label", d.txtRemoveLabel);
      var entry = { url: url, li: li };
      btn.addEventListener("click", function () {
        URL.revokeObjectURL(url);
        li.remove();
        photos = photos.filter(function (p) { return p !== entry; });
        say(msg, d.txtRemoved, true);
        renderCounter();
      });
      li.appendChild(img); li.appendChild(btn);
      grid.appendChild(li);
      photos.push(entry);
    });
    if (problem) say(msg, problem, false);
    else if (images.length) say(msg, d.txtAdded, true);
    renderCounter();
  }

  inputs.forEach(function (input) {
    input.addEventListener("change", function () {
      if (input.files && input.files.length) addPhotos(input.files);
      input.value = "";
    });
  });

  /* ----- video's ----- */
  root.querySelectorAll("[data-video]").forEach(function (card) {
    var vmsg = card.querySelector("[data-video-msg]");
    var clear = card.querySelector("[data-video-clear]");
    var vinputs = card.querySelectorAll("[data-video-input]");
    var current = null;

    function reset() {
      if (current) URL.revokeObjectURL(current);
      current = null;
      clear.hidden = true;
      vinputs.forEach(function (i) { i.disabled = false; });
    }

    clear.addEventListener("click", function () { reset(); say(vmsg, d.txtRemoved, true); });

    vinputs.forEach(function (input) {
      input.addEventListener("change", function () {
        var file = input.files && input.files[0];
        input.value = "";
        if (!file) return;
        if (!/^video\//.test(file.type)) { say(vmsg, d.txtNotVideo, false); return; }
        var url = URL.createObjectURL(file);
        var probe = document.createElement("video");
        probe.preload = "metadata";
        probe.muted = true;
        probe.onloadedmetadata = function () {
          var secs = Math.round(probe.duration);
          probe.removeAttribute("src"); probe.load();
          if (!isFinite(secs) || secs <= 0) { URL.revokeObjectURL(url); say(vmsg, d.txtUnreadable, false); return; }
          if (secs > videoSeconds) { URL.revokeObjectURL(url); say(vmsg, fill(d.txtTooLong, { n: secs, max: videoSeconds }), false); return; }
          reset();
          current = url;
          say(vmsg, fill(d.txtVideoOk, { name: file.name, n: secs }), true);
          clear.hidden = false;
          vinputs.forEach(function (i) { i.disabled = true; });
        };
        probe.onerror = function () { URL.revokeObjectURL(url); say(vmsg, d.txtUnreadable, false); };
        probe.src = url;
      });
    });
  });

  window.addEventListener("pagehide", function () {
    photos.forEach(function (p) { URL.revokeObjectURL(p.url); });
  });
})();
