/* TTT Map Viewer — vanilla JS SVG renderer
 * Loads global + theater JSON + deployments.csv, renders pointy-top hex grids,
 * supports click-to-inspect and global -> theater drill-down.
 */

(function () {
  'use strict';

  // ---------- Display mode ----------
  // ?display=clean hides all chrome (header, sidebar, inspector, edit panel)
  // Used by public screen, participant interface, and any embed.
  const urlParams = new URLSearchParams(window.location.search);
  const DISPLAY_CLEAN = urlParams.get('display') === 'clean';
  // ?theater=eastern_ereb or ?theater=mashriq — render only that theater
  const FORCE_THEATER = urlParams.get('theater') || null;
  // ?mode=attack&country=X — attack mode: clicks send postMessage to parent
  const ATTACK_MODE = urlParams.get('mode') === 'attack';
  const ATTACK_COUNTRY = urlParams.get('country') || null;
  // sim_run_id at module scope (needed by message listener)
  const SIM_RUN_ID_PARAM = urlParams.get('sim_run_id') || null;
  if (DISPLAY_CLEAN) {
    document.documentElement.style.cssText = 'margin:0; padding:0; overflow:hidden; background:#0A0E1A;';
    document.body.style.cssText = 'margin:0; padding:0; overflow:hidden; background:#0A0E1A;';
    // Hide chrome — runs both immediately and on DOMContentLoaded for reliability
    const applyClean = () => {
      const hide = (sel) => { const el = document.querySelector(sel); if (el) el.style.display = 'none'; };
      hide('.app-header');
      hide('.legend');
      hide('.inspector');
      hide('.edit-panel');
      hide('#editWarnings');
      hide('#editToast');
      const main = document.querySelector('.app-main');
      if (main) main.style.cssText = 'display:block; height:100vh; width:100vw; padding:0; margin:0;';
      const stage = document.querySelector('.map-stage');
      if (stage) stage.style.cssText = 'width:100%; height:100%; padding:0; margin:0;';
      const svg = document.getElementById('mapSvg');
      if (svg) svg.style.cssText = 'width:100%; height:100%;';
    };
    // Try immediately (script at bottom of body — DOM likely ready)
    applyClean();
    // Also on DOMContentLoaded as fallback
    document.addEventListener('DOMContentLoaded', applyClean);
  }

  // ---------- State ----------
  const state = {
    global: null,
    theaters: { eastern_ereb: null, mashriq: null },
    deployments: null,   // legacy compat shim: {rows, by_hex}
    countries: null,     // {countries, palette}
    view: 'global',      // 'global' | 'eastern_ereb' | 'mashriq'
    selected: null,      // {row, col} in current view
    // --- Edit mode ---
    editMode: false,
    editableUnits: null,   // mutable copy of units list when in edit mode
    editDirty: false,
    editCountry: null,     // currently selected country in edit panel
    editUnitType: null,    // currently expanded unit type
    armedUnitId: null,     // id of unit selected for placement
  };

  // ---------- Constants ----------
  const HEX_R_GLOBAL = 34;   // circumradius
  const HEX_R_THEATER = 40;
  const PAD = 60;            // padding around grid

  // Theater display labels — sourced from central MAP_CONFIG.
  // Legacy per-hex linkage tables (MASHRIQ_LINKS) removed — use
  // window.MAP_CONFIG.theaterLinkHexes() / theaterForGlobalHex().
  const THEATER_LABELS = (function () {
    const out = {};
    const cfg = (window.MAP_CONFIG && window.MAP_CONFIG.THEATERS) || {};
    Object.keys(cfg).forEach(k => { out[k] = cfg[k].display_name; });
    return out;
  })();

  // (Legacy zone_id tables removed — units now carry coords directly.)

  // ---------- Boot ----------
  document.addEventListener('DOMContentLoaded', init);

  async function init() {
    const geographyMode = window.MAP_VIEWER_MODE === 'geography';
    setStatus('loading', 'Loading data…');
    try {
      // Core map data (always needed)
      const [g, ee, mq, cs] = await Promise.all([
        fetchJson('/api/map/global'),
        fetchJson('/api/map/theater/eastern_ereb'),
        fetchJson('/api/map/theater/mashriq'),
        fetchJson('/api/map/countries'),
      ]);
      state.global = g;
      state.theaters.eastern_ereb = ee;
      state.theaters.mashriq = mq;
      state.countries = cs;

      // Unit data (skip in geography mode)
      // sim_run_id is required for unit display — always load from FastAPI
      const SIM_RUN_ID = urlParams.get('sim_run_id');
      if (!geographyMode) {
        let un;
        if (SIM_RUN_ID) {
          un = await fetchJson(`/api/sim/${SIM_RUN_ID}/map/units`);
        } else {
          // Fallback: try legacy endpoint (template editor, standalone viewer)
          un = await fetchJson('/api/map/units');
        }
        state.deployments = { rows: [], by_hex: {} };
        // Fill in missing global coords only (respects canonical mapping as default)
        (un.units || []).forEach(u => {
          if (u.theater && u.theater_row != null && u.theater_col != null &&
              (u.global_row == null || u.global_col == null)) {
            const g = globalHexForTheaterCell(u.theater, u.theater_row, u.theater_col);
            if (g) { u.global_row = g[0]; u.global_col = g[1]; }
          }
        });
        state.units = un;
        // Load occupation from DB (authoritative — respects basing rights)
        await loadHexControl();
      } else {
        state.deployments = { rows: [], by_hex: {} };
        state.units = { units: [] };
      }

      // Load combat events for blast markers (only with sim_run_id)
      state.combatEvents = [];
      if (SIM_RUN_ID) {
        try {
          const evtsResp = await fetch(`/api/sim/${SIM_RUN_ID}/state`).catch(() => null);
          const simState = evtsResp && evtsResp.ok ? await evtsResp.json() : null;
          const currentRound = simState?.current_round || 1;

          const combatResp = await fetch(
            `/api/sim/${SIM_RUN_ID}/map/combat-events?round_num=${currentRound}`
          ).catch(() => null);
          if (combatResp && combatResp.ok) {
            const combatData = await combatResp.json();
            state.combatEvents = combatData.events || [];
          }
        } catch (e) { console.debug('combat events load failed:', e); }
      }

      buildCountryLegend();
      // If a specific theater is requested, render it directly; otherwise global
      renderView(FORCE_THEATER && state.theaters[FORCE_THEATER] ? FORCE_THEATER : 'global');
      const unitInfo = geographyMode ? '' : ` · ${state.deployments.rows.length} unit entries`;
      setStatus('ok', `${countLandHexes(g)} land hexes${unitInfo}`);
    } catch (err) {
      console.error(err);
      showError(`Failed to load map data: ${err.message}`);
      setStatus('err', 'Error');
    }

    document.getElementById('backBtn').addEventListener('click', () => {
      renderView('global');
    });

    // Edit mode wiring (skip in geography mode — edit buttons don't exist)
    if (!geographyMode) {
      document.getElementById('editBtn')?.addEventListener('click', toggleEditMode);
      document.getElementById('editSaveBtn')?.addEventListener('click', () => saveLayout(false));
      document.getElementById('editSaveAsBtn')?.addEventListener('click', () => saveLayout(true));
      document.getElementById('editResetBtn')?.addEventListener('click', resetCountryToReserve);
      document.getElementById('editClearAllBtn')?.addEventListener('click', clearAllDeployments);
      document.getElementById('editLoadBtn')?.addEventListener('click', loadLayout);
      document.getElementById('editUndoBtn')?.addEventListener('click', undoEdit);
      document.getElementById('editRedoBtn')?.addEventListener('click', redoEdit);

      // View-mode layout picker — populate & wire
      refreshViewLayoutList();
      document.getElementById('viewLayoutSelect')?.addEventListener('change', viewLoadLayout);
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && state.armedUnitId) {
        disarmUnit();
      }
      if (e.key === 'Escape') closeHexPopover();
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && state.editMode) {
        e.preventDefault();
        if (e.shiftKey) redoEdit(); else undoEdit();
      }
    });
  }

  async function fetchJson(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${url} -> ${r.status}`);
    return r.json();
  }

  function setStatus(kind, text) {
    const p = document.getElementById('statusPill');
    p.textContent = text;
    p.className = 'status-pill' + (kind ? ' ' + kind : '');
  }

  function showError(msg) {
    const el = document.getElementById('mapError');
    el.textContent = msg;
    el.style.display = 'block';
  }

  function countLandHexes(g) {
    let n = 0;
    g.grid.forEach(row => row.forEach(h => { if (h.owner && h.owner !== 'sea') n++; }));
    return n;
  }

  // ---------- Country colors ----------
  function colorFor(ownerId) {
    const p = state.countries?.palette?.[ownerId];
    if (p) return p.map;
    if (ownerId === 'sea') return '#2a4a6a';
    return '#556677';
  }
  function uiColorFor(ownerId) {
    const p = state.countries?.palette?.[ownerId];
    return (p && p.ui) || '#888';
  }
  function countryName(id) {
    const c = state.countries?.countries?.[id];
    if (c && c.name) return c.name;
    return id ? id.charAt(0).toUpperCase() + id.slice(1) : '';
  }

  // ---------- Hex geometry (pointy-top, offset rows) ----------
  function hexPoints(cx, cy, r) {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const angle = Math.PI / 180 * (60 * i - 30); // pointy-top
      pts.push([cx + r * Math.cos(angle), cy + r * Math.sin(angle)]);
    }
    return pts.map(p => p[0].toFixed(2) + ',' + p[1].toFixed(2)).join(' ');
  }
  function hexCenter(row, col, r) {
    // pointy-top offset: horizontal distance = sqrt(3) * r; vertical = 1.5 * r
    const w = Math.sqrt(3) * r;
    const h = 1.5 * r;
    const xOffset = (row % 2 === 1) ? w / 2 : 0;
    return {
      x: PAD + col * w + xOffset + w / 2,
      y: PAD + row * h + r,
    };
  }

  // ---------- Render a view ----------
  function renderView(viewName) {
    state.view = viewName;
    state.selected = null;
    clearInspector();

    const svg = document.getElementById('mapSvg');
    svg.classList.add('fading');

    setTimeout(() => {
      // swap content
      if (viewName === 'global') {
        const backBtn = document.getElementById('backBtn');
        if (backBtn) backBtn.style.display = 'none';
        const sub = document.getElementById('mapSubtitle');
        if (sub) sub.textContent = '— Global';
        renderGlobal(svg);
        renderBlastMarkers(svg, 'global');
      } else {
        const backBtn = document.getElementById('backBtn');
        if (backBtn) backBtn.style.display = 'inline-block';
        const sub2 = document.getElementById('mapSubtitle');
        if (sub2) sub2.textContent = '— ' + THEATER_LABELS[viewName];
        renderTheater(svg, viewName);
        renderBlastMarkers(svg, viewName);
      }
      svg.classList.remove('fading');
    }, 150);
  }

  // ---------- Global view ----------
  function renderGlobal(svg) {
    const data = state.global;
    const rows = data.rows, cols = data.cols;
    const r = HEX_R_GLOBAL;

    // compute size
    const w = Math.sqrt(3) * r;
    const h = 1.5 * r;
    const width = PAD * 2 + cols * w + w / 2;
    const height = PAD * 2 + rows * h + r * 0.5;

    svg.innerHTML = '';
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    if (!DISPLAY_CLEAN) {
      svg.setAttribute('width', width);
      svg.setAttribute('height', height);
    }

    // grid edge labels (col numbers on top, row numbers on left)
    for (let c = 0; c < cols; c++) {
      const cx = PAD + c * w + w / 2; // aligned with even-row hex centers
      addText(svg, cx, PAD - 18, String(c + 1), 'grid-edge-label');
    }
    for (let rIdx = 0; rIdx < rows; rIdx++) {
      const cy = PAD + rIdx * h + r;
      addText(svg, PAD - 20, cy, String(rIdx + 1), 'grid-edge-label');
    }

    // Aggregate deployments to global hexes
    const globalUnits = aggregateGlobalUnits();

    // theater-link lookup for this render
    const theaterLinks = buildGlobalTheaterLinks();

    // Render hexes
    for (let rIdx = 0; rIdx < rows; rIdx++) {
      for (let c = 0; c < cols; c++) {
        const hex = data.grid[rIdx][c];
        const center = hexCenter(rIdx, c, r);
        const key1 = `${rIdx + 1},${c + 1}`;
        const theaterKey = theaterLinks[key1];

        const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        poly.setAttribute('points', hexPoints(center.x, center.y, r));
        if (hex.occupied_by) {
          const patId = ensurePattern(svg, hex.owner, hex.occupied_by);
          poly.setAttribute('fill', `url(#${patId})`);
        } else {
          poly.setAttribute('fill', colorFor(hex.owner));
        }
        let cls = 'hex';
        if (hex.owner === 'sea') cls += ' sea';
        if (theaterKey) cls += ' theater-link';
        poly.setAttribute('class', cls);
        poly.dataset.row = rIdx;
        poly.dataset.col = c;
        poly.dataset.owner = hex.owner || 'sea';
        poly.addEventListener('click', () => selectHex(rIdx, c));
        svg.appendChild(poly);
      }
    }

    // Chokepoints labels
    const cps = data.chokepoints || {};
    Object.keys(cps).forEach(k => {
      const cp = cps[k];
      const center = hexCenter(cp.row, cp.col, r);
      // replace fill with cp styling
      const poly = svg.querySelector(`polygon[data-row="${cp.row}"][data-col="${cp.col}"]`);
      if (poly) poly.classList.add('chokepoint');
      addText(svg, center.x, center.y - 2, cp.name.toUpperCase(), 'chokepoint-label');
    });

    // Hex labels (row,col) - only for land
    for (let rIdx = 0; rIdx < rows; rIdx++) {
      for (let c = 0; c < cols; c++) {
        const hex = data.grid[rIdx][c];
        if (hex.owner === 'sea') continue;
        const center = hexCenter(rIdx, c, r);
        addText(svg, center.x, center.y - 12, `${rIdx + 1},${c + 1}`, 'hex-label');
      }
    }

    // Country name labels at centroid
    renderCountryLabels(svg, data, r);

    // Units
    // Units overlay (skip in geography-only mode)
    if (window.MAP_VIEWER_MODE !== 'geography') {
      for (let rIdx = 0; rIdx < rows; rIdx++) {
        for (let c = 0; c < cols; c++) {
          const key1 = `${rIdx + 1},${c + 1}`;
          const units = globalUnits[key1];
          if (!units || units.length === 0) continue;
          const center = hexCenter(rIdx, c, r);
          renderUnitStack(svg, center.x, center.y + 6, units, 'global');
        }
      }
      renderEmbarkBadges(svg,'global', r);
    }

    // Nuclear sites overlay — read from template data, not hardcoded
    // Sources: (1) saved nuclearSites in global JSON, (2) MAP_CONFIG fallback
    const savedNuclear = data.nuclearSites || data.nuclear_sites || {};
    const configNuclear = (window.MAP_CONFIG && window.MAP_CONFIG.NUCLEAR_SITES) || {};
    const nuclearSites = Object.keys(savedNuclear).length > 0 ? savedNuclear : configNuclear;
    Object.entries(nuclearSites).forEach(([country, coords]) => {
      const [nRow, nCol] = Array.isArray(coords) ? coords : [coords.row + 1, coords.col + 1]; // 1-indexed
      const center = hexCenter(nRow - 1, nCol - 1, r);
      // Mark the hex polygon with data-nuclear
      const poly = svg.querySelector(`polygon[data-row="${nRow - 1}"][data-col="${nCol - 1}"]`);
      if (poly) poly.dataset.nuclear = 'true';
      // Classic radiation trefoil ☢
      const nuc = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      nuc.setAttribute('x', center.x);
      nuc.setAttribute('y', center.y + r * 0.15);
      nuc.setAttribute('text-anchor', 'middle');
      nuc.setAttribute('dominant-baseline', 'central');
      nuc.setAttribute('font-size', r * 0.7);
      nuc.setAttribute('fill', '#B03A3A');
      nuc.style.pointerEvents = 'none';
      nuc.textContent = '☢';
      svg.appendChild(nuc);
    });

    // Render both theaters as collapsible SVGs below the global map
    // Skip in clean display mode (public screen — global map only)
    if (!DISPLAY_CLEAN) {
      const container = document.getElementById('theaterMapsContainer');
      if (container) {
        container.innerHTML = '';
        container.style.cssText = 'display:flex; gap:10px; padding:10px 0; clear:both;';

        const theaters = ['eastern_ereb', 'mashriq'];
        theaters.forEach((tName) => {
          const tData = state.theaters[tName];
          if (!tData) return;
          const tRows = tData.rows || 10;
          const tCols = tData.cols || 10;
          const tR = HEX_R_GLOBAL;
          const tW = Math.sqrt(3) * tR;
          const tSvgW = PAD * 2 + tCols * tW + tW / 2;
          const tSvgH = PAD * 2 + tRows * (1.5 * tR) + tR * 0.5 + 20; // +20 for title

          const wrapper = document.createElement('div');

          // Title (clickable to collapse/expand)
          const titleDiv = document.createElement('div');
          titleDiv.style.cssText = 'cursor:pointer; font-family:var(--font-heading); font-size:13px; color:var(--accent); padding:4px 8px; user-select:none;';
          titleDiv.textContent = '▼ ' + (THEATER_LABELS[tName] || tName);

          const tSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
          tSvg.setAttribute('viewBox', `0 0 ${tSvgW} ${tSvgH}`);
          tSvg.setAttribute('width', tSvgW);
          tSvg.setAttribute('height', tSvgH);
          tSvg.classList.add('map-svg');

          // Start collapsed
          tSvg.style.display = 'none';
          titleDiv.textContent = '▶ ' + (THEATER_LABELS[tName] || tName);

          titleDiv.addEventListener('click', () => {
            const visible = tSvg.style.display !== 'none';
            tSvg.style.display = visible ? 'none' : 'block';
            titleDiv.textContent = (visible ? '▶ ' : '▼ ') + (THEATER_LABELS[tName] || tName);
          });

          // Grid labels
          for (let c = 0; c < tCols; c++) {
            const cx = PAD + c * tW + tW / 2;
            addText(tSvg, cx, PAD - 8, String(c + 1), 'grid-edge-label');
          }
          for (let rr = 0; rr < tRows; rr++) {
            const cy = PAD + rr * (1.5 * tR) + tR;
            addText(tSvg, PAD - 14, cy + 4, String(rr + 1), 'grid-edge-label');
          }

          // Hexes
          for (let rr = 0; rr < tRows; rr++) {
            for (let cc = 0; cc < tCols; cc++) {
              const hex = tData.grid[rr][cc];
              const xOff = (rr % 2 === 1) ? tW / 2 : 0;
              const cx = PAD + cc * tW + xOff + tW / 2;
              const cy = PAD + rr * (1.5 * tR) + tR;
              const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
              poly.setAttribute('points', hexPoints(cx, cy, tR));
              poly.setAttribute('fill', hex.occupied_by ? colorFor(hex.owner) : colorFor(hex.owner));
              let cls = 'hex';
              if (hex.owner === 'sea') cls += ' sea';
              poly.setAttribute('class', cls);
              poly.dataset.row = rr;
              poly.dataset.col = cc;
              poly.dataset.owner = hex.owner || 'sea';
              poly.dataset.theater = tName;
              poly.addEventListener('click', () => renderView(tName));
              tSvg.appendChild(poly);

              if (hex.owner && hex.owner !== 'sea') {
                addText(tSvg, cx, cy - 12, `${rr+1},${cc+1}`, 'hex-label');
              }
            }
          }

          // Die-hards
          const tDieHards = tData.dieHards || {};
          Object.keys(tDieHards).forEach(k => {
            const dh = tDieHards[k];
            const xOff = (dh.row % 2 === 1) ? tW / 2 : 0;
            const cx = PAD + dh.col * tW + xOff + tW / 2;
            const cy = PAD + dh.row * (1.5 * tR) + tR;
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', cx);
            circle.setAttribute('cy', cy);
            circle.setAttribute('r', tR * 0.85);
            circle.setAttribute('class', 'die-hard-marker');
            tSvg.appendChild(circle);
            addText(tSvg, cx, cy + 3, dh.name, 'chokepoint-label');
          });

          wrapper.appendChild(titleDiv);
          wrapper.appendChild(tSvg);
          container.appendChild(wrapper);
        });
      }
    }
  }

  // ---------- Theater view ----------
  function renderTheater(svg, theaterName) {
    const data = state.theaters[theaterName];
    if (!data) { showError('Theater data missing: ' + theaterName); return; }
    const rows = data.rows, cols = data.cols;
    const r = HEX_R_THEATER;

    const w = Math.sqrt(3) * r;
    const h = 1.5 * r;
    const width = PAD * 2 + cols * w + w / 2;
    const height = PAD * 2 + rows * h + r * 0.5;

    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    if (!DISPLAY_CLEAN) {
      svg.setAttribute('width', width);
      svg.setAttribute('height', height);
    }
    svg.innerHTML = '';

    // grid edge labels
    for (let c = 0; c < cols; c++) {
      const cx = PAD + c * w + w / 2; // aligned with even-row hex centers
      addText(svg, cx, PAD - 18, String(c + 1), 'grid-edge-label');
    }
    for (let rIdx = 0; rIdx < rows; rIdx++) {
      const cy = PAD + rIdx * h + r;
      addText(svg, PAD - 20, cy, String(rIdx + 1), 'grid-edge-label');
    }

    // Render hexes
    for (let rIdx = 0; rIdx < rows; rIdx++) {
      for (let c = 0; c < cols; c++) {
        const hex = data.grid[rIdx][c];
        const center = hexCenter(rIdx, c, r);
        const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        poly.setAttribute('points', hexPoints(center.x, center.y, r));

        // Handle occupied hexes with striped pattern (approximate — use occupier color with cross-hatch via filter)
        if (hex.occupied_by) {
          const patId = ensurePattern(svg, hex.owner, hex.occupied_by);
          poly.setAttribute('fill', `url(#${patId})`);
        } else {
          poly.setAttribute('fill', colorFor(hex.owner));
        }
        let cls = 'hex';
        if (hex.owner === 'sea') cls += ' sea';
        poly.setAttribute('class', cls);
        poly.dataset.row = rIdx;
        poly.dataset.col = c;
        poly.dataset.owner = hex.owner || 'sea';
        poly.addEventListener('click', () => selectHex(rIdx, c));
        svg.appendChild(poly);

        // Hex label
        if (hex.owner !== 'sea') {
          addText(svg, center.x, center.y - 16, `${rIdx + 1},${c + 1}`, 'hex-label');
        }
      }
    }

    // Die-Hards
    const dieHards = data.dieHards || {};
    Object.keys(dieHards).forEach(k => {
      const dh = dieHards[k];
      // JSON die-hard coords need +1 row, +1 col correction to match theater map layout.
      const center = hexCenter(dh.row, dh.col, r);
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', center.x);
      circle.setAttribute('cy', center.y);
      circle.setAttribute('r', r * 0.85);
      circle.setAttribute('class', 'die-hard-marker');
      svg.appendChild(circle);
      addText(svg, center.x, center.y + 3, dh.name, 'chokepoint-label');
    });

    // Country name labels at centroid
    renderCountryLabels(svg, data, r);

    // Units overlay (skip in geography-only mode)
    if (window.MAP_VIEWER_MODE !== 'geography') {
      renderEmbarkBadges(svg,theaterName, r);
      const theaterUnits = aggregateTheaterUnits(theaterName);
      for (let rIdx = 0; rIdx < rows; rIdx++) {
        for (let c = 0; c < cols; c++) {
          const key1 = `${rIdx + 1},${c + 1}`;
          const units = theaterUnits[key1];
          if (!units || units.length === 0) continue;
          const center = hexCenter(rIdx, c, r);
          renderUnitStack(svg, center.x, center.y + 6, units, 'theater');
        }
      }
    }

    // Die-hard zones already rendered above (line ~381)
  }

  // ---------- Country name labels at centroid ----------
  // Groups land hexes by owner, computes centroid, renders country name.
  // Skips sea and single-hex countries where the hex label would collide.
  // ---------- Blast markers (combat events) ----------
  function renderBlastMarkers(svg, viewName) {
    if (!state.combatEvents || state.combatEvents.length === 0) return;

    const isGlobal = viewName === 'global';
    const r = isGlobal ? HEX_R_GLOBAL : HEX_R_THEATER;

    state.combatEvents.forEach((evt) => {
      let row, col;
      if (isGlobal) {
        row = evt.global_row;
        col = evt.global_col;
      } else {
        // Theater view — use theater coords if event matches this theater
        if (evt.theater !== viewName) return;
        row = evt.theater_row;
        col = evt.theater_col;
      }
      if (row == null || col == null) return;

      // Convert to 0-indexed for hexCenter
      const center = hexCenter(row - 1, col - 1, r);

      // Explosion burst SVG — starburst shape
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('transform', `translate(${center.x},${center.y})`);
      g.style.pointerEvents = 'none';

      // Outer glow
      const glow = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      glow.setAttribute('r', r * 0.7);
      glow.setAttribute('fill', 'rgba(255,60,20,0.25)');
      glow.setAttribute('stroke', 'none');
      g.appendChild(glow);

      // Starburst
      const burst = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      burst.setAttribute('text-anchor', 'middle');
      burst.setAttribute('dominant-baseline', 'central');
      burst.setAttribute('font-size', r * 0.9);
      burst.setAttribute('fill', '#FF3C14');
      burst.setAttribute('opacity', '0.9');
      burst.textContent = '\u{1F4A5}';  // 💥 explosion emoji
      g.appendChild(burst);

      // Pulsing animation
      const anim = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
      anim.setAttribute('attributeName', 'opacity');
      anim.setAttribute('values', '0.9;0.5;0.9');
      anim.setAttribute('dur', '1.5s');
      anim.setAttribute('repeatCount', 'indefinite');
      glow.appendChild(anim);

      svg.appendChild(g);
    });
  }

  function renderCountryLabels(svg, data, hexRadius) {
    const groups = {}; // owner -> [{x,y}]
    for (let rIdx = 0; rIdx < data.rows; rIdx++) {
      for (let c = 0; c < data.cols; c++) {
        const hex = data.grid[rIdx][c];
        if (!hex || !hex.owner || hex.owner === 'sea') continue;
        const center = hexCenter(rIdx, c, hexRadius);
        (groups[hex.owner] = groups[hex.owner] || []).push(center);
      }
    }
    Object.keys(groups).forEach(owner => {
      const pts = groups[owner];
      // True geometric centroid — label can sit between hexes, classic cartographic style
      const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
      const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;
      const t = addText(svg, cx, cy, countryName(owner).toUpperCase(), 'country-label');
      t.style.fill = uiColorFor(owner);
    });
  }

  // ---------- SVG helpers ----------
  function addText(svg, x, y, text, cls) {
    const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    t.setAttribute('x', x);
    t.setAttribute('y', y);
    if (cls) t.setAttribute('class', cls);
    t.textContent = text;
    svg.appendChild(t);
    return t;
  }

  // Pattern for occupied hexes (diagonal stripes)
  function ensurePattern(svg, owner, occupier) {
    const id = `occ_${owner}_${occupier}`;
    if (document.getElementById(id)) return id;
    let defs = svg.querySelector('defs');
    if (!defs) {
      defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
      svg.insertBefore(defs, svg.firstChild);
    }
    const pat = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
    pat.setAttribute('id', id);
    pat.setAttribute('patternUnits', 'userSpaceOnUse');
    pat.setAttribute('width', '8');
    pat.setAttribute('height', '8');
    pat.setAttribute('patternTransform', 'rotate(45)');
    const base = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    base.setAttribute('width', '8'); base.setAttribute('height', '8');
    base.setAttribute('fill', colorFor(owner));
    const stripe = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    stripe.setAttribute('width', '4'); stripe.setAttribute('height', '8');
    stripe.setAttribute('fill', uiColorFor(occupier));
    stripe.setAttribute('fill-opacity', '0.65');
    pat.appendChild(base); pat.appendChild(stripe);
    defs.appendChild(pat);
    return id;
  }

  // Unit stack: icons 3 per row, 60% overlap
  function renderUnitStack(svg, cx, cy, units, scale) {
    // Each unit entry: {country_id, unit_type, count}
    // Hybrid rendering:
    //  - If total units on hex ≤ 5: show individual icons (one per unit)
    //  - If total units on hex ≥ 6: compact batch — one icon per (country,type)
    //  - Count badge appears only when a (country,type) group has 3+ units
    //  - Units are grouped into country clusters (not mixed across countries)
    if (!units || units.length === 0) return;
    const totalCount = units.reduce((s, u) => s + u.count, 0);
    const batched = totalCount >= 6;
    // Group by country: sort so same-country units stay adjacent
    const sorted = [...units].sort((a, b) => {
      if (a.country_id !== b.country_id) return a.country_id < b.country_id ? -1 : 1;
      return a.unit_type < b.unit_type ? -1 : a.unit_type > b.unit_type ? 1 : 0;
    });
    let show;
    if (batched) {
      show = sorted;
    } else {
      show = [];
      sorted.forEach(u => {
        for (let i = 0; i < u.count; i++) show.push({ ...u, count: 1 });
      });
    }

    const perRow = 3;
    const base = scale === 'global' ? 14 : 16;
    const sizeByType = {
      naval: base + 7, ground: base, tactical_air: base - 2,
      air_defense: base, strategic_missile: base,
    };
    // Spacing widens with crowd: 3+ units get more breathing room
    const spacing = show.length >= 3 ? 0.95 : 0.75;
    const jitterAmt = show.length >= 3 ? 0.38 : 0.22;

    // Find widest in each row for centering
    const rowCount = Math.ceil(show.length / perRow);
    const rowHeight = base * spacing * 1.5;
    const startY = cy - (rowCount - 1) * rowHeight / 2;

    // Deterministic jitter based on index — spreads icons naturally across hex
    const jitter = (idx, amt) => {
      const s = Math.sin(idx * 12.9898 + idx * 78.233) * 43758.5453;
      return ((s - Math.floor(s)) - 0.5) * 2 * amt;
    };

    for (let i = 0; i < show.length; i++) {
      const u = show[i];
      const rowIdx = Math.floor(i / perRow);
      const colIdx = i % perRow;
      const rowLen = Math.min(perRow, show.length - rowIdx * perRow);
      const size = sizeByType[u.unit_type] || base;
      const step = size * spacing;
      const jx = jitter(i * 2 + 1, size * jitterAmt);
      const jy = jitter(i * 2 + 7, size * jitterAmt * 0.82);
      const x = cx + (colIdx - (rowLen - 1) / 2) * step + jx;
      const y = startY + rowIdx * rowHeight + jy;

      const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
      const iconId = unitIconId(u.unit_type, u.country_id);
      use.setAttribute('href', '#' + iconId);
      use.setAttribute('x', x - size / 2);
      use.setAttribute('y', y - size / 2);
      use.setAttribute('width', size);
      use.setAttribute('height', size);
      use.setAttribute('style', `color:${uiColorFor(u.country_id)}`);
      use.style.pointerEvents = 'none';
      svg.appendChild(use);

      // Count badge only when 3+ units of this (country,type) in this area
      if (u.count >= 3) {
        const badge = addText(svg, x + size * 0.5, y + size * 0.5,
          String(u.count), 'unit-count-badge');
        badge.style.fill = uiColorFor(u.country_id);
      }
    }
  }

  function unitIconId(unit_type, country_id) {
    if (unit_type === 'ground') {
      // Sarmatia faces left on theater maps per style guide — approximate: Sarmatia uses left, others right.
      // For simplicity, use right everywhere except Sarmatia on theater.
      if (country_id === 'sarmatia' && state.view !== 'global') return 'unit-ground-left';
      return 'unit-ground-right';
    }
    if (unit_type === 'naval') return 'unit-naval';
    if (unit_type === 'tactical_air') return 'unit-tactical-air';
    if (unit_type === 'air_defense') return 'unit-air-defense';
    if (unit_type === 'strategic_missile') return 'unit-strategic-missile';
    return 'unit-ground-right';
  }

  // ---------- Aggregations ----------
  // Build {row,col (1-indexed): theaterName} for global theater-link hexes.
  // Derived from the canonical mapping (globalHexForTheaterCell) to guarantee
  // that badges/drilldown match placement routing.
  function buildGlobalTheaterLinks() {
    const links = {};
    window.MAP_CONFIG.THEATER_NAMES.forEach(theater => {
      const t = state.theaters && state.theaters[theater];
      if (!t || !t.grid) return;
      for (let ri = 0; ri < t.rows; ri++) {
        for (let ci = 0; ci < t.cols; ci++) {
          const g = globalHexForTheaterCell(theater, ri + 1, ci + 1);
          if (g) links[`${g[0]},${g[1]}`] = theater;
        }
      }
    });
    return links;
  }

  // Return the active list of units (editable copy in edit mode, raw otherwise).
  function currentUnits() {
    if (state.editMode && state.editableUnits) return state.editableUnits;
    return (state.units && state.units.units) || [];
  }

  // Aggregate active units onto theater cells by (theater_row, theater_col).
  function aggregateTheaterUnits(theaterName) {
    const out = {};
    for (const u of currentUnits()) {
      if (u.status !== 'active') continue;
      if (u.theater !== theaterName) continue;
      if (u.theater_row == null || u.theater_col == null) continue;
      const key = `${u.theater_row},${u.theater_col}`;
      out[key] = out[key] || [];
      const existing = out[key].find(x => x.country_id === u.country_id && x.unit_type === u.unit_type);
      if (existing) existing.count += 1;
      else out[key].push({ country_id: u.country_id, unit_type: u.unit_type, count: 1 });
    }
    return out;
  }

  // Aggregate active units onto the global map by (global_row, global_col).
  function aggregateGlobalUnits() {
    const out = {};
    for (const u of currentUnits()) {
      if (u.status !== 'active') continue;
      if (u.global_row == null || u.global_col == null) continue;
      const key = `${u.global_row},${u.global_col}`;
      out[key] = out[key] || [];
      const existing = out[key].find(x => x.country_id === u.country_id && x.unit_type === u.unit_type);
      if (existing) existing.count += 1;
      else out[key].push({ country_id: u.country_id, unit_type: u.unit_type, count: 1 });
    }
    return out;
  }

  /**
   * Load persisted hex occupation from DB (hex_control table).
   * Sets occupied_by on grid cells from authoritative DB state.
   */
  async function loadHexControl() {
    if (!SIM_RUN_ID_PARAM) return;
    try {
      const resp = await fetch(`/api/sim/${SIM_RUN_ID_PARAM}/map/hex-control`);
      if (!resp.ok) return;
      const data = await resp.json();
      (data.hexes || []).forEach(h => {
        // Apply to global grid
        if (state.global && state.global.grid) {
          const rIdx = h.global_row - 1, cIdx = h.global_col - 1;
          if (state.global.grid[rIdx] && state.global.grid[rIdx][cIdx]) {
            state.global.grid[rIdx][cIdx].occupied_by = h.controlled_by;
          }
        }
        // Apply to theater grid
        if (h.theater && h.theater_row && state.theaters[h.theater] && state.theaters[h.theater].grid) {
          const trIdx = h.theater_row - 1, tcIdx = h.theater_col - 1;
          if (state.theaters[h.theater].grid[trIdx] && state.theaters[h.theater].grid[trIdx][tcIdx]) {
            state.theaters[h.theater].grid[trIdx][tcIdx].occupied_by = h.controlled_by;
          }
        }
      });
    } catch (e) { console.debug('hex-control load failed:', e); }
  }

  /**
   * Derive occupied_by on hex grid from unit positions.
   * A hex is "occupied" when a country has active ground units on a hex
   * whose owner is a different country (and not 'sea').
   * Updates grid cells in-place for both global and theater views.
   */
  function deriveOccupation() {
    const units = currentUnits();
    if (!units || !units.length) return;

    // Build occupier map: hex → strongest foreign ground presence
    function applyToGrid(gridData, getCoords) {
      if (!gridData || !gridData.grid) return;
      // Clear previous occupation
      for (const row of gridData.grid) {
        for (const cell of row) {
          if (cell) cell.occupied_by = null;
        }
      }
      // Group ground units by hex
      const groundByHex = {};
      for (const u of units) {
        if (u.status !== 'active' || u.unit_type !== 'ground') continue;
        const coords = getCoords(u);
        if (!coords) continue;
        const key = `${coords[0]},${coords[1]}`;
        groundByHex[key] = groundByHex[key] || {};
        groundByHex[key][u.country_id] = (groundByHex[key][u.country_id] || 0) + 1;
      }
      // Mark occupation
      for (const [key, countries] of Object.entries(groundByHex)) {
        const [r, c] = key.split(',').map(Number);
        const rIdx = r - 1, cIdx = c - 1;
        if (!gridData.grid[rIdx] || !gridData.grid[rIdx][cIdx]) continue;
        const cell = gridData.grid[rIdx][cIdx];
        if (cell.owner === 'sea') continue;
        // Find strongest foreign country on this hex
        let occupier = null, maxCount = 0;
        for (const [cc, count] of Object.entries(countries)) {
          if (cc !== cell.owner && count > maxCount) {
            occupier = cc;
            maxCount = count;
          }
        }
        if (occupier) cell.occupied_by = occupier;
      }
    }

    // Apply to global grid
    applyToGrid(state.global, u => (u.global_row != null ? [u.global_row, u.global_col] : null));

    // Apply to theater grids
    for (const tName of ['eastern_ereb', 'mashriq']) {
      if (state.theaters[tName]) {
        applyToGrid(state.theaters[tName], u => (
          u.theater === tName && u.theater_row != null ? [u.theater_row, u.theater_col] : null
        ));
      }
    }
  }

  // ---------- Interaction / Inspector ----------
  function selectHex(rIdx, cIdx) {
    // Attack mode: send hex click to parent via postMessage
    if (ATTACK_MODE) {
      handleAttackHexClick(rIdx, cIdx);
      return;
    }
    // Edit-mode with armed unit: handle placement routing instead of inspector.
    if (state.editMode && state.armedUnitId) {
      handleArmedHexClick(rIdx, cIdx);
      return;
    }
    // Edit-mode, nothing armed: show per-unit popover for this hex
    if (state.editMode) {
      showHexUnitPopover(rIdx, cIdx);
      return;
    }
    // View mode: second click on same theater-link hex auto-opens the theater
    if (state.view === 'global') {
      const r1 = rIdx + 1, c1 = cIdx + 1;
      const tLink = theaterLinkForGlobalHex(r1, c1);
      if (tLink) {
        const key = `${r1},${c1}`;
        if (state.lastClickedHex === key) {
          state.lastClickedHex = null;
          renderView(tLink);
          return;
        }
        state.lastClickedHex = key;
      } else {
        state.lastClickedHex = null;
      }
    } else {
      state.lastClickedHex = null;
    }
    // Clear prior
    document.querySelectorAll('.hex.selected').forEach(el => el.classList.remove('selected'));
    const poly = document.querySelector(
      `#mapSvg polygon[data-row="${rIdx}"][data-col="${cIdx}"]`
    );
    if (poly) poly.classList.add('selected');
    state.selected = { row: rIdx, col: cIdx };

    const data = state.view === 'global' ? state.global : state.theaters[state.view];
    const hex = data.grid[rIdx][cIdx];
    populateInspector(rIdx, cIdx, hex);
  }

  function populateInspector(rIdx, cIdx, hex) {
    const empty = document.getElementById('inspectorEmpty');
    const content = document.getElementById('inspectorContent');
    empty.style.display = 'none';
    content.style.display = 'block';

    const r1 = rIdx + 1, c1 = cIdx + 1;
    const key1 = `${r1},${c1}`;
    const isGlobal = state.view === 'global';
    const ownerCol = uiColorFor(hex.owner);
    const ownerName = countryName(hex.owner);

    // Zone/hex label
    let displayName = hex.owner === 'sea' ? 'Open Waters' : ownerName + ' Territory';
    let zoneIdLabel = isGlobal ? `global / ${key1}` : `${state.view} / ${key1}`;

    // Chokepoint check
    let chokepointInfo = null;
    if (isGlobal && state.global.chokepoints) {
      Object.values(state.global.chokepoints).forEach(cp => {
        if (cp.row === rIdx && cp.col === cIdx) chokepointInfo = cp.name;
      });
    }
    if (chokepointInfo) displayName = chokepointInfo;

    // Theater link
    let theaterLink = null;
    if (isGlobal) {
      const links = buildGlobalTheaterLinks();
      if (links[key1]) theaterLink = links[key1];
    }

    // Units on this hex
    let units = [];
    if (isGlobal) {
      units = (aggregateGlobalUnits()[key1]) || [];
    } else {
      units = (aggregateTheaterUnits(state.view)[key1]) || [];
    }

    // Adjacencies (simple cube/offset neighbors on odd-r offset grid)
    const adj = getAdjacencies(rIdx, cIdx);
    const gridData = state.view === 'global' ? state.global : state.theaters[state.view];
    const adjacentInfo = adj.filter(n =>
      n.row >= 0 && n.row < gridData.rows && n.col >= 0 && n.col < gridData.cols
    ).map(n => {
      const nh = gridData.grid[n.row][n.col];
      return {
        coord: `${n.row + 1},${n.col + 1}`,
        owner: nh.owner,
        ownerName: countryName(nh.owner),
      };
    });

    // Build HTML
    let html = '';
    html += `<div class="ins-zone-id">${escapeHtml(zoneIdLabel)}</div>`;
    html += `<div class="ins-name">${escapeHtml(displayName)}</div>`;
    html += `<div class="ins-owner-badge">
      <span class="swatch" style="background:${ownerCol}"></span>
      <span>${escapeHtml(ownerName || 'Unowned')}</span>
    </div>`;

    html += `<div class="ins-section">
      <div class="ins-meta-row"><span class="k">Coordinates</span><span class="v">${key1}</span></div>
      <div class="ins-meta-row"><span class="k">Owner</span><span class="v">${escapeHtml(hex.owner)}</span></div>
      ${hex.occupied_by ? `<div class="ins-meta-row"><span class="k">Occupied by</span><span class="v">${escapeHtml(hex.occupied_by)}</span></div>` : ''}
      ${hex.global_link ? `<div class="ins-meta-row"><span class="k">Global link</span><span class="v">${escapeHtml(hex.global_link)}</span></div>` : ''}
      ${chokepointInfo ? `<div class="ins-meta-row"><span class="k">Chokepoint</span><span class="v">yes</span></div>` : ''}
    </div>`;

    if (theaterLink) {
      html += `<div class="ins-section">
        <div class="ins-theater-note">⊕ Has detailed theater map</div>
        <button class="ins-theater-cta" data-theater="${theaterLink}">Open ${THEATER_LABELS[theaterLink]} →</button>
      </div>`;
    }

    if (units.length > 0) {
      html += `<div class="ins-section"><h4>Units</h4><table class="ins-units-table">`;
      // Sort: naval, ground, tactical_air, air_defense, strategic_missile
      const order = ['naval', 'ground', 'tactical_air', 'air_defense', 'strategic_missile'];
      units.sort((a, b) =>
        (order.indexOf(a.unit_type) - order.indexOf(b.unit_type)) ||
        a.country_id.localeCompare(b.country_id)
      );
      for (const u of units) {
        const iconId = unitIconId(u.unit_type, u.country_id);
        const col = uiColorFor(u.country_id);
        html += `<tr>
          <td class="ico"><svg viewBox="0 0 24 24" style="color:${col}"><use href="#${iconId}"/></svg></td>
          <td class="utype">${escapeHtml(u.unit_type.replace('_', ' '))}</td>
          <td class="country">${escapeHtml(countryName(u.country_id))}</td>
          <td class="cnt">${u.count}</td>
        </tr>`;
      }
      html += `</table></div>`;
    } else {
      html += `<div class="ins-section"><h4>Units</h4><div class="ins-empty-note">No deployed units on this hex.</div></div>`;
    }

    if (adjacentInfo.length > 0) {
      html += `<div class="ins-section"><h4>Adjacent Hexes</h4>`;
      adjacentInfo.forEach(a => {
        html += `<div class="ins-meta-row"><span class="k">${a.coord}</span><span class="v">${escapeHtml(a.ownerName)}</span></div>`;
      });
      html += `</div>`;
    }

    content.innerHTML = html;

    // Wire up theater CTA
    const cta = content.querySelector('.ins-theater-cta');
    if (cta) {
      cta.addEventListener('click', (e) => {
        const theater = e.currentTarget.dataset.theater;
        renderView(theater);
      });
    }
  }

  function getAdjacencies(rIdx, cIdx) {
    // Odd-r offset neighbors (pointy-top)
    const odd = rIdx % 2 === 1;
    const deltas = odd
      ? [[-1, 0], [-1, 1], [0, -1], [0, 1], [1, 0], [1, 1]]
      : [[-1, -1], [-1, 0], [0, -1], [0, 1], [1, -1], [1, 0]];
    return deltas.map(([dr, dc]) => ({ row: rIdx + dr, col: cIdx + dc }));
  }

  function clearInspector() {
    document.getElementById('inspectorEmpty').style.display = 'block';
    document.getElementById('inspectorContent').style.display = 'none';
    document.getElementById('inspectorContent').innerHTML = '';
  }

  function escapeHtml(s) {
    if (s == null) return '';
    const div = document.createElement('div');
    div.textContent = String(s);
    return div.innerHTML;
  }

  // ---------- Country legend ----------
  function buildCountryLegend() {
    const el = document.getElementById('countryLegend');
    const pal = state.countries.palette;
    const ids = Object.keys(pal).filter(k => k !== 'sea').sort();
    el.innerHTML = '';
    ids.forEach(cid => {
      const row = document.createElement('div');
      row.className = 'country-row';
      row.innerHTML = `<span class="swatch" style="background:${pal[cid].map}"></span><span class="cname">${escapeHtml(countryName(cid))}</span>`;
      el.appendChild(row);
    });
  }

  // ============================================================
  // EDIT MODE
  // ============================================================

  const UNIT_TYPES = window.MAP_CONFIG.UNIT_TYPES;

  // Theater cell -> parent global hex. Delegates to central MAP_CONFIG.
  // Looks up cell owner from theater state JSON, then calls the canonical
  // mapping in window.MAP_CONFIG.globalHexForTheaterCell.
  function globalHexForTheaterCell(theater, trow, tcol) {
    const tData = state.theaters && state.theaters[theater];
    let owner = null;
    if (tData && tData.grid && tData.grid[trow - 1] && tData.grid[trow - 1][tcol - 1]) {
      owner = tData.grid[trow - 1][tcol - 1].owner;
    }
    return window.MAP_CONFIG.globalHexForTheaterCell(theater, trow, tcol, owner);
  }

  // Theater-link global hex keys (1-indexed "row,col") -> theater name
  function theaterLinkForGlobalHex(row1, col1) {
    const links = buildGlobalTheaterLinks();
    return links[`${row1},${col1}`] || null;
  }

  function toggleEditMode() {
    state.editMode = !state.editMode;
    const btn = document.getElementById('editBtn');
    const panel = document.getElementById('editPanel');
    const inspector = document.getElementById('inspector');
    if (state.editMode) {
      btn.classList.add('active');
      btn.innerHTML = '&#10004; Exit Edit';
      panel.style.display = 'flex';
      inspector.style.display = 'none';
      if (!state.editableUnits) {
        state.editableUnits = ((state.units && state.units.units) || [])
          .map(u => Object.assign({}, u));
      }
      // Default country selection
      if (!state.editCountry) {
        const countries = listEditableCountries();
        state.editCountry = countries[0] || null;
      }
      renderEditPanel();
      refreshLayoutList();
      updateCurrentLayoutLabel();
      updateUndoButtons();
      // Re-render current view to reflect editableUnits source
      renderView(state.view);
    } else {
      // offer to save if dirty
      if (state.editDirty) {
        const ok = confirm('Unsaved changes — save now?');
        if (ok) { saveLayout(false); }
      }
      btn.classList.remove('active');
      btn.innerHTML = '&#9998; Edit Layout';
      panel.style.display = 'none';
      inspector.style.display = 'block';
      disarmUnit(true);
      renderView(state.view);
    }
  }

  function listEditableCountries() {
    const set = new Set();
    (state.editableUnits || []).forEach(u => { if (u.country_id) set.add(u.country_id); });
    return Array.from(set).sort();
  }

  function renderEditPanel() {
    renderCountryGrid();
    renderLedger();
    renderUnitList();
    renderReservesOverview();
    updateStatusLine();
    updateCurrentLayoutLabel();
    updateUndoButtons();
  }

  function renderCountryGrid() {
    const el = document.getElementById('editCountryGrid');
    const countries = listEditableCountries();
    el.innerHTML = '';
    countries.forEach(cid => {
      const b = document.createElement('button');
      // Count this country's units
      let placed = 0, total = 0;
      (state.editableUnits || []).forEach(u => {
        if (u.country_id !== cid || u.status === 'destroyed') return;
        total += 1;
        if (u.embarked_on || (u.global_row != null && u.global_col != null)) placed += 1;
      });
      let cls = 'edit-country-btn';
      if (cid === state.editCountry) cls += ' active';
      if (total > 0 && placed === total) cls += ' complete';
      b.className = cls;
      b.innerHTML = `<span class="swatch" style="background:${uiColorFor(cid)}"></span>` +
        `<span>${escapeHtml(countryName(cid))}</span>` +
        `<span class="cnt">${placed}/${total}</span>`;
      b.addEventListener('click', () => {
        state.editCountry = cid;
        state.editUnitType = null;
        renderEditPanel();
      });
      el.appendChild(b);
    });
  }

  function countCountryUnits(country) {
    const counts = {};
    UNIT_TYPES.forEach(t => counts[t] = { placed: 0, reserve: 0, embarked: 0, total: 0 });
    (state.editableUnits || []).forEach(u => {
      if (u.country_id !== country) return;
      const t = u.unit_type;
      if (!counts[t]) counts[t] = { placed: 0, reserve: 0, embarked: 0, total: 0 };
      counts[t].total += 1;
      if (u.embarked_on) counts[t].embarked += 1;
      else if (u.global_row != null && u.global_col != null) counts[t].placed += 1;
      else counts[t].reserve += 1;
    });
    return counts;
  }

  function renderLedger() {
    const el = document.getElementById('editLedger');
    if (!state.editCountry) { el.innerHTML = ''; return; }
    const counts = countCountryUnits(state.editCountry);
    el.innerHTML = '';
    UNIT_TYPES.forEach(t => {
      const c = counts[t];
      const row = document.createElement('div');
      let cls = 'edit-ledger-row' + (t === state.editUnitType ? ' active' : '');
      if (c.total === 0) cls += ' empty';
      row.className = cls;
      const placedAll = c.placed + c.embarked;
      row.innerHTML =
        `<span class="ltype">${escapeHtml(t.replace('_', ' '))}</span>` +
        `<span class="lcounts">${placedAll}/${c.reserve}/${c.total}</span>`;
      row.title = c.total === 0
        ? `No ${t.replace('_', ' ')} units — click to add`
        : `${placedAll} placed / ${c.reserve} reserve / ${c.total} total`;
      row.addEventListener('click', () => {
        state.editUnitType = (state.editUnitType === t) ? null : t;
        renderUnitList();
        renderLedger();
      });
      el.appendChild(row);
    });
  }

  function renderUnitList() {
    const el = document.getElementById('editUnitList');
    el.innerHTML = '';
    if (!state.editCountry || !state.editUnitType) return;
    const units = (state.editableUnits || []).filter(
      u => u.country_id === state.editCountry && u.unit_type === state.editUnitType
    );
    units.forEach(u => {
      const row = document.createElement('div');
      let cls = 'edit-unit-row';
      let label = '';
      if (u.embarked_on) {
        cls += ' embarked';
        label = `\u2693 ${u.unit_id} on ${u.embarked_on}`;
      } else if (u.global_row != null && u.global_col != null) {
        cls += ' placed';
        const loc = u.theater
          ? `${u.theater} ${u.theater_row},${u.theater_col}`
          : `${u.global_row},${u.global_col}`;
        label = `\ud83d\udccd ${u.unit_id} @ ${loc}`;
      } else {
        cls += ' reserve';
        label = `\u23f8 ${u.unit_id} \u2014 in reserve`;
      }
      if (u.unit_id === state.armedUnitId) cls += ' armed';
      row.className = cls;
      // Label span + delete button
      const lbl = document.createElement('span');
      lbl.className = 'unit-label';
      lbl.textContent = label;
      lbl.title = label;
      row.appendChild(lbl);
      const del = document.createElement('span');
      del.className = 'unit-del';
      del.textContent = '\u00d7';
      del.title = 'Delete unit';
      del.addEventListener('click', (ev) => {
        ev.stopPropagation();
        deleteUnit(u.unit_id);
      });
      row.appendChild(del);
      row.addEventListener('click', () => {
        if (u.unit_id === state.armedUnitId) {
          disarmUnit();
        } else if ((u.global_row != null && u.global_col != null) || u.embarked_on) {
          pickUpUnit(u.unit_id);
        } else {
          armUnit(u.unit_id);
        }
      });
      el.appendChild(row);
    });
    // "+ Add unit" row at bottom
    const addRow = document.createElement('div');
    addRow.className = 'edit-unit-row add-unit';
    addRow.textContent = `+ Add ${state.editUnitType.replace('_', ' ')} unit to reserve`;
    addRow.title = 'Create a new unit of this type for this country';
    addRow.addEventListener('click', () => addNewUnit(state.editCountry, state.editUnitType));
    el.appendChild(addRow);
  }

  // Country 3-letter abbreviations (matches existing unit_id convention)
  const COUNTRY_ABBREV = {
    columbia: 'col', cathay: 'cat', sarmatia: 'sar', ruthenia: 'rut',
    persia: 'per', gallia: 'gal', teutonia: 'teu', freeland: 'fre',
    ponte: 'pon', albion: 'alb', bharata: 'bha', levantia: 'lev',
    formosa: 'for', phrygia: 'phr', yamato: 'yam', solaria: 'sol',
    choson: 'cho', hanguk: 'han', caribe: 'car', mirage: 'mir',
  };
  const TYPE_ABBREV = {
    ground: 'g', tactical_air: 'a', strategic_missile: 'm',
    air_defense: 'd', naval: 'n',
  };

  function nextUnitId(country, type) {
    const c = COUNTRY_ABBREV[country] || country.slice(0, 3);
    const t = TYPE_ABBREV[type] || type[0];
    const prefix = `${c}_${t}_`;
    // Find max numeric suffix (skip reserve suffixes like r1, r2)
    let max = 0;
    (state.editableUnits || []).forEach(u => {
      if (!u.unit_id || !u.unit_id.startsWith(prefix)) return;
      const tail = u.unit_id.slice(prefix.length);
      const n = parseInt(tail, 10);
      if (!isNaN(n) && n > max) max = n;
    });
    const seq = String(max + 1).padStart(2, '0');
    return `${prefix}${seq}`;
  }

  function addNewUnit(country, type) {
    snapshotEdit();
    const id = nextUnitId(country, type);
    const unit = {
      unit_id: id,
      country_id: country,
      unit_type: type,
      global_row: null, global_col: null,
      theater: '', theater_row: null, theater_col: null,
      embarked_on: '',
      status: 'reserve',
      notes: '',
    };
    state.editableUnits.push(unit);
    state.editDirty = true;
    renderEditPanel();
    renderView(state.view);
    showToast(`Added ${id} to ${countryName(country)} reserve`, false);
  }

  function deleteUnit(unitId) {
    const u = findUnit(unitId);
    if (!u) return;
    const ok = confirm(`Delete unit ${unitId} permanently?`);
    if (!ok) return;
    snapshotEdit();
    // If the armed unit is being deleted, disarm
    if (state.armedUnitId === unitId) disarmUnit(true);
    // If any unit is embarked on this one, un-embark them to reserve
    (state.editableUnits || []).forEach(other => {
      if (other.embarked_on === unitId) {
        clearUnitCoords(other);
        other.status = 'reserve';
      }
    });
    state.editableUnits = (state.editableUnits || []).filter(x => x.unit_id !== unitId);
    state.editDirty = true;
    renderEditPanel();
    renderView(state.view);
    showToast(`Deleted ${unitId}`, false);
  }

  function armUnit(unitId) {
    state.armedUnitId = unitId;
    document.getElementById('mapSvg').classList.add('armed');
    renderUnitList();
    updateStatusLine();
  }

  function disarmUnit(silent) {
    state.armedUnitId = null;
    document.getElementById('mapSvg').classList.remove('armed');
    if (!silent) {
      renderUnitList();
      updateStatusLine();
    }
  }

  function pickUpUnit(unitId) {
    const u = findUnit(unitId);
    if (!u) return;
    snapshotEdit();
    clearUnitCoords(u);
    if (u.status !== 'destroyed') u.status = 'reserve';
    state.editDirty = true;
    armUnit(unitId);
    renderView(state.view);
    renderLedger();
    renderUnitList();
    renderReservesOverview();
  }

  function findUnit(unitId) {
    return (state.editableUnits || []).find(u => u.unit_id === unitId);
  }

  // Clear all coordinate/embark fields on a unit (sets reserve-like state).
  function clearUnitCoords(u) {
    u.global_row = null;
    u.global_col = null;
    u.theater = '';
    u.theater_row = null;
    u.theater_col = null;
    u.embarked_on = '';
  }

  function updateStatusLine() {
    const el = document.getElementById('editStatus');
    if (!state.armedUnitId) {
      el.className = 'edit-status';
      el.textContent = 'No unit selected';
      return;
    }
    el.className = 'edit-status armed';
    el.textContent = `Click any hex to place ${state.armedUnitId}`;
  }

  // Handle hex click while a unit is armed
  // ---------- Hex unit picker popover (edit mode, nothing armed) ----------
  function showHexUnitPopover(rIdx, cIdx) {
    closeHexPopover();
    const r1 = rIdx + 1, c1 = cIdx + 1;
    // Collect individual units on this hex (not aggregated)
    const list = currentUnits();
    let units;
    if (state.view === 'global') {
      units = list.filter(u =>
        u.status === 'active' &&
        u.global_row === r1 && u.global_col === c1 && !u.theater
      );
    } else {
      units = list.filter(u =>
        u.status === 'active' &&
        u.theater === state.view &&
        u.theater_row === r1 && u.theater_col === c1
      );
    }
    // Also include ships and their embarked units (if any ship on this hex)
    const shipsHere = list.filter(u =>
      u.unit_type === 'naval' && u.status === 'active' &&
      ((state.view === 'global' && u.global_row === r1 && u.global_col === c1 && !u.theater) ||
       (state.view !== 'global' && u.theater === state.view && u.theater_row === r1 && u.theater_col === c1))
    );
    const embarked = [];
    shipsHere.forEach(ship => {
      list.forEach(u => {
        if (u.embarked_on === ship.unit_id) embarked.push(u);
      });
    });
    const all = units.concat(embarked.filter(u => !units.includes(u)));
    if (all.length === 0) {
      // Nothing here — flash hex briefly
      return;
    }
    // Build popover DOM
    const pop = document.createElement('div');
    pop.id = 'hexPopover';
    pop.className = 'hex-popover';
    pop.innerHTML = `<div class="hex-popover-head">Hex ${r1},${c1} — ${all.length} unit${all.length === 1 ? '' : 's'}</div>`;
    const list_el = document.createElement('div');
    list_el.className = 'hex-popover-list';
    all.forEach(u => {
      const row = document.createElement('div');
      row.className = 'hex-popover-row';
      const dotColor = uiColorFor(u.country_id);
      const embarkedOn = u.embarked_on ? ` ⚓${u.embarked_on}` : '';
      row.innerHTML = `<span class="dot" style="background:${dotColor}"></span>` +
        `<span class="uid">${escapeHtml(u.unit_id)}</span>` +
        `<span class="meta">${escapeHtml(u.unit_type.replace('_', ' '))} · ${escapeHtml(countryName(u.country_id))}${embarkedOn}</span>`;
      row.addEventListener('click', () => {
        // Switch edit panel to this unit's country/type and arm it for relocation
        state.editCountry = u.country_id;
        state.editUnitType = u.unit_type;
        renderEditPanel();
        pickUpUnit(u.unit_id);
        closeHexPopover();
      });
      list_el.appendChild(row);
    });
    pop.appendChild(list_el);
    // Position popover near the clicked hex center
    const hexR = state.view === 'global' ? HEX_R_GLOBAL : HEX_R_THEATER;
    const ctr = hexCenter(rIdx, cIdx, hexR);
    const svg = document.getElementById('mapSvg');
    const svgRect = svg.getBoundingClientRect();
    const vb = svg.viewBox.baseVal;
    const scale = svgRect.width / vb.width;
    const screenX = svgRect.left + ctr.x * scale;
    const screenY = svgRect.top + ctr.y * scale;
    pop.style.left = (screenX + 16) + 'px';
    pop.style.top = (screenY - 8) + 'px';
    document.body.appendChild(pop);
    // Dismiss on outside click or ESC
    setTimeout(() => {
      document.addEventListener('click', _outsidePopoverClick, true);
    }, 0);
  }
  function _outsidePopoverClick(e) {
    const pop = document.getElementById('hexPopover');
    if (!pop) return;
    if (!pop.contains(e.target)) closeHexPopover();
  }
  function closeHexPopover() {
    const pop = document.getElementById('hexPopover');
    if (pop) pop.remove();
    document.removeEventListener('click', _outsidePopoverClick, true);
  }

  function handleArmedHexClick(rIdx, cIdx) {
    const armedId = state.armedUnitId;
    const unit = findUnit(armedId);
    if (!unit) { disarmUnit(); return; }

    const data = state.view === 'global' ? state.global : state.theaters[state.view];
    const hex = data.grid[rIdx][cIdx];
    const row1 = rIdx + 1, col1 = cIdx + 1;

    // Global view: check theater-link auto-drill
    if (state.view === 'global') {
      const tLink = theaterLinkForGlobalHex(row1, col1);
      if (tLink) {
        showWarning('info', `Entering ${THEATER_LABELS[tLink]} — pick a cell to place ${armedId}.`);
        renderView(tLink);
        return;
      }
      // Global-only placement (no theater coords).
      attemptPlace(unit, hex, {
        globalRow: row1, globalCol: col1,
        theater: '', theaterRow: null, theaterCol: null,
      });
      return;
    }

    // Theater view: resolve cell -> correct parent global hex.
    const link = globalHexForTheaterCell(state.view, row1, col1);
    const gRow = link ? link[0] : null;
    const gCol = link ? link[1] : null;
    attemptPlace(unit, hex, {
      globalRow: gRow, globalCol: gCol,
      theater: state.view, theaterRow: row1, theaterCol: col1,
    });
  }

  // Attempt to place the armed unit on a hex. Runs validation, places.
  function attemptPlace(unit, hex, target) {
    // target = { globalRow, globalCol, theater, theaterRow, theaterCol }
    // Check for ships on this hex for embarkation prompt
    const shipsHere = findShipsAtCell(target).filter(s => s.unit_id !== unit.unit_id);
    const ownShipHere = shipsHere.find(s => s.country_id === unit.country_id);
    const foreignShipHere = shipsHere.find(s => s.country_id !== unit.country_id);

    // For ground/air/missile/AD units and a ship is present, offer embark
    const landUnitTypes = ['ground', 'tactical_air', 'strategic_missile', 'air_defense'];
    if (landUnitTypes.includes(unit.unit_type) && ownShipHere) {
      const ok = confirm(`Embark ${unit.unit_id} on ${ownShipHere.unit_id}?`);
      if (ok) {
        embarkUnit(unit, ownShipHere);
        return;
      }
    } else if (landUnitTypes.includes(unit.unit_type) && foreignShipHere && hex.owner === 'sea') {
      const ok = confirm(`Embark on foreign ship ${foreignShipHere.unit_id} (${foreignShipHere.country_id})?`);
      if (ok) {
        showWarning('warn', `Foreign ship embark: ${unit.unit_id} on ${foreignShipHere.unit_id}`);
        embarkUnit(unit, foreignShipHere);
        return;
      }
    }

    // Hard blocks
    const isSea = hex.owner === 'sea';
    if (unit.unit_type === 'naval' && !isSea) {
      showWarning('block', `Cannot place naval on land hex.`);
      return;
    }
    if (landUnitTypes.includes(unit.unit_type) && isSea) {
      showWarning('block', `Cannot place ${unit.unit_type} on sea hex without own-country ship.`);
      return;
    }

    // Soft warnings
    if (!isSea && hex.owner && hex.owner !== unit.country_id) {
      // Unit placing on a hex its own country OCCUPIES is valid (no warning)
      if (hex.occupied_by === unit.country_id) {
        // occupied territory — legitimate placement, no warning
      } else {
        const unitCountry = state.countries.countries[unit.country_id];
        const atWar = (unitCountry && unitCountry.at_war_with) || [];
        if (atWar.includes(hex.owner)) {
          showWarning('enemy', `Placing on ENEMY territory: ${countryName(unit.country_id)} unit on ${countryName(hex.owner)}.`);
        } else {
          showWarning('warn', `${countryName(unit.country_id)} unit on ${countryName(hex.owner)} territory — basing rights?`);
        }
      }
    }

    placeUnit(unit, target);
  }

  function placeUnit(unit, target) {
    snapshotEdit();
    unit.global_row = target.globalRow;
    unit.global_col = target.globalCol;
    unit.theater = target.theater || '';
    unit.theater_row = target.theaterRow;
    unit.theater_col = target.theaterCol;
    unit.embarked_on = '';
    if (unit.status !== 'destroyed') unit.status = 'active';
    state.editDirty = true;
    disarmUnit(true);
    renderView(state.view);
    renderLedger();
    renderUnitList();
    renderReservesOverview();
    updateStatusLine();
  }

  function embarkUnit(unit, ship) {
    snapshotEdit();
    clearUnitCoords(unit);
    unit.embarked_on = ship.unit_id;
    unit.status = 'embarked';
    state.editDirty = true;
    disarmUnit(true);
    renderView(state.view);
    renderLedger();
    renderUnitList();
    renderReservesOverview();
    updateStatusLine();
  }

  // Find naval units at the same cell as a placement target.
  // On global view: match global_row/col. On theater view: match theater + theater_row/col.
  function findShipsAtCell(target) {
    const list = state.editableUnits || [];
    return list.filter(u => {
      if (u.unit_type !== 'naval' || u.status !== 'active') return false;
      if (target.theater) {
        return u.theater === target.theater
          && u.theater_row === target.theaterRow
          && u.theater_col === target.theaterCol;
      }
      return u.global_row === target.globalRow
        && u.global_col === target.globalCol;
    });
  }

  function resetCountryToReserve() {
    if (!state.editCountry) return;
    const ok = confirm(`Reset all ${countryName(state.editCountry)} units to reserve?`);
    if (!ok) return;
    snapshotEdit();
    (state.editableUnits || []).forEach(u => {
      if (u.country_id === state.editCountry) {
        clearUnitCoords(u);
        if (u.status !== 'destroyed') u.status = 'reserve';
      }
    });
    state.editDirty = true;
    disarmUnit(true);
    renderView(state.view);
    renderEditPanel();
  }

  function saveLayout(promptForName) {
    let name = state.currentLayoutName;
    if (promptForName || !name) {
      const input = prompt(
        name ? `Save as new layout (current: ${name}):` : 'Name this layout:',
        name || 'my_layout'
      );
      if (!input || !input.trim()) return;
      name = input.trim();
    }
    const payload = { name, units: state.editableUnits || [] };
    fetch('/api/map/units/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(r => r.json()).then(resp => {
      if (resp.success) {
        state.currentLayoutName = resp.name;
        state.editDirty = false;
        showToast(`Saved ${resp.count} units → ${resp.name}.csv`);
        refreshLayoutList();
        refreshViewLayoutList();
        updateCurrentLayoutLabel();
      } else {
        showToast(`Save failed: ${resp.error || 'unknown error'}`, true);
      }
    }).catch(err => {
      showToast(`Save failed: ${err.message}`, true);
    });
  }

  // Undo/redo stack
  const UNDO_LIMIT = 100;
  function snapshotEdit() {
    // Deep-clone current editable state, push to undo stack, clear redo stack
    if (!state.editableUnits) return;
    const snap = JSON.parse(JSON.stringify(state.editableUnits));
    state.undoStack = state.undoStack || [];
    state.redoStack = state.redoStack || [];
    state.undoStack.push(snap);
    if (state.undoStack.length > UNDO_LIMIT) state.undoStack.shift();
    state.redoStack.length = 0;
    updateUndoButtons();
  }
  function undoEdit() {
    if (!state.undoStack || state.undoStack.length === 0) return;
    const prev = state.undoStack.pop();
    state.redoStack = state.redoStack || [];
    state.redoStack.push(JSON.parse(JSON.stringify(state.editableUnits)));
    state.editableUnits = prev;
    state.editDirty = true;
    disarmUnit(true);
    renderView(state.view);
    renderEditPanel();
    updateCurrentLayoutLabel();
    updateUndoButtons();
  }
  function redoEdit() {
    if (!state.redoStack || state.redoStack.length === 0) return;
    const next = state.redoStack.pop();
    state.undoStack = state.undoStack || [];
    state.undoStack.push(JSON.parse(JSON.stringify(state.editableUnits)));
    state.editableUnits = next;
    state.editDirty = true;
    disarmUnit(true);
    renderView(state.view);
    renderEditPanel();
    updateCurrentLayoutLabel();
    updateUndoButtons();
  }
  function updateUndoButtons() {
    const u = document.getElementById('editUndoBtn');
    const r = document.getElementById('editRedoBtn');
    if (u) u.disabled = !(state.undoStack && state.undoStack.length > 0);
    if (r) r.disabled = !(state.redoStack && state.redoStack.length > 0);
  }

  function clearAllDeployments() {
    console.log('[clearAll] called. editableUnits length:', (state.editableUnits || []).length);
    const ok = confirm('Clear ALL deployments (all 20 countries)? All units return to reserve.');
    if (!ok) return;
    snapshotEdit();
    let cleared = 0;
    (state.editableUnits || []).forEach(u => {
      if (u.status === 'destroyed') return;
      clearUnitCoords(u);
      u.status = 'reserve';
      cleared++;
    });
    console.log('[clearAll] cleared units:', cleared);
    state.editDirty = true;
    disarmUnit(true);
    renderView(state.view);
    renderEditPanel();
    updateCurrentLayoutLabel();
    showToast('All deployments cleared — ready to place from scratch', false);
  }

  function refreshViewLayoutList() {
    const sel = document.getElementById('viewLayoutSelect');
    if (!sel) return;
    fetch('/api/map/layouts').then(r => r.json()).then(resp => {
      const layouts = resp.layouts || [];
      const current = sel.value;
      sel.innerHTML = '<option value="">— default (units.csv) —</option>';
      layouts.forEach(l => {
        const opt = document.createElement('option');
        opt.value = l.name;
        opt.textContent = `${l.name} (${l.count})`;
        sel.appendChild(opt);
      });
      if (current) sel.value = current;
    }).catch(() => {});
  }

  function viewLoadLayout() {
    const sel = document.getElementById('viewLayoutSelect');
    const name = sel.value;
    if (!name) {
      fetch('/api/map/units').then(r => r.json()).then(resp => {
        (resp.units || []).forEach(u => {
          if (u.theater && u.theater_row != null && u.theater_col != null &&
              (u.global_row == null || u.global_col == null)) {
            const g = globalHexForTheaterCell(u.theater, u.theater_row, u.theater_col);
            if (g) { u.global_row = g[0]; u.global_col = g[1]; }
          }
        });
        state.units = resp;
        renderView(state.view);
        setStatus('ok', `default units.csv · ${(resp.units || []).length} units`);
      });
      return;
    }
    fetch(`/api/map/layouts/load?name=${encodeURIComponent(name)}`).then(r => r.json()).then(resp => {
      if (resp.success) {
        resp.units.forEach(u => {
          if (u.theater && u.theater_row != null && u.theater_col != null &&
              (u.global_row == null || u.global_col == null)) {
            const g = globalHexForTheaterCell(u.theater, u.theater_row, u.theater_col);
            if (g) { u.global_row = g[0]; u.global_col = g[1]; }
          }
        });
        state.units = { units: resp.units, total: resp.count };
        renderView(state.view);
        setStatus('ok', `Layout: ${resp.name} · ${resp.count} units`);
      } else {
        setStatus('err', `Load failed: ${resp.error || 'unknown'}`);
      }
    });
  }

  function refreshLayoutList() {
    const sel = document.getElementById('editLoadSelect');
    if (!sel) return;
    fetch('/api/map/layouts').then(r => r.json()).then(resp => {
      const layouts = resp.layouts || [];
      sel.innerHTML = '<option value="">— select to load —</option>';
      layouts.forEach(l => {
        const opt = document.createElement('option');
        opt.value = l.name;
        opt.textContent = `${l.name} (${l.count} units)`;
        sel.appendChild(opt);
      });
    }).catch(() => {});
  }

  function loadLayout() {
    const sel = document.getElementById('editLoadSelect');
    if (!sel) return;
    const name = sel.value;
    if (!name) return;
    if (state.editDirty) {
      const ok = confirm('You have unsaved changes. Load anyway?');
      if (!ok) return;
    }
    fetch(`/api/map/layouts/load?name=${encodeURIComponent(name)}`).then(r => r.json()).then(resp => {
      if (resp.success) {
        // Only re-derive global coords for theater units when they are missing.
        // If layout has coords, trust them — preserves the saved state.
        resp.units.forEach(u => {
          if (u.theater && u.theater_row != null && u.theater_col != null &&
              (u.global_row == null || u.global_col == null)) {
            const g = globalHexForTheaterCell(u.theater, u.theater_row, u.theater_col);
            if (g) { u.global_row = g[0]; u.global_col = g[1]; }
          }
        });
        state.editableUnits = resp.units;
        state.currentLayoutName = resp.name;
        state.editDirty = false;
        disarmUnit(true);
        renderView(state.view);
        renderEditPanel();
        updateCurrentLayoutLabel();
        showToast(`Loaded ${resp.count} units from ${resp.name}.csv`);
      } else {
        showToast(`Load failed: ${resp.error || 'unknown'}`, true);
      }
    }).catch(err => showToast(`Load failed: ${err.message}`, true));
  }

  function updateCurrentLayoutLabel() {
    const el = document.getElementById('editCurrentLayout');
    if (!el) return;
    if (state.currentLayoutName) {
      el.textContent = `Current: ${state.currentLayoutName}`;
      el.classList.toggle('dirty', !!state.editDirty);
    } else {
      el.textContent = state.editDirty ? 'Unsaved (new)' : 'No layout loaded';
      el.classList.toggle('dirty', !!state.editDirty);
    }
  }

  // ---------- Warnings / Toast ----------
  function showWarning(kind, text) {
    const el = document.getElementById('editWarnings');
    el.style.display = 'flex';
    const w = document.createElement('div');
    w.className = 'edit-warning' + (kind === 'enemy' ? ' enemy' : '') + (kind === 'block' ? ' block' : '');
    const icon = kind === 'enemy' ? '\u26a0\ufe0f' : kind === 'block' ? '\u26d4' : kind === 'info' ? '\u2139\ufe0f' : '\u26a0\ufe0f';
    w.innerHTML = `<span>${icon}</span><span>${escapeHtml(text)}</span><span class="close">\u00d7</span>`;
    w.querySelector('.close').addEventListener('click', () => {
      w.remove();
      if (el.children.length === 0) el.style.display = 'none';
    });
    el.appendChild(w);
    // Auto-dismiss info/warn after 6s
    if (kind !== 'block' && kind !== 'enemy') {
      setTimeout(() => {
        w.remove();
        if (el.children.length === 0) el.style.display = 'none';
      }, 6000);
    }
  }

  function showToast(text, isErr) {
    const el = document.getElementById('editToast');
    el.textContent = text;
    el.className = 'edit-toast' + (isErr ? ' err' : '');
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 3500);
  }

  // ---------- Embark pictograms on ships ----------
  // For each ship with embarked units, render small unit icons of the embarked
  // units (not anchor badges), positioned close to the ship's hex.
  function renderEmbarkBadges(svg, viewName, hexR) {
    const list = currentUnits();
    // Group embarked units by carrier ship_id
    const embarkByShip = {};
    list.forEach(u => {
      if (u.embarked_on) {
        (embarkByShip[u.embarked_on] = embarkByShip[u.embarked_on] || []).push(u);
      }
    });
    // For each ship with embarks, find its hex and render mini icons
    const byHex = {}; // hexKey -> list of embarked units
    list.forEach(ship => {
      if (ship.unit_type !== 'naval' || ship.status !== 'active') return;
      const emb = embarkByShip[ship.unit_id];
      if (!emb || emb.length === 0) return;
      let cell = null;
      if (viewName === 'global') {
        if (ship.global_row != null && ship.global_col != null) cell = [ship.global_row, ship.global_col];
      } else {
        if (ship.theater === viewName && ship.theater_row != null && ship.theater_col != null) {
          cell = [ship.theater_row, ship.theater_col];
        }
      }
      if (!cell) return;
      const key = `${cell[0]},${cell[1]}`;
      (byHex[key] = byHex[key] || []).push(...emb);
    });
    // Render mini icons per hex — noticeably smaller than the ship icon
    const miniSize = Math.round(hexR * 0.26);
    Object.keys(byHex).forEach(key => {
      const [r1, c1] = key.split(',').map(Number);
      const center = hexCenter(r1 - 1, c1 - 1, hexR);
      // Position cluster tight against ship icon (ship renders near hex center)
      const baseX = center.x + hexR * 0.15;
      const baseY = center.y - hexR * 0.15;
      const units = byHex[key];
      units.forEach((u, i) => {
        const iconId = unitIconId(u.unit_type, u.country_id);
        const x = baseX + (i % 3) * (miniSize * 0.6);
        const y = baseY + Math.floor(i / 3) * (miniSize * 0.7);
        const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
        use.setAttribute('href', '#' + iconId);
        use.setAttribute('x', x - miniSize / 2);
        use.setAttribute('y', y - miniSize / 2);
        use.setAttribute('width', miniSize);
        use.setAttribute('height', miniSize);
        use.setAttribute('style', `color:${uiColorFor(u.country_id)}`);
        use.setAttribute('class', 'embark-mini');
        use.style.pointerEvents = 'none';
        svg.appendChild(use);
      });
    });
  }

  // ---------- Reserves overview on map ----------
  function renderReservesOverview() {
    let el = document.getElementById('reservesOverview');
    if (!state.editMode || !state.editCountry) {
      if (el) el.remove();
      return;
    }
    const stage = document.querySelector('.map-stage');
    if (!el) {
      el = document.createElement('div');
      el.id = 'reservesOverview';
      el.className = 'reserves-overview';
      stage.appendChild(el);
    }
    const counts = countCountryUnits(state.editCountry);
    const lines = [];
    lines.push(`<strong>${escapeHtml(countryName(state.editCountry))} reserves</strong>`);
    let total = 0;
    UNIT_TYPES.forEach(t => {
      const c = counts[t];
      if (c.reserve > 0) {
        lines.push(`${t.replace('_', ' ')}: ${c.reserve}`);
        total += c.reserve;
      }
    });
    if (total === 0) lines.push('<em style="color:var(--text-muted)">(all deployed)</em>');
    el.innerHTML = lines.join('<br>');
  }

  // ---------- Attack Mode (postMessage integration) ----------

  function handleAttackHexClick(rIdx, cIdx) {
    // Convert 0-indexed (renderer) to 1-indexed (engine)
    const row = rIdx + 1, col = cIdx + 1;

    // Get units at this hex — match by global coords (global view) or theater coords (theater view)
    const allUnits = currentUnits() || [];
    const isTheater = state.view !== 'global';
    const activeHere = allUnits.filter(u => {
      if (u.status !== 'active') return false;
      if (isTheater) return u.theater === state.view && u.theater_row === row && u.theater_col === col;
      return u.global_row === row && u.global_col === col;
    });
    // Find carrier unit_ids at this hex
    const carrierIds = new Set(activeHere.filter(u => u.unit_type === 'naval').map(u => u.unit_id));
    // Include embarked units whose carrier is at this hex
    const embarkedHere = carrierIds.size > 0
      ? allUnits.filter(u => u.status === 'embarked' && u.embarked_on && carrierIds.has(u.embarked_on))
      : [];
    const units = [...activeHere, ...embarkedHere];

    // Get hex owner from grid
    const data = state.view === 'global' ? state.global : state.theaters[state.view];
    const hex = data && data.grid && data.grid[rIdx] ? data.grid[rIdx][cIdx] : null;
    const owner = hex ? hex.owner : null;

    // For theater view: resolve global coords to send to parent (engine uses global)
    let globalRow = row, globalCol = col;
    if (isTheater && units.length > 0 && units[0].global_row != null) {
      globalRow = units[0].global_row;
      globalCol = units[0].global_col;
    } else if (isTheater) {
      // Try to resolve from theater linkage
      const g = globalHexForTheaterCell(state.view, row, col);
      if (g) { globalRow = g[0]; globalCol = g[1]; }
    }

    // Visual selection
    document.querySelectorAll('.hex.selected').forEach(el => el.classList.remove('selected'));
    const poly = document.querySelector(
      `#mapSvg polygon[data-row="${rIdx}"][data-col="${cIdx}"]`
    );
    if (poly) poly.classList.add('selected');
    state.selected = { row: rIdx, col: cIdx };

    // Send to parent — always global coordinates (engine uses global)
    // Also include theater info for highlighting in theater view
    window.parent.postMessage({
      type: 'hex-click',
      row: globalRow,
      col: globalCol,
      theater: isTheater ? state.view : null,
      theater_row: isTheater ? row : null,
      theater_col: isTheater ? col : null,
      owner: owner,
      view: state.view,
      units: units.map(u => ({
        unit_id: u.unit_id,
        country_id: u.country_id,
        unit_type: u.unit_type,
        status: u.status || 'active',
      })),
    }, '*');
  }

  /**
   * Highlight a set of hexes on the map (used by parent to show valid targets).
   * hexes: [{row, col}] — 1-indexed GLOBAL coordinates (engine convention).
   * style: 'target' (red glow) | 'source' (blue glow) | 'clear'
   * When in theater view, resolves global → theater coords via unit data.
   */
  function highlightHexes(hexes, style) {
    // Clear previous highlights
    document.querySelectorAll('polygon.hex.attack-target, polygon.hex.attack-source').forEach(el => {
      el.classList.remove('attack-target', 'attack-source');
    });

    if (style === 'clear' || !hexes || !hexes.length) return;

    const cls = style === 'source' ? 'attack-source' : 'attack-target';
    const isTheater = state.view !== 'global';

    hexes.forEach(h => {
      let rIdx, cIdx;
      if (isTheater) {
        // Use theater coords if provided by API, otherwise resolve via unit data
        if (h.theater === state.view && h.theater_row != null && h.theater_col != null) {
          rIdx = h.theater_row - 1;
          cIdx = h.theater_col - 1;
        } else {
          const allUnits = currentUnits() || [];
          const match = allUnits.find(u =>
            u.global_row === h.row && u.global_col === h.col &&
            u.theater === state.view && u.theater_row != null
          );
          if (match) {
            rIdx = match.theater_row - 1;
            cIdx = match.theater_col - 1;
          } else {
            return; // hex not in this theater
          }
        }
      } else {
        rIdx = h.row - 1;
        cIdx = h.col - 1;
      }
      const poly = document.querySelector(
        `#mapSvg polygon.hex[data-row="${rIdx}"][data-col="${cIdx}"]`
      );
      if (poly) poly.classList.add(cls);
    });
  }

  // Listen for messages from parent (React)
  window.addEventListener('message', (event) => {
    const msg = event.data;
    if (!msg || !msg.type) return;

    if (msg.type === 'highlight-hexes') {
      highlightHexes(msg.hexes, msg.style || 'target');
    }
    if (msg.type === 'clear-highlights') {
      highlightHexes(null, 'clear');
    }
    if (msg.type === 'navigate-theater') {
      renderView(msg.theater || 'global');
    }
    if (msg.type === 'refresh-units') {
      // Re-fetch units from API and re-render
      if (SIM_RUN_ID_PARAM) {
        fetchJson(`/api/sim/${SIM_RUN_ID_PARAM}/map/units`).then(un => {
          (un.units || []).forEach(u => {
            if (u.theater && u.theater_row != null && u.theater_col != null &&
                (u.global_row == null || u.global_col == null)) {
              const g = globalHexForTheaterCell(u.theater, u.theater_row, u.theater_col);
              if (g) { u.global_row = g[0]; u.global_col = g[1]; }
            }
          });
          state.units = un;
          loadHexControl().then(() => renderView(state.view));
        });
      }
    }
  });

  // Inject attack-mode CSS for hex highlights
  if (ATTACK_MODE) {
    const style = document.createElement('style');
    style.textContent = `
      polygon.hex.attack-target {
        stroke: #FF3C14 !important;
        stroke-width: 2.5 !important;
        filter: drop-shadow(0 0 6px rgba(255,60,20,0.6));
        cursor: crosshair !important;
      }
      polygon.hex.attack-source {
        stroke: #3B82F6 !important;
        stroke-width: 2.5 !important;
        filter: drop-shadow(0 0 6px rgba(59,130,246,0.6));
      }
      polygon.hex { cursor: pointer; }
    `;
    document.head.appendChild(style);
  }

})();
