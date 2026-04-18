# Action Contract Audit — Gap Analysis
**Date:** 2026-04-18 | **Status:** ACTIVE — territory occupation + unit capture landed 2026-04-18

---

## Overview

The 33 canonical action types are routed through the dispatcher and reach their engines.
As of 2026-04-18, **all 5 combat types are fully wired** (engine → dispatcher → DB losses) with
a unified map-based Attack UX, theater-level adjacency, moderator controls, territory occupation
(`hex_control` table), and unit capture mechanics (CONTRACT_GROUND_COMBAT compliant).
Remaining gaps are primarily in validation strictness and non-combat action flows.

This document tracks the gap between current implementation and contract spec for each action.

---

## Gap Summary

### Severity Levels
- **WORKING**: Fully matches contract, tested
- **SIMPLIFIED**: Routes to engine but skips validation/contract details
- **STUB**: Acknowledged, no engine processing
- **NOT WIRED**: Engine exists but dispatcher doesn't call it correctly

---

## Military Actions

### ground_attack — WORKING (2026-04-18)
**Contract:** `CONTRACT_GROUND_COMBAT.md` v1.0 (LOCKED)
**Current:** Full map-based UX. Source hex → Target hex with BFS adjacency validation (`hex_range()`). Attacker selects specific units from source hex (max = min(3, count-1) — must leave 1 behind). RISK dice mechanics (1-3 units, iterative exchanges). DB losses applied. Moderator approval flow (or auto-attack bypass). Physical dice mode supported (3 atk + 2 def dice input). **Territory occupation:** `hex_control` upserted on victory (controlled_by = attacker). **Unit capture (CONTRACT §unattended):** on victory, surviving non-ground enemy units captured as trophies (country_id changed to attacker, status=reserve, position cleared; naval units excluded; type preserved). Map shows diagonal stripe overlay for occupied hexes (owner + occupier colors). Captured trophies shown as icons + "-> reserve" in combat results. **Modifier fix (2026-04-18):** Modifiers (AI L4, low morale, air support) were displayed in preview but NOT passed to engine — now computed before pending/immediate branch, stored in engine format, applied in both paths (pending confirm + immediate dispatch).
**Remaining gaps:** Chain attack logic not yet implemented.
**Effort:** Small — chain logic only

### air_strike — WORKING (2026-04-17)
**Current:** Map-based UX. Source hex air units selected (including embarked on carriers). 12%/6% hit probability. 15% chance downed by AD. DB losses applied. Probability-based (no dice input).
**Remaining gaps:** Sortie mechanics, air superiority contest.

### naval_combat — WORKING (2026-04-17)
**Current:** Map-based UX. 1v1 dice per pair, ties → defender wins. DB losses applied. Physical dice mode supported (1+1 dice input). Fixed: unit_code format (was count dict, now unit dict).

### naval_bombardment — WORKING (2026-04-17)
**Current:** 10% hit per naval unit. DB losses applied. Probability-based (no dice).

### launch_missile_conventional — WORKING (2026-04-17)
**Current:** 80% accuracy, AD halving, missile consumed on use. DB losses applied. Probability-based (no dice).

### naval_blockade — STUB
**Current:** Returns "acknowledged" message. Engine function exists but needs Input objects with zone/country data.
**Fix when:** M6 remaining sprints

### nuclear_test — NOT WIRED
**Current:** Engine expects `NuclearTestInput` Pydantic model. Dispatcher passes kwargs.
**Fix when:** M5 (AI agents may attempt nuclear tests)

### nuclear_authorize, nuclear_intercept, nuclear_launch_initiate — WIRED
**Current:** Connected to `NuclearChainOrchestrator`. Multi-step flow works.
**Status:** OK for M4 purposes. Full testing at M10.

### basing_rights — WORKING
**Current:** Routes to engine correctly.

### martial_law — WORKING
**Current:** Routes to engine correctly.

### ground_move — WORKING (2026-04-18)
**Current:** Ground advance to adjacent LAND hex. Sea hexes filtered via `GLOBAL_SEA_HEXES` + `THEATER_SEA_HEXES` frozensets + `is_sea_hex()` helper. Must leave 1 unit behind (max = min(3, count-1)). Authorized by `ground_attack` permission. 100% probability (always succeeds). Embarked units can land (disembark from carrier). `hex_control` upserted on advance. Undefended hex: non-ground enemies captured as trophies. `GLOBAL_HEX_OWNERS` (64 land hexes) + `hex_owner()` for canonical territory ownership.

### move_units — STUB
**Current:** Returns acknowledged. General unit movement is an inter-round mechanic (ground_move covers attack-phase advance).
**Fix when:** M4 Phase 4 was deferred. Implement when inter-round flow is tested.

---

## Economic Actions

### set_budget, set_tariffs, set_sanctions, set_opec — QUEUED
**Current:** Written to `agent_decisions` table. Phase B orchestrator collects and processes.
**Status:** Working for Phase B batch processing. No per-action validation.
**Fix when:** M6 (validate budget percentages, tariff levels, etc.)

### propose_transaction, accept_transaction — ROUTED
**Current:** Routes to transaction_engine. Engine has its own validation.
**Status:** Needs testing with real payloads.
**Fix when:** M5/M6

---

## Diplomatic Actions

### public_statement — WORKING
**Current:** Logs to observatory. No engine processing needed.

### propose_agreement, sign_agreement — ROUTED
**Current:** Routes to agreement_engine. Added `visibility` field (public/secret).
**Status:** Needs testing.
**Fix when:** M5/M6

### declare_war — WORKING (2026-04-17)
**Current:** Unilateral action. Sets both directions of the relationship to `at_war` in the `relationships` table. Writes observatory event. No moderator confirmation needed. Category: diplomatic.
**Roles:** diplomat, head_of_state (all countries)
**Location:** `action_dispatcher.py` → `_declare_war()`, `ParticipantDashboard.tsx` → `DeclareWarForm`
**Wired to:** relationships table (both directions), observatory_events
**Status:** Fully working, tested.

### call_org_meeting, meet_freely — STUB
**Current:** Returns acknowledged. Meeting system not built.
**Fix when:** M6 (humans need meetings) or M7 (Navigator facilitates)

---

## Covert Actions

### covert_operation — ROUTED
**Current:** Routes by `op_type` (sabotage, propaganda, election_meddling).
**Status:** Engines exist, need testing.
**Fix when:** M5 (AI agents do covert ops)

### intelligence — ROUTED
**Current:** Routes to intelligence_engine. Known format bug in `_section_events`.
**Fix when:** M5

---

## Political Actions

### arrest — ROUTED (requires confirmation)
**Current:** Routes to arrest_engine after moderator approval.
**Status:** Needs target role validation.

### assassination — ROUTED (requires confirmation)
**Current:** Routes to assassination_engine after moderator approval.
**Status:** Needs target validation, domestic/international check.

### change_leader — WORKING
**Current:** Full 3-phase voting flow (initiate → removal vote → election).
**Status:** Tested end-to-end.

### reassign_types — ROUTED
**Current:** Routes to power_assignments. Missing `round_num` param.
**Fix when:** M6

### self_nominate, cast_vote — ROUTED
**Current:** Routes to election_engine. Needs election context (type, round).
**Fix when:** M4 key events trigger elections → these become usable.

---

## Combat Theater Issue — RESOLVED (2026-04-17)

**Problem (was):** All combat happened on global hex coordinates. Theater grids (10x10) were ignored, mixing all units in a region.

**Solution:** `GET /api/sim/{id}/attack/valid-targets` accepts `theater=` parameter. When theater is specified, adjacency is computed in theater coordinates (`theater_row/theater_col`) on the 10x10 grid, not global. Map iframe sends theater context via postMessage. Theater view resolves coordinates correctly (was matching global coords instead of theater coords — bug fixed).

**Status:** Fully working for Eastern Ereb and Mashriq theaters. Global map combat also works.

---

## Reconciliation Schedule

### M6 (Human Participant Interface) — MAJOR ACTION WIRING SPRINT

M6 is not just "participant UI." It is the **full action pipeline integration** — every action
wired to contract spec, with submission interface, validation, engine resolution, outcome display,
and systematic testing. The human interface forces honesty: if a participant clicks "Attack," it
must work exactly per CONTRACT_GROUND_COMBAT.

**Scope: ALL 33 action types wired and tested during M6.**

| Category | Actions | What M6 delivers |
|---|---|---|
| **Military** | ground_attack, air_strike, naval_combat, naval_bombardment, ~~naval_blockade~~, launch_missile | ✅ **DONE (2026-04-18):** Unified Attack UX, source→target hex, unit selection, BFS adjacency, theater-level combat, moderator approval/auto-attack, dice mode. Territory occupation (`hex_control`). Unit capture (non-ground trophies). Ground movement (land-only, leave-1-behind). **Remaining:** chain attacks, naval_blockade |
| **Military: Movement** | move_units, ground_move | `ground_move` DONE (2026-04-18) — attack-phase advance. `move_units` inter-round repositioning still stub. |
| **Military: Nuclear** | nuclear_test, nuclear_launch_initiate, nuclear_authorize, nuclear_intercept | Already wired — M6 adds participant UI + testing |
| **Military: Other** | basing_rights, martial_law | Already working — M6 adds participant UI |
| **Economic** | set_budget, set_tariffs, set_sanctions, set_opec | Validation (ranges, allowed targets), submission UI, Phase B integration verified |
| **Economic: Transactions** | propose_transaction, accept_transaction | Full flow: propose → counterparty sees → accept/reject → asset transfer. Visibility (public/secret). |
| **Diplomatic** | propose_agreement, sign_agreement | Full flow: propose → signatories → sign → active. Visibility (public/secret). Terms enforcement. |
| **Diplomatic** | declare_war | ✅ **DONE (2026-04-17):** Unilateral, sets both directions at_war, DeclareWarForm in ParticipantDashboard |
| **Diplomatic** | public_statement, call_org_meeting, meet_freely | Statement UI, meeting creation, participant notification |
| **Covert** | covert_operation, intelligence | Op type selection, target country, detection probability, outcome display |
| **Political** | arrest, assassination, change_leader, reassign_types | Confirmation queue verified, 3-phase voting tested, target validation |
| **Political** | self_nominate, cast_vote | Election flow: nominations → voting → results. Integrated with key events. |

**Testing during M6:**
- Every action submitted through the participant UI
- Every validator enforced (adjacency, ownership, resources, permissions)
- Every engine result displayed correctly
- Every error case handled (insufficient units, wrong phase, unauthorized)
- Theater-level combat verified (Eastern Ereb, Mashriq)
- Transaction lifecycle (propose → accept → assets move)
- Agreement lifecycle (propose → sign → active → broken?)
- Covert ops (submit → probability → outcome → detected/undetected)

### M5 (AI Participant)
- AI agents use the same validated pipeline from M6
- Focus: generating proper contract-compliant payloads via LLM
- All 33 schemas tested with AI-generated decisions

### M10 (Final Assembly)
- Full sweep: every action, every edge case, stress test
- Mixed mode: 25 humans + AI agents playing simultaneously
- Performance: 33 concurrent action submissions
- Data integrity: verify all DB state changes are correct
- Error recovery: what happens when engine fails mid-action?

---

---

## Bugs Fixed (2026-04-17)

| Bug | Impact | Fix |
|---|---|---|
| Hex parity inverted (odd/even) | All adjacency calculations wrong | Fixed even rows (1-indexed) shifted right to match renderer |
| Attacker units loaded from wrong hex | Attacker got target's units | Load from source hex, not target hex |
| Naval combat wrong argument format | Errors on naval combat | Changed from count dict to unit dict |
| SIM_RUN_ID not defined in map listener | Map postMessage handler crashed | Passed SIM_RUN_ID into message listener scope |
| Theater view matched global coords | Unit selection failed in theater | Match theater_row/theater_col instead of global |
| Theater target highlighting wrong coords | Highlights on wrong hexes | Resolve theater coords correctly |
| Pending combat showed "DEFEAT" | Misleading UI | Show "ATTACK SUBMITTED — awaiting approval" for pending |
| Air/bombardment/missile required dice input | Unnecessary moderator friction | Only ground_attack and naval_combat use dice; others probability-based |

## Bugs Fixed (2026-04-18)

| Bug | Impact | Fix |
|---|---|---|
| `.in_()` used instead of `.in()` in JS | Runtime error in frontend filtering | Changed to `.in()` |
| Duplicate org memberships | Countries appeared twice in org lists | Fixed at template source data |
| ground_move had non-100% probability | Movement could randomly fail | Set to 100% probability (always succeeds) |
| Basing rights units treated as occupiers | Foreign allied units triggered occupation overlay | Added basing agreement check — basing units are NOT occupiers |
| Combat modifiers not passed to engine | AI L4, low morale, air support displayed in preview but ignored in resolution | Computed before pending/immediate branch, stored in engine format, applied in both paths |
| `body: dict = {}` never parsed as JSON | FastAPI treated dict default as query param — `/mode`, `/confirm` endpoints silently received empty body | All endpoints now use `Request.json()` |
| Pending action race condition | Realtime hook removed card mid-confirm, result never displayed | Keep resolved actions visible 30s, result stored on pending_action row |
| Restart simulation incomplete | Old sim state persisted after restart (stale hex_control, agreements, etc.) | Full reset: re-copy 11 tables + delete transient data; page reload clears frontend |

---

*This audit should be reviewed at the start of each M6 sprint. It defines the scope of M6 as much as the UI does.*
