# Global Map Structure

> Size: 10 rows × 20 cols

---

## Map Architecture Decision

**Global Map:** 10×20 hex grid, 22 countries, 3 chokepoints (Formosa Strait, Gulf Gate, Caribe Passage)

**Theater Maps:** Only Eastern Ereb has a detailed theater map (10×10 hexes).
Other theaters (Formosa, Mashriq, Caribbean, Thule, Korea) resolved at global hex level:
- Formosa blockade: fleet occupies all water hexes adjacent to Formosa global hex
- Gulf Gate blockade: Persia coast hex ground forces maintain blockade
- Amphibious assault: 4:1 ratio applies at global hex level
- Caribbean/Thule/Korea: political events, 1 hex resolution sufficient

**Global-Theater Link:** Eastern Ereb theater hexes link to global hexes:
- All Heartland theater hexes → global (11,4)
- Nordostan rows 1-3 → global (12,3)
- Nordostan rows 4+ → global (12,4)

---

## Land Hex Registry

| hex_id | owner | row | col |
|--------|-------|-----|-----|
| freeland_1 | freeland | 1 | 9 |
| nordostan_1 | nordostan | 1 | 10 |
| nordostan_2 | nordostan | 1 | 11 |
| nordostan_3 | nordostan | 1 | 15 |
| columbia_1 | columbia | 2 | 2 |
| teutonia_1 | teutonia | 2 | 5 |
| albion_1 | albion | 2 | 7 |
| freeland_2 | freeland | 2 | 9 |
| heartland_1 | heartland | 2 | 10 |
| nordostan_4 | nordostan | 2 | 11 |
| nordostan_5 | nordostan | 2 | 12 |
| nordostan_6 | nordostan | 2 | 13 |
| nordostan_7 | nordostan | 2 | 14 |
| nordostan_8 | nordostan | 2 | 15 |
| choson_1 | choson | 2 | 17 |
| columbia_2 | columbia | 3 | 1 |
| columbia_3 | columbia | 3 | 2 |
| albion_2 | albion | 3 | 6 |
| teutonia_2 | teutonia | 3 | 8 |
| teutonia_3 | teutonia | 3 | 9 |
| heartland_2 | heartland | 3 | 10 |
| nordostan_9 | nordostan | 3 | 11 |
| nordostan_10 | nordostan | 3 | 12 |
| nordostan_11 | nordostan | 3 | 13 |
| nordostan_12 | nordostan | 3 | 15 |
| hanguk_1 | hanguk | 3 | 16 |
| yamato_1 | yamato | 3 | 18 |
| columbia_4 | columbia | 4 | 2 |
| columbia_5 | columbia | 4 | 3 |
| columbia_6 | columbia | 4 | 4 |
| gallia_1 | gallia | 4 | 8 |
| gallia_2 | gallia | 4 | 9 |
| phrygia_1 | phrygia | 4 | 10 |
| sogdiana_1 | sogdiana | 4 | 13 |
| cathay_1 | cathay | 4 | 14 |
| cathay_2 | cathay | 4 | 15 |
| cathay_3 | cathay | 4 | 16 |
| yamato_2 | yamato | 4 | 18 |
| columbia_7 | columbia | 5 | 2 |
| columbia_8 | columbia | 5 | 3 |
| ponte_1 | ponte | 5 | 7 |
| levantia_1 | levantia | 5 | 9 |
| phrygia_2 | phrygia | 5 | 10 |
| persia_1 | persia | 5 | 11 |
| sogdiana_2 | sogdiana | 5 | 12 |
| sogdiana_3 | sogdiana | 5 | 13 |
| cathay_4 | cathay | 5 | 14 |
| cathay_5 | cathay | 5 | 15 |
| columbia_9 | columbia | 6 | 3 |
| ponte_2 | ponte | 6 | 8 |
| solaria_1 | solaria | 6 | 10 |
| persia_2 | persia | 6 | 12 |
| bharata_1 | bharata | 6 | 13 |
| bharata_2 | bharata | 6 | 14 |
| cathay_6 | cathay | 6 | 15 |
| formosa_1 | formosa | 6 | 17 |
| solaria_2 | solaria | 7 | 9 |
| mirage_1 | mirage | 7 | 10 |
| persia_3 | persia | 7 | 12 |
| bharata_3 | bharata | 7 | 13 |
| bharata_4 | bharata | 7 | 14 |
| caribe_1 | caribe | 8 | 4 |
| horn_1 | horn | 8 | 9 |
| bharata_5 | bharata | 8 | 14 |

## Chokepoints

| Name | Row | Col |
|------|-----|-----|
| Formosa Strait | 6 | 16 |
| Gulf Gate | 7 | 11 |
| Caribe Passage | 7 | 3 |
