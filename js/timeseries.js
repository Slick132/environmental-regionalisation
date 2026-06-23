(function () {
  var cvs = document.getElementById('tsCanvas');
  if (!cvs || !window.TS_DATA) { return; }
  var ctx = cvs.getContext('2d');
  var W = 728, H = 560, DPR = 1;

  var INTER = "'Inter', 'Segoe UI', system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif";
  var FRAUNCES = "'Fraunces', Georgia, 'Times New Roman', serif";
  var THEMES = {
    maroon: { font: INTER, ink: '#2B1F24', muted: '#6B5D63', grid: 'rgba(120,100,90,0.13)', axis: 'rgba(120,100,90,0.34)',
              cols: ['#61223B', '#9C5A74', '#1D9E75', '#5FB89A', '#185FA5', '#D85A30'] },
    fable: { font: FRAUNCES, ink: '#34301F', muted: '#756B4F', grid: 'rgba(120,95,45,0.16)', axis: 'rgba(90,70,40,0.38)',
             cols: ['#A4503C', '#C0892E', '#2E7D6B', '#7BAE92', '#4A6B8A', '#C0892E'] }
  };
  function curTheme() { return document.documentElement.getAttribute('data-theme') === 'fable' ? THEMES.fable : THEMES.maroon; }
  var TH = curTheme();

  var D = window.TS_DATA;
  var DEG = String.fromCharCode(176);
  var SERIES = [
    { key: 'tmax',  name: 'Max temp', unit: DEG + 'C',  kind: 'line' },
    { key: 'tmin',  name: 'Min temp', unit: DEG + 'C',  kind: 'line' },
    { key: 'rhmax', name: 'Max RH',   unit: '%',         kind: 'line' },
    { key: 'rhmin', name: 'Min RH',   unit: '%',         kind: 'line' },
    { key: 'precip', name: 'Precip',  unit: 'mm',        kind: 'bar' },
    { key: 'wind',  name: 'Wind',     unit: 'm/s',       kind: 'line' }
  ];
  var N = D.tmax.length;
  var MONTH0 = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  var MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  function resize() {
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = cvs.clientWidth || 728; H = cvs.clientHeight || 560;
    cvs.width = Math.round(W * DPR); cvs.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    draw();
  }

  function niceRound(v) { var a = Math.abs(v); return a >= 100 ? Math.round(v) : (a >= 10 ? Math.round(v) : Math.round(v * 10) / 10); }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    var padL = 72, padR = 14, padT = 6, padB = 20, gap = 12;
    var plotW = W - padL - padR;
    var panelH = (H - padT - padB - gap * 5) / SERIES.length;
    function px(i) { return padL + (i / (N - 1)) * plotW; }

    // faint vertical month gridlines across the whole stack
    var stackBot = padT + SERIES.length * panelH + (SERIES.length - 1) * gap;
    ctx.strokeStyle = TH.grid; ctx.lineWidth = 1;
    for (var m = 0; m < 12; m++) {
      var gx = px(MONTH0[m]);
      ctx.beginPath(); ctx.moveTo(gx, padT); ctx.lineTo(gx, stackBot); ctx.stroke();
    }

    var nDraw = Math.max(1, Math.ceil(prog * N));

    for (var s = 0; s < SERIES.length; s++) {
      var spec = SERIES[s], vals = D[spec.key], col = TH.cols[s];
      var top = padT + s * (panelH + gap), bot = top + panelH;
      var mn = Infinity, mx = -Infinity;
      for (var i = 0; i < N; i++) { if (vals[i] < mn) mn = vals[i]; if (vals[i] > mx) mx = vals[i]; }
      var ymin, ymax;
      if (spec.kind === 'bar') { ymin = 0; ymax = mx * 1.08 || 1; }
      else { var r = (mx - mn) || 1; ymin = mn - 0.08 * r; ymax = mx + 0.08 * r; }
      function py(v) { return bot - (v - ymin) / (ymax - ymin) * panelH; }

      // baseline
      ctx.strokeStyle = TH.axis; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(padL, bot + 0.5); ctx.lineTo(padL + plotW, bot + 0.5); ctx.stroke();

      // y-tick labels (min and max)
      ctx.fillStyle = TH.muted; ctx.font = '9px ' + TH.font; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
      ctx.fillText(String(niceRound(spec.kind === 'bar' ? mx : mx)), padL - 5, py(spec.kind === 'bar' ? mx : mx) + 1);
      ctx.fillText(String(niceRound(spec.kind === 'bar' ? 0 : mn)), padL - 5, py(spec.kind === 'bar' ? 0 : mn) - 1);

      // series
      if (spec.kind === 'bar') {
        var bw = Math.max(1, plotW / N * 0.85);
        ctx.fillStyle = col;
        for (var b = 0; b < nDraw; b++) { var h = bot - py(vals[b]); if (h > 0) ctx.fillRect(px(b) - bw / 2, py(vals[b]), bw, h); }
      } else {
        ctx.strokeStyle = col; ctx.lineWidth = 1.4; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
        ctx.beginPath();
        for (var j = 0; j < nDraw; j++) { var X = px(j), Y = py(vals[j]); if (j) ctx.lineTo(X, Y); else ctx.moveTo(X, Y); }
        ctx.stroke();
      }

      // left label: name + unit, centred in the panel
      ctx.fillStyle = TH.ink; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
      ctx.font = '600 11px ' + TH.font;
      ctx.fillText(spec.name, 50, (top + bot) / 2 - 7);
      ctx.fillStyle = TH.muted; ctx.font = '9px ' + TH.font;
      ctx.fillText('(' + spec.unit + ')', 50, (top + bot) / 2 + 7);
    }

    // month labels along the bottom, thinned out when they would crowd
    ctx.fillStyle = TH.muted; ctx.font = '9px ' + TH.font; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    var spacing = plotW / 11;
    var step = spacing >= 30 ? 1 : (spacing >= 20 ? 2 : 3);
    for (var k = 0; k < 12; k += step) { ctx.fillText(MONTH[k], px(MONTH0[k]), stackBot + 5); }
  }

  // --- one-time draw-in -----------------------------------------------------
  var prog = 0, started = false, t0 = null, DUR = 1.35;
  function frame(ts) {
    if (t0 == null) t0 = ts;
    var e = (ts - t0) / 1000, raw = Math.min(1, e / DUR);
    prog = raw * raw * (3 - 2 * raw);
    draw();
    if (raw < 1) { requestAnimationFrame(frame); } else { prog = 1; draw(); }
  }
  function reveal() { if (started) { return; } started = true; t0 = null; requestAnimationFrame(frame); }

  resize();
  if (window.ResizeObserver) { new ResizeObserver(resize).observe(cvs); }
  window.addEventListener('resize', resize);
  new MutationObserver(function () { TH = curTheme(); draw(); }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { reveal(); io.disconnect(); } }, { threshold: 0.3 });
    io.observe(cvs);
  } else { prog = 1; reveal(); }
})();
