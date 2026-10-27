(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- theme toggle ---------- */
  var btn = $("#theme-btn");
  if (btn) {
    btn.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
    });
  }

  /* ---------- home: feed tabs + relative ages ---------- */
  var tabs = $$(".lw-tab");
  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      tabs.forEach(function (t) { t.setAttribute("aria-selected", String(t === tab)); });
      $$("[data-feed-list]").forEach(function (l) { l.hidden = l.getAttribute("data-feed-list") !== tab.getAttribute("data-feed"); });
    });
  });
  $$("time.js-age").forEach(function (el) {
    var days = Math.floor((Date.now() - new Date(el.getAttribute("datetime")).getTime()) / 864e5);
    if (days < 0) return;
    el.title = el.textContent;
    el.textContent = days < 1 ? "today" : days < 30 ? days + "d" : days < 365 ? Math.floor(days / 30) + "mo" : Math.floor(days / 365) + "y";
  });

  /* ---------- post: table of contents + scroll-spy ---------- */
  var article = $("#article");
  var toc = $("#lw-toc");
  if (article && toc) {
    $$("h2, h3", article).forEach(function (h) {
      if (!h.id) return;
      var a = document.createElement("a");
      a.href = "#" + h.id;
      a.className = "lvl-" + h.tagName.charAt(1);
      a.textContent = h.textContent;
      toc.appendChild(a);
      // heading permalink
      h.classList.add("group");
      var l = document.createElement("a");
      l.className = "heading-link";
      l.href = "#" + h.id;
      l.textContent = " #";
      l.setAttribute("aria-hidden", "true");
      h.appendChild(l);
    });
    var ca = document.createElement("a");
    ca.href = "#comments";
    ca.className = "lvl-2";
    ca.textContent = "Comments";
    toc.appendChild(ca);

    var links = $$("a", toc);
    var targets = links.map(function (a) { return document.getElementById(decodeURIComponent(a.hash.slice(1))); });
    var spy = function () {
      var current = -1;
      targets.forEach(function (el, i) { if (el && el.getBoundingClientRect().top <= 120) current = i; });
      links.forEach(function (a, i) { a.classList.toggle("active", i === current); });
    };
    document.addEventListener("scroll", spy, { passive: true });
    spy();
  }

  /* ---------- post: Tufte-style margin notes from footnotes ---------- */
  var margin = $("#lw-margin");
  var notes = article && $("div.footnotes", article);
  if (margin && notes) {
    var wide = window.matchMedia("(min-width: 1300px)");
    var layout = function () {
      margin.innerHTML = "";
      article.classList.remove("has-sidenotes");
      if (!wide.matches) return;
      article.classList.add("has-sidenotes");
      var top = margin.getBoundingClientRect().top + window.scrollY;
      var nextFree = 0;
      $$("a.footnote", article).forEach(function (ref, i) {
        var li = document.getElementById(ref.getAttribute("href").slice(1));
        if (!li) return;
        var note = document.createElement("div");
        note.className = "lw-sidenote";
        note.innerHTML = '<span class="sn-num">' + (i + 1) + "</span>" + li.innerHTML;
        margin.appendChild(note);
        var y = ref.getBoundingClientRect().top + window.scrollY - top;
        var pos = Math.max(y, nextFree);
        note.style.top = pos + "px";
        nextFree = pos + note.offsetHeight + 12;
      });
    };
    layout();
    wide.addEventListener("change", layout);
    window.addEventListener("load", layout);
    window.addEventListener("resize", layout);
  }

  /* ---------- search page ---------- */
  var input = $("#search-input");
  if (input) {
    var results = $("#search-results");
    var count = $("#search-count");
    var base = document.querySelector('link[href$="main.css"]').getAttribute("href").replace(/assets\/css\/main\.css.*$/, "");
    var data = [];
    var esc = function (s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
    var render = function () {
      var q = input.value.trim().toLowerCase();
      var hits = q ? data.filter(function (p) { return (p.title + " " + p.description + " " + p.tags).toLowerCase().indexOf(q) !== -1; }) : [];
      count.textContent = q ? hits.length + " result" + (hits.length === 1 ? "" : "s") + ' for "' + input.value + '"' : "";
      results.innerHTML = hits.map(function (p) {
        return '<li class="lw-item" style="grid-template-columns:minmax(0,1fr)"><a class="lw-item-title" href="' + p.url + '">' + esc(p.title) + '</a><div class="lw-item-sub" style="grid-column:1">' + esc(p.date) + " · " + esc(p.description) + "</div></li>";
      }).join("");
    };
    fetch(base + "search.json").then(function (r) { return r.json(); }).then(function (d) { data = d; render(); });
    input.addEventListener("input", render);
    var q0 = new URLSearchParams(location.search).get("q");
    if (q0) input.value = q0;
  }
})();
