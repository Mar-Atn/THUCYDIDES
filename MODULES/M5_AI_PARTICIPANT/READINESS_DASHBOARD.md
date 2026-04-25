# M5 AI Participant — Readiness Dashboard

**Last updated:** 2026-04-25
**Goal:** Mixed human+AI simulation where AI participants use ALL available actions, communicate with humans and each other, and the system orchestrates everything reliably.

**Legend:** ✅ Proven working | 🔶 Partially tested / works with caveats | 🔴 Not tested / known gap | ➖ Not applicable

---

## 1. ACTION READINESS MATRIX (33 canonical actions)

Every action must work through: Schema validation → Dispatch → Engine → DB state change → Observable event

### Military — Combat (6)

| Action | Schema | Dispatch | Engine | AI Agent Used It | Human UI (M6) | E2E Plumbing Test | Real Agent Test |
|--------|:------:|:--------:|:------:|:----------------:|:--------------:|:-----------------:|:---------------:|
| `ground_attack` | ✅ | ✅ (field fix applied) | ✅ | ✅ Sarmatia | ✅ | ✅ L2 | ✅ Real session |
| `ground_move` | ✅ | ✅ (field fix applied) | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `air_strike` | ✅ | ✅ (field fix applied) | ✅ | ✅ Columbia, Sarmatia | ✅ | 🔶 L2 skip (no units) | ✅ Real session |
| `naval_combat` | ✅ | ✅ (field fix applied) | ✅ | 🔴 | ✅ | 🔶 L2 skip (no units) | 🔴 |
| `naval_bombardment` | ✅ | ✅ (field fix applied) | ✅ | ✅ Columbia | ✅ | 🔶 L2 skip (no units) | ✅ Real session |
| `launch_missile_conventional` | ✅ | ✅ (field fix applied) | ✅ | 🔴 | ✅ | 🔶 L2 skip (no units) | 🔴 |

### Military — Non-Combat (7+1)

| Action | Schema | Dispatch | Engine | AI Agent Used It | Human UI (M6) | E2E Plumbing | Real Agent |
|--------|:------:|:--------:|:------:|:----------------:|:--------------:|:------------:|:----------:|
| `move_units` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 (rejection) | 🔴 |
| `naval_blockade` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `basing_rights` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `martial_law` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `nuclear_test` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `nuclear_launch_initiate` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 (initiate only) | 🔴 |
| `nuclear_authorize` | ✅ | ✅ (UUID guard) | ✅ | 🔴 | ✅ | 🔶 L2 skip (no nukes) | 🔴 |
| `nuclear_intercept` | ✅ | ✅ (UUID guard) | ✅ | 🔴 | ✅ | 🔶 L2 skip (no nukes) | 🔴 |

### Economic — Batch (4, Phase B only)

| Action | Schema | Dispatch | Engine | AI Agent Used It | Human UI (M6) | E2E Plumbing | Real Agent |
|--------|:------:|:--------:|:------:|:----------------:|:--------------:|:------------:|:----------:|
| `set_budget` | ✅ | ✅ | ✅ | ✅ Solaria | ✅ | ✅ L2 + L3 lifecycle | ✅ Phase B session |
| `set_tariffs` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `set_sanctions` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `set_opec` | ✅ | ✅ | ✅ | ✅ Solaria | ✅ | ✅ L2 | ✅ Phase B session |

### Communication (3)

| Action | Schema | Dispatch | Engine | AI Agent Used It | Human UI (M6) | E2E Plumbing | Real Agent |
|--------|:------:|:--------:|:------:|:----------------:|:--------------:|:------------:|:----------:|
| `public_statement` | ✅ | ✅ | ✅ | ✅ All 5 countries | ✅ | ✅ L2 + L3 | ✅ |
| `invite_to_meet` | ✅ | ✅ (tool-routed) | ✅ | ✅ Phrygia | ✅ | ✅ L2 meetings | ✅ Real session |
| `call_org_meeting` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |

### Diplomatic (5)

| Action | Schema | Dispatch | Engine | AI Agent Used It | Human UI (M6) | E2E Plumbing | Real Agent |
|--------|:------:|:--------:|:------:|:----------------:|:--------------:|:------------:|:----------:|
| `declare_war` | ✅ | ✅ | ✅ | 🔴 (existing wars) | ✅ | ✅ L2 + L3 | 🔴 |
| `propose_agreement` | ✅ | ✅ (field fix) | ✅ | 🔴 | ✅ | ✅ L2 + L3 lifecycle | 🔴 |
| `sign_agreement` | ✅ | ✅ (UUID guard) | ✅ | 🔴 | ✅ | ✅ L2 + L3 lifecycle | 🔴 |
| `propose_transaction` | ✅ | ✅ (field fix) | ✅ | ✅ Columbia, Phrygia | ✅ | ✅ L2 + L3 lifecycle | ✅ AI-Human |
| `accept_transaction` | ✅ | ✅ (UUID guard) | ✅ | 🔴 (agent not prompted) | ✅ | ✅ L3 lifecycle | 🔶 AI-Human |

### Covert (2)

| Action | Schema | Dispatch | Engine | AI Agent Used It | Human UI (M6) | E2E Plumbing | Real Agent |
|--------|:------:|:--------:|:------:|:----------------:|:--------------:|:------------:|:----------:|
| `covert_operation` | ✅ | ✅ (param fix) | ✅ | ✅ Columbia, Sarmatia, Persia | ✅ | ✅ L2 (3 subtypes) | ✅ |
| `intelligence` | ✅ | ✅ (schema fix) | ✅ (LLM) | ✅ Columbia, Persia | ✅ | ✅ L2 | ✅ |

### Political (6)

| Action | Schema | Dispatch | Engine | AI Agent Used It | Human UI (M6) | E2E Plumbing | Real Agent |
|--------|:------:|:--------:|:------:|:----------------:|:--------------:|:------------:|:----------:|
| `arrest` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `assassination` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `change_leader` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `reassign_types` | ✅ | ✅ (field fix) | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `self_nominate` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |
| `cast_vote` | ✅ | ✅ | ✅ | 🔴 | ✅ | ✅ L2 | 🔴 |

---

## 2. CAPABILITY READINESS

| Capability | M5 (AI Agent) | M4 (Sim Runner) | M2 (Contracts) | M6 (Human UI) | E2E Verified |
|------------|:-------------:|:----------------:|:--------------:|:-------------:|:------------:|
| **Phase A immediate actions** | ✅ 9 types used | ✅ | ✅ | ✅ | ✅ |
| **Phase B batch decisions** | 🔶 1 agent tested | ✅ | ✅ | ✅ | 🔶 |
| **Phase B with 5+ agents** | 🔴 | ✅ | ✅ | ✅ | 🔴 |
| **Move units (inter-round)** | 🔴 | ✅ | ✅ | ✅ | 🔴 |
| **Round transition (A→B→R2)** | ✅ lifecycle test | ✅ | ✅ | ✅ | ✅ |
| **Multi-round (2+ rounds)** | 🔶 round 2 action works | ✅ | ✅ | ✅ | 🔶 |
| **AI-AI meeting** | 🔴 invitation not delivered | ✅ infra | ✅ | ➖ | 🔴 |
| **AI-Human meeting** | 🔴 never tested | ✅ infra | ✅ | ✅ | 🔴 |
| **Human-AI meeting** | 🔴 never tested | ✅ infra | ✅ | ✅ | 🔴 |
| **AI-AI transaction** | 🔶 scripted only | ✅ | ✅ | ➖ | 🔶 |
| **AI-Human transaction** | ✅ real session | ✅ | ✅ | ✅ | ✅ |
| **Combat → reaction chain** | 🔴 skip (units consumed) | ✅ | ✅ | ➖ | 🔴 |
| **Event delivery to agents** | ✅ dispatcher works | ✅ | ✅ | ➖ | ✅ |
| **Agent memory (write/read)** | ✅ | ➖ | ➖ | ➖ | ✅ |
| **Agent observation tools** | ✅ 6 tools verified | ✅ | ✅ | ✅ | ✅ |
| **Nuclear chain (full)** | 🔴 no capable test data | ✅ | ✅ | ✅ | 🔴 |
| **Assertiveness dial** | 🔴 not tested | ✅ config | ➖ | ➖ | 🔴 |
| **Theater map awareness** | 🔶 tools exist, not verified | ✅ | ➖ | ✅ | 🔴 |
| **Reserve deployment** | 🔴 | ✅ | ✅ | ✅ | 🔴 |
| **Freeze/resume agent** | 🔴 not tested | ✅ | ➖ | ✅ | 🔴 |

---

## 3. KNOWN BUGS / GAPS

| # | Issue | Severity | Module | Status |
|---|-------|----------|--------|--------|
| 1 | Meeting invitation not delivered to invitee agent | **CRITICAL** | M5 (tool_executor) | 🔴 Open |
| 2 | AI agents don't proactively find adjacent enemies for combat | MEDIUM | M5 (game_rules_context) | 🔴 Open |
| 3 | `_submit_action` doesn't pass `transaction_id`/`agreement_id` back to agent | LOW | M5 (tool_executor) | 🔶 Workaround (DB lookup) |
| 4 | `respond_to_invitation` doesn't check `expires_at` | LOW | M5 (tool_executor) | 🔶 Documented |
| 5 | Map units colored same color (missing `country_id` field) | LOW | M4 (main.py) | ✅ Fixed |

---

## 4. TEST INVENTORY

| Suite | File | Tests | Pass | Skip |
|-------|------|:-----:|:----:|:----:|
| Contract | test_action_contracts.py | 7 | 7 | 0 |
| L2 Single Agent | test_l2_single_agent.py | 15 | 15 | 0 |
| L2 Military Combat | test_l2_military_combat.py | 8 | 3 | 5 |
| L2 Military Non-Combat | test_l2_military_noncombat.py | 6 | 6 | 0 |
| L2 Nuclear Chain | test_l2_nuclear_chain.py | 5 | 2 | 3 |
| L2 Economic Batch | test_l2_economic_batch.py | 9 | 9 | 0 |
| L2 Political | test_l2_political.py | 6 | 6 | 0 |
| L2 Elections | test_l2_elections.py | 5 | 5 | 0 |
| L2 Meetings | test_l2_meetings.py | 9 | 9 | 0 |
| L2 Communication | test_l2_communication.py | 8 | 8 | 0 |
| L3 Multi-Agent | test_l3_multi_agent.py | 5 | 5 | 0 |
| L3 Phase B Lifecycle | test_l3_phase_b_lifecycle.py | 7 | 7 | 0 |
| L3 Real Single Agent | test_l3_real_single_agent.py | 5 | 5 | 0 |
| L3 Real Multi-Agent | test_l3_real_multi_agent.py | 3 | 1 | 2 |
| L3 Assessment | test_l3_assessment.py | 7 | 7 | 0 |
| **TOTAL** | | **105** | **95** | **10** |

---

## 5. BUGS FIXED (14 total across Sprints 1-3)

| # | Bug | Fix Location |
|---|-----|-------------|
| 1 | propose_transaction field mapping | action_dispatcher.py |
| 2 | propose_agreement field mapping | action_dispatcher.py |
| 3 | rd_investment stale action | action_schemas.py |
| 4 | UUID validation crashes | action_dispatcher.py |
| 5 | reassign_types field mapping | action_dispatcher.py |
| 6 | Return format missing success | action_dispatcher.py |
| 7 | _load_roles wrong sim | transaction_engine.py, agreement_engine.py |
| 8 | success field not boolean | action_dispatcher.py |
| 9 | Combat target field mapping | tool_executor.py |
| 10 | Missile launcher field mapping | tool_executor.py |
| 11 | Nuclear authorize→confirm | tool_executor.py |
| 12 | Intelligence parameter order | action_dispatcher.py |
| 13 | Covert ops parameter swap | action_dispatcher.py |
| 14 | Intelligence schema wrong model | action_schemas.py |

---

## 6. REAL AGENT SESSION RESULTS

**5 countries tested with real Claude managed agent sessions:**

| Country | Role | Actions Used | Session Cost |
|---------|------|-------------|:------------:|
| Sarmatia | Pathfinder | air_strike, covert_operation, ground_attack, public_statement | ~$0.10 |
| Columbia | Dealer | air_strike, covert_op, intelligence, naval_bombardment, propose_transaction, public_statement | ~$0.10 |
| Persia | Furnace | covert_operation, intelligence, public_statement | ~$0.10 |
| Solaria | Wellspring | set_budget, set_opec | ~$0.10 |
| Phrygia | Vizier | propose_transaction + meeting request | ~$0.10 |
| **Columbia (AI-Human)** | Dealer | Responded to human transaction proposal | ~$0.10 |

**Totals:** 35 submissions, 28 executed (80%), 9 distinct action types, 31 observatory events

---

## 7. NEXT PRIORITIES (Sprint 4)

1. 🔴 **Fix meeting invitation delivery** → unblocks AI-AI and AI-Human meetings
2. 🔴 **AI-AI meeting end-to-end** → ConversationRouter with 2 real agents
3. 🔴 **AI-Human meeting emulation** → real agent + ToolExecutor human
4. 🔴 **Phase B with 5 agents + humans** → full lifecycle graduation test
5. 🔶 **Military AI enhancement** → game rules context for combat planning
6. 🔶 **Combat reaction chain** → attack → event → ally reacts
7. 🔴 **Reserve deployment** → agents learn to use reserves
8. 🔴 **Nuclear chain with real agents** → using Sarmatia/Columbia (L3 capable)
