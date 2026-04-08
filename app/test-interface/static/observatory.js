/* TTT Observatory — live monitoring UI (vanilla JS + SVG).
 *
 * v0.2 Sprint A:
 *   - 3-screen tabbed layout (MAPS / DASHBOARD / ACTIVITY)
 *   - MAPS: full parity with /map viewer — chokepoints, theater-link badges,
 *     compact unit batching, jitter, country labels, inspector panel
 *   - Battle visualization: combat ticker + on-map 💥 markers + attack arrows
 *   - Movement animations (tween units between rounds, fade-in reserves)
 *   - Round timer + total elapsed timer
 *
 * Reads map config from window.MAP_CONFIG.
 */
(function () {
  'use strict';

  // ================================================================
  // State
  // ================================================================
  var state = {
    runtime: null,
    round: 0,
    prevRound: null,
    scenario: 'start_one',
    totalRounds: 6,
    speedSec: 15,
    paused: false,

    // Data caches
    globalMap: null,
    theaters: { eastern_ereb: null, mashriq: null },
    countries: {},      // { id: {id,name,colors,...} }
    palette: {},
    units: [],          // current round units
    unitsByHex: {},     // "row,col" -> array of units
    countryStates: [],  // current round country snapshots
    events: [],         // most recent first
    combats: [],        // current round combats
    blockades: [],      // declared blockades for current round
    globalSeries: [],   // [{round_num, oil_price, stock_index, bond_yield, gold_price}, ...]
    viewRound: null,    // round selected in scrubber (null = current)
    chartMetric: 'oil_price',  // which metric to chart
    lastEventId: null,

    // Map view
    view: 'global',     // 'global' | 'eastern_ereb' | 'mashriq'

    // UI
    pollTimer: null,
    pollInterval: 3000, // ms

    // Animation / movement tracking
    prevUnitPositions: {}, // unit_id -> "row,col" from the previous render
    roundStartedAt: null,
    currentScreen: 'maps',

    // Dashboard sort / prev-round cache for deltas
    dashSort: 'code',       // 'code'|'gdp'|'stability'|'units'|'nuclear'
    prevCountryStates: {},  // country_code -> last seen snapshot
    decisionsByCountry: {}, // country_code -> last action committed this round

    // Activity feed filters
    feedFilterType: 'all',  // 'all'|'round'|'action'|'combat'|'memory'|'diplomatic'
    feedFilterCountry: '',
    feedFilterRound: '',
    feedSearch: '',
  };

  var THEATER_LABELS = (function () {
    var out = {};
    var cfg = (window.MAP_CONFIG && window.MAP_CONFIG.THEATERS) || {};
    Object.keys(cfg).forEach(function (k) { out[k] = cfg[k].display_name; });
    return out;
  })();

  // ================================================================
  // Init
  // ================================================================
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    wireControls();
    wireScreenNav();
    Promise.all([
      fetchJSON('/api/map/countries').then(function (d) {
        state.countries = d.countries || {};
        state.palette = d.palette || {};
      }),
      fetchJSON('/api/map/global').then(function (d) { state.globalMap = d; }),
      fetchJSON('/api/map/theater/eastern_ereb').then(function (d) { state.theaters.eastern_ereb = d; }).catch(noop),
      fetchJSON('/api/map/theater/mashriq').then(function (d) { state.theaters.mashriq = d; }).catch(noop),
    ]).then(function () {
      renderCountryGrid();
      renderMap();
      refreshAll();
      startPolling();
      tryRealtime();
      setPill('ok', 'live');
    }).catch(function (err) {
      console.error('Observatory init failed', err);
      setPill('err', 'init failed');
      showMapError('Failed to load base config: ' + err.message);
    });
  }

  function wireControls() {
    document.getElementById('btnNewRun').addEventListener('click', onNewRun);
    document.getElementById('btnStart').addEventListener('click', onStart);
    document.getElementById('btnPause').addEventListener('click', onPause);
    document.getElementById('btnResume').addEventListener('click', onResume);
    document.getElementById('btnStop').addEventListener('click', onStop);
    document.getElementById('btnRewind').addEventListener('click', onRewind);
    document.getElementById('speedSelect').addEventListener('change', onSpeedChange);
    document.getElementById('detailClose').addEventListener('click', closeDetail);
    var backBtn = document.getElementById('btnMapBack');
    if (backBtn) backBtn.addEventListener('click', function () { setMapView('global'); });
  }

  function wireScreenNav() {
    var tabs = document.querySelectorAll('.obs-nav-tab');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var screen = tab.getAttribute('data-screen');
        switchScreen(screen);
      });
    });
  }

  function switchScreen(screen) {
    state.currentScreen = screen;
    document.querySelectorAll('.obs-nav-tab').forEach(function (t) {
      t.classList.toggle('active', t.getAttribute('data-screen') === screen);
    });
    document.querySelectorAll('.obs-screen').forEach(function (s) {
      s.classList.toggle('active', s.id === 'screen-' + screen);
    });
  }

  // ================================================================
  // Polling
  // ================================================================
  function startPolling() {
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = setInterval(refreshAll, state.pollInterval);
  }

  function refreshAll() {
    // Use the scrubbed round if user is browsing history, else current
    var dataRound = state.viewRound != null ? state.viewRound : state.round;
    var sc = encodeURIComponent(state.scenario);
    Promise.all([
      fetchJSON('/api/observatory/state').catch(noop),
      fetchJSON('/api/observatory/units?round=' + dataRound + '&scenario=' + sc).catch(noop),
      fetchJSON('/api/observatory/countries?round=' + dataRound + '&scenario=' + sc).catch(noop),
      fetchJSON('/api/observatory/events?limit=50&scenario=' + sc).catch(noop),
      fetchJSON('/api/observatory/combats?round=' + dataRound + '&scenario=' + sc).catch(noop),
      fetchJSON('/api/observatory/blockades?round=' + dataRound + '&scenario=' + sc).catch(noop),
      fetchJSON('/api/observatory/global-series?scenario=' + sc).catch(noop),
    ]).then(function (res) {
      var rt = res[0], un = res[1], co = res[2], ev = res[3], cb = res[4], bl = res[5], gs = res[6];
      if (rt) applyRuntime(rt);
      // Don't overwrite user's scrubbed view with current-round data
      // during active run. Only apply units/countries if no scrub active
      // OR if the runtime is not running (finished/idle/paused).
      var runtimeStatus = rt ? (rt.status || 'idle') : 'idle';
      var isLive = (state.viewRound == null) || runtimeStatus !== 'running';
      if (isLive) {
        if (un) applyUnits(un);
        if (co) applyCountries(co);
      }
      if (cb && isLive) applyCombats(cb);
      if (ev) applyEvents(ev);
      if (bl && isLive) applyBlockades(bl);
      if (gs) applyGlobalSeries(gs);
    });
  }

  function applyBlockades(bl) {
    state.blockades = bl.blockades || [];
    // re-render map so blockade contours update
    renderMap();
  }

  function applyGlobalSeries(gs) {
    state.globalSeries = gs.rounds || [];
    renderGlobalStrip();
    renderGlobalChart();
  }

  // ================================================================
  // State appliers
  // ================================================================
  function applyRuntime(rt) {
    state.runtime = rt;
    var status = rt.status || 'idle';
    var round = rt.current_round != null ? rt.current_round : 0;
    state.totalRounds = rt.total_rounds || state.totalRounds;
    state.speedSec = rt.speed_sec || state.speedSec;
    if (status === 'idle' && rt.db_latest_round != null && rt.db_latest_round > round) {
      round = rt.db_latest_round;
    }
    if (round !== state.round) {
      state.prevRound = state.round;
      state.round = round;
      state.roundStartedAt = Date.now();
    }
    document.getElementById('roundCurrent').textContent = state.round;
    document.getElementById('roundTotal').textContent = state.totalRounds;
    var badge = document.getElementById('runStatusBadge');
    badge.textContent = status.toUpperCase();
    badge.setAttribute('data-status', status);
    var nameEl = document.getElementById('runName');
    if (nameEl) nameEl.textContent = rt.run_name ? '📛 ' + rt.run_name : '';
    state.startedAt = rt.started_at || state.startedAt;
    // Timer: only tick while RUNNING. Pause/stop/finish = freeze clock.
    if (status === 'running' && !state.timerInterval) {
      state.timerInterval = setInterval(tickTimer, 1000);
      if (!state.roundStartedAt) state.roundStartedAt = Date.now();
    }
    if (status !== 'running' && state.timerInterval) {
      clearInterval(state.timerInterval); state.timerInterval = null;
      if (status === 'idle') {
        var tEl = document.getElementById('runTimer');
        if (tEl) tEl.textContent = '⏱ 00:00';
        var rtEl = document.getElementById('roundTimer');
        if (rtEl) rtEl.textContent = '◷ 00:00';
        state.roundStartedAt = null;
      }
      // paused/finished: keep the final timer values displayed (frozen)
    }
    tickTimer();
  }

  function tickTimer() {
    var tEl = document.getElementById('runTimer');
    var rtEl = document.getElementById('roundTimer');
    var pad = function (n) { return n < 10 ? '0' + n : String(n); };
    var fmt = function (secs) {
      var hh = Math.floor(secs / 3600);
      var mm = Math.floor((secs % 3600) / 60);
      var ss = secs % 60;
      return (hh > 0 ? pad(hh) + ':' : '') + pad(mm) + ':' + pad(ss);
    };
    if (tEl && state.startedAt) {
      var started = Date.parse(state.startedAt);
      if (!isNaN(started)) {
        var secs = Math.max(0, Math.floor((Date.now() - started) / 1000));
        tEl.textContent = '⏱ ' + fmt(secs);
      }
    }
    if (rtEl && state.roundStartedAt) {
      var rsecs = Math.max(0, Math.floor((Date.now() - state.roundStartedAt) / 1000));
      rtEl.textContent = '◷ ' + fmt(rsecs);
    }
  }

  function applyUnits(un) {
    // Save prior positions BEFORE updating
    var priorPos = {};
    Object.keys(state.prevUnitPositions).forEach(function (k) { priorPos[k] = state.prevUnitPositions[k]; });

    state.units = un.units || [];
    var byHex = {};
    var newPos = {};
    state.units.forEach(function (u) {
      var r = u.global_row, c = u.global_col;
      var uid = u.unit_code || u.unit_id;
      if (r == null || c == null) {
        if (uid) newPos[uid] = null; // reserve / embarked
        return;
      }
      var key = r + ',' + c;
      (byHex[key] = byHex[key] || []).push(u);
      if (uid) newPos[uid] = key;
    });
    state.unitsByHex = byHex;

    // Diff to produce per-unit animation deltas
    var moved = {};
    Object.keys(newPos).forEach(function (uid) {
      var prev = priorPos[uid];
      var now = newPos[uid];
      if (prev && now && prev !== now) {
        moved[uid] = { from: prev, to: now, kind: 'move' };
      } else if (!prev && now) {
        moved[uid] = { from: null, to: now, kind: 'deploy' };
      }
    });
    state.prevUnitPositions = newPos;
    renderMap(moved);
    setMeta('mapMeta', state.units.length + ' units · src:' + (un.source || '?'));
  }

  function applyCountries(co) {
    // Cache previous snapshot for delta rendering
    var prevMap = {};
    (state.countryStates || []).forEach(function (cs) {
      var code = cs.country_code || cs.country_id;
      if (code) prevMap[code] = cs;
    });
    // Only update prevCountryStates if round changed
    var newRound = co.round || state.round;
    var wasRound = state._prevRoundForDeltas;
    if (wasRound !== newRound && wasRound != null) {
      state.prevCountryStates = prevMap;
    } else if (!state.prevCountryStates || !Object.keys(state.prevCountryStates).length) {
      // First load — seed prev = current so deltas are 0 rather than huge
      state.prevCountryStates = prevMap;
    }
    state._prevRoundForDeltas = newRound;
    state.countryStates = co.countries || [];
    updateCountryTiles();
    setMeta('dashMeta', state.countryStates.length + ' countries · src:' + (co.source || '?'));
  }

  function applyEvents(ev) {
    var incoming = (ev.events || []).slice();
    state.events = incoming;
    // Extract latest committed action per country (from agent_committed events in current round)
    var curRound = state.round;
    var decisions = {};
    incoming.forEach(function (e) {
      if (e.event_type !== 'agent_committed' || e.round_num !== curRound) return;
      var c = e.country_code;
      if (!c) return;
      // Parse summary like "Sakura committed military_move"
      var m = /committed\s+(\S+)/.exec(e.summary || '');
      var actionType = m ? m[1] : (e.payload && e.payload.action_type) || 'action';
      if (!decisions[c] || new Date(e.created_at) > new Date(decisions[c]._ts)) {
        decisions[c] = { action_type: actionType, _ts: e.created_at };
      }
    });
    state.decisionsByCountry = decisions;
    updateCountryTiles();
    renderFeed();
    setMeta('feedMeta', state.events.length + ' events');
  }

  function applyCombats(cb) {
    state.combats = cb.combats || [];
    renderCombatTicker();
    renderBattleMarkers();
    setMeta('combatMeta', state.combats.length + ' combat' + (state.combats.length === 1 ? '' : 's'));
  }

  // ================================================================
  // Country Dashboard
  // ================================================================
  function renderCountryGrid() {
    wireDashSort();
    updateCountryTiles();
  }

  function wireDashSort() {
    var btns = document.querySelectorAll('.obs-dash-sort-btn');
    if (!btns.length || btns[0]._wired) return;
    btns.forEach(function (b) {
      b._wired = true;
      b.addEventListener('click', function () {
        btns.forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active');
        state.dashSort = b.getAttribute('data-sort');
        updateCountryTiles();
      });
    });
  }

  function updateCountryTiles() {
    var grid = document.getElementById('countryGrid');
    if (!grid) return;
    var codes = (window.MAP_CONFIG && window.MAP_CONFIG.COUNTRY_CODES) || [];
    var byCode = {};
    state.countryStates.forEach(function (cs) {
      var code = cs.country_code || cs.country_id || cs.id;
      if (code) byCode[code] = cs;
    });
    var activeByCountry = {}, reserveByCountry = {};
    state.units.forEach(function (u) {
      var c = u.country_code || u.country_id;
      if (!c) return;
      var s = u.status || 'active';
      if (s === 'active' || s === 'embarked') activeByCountry[c] = (activeByCountry[c] || 0) + 1;
      else if (s === 'reserve') reserveByCountry[c] = (reserveByCountry[c] || 0) + 1;
    });

    // Build enriched rows for sorting
    var rows = codes.map(function (code) {
      var cs = byCode[code] || {};
      var country = state.countries[code] || { name: code };
      return {
        code: code,
        name: country.name || code,
        colors: country.colors || state.palette[code] || {},
        atWar: (country.at_war_with || []).length > 0,
        gdp: numOr(cs.gdp, 0),
        treasury: numOr(cs.treasury, 0),
        inflation: numOr(cs.inflation, 0),
        stability: intOr(cs.stability, 5),
        polSupport: intOr(cs.political_support, 5),
        warTired: intOr(cs.war_tiredness, 0),
        nuclear: intOr(cs.nuclear_level, 0),
        aiLevel: intOr(cs.ai_level, 0),
        active: activeByCountry[code] || 0,
        reserve: reserveByCountry[code] || 0,
        prev: state.prevCountryStates[code] || null,
        action: state.decisionsByCountry[code] || null,
      };
    });

    // Sort
    var sortKey = state.dashSort || 'code';
    rows.sort(function (a, b) {
      if (sortKey === 'code') return a.code.localeCompare(b.code);
      if (sortKey === 'gdp') return b.gdp - a.gdp;
      if (sortKey === 'stability') return b.stability - a.stability;
      if (sortKey === 'units') return (b.active + b.reserve) - (a.active + a.reserve);
      if (sortKey === 'nuclear') return b.nuclear - a.nuclear || b.aiLevel - a.aiLevel;
      return 0;
    });

    grid.innerHTML = '';
    rows.forEach(function (r) {
      var status = 'peace';
      if (r.atWar) status = 'at-war';
      if (r.stability <= 0 || r.gdp < 10) status = 'collapse';

      var tile = document.createElement('div');
      tile.className = 'obs-country-tile';
      tile.setAttribute('data-country', r.code);
      tile.setAttribute('data-status', status);
      tile.addEventListener('click', function () { showCountryDetail(r.code); });

      var stabCls = r.stability <= 2 ? 'crit' : (r.stability <= 4 ? 'lo' : '');
      var gdpDelta = r.prev ? delta(r.gdp, r.prev.gdp) : '';
      var stabDelta = r.prev ? deltaInt(r.stability, r.prev.stability) : '';
      var treasDelta = r.prev ? delta(r.treasury, r.prev.treasury) : '';
      var actionHtml;
      if (r.action) {
        var aType = (r.action.action_type || 'action').replace(/_/g, ' ');
        actionHtml = '<div class="obs-tile-action"><span class="action-emoji">' +
                     actionEmoji(r.action.action_type) + '</span> ' +
                     '<span class="action-name">' + escapeHtml(aType) + '</span></div>';
      } else {
        actionHtml = '<div class="obs-tile-action no-action">— no action committed —</div>';
      }

      tile.innerHTML =
        '<div class="obs-tile-head">' +
          '<span class="obs-tile-flag" style="background:' + (r.colors.ui || '#555') + '"></span>' +
          '<span class="obs-tile-name">' + escapeHtml(r.name) + '</span>' +
        '</div>' +
        '<div class="obs-tile-metrics">' +
          '<div class="obs-tile-metric"><span class="k">GDP</span> <span class="v">$' + fmtNum(r.gdp) + '</span>' + gdpDelta + '</div>' +
          '<div class="obs-tile-metric"><span class="k">Treas</span> <span class="v">$' + fmtNum(r.treasury) + '</span>' + treasDelta + '</div>' +
          '<div class="obs-tile-metric"><span class="k">Stab</span> <span class="v ' + stabCls + '">' + r.stability + '</span>' + stabDelta + '</div>' +
          '<div class="obs-tile-metric"><span class="k">Infl</span> <span class="v">' + fmtPct(r.inflation) + '</span></div>' +
          '<div class="obs-tile-metric"><span class="k">Forces</span> <span class="v">' + r.active + (r.reserve ? '+' + r.reserve : '') + '</span></div>' +
          '<div class="obs-tile-metric"><span class="k">PolSup</span> <span class="v">' + r.polSupport + '</span></div>' +
          '<div class="obs-tile-metric"><span class="k">Nuc</span> <span class="v">' + r.nuclear + '</span></div>' +
          '<div class="obs-tile-metric"><span class="k">AI</span> <span class="v">' + r.aiLevel + '</span></div>' +
        '</div>' +
        actionHtml;
      grid.appendChild(tile);
    });

    renderDashSummary(rows);
  }

  var GLOBAL_METRICS = [
    { key: 'oil_price',   label: 'Oil $/bbl',  fmt: function(v){return '$'+v.toFixed(2);} },
    { key: 'stock_index', label: 'Stock Idx',  fmt: function(v){return v.toFixed(1);} },
    { key: 'bond_yield',  label: 'Bond Yield', fmt: function(v){return v.toFixed(2)+'%';} },
    { key: 'gold_price',  label: 'Gold $/oz',  fmt: function(v){return '$'+v.toFixed(0);} },
  ];

  function renderGlobalStrip() {
    var el = document.getElementById('globalStrip');
    if (!el) return;
    var series = state.globalSeries || [];
    if (!series.length) {
      el.innerHTML = '<span style="color:var(--text-muted);font-size:10px">No global series data.</span>';
      return;
    }
    // pick row for the selected view round (default: latest available)
    var avail = series.map(function (r) { return r.round_num; });
    var viewR = state.viewRound != null ? state.viewRound : avail[avail.length - 1];
    var row = series.find(function (r) { return r.round_num === viewR; }) || series[series.length - 1];
    var prevRow = series.find(function (r) { return r.round_num === row.round_num - 1; });

    var html = '';
    GLOBAL_METRICS.forEach(function (m) {
      var v = row[m.key];
      var pv = prevRow ? prevRow[m.key] : null;
      var d = '';
      if (pv != null) {
        var diff = v - pv;
        var cls = Math.abs(diff) < 0.01 ? 'flat' : (diff > 0 ? 'up' : 'down');
        var arrow = cls === 'flat' ? '•' : (diff > 0 ? '▲' : '▼');
        d = '<span class="d ' + cls + '">' + arrow + '</span>';
      }
      var sel = state.chartMetric === m.key ? ' selected' : '';
      html += '<div class="obs-global-item' + sel + '" data-metric="' + m.key + '">' +
              '<span class="k">' + m.label + '</span>' +
              '<span class="v">' + m.fmt(v) + '</span>' + d + '</div>';
    });
    // Round scrubber
    html += '<div class="obs-round-scrubber"><span class="label">Round</span>';
    series.forEach(function (r) {
      var active = r.round_num === viewR ? ' active' : '';
      html += '<button class="obs-scrub-btn' + active + '" data-round="' + r.round_num + '">' + r.round_num + '</button>';
    });
    html += '</div>';
    el.innerHTML = html;

    // Wire clicks
    el.querySelectorAll('.obs-global-item').forEach(function (it) {
      it.addEventListener('click', function () {
        state.chartMetric = it.getAttribute('data-metric');
        renderGlobalStrip();
        renderGlobalChart();
      });
    });
    el.querySelectorAll('.obs-scrub-btn').forEach(function (b) {
      b.addEventListener('click', function () {
        var rnd = parseInt(b.getAttribute('data-round'), 10);
        state.viewRound = rnd;
        renderGlobalStrip();
        renderGlobalChart();
        // Re-fetch country + unit data for the selected round
        Promise.all([
          fetchJSON('/api/observatory/units?round=' + rnd + '&scenario=' + encodeURIComponent(state.scenario)).catch(noop),
          fetchJSON('/api/observatory/countries?round=' + rnd + '&scenario=' + encodeURIComponent(state.scenario)).catch(noop),
          fetchJSON('/api/observatory/combats?round=' + rnd + '&scenario=' + encodeURIComponent(state.scenario)).catch(noop),
        ]).then(function (res) {
          if (res[0]) applyUnits(res[0]);
          if (res[1]) applyCountries(res[1]);
          if (res[2]) applyCombats(res[2]);
        });
      });
    });
  }

  function renderGlobalChart() {
    var svg = document.getElementById('globalChart');
    if (!svg) return;
    svg.innerHTML = '';
    var series = state.globalSeries || [];
    if (series.length < 2) return;
    var key = state.chartMetric || 'oil_price';
    var meta = GLOBAL_METRICS.find(function (m) { return m.key === key; }) || GLOBAL_METRICS[0];

    var W = svg.clientWidth || 600;
    var H = 120;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    var pad = { l: 48, r: 18, t: 16, b: 20 };
    var chartW = W - pad.l - pad.r;
    var chartH = H - pad.t - pad.b;

    var values = series.map(function (r) { return r[key]; });
    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);
    if (min === max) { min -= 1; max += 1; }
    var range = max - min;

    var xFor = function (i) { return pad.l + (i / (series.length - 1)) * chartW; };
    var yFor = function (v) { return pad.t + chartH - ((v - min) / range) * chartH; };

    // gridlines (3 horizontal)
    for (var g = 0; g <= 3; g++) {
      var gy = pad.t + (g / 3) * chartH;
      var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('class', 'grid-line');
      line.setAttribute('x1', pad.l); line.setAttribute('x2', pad.l + chartW);
      line.setAttribute('y1', gy); line.setAttribute('y2', gy);
      svg.appendChild(line);
      var val = max - (g / 3) * range;
      var txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      txt.setAttribute('class', 'axis-label');
      txt.setAttribute('x', pad.l - 6); txt.setAttribute('y', gy + 3);
      txt.setAttribute('text-anchor', 'end');
      txt.textContent = meta.fmt(val).replace(/^\$/, '');
      svg.appendChild(txt);
    }

    // x-axis labels (round numbers)
    series.forEach(function (r, i) {
      var t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      t.setAttribute('class', 'axis-label');
      t.setAttribute('x', xFor(i)); t.setAttribute('y', H - 6);
      t.setAttribute('text-anchor', 'middle');
      t.textContent = 'R' + r.round_num;
      svg.appendChild(t);
    });

    // polyline
    var points = series.map(function (r, i) { return xFor(i) + ',' + yFor(r[key]); }).join(' ');
    var poly = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    poly.setAttribute('class', 'series-line');
    poly.setAttribute('points', points);
    svg.appendChild(poly);

    // points — highlight the selected view round
    var viewR = state.viewRound != null ? state.viewRound : series[series.length - 1].round_num;
    series.forEach(function (r, i) {
      var pt = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      pt.setAttribute('class', 'series-point' + (r.round_num === viewR ? ' current' : ''));
      pt.setAttribute('cx', xFor(i)); pt.setAttribute('cy', yFor(r[key]));
      pt.setAttribute('r', r.round_num === viewR ? 4 : 2.5);
      svg.appendChild(pt);
    });

    // title
    var title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    title.setAttribute('class', 'title-label');
    title.setAttribute('x', pad.l);
    title.setAttribute('y', pad.t - 4);
    title.textContent = meta.label + ' — Round 0 → ' + series[series.length - 1].round_num;
    svg.appendChild(title);
  }

  function renderDashSummary(rows) {
    var el = document.getElementById('dashSummary');
    if (!el) return;
    var atWar = 0, collapsed = 0, peace = 0, nuclear = 0;
    var gdpSum = 0, stabAvg = 0, forcesSum = 0, committed = 0;
    rows.forEach(function (r) {
      if (r.action) committed++;
      if (r.nuclear > 0) nuclear++;
      if (r.atWar) atWar++;
      else if (r.stability <= 0 || r.gdp < 10) collapsed++;
      else peace++;
      gdpSum += r.gdp;
      stabAvg += r.stability;
      forcesSum += r.active + r.reserve;
    });
    var n = rows.length || 1;
    el.innerHTML =
      '<div class="obs-dash-stat"><span class="k">World GDP</span><span class="v">$' + fmtNum(gdpSum) + '</span></div>' +
      '<div class="obs-dash-stat"><span class="k">Avg Stab</span><span class="v">' + (stabAvg / n).toFixed(1) + '</span></div>' +
      '<div class="obs-dash-stat"><span class="k">Forces</span><span class="v">' + forcesSum + '</span></div>' +
      '<div class="obs-dash-stat"><span class="k">At War</span><span class="v ' + (atWar > 0 ? 'danger' : '') + '">' + atWar + '</span></div>' +
      '<div class="obs-dash-stat"><span class="k">Peace</span><span class="v success">' + peace + '</span></div>' +
      '<div class="obs-dash-stat"><span class="k">Collapse</span><span class="v ' + (collapsed > 0 ? 'warning' : '') + '">' + collapsed + '</span></div>' +
      '<div class="obs-dash-stat"><span class="k">Nuclear</span><span class="v">' + nuclear + '</span></div>' +
      '<div class="obs-dash-stat"><span class="k">Committed</span><span class="v">' + committed + '/' + n + '</span></div>';
  }

  function delta(now, prev) {
    if (prev == null || now == null) return '';
    var d = now - prev;
    if (Math.abs(d) < 0.01) return '<span class="obs-tile-delta flat">•</span>';
    var sign = d > 0 ? '+' : '';
    var cls = d > 0 ? 'up' : 'down';
    var arrow = d > 0 ? '▲' : '▼';
    return '<span class="obs-tile-delta ' + cls + '">' + arrow + sign + fmtNum(d) + '</span>';
  }
  function deltaInt(now, prev) {
    if (prev == null || now == null) return '';
    var d = now - prev;
    if (d === 0) return '<span class="obs-tile-delta flat">•</span>';
    var cls = d > 0 ? 'up' : 'down';
    var arrow = d > 0 ? '▲' : '▼';
    return '<span class="obs-tile-delta ' + cls + '">' + arrow + (d > 0 ? '+' : '') + d + '</span>';
  }
  function fmtPct(v) {
    if (v == null) return '—';
    return (v * 100).toFixed(1) + '%';
  }
  function actionEmoji(actionType) {
    if (!actionType) return '•';
    var s = actionType.toLowerCase();
    if (s.indexOf('attack') >= 0 || s.indexOf('strike') >= 0) return '⚔';
    if (s.indexOf('move') >= 0 || s.indexOf('deploy') >= 0) return '➜';
    if (s.indexOf('diplom') >= 0 || s.indexOf('negoti') >= 0) return '🤝';
    if (s.indexOf('econ') >= 0 || s.indexOf('trade') >= 0 || s.indexOf('sanc') >= 0) return '💰';
    if (s.indexOf('research') >= 0 || s.indexOf('rd') >= 0 || s.indexOf('r_d') >= 0) return '🔬';
    if (s.indexOf('intel') >= 0 || s.indexOf('cov') >= 0) return '🕵';
    if (s.indexOf('defen') >= 0 || s.indexOf('fortif') >= 0) return '🛡';
    return '🎯';
  }

  // ================================================================
  // Map — full parity with /map viewer
  // ================================================================
  var HEX_R_GLOBAL = 30;
  var HEX_R_THEATER = 38;
  var PAD = 40;

  function currentHexRadius() {
    return state.view === 'global' ? HEX_R_GLOBAL : HEX_R_THEATER;
  }
  function currentMapData() {
    if (state.view === 'global') return state.globalMap;
    return state.theaters[state.view] || null;
  }

  function setMapView(viewName) {
    state.view = viewName;
    var backBtn = document.getElementById('btnMapBack');
    var subt = document.getElementById('mapSubtitle');
    if (viewName === 'global') {
      if (backBtn) backBtn.style.display = 'none';
      if (subt) subt.textContent = '— Global';
    } else {
      if (backBtn) backBtn.style.display = 'inline-block';
      if (subt) subt.textContent = '— ' + (THEATER_LABELS[viewName] || viewName);
    }
    renderMap();
  }

  function renderMap(movedUnits) {
    var svg = document.getElementById('obsMapSvg');
    if (!svg) return;
    var data = currentMapData();
    if (!data) return;
    var rows = data.rows, cols = data.cols;
    var r = currentHexRadius();
    var w = Math.sqrt(3) * r;
    var h = 1.5 * r;
    var width = PAD * 2 + cols * w + w / 2;
    var height = PAD * 2 + rows * h + r * 0.5;
    svg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
    svg.innerHTML = '';

    // theater-link lookup (global view only)
    var theaterLinks = state.view === 'global' ? buildGlobalTheaterLinks() : {};

    // hex polygons
    for (var ri = 0; ri < rows; ri++) {
      for (var ci = 0; ci < cols; ci++) {
        var hex = data.grid[ri][ci];
        var center = hexCenter(ri, ci, r);
        var poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        poly.setAttribute('points', hexPoints(center.x, center.y, r));
        if (hex.occupied_by && hex.occupied_by !== hex.owner) {
          var patId = ensureOccPattern(svg, hex.owner, hex.occupied_by);
          poly.setAttribute('fill', 'url(#' + patId + ')');
        } else {
          poly.setAttribute('fill', mapColorFor(hex.owner));
        }
        var cls = 'hex';
        if (hex.owner === 'sea') cls += ' sea';
        var key1 = (ri + 1) + ',' + (ci + 1);
        if (theaterLinks[key1]) cls += ' theater-link';
        poly.setAttribute('class', cls);
        poly.setAttribute('data-row', ri);
        poly.setAttribute('data-col', ci);
        poly.addEventListener('click', (function (rr, cc, tLink) {
          return function () {
            if (tLink && state.view === 'global') {
              // Drill down on second click of same hex
              var k = (rr + 1) + ',' + (cc + 1);
              if (state.lastClickedHex === k) {
                state.lastClickedHex = null;
                setMapView(tLink);
                return;
              }
              state.lastClickedHex = k;
            } else {
              state.lastClickedHex = null;
            }
            selectHex(rr, cc);
          };
        })(ri, ci, theaterLinks[key1]));
        svg.appendChild(poly);
      }
    }

    // chokepoints (global only)
    if (state.view === 'global' && data.chokepoints) {
      Object.keys(data.chokepoints).forEach(function (k) {
        var cp = data.chokepoints[k];
        var poly = svg.querySelector('polygon[data-row="' + cp.row + '"][data-col="' + cp.col + '"]');
        if (poly) poly.classList.add('chokepoint');
        var cen = hexCenter(cp.row, cp.col, r);
        addText(svg, cen.x, cen.y - 2, (cp.name || '').toUpperCase(), 'chokepoint-label');
      });
    }

    // theater-link badges removed per Marat 2026-04-05 — the dashed
    // outline on theater-link hexes is signal enough; ⊕ adds noise.

    // die-hards (theater view only)
    if (state.view !== 'global' && data.dieHards) {
      Object.keys(data.dieHards).forEach(function (k) {
        var dh = data.dieHards[k];
        var cen = hexCenter(dh.row, dh.col, r);
        var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', cen.x);
        circle.setAttribute('cy', cen.y);
        circle.setAttribute('r', r * 0.85);
        circle.setAttribute('class', 'die-hard-marker');
        svg.appendChild(circle);
        addText(svg, cen.x, cen.y + r + 4, dh.name, 'chokepoint-label');
      });
    }

    // country centroid labels
    renderCountryLabels(svg, data, r);

    // units per hex
    if (state.view === 'global') {
      Object.keys(state.unitsByHex).forEach(function (key) {
        var parts = key.split(',');
        var gr = parseInt(parts[0], 10);
        var gc = parseInt(parts[1], 10);
        if (!gr || !gc) return;
        var units = state.unitsByHex[key];
        var center = hexCenter(gr - 1, gc - 1, r);
        renderUnitStack(svg, center.x, center.y + 6, units, movedUnits || {}, r);
      });
    } else {
      // theater view: aggregate units whose theater matches current view
      var tByHex = {};
      (state.units || []).forEach(function (u) {
        if (u.theater !== state.view) return;
        var tr = u.theater_row, tc = u.theater_col;
        if (tr == null || tc == null) return;
        var k = tr + ',' + tc;
        (tByHex[k] = tByHex[k] || []).push(u);
      });
      Object.keys(tByHex).forEach(function (key) {
        var parts = key.split(',');
        var tr = parseInt(parts[0], 10);
        var tc = parseInt(parts[1], 10);
        if (!tr || !tc) return;
        var center = hexCenter(tr - 1, tc - 1, r);
        renderUnitStack(svg, center.x, center.y + 6, tByHex[key], movedUnits || {}, r);
      });
    }

    // blockade zones — mark sea hexes with orange contours
    renderBlockadeZones(svg, data);

    // embark badges — mini icons on ship hexes showing loaded cargo
    renderEmbarkBadges(svg, r);

    // battle markers (both global + theater view)
    renderBattleMarkers(svg, r);
  }

  // ================================================================
  // Blockade rendering — from DECLARED actions only (Marat 2026-04-06)
  // ================================================================
  // Earlier version derived from unit positions → too many false
  // positives. Now: observatory fetches /api/observatory/blockades which
  // returns committed declare_blockade agent_decisions. Each has
  // payload: {target_hexes: [[r,c],...], level: 'partial'|'full'}.
  // Until the action is wired into the catalog, this returns [] → no
  // contours drawn.
  function renderBlockadeZones(svg, data) {
    if (!data || !data.grid) return;
    if (state.view !== 'global') return;
    // Only render DECLARED blockades from state.blockades (populated by
    // fetchBlockades()). Each entry: {payload:{target_hexes, level}}.
    var list = state.blockades || [];
    if (!list.length) return;
    list.forEach(function (decl) {
      var payload = decl.payload || {};
      var hexes = payload.target_hexes || [];
      var level = payload.level === 'full' ? 'full' : 'partial';
      hexes.forEach(function (hx) {
        if (!Array.isArray(hx) || hx.length < 2) return;
        var rr = hx[0] - 1, cc = hx[1] - 1;
        var poly = svg.querySelector('polygon[data-row="' + rr + '"][data-col="' + cc + '"]');
        if (poly) poly.classList.add('blockade-' + level);
      });
    });
    return;

    // --- disabled (kept for reference) ---
    // Blockadeable hexes (Marat rule 2026-04-05): only chokepoints
    // + sea hexes adjacent to island nations (Formosa). Other sea
    // hexes cannot be "blockaded" even if naval sits there.
    var blockadeable = {};  // "r,c" (1-indexed) -> target country name
    // 1a. Chokepoints
    if (data.chokepoints) {
      Object.keys(data.chokepoints).forEach(function (k) {
        var cp = data.chokepoints[k];
        // chokepoints block trade in general — target = whichever country
        // is adjacent. Use adjacent land owner if any; else 'world'.
        var cr = cp.row, cc = cp.col;  // 0-indexed
        var nbrs = neighborCells(cr, cc);
        var target = null;
        nbrs.forEach(function (n) {
          if (n.r < 0 || n.r >= data.rows || n.c < 0 || n.c >= data.cols) return;
          var nh = data.grid[n.r][n.c];
          if (nh && nh.owner && nh.owner !== 'sea') target = nh.owner;
        });
        blockadeable[(cr + 1) + ',' + (cc + 1)] = target || 'chokepoint';
      });
    }
    // 1b. Island nations — hard-coded list (only Formosa today;
    // extend when more islands added)
    var ISLAND_NATIONS = ['formosa'];
    var rows = data.rows, cols = data.cols;
    ISLAND_NATIONS.forEach(function (country) {
      for (var ri = 0; ri < rows; ri++) {
        for (var ci = 0; ci < cols; ci++) {
          var hx = data.grid[ri][ci];
          if (!hx || hx.owner !== country) continue;
          var nbrs = neighborCells(ri, ci);
          nbrs.forEach(function (n) {
            if (n.r < 0 || n.r >= rows || n.c < 0 || n.c >= cols) return;
            var nh = data.grid[n.r][n.c];
            if (nh && nh.owner === 'sea') {
              blockadeable[(n.r + 1) + ',' + (n.c + 1)] = country;
            }
          });
        }
      }
    });

    // 1. Build coastal-sea set per country, but ONLY include blockadeable hexes
    var coastByCountry = {};
    for (var ri2 = 0; ri2 < rows; ri2++) {
      for (var ci2 = 0; ci2 < cols; ci2++) {
        var hex = data.grid[ri2][ci2];
        if (!hex || !hex.owner || hex.owner === 'sea') continue;
        var c = hex.owner;
        coastByCountry[c] = coastByCountry[c] || {};
        var nbrs = neighborCells(ri2, ci2);
        nbrs.forEach(function (n) {
          if (n.r < 0 || n.r >= rows || n.c < 0 || n.c >= cols) return;
          var nh = data.grid[n.r][n.c];
          if (nh && nh.owner === 'sea') {
            var k = (n.r + 1) + ',' + (n.c + 1);
            if (blockadeable[k]) coastByCountry[c][k] = true;
          }
        });
      }
    }

    // 2. Index naval units by sea hex
    var navalByHex = {};  // "r,c" -> [units]
    (state.units || []).forEach(function (u) {
      if (u.unit_type !== 'naval' || u.status !== 'active') return;
      if (u.global_row == null || u.global_col == null) return;
      var k = u.global_row + ',' + u.global_col;
      (navalByHex[k] = navalByHex[k] || []).push(u);
    });

    // 3. For each country, count which of its coastal hexes have enemy naval
    var countryBlockadeState = {};  // country -> 'full'|'partial'|null
    Object.keys(coastByCountry).forEach(function (country) {
      var coast = coastByCountry[country];
      var total = 0, blocked = 0;
      Object.keys(coast).forEach(function (k) {
        total++;
        var navs = navalByHex[k];
        if (navs && navs.some(function (u) { return (u.country_code || u.country_id) !== country; })) {
          blocked++;
        }
      });
      if (total === 0 || blocked === 0) {
        countryBlockadeState[country] = null;
      } else if (blocked === total) {
        countryBlockadeState[country] = 'full';
      } else {
        countryBlockadeState[country] = 'partial';
      }
    });

    // 4. For each blockading sea hex, apply a class reflecting MAX intensity
    //    across all countries it blocks. Also scribble a tiny marker.
    var hexBlockadeClass = {};  // "r,c" -> 'full'|'partial'
    Object.keys(coastByCountry).forEach(function (country) {
      var level = countryBlockadeState[country];
      if (!level) return;
      var coast = coastByCountry[country];
      Object.keys(coast).forEach(function (k) {
        var navs = navalByHex[k];
        if (!navs) return;
        var hasEnemy = navs.some(function (u) { return (u.country_code || u.country_id) !== country; });
        if (!hasEnemy) return;
        // max intensity: full > partial
        if (level === 'full') hexBlockadeClass[k] = 'full';
        else if (hexBlockadeClass[k] !== 'full') hexBlockadeClass[k] = 'partial';
      });
    });

    // 5. Apply CSS class to the hex polygon
    Object.keys(hexBlockadeClass).forEach(function (k) {
      var parts = k.split(',');
      var rr = parseInt(parts[0], 10) - 1;  // back to 0-indexed
      var cc = parseInt(parts[1], 10) - 1;
      var poly = svg.querySelector('polygon[data-row="' + rr + '"][data-col="' + cc + '"]');
      if (poly) {
        poly.classList.add('blockade-' + hexBlockadeClass[k]);
      }
    });
  }

  // Helper: 0-indexed pointy-top odd-r offset neighbors (matches getAdjacencies)
  function neighborCells(rIdx, cIdx) {
    var odd = rIdx % 2 === 1;
    var deltas = odd
      ? [[-1, 0], [-1, 1], [0, -1], [0, 1], [1, 0], [1, 1]]
      : [[-1, -1], [-1, 0], [0, -1], [0, 1], [1, -1], [1, 0]];
    return deltas.map(function (d) { return { r: rIdx + d[0], c: cIdx + d[1] }; });
  }

  function renderEmbarkBadges(svg, hexR) {
    var list = state.units || [];
    // Group embarked units by carrier
    var embarkByShip = {};
    list.forEach(function (u) {
      if (u.embarked_on) {
        (embarkByShip[u.embarked_on] = embarkByShip[u.embarked_on] || []).push(u);
      }
    });
    var byHex = {};
    list.forEach(function (ship) {
      if (ship.unit_type !== 'naval' || ship.status !== 'active') return;
      var shipId = ship.unit_code || ship.unit_id;
      var emb = embarkByShip[shipId];
      if (!emb || emb.length === 0) return;
      var cell = null;
      if (state.view === 'global') {
        if (ship.global_row != null && ship.global_col != null) cell = [ship.global_row, ship.global_col];
      } else {
        if (ship.theater === state.view && ship.theater_row != null && ship.theater_col != null) {
          cell = [ship.theater_row, ship.theater_col];
        }
      }
      if (!cell) return;
      var key = cell[0] + ',' + cell[1];
      (byHex[key] = byHex[key] || []).push.apply(byHex[key], emb);
    });
    var miniSize = Math.round(hexR * 0.26);
    Object.keys(byHex).forEach(function (key) {
      var parts = key.split(',').map(Number);
      var cen = hexCenter(parts[0] - 1, parts[1] - 1, hexR);
      var baseX = cen.x + hexR * 0.15;
      var baseY = cen.y - hexR * 0.15;
      var units = byHex[key];
      units.forEach(function (u, i) {
        var iconId = iconIdFor(u.unit_type, u.country_code || u.country_id);
        var x = baseX + (i % 3) * (miniSize * 0.6);
        var y = baseY + Math.floor(i / 3) * (miniSize * 0.7);
        var use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttribute('href', '#' + iconId);
        use.setAttribute('x', x - miniSize / 2);
        use.setAttribute('y', y - miniSize / 2);
        use.setAttribute('width', miniSize);
        use.setAttribute('height', miniSize);
        use.setAttribute('style', 'color:' + uiColorFor(u.country_code || u.country_id));
        use.setAttribute('class', 'embark-mini');
        use.style.pointerEvents = 'none';
        svg.appendChild(use);
      });
    });
  }

  function renderUnitStack(svg, cx, cy, units, movedUnits, hexR) {
    if (!units || units.length === 0) return;
    // Group by (country, type)
    var byCT = {};
    units.forEach(function (u) {
      var k = (u.country_code || u.country_id) + '|' + u.unit_type;
      byCT[k] = byCT[k] || { country: u.country_code || u.country_id, type: u.unit_type, count: 0, units: [] };
      byCT[k].count++;
      byCT[k].units.push(u);
    });

    // Determine rendering mode (batched vs individual)
    var totalCount = units.length;
    var batched = totalCount >= 6;
    var sorted = Object.keys(byCT).map(function (k) { return byCT[k]; })
      .sort(function (a, b) {
        if (a.country !== b.country) return a.country < b.country ? -1 : 1;
        return a.type < b.type ? -1 : a.type > b.type ? 1 : 0;
      });

    var show = [];
    if (batched) {
      show = sorted;
    } else {
      sorted.forEach(function (e) {
        for (var i = 0; i < e.count; i++) show.push({ country: e.country, type: e.type, count: 1, units: [e.units[i]] });
      });
    }

    var perRow = 3;
    var base = hexR >= 36 ? 16 : 14;
    var sizeByType = {
      naval: base + 6, ground: base, tactical_air: base - 2,
      air_defense: base, strategic_missile: base,
    };
    var spacing = show.length >= 3 ? 0.95 : 0.75;
    var jitterAmt = show.length >= 3 ? 0.38 : 0.22;

    var rowCount = Math.ceil(show.length / perRow);
    var rowHeight = base * spacing * 1.5;
    var startY = cy - (rowCount - 1) * rowHeight / 2;

    var jitter = function (idx, amt) {
      var s = Math.sin(idx * 12.9898 + idx * 78.233) * 43758.5453;
      return ((s - Math.floor(s)) - 0.5) * 2 * amt;
    };

    for (var i = 0; i < show.length; i++) {
      var e = show[i];
      var rowIdx = Math.floor(i / perRow);
      var colIdx = i % perRow;
      var rowLen = Math.min(perRow, show.length - rowIdx * perRow);
      var size = sizeByType[e.type] || base;
      var step = size * spacing;
      var jx = jitter(i * 2 + 1, size * jitterAmt);
      var jy = jitter(i * 2 + 7, size * jitterAmt * 0.82);
      var x = cx + (colIdx - (rowLen - 1) / 2) * step + jx;
      var y = startY + rowIdx * rowHeight + jy;

      var g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', 'unit-icon');
      g.setAttribute('transform', 'translate(' + (x - size / 2) + ',' + (y - size / 2) + ')');
      g.setAttribute('data-country', e.country);
      g.style.color = uiColorFor(e.country);

      // Movement animation / destroyed styling
      var someMoved = e.units.some(function (u) {
        var uid = u.unit_code || u.unit_id;
        return uid && movedUnits[uid];
      });
      var allDead = e.units.every(function (u) { return u.status === 'destroyed'; });
      var reserveDeploy = e.units.some(function (u) {
        var uid = u.unit_code || u.unit_id;
        return uid && movedUnits[uid] && movedUnits[uid].kind === 'deploy';
      });
      if (someMoved) g.classList.add('moving');
      if (reserveDeploy) g.classList.add('deploying');
      if (allDead) g.classList.add('destroyed');

      var iconId = iconIdFor(e.type, e.country);
      var use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
      use.setAttribute('href', '#' + iconId);
      use.setAttribute('width', size);
      use.setAttribute('height', size);
      g.appendChild(use);

      if (e.count >= 2) {
        var t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('x', size * 0.9);
        t.setAttribute('y', size * 0.3);
        t.setAttribute('class', 'unit-count-badge-obs');
        t.textContent = e.count;
        g.appendChild(t);
      }
      g.addEventListener('click', (function (entry) {
        return function (ev) { ev.stopPropagation(); showUnitDetail(entry); };
      })(e));
      svg.appendChild(g);

      // Tween from prior position
      if (someMoved && !reserveDeploy) {
        animateTween(g, e, movedUnits, hexR, x - size / 2, y - size / 2);
      } else if (reserveDeploy) {
        animateDeploy(g, e, hexR);
      }
    }
  }

  function animateTween(g, entry, movedUnits, hexR, finalX, finalY) {
    // Compute avg starting position from priorPos of units in entry
    var data = currentMapData();
    if (!data) return;
    var srcHex = null;
    entry.units.forEach(function (u) {
      var uid = u.unit_code || u.unit_id;
      var delta = movedUnits[uid];
      if (delta && delta.from) srcHex = delta.from;
    });
    if (!srcHex) return;
    var parts = srcHex.split(',');
    var sr = parseInt(parts[0], 10) - 1;
    var sc = parseInt(parts[1], 10) - 1;
    if (sr < 0 || sc < 0) return;
    var srcCenter = hexCenter(sr, sc, hexR);
    var use = g.querySelector('use');
    if (!use) return;
    var sizeW = parseFloat(use.getAttribute('width')) || 16;
    var sizeH = parseFloat(use.getAttribute('height')) || 16;
    var deltaX = srcCenter.x - (finalX + sizeW / 2);
    var deltaY = srcCenter.y - (finalY + sizeH / 2);
    g.style.transition = 'none';
    g.style.transform = 'translate(' + deltaX + 'px,' + deltaY + 'px)';
    // Force reflow
    void g.getBoundingClientRect();
    requestAnimationFrame(function () {
      g.style.transition = 'transform 800ms cubic-bezier(.4,.0,.2,1)';
      g.style.transform = 'translate(0,0)';
    });
  }

  function animateDeploy(g, entry, hexR) {
    // Fade in from country centroid
    var data = currentMapData();
    if (!data) return;
    // Find country centroid
    var pts = [];
    for (var ri = 0; ri < data.rows; ri++) {
      for (var ci = 0; ci < data.cols; ci++) {
        var hx = data.grid[ri][ci];
        if (hx && hx.owner === entry.country && hx.owner !== 'sea') {
          pts.push(hexCenter(ri, ci, hexR));
        }
      }
    }
    if (!pts.length) return;
    var cx = pts.reduce(function (s, p) { return s + p.x; }, 0) / pts.length;
    var cy = pts.reduce(function (s, p) { return s + p.y; }, 0) / pts.length;
    // Current transform is final. Apply reverse delta.
    var use = g.querySelector('use');
    if (!use) return;
    var sizeW = parseFloat(use.getAttribute('width')) || 16;
    var sizeH = parseFloat(use.getAttribute('height')) || 16;
    var tr = g.getAttribute('transform') || '';
    var m = tr.match(/translate\(([^,]+),([^)]+)\)/);
    if (!m) return;
    var fx = parseFloat(m[1]);
    var fy = parseFloat(m[2]);
    var deltaX = cx - (fx + sizeW / 2);
    var deltaY = cy - (fy + sizeH / 2);
    g.style.transition = 'none';
    g.style.opacity = '0';
    g.style.transform = 'translate(' + deltaX + 'px,' + deltaY + 'px) scale(0.5)';
    void g.getBoundingClientRect();
    requestAnimationFrame(function () {
      g.style.transition = 'transform 900ms cubic-bezier(.3,.0,.2,1), opacity 500ms ease';
      g.style.opacity = '1';
      g.style.transform = 'translate(0,0) scale(1)';
    });
  }

  function renderBattleMarkers(svgArg, rArg) {
    // If called fresh with args: inject into those. If called standalone (from applyCombats), find svg.
    var svg = svgArg || document.getElementById('obsMapSvg');
    if (!svg) return;
    var r = rArg || currentHexRadius();
    // Remove existing markers
    svg.querySelectorAll('.battle-marker, .attack-arrow').forEach(function (n) { n.remove(); });
    if (!state.combats || !state.combats.length) return;

    // Build a lookup: unit_code -> {theater, theater_row, theater_col}
    var unitPos = {};
    (state.units || []).forEach(function (u) {
      var uc = u.unit_code || u.unit_id;
      if (uc) unitPos[uc] = u;
    });

    state.combats.forEach(function (c) {
      var tr, tc;
      if (state.view === 'global') {
        tr = c.location_global_row;
        tc = c.location_global_col;
      } else {
        // Theater view: locate blast at any affected unit in this theater.
        var losses = [].concat(c.defender_losses || [], c.attacker_losses || []);
        var hit = null;
        for (var i = 0; i < losses.length; i++) {
          var uc = typeof losses[i] === 'string' ? losses[i] : (losses[i] && losses[i].unit_code);
          var u = unitPos[uc];
          if (u && u.theater === state.view && u.theater_row != null && u.theater_col != null) {
            hit = u;
            break;
          }
        }
        if (!hit) return;
        tr = hit.theater_row;
        tc = hit.theater_col;
      }
      if (tr == null || tc == null) return;
      var tCenter = hexCenter(tr - 1, tc - 1, r);
      // Attempt to find attacker hex from attacker_units (first unit's coords)
      var src = null;
      if (c.attacker_units && Array.isArray(c.attacker_units) && c.attacker_units.length) {
        var u0 = c.attacker_units[0];
        if (u0 && u0.global_row != null && u0.global_col != null) {
          src = hexCenter(u0.global_row - 1, u0.global_col - 1, r);
        }
      }
      // Attack arrow
      if (src && (src.x !== tCenter.x || src.y !== tCenter.y)) {
        var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', src.x); line.setAttribute('y1', src.y);
        line.setAttribute('x2', tCenter.x); line.setAttribute('y2', tCenter.y);
        line.setAttribute('class', 'attack-arrow');
        svg.appendChild(line);
      }
      // 💥 marker — anchored to hex center, small pulse
      var marker = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      marker.setAttribute('x', tCenter.x);
      marker.setAttribute('y', tCenter.y);
      marker.setAttribute('class', 'battle-marker');
      marker.textContent = '💥';
      svg.appendChild(marker);
    });
  }

  function renderCountryLabels(svg, data, r) {
    var groups = {};
    for (var ri = 0; ri < data.rows; ri++) {
      for (var ci = 0; ci < data.cols; ci++) {
        var hx = data.grid[ri][ci];
        if (!hx || !hx.owner || hx.owner === 'sea') continue;
        var cen = hexCenter(ri, ci, r);
        (groups[hx.owner] = groups[hx.owner] || []).push(cen);
      }
    }
    Object.keys(groups).forEach(function (owner) {
      var pts = groups[owner];
      if (!pts.length) return;
      var cx = pts.reduce(function (s, p) { return s + p.x; }, 0) / pts.length;
      var cy = pts.reduce(function (s, p) { return s + p.y; }, 0) / pts.length;
      var t = addText(svg, cx, cy, countryName(owner).toUpperCase(), 'country-label');
      t.style.fill = uiColorFor(owner);
    });
  }

  function buildGlobalTheaterLinks() {
    // Read from MAP_CONFIG (canonical)
    var out = {};
    var cfg = window.MAP_CONFIG;
    if (!cfg) return out;
    // Iterate theaters via helper if available, else hard-code from MAP_CONFIG THEATER_LINK_HEXES is missing → derive from theater owners
    // MAP_CONFIG exposes globalHexForTheaterCell; use it with known owner from theater grid
    (cfg.THEATER_NAMES || []).forEach(function (theater) {
      var t = state.theaters && state.theaters[theater];
      if (!t || !t.grid) return;
      for (var ri = 0; ri < t.rows; ri++) {
        for (var ci = 0; ci < t.cols; ci++) {
          var cell = t.grid[ri][ci];
          if (!cell) continue;
          var g = cfg.globalHexForTheaterCell(theater, ri + 1, ci + 1, cell.owner);
          if (g) out[g[0] + ',' + g[1]] = theater;
        }
      }
    });
    return out;
  }

  function iconIdFor(type, country) {
    if (type === 'ground') {
      if (country === 'sarmatia' && state.view !== 'global') return 'unit-ground-left';
      return 'unit-ground-right';
    }
    if (type === 'naval') return 'unit-naval';
    if (type === 'tactical_air') return 'unit-tactical-air';
    if (type === 'air_defense') return 'unit-air-defense';
    if (type === 'strategic_missile') return 'unit-strategic-missile';
    return 'unit-ground-right';
  }

  function ensureOccPattern(svg, owner, occupier) {
    var id = 'occ_' + owner + '_' + occupier;
    if (document.getElementById(id)) return id;
    var defs = svg.querySelector('defs');
    if (!defs) {
      defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
      svg.insertBefore(defs, svg.firstChild);
    }
    var pat = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
    pat.setAttribute('id', id);
    pat.setAttribute('patternUnits', 'userSpaceOnUse');
    pat.setAttribute('width', '8');
    pat.setAttribute('height', '8');
    pat.setAttribute('patternTransform', 'rotate(45)');
    var base = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    base.setAttribute('width', '8'); base.setAttribute('height', '8');
    base.setAttribute('fill', mapColorFor(owner));
    var stripe = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    stripe.setAttribute('width', '4'); stripe.setAttribute('height', '8');
    stripe.setAttribute('fill', uiColorFor(occupier));
    stripe.setAttribute('fill-opacity', '0.65');
    pat.appendChild(base); pat.appendChild(stripe);
    defs.appendChild(pat);
    return id;
  }

  function mapColorFor(owner) {
    if (!owner || owner === 'sea') return '#2a4a6a';
    var c = state.countries[owner];
    if (c && c.colors && c.colors.map) return c.colors.map;
    if (state.palette[owner] && state.palette[owner].map) return state.palette[owner].map;
    return '#3a3a3a';
  }
  function uiColorFor(owner) {
    if (!owner) return '#888';
    var c = state.countries[owner];
    if (c && c.colors && c.colors.ui) return c.colors.ui;
    if (state.palette[owner] && state.palette[owner].ui) return state.palette[owner].ui;
    return '#888';
  }
  function countryName(id) {
    var c = state.countries[id];
    if (c && c.name) return c.name;
    return id ? id.charAt(0).toUpperCase() + id.slice(1) : '';
  }

  function hexPoints(cx, cy, r) {
    var pts = [];
    for (var i = 0; i < 6; i++) {
      var a = Math.PI / 180 * (60 * i - 30);
      pts.push((cx + r * Math.cos(a)).toFixed(2) + ',' + (cy + r * Math.sin(a)).toFixed(2));
    }
    return pts.join(' ');
  }
  function hexCenter(row, col, r) {
    var w = Math.sqrt(3) * r;
    var h = 1.5 * r;
    var xOff = (row % 2 === 1) ? w / 2 : 0;
    return { x: PAD + col * w + xOff + w / 2, y: PAD + row * h + r };
  }

  function addText(svg, x, y, text, cls) {
    var t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    t.setAttribute('x', x);
    t.setAttribute('y', y);
    if (cls) t.setAttribute('class', cls);
    t.textContent = text;
    svg.appendChild(t);
    return t;
  }

  // ================================================================
  // Combat Ticker
  // ================================================================
  function renderCombatTicker() {
    var el = document.getElementById('combatTicker');
    if (!el) return;
    if (!state.combats || !state.combats.length) {
      el.innerHTML = '<div class="obs-feed-empty">No combats this round.</div>';
      return;
    }
    el.innerHTML = '';
    state.combats.forEach(function (c) {
      var card = document.createElement('div');
      card.className = 'obs-combat-card';
      card.addEventListener('click', function () { card.classList.toggle('expanded'); });
      var atk = c.attacker_country || '?';
      var def = c.defender_country || '?';
      var coord = (c.location_global_row != null && c.location_global_col != null)
        ? '@(' + c.location_global_row + ',' + c.location_global_col + ')' : '';
      var ctype = c.combat_type || 'combat';

      // Extract dice/outcome hints
      var rolls = Array.isArray(c.attacker_rolls) ? c.attacker_rolls : [];
      var firstRoll = rolls[0] || {};
      var diceTxt = '';
      if (firstRoll.roll != null && firstRoll.threshold != null) {
        var hit = firstRoll.roll <= firstRoll.threshold;
        diceTxt = '🎲 roll ' + fmtDice(firstRoll.roll) + ' vs ' + fmtDice(firstRoll.threshold) + ' → ' + (hit ? 'HIT' : 'MISS');
      } else if (firstRoll.outcome) {
        diceTxt = '🎲 ' + firstRoll.outcome;
      }
      var probTxt = firstRoll.threshold != null
        ? 'Probability: ' + Math.round(firstRoll.threshold * 100) + '%'
        : '';

      var destroyed = Array.isArray(c.defender_losses) ? c.defender_losses : [];
      var destroyedTxt = destroyed.length
        ? '💥 Destroyed: ' + destroyed.map(function (x) { return typeof x === 'string' ? x : (x.unit_code || x.id || '?'); }).join(', ')
        : '';

      card.innerHTML =
        '<div class="obs-combat-head">' +
          '<span class="obs-combat-title">⚔ R' + (c.round_num != null ? c.round_num : state.round) +
            ' • <b style="color:' + uiColorFor(atk) + '">' + escapeHtml(atk) + '</b>' +
            ' → <b style="color:' + uiColorFor(def) + '">' + escapeHtml(def) + '</b> ' + escapeHtml(coord) + '</span>' +
          '<span class="obs-combat-type">' + escapeHtml(ctype.replace(/_/g, ' ')) + '</span>' +
        '</div>' +
        '<div class="obs-combat-body">' +
          (probTxt ? '<div class="obs-combat-line">' + escapeHtml(probTxt) + (diceTxt ? ' | ' + escapeHtml(diceTxt) : '') + '</div>' : '') +
          (destroyedTxt ? '<div class="obs-combat-line dmg">' + escapeHtml(destroyedTxt) + '</div>' : '') +
          (c.narrative ? '<div class="obs-combat-narrative">' + escapeHtml(c.narrative) + '</div>' : '') +
        '</div>' +
        '<pre class="obs-combat-detail">' + escapeHtml(JSON.stringify({
          attacker_units: c.attacker_units, defender_units: c.defender_units,
          attacker_rolls: c.attacker_rolls, defender_rolls: c.defender_rolls,
          attacker_losses: c.attacker_losses, defender_losses: c.defender_losses,
        }, null, 2)) + '</pre>';
      el.appendChild(card);
    });
  }

  function fmtDice(n) {
    if (typeof n !== 'number') return String(n);
    return n.toFixed(2);
  }

  // ================================================================
  // Activity Feed
  // ================================================================
  function renderFeed() {
    wireFeedToolbar();
    renderFeedChips();
    populateFeedSelects();
    renderFeedBody();
  }

  function wireFeedToolbar() {
    var chips = document.getElementById('feedChips');
    var countrySel = document.getElementById('feedCountry');
    var roundSel = document.getElementById('feedRound');
    var search = document.getElementById('feedSearch');
    if (!chips || chips._wired) return;
    chips._wired = true;
    countrySel.addEventListener('change', function () { state.feedFilterCountry = this.value; renderFeedBody(); });
    roundSel.addEventListener('change', function () { state.feedFilterRound = this.value; renderFeedBody(); });
    search.addEventListener('input', function () { state.feedSearch = this.value.toLowerCase(); renderFeedBody(); });
  }

  var FEED_CATEGORIES = [
    { key: 'all',        label: 'All' },
    { key: 'round',      label: '🌍 Round' },
    { key: 'action',     label: '🎯 Action' },
    { key: 'combat',     label: '⚔ Combat' },
    { key: 'diplomatic', label: '🤝 Diplo' },
    { key: 'memory',     label: '💭 Memory' },
  ];

  function renderFeedChips() {
    var el = document.getElementById('feedChips');
    if (!el) return;
    var counts = { all: state.events.length, round: 0, action: 0, combat: 0, diplomatic: 0, memory: 0 };
    state.events.forEach(function (ev) {
      var c = classifyEvent(ev.event_type);
      if (counts[c] != null) counts[c]++;
    });
    el.innerHTML = '';
    FEED_CATEGORIES.forEach(function (cat) {
      var b = document.createElement('button');
      b.className = 'obs-feed-chip' + (state.feedFilterType === cat.key ? ' active' : '');
      b.innerHTML = cat.label + ' <span class="count">' + counts[cat.key] + '</span>';
      b.addEventListener('click', function () {
        state.feedFilterType = cat.key;
        renderFeedChips();
        renderFeedBody();
      });
      el.appendChild(b);
    });
  }

  function populateFeedSelects() {
    var countrySel = document.getElementById('feedCountry');
    var roundSel = document.getElementById('feedRound');
    if (!countrySel || !roundSel) return;
    // Countries — collect from events
    var countries = {};
    var rounds = {};
    state.events.forEach(function (ev) {
      if (ev.country_code) countries[ev.country_code] = true;
      if (ev.round_num != null) rounds[ev.round_num] = true;
    });
    var curC = state.feedFilterCountry;
    var curR = state.feedFilterRound;
    countrySel.innerHTML = '<option value="">All countries</option>' +
      Object.keys(countries).sort().map(function (c) {
        return '<option value="' + c + '"' + (c === curC ? ' selected' : '') + '>' + c + '</option>';
      }).join('');
    roundSel.innerHTML = '<option value="">All rounds</option>' +
      Object.keys(rounds).sort(function (a, b) { return parseInt(b) - parseInt(a); }).map(function (r) {
        return '<option value="' + r + '"' + (r === curR ? ' selected' : '') + '>Round ' + r + '</option>';
      }).join('');
  }

  function renderFeedBody() {
    var el = document.getElementById('activityFeed');
    if (!el) return;
    var filtered = state.events.filter(function (ev) {
      if (state.feedFilterType !== 'all' && classifyEvent(ev.event_type) !== state.feedFilterType) return false;
      if (state.feedFilterCountry && ev.country_code !== state.feedFilterCountry) return false;
      if (state.feedFilterRound && String(ev.round_num) !== state.feedFilterRound) return false;
      if (state.feedSearch) {
        var hay = ((ev.summary || '') + ' ' + (ev.event_type || '') + ' ' + (ev.country_code || '')).toLowerCase();
        if (hay.indexOf(state.feedSearch) < 0) return false;
      }
      return true;
    });
    if (!filtered.length) {
      el.innerHTML = '<div class="obs-feed-empty">No events match the current filters.</div>';
      return;
    }
    el.innerHTML = '';
    var lastRound = null;
    filtered.forEach(function (ev) {
      if (ev.round_num !== lastRound) {
        lastRound = ev.round_num;
        var div = document.createElement('div');
        div.className = 'obs-feed-round-divider';
        div.textContent = 'Round ' + (ev.round_num == null ? '—' : ev.round_num);
        el.appendChild(div);
      }
      var typeClass = classifyEvent(ev.event_type);
      var item = document.createElement('div');
      item.className = 'obs-feed-item';
      item.setAttribute('data-type', typeClass);
      item.addEventListener('click', function () { item.classList.toggle('expanded'); });
      var time = formatTime(ev.created_at);
      var emoji = emojiForEvent(ev.event_type);
      var country = ev.country_code ? '<span class="obs-feed-item-country">' + escapeHtml(ev.country_code) + '</span>' : '';
      var detail = ev.payload && Object.keys(ev.payload).length ? JSON.stringify(ev.payload, null, 2) : '';
      item.innerHTML =
        '<div class="obs-feed-item-head">' +
          '<span class="obs-feed-item-time">' + escapeHtml(time) + '</span>' +
          '<span class="obs-feed-item-emoji">' + emoji + '</span>' +
          country +
        '</div>' +
        '<div class="obs-feed-item-summary">' + escapeHtml(ev.summary || ev.event_type || '(no summary)') + '</div>' +
        (detail ? '<div class="obs-feed-item-detail">' + escapeHtml(detail) + '</div>' : '');
      el.appendChild(item);
    });
    setMeta('feedMeta', filtered.length + ' / ' + state.events.length);
  }

  function classifyEvent(etype) {
    if (!etype) return 'action';
    if (etype.indexOf('combat') >= 0) return 'combat';
    if (etype.indexOf('memory') >= 0) return 'memory';
    if (etype.indexOf('round') >= 0) return 'round';
    if (etype.indexOf('diplomat') >= 0 || etype.indexOf('conversation') >= 0) return 'diplomatic';
    return 'action';
  }
  function emojiForEvent(etype) {
    if (!etype) return '•';
    if (etype.indexOf('combat') >= 0) return '⚔';
    if (etype.indexOf('memory') >= 0) return '💭';
    if (etype.indexOf('round') >= 0) return '🌍';
    if (etype.indexOf('diplomat') >= 0) return '🤝';
    if (etype.indexOf('conversation') >= 0) return '💬';
    if (etype.indexOf('action') >= 0) return '🎯';
    return '•';
  }

  // ================================================================
  // Controls
  // ================================================================
  function onNewRun() {
    var confirmed = confirm(
      'Start a NEW test run?\n\n' +
      'This will WIPE all existing round data for this scenario:\n' +
      '  • All rounds >= 1\n' +
      '  • All agent decisions + memories\n' +
      '  • All combat results + events\n\n' +
      'Round 0 (Template v1.0 snapshot) is preserved.\n\n' +
      'Continue?'
    );
    if (!confirmed) return;
    var defaultName = 'Run ' + new Date().toISOString().slice(0, 16).replace('T', ' ');
    var name = prompt('Name this new test run:', defaultName);
    if (name === null) return;
    name = name.trim() || defaultName;
    postJSON('/api/observatory/reset', { scenario: state.scenario }).then(function (r) {
      if (!r || !r.success) {
        alert('Reset failed: ' + (r && r.error || 'unknown error'));
        return;
      }
      // Reset scrubber to live tracking
      state.viewRound = null;
      state.globalSeries = [];
      state.prevCountryStates = {};
      postJSON('/api/observatory/start', {
        scenario: state.scenario,
        total_rounds: state.totalRounds,
        run_name: name,
      }).then(function (s) {
        if (s && s.state) applyRuntime(s.state);
        refreshAll();
      });
    });
  }

  function onStart() {
    var existingName = (state.runtime && state.runtime.run_name) || '';
    var defaultName = 'Run ' + new Date().toISOString().slice(0, 16).replace('T', ' ');
    var name = existingName || prompt('Name this test run:', defaultName);
    if (name === null) return;
    name = (name || '').trim() || defaultName;
    postJSON('/api/observatory/start', {
      scenario: state.scenario,
      total_rounds: state.totalRounds,
      run_name: name,
    }).then(function (r) {
      if (r && r.state) applyRuntime(r.state);
      refreshAll();
    });
  }
  function onPause() { postJSON('/api/observatory/pause', {}).then(function (r) { if (r && r.state) applyRuntime(r.state); }); }
  function onStop() {
    if (!confirm('Stop the simulation? Current agent will finish, then halt.')) return;
    postJSON('/api/observatory/stop', {}).then(function (r) { if (r && r.state) applyRuntime(r.state); });
  }
  function onResume() { postJSON('/api/observatory/resume', {}).then(function (r) { if (r && r.state) applyRuntime(r.state); }); }
  function onRewind() {
    var to = prompt('Rewind to round #', Math.max(0, state.round - 1));
    if (to == null) return;
    var n = parseInt(to, 10);
    if (isNaN(n) || n < 0) return;
    postJSON('/api/observatory/rewind', { to_round: n }).then(function (r) {
      if (r && r.state) applyRuntime(r.state);
      refreshAll();
    });
  }
  function onSpeedChange(ev) {
    var s = parseInt(ev.target.value, 10) || 15;
    state.speedSec = s;
    postJSON('/api/observatory/speed', { speed_sec: s }).then(function (r) { if (r && r.state) applyRuntime(r.state); });
  }

  // ================================================================
  // Detail panel
  // ================================================================
  function selectHex(rIdx, cIdx) {
    var data = currentMapData();
    if (!data) return;
    var hex = data.grid[rIdx][cIdx];
    var r1 = rIdx + 1, c1 = cIdx + 1;
    var key1 = r1 + ',' + c1;
    // Collect units on this hex
    var here = (state.view === 'global') ? (state.unitsByHex[key1] || []) : [];
    var ownerName = countryName(hex.owner || '') || '(unowned)';
    var cp = null;
    if (state.view === 'global' && state.globalMap && state.globalMap.chokepoints) {
      Object.values(state.globalMap.chokepoints).forEach(function (p) {
        if (p.row === rIdx && p.col === cIdx) cp = p.name;
      });
    }
    var html = '<h3>' + escapeHtml(cp || (hex.owner === 'sea' ? 'Open Waters' : ownerName + ' Territory')) + '</h3>';
    html += '<div class="obs-detail-row"><span class="k">Coord</span><span class="v">' + key1 + '</span></div>';
    html += '<div class="obs-detail-row"><span class="k">Owner</span><span class="v" style="color:' + uiColorFor(hex.owner) + '">' + escapeHtml(hex.owner || '—') + '</span></div>';
    if (cp) html += '<div class="obs-detail-row"><span class="k">Chokepoint</span><span class="v">yes</span></div>';
    if (here.length) {
      html += '<div style="margin-top:10px;font-weight:600;color:var(--text-primary);font-size:11px">Units (' + here.length + ')</div>';
      // Group by country+type
      var byCT = {};
      here.forEach(function (u) {
        var k = (u.country_code || u.country_id) + '|' + u.unit_type;
        byCT[k] = byCT[k] || { country: u.country_code || u.country_id, type: u.unit_type, count: 0 };
        byCT[k].count++;
      });
      Object.keys(byCT).forEach(function (k) {
        var e = byCT[k];
        html += '<div class="obs-detail-row"><span class="k" style="color:' + uiColorFor(e.country) + '">' + escapeHtml(e.country) + '</span><span class="v">' + escapeHtml(e.type.replace('_', ' ')) + ' × ' + e.count + '</span></div>';
      });
    } else {
      html += '<div style="margin-top:10px;color:var(--text-muted);font-style:italic;font-size:11px">No units on this hex.</div>';
    }
    openDetail(html);
  }

  function showCountryDetail(code) {
    var country = state.countries[code] || {};
    var byCode = {};
    state.countryStates.forEach(function (cs) {
      var c = cs.country_code || cs.country_id || cs.id;
      if (c) byCode[c] = cs;
    });
    var cs = byCode[code] || {};
    var rows = [
      ['GDP', '$' + fmtNum(numOr(cs.gdp, 0))],
      ['Treasury', '$' + fmtNum(numOr(cs.treasury, 0))],
      ['Inflation', (numOr(cs.inflation, 0)).toFixed(2)],
      ['Stability', String(intOr(cs.stability, 5))],
      ['Pol. Support', String(intOr(cs.political_support, 50))],
      ['War Tiredness', String(intOr(cs.war_tiredness, 0))],
      ['Nuclear Lvl', String(intOr(cs.nuclear_level, 0))],
      ['AI Level', String(intOr(cs.ai_level, 0))],
      ['At War With', (country.at_war_with || []).join(', ') || '—'],
      ['Regime', country.regime || '—'],
    ];
    var html = '<h3>' + escapeHtml(country.name || code) + '</h3>';
    rows.forEach(function (r) {
      html += '<div class="obs-detail-row"><span class="k">' + escapeHtml(r[0]) + '</span><span class="v">' + escapeHtml(r[1]) + '</span></div>';
    });
    openDetail(html);
  }
  function showUnitDetail(entry) {
    var html = '<h3>' + escapeHtml(entry.country) + ' — ' + escapeHtml(entry.type.replace('_', ' ')) + '</h3>';
    html += '<div class="obs-detail-row"><span class="k">Count</span><span class="v">' + entry.count + '</span></div>';
    entry.units.slice(0, 12).forEach(function (u) {
      html += '<div class="obs-detail-row"><span class="k">' + escapeHtml(u.unit_code || u.unit_id || '?') + '</span>' +
              '<span class="v">' + escapeHtml(u.status || 'active') + (u.notes ? ' · ' + escapeHtml(u.notes) : '') + '</span></div>';
    });
    openDetail(html);
  }
  function openDetail(html) {
    var p = document.getElementById('detailPanel');
    document.getElementById('detailContent').innerHTML = html;
    p.style.display = 'block';
  }
  function closeDetail() { document.getElementById('detailPanel').style.display = 'none'; }

  // ================================================================
  // Supabase Realtime
  // ================================================================
  function tryRealtime() {
    fetchJSON('/api/observatory/realtime_config').then(function (cfg) {
      if (!cfg || !cfg.supabase_url || !cfg.supabase_anon_key) {
        console.info('[observatory] Realtime config not present — using polling only.');
        return;
      }
      var s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js';
      s.onload = function () {
        try {
          var client = window.supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key, {
            realtime: { params: { eventsPerSecond: 10 } },
          });
          client.channel('obs-units')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'unit_states_per_round' },
                function () { refreshAll(); }).subscribe();
          client.channel('obs-events')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'observatory_events' },
                function () { refreshAll(); }).subscribe();
          client.channel('obs-rounds')
            .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'round_states' },
                function () { refreshAll(); }).subscribe();
          client.channel('obs-combats')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'observatory_combat_results' },
                function () { refreshAll(); }).subscribe();
          console.info('[observatory] Supabase Realtime subscribed.');
          setPill('ok', 'realtime');
        } catch (e) { console.warn('[observatory] Realtime setup failed, polling only.', e); }
      };
      s.onerror = function () { console.warn('[observatory] Supabase JS CDN load failed — polling only.'); };
      document.head.appendChild(s);
    }).catch(function () { /* polling only */ });
  }

  // ================================================================
  // Utilities
  // ================================================================
  function fetchJSON(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ' → ' + r.status);
      return r.json();
    });
  }
  function postJSON(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    }).then(function (r) { return r.ok ? r.json() : null; }).catch(noop);
  }
  function noop() { return null; }
  function setPill(kind, text) {
    var p = document.getElementById('obsStatusPill');
    p.className = 'status-pill ' + (kind || '');
    p.textContent = text;
  }
  function setMeta(id, text) { var el = document.getElementById(id); if (el) el.textContent = text; }
  function showMapError(msg) {
    var el = document.getElementById('mapError');
    el.textContent = msg; el.style.display = 'block';
  }
  function escapeHtml(s) {
    if (s == null) return '';
    return String(s).replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }
  function intOr(v, d) { var n = parseInt(v, 10); return isNaN(n) ? d : n; }
  function numOr(v, d) { var n = parseFloat(v); return isNaN(n) ? d : n; }
  function fmtNum(n) {
    if (n >= 1e12) return (n / 1e12).toFixed(1) + 'T';
    if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return (n / 1e6).toFixed(0) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(0) + 'k';
    return String(Math.round(n));
  }
  function formatTime(iso) {
    if (!iso) return '—';
    try {
      var d = new Date(iso);
      var hh = String(d.getHours()).padStart(2, '0');
      var mm = String(d.getMinutes()).padStart(2, '0');
      return hh + ':' + mm;
    } catch (e) { return '—'; }
  }

})();
