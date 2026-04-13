# CONTRACT: Naval Combat Decision

**Status:** 🔒 **LOCKED** (2026-04-12) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §1.5 + `CARD_FORMULAS.md` D.3

---

## 1. PURPOSE

One-on-one ship-vs-ship combat. Each side rolls 1d6 + modifiers, higher wins (ties → defender). Loser destroyed. No movement after — ships stay where they are. No fleet advantage; to destroy a fleet, attack multiple times.

---

## 2. DECISION SCHEMA

### 2.1 change

```json
{
  "action_type": "attack_naval",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change",
  "rationale": "string >= 30 chars",
  "changes": {
    "attacker_unit_code": "col_n_01",
    "target_unit_code": "sar_n_02"
  }
}
```

| Field | Type | Required | Semantics |
|---|---|---|---|
| `action_type` | string | yes | `"attack_naval"` |
| `country_code` | string | yes | Attacking country |
| `round_num` | int | yes | Round |
| `decision` | string | yes | `"change"` or `"no_change"` |
| `rationale` | string | yes | ≥ 30 chars |
| `changes.attacker_unit_code` | string | yes (change) | Single own naval unit |
| `changes.target_unit_code` | string | yes (change) | Single enemy naval unit |

### 2.2 no_change — omit `changes` entirely.

### 2.3 Multiple attacks — submit one `attack_naval` decision per 1v1 engagement.

---

## 3. VALIDATION RULES

`validate_naval_attack(payload, units, country_state) → {valid, errors, warnings, normalized}`

| Code | Rule |
|---|---|
| `INVALID_PAYLOAD` | dict |
| `INVALID_ACTION_TYPE` | `attack_naval` |
| `INVALID_DECISION` | change / no_change |
| `RATIONALE_TOO_SHORT` | ≥ 30 chars |
| `MISSING_CHANGES` | change requires changes |
| `UNEXPECTED_CHANGES` | no_change omits changes |
| `UNKNOWN_FIELD` | extra keys |
| `MISSING_UNIT_CODE` | attacker/target unit codes required |
| `UNKNOWN_UNIT` | unit must exist |
| `NOT_OWN_UNIT` | attacker must belong to country_code |
| `WRONG_UNIT_TYPE` | both must be `naval` |
| `UNIT_NOT_ACTIVE` | both must be status=active |
| `TARGET_FRIENDLY` | target must be enemy (not own country) |
| `NOT_ADJACENT_OR_SAME` | attacker and target must be on same or adjacent sea hex |
| `SAME_UNIT` | cannot attack yourself |

---

## 4. ENGINE

```python
def resolve_naval_combat(
    attacker: dict, defender: dict,
    modifiers: list[dict] | None = None,
    precomputed_rolls: dict | None = None,
) -> NavalCombatResult
```

`NavalCombatResult`:
- `combat_type = "naval"`
- `attacker_roll: int` (1-6)
- `defender_roll: int` (1-6)
- `attacker_modified: int` (roll + bonus)
- `defender_modified: int` (roll + bonus)
- `winner: str` ("attacker" | "defender")
- `destroyed_unit: str` (unit_code of loser)
- `modifier_breakdown: list[dict]`
- `rolls_source: str`
- `narrative: str`

Modifiers (per CARD_FORMULAS D.3): AI L4 (+1) and low morale (-1) only.

`precomputed_rolls`: `{"attacker": 5, "defender": 3}` — single int per side.

---

## 5. PERSISTENCE

- `country_states_per_round.attack_naval_decision JSONB` (audit)
- `observatory_combat_results` row: `combat_type='naval'`, `attacker_rolls=[{roll, modified}]`, `defender_rolls=[{roll, modified}]`
- `unit_states_per_round`: loser → status='destroyed'
- `observatory_events`: `event_type='naval_combat'`

---

## 6. LOCKED INVARIANTS

1. `action_type = "attack_naval"`
2. 1v1 only — one attacker, one defender, both naval
3. Each rolls 1d6, ties → defender wins
4. Modifiers: AI L4 (+1), low morale (-1) only. No fleet bonus.
5. Loser destroyed, winner stays in place
6. Same or adjacent sea hex required
7. `precomputed_rolls` hook: `{"attacker": int, "defender": int}`
8. Validator pure, no DB access
