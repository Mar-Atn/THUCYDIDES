# CONTRACT: Sabotage

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §4.2

---

## 1. PURPOSE

Covert destructive operation against a target country's assets. Card-based
(consumable). Three probability rolls: success, detection, attribution.

---

## 2. SCHEMA

```json
{
  "action_type": "covert_op",
  "op_type": "sabotage",
  "role_id": "shadow",
  "country_code": "columbia",
  "round_num": 3,
  "rationale": ">= 30 chars",
  "target_country": "persia",
  "target_type": "nuclear_tech"
}
```

| `target_type` | Effect on success |
|---|---|
| `infrastructure` | -1 coin from target treasury |
| `nuclear_tech` | -30% of current nuclear R&D progress |
| `military` | 50% chance to destroy 1 random active unit |

---

## 3. PROBABILITY ROLLS

| Roll | Probability | Meaning |
|---|---|---|
| **Success** | 50% | Operation succeeds → damage applied |
| **Detection** | 50% | Target learns sabotage happened (independent of success) |
| **Attribution** | 50% (only if detected) | Everyone learns WHO did it |

All three rolls are independent. A failed attempt can still be detected.

---

## 4. EVENT VISIBILITY

| Outcome | Attacker sees | Target sees | Public sees |
|---|---|---|---|
| Success + undetected | Full details (CLASSIFIED) | Nothing | Nothing |
| Success + detected anonymous | Full details | "Unknown actor sabotaged our X" | Nothing |
| Success + detected attributed | Full details | "Country Y sabotaged our X" | Same |
| Failure + undetected | "Operation failed" | Nothing | Nothing |
| Failure + detected attributed | "Operation failed" | "Country Y attempted sabotage" | Same |

---

## 5. LOCKED INVARIANTS

1. Card-based: `sabotage_cards` (per SIM, consumable)
2. No self-sabotage
3. Success 50%, detection 50%, attribution 50% (all Template-customizable)
4. `precomputed_rolls` hook for deterministic testing
5. Damage is immediate (not deferred to engine tick)
6. Military sabotage has an additional 50% roll for unit destruction
