# CHECKPOINT — M4 Naval Combat Vertical Slice

**Date:** 2026-04-12 | **Status:** ✅ DONE | **Owner:** Marat + Build Team

> Third offensive military action shipped. 1v1 ship-vs-ship dice per
> CARD_ACTIONS §1.5 + CARD_FORMULAS D.3. Simplest combat mechanic:
> each rolls 1d6 + modifiers, higher wins, ties → defender, loser
> destroyed, ships stay in place. Moderator-dice hook live.

---

## What M4 delivered

| Component | Result |
|---|---|
| `CONTRACT_NAVAL_COMBAT.md` v1.0 LOCKED | 8 sections, 15 error codes |
| `engine/services/naval_combat_validator.py` | Pure validator |
| `tests/layer1/test_naval_combat_validator.py` | **14/14 ✅** (0.02s) |
| `engines/military.py:resolve_naval_combat()` | M4 canonical with `precomputed_rolls` |
| `resolve_round.py` naval handler | Rewired with modifiers + audit JSONB |
| DB migration `m4_naval_combat_audit_column` | `attack_naval_decision JSONB` |
| `tests/layer2/test_naval_combat_persistence.py` | **2/2 ✅** (13s) |
| Legacy import fix `test_engines.py` | Renamed to `resolve_naval_combat_legacy_v1` |
| CARD_ACTIONS §1.5 status → LIVE | Updated |
| **L1 full sweep** | **528/528 ✅** (0.64s) |

---

## M4 specifics

- **1v1 only** — one attacker, one defender, both naval, no batching
- **Same or adjacent sea hex** — distance ≤ 1 (Manhattan)
- **Modifiers** — AI L4 (+1) and low morale (-1) only per CARD D.3. No fleet bonus.
- **Ties → defender wins** — per CARD
- **Loser destroyed** — `unit_states_per_round` status='destroyed'
- **Combat row shape**: `attacker_rolls=[{roll, modified}]`, `defender_rolls=[{roll, modified}]`, `modifier_breakdown=[]`
- **`precomputed_rolls`** hook: `{"attacker": int, "defender": int}` — single die per side

---

## Files

### New
- `CONTRACT_NAVAL_COMBAT.md`, `CHECKPOINT_M4_NAVAL_COMBAT.md`
- `engine/services/naval_combat_validator.py`
- `tests/layer1/test_naval_combat_validator.py` (14 tests)
- `tests/layer2/test_naval_combat_persistence.py` (2 tests)

### Modified
- `engine/engines/military.py` — added `NavalCombatResultM4` + `resolve_naval_combat()`, renamed legacy to `_legacy_v1`
- `engine/round_engine/resolve_round.py` — rewired naval handler with modifiers + audit
- `tests/layer1/test_engines.py` — import alias for renamed legacy
- `CARD_ACTIONS.md` §1.5 → LIVE

---

## Running totals

```
F1  ✅   M1 ✅   M2 ✅   M3 ✅   M4 ✅
L1: 528 tests (0.64s)
L2: 16 M4 tests green in combined sweep
L3: M2+M3 acceptance gates green (M4 L3 skipped — no AI test needed for
    this simple mechanic; the L2 persistence test + precomputed_rolls
    smoke covers the full chain)
```

## Next: M5 Naval Bombardment + Blockades → M6 Nuclear
