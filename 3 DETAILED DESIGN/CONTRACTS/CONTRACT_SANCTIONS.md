# CONTRACT: Sanctions Decision

**Status:** 🔒 **LOCKED** (2026-04-10) — canonical reference, frozen for the Unmanned Spacecraft phase.
Engine, validator, persistence, context builder, tests, and human UI (future) MUST all match this document. Any change requires (a) Marat's explicit approval, (b) a version bump, and (c) reconciliation of all listed consumers in the same commit.

**Version:** 1.0 (2026-04-10)
**Owner:** Marat
**Engine rewritten 2026-04-10** — the old `calc_sanctions_coefficient` (with trade_openness + global 0.87 ceiling + sector_vulnerability multiplier) was replaced with a simpler sector-derived ceiling model. Regression guards: `app/tests/layer1/test_sanctions_engine.py` (27 tests).
**Used by:**
- Engine: `app/engine/engines/economic.py` (`calc_sanctions_coefficient`, `_sanctions_max_damage`)
- Validator: `app/engine/services/sanction_validator.py`
- Context builder: `app/engine/services/sanction_context.py` (decision-specific only, no dry-run)
- Persistence: `app/engine/round_engine/resolve_round.py` (set_sanctions handler) + existing `sanctions` state table + `country_states_per_round.sanction_decision` JSONB column (new 2026-04-10)
- Tests: `app/tests/layer1/test_sanctions_engine.py`, `app/tests/layer2/test_sanction_persistence.py`, `app/tests/layer2/test_sanction_context.py`, `app/tests/layer3/test_skill_mandatory_decisions.py` (D2 portion), `app/tests/layer3/test_sanctions_full_chain_ai.py`
- Human UI (future — not yet implemented)

---

## 1. PURPOSE

A country's sanctions decision is submitted at the end of each round. It declares the country's bilateral sanctions posture toward any subset of the other 19 countries, including the option of supporting sanctions EVASION against a target (negative level). The engine consumes this decision, computes coalition coverage, applies the sector-derived ceiling, and produces a per-target GDP coefficient.

**Key design principles:**

1. **Sanctions are coalition-driven.** A solo actor barely moves the needle. Crossing the 50-60% coverage tipping point doubles effectiveness. "Will Cathay join?" is the single most strategically pivotal question.
2. **Per-target ceiling from economic structure.** Resource-heavy economies (Sarmatia, Caribe, Solaria) are structurally resilient — max damage ~13%. Tech/services-heavy economies (Columbia, Levantia) are vulnerable — max damage ~22%. Each target has its own ceiling derived from sector mix.
3. **Signed levels — evasion support is a first-class choice.** Level ∈ [−3, +3]. Positive = active sanctioner. Negative = evasion support (buying discounted exports, providing workarounds). Total coverage is clamped at [0, 1]: evasion can cancel a sanctions coalition but cannot produce a GDP bonus.
4. **One-time shocks, not recurring drains.** Sanctions are applied as a RATIO in GDP growth (`new_sanc / old_sanc`). Imposing produces a one-time hit. Keeping sanctions steady produces zero additional effect. Lifting produces a one-time recovery bounce. No compounding, no adaptation.
5. **No imposer cost, no evasion benefit for now.** Target-damage-only model. Sanctioning a rival is mechanically free (the strategic cost is diplomatic, not fiscal). Evasion support doesn't mechanically reward the supporter. These may be added in a future calibration pass.
6. **Sanctions are a possibility, not an obligation.** `no_change` is a fully legitimate explicit choice. Sanctions churn for the sake of churn is bad strategy and the contract makes that obvious.
7. **Decision-specific context only — no cognitive layer in this contract.** The system supplies what the participant needs to know about THIS decision (own state, counterparties, current coalition coverage on each potential target, decision rules). The participant's cognitive context (identity, memory, goals, world rules) belongs to the AI Participant Module (future). Tests emulate the cognitive layer with a hand-crafted persona stub that lives only in the test harness.

---

## 2. DECISION SCHEMA

### 2.1 The decision object

```json
{
  "action_type": "set_sanctions",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change" | "no_change",
  "rationale": "string, >= 30 chars, required in both cases",
  "changes": {
    "sanctions": {
      "persia":  3,
      "choson":  3,
      "bharata": 0
    }
  }
}
```

### 2.2 Field specifications

| Field | Type | Values | Required | Semantics |
|---|---|---|---|---|
| `action_type` | string | `"set_sanctions"` (PLURAL) | yes | Distinct from legacy singular `set_sanction` which still works in parallel during migration |
| `country_code` | string | canonical country code | yes | Decision owner (the actor — may be sanctioner OR evasion supporter) |
| `round_num` | int | ≥ 0 | yes | Round this decision applies to |
| `decision` | string | `"change"` or `"no_change"` | yes | Explicit choice. `no_change` is legitimate. |
| `rationale` | string | ≥ 30 chars | yes | Required in both branches. |
| `changes` | object | see §2.3 | only if `decision=="change"` | Must be absent when `no_change`. |

### 2.3 The `changes` object

```
changes: {
  sanctions: { <target_country_code>: int -3..+3, ... }   # SPARSE
}
```

- **`changes.sanctions` is a flat dict** mapping target country codes to signed integer levels.
- **SPARSE.** Only name targets you want to change. Untouched targets carry forward via the `sanctions` state table.
- **Setting a target to `0` LIFTS the sanction** (or the evasion support). No separate "lift" action.
- **Negative levels are valid** — they mean evasion support. `cathay → sarmatia = -2` means Cathay actively undermines the coalition against Sarmatia at moderate intensity.
- **At least one entry required when `decision=="change"`.** Empty dict is `EMPTY_CHANGES`.
- **Self-sanction forbidden.** `sanctions.<own_country_code>` is `SELF_SANCTION`.
- **Unknown target forbidden.** Target must be in the 20-country roster (`UNKNOWN_TARGET`).

### 2.4 Level scale

| Level | Meaning | Coverage contribution (per unit of actor's world GDP share) |
|---|---|---|
| **+3** | Maximum sanctions | +1.00 × actor_gdp_share |
| **+2** | Broad sanctions | +0.67 × actor_gdp_share |
| **+1** | Targeted sanctions | +0.33 × actor_gdp_share |
| **0** | None / lift | 0 (no contribution) |
| **−1** | Light evasion support | −0.33 × actor_gdp_share |
| **−2** | Moderate evasion support | −0.67 × actor_gdp_share |
| **−3** | Full evasion support | −1.00 × actor_gdp_share |

Coverage is **summed signed** across all actors, then clamped to `[0, 1]`. Evasion can cancel sanctions (drive coverage to 0) but cannot produce negative coverage / positive GDP bonus.

### 2.5 No_change example

```json
{
  "action_type": "set_sanctions",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "no_change",
  "rationale": "Current coalition pressure on Sarmatia and Persia is already at maximum intensity from Columbia. No additional escalation possible or strategically warranted this round."
}
```

No `changes` field — just the envelope.

---

## 3. CONTEXT PROVIDED TO DECISION-MAKER (decision-specific only)

This contract specifies what the **SYSTEM** supplies to the participant about THIS decision. The participant's **cognitive context** (identity, memory, goals, world rules) is OUT OF SCOPE — that is the responsibility of the AI Participant Module (future) for AI participants, or the human UI (future) for humans.

> **Strategy note (2026-04-10):** This phase ships engines + contracts + DBs + decision-specific contexts for *every* SIM activity, one at a time. The AI Participant Module v1.0 is built afterwards on top of a complete substrate. Until then, L3 tests emulate the cognitive layer with a hand-crafted persona stub that lives only in the test harness. See `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` "Boundary statement."

### 3.1 What the system provides

```
[ECONOMIC STATE]                  ← own country snapshot for the round
[ALL 20 COUNTRIES]                ← full roster with sector profile + relationship + current coalition coverage on each
[CURRENT SANCTIONS — IMPOSED BY ME] ← bilateral, the rows you can change
[CURRENT SANCTIONS — IMPOSED ON ME] ← bilateral, informational only
[DECISION RULES]                  ← schema, validation rules summary, no_change reminder
[INSTRUCTION]                     ← what decision is needed
```

### 3.2 [ECONOMIC STATE]

```
GDP:               {gdp}
Treasury:          {treasury}
Inflation:         {inflation}%
Sector mix:        resources {pct} | industry {pct} | services {pct} | tech {pct}
Trade balance:     {trade_balance}
Oil:               {producer/importer}
Stability:         {stability}/10
Political support: {political_support}%
My max_damage ceiling (if I were sanctioned): {pct}%
```

### 3.3 [ALL 20 COUNTRIES] — full roster with coalition coverage signal

The single most important signal for a sanctions decision: **who's already sanctioning each potential target, and how close is the coalition to the tipping point.** The system provides per-target coalition state so the participant can see where marginal action will actually matter.

```
ALL 20 COUNTRIES — potential targets and their current coalition state

  code        GDP    sector profile      rel w/me        coalition coverage    max_damage   current GDP loss
  ----        ----   ------------------  -----------     ------------------    ----------   ----------------
  cathay      190    industrial          hostile         0.032 (noise)         17.5%         0.3%
  persia        5    resource            military_conflict 0.48 (serious)      14.3%         5.0%
  sarmatia     20    resource            military_conflict 0.51 (tipping)      13.9%         5.1%
  choson      0.3    industrial          hostile         0.55 (past tipping)   16.0%         8.8%
  teutonia     45    services            allied           0.00 (none)          20.9%         0.0%
  ...
  (all 20 listed, each annotated)
```

The "coalition coverage" column is the single most valuable piece of intelligence: it tells the participant whether joining a sanctions coalition would move the needle (below 0.5) or be redundant (already past 0.8).

### 3.4 [CURRENT SANCTIONS — IMPOSED BY ME]

```
CURRENT SANCTIONS — IMPOSED BY ME (you can change these)
  persia    L3  (since R0)
  choson    L3  (since R0)
  sarmatia  L3  (since R0)
  (or "(none — you currently sanction no one)")
```

If the actor has any **negative levels** (evasion support they're providing), those appear here too with clear labeling:

```
  ruthenia  L-2 (evasion support, since R2)
```

### 3.5 [CURRENT SANCTIONS — IMPOSED ON ME]

```
CURRENT SANCTIONS — IMPOSED ON ME (informational only — you cannot change these)
  caribe    L1  (since R0)
  (or "(none — no country currently sanctions you)")
```

Plus any countries SUPPORTING EVASION on you (if applicable — positive for the target):

```
  cathay    L-1 (evasion support — reduces coalition against me, since R0)
```

### 3.6 [DECISION RULES] — schema reminder + no_change reminder

```
HOW SANCTIONS WORK (mechanically)
- Levels ∈ [-3, +3]. Positive = active sanctioner. Negative = evasion support.
- Coverage = Σ (actor_gdp_share × level/3) across all actors on a target, clamped to [0, 1].
- Effectiveness = S-curve(coverage). Flat below 0.4, steep at 0.5-0.6, saturates near 1.0.
- Per-target damage ceiling derived from sector mix:
  max_damage = tec×0.25 + svc×0.25 + ind×0.125 + res×0.05
  (tech/services economies up to ~22%; resource economies ~13%)
- Final GDP loss = max_damage × effectiveness (one-time shock, not recurring).
- Setting a target to 0 LIFTS any existing sanction (or evasion support).
- Untouched targets keep their previous level (carry-forward).
- No imposer cost, no evasion benefit — you don't pay a mechanical fee to sanction.

DECISION RULES
- decision="change"    → must include changes.sanctions with ≥1 (target, level) entry
- decision="no_change" → must OMIT the changes field entirely
- rationale ≥30 chars REQUIRED in both cases
- self-sanction and unknown-target are validation errors

REMINDER — no_change is a legitimate choice
Sanctions are a possibility, not an obligation. If your current posture still
serves your goals, no_change is the right answer. Do not churn sanctions for
the sake of action.
```

### 3.7 [INSTRUCTION]

```
Decide whether to CHANGE your sanctions posture or keep it NO_CHANGE.
Either way you MUST provide a rationale of at least 30 characters
explaining WHY.

Respond with JSON ONLY, matching the schema in CONTRACT_SANCTIONS §2.
```

### 3.8 What the system does NOT provide (out of contract scope)

| Layer | Provided by |
|---|---|
| Identity / character / personality | AI Participant Module (future) |
| Memory / self-curated round history | AI Participant Module (future) |
| Strategic objectives / goals | AI Participant Module (future) |
| General SIM mechanics (Block 1) | AI Participant Module (future) |

### 3.9 Testing convention

L3 tests emulate the cognitive layer with a **hand-crafted persona stub** in the test harness — a few sentences of character + objectives stapled to the LLM system prompt. This is explicitly a TEST FIXTURE, not part of the contract. When the AI Participant Module ships, the stub is replaced by `agent.get_cognitive_state()` and **this contract is unchanged**.

---

## 4. VALIDATION RULES

The validator is a pure function `validate_sanctions_decision(payload) → {valid, errors, warnings, normalized}`. **All errors are collected in a single pass.**

### 4.1 Error codes

| Code | Rule | Trigger |
|---|---|---|
| `INVALID_PAYLOAD` | top-level must be a dict | non-dict input |
| `INVALID_ACTION_TYPE` | `action_type == "set_sanctions"` | missing or wrong value |
| `INVALID_DECISION` | `decision in {"change", "no_change"}` | missing or wrong value |
| `RATIONALE_TOO_SHORT` | rationale string ≥ 30 chars after strip | missing, non-string, or too short |
| `MISSING_CHANGES` | `decision=="change"` requires `changes.sanctions` (a dict) | change without changes |
| `UNEXPECTED_CHANGES` | `decision=="no_change"` must omit the `changes` field | `no_change` with `changes` present |
| `EMPTY_CHANGES` | `decision=="change"` with empty sanctions dict | empty on a change |
| `UNKNOWN_FIELD` | top-level or changes-level keys must be in the allowed set | extra fields |
| `INVALID_LEVEL` | every value must be `int in [-3, +3]` | non-int, out-of-range, bool, str |
| `UNKNOWN_TARGET` | target must be in the canonical 20-country roster | unknown country code |
| `SELF_SANCTION` | imposer cannot sanction itself | self in sanctions dict |

### 4.2 Allowed fields

Top level: `action_type`, `country_code`, `round_num`, `decision`, `rationale`, `changes`.
Inside `changes`: `sanctions` (only).

### 4.3 Normalized output (when valid)

```json
{
  "action_type": "set_sanctions",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change",
  "rationale": "<trimmed string>",
  "changes": { "sanctions": { "persia": 3, "bharata": -1 } }
}
```

For `no_change`, the `changes` field is omitted.
Levels coerced to `int`. Country codes lowercased. Whitespace stripped.

---

## 5. PERSISTENCE

### 5.1 The two storage layers

| Layer | Purpose | Mutated by |
|---|---|---|
| **`sanctions` state table** (existing) | Canonical world state — current bilateral level for every (actor, target) pair. Read by the engine each round via `_load_state_from_tables`. | `resolve_round` set_sanctions handler |
| **`country_states_per_round.sanction_decision` JSONB** (NEW 2026-04-10) | Per-round audit record of the decision the participant submitted, including `no_change` decisions with rationale. | `resolve_round` set_sanctions handler |

### 5.2 DB migration — applied 2026-04-10

Migration name: `sanctions_v1_canonical_schema`

Changes:
- `country_states_per_round.sanction_decision jsonb` (NEW)
- `countries.sanctions_adaptation_rounds` DROPPED (dead column)
- `countries.sanctions_recovery_rounds` DROPPED (dead column)
- `sanctions.notes` cleared of sectoral text for all 36 rows (column kept for future use)
- Cathay → Sarmatia L=−1 row PRESERVED (now canonically valid under signed-coverage model)

### 5.3 Write path (resolve_round set_sanctions handler)

```
1. Build full envelope payload from the agent_decisions row
2. Call validate_sanctions_decision(payload)
3. If invalid:
     - Log warning
     - Emit observatory_event(type="sanction_rejected", country, payload, errors)
     - DO NOT touch sanctions table or sanction_decision column
4. If valid and decision == "no_change":
     - Write {"decision": "no_change", "rationale": "..."} to
       country_states_per_round.sanction_decision for (country, round)
     - DO NOT touch sanctions table — carry-forward by inaction
5. If valid and decision == "change":
     - For each (target, level) in normalized changes.sanctions:
         upsert sanctions (sim_run_id, actor, target, level)
         on_conflict (sim_run_id, imposer_country_id, target_country_id) do update
         level=0 is allowed and means "lifted"
         negative levels (evasion support) are stored as-is
     - Write the full normalized payload to
       country_states_per_round.sanction_decision for (country, round)
```

### 5.4 Read path

The engine reads the `sanctions` state table via the existing `_load_state_from_tables` in `round_tick.py`. **No round_tick changes for this slice** (loader already supports the shape). The new `sanction_decision` column is read only by the context builder (Step 5) and observatory queries (future).

---

## 6. ENGINE BEHAVIOR

**Rewritten 2026-04-10.** See `calc_sanctions_coefficient` and `_sanctions_max_damage` in `app/engine/engines/economic.py`.

### 6.1 Max damage ceiling (per target, derived from sector mix)

```
max_damage = tec% × 0.25  +  svc% × 0.25
           + ind% × 0.125 + res% × 0.05
```

Where:
- `SANCTIONS_WEIGHT_TEC = 0.25`
- `SANCTIONS_WEIGHT_SVC = 0.25`
- `SANCTIONS_WEIGHT_IND = 0.125`
- `SANCTIONS_WEIGHT_RES = 0.05`

Sector percentages taken from `countries.sector_*` (values 0-100). Result is a fraction in `[0, 0.25]` (no sector exceeds 50% × 0.5 in practice since resources+industry+services+technology = 100%).

Empirical range across the 20-country roster: `~12.5% (Caribe, pure resource) to ~22.5% (Levantia, services/tech heavy)`.

### 6.2 Coverage (signed, clamped)

```
coverage = Σ (actor_gdp_share × level / 3)   for all (actor, level) on target
coverage = clamp(coverage, 0, 1)
```

Where:
- `actor_gdp_share = actor_starting_gdp / world_starting_gdp` (uses `_starting_gdp` for determinism, falls back to `gdp` if missing)
- `level ∈ [-3, +3]` (signed; negative = evasion support)
- Coverage is computed per target; each target has its own independent coalition

Evasion can drive coverage toward 0 but cannot produce negative coverage / a GDP bonus.

### 6.3 S-curve effectiveness

```python
SANCTIONS_S_CURVE = [
    (0.0, 0.00), (0.1, 0.05), (0.2, 0.10), (0.3, 0.15),
    (0.4, 0.25), (0.5, 0.35), (0.6, 0.55), (0.7, 0.65),
    (0.8, 0.75), (0.9, 0.90), (1.0, 1.00),
]
effectiveness = interpolate_s_curve(coverage, SANCTIONS_S_CURVE)
```

Steeper shape with tipping point at 0.5 → 0.6 (+0.20 effectiveness for +0.1 coverage). Below 0.4 the curve is very flat (solo action is noise). Above 0.8 the curve approaches saturation.

### 6.4 Final coefficient

```
damage      = max_damage × effectiveness
coefficient = max(SANCTIONS_FLOOR, 1.0 - damage)
```

Where `SANCTIONS_FLOOR = 0.15` (safety rail — mostly unreachable given sector weights cap max_damage at ~22.5%).

### 6.5 Application (one-time shock, not recurring drain)

The coefficient is applied via RATIO in `calc_gdp_growth`:

```python
sanc_ratio = new_coef / old_coef
new_gdp    = gdp_after_growth × sanc_ratio
```

This means:
- **Round N (sanctions first imposed):** `old=1.0, new=0.95 → ratio=0.95 → -5% one-time shock`
- **Round N+1 (no change):** `old=0.95, new=0.95 → ratio=1.0 → zero additional effect`
- **Round M (sanctions lifted):** `old=0.95, new=1.0 → ratio=1.053 → +5.3% recovery bounce`

No compounding, no adaptation, no temporal drain.

### 6.6 Related effects (separate mechanisms, unchanged)

- **Target revenue cost** (`calc_revenue`): `Σ level × bilateral_weight × 0.015 × gdp` subtracted from target's revenue per round. Uses the `sanctions` table, counts positive levels only.
- **Oil producer supply effect** (`calc_oil_price`): L2+ sanctions on oil producers reduce effective supply by `0.10 × producer_share` in the world oil market.

### 6.7 What was REMOVED from the old engine (2026-04-10)

- Global `SANCTIONS_MAX_DAMAGE = 0.87` constant (replaced by per-country sector-derived ceiling)
- `trade_openness` factor (`|trade_balance|/gdp + 0.3`) — redundant with sector composition
- Old `sector_vulnerability` multiplicative factor (`0.5 + (svc+tec)×0.8 - res×0.6`) — replaced by direct sector-weighted sum
- `SANCTIONS_ADAPTATION_RATE`, `SANCTIONS_PERMANENT_FRACTION`, `SANCTIONS_DIMINISHING_THRESHOLD`, `SANCTIONS_DIMINISHING_FACTOR` — temporal adaptation entirely dropped
- `update_sanctions_rounds()` function + `sanctions_rounds` counter — no consumer remains
- Political engine's `sanctions_rounds > 4 ? 0.70 : 1.0` stability multiplier — consistency with "drop adaptation" decision
- Hard floor 0.50 in coefficient (changed to 0.15, and largely unreachable anyway)

### 6.8 Canonical calibration anchors (Sarmatia)

Locked as L1 regression tests in `app/tests/layer1/test_sanctions_engine.py`:

| Scenario | Coverage | Effectiveness | Coefficient | GDP loss |
|---|---|---|---|---|
| Clean world (no sanctions) | 0.000 | 0.000 | 1.0000 | 0.00% |
| Teutonia alone L3 | 0.057 | 0.029 | 0.9960 | 0.40% |
| Columbia alone L3 | 0.357 | 0.206 | 0.9714 | 2.86% |
| Real DB starting (12 actors incl. Cathay L−1 evasion) | 0.509 | 0.367 | 0.9490 | 5.10% |
| Starting + Cathay flips L−1 → L+2 | 0.751 | 0.701 | 0.9028 | 9.72% |

---

## 7. WHAT IS OUT OF SCOPE FOR THIS SLICE

- **Cognitive blocks** (rules/identity/memory/goals) — provided by the AI Participant Module (future), NOT by this contract.
- **AI agent persistence** (cognitive_states table, save/load, self-curated memory loop, goal evolution, agent rehydration) — covered by AI Participant Module v1.0 in a later phase block.
- **Imposer cost / evasion benefit** — explicitly dropped per Marat 2026-04-10 "no negative impact for now in system". Target-damage model only. May be added in a future calibration pass.
- **Temporal adaptation / diminishing returns** — explicitly dropped per Marat 2026-04-10 ("too complex, too many edge cases with async join/lift, effect negligible for sim experience").
- **Sector carve-outs** (financial / technology / energy separate lanes) — explicitly dropped per Marat 2026-04-10. Single integer level only. Sector detail is implicit in the max_damage ceiling per target.
- **Per-role effectiveness modifiers** (e.g., Mirage ±20% sanctions routing) — explicitly DROPPED from DET_A1 per Marat 2026-04-10.
- **Sanctions intel / secondary sanctions detection** — belongs to the covert-ops slice (separate).
- Dropping or deprecating the legacy `set_sanction` (singular) / `impose_sanction` / `lift_sanction` actions — they keep working in parallel during migration.
- Rendering the context package as text — caller's responsibility.
- Forecast / dry-run preview — deferred, participants learn by doing.

---

## 8. STANDARD OUTPUT (what the engine produces)

Per target country, per round:
- `sanctions_coefficient` (numeric column on `country_states_per_round`, written by `round_tick` write-back payload). Range `[SANCTIONS_FLOOR, 1.0]`. Applied via ratio to GDP in `calc_gdp_growth`.
- Cascading effects:
  - GDP reduced by the ratio delta
  - Target revenue reduced by `sanctions_cost` (existing `calc_revenue` formula)
  - Oil price affected if target is an L2+ sanctioned producer (existing `calc_oil_price` formula)
  - Political stability friction in `political.py` (now full-strength always — no adaptation)

Tests assert against:
- The `sanctions_coefficient` column on the snapshot (matches hand-computed value)
- The `sanction_decision` JSONB column (matches submitted decision byte-for-byte)
- The `sanctions` state table rows (upserted with new levels; carry-forward for untouched targets)

---

## 9. ACCEPTANCE CRITERIA

Before marking the slice DONE:

- [x] **Engine** — `calc_sanctions_coefficient` rewritten, `_sanctions_max_damage` added, old constants removed, dead code deleted (DONE 2026-04-10)
- [x] **L1 regression tests** — 27 tests in `test_sanctions_engine.py` pinning constants, max_damage by sector, 4 canonical Sarmatia anchors, signed coverage, level ladder, floor safety, S-curve shape (DONE 2026-04-10)
- [x] **Docs reconciliation** — SEED_D8 §Sanctions Hit, CARD_FORMULAS A.2, CARD_ACTIONS 2.3, DET_C1 §MandatoryInputs all updated (DONE 2026-04-10)
- [x] **DB migration** — `sanction_decision` JSONB added, dead columns dropped, `sanctions.notes` cleared (DONE 2026-04-10)
- [ ] **Step 1 — Contract** — this document (IN PROGRESS)
- [ ] **Step 2 — Validator (L1)** — `sanction_validator.py` with all 11 error codes
- [ ] **Step 4 — Persistence (L2)** — `resolve_round.py` set_sanctions handler, L2 tests for change/no_change/lift/invalid
- [ ] **Step 5 — Decision-specific context (L2)** — `sanction_context.py` with economic state + all 20 countries + coalition coverage per target + current bilateral both directions + no_change reminder
- [ ] **Step 6 — AI skill harness (L3)** — D2 prompt updated to v1.0 schema with persona stub
- [ ] **Step 7 — AI acceptance gate (L3)** — `test_sanctions_full_chain_ai.py` with real LLM → validator → DB → engine → snapshot, no fixup
- [ ] **Closing** — CHECKPOINT_SANCTIONS.md, CHANGES_LOG.md milestone entry, PHASE.md updated, commit

---

## 10. CHANGE LOG

- **v1.0 🔒 LOCKED (2026-04-10)** — Initial canonical version. Engine rewritten. Docs reconciled. DB migrated. Slice Steps 2-7 pending execution but design decisions all locked.
