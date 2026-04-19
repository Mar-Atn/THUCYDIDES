# Positions & Actions — Authorization Model

**Date:** 2026-04-18 | **Status:** DRAFT — awaiting Marat review
**Depends on:** All M6 action implementations, CONTRACT files

---

## 1. Core Concept

A **position** is a functional hat that a role wears. It defines what actions are available. Positions are **transferable** — they can be assigned, removed, and combined.

Actions are **not statically assigned** to roles. They are **computed** from:
1. The role's current positions (0 to many)
2. The country's game state (nuclear level, OPEC membership, etc.)
3. The current game phase (Phase A vs Phase B, election rounds, etc.)
4. Contextual triggers (nuclear launch in progress, etc.)

---

## 2. Position Types

| Position | Max per Country | Description |
|----------|----------------|-------------|
| `head_of_state` | 1 | Political leader, top authority |
| `military` | 1 | Commands military forces |
| `economy` | 1 | Budget, trade, sanctions |
| `diplomat` | 1 | Agreements, treaties, transactions |
| `security` | 1 | Intelligence, covert operations |
| `opposition` | unlimited | Default for unassigned roles; basic rights |

**Rules:**
- A role can hold **0 to N positions** (e.g., Furnace = HoS + Security)
- A role with **no positions** automatically receives `opposition`
- Each country can have **at most 1** of HoS, military, economy, diplomat, security
- `opposition` has **no limit** — multiple roles can hold it simultaneously
- Positions are stored as `roles.positions: text[]`

---

## 3. Action Layers

Actions are determined by three layers, evaluated in order:

### Layer 1: Universal Actions (available to ALL roles, regardless of position)

| Action | Phase | Notes |
|--------|-------|-------|
| `public_statement` | A | — |
| `call_org_meeting` | A | If member of an org |
| `meet_freely` | A | — |
| `change_leader` | A | Non-HoS initiates removal vote; HoS can voluntarily initiate (step down) |
| `cast_vote` | A | When a leadership change vote is active in their country |

### Layer 2: Position Actions (available based on position held)

#### head_of_state
| Action | Phase | Dynamic Condition |
|--------|-------|-------------------|
| `declare_war` | A | — |
| `arrest` | A | Target must be same country, active |
| `reassign_types` | A | *Design pending* |
| `martial_law` | A | Country in eligible list AND not yet declared |
| `basing_rights` | A | — |
| `set_budget` | A | — |
| `set_tariffs` | A | — |
| `set_sanctions` | A | — |
| `set_opec` | A | Country is OPEC+ member |
| `ground_attack` | A | — |
| `air_strike` | A | — |
| `naval_combat` | A | — |
| `naval_bombardment` | A | — |
| `launch_missile_conventional` | A | Country has deployed strategic_missile units |
| `naval_blockade` | A | — |
| `move_units` | B | Inter-round only |
| `ground_move` | A | — |
| `nuclear_test` | A | Country has `nuclear_level >= 1` |
| `nuclear_launch_initiate` | A | Country has `nuclear_confirmed = true` |
| `nuclear_intercept` | A* | Country has `nuclear_level >= 2` AND confirmed; *only during active launch* |
| `propose_transaction` | A | — |
| `accept_transaction` | A | When pending transaction received |
| `propose_agreement` | A | — |
| `sign_agreement` | A | When pending agreement received |

#### military
| Action | Phase | Dynamic Condition |
|--------|-------|-------------------|
| `ground_attack` | A | — |
| `air_strike` | A | — |
| `naval_combat` | A | — |
| `naval_bombardment` | A | — |
| `launch_missile_conventional` | A | Country has deployed strategic_missile units |
| `naval_blockade` | A | — |
| `move_units` | B | Inter-round only |
| `ground_move` | A | — |
| `nuclear_authorize` | A* | *Only when authorization request pending* |
| `nuclear_intercept` | A* | Country has `nuclear_level >= 2` AND confirmed; *only during active launch* |
| `intelligence` | A | *Design pending — card-based or unlimited?* |
| `covert_operation` | A | *Design pending* |
| `assassination` | A | *Design pending* |

#### economy
| Action | Phase | Dynamic Condition |
|--------|-------|-------------------|
| `set_budget` | A | — |
| `set_tariffs` | A | — |
| `set_sanctions` | A | — |
| `set_opec` | A | Country is OPEC+ member |
| `nuclear_authorize` | A* | *Only when authorization request pending* |

#### diplomat
| Action | Phase | Dynamic Condition |
|--------|-------|-------------------|
| `propose_transaction` | A | — |
| `accept_transaction` | A | When pending transaction received |
| `propose_agreement` | A | — |
| `sign_agreement` | A | When pending agreement received |
| `basing_rights` | A | — |
| `nuclear_authorize` | A* | *Only when authorization request pending* |
| `intelligence` | A | *Design pending* |

#### security
| Action | Phase | Dynamic Condition |
|--------|-------|-------------------|
| `intelligence` | A | *Design pending* |
| `covert_operation` | A | *Design pending* |
| `assassination` | A | *Design pending* |

#### opposition (default for unassigned roles)
| Action | Phase | Dynamic Condition |
|--------|-------|-------------------|
| `intelligence` | A | *Design pending — limited scope?* |
| `self_nominate` | A | Columbia only, specific election rounds, moderator-confirmed |
| `cast_vote` | A | Columbia only, during active election |

*Note: opposition also gets all Universal actions (Layer 1).*

### Layer 3: Contextual Actions (appear/disappear based on game events)

These are NOT stored in role_actions. They appear dynamically in the UI:

| Action | Trigger | Who sees it |
|--------|---------|-------------|
| `nuclear_authorize` | Nuclear launch initiated by own country | Roles with military/economy/diplomat position |
| `nuclear_intercept` | Nuclear launch in flight phase | HoS + military of L2+ nuclear countries |
| `accept_transaction` | Transaction proposed to this country | HoS + diplomat |
| `sign_agreement` | Agreement proposed with this country as signatory | HoS + diplomat |
| `cast_vote` | Leadership change vote active in country | All citizens of that country |
| `move_units` | Phase B (inter-round) | HoS + military |

---

## 4. Country-Level Modifiers

Some actions depend on country state, not just position:

| Modifier | Actions Affected | Rule |
|----------|-----------------|------|
| `nuclear_level >= 1` | `nuclear_test` | Unlocked for HoS |
| `nuclear_confirmed = true` | `nuclear_launch_initiate` | Unlocked for HoS |
| `nuclear_level >= 2 + confirmed` | `nuclear_intercept` | Unlocked for HoS + military |
| OPEC+ membership | `set_opec` | Unlocked for HoS + economy |
| `MARTIAL_LAW_POOLS` country | `martial_law` | Unlocked for HoS (one-time) |
| Columbia | `self_nominate`, `cast_vote` | Unlocked for opposition (election rounds) |

---

## 5. Position Constraints

| Rule | Detail |
|------|--------|
| Max 1 HoS per country | Enforced at assignment time |
| Max 1 military per country | Enforced at assignment time |
| Max 1 economy per country | Enforced at assignment time |
| Max 1 diplomat per country | Enforced at assignment time |
| Max 1 security per country | Enforced at assignment time |
| Position combos allowed | e.g., HoS + security (Furnace), economy + diplomat (Dawn) |
| Role with 0 positions | Normal citizen — gets universal actions only (Layer 1) |

---

## 6. Position Changes

### 6.1 Change Leader (removes + assigns HoS)
- **Citizen-initiated:** Non-HoS starts removal vote → election (current flow)
- **HoS voluntary step-down:** HoS initiates → skips removal vote → goes straight to election
- Removal: old HoS loses `head_of_state` from positions array
- Election: winner gains `head_of_state` added to positions array
- Actions recomputed for both roles

### 6.2 Reassign Types (HoS reassigns any non-HoS position)
- HoS can move `military`, `economy`, `diplomat`, `security` to any role in the country
- HoS CANNOT reassign the `head_of_state` position (use change_leader for that)
- Can leave a position vacant (remove from source without assigning to target)
- Can assign to a role that already holds other positions (creates combo)
- Source role loses the position; target role gains it
- Actions recomputed for affected roles

---

## 7. Intelligence & Covert Ops — Limits per Round

Operations are **limited per round** by position. When a position is reassigned mid-round, the **remaining quota transfers** to the new holder.

| Position | Intelligence | Covert Ops | Assassination |
|----------|-------------|------------|---------------|
| `security` | 5/round | 5/round | 3/round |
| `military` | 5/round | 5/round | 2/round |
| `diplomat` | 1/round | — | — |
| `opposition` / citizen (no position) | 2/round | — | — |

*Note: These are per-round limits. Country-level modifiers may apply in future.*

---

## 8. Columbia Elections

- `self_nominate` and `cast_vote` are **Columbia-only** mechanisms
- Available in designated election rounds, confirmed by moderator
- Not applicable to other countries

---

## 9. Implementation Architecture

```
roles.positions: text[]              -- e.g. ['head_of_state', 'security']
engine/config/position_actions.py    -- rules engine (Layer 2 + conditions)
role_actions table                   -- computed from positions + country state
```

**Recompute triggers:**
- Position assigned/removed (change_leader, reassign_types)
- Country state changes (nuclear_level upgrade, OPEC join/leave)
- Game phase changes (Phase A ↔ Phase B)

**The role_actions table is a CACHE of computed permissions, not a source of truth.** The source of truth is: `positions[] + country state + game phase → available actions`.

---

## 10. Decisions Log

| # | Question | Decision | Date |
|---|----------|----------|------|
| 1 | HoS voluntary step-down | Yes — skip removal vote, straight to election | 2026-04-19 |
| 2 | Unpositioned roles | Normal citizen (no forced "opposition" label), gets universal actions + 2 intelligence/round | 2026-04-19 |
| 3 | Reassign_types scope | Any position to any role, except HoS's own position. Can leave vacant. | 2026-04-19 |
| 4 | Columbia elections | Columbia only | 2026-04-19 |
| 5 | Diplomat intelligence | Same scope as security, 1 request/round | 2026-04-19 |
| 6 | Covert ops limits | Limited by position per round (see §7). On reassignment, remaining quota transfers. | 2026-04-19 |

---

## 11. Actions Still Pending Final Design

| Action | Status | Notes |
|--------|--------|-------|
| `intelligence` | Limits decided, mechanics TBD | LLM-generated report with noise |
| `covert_operation` | Limits decided, mechanics TBD | Sabotage, propaganda, election meddling |
| `assassination` | Limits decided, mechanics TBD | Target selection, success probability |
| `reassign_types` | Rules decided, UX TBD | Position transfer UI |
| `self_nominate` | Columbia-only, mechanics TBD | Election round trigger |
| `cast_vote` | Columbia-only, mechanics TBD | Simple majority |

---

*APPROVED by Marat 2026-04-19. Implementation can proceed for the positions array + recompute engine. Pending actions (§11) designed separately.*
