# CONTRACT: Propaganda / Disinformation

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §4.3

---

## 1. PURPOSE

Stability manipulation via disinformation campaigns. Two modes: boost
own country's stability or destabilize a foreign (or own) country.
Card-based (consumable). Diminishing returns on repeated use.

---

## 2. SCHEMA

```json
{
  "action_type": "covert_op", "op_type": "propaganda",
  "target": "sarmatia", "intent": "destabilize",
  "content": "Leaked documents showing regime corruption..."
}
```

| `intent` | Target | Effect on success |
|---|---|---|
| `boost` | Own country | Stability **+0.3** |
| `destabilize` | Foreign country | Stability **-0.3** |
| `destabilize` | Own country | Stability **-0.3** (opposition use) |

---

## 3. ROLLS

| Roll | Probability |
|---|---|
| Success | **55%** |
| Detection | **25%** |
| Attribution (if detected) | **20%** |

---

## 4. DIMINISHING RETURNS

Each successive successful use by the same attacker against the same
target halves the effect: 0.3 → 0.15 → 0.075 → ...

---

## 5. LOCKED INVARIANTS

1. Card-based: `disinfo_cards` (consumable)
2. Success 55%, detection 25%, attribution 20%
3. Base effect ±0.3 stability (integer-rounded for DB)
4. Diminishing returns: ×0.5 per successive use
5. Same detection/attribution event pattern as sabotage
6. `precomputed_rolls` hook for deterministic testing
