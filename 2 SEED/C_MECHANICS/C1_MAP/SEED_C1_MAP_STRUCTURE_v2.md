# TTT Map Structure Export

> Exported 2026-03-27

---

## Land Hex Registry

| hex_id | owner | row | col |
|--------|-------|-----|-----|
| nordostan_1 | nordostan | 2 | 10 |
| freeland_1 | freeland | 3 | 9 |
| nordostan_2 | nordostan | 3 | 10 |
| nordostan_3 | nordostan | 3 | 11 |
| nordostan_4 | nordostan | 3 | 15 |
| columbia_1 | columbia | 4 | 2 |
| teutonia_1 | teutonia | 4 | 5 |
| albion_1 | albion | 4 | 7 |
| freeland_2 | freeland | 4 | 9 |
| heartland_1 | heartland | 4 | 10 |
| nordostan_5 | nordostan | 4 | 11 |
| nordostan_6 | nordostan | 4 | 12 |
| nordostan_7 | nordostan | 4 | 13 |
| nordostan_8 | nordostan | 4 | 14 |
| nordostan_9 | nordostan | 4 | 15 |
| choson_1 | choson | 4 | 17 |
| columbia_2 | columbia | 5 | 1 |
| columbia_3 | columbia | 5 | 2 |
| albion_2 | albion | 5 | 6 |
| teutonia_2 | teutonia | 5 | 8 |
| teutonia_3 | teutonia | 5 | 9 |
| heartland_2 | heartland | 5 | 10 |
| nordostan_10 | nordostan | 5 | 11 |
| nordostan_11 | nordostan | 5 | 12 |
| nordostan_12 | nordostan | 5 | 13 |
| nordostan_13 | nordostan | 5 | 15 |
| hanguk_1 | hanguk | 5 | 16 |
| yamato_1 | yamato | 5 | 18 |
| columbia_4 | columbia | 6 | 2 |
| columbia_5 | columbia | 6 | 3 |
| columbia_6 | columbia | 6 | 4 |
| gallia_1 | gallia | 6 | 8 |
| gallia_2 | gallia | 6 | 9 |
| phrygia_1 | phrygia | 6 | 10 |
| sogdiana_1 | sogdiana | 6 | 13 |
| cathay_1 | cathay | 6 | 14 |
| cathay_2 | cathay | 6 | 15 |
| cathay_3 | cathay | 6 | 16 |
| yamato_2 | yamato | 6 | 18 |
| columbia_7 | columbia | 7 | 2 |
| columbia_8 | columbia | 7 | 3 |
| ponte_1 | ponte | 7 | 7 |
| levantia_1 | levantia | 7 | 9 |
| phrygia_2 | phrygia | 7 | 10 |
| persia_1 | persia | 7 | 11 |
| sogdiana_2 | sogdiana | 7 | 12 |
| sogdiana_3 | sogdiana | 7 | 13 |
| cathay_4 | cathay | 7 | 14 |
| cathay_5 | cathay | 7 | 15 |
| columbia_9 | columbia | 8 | 3 |
| ponte_2 | ponte | 8 | 8 |
| solaria_1 | solaria | 8 | 10 |
| persia_2 | persia | 8 | 12 |
| bharata_1 | bharata | 8 | 13 |
| bharata_2 | bharata | 8 | 14 |
| cathay_6 | cathay | 8 | 15 |
| formosa_1 | formosa | 8 | 17 |
| solaria_2 | solaria | 9 | 9 |
| mirage_1 | mirage | 9 | 10 |
| persia_3 | persia | 9 | 12 |
| bharata_3 | bharata | 9 | 13 |
| bharata_4 | bharata | 9 | 14 |
| caribe_1 | caribe | 10 | 4 |
| horn_1 | horn | 10 | 9 |
| bharata_5 | bharata | 10 | 14 |

## Chokepoints

| name | key | row | col |
|------|-----|-----|-----|
| Formosa Strait | formosa_strait | 8 | 16 |
| Gulf Gate | gulf_gate | 9 | 11 |
| Caribe Passage | caribe_passage | 9 | 3 |

## Adjacency List

Land-to-land adjacencies (computed from grid positions):

```
nordostan_1: freeland_1, nordostan_2
freeland_1: nordostan_1, nordostan_2, freeland_2, heartland_1
nordostan_2: nordostan_1, freeland_1, nordostan_3, heartland_1, nordostan_5
nordostan_3: nordostan_2, nordostan_5, nordostan_6
nordostan_4: nordostan_9
columbia_1: columbia_2, columbia_3
teutonia_1: (island, no land adjacency)
albion_1: albion_2
freeland_2: freeland_1, heartland_1, teutonia_2, teutonia_3
heartland_1: freeland_1, nordostan_2, freeland_2, nordostan_5, teutonia_3, heartland_2
nordostan_5: nordostan_2, nordostan_3, heartland_1, nordostan_6, heartland_2, nordostan_10
nordostan_6: nordostan_3, nordostan_5, nordostan_7, nordostan_10, nordostan_11
nordostan_7: nordostan_6, nordostan_8, nordostan_11, nordostan_12
nordostan_8: nordostan_7, nordostan_9, nordostan_12
nordostan_9: nordostan_4, nordostan_8, nordostan_13
choson_1: hanguk_1
columbia_2: columbia_1, columbia_3, columbia_4
columbia_3: columbia_1, columbia_2, columbia_4, columbia_5
albion_2: albion_1
teutonia_2: freeland_2, teutonia_3, gallia_1, gallia_2
teutonia_3: freeland_2, heartland_1, teutonia_2, heartland_2, gallia_2, phrygia_1
heartland_2: heartland_1, nordostan_5, teutonia_3, nordostan_10, phrygia_1
nordostan_10: nordostan_5, nordostan_6, heartland_2, nordostan_11
nordostan_11: nordostan_6, nordostan_7, nordostan_10, nordostan_12, sogdiana_1
nordostan_12: nordostan_7, nordostan_8, nordostan_11, sogdiana_1, cathay_1
nordostan_13: nordostan_9, hanguk_1, cathay_2, cathay_3
hanguk_1: choson_1, nordostan_13, cathay_3
yamato_1: yamato_2
columbia_4: columbia_2, columbia_3, columbia_5, columbia_7
columbia_5: columbia_3, columbia_4, columbia_6, columbia_7, columbia_8
columbia_6: columbia_5, columbia_8
gallia_1: teutonia_2, gallia_2, ponte_1
gallia_2: teutonia_2, teutonia_3, gallia_1, phrygia_1, levantia_1
phrygia_1: teutonia_3, heartland_2, gallia_2, levantia_1, phrygia_2
sogdiana_1: nordostan_11, nordostan_12, cathay_1, sogdiana_2, sogdiana_3
cathay_1: nordostan_12, sogdiana_1, cathay_2, sogdiana_3, cathay_4
cathay_2: nordostan_13, cathay_1, cathay_3, cathay_4, cathay_5
cathay_3: nordostan_13, hanguk_1, cathay_2, cathay_5
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
