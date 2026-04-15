/* TTT Map Configuration — browser mirror of app/engine/config/map_config.py
 * Single source of truth for map dimensions + theater/global linkage.
 * Any browser code touching these values MUST read them from window.MAP_CONFIG.
 */
(function () {
  'use strict';

  var THEATER_LINK_HEXES = {
    // Eastern Ereb
    '3,12': 'eastern_ereb',
    '4,12': 'eastern_ereb',
    '4,11': 'eastern_ereb',
    '5,12': 'eastern_ereb',
    // Mashriq
    '6,11': 'mashriq',
    '7,11': 'mashriq',
    '8,11': 'mashriq',
    '6,12': 'mashriq',
    '7,13': 'mashriq',
    '8,13': 'mashriq',
    '7,12': 'mashriq',
    '8,12': 'mashriq',
  };

  window.MAP_CONFIG = {
    VERSION: '1.0',
    GLOBAL_ROWS: 10,
    GLOBAL_COLS: 20,
    THEATERS: {
      eastern_ereb: { rows: 10, cols: 10, display_name: 'Eastern Ereb' },
      mashriq:      { rows: 10, cols: 10, display_name: 'Mashriq' },
    },
    THEATER_NAMES: ['eastern_ereb', 'mashriq'],
    COUNTRY_CODES: [
      'albion','bharata','caribe','cathay','choson','columbia','formosa',
      'freeland','gallia','hanguk','levantia','mirage','persia','phrygia',
      'ponte','ruthenia','sarmatia','solaria','teutonia','yamato',
    ],
    UNIT_TYPES: ['ground','tactical_air','strategic_missile','air_defense','naval'],
    UNIT_STATUSES: ['active','reserve','embarked','destroyed'],

    /* Canonical theater cell -> global hex mapping (Marat 2026-04-05).
     * Returns [row, col] 1-indexed, or null if no mapping.
     * cellOwner is required — pass the owner of the theater cell.
     */
    globalHexForTheaterCell: function (theater, trow, tcol, cellOwner) {
      if (cellOwner == null) return null;
      if (theater === 'eastern_ereb') {
        if (cellOwner === 'sea') return [5, 12];
        if (cellOwner === 'sarmatia') return trow <= 4 ? [3, 12] : [4, 12];
        if (cellOwner === 'ruthenia') return [4, 11];
        return null;
      }
      if (theater === 'mashriq') {
        if (cellOwner === 'phrygia') return [6, 11];
        if (cellOwner === 'solaria') return [7, 11];
        if (cellOwner === 'mirage') return [8, 11];
        if (cellOwner === 'persia') {
          if (trow <= 3) return [6, 12];
          if (trow <= 6) return [7, 13];
          return [8, 13];
        }
        if (cellOwner === 'sea') {
          if (trow >= 3 && trow <= 6) return [7, 12];
          if (trow >= 7 && trow <= 10) return [8, 12];
          return null;
        }
        return null;
      }
      return null;
    },

    /* Static {"row,col": theater_name} for all global hexes that carry a theater link. */
    theaterLinkHexes: function () {
      return Object.assign({}, THEATER_LINK_HEXES);
    },

    isTheaterLinkHex: function (row, col) {
      return Object.prototype.hasOwnProperty.call(THEATER_LINK_HEXES, row + ',' + col);
    },

    theaterForGlobalHex: function (row, col) {
      return THEATER_LINK_HEXES[row + ',' + col] || null;
    },

    inGlobalBounds: function (row, col) {
      return row >= 1 && row <= 10 && col >= 1 && col <= 20;
    },

    inTheaterBounds: function (theater, row, col) {
      var t = this.THEATERS[theater];
      if (!t) return false;
      return row >= 1 && row <= t.rows && col >= 1 && col <= t.cols;
    },

    // Nuclear sites — (row, col) 1-indexed global coordinates
    NUCLEAR_SITES: {
      persia: [7, 13],
      choson: [3, 18],
    },
  };
})();
