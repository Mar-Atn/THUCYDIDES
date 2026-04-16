/* Geography Edit Mode — sidebar legend becomes interactive tool palette.
 * Paint ownership, toggle features, copy hexes, undo/redo, save to template.
 */
(function () {
  'use strict';

  const geo = {
    active: false,
    tool: null,           // 'sea' | 'chokepoint' | 'diehard' | 'nuclear' | 'copy' | country_id
    copySource: null,     // {row, col, owner, fill} for copy tool
    palette: {},          // cid -> {ui, map, light}
    dirty: false,
    undoStack: [],        // [{row, col, prev: {owner, fill, chokepoint, diehard, nuclear}}]
    redoStack: [],
  };

  // ---- Wait for map.js ----
  const waitForMap = setInterval(() => {
    const svg = document.getElementById('mapSvg');
    if (!svg || svg.childElementCount === 0) return;
    clearInterval(waitForMap);
    init();
  }, 300);

  async function init() {
    try {
      const resp = await fetch('/api/map/countries');
      const data = await resp.json();
      geo.palette = data.palette || {};
    } catch (e) {
      console.error('geo_edit: failed to load countries', e);
    }

    wireEditButton();
    wireHexClicks();
    wireLegendClicks();
    wireSave();
    wireKeyboard();
  }

  // ---- Color helper ----
  function mapColorFor(cid) {
    if (cid === 'sea') return getComputedStyle(document.documentElement).getPropertyValue('--sea').trim() || '#2a4a6a';
    const p = geo.palette[cid];
    if (p && p.map) return p.map;
    if (typeof p === 'string') return p;
    return '#888';
  }

  // ---- Edit Mode Toggle ----
  function wireEditButton() {
    const btn = document.getElementById('geoEditBtn');
    if (!btn) return;
    btn.addEventListener('click', toggleEdit);
  }

  function toggleEdit() {
    geo.active = !geo.active;
    geo.tool = null;
    geo.copySource = null;
    clearSelection();

    const btn = document.getElementById('geoEditBtn');
    const legend = document.getElementById('legend');
    const actions = document.getElementById('geoEditActions');
    const undoBar = document.getElementById('geoUndoBar');

    if (geo.active) {
      btn.textContent = '✕ Stop Editing';
      btn.style.color = '#D45B5B';
      legend.classList.add('geo-edit-active');
      if (actions) actions.style.display = 'block';
      showUndoBar(true);
    } else {
      btn.textContent = '✎ Edit Map';
      btn.style.color = '';
      legend.classList.remove('geo-edit-active');
      if (actions) actions.style.display = 'none';
      showUndoBar(false);
    }
  }

  function showUndoBar(show) {
    let bar = document.getElementById('geoUndoBar');
    if (!bar && show) {
      // Create undo bar before save button
      const actions = document.getElementById('geoEditActions');
      if (!actions) return;
      bar = document.createElement('div');
      bar.id = 'geoUndoBar';
      bar.style.cssText = 'display:flex; gap:4px; margin-bottom:6px;';
      bar.innerHTML = `
        <button id="geoUndoBtn" style="flex:1; padding:4px; background:var(--card); color:var(--text-secondary); border:1px solid var(--border); border-radius:3px; font-size:10px; cursor:pointer; font-family:var(--font-body);" title="Undo (Cmd+Z)">↶ Undo</button>
        <button id="geoRedoBtn" style="flex:1; padding:4px; background:var(--card); color:var(--text-secondary); border:1px solid var(--border); border-radius:3px; font-size:10px; cursor:pointer; font-family:var(--font-body);" title="Redo (Cmd+Shift+Z)">↷ Redo</button>
        <button id="geoRevertBtn" style="flex:1; padding:4px; background:var(--card); color:var(--danger); border:1px solid var(--border); border-radius:3px; font-size:10px; cursor:pointer; font-family:var(--font-body);" title="Revert all changes">⟲ Revert</button>
      `;
      actions.insertBefore(bar, actions.firstChild);
      document.getElementById('geoUndoBtn').addEventListener('click', undo);
      document.getElementById('geoRedoBtn').addEventListener('click', redo);
      document.getElementById('geoRevertBtn').addEventListener('click', revertAll);
    }
    if (bar) bar.style.display = show ? 'flex' : 'none';
  }

  // ---- Legend Click Handling ----
  function wireLegendClicks() {
    // Feature tools
    document.querySelectorAll('.geo-selectable').forEach(row => {
      row.addEventListener('click', () => {
        if (!geo.active) return;
        const tool = row.dataset.geoTool;
        if (!tool) return;
        clearSelection();
        geo.tool = tool;
        geo.copySource = null;
        row.classList.add('geo-selected');
        showStatus(toolLabel(tool));
      });
    });

    // Country legend (map.js builds these as .country-row)
    const countryLegend = document.getElementById('countryLegend');
    if (!countryLegend) return;

    const wireItems = () => {
      countryLegend.querySelectorAll('.country-row').forEach(row => {
        if (row._geoWired) return;
        row._geoWired = true;
        row.classList.add('legend-row');

        // Single click: select for painting
        row.addEventListener('click', () => {
          if (!geo.active) return;
          const nameSpan = row.querySelector('.cname');
          if (!nameSpan) return;
          const name = nameSpan.textContent.trim();
          const cid = findCountryId(name);
          if (!cid) return;
          clearSelection();
          geo.tool = cid;
          geo.copySource = null;
          row.classList.add('geo-selected');
          showStatus('Paint: ' + name);
        });

        // Double click: open color picker
        row.addEventListener('dblclick', (e) => {
          if (!geo.active) return;
          e.stopPropagation();
          const nameSpan = row.querySelector('.cname');
          if (!nameSpan) return;
          const cid = findCountryId(nameSpan.textContent.trim());
          if (!cid) return;
          openColorPicker(cid, row);
        });
      });
    };
    wireItems();
    new MutationObserver(wireItems).observe(countryLegend, { childList: true });
  }

  function findCountryId(displayName) {
    // Match display name to country id
    const lower = displayName.toLowerCase();
    for (const cid of Object.keys(geo.palette)) {
      if (cid === lower) return cid;
      // Capitalize first letter comparison
      if (cid.charAt(0).toUpperCase() + cid.slice(1) === displayName) return cid;
    }
    return null;
  }

  function clearSelection() {
    document.querySelectorAll('.geo-selected').forEach(el => el.classList.remove('geo-selected'));
    // Clear copy source outline
    document.querySelectorAll('#mapSvg polygon').forEach(p => p.style.outline = '');
  }

  function toolLabel(tool) {
    return {
      sea: 'Click hexes → Sea',
      chokepoint: 'Click hexes → Toggle Chokepoint',
      diehard: 'Click hexes → Toggle Die Hard',
      nuclear: 'Click hexes → Toggle Nuclear Site',
      copy: 'Click source hex, then click target',
    }[tool] || 'Paint: ' + tool;
  }

  // ---- Hex Click ----
  function wireHexClicks() {
    const svg = document.getElementById('mapSvg');
    if (!svg) return;
    svg.addEventListener('click', handleClick, true);
  }

  function handleClick(e) {
    if (!geo.active || !geo.tool) return;

    let target = e.target;
    while (target && target.tagName !== 'polygon' && target !== e.currentTarget) {
      target = target.parentElement;
    }
    if (!target || target.tagName !== 'polygon') return;

    const row = parseInt(target.dataset.row);
    const col = parseInt(target.dataset.col);
    if (isNaN(row) || isNaN(col)) return;

    e.stopPropagation();
    e.preventDefault();

    const tool = geo.tool;

    // ---- Copy tool ----
    if (tool === 'copy') {
      if (!geo.copySource) {
        // Pick source
        geo.copySource = {
          row, col,
          owner: target.dataset.owner || 'sea',
          fill: target.getAttribute('fill'),
          chokepoint: target.dataset.chokepoint || 'false',
          diehard: target.dataset.diehard || 'false',
          nuclear: target.dataset.nuclear || 'false',
        };
        target.style.outline = '3px solid #5B9BD5';
        showStatus(`Source (${row+1},${col+1}) [${geo.copySource.owner}] → click target`);
        return;
      }
      // Paste to target
      const src = geo.copySource;
      saveUndo(target, row, col);
      target.setAttribute('fill', src.fill);
      target.dataset.owner = src.owner;
      target.dataset.chokepoint = src.chokepoint;
      target.dataset.diehard = src.diehard;
      target.dataset.nuclear = src.nuclear;
      target.setAttribute('class', src.owner === 'sea' ? 'hex sea' : 'hex');
      showStatus(`Pasted → (${row+1},${col+1})`);
      // Clear source outline
      document.querySelectorAll('#mapSvg polygon').forEach(p => p.style.outline = '');
      geo.copySource = null;
      geo.dirty = true;
      return;
    }

    // ---- Feature toggles ----
    if (tool === 'chokepoint' || tool === 'diehard' || tool === 'nuclear') {
      saveUndo(target, row, col);
      toggleFeature(target, row, col, tool);
      geo.dirty = true;
      return;
    }

    // ---- Paint (country or sea) ----
    const owner = (tool === 'sea') ? 'sea' : tool;
    saveUndo(target, row, col);
    const color = mapColorFor(owner);
    target.setAttribute('fill', color);
    target.dataset.owner = owner;
    target.setAttribute('class', owner === 'sea' ? 'hex sea' : 'hex');
    showStatus(`(${row+1},${col+1}) → ${owner}`);
    geo.dirty = true;
  }

  function toggleFeature(poly, row, col, feature) {
    const current = poly.dataset[feature] === 'true';
    poly.dataset[feature] = current ? 'false' : 'true';

    if (!current) {
      const cfg = { chokepoint: ['#E8B84D', '4 2'], diehard: ['#C4922A', '6 3'], nuclear: ['#B03A3A', 'none'] };
      const [color, dash] = cfg[feature];
      poly.style.stroke = color;
      poly.style.strokeWidth = '3';
      poly.style.strokeDasharray = dash;
    } else {
      const hasOther = ['chokepoint', 'diehard', 'nuclear'].some(f => f !== feature && poly.dataset[f] === 'true');
      if (!hasOther) {
        poly.style.stroke = '';
        poly.style.strokeWidth = '';
        poly.style.strokeDasharray = '';
      }
    }
    showStatus(`(${row+1},${col+1}) ${feature}: ${!current}`);
  }

  // ---- Undo / Redo ----
  function saveUndo(poly, row, col) {
    geo.undoStack.push({
      row, col,
      prev: {
        owner: poly.dataset.owner || 'sea',
        fill: poly.getAttribute('fill'),
        cls: poly.getAttribute('class'),
        chokepoint: poly.dataset.chokepoint || 'false',
        diehard: poly.dataset.diehard || 'false',
        nuclear: poly.dataset.nuclear || 'false',
        stroke: poly.style.stroke,
        strokeWidth: poly.style.strokeWidth,
        strokeDasharray: poly.style.strokeDasharray,
      }
    });
    geo.redoStack = []; // Clear redo on new action
  }

  function undo() {
    if (geo.undoStack.length === 0) return;
    const entry = geo.undoStack.pop();
    const poly = document.querySelector(`#mapSvg polygon[data-row="${entry.row}"][data-col="${entry.col}"]`);
    if (!poly) return;

    // Save current state for redo
    geo.redoStack.push({
      row: entry.row, col: entry.col,
      prev: {
        owner: poly.dataset.owner, fill: poly.getAttribute('fill'), cls: poly.getAttribute('class'),
        chokepoint: poly.dataset.chokepoint || 'false', diehard: poly.dataset.diehard || 'false',
        nuclear: poly.dataset.nuclear || 'false',
        stroke: poly.style.stroke, strokeWidth: poly.style.strokeWidth, strokeDasharray: poly.style.strokeDasharray,
      }
    });

    // Restore previous state
    applyState(poly, entry.prev);
    showStatus(`Undo → (${entry.row+1},${entry.col+1})`);
  }

  function redo() {
    if (geo.redoStack.length === 0) return;
    const entry = geo.redoStack.pop();
    const poly = document.querySelector(`#mapSvg polygon[data-row="${entry.row}"][data-col="${entry.col}"]`);
    if (!poly) return;

    geo.undoStack.push({
      row: entry.row, col: entry.col,
      prev: {
        owner: poly.dataset.owner, fill: poly.getAttribute('fill'), cls: poly.getAttribute('class'),
        chokepoint: poly.dataset.chokepoint || 'false', diehard: poly.dataset.diehard || 'false',
        nuclear: poly.dataset.nuclear || 'false',
        stroke: poly.style.stroke, strokeWidth: poly.style.strokeWidth, strokeDasharray: poly.style.strokeDasharray,
      }
    });

    applyState(poly, entry.prev);
    showStatus(`Redo → (${entry.row+1},${entry.col+1})`);
  }

  function revertAll() {
    if (geo.undoStack.length === 0) return;
    if (!confirm(`Revert ${geo.undoStack.length} changes?`)) return;
    // Undo everything in reverse order
    while (geo.undoStack.length > 0) {
      const entry = geo.undoStack.pop();
      const poly = document.querySelector(`#mapSvg polygon[data-row="${entry.row}"][data-col="${entry.col}"]`);
      if (poly) applyState(poly, entry.prev);
    }
    geo.redoStack = [];
    geo.dirty = false;
    showStatus('All changes reverted');
  }

  function applyState(poly, state) {
    poly.dataset.owner = state.owner;
    poly.setAttribute('fill', state.fill);
    poly.setAttribute('class', state.cls);
    poly.dataset.chokepoint = state.chokepoint;
    poly.dataset.diehard = state.diehard;
    poly.dataset.nuclear = state.nuclear;
    poly.style.stroke = state.stroke || '';
    poly.style.strokeWidth = state.strokeWidth || '';
    poly.style.strokeDasharray = state.strokeDasharray || '';
  }

  // ---- Keyboard shortcuts ----
  function wireKeyboard() {
    document.addEventListener('keydown', (e) => {
      if (!geo.active) return;
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        e.preventDefault();
        if (e.shiftKey) redo(); else undo();
      }
    });
  }

  // ---- Save ----
  function wireSave() {
    document.getElementById('geoSaveBtn')?.addEventListener('click', saveGeography);
  }

  async function saveGeography() {
    showStatus('Saving...', 'var(--warning)');
    try {
      const hexes = document.querySelectorAll('#mapSvg polygon[data-row][data-col]');
      const resp = await fetch('/api/map/global');
      const globalData = await resp.json();
      const grid = globalData.grid;
      const chokepoints = {};
      const dieHards = {};
      const nuclearSites = {};

      hexes.forEach(hex => {
        const r = parseInt(hex.dataset.row);
        const c = parseInt(hex.dataset.col);
        const owner = hex.dataset.owner;
        if (owner && grid[r] && grid[r][c]) grid[r][c].owner = owner;
        if (hex.dataset.chokepoint === 'true') chokepoints[`cp_${r+1}_${c+1}`] = { row: r, col: c, name: `Chokepoint (${r+1},${c+1})` };
        if (hex.dataset.diehard === 'true') dieHards[`dh_${r+1}_${c+1}`] = { row: r, col: c, name: 'Die Hard' };
        if (hex.dataset.nuclear === 'true' && owner && owner !== 'sea') nuclearSites[owner] = [r+1, c+1];
      });

      // Collect color changes
      const colorChanges = {};
      for (const [cid, pal] of Object.entries(geo.palette)) {
        if (pal && typeof pal === 'object' && pal.map) {
          colorChanges[cid] = { color_map: pal.map };
        }
      }

      const saveResp = await fetch('/api/map/save_geography', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grid, chokepoints, dieHards, nuclearSites, colorChanges }),
      });

      if (saveResp.ok) {
        showStatus('Saved!', 'var(--success)');
        geo.dirty = false;
        geo.undoStack = [];
        geo.redoStack = [];
      } else {
        showStatus('Save failed', 'var(--danger)');
      }
    } catch (e) {
      showStatus('Error: ' + e.message, 'var(--danger)');
    }
  }

  // ---- Color Picker ----
  function openColorPicker(cid, legendRow) {
    // Remove existing picker
    document.getElementById('geoColorPicker')?.remove();

    const currentColor = mapColorFor(cid);
    const picker = document.createElement('div');
    picker.id = 'geoColorPicker';
    picker.style.cssText = 'position:absolute; background:var(--card); border:1px solid var(--border); border-radius:6px; padding:8px; z-index:200; box-shadow:0 4px 12px rgba(0,0,0,0.3);';

    picker.innerHTML = `
      <div style="font-size:10px; color:var(--text-secondary); margin-bottom:4px;">Color for ${cid}</div>
      <div style="display:flex; gap:6px; align-items:center; margin-bottom:6px;">
        <label style="font-size:9px; color:var(--text-muted);">Map:</label>
        <input type="color" id="geoPickMap" value="${currentColor}" style="width:32px; height:24px; border:none; cursor:pointer;">
      </div>
      <div style="display:flex; gap:4px;">
        <button id="geoPickApply" style="flex:1; padding:3px; background:var(--action); color:white; border:none; border-radius:3px; font-size:10px; cursor:pointer;">Apply</button>
        <button id="geoPickClose" style="flex:1; padding:3px; background:var(--card); color:var(--text-secondary); border:1px solid var(--border); border-radius:3px; font-size:10px; cursor:pointer;">Close</button>
      </div>
    `;

    // Position near the legend row
    const rect = legendRow.getBoundingClientRect();
    picker.style.left = (rect.right + 5) + 'px';
    picker.style.top = rect.top + 'px';
    document.body.appendChild(picker);

    document.getElementById('geoPickApply').addEventListener('click', () => {
      const newColor = document.getElementById('geoPickMap').value;
      // Update palette
      if (!geo.palette[cid]) geo.palette[cid] = {};
      if (typeof geo.palette[cid] === 'object') {
        geo.palette[cid].map = newColor;
      }
      // Update legend swatch
      const swatch = legendRow.querySelector('.swatch');
      if (swatch) swatch.style.background = newColor;
      // Update all hexes with this owner
      document.querySelectorAll(`#mapSvg polygon[data-owner="${cid}"]`).forEach(poly => {
        poly.setAttribute('fill', newColor);
      });
      geo.dirty = true;
      showStatus(`Color updated: ${cid} → ${newColor}`);
      picker.remove();
    });

    document.getElementById('geoPickClose').addEventListener('click', () => picker.remove());
  }

  // ---- Helpers ----
  function showStatus(msg, color) {
    const el = document.getElementById('geoSaveStatus');
    if (el) { el.textContent = msg; el.style.color = color || 'var(--text-secondary)'; }
  }
})();
