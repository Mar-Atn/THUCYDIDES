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
| Unlimited opposition | Default; any number of roles |
| Role with 0 positions → opposition | Automatic fallback |
| Position combos allowed | e.g., HoS + security (Furnace), economy + diplomat (Dawn) |

---

## 6. Position Changes

### 6.1 Change Leader (removes + assigns HoS)
- Removal: old HoS loses `head_of_state` from positions array
- Election: winner gains `head_of_state` added to positions array
- Actions recomputed for both roles

### 6.2 Reassign Types (HoS transfers any non-HoS position)
- *Design pending* — HoS can move military/economy/diplomat/security between roles
- Source role loses the position; target role gains it
- Actions recomputed for both roles

### 6.3 Voluntary Step-Down (HoS initiates change_leader on self)
- Same flow as change_leader but initiated by HoS
- Triggers election phase directly (no removal vote needed)

---

## 7. Implementation Architecture

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

## 8. Open Questions for Marat

1. **HoS voluntary step-down:** Should this skip the removal vote entirely and go straight to election? Or should HoS just be able to initiate the same change_leader flow?

2. **Opposition intelligence:** Should opposition roles have any intelligence capability? The Excel gives Columbia opposition some intelligence points (3). Should all opposition get basic intelligence?

3. **Reassign_types scope:** Can HoS reassign ANY position to ANY role? Or only vacant positions? Can HoS remove a position from someone without giving it to someone else (leave it vacant)?

4. **Columbia elections:** Self-nominate and cast_vote are currently Columbia-only. Should the election mechanism be available to other democratic countries in the future?

5. **Intelligence for diplomats:** The Excel gives diplomats intelligence. The contracts say "Intelligence Director or similar." Should diplomat intelligence be the same scope as security intelligence, or more limited (e.g., only about other countries' diplomatic activities)?

6. **Covert ops cards:** Are intelligence/covert_operation/assassination card-limited (consume a card from a pool) or unlimited? The contracts mention card pools but the implementation varies.

---

*DRAFT — requires Marat approval before implementation.*
