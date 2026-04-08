# ARCHITECTURE AUDIT: Communication Layer Compliance

**Date:** 2026-04-08
**Auditor:** LEAD Agent
**Mandate:** ALL data exchanges between modules MUST go via a SINGLE COMMUNICATION LAYER (DB state tables + typed contracts). No exceptions.
**Files audited:** 11 core modules, every DB read/write catalogued.

---

## 1. EXECUTIVE SUMMARY

| Metric | Count |
|--------|-------|
| **Files audited** | 11 |
| **Total DB reads catalogued** | 47 |
| **Total DB writes catalogued** | 18 |
| **CRITICAL violations** | 3 (1 fixed: V-7) |
| **MEDIUM violations** | 5 (1 fixed: V-1) |
| **LOW violations** | 4 |
| **Missing state tables** | 2 (1 fixed: blockades) |
| **Missing contracts** | 6 |

**Overall assessment: The CORE data flow (Agent -> agent_decisions -> resolve_round -> state tables -> engine tick -> state tables) is CORRECTLY wired.** The 2026-04-08 architecture work on `round_tick.py` and `resolve_round.py` successfully separated the engine from agent_decisions. However, there are significant violations in peripheral paths (blockade state, agent tools reading stale template data instead of live state, observatory reading agent_decisions directly for blockades, and full_round_runner querying agent_decisions for current economic state).

### Severity Definitions

- **CRITICAL**: Module directly bypasses the communication layer; engine reads agent internals or vice versa. Must fix before next run.
- **MEDIUM**: Data path is semi-correct but uses wrong source (e.g., CSV/template instead of live DB state). Creates stale/incorrect data. Fix within current sprint.
- **LOW**: Architectural smell; works now but will break at scale or when humans join. Fix in next sprint.

---

## 2. PER-FILE AUDIT

### FILE 1: `app/engine/engines/round_tick.py`
**MODULE:** Engine Tick Orchestrator

**DB READS:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `sim_scenarios` | id | Resolve scenario code to UUID | NO |
| `country_states_per_round` | * | Load per-round economic/political state | NO |
| `countries` | * | Load structural base data (immutable) | NO |
| `sanctions` | imposer_country_id, target_country_id, level | Sanctions state for engine input | NO |
| `tariffs` | imposer_country_id, target_country_id, level | Tariff state for engine input | NO |
| `blockades` | zone_id, imposer_country_id, level, status | Blockade state | ~~**MEDIUM** (V-1)~~ **FIXED 2026-04-08** |
| `country_states_per_round` | budget columns | Budget allocations | NO |
| `country_states_per_round` | opec_production | OPEC production level | NO |
| `relationships` | country_a, country_b, status | War state | NO |
| `observatory_combat_results` | attacker/defender countries + losses | Combat losses | NO |

**DB WRITES:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `country_states_per_round` | gdp, treasury, inflation, stability, political_support, war_tiredness | Engine output | NO |
| `global_state_per_round` | oil_price, stock_index | Global economic output | NO |

**CROSS-MODULE IMPORTS:**
- `engine.engines.economic.process_economy` — OK (pure engine function)
- `engine.engines.political.*` — OK (pure engine functions)
- `engine.config.settings.Settings` — OK (config)

**VERDICT:** Mostly clean. One medium violation (V-1: blockade state from observatory_events).

---

### FILE 2: `app/engine/round_engine/resolve_round.py`
**MODULE:** Round Resolver

**DB READS:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `sim_scenarios` | id | Resolve scenario code | NO |
| `unit_states_per_round` | * | Load unit positions for combat | NO |
| `country_states_per_round` | * | Load country state for modifications | NO |
| `agent_decisions` | * | Load committed decisions for this round | NO (this is the CORRECT entry point) |

**DB WRITES:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `round_states` | status | Mark round resolving/completed | NO |
| `sanctions` | imposer_country_id, target_country_id, level, notes | Upsert sanction state from decisions | NO |
| `tariffs` | imposer_country_id, target_country_id, level, notes | Upsert tariff state from decisions | NO |
| `agreements` | scenario_id, round_num, agreement_name, etc. | Insert proposed agreements | NO |
| `relationships` | basing_rights_a_to_b | Update basing rights | NO |
| `unit_states_per_round` | * | Write new unit snapshot | NO |
| `country_states_per_round` | * | Write new country snapshot | NO |
| `observatory_combat_results` | * | Write combat results | NO |
| `observatory_events` | * | Write all events | NO |
| `exchange_transactions` | * | Write exchange proposals | NO |

**CROSS-MODULE IMPORTS:**
- `engine.round_engine.combat` — OK (sub-module)
- `engine.round_engine.movement` — OK (sub-module)
- `engine.round_engine.rd` — OK (sub-module)
- `engine.agents.tools` (line 446-458) — **LOW** (V-8: resolve_round calls agent_tools.read_memory/write_memory for intelligence reports)

**VERDICT:** This module is the CORRECT bridge: it reads agent_decisions (the action log), processes them, and writes to state tables. The architecture comment on line 299-301 confirms intent. Intelligence report persistence via agent_tools is a minor coupling.

---

### FILE 3: `app/engine/agents/full_round_runner.py`
**MODULE:** AI Participant Module (orchestration)

**DB READS:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `sim_scenarios` | id | Resolve scenario code | NO |
| `observatory_events` | event_type, country_code, summary | Emit events | NO (write) |
| `agent_decisions` | action_payload, round_num | `_load_current_economic_state` — Load latest budget/tariff/sanction/OPEC for mandatory prompt | **CRITICAL** (V-2) |
| `country_states_per_round` | * | `_load_situation_context` — Load economic state | NO |
| `relationships` | from_country_id, to_country_id, status | Wars/alliances for context | NO |
| `agent_decisions` | country_code, action_payload | `_load_situation_context` line 304 — Sanctions received check | **CRITICAL** (V-3) |
| `observatory_events` | event_type, summary | Recent events for context | NO |

**DB WRITES:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `observatory_events` | event_type, country_code, summary, payload | Agent started/committed events | NO |

**CROSS-MODULE IMPORTS:**
- `engine.agents.leader_round.run_leader_round` — OK (same module boundary)
- `engine.agents.stage2_test.load_hos_agents` — OK (profile loading)

**VERDICT:** Two CRITICAL violations. `_load_current_economic_state` (line 244-260) reads from `agent_decisions` to build the mandatory economic decisions prompt. It should read from `sanctions`, `tariffs`, and `country_states_per_round` state tables instead. Similarly, `_load_situation_context` (line 304-313) reads sanctions from `agent_decisions` instead of the `sanctions` table.

---

### FILE 4: `app/engine/agents/leader_round.py`
**MODULE:** AI Participant Module (single-agent runner)

**DB READS:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `sim_scenarios` | id | Resolve scenario code (via _get_events) | NO |
| `observatory_events` | event_type, country_code, summary | Events affecting this country | NO |

**DB WRITES:** None directly (delegates to tools.py via dispatcher)

**CROSS-MODULE IMPORTS:**
- `engine.agents.tools` — OK (same module)
- `engine.agents.leader.LeaderAgent` — OK (same module)
- `engine.agents.stage3_test`, `stage4_test`, `stage5_test` — TOOL_SCHEMAS only, OK
- `engine.services.llm_tools` — OK (service layer)

**VERDICT:** Clean. This module correctly delegates all DB interactions to the tools layer.

---

### FILE 5: `app/engine/agents/tools.py`
**MODULE:** AI Participant Module (domain tools)

**DB READS:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `unit_layouts` | id | Resolve layout code | NO |
| `layout_units` | * | Get my forces / hex info / enemy forces | **MEDIUM** (V-4) |
| `sim_templates` | default_country_stats | Strategic context, relationships, orgs, econ state | **MEDIUM** (V-5) |
| `countries` | sim_name, gdp, treasury, etc. | Strategic context, economic state | NO (structural base data) |
| `sim_scenarios` | id | Memory operations | NO |
| `agent_memories` | content, round_num | Read/list/write agent memory | NO |

**DB WRITES:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `agent_decisions` | scenario_id, country_code, action_type, action_payload, round_num | Commit action | NO |
| `agent_memories` | content, round_num | Write/upsert memory | NO |

**CROSS-MODULE IMPORTS:**
- `engine.services.supabase` — OK
- `engine.config.map_config` — OK

**VERDICT:** Two MEDIUM violations:
- **V-4:** `get_my_forces`, `get_hex_info`, `get_enemy_forces` read from `layout_units` (the template/seed layout) rather than `unit_states_per_round` (live game state). Once combat/movement occurs, these tools return STALE positions. Agents make military decisions based on Round 0 unit positions.
- **V-5:** `get_strategic_context`, `get_economic_state`, `get_relationships`, `get_political_state`, `get_tech_state` all read from `sim_templates.default_country_stats` + `countries` table (structural/seed data) rather than `country_states_per_round` (live per-round state). GDP, treasury, inflation, stability shown to agents are ROUND 0 VALUES, not current round values.

---

### FILE 6: `app/engine/agents/world_context.py`
**MODULE:** AI Participant Module (Block 1 context builder)

**DB READS:** None from DB. Reads from CSV files:
| Source | Data | Purpose | Violation? |
|--------|------|---------|------------|
| `roles.csv` | All HoS roles | Participant roster | NO (Block 1 uses seed data by design) |
| `countries.csv` | All countries | Roster + starting situation | NO (but see V-6) |
| `relationships.csv` | Bilateral relationships | Tension display | NO (seed) |
| `sanctions.csv` | Starting sanctions | Situation display | **LOW** (V-6) |

**DB WRITES:** None

**CROSS-MODULE IMPORTS:**
- `engine.agents.map_context` — OK (same module)

**VERDICT:** This module builds Block 1 (RULES), which is stated as "NEVER updated during the SIM." Reading from CSV (seed data) is architecturally correct for Round 1 but becomes stale for subsequent rounds. V-6: `build_starting_situation` always shows "Current Situation (Round 1)" even in later rounds.

---

### FILE 7: `app/engine/agents/transactions.py`
**MODULE:** AI Participant Module (transaction system)

**DB READS:** None (operates on in-memory country dicts passed from caller)

**DB WRITES:** None directly (modifies in-memory dicts; caller persists)

**CROSS-MODULE IMPORTS:**
- `engine.services.llm` — OK
- `engine.agents.decisions._build_system_prompt, _parse_json` — OK (same module)

**VERDICT:** Clean. Pure in-memory operations. However, transaction execution (`execute_transaction`) mutates country dicts in-place without persisting to DB. The caller (full_round_runner or runner.py) is responsible for persistence. This is acceptable architecture but needs a note: **transactions must be persisted to `exchange_transactions` table by the caller.**

---

### FILE 8: `app/engine/agents/conversations.py`
**MODULE:** AI Participant Module (bilateral conversations)

**DB READS:** None (uses LeaderAgent cognitive blocks in-memory)

**DB WRITES:** None directly (updates LeaderAgent cognitive blocks in-memory)

**CROSS-MODULE IMPORTS:**
- `engine.services.llm` — OK

**VERDICT:** Clean. Pure LLM-driven conversation with in-memory cognitive state updates. No DB bypass.

---

### FILE 9: `app/engine/agents/decisions.py`
**MODULE:** AI Participant Module (decision functions)

**DB READS:** None (receives country/round_context dicts from caller)

**DB WRITES:** None (returns decision dicts to caller)

**CROSS-MODULE IMPORTS:**
- `engine.services.llm` — OK
- `engine.agents.map_context` — OK

**VERDICT:** Clean. Pure decision-making functions that receive data and return decisions. No DB access. This is exactly how decision modules should work.

---

### FILE 10: `app/engine/context/assembler.py`
**MODULE:** Context Assembly

**DB READS:** None directly (receives all data via constructor or `set_data()`)

**DB WRITES:** None

**CROSS-MODULE IMPORTS:**
- `engine.context.blocks` — OK (sub-module)

**VERDICT:** Clean. The assembler is a pass-through that builds text from pre-loaded data. It does not access the DB or any module internals. This is the correct architecture for context assembly.

`engine/context/blocks.py` also has no DB reads — it operates on data supplied by the assembler.

---

### FILE 11: `app/test-interface/server.py`
**MODULE:** Observatory

**DB READS:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| `round_states` | round_num, status | Observatory state | NO |
| `unit_states_per_round` | * | Units at round N | NO |
| `country_states_per_round` | * | Country states at round N | NO |
| `observatory_combat_results` | * | Combat log | NO |
| `global_state_per_round` | round_num, oil_price, etc. | Global series chart | NO |
| `observatory_events` | * | Event feed | NO |
| `blockades` | zone_id, imposer_country_id, level, status, established_round | Blockade display | ~~**CRITICAL** (V-7)~~ **FIXED 2026-04-08** |

**DB WRITES:**
| Table | Columns | Purpose | Violation? |
|-------|---------|---------|------------|
| (various via delegated calls) | | Observatory start triggers full_round_runner | NO (indirect) |

**CROSS-MODULE IMPORTS:**
- `engine.agents.leader.LeaderAgent` — OK (for test interface agent chat)
- `engine.agents.profiles` — OK
- `engine.agents.conversations.ConversationEngine` — OK
- `engine.agents.decisions` — OK (for test decision UI)
- `engine.agents.runner` — OK (for test sim runs)

**VERDICT:** One CRITICAL violation. `_observatory_blockades` (line 1138-1171) reads directly from `agent_decisions` table filtered by `action_type=declare_blockade`. This bypasses the communication layer — the Observatory should read from a `blockades` state table, not from agent_decisions.

---

## 3. VIOLATIONS LIST (Prioritized)

### CRITICAL (Must fix before next run)

**V-2: full_round_runner._load_current_economic_state reads agent_decisions**
- **File:** `app/engine/agents/full_round_runner.py`, lines 226-260
- **What:** Queries `agent_decisions` for latest set_budget, set_tariff, set_sanction, set_opec decisions
- **Why it matters:** The mandatory decisions prompt shows agents what their "current settings" are, but reads them from the action log instead of state tables. This means if resolve_round ever fails to process a decision, the agent still sees it as "current."
- **Fix:** Read current budgets from `country_states_per_round` (budget columns). Read current tariffs from `tariffs` table. Read current sanctions from `sanctions` table. Read OPEC from `country_states_per_round.opec_production`.

**V-3: full_round_runner._load_situation_context reads sanctions from agent_decisions**
- **File:** `app/engine/agents/full_round_runner.py`, lines 304-313
- **What:** Queries `agent_decisions` where `action_type=set_sanction` to find sanctions against a country
- **Why it matters:** Agent sees sanctions that may not have been processed. State table `sanctions` is the canonical source.
- **Fix:** Replace with query to `sanctions` table where `target_country_id=country_code`.

**~~V-7: Observatory._observatory_blockades reads agent_decisions~~ FIXED 2026-04-08**
- **File:** `app/test-interface/server.py`
- **Fix applied:** Created `blockades` state table. resolve_round upserts blockade state. Observatory reads from `blockades`. `_detect_formosa_blockade` also reads from `blockades`.

### MEDIUM (Fix within current sprint)

**~~V-1: round_tick reads blockade state from observatory_events~~ FIXED 2026-04-08**
- **File:** `app/engine/engines/round_tick.py`
- **Fix applied:** `_load_state_from_tables` now reads from `blockades` state table. `_detect_formosa_blockade` also reads from `blockades` table. No more observatory_events scanning for blockade state.

**V-4: Agent tools read unit positions from layout_units (seed), not unit_states_per_round (live)**
- **File:** `app/engine/agents/tools.py`, lines 70-269 (get_my_forces, get_hex_info, get_enemy_forces)
- **What:** All military situation tools query `layout_units` (the initial template layout) rather than `unit_states_per_round` (updated each round by resolve_round)
- **Why it matters:** After Round 1, agents see unit positions from the starting setup, not the current game state. Combat, movement, and mobilization effects are invisible to agents.
- **Fix:** Tools should query `unit_states_per_round` for the current round (falling back to `layout_units` if no round state exists). Requires passing scenario_id + round_num into the tools.

**V-5: Agent tools read country stats from templates/base tables, not live state**
- **File:** `app/engine/agents/tools.py`, lines 275-594 (get_strategic_context, get_economic_state, get_political_state, get_tech_state)
- **What:** These tools read from `sim_templates.default_country_stats` and `countries` table — both are seed/structural data that never change during a game
- **Why it matters:** Agents see Round 0 GDP, treasury, stability, etc. regardless of current round. Engine tick updates are invisible to agents. An agent whose country's GDP crashed from 280 to 200 still sees "GDP: 280."
- **Fix:** These tools should query `country_states_per_round` for the current round, falling back to base data. Requires passing scenario_id + round_num.

### LOW (Fix in next sprint)

**V-6: world_context.build_starting_situation always shows Round 1 data**
- **File:** `app/engine/agents/world_context.py`, lines 212-308
- **What:** Block 1 starting situation reads from CSV seed data (sanctions.csv, countries.csv), not live DB
- **Why it matters:** Block 1 is documented as "NEVER updated during the SIM" (per metacognitive architecture), so this is architecturally intentional. However, if the round_num is > 1, the heading still says "Current Situation (Round 1)" which is misleading.
- **Fix:** Change heading to "Starting Situation (as of game start)" or make it round-aware.

**V-8: resolve_round calls agent_tools for intelligence report memory persistence**
- **File:** `app/engine/round_engine/resolve_round.py`, lines 446-459
- **What:** The round resolver imports `engine.agents.tools` to call `read_memory` and `write_memory` for persisting intelligence reports
- **Why it matters:** This creates a back-channel where the resolver (Module 2) directly uses agent module (Module 1) code. The correct path is for resolve_round to write to `agent_memories` table directly or use a service function.
- **Fix:** Replace with direct DB write to `agent_memories` table, or extract memory persistence to a shared service in `engine/services/`.

**V-9: Observatory emits events during agent runs via full_round_runner**
- **File:** `app/engine/agents/full_round_runner.py`, `_emit_event` function
- **What:** The agent orchestrator writes to `observatory_events` as agents start/commit. This is technically the agent module writing to the display layer's table.
- **Why it matters:** Minor — observatory_events is a shared communication table by design. But the events are "agent_started" and "agent_committed" which are operational metadata, not game events.
- **Fix:** Consider a separate `agent_activity_log` table for operational events, keeping `observatory_events` for game-state events only.

**V-10: Covert ops in resolve_round mutate country_state dict without going through state tables**
- **File:** `app/engine/round_engine/resolve_round.py`, lines 460-490
- **What:** Sabotage reduces treasury, propaganda changes stability, election meddling changes political_support — all applied directly to the in-memory `country_state` dict which is then snapshot-written at the end of resolve_round.
- **Why it matters:** This is technically correct (the modified dict IS written to `country_states_per_round` via `_write_country_snapshot`), but the mutation happens outside the engine tick. The engine tick then reads this modified state and applies economic/political formulas on top. The order of operations matters: resolve_round snapshot write -> engine tick reads -> engine tick writes. If the engine tick runs before resolve_round completes, data is stale. Currently sequential, so OK.
- **Fix:** Document the ordering contract explicitly. No code change needed if ordering is guaranteed.

---

## 4. RECOMMENDED FIXES (Specific, Actionable)

### Fix 1: Create `blockades` state table (Fixes V-1, V-7)

```sql
CREATE TABLE blockades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id UUID NOT NULL REFERENCES sim_runs(id),
    zone_id TEXT NOT NULL,
    imposer_country_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',  -- active | lifted
    level TEXT DEFAULT 'full',              -- partial | full
    established_round INT NOT NULL,
    lifted_round INT,
    notes TEXT,
    UNIQUE(sim_run_id, zone_id, imposer_country_id)
);
```

**resolve_round:** Add blockade upsert (like sanctions/tariffs)
**round_tick:** Read from `blockades` table instead of `observatory_events`
**server.py:** Read from `blockades` table instead of `agent_decisions`

### Fix 2: Wire agent tools to live state (Fixes V-4, V-5)

Add `scenario_code` and `round_num` parameters to all domain tools. Each tool queries `country_states_per_round` / `unit_states_per_round` for the current round, falling back to seed data if no round state exists.

Implementation pattern:
```python
def get_my_forces(country_code, scenario_code="start_one", round_num=None, ...):
    if round_num:
        # Query unit_states_per_round for live positions
        ...
    else:
        # Fallback to layout_units (Round 0 seed)
        ...
```

Update `leader_round.py` `_build_tool_dispatcher` to pass `scenario_code` and `round_num` to all tool calls.

### Fix 3: Fix full_round_runner to read from state tables (Fixes V-2, V-3)

**`_load_current_economic_state`:** Replace `agent_decisions` queries with:
- Budget: `country_states_per_round` budget columns
- Tariffs: `tariffs` table where `imposer_country_id=country_code`
- Sanctions: `sanctions` table where `imposer_country_id=country_code`
- OPEC: `country_states_per_round.opec_production`

**`_load_situation_context`:** Replace sanctions-from-agent_decisions query (line 304) with:
```python
sanctions_on_me = client.table("sanctions").select("imposer_country_id, level") \
    .eq("target_country_id", country_code) \
    .gt("level", 0).execute()
```

### Fix 4: Extract memory persistence to service (Fixes V-8)

Move `read_memory` and `write_memory` from `agents/tools.py` to `services/memory.py`. Both tools.py and resolve_round.py import from the shared service. This removes the cross-module coupling.

---

## 5. MISSING STATE TABLES

| Table | Purpose | Currently stored in | Impact |
|-------|---------|-------------------|--------|
| ~~`blockades`~~ | ~~Current blockade state per zone~~ | ~~`observatory_events` (event log)~~ | **FIXED 2026-04-08** — `blockades` table created, resolve_round writes, round_tick + observatory read |
| `budgets` (or columns on country_states) | Current budget settings per country | `agent_decisions` (action log) OR `country_states_per_round` budget columns | Budget columns exist but may not be populated by resolve_round |

The `sanctions` and `tariffs` state tables already exist and are correctly maintained by resolve_round. `country_states_per_round` and `unit_states_per_round` are correctly used as the primary state tables.

---

## 6. MISSING CONTRACTS (Typed Interfaces)

| Contract | Between | Status |
|----------|---------|--------|
| **AgentDecision → ResolveRound** | Agent module → Round resolver | Partially defined. Pydantic models exist in tools.py for validation, but there is no formal contract type for the complete set of action types and their expected state-table effects. |
| **ResolveRound → StateTables** | Round resolver → State tables | Implicit. The resolver writes to sanctions, tariffs, unit_states, country_states, but there is no typed interface defining what resolve_round guarantees to produce. |
| **StateTables → EngineInput** | State tables → Engine tick | Defined in `_load_state_from_tables` return dict, but not as a Pydantic model. Should be a formal typed contract. |
| **EngineOutput → StateTables** | Engine tick → State tables | Implicit. The payload written to country_states_per_round is defined inline. Should be a Pydantic model. |
| **StateTables → AgentContext** | State tables → Agent tools | Missing entirely. Tools read seed data, not live state. When fixed, this needs a formal contract defining what data agents receive and from which tables. |
| **StateTables → Observatory** | State tables → Display layer | Partially defined. Observatory reads from correct tables (mostly), but blockade path bypasses. |

---

## 7. DATA FLOW DIAGRAM (Current State)

```
AI AGENT
  │
  ├─[commit_action]─────────────► agent_decisions (action log)
  │                                      │
  │                               resolve_round READS
  │                                      │
  │                               ┌──────┴──────────────────────┐
  │                               │  WRITES to state tables:    │
  │                               │  • sanctions ✅             │
  │                               │  • tariffs ✅               │
  │                               │  • unit_states_per_round ✅ │
  │                               │  • country_states_per_round✅│
  │                               │  • agreements ✅            │
  │                               │  • observatory_events ✅    │
  │                               │  • observatory_combat ✅    │
  │                               │  • relationships ✅         │
  │                               │  • blockades ✅              │
  │                               └──────┬──────────────────────┘
  │                                      │
  │                               round_tick READS state tables
  │                                      │
  │                               ┌──────┴──────────────────────┐
  │                               │  READS:                     │
  │                               │  • sanctions ✅             │
  │                               │  • tariffs ✅               │
  │                               │  • country_states ✅        │
  │                               │  • relationships ✅         │
  │                               │  • combat_results ✅        │
  │                               │  • blockades ✅              │
  │                               └──────┬──────────────────────┘
  │                                      │
  │                               WRITES updated state:
  │                               • country_states_per_round ✅
  │                               • global_state_per_round ✅
  │
  ├─[domain tools]──────────────► layout_units ⚠️ (should be unit_states)
  │                               sim_templates ⚠️ (should be country_states)
  │                               countries (base) ✅
  │
  ├─[memory tools]──────────────► agent_memories ✅
  │
  └─[mandatory decisions]───────► agent_decisions ❌ (should read state tables)

OBSERVATORY
  │
  ├─ country_states_per_round ✅
  ├─ unit_states_per_round ✅
  ├─ observatory_events ✅
  ├─ observatory_combat_results ✅
  ├─ global_state_per_round ✅
  └─ blockades ✅ (was agent_decisions, fixed 2026-04-08)
```

---

## 8. PRIORITY EXECUTION ORDER

1. ~~**Create `blockades` table + wire resolve_round + round_tick + observatory** (V-1, V-7) — 2 hours~~ **DONE 2026-04-08**
2. **Fix full_round_runner to read state tables** (V-2, V-3) — 1 hour
3. **Wire agent tools to live state** (V-4, V-5) — 3 hours (largest change, affects all tool functions)
4. **Extract memory service** (V-8) — 30 min
5. **Add typed contracts** (Pydantic models for state-table I/O) — 2 hours
6. **Fix world_context round label** (V-6) — 15 min

**Total estimated effort: ~9 hours**

---

*Audit complete. Every DB read and write in the 11 core files has been catalogued. The communication layer architecture is fundamentally sound — the core flow through state tables works. The violations are in peripheral paths (agent tools, mandatory decisions prompt, blockade state, observatory blockade display) that still use direct reads from agent_decisions or seed data instead of live state tables.*
