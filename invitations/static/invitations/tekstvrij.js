/* Tekst blijft vrij van knalplaatjes: confetti, sterretjes en sneeuwvlokken van het openen en vieren (de .fx-burst-laag
   van effects.js, die boven de pagina ligt) worden rond de zichtbare tekst weggeknipt, zodat ze de tekst nooit bedekken.
   Alleen de ontwerpen die dit script laden hebben er last van gehad; de effecten zelf blijven zoals ze waren.
   Zonder JavaScript of bij 'minder beweging' (dan is de laag er niet) gebeurt er niets. */
(function () {
  "use strict";
  var PAD = 5, STAP = 70;
  var last = "", timer = 0;

  function holes(host) {
    var list = [], w = window.innerWidth, h = window.innerHeight;
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (!/\S/.test(n.nodeValue)) return NodeFilter.FILTER_REJECT;
        var p = n.parentNode;
        if (!p || p.closest("script, style, noscript, .fx-burst, .fx-slot, .fx-toggle, [hidden]")) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var range = document.createRange();
    for (var n = walker.nextNode(); n; n = walker.nextNode()) {
      var box = n.parentNode.getBoundingClientRect();
      if (box.bottom < -40 || box.top > h + 40 || box.right < -40 || box.left > w + 40) continue;
      var cs = window.getComputedStyle(n.parentNode);
      if (cs.visibility === "hidden" || cs.display === "none" || parseFloat(cs.opacity) < 0.05) continue;
      range.selectNodeContents(n);
      var rects = range.getClientRects();
      for (var i = 0; i < rects.length; i++) {
        var r = rects[i];
        if (r.width < 2 || r.height < 2) continue;
        list.push([Math.max(0, r.left - PAD), Math.max(0, r.top - PAD), Math.min(w, r.right + PAD), Math.min(h, r.bottom + PAD)]);
      }
    }
    return merge(list);
  }

  /* Overlappende vlakken worden één vlak, anders vult de even-oneven-regel ze weer op. */
  function merge(list) {
    var changed = true;
    while (changed) {
      changed = false;
      for (var i = 0; i < list.length && !changed; i++) {
        for (var j = i + 1; j < list.length; j++) {
          var a = list[i], b = list[j];
          if (a[0] <= b[2] && b[0] <= a[2] && a[1] <= b[3] && b[1] <= a[3]) {
            list[i] = [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])];
            list.splice(j, 1);
            changed = true;
            break;
          }
        }
      }
    }
    return list;
  }

  function update() {
    timer = window.setTimeout(update, STAP);
    if (document.hidden) return;
    var host = document.querySelector(".fx-burst");
    if (!host) return;
    var w = window.innerWidth, h = window.innerHeight;
    var d = "M0 0H" + w + "V" + h + "H0Z", list = holes(host);
    for (var i = 0; i < list.length; i++) {
      var r = list[i];
      d += "M" + Math.round(r[0]) + " " + Math.round(r[1]) + "H" + Math.round(r[2]) + "V" + Math.round(r[3]) + "H" + Math.round(r[0]) + "Z";
    }
    if (d === last) return;
    last = d;
    host.style.clipPath = "path(evenodd, '" + d + "')";
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", update);
  else update();
})();
