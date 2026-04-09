# CONTRACT: Budget Decision

**Status:** Canonical reference — engine, persistence, communication layer, AI prompt builder, and human UI MUST all match this document. If code and this contract disagree: STOP, update one to match the other, then proceed.

**Version:** 1.1 (2026-04-10)
**Owner:** Marat
**Used by:** `resolve_round.py`, `round_tick.py`, `economic.py`, mandatory-decisions skill harness, human budget UI (future)

---

## 1. PURPOSE

A country's budget decision is submitted at the end of each round. It governs how the country's revenue will be spent in the coming round. The engine consumes this decision, computes coin flows automatically, produces units, updates R&D progress, and derives political side-effects (stability, support).

**Key design principle:** Participants (human OR AI) set LEVELS, not coins. The engine computes actual coin expenditure based on level × standard cost. This removes an entire category of input errors (typing wrong numbers, exceeding caps) and matches how real policymakers think ("build at maximum pace" vs. "spend 12.37 coins on ground units").

---

## 2. DECISION SCHEMA

### 2.1 The decision object

```json
{
  "action_type": "set_budget",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change" | "no_change",
  "rationale": "string, >= 30 chars, required in both cases",
  "changes": {
    "social_pct": 1.0,
    "production": {
      "ground":            1,
      "naval":             0,
      "tactical_air":      2,
      "strategic_missile": 0,
      "air_defense":       1
    },
    "research": {
      "nuclear_coins": 0,
      "ai_coins":      5
    }
  }
}
```

### 2.2 Field specifications

| Field | Type | Values | Required | Semantics |
|---|---|---|---|---|
| `action_type` | string | `"set_budget"` | yes | Action identifier (per CARD_ACTIONS) |
| `country_code` | string | canonical country code | yes | Decision owner |
| `round_num` | int | ≥ 0 | yes | Round this decision applies to |
| `decision` | string | `"change"` or `"no_change"` | yes | Explicit choice |
| `rationale` | string | ≥ 30 chars | yes | Required even for no_change |
| `changes` | object | see below | only if `decision=="change"` | Must be absent or `null` when `no_change` |

### 2.3 Production level scale

Production levels use the same integer scale across all military branches:

| Level | Name | Coin multiplier | Output multiplier |
|---|---|---|---|
| `0` | none | 0× (no spending) | 0× (no output) |
| `1` | normal | 1× (standard cost) | 1× (standard output) |
| `2` | accelerated | 2× (double cost) | 2× (double output, rushed) |
| `3` | maximum | 4× (quadruple cost) | 3× (triple output, inefficient) |

**Why non-linear at level 3:** Maximum-pace production is inefficient — overtime, backup suppliers, defects. You get 3× units for 4× cost. Deliberate "emergency gear" worthwhile only in crisis.

### 2.4 Social spending — continuous slider

```
social_pct: float in [0.5, 1.5]
```

Unlike production (discrete levels), social spending is a continuous slider — any value from 0.5 (50% of baseline, austerity) to 1.5 (150% of baseline, generous).

**Stability and support effects are linear based on deviation from 1.0:**

| social_pct | Name | Stability delta | Political support delta |
|---|---|---|---|
| `0.5` | austerity | -2.0 / round | -3 / round |
| `0.75` | reduced | -1.0 | -1.5 |
| `1.0` | normal | 0 | 0 |
| `1.25` | generous | +1.0 | +1.5 |
| `1.5` | maximum | +2.0 | +3 |

**Linear formula:**
```
stability_delta = (social_pct - 1.0) × 4.0
support_delta   = (social_pct - 1.0) × 6
```

**Revenue formula:** `social_spending_coins = baseline_pct × revenue × social_pct`

Where `baseline_pct` is the country's `social_spending_baseline` (Template data, typically 0.20–0.35 depending on regime).

### 2.5 Production levels — per military branch

```
production: {
  ground:            0 | 1 | 2 | 3,
  naval:             0 | 1 | 2 | 3,
  tactical_air:      0 | 1 | 2 | 3,
  strategic_missile: 0 | 1 | 2 | 3,
  air_defense:       0 | 1 | 2 | 3
}
```

**All 5 branches are always present.** Missing fields = invalid decision. This forces explicit consideration.

**Branch standard costs (normal tier, 1 unit = 1 standard production):**

| Branch | Normal cost/unit | Standard output/round | Notes |
|---|---|---|---|
| `ground` | 3 coins | per country's `prod_cap_ground` | Ground brigades |
| `naval` | 6 coins | per `prod_cap_naval` | Cruisers/destroyers/subs |
| `tactical_air` | 5 coins | per `prod_cap_tactical_air` | Fighters/strike aircraft |
| `strategic_missile` | 8 coins | per `prod_cap_strategic_missile` (default 0) | ICBM/SLBM launchers — no country produces at start |
| `air_defense` | 4 coins | per `prod_cap_air_defense` (default 0) | SAM batteries — no country produces at start |

**Note on strategic_missile and air_defense (v1.1):** Schema is defined and accepted, but all countries start with capacity 0 for these branches. Any production level > 0 will still produce 0 units (capacity × multiplier = 0). This is intentional — the schema is forward-compatible for when we raise capacities later. Participants can set the level but it's a no-op for now.

**Level expansion:**

| Level | Ground (cost×cap) | Naval | Tac Air | Missile | AD |
|---|---|---|---|---|---|
| 0 | 0 × 0 | 0 × 0 | 0 × 0 | 0 × 0 | 0 × 0 |
| 1 | 3 × cap | 6 × cap | 5 × cap | 8 × cap | 4 × cap |
| 2 | 6 × (2×cap) | 12 × (2×cap) | 10 × (2×cap) | 16 × (2×cap) | 8 × (2×cap) |
| 3 | 12 × (3×cap) | 24 × (3×cap) | 20 × (3×cap) | 32 × (3×cap) | 16 × (3×cap) |

**Standard production capacity** is per-country (Template data). It reflects industrial base. Columbia might have ground=4, naval=2; Choson might have ground=2, naval=0.

### 2.6 Research — absolute coins per domain

```
research: {
  nuclear_coins: int (≥ 0),
  ai_coins:      int (≥ 0)
}
```

Unlike production (levels), research is direct coin allocation. The participant chooses how much treasury to pour into each tech domain. The engine converts coins to R&D progress internally.

**Progress formula (per SEED_D8):**
```
progress_per_round = (coins / gdp) × RD_MULTIPLIER × rare_earth_factor
```

Where `RD_MULTIPLIER = 0.8` and `rare_earth_factor` depends on Cathay's rare earth restrictions (1.0 if no restriction, lower otherwise).

**Examples (Columbia, GDP 280):**
- `0 coins`: 0 progress
- `3 coins`: 0.0086 progress/round (slow)
- `6 coins`: 0.017 progress/round (normal — reaches T3→T4 in ~12 rounds at AI L3)
- `12 coins`: 0.034 progress/round (accelerated)
- `25 coins`: 0.071 progress/round (crash program)

**R&D locked once maxed:** Nuclear T3 and AI L4 are the ceiling. Investment at max level = wasted coins. Context warns when applicable.

**Research cap:** Total R&D spending (`nuclear_coins + ai_coins`) capped at 30% of discretionary budget after mandatory + military. If exceeded → scaled down proportionally.

---

## 3. CONTEXT PROVIDED TO DECISION-MAKER

The communication layer assembles a standard context package from DB state + cognitive blocks. Same package for AI or human — different rendering.

### 3.1 Structure of the context package

```
[IDENTITY]              ← from LeaderAgent Block 2 (AI) or user profile (human)
[MEMORY]                ← from LeaderAgent Block 3 (AI) or notes panel (human)
[GOALS]                 ← from LeaderAgent Block 4 (AI) or objective tracker (human)
[RULES / REFERENCE]     ← from LeaderAgent Block 1 or rules panel (human)
[ROUND STATE]           ← from DB state tables (country_states, relationships, wars)
[BUDGET REVIEW DATA]    ← computed from current round state + standard costs
[CURRENT SETTINGS]      ← from country_states_per_round (last round's decision)
[INSTRUCTION]           ← what decision is being requested
```

### 3.2 BUDGET REVIEW DATA — specific payload

```
ECONOMIC STATE
  GDP:                 <current>
  Treasury:            <current>
  Inflation:           <current %>
  Debt ratio:          <current>
  Stability:           <current /10>
  Political support:   <current %>
  At war with:         <list or "none">

REVENUE FORECAST
  Base revenue:        <GDP × tax_rate>
  Oil revenue:         <if producer, else 0>
  Sanctions cost:      <subtracted if imposer>
  Debt servicing:      <subtracted>
  Inflation erosion:   <subtracted>
  ─────────────────────
  Expected total:      <sum>

MANDATORY COSTS (auto-deducted before discretionary)
  Social baseline:     <baseline × revenue × social_multiplier>
  Military maintenance: <total_units × cost × 3.0>
  ─────────────────────
  Total mandatory:     <sum>

DISCRETIONARY BUDGET
  Available:           <revenue - mandatory>
  Military cap:        <40% of discretionary>
  R&D cap:             <30% of remaining after military>

CURRENT MILITARY STATE
  Ground units:        <active> active, <reserve> reserve
  Naval units:         <active>
  Tactical air:        <active>
  Strategic missiles:  <count>
  Air defense:         <count>
  Nuclear level:       T<0-3>
  AI tech level:       L<0-4>

STANDARD PRODUCTION CAPACITY (what level 1 produces per round)
  Ground:              <cap> units (3 coins each)
  Naval:               <cap> units (6 coins each)
  Tactical air:        <cap> units (5 coins each)
  Strategic missile:   <cap> units (8 coins each)
  Air defense:         <cap> units (4 coins each)

LEVEL MEANING REMINDER
  0 = none (no production, no cost)
  1 = normal (standard output at standard cost)
  2 = accelerated (2× output at 2× cost)
  3 = maximum (3× output at 4× cost — emergency gear)

R&D PROGRESS
  Nuclear:             T<level> (progress <x>/<threshold> to next)
  AI:                  L<level> (progress <x>/<threshold> to next)
  Nuclear R&D at level 1 would cost: <2% × GDP = x coins>
  AI R&D at level 1 would cost:      <2% × GDP = x coins>

CURRENT BUDGET (from last round — will carry forward if no_change)
  Social level:        <0.5-1.5> (<name>)
  Production:          ground=<0-3>, naval=<0-3>, tac_air=<0-3>, missile=<0-3>, ad=<0-3>
  Research:            nuclear=<x coins>, ai=<x coins>

NO-CHANGE FORECAST (what happens if you keep current settings)
  Social spending:     <coins>
  Military spending:   <coins> → expected units: <ground=x, naval=y, tac_air=z, missile=0, ad=0>
  R&D spending:        <coins> → expected progress: <nuclear +0.00x, ai +0.00y>
  Total spending:      <sum>
  Revenue:             <sum>
  Deficit/surplus:     <delta>   [warning if deficit > 0]
  Expected stability:  <current> + <social delta> = <new>
  Expected support:    <current> + <social delta> = <new>

This forecast assumes unchanged sanctions/tariffs/combat outcomes.
```

### 3.3 Context assembly contract

A single function `build_budget_context(country_code, round_num)` returns the BUDGET REVIEW DATA block. It is pure (no LLM, no mutations), reads only from state tables + country structural data.

This function is used identically by:
- AI skill harness (adds to system prompt)
- Human UI (renders as form with real-time preview)
- Test fixtures (verifies context correctness)

---

## 4. VALIDATION RULES

Every decision submission passes through a validator before persistence.

### 4.1 Structural validation

| Rule | Error code |
|---|---|
| `action_type == "set_budget"` | `INVALID_ACTION_TYPE` |
| `decision` in `{"change", "no_change"}` | `INVALID_DECISION` |
| `rationale` present and ≥ 30 chars | `RATIONALE_TOO_SHORT` |
| If `change`: `changes` object present | `MISSING_CHANGES` |
| If `no_change`: `changes` absent or null | `UNEXPECTED_CHANGES` |

### 4.2 Range validation (when `change`)

| Rule | Error code |
|---|---|
| `social_pct` is float in `[0.5, 1.5]` | `INVALID_SOCIAL_PCT` |
| All 5 production branches present (ground, naval, tactical_air, strategic_missile, air_defense) | `MISSING_PRODUCTION_BRANCH` |
| Each production level is int in `[0, 3]` | `INVALID_PRODUCTION_LEVEL` |
| `research.nuclear_coins` is int `≥ 0` | `INVALID_RESEARCH_COINS` |
| `research.ai_coins` is int `≥ 0` | `INVALID_RESEARCH_COINS` |
| No extra unknown fields | `UNKNOWN_FIELD` |

### 4.3 Contextual warnings (soft — non-blocking)

These don't reject the decision but return warnings the participant may review:

- R&D at level > 0 when tech is already maxed → "Nuclear already at T3, investment wasted"
- Total estimated cost > discretionary capacity → "Budget will run a deficit of X coins, inflation may rise"
- All production levels = 0 → "No military production this round — intended?"
- Social level = 0 (austerity) and stability < 4 → "Austerity during unrest may trigger crisis"

### 4.4 Validator return format

```json
{
  "valid": true | false,
  "errors": ["INVALID_SOCIAL_LEVEL: got 5, must be 0-3"],
  "warnings": ["Nuclear already at T3, research investment wasted"],
  "normalized": { ... }  // sanitized decision object if valid
}
```

---

## 5. PERSISTENCE

### 5.1 Where the decision is stored

**Primary:** `agent_decisions` table
- `action_type`: `"set_budget"`
- `action_payload`: full decision JSON (including rationale)
- `validation_status`: `"passed"` | `"failed"`

**Engine input:** `country_states_per_round` columns (new schema)
- `budget_social_pct` (NUMERIC, 0.5-1.5)
- `budget_production` (JSONB — `{ground: int, naval: int, tactical_air: int, strategic_missile: int, air_defense: int}`)
- `budget_research` (JSONB — `{nuclear_coins: int, ai_coins: int}`)

**Deprecate:** `budget_military_coins`, `budget_tech_coins` (old flat columns — remove after migration). `budget_social_pct` is kept and reused (same name, same semantics, just now populated from participant's slider instead of default 1.0).

### 5.2 Persistence flow

1. Participant submits → communication layer → validator
2. If valid → write to `agent_decisions` (action log)
3. `resolve_round` reads `agent_decisions`, writes to `country_states_per_round` (current round's budget columns)
4. `round_tick` reads `country_states_per_round` → builds engine input → calls `process_economy`
5. Engine writes updated state back to `country_states_per_round` (new GDP, treasury, unit counts, etc.)

### 5.3 "no_change" handling

- If `decision == "no_change"`: previous round's budget is carried forward.
- `resolve_round` copies `budget_social_pct`, `budget_production`, `budget_research` from round N-1 to round N.
- This keeps engine input consistent — the engine always sees explicit values, never "null means default."

---

## 6. ENGINE BEHAVIOR

### 6.1 Input expected by `process_economy`

The budget dict passed to `calc_budget_execution` and `calc_military_production`:

```python
budget = {
    "social_pct": 1.0,                    # float 0.5-1.5
    "production": {
        "ground":            1,            # int 0-3
        "naval":             0,
        "tactical_air":      2,
        "strategic_missile": 0,
        "air_defense":       1,
    },
    "research": {
        "nuclear_coins": 0,                # int ≥ 0
        "ai_coins":      5,
    },
}
```

### 6.2 Engine expansion of levels and coins

```python
# Production level tables
PRODUCTION_COST_MULT   = {0: 0, 1: 1, 2: 2, 3: 4}
PRODUCTION_OUTPUT_MULT = {0: 0, 1: 1, 2: 2, 3: 3}

BRANCH_UNIT_COST = {
    "ground":            3,
    "naval":             6,
    "tactical_air":      5,
    "strategic_missile": 8,
    "air_defense":       4,
}

# R&D
RD_MULTIPLIER = 0.8   # per SEED_D8
```

**Process:**

1. **Social spending** (continuous slider):
   ```
   social_spending_coins = baseline_pct × revenue × social_pct
   stability_delta       = (social_pct - 1.0) × 4.0
   support_delta         = (social_pct - 1.0) × 6
   ```

2. **For each production branch:**
   ```
   level = budget.production[branch]
   unit_cost_base = BRANCH_UNIT_COST[branch]
   cap = country.prod_cap_<branch>

   coins = unit_cost_base × cap × PRODUCTION_COST_MULT[level]
   units = cap × PRODUCTION_OUTPUT_MULT[level]

   # strategic_missile and air_defense: cap = 0, so always 0 units / 0 coins
   ```

3. **For each research domain:**
   ```
   coins = budget.research.<domain>_coins   # already in coins, no conversion
   progress_delta = (coins / gdp) × RD_MULTIPLIER × rare_earth_factor
   ```

4. **Sum all coins** → `total_spending`
5. **Apply cap checks and deficit cascade** (see §6.3)

### 6.3 Cap enforcement

- **Military cap:** total military production coins ≤ 40% of discretionary. If over → scale all production branches down proportionally (reduce by ratio, not drop branches).
- **R&D cap:** total R&D coins ≤ 30% of discretionary after military. Same scale-down rule.
- **Deficit:** if (social + military + R&D + maintenance) > revenue → draw from treasury → if insufficient → print money → inflation increases.

### 6.4 Political side-effects

`social_pct` directly modifies stability and political support:
```
stability_delta = (social_pct - 1.0) × 4.0
support_delta   = (social_pct - 1.0) × 6
```

Examples:
- `0.5` → stability -2.0, support -3
- `0.75` → stability -1.0, support -1.5
- `1.0` → no change
- `1.25` → stability +1.0, support +1.5
- `1.5` → stability +2.0, support +3

No other budget fields affect stability/support directly — those come from other game events (war, sanctions, etc.).

---

## 7. WHAT IS OUT OF SCOPE FOR BUDGET

The participant does NOT set:
- Absolute coin amounts (engine computes)
- Unit production caps (Template data)
- Production costs (Template data)
- Tax rates (Template data)
- Maintenance costs (computed automatic)
- Debt servicing (automatic)
- Personal coins for role (separate system)
- Covert op card allocation (separate system)
- Tariffs, sanctions, OPEC (separate decisions — not budget)

---

## 8. STANDARD OUTPUT OF ENGINE (what budget produces)

After processing, the engine returns a `BudgetExecutionResult`:

```python
{
  "social_spending": 12.4,
  "military_spending": 18.0,
  "research_spending": 5.0,
  "maintenance": 28.8,
  "total_spending": 64.2,
  "revenue": 62.1,
  "deficit": 2.1,
  "treasury_drawn": 2.1,
  "money_printed": 0.0,
  "units_produced": {
    "ground":            4,   # level 1, capacity 4 → 4 units
    "naval":             0,   # level 0 → 0 units
    "tactical_air":      6,   # level 2, capacity 3 → 6 units
    "strategic_missile": 0,   # capacity 0 for all countries at start
    "air_defense":       0,   # capacity 0 for all countries at start
  },
  "coins_by_branch": {
    "ground":            12,  # 3 × 4 × 1
    "naval":             0,
    "tactical_air":      30,  # 5 × 3 × 2
    "strategic_missile": 0,
    "air_defense":       0,
  },
  "research_progress": {
    "nuclear": {"coins": 0, "delta": 0.000, "total": 1.0, "level": 3, "leveled_up": false},
    "ai":      {"coins": 5, "delta": 0.014, "total": 0.254, "level": 3, "leveled_up": false},
  },
  "stability_delta": 0.0,       # social_pct was 1.0
  "political_support_delta": 0,
  "warnings": []
}
```

This result is used by `round_tick` to update `country_states_per_round` and by the Observatory to display round outcomes.

---

## 9. ACCEPTANCE CRITERIA FOR THIS CONTRACT

Before declaring the budget vertical slice DONE, all of the following must be verified:

1. **Contract consistency:** This document, `economic.py`, `resolve_round.py`, `round_tick.py`, the validator, the skill harness, and the battery test all use identical field names and level semantics. Cross-checked by a single audit pass.

2. **Battery test passes:** Scripted budget decisions at each level (0/1/2/3) on each branch produce expected unit counts and coin flows. Deficit cases handled correctly. no_change carries forward correctly.

3. **Validator rejects invalid input:** Missing fields, out-of-range values, wrong types all caught with clear error codes.

4. **Engine produces expected results:** For a controlled scenario (Columbia with known GDP/units), setting `social_level=0, production.ground=2, research.ai=1` produces measurable changes matching the formulas in §6.2.

5. **Context assembly correct:** `build_budget_context` returns a package matching §3.2 structure, populated from real DB state.

6. **AI skill harness produces valid decisions:** Given the standard context, the AI participant returns budget JSON matching this contract. Validation passes. At least 8/10 leaders produce valid output on a fresh run.

7. **End-to-end round test:** Run resolve_round → engine_tick for one round with scripted budgets for all 20 countries. Observatory reflects the results. No errors, no silent data drops.

8. **Documentation:** This contract is referenced from `CARD_ACTIONS.md` §2.1 Set Budget. CARD_ACTIONS mentions the deprecation of the old schema.

---

## 10. CHANGE LOG

- **2026-04-10 v1.1** — Revisions per Marat:
  - Social: continuous slider `social_pct: float [0.5, 1.5]` (not level enum). Linear stability/support deltas.
  - Research: `nuclear_coins` + `ai_coins` as int (not levels). Engine converts to progress.
  - Strategic missile + air defense schema defined but all countries start with capacity 0 (no production until later raised).
  - Context now includes "no-change forecast" block so participant sees predicted outcome before deciding.
- **2026-04-10 v1.0** — Initial contract. Level-based schema (0/1/2/3). 5 production branches. Replaces old flat-coin approach.
