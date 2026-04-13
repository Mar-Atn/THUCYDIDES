# CONTRACT: Power Assignments (Replaces Fire/Reassign)

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §6.3 (replaced fire_role concept)

---

## 1. PURPOSE

Power assignments are the **authorization backbone** of the SIM. They
determine which role can act on behalf of a country for three categories
of actions:

| Power | What it authorizes |
|---|---|
| **Military** | move_units, attack_*, blockade, launch_missile, martial_law, basing_rights |
| **Economic** | set_budget, set_tariffs, set_sanctions, set_opec, propose_transaction (country assets) |
| **Foreign Affairs** | propose_agreement, propose_transaction (deals), sign agreements |

**HoS is IMPLICIT** — always authorized for everything. Not stored in the
table. The HoS can also reassign any power slot to a different role, or
vacate it (taking the responsibility back).

---

## 2. CANONICAL STARTING ASSIGNMENTS (Template v1.0)

| Country | Military | Economic | Foreign Affairs |
|---|---|---|---|
| **Columbia** | `shield` | `volt` | `anchor` |
| **Cathay** | `rampart` | `abacus` | `sage` |
| **Sarmatia** | `ironhand` | `compass` | `compass` |
| **Ruthenia** | `bulwark` | `broker` | *(vacant — HoS holds)* |
| **Persia** | `anvil` | *(vacant — HoS holds)* | `dawn` |

Single-HoS countries (all others): HoS holds all three powers. No entries
in the table needed.

---

## 3. REASSIGN_POWERS ACTION

```json
{
  "action_type": "reassign_powers",
  "role_id": "dealer",
  "country_code": "columbia",
  "round_num": 3,
  "changes": {
    "power_type": "military",
    "new_role": "shadow"
  }
}
```

| Field | Values |
|---|---|
| `power_type` | `"military"`, `"economic"`, `"foreign_affairs"` |
| `new_role` | Role ID within same country, or `null` (vacate → HoS holds) |

**Who:** HoS only. Non-HoS cannot reassign powers.

**Effect:** Immediate. Previous holder loses the power. New holder gains it.
Both notified. Event logged (public — all see).

---

## 4. AUTHORIZATION CHECK

`check_authorization(role_id, action_type, sim_run_id, country_code)`:

1. Action is unrestricted (public_statement, covert ops, etc.) → **authorized**
2. Role is HoS of the country → **authorized** (always)
3. Action maps to a power_type → look up `power_assignments` table
4. Role matches the assigned role → **authorized**
5. Slot is vacant (NULL) → only HoS can act → **unauthorized**
6. Different role is assigned → **unauthorized** (error says who holds it)

---

## 5. PERSISTENCE

`power_assignments` table:
```
id, sim_run_id, country_code,
power_type (military|economic|foreign_affairs),
assigned_role_id (nullable — NULL = vacant/HoS holds),
assigned_by_role, assigned_round,
created_at
UNIQUE (sim_run_id, country_code, power_type)
```

Seeded at run start via `seed_defaults(sim_run_id)`.

---

## 6. LOCKED INVARIANTS

1. HoS always authorized — implicit, not stored
2. Only HoS can reassign powers
3. Three power categories only: military, economic, foreign_affairs
4. Every action_type maps to exactly one power category (or is unrestricted)
5. Vacant slot = HoS-only authority
6. Reassignment is immediate and public
7. One role can hold multiple powers (compass holds economic + foreign in Sarmatia)
8. Single-HoS countries have no entries — HoS holds all by default
