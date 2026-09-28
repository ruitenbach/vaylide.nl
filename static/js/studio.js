/* Vaylide samenstellen: verbeteringen bovenop werkende formulieren.
   Zonder JavaScript werkt alles ook (gewone formulieren, schuifjes en knoppen). */
(function () {
  "use strict";
  var html = document.documentElement;
  html.classList.add("js-enabled");

  // Uitnodiging of wenskaart: bij een wenskaart verdwijnen 'Wanneer' en 'Waar' (de ingevulde waarden blijven bewaard).
  document.querySelectorAll("[data-soort-keuze]").forEach(function (group) {
    var form = group.closest("form");
    function update() {
      var checked = group.querySelector("input[name=soort]:checked");
      var wens = checked && checked.value === "wenskaart";
      form.querySelectorAll("[data-alleen-uitnodiging]").forEach(function (el) { el.hidden = wens; });
    }
    group.addEventListener("change", update);
    update();
  });

  function csrfToken() {
    var input = document.querySelector("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  /* ---------- Herhaalbare rijen (programma, praktische info, vragen) ---------- */
  document.querySelectorAll("[data-repeat]").forEach(function (list) {
    var add = list.querySelector("[data-repeat-add]");
    if (!add) return;
    function hiddenRows() { return list.querySelectorAll("[data-repeat-row].is-empty"); }
    function sync() { add.hidden = hiddenRows().length === 0; }
    add.addEventListener("click", function () {
      var next = hiddenRows()[0];
      if (!next) return;
      next.classList.remove("is-empty");
      var input = next.querySelector("input:not([type=hidden]), textarea, select");
      if (input) input.focus();
      sync();
    });
    sync();
  });

  /* ---------- Enter in een tekstveld = 'Volgende' ---------- */
  document.querySelectorAll("form").forEach(function (form) {
    var next = form.querySelector("[data-default-action]");
    if (!next) return;
    form.addEventListener("keydown", function (event) {
      var target = event.target;
      if (event.key !== "Enter" || !target || target.tagName !== "INPUT") return;
      if (["text", "email", "tel", "url", "number", "date", "time"].indexOf(target.type) === -1) return;
      event.preventDefault();
      next.click();
    });
  });

  /* ---------- Waarschuwing bij niet-opgeslagen wijzigingen ---------- */
  document.querySelectorAll("form[data-dirty-check]").forEach(function (form) {
    var dirty = false;
    form.addEventListener("input", function () { dirty = true; });
    form.addEventListener("change", function () { dirty = true; });
    form.addEventListener("submit", function () { dirty = false; });
    window.addEventListener("beforeunload", function (event) {
      if (!dirty) return;
      event.preventDefault();
      event.returnValue = "";
    });
    form.markDirty = function () { dirty = true; };
  });

  /* ---------- Start: ontwerpen filteren op gelegenheid ---------- */
  var occasionRadios = document.querySelectorAll("[data-occasion-radio]");
  if (occasionRadios.length) {
    var filter = function () {
      var checked = document.querySelector("[data-occasion-radio]:checked");
      var occasion = checked ? checked.value : "";
      document.querySelectorAll(".design-pick[data-occasions]").forEach(function (card) {
        var fits = !occasion || card.getAttribute("data-occasions").split(" ").indexOf(occasion) !== -1;
        card.classList.toggle("is-hidden", !fits);
        var radio = card.querySelector("input[type=radio]");
        if (!fits && radio && radio.checked) radio.checked = false;
      });
    };
    occasionRadios.forEach(function (radio) { radio.addEventListener("change", filter); });
    filter();
  }

  /* ---------- Foto's uploaden met controle vooraf en voortgang ---------- */
  document.querySelectorAll("form[data-upload]").forEach(function (form) {
    var input = form.querySelector("input[type=file]");
    var status = form.querySelector("[data-upload-status]");
    var button = form.querySelector("[data-upload-submit]");
    var maxBytes = parseInt(form.getAttribute("data-max-bytes"), 10) || 12 * 1024 * 1024;
    var allowed = ["image/jpeg", "image/png", "image/webp"];
    var drop = form.querySelector(".upload-drop");
    function say(text, kind) {
      status.textContent = text;
      status.classList.toggle("is-error", kind === "error");
      status.classList.toggle("is-ok", kind === "ok");
    }
    function check() {
      var problems = [];
      Array.prototype.forEach.call(input.files || [], function (file) {
        if (allowed.indexOf(file.type) === -1 && !/\.(jpe?g|png|webp)$/i.test(file.name)) {
          problems.push(file.name + ": dit bestandstype wordt niet ondersteund (gebruik JPG, PNG of WebP).");
        } else if (file.size > maxBytes) {
          problems.push(file.name + ": te groot (" + Math.round(file.size / 1048576) + " MB, maximaal " + Math.round(maxBytes / 1048576) + " MB).");
        }
      });
      return problems;
    }
    if (drop) {
      ["dragenter", "dragover"].forEach(function (name) { drop.addEventListener(name, function (e) { e.preventDefault(); drop.classList.add("is-dragover"); }); });
      ["dragleave", "drop"].forEach(function (name) { drop.addEventListener(name, function () { drop.classList.remove("is-dragover"); }); });
      drop.addEventListener("drop", function (e) {
        e.preventDefault();
        if (e.dataTransfer && e.dataTransfer.files.length) { input.files = e.dataTransfer.files; input.dispatchEvent(new Event("change")); }
      });
    }
    input.addEventListener("change", function () {
      var problems = check();
      if (problems.length) { say(problems.join(" "), "error"); return; }
      if (input.files.length) { say(input.files.length + " bestand(en) gekozen. Bezig met uploaden…"); upload(); }
    });
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var problems = check();
      if (problems.length) { say(problems.join(" "), "error"); return; }
      if (!input.files || !input.files.length) { say("Kies eerst een of meer foto's.", "error"); return; }
      upload();
    });
    function upload() {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", form.action);
      xhr.setRequestHeader("Accept", "application/json");
      xhr.setRequestHeader("X-Requested-With", "fetch");
      xhr.upload.addEventListener("progress", function (e) {
        if (e.lengthComputable) say("Uploaden… " + Math.round((e.loaded / e.total) * 100) + "%");
      });
      xhr.addEventListener("load", function () {
        var data = {};
        try { data = JSON.parse(xhr.responseText); } catch (e) { data = { errors: ["Uploaden is niet gelukt. Probeer het opnieuw."] }; }
        if (xhr.status === 413) data.errors = ["Deze bestanden zijn samen te groot. Upload er minder tegelijk."];
        if (data.errors && data.errors.length) {
          say(data.errors.join(" "), "error");
          if (data.created && data.created.length) window.setTimeout(function () { window.location.reload(); }, 2500);
          return;
        }
        say("Geüpload. De pagina wordt bijgewerkt…", "ok");
        window.location.hash = "uploads";
        window.location.reload();
      });
      xhr.addEventListener("error", function () { say("Geen verbinding. Je foto's zijn nog niet geüpload.", "error"); });
      if (button) button.disabled = true;
      xhr.send(new FormData(form));
    }
  });

  /* ---------- Uitsnede: middelpunt kiezen door te tikken of te slepen ---------- */
  document.querySelectorAll("[data-photo]").forEach(function (card) {
    var uid = card.getAttribute("data-uid");
    var frame = card.querySelector("[data-focus-frame]");
    var img = card.querySelector("[data-focus-img]");
    var marker = card.querySelector("[data-focus-marker]");
    var x = card.querySelector("input[name='x_" + uid + "']");
    var y = card.querySelector("input[name='y_" + uid + "']");
    var z = card.querySelector("input[name='z_" + uid + "']");
    if (!frame || !x || !y) return;
    function render() {
      var px = parseFloat(x.value || 50), py = parseFloat(y.value || 50), zoom = (parseFloat((z && z.value) || 100)) / 100;
      img.style.objectPosition = px + "% " + py + "%";
      img.style.transformOrigin = px + "% " + py + "%";
      img.style.transform = zoom > 1.001 ? "scale(" + zoom + ")" : "";
      marker.style.left = px + "%";
      marker.style.top = py + "%";
    }
    function fromPointer(event) {
      var rect = frame.getBoundingClientRect();
      var px = Math.max(0, Math.min(100, ((event.clientX - rect.left) / rect.width) * 100));
      var py = Math.max(0, Math.min(100, ((event.clientY - rect.top) / rect.height) * 100));
      x.value = Math.round(px);
      y.value = Math.round(py);
      render();
      var form = x.form;
      if (form && form.markDirty) form.markDirty();
    }
    var dragging = false;
    frame.addEventListener("pointerdown", function (e) { dragging = true; frame.setPointerCapture(e.pointerId); fromPointer(e); });
    frame.addEventListener("pointermove", function (e) { if (dragging) fromPointer(e); });
    frame.addEventListener("pointerup", function () { dragging = false; });
    [x, y, z].forEach(function (input) { if (input) input.addEventListener("input", render); });
    render();
  });

  /* ---------- Tekstvoorstel (AI of testmodus) ---------- */
  document.querySelectorAll("[data-ai]").forEach(function (box) {
    box.hidden = false;
    var url = box.getAttribute("data-ai-url");
    var field = box.getAttribute("data-ai-field");
    var target = document.querySelector("[data-ai-field='" + field + "']:not([data-ai])");
    var go = box.querySelector("[data-ai-go]");
    var out = box.querySelector("[data-ai-result]");
    go.addEventListener("click", function () {
      var body = new FormData();
      body.append("field", field);
      body.append("tone", box.querySelector("[data-ai-tone]").value);
      body.append("notes", box.querySelector("[data-ai-notes]").value);
      body.append("current", target ? target.value : "");
      go.disabled = true;
      out.textContent = "Bezig met een voorstel…";
      fetch(url, { method: "POST", body: body, headers: { "X-CSRFToken": csrfToken(), "Accept": "application/json" }, credentials: "same-origin" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          go.disabled = false;
          out.textContent = "";
          if (!data.ok) { out.textContent = data.message || "Er kon geen voorstel worden gemaakt."; return; }
          var note = document.createElement("p");
          note.className = "small muted";
          note.textContent = data.notice;
          var text = document.createElement("p");
          text.className = "ai-help__suggestion";
          text.textContent = data.suggestion;
          var use = document.createElement("button");
          use.type = "button";
          use.className = "btn btn--primary btn--sm";
          use.textContent = "Gebruik dit voorstel";
          use.addEventListener("click", function () {
            if (target) {
              target.value = data.suggestion;
              target.dispatchEvent(new Event("input", { bubbles: true }));
              target.focus();
            }
            out.textContent = "Voorstel overgenomen. Pas het gerust aan en vergeet niet op te slaan.";
          });
          out.appendChild(note);
          out.appendChild(text);
          out.appendChild(use);
        })
        .catch(function () { go.disabled = false; out.textContent = "Geen verbinding. Probeer het opnieuw."; });
    });
  });

  /* ---------- Voorbeeld: telefoon of computer ---------- */
  document.querySelectorAll("[data-preview]").forEach(function (stage) {
    var frame = stage.querySelector("[data-preview-frame]");
    stage.querySelectorAll("[data-device]").forEach(function (button) {
      button.addEventListener("click", function () {
        stage.querySelectorAll("[data-device]").forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
        button.setAttribute("aria-pressed", "true");
        frame.className = "preview-frame preview-frame--" + button.getAttribute("data-device");
      });
    });
  });

  /* ---------- Bestellen: bedrag direct bijwerken bij een andere keuze ---------- */
  document.querySelectorAll("[data-recalc]").forEach(function (input) {
    input.addEventListener("change", function () {
      var form = input.form;
      var action = form.querySelector("[data-checkout-action]");
      if (action) action.value = "herberekenen";
      form.submit();
    });
  });
})();
