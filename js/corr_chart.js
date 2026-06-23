(function () {
  var el = document.getElementById('elevCorrChart');
  if (!el) { return; }

  // Spearman correlation of each learned dimension with site elevation.
  // The latent sign is arbitrary, so the bar length is the magnitude and the
  // signed value is shown as a label. Sorted strongest first.
  var data = [
    { z: 'z2', rho: 0.835 },
    { z: 'z3', rho: -0.660 },
    { z: 'z1', rho: -0.330 },
    { z: 'z5', rho: -0.249 },
    { z: 'z4', rho: -0.103 }
  ];

  function fmt(v) { return (v >= 0 ? '+' : '-') + Math.abs(v).toFixed(2); }

  var rows = '';
  for (var i = 0; i < data.length; i++) {
    var d = data[i], mag = Math.abs(d.rho);
    rows += '<div class="cc-row" style="--mag:' + mag.toFixed(3) + '">'
         +    '<span class="cc-label">' + d.z + '</span>'
         +    '<span class="cc-track"><span class="cc-bar"></span></span>'
         +    '<span class="cc-val">' + fmt(d.rho) + '</span>'
         +  '</div>';
  }
  var axis = '<div class="cc-axis"><span class="cc-scale"><span>0.0</span><span>0.5</span><span>1.0</span></span></div>';
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
