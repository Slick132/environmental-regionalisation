(function () {
  var data = window.REGION_OVERLAY;
  var el = document.getElementById('regionMap');
  if (!el || !window.L || !data) { return; }

  var sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 18, attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics'
  });
  var topo = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
    maxZoom: 17, attribution: 'Map data: &copy; OpenStreetMap contributors, SRTM | Style: &copy; OpenTopoMap (CC-BY-SA)'
  });

  var map = L.map(el, { center: data.center, zoom: 6, layers: [sat], scrollWheelZoom: false });

  var overlay = L.imageOverlay(data.img, data.bounds, { opacity: 1.0, interactive: false, className: 'region-overlay' });
  overlay.addTo(map);
  map.fitBounds(data.bounds, { padding: [12, 12] });

  L.control.layers({ 'Satellite': sat, 'Terrain': topo }, {}, { collapsed: false }).addTo(map);

  var sl = document.getElementById('mapOpacity');
  if (sl) { sl.value = 100; }
  function curOp() { return sl ? parseInt(sl.value, 10) / 100 : 1.0; }
  if (sl) { sl.addEventListener('input', function () { overlay.setOpacity(curOp()); }); }

  var legEl = document.getElementById('mapLegend');
  var varPanel = document.getElementById('varPanel');
  var cbBar = document.getElementById('cbBar');
  var cbMin = document.getElementById('cbMin');
  var cbMax = document.getElementById('cbMax');
  var varBars = document.getElementById('varBars');

  function buildRegionLegend() {
    var html = '';
    for (var i = 0; i < data.legend.length; i++) {
      var d = data.legend[i];
      html += '<span class="item"><span class="swatch dot" style="background:' + d.color + ';"></span>' + d.name + ' <span class="n">(' + d.n.toLocaleString() + ')</span></span>';
    }
    legEl.innerHTML = html;
  }
  buildRegionLegend();

  function setOverlayImage(url) {
    overlay.setOpacity(0);
    overlay.once('load', function () { overlay.setOpacity(curOp()); });
    overlay.setUrl(url);
  }

  function showVariable(v) {
    cbBar.style.background = 'linear-gradient(to right,' + v.stops.join(',') + ')';
    cbMin.innerHTML = v.vmin + ' ' + v.unit;
    cbMax.innerHTML = v.vmax + ' ' + v.unit;
    var regs = v.regions.slice().sort(function (a, b) { return b.value - a.value; });
    var span = (v.vmax - v.vmin) || 1;
    var html = '';
    for (var i = 0; i < regs.length; i++) {
      var r = regs[i];
      var w = Math.max(4, Math.round(((r.value - v.vmin) / span) * 100));
      html += '<div class="vbar-row"><span class="vbar-label">R' + (r.k + 1) + '</span>'
        + '<span class="vbar-track"><span class="vbar-fill" style="width:' + w + '%;background:' + r.color + ';"></span></span>'
        + '<span class="vbar-val">' + r.value + ' ' + v.unit + '</span></div>';
    }
    varBars.innerHTML = html;
    legEl.hidden = true;
    varPanel.hidden = false;
  }

  function showRegions() { legEl.hidden = false; varPanel.hidden = true; }

  var btns = [].slice.call(document.querySelectorAll('#mapVars button'));
  btns.forEach(function (b) {
    b.addEventListener('click', function () {
      btns.forEach(function (o) { o.classList.toggle('active', o === b); });
      var name = b.getAttribute('data-var');
      if (name === 'regions') { setOverlayImage(data.img); showRegions(); }
      else { var v = data.variables[name]; if (!v) { return; } setOverlayImage(v.img); showVariable(v); }
    });
  });

  setTimeout(function () { map.invalidateSize(); map.fitBounds(data.bounds, { padding: [12, 12] }); }, 250);
})();
