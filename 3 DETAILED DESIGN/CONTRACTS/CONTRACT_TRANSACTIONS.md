# CONTRACT: Exchange Transactions

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §5.1 + `TRANSACTION_LOGIC.md` Part 1

---

## 1. PURPOSE

Exchange transactions are the economic backbone of the SIM. Any
authorized participant (human, AI, or moderator) can propose a deal
to any other participant at any time during a round. Deals execute
**instantly and atomically** once both sides confirm.

Two scopes of trading:
- **Country scope:** authorized officials trade country assets (treasury,
  military units, technology, basing rights)
- **Personal scope:** any individual trades their personal coins

---

## 2. THE FLOW

```
A proposes  ──→  B accepts   ──→  VALIDATE BOTH ──→ EXECUTE (instant, atomic)
                 B declines  ──→  CLOSED
                 B counters  ──→  A accepts  ──→  VALIDATE BOTH ──→ EXECUTE
                                  A declines ──→  CLOSED
```

One counter-offer maximum. Can always start a fresh proposal.

No timers. No delays. No special unmanned mode. The chain is
participant-driven: each step happens when the participant decides.

---

## 3. PROPOSAL SCHEMA

### 3.1 propose_transaction

```json
{
  "action_type": "propose_transaction",
  "proposer_role_id": "dealer",
  "proposer_country_code": "columbia",
  "scope": "country",
  "counterpart_role_id": "pathfinder",
  "counterpart_country_code": "sarmatia",
  "round_num": 3,
  "offer": {
    "coins": 5,
    "units": ["col_g_05", "col_g_06"],
    "technology": {"nuclear": true},
    "basing_rights": false
  },
  "request": {
    "coins": 0,
    "units": [],
    "technology": {"ai": true},
    "basing_rights": true
  },
  "rationale": "Trading ground units + nuclear tech for AI tech + basing rights"
}
```

| Field | Type | Notes |
|---|---|---|
| `scope` | `"country"` or `"personal"` | Country = treasury + units + tech + basing. Personal = personal coins only. |
| `offer` | structured dict | What the proposer GIVES. Validated at proposal time. |
| `request` | structured dict | What the proposer WANTS. NOT validated until execution. |
| `offer.coins` | int | From country treasury (scope=country) or personal wallet (scope=personal) |
| `offer.units` | list[str] | Specific unit_codes to transfer. Must be own, active or reserve. |
| `offer.technology` | dict | `{nuclear: true}` and/or `{ai: true}` — share R&D progress |
| `offer.basing_rights` | bool | Grant counterpart permission to deploy on your territory |
| `request.*` | same shape | Mirror of offer fields — what you want back |

### 3.2 respond_to_transaction

```json
{
  "transaction_id": "uuid",
  "response": "accept",
  "rationale": "Terms are acceptable — AI tech for ground forces is a fair trade"
}
```

| `response` | Effect |
|---|---|
| `"accept"` | Validate both sides → execute atomically |
| `"decline"` | Transaction closed, both notified |
| `"counter"` | New terms sent back to proposer. Must include `counter_offer` + `counter_request`. |

### 3.3 Counter-offer

```json
{
  "transaction_id": "uuid",
  "response": "counter",
  "counter_offer": { "coins": 3 },
  "counter_request": { "coins": 0, "units": ["col_g_05"], "basing_rights": true },
  "rationale": "I want fewer units and more basing rights"
}
```

Proposer then sees the counter and responds: `accept` or `decline`. No further iteration.

---

## 4. VALIDATION

### 4.1 Proposal validation (proposer side only)

| Code | Rule |
|---|---|
| `INVALID_SCOPE` | scope must be "country" or "personal" |
| `UNAUTHORIZED_ROLE` | role must have permission for the asset types offered |
| `INSUFFICIENT_COINS` | offered coins > available treasury/wallet |
| `UNKNOWN_UNIT` | offered unit_code doesn't exist |
| `NOT_OWN_UNIT` | unit doesn't belong to proposer's country |
| `UNIT_DESTROYED` | unit status is 'destroyed' |
| `INVALID_COUNTERPART` | counterpart role/country doesn't exist |
| `SELF_TRADE` | cannot trade with yourself |
| `EMPTY_TRADE` | offer and request are both empty |
| `PERSONAL_SCOPE_LIMIT` | personal scope can only trade coins, not units/tech/basing |

### 4.2 Execution validation (both sides)

At execution time, re-validate BOTH sides:
- Proposer still has offered assets?
- Counterpart has requested assets?
- If either fails → deal fails, both notified, status='failed_validation'

### 4.3 Role authorization

| Role type | Can trade (country scope) |
|---|---|
| **HoS** | Everything: coins, units, tech, basing |
| **Military chief** | Units only |
| **FM / diplomat** | Coins + basing rights |
| **Tycoon / businessman** | Personal coins only (personal scope) |
| **Any role** | Personal coins (personal scope) |

Authorization is looked up from the `roles` table `powers` field.
Simplified: if role `is_head_of_state=true` → full authority.
If `is_military_chief=true` → units only.
Otherwise → check `powers` for trade-relevant flags.

---

## 5. EXECUTION — what happens atomically

When both sides confirm, the engine executes ALL transfers in a single
atomic operation. If any single transfer fails, the entire deal rolls
back.

### 5.1 Coins (country scope)

```
proposer.country_states_per_round.treasury -= offer.coins
counterpart.country_states_per_round.treasury += offer.coins
counterpart.country_states_per_round.treasury -= request.coins
proposer.country_states_per_round.treasury += request.coins
```

### 5.2 Coins (personal scope)

```
proposer.role_state.personal_coins -= offer.coins
counterpart.role_state.personal_coins += offer.coins
(and reverse for request)
```

Note: `role_state` table may need creation if not exists. Fallback:
store personal coins on the roles row or a JSONB field.

### 5.3 Military units

```
For each unit_code in offer.units:
  unit_states_per_round[unit_code].country_code = counterpart
  unit_states_per_round[unit_code].status = 'reserve'
  unit_states_per_round[unit_code].global_row = NULL
  unit_states_per_round[unit_code].global_col = NULL
```

Transferred units go to reserve, deployable next round.

### 5.4 Technology

Per CARD_FORMULAS C.4:
- Nuclear tech share: receiver gets **+0.20** nuclear_rd_progress
- AI tech share: receiver gets **+0.15** ai_rd_progress
- Donor must be ≥1 level ahead of receiver for the transfer to apply

```
If offer.technology.nuclear:
  counterpart.nuclear_rd_progress += 0.20
If offer.technology.ai:
  counterpart.ai_rd_progress += 0.15
```

### 5.5 Basing rights

```
If offer.basing_rights:
  relationships.basing_rights[proposer → counterpart] = true
```

Revocable by host (proposer) at any time via a separate `basing_rights` action.

---

## 6. PERSISTENCE

### 6.1 `exchange_transactions` table (enhanced)

```sql
exchange_transactions:
  id, sim_run_id, round_num,
  proposer_role_id, proposer_country_code, scope,
  counterpart_role_id, counterpart_country_code,
  offer (jsonb), request (jsonb),
  status (pending|accepted|declined|countered|executed|failed_validation|expired),
  counter_offer (jsonb), counter_request (jsonb),
  proposer_rationale, counterpart_rationale,
  executed_at, created_at
```

### 6.2 Events

- `event_type='transaction_proposed'` — when proposal created
- `event_type='transaction_accepted'` — when counterpart accepts
- `event_type='transaction_executed'` — when assets transfer
- `event_type='transaction_declined'` — when declined
- `event_type='transaction_countered'` — when counter-offered
- `event_type='transaction_failed'` — when validation fails at execution

---

## 7. CONTEXT PROVIDED TO COUNTERPART

When a proposal arrives, the counterpart sees:

```
[INCOMING TRANSACTION PROPOSAL]
  From: {proposer_role} of {proposer_country}
  Scope: country | personal

  THEY OFFER:
    Coins: 5 (from their treasury)
    Units: col_g_05 (ground), col_g_06 (ground)
    Technology: nuclear R&D share
    Basing rights: no

  THEY REQUEST:
    Coins: 0
    Units: (none)
    Technology: AI R&D share
    Basing rights: yes (deploy on your territory)

  Rationale: "Trading ground units + nuclear tech for AI tech + basing rights"

[YOUR CURRENT STATE]
  Treasury: 50 coins
  AI R&D progress: 0.45
  Nuclear R&D progress: 0.20
  (other relevant context)

[DECISION]
  Respond: ACCEPT / DECLINE / COUNTER
  If COUNTER: specify your revised offer + request terms.
  Rationale required (>= 30 chars).
```

---

## 8. LOCKED INVARIANTS

1. Both sides must explicitly confirm — no assumed acceptance
2. Proposer's assets validated at PROPOSAL. Both sides validated at EXECUTION.
3. Execution is atomic — all transfers succeed or all fail
4. One counter-offer maximum per proposal
5. Coins flow is instant and irreversible (except basing = revocable)
6. Unit transfers: specific unit_codes, receiver gets them in reserve
7. Tech transfer: +0.20 nuclear, +0.15 AI (CARD_FORMULAS C.4)
8. Role authorization enforced: HoS = all, military = units, FM = coins+basing
9. Personal scope = personal coins only
10. Transaction system is actor-agnostic: same API for human, AI, moderator
