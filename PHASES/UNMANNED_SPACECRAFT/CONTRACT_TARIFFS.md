# CONTRACT: Tariff Decision

**Status:** 🔒 **LOCKED** (2026-04-10) — canonical reference, frozen for the Unmanned Spacecraft phase.
Engine (UNCHANGED — behavior locked, not redesigned), validator, persistence, context builder, tests, and human UI (future) MUST all match this document. Any change requires (a) Marat's explicit approval, (b) a version bump, and (c) reconciliation of all listed consumers in the same commit. If code and this contract disagree: STOP, update one to match the other, then proceed.

**Version:** 1.0 (2026-04-10)
**Verified end-to-end:** 2026-04-10 — L1 (63 tests) + L2 (10 tests) + L3 (10 AI decisions + 1 acceptance gate) all passing. See `CHECKPOINT_TARIFFS.md`.
**Owner:** Marat
**Slice methodology:** `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` (the 7-step template)
**Will be used by** (when slice is complete):
- Engine: `app/engine/engines/economic.py` (`calc_tariff_coefficient`) — **UNCHANGED**, this slice locks a contract around existing engine behavior
- Validator: `app/engine/services/tariff_validator.py` (NEW)
- Context builder: `app/engine/services/tariff_context.py` (NEW — read-only, no dry-run)
- Persistence: `app/engine/round_engine/resolve_round.py` (set_tariffs handler) + `tariffs` state table (existing) + `country_states_per_round.tariff_decision` JSONB (NEW column)
- Tests: `app/tests/layer1/test_tariff_validator.py`, `app/tests/layer1/test_tariff_engine.py`, `app/tests/layer2/test_tariff_persistence.py`, `app/tests/layer2/test_tariff_context.py`, `app/tests/layer2/test_tariff_e2e.py`, `app/tests/layer3/test_skill_mandatory_decisions.py` (D3), `app/tests/layer3/test_tariffs_full_chain_ai.py`
- Human UI (future — not yet implemented)

---

## 1. PURPOSE

A country's tariff decision is submitted at the end of each round. It declares the country's bilateral tariff posture toward any subset of the other 19 countries. The engine consumes this decision, computes per-country GDP coefficients for both imposer and target, customs revenue for the imposer, and bilateral inflation pressure.

**Key design principles:**

1. **Tariffs are bilateral and asymmetric.** A country can impose L0 on Teutonia and L3 on Cathay simultaneously. The matrix is not symmetric (Cathay's tariff on Columbia is independent of Columbia's on Cathay).
2. **Tariffs are a possibility, not an obligation.** `no_change` is a fully legitimate explicit choice and is what a participant should pick if their current posture still serves their goals. Tariff churn for the sake of churn is bad strategy and the contract makes that obvious.
3. **One submission carries the country's full intent for the round.** The schema is designed so a participant deliberates "my trade posture this round" once, not "my Cathay tariff" + "my Persia tariff" + "my Bharata tariff" as three independent actions.
4. **Sparse changes, persistent state.** A `change` decision names only the targets the participant wants to *modify*. All untouched targets keep their previous level via the `tariffs` state table — same carry-forward mechanic the engine already uses for sanctions.
5. **No forecast in the context package.** Tariff consequences are diplomatically and economically emergent (retaliation, coalition shifts, contagion). A one-round dry-run forecast would be misleadingly precise. Participants learn by doing (round-N outcomes inform round-N+1) or task intelligence (a future skill, out of scope here).
6. **Decision-specific context only — no cognitive layer in this contract.** The system supplies what the participant needs to know about THIS decision (own state, counterparties, current state of the dimension, decision rules). The participant's cognitive context (identity, memory, goals, world rules) belongs to the AI Participant Module (future) for AI participants or the human UI (future) for humans. The two layers are deliberately separated. Tests emulate the cognitive layer with a hand-crafted persona stub that lives only in the test harness.

---

## 2. DECISION SCHEMA

### 2.1 The decision object

```json
{
  "action_type": "set_tariffs",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change" | "no_change",
  "rationale": "string, >= 30 chars, required in both cases",
  "changes": {
    "tariffs": {
      "cathay": 3,
      "caribe": 1
    }
  }
}
```

### 2.2 Field specifications

| Field | Type | Values | Required | Semantics |
|---|---|---|---|---|
| `action_type` | string | `"set_tariffs"` (PLURAL) | yes | Action identifier. Note plural — distinct from the legacy singular `set_tariff` action which still works in parallel during migration. |
| `country_code` | string | canonical country code | yes | Decision owner (the imposer) |
| `round_num` | int | ≥ 0 | yes | Round this decision applies to |
| `decision` | string | `"change"` or `"no_change"` | yes | Explicit choice. `no_change` is fully legitimate. |
| `rationale` | string | ≥ 30 chars | yes | Required even for `no_change` — forces explicit reasoning. No silent defaults. |
| `changes` | object | see §2.3 | only if `decision=="change"` | Must be absent (not null, not `{}`) when `no_change`. |

### 2.3 The `changes` object

```
changes: {
  tariffs: { <target_country_code>: int 0..3, ... }   # SPARSE
}
```

- **`changes.tariffs` is a flat dict** mapping target country codes to integer levels.
- **It is SPARSE.** Only countries the participant wants to *change* appear. All other targets keep their previous level via the `tariffs` state table.
- **Setting a target to `0` means LIFT.** No separate `lift_tariff` semantic. The persistence layer upserts the row with `level=0` (the engine treats 0 as no tariff).
- **At least one entry required when `decision=="change"`.** An empty `tariffs` dict is invalid (`EMPTY_CHANGES`). Use `no_change` instead.
- **Self-tariff forbidden.** `tariffs.<own_country_code>` is invalid (`SELF_TARIFF`).
- **Unknown target forbidden.** Target must be in the canonical 20-country roster (`UNKNOWN_TARGET`).

### 2.4 Tariff level scale

| Level | Name | Effect (per CARD_FORMULAS A.3) |
|---|---|---|
| `0` | none / lift | No tariff. Engine treats as removed. |
| `1` | light | `intensity = 0.33`. Mild GDP drag both sides. Small customs revenue. |
| `2` | moderate | `intensity = 0.67`. Significant bilateral disruption + inflation pressure. |
| `3` | heavy / embargo | `intensity = 1.00`. Near trade cutoff. Hurts both sides asymmetrically (target more, imposer less via `TARIFF_IMPOSER_FRACTION = 0.5`). |

The level scale is **identical** to the existing engine — this slice locks the contract around behavior that already works. No engine math changes. See §6 for the unchanged formula.

### 2.5 No_change example

```json
{
  "action_type": "set_tariffs",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "no_change",
  "rationale": "Current bilateral posture (L3 on Persia/Caribe wartime, L2 on Cathay retaliatory, L0 with allies) still serves containment objectives. No new escalation justified this round."
}
```

Note: NO `changes` field. Just `decision`, `rationale`, and the envelope.

---

## 3. CONTEXT PROVIDED TO DECISION-MAKER (decision-specific only)

This contract specifies what the **SYSTEM** supplies to the participant about THIS decision. The participant's **cognitive context** (identity, memory, goals, world rules) is OUT OF SCOPE — that is the responsibility of the AI Participant Module (future) for AI participants, or the human UI (future) for humans. The two layers are deliberately separated so each can be built and tested independently.

> **Strategy note (2026-04-10):** This phase ships engines + contracts + DBs + decision-specific contexts for *every* SIM activity, one at a time. The AI Participant Module v1.0 (cognitive persistence, self-curated memory, goal evolution, rehydration) is built afterwards on top of a complete substrate. Until then, L3 tests emulate the cognitive layer with a hand-crafted persona stub that lives only in the test harness. See `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` "Boundary statement."

### 3.1 What the system provides

The communication layer assembles a structured dict from DB state. Same payload for AI or human — different rendering by the consumer (skill harness, UI).

```
[ECONOMIC STATE]                  ← own country snapshot for the round
[ALL 20 COUNTRIES]                ← full roster, every country is a possible target
[CURRENT TARIFFS — IMPOSED BY ME] ← bilateral, the rows you can change
[CURRENT TARIFFS — IMPOSED ON ME] ← bilateral, informational only
[DECISION RULES]                  ← schema, validation rules summary, no_change reminder
[INSTRUCTION]                     ← what decision is needed
```

### 3.2 [ECONOMIC STATE] — own country snapshot

```
GDP:               {gdp}
Treasury:          {treasury}
Inflation:         {inflation}%
Sector mix:        resources {pct} | industry {pct} | services {pct} | tech {pct}
Trade balance:     {trade_balance}
Oil:               {producer/importer, mbpd if producer}
Stability:         {stability}/10
Political support: {political_support}%
```

### 3.3 [ALL 20 COUNTRIES] — full roster

The participant must be able to consider ANY country as a target (or as a "should I lift?" candidate). The system provides one line per country, never a filtered subset.

```
ALL 20 COUNTRIES (the full roster — anyone is a possible target)

  code        GDP    sector profile        relationship   trade-rank w/ me
  ----        ----   ------------------    ------------   ----------------
  cathay      245    industrial / mfg      tense           #1
  teutonia    48     services / industry   allied          #2
  bharata     34     industrial / serv     friendly        #3
  yamato      42     tech / services       allied          #4
  ...
  (all 20 listed)
```

- **`sector profile`** — short label derived from the dominant 1-2 sectors in `countries.sector_*`.
- **`relationship`** — 8-state diplomatic status from the `relationships` table (allied / friendly / neutral / tense / hostile / military_conflict / armistice / peace).
- **`trade-rank`** — 1..19 ordering from `derive_trade_weights(countries)[me][target]`. Already-trusted runtime function used by sanctions, contagion, and revenue. No new data needed.

### 3.4 [CURRENT TARIFFS — IMPOSED BY ME]

Read from the `tariffs` state table. These are the rows the participant can change.

```
CURRENT TARIFFS — IMPOSED BY ME (you can change these)
  cathay   L2  (set R1, "Retaliatory")
  persia   L3  (set R0, "Wartime")
  caribe   L3  (set R0, "Energy blockade")
  sarmatia L2  (set R0, "Sanctions-aligned")
  (or "(none — you currently impose no tariffs)")
```

Each line: target, level, since-round, notes (from `tariffs.notes`).

### 3.5 [CURRENT TARIFFS — IMPOSED ON ME]

```
CURRENT TARIFFS — IMPOSED ON ME (informational only — you cannot change these)
  cathay   L2  (since R0)
  persia   L2  (since R1)
  caribe   L1  (since R1, "Counter-sanctions symbolic")
  (or "(none — no country currently tariffs you)")
```

### 3.6 [DECISION RULES] — schema reminder + no_change reminder

```
HOW TARIFFS WORK (mechanically)
- Bilateral. Set a level (0-3) for any subset of the other 19 countries.
- Levels: 0 = none / lift, 1 = light, 2 = moderate, 3 = heavy / near-embargo.
- As imposer you get: customs revenue + small self-damage + inflation pressure.
- As target you get: GDP hit proportional to imposer's market share.
- Setting a target to 0 LIFTS the tariff. No separate "lift" action.
- Untouched targets keep their previous level (carry-forward).
- Trade agreements (separate action) override tariffs between signatories.

DECISION RULES
- decision="change"    → must include changes.tariffs with ≥1 (target, level) entry
- decision="no_change" → must OMIT the changes field entirely
- rationale ≥30 chars REQUIRED in both cases
- self-tariff and unknown-target are validation errors

REMINDER — no_change is a legitimate choice
Tariffs are a possibility, not an obligation. If your current posture still
serves your goals, no_change is the right answer with a clear rationale.
Do not invent changes for the sake of action.
```

### 3.7 [INSTRUCTION]

```
Decide whether to CHANGE your tariff posture or keep it NO_CHANGE.
Either way you MUST provide a rationale of at least 30 characters
explaining WHY.

Respond with JSON ONLY, matching the schema in CONTRACT_TARIFFS §2.
```

### 3.8 What the system does NOT provide (out of contract scope)

| Layer | Provided by |
|---|---|
| Identity / character / personality | AI Participant Module (future) |
| Memory / self-curated round history / interpreted events | AI Participant Module (future) |
| Strategic objectives / goals / round intentions | AI Participant Module (future) |
| General SIM mechanics knowledge (Block 1 / world rules) | AI Participant Module (future) |
| Authority constraints (per-role permissions) | AI Participant Module (future) |

### 3.9 Testing convention (until AI Participant Module v1.0 lands)

L3 tests emulate the cognitive layer with a **hand-crafted persona stub** in the test harness — a few sentences of character + objectives stapled to the LLM system prompt. This is explicitly a TEST FIXTURE, not part of the contract. When the AI Participant Module ships, the stub is replaced by `agent.get_cognitive_state()` and **this contract is unchanged**.

The boundary is strict: the **decision-specific context** in §3.1-3.7 is what the SYSTEM serves. Anything cognitive in the test prompt comes from the persona stub, not from `tariff_context.py`.

---

## 4. VALIDATION RULES

The validator is a pure function `validate_tariffs_decision(payload) → {valid, errors, warnings, normalized}`. **All errors are collected in a single pass.** The validator does not stop at the first failure.

### 4.1 Error codes

| Code | Rule | Trigger |
|---|---|---|
| `INVALID_PAYLOAD` | top-level must be a dict | non-dict input |
| `INVALID_ACTION_TYPE` | `action_type == "set_tariffs"` | missing or wrong value |
| `INVALID_DECISION` | `decision in {"change", "no_change"}` | missing or wrong value |
| `RATIONALE_TOO_SHORT` | rationale string ≥ 30 chars after strip | missing, non-string, or too short |
| `MISSING_CHANGES` | `decision=="change"` requires `changes.tariffs` (a dict) | change without changes; non-dict changes; non-dict tariffs |
| `UNEXPECTED_CHANGES` | `decision=="no_change"` must omit the `changes` field | `no_change` with `changes` present |
| `EMPTY_CHANGES` | `decision=="change"` with `changes.tariffs == {}` | empty tariffs dict on a change |
| `UNKNOWN_FIELD` | top-level or changes-level keys must be in the allowed set | extra fields anywhere |
| `INVALID_LEVEL` | every value in `changes.tariffs` must be `int in [0, 3]` | non-int, out-of-range, bool, str |
| `UNKNOWN_TARGET` | target must be in the canonical country roster | unknown country code |
| `SELF_TARIFF` | imposer (`country_code`) cannot tariff itself | self in tariffs dict |

### 4.2 Allowed fields

Top level: `action_type`, `country_code`, `round_num`, `decision`, `rationale`, `changes`.
Inside `changes`: `tariffs` (only — no other fields).

### 4.3 Normalized output (when valid)

```json
{
  "action_type": "set_tariffs",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change",
  "rationale": "<trimmed string>",
  "changes": { "tariffs": { "cathay": 3, "caribe": 1 } }
}
```

For `no_change`, the `changes` field is omitted.
Levels are coerced to `int`. Country codes are lowercased. Extra whitespace stripped.

---

## 5. PERSISTENCE

### 5.1 The two storage layers

| Layer | Purpose | Mutated by |
|---|---|---|
| **`tariffs` state table** (existing) | Canonical world state — current bilateral level for every (imposer, target) pair. Read by the engine each round via `_load_state_from_tables`. | `resolve_round` set_tariffs handler |
| **`country_states_per_round.tariff_decision` JSONB** (NEW column, this slice) | Per-round audit record of the decision the participant submitted, including `no_change` decisions with rationale. Used for replay, observatory, and "what did this AI actually decide last round" lookups. | `resolve_round` set_tariffs handler |

### 5.2 The DB migration (the only schema change in this slice)

```sql
ALTER TABLE country_states_per_round
  ADD COLUMN IF NOT EXISTS tariff_decision jsonb;

COMMENT ON COLUMN country_states_per_round.tariff_decision IS
  'Per-round record of the set_tariffs decision (CONTRACT_TARIFFS v1.0). '
  'Stores the normalized decision payload including no_change with rationale. '
  'Canonical world state lives in the tariffs table; this column is the audit trail.';
```

No backfill needed — existing rows are NULL until a decision is recorded.

### 5.3 Write path (resolve_round set_tariffs handler)

```
1. Build full envelope payload (action_type, country_code, round_num,
   decision, rationale, changes if any) from the agent_decisions row.
2. Call validate_tariffs_decision(payload).
3. If invalid:
     - Log warning
     - Emit observatory_event(type="tariff_rejected", country, payload, errors)
     - DO NOT touch the tariffs table or tariff_decision column.
4. If valid and decision == "no_change":
     - Write {"decision": "no_change", "rationale": "..."} to
       country_states_per_round.tariff_decision for (country, round).
     - DO NOT touch the tariffs table — carry-forward by inaction.
5. If valid and decision == "change":
     - For each (target, level) in normalized changes.tariffs:
         upsert tariffs (sim_run_id, country, target, level)
         on_conflict (sim_run_id, imposer, target) do update.
         level=0 is allowed and means "lifted" (engine treats as no tariff).
     - Write the full normalized payload to
       country_states_per_round.tariff_decision for (country, round).
```

### 5.4 Read path

The engine reads `tariffs` state table via the existing `_load_state_from_tables` in `round_tick.py`. **No changes to round_tick.py for this slice.** The new `tariff_decision` column is read only by the context builder (Step 5) and observatory queries (future).

---

## 6. ENGINE BEHAVIOR

**UNCHANGED.** This is the key design point of the slice — the engine math is already correct. The slice locks a contract around it.

The relevant function is `app/engine/engines/economic.py:calc_tariff_coefficient()` (currently around line 904). It's called per country, per round, by `process_economy`. It reads bilateral tariffs from the actions dict (which `_load_state_from_tables` populates from the `tariffs` table) and returns `(coefficient, inflation_add, customs_revenue)`.

For reference, the formula (from CARD_FORMULAS A.3):

```
Constants: TARIFF_K=0.54, TARIFF_IMPOSER_FRACTION=0.50,
           TARIFF_REVENUE_RATE=0.075, TARIFF_INFLATION_RATE=12.5

For each tariff I IMPOSE (target_id, level):
  intensity        = level / 3.0
  target_share     = target_starting_gdp / total_starting_gdp
  my_exposure      = (|my_trade_balance| + 0.25 * my_gdp) / my_gdp
  target_exposure  = (|target_trade_balance| + 0.25 * target_gdp) / target_gdp

  self_damage      = target_share * my_exposure * intensity * 0.54 * 0.50
  customs_revenue += target_gdp * target_exposure * intensity * 0.075
  inflation_add   += intensity * target_share * 12.5
  total_gdp_hit   += self_damage

For each tariff IMPOSED ON ME by imposer_id:
  intensity        = level / 3.0
  imposer_share    = imposer_starting_gdp / total_starting_gdp
  target_damage    = imposer_share * my_exposure * intensity * 0.54
  total_gdp_hit   += target_damage

coefficient = max(0.80, 1.0 - total_gdp_hit)
```

This formula and its constants are **OUT OF SCOPE** for this slice. Any future change requires a separate ticket and either a new contract version or a CARD_FORMULAS revision.

### 6.1 Write-back

The engine writes the new `tariff_coefficient` (a numeric column) to `country_states_per_round` via the existing `round_tick.py` write-back payload. **No new write-back code needed** — the column already exists and is already written.

### 6.2 Customs revenue and inflation

`customs_revenue` and `inflation_add` are returned from `calc_tariff_coefficient` and applied to the country's economic state in `process_economy` Step 1 (already wired). **No new code needed.**

---

## 7. WHAT IS OUT OF SCOPE FOR THIS SLICE

- **Cognitive blocks** (rules/identity/memory/goals) — provided by the AI Participant Module (future), NOT by this contract. This contract specifies only the decision-specific context the SYSTEM supplies.
- **AI agent persistence** (cognitive_states table, save/load, self-curated memory loop, goal evolution, agent rehydration) — covered by AI Participant Module v1.0 in a later phase block. This slice does NOT touch the AI module or assemble cognitive context from world data.
- Any change to `calc_tariff_coefficient` or its constants (TARIFF_K, TARIFF_IMPOSER_FRACTION, TARIFF_REVENUE_RATE, TARIFF_INFLATION_RATE)
- Trade agreement actions (`trade_agreement` is a separate action and a separate slice)
- Tariff carve-outs by sector or commodity (always whole-country for now)
- Multilateral coalition logic (coalition effects emerge from individual decisions; no explicit coalition contract)
- Dropping or deprecating the legacy `set_tariff` (singular) or `lift_tariff` actions — they keep working in parallel; new `set_tariffs` is the canonical path going forward
- Schema cleanup of `tariffs.notes` text field
- Forecast / dry-run preview of tariff consequences (deferred — participants learn by doing or task intelligence)
- A `tariff_history` query API (future)
- Rendering the context package as text — that's the responsibility of the caller (skill harness for AI, UI for human)

---

## 8. STANDARD OUTPUT (what the engine produces)

The engine doesn't produce a "tariff result object" the way budget produces a `BudgetResult` — tariff effects are folded into the existing `CountryEconomicResult`:

```
CountryEconomicResult (per country, per round):
  tariffs: TariffResult(
    cost_as_imposer:    float,
    revenue_as_imposer: float,
    cost_as_target:     float,
    net_gdp_cost:       float,
  )
  ...other fields (gdp, revenue, budget, sanctions, ...)
```

Plus the per-country numeric column `country_states_per_round.tariff_coefficient` (already exists, populated each round).

Tests assert against:
- The `tariff_coefficient` column on the snapshot (matches hand-computed value)
- The `customs_revenue` reflected in `treasury` delta
- The `inflation_add` reflected in `inflation` delta
- The `tariff_decision` JSONB column (matches submitted decision byte-for-byte)
- The `tariffs` state table rows (upserted with new levels; carry-forward for untouched targets)

---

## 9. ACCEPTANCE CRITERIA

Before marking the slice DONE:

- [ ] **Step 1 — Contract** — this document, reviewed and locked
- [ ] **Step 2 — Validator (L1)** — all 11 error codes covered, valid examples accepted, normalized output matches §4.3
- [ ] **Step 3 — Engine regression lock (L1)** — canonical examples lock current `calc_tariff_coefficient` behavior so future changes are visible
- [ ] **Step 4 — Persistence (L2)** — migration applied; round-trip test passes; `no_change` carries forward; level=0 lifts row; invalid rejected with observatory event
- [ ] **Step 5 — Decision-specific context (L2)** — all decision-specific blocks present (economic state, all 20 countries, current bilateral tariffs both directions, decision rules incl. no_change reminder, instruction); trade-rank derived from `derive_trade_weights`; **NO cognitive blocks** (those belong to AI Participant Module future work)
- [ ] **Step 6 — AI skill harness (L3)** — D3 prompt updated to v1.0 schema; persona stub used for cognitive layer (test fixture only); 10 leaders produce valid decisions through the production validator; scripted e2e test passes
- [ ] **Step 7 — AI acceptance gate (L3)** — `test_tariffs_full_chain_ai.py`: real LLM → validator → DB → engine → snapshot, no fixup; tariff_decision JSONB matches; tariffs table updated; tariff_coefficient changed in snapshot
- [ ] **Closing** — CHECKPOINT_TARIFFS.md written; CARD_FORMULAS A.3 + CARD_ACTIONS 2.2 reconciled; PHASE.md updated; CHANGES_LOG.md milestone entry; CONTRACT_TARIFFS marked 🔒 LOCKED; VERTICAL_SLICE_PATTERN.md updated with the "Boundary statement"; commit

---

## 10. CHANGE LOG

- **v1.0 🔒 LOCKED (2026-04-10)** — Slice complete end-to-end. 84 tests green (L1 validator 41, L1 engine regression 22, L2 persistence 4, L2 context 6, L3 AI 10, L3 acceptance gate 1). See `CHECKPOINT_TARIFFS.md`.
- **v1.0-rev2 (2026-04-10)** — Strategy correction: cognitive blocks (rules/identity/memory/goals) removed from §3 per Marat's directive. The system supplies decision-specific context only; cognitive layer is the responsibility of the AI Participant Module (future). §3 rewritten, §7 updated, §9 acceptance criteria adjusted. This boundary applies to ALL decision slices going forward and is recorded in `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md`.
- **v1.0 (2026-04-10)** — Initial draft. Pending Marat's 5-minute review before Step 2.
