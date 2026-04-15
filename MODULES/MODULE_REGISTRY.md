# MODULE REGISTRY — Live Status
**Last updated:** 2026-04-15

| Module | Status | SPEC | KING | Progress |
|---|---|---|---|---|
| M1 World Model Engines | ⚠️ NEEDS UPDATE | N/A | N/A | 25 engines, 713 L1 tests passing. Simplification changes: political_support deprecated, stability-only, change_leader replaces coup/protest. Some engine files still reference deprecated fields — cleanup needed. |
| M2 Communication & Standards | ⚠️ NEEDS UPDATE | N/A | N/A | 24 action types (was 25: -coup_attempt, -lead_protest, +change_leader). 2 new contracts (CHANGE_LEADER, COLUMBIA_ELECTIONS). 3 contracts archived (COUP, MASS_PROTEST, old ELECTIONS). Agreement types: 5. Relation types: 5. |
| M3 Data Foundation | ⚠️ NEEDS UPDATE | N/A | N/A | 55+ tables. Template/Run hierarchy (scenario level removed). Deprecated fields: political_support, personal_coins, dem_rep_split. New tables: role_actions, role_relationships. New columns: position_type, confidential_brief, country_brief, party. |
| M10.1 Auth | ✅ DONE | ✅ | ✅ | Email/password + Google OAuth, RLS, GDPR consent, moderator approval flow. |
| M9 Sim Setup | ⚠️ Phase A+B DONE, polish in progress | ✅ | ✅ | Dashboard, SimRun wizard, User Mgmt, AI Setup, 10-tab Template Editor, 41 roles (5 types), 724 action assignments, 20 country briefs, 40 role briefs. Simplification A-E complete. |
| M4 Sim Runner | ⚠️ PARTIAL | — | — | Orchestrator exists. Needs: change_leader voting flow, election voting flow, agreement auto-transitions, round flow with new mechanics. |
| M8 Public Screen | ⚠️ ~40% | — | — | Hex map + basic dashboards |
| M6 Human Interface | ❌ NOT STARTED | — | — | Week 3-5 |
| M5 AI Participant | ⚠️ PARTIAL | — | — | Single-agent loop works, no conversations |
| M7 Navigator | ❌ NOT STARTED | — | — | Week 5-6 |
| M10 Final Assembly | ❌ NOT STARTED | — | — | Week 6 |

## Simplification Sprint (2026-04-15) — ALL COMPLETE
- A. political_support → stability only ✅
- B. personal_coins deprecated ✅
- C. Relations: 5 types, 5 agreement types, auto-transitions ✅
- D. change_leader replaces coup/protest ✅
- E. Columbia elections: 9+bonus votes, simple majority ✅
