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
  ├── Arrest                 HoS only            Phase A
  ├── Reassign Types         HoS only            Phase A
  ├── Martial Law            HoS only            Phase A  [eligible country, one-time]
  ├── Change Leader          All citizens         Phase A  [stability ≤ threshold]
  └── Cast Vote              All citizens         Reactive [vote active in country]

COVERT & INTELLIGENCE
  ├── Intelligence           Security, Military, Diplomat, Citizen   Phase A  [per-round limit]
  ├── Covert Operation       Security, Military                     Phase A  [per-round limit]
  └── Assassination          Security, Military                     Phase A  [per-round limit]

COLUMBIA ELECTIONS
  ├── Self-Nominate          Columbia citizens    Phase A  [election round, moderator]
  └── Cast Election Vote     Columbia citizens    Reactive [nomination open]

COMMUNICATION (Universal)
  ├── Public Statement       All                 Phase A
  ├── Call Org Meeting       All                 Phase A
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
| **arrest** | HoS | Static | Target same country, active | unlimited |
| **reassign_types** | HoS | Static | Cannot reassign own HoS | unlimited |
| **martial_law** | HoS | Dynamic | Country in eligible list AND not yet declared | 1/sim |
| **change_leader** | All citizens | Dynamic | Stability ≤ threshold (or HoS voluntary) | 1/round |
| **cast_vote** | All citizens | Reactive | Leadership change vote active in country | 1 per vote |
| **intelligence** | security, military, diplomat, citizen | Static | — | see limits |
| **covert_operation** | security, military | Static | — | see limits |
| **assassination** | security, military | Static | — | see limits |
| **self_nominate** | Columbia citizens | Dynamic | Election round, moderator confirmed | 1/election |
| **cast_election_vote** | Columbia citizens | Reactive | Nomination open | 1/election |
| **public_statement** | All | Static | — | 3/round |
| **call_org_meeting** | All | Static | Must be org member | unlimited |
| **meet_freely** | All | Static | — | unlimited |

### 3.3 Intelligence & Covert Ops Limits (per round)

| Position | intelligence | covert_operation | assassination |
|----------|-------------|-----------------|---------------|
| security | 5 | 5 | 3 |
| military | 5 | 5 | 2 |
| diplomat | 1 | — | — |
| citizen (no position) | 2 | — | — |

On position reassignment: remaining quota transfers to new holder.

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

## 5. Open Questions

1. Should reactive actions (nuclear_authorize, accept_transaction, sign_agreement, cast_vote) be stored in role_actions at all? Or should they be computed at runtime only?

2. Should the template store the nuclear_authorize assignments (which 2 roles per country) as a separate config, or derive from position priority at sim creation?

---

*DRAFT — requires Marat review and approval.*
