/* IRAN Tracker — demo frontend.
 * All ship data is SIMULATED. To go live, replace loadDemoShips() with a real
 * AIS provider fetch (see Methodology tab). */
(function () {
  "use strict";

  var DEMO = true; // flip to false when a live AIS feed is wired in
  var snapshotISO = new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC";

  /* ---------- tabs ---------- */
  var tabBtns = document.querySelectorAll("nav.tabs button");
  var panels = document.querySelectorAll("section.panel");
  function showTab(name) {
    tabBtns.forEach(function (b) { b.classList.toggle("active", b.dataset.tab === name); });
    panels.forEach(function (p) { p.classList.toggle("active", p.id === "panel-" + name); });
    if (name === "satellite") initSatMap();
    if (name === "map" && map) setTimeout(function () { map.invalidateSize(); }, 50);
  }
  tabBtns.forEach(function (b) { b.addEventListener("click", function () { showTab(b.dataset.tab); }); });
  document.querySelectorAll('[data-tab]').forEach(function (el) {
    if (el.tagName === "BUTTON") return;
    el.addEventListener("click", function () { showTab(el.dataset.tab); });
  });
  if (location.hash === "#methodology") showTab("methodology");

  function setSnapTimes() {
    document.querySelectorAll(".snapTime").forEach(function (el) { el.textContent = snapshotISO; });
    var m = document.getElementById("mapUpdated");
    if (m) m.textContent = snapshotISO;
  }

  function fmt(n) { return n.toLocaleString("en-US"); }

  /* ---------- demo ship markers ---------- */
  var map = null;
  function shipIcon(course, outbound) {
    var color = outbound ? "#f59e0b" : "#38bdf8";
    var html = '<div class="ship-icon" style="transform:rotate(' + course + 'deg);' +
      'width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;' +
      'border-bottom:14px solid ' + color + ';"></div>';
    return L.divIcon({ html: html, className: "", iconSize: [14, 14], iconAnchor: [7, 7] });
  }

  function initMap(ships) {
    if (typeof L === "undefined") {
      document.getElementById("map").innerHTML =
        '<p class="note" style="padding:20px">Map library failed to load (network blocked). Ship data is still listed in the Crossings and Ship Directory tabs.</p>';
      return;
    }
    map = L.map("map").setView([26.55, 56.35], 9);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18, attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
    ships.forEach(function (s) {
      var m = L.marker([s.lat, s.lon], { icon: shipIcon(s.course, s.status === "Outbound") }).addTo(map);
      m.bindPopup("<b>" + s.name + "</b><br>" + s.type + " · " + s.flag +
        "<br>DWT " + fmt(s.dwt) + " · " + s.length + " m" +
        "<br>Speed " + s.speed + " kn · Course " + s.course + "&deg;" +
        "<br>Status: " + s.status + " · Dest: " + s.dest +
        "<br><span class='tag demo'>DEMO</span>");
    });
  }

  /* ---------- stats + tables ---------- */
  function renderStats(ships) {
    var inbound = ships.filter(function (s) { return s.status === "Inbound"; }).length;
    var outbound = ships.filter(function (s) { return s.status === "Outbound"; }).length;
    var oilBbl = ships.reduce(function (a, s) { return a + (s.oil_bbl || 0); }, 0);
    var oilM = (oilBbl / 1e6).toFixed(2);
    document.getElementById("statCards").innerHTML =
      card(fmt(ships.length * 2), "Simulated crossings · 24h", true) +
      card(fmt(ships.length), "In strait (demo snapshot)", true) +
      card(fmt(inbound), "Inbound (demo)", true) +
      card(fmt(outbound), "Outbound (demo)", true) +
      card(oilM + " M bbl", "Illustrative oil in snapshot", true);
  }
  function card(v, l, warn) {
    return '<div class="card' + (warn ? " warn" : "") + '"><div class="v">' + v +
      '</div><div class="l">' + l + ' <span class="tag demo">DEMO</span></div></div>';
  }

  function renderCrossings(ships) {
    var tb = document.querySelector("#crossingsTable tbody");
    var now = Date.now();
    var rows = ships.slice(0, 14).map(function (s, i) {
      var t = new Date(now - i * 47 * 60000); // ~47 min apart, deterministic
      var ts = t.toISOString().replace("T", " ").slice(0, 16);
      var oil = s.oil_bbl ? (s.oil_bbl / 1e6).toFixed(2) : "-";
      return "<tr><td>" + ts + "</td><td><span class='tag " + s.status.toLowerCase() +
        "'>" + s.status + "</span></td><td>" + s.name + "</td><td>" + s.type +
        "</td><td>" + s.flag + "</td><td>" + fmt(s.dwt) + "</td><td>" + oil +
        "</td><td>" + s.dest + "</td></tr>";
    }).join("");
    tb.innerHTML = rows;
  }

  function renderShips(ships) {
    var tb = document.querySelector("#shipsTable tbody");
    tb.innerHTML = ships.map(function (s) {
      return "<tr><td><b>" + s.name + "</b></td><td>" + s.type + "</td><td>" + s.flag +
        "</td><td>" + fmt(s.dwt) + "</td><td>" + s.length + " m</td><td>" + s.speed +
        "</td><td>" + s.course + "&deg;</td><td><span class='tag " + s.status.toLowerCase() +
        "'>" + s.status + "</span></td></tr>";
    }).join("");
  }

  /* ---------- satellite map (lazy) ---------- */
  var satMap = null, satInit = false;
  function initSatMap() {
    if (satInit) { if (satMap) setTimeout(function () { satMap.invalidateSize(); }, 50); return; }
    satInit = true;
    if (typeof L === "undefined") {
      document.getElementById("satmap").innerHTML =
        '<p class="note" style="padding:20px">Map library failed to load (network blocked). Key locations are listed in the table below.</p>';
      return;
    }
    satMap = L.map("satmap").setView([28.5, 55.5], 5);
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 18, attribution: "Imagery &copy; Esri &mdash; basemap mosaic, not live"
    }).addTo(satMap);
    fetch("data/locations.json").then(function (r) { return r.json(); }).then(function (d) {
      var tb = document.querySelector("#locTable tbody");
      tb.innerHTML = d.locations.map(function (loc) {
        L.marker([loc.lat, loc.lon]).addTo(satMap)
          .bindPopup("<b>" + loc.name + "</b><br>" + loc.desc);
        return "<tr><td><b>" + loc.name + "</b></td><td>" + loc.kind + "</td><td>" +
          loc.lat.toFixed(4) + ", " + loc.lon.toFixed(4) + "</td><td>" + loc.desc + "</td></tr>";
      }).join("");
    }).catch(function () {
      document.querySelector("#locTable tbody").innerHTML =
        "<tr><td colspan='4'>Could not load locations.json</td></tr>";
    });
    setTimeout(function () { satMap.invalidateSize(); }, 100);
  }

  /* ---------- boot ---------- */
  setSnapTimes();
  fetch("data/demo_ships.json").then(function (r) { return r.json(); }).then(function (d) {
    var ships = d.ships;
    initMap(ships);
    renderStats(ships);
    renderCrossings(ships);
    renderShips(ships);
  }).catch(function () {
    document.getElementById("statCards").innerHTML =
      '<div class="card warn"><div class="v">—</div><div class="l">Could not load demo_ships.json</div></div>';
  });
})();
