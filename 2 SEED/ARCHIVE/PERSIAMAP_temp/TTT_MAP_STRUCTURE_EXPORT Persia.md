# TTT Map Structure Export

> Exported 2026-03-31

---

## Land Hex Registry

| hex_id | owner | occupied_by | global_link | row | col |
|--------|-------|-------------|-------------|-----|-----|
| phrygia_1 | phrygia |  |  | 0 | 0 |
| phrygia_2 | phrygia |  |  | 0 | 1 |
| phrygia_3 | phrygia |  |  | 0 | 2 |
| persia_1 | persia |  |  | 0 | 3 |
| persia_2 | persia |  |  | 0 | 4 |
| persia_3 | persia |  |  | 0 | 5 |
| persia_4 | persia |  |  | 0 | 6 |
| persia_5 | persia |  |  | 0 | 7 |
| persia_6 | persia |  |  | 0 | 8 |
| persia_7 | persia |  |  | 0 | 9 |
| phrygia_4 | phrygia |  |  | 1 | 0 |
| phrygia_5 | phrygia |  |  | 1 | 1 |
| persia_8 | persia |  |  | 1 | 2 |
| persia_9 | persia |  |  | 1 | 3 |
| persia_10 | persia |  |  | 1 | 4 |
| persia_11 | persia |  |  | 1 | 5 |
| persia_12 | persia |  |  | 1 | 6 |
| persia_13 | persia |  |  | 1 | 7 |
| persia_14 | persia |  |  | 1 | 8 |
| persia_15 | persia |  |  | 1 | 9 |
| phrygia_6 | phrygia |  |  | 2 | 0 |
| persia_16 | persia |  |  | 2 | 3 |
| persia_17 | persia |  |  | 2 | 4 |
| persia_18 | persia |  |  | 2 | 5 |
| persia_19 | persia |  |  | 2 | 6 |
| persia_20 | persia |  |  | 2 | 7 |
| persia_21 | persia |  |  | 2 | 8 |
| persia_22 | persia |  |  | 2 | 9 |
| solaria_1 | solaria |  |  | 3 | 0 |
| persia_23 | persia |  |  | 3 | 3 |
| persia_24 | persia |  |  | 3 | 4 |
| persia_25 | persia |  |  | 3 | 5 |
| persia_26 | persia |  |  | 3 | 6 |
| persia_27 | persia |  |  | 3 | 7 |
| persia_28 | persia |  |  | 3 | 8 |
| persia_29 | persia |  |  | 3 | 9 |
| solaria_2 | solaria |  |  | 4 | 0 |
| persia_30 | persia |  |  | 4 | 5 |
| persia_31 | persia |  |  | 4 | 6 |
| persia_32 | persia |  |  | 4 | 7 |
| persia_33 | persia |  |  | 4 | 8 |
| persia_34 | persia |  |  | 4 | 9 |
| solaria_3 | solaria |  |  | 5 | 0 |
| persia_35 | persia |  |  | 5 | 5 |
| persia_36 | persia |  |  | 5 | 6 |
| persia_37 | persia |  |  | 5 | 7 |
| persia_38 | persia |  |  | 5 | 8 |
| persia_39 | persia |  |  | 5 | 9 |
| solaria_4 | solaria |  |  | 6 | 0 |
| persia_40 | persia |  |  | 6 | 6 |
| persia_41 | persia |  |  | 6 | 7 |
| persia_42 | persia |  |  | 6 | 8 |
| persia_43 | persia |  |  | 6 | 9 |
| solaria_5 | solaria |  |  | 7 | 0 |
| persia_44 | persia |  |  | 7 | 5 |
| persia_45 | persia |  |  | 7 | 7 |
| persia_46 | persia |  |  | 7 | 8 |
| persia_47 | persia |  |  | 7 | 9 |
| mirage_1 | mirage |  |  | 8 | 0 |
| mirage_2 | mirage |  |  | 8 | 1 |
| mirage_3 | mirage |  |  | 8 | 2 |
| persia_48 | persia |  |  | 8 | 8 |
| persia_49 | persia |  |  | 8 | 9 |
| mirage_4 | mirage |  |  | 9 | 0 |
| mirage_5 | mirage |  |  | 9 | 1 |
| mirage_6 | mirage |  |  | 9 | 2 |
| mirage_7 | mirage |  |  | 9 | 3 |
| mirage_8 | mirage |  |  | 9 | 4 |
| persia_50 | persia |  |  | 9 | 8 |
| persia_51 | persia |  |  | 9 | 9 |

## Chokepoints

| name | key | row | col |
|------|-----|-----|-----|
| Formosa Strait | formosa_strait | -- | -- |
| Gulf Gate | gulf_gate | -- | -- |
| Caribe Passage | caribe_passage | -- | -- |

## Die Hard

| name | key | row | col |
|------|-----|-----|-----|
| Die Hard | die_hard_1 | -- | -- |

## Adjacency List

Land-to-land adjacencies (computed from grid positions):

```
phrygia_1: phrygia_2, phrygia_4
phrygia_2: phrygia_1, phrygia_3, phrygia_4, phrygia_5
phrygia_3: phrygia_2, persia_1, phrygia_5, persia_8
persia_1: phrygia_3, persia_2, persia_8, persia_9
persia_2: persia_1, persia_3, persia_9, persia_10
persia_3: persia_2, persia_4, persia_10, persia_11
persia_4: persia_3, persia_5, persia_11, persia_12
persia_5: persia_4, persia_6, persia_12, persia_13
persia_6: persia_5, persia_7, persia_13, persia_14
persia_7: persia_6, persia_14, persia_15
phrygia_4: phrygia_1, phrygia_2, phrygia_5, phrygia_6
phrygia_5: phrygia_2, phrygia_3, phrygia_4, persia_8
persia_8: phrygia_3, persia_1, phrygia_5, persia_9, persia_16
persia_9: persia_1, persia_2, persia_8, persia_10, persia_16, persia_17
persia_10: persia_2, persia_3, persia_9, persia_11, persia_17, persia_18
persia_11: persia_3, persia_4, persia_10, persia_12, persia_18, persia_19
persia_12: persia_4, persia_5, persia_11, persia_13, persia_19, persia_20
persia_13: persia_5, persia_6, persia_12, persia_14, persia_20, persia_21
persia_14: persia_6, persia_7, persia_13, persia_15, persia_21, persia_22
persia_15: persia_7, persia_14, persia_22
phrygia_6: phrygia_4, solaria_1
persia_16: persia_8, persia_9, persia_17, persia_23
persia_17: persia_9, persia_10, persia_16, persia_18, persia_23, persia_24
persia_18: persia_10, persia_11, persia_17, persia_19, persia_24, persia_25
persia_19: persia_11, persia_12, persia_18, persia_20, persia_25, persia_26
persia_20: persia_12, persia_13, persia_19, persia_21, persia_26, persia_27
persia_21: persia_13, persia_14, persia_20, persia_22, persia_27, persia_28
persia_22: persia_14, persia_15, persia_21, persia_28, persia_29
solaria_1: phrygia_6, solaria_2
persia_23: persia_16, persia_17, persia_24
persia_24: persia_17, persia_18, persia_23, persia_25, persia_30
persia_25: persia_18, persia_19, persia_24, persia_26, persia_30, persia_31
persia_26: persia_19, persia_20, persia_25, persia_27, persia_31, persia_32
persia_27: persia_20, persia_21, persia_26, persia_28, persia_32, persia_33
persia_28: persia_21, persia_22, persia_27, persia_29, persia_33, persia_34
persia_29: persia_22, persia_28, persia_34
solaria_2: solaria_1, solaria_3
persia_30: persia_24, persia_25, persia_31, persia_35
persia_31: persia_25, persia_26, persia_30, persia_32, persia_35, persia_36
persia_32: persia_26, persia_27, persia_31, persia_33, persia_36, persia_37
persia_33: persia_27, persia_28, persia_32, persia_34, persia_37, persia_38
persia_34: persia_28, persia_29, persia_33, persia_38, persia_39
solaria_3: solaria_2, solaria_4
persia_35: persia_30, persia_31, persia_36, persia_40
persia_36: persia_31, persia_32, persia_35, persia_37, persia_40, persia_41
persia_37: persia_32, persia_33, persia_36, persia_38, persia_41, persia_42
persia_38: persia_33, persia_34, persia_37, persia_39, persia_42, persia_43
persia_39: persia_34, persia_38, persia_43
solaria_4: solaria_3, solaria_5
persia_40: persia_35, persia_36, persia_41, persia_44
persia_41: persia_36, persia_37, persia_40, persia_42, persia_45
persia_42: persia_37, persia_38, persia_41, persia_43, persia_45, persia_46
persia_43: persia_38, persia_39, persia_42, persia_46, persia_47
solaria_5: solaria_4, mirage_1, mirage_2
persia_44: persia_40
persia_45: persia_41, persia_42, persia_46, persia_48
persia_46: persia_42, persia_43, persia_45, persia_47, persia_48, persia_49
persia_47: persia_43, persia_46, persia_49
mirage_1: solaria_5, mirage_2, mirage_4
mirage_2: solaria_5, mirage_1, mirage_3, mirage_4, mirage_5
mirage_3: mirage_2, mirage_5, mirage_6
persia_48: persia_45, persia_46, persia_49, persia_50
persia_49: persia_46, persia_47, persia_48, persia_50, persia_51
mirage_4: mirage_1, mirage_2, mirage_5
mirage_5: mirage_2, mirage_3, mirage_4, mirage_6
mirage_6: mirage_3, mirage_5, mirage_7
mirage_7: mirage_6, mirage_8
mirage_8: mirage_7
persia_50: persia_48, persia_49, persia_51
persia_51: persia_49, persia_50
```
