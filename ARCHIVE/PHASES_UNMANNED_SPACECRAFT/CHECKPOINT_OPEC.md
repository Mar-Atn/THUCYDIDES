# CHECKPOINT: OPEC Vertical Slice

**Status:** ✅ DONE end-to-end
**Date:** 2026-04-11
**Owner:** Marat + Build Team
**Authoritative contract:** `CONTRACT_OPEC.md` v1.0 (🔒 locked)
**Methodology:** `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md` v1.1

This is the durable record of the **fourth and final mandatory-decision vertical slice** — completing the Budget → Tariffs → Sanctions → OPEC sequence. All 4 mandatory end-of-round decisions in the TTT sim now have canonical contracts, validators, engines (or regression locks), decision-specific context builders, persistence handlers, AI skill harnesses, and full-chain acceptance gates.

---

## 1. Scope

The OPEC slice covers one mandatory end-of-round decision for **OPEC+ member countries only**:

- **Single-value production posture** — enum `∈ {min, low, normal, high, max}` (5 levels)
- **Actor must be an OPEC+ member** — 5 canonical members: Caribe, Mirage, Persia, Sarmatia, Solaria
- **Effect is on the world oil price** via supply-side math with 2× cartel leverage amplifier
- **Cascades to every country** — oil price changes GDP growth shocks, revenue (for producers), inflation pressure (for importers)
- **`no_change`** is a fully legitimate explicit choice

Unlike tariffs/sanctions (bilateral matrices), OPEC is a **single-value decision per member** — conceptually the simplest mandatory decision in the sim.

---

## 2. Design decisions locked (per Marat, 2026-04-10/11)

| # | Gap | Decision |
|---|---|---|
| **G1** | Field name chaos (`production` vs `production_level` vs `new_level` across docs/code/tests) | **Canonical: `production_level`** — most descriptive, already what resolve_round handler uses. Nested inside `changes.production_level` for consistency with budget/tariffs/sanctions schema pattern. |
| **G2** | No validator | **NEW** `opec_validator.py` with 9 error codes. Pure function, collects all errors in one pass. |
| **G3** | OPEC+ roster mismatch (code said `{solaria, persia, mirage, caribe}`, DB said `{sarmatia, solaria, persia, mirage}`, real-world OPEC+ includes both Sarmatia/Russia and Caribe/Venezuela) | **5 canonical members** per Marat 2026-04-11: `{caribe, mirage, persia, sarmatia, solaria}`. Fixed the DB (Caribe set to `opec_member=true`), fixed the code constant (`OPEC_MEMBERS` updated), fixed the contract. Canonical source of truth is `CANONICAL_OPEC_MEMBERS` frozenset in `opec_validator.py`. |
| **G4** | R0 snapshot pollution (all 20 countries had `opec_production="normal"`) | **Migration cleans non-OPEC rows to `"na"`.** Post-migration: 5 OPEC+ members at `"normal"`, 15 non-members at `"na"`. |
| **G5** | Engine doesn't enforce OPEC membership | **Not an engine problem — enforced at validator + resolve_round handler layer.** The engine iterates whatever is in the `opec_production` dict; the validator guarantees only OPEC+ members ever get there. Documented as an implicit contract in test_opec_engine.py::TestNonOpecImmune. |
| **G6** | No per-round decision audit | **NEW** `country_states_per_round.opec_decision` JSONB column (matches the `tariff_decision`/`sanction_decision` pattern). |
| **G7** | No mandatory-decision flow | **Slice work.** Contract + validator + context + persistence + harness + acceptance gate all built. |
| **G8** | D4 skill harness had wrong roster + wrong field name (`new_level`) + old 20-char rationale threshold | **Slice work.** Harness rewritten to v1.0 schema with 30-char rationale, `production_level` field, 5-member roster via `OPEC_MEMBERS` (now correct). |

## 3. What changed

### 3.1 Engine (`app/engine/engines/economic.py`)

**UNCHANGED.** This is a contract-around-existing-behavior slice (the tariff pattern — vs sanctions which needed a rewrite). The existing `calc_oil_price` OPEC section at lines ~650-659 already matches SEED_D8 + CARD_FORMULAS A.1 exactly. Constants locked in L1 regression tests:

```python
OPEC_PRODUCTION_MULTIPLIER: dict[str, float] = {
    "min": 0.70, "low": 0.85, "normal": 1.00, "high": 1.15, "max": 1.30,
}
```

Plus the **2× cartel leverage amplifier** applied per-member:
```
supply += (multiplier - 1.0) × member_share × 2.0
```

Tests pin both the constants and the leverage formula. Any future change breaks loudly.

### 3.2 Code fixes

- **`engine/agents/full_round_runner.py:OPEC_MEMBERS`** — was `{"solaria", "persia", "mirage", "caribe"}` (missing Sarmatia), now `{"caribe", "mirage", "persia", "sarmatia", "solaria"}` (5 members, canonical).
- **`engine/round_engine/resolve_round.py` set_opec handler** — rewritten: validates via `validate_opec_decision`, writes `opec_decision` JSONB audit, writes `opec_production` live value on change, emits `opec_rejected` events on invalid, handles no_change correctly.

### 3.3 New services

| Service | File | Purpose |
|---|---|---|
| **Validator** | `app/engine/services/opec_validator.py` | Pure `validate_opec_decision(payload) → {valid, errors, warnings, normalized}`. 9 error codes incl. `NOT_OPEC_MEMBER`. `CANONICAL_OPEC_MEMBERS` + `VALID_PRODUCTION_LEVELS` frozensets. |
| **Context builder** | `app/engine/services/opec_context.py` | `build_opec_context(country_code, scenario_code, round_num) → dict`. Returns 9 blocks: economic_state, oil_market_state, **oil_price_history (all rounds played)**, **unified oil_producers_table** (all 6 producers with current level), chokepoint_blockades, sanctions_on_producers, tariffs_on_producers, decision_rules (with no_change reminder), instruction. **Data only — no commentary per Marat's 2026-04-10 directive.** |

### 3.4 DB migration

**Migration name:** `opec_v1_canonical_schema` (applied 2026-04-10)

Changes:
- **Added** `country_states_per_round.opec_decision jsonb` (per-round audit column)
- **Fixed** `countries.opec_member = true` for Caribe (Venezuela — was incorrectly `false`)
- **Cleaned** R0 snapshot pollution: set `opec_production = 'na'` for all 15 non-OPEC-member rows at round 0 (previously all 20 rows were polluted with `"normal"`)

**Post-migration state:**
- 5 OPEC+ members in `countries.opec_member = true`: Caribe, Mirage, Persia, Sarmatia, Solaria
- R0 `opec_production`: 5 members at `"normal"`, 15 non-members at `"na"`
- `opec_decision` JSONB column present and ready for audit writes

### 3.5 Docs reconciled

| Document | Change |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_OPEC.md` | NEW — 🔒 LOCKED v1.0 |
| `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_OPEC.md` | NEW — this document |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` | 2.4 rewritten with v1.0 schema, 5-member roster, removed stale notes |
| `PHASES/UNMANNED_SPACECRAFT/PHASE.md` | OPEC DONE status block + Sprint B6 updated to **ALL 4 DONE** |

---

## 4. Test coverage (acceptance evidence)

| Layer | File | Count | Purpose |
|---|---|---|---|
| **L1** | `tests/layer1/test_opec_validator.py` | **47** | All 9 error codes + canonical roster + 5 members accepted + all 5 levels valid + rationale boundary + signed level support + error accumulation + normalized output integrity |
| **L1** | `tests/layer1/test_opec_engine.py` | **20** | Engine regression lock: 4 constants, 2 trivial cases, 5 single-member decision effects, 1 cartel-leverage verification, 2 non-member immunity cases, 3 symmetry tests, 2 collective decision tests, 1 validator-gates-membership test |
| **L2** | `tests/layer2/test_opec_persistence.py` | **4** | Change decision persisted; no_change preserves live value; non-member rejected with opec_rejected event; invalid level rejected |
| **L2** | `tests/layer2/test_opec_context.py` | **10** | All 9 context blocks present; all 20 countries' oil_producers_table correct; current level reflects DB; chokepoint blockades have 3 keys; sanctions + tariffs on producers; decision_rules with no_change reminder; non-OPEC member rejected |
| **L3** | `tests/layer3/test_skill_mandatory_decisions.py` (D4 portion) | **(updated)** | D4 OPEC prompt rewritten to v1.0 schema with `production_level` field, 5-member roster, ≥30 char rationale; real validator used for assertion |
| **L3** | `tests/layer3/test_opec_full_chain_ai.py` | **1** | **THE acceptance gate** — real LLM → validator → DB → engine → snapshot, no fixup |

**Totals:** 82 OPEC-specific tests passing. Full L1 suite: 362 passing (295 from earlier + 67 new OPEC L1).

---

## 5. Concrete demo (2026-04-11 acceptance gate run)

Solaria R40→R41, real LLM decision:

```json
{
  "action_type": "set_opec",
  "country_code": "solaria",
  "round_num": 41,
  "decision": "no_change",
  "rationale": "Current oil price at $78/bbl provides solid revenue while maintaining market stability. No immediate need to adjust production given stable economic conditions and absence of external pressures."
}
```

**Persistence + engine result:**
- `opec_decision` JSONB byte-for-byte matches normalized AI output ✅
- `opec_production` on Solaria R41: unchanged from R40 baseline (`normal`) ✅ (no_change path)
- Oil price: R40 $85.00 → R41 $87.20 (engine recomputed successfully) ✅
- Engine tick: `success=True` ✅

The AI correctly identified that the current posture serves its goals and explicitly chose `no_change` with a substantive rationale — demonstrating that the `no_change` path is viable and preferred when appropriate.

---

## 6. Canonical engine math (locked in L1 tests)

### Per-member supply contribution

```
share = member_mbpd / total_world_mbpd
supply_delta = (OPEC_PRODUCTION_MULTIPLIER[level] - 1.0) × share × 2.0
supply += supply_delta
```

### Symmetry properties (verified in L1)

- `min` (0.70) and `max` (1.30) produce equal-magnitude opposite-sign deltas
- `low` (0.85) and `high` (1.15) produce equal-magnitude opposite-sign deltas
- `low` contribution is exactly half of `min` contribution (and similarly `high`/`max`)
- `normal` (1.00) is exactly zero contribution

### Calibration anchors (locked in L1)

| Scenario | Solaria share | Delta | Notes |
|---|---|---|---|
| Solaria alone at `min` | 10/40.8 ≈ 24.5% | −0.147 supply | Single big member's cut is ~15% supply reduction |
| Solaria alone at `max` | 24.5% | +0.147 supply | Symmetric |
| Caribe alone at `min` | 0.8/40.8 ≈ 2.0% | −0.012 supply | Smallest member, marginal effect |
| All 5 OPEC+ at `max` | 68% combined | +0.409 supply | Market flood scenario |

These numbers are pinned in `test_opec_engine.py::TestSingleMemberDecision` and `TestCollectiveDecision`.

---

## 7. Known non-gap observations

- **Engine doesn't check `opec_member`** — it iterates `opec_production.items()` and checks `if member in producer_output` (oil_producer + mbpd > 0). Membership enforcement happens at the validator + persistence handler layer. This is documented in `test_opec_engine.py::TestNonOpecImmune::test_validator_must_gate_membership`. The implicit contract: the validator rejects non-members, so the engine's dict never contains non-OPEC+ actors with a set level.
- **`country_states_per_round.opec_production` column stays text** — didn't migrate to JSONB or enum. Good enough.
- **Legacy top-level `production_level` field** (without the `changes` wrapper) is backward-compatible in the resolve_round handler. Old payloads get auto-migrated.
- **Columbia is the biggest producer in the world** (13 mbpd, 31.7% of world supply) but is NOT an OPEC+ member. It's a free-agent producer that can undercut any cartel cut. This is by design — Columbia equivalents to the US, which historically has had independent oil policy. The context shows Columbia's level as `"na"` in the unified oil_producers_table.

---

## 8. Pointers (copy-pasteable)

```
# Contract
PHASES/UNMANNED_SPACECRAFT/CONTRACT_OPEC.md             🔒 v1.0

# Engine (UNCHANGED — regression-locked by L1 tests)
app/engine/engines/economic.py                         calc_oil_price (OPEC section lines ~650-659),
                                                       OPEC_PRODUCTION_MULTIPLIER constant

# Persistence handler
app/engine/round_engine/resolve_round.py               set_opec handler (v1.0 block)

# Canonical roster
app/engine/agents/full_round_runner.py                 OPEC_MEMBERS frozenset (5 members)
app/engine/services/opec_validator.py                  CANONICAL_OPEC_MEMBERS frozenset (same 5)

# Services
app/engine/services/opec_validator.py                  validate_opec_decision + 9 error codes
app/engine/services/opec_context.py                    build_opec_context (decision-specific, data only)

# Tests
app/tests/layer1/test_opec_validator.py                47 tests
app/tests/layer1/test_opec_engine.py                   20 tests (regression lock)
app/tests/layer2/test_opec_persistence.py              4 tests
app/tests/layer2/test_opec_context.py                  10 tests
app/tests/layer3/test_skill_mandatory_decisions.py     D4 portion updated to v1.0
app/tests/layer3/test_opec_full_chain_ai.py            acceptance gate (1 test)

# Docs reconciled
PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md             2.4 rewritten with v1.0 schema + 5-member roster
PHASES/UNMANNED_SPACECRAFT/PHASE.md                    OPEC DONE + Sprint B6 ALL 4 DONE

# DB migration
opec_v1_canonical_schema                               Applied 2026-04-10 to Supabase project lukcymegoldprbovglmn
```

---

## 9. All 4 mandatory decisions — COMPLETE

With OPEC locked, **all 4 mandatory decisions are now shipped end-to-end** under the same 7-step vertical slice pattern:

| Decision | Status | Commit | Test count |
|---|---|---|---|
| ✅ **Budget** | 🔒 DONE 2026-04-10 | `776aaaf` | 37 L1+L2 + 1 L3 |
| ✅ **Tariffs** | 🔒 DONE 2026-04-10 | `8a4c9d1` | 84 |
| ✅ **Sanctions** | 🔒 DONE 2026-04-10 | `175fbe3` | 83 |
| ✅ **OPEC** | 🔒 DONE 2026-04-11 | this commit | 82 |

**All 4 contracts follow the same pattern:**
- Contract document with explicit design decisions locked
- Validator with error-code-per-rule, collects all errors in one pass
- Engine math either locked (tariffs, OPEC) or rewritten (budget, sanctions)
- Persistence: state table (where applicable) + per-round decision JSONB audit column
- Decision-specific context builder — **no cognitive layer** per the VERTICAL_SLICE_PATTERN boundary
- AI skill harness D1/D2/D3/D4 prompts using real production validators
- Full-chain acceptance gate (real LLM → validator → DB → engine → snapshot)

**Next per Marat's strategy directive:**

```
✅ Budget       DONE  2026-04-10
✅ Tariffs      DONE  2026-04-10
✅ Sanctions    DONE  2026-04-10
✅ OPEC         DONE  2026-04-11
---
   Military Actions (standard / blockade / nuclear)
   Military Movements
   Nuclear Decisions
   Transactions
   Agreements
   Other Actions (fire/reassign / assassination / arrest / propaganda / sabotage / private investments)
```

After all remaining slices ship → reconcile up to CONCEPT and SEED in a single coherent pass. Then → AI Participant Module v1.0 on top of the complete substrate.

**Milestone:** with OPEC shipped, the economic decision layer is complete. The participant (AI or future human) has a fully specified, tested, canonical way to control every economic lever in the sim: fiscal (budget), trade (tariffs), coercion (sanctions), and commodity markets (OPEC).
