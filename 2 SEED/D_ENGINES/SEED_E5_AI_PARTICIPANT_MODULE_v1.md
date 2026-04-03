# AI Participant Module — SEED Specification
## Thucydides Trap SIM
**Version:** 1.0 | **Date:** 2026-04-04 | **Status:** Active
**Concept reference:** CON_C1 F1 (AI Participant Module), SEED_E2 (AI Conversations)
**Architecture:** KING-style 4-block cognitive model with context caching
**Dependencies:** Context Assembly Service (D9), NOUS (D10), Engine (D8)

---

## 1. Overview

21 AI-operated country leaders, each an autonomous LLM-powered agent. Each leader receives visibility-scoped world state, reasons about strategy, submits structured actions, conducts bilateral conversations, and executes transactions. Decisions flow into the engine for processing.

**Architecture:** KING-proven 4-block model with explicit context caching (~85% cost reduction). Each round: assemble context → LLM strategic reasoning → structured action output → conversations → transactions → submit to engine.

**Future extension:** Option B (Anthropic persistent agent) to be tested once Option A is stable.

---

## 2. Cognitive Model (4 Blocks)

### Block 1: RULES (fixed per SIM)
Game mechanics, available actions, combat odds, production costs, economic formulas summary, map structure. Same for all agents. **Cached once.**

### Block 2: IDENTITY (fixed per SIM, generated at init)
Character personality, values, speaking style, negotiation approach, risk orientation. Generated from role brief via LLM call at T=0.85 for diversity. **Cached once.**

Example: *"You are the Helmsman — patient, strategic, obsessed with legacy. You speak in measured terms, rarely reveal your full hand. You believe Formosa is your defining challenge. You distrust Columbia but need Sarmatia. You are 72 — time is not on your side."*

### Block 3: MEMORY (updated per round)
Accumulated experience: previous decisions and outcomes, conversation summaries, relationship scores, promises made/broken, intelligence gathered. Rebuilt from event log each round. Grows over time. **Refreshed each round.**

### Block 4: GOALS & STRATEGY (updated per round)
Current priorities, action plans, contingencies. Derived from role objectives + current situation assessment. Revised after each round based on outcomes. **Refreshed each round.**

### Context Caching
Blocks 1+2 cached for the entire SIM. Blocks 3+4 refreshed per round. On a typical call:
- Cached tokens: ~4K (rules + identity)
- Fresh tokens: ~6K (memory + goals + world state + instruction)
- Cost saving: ~40% per call (Anthropic prompt caching)

---

## 3. Initialization

```
For each of 21 leaders:
  1. Load role data (roles.csv: character_name, powers, objectives, ticking_clock)
  2. Load role brief (role_briefs/ROLE_ID.md — character description, background)
  3. Generate Block 2 IDENTITY via LLM (T=0.85, ~500 tokens out)
  4. Initialize Block 3 MEMORY:
     - Relationships from world state (ally=0.8, neutral=0.0, at_war=-1.0)
     - Empty decision history
     - Empty conversation log
  5. Initialize Block 4 GOALS:
     - Extract objectives from role brief
     - Rank by urgency: urgency = max(0.3, 1.0 - (8 - round_num) × 0.1)
     - Set initial strategy based on starting situation
  6. Cache Blocks 1+2
```

**Cost:** 21 identity generation calls × ~500 tokens = ~10.5K tokens total. One-time.

---

## 4. Per-Round Decision Flow

```
ROUND START
    │
    ▼
┌── CONTEXT ASSEMBLY ──────────────────────────────┐
│  Build per-leader context via Context Assembly:   │
│  - sim_rules (cached Block 1)                     │
│  - role_identity (cached Block 2)                 │
│  - world_state:{country}_visible                  │
│  - memory (Block 3 — decisions, conversations)    │
│  - goals (Block 4 — priorities, strategy)         │
│  - available_actions (filtered by role powers)    │
│  - round_context (scheduled events, deadlines)    │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
┌── STRATEGIC REASONING (LLM call) ────────────────┐
│  "Given your situation, what are your priorities  │
│   this round? What actions do you take?"          │
│                                                   │
│  Output: Structured JSON with ALL decisions       │
│  - mandatory_inputs (budget, tariffs, sanctions)  │
│  - military_orders (attacks, blockades, deploy)   │
│  - covert_operations (if intel pool > 0)          │
│  - political_actions (propaganda, repression)     │
│  - economic_actions (money printing, OPEC)        │
│  - conversation_requests (who to talk to, why)    │
│  - transaction_proposals (deals to offer)         │
│  - public_statements (if any)                     │
│  - reasoning (private strategic notes)            │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
┌── CONVERSATIONS (bilateral, 8 turns max) ────────┐
│  For each conversation_request:                   │
│  - Check if counterpart also requested (mutual)   │
│  - Or initiate (one-sided request honored)        │
│  - Max conversations per leader per round: 3      │
│  - Each conversation: 8 turns (4 per side)        │
│  - Context: identity + relationship + intent      │
│  - Output: transcript + any proposals made        │
│  Total: up to ~30 conversations per round         │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
┌── TRANSACTIONS ──────────────────────────────────┐
│  For each transaction_proposal:                   │
│  - Counterpart evaluates (LLM call with context)  │
│  - Accept / reject / counter-propose              │
│  - If accepted: execute (coin/arms/tech transfer) │
│  - Logged as events                               │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
┌── ACTION SUBMISSION ─────────────────────────────┐
│  All decisions collected into round_actions dict   │
│  Validated against authorization rules             │
│  Fed to engine orchestrator                        │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
    ENGINE (Pass 1 → NOUS Pass 2 → results)
                       │
                       ▼
┌── REFLECTION ────────────────────────────────────┐
│  Each leader receives round results               │
│  Update Block 3 MEMORY:                           │
│  - Record decisions + outcomes                    │
│  - Update relationship scores                     │
│  - Log conversation summaries                     │
│  Update Block 4 GOALS:                            │
│  - Revise priorities based on what happened       │
│  - New urgencies (election approaching, etc.)     │
└──────────────────────────────────────────────────┘
```

---

## 5. Complete Action Set

### 5.1 Mandatory Inputs (once per round, HoS submits)

| Action | Parameters | Validation |
|--------|-----------|-----------|
| `budget_submit` | social_pct (0.5-1.5), military_coins, tech_coins | Total ≤ revenue |
| `tariff_set` | {target_country: level(0-3)} per country | Any country |
| `sanction_set` | {target_country: level(0-3)} per country | Any country |
| `opec_production` | level: min/low/normal/high/max | OPEC members only |

### 5.2 Military Actions (anytime, mil chief or HoS)

| Action | Parameters | Authorization | Resolution |
|--------|-----------|--------------|-----------|
| `ground_attack` | from_zone, to_zone, units | Mil chief + HoS co-sign | RISK dice + modifiers |
| `naval_combat` | zone, target_country | Mil chief | RISK dice (naval) |
| `naval_bombardment` | target_zone, ships | Mil chief | Random unit destroyed |
| `air_strike` | target_zone, aircraft | Mil chief | Random unit destroyed |
| `blockade_set` | chokepoint, level(partial/full) | Mil chief | Supply/trade reduction |
| `strategic_missile` | target_zone, quantity | HoS + mil chief | Zone damage |
| `nuclear_authorize` | target_zone | HoS + mil chief + 1 more | MAD-level destruction |
| `mobilize` | units_from_pool | HoS or mil chief | Pool → active units |
| `reserve_move` | units, to_reserve | Mil chief | Active → reserve |
| `deploy` | units, to_zone | HoS | Reserve → zone (Phase C) |

### 5.3 Covert Operations (limited pool, intel role)

| Action | Parameters | Success rate | Detection | Effect |
|--------|-----------|-------------|-----------|--------|
| `espionage` | target_country | 70% | 20% | Reveal hidden data |
| `sabotage_military` | target_country | 50% | 40% | Destroy 1 unit |
| `sabotage_economic` | target_country | 50% | 40% | Destroy coins |
| `sabotage_infrastructure` | target_country | 50% | 40% | Ongoing GDP damage |
| `sabotage_nuclear` | target_country | 40% | 50% | -15-20% nuclear progress |
| `cyber_attack` | target_country | 60% | 30% | Disrupt systems |
| `disinformation` | target_country | 55% | 25% | -stability/-support |
| `election_meddling` | target_country | 40% | 35% | Shift election outcome |
| `assassination` | target_role | 20-60% | varies | Eliminate leader |
| `proxy_attack` | target_country | 50% | 30% | Deniable damage |

### 5.4 Political Actions (HoS or designated roles)

| Action | Parameters | Effect |
|--------|-----------|--------|
| `propaganda` | coins_spent (1-3) | +stability, +support |
| `repression` | intensity (1-3) | +stability, -support (autocracy) |
| `arrest` | target_role_id | Remove from active play |
| `fire` | target_role_id | Remove from position (HoS only) |
| `public_statement` | text | Visible to all, affects relationships |
| `call_election` | (Ruthenia forced) | 2 of 3 players can force |

### 5.5 Economic Actions

| Action | Parameters | Effect |
|--------|-----------|--------|
| `print_money` | (once/round) | +3% GDP to treasury, +inflation |
| `tech_investment` | coins, program(ai/nuclear) | Accelerate R&D |
| `private_tech_investment` | personal_coins | Pioneer/Circuit role action |

### 5.6 Transactions (bilateral, 2-phase: propose → accept)

| Transaction | Proposer gives | Proposer receives | Validation |
|------------|---------------|------------------|-----------|
| `coin_transfer` | coins | (goodwill / deal term) | Treasury check |
| `arms_sale` | military units | coins | Unit availability |
| `arms_gift` | military units | (alliance / deal) | Unit availability |
| `tech_transfer` | tech level access | coins or reciprocal | Ownership check |
| `basing_rights` | zone access | coins / security | Zone control |
| `ceasefire` | stop attacks | mutual stop | Active war exists |
| `peace_treaty` | end war | mutual end | Active war exists |
| `alliance` | mutual defense | mutual defense | Both agree |
| `trade_agreement` | tariff reduction | mutual reduction | Both HoS |
| `sanctions_coordination` | joint sanctions | shared burden | Coalition logic |

### 5.7 Communication

| Type | Participants | Turns | Per round limit |
|------|-------------|-------|----------------|
| `bilateral_conversation` | 2 leaders | 8 max (4 each) | 3 per leader |
| `public_speech` | 1 leader → all | 1 (monologue) | 1 per leader |

**Conversation flow:**
1. Leader A requests conversation with Leader B (part of strategic reasoning output)
2. If mutual: both have intent, richer conversation
3. If one-sided: counterpart responds reactively
4. Context per conversation: identity + relationship history + intent notes (private)
5. Each turn: ~100-200 tokens
6. Total per conversation: ~2K tokens (both sides)
7. Transcript logged → feeds into memory for both participants

**No multi-party meetings in unmanned v1.** Added later.

---

## 6. Structured Action Output Schema

The strategic reasoning LLM call returns:

```json
{
  "round_num": 3,
  "role_id": "dealer",
  "country_id": "columbia",

  "mandatory_inputs": {
    "budget": {"social_pct": 1.0, "military_coins": 8, "tech_coins": 5},
    "tariffs": {"cathay": 2, "sarmatia": 0},
    "sanctions": {"sarmatia": 3, "persia": 3},
    "opec_production": null
  },

  "military_orders": [
    {"action": "blockade_set", "chokepoint": "caribbean", "level": "partial"},
    {"action": "air_strike", "target_zone": "persia_2", "units": 2}
  ],

  "covert_operations": [
    {"action": "sabotage_nuclear", "target": "persia"}
  ],

  "political_actions": [
    {"action": "propaganda", "coins": 2}
  ],

  "economic_actions": [],

  "conversation_requests": [
    {"target_leader": "helmsman", "intent": "Warn about Formosa consequences", "priority": "high"},
    {"target_leader": "pathfinder", "intent": "Coordinate sanctions pressure", "priority": "medium"}
  ],

  "transaction_proposals": [
    {"type": "arms_sale", "target": "ruthenia", "units": {"ground": 2}, "price": 4,
     "rationale": "Strengthen ally against Sarmatia"}
  ],

  "public_statements": [
    "Columbia stands firmly with its allies. Any aggression against Formosa will be met with a decisive response."
  ],

  "strategic_reasoning": "Cathay approaching AI L3 — must signal deterrence on Formosa while maintaining sanctions pressure on Sarmatia. Arms to Ruthenia extends the war. Persia nuclear sabotage is high priority before breakout.",

  "priority_assessment": {
    "formosa_deterrence": "urgent",
    "persia_nuclear": "critical",
    "sarmatia_sanctions": "maintaining",
    "domestic_economy": "stable",
    "election_prep": "R5 approaching — need support above 40%"
  }
}
```

---

## 7. Memory System

### Per-Round Memory Update

After engine processing, each leader's Block 3 is updated:

```json
{
  "round_3_memory": {
    "my_decisions": {"tariffs": {"cathay": 2}, "military": ["air_strike persia_2"]},
    "outcomes": {"oil_price": 118, "my_gdp_change": "+1.0%", "persia_nuclear": "sabotage failed, detected"},
    "conversations": [
      {"with": "helmsman", "summary": "Warned about Formosa. He was evasive. Suspects we know about naval buildup.", "trust_change": -0.1},
      {"with": "pathfinder", "summary": "Agreed to maintain sanctions L3. He wants more arms.", "trust_change": +0.1}
    ],
    "transactions": [{"arms_sale to ruthenia": "2 ground units for 4 coins, accepted"}],
    "surprises": ["Caribe declared in crisis by NOUS", "Persia detected our sabotage — diplomatic cost"],
    "relationship_updates": {"helmsman": -0.1, "pathfinder": +0.1, "furnace": -0.2}
  }
}
```

### Memory Compression

After round 4+, early memories are summarized to control token growth:
- Rounds 1-2: compressed to ~200 tokens each
- Round 3+: full detail (~500 tokens each)
- Conversations: only summaries kept (not full transcripts)

---

## 8. Testing Interface

### Chat with Agent (debugging/calibration tool)

A CLI or simple web interface that lets a human talk to any AI participant at any time:

```
> /talk dealer round:3

DEALER (Columbia President): [ready, round 3 context loaded]

You: Why did you escalate tariffs on Cathay?

DEALER: Cathay is approaching AI L3 — if they reach it, the economic gap
narrows permanently. Tariffs slow their growth and signal resolve. My
advisors tell me the cost to us is manageable at L2. If Helmsman retaliates,
we escalate to L3 and rally the Western Treaty allies.

You: What's your biggest concern right now?

DEALER: Persia. The sabotage failed and they know it was us. If they reach
nuclear L1 this round, the entire Mashriq theater changes. I need Levantia
to keep pressure on while I manage the Cathay situation.

You: /inspect blocks
[Block 1: RULES — 3,200 tokens, cached]
[Block 2: IDENTITY — 480 tokens, cached]
[Block 3: MEMORY — 1,850 tokens, 3 rounds of history]
[Block 4: GOALS — 620 tokens, 6 objectives ranked]
```

Commands:
- `/talk {role_id} round:{N}` — start conversation with agent at specific round
- `/inspect blocks` — show current 4-block state
- `/inspect memory` — show full memory contents
- `/inspect decisions round:{N}` — show what agent decided and why
- `/reset` — reload agent from scratch

---

## 9. LLM Cost Estimate (per full SIM run)

| Activity | Calls | Tokens/call | Total tokens | Model |
|----------|-------|-------------|-------------|-------|
| Identity generation | 21 | ~1K | ~21K | Sonnet |
| Strategic reasoning | 21 × 6 rounds = 126 | ~12K in, ~2K out | ~1.8M | Sonnet |
| Conversations | ~30/round × 6 = 180 | ~3K in, ~1K out | ~720K | Flash |
| Transaction evaluation | ~20/round × 6 = 120 | ~2K in, ~500 out | ~300K | Flash |
| Reflection | 21 × 6 = 126 | ~4K in, ~1K out | ~630K | Flash |
| NOUS judgment | 6 | ~8K in, ~1K out | ~54K | Sonnet |
| **Total** | **~579 calls** | | **~3.5M tokens** | |

**Estimated cost per full SIM:** ~$3-5 (at Sonnet/Flash pricing)
**Time per full SIM:** ~15-25 minutes (with parallel agent calls)

---

## 10. Module Structure

```
app/engine/agents/
├── __init__.py
├── leader.py            ← LeaderAgent class (4-block, context assembly)
├── profiles.py          ← Role data loading, identity generation
├── decisions.py         ← Action output schema, validation
├── conversations.py     ← 8-turn bilateral conversation engine
├── transactions.py      ← Propose → evaluate → execute flow
├── memory.py            ← Block 3/4 management, compression
├── runner.py            ← Run all 21 leaders, collect actions, orchestrate conversations
└── chat.py              ← Debug chat interface (/talk command)
```

---

## 11. Implementation Stages

### Stage 1: Strategic Reasoning + Actions
- LeaderAgent class with 4-block context
- Single LLM call per leader per round → structured action JSON
- Action validation and engine integration
- Full round loop: 21 agents → engine → NOUS → results
- **Test:** Run 1 full SIM (6 rounds), verify all 21 leaders produce valid actions

### Stage 2: Conversations
- 8-turn bilateral conversation engine
- Intent notes from strategic reasoning
- Transcript → memory integration
- **Test:** Run SIM with conversations, verify deals emerge naturally

### Stage 3: Transactions
- Propose → evaluate → execute flow
- Arms sales, coin transfers, basing rights, treaties
- **Test:** Verify bilateral deals execute correctly, economy balances

### Stage 4: Memory + Reflection
- Round-by-round memory accumulation
- Memory compression for late rounds
- Strategic revision based on outcomes
- **Test:** Verify agent behavior evolves across rounds (not repetitive)

### Stage 5: Testing Interface
- `/talk` chat command
- Block inspection
- Decision replay

### Stage 6: Option B (Anthropic persistent agent)
- Alternative architecture using persistent conversation
- Compare reasoning quality, cost, reliability vs Option A
