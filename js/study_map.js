(function () {
  var el = document.getElementById('studyMap');
  if (!el || !window.L) { return; }

  // Geographic bounds of the study-area hex overlay (Web Mercator raster,
  // matches build_study_overlay.py / the region overlay bounds).
  var bounds = [[-31.2349, 26.2583], [-21.91915, 33.0295]];

  var sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 18, attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics'
  });
  var map = L.map(el, { layers: [sat], scrollWheelZoom: false, attributionControl: true });

  L.imageOverlay('figures/study_area_overlay.png', bounds, { opacity: 1.0, interactive: false }).addTo(map);

  // Show the study area within the surrounding country for context.
  function fit() { map.fitBounds(L.latLngBounds(bounds).pad(0.55)); }
  fit();
  setTimeout(function () { map.invalidateSize(); fit(); }, 250);
})();
