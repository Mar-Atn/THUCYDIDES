# Actions Tab — Template Customization

**Date:** 2026-04-19 | **Status:** DRAFT — awaiting Marat review
**Module:** M9 (Template Editor) | **Tab position:** After Roles

---

## 1. Purpose

A dedicated tab for reviewing and configuring all action permissions across the simulation. The single place where a game designer can see WHO can do WHAT under WHICH conditions — and customize it for each template.

---

## 2. Layout

### Left Panel (30%): Action Library

Grouped by category, each action shown as a row:

```
MILITARY ACTIONS
  ├── Ground Attack          HoS, Military       Phase A
  ├── Air Strike             HoS, Military       Phase A
  ├── Naval Combat           HoS, Military       Phase A
  ├── Naval Bombardment      HoS, Military       Phase A
  ├── Missile (conventional) HoS, Military       Phase A  [country has missiles]
  ├── Naval Blockade         HoS, Military       Phase A
  └── Move Units             HoS, Military       Phase B only

NUCLEAR CHAIN
  ├── Nuclear Test           HoS only            Phase A  [nuclear_level ≥ 1]
  ├── Nuclear Launch         HoS only            Phase A  [nuclear_confirmed]
  ├── Nuclear Authorize      2 per country *     Reactive [launch pending]
  └── Nuclear Intercept      HoS, Military       Reactive [missile in flight, L2+]

ECONOMIC
  ├── Set Budget             HoS, Economy        Phase A
  ├── Set Tariffs            HoS, Economy        Phase A
  ├── Set Sanctions          HoS, Economy        Phase A
  └── Set Oil Production     HoS, Economy        Phase A  [OPEC member]

DIPLOMATIC
  ├── Declare War            HoS only            Phase A
  ├── Propose Agreement      HoS, Diplomat       Phase A
  ├── Sign Agreement         HoS, Diplomat       Reactive [agreement proposed]
  ├── Propose Transaction    HoS, Diplomat       Phase A
  ├── Accept Transaction     HoS, Diplomat       Reactive [transaction proposed]
  └── Basing Rights          HoS, Diplomat       Phase A

POLITICAL
  ├── Arrest                 HoS, Security       Phase A  [arrested = no actions]
  ├── Reassign Types         HoS only            Phase A
  ├── Martial Law            HoS only            Phase A  [eligible country, one-time]
  ├── Change Leader          All citizens         Phase A  [stability ≤ threshold]
  └── Cast Vote              All citizens         Reactive [vote active in country]

COVERT & INTELLIGENCE
  ├── Intelligence           Security, Military, Diplomat, Opposition  Phase A  [per-SIM limit]
  ├── Covert Operation       Security, Military                       Phase A  [per-SIM limit]
  └── Assassination          Security, Military                       Phase A  [per-SIM limit]

COLUMBIA ELECTIONS
  ├── Self-Nominate          Columbia citizens    Phase A  [election round, moderator]
  └── Cast Election Vote     Columbia citizens    Reactive [nomination open]

COMMUNICATION (Universal)
  ├── Public Statement       All                 Phase A
  ├── Call Org Meeting       Org members          Phase A
  ├── Publish Org Decision   Org chairmen         Phase A  [formal publication]
  └── Meet Freely            All                 Phase A
```

### Right Panel (70%): Action Detail

When an action is selected, shows:

```
┌────────────────────────────────────────────────────┐
│ GROUND ATTACK                              Phase A │
├────────────────────────────────────────────────────┤
│ Positions: head_of_state, military                 │
│ Type: Static (always available to these positions) │
│                                                    │
│ ASSIGNMENTS (this template):                       │
│ ┌──────────────┬──────────┬───────┬──────────────┐ │
│ │ Country      │ Role     │ Has?  │ Limit        │ │
│ ├──────────────┼──────────┼───────┼──────────────┤ │
│ │ Columbia     │ Dealer   │ ✓     │ unlimited    │ │
│ │ Columbia     │ Shield   │ ✓     │ unlimited    │ │
│ │ Columbia     │ Volt     │ ✗     │ —            │ │
│ │ Columbia     │ Anchor   │ ✗     │ —            │ │
│ │ ...          │ ...      │       │              │ │
│ │ Cathay       │ Helmsman │ ✓     │ unlimited    │ │
│ │ Cathay       │ Rampart  │ ✓     │ unlimited    │ │
│ │ ...          │ ...      │       │              │ │
│ └──────────────┴──────────┴───────┴──────────────┘ │
│                                                    │
│ DYNAMIC CONDITIONS:                                │
│  (none — always available to assigned positions)   │
│                                                    │
│ [Assign to All Matching Positions]                 │
│ [Override: Add/Remove for specific role]           │
└────────────────────────────────────────────────────┘
```

For a dynamic action like Nuclear Test:

```
┌────────────────────────────────────────────────────┐
│ NUCLEAR TEST                               Phase A │
├────────────────────────────────────────────────────┤
│ Positions: head_of_state                           │
│ Type: Dynamic                                      │
│                                                    │
│ CONDITIONS:                                        │
│  ● Country must have nuclear_level ≥ 1             │
│  ● HoS position required                          │
│                                                    │
│ CURRENTLY ELIGIBLE (based on country state):       │
│  ✓ Sarmatia  (Pathfinder, L3 confirmed)           │
│  ✓ Cathay    (Helmsman, L2 confirmed)             │
│  ✓ Columbia  (Dealer, L3 confirmed)               │
│  ✗ Persia    (Anvil, L1 NOT confirmed)            │
│  ✗ Ruthenia  (Sentinel-R, L0)                     │
│  ...                                               │
└────────────────────────────────────────────────────┘
```

For Nuclear Authorize:

```
┌────────────────────────────────────────────────────┐
│ NUCLEAR AUTHORIZE                         Reactive │
├────────────────────────────────────────────────────┤
│ Type: Country-specific (2 roles per country)       │
│ Selection priority: military > security >          │
│   diplomat > economy > opposition                  │
│                                                    │
│ ASSIGNED AUTHORIZERS:                              │
│  Columbia:  Shield (military), Shadow (security)   │
│  Cathay:    Rampart (military), Abacus (economy)   │
│  Sarmatia:  Ironhand (military), Compass (security)│
│  Persia:    Anvil (military), Dawn (economy)       │
│  Ruthenia:  Bulwark (military), Broker (economy)   │
│  ...single-role countries: AI Officer auto-assigns │
│                                                    │
│ TRIGGER: Only appears when HoS initiates nuclear   │
│ launch in that country                             │
│                                                    │
│ [Auto-assign by priority] [Override per country]   │
└────────────────────────────────────────────────────┘
```

---

## 3. Comprehensive Action Rules

### 3.1 Action Types

| ID | Type | Description |
|----|------|-------------|
| **Static** | Always available to assigned positions | Most actions |
| **Dynamic** | Available only when country state meets conditions | Nuclear, OPEC, martial law |
| **Reactive** | Appears only when triggered by another action/event | Authorize, intercept, accept, sign, cast_vote |
| **Phase-restricted** | Available only in specific game phase | move_units (Phase B only) |

### 3.2 Full Rules Table

| Action | Positions | Type | Conditions | Limit |
|--------|-----------|------|------------|-------|
| **ground_attack** | HoS, military | Static | — | unlimited |
| **air_strike** | HoS, military | Static | — | unlimited |
| **naval_combat** | HoS, military | Static | — | unlimited |
| **naval_bombardment** | HoS, military | Static | — | unlimited |
| **launch_missile_conventional** | HoS, military | Dynamic | Country has deployed strategic_missile units | unlimited |
| **naval_blockade** | HoS, military | Static | — | unlimited |
| **move_units** | HoS, military | Phase-restricted | Phase B only | unlimited |
| **ground_move** | HoS, military | Static | — | unlimited |
| **nuclear_test** | HoS | Dynamic | `nuclear_level ≥ 1` | unlimited |
| **nuclear_launch_initiate** | HoS | Dynamic | `nuclear_confirmed = true` | unlimited |
| **nuclear_authorize** | 2 per country (configurable) | Reactive | Nuclear launch pending in own country | 1 per launch |
| **nuclear_intercept** | HoS, military | Reactive + Dynamic | Missile in flight AND `nuclear_level ≥ 2` AND confirmed | 1 per launch |
| **set_budget** | HoS, economy | Static | — | 1/round |
| **set_tariffs** | HoS, economy | Static | — | 1/round |
| **set_sanctions** | HoS, economy | Static | — | 1/round |
| **set_opec** | HoS, economy | Dynamic | Country is OPEC+ member | 1/round |
| **declare_war** | HoS | Static | — | unlimited |
| **propose_agreement** | HoS, diplomat | Static | — | unlimited |
| **sign_agreement** | HoS, diplomat | Reactive | Agreement proposed to country | — |
| **propose_transaction** | HoS, diplomat | Static | — | unlimited |
| **accept_transaction** | HoS, diplomat | Reactive | Transaction proposed to country | — |
| **basing_rights** | HoS, diplomat | Static | — | unlimited |
| **arrest** | HoS, security | Static | Target same country, active. Arrested participant has NO actions available until released. | unlimited |
| **reassign_types** | HoS | Static | Cannot reassign own HoS | unlimited |
| **martial_law** | HoS | Dynamic | Country in eligible list AND not yet declared | 1/sim |
| **change_leader** | All citizens | Dynamic | Stability ≤ threshold (or HoS voluntary) | 1/round |
| **cast_vote** | All citizens | Reactive | Leadership change vote active in country | 1 per vote |
| **intelligence** | security, military, diplomat, opposition | Static | — | see limits |
| **covert_operation** | security, military | Static | — | see limits |
| **assassination** | security, military | Static | — | see limits |
| **self_nominate** | Columbia citizens | Dynamic | Election round, moderator confirmed | 1/election |
| **cast_election_vote** | Columbia citizens | Reactive | Nomination open | 1/election |
| **public_statement** | All | Static | — | 3/round |
| **call_org_meeting** | All org members | Static | Must be member of the organization | unlimited |
| **publish_org_decision** | Org chairmen | Static | Must be chairman of the organization. Formal publication of org decisions (appears on public screen). | unlimited |
| **meet_freely** | All | Static | — | unlimited |

### 3.3 Intelligence & Covert Ops Limits (per SIM)

Limits are **per entire SIM** (not per round). When a position is reassigned, the **remaining quota transfers** to the new holder.

| Position | intelligence | covert_operation | assassination |
|----------|-------------|-----------------|---------------|
| security | 5 | 5 | 3 |
| military | 5 | 5 | 2 |
| diplomat | 1 | — | — |
| opposition | 2 | — | — |
| citizen (no position) | 0 | — | — |

On position reassignment: remaining uses transfer to the new position holder.

### 3.4 Nuclear Authorize — Country-Specific Assignment

2 roles per country, auto-selected by position priority:
`military > security > diplomat > economy > opposition`

Template can override to assign specific roles.

For single-role countries (e.g., Gallia): 1 AI Officer auto-assigned.

### 3.5 Dynamic Condition Sources

| Condition | Source Table | Field |
|-----------|-------------|-------|
| nuclear_level | countries | nuclear_level |
| nuclear_confirmed | countries | nuclear_confirmed |
| OPEC membership | config (static list) | — |
| Martial law eligible | config (static list) | — |
| martial_law_declared | countries | martial_law_declared |
| Stability threshold | sim_runs.schedule | change_leader_threshold |
| Phase A/B | sim_runs | current_phase |
| Missile in flight | nuclear_actions | status = 'awaiting_interception' |
| Vote active | leadership_votes | status = 'voting' |
| Agreement pending | agreements | status = 'proposed' |
| Transaction pending | exchange_transactions | status = 'pending' |

---

## 4. Template Storage

### Option: role_actions table with metadata

Current `role_actions` table has: `sim_run_id, role_id, action_id, uses_per_round, uses_total, notes`

This is sufficient. The Actions tab reads and writes this table.

### Computed vs Manual

Two modes for populating role_actions:

1. **Auto-compute from positions:** `compute_actions(role.positions, country, state)` → generates role_actions rows. Used for initial setup and after position changes.

2. **Manual override:** Game designer adds/removes specific actions for specific roles via the Actions tab. Overrides are flagged with `notes = 'manual_override'` to prevent auto-compute from reverting them.

---

## 5. Position Types (canonical list)

| Position | Max per Country | Description |
|----------|----------------|-------------|
| `head_of_state` | 1 | Political leader, top authority |
| `military` | 1 | Commands military forces |
| `economy` | 1 | Budget, trade, sanctions |
| `diplomat` | 1 | Agreements, treaties, transactions |
| `security` | 1 | Intelligence, covert operations, arrests |
| `opposition` | unlimited | Formal opposition with limited intelligence |
| *(citizen)* | — | Default fallback: no position. Universal actions only. |

A role can hold 0–N positions. A role with no positions is a *citizen*.

---

## 6. Reactive Actions — Runtime Only

**DECIDED:** Reactive actions are NOT stored in role_actions. They are computed at runtime when triggered. This prevents stale permissions after position changes or arrests.

Reactive actions: `nuclear_authorize`, `nuclear_intercept`, `accept_transaction`, `sign_agreement`, `cast_vote`, `cast_election_vote`.

These appear in **Actions Expected Now** when their trigger condition is met.

---

## 7. Nuclear Authorize — Derived from Position Priority

**DECIDED:** Not stored as config. Derived at launch time from position priority:
`military > security > diplomat > economy > opposition`

Pick the top 2 available roles in the launching country. Single-role countries: 1 AI Officer auto-assigned.

---

## 8. Decisions Log

| # | Question | Decision | Date |
|---|----------|----------|------|
| 1 | Reactive actions in role_actions? | No — computed at runtime only. Prevents stale permissions. | 2026-04-19 |
| 2 | Nuclear authorize storage? | Derived from position priority at launch time, not stored. | 2026-04-19 |
| 3 | Arrest available to? | HoS + security (was HoS only) | 2026-04-19 |
| 4 | Intel/covert limits scope? | Per entire SIM (not per round). Remaining quota transfers on position change. | 2026-04-19 |
| 5 | Position naming? | HoS, military, economy, diplomat, security, opposition. Citizen = no position (fallback). | 2026-04-19 |
| 6 | Call org meeting? | Org members only | 2026-04-19 |
| 7 | Publish org decision? | New action — org chairmen only. Formal publication on public screen. | 2026-04-19 |
| 8 | Intelligence for opposition? | Yes, 2/sim. Citizens (no position) get 0. | 2026-04-19 |

---

*APPROVED by Marat 2026-04-19. Ready for implementation.*
