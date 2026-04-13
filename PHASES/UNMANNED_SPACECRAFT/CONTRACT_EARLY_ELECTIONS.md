# CONTRACT: Call Early Elections

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §6.7

---

## 1. PURPOSE

Head of State voluntarily calls early elections. Deterministic (no
probability roll). Sets a flag on `country_states_per_round` so the
orchestrator triggers the election engine in the next round.

---

## 2. SCHEMA

```json
{
  "action_type": "call_early_elections",
  "role_id": "pathfinder",
  "country_code": "sarmatia",
  "rationale": "Public demands democratic renewal..."
}
```

---

## 3. AUTHORIZATION

- **HoS only** — `is_head_of_state = true` required
- Role must be active (not arrested/killed/deposed)
- Rationale required (min 30 characters)

---

## 4. EFFECTS

| What | Effect |
|---|---|
| `early_election_called` flag | Set to `true` on current round's `country_states_per_round` |
| Election timing | Orchestrator processes election in **round_num + 1** |
| Election engine | Uses same `process_election()` as scheduled elections |

No stability/support cost for calling elections.

---

## 5. LOCKED INVARIANTS

1. HoS-only action (validator enforces)
2. Deterministic — no probability roll
3. Sets `early_election_called` boolean on `country_states_per_round`
4. Election happens next round (round_num + 1)
5. Same election engine as scheduled elections (§6.6)
6. Observatory event logged (`early_elections_called`)
7. No `precomputed_rolls` needed (deterministic)
