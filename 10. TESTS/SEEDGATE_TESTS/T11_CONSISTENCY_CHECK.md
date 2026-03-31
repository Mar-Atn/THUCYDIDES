# T11 CONSISTENCY CHECK — Results
## SEED Gate Test | Automated Validation
**Date:** 2026-03-30 | **Tester:** Independent

---

## Summary: 12 PASS, 4 FAIL out of 16 checks

## Data Volumes
| CSV | Rows |
|-----|------|
| countries | 20 |
| roles | 40 |
| relationships | 380 |
| organizations | 9 |
| org_memberships | 60 |
| zones | 112 |
| zone_adjacency | 96 |
| deployments | 146 |
| sanctions | 36 |
| tariffs | 29 |

## Results

| Check | Name | Status | Details |
|-------|------|--------|---------|
| A1 | roles→countries | **PASS** | All 40 roles reference valid countries |
| A2 | deployments→countries | **PASS** | All deployment countries valid |
| A3 | deployments→zones | **PASS** | 39 land + 8 water zones OK |
| A4 | adjacency→zones | **PASS** | All adjacency references valid |
| A5 | memberships→orgs | **PASS** | All org references valid |
| A6 | memberships→countries | **PASS** | All membership countries valid |
| A7 | sanctions→countries | **PASS** | All sanctions countries valid |
| A8 | tariffs→countries | **PASS** | All tariff countries valid |
| A9 | unit totals match | **FAIL** | 2 mismatches: columbia.mil_naval: CSV=11 vs deploy=10; cathay.mil_naval: CSV=7 vs deploy=6 |
| A10 | no duplicate IDs | **FAIL** | Dups: countries=False roles=False zones=True orgs=False |
| A11 | no empty required fields | **FAIL** | ['zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id', 'zones: empty id'] |
| A12 | home_zones→zones | **PASS** | All home zones valid |
| D1 | relationship coverage | **PASS** | 20 entities in relationships |
| E1 | no orphan zones | **FAIL** | Orphans: ['yamato_1', 'thule', 'albion', 'yamato_2'] |
| E2 | chokepoints exist | **PASS** | All 3 chokepoints present |
| E4 | Thule separate | **PASS** | Thule zones: ['thule'] |

---

## Verdict: **BLOCKED — fix required**

4 issues found — review before proceeding.
