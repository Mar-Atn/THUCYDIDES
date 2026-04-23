# TTT WORLD MODEL — The Simulation Specification

**Version:** 2.0 DRAFT | **Date:** 2026-04-22
**Status:** UNDER REVIEW — Marat must validate before this becomes canonical
**Purpose:** Single source of truth for what the TTT simulation IS — its entities, rules, actions, and lifecycle.
**Audience:** Developers, AI agents, facilitators, product owner.

**Methodology:** Every claim in this document has been verified against the actual codebase (engine source, DB schema, module SPECs). No invented content. Where code contradicts spec, both are noted.

---

## 1. THE SIMULATION

### Purpose

The Thucydides Trap (TTT) is an immersive leadership simulation that places human participants and AI-operated countries into a fictional geopolitical crisis modeled on a great-power transition.

**The central question:** What happens to the global order when the power that built it can no longer sustain it alone — and the power rising to challenge it has a fundamentally different vision?

The trap operates at three layers simultaneously:
- **Structural:** The visible power balance is shifting. Neither side has decisive advantage.
- **Situational:** Multiple simultaneous crises overwhelm the system's capacity to respond.
- **Personal:** Leaders face the intersection of national interest and personal survival.

### What Participants Experience

Each round (representing ~6 months of real time), participants:
1. **Negotiate freely** — face-to-face, in bilateral meetings, through back-channels
2. **Take actions** — military, economic, diplomatic, covert, political
3. **Receive consequences** — engines update the world state
4. **Adapt** — new intelligence, new crises, new opportunities

### Design Principles

- **Communication is primary.** The simulation is primarily about negotiation, persuasion, and deal-making. Actions are tools; conversations are strategy.
- **Fictional names, real dynamics.** Country names are fictional with transparent real-world parallels.
- **Both war and peace are plausible.** No predetermined outcome.

---

## 2. TEMPLATE AND SIM RUN

**Two-level hierarchy** (scenarios retired per M9 architectural decision):

```
TEMPLATE (master SIM design — editable, versioned)
  └── SIM RUN (one execution — snapshot of template at creation, mutable during play)
```

### Template

The template defines the complete world design:
- Countries with starting economic, political, military, and technological state
- Roles with character names, titles, objectives, powers, covert cards
- Organizations with memberships, decision rules, voting thresholds
- Starting relationships, sanctions, tariffs between countries
- Military deployments (individual units with hex positions)
- Map configuration, theater linkage, zone definitions
- Formula coefficients for all engines
- Schedule defaults (round count, phase durations)
- Key events (elections, scheduled crises)

The template data lives in the **default SimRun** (UUID `00000000-...-000000000001`), which serves as the canonical source for all game data.

### Sim Run

When a moderator creates a SimRun, the server copies all game tables from the source SimRun, re-keying `sim_run_id`. Tables copied: countries, roles, role_actions, relationships, zones, deployments, organizations, org_memberships, sanctions, tariffs, world_state (round 0), artefacts.

From that point, the SimRun's data is independent and mutable during play.

**Sim run states:** `setup` → `pre_start` → `active` ↔ `paused` → `processing` → `active` (next round) → ... → `completed` or `aborted`

The `paused` state is used during nuclear launch sequences (authorization and interception are allowed while paused).

---

## 3. ENTITIES

### Countries

Each country in the template has:

| Category | Key Attributes |
|----------|---------------|
| **Identity** | sim_name, real-world parallel, country_brief |
| **Team** | regime_type (democracy, hybrid, autocracy), team_size, AI-operated flag |
| **Economy** | GDP, GDP growth rate, treasury, inflation, trade balance, tax rate, debt burden, debt ratio, sector weights (resources, industry, services, technology) |
| **Oil** | oil_producer flag, OPEC member flag, production level (mbpd) |
| **Military** | unit counts by type (ground, naval, tactical_air, strategic_missiles, air_defense), production costs and capacities, maintenance cost per unit |
| **Political** | stability (range 1.0–9.0), war_tiredness, martial_law flag |
| **Technology** | nuclear_level (0–3), nuclear R&D progress, AI level (0–4), AI R&D progress |

Countries are organized into **team countries** (multiple human players each) and **solo countries** (1 human or AI each). The specific countries and their parallels are defined by the template.

### Roles

Each role represents one participant character:

| Category | Key Attributes |
|----------|---------------|
| **Identity** | character_name, title, country_code |
| **Position** | position_type: head_of_state, minister, general, diplomat, special |
| **Permissions** | positions array (determines which actions this role can take via `role_actions` table) |
| **Flags** | is_head_of_state, is_military_chief, is_diplomat, is_economy_officer |
| **Capabilities** | powers (special abilities), objectives (personal goals) |
| **Covert cards** | intelligence, sabotage, cyber, disinformation, election_meddling, assassination (integer counts, consumed permanently on use) |
| **Content** | public_bio (visible to all), confidential_brief (only this player sees it) |
| **Status** | active, arrested, killed |

### Military Forces

**Individual unit model:** Each unit is one row in the `deployments` table.

| Unit Type | Purpose |
|-----------|---------|
| `ground` | Land combat (RISK dice), territory control, garrison |
| `naval` | Sea combat, bombardment of adjacent land, blockade support |
| `tactical_air` | Air strikes (2-hex range), air defense counter |
| `strategic_missile` | Long-range conventional or nuclear strike. Consumed on firing. |
| `air_defense` | Intercepts missiles, reduces air strike effectiveness |

Units have: `unit_id`, `country_code`, `unit_type`, position (`global_row/col` + `theater/row/col`), `unit_status` (active/reserve/destroyed/captured), `embarked_on` (carrier unit for transport).

**Producible types:** Only ground, naval, and tactical_air can be produced via budget allocation. Strategic missiles and air defense are template-defined starting assets.

### Organizations

International bodies with distinct decision rules:

| Attribute | Description |
|-----------|-------------|
| **decision_rule** | consensus, majority, or unanimity |
| **chair_role_id** | Who presides |
| **voting_threshold** | unanimous, simple_majority, etc. |
| **has_veto** | Per-member flag (e.g., P5 in UNSC) |

Organizations can hold meetings, and players may propose creating new organizations. The specific organizations and their memberships are defined by the template.

---

## 4. RELATIONSHIPS

### Between Countries

Each country pair has a bilateral relationship record:

| Field | Values | Effect |
|-------|--------|--------|
| **relationship** | allied, friendly, neutral, tense, hostile | Diplomatic context |
| **status** | peace, at_war | Determines combat legality |
| **basing_rights** | a_to_b, b_to_a (boolean each) | Allows military presence on foreign territory |

### Sanctions

Per-country bilateral. Levels -3 to +3:
- Positive = sanctions imposed. S-curve damage model: coverage below 0.3 = minimal, above 0.6 = severe (tipping point at 0.5–0.6). Maximum damage depends on target's economic sector composition.
- Negative = evasion support (helping target circumvent others' sanctions).
- Stateless: recomputed every round from current levels and global GDP shares.

### Tariffs

Per-country bilateral. Levels 0 to 3. Prisoner's dilemma model: hurts BOTH sides (imposer at 50% of target's pain). Generates customs revenue for imposer. Adds tariff-driven inflation. GDP impact capped at -20%.

### Agreements

Formal treaties between countries. Types: security, trade, basing, technology_sharing, ceasefire, general.
- Proposer auto-signs; counterpart(s) must countersign to activate.
- Can be public or secret. Multiple signatories possible.
- **Auto-relationship update** on activation: military_alliance → sets relationship to "alliance", trade_agreement → "economic_partnership", ceasefire → "hostile" (stops combat but not friendly).
- No enforcement mechanism — agreements are diplomatic records.

### Transactions

Bilateral asset exchanges. One side offers, the other provides. Tradeable assets: coins, units (specific units from reserve), technology (nuclear or AI progress), basing rights. Counterpart can accept, decline, or counter-offer. Can be public or secret.

**Technology transfer values:** Nuclear = +0.20 progress to recipient. AI = +0.15 progress.

---

## 5. ACTIONS

### Canonical Action Catalog

**Source of truth:** `MODULES/MODULE_REGISTRY.md`, ACTION_NAMING section.

Every action has: a canonical name, required fields, an engine that processes it, and defined effects. The `role_actions` table defines which actions each role is permitted to perform.

#### Military — Combat (6 actions)

| Action | Mechanic |
|--------|----------|
| `ground_attack` | RISK iterative dice. Attacker rolls min(3, alive), defender rolls min(2, alive). Sorted descending, paired, ties → defender wins. Loop until one side eliminated. Max 50 exchanges. |
| `ground_move` | Unopposed advance into hex with no enemy ground defenders. 100% success (no dice). Captures non-ground enemy units as trophies (to attacker's reserve). Records territory in `hex_control`. Must leave 1 ground unit behind on foreign occupied hexes. |
| `air_strike` | Per-unit independent rolls. 12% hit (6% if target has air defense). 2-hex range. Air superiority: +2% per extra unit (cap +4%). Clamped 3–20%. 15% chance attacker downed if AD present. |
| `naval_combat` | RISK iterative dice at sea. Both sides roll up to 3 dice (unlike ground where defender rolls max 2). Fleet advantage modifier: larger fleet gets +N to highest die (N = size difference, clamped ±3). |
| `naval_bombardment` | 10% hit per naval unit, sea → adjacent land hex. Each hit destroys one random ground defender. |
| `launch_missile_conventional` | Two-phase: AD interception (50% per AD unit in zone), then hit roll (75% flat). 4 target choices (military, infrastructure, nuclear_site, AD). Range by nuclear tier: T1=2 hex, T2=4 hex, T3=global. Missile consumed on firing. |

**Combat modifiers (ground):** AI L3 (+1 die), AI L4 (+2 dice, 50% chance determined at level-up), low morale (-1 if stability ≤3), die-hard terrain (+1 defender), air support (+1 defender, doesn't stack with die-hard), amphibious penalty (-1 attacker for sea-to-land).

#### Military — Non-Combat (7 actions)

| Action | What it does |
|--------|-------------|
| `move_units` | Peaceful repositioning of own units. Batch operation: deploy from reserve, withdraw to reserve, reposition between hexes, embark/debark. Own territory or basing rights only. Allowed in both Phase A and inter-round. |
| `naval_blockade` | Establish, lift, or reduce blockade at chokepoints. Requires naval units at the chokepoint (Gulf Gate also accepts ground on adjacent land). Levels: full or partial. Auto-integrity check after combat: 0 units → auto-lift. |
| `basing_rights` | Host country grants or revokes foreign military access to their territory. |
| `martial_law` | Emergency powers. One-time per country per simulation. Eligible countries defined by template. |
| `nuclear_test` | Underground (-0.2 stability, +5 support) or surface (-0.4 global stability, -0.6 adjacent, -5% own GDP, +5 support). Success: 70% below T2, 95% at T2+. Requires 3-way authorization (HoS + military chief + moderator). |
| `nuclear_launch_initiate` | Begin nuclear launch chain. 4-phase: initiate → authorize → intercept → resolve. 3-way authorization required. |
| `nuclear_authorize` / `nuclear_intercept` | Steps in the nuclear chain. Allowed even when simulation is paused. |

#### Economic (6 actions)

| Action | What it does |
|--------|-------------|
| `set_budget` | Allocate: social spending (0.5–1.5× baseline), military production coins, tech R&D coins. Cutting social spending damages stability and support. Deficit → money printing → inflation. |
| `set_tariffs` | Set tariff level (0–3) against a specific country. Hurts both sides. |
| `set_sanctions` | Set sanction level (-3 to +3) against a specific country. |
| `set_opec` | Set production level (min/low/normal/high/max). Affects global oil price. OPEC members only. |
| `propose_transaction` | Propose bilateral asset exchange (coins, units, tech, basing). |
| `accept_transaction` | Accept, decline, or counter a proposed transaction. |

*Budget, tariffs, sanctions, and OPEC are submitted during Phase A but processed in batch during Phase B by the economic engine.*

#### Diplomatic (5+ actions)

| Action | What it does |
|--------|-------------|
| `public_statement` | Attributed public text visible to all. Signaling, threats, reassurance. |
| `declare_war` | Sets bilateral relationship to at_war in both directions. |
| `propose_agreement` | Propose a formal treaty. |
| `sign_agreement` | Countersign a proposed agreement to activate it. |
| `call_org_meeting` | Convene an organization meeting with an agenda. |

*Meeting invitations are handled through the meeting system (see Section 6), not as standard actions.*

#### Covert (2 actions)

| Action | What it does |
|--------|-------------|
| `covert_operation` | Execute covert op. Subtypes: espionage (60%), sabotage (45%, 2% GDP damage), cyber (50%, 1% GDP), disinformation (55%, -0.3 stability / -3 support), election_meddling (40%, -2 to -5% support). Cards consumed permanently. AI level adds +5% per level. Repeated ops vs same target: -5% success, +10% detection. |
| `intelligence` | AI-generated analytical report on a target. NOT a covert card operation — does not consume cards. Returns data with 85% accuracy on success, 45% on failure (you don't know which). |

#### Political (6 actions)

| Action | What it does |
|--------|-------------|
| `arrest` | Head of state arrests a team member. Requires moderator confirmation. |
| `assassination` | 1 card per role per game. Domestic 60% / international 20% base (Levantia +30%, Sarmatia +10%). On hit: 50% kill (martyr +15 support), 50% survive-injured (+10 support). Requires moderator confirmation. |
| `change_leader` | Initiate leadership change. Requires low stability, non-HoS initiator, 3+ team. Three-phase voting. |
| `reassign_types` | Head of state reassigns military/economic/foreign affairs control to a different role. |
| `self_nominate` | Self-nominate for an upcoming election. |
| `cast_vote` | Cast a secret ballot in an election. |

#### Reactive / System Actions

These are triggered by game events, not directly initiated by players:

| Action | Trigger |
|--------|---------|
| `release_arrest` | Moderator releases an arrested role |
| `respond_meeting` | Respond to a meeting invitation |
| `withdraw_nomination` | Withdraw from an election |
| `cast_election_vote` | Cast vote in election (variant routing) |
| `resolve_election` | Moderator resolves election results |

### Moderator Approval Queue

Some actions require moderator confirmation before execution: assassination, arrest, change_leader, and optionally combat (when dice mode is on). These enter the `pending_actions` queue. Auto-approve mode bypasses this for testing.

---

## 6. COMMUNICATION

### Bilateral Meetings

The primary diplomatic tool. Private conversations between leaders.

**For human participants:** Unrestricted. Any format, any number, face-to-face or digital. No technical limits imposed.

**For AI participants:** 1-on-1 bilateral meetings through the meeting system:
1. **Invite** — leader sends invitation with agenda (max 2 active invitations, 10-minute expiry)
2. **Accept/Decline** — counterpart responds
3. **Active meeting** — text-based conversation (max 16 turns)
4. **End** — either participant can end

*Multilateral AI meetings planned for future.*

### Public Statements

Attributed text visible to all participants and on the public screen.

### Proposals

Transactions and agreements create proposals requiring counterpart response. Transactions allow counter-offers; agreements require accept or decline.

---

## 7. ROUND LIFECYCLE

### Two Phases

**Phase A — Active Round** (timed, configurable per template):
- All actions available to participants
- Free communication and negotiation
- Immediate actions execute on submission (combat, covert, diplomacy, transactions)
- Batch decisions (budget, tariffs, sanctions, OPEC) submitted but queued for Phase B
- AI participants triggered multiple times during Phase A
- AI explicitly prompted to submit batch decisions near end of round
- Moderator monitors, approves pending actions, can pause/extend

**Phase B — Processing & Movement** (~10 minutes):
- Economic engine runs: oil → GDP → revenue → budget → production → tech → inflation → debt → crisis state → momentum → contagion → market indexes
- Political engine runs: stability, elections (if scheduled), war tiredness
- Results written to per-round snapshot tables
- Unit movement (`move_units`) allowed during this phase — military repositioning
- Moderator reviews results, can adjust before publishing
- Results published → all participants see updated world → next round's Phase A begins

### Moderator Controls

- Start / pause / resume / end / abort / restart the simulation
- Advance phases, extend time
- Toggle auto-approve (skip confirmation queue)
- Toggle auto-attack (immediate combat resolution vs. dice queue)
- Toggle dice mode (physical dice vs. computed)
- Approve/reject pending actions
- Override any decision

### Key Events

Templates define scheduled events that create dramatic structure (elections, crises, votes). These are template data — the World Model supports any schedule configuration.

---

## 8. ECONOMY

### GDP Model

Additive factor model with crisis multiplier. Processing is chained (not parallel):

**Growth formula:** `base_growth + cyclical_factors × crisis_modifier`

Where base growth is protected from shocks, and cyclical factors include:
- Tariff drag (bilateral, prisoner's dilemma model)
- Sanctions impact (S-curve: sector-weighted max damage × effectiveness curve)
- Oil shock (importers hurt by high prices, producers benefit)
- Semiconductor disruption (Formosa dependency × severity, escalates over rounds)
- War damage (occupied zones + infrastructure damage)
- AI technology boost (L2: +0.3%, L3: +1.0%, L4: +2.5%)
- Blockade impact (chokepoint-specific oil and trade disruption)
- Bilateral trade drag (if major trade partner is contracting)

Crisis states amplify negative shocks: normal (1.0×), stressed (1.2×), crisis (1.3×), collapse (2.0×).

### Crisis States

Four-state ladder: `normal` → `stressed` → `crisis` → `collapse`

**Downward (fast):** 2+ stress triggers → stressed. 2+ crisis triggers → crisis. 3+ rounds in crisis with triggers still active → collapse.

**Upward (slow):** 0 triggers for 2-3 consecutive rounds needed to recover one level.

**Stress triggers:** Oil >$150 (importers), inflation >baseline+15, GDP growth <-1%, empty treasury, stability <4, Formosa disruption with high dependency.

**Crisis triggers:** Oil >$200, inflation >baseline+30, GDP growth <-3%, empty treasury AND high debt, prolonged Formosa disruption.

### Budget

Revenue = GDP × tax_rate + oil_revenue - debt_service - inflation_erosion - war_damage - sanctions_costs.

Spending: maintenance (mandatory) + social + military production + R&D. Deficit → draw from treasury → if insufficient, print money → inflation spiral (60× multiplier) → debt accumulation.

Social spending effects: cutting hurts stability (4× multiplier) and support (6× multiplier). Increasing boosts both.

### Oil Price

Driven by supply/demand model:
- **Supply:** OPEC production decisions, sanctions on producers, blockades at Gulf chokepoints
- **Demand:** Economic health of major economies, demand destruction after prolonged high prices
- **War premium:** +5% per war involving Gulf countries (cap +15%)
- **Formula:** `base_price × (demand/supply)^2.5 × (1 + war_premium)`, with inertia (70% new, 30% previous) and soft cap above $200

### Market Indexes

Three regional indexes (Wall Street, Europa, Dragon), range 0–200, baseline 100. Each is a weighted average of component country "health scores." Countries whose primary index falls below 70 suffer stability penalty (-0.10); below 40 = crisis penalty (-0.30).

---

## 9. MILITARY

### Map

- **Global map:** 10×20 hex grid, 1-indexed, (row, col) convention, pointy-top hexes
- **Theater maps:** 10×10 hex grids for zoomed-in areas
- **Sea hexes:** Defined in map_config (111 global sea hexes)
- **Chokepoints:** Template-defined strategic locations (e.g., 3 in canonical template)

### Territory

Ground forces capture territory on advance. `hex_control` table tracks: owner, controlled_by, captured_round. Non-ground enemy units at captured hex become trophies (flipped to attacker's reserve). Must leave 1 ground unit behind on foreign occupied hexes.

### Nuclear

Three-tier capability (Level 0–3). R&D investment progresses toward each level:
- L0→L1: threshold 0.60 progress
- L1→L2: threshold 0.80
- L2→L3: threshold 1.00

Nuclear launch is a multi-step chain: **Initiate → Authorize (3-way) → Alert + Intercept attempts → Resolve.**

Nuclear strike damage: 50% of all military units on target hex destroyed, 30% of target GDP destroyed (divided by number of target hexes). T3 salvo (3+ missiles): -1.5 global stability, -2.5 target stability, 1/6 chance of target leader death.

---

## 10. POLITICS

### Stability

Range **1.0 to 9.0**. Driven by:
- GDP growth (positive above 2%, negative below -2%)
- Social spending decisions (up to ±2.0 impact)
- War (frontline defender -0.10/round, primary belligerent -0.08, other -0.05)
- Casualties and territory lost/gained
- War tiredness friction
- Sanctions friction (-0.1 per level)
- Inflation friction (above 3pp delta: -0.05/pp, above 20pp: additional -0.03/pp)
- Crisis state penalty (stressed -0.10, crisis -0.30, collapse -0.50)
- Market stress (from regional indexes)

Autocracies have 75% resilience (negative deltas reduced). Peaceful non-sanctioned countries have 50% dampening on negative changes.

### Elections

Template-scheduled events. Two voting components:
- **AI score** (50%): based on GDP growth, stability, war status, crisis state, arrests, agreements, territory
- **Player vote** (50%): actual votes from team members
- Incumbent wins at ≥50 combined score

### War Tiredness

Accumulates per round while at war: defenders +0.20, attackers +0.15, allies +0.10. Halves after 3+ rounds (society adaptation). Cap: 10.0. Peacetime decay: -20% per round.

### Leadership Change

Non-electoral path: if stability falls below threshold, non-HoS roles with 3+ team can initiate removal vote → if successful, election for replacement. Three-phase process.

### Capitulation

Triggered when a country has been in economic crisis state for 3+ consecutive rounds.

### Covert Operations

Cards-based system. Success rates per type (see Section 5). Detection and attribution are separate probabilistic rolls. AI level adds +5% success per level. Repeated operations against the same target suffer -5% success and +10% detection per prior op.

---

## 11. TECHNOLOGY

### R&D Tracks

| Track | Levels | Progression Thresholds | Effects |
|-------|--------|----------------------|---------|
| **Nuclear** | 0→1→2→3 | 0.60 / 0.80 / 1.00 | Unlocks nuclear test, then launch. Missile range increases: T1=2 hex, T2=4 hex, T3=global. |
| **AI** | 0→1→2→3→4 | 0.20 / 0.40 / 0.60 / 1.00 | +5% covert ops per level. L2: +0.3% GDP. L3: +1.0% GDP, +1 combat die. L4: +2.5% GDP, +2 combat dice (50% chance). |

**R&D formula:** `progress += (investment / GDP) × 0.8 × rare_earth_factor`

**Rare earth restrictions:** Each level reduces R&D efficiency by 15% (floor 40%).

**Technology transfer:** Via transactions. Nuclear: +0.20 progress to recipient. AI: +0.15 progress. Donor must be ≥1 level ahead. Does not directly level up — adds to progress.

---

## APPENDIX: Known Spec-Code Divergences

These were discovered during verification and need resolution:

| Issue | Spec Says | Code Does | Resolution Needed |
|-------|-----------|-----------|-------------------|
| ground_move leave-1-behind | Must leave 1 unit behind | Does not enforce | Add enforcement for foreign occupied hexes |
| Phase count | 2 phases (design intent) | 3 states in code (A, B, inter_round) | Align code terminology or document inter_round as Phase B sub-step |
| Legacy v1 vs v2 combat | v2 is canonical | Both exist in military.py | Remove or clearly deprecate v1 functions |

---

*Version 2.0 DRAFT — Built from verified engine code (economic.py 2191 lines, military.py 3076 lines, political.py, technology.py), DB schema audit (54 tables), module SPECs (M4, M6, M9), and MODULE_REGISTRY. All constants verified with line numbers. Template-specific data removed — only world rules remain.*
