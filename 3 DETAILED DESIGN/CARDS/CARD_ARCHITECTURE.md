# CARD: ARCHITECTURE CONTRACTS

**Principle:** Every module is autonomous. Switchable without major refactoring. Standard communication via typed Pydantic models + Supabase tables.

---

## COORDINATE CONTRACT (hard, immutable)

Every unit on the map has a **global position.** Units on global hexes that link to a local theater map **also have local coordinates:**

| Field | When set | Meaning |
|---|---|---|
| `global_row`, `global_col` | **Always** (if unit is on map) | Position on the 10×20 global hex grid |
| `map_id` | Only if on a hex with local map linkage | Which local map: `"eastern_ereb"` \| `"mashriq"` |
| `theater_row`, `theater_col` | Only if `map_id` is set | Position on the 10×10 local hex grid |

### Rules

1. **Both are REAL positions, not derived.** The unit physically exists in both spaces simultaneously.
2. **Both are set/cleared together.** One function handles placement — never set global without theater (if linked) or vice versa. Source: `map_config.py` linkage matrix.
3. **Units on non-linked global hexes** have `global_row/col` only. `map_id`, `theater_row/col` are NULL.
4. **Units on linked global hexes** MUST have both global AND theater coordinates.
5. **Reserve/embarked units** have all coordinate fields NULL.

### Adjacency / Attack Validation

```
Can unit A reach target B?
  Check 1: adjacent in GLOBAL space (global_row/col)?  → valid
  Check 2: adjacent in LOCAL space (same map_id, theater_row/col)?  → valid
  EITHER passes → action proceeds on the passing space
```

Both checks always run. No need to choose "primary" space. This handles cross-map attacks naturally — a unit on a local map hex can attack a neighboring global hex because its global coords are adjacent.

### Grid dimensions

| Map | Rows | Cols | Notes |
|---|---|---|---|
| Global | 1–10 | 1–20 | Hex topology: pointy-top, odd-row offset |
| Eastern Ereb (local 1) | 1–10 | 1–10 | Linked to global hexes via `map_config.py` |
| Mashriq (local 2) | 1–10 | 1–10 | Linked to global hexes via `map_config.py` |
| Future local maps | 1–10 | 1–10 | Max 10×10 per local map |

### Linkage matrix

Canonical source: `engine/config/map_config.py` → `global_hex_for_theater_cell()` + `_THEATER_LINK_HEXES`

Example: Eastern Ereb theater cell (row 3, col 5, owner=sarmatia) → global hex (3, 12).

This matrix is **immutable per template version.** Changing it = new template version.

---

## MODULE MAP

```
┌──────────────────────────────────────────────────────────────────┐
│                    OBSERVATORY (test-interface/)                   │
│  server.py → HTTP API → observatory.js (vanilla JS + SVG)        │
│  Polls DB every 3s. Supabase Realtime for push updates.          │
└──────────────────┬───────────────────────────────────────────────┘
                   │ HTTP API
┌──────────────────▼───────────────────────────────────────────────┐
│               ROUND RUNNER (agents/full_round_runner.py)          │
│  20 agents in parallel (asyncio.Semaphore(10))                    │
│  Per round: agents → resolve → engine tick → snapshot             │
└─────┬────────────┬────────────┬──────────────────────────────────┘
      │            │            │
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────────────────────────────────┐
│  LEADER  │ │ RESOLVE  │ │         ENGINE TICK                   │
│  ROUND   │ │ ROUND    │ │    (engines/round_tick.py)            │
│          │ │          │ │                                        │
│ leader   │ │ combat   │ │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│ _round   │ │ movement │ │  │ECONOMIC │ │POLITICAL│ │  TECH  │ │
│ .py      │ │ R&D      │ │  │  .py    │ │  .py    │ │  .py   │ │
│          │ │ events   │ │  └─────────┘ └─────────┘ └────────┘ │
└────┬─────┘ └────┬─────┘ └──────────────────┬───────────────────┘
     │            │                           │
     ▼            ▼                           ▼
┌────────────────────────────────────────────────────────────────┐
│                    SUPABASE (DB layer)                          │
│  services/supabase.py — single client singleton                │
│                                                                  │
│  Tables:                                                         │
│  ├── agent_decisions      (agent commits per round)              │
│  ├── agent_memories       (persistent per-agent memory)          │
│  ├── unit_states_per_round   (unit snapshots)                    │
│  ├── country_states_per_round (country snapshots)                │
│  ├── global_state_per_round  (oil, stock, bond, gold)            │
│  ├── observatory_events      (activity feed)                     │
│  ├── observatory_combat_results (combat audit)                   │
│  ├── round_states            (round lifecycle)                   │
│  ├── countries               (structural base data)              │
│  ├── roles                   (40 character sheets)               │
│  ├── relationships           (bilateral state)                   │
│  ├── sim_scenarios           (scenario config)                   │
│  ├── sim_templates           (template with map + rules)         │
│  ├── layout_units            (unit placement layouts)            │
│  ├── sim_config              (methodology + prompt templates)    │
│  ├── blockades                 (zone blockade state)              │
│  └── global_state_per_round  (market data)                       │
└────────────────────────────────────────────────────────────────┘
     ▲
     │
┌────┴───────────────────────────────────────────────────────────┐
│                    LLM PROVIDER                                 │
│  services/llm_tools.py — dual provider tool-use adapter         │
│  services/llm.py — dual provider plain text                     │
│                                                                  │
│  Gemini 2.5 Flash (default) ↔ Anthropic Sonnet 4 (fallback)    │
│  Auto-failover on provider health. ENV: LLM_AGENT_PROVIDER     │
└────────────────────────────────────────────────────────────────┘
```

---

## MODULE CONTRACTS

### Leader Round (`agents/leader_round.py`)
| | |
|---|---|
| **Input** | `country_code` or `role_id`, `round_num`, `scenario_code` |
| **Output** | `dict` with committed action, tool calls, memory audit, cognitive snapshot |
| **Calls** | `llm_tools.call_tool_llm()`, `agents/tools.*` (domain tools), DB via tools |
| **Writes to** | `agent_decisions`, `agent_memories` |
| **Reads from** | `roles` (CSV), `countries` (CSV), DB via domain tools |
| **Stateless** | Yes — each call is independent |

### Resolve Round (`round_engine/resolve_round.py`)
| | |
|---|---|
| **Input** | `scenario_code`, `round_num` |
| **Output** | `dict` with decisions_processed, combats, events, narratives |
| **Reads from** | `agent_decisions`, `unit_states_per_round` (prev round), `country_states_per_round` (prev round) |
| **Writes to** | `unit_states_per_round` (new), `country_states_per_round` (new), `observatory_combat_results`, `observatory_events`, `round_states`, `sanctions` (state table), `tariffs` (state table), `blockades` (state table) |
| **Calls** | `round_engine/combat.*`, `round_engine/movement.*`, `round_engine/rd.*` |

### Engine Tick (`engines/round_tick.py`)
| | |
|---|---|
| **Input** | `scenario_code`, `round_num` |
| **Output** | `dict` with success, countries_updated, oil_price |
| **Reads from** | `countries` (base structural), `country_states_per_round` (current), `sanctions` (state table), `tariffs` (state table), `blockades` (state table), `relationships` (war state), `observatory_combat_results` (losses) |
| **Writes to** | `country_states_per_round` (updated GDP/stability/treasury), `global_state_per_round` (oil/stock) |
| **Calls** | `engines/economic.process_economy()`, `engines/political.calc_stability()`, `engines/political.calc_political_support()`, `engines/political.update_war_tiredness()` |
| **NEVER reads** | `agent_decisions` — engine is agnostic to decision source (human or AI) |

### Economic Engine (`engines/economic.py`)
| | |
|---|---|
| **Input** | `countries` dict, `world_state` dict, `actions` dict, `previous_states` dict |
| **Output** | `EconomicResult` (Pydantic) |
| **DB calls** | **NONE** — pure function |
| **Mutates** | `countries` dict in-place (GDP, treasury, inflation, debt) |

### Political Engine (`engines/political.py`)
| | |
|---|---|
| **Functions** | `calc_stability()`, `calc_political_support()`, `update_war_tiredness()`, `process_election()`, `check_revolution()`, `check_capitulation()` |
| **DB calls** | **NONE** — pure functions |
| **I/O** | Pydantic input → Pydantic result |

### Military Engine (`engines/military.py`)
| | |
|---|---|
| **Zone v1 (live)** | `resolve_attack()`, `resolve_air_strike()`, `resolve_naval_combat()`, `resolve_blockade()`, `resolve_covert_op()`, `resolve_assassination()`, `resolve_nuclear_test()` |
| **Unit v2 (reference)** | `resolve_ground_attack_units()`, `resolve_air_strike_units()`, `resolve_missile_strike_units()`, `resolve_naval_combat_units()`, `resolve_naval_bombardment_units()`, `resolve_nuclear_salvo_interception()` |
| **DB calls** | **NONE** — pure functions |

### LLM Tools (`services/llm_tools.py`)
| | |
|---|---|
| **Input** | `system` prompt, `messages`, `tools` (Anthropic-shape schemas), `use_case`, `provider_override` |
| **Output** | `ToolLLMResponse` with content blocks, stop_reason, usage |
| **Adapters** | Anthropic SDK (native) ↔ Gemini SDK (translated) |
| **Failover** | On error, tries opposite provider if configured + healthy |

---

## ENGINE STATE ISOLATION (2026-04-08)

**Architectural invariant:** The engine (round_tick.py + economic/political/military engines) NEVER reads from `agent_decisions`. It reads from **DB state tables** only.

```
CORRECT flow:
  Participant (human or AI) -> agent_decisions table
  resolve_round -> reads agent_decisions -> WRITES to state tables (sanctions, tariffs, relationships, etc.)
  round_tick -> reads state tables -> runs engines -> writes updated state

WRONG (eliminated 2026-04-08):
  round_tick -> reads agent_decisions directly
```

**State tables the engine reads:**
| Table | What | Written by |
|---|---|---|
| `sanctions` | Bilateral sanction levels (imposer, target, level) | resolve_round (upsert on set_sanction/impose_sanction/lift_sanction) |
| `tariffs` | Bilateral tariff levels (imposer, target, level) | resolve_round (upsert on set_tariff/impose_tariff/lift_tariff) |
| `blockades` | Zone blockade state (zone, imposer, level, status) | resolve_round (upsert on declare_blockade/lift) |
| `relationships` | Bilateral diplomatic status (war/peace/allied) | resolve_round (on declare_war/ceasefire/etc.) |
| `country_states_per_round` | Per-country economic/political snapshot | round_tick (writes back after engine runs) |
| `global_state_per_round` | Oil price, stock index | round_tick (writes back after engine runs) |
| `observatory_combat_results` | Combat losses per round | resolve_round (combat resolution) |

**Why:** The engine must be agnostic to whether a human or AI made the decision. Starting data (36 sanctions, 29 tariffs loaded at SIM start) flows through the same path as mid-game changes. This enables the "unmanned spacecraft" to run identically whether participants are AI agents or humans.

---

## COMMUNICATION PATTERNS

### Agent ↔ DB
Via `agents/tools.py` helper functions. Each tool queries one table and returns a dict. Agent never touches Supabase client directly.

### Engine ↔ Engine
**No direct calls.** Round_tick.py mediates: loads state → calls economic → calls political → writes back. Engines receive dicts, return Pydantic models.

### Observatory ↔ Server
HTTP polling (GET every 3s). POST for controls (start/stop/pause/reset). JSON responses. No WebSocket yet (Supabase Realtime planned for push).

### Round Walkthrough (distilled from SEED_C7 + CON_E1)

A round represents ~6 months of geopolitical time. Two phases:

**PHASE A — Free Action & Negotiation (the heart of the SIM)**

Everyone acts simultaneously. No turn order. Real-time.

```
Leaders talk bilaterally (8-turn conversations)
  → form alliances, threaten, negotiate, trade
  → memory updated after each conversation

Covert ops executed (intelligence, sabotage, propaganda)
  → engine resolves immediately, results private to operator

Military actions declared (attacks, blockades, missile launches)
  → Live Action Engine resolves instantly: dice → casualties → map updated
  → Global alerts for nuclear launches (10 min real-time window)

Transactions proposed and executed (coins, units, tech, basing rights)
  → asset validation → both confirm → immediate transfer

Agreements drafted and signed (ceasefire, treaties, alliances)
  → engine enforces ceasefire/armistice, records all others

Public statements broadcast (war declarations, peace offers, threats)
  → visible to all immediately

Mandatory submissions due at end of Phase A:
  → Budget (social/military/tech allocation)
  → Tariff levels per country
  → Sanction levels per country
  → OPEC production (members only)
  → If not submitted: previous round settings carry forward
```

**PHASE B — Engine Processing (between rounds)**

Sequential, deterministic. No player input.

```
1. Movement / deployment phase (move_unit, deploy reserves, withdraw)
2. Martial law (if declared — one-off troop boost)
3. Military production (from budget allocation + production tiers)
4. Economic engine (23-step pipeline — see CARD_FORMULAS):
   Oil → Sanctions → Tariffs → GDP → Revenue → Budget → Production
   → Tech → Inflation → Debt → Economic state → Momentum → Contagion
   → Dollar credibility → Market indexes
5. Political engine:
   Stability → Political support → War tiredness → Threshold flags
6. Elections (if scheduled or triggered this round)
7. Revolution check (if stability ≤ 2)
8. Health events (elderly leaders)
9. Capitulation check
10. Snapshot: all state persisted to per-round tables
11. Observatory updated, next round begins
```

**Unmanned mode difference:** Phase A compressed (agents run in parallel, ~30-60s per agent instead of 45-80 min). Phase B identical.

### Round flow sequence (target architecture) — Updated 2026-04-08

```
ROUND N FLOW:

PHASE A — Free Actions (agents submit actions, conversations, transactions):
  ├── Bilateral conversations (initiate/accept/decline, 8-turn)
  ├── Public statements
  ├── Exchange transactions (propose/accept/counter)
  ├── Agreements (propose/sign)
  ├── Covert operations (intelligence, sabotage, propaganda, election meddling)
  ├── Domestic political actions (arrest, fire, coup — AUTOMATIC execution in unmanned mode)
  ├── Military actions (attack, air strike, missile launch, blockade, bombardment)
  ├── All resolved immediately by engine, results visible in Observatory
  │
  └── Mandatory decision prompt: ~2 min before deadline
      → Agents MUST submit: budget, sanctions, tariffs, OPEC before round closes
      → Default: previous round values if not submitted
      → In unmanned mode: agent explicitly prompted to submit before committing other actions

PHASE B — Batch Processing (between rounds):
  1. Budget submissions processed (mandatory, status quo if not submitted)
  2. Tariff/sanction/OPEC changes applied
  3. Martial law (if declared)
  4. Engine tick:
     ├── Economic engine (oil → GDP → revenue → budget → production → inflation → debt → state)
     ├── Political engine (stability → support → war tiredness → threshold flags)
     ├── Technology engine (R&D advancement)
     ├── Elections (if scheduled or triggered this round)
     ├── Revolution check (if stability ≤ 2)
     ├── Health events (elderly leaders)
     └── Capitulation check
  5. Snapshot: unit_states, country_states, global_state persisted
  6. Observatory updated

INTER-ROUND PHASE — Relocation (added 2026-04-08):
  → Responsible actors: military chiefs (multi-role) or HoS (20-role mode)
  → Deploy/redeploy troops (move_unit, deploy from reserve, withdraw)
  → Strategic repositioning — separate from in-round tactical actions
  → Processed BEFORE next round's engine tick begins

ROUND N+1 begins...
```

### Current implementation (simplified)

```
1. full_round_runner.run_full_round(scenario, round_num)
2.   ├── 20× _run_one_agent() in parallel → leader_round.run_leader_round()
3.   │     └── LLM tool-use loop → commit_action → agent_decisions table
4.   ├── _try_resolve_round() → resolve_round.resolve_round()
5.   │     └── combat/movement/R&D → unit_states + country_states + events
6.   └── _try_engine_tick() → round_tick.run_engine_tick()
7.         └── economic + political engines → updated country_states + global_state
```

Gap: steps 1-7 above are batch-only. Active loop (conversations, real-time actions) not yet wired.

### Testing Architecture

```
app/tests/
├── layer1/              ← Pure function tests (no DB, no LLM)
│   ├── test_combat.py   ← ground dice, air strike %, missile %, chain, trophies
│   ├── test_economic.py ← GDP, oil, sanctions, tariffs, budget, inflation
│   ├── test_political.py ← stability, support, coups, elections
│   └── test_technology.py ← R&D, rare earth, tech transfer
├── layer2/              ← Integration tests (DB, no LLM)
│   ├── test_resolve_round.py  ← decisions → combat → snapshots
│   ├── test_engine_tick.py    ← country_states mutated correctly
│   └── test_transactions.py   ← exchange execution, agreement recording
└── layer3/              ← Smoke tests (1 LLM call)
    └── test_single_agent.py   ← one agent commits on Gemini
```

Run: `cd app && PYTHONPATH=. pytest tests/layer1/ -v` (seconds, free)
Run: `cd app && PYTHONPATH=. pytest tests/layer2/ -v` (seconds, DB only)

### Moderator actions in unmanned mode

Actions that require moderator confirmation in human play (arrest, assassination, coup, protest) are **executed automatically** in unmanned mode. The engine validates conditions and resolves — no human moderator needed. NOUS judgment layer (when wired) can provide the "moderator reasoning" for these actions.

---

## DB SCHEMA (key tables)

### agent_decisions
```sql
id uuid PK, scenario_id FK, country_code text, action_type text,
action_payload jsonb, rationale text, validation_status text,
validation_notes text, round_num int, created_at timestamptz
```

### unit_states_per_round
```sql
id uuid PK, scenario_id FK, round_num int, unit_code text,
country_code text, unit_type text, global_row int, global_col int,
map_id text,          -- NULL if global-only; 'eastern_ereb' | 'mashriq' if on local map
theater_row int,      -- local map row (NULL if global-only)
theater_col int,      -- local map col (NULL if global-only)
embarked_on text, status text, notes text, created_at timestamptz
UNIQUE(scenario_id, round_num, unit_code)
```

### country_states_per_round
```sql
id uuid PK, scenario_id FK, round_num int, country_code text,
gdp numeric, treasury numeric, inflation numeric, stability int,
political_support int, war_tiredness int, nuclear_level int,
nuclear_rd_progress int, nuclear_confirmed bool,  -- test passed for this level?
ai_level int, ai_rd_progress int,
created_at timestamptz
UNIQUE(scenario_id, round_num, country_code)
```

### global_state_per_round
```sql
id uuid PK, scenario_id FK, round_num int,
oil_price numeric, stock_index numeric,
notes text, created_at timestamptz
UNIQUE(scenario_id, round_num)
-- NOTE: bond_yield and gold_price removed (Marat 2026-04-08 — not part of SIM)
```

### relationships (bilateral state — updated 2026-04-08)
```sql
id uuid PK, sim_run_id FK,
from_country_id text, to_country_id text,
relationship text,  -- alliance | close_ally | friendly | neutral | tense | hostile | at_war | strategic_rival
status text,        -- allied | friendly | neutral | tense | hostile | military_conflict | armistice | peace
basing_rights_a_to_b bool,  -- from_country (a) HOSTS bases of to_country (b)
basing_rights_b_to_a bool,  -- to_country (b) HOSTS bases of from_country (a)
dynamic text,       -- narrative description
UNIQUE(sim_run_id, from_country_id, to_country_id)
```

**Dual-column semantics (2026-04-08):**
- `relationship` = STARTING/REFERENCE value (frozen per template, legacy labels from CSV)
- `status` = LIVE engine state (canonical 8-state model, updated during play)
- Engine reads `status` for all war/peace checks, never `relationship`

**8-state model for `status`:**
`allied` → `friendly` → `neutral` → `tense` → `hostile` → `military_conflict` → `armistice` → `peace`
- `military_conflict` is STICKY — only exits via signed armistice or peace treaty
- Armistice breach (attack after signing) → auto-return to `military_conflict` + all countries notified

**Starting basing rights (12 records):** Columbia hosted in 9 allied countries (Yamato, Hanguk, Teutonia, Albion, Phrygia, Formosa, Mirage, Ponte, Freeland). Sarmatia-Choson mutual. Gallia in Mirage.

### agreements
```sql
id uuid PK, scenario_id FK, round_num int,
agreement_name text, agreement_type text,
signatories text[],   -- list of country codes
visibility text,      -- 'public' | 'secret'
terms text,           -- free text
status text,          -- 'active' | 'breached' | 'expired'
created_at timestamptz
```

### exchange_transactions
```sql
id uuid PK, scenario_id FK, round_num int,
proposer text, counterpart text,  -- country or role
offer jsonb,     -- {coins: N, units: [...], basing_to: [...], tech: [...]}
request jsonb,   -- same structure
status text,     -- 'proposed' | 'accepted' | 'declined' | 'countered'
executed_at timestamptz
```

### covert_ops_log
```sql
id uuid PK, scenario_id FK, round_num int,
operator_country text, operator_role text,
op_type text, target_country text,
success bool, detected bool, attributed bool,
effect jsonb, narrative text,
created_at timestamptz
```

### pre_seeded_meetings (Template data)
```sql
id uuid PK, template_id FK,
round_num int, meeting_type text,  -- 'bilateral' | 'org_meeting'
organization_code text,            -- NULL if bilateral
participants text[],               -- country codes or role IDs
agenda text, location text,
created_at timestamptz
```
