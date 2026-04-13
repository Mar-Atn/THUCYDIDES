# CONTRACT: Basing Rights

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §1.11

---

## 1. PURPOSE

Basing rights allow a guest country to deploy military units on the host country's territory. This is a **unilateral** action by the host — no confirmation from the guest needed for granting. Revocation is also unilateral, BUT blocked if the guest has active forces on host soil.

Two entry points produce the same DB state:
- **Standalone action** (`basing_rights`): host grants/revokes directly
- **Transaction** (`propose_transaction`): basing rights as part of a deal

Both route through `basing_rights_engine.py` — single source of truth.

---

## 2. DECISION SCHEMA

```json
{
  "action_type": "basing_rights",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change",
  "rationale": "string >= 30 chars",
  "changes": {
    "counterpart_country": "teutonia",
    "action": "grant"
  }
}
```

| Field | Values |
|---|---|
| `changes.counterpart_country` | Valid country code (the guest) |
| `changes.action` | `"grant"` or `"revoke"` |

---

## 3. VALIDATION

| Code | Rule |
|---|---|
| `INVALID_SCOPE` | Standard structural checks |
| `INVALID_GUEST` | Guest must be valid country |
| `SELF_BASING` | Cannot grant to yourself |
| `INVALID_ACTION` | Must be grant or revoke |
| `GUEST_FORCES_PRESENT` | **Cannot revoke if guest has active units on host territory** — they must withdraw first |

---

## 4. ENGINE BEHAVIOR

### Grant
- Upserts `basing_rights` row: `(sim_run_id, host, guest)` → status=active
- If previously revoked, reactivates (same row, upsert)
- Events: host notified "granted", guest notified "received"

### Revoke
- Updates `basing_rights` row: status=revoked, revoked_round set
- Events: host notified "revoked", guest notified "lost — must withdraw"
- **Validator enforces**: no revoke while guest troops present

---

## 5. PERSISTENCE

`basing_rights` table:
```
id, sim_run_id, host_country, guest_country,
granted_by_role, granted_round,
status (active|revoked), revoked_round,
source (direct|transaction|template),
created_at
UNIQUE (sim_run_id, host_country, guest_country)
```

---

## 6. LOCKED INVARIANTS

1. Grant is unilateral — no guest confirmation needed
2. Revoke is unilateral — BUT blocked if guest has troops on host soil
3. Single source of truth: `basing_rights` table (not `relationships`)
4. Transaction engine routes through the same `basing_rights_engine`
5. Revoked rights can be re-granted (upsert reactivates)
6. Both host and guest receive event notifications
