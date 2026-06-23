(function () {
  var cvs = document.getElementById('aeCanvas');
  if (!cvs) { return; }
  var ctx = cvs.getContext('2d');
  var W = 680, H = 470, DPR = 1;

  function resize() {
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = cvs.clientWidth || 680;
    H = cvs.clientHeight || 470;
    cvs.width = Math.round(W * DPR);
    cvs.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  resize();
  if (window.ResizeObserver) { new ResizeObserver(resize).observe(cvs); }
  window.addEventListener('resize', resize);

  var INTER = "'Inter', 'Segoe UI', system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif";
  var FRAUNCES = "'Fraunces', Georgia, 'Times New Roman', serif";

  var CHANS = [
    { short: 'Tmax',  long: 'Tmax',          kind: 'tmax' },
    { short: 'Tmin',  long: 'Tmin',          kind: 'tmin' },
    { short: 'RHmax', long: 'RH max',        kind: 'rhmax' },
    { short: 'RHmin', long: 'RH min',        kind: 'rhmin' },
    { short: 'Precip', long: 'Precipitation', kind: 'precip' },
    { short: 'Wind',  long: 'Wind',          kind: 'wind' }
  ];
  var N = CHANS.length;

  var THEMES = {
    maroon: {
      font: INTER, paper: '#FBF8F4', sub: '#8A7A73',
      encNode: '#F0E2E7', encStroke: '#61223B',
      decNode: '#E2F2EC', decStroke: '#1D9E75',
      code: '#B79961', codeStroke: '#7E6432', codeLabel: '#5C4A20', codeGlow: 'rgba(183,153,97,0.30)',
      pIn: '#61223B', pMid: '#B79961', pOut: '#1D9E75',
      wireIn: 'rgba(120,100,90,0.05)', wire: 'rgba(120,100,90,0.10)',
      chanCols: ['#61223B', '#9C5A74', '#1D9E75', '#5FB89A', '#185FA5', '#D85A30']
    },
    fable: {
      font: FRAUNCES, paper: '#F4ECD8', sub: '#8A7A52',
      encNode: '#EAD9C4', encStroke: '#A4503C',
      decNode: '#DDE7CC', decStroke: '#5C7A3A',
      code: '#B07A24', codeStroke: '#7E5414', codeLabel: '#5A3E12', codeGlow: 'rgba(176,122,36,0.30)',
      pIn: '#A4503C', pMid: '#B07A24', pOut: '#2E7D6B',
      wireIn: 'rgba(90,70,40,0.06)', wire: 'rgba(90,70,40,0.13)',
      chanCols: ['#A4503C', '#C08A6A', '#2E7D6B', '#7BAE92', '#4A6B8A', '#C0892E']
    }
  };
  var TH = THEMES.maroon;

  function frac(x) { return x - Math.floor(x); }
  function hash(x) { return frac(Math.sin(x * 12.9898 + 78.233) * 43758.5453); }
  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }

  function sig(ci, day) {
    var k = CHANS[ci].kind, v;
    if (k === 'tmax') v = 0.34 + 0.34 * Math.sin(2 * Math.PI * day / 365 - 1.6) + 0.022 * Math.sin(2 * Math.PI * day / 30);
    else if (k === 'tmin') v = 0.24 + 0.27 * Math.sin(2 * Math.PI * day / 365 - 1.4) + 0.022 * Math.sin(2 * Math.PI * day / 30 + 1);
    else if (k === 'rhmax') v = 0.64 + 0.18 * Math.sin(2 * Math.PI * day / 365 + 1.4) + 0.02 * Math.sin(2 * Math.PI * day / 30 + 2);
    else if (k === 'rhmin') v = 0.40 + 0.20 * Math.sin(2 * Math.PI * day / 365 + 1.65) + 0.02 * Math.sin(2 * Math.PI * day / 30 + 2.6);
    else if (k === 'precip') {
      var env = 0.5 + 0.5 * Math.sin(2 * Math.PI * day / 365 + 0.6);
      var hump = Math.pow(Math.max(0, Math.sin(2 * Math.PI * day / 17 + 1.3 * hash(Math.floor(day / 17)))), 4);
      v = 0.09 + 0.62 * env * hump;
    }
    else v = 0.46 + 0.20 * Math.sin(2 * Math.PI * day / 365 + 2.7) + 0.08 * Math.sin(2 * Math.PI * day / 26) + 0.045 * (hash(Math.floor(day / 4)) - 0.5);
    return clamp(v, 0.04, 0.96);
  }
  function recon(ci, day) {
    return clamp(0.5 * sig(ci, day) + 0.25 * sig(ci, day - 3) + 0.25 * sig(ci, day + 3), 0.04, 0.96);
  }
  function hx(h) { return [parseInt(h.substr(1, 2), 16), parseInt(h.substr(3, 2), 16), parseInt(h.substr(5, 2), 16)]; }
  function mix(a, b, t) {
    var A = hx(a), B = hx(b); t = clamp(t, 0, 1);
    return 'rgb(' + Math.round(A[0] + (B[0] - A[0]) * t) + ',' + Math.round(A[1] + (B[1] - A[1]) * t) + ',' + Math.round(A[2] + (B[2] - A[2]) * t) + ')';
  }

  var scroll = 22, windowDays = 150;
  function spark(x0, x1, yc, h, fn, col, lw, alpha) {
    ctx.save(); ctx.beginPath();
    var n = 88;
    for (var i = 0; i <= n; i++) {
      var u = i / n; var x = x0 + (x1 - x0) * u; var day = CLOCK * scroll + u * windowDays;
      var v = fn(day); var y = yc + (0.5 - v) * h;
      if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
    }
    ctx.strokeStyle = col; ctx.globalAlpha = alpha; ctx.lineWidth = lw;
    ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke(); ctx.restore();
  }

  var Ln = [8, 6, 5, 6, 8];
  var parts = [], spawnAcc = 0;
  function spawn() {
    parts.push({
      cIn: (Math.random() * N) | 0, cOut: (Math.random() * N) | 0,
      a: (Math.random() * 8) | 0, b: (Math.random() * 6) | 0, c: (Math.random() * 5) | 0,
      d: (Math.random() * 6) | 0, e: (Math.random() * 8) | 0,
      p: 0, sp: 0.22 + 0.06 * Math.random()
    });
  }
  function update(dt) {
    spawnAcc += dt;
    while (spawnAcc > 0.068) { spawnAcc -= 0.068; spawn(); }
    for (var i = 0; i < parts.length; i++) parts[i].p += parts[i].sp * dt;
    parts = parts.filter(function (p) { return p.p < 1; });
  }

  var CLOCK = 0, last = null, running = true;
  function frame(ts) {
    if (last == null) last = ts;
    var dt = Math.min((ts - last) / 1000, 0.05); last = ts;
    if (running) { CLOCK += dt; update(dt); }
    draw();
    requestAnimationFrame(frame);
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = TH.paper; ctx.fillRect(0, 0, W, H);

    var narrow = W < 600;
    var headerFs = narrow ? 11 : 12;
    var labelFs = 12;
    var labelGap = 8;

    // Reserve a left margin sized to the widest channel label so labels never
    // clip off the edge on a narrow phone screen.
    ctx.font = labelFs + 'px ' + TH.font;
    var labW = 0;
    for (var qi = 0; qi < N; qi++) { labW = Math.max(labW, ctx.measureText(CHANS[qi].short).width); }

    var sparkW = narrow ? 44 : Math.round(0.135 * W);
    var mRight = narrow ? 10 : Math.round(0.05 * W);
    var netGap = narrow ? 16 : Math.round(0.045 * W);

    var plotTop = narrow ? 74 : 64, plotBot = H - 34;
    var availH = plotBot - plotTop, cy = (plotTop + plotBot) / 2;
    var P = availH / 7 * (narrow ? 0.86 : 0.92);
    function ny(li, j) { return cy + (j - (Ln[li] - 1) / 2) * P; }
    var bandH = availH / N;
    function yc(ci) { return plotTop + (ci + 0.5) * bandH; }

    var xInL = Math.round(labW + labelGap + 6);
    var xInR = xInL + sparkW;
    var xOutR = W - mRight;
    var xOutL = xOutR - sparkW;
    var netL = xInR + netGap, netR = xOutL - netGap;
    var Lx = [0, 1, 2, 3, 4].map(function (i) { return netL + (netR - netL) * (i / 4); });

    ctx.strokeStyle = TH.wireIn; ctx.lineWidth = 0.6; ctx.beginPath();
    for (var ci = 0; ci < N; ci++) for (var j0 = 0; j0 < Ln[0]; j0++) { ctx.moveTo(xInR, yc(ci)); ctx.lineTo(Lx[0], ny(0, j0)); }
    for (var co = 0; co < N; co++) for (var j4 = 0; j4 < Ln[4]; j4++) { ctx.moveTo(Lx[4], ny(4, j4)); ctx.lineTo(xOutL, yc(co)); }
    ctx.stroke();

    ctx.strokeStyle = TH.wire; ctx.lineWidth = 0.6; ctx.beginPath();
    for (var li = 0; li < 4; li++) for (var j = 0; j < Ln[li]; j++) {
      var x1 = Lx[li], y1 = ny(li, j);
      for (var k = 0; k < Ln[li + 1]; k++) { ctx.moveTo(x1, y1); ctx.lineTo(Lx[li + 1], ny(li + 1, k)); }
    }
    ctx.stroke();

    var xStart = xInR, xEnd = xOutL, xMid = Lx[2];
    for (var pi = 0; pi < parts.length; pi++) {
      var pt = parts[pi];
      var wx = [xStart, Lx[0], Lx[1], Lx[2], Lx[3], Lx[4], xEnd];
      var wy = [yc(pt.cIn), ny(0, pt.a), ny(1, pt.b), ny(2, pt.c), ny(3, pt.d), ny(4, pt.e), yc(pt.cOut)];
      var fp = pt.p * 6, seg = Math.min(5, Math.floor(fp)), u = fp - seg;
      var x = wx[seg] + (wx[seg + 1] - wx[seg]) * u, y = wy[seg] + (wy[seg + 1] - wy[seg]) * u;
      var col = x <= xMid ? mix(TH.pIn, TH.pMid, (x - xStart) / (xMid - xStart)) : mix(TH.pMid, TH.pOut, (x - xMid) / (xEnd - xMid));
      var fade = clamp(Math.min(pt.p, 1 - pt.p) * 9, 0, 1);
      ctx.beginPath(); ctx.arc(x, y, 2.7, 0, 7); ctx.fillStyle = col; ctx.globalAlpha = 0.9 * fade; ctx.fill();
    }
    ctx.globalAlpha = 1;

    for (var L = 0; L < 5; L++) {
      for (var m = 0; m < Ln[L]; m++) {
        var nx = Lx[L], nyy = ny(L, m);
        if (L === 2) {
          var r = 9 * (1 + 0.06 * Math.sin(CLOCK * 2 + m));
          ctx.beginPath(); ctx.arc(nx, nyy, r + 3, 0, 7); ctx.fillStyle = TH.codeGlow; ctx.fill();
          ctx.beginPath(); ctx.arc(nx, nyy, r, 0, 7); ctx.fillStyle = TH.code; ctx.fill();
          ctx.strokeStyle = TH.codeStroke; ctx.lineWidth = 1; ctx.stroke();
          ctx.fillStyle = TH.codeLabel; ctx.font = (narrow ? 10 : 11) + 'px ' + TH.font; ctx.textAlign = 'left';
          ctx.fillText('z' + (m + 1), nx + r + (narrow ? 3 : 6), nyy + 4);
        } else {
          var enc = L < 2;
          ctx.beginPath(); ctx.arc(nx, nyy, 6, 0, 7);
          ctx.fillStyle = enc ? TH.encNode : TH.decNode; ctx.fill();
          ctx.strokeStyle = enc ? TH.encStroke : TH.decStroke; ctx.lineWidth = 1; ctx.stroke();
        }
      }
    }

    ctx.textAlign = 'right'; ctx.font = labelFs + 'px ' + TH.font;
    for (var ic = 0; ic < N; ic++) {
      (function (ic) {
        ctx.fillStyle = TH.chanCols[ic];
        ctx.fillText(CHANS[ic].short, xInL - labelGap, yc(ic) + 4);
        spark(xInL, xInR, yc(ic), bandH * 0.62, function (d) { return sig(ic, d); }, TH.chanCols[ic], 2, 0.95);
      })(ic);
    }
    for (var oc = 0; oc < N; oc++) {
      (function (oc) {
        spark(xOutL, xOutR, yc(oc), bandH * 0.62, function (d) { return recon(oc, d); }, TH.pOut, 2, 0.95);
      })(oc);
    }

    ctx.textAlign = 'center'; ctx.fillStyle = TH.sub; ctx.font = headerFs + 'px ' + TH.font;
    var hy = plotTop - 16;
    ctx.fillText(narrow ? 'daily input' : 'daily climate input', (xInL + xInR) / 2, hy);
    ctx.fillText(narrow ? 'code' : '5-number code', Lx[2], hy);
    ctx.fillText(narrow ? 'output' : 'reconstruction', (xOutL + xOutR) / 2, hy);
  }

  function buildLegend() {
    var el = document.getElementById('aeLegend');
    if (!el) { return; }
    var html = '';
    for (var i = 0; i < N; i++) {
      html += '<span class="item"><span class="swatch" style="background:' + TH.chanCols[i] + ';"></span>' + CHANS[i].long + '</span>';
    }
    html += '<span class="item"><span class="swatch dot" style="background:' + TH.code + ';"></span>5-number code</span>';
    html += '<span class="item"><span class="swatch" style="background:' + TH.pOut + ';"></span>reconstruction</span>';
    el.innerHTML = html;
  }

  window.aeSetTheme = function (name) {
    if (THEMES[name]) { TH = THEMES[name]; buildLegend(); }
  };

  var ICON_PAUSE = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5h3v14H7zM14 5h3v14h-3z"/></svg>';
  var ICON_PLAY = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
  var btn = document.getElementById('aeToggle');
  if (btn) {
    btn.innerHTML = ICON_PAUSE;
    btn.addEventListener('click', function () {
      running = !running; last = null;
      btn.innerHTML = running ? ICON_PAUSE : ICON_PLAY;
      btn.setAttribute('aria-label', running ? 'Pause animation' : 'Play animation');
    });
  }

  buildLegend();
  requestAnimationFrame(frame);
})();
