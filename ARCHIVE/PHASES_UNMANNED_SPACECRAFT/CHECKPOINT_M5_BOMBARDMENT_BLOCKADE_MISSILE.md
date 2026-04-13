# CHECKPOINT — M5 Naval Bombardment + Blockade + Conventional Missile

**Date:** 2026-04-12 | **Status:** ✅ DONE | **Owner:** Marat + Build Team

> Three remaining conventional military actions shipped in one slice:
> naval bombardment (10% per ship), blockade (3 chokepoints + economic
> cascade), and conventional missile launch (70% hit + AD interception).
> This completes ALL conventional military actions.

---

## What M5 delivered

| Component | Result |
|---|---|
| `CONTRACT_NAVAL_BOMBARDMENT_BLOCKADE.md` v1.0 LOCKED | 2-part contract (bombardment + blockade + missile) |
| `engine/services/bombardment_validator.py` | Pure validator |
| `engine/services/blockade_validator.py` | Pure validator (3 chokepoints) |
| `engine/services/missile_validator.py` | Pure validator (conventional only, nuclear = M6) |
| `tests/layer1/test_m5_validators.py` | **21/21 ✅** (0.03s) — 8 bombardment + 6 blockade + 7 missile |
| DB migration `m5_bombardment_blockade_missile_audit` | 3 JSONB audit columns added |
| `resolve_round.py` action constants | `BOMBARDMENT_ACTIONS`, `BLOCKADE_ACTIONS`, `MISSILE_ACTIONS` extended |
| CARD_ACTIONS §1.7, §1.10 status → LIVE | Updated |
| **L1 full sweep** | **549/549 ✅** (0.61s) |

---

## Action type summary

| action_type | Mechanic | Validator | Contract |
|---|---|---|---|
| `attack_bombardment` | 10% per naval at adjacent land hex | `bombardment_validator.py` | Part A |
| `blockade` | State declaration at 3 chokepoints → economic cascade | `blockade_validator.py` | Part B |
| `launch_missile` (conventional) | 70% hit, AD 50% intercept, missile consumed | `missile_validator.py` | Part C |

---

## All conventional military actions — COMPLETE

```
§1.1  move_units           ✅ M1
§1.2  martial_law           ⬜ (domestic — later sprint)
§1.3  attack_ground         ✅ M2
§1.4  attack_air            ✅ M3
§1.5  attack_naval          ✅ M4
§1.7  attack_bombardment    ✅ M5  ← this slice
§1.8a launch_missile (conv) ✅ M5  ← this slice
§1.10 blockade              ✅ M5  ← this slice
§1.11 basing_rights          ⬜ (diplomatic — later sprint)
```

**7 of 9 military actions shipped under contract.** Remaining 2 (martial_law, basing_rights) are domestic/diplomatic, not combat — they'll be covered in a later sprint alongside transactions/agreements/covert.

---

## Running totals

```
F1  ✅   M1 ✅   M2 ✅   M3 ✅   M4 ✅   M5 ✅
L1: 549 tests (0.61s)
```

## Next: M6 Nuclear (tests + launch with nuclear warhead + T3 interception)
