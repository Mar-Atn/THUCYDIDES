# CONTRACT: OPEC Production Decision

**Status:** 🔒 **LOCKED** (2026-04-11) — canonical reference, frozen for the Unmanned Spacecraft phase.
Any change requires (a) Marat's explicit approval, (b) a version bump, and (c) reconciliation of all listed consumers in the same commit.

**Version:** 1.0 (2026-04-11)
**Verified end-to-end:** 2026-04-11 — L1 (67 tests: 47 validator + 20 engine) + L2 (14 tests: 4 persistence + 10 context) + L3 (1 AI acceptance gate) all passing. Total: **82 tests**. See `CHECKPOINT_OPEC.md`.
**Owner:** Marat
**Will be used by:**
- Engine: `app/engine/engines/economic.py` `calc_oil_price()` (OPEC production section) — **UNCHANGED**, regression-locked
- Validator: `app/engine/services/opec_validator.py` (NEW)
- Context builder: `app/engine/services/opec_context.py` (NEW — read-only, no dry-run)
- Persistence: `app/engine/round_engine/resolve_round.py` (set_opec handler — rewritten) + existing `country_states_per_round.opec_production` column (live value) + NEW `country_states_per_round.opec_decision` JSONB column (per-round audit)
- Tests: `app/tests/layer1/test_opec_engine.py`, `app/tests/layer1/test_opec_validator.py`, `app/tests/layer2/test_opec_persistence.py`, `app/tests/layer2/test_opec_context.py`, `app/tests/layer3/test_skill_mandatory_decisions.py` (D4 portion — updated), `app/tests/layer3/test_opec_full_chain_ai.py`
- Human UI (future — not yet implemented)

---

## 1. PURPOSE

OPEC+ member countries control global oil supply through coordinated production decisions. Each round, each OPEC+ member submits a production posture (cut, hold, or flood) that affects the world oil price via the cartel leverage mechanism. This is the most impactful single-value decision in the sim — 4 members collectively move ~60% of world oil supply, and oil price cascades into every country's revenue, GDP growth, and inflation.

**Key design principles:**

1. **OPEC+ membership is canonical from the DB.** The 5 members are: **Caribe (Venezuela), Mirage, Persia, Sarmatia (OPEC+), Solaria**. Non-members cannot submit this decision (validator rejects with `NOT_OPEC_MEMBER`).
2. **Single-value decision.** Not a bilateral matrix like tariffs/sanctions. Each member picks ONE production level per round: `min | low | normal | high | max`.
3. **Cartel leverage amplifies decisions 2×.** The engine applies a 2× multiplier on top of each member's world-supply share, reflecting OPEC's ability to move markets beyond its raw share.
4. **Carry-forward by inaction.** If a member doesn't submit, their previous level persists. `no_change` is a fully legitimate explicit choice.
5. **Decision affects ALL countries, not just the actor.** Unlike tariffs/sanctions which are bilateral, OPEC decisions change the world oil price, which affects every country's oil revenue (if producer), oil cost (if importer), GDP shocks, and inflation pressure.
6. **Engine math is UNCHANGED.** The existing `calc_oil_price` OPEC section already matches SEED_D8 + CARD_FORMULAS A.1 exactly. This slice locks a contract around existing behavior and pins constants as regression guards.
7. **Decision-specific context is data-only.** Per Marat 2026-04-10: no commentary, no warnings, no "consider X" hints. The context delivers raw facts the participant needs to decide; interpretation is the participant's job.
8. **No cognitive layer in this contract** per the VERTICAL_SLICE_PATTERN boundary. Tests emulate the cognitive layer with a hand-crafted persona stub that lives only in the test harness.

---

## 2. DECISION SCHEMA

### 2.1 The decision object

```json
{
  "action_type": "set_opec",
  "country_code": "solaria",
  "round_num": 3,
  "decision": "change" | "no_change",
  "rationale": "string, >= 30 chars, required in both cases",
  "changes": {
    "production_level": "min" | "low" | "normal" | "high" | "max"
  }
}
```

### 2.2 Field specifications

| Field | Type | Values | Required | Semantics |
|---|---|---|---|---|
| `action_type` | string | `"set_opec"` | yes | Singular — there is only one field to set |
| `country_code` | string | must be in {caribe, mirage, persia, sarmatia, solaria} | yes | Decision owner. Must be an OPEC+ member. |
| `round_num` | int | ≥ 0 | yes | Round this decision applies to |
| `decision` | string | `"change"` or `"no_change"` | yes | Explicit choice. `no_change` is legitimate. |
| `rationale` | string | ≥ 30 chars | yes | Required in both branches. |
| `changes` | object | see §2.3 | only if `decision=="change"` | Must be absent when `no_change`. |

### 2.3 The `changes` object

```
changes: {
  production_level: "min" | "low" | "normal" | "high" | "max"
}
```

Single field, enum value. No sparse matrix, no signed levels, no multiple targets.

### 2.4 Level scale and market effect

| Level | Multiplier | World-supply contribution per member |
|---|---|---|
| `min` | 0.70× | `−0.30 × share × 2.0` |
| `low` | 0.85× | `−0.15 × share × 2.0` |
| `normal` | 1.00× | `0` |
| `high` | 1.15× | `+0.15 × share × 2.0` |
| `max` | 1.30× | `+0.30 × share × 2.0` |

The 2× cartel leverage is applied per-member on top of their world-supply share.

### 2.5 No_change example

```json
{
  "action_type": "set_opec",
  "country_code": "solaria",
  "round_num": 3,
  "decision": "no_change",
  "rationale": "Current 'normal' production is generating 95 coins/round of oil revenue at $85/bbl. Treasury stable. No strategic reason to disrupt the market this round."
}
```

Note: NO `changes` field.

---

## 3. CONTEXT PROVIDED TO DECISION-MAKER (decision-specific only)

This contract specifies what the **SYSTEM** supplies to the participant about THIS decision. The participant's **cognitive context** (identity, memory, goals, world rules) is OUT OF SCOPE — that is the responsibility of the AI Participant Module (future).

### 3.1 What the system provides

```
[ECONOMIC STATE]          ← own country snapshot, oil revenue focus
[OIL MARKET STATE]        ← current world oil price + supply/demand balance
[OIL PRICE HISTORY]       ← oil price for every round already played (round 0 to N-1)
[OIL PRODUCERS TABLE]     ← ALL oil-producing countries with mbpd, share, current production level
[CHOKEPOINT BLOCKADES]    ← current status of Gulf Gate, Caribe Passage, Formosa Strait
[SANCTIONS ON PRODUCERS]  ← which oil producers are under L2+ sanctions (triggers −10% × share supply penalty)
[TARIFFS ON PRODUCERS]    ← any active tariffs imposed on or by oil producers
[DECISION RULES]          ← schema + no_change reminder
[INSTRUCTION]
```

### 3.2 [ECONOMIC STATE] — own country snapshot

```
GDP:                          {gdp}
Treasury:                     {treasury}
Inflation:                    {inflation}%
Stability:                    {stability}/10
My oil production:            {mbpd} mbpd ({pct}% of world)
My oil revenue (last round):  {coins}
My current production level:  {min/low/normal/high/max}
```

### 3.3 [OIL MARKET STATE]

```
Current oil price:            ${price}/bbl
Total world supply:           {total_mbpd} mbpd
OPEC+ share:                  {opec_pct}% of world supply
```

### 3.4 [OIL PRICE HISTORY] — all rounds already played

```
Round 0:  $80/bbl
Round 1:  $83/bbl
Round 2:  $85/bbl
Round 3:  $78/bbl
...up to the current round
```

Sourced from `global_state_per_round.oil_price` for rounds `[0, current_round - 1]`. All historical prices, no trend commentary.

### 3.5 [OIL PRODUCERS TABLE] — all producers, unified

```
code        mbpd    world share    current level
--------    ----    -----------    -------------
columbia    13.0    31.7%          na
solaria     10.0    24.4%          normal
sarmatia    10.0    24.4%          normal
persia       3.5     8.5%          normal
mirage       3.5     8.5%          normal
caribe       0.8     2.0%          normal
```

One row per oil producer (`oil_producer = true` AND `mbpd > 0`). `current level` is `na` for non-OPEC+ members (Columbia) and one of `min/low/normal/high/max` for OPEC+ members (the 5 canonical members). Data only, no annotations.

### 3.6 [CHOKEPOINT BLOCKADES]

```
gulf_gate:       none | partial | full   (affects solaria, mirage, persia)
caribe_passage:  none | partial | full   (affects caribe)
formosa_strait:  none | partial | full   (affects global semiconductor supply)
```

Sourced from the `blockades` state table + `chokepoint_status` dict. Current status only.

### 3.7 [SANCTIONS ON PRODUCERS]

```
columbia   : none
solaria    : none
sarmatia   : L3 (from 10 sanctioners incl. columbia, gallia, albion...)
persia     : L3 (from 4 sanctioners incl. columbia, levantia...)
mirage     : none
caribe     : none
```

One row per oil producer showing the maximum sanctions level imposed on them (any sanctioner). L2+ triggers the −10% × share supply penalty in `calc_oil_price`.

### 3.8 [TARIFFS ON PRODUCERS]

```
Tariffs imposed BY or ON oil producers (active rows from tariffs table):
  columbia → persia      L3
  columbia → caribe      L3
  cathay   → columbia    L2
  ...
```

Only tariff rows where at least one side is an oil producer. Data only.

### 3.9 [DECISION RULES]

```
HOW OPEC+ WORKS
- 5 members (caribe, mirage, persia, sarmatia, solaria) collectively control a majority of world oil
- Each member picks ONE level per round: min / low / normal / high / max
- Engine applies 2× cartel leverage on top of each member's share of world oil
- Effect is on the world oil price → cascades to every country's GDP, revenue, inflation
- Cuts (min/low) push price UP; floods (high/max) push price DOWN

YOUR AUTHORITY
- Only OPEC+ members can submit set_opec (you are one)
- Your decision affects every oil-importing and oil-exporting country

DECISION RULES
- decision="change"    → must include changes.production_level with one of min/low/normal/high/max
- decision="no_change" → must OMIT the changes field entirely
- rationale ≥30 chars REQUIRED in both cases
- Non-OPEC members are rejected with NOT_OPEC_MEMBER

REMINDER — no_change is a legitimate choice
Market churn is expensive and signals weakness. If current level still serves
your goals, no_change with a clear rationale is the correct answer.
```

### 3.10 [INSTRUCTION]

```
Decide whether to CHANGE your OPEC+ production level or keep it NO_CHANGE.
Either way you MUST provide a rationale of at least 30 characters explaining WHY.

Respond with JSON ONLY, matching the schema in CONTRACT_OPEC §2.
```

### 3.8 What the system does NOT provide

| Layer | Provided by |
|---|---|
| Identity / character / personality | AI Participant Module (future) |
| Memory / self-curated round history | AI Participant Module (future) |
| Strategic objectives / goals | AI Participant Module (future) |
| General SIM mechanics (Block 1) | AI Participant Module (future) |
| Quantitative forecast of oil price if you change level | Deferred — participants learn by doing |

---

## 4. VALIDATION RULES

Pure function `validate_opec_decision(payload) → {valid, errors, warnings, normalized}`. All errors collected in one pass.

### 4.1 Error codes

| Code | Rule | Trigger |
|---|---|---|
| `INVALID_PAYLOAD` | top-level must be a dict | non-dict input |
| `INVALID_ACTION_TYPE` | `action_type == "set_opec"` | missing or wrong value |
| `INVALID_DECISION` | `decision in {"change", "no_change"}` | missing or wrong value |
| `RATIONALE_TOO_SHORT` | rationale string ≥ 30 chars after strip | missing, non-string, or too short |
| `MISSING_CHANGES` | `decision=="change"` requires `changes.production_level` | change without changes; non-dict changes |
| `UNEXPECTED_CHANGES` | `decision=="no_change"` must omit the `changes` field | `no_change` with `changes` present |
| `INVALID_LEVEL` | `production_level` must be one of `{min, low, normal, high, max}` | wrong value or missing |
| `UNKNOWN_FIELD` | top-level or changes-level keys must be in the allowed set | extra fields |
| `NOT_OPEC_MEMBER` | `country_code` must be in the canonical OPEC+ roster | non-member trying to submit |

### 4.2 Allowed fields

Top level: `action_type`, `country_code`, `round_num`, `decision`, `rationale`, `changes`.
Inside `changes`: `production_level` (only).

### 4.3 Canonical OPEC+ roster

```python
CANONICAL_OPEC_MEMBERS: frozenset[str] = frozenset({
    "caribe", "mirage", "persia", "sarmatia", "solaria",
})
```

5 members. Sourced from `countries.opec_member = true` as of 2026-04-10 AFTER the data fix in this slice (Caribe/Venezuela was incorrectly `false` — corrected by this migration, Sarmatia was already `true`). The `OPEC_MEMBERS` constant in `engine/agents/full_round_runner.py` (currently `{solaria, persia, mirage, caribe}`) is also updated to match: add `sarmatia`, keep `caribe`.

### 4.4 Normalized output (when valid)

```json
{
  "action_type": "set_opec",
  "country_code": "solaria",
  "round_num": 3,
  "decision": "change",
  "rationale": "<trimmed string>",
  "changes": { "production_level": "min" }
}
```

For `no_change`, the `changes` field is omitted. Country codes lowercased. Whitespace stripped.

---

## 5. PERSISTENCE

### 5.1 Two columns on `country_states_per_round`

| Column | Purpose | Mutated by |
|---|---|---|
| **`opec_production`** (existing, text) | Canonical live value — the current production level the engine reads each round. One of `min/low/normal/high/max` for OPEC+ members, or `"na"` for non-members. | `resolve_round` set_opec handler |
| **`opec_decision`** (NEW, JSONB, 2026-04-10) | Per-round audit record of the submitted decision, including `no_change` decisions with rationale. | `resolve_round` set_opec handler |

### 5.2 DB migration

Migration name: `opec_v1_canonical_schema`

Changes:
- **Add** `country_states_per_round.opec_decision jsonb` (NEW audit column)
- **Fix `countries.opec_member`:** set Caribe (Venezuela) to `true` (currently incorrectly `false`)
- **Fix R0 snapshot pollution:** set `opec_production = 'na'` for all non-OPEC-member rows at round 0 (currently all 20 countries have `"normal"` including non-members)
- **Update** `engine/agents/full_round_runner.py:OPEC_MEMBERS` to match the corrected DB: `{"caribe", "mirage", "persia", "sarmatia", "solaria"}` (add sarmatia, keep caribe)

### 5.3 Write path (resolve_round set_opec handler)

```
1. Build full envelope payload from the agent_decisions row
2. Call validate_opec_decision(payload)
3. If invalid:
     - Log warning
     - Emit observatory_event(type="opec_rejected", country, payload, errors)
     - DO NOT touch opec_production or opec_decision columns
4. If valid and decision == "no_change":
     - Write {"decision": "no_change", "rationale": "..."} to
       country_states_per_round.opec_decision for (country, round)
     - DO NOT touch opec_production column (carry-forward by inaction)
5. If valid and decision == "change":
     - Write normalized production_level value to country_states_per_round.opec_production
     - Write the full normalized payload to country_states_per_round.opec_decision
```

### 5.4 Read path

The engine reads `opec_production` from `country_states_per_round` via `round_tick._load_state_from_tables` (existing behavior, unchanged). The new `opec_decision` JSONB column is read only by the context builder (Step 5) and observatory queries (future).

---

## 6. ENGINE BEHAVIOR

**UNCHANGED.** This is a contract-around-existing-behavior slice (like tariffs). The sanctions slice had to rewrite the engine; OPEC does not.

The relevant function is `app/engine/engines/economic.py:calc_oil_price()` (around line 622). The OPEC section is lines 650-659:

```python
# OPEC production decisions (weighted by actual production share)
# OPEC controls ~40-50% of global oil — their decisions move markets significantly
supply = 1.0
if total_production > 0:
    for member, decision in opec_production.items():
        if member in producer_output:
            share = producer_output[member] / total_production
            multiplier = OPEC_PRODUCTION_MULTIPLIER.get(decision, 1.0)
            # 2× amplifier: OPEC decisions have outsized market impact (cartel leverage)
            supply += (multiplier - 1.0) * share * 2.0
```

Constants (locked in L1 regression tests):

```python
OPEC_PRODUCTION_MULTIPLIER: dict[str, float] = {
    "min": 0.70, "low": 0.85, "normal": 1.00, "high": 1.15, "max": 1.30,
}
```

**2× cartel leverage amplifier** is the critical calibration — OPEC's outsized influence on markets.

**Important engine-level design note:** the engine iterates the `opec_production` dict keys and checks `if member in producer_output` (oil_producer + mbpd > 0). It does NOT check `opec_member`. This means membership enforcement happens at the validator + resolve_round handler layer, not the engine layer. This is fine for v1.0 — the validator rejects non-members, so the engine's dict never contains non-OPEC actors with a set level (they carry forward as `"na"` which the engine ignores).

**Related effects (separate mechanisms, unchanged):**
- **Sanctions on oil producers (L2+)** reduce supply by 10% × share (per CARD_FORMULAS A.1 + SANCTIONS slice)
- **Gulf Gate / Caribe / Formosa blockades** reduce effective mbpd for affected producers
- **Oil revenue** to each producer: `price × effective_mbpd × 0.009` per round

---

## 7. WHAT IS OUT OF SCOPE FOR THIS SLICE

- **Cognitive blocks** (rules/identity/memory/goals) — AI Participant Module (future)
- **AI agent persistence** — AI Participant Module v1.0 (separate phase block)
- **Any change to `calc_oil_price` or its constants** (OPEC multipliers, cartel leverage 2×, blockade %, price inertia, etc.) — engine is locked, changes require separate ticket
- **Multilateral OPEC coordination mechanism** — coordination happens via diplomacy outside the schema; the contract is per-member
- **Quantitative price forecast in the context package** — deferred, participants learn by doing
- **Expanding OPEC+ roster mid-sim** — membership is Template data, not per-round
- **Columbia/Caribe joining OPEC+** — not in scope; they're free-agent producers
- **Legacy `set_opec` (current handler with `production_level` field) compatibility** — we KEEP the same field name and same handler shell, just add validation + audit. No breaking changes.

---

## 8. STANDARD OUTPUT (what the engine produces)

Per member decision submitted, the engine produces:

- **`country_states_per_round.opec_production`** (text) — the member's current level, read each round by `calc_oil_price`
- **`country_states_per_round.opec_decision`** (JSONB) — the audit envelope
- **Global oil price** — recomputed each round by `calc_oil_price` based on aggregate OPEC+ levels + sanctions on producers + blockades. Persisted in `global_state_per_round.oil_price`.
- **Cascading effects on all countries:**
  - Oil revenue (producers): `price × effective_mbpd × 0.009`
  - Oil shock on GDP growth (importers): `-2% × (oil_delta / 50) × import_exposure`
  - Oil shock on GDP growth (producers): `+1% × (oil_delta / 50) × resource_pct × 3`
  - Inflation pressure (importers): tied to oil price delta

Tests assert against:
- The `opec_production` column on the snapshot (matches normalized level)
- The `opec_decision` JSONB column (matches submitted decision byte-for-byte)
- The `oil_price` column on `global_state_per_round` (recomputed after the decision)
- Non-member rejection: `opec_rejected` observatory event + no column changes

---

## 9. ACCEPTANCE CRITERIA

- [ ] **Step 1 — Contract** — this document (IN PROGRESS pending Marat review)
- [ ] **Step 2 — Validator (L1)** — `opec_validator.py` with 9 error codes; `CANONICAL_OPEC_MEMBERS` frozenset; L1 tests
- [ ] **Step 3 — Engine regression lock (L1)** — canonical examples pinning `OPEC_PRODUCTION_MULTIPLIER` constants + 2× cartel leverage + per-member supply contribution
- [ ] **Step 4 — Persistence (L2)** — migration applied (opec_decision JSONB + R0 cleanup + OPEC_MEMBERS code fix); set_opec handler rewritten with validator; L2 tests for change / no_change / invalid / non-member rejection
- [ ] **Step 5 — Decision-specific context (L2)** — `opec_context.py` with economic state + oil market state + OPEC+ coalition table + non-OPEC producer table + decision rules; L2 tests
- [ ] **Step 6 — AI skill harness (L3)** — D4 prompt updated to v1.0 schema (production_level field, fixed OPEC+ roster including Sarmatia, ≥30 char rationale); persona stub; validates via real production validator
- [ ] **Step 7 — AI acceptance gate (L3)** — `test_opec_full_chain_ai.py`: real LLM → validator → DB → engine → snapshot, no fixup. Verify opec_production column updated, opec_decision JSONB matches, oil_price recomputed.
- [ ] **Closing** — CHECKPOINT_OPEC.md, CARD_FORMULAS A.1 touch-up (if needed), CARD_ACTIONS 2.4 rewritten with v1.0 schema, PHASE.md + CHANGES_LOG milestone, CONTRACT_OPEC marked 🔒 LOCKED, commit

---

## 10. CHANGE LOG

- **v1.0 🔒 LOCKED (2026-04-11)** — Slice complete end-to-end. 82 tests green (L1 67: 47 validator + 20 engine regression / L2 14: 4 persistence + 10 context / L3 1 acceptance gate). DB migration `opec_v1_canonical_schema` applied (opec_decision JSONB added, Caribe/Venezuela OPEC+ membership corrected, R0 snapshot pollution cleaned). Engine math unchanged, constants pinned. See `CHECKPOINT_OPEC.md`.
- **v1.0-rev2 (2026-04-10)** — Context §3 rewritten per Marat's data-only directive: removed commentary, unified oil producers table (including non-OPEC Columbia), added chokepoint blockades + sanctions on producers + tariffs on producers blocks, added full oil price history (all rounds played). Caribe (Venezuela) confirmed as OPEC+ member (5 members total: Caribe, Mirage, Persia, Sarmatia, Solaria). no_change reminder kept.
- **v1.0 (2026-04-10)** — Initial draft.
