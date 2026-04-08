# TTT Observatory — Spec v0.1

**Status:** Draft, to be updated iteratively as built
**Date:** 2026-04-05
**Owner:** Marat + Build team

---

## Purpose

Live monitoring interface for unmanned-spacecraft AI test runs. Let Marat observe 20 AI agents playing autonomously across 6-8 rounds, pause/resume, and inspect any element of the game state in real time.

This is the **observability layer** that unblocks all subsequent testing stages (6-8) and IS the core of Stage 9 (full Unmanned Spacecraft).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  20 AI AGENTS (parallel)                                │
│  Each round: read state → reason → commit action       │
│  Writes to: agent_decisions, agent_memories             │
└──────────────────┬──────────────────────────────────────┘
                   │ (all 20 committed)
                   ▼
┌─────────────────────────────────────────────────────────┐
│  ROUND RESOLUTION ENGINE                                │
│  Processes committed actions → applies combat →         │
│  updates world state                                    │
│  Writes to: unit_states_per_round, country_states,      │
│              combat_results, events                      │
└──────────────────┬──────────────────────────────────────┘
                   │ (round N complete)
                   ▼
┌─────────────────────────────────────────────────────────┐
│  OBSERVATORY UI (localhost:8888/observatory)           │
│  3 panels: Live Map | Dashboard | Activity Monitor     │
│  Realtime push via Supabase subscriptions              │
│  Controls: Start, Pause, Resume, Rewind, Speed         │
└─────────────────────────────────────────────────────────┘
```

---

## 3 UI Surfaces

### 1. Live Map (left 60%)
- Existing hex grid (global + 2 theaters) — reuses `/map` viewer code
- Units render from `unit_states_per_round` (current round)
- **Movement animations**: units drift to new coords when moved
- **Battle markers**: 💥 at attack locations with attacker + target info
- **Destroyed units**: grey out / fade
- Click unit → full history panel

### 2. Dashboard (right 25%)
- 20 country tiles, each showing: GDP | Stability | Active Units | Nuclear Level
- Click country → expanded view with:
  - Current strategic plan (from `agent_memories`)
  - Last committed action
  - Full per-domain stats
- **Simple line graphs** (Phase 2): GDP, stability, treasury over rounds

### 3. Activity Monitor (right 15%)
- Reverse-chronological feed:
  - 🎯 Action commits
  - ⚔ Combat results
  - 💭 Memory updates (summarized)
  - 🌍 Round start/end markers
  - 💬 Bilateral conversations (Stage 7+)
- Filter by: country, event type, round
- Click item → expand full details

---

## Controls (top bar)

```
[ Round 3/8 ] [Start ▶] [Pause ⏸] [Resume ▶] [Rewind ⏮] [Speed: 15s/round]
```

- **Auto-advance ON by default**, 15s pause between rounds
- Pause halts auto-advance
- Resume continues
- Rewind: view DB state at end of any past round (read-only)
- Speed control: 5s / 15s / 30s / manual

---

## Combat Engine (full spec)

Per committed `declare_attack` action, resolve via rules from `CON_C2_ACTION_SYSTEM_v2.frozen.md`:

### Ground Combat (RISK-style with modifiers)
- Attacker rolls up to 3 dice (N ground units committed, max 3)
- Defender rolls up to 2 dice (M units on target hex, max 2)
- Compare highest dice: attacker high vs defender high, then second-high
- Attacker LOSES tied rolls
- **Modifiers** (add to dice before comparison):
  - Defender terrain bonus: +1 (land_contested / die_hard hex)
  - Attacker 3:1 ratio: +1 for amphibious assault
  - Air superiority bonus: +1 if attacker has tactical_air unit in support
- Casualties: each losing pair = 1 unit destroyed (status → 'destroyed')

### Air Strikes
- Attacker commits tactical_air unit
- Target's air_defense units absorb strikes (up to 3 strikes per AD unit over the SIM)
- If attacker penetrates: attacker destroys 1 target unit (ground or air or AD)
- Strike success probability: 60% base, -15% per active AD, +10% per air superiority

### Naval Engagement
- Ship-vs-ship: dice-based, larger fleet gets +1 per unit advantage
- Anti-ship missile: strategic_missile unit → naval target, 50% success, reduces to 30% if AD present

### Amphibious Assault
- Ground units on naval ship attacking coastal hex
- Requires 3:1 attacker:defender ratio (4:1 for Formosa)
- Defender rolls +1 on first round

### Blockade
- naval unit on sea hex adjacent to coastal country
- Declares blockade → marked active
- Economic cascade: 10% GDP penalty to blockaded country per round blockade active
- Lifts when naval unit leaves hex

### Nuclear Strikes
- **L1 (tactical)**: attacker commits strategic_missile, target hex loses 50% of troops, economy -2 coins
- **L2 (strategic)**: target country loses 30% economic capacity + 50% military, 1/6 leader survival roll
- Air defense reduces nuclear damage by 25% per active AD (does NOT block fully for L2)
- Global stability shock: all countries lose 1 stability on nuclear use

### Resolution order per round
1. Diplomatic actions (declarations, log only)
2. Movement (`move_unit`, `mobilize_reserve`) — units arrive at new positions
3. Ranged strikes (air, missile) — resolve first
4. Ground combat — melee engagements
5. Naval engagements
6. Nuclear (if any)
7. Blockade status updates
8. R&D progress increments
9. Economic/political effects (sanctions, tariffs — record only, full engine later)

---

## Data Model Additions

### New tables needed

```sql
-- Per-round unit snapshots (populated by round engine)
unit_states_per_round (
  id UUID PK,
  scenario_id UUID FK,
  round_num INT,
  unit_code TEXT,
  country_code TEXT,
  global_row INT, global_col INT,
  theater TEXT, theater_row INT, theater_col INT,
  embarked_on TEXT,
  status TEXT,  -- active, reserve, embarked, destroyed
  notes TEXT,
  UNIQUE (scenario_id, round_num, unit_code)
)

-- Per-round country state snapshots
country_states_per_round (
  id UUID PK,
  scenario_id UUID FK,
  round_num INT,
  country_code TEXT,
  gdp NUMERIC, treasury NUMERIC, inflation NUMERIC,
  stability INT, political_support INT, war_tiredness INT,
  nuclear_level INT, nuclear_rd_progress NUMERIC,
  ai_level INT, ai_rd_progress NUMERIC,
  UNIQUE (scenario_id, round_num, country_code)
)

-- Combat results log
combat_results (
  id UUID PK,
  scenario_id UUID FK,
  round_num INT,
  combat_type TEXT,  -- ground/air/naval/nuclear
  attacker_country TEXT,
  defender_country TEXT,
  location_global_row INT, location_global_col INT,
  attacker_units TEXT[],  -- unit_codes
  defender_units TEXT[],
  attacker_rolls INT[],
  defender_rolls INT[],
  attacker_losses TEXT[],  -- destroyed unit_codes
  defender_losses TEXT[],
  narrative TEXT,
  created_at TIMESTAMPTZ
)

-- Round metadata
round_states (
  id UUID PK,
  scenario_id UUID FK,
  round_num INT UNIQUE,
  status TEXT,  -- pending, agents_reasoning, resolving, completed
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
)

-- General event log
observatory_events (
  id UUID PK,
  scenario_id UUID FK,
  round_num INT,
  event_type TEXT,  -- action_committed, combat_resolved, memory_updated, ...
  country_code TEXT,
  summary TEXT,
  payload JSONB,
  created_at TIMESTAMPTZ
)
```

---

## Round Lifecycle (20 agents, parallel)

```
ROUND N start
  ↓
1. Set round_states.status = 'agents_reasoning'
  ↓
2. Launch 20 agents IN PARALLEL (asyncio.gather)
   Each agent:
   - Reads memory + state via tools
   - Reasons across 4 domains
   - Commits ONE action to agent_decisions
   - Updates memory
  ↓
3. Set round_states.status = 'resolving'
  ↓
4. Round engine processes all 20 commits:
   - Movements → new unit_states rows
   - Combat → dice rolls → casualties + combat_results rows
   - R&D → updated country_states
   - Sanctions/tariffs → bilateral updates
   - Diplomatic → event log entries
  ↓
5. Publish round N snapshot (unit_states_per_round, country_states_per_round)
  ↓
6. Set round_states.status = 'completed'
  ↓
7. Realtime broadcast fires → UI updates
  ↓
8. Wait auto-advance delay (default 15s)
  ↓
ROUND N+1 start
```

---

## Build Sub-Sprints

**Sub-Sprint A: DB schema + migrations** (fastest)
- Create 5 new tables
- Populate round 0 snapshots from current state

**Sub-Sprint B: Combat Engine + Round Resolver**
- `app/engine/round_engine/resolve_round.py`
- `app/engine/round_engine/combat.py` (dice, modifiers, resolution)
- `app/engine/round_engine/movement.py`
- Unit tests for each combat type

**Sub-Sprint C: 20-agent parallel runner**
- `app/engine/agents/full_round_runner.py`
- asyncio.gather across all 20 HoS agents
- Error handling per-agent (one failure ≠ round failure)

**Sub-Sprint D: Observatory UI**
- `/observatory` route
- 3-panel layout
- Realtime subscriptions
- Controls (Start/Pause/Resume/Rewind/Speed)

**Sub-Sprint E: Wire together**
- `POST /api/observatory/start` — begins auto-advance loop
- `POST /api/observatory/pause`, `/resume`
- `POST /api/observatory/rewind?to_round=N`
- Round trigger chain

---

## Phase 1 = MVP Scope

**In scope:**
- 20 agents, parallel reasoning, 1 action commit each per round
- Combat: ground + air strikes + AD interception + amphibious + ranged (SIMPLE)
- Movement, mobilization, R&D increments
- 3-panel UI, auto-advance + pause/resume
- 6-round auto-run

**Deferred to Phase 2:**
- Naval combat nuances
- Blockade economic cascade
- Nuclear L2
- Bilateral conversations (Stage 7)
- Meetings/deals (Stage 7)
- Moderator event injection
- Economic engine (sanctions→GDP, tariffs→trade)

---

## Success Criteria

Phase 1 is DONE when:
1. Marat clicks "Start" → 20 agents play 6 rounds autonomously
2. Units move on the map, combat resolves, casualties appear
3. Dashboard updates GDP/stability/units per round
4. Activity Monitor shows every action + combat result in real-time
5. Pause/Resume works cleanly
6. Rewind shows correct historical state
7. Total runtime per round: <60s (target 30-45s)

---

## Open Questions (living list)

- Should agents see each other's committed actions IMMEDIATELY or only after all 20 commit? (currently: all see DB state, so simultaneous reads = Round N-1 state)
- Does the Observatory need user annotations (Marat leaves notes during playback)?
- Should failed combat attempts still be visible (e.g., "Columbia tried to attack but wasn't adjacent")?
- What's the MVP budget per round? 20 agents × ~40s Stage 3 equivalent = ~15 min serial, parallel = ~60s

---

*Spec v0.1 — will be updated as build progresses.*
