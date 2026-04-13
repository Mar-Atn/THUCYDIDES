# CONTRACT: Martial Law (Conscription)

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §1.2

---

## 1. PURPOSE

One-time conscription boost for eligible countries. Spawns ground units
from a fixed martial-law pool into reserve. Immediate stability and war
tiredness cost. Can only be declared **ONCE per country per SIM**.

---

## 2. SCHEMA

```json
{
  "action_type": "declare_martial_law",
  "country_code": "sarmatia",
  "round_num": 3,
  "decision": "change",
  "rationale": ">= 30 chars"
}
```

No parameters — the pool size is fixed per country in Template data.

---

## 3. ELIGIBLE COUNTRIES + POOL SIZES (Template v1.0)

| Country | Pool | Meaning |
|---|---|---|
| Sarmatia | 10 ground units | Full wartime mobilization |
| Cathay | 10 ground units | People's Liberation conscription |
| Persia | 8 ground units | Revolutionary Guard expansion |
| Ruthenia | 6 ground units | Emergency defense mobilization |

All other countries: not eligible.

---

## 4. EXECUTION

1. **Spawn N new ground units** into `unit_states_per_round` with `status='reserve'`
   - Unit codes: `{country_prefix}_conscript_01` through `_N`
   - Deployable next round via `move_units`
2. **Stability: -1** (integer, immediate)
3. **War tiredness: +1** (integer, immediate)
4. **`martial_law_declared = true`** on `country_states_per_round` (prevents re-use)
5. **Event: PUBLIC** — all participants notified

---

## 5. VALIDATION

| Code | Rule |
|---|---|
| `NOT_ELIGIBLE` | Country must be in the eligible list |
| `ALREADY_DECLARED` | `martial_law_declared` must be false |

---

## 6. PERSISTENCE

- `unit_states_per_round`: N new rows (conscripts in reserve)
- `country_states_per_round.stability`: -1
- `country_states_per_round.war_tiredness`: +1
- `country_states_per_round.martial_law_declared`: true
- `observatory_events`: `martial_law_declared` event

---

## 7. LOCKED INVARIANTS

1. One-time per country per SIM (tracked by `martial_law_declared` flag)
2. Pool sizes are Template-level data (not modifiable during SIM)
3. Conscripts are regular ground units — no special combat behavior
4. Costs are immediate (not deferred to engine tick)
5. No stability gate — any eligible country can declare regardless of current stability
