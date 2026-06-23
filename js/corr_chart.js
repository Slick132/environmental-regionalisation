(function () {
  var el = document.getElementById('elevCorrChart');
  if (!el) { return; }

  // Spearman correlation of each learned dimension with site elevation, in
  // order z1..z5. The chart diverges from zero: bars extend right for a
  // positive correlation and left for a negative one, so direction is shown.
  var data = [
    { z: 'z1', rho: -0.330 },
    { z: 'z2', rho: 0.835 },
    { z: 'z3', rho: -0.660 },
    { z: 'z4', rho: -0.103 },
    { z: 'z5', rho: -0.249 }
  ];

  function fmt(v) { return (v >= 0 ? '+' : '-') + Math.abs(v).toFixed(2); }

  var rows = '';
  for (var i = 0; i < data.length; i++) {
    var d = data[i];
    var w = (Math.abs(d.rho) * 50).toFixed(2);   // half the track width per unit correlation
    var cls = d.rho >= 0 ? 'cc-pos' : 'cc-neg';
    rows += '<div class="cc-row">'
         +    '<span class="cc-label">' + d.z + '</span>'
         +    '<span class="cc-track"><span class="cc-bar ' + cls + '" style="--w:' + w + '"></span></span>'
         +    '<span class="cc-val">' + fmt(d.rho) + '</span>'
         +  '</div>';
  }
  var ticks = ['-1.0', '-0.5', '0.0', '+0.5', '+1.0'];
  var scale = '';
  for (var t = 0; t < ticks.length; t++) { scale += '<span>' + ticks[t] + '</span>'; }
  var axis = '<div class="cc-axis"><span class="cc-scale">' + scale + '</span></div>';
  el.innerHTML = '<div class="cc-rows">' + rows + '</div>' + axis;

  function reveal() { el.classList.add('cc-in'); }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      if (es[0].isIntersecting) { reveal(); io.disconnect(); }
    }, { threshold: 0.25 });
    io.observe(el);
  } else {
    reveal();
  }
})();
