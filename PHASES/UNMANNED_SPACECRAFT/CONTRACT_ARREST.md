# CONTRACT: Arrest

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §6.1

---

## 1. PURPOSE

HoS (or authorized role) arrests a target role within the same country.
Target is removed from play for the remainder of the round (cannot act,
attend meetings, or communicate). Auto-released at round end.

**Moderator-confirmed:** In human/combined mode, moderator verifies the
target is on own soil and confirms. In unmanned mode, auto-confirmed.

---

## 2. FLOW

```
Initiator submits arrest request (target + justification)
  → MODERATOR confirms (or auto-confirm in unmanned)
    → run_roles.status = 'arrested'
    → PUBLIC event: all participants notified
    → At round end: run_roles.status = 'active' (auto-release)
```

---

## 3. SCHEMA

```json
{
  "action_type": "arrest",
  "role_id": "dealer",
  "country_code": "columbia",
  "round_num": 2,
  "rationale": ">= 30 chars justification",
  "changes": { "target_role": "shadow" }
}
```

---

## 4. VALIDATION

| Code | Rule |
|---|---|
| `UNAUTHORIZED` | Arrester must be HoS |
| `WRONG_COUNTRY` | Target must be same country |
| `SELF_ARREST` | Cannot arrest yourself |
| `UNKNOWN_TARGET` | Target role must exist |
| `ALREADY_ARRESTED` | Target must be status=active |

---

## 5. ENGINE

- `request_arrest(sim_run_id, arrester, target, justification, round)` → executes arrest
- `release_arrested_roles(sim_run_id, round)` → auto-releases all arrested at round end
- Both write through `run_roles.update_role_status()`
- Events: PUBLIC — all participants see the arrest + release

---

## 6. PERSISTENCE

- `run_roles.status = 'arrested'` (target row)
- `run_roles.status_changed_round`, `status_changed_by`, `status_change_reason`
- `observatory_events`: `role_status_arrested` + `role_status_active` (release)

---

## 7. LOCKED INVARIANTS

1. HoS only (or authorized role with arrest power)
2. Same country only
3. Auto-release at round end (no indefinite detention)
4. Moderator confirmation required in human/combined mode
5. Target's powers and coins are preserved — they resume at round end
6. Arrested person's assigned powers (military/economic/foreign) remain assigned to them — HoS must separately reassign if desired
