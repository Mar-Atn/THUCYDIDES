# CONTRACT: Coup Attempt

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §6.4

---

## 1. PURPOSE

Regime change attempt by two conspirators within the same country.
Co-conspirator must independently agree (AI asked via LLM in unmanned).
Probability modified by country conditions.

---

## 2. SCHEMA

```json
{
  "action_type": "coup_attempt",
  "role_id": "ironhand",
  "country_code": "sarmatia",
  "co_conspirator_role": "compass"
}
```

---

## 3. PROBABILITY

| Factor | Modifier |
|---|---|
| Base | **15%** |
| Active protest | +25% |
| Stability < 3 | +15% |
| Stability 3-4 | +5% |
| Support < 30% | +10% |
| Clamp | [0%, 90%] |

---

## 4. OUTCOMES

| Result | Initiator | Old HoS | Stability | World |
|---|---|---|---|---|
| **Success** | Becomes HoS | Arrested | **-2** | Notified (regime change) |
| **Failure** | Arrested | Untouched | **-1** | Notified (failed coup) |
| **Refused** | Nothing | Nothing | No change | Logged privately |

---

## 5. CO-CONSPIRATOR

Both must be same country. Co-conspirator is asked independently:
- In unmanned: AI LLM call (considers loyalty, ambition, risk)
- In human: direct question to the participant
- Refusal → no attempt, no consequences

---

## 6. LOCKED INVARIANTS

1. Two conspirators required, same country
2. Moderator-confirmed (auto in unmanned)
3. Co-conspirator independently decides (AI LLM call)
4. Probability modifiers from country_states (stability, support, protests)
5. Success swaps HoS via run_roles (is_head_of_state flag)
6. Failure arrests both via run_roles
7. `precomputed_rolls` hook + `co_conspirator_agrees` override for testing
