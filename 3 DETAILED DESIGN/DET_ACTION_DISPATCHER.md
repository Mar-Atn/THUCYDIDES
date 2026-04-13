# DET — Action Dispatcher (Routing Layer Spec)

**Version:** 1.0 | **Status:** Active | **Date:** 2026-04-13
**Source:** `app/engine/services/action_dispatcher.py`, `app/engine/agents/action_schemas.py`
**Related:** `PHASES/UNMANNED_SPACECRAFT/CONTRACT_ROUND_FLOW.md`, `CARD_ACTIONS.md`, `CARD_ARCHITECTURE.md`

---

## 1. PURPOSE

The Action Dispatcher is the central routing layer that connects all participant actions (submitted by AI agents or human players) to their engine implementations. Every action flows through a single entry point — `dispatch_action()` — which:

1. Receives a validated action payload from `agent_decisions` (persisted by `commit_action`)
2. Routes to the correct engine function based on `action_type`
3. Returns a standardized result `{success: bool, narrative: str}`
4. Logs every dispatch to the Observatory audit trail

The dispatcher is **domain-agnostic glue** — it does not contain business logic. All resolution logic lives in the individual engine modules.

---

## 2. ARCHITECTURE

```
                          ┌─────────────────────┐
                          │  AI Agent / Human    │
                          │  (submits action)    │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  commit_action()     │  agents/tools.py
                          │  (Pydantic validate  │
                          │   + persist to DB)   │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  agent_decisions     │  Supabase table
                          │  (queue: unprocessed)│
                          └──────────┬──────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │  orchestrator                    │
                    │  _dispatch_phase_a_actions()     │  engines/orchestrator.py
                    │  (reads unprocessed rows,        │
                    │   calls dispatcher per action)   │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │  ACTION DISPATCHER               │
                    │  dispatch_action()               │  services/action_dispatcher.py
                    │  └─ _route()                     │
                    │     └─ engine function call      │
                    └────────────────┬────────────────┘
                                     │
              ┌──────────┬───────────┼───────────┬──────────┐
              ▼          ▼           ▼           ▼          ▼
          military   covert_ops  domestic   political  transactions
          engines    engines     engines    engines    engines
```

**Key files:**

| File | Role |
|------|------|
| `engine/agents/tools.py` | `commit_action()` — validates + persists to `agent_decisions` |
| `engine/agents/action_schemas.py` | 25 Pydantic models for action payloads |
| `engine/services/action_dispatcher.py` | `dispatch_action()` + `_route()` — central routing |
| `engine/engines/orchestrator.py` | `_dispatch_phase_a_actions()` — loads from DB + calls dispatcher |

---

## 3. ACTION ROUTING TABLE

All 25 action types with their Pydantic validator, engine target, and resolution timing.

### 3.1 Military Actions

| action_type | Pydantic Model | Engine File | Engine Function | Timing |
|---|---|---|---|---|
| `declare_attack` | `AttackDeclarationOrder` | `engines/military.py` | `resolve_ground_combat`, `resolve_air_strike`, `resolve_naval_combat`, `resolve_naval_bombardment` (by `attack_type`) | Immediate |
| `launch_missile` | `MissileLaunchOrder` | `engines/military.py` | `resolve_missile_strike` | Immediate |
| `blockade` | `BlockadeOrder` | `engines/military.py` | `resolve_blockade` | Immediate |
| `basing_rights` | `BasingRightsOrder` | `services/basing_rights_engine.py` | `grant_basing_rights` / `revoke_basing_rights` (by `operation`) | Immediate |
| `martial_law` | `MartialLawOrder` | `services/martial_law_engine.py` | `execute_martial_law` | Immediate + Phase B effects |
| `nuclear_test` | `NuclearTestOrder` | `engines/military.py` | `resolve_nuclear_test` | Immediate |
| `move_units` | `MoveUnitsOrder` | `round_engine/resolve_round.py` | `_process_movement` | Inter-round |

### 3.2 Covert Operations

All covert ops are dispatched through `_dispatch_covert()` which sub-routes on `op_type`.

| action_type | Pydantic Model | Engine File | Engine Function | Timing |
|---|---|---|---|---|
| `covert_op` (intelligence) | `CovertOpOrder` | `services/intelligence_engine.py` | `generate_intelligence_report` | Immediate |
| `covert_op` (sabotage) | `CovertOpOrder` | `services/sabotage_engine.py` | `execute_sabotage` | Immediate |
| `covert_op` (propaganda) | `CovertOpOrder` | `services/propaganda_engine.py` | `execute_propaganda` | Immediate |
| `covert_op` (election_meddling) | `CovertOpOrder` | `services/election_meddling_engine.py` | `execute_election_meddling` | Immediate |

### 3.3 Domestic / Political Actions

| action_type | Pydantic Model | Engine File | Engine Function | Timing |
|---|---|---|---|---|
| `arrest` | `ArrestOrder` | `services/arrest_engine.py` | `request_arrest` | Immediate |
| `assassination` | `AssassinationOrder` | `services/assassination_engine.py` | `execute_assassination` | Immediate |
| `coup_attempt` | `CoupAttemptOrder` | `services/coup_engine.py` | `execute_coup` | Immediate |
| `lead_protest` | `LeadProtestOrder` | `services/protest_engine.py` | `execute_mass_protest` | Immediate |
| `reassign_powers` | `ReassignPowersOrder` | `services/power_assignments.py` | `reassign_power` | Immediate |
| `call_early_elections` | `CallEarlyElectionsOrder` | `services/early_elections_engine.py` | `execute_early_elections` | Immediate |
| `submit_nomination` | `SubmitNominationOrder` | `services/election_engine.py` | `submit_nomination` | Immediate |
| `cast_vote` | `CastVoteOrder` | `services/election_engine.py` | `cast_vote` | Immediate |

### 3.4 Transactions / Agreements

| action_type | Pydantic Model | Engine File | Engine Function | Timing |
|---|---|---|---|---|
| `propose_transaction` | `TransactionOrder` | `services/transaction_engine.py` | `propose_exchange` | Immediate (proposal) |
| `propose_agreement` | `TransactionOrder` | `services/agreement_engine.py` | `propose_agreement` | Immediate (proposal) |
| `respond_exchange` | `RespondExchangeOrder` | `services/transaction_engine.py` | `respond_to_exchange` | Immediate |
| `sign_agreement` | `SignAgreementOrder` | `services/agreement_engine.py` | `sign_agreement` | Immediate |

### 3.5 Economic / Regular Decisions

| action_type | Pydantic Model | Engine File | Engine Function | Timing |
|---|---|---|---|---|
| `set_sanction` | `SanctionOrder` | `engines/orchestrator.py` | `_apply_sanctions` | Batch (Phase B Step 0) |
| `set_tariff` | `TariffOrder` | `engines/orchestrator.py` | `_apply_tariffs` | Batch (Phase B Step 0) |

### 3.6 Communications

| action_type | Pydantic Model | Engine File | Engine Function | Timing |
|---|---|---|---|---|
| `public_statement` | `PublicStatementOrder` | `services/action_dispatcher.py` | `_log_public_statement` (no engine, Observatory only) | Immediate |
| `call_org_meeting` | `OrgMeetingOrder` | — | Not yet wired | — |

### 3.7 Technology

| action_type | Pydantic Model | Engine File | Engine Function | Timing |
|---|---|---|---|---|
| `rd_investment` | `RDInvestmentOrder` | — | Not yet wired (processed in Phase B tech engine) | Batch |

---

## 4. DISPATCH CATEGORIES

Three dispatch categories correspond to the three phases of a round (see CONTRACT_ROUND_FLOW.md Section 2).

### 4.1 IMMEDIATE_DISPATCH (Phase A Free Actions)

Dispatched by `_dispatch_phase_a_actions()` in the orchestrator. These resolve as soon as submitted. The orchestrator reads all unprocessed rows from `agent_decisions` and sends each through `dispatch_action()`.

**Includes:** All military combat, covert ops, domestic/political actions, transaction proposals, public statements.

**Exclusion filter** in orchestrator (skipped during Phase A dispatch):
```python
BATCH_TYPES = {"set_budget", "set_sanction", "set_tariff", "set_opec", "move_units"}
```

Actions with `action_type` in `BATCH_TYPES` are left in the queue for later processing.

### 4.2 BATCH_DISPATCH (Phase B Regular Decisions)

Applied at the start of Phase B (Step 0) by the orchestrator's `_apply_actions()`. These are mandatory per-country decisions submitted once per round.

**Includes:** `set_budget`, `set_sanction`, `set_tariff`, `set_opec`

These are processed directly by orchestrator methods — they do not pass through `action_dispatcher.py` but are applied inline by the orchestrator before running the engine pipeline (Steps 1-19).

### 4.3 MOVEMENT_DISPATCH (Inter-Round Window)

Processed during the inter-round window (between Phase B of round N and Phase A of round N+1).

**Includes:** `move_units` only

Movement is submitted by agents/humans during a 5-10 minute window while Phase B processes. The orchestrator dispatches these to `resolve_round._process_movement`.

---

## 5. ACTION SCHEMAS

All 25 Pydantic v2 models defined in `engine/agents/action_schemas.py`. Every model includes `action_type` (Literal) and `rationale` (str).

| # | Model Class | action_type | Key Fields |
|---|---|---|---|
| 1 | `MoveUnitsOrder` | `move_units` | `decision` (change/no_change), `changes` (dict) |
| 2 | `AttackDeclarationOrder` | `declare_attack` | `attacker_unit_codes` (list[str]), `target_global_row/col`, `target_description` |
| 3 | `SanctionOrder` | `set_sanction` | `target_country`, `sanction_type`, `level` (-3..3) |
| 4 | `TariffOrder` | `set_tariff` | `target_country`, `level` (0..3) |
| 5 | `RDInvestmentOrder` | `rd_investment` | `domain` (nuclear/ai/strategic_missile), `amount` (float) |
| 6 | `PublicStatementOrder` | `public_statement` | `content` (str) |
| 7 | `OrgMeetingOrder` | `call_org_meeting` | `organization_code`, `agenda` |
| 8 | `CovertOpOrder` | `covert_op` | `op_type` (intelligence/sabotage/propaganda/election_meddling), `target_country`, `target_type`, `intent`, `question`, `content` |
| 9 | `TransactionOrder` | `propose_transaction` / `propose_agreement` | `counterpart_country`, `terms`, `offer` (dict), `request` (dict), `agreement_name`, `agreement_type`, `visibility` |
| 10 | `RespondExchangeOrder` | `respond_exchange` | `transaction_id`, `response` (accept/decline/counter), `counter_offer` |
| 11 | `SignAgreementOrder` | `sign_agreement` | `agreement_id` |
| 12 | `ArrestOrder` | `arrest` | `target_role` |
| 13 | `MartialLawOrder` | `martial_law` | (no extra fields — HoS only, once per SIM) |
| 14 | `AssassinationOrder` | `assassination` | `target_role`, `domestic` (bool) |
| 15 | `CoupAttemptOrder` | `coup_attempt` | `co_conspirator_role` |
| 16 | `LeadProtestOrder` | `lead_protest` | (no extra fields) |
| 17 | `ReassignPowersOrder` | `reassign_powers` | `power_type` (military/economic/foreign_affairs), `new_holder_role` |
| 18 | `CallEarlyElectionsOrder` | `call_early_elections` | (no extra fields — HoS only) |
| 19 | `SubmitNominationOrder` | `submit_nomination` | `election_type`, `election_round` |
| 20 | `CastVoteOrder` | `cast_vote` | `election_type`, `candidate_role_id` |
| 21 | `BasingRightsOrder` | `basing_rights` | `operation` (grant/revoke), `guest_country`, `zone_id` |
| 22 | `BlockadeOrder` | `blockade` | `zone_id`, `imposer_units` (list[str]) |
| 23 | `MissileLaunchOrder` | `launch_missile` | `launcher_unit_code`, `target_global_row/col` |
| 24 | `NuclearTestOrder` | `nuclear_test` | (no extra fields) |

The discriminated union `AnyAction` and lookup dict `ACTION_TYPE_TO_MODEL` provide runtime validation and dispatch support. Note: `TransactionOrder` serves double duty for both `propose_transaction` and `propose_agreement` via a Literal union on `action_type`.

---

## 6. VALIDATION PIPELINE

The full lifecycle of an action from submission to resolution:

```
Step 1: Agent/human submits action dict
            │
Step 2: commit_action() in agents/tools.py
            ├─ Check action_type exists and is in ACTION_TYPE_TO_MODEL
            │  └─ REJECT if unknown → return {success: false, validation_status: "rejected"}
            ├─ Pydantic model_validate(action) against the matching schema
            │  └─ REJECT if schema fails → return validation error
            ├─ Light validations (unit ownership, coord bounds)
            │  └─ WARN only — action still commits with validation_status: "warned"
            ├─ Resolve sim_run_id from scenario_code
            │  └─ REJECT if scenario not found
            └─ INSERT into agent_decisions table
               {sim_run_id, scenario_id, country_code, action_type,
                action_payload, rationale, validation_status, round_num}
            │
Step 3: Orchestrator _dispatch_phase_a_actions()
            ├─ SELECT from agent_decisions WHERE processed_at IS NULL
            ├─ Skip BATCH_TYPES (set_budget, set_sanction, set_tariff, set_opec, move_units)
            └─ For each qualifying row:
                │
Step 4: dispatch_action(sim_run_id, round_num, payload)
            ├─ Extract action_type, role_id, country_code
            ├─ Call _route() to find engine function
            ├─ Engine resolves → returns {success, narrative, ...}
            ├─ _log_dispatch() writes to observatory_events
            └─ Return result to orchestrator
                │
Step 5: Orchestrator marks agent_decisions row as processed
            └─ UPDATE processed_at = now()
```

**Validation status values:**
- `"passed"` — clean commit, no issues
- `"warned"` — committed with warnings (e.g., unit ownership drift, coord out of bounds)
- `"rejected"` — not committed (unknown action_type, schema failure, missing scenario)

---

## 7. ERROR HANDLING

Two classes of errors with distinct handling:

### 7.1 Validation Rejects (commit_action level)

Occur before the action enters `agent_decisions`. The action is **not persisted**.

| Error | Cause | Return |
|---|---|---|
| Missing `action_type` | Payload has no `action_type` key | `{success: false, validation_status: "rejected", validation_notes: "missing 'action_type'"}` |
| Unknown `action_type` | Not in `ACTION_TYPE_TO_MODEL` | `{success: false, validation_status: "rejected", validation_notes: "unknown action_type '...'"}` |
| Schema validation failure | Pydantic `model_validate()` raises | `{success: false, validation_status: "rejected", validation_notes: "schema validation failed: ..."}` |
| Scenario not found | `resolve_sim_run_id()` raises ValueError | `{success: false, validation_status: "rejected", validation_notes: "Cannot resolve '...'"}` |

### 7.2 Engine Errors (dispatch level)

Occur after the action is persisted in `agent_decisions` but the engine raises during resolution.

| Error | Cause | Return |
|---|---|---|
| Engine exception | Any unhandled exception in engine code | `{success: false, narrative: "Engine error: ..."}` |
| Unknown action_type in router | `_route()` falls through all branches | `{success: false, narrative: "Unknown action_type: ..."}` |
| Unknown sub-type | e.g., unknown `attack_type` or `op_type` | `{success: false, narrative: "Unknown attack_type: ..." / "Unknown op_type: ..."}` |

All engine errors are caught by the `try/except` in `dispatch_action()` and logged via `logger.exception()`. The action remains in `agent_decisions` and is marked as processed regardless of success/failure.

---

## 8. ORCHESTRATOR INTEGRATION

### 8.1 _dispatch_phase_a_actions()

Located in `engines/orchestrator.py`. Called once per round during the transition from Phase A to Phase B.

**Flow:**

1. **Query** `agent_decisions` for all rows matching `sim_run_id` + `round_num` where `processed_at IS NULL`
2. **Filter** — skip any `action_type` in `BATCH_TYPES` (`set_budget`, `set_sanction`, `set_tariff`, `set_opec`, `move_units`)
3. **Dispatch** each qualifying action through `action_dispatcher.dispatch_action()`
4. **Mark** each row as processed (`UPDATE processed_at = now()`)
5. **Return** list of result dicts to the orchestrator log

### 8.2 Phase B Regular Decisions

Budget, sanctions, tariffs, and OPEC decisions are processed by the orchestrator's `_apply_actions()` method at Step 0 of Phase B. These bypass the action dispatcher — they are read directly from the decisions data structure and applied inline to `world_state`.

### 8.3 Inter-Round Movement

Movement orders (`move_units`) are processed in the inter-round window. The orchestrator calls `resolve_round._process_movement` for each pending movement batch.

### 8.4 Round Lifecycle Summary

```
Phase A:  Agents submit actions → commit_action() → agent_decisions table
          Orchestrator calls _dispatch_phase_a_actions() → immediate resolution
Phase B:  Orchestrator reads regular decisions → _apply_actions() → engine pipeline
          Steps 1-19 execute sequentially (no participant input)
Inter:    Orchestrator processes move_units from agent_decisions
```

---

## 9. CROSS-REFERENCES

| Document | Relevance |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_ROUND_FLOW.md` | Canonical round flow — Phase A / B / Inter-Round definitions, dispatch table (Section 4) |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` | All 25+ action types with domain groupings and game-design intent |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ARCHITECTURE.md` | System architecture — where dispatcher fits in the module graph |
| `3 DETAILED DESIGN/DET_F5_ENGINE_API.md` | Engine API contracts — how orchestrator calls engines |
| `3 DETAILED DESIGN/DET_C1_SYSTEM_CONTRACTS.md` | Inter-module communication contracts |
| `app/engine/services/action_dispatcher.py` | Implementation — central routing code |
| `app/engine/agents/action_schemas.py` | Implementation — 25 Pydantic action models |
| `app/engine/agents/tools.py` | Implementation — `commit_action()` validation + persistence |
| `app/engine/engines/orchestrator.py` | Implementation — `_dispatch_phase_a_actions()` + round orchestration |
