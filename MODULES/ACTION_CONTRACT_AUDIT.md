# Action Contract Audit — Gap Analysis
**Date:** 2026-04-16 | **Status:** DOCUMENTED — fixes scheduled per module

---

## Overview

The 33 canonical action types are routed through the dispatcher and reach their engines.
However, many actions use **simplified wiring** that doesn't match the full contract specifications.
The contracts (in `3 DETAILED DESIGN/CONTRACTS/`) specify validators, schemas, adjacency checks,
multi-step flows, and specific payload formats that are not yet enforced.

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

### ground_attack — SIMPLIFIED
**Contract:** `CONTRACT_GROUND_COMBAT.md` v1.0 (LOCKED)
**Current:** Loads ALL units at target hex, fights all defenders. No source hex, no unit selection, no adjacency check, no chain attacks.
**Contract requires:**
- Source hex → Target hex (adjacent, validated)
- Attacker selects specific unit_codes from source hex
- Adjacency validation (hex neighbors)
- Leave ≥1 unit on foreign hexes
- Chain attack logic (winner continues to next adjacent hex)
- Validator: `ground_combat_validator.py` (referenced in contract, may not exist)
**Fix when:** M6 (humans submit attacks) or M5 (AI generates attack decisions)
**Effort:** Medium — need validator + source/target flow + chain logic

### air_strike — SIMPLIFIED
**Current:** Loads all air units at hex, strikes all ground/naval defenders. Basic resolution.
**Missing:** Sortie mechanics, target selection, air superiority contest, proper hit probability.
**Fix when:** M5/M6

### naval_combat — NOT WIRED
**Current:** Passes unit counts but engine expects `unit_code` on attacker/defender dicts. Errors.
**Fix when:** M5/M6

### naval_bombardment, naval_blockade, launch_missile_conventional — STUB
**Current:** Returns "acknowledged" message. Engine functions exist but need Input objects with zone/country data.
**Fix when:** M5/M6

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

### move_units — STUB
**Current:** Returns acknowledged. Unit movement is an inter-round mechanic.
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

### declare_war — WORKING
**Current:** Unilateral action. Sets both directions of the relationship to `at_war` in the `relationships` table. Writes observatory event. No moderator confirmation needed.
**Roles:** diplomat, head_of_state (all countries)
**Location:** `action_dispatcher.py` → `_declare_war()`, `ParticipantDashboard.tsx` → `DeclareWarForm`
**Wired to:** relationships table (both directions), observatory_events

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

## Combat Theater Issue

**Problem:** All combat currently happens on global hex coordinates. But Eastern Ereb and Mashriq have detailed theater grids (10x10) where combat should be resolved at theater resolution, not global resolution.

**Current:** `_resolve_combat` in dispatcher loads units by `global_row/col`. Units in the Eastern Ereb theater all share the same few global hexes, so combat mixes all units in the region.

**Required:** Combat in theater regions should use `theater_row/theater_col`. The attacker specifies which theater they're fighting in and which theater hex they target.

**Fix when:** M5/M6 — when real combat decisions need theater-level precision.

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
| **Military** | ground_attack, air_strike, naval_combat, naval_bombardment, naval_blockade, launch_missile | Full contract: source→target hex, unit selection, adjacency, theater-level combat, chain attacks, validators |
| **Military: Movement** | move_units | Inter-round unit repositioning with adjacency validation |
| **Military: Nuclear** | nuclear_test, nuclear_launch_initiate, nuclear_authorize, nuclear_intercept | Already wired — M6 adds participant UI + testing |
| **Military: Other** | basing_rights, martial_law | Already working — M6 adds participant UI |
| **Economic** | set_budget, set_tariffs, set_sanctions, set_opec | Validation (ranges, allowed targets), submission UI, Phase B integration verified |
| **Economic: Transactions** | propose_transaction, accept_transaction | Full flow: propose → counterparty sees → accept/reject → asset transfer. Visibility (public/secret). |
| **Diplomatic** | propose_agreement, sign_agreement | Full flow: propose → signatories → sign → active. Visibility (public/secret). Terms enforcement. |
| **Diplomatic** | declare_war | Already working — M6 adds participant UI |
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

*This audit should be reviewed at the start of M6. It defines the scope of M6 as much as the UI does.*
