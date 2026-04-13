# CONTRACT: Election Meddling

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §4.4

---

## 1. PURPOSE

Covert interference in a target country's elections. Card-based. Shifts
`political_support` by ±2-5%. Only meaningful when elections are scheduled
(timing gate is a future enhancement — engine applies shift regardless).

---

## 2. SCHEMA

```json
{
  "action_type": "covert_op", "op_type": "election_meddling",
  "target_country": "ruthenia", "direction": "boost", "candidate": "beacon"
}
```

---

## 3. ROLLS

| Roll | Probability |
|---|---|
| Success | **40%** |
| Detection | **45%** |
| Attribution | **50%** (if detected) |

On success: `political_support` shifted by random 2-5%.

---

## 4. LOCKED INVARIANTS

1. Card-based: `election_meddling_cards` (consumable)
2. Success 40%, detection 45%, attribution 50%
3. Support shift ±2-5% (random within range)
4. Same detection/attribution event pattern as sabotage/propaganda
5. `precomputed_rolls` hook (including `shift_amount` override)
