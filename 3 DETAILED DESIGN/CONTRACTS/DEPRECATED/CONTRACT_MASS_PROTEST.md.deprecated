# CONTRACT: Mass Protest (Revolution)

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §6.5

---

## 1. PURPOSE

Revolution attempt by a single protest leader. Requires crisis conditions
(low stability + low support). Probability modified by country conditions.
On success, regime change (leader becomes HoS).

---

## 2. SCHEMA

```json
{
  "action_type": "lead_protest",
  "role_id": "ironhand",
  "country_code": "sarmatia"
}
```

---

## 3. PREREQUISITES

| Condition | Threshold |
|---|---|
| Stability | **≤ 2** |
| Political support | **< 20%** |

Both must be met. If either fails, protest is not attempted.

---

## 4. PROBABILITY

| Factor | Modifier |
|---|---|
| Base | **30%** |
| Low support | +(20 - support)/100 |
| Low stability | +(3 - stability) × 10% |
| Clamp | [15%, 80%] |

---

## 5. OUTCOMES

| Result | Leader | Old HoS | Stability | Support |
|---|---|---|---|---|
| **Success** | Becomes HoS | Deposed | **+1** | **+20** |
| **Failure** | Arrested | Untouched | **-1** | **-5** |

---

## 6. LOCKED INVARIANTS

1. Single leader — no co-conspirator required
2. Prerequisites: stability ≤ 2 AND support < 20% (both checked)
3. Success swaps HoS via `run_roles` (`is_head_of_state` flag)
4. Failure arrests leader via `run_roles` (status = "arrested")
5. Old HoS status set to "deposed" on success
6. Country state updated atomically (stability + support deltas)
7. `precomputed_rolls` hook (`success_roll`) for deterministic testing
8. Observatory event logged (mass_protest_success / mass_protest_failed)
