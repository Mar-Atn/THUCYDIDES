# MODULE REGISTRY — Live Status
**Last updated:** 2026-04-15

| Module | Status | SPEC | Progress |
|---|---|---|---|
| M1 World Model Engines | ✅ ALIGNED | N/A | 720 L1 tests passing. Deprecated fields marked (political_support, dem_rep_split). Agent prompts use stability only. New actions: change_leader (stub for M4). |
| M2 Communication & Standards | ✅ ALIGNED | N/A | 24 action types. 3 new contracts (CHANGE_LEADER, COLUMBIA_ELECTIONS, MAP_RENDERING). 3 archived. Orphaned validators marked deprecated. |
| M3 Data Foundation | ✅ ALIGNED | N/A | Template/Run hierarchy. Hex map in template JSONB. Country colors in DB. Deprecated fields marked, backward compatible. |
| M10.1 Auth | ✅ DONE | ✅ | Email/password + Google OAuth, RLS, GDPR consent. Auth persists across HMR. |
| M9 Sim Setup | ✅ v1 DONE | ✅ | 10-tab Template Editor, SimRun wizard, User Mgmt, AI Setup. 40 roles (5 types), country/role briefs, map viewer/editor, deployment editor. Simplification A-E complete. |
| M4 Sim Runner | ⚠️ NEXT | — | Needs: change_leader voting, elections, agreement auto-transitions, round flow. |
| M8 Public Screen | ⚠️ ~40% | — | Hex map rendering contract ready (CONTRACT_MAP_RENDERING). |
| M6 Human Interface | ❌ NOT STARTED | — | Map rendering contract ready. |
| M5 AI Participant | ⚠️ PARTIAL | — | Agent prompts updated (stability only, no political_support). |
| M7 Navigator | ❌ NOT STARTED | — | |
| M10 Final Assembly | ❌ NOT STARTED | — | |

## Simplification Sprint (2026-04-15) — ALL COMPLETE + RECONCILED
- A. political_support → stability only ✅ (engine, context, agents updated)
- B. personal_coins deprecated ✅ (contract updated, code marked)
- C. Relations: 5 types, 5 agreement types, auto-transitions ✅
- D. change_leader replaces coup/protest ✅ (contract, schema, dispatcher)
- E. Columbia elections: 9+bonus votes, simple majority ✅
- Cross-module reconciliation: ✅ (720 L1 tests pass)

## Active Contracts
| Contract | Version | Status |
|---|---|---|
| CONTRACT_CHANGE_LEADER | 1.0 | LOCKED 2026-04-15 |
| CONTRACT_COLUMBIA_ELECTIONS | 2.0 | LOCKED 2026-04-15 |
| CONTRACT_MAP_RENDERING | 1.0 | LOCKED 2026-04-15 |
| CONTRACT_POWER_ASSIGNMENTS | 1.0 | LOCKED 2026-04-13 |
| CONTRACT_RUN_ROLES | 1.0 | Updated 2026-04-15 (personal_coins deprecated) |
| CONTRACT_BUDGET | 1.1 | LOCKED 2026-04-10 |
| CONTRACT_SANCTIONS | 1.0 | LOCKED |
| CONTRACT_NUCLEAR_CHAIN | 1.0 | LOCKED 2026-04-13 |

## Archived Contracts (in DEPRECATED/)
- CONTRACT_COUP.md
- CONTRACT_MASS_PROTEST.md
- CONTRACT_ELECTIONS.md (v1, old camp system)
