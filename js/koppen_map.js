(function () {
  var data = window.KOPPEN_OVERLAY;
  var el = document.getElementById('koppenMap');
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

  var sl = document.getElementById('koppenOpacity');
  if (sl) {
    sl.value = 100;
    sl.addEventListener('input', function () { overlay.setOpacity(parseInt(sl.value, 10) / 100); });
  }

  var legEl = document.getElementById('koppenLegend');
  if (legEl) {
    var html = '';
    for (var i = 0; i < data.legend.length; i++) {
      var d = data.legend[i];
      html += '<span class="kitem">'
        + '<span class="kswatch" style="background:' + d.color + ';"></span>'
        + '<span class="kcode">' + d.code + '</span>'
        + '<span class="kname">' + d.name + '</span>'
        + '<span class="kn">' + d.n.toLocaleString() + '</span>'
        + '</span>';
    }
    legEl.innerHTML = html;
  }

  // The shared reveal observer in clustering.js only un-hides the regions map
  // (#results .map-panel). This panel must reveal itself or it stays at the
  // .map-panel default of opacity 0. Reveal it once the map is set up, and keep
  // an observer only to re-size the map when it scrolls into view.
  var panel = el.closest('.map-panel');
  function fit() { map.invalidateSize(); map.fitBounds(data.bounds, { padding: [12, 12] }); }
  setTimeout(function () { if (panel) { panel.classList.add('in'); } fit(); }, 60);
  if ('IntersectionObserver' in window && panel) {
    new IntersectionObserver(function (es) { if (es[0].isIntersecting) { panel.classList.add('in'); fit(); } }, { threshold: 0.06 }).observe(panel);
  }
})();
