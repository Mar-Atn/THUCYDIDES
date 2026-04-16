# CONTRACT: Run Roles (Per-Run Role State)

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Architectural pattern:** Same as KING (simulation_templates → clans/roles per run)

---

## 1. PURPOSE

The SIM has a **template-level** ``roles`` table with canonical character
definitions (name, title, country, powers, personal_coins). This data is
**frozen** — it describes the game design, not a specific playthrough.

For each sim_run, we **clone** these into a ``run_roles`` table where
they can be mutated: arrested, killed, deposed, coins spent/earned,
powers overridden. This follows the same pattern as
``country_states_per_round`` (template countries → per-round snapshots).

```
roles (template, frozen)
     ↓ seed_run_roles(sim_run_id)
run_roles (per-run, mutable)
     ↓ game actions
  status: active → arrested → released
  status: active → killed
  status: active → deposed (coup)
  personal_coins: earned / spent
```

**Source pattern:** KING's ``roles`` table has ``run_id`` FK — each run
gets its own copy of roles from the template. We replicate this with
the ``run_roles`` table.

---

## 2. SCHEMA

```sql
run_roles (
  id uuid PK,
  sim_run_id uuid FK → sim_runs,
  role_id text,              -- references template roles.id
  country_code text,
  character_name text,
  title text,
  is_head_of_state boolean,
  is_military_chief boolean,
  is_diplomat boolean,
  status text (active|arrested|killed|deposed|inactive),
  personal_coins integer,    -- DEPRECATED 2026-04-15: no personal transactions in simplified model
  powers text,
  status_changed_round int,
  status_changed_by text,
  status_change_reason text,
  created_at timestamptz,
  UNIQUE (sim_run_id, role_id)
)
```

---

## 3. LIFECYCLE

### Seed
``seed_run_roles(sim_run_id)`` clones all 40 template roles into
``run_roles`` with ``status='active'`` and starting ``personal_coins``
from the template.

### Query
- ``get_run_role(sim_run_id, role_id)`` — single role
- ``get_run_roles(sim_run_id, country_code?, status?)`` — filtered list

### Mutate
- ``update_role_status(sim_run_id, role_id, new_status, by, reason, round)``
- ``update_personal_coins(sim_run_id, role_id, delta)``  -- DEPRECATED 2026-04-15

### Status transitions
```
active → arrested (by HoS or authorized role — moderator confirms)
arrested → active (auto at round end, or by moderator)
active → killed (assassination success)
active → deposed (coup success)
active → inactive (fired — powers reassigned but person stays in game)
```

---

## 4. RELATIONSHIP TO OTHER SYSTEMS

| System | How it uses run_roles |
|---|---|
| **Power assignments** | ``check_authorization()`` looks up role's ``is_head_of_state`` flag from ``run_roles`` |
| **Transactions** | Personal coin balance read from ``run_roles.personal_coins`` |
| **Arrest action** | Sets ``status='arrested'`` on target role |
| **Assassination engine** | Sets ``status='killed'`` on success |
| **Coup engine** | Sets ``status='deposed'`` on HoS if coup succeeds |
| **Nuclear chain** | Reads ``run_roles`` to find authorizer roles per country |
| **AI Participant Module** | Will read ``run_roles`` to know which character the agent plays |

---

## 5. LOCKED INVARIANTS

1. Template ``roles`` table is NEVER modified during a run
2. ``run_roles`` is cloned at run start — one copy per sim_run
3. All role mutations go through ``run_roles`` update functions
4. ``status`` field is the authoritative source for whether a role can act
5. Personal coins are per-run (not template-level)
6. CASCADE delete: deleting a sim_run removes all its run_roles
7. 40 roles seeded per run (Template v1.0)
