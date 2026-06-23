(function () {
  var INTER = "'Inter', 'Segoe UI', system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif";
  var FRAUNCES = "'Fraunces', Georgia, 'Times New Roman', serif";

  var CTHEMES = {
    maroon: {
      name: 'maroon', contour: null,
      paper: '#FBF8F4', ink: '#2B1F24', inkSoft: '#6B5D63', sub: '#8A7A73',
      grid: 'rgba(120,100,90,0.10)', line: 'rgba(120,100,90,0.30)',
      code: '#B79961', codeStroke: '#7E6432', unassigned: '#CBBFB4', font: INTER,
      clusters: ['#61223B', '#B79961', '#1D9E75', '#185FA5', '#D85A30', '#7A4E8C', '#2E9CA6', '#C2577E']
    },
    fable: {
      name: 'fable', contour: null,
      paper: '#F4ECD8', ink: '#34301F', inkSoft: '#756B4F', sub: '#8A7A52',
      grid: 'rgba(120,95,45,0.13)', line: 'rgba(90,70,40,0.32)',
      code: '#B07A24', codeStroke: '#7E5414', unassigned: '#CBB994', font: FRAUNCES,
      clusters: ['#A4503C', '#C0892E', '#5C7A3A', '#4A6B8A', '#2E7D6B', '#8A6D3B', '#9C5A74', '#6E8A4A']
    }
  };
  var CT = CTHEMES.maroon;

  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }
  function ease(t) { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); }
  function hx(h) { return [parseInt(h.substr(1, 2), 16), parseInt(h.substr(3, 2), 16), parseInt(h.substr(5, 2), 16)]; }
  function mix(a, b, t) {
    var A = hx(a), B = hx(b); t = clamp(t, 0, 1);
    return 'rgb(' + Math.round(A[0] + (B[0] - A[0]) * t) + ',' + Math.round(A[1] + (B[1] - A[1]) * t) + ',' + Math.round(A[2] + (B[2] - A[2]) * t) + ')';
  }

  function makeBridge(canvasId, opts) {
    var c = document.getElementById(canvasId);
    if (!c) { return null; }
    opts = opts || {};
    var mode = opts.colorMode || 'code';
    var ctx = c.getContext('2d'); var W, H;
    function rs() { var d = Math.min(window.devicePixelRatio || 1, 2); W = c.clientWidth || 320; H = c.clientHeight || 170; c.width = Math.round(W * d); c.height = Math.round(H * d); ctx.setTransform(d, 0, 0, d, 0, 0); }
    rs(); if (window.ResizeObserver) { new ResizeObserver(rs).observe(c); } window.addEventListener('resize', rs);
    var ps = [], acc = 0, active = false;
    function nodeFill(i) { return mode === 'cluster' ? CT.clusters[i % CT.clusters.length] : CT.code; }
    function nodeStroke(i) { return mode === 'cluster' ? CT.inkSoft : CT.codeStroke; }
    function partCol(i, p) { return mix(mode === 'cluster' ? CT.clusters[i % CT.clusters.length] : CT.code, CT.inkSoft, p); }
    function tick(dt) {
      if (!active) { return; }
      acc += dt;
      while (acc > 0.13) { acc -= 0.13; ps.push({ i: (Math.random() * 5) | 0, p: 0, sp: 0.5 + 0.12 * Math.random() }); }
      for (var i = 0; i < ps.length; i++) ps[i].p += ps[i].sp * dt;
      ps = ps.filter(function (o) { return o.p < 1; });
      draw();
    }
    function draw() {
      ctx.clearRect(0, 0, W, H);
      var cx = W / 2, topY = H * 0.16, convY = H * 0.52, tipY = H * 0.92, sp = (W * 0.42) / 4;
      ctx.strokeStyle = CT.line; ctx.lineWidth = 1; ctx.lineCap = 'round';
      for (var i = 0; i < 5; i++) { var sx = cx + (i - 2) * sp; ctx.beginPath(); ctx.moveTo(sx, topY); ctx.lineTo(cx, convY); ctx.stroke(); }
      ctx.beginPath(); ctx.moveTo(cx, convY); ctx.lineTo(cx, tipY - 11); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx, tipY); ctx.lineTo(cx - 7, tipY - 12); ctx.lineTo(cx + 7, tipY - 12); ctx.closePath(); ctx.fillStyle = CT.inkSoft; ctx.fill();
      for (i = 0; i < 5; i++) { var sx2 = cx + (i - 2) * sp; ctx.beginPath(); ctx.arc(sx2, topY, 4.6, 0, 7); ctx.fillStyle = nodeFill(i); ctx.fill(); ctx.strokeStyle = nodeStroke(i); ctx.lineWidth = 1; ctx.stroke(); }
      for (var j = 0; j < ps.length; j++) {
        var o = ps[j], x, y, sx3 = cx + (o.i - 2) * sp;
        if (o.p < 0.55) { var u = ease(o.p / 0.55); x = sx3 + (cx - sx3) * u; y = topY + (convY - topY) * u; }
        else { var u2 = ease((o.p - 0.55) / 0.45); x = cx; y = convY + ((tipY - 12) - convY) * u2; }
        ctx.beginPath(); ctx.arc(x, y, 2.6, 0, 7); ctx.fillStyle = partCol(o.i, o.p); ctx.globalAlpha = 0.9 * Math.sin(o.p * Math.PI); ctx.fill(); ctx.globalAlpha = 1;
      }
    }
    return { tick: tick, setActive: function (v) { active = v; } };
  }

  // Encoder head: a 2-layer feed-forward network pointing down, an arrow to a
  // 5-value output vector whose numbers drift continuously to random values.
  function makeEncoder(canvasId) {
    var c = document.getElementById(canvasId);
    if (!c) { return null; }
    var ctx = c.getContext('2d'); var W, H;
    function rs() { var d = Math.min(window.devicePixelRatio || 1, 2); W = c.clientWidth || 460; H = c.clientHeight || 230; c.width = Math.round(W * d); c.height = Math.round(H * d); ctx.setTransform(d, 0, 0, d, 0, 0); }
    rs(); if (window.ResizeObserver) { new ResizeObserver(rs).observe(c); } window.addEventListener('resize', rs);

    var LN = [7, 5, 5];            // input, hidden, output (the 5 numbers)
    var LY = [0.12, 0.34, 0.56];   // layer y, fraction of height
    var ps = [], acc = 0, active = false;
    var val = [0.5, -0.01, 0.98, 1.23, 4.2];
    var tgt = val.slice(), spd = [0, 0, 0, 0, 0];
    function retarget(i) { tgt[i] = -1.6 + 6.0 * Math.random(); spd[i] = 0.8 + 1.3 * Math.random(); }

    function nodeX(li, i) { var n = LN[li], span = Math.min(W * 0.9, 430) * [1.0, 0.56, 0.34][li]; return W / 2 + (i - (n - 1) / 2) * (span / Math.max(n - 1, 1)); }
    function nodeY(li) { return LY[li] * H; }
    function spawn() { ps.push({ a: (Math.random() * LN[0]) | 0, b: (Math.random() * LN[1]) | 0, c: (Math.random() * LN[2]) | 0, p: 0, sp: 0.30 + 0.12 * Math.random() }); }

    function tick(dt) {
      if (!active) { return; }
      for (var i = 0; i < 5; i++) {
        val[i] += (tgt[i] - val[i]) * Math.min(1, spd[i] * dt);
        if (Math.abs(tgt[i] - val[i]) < 0.04) { retarget(i); }
      }
      acc += dt;
      while (acc > 0.085) { acc -= 0.085; spawn(); }
      for (var j = 0; j < ps.length; j++) ps[j].p += ps[j].sp * dt;
      ps = ps.filter(function (o) { return o.p < 1; });
      draw();
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = CT.line; ctx.lineWidth = 1;
      for (var li = 0; li < 2; li++) {
        for (var i = 0; i < LN[li]; i++) {
          var x1 = nodeX(li, i), y1 = nodeY(li);
          for (var k = 0; k < LN[li + 1]; k++) { ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(nodeX(li + 1, k), nodeY(li + 1)); ctx.stroke(); }
        }
      }
      var ax = W / 2, ay0 = nodeY(2) + 16, ay1 = H * 0.72;
      ctx.strokeStyle = CT.inkSoft; ctx.lineWidth = 2; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(ax, ay0); ctx.lineTo(ax, ay1 - 9); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(ax, ay1); ctx.lineTo(ax - 6, ay1 - 10); ctx.lineTo(ax + 6, ay1 - 10); ctx.closePath(); ctx.fillStyle = CT.inkSoft; ctx.fill();
      for (var m = 0; m < ps.length; m++) {
        var o = ps[m], seg = o.p < 0.5 ? 0 : 1, u = ease((o.p - seg * 0.5) / 0.5);
        var fromI = seg === 0 ? o.a : o.b, toI = seg === 0 ? o.b : o.c;
        var x0 = nodeX(seg, fromI), y0 = nodeY(seg), xe = nodeX(seg + 1, toI), ye = nodeY(seg + 1);
        var x = x0 + (xe - x0) * u, y = y0 + (ye - y0) * u;
        ctx.beginPath(); ctx.arc(x, y, 2.4, 0, 7); ctx.fillStyle = mix(CT.code, CT.inkSoft, o.p); ctx.globalAlpha = 0.9 * Math.sin(o.p * Math.PI); ctx.fill(); ctx.globalAlpha = 1;
      }
      for (var li2 = 0; li2 < 3; li2++) {
        for (var i2 = 0; i2 < LN[li2]; i2++) {
          ctx.beginPath(); ctx.arc(nodeX(li2, i2), nodeY(li2), 4.2, 0, 7);
          ctx.fillStyle = CT.code; ctx.fill(); ctx.strokeStyle = CT.codeStroke; ctx.lineWidth = 1; ctx.stroke();
        }
      }
      var nums = val.map(function (v) { return (v >= 0 ? ' ' : '') + v.toFixed(2); }).join('  ');
      var lb = '[ ', rb = ' ]';
      var fs = Math.max(12, Math.min(18, W / 22));
      ctx.font = '600 ' + fs + 'px ui-monospace, "SF Mono", Menlo, Consolas, monospace';
      var total = ctx.measureText(lb + nums + rb).width, maxW = W * 0.92;
      if (total > maxW) { fs *= maxW / total; ctx.font = '600 ' + fs + 'px ui-monospace, "SF Mono", Menlo, Consolas, monospace'; }
      ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
      var wL = ctx.measureText(lb).width, wN = ctx.measureText(nums).width, wR = ctx.measureText(rb).width;
      var sx = W / 2 - (wL + wN + wR) / 2, vy = H * 0.88;
      ctx.fillStyle = CT.codeStroke; ctx.fillText(lb, sx, vy);
      ctx.fillStyle = CT.ink; ctx.fillText(nums, sx + wL, vy);
      ctx.fillStyle = CT.codeStroke; ctx.fillText(rb, sx + wL + wN, vy);
      ctx.textAlign = 'center';
    }

    return { tick: tick, setActive: function (v) { active = v; } };
  }

  function KM(canvasId, cfg) {
    var c = document.getElementById(canvasId);
    if (!c) { return null; }
    var ctx = c.getContext('2d'); var W, H;
    function rs() { var d = Math.min(window.devicePixelRatio || 1, 2); W = c.clientWidth || 400; H = c.clientHeight || 340; c.width = Math.round(W * d); c.height = Math.round(H * d); ctx.setTransform(d, 0, 0, d, 0, 0); }
    rs(); if (window.ResizeObserver) { new ResizeObserver(rs).observe(c); } window.addEventListener('resize', rs);
    var pad = cfg.pad || 16, K = cfg.K, stepEl = cfg.stepId ? document.getElementById(cfg.stepId) : null;
    var pts = [], cents = [], phase = 'init', timer = 0, prev = null, assignStr = '', iter = 0, cycle = 0, active = false, contours = [];

    function gauss() { return (Math.random() + Math.random() + Math.random() - 1.5); }
    function genContours() {
      var arr = [], nc = cfg.contourCentres || 3;
      for (var ci = 0; ci < nc; ci++) {
        var ccx = 0.18 + 0.64 * Math.random(), ccy = 0.18 + 0.64 * Math.random();
        var asp = 0.8 + 0.4 * Math.random();
        var ph1 = Math.random() * 6.283, ph2 = Math.random() * 6.283, ph3 = Math.random() * 6.283;
        var a1 = 0.10 + 0.10 * Math.random(), a2 = 0.05 + 0.07 * Math.random();
        var loops = 4 + ((Math.random() * 2) | 0);
        for (var L = 0; L < loops; L++) {
          var baseR = 0.05 + L * 0.052, pp = [];
          for (var a = 0; a <= 48; a++) {
            var th = a / 48 * 6.2832;
            var r = baseR * (1 + a1 * Math.sin(3 * th + ph1) + a2 * Math.sin(5 * th + ph2) + 0.06 * Math.sin(2 * th + ph3));
            pp.push({ x: ccx + Math.cos(th) * r * asp, y: ccy + Math.sin(th) * r });
          }
          arr.push({ pts: pp, bold: L === loops - 1 });
        }
      }
      return arr;
    }
    function drawContours() {
      for (var i = 0; i < contours.length; i++) {
        var lo = contours[i]; ctx.beginPath();
        for (var j = 0; j < lo.pts.length; j++) { var x = lo.pts[j].x * W, y = lo.pts[j].y * H; if (j) ctx.lineTo(x, y); else ctx.moveTo(x, y); }
        ctx.closePath();
        ctx.strokeStyle = lo.bold ? (CT.contourBold || CT.contour) : CT.contour;
        ctx.lineWidth = lo.bold ? 1.1 : 0.8;
        ctx.stroke();
      }
    }
    function gen() {
      pts = [];
      for (var b = 0; b < cfg.nb; b++) {
        var bx = 0.2 + 0.6 * Math.random(), by = 0.2 + 0.6 * Math.random();
        for (var i = 0; i < cfg.count; i++) {
          pts.push({ x: clamp(bx + gauss() * cfg.spread, 0.05, 0.95), y: clamp(by + gauss() * cfg.spread, 0.05, 0.95), cl: -1, fromCl: -1, toCl: -1, t: 1 });
        }
      }
    }
    function placeCents() {
      cents = []; var pool = pts.slice();
      for (var k = 0; k < K; k++) {
        var p = pool.length ? pool.splice((Math.random() * pool.length) | 0, 1)[0] : pts[(Math.random() * pts.length) | 0];
        cents.push({ x: p.x, y: p.y, sx: p.x, sy: p.y, tx: p.x, ty: p.y, mt: 1, k: k });
      }
    }
    function nearest(p) { var bi = 0, bd = 1e9; for (var k = 0; k < cents.length; k++) { var dx = p.x - cents[k].x, dy = p.y - cents[k].y, d = dx * dx + dy * dy; if (d < bd) { bd = d; bi = k; } } return bi; }
    function setStep(s) {
      if (!stepEl) { return; }
      var m = { init: '1   Place the centres', assign: '2   Assign points to the nearest', move: '3   Move centres to the mean', done: 'Converged   start again' };
      stepEl.textContent = m[s] || '';
    }
    function enterInit() { phase = 'init'; timer = 0; placeCents(); for (var i = 0; i < pts.length; i++) { var p = pts[i]; p.cl = -1; p.fromCl = -1; p.toCl = -1; p.t = 1; } iter = 0; prev = null; setStep('init'); }
    function enterAssign() { phase = 'assign'; timer = 0; iter++; for (var i = 0; i < pts.length; i++) { var p = pts[i]; p.fromCl = p.cl; p.toCl = nearest(p); p.t = 0; } setStep('assign'); }
    function enterMove() {
      phase = 'move'; timer = 0;
      for (var i = 0; i < pts.length; i++) pts[i].cl = pts[i].toCl;
      for (var k = 0; k < cents.length; k++) {
        var sx = 0, sy = 0, n = 0;
        for (var j = 0; j < pts.length; j++) { if (pts[j].cl === k) { sx += pts[j].x; sy += pts[j].y; n++; } }
        var c2 = cents[k]; c2.sx = c2.x; c2.sy = c2.y;
        if (n) { c2.tx = sx / n; c2.ty = sy / n; } else { c2.tx = c2.x; c2.ty = c2.y; }
        c2.mt = 0;
      }
      assignStr = pts.map(function (p) { return p.cl; }).join(',');
      setStep('move');
    }
    function enterDone() { phase = 'done'; timer = 0; setStep('done'); }

    contours = genContours(); gen(); enterInit();

    function tick(dt) {
      if (!active) { return; }
      timer += dt;
      if (phase === 'init') { if (timer >= cfg.initDur) enterAssign(); }
      else if (phase === 'assign') { var t = Math.min(timer / cfg.assignDur, 1); for (var i = 0; i < pts.length; i++) pts[i].t = t; if (timer >= cfg.assignDur) enterMove(); }
      else if (phase === 'move') {
        var t2 = Math.min(timer / cfg.moveDur, 1);
        for (var k = 0; k < cents.length; k++) cents[k].mt = t2;
        if (timer >= cfg.moveDur) {
          for (var k2 = 0; k2 < cents.length; k2++) { var c2 = cents[k2]; c2.x = c2.tx; c2.y = c2.ty; c2.sx = c2.x; c2.sy = c2.y; c2.mt = 1; }
          if (assignStr === prev || iter >= cfg.maxIter) { enterDone(); } else { prev = assignStr; enterAssign(); }
        }
      }
      else if (phase === 'done') { if (timer >= cfg.holdDur) { cycle++; if (cycle % 2 === 0) gen(); enterInit(); } }
      draw();
    }

    function mapX(nx) { return pad + nx * (W - 2 * pad); }
    function mapY(ny) { return pad + ny * (H - 2 * pad); }
    function colorOf(idx) { return idx < 0 ? CT.unassigned : CT.clusters[idx % CT.clusters.length]; }

    function draw() {
      ctx.clearRect(0, 0, W, H); ctx.fillStyle = CT.paper; ctx.fillRect(0, 0, W, H);
      if (CT.contour) { drawContours(); }
      else if (cfg.grid) {
        ctx.strokeStyle = CT.grid; ctx.lineWidth = 1; var g = 26; ctx.beginPath();
        for (var gx = g; gx < W; gx += g) { ctx.moveTo(gx, 0); ctx.lineTo(gx, H); }
        for (var gy = g; gy < H; gy += g) { ctx.moveTo(0, gy); ctx.lineTo(W, gy); }
        ctx.stroke();
      }
      if (cfg.lines && (phase === 'assign' || phase === 'move')) {
        ctx.strokeStyle = CT.line; ctx.lineWidth = 1;
        for (var i = 0; i < pts.length; i++) {
          var p = pts[i], c2 = cents[p.toCl]; if (!c2) { continue; }
          var ex = c2.sx + (c2.tx - c2.sx) * ease(c2.mt), ey = c2.sy + (c2.ty - c2.sy) * ease(c2.mt);
          ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.moveTo(mapX(p.x), mapY(p.y)); ctx.lineTo(mapX(ex), mapY(ey)); ctx.stroke(); ctx.globalAlpha = 1;
        }
      }
      for (var i2 = 0; i2 < pts.length; i2++) {
        var q = pts[i2], col = mix(colorOf(q.fromCl), colorOf(q.toCl), q.t);
        ctx.beginPath(); ctx.arc(mapX(q.x), mapY(q.y), cfg.ptR, 0, 7); ctx.fillStyle = col; ctx.globalAlpha = 0.92; ctx.fill(); ctx.globalAlpha = 1;
      }
      for (var k = 0; k < cents.length; k++) {
        var cc = cents[k];
        var ex2 = cc.sx + (cc.tx - cc.sx) * ease(cc.mt), ey2 = cc.sy + (cc.ty - cc.sy) * ease(cc.mt);
        var x = mapX(ex2), y = mapY(ey2), col2 = CT.clusters[k % CT.clusters.length], R = cfg.centR;
        ctx.strokeStyle = col2; ctx.lineWidth = 2.6; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(x - R, y - R); ctx.lineTo(x + R, y + R); ctx.moveTo(x + R, y - R); ctx.lineTo(x - R, y + R); ctx.stroke();
        ctx.beginPath(); ctx.arc(x, y, R + 3, 0, 7); ctx.lineWidth = 1.6; ctx.globalAlpha = 0.65; ctx.stroke(); ctx.globalAlpha = 1;
      }
    }

    return { tick: tick, setActive: function (v) { active = v; } };
  }

  var bridge = makeEncoder('bridgeCanvas');
  var bridge2 = makeBridge('bridgeCanvas2', { colorMode: 'cluster' });
  var clusterKM = KM('clusterCanvas', { K: 8, nb: 8, count: 10, spread: 0.05, initDur: 0.22, assignDur: 0.38, moveDur: 0.46, holdDur: 0.4, ptR: 3.4, centR: 8, lines: false, grid: false, maxIter: 9, contourCentres: 3 });

  var animators = [bridge, bridge2, clusterKM].filter(Boolean);
  var last = null;
  function loop(ts) { if (last == null) last = ts; var dt = Math.min((ts - last) / 1000, 0.05); last = ts; for (var i = 0; i < animators.length; i++) animators[i].tick(dt); requestAnimationFrame(loop); }
  requestAnimationFrame(loop);

  function vis(el, cb) {
    if (!el) { return; }
    if (!('IntersectionObserver' in window)) { cb(true); return; }
    new IntersectionObserver(function (es) { cb(es[0].isIntersecting); }, { threshold: 0.06 }).observe(el);
  }
  vis(document.getElementById('to-clustering'), function (on) { if (bridge) bridge.setActive(on); var bw = document.querySelector('#to-clustering .bridge-wrap'); if (bw) bw.classList.toggle('in', on); });
  vis(document.getElementById('clustering'), function (on) { if (clusterKM) clusterKM.setActive(on); });
  vis(document.getElementById('to-results'), function (on) { if (bridge2) bridge2.setActive(on); var bw2 = document.querySelector('#to-results .bridge-wrap'); if (bw2) bw2.classList.toggle('in', on); });
  vis(document.getElementById('results'), function (on) { var mp = document.querySelector('#results .map-panel'); if (mp) mp.classList.toggle('in', on); });

  window.clusterSetTheme = function (n) { if (CTHEMES[n]) { CT = CTHEMES[n]; } };
})();
