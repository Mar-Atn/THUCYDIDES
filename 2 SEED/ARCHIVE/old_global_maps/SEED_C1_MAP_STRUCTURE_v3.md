# TTT Map Structure Export

> Exported 2026-03-27

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

| name | key | row | col |
|------|-----|-----|-----|
| Formosa Strait | formosa_strait | 6 | 16 |
| Gulf Gate | gulf_gate | 7 | 11 |
| Caribe Passage | caribe_passage | 7 | 3 |

## Adjacency List

Land-to-land adjacencies (computed from grid positions):

```
freeland_1: nordostan_1, freeland_2, heartland_1
nordostan_1: freeland_1, nordostan_2, heartland_1, nordostan_4
nordostan_2: nordostan_1, nordostan_4, nordostan_5
nordostan_3: nordostan_8
columbia_1: columbia_2, columbia_3
teutonia_1: (island, no land adjacency)
albion_1: albion_2
freeland_2: freeland_1, heartland_1, teutonia_2, teutonia_3
heartland_1: freeland_1, nordostan_1, freeland_2, nordostan_4, teutonia_3, heartland_2
nordostan_4: nordostan_1, nordostan_2, heartland_1, nordostan_5, heartland_2, nordostan_9
nordostan_5: nordostan_2, nordostan_4, nordostan_6, nordostan_9, nordostan_10
nordostan_6: nordostan_5, nordostan_7, nordostan_10, nordostan_11
nordostan_7: nordostan_6, nordostan_8, nordostan_11
nordostan_8: nordostan_3, nordostan_7, nordostan_12
choson_1: hanguk_1
columbia_2: columbia_1, columbia_3, columbia_4
columbia_3: columbia_1, columbia_2, columbia_4, columbia_5
albion_2: albion_1
teutonia_2: freeland_2, teutonia_3, gallia_1, gallia_2
teutonia_3: freeland_2, heartland_1, teutonia_2, heartland_2, gallia_2, phrygia_1
heartland_2: heartland_1, nordostan_4, teutonia_3, nordostan_9, phrygia_1
nordostan_9: nordostan_4, nordostan_5, heartland_2, nordostan_10
nordostan_10: nordostan_5, nordostan_6, nordostan_9, nordostan_11, sogdiana_1
nordostan_11: nordostan_6, nordostan_7, nordostan_10, sogdiana_1, cathay_1
nordostan_12: nordostan_8, hanguk_1, cathay_2, cathay_3
hanguk_1: choson_1, nordostan_12, cathay_3
yamato_1: yamato_2
columbia_4: columbia_2, columbia_3, columbia_5, columbia_7
columbia_5: columbia_3, columbia_4, columbia_6, columbia_7, columbia_8
columbia_6: columbia_5, columbia_8
gallia_1: teutonia_2, gallia_2, ponte_1
gallia_2: teutonia_2, teutonia_3, gallia_1, phrygia_1, levantia_1
phrygia_1: teutonia_3, heartland_2, gallia_2, levantia_1, phrygia_2
sogdiana_1: nordostan_10, nordostan_11, cathay_1, sogdiana_2, sogdiana_3
cathay_1: nordostan_11, sogdiana_1, cathay_2, sogdiana_3, cathay_4
cathay_2: nordostan_12, cathay_1, cathay_3, cathay_4, cathay_5
cathay_3: nordostan_12, hanguk_1, cathay_2, cathay_5
yamato_2: yamato_1
columbia_7: columbia_4, columbia_5, columbia_8, columbia_9
columbia_8: columbia_5, columbia_6, columbia_7, columbia_9
ponte_1: gallia_1, ponte_2
levantia_1: gallia_2, phrygia_1, phrygia_2, solaria_1
phrygia_2: phrygia_1, levantia_1, persia_1, solaria_1
persia_1: phrygia_2, sogdiana_2, persia_2
sogdiana_2: sogdiana_1, persia_1, sogdiana_3, persia_2, bharata_1
sogdiana_3: sogdiana_1, cathay_1, sogdiana_2, cathay_4, bharata_1, bharata_2
cathay_4: cathay_1, cathay_2, sogdiana_3, cathay_5, bharata_2, cathay_6
cathay_5: cathay_2, cathay_3, cathay_4, cathay_6
columbia_9: columbia_7, columbia_8
ponte_2: ponte_1
solaria_1: levantia_1, phrygia_2, solaria_2, mirage_1
persia_2: persia_1, sogdiana_2, bharata_1, persia_3
bharata_1: sogdiana_2, sogdiana_3, persia_2, bharata_2, persia_3, bharata_3
bharata_2: sogdiana_3, cathay_4, bharata_1, cathay_6, bharata_3, bharata_4
cathay_6: cathay_4, cathay_5, bharata_2, bharata_4
formosa_1: (island, no land adjacency)
solaria_2: solaria_1, mirage_1, horn_1
mirage_1: solaria_1, solaria_2
persia_3: persia_2, bharata_1, bharata_3
bharata_3: bharata_1, bharata_2, persia_3, bharata_4, bharata_5
bharata_4: bharata_2, cathay_6, bharata_3, bharata_5
caribe_1: (island, no land adjacency)
horn_1: solaria_2
bharata_5: bharata_3, bharata_4
```
