# TTT WORLD MODEL — The Simulation Specification

**Version:** 1.0 DRAFT | **Date:** 2026-04-22
**Status:** UNDER REVIEW — Marat must validate before this becomes canonical
**Purpose:** Single source of truth for what the TTT simulation IS — its entities, rules, actions, and lifecycle.
**Audience:** Developers, AI agents, facilitators, and the product owner.

---

## 1. THE SIMULATION

### Purpose

The Thucydides Trap (TTT) is an immersive leadership simulation that places 25-39 human participants and AI-operated countries into a fictional-but-recognizable geopolitical crisis modeled on the real US-China power transition.

**The central question is not "will there be war."** It is: what happens to the entire global order when the power that built it can no longer sustain it alone — and the power rising to challenge it has a fundamentally different vision?

The simulation operates the Thucydides Trap at three layers simultaneously:
- **Structural:** The visible power balance is shifting. Neither side has decisive advantage.
- **Situational:** Five simultaneous crises create a "too many fires" problem that overwhelms the system's capacity to respond.
- **Personal:** Leaders face the intersection of national interest and personal survival. The structural clock says patience; the personal clock says act now.

### What Participants Experience

Each round (representing ~6 months of real time), participants:
1. **Negotiate freely** — face-to-face, in bilateral meetings, through back-channels
2. **Take actions** — military, economic, diplomatic, covert, political — processed by live engines
3. **Receive consequences** — updated world state: economic indicators, stability shifts, military positions, events
4. **Adapt** — new intelligence, new crises, new opportunities emerging from prior decisions

### Key Design Principles

- **Communication is primary.** The simulation is primarily about negotiation, persuasion, deal-making, and relationship management. Actions are tools; conversations are strategy.
- **Fictional names, real dynamics.** Country names are fictional (Columbia, Cathay, Sarmatia...) with transparent real-world parallels — close enough for recognition, distant enough for freedom.
- **Both war and peace are plausible.** The simulation does not assume any outcome. Participant choices determine the result.

---

## 2. TEMPLATE, SCENARIO, AND SIM RUN

The simulation system has a three-level configuration hierarchy:

```
TEMPLATE (master SIM design — evolves over months)
  └── SCENARIO (configured for a specific event — limited customization)
        └── SIM RUN (one execution — state is mutable during play)
```

### Template

The template defines the complete world design:
- All 21 countries with their starting economic, political, military, and technological state
- All 40 roles with character names, titles, objectives, powers, covert cards
- All organizations and their memberships, decision rules, voting thresholds
- Starting relationships between all countries (alliances, tensions, wars)
- Starting sanctions and tariffs
- Starting military deployments (345 units across 68 hex positions)
- Map configuration, theater linkage, zone definitions
- Formula coefficients for all engines (economic, military, political, technology)
- Default schedule (round count, phase durations)
- Key events (elections, scheduled crises)

**The canonical template (v1.0)** models the world of H2 2026, with the US-China power transition as the structural backdrop and five active crises.

### Scenario

A scenario inherits everything from a template and allows limited overrides:
- Starting date, max rounds, oil price
- Active theaters and organizations
- Phase A duration
- Country stat overrides, relationship overrides
- Role briefing and persona overrides
- Scripted events and election schedule
- Unit layout selection

### Sim Run

A sim run is one execution of a scenario. Once created, the sim run copies all template/scenario data into its own tables — countries, roles, deployments, relationships, sanctions, tariffs, zones, organizations, memberships, artefacts. From that point, the sim run's data is independent and mutable during play.

**Sim run states:** `setup` → `pre_start` → `active` → `processing` → `inter_round` → `active` (next round) → ... → `completed`

---

## 3. ENTITIES

### Countries (21)

Each country has:

| Category | Key Fields |
|----------|-----------|
| **Identity** | sim_name, parallel (real-world equivalent), country_brief |
| **Team** | regime_type, team_size, whether AI-operated by default |
| **Economy** | GDP, GDP growth rate, treasury, inflation, trade balance, tax rate, debt burden, debt ratio |
| **Sectors** | resources, industry, services, technology (relative weights) |
| **Oil** | oil_producer flag, OPEC member flag, production level |
| **Military** | counts by type (ground, naval, tactical_air, strategic_missiles, air_defense) |
| **Production** | per-unit costs, production capacity, maintenance cost per unit |
| **Political** | stability (0-1), war_tiredness, martial_law flag |
| **Technology** | nuclear_level (0-3), nuclear R&D progress, AI level (0-5), AI R&D progress |

**Team countries** (multiple human players): Columbia (USA), Cathay (China), Gallia (France), Teutonia (Germany), Freeland (Poland), Ponte (Italy), Albion (UK), Sarmatia (Russia), Ruthenia (Ukraine), Persia (Iran).

**Solo countries** (1 human or AI each): Bharata (India), Levantia (Israel), Formosa (Taiwan), Phrygia (Turkey), Yamato (Japan), Solaria (Saudi Arabia), Choson (N. Korea), Hanguk (S. Korea), Caribe (Cuba+Venezuela), Mirage (UAE).

**Special:** Neustadt (Switzerland) — observer/mediator role.

### Roles (40)

Each role represents one participant character:

| Category | Key Fields |
|----------|-----------|
| **Identity** | character_name, title, country_code |
| **Position** | position_type (head_of_state, minister, general, diplomat, special), positions array |
| **Flags** | is_head_of_state, is_military_chief, is_diplomat, is_economy_officer |
| **Capabilities** | powers (array of special abilities), objectives (personal goals) |
| **Covert cards** | intelligence, sabotage, cyber, disinformation, election_meddling, assassination, protest_stimulation (integer counts, consumed on use) |
| **Content** | public_bio, confidential_brief (asymmetric — only this player sees it) |
| **Status** | active, arrested, killed |

**Positions determine permissions.** Head of state has broadest powers. Ministers/generals have domain-specific actions. The `role_actions` table lists exactly which actions each role can perform.

### Military Forces

**Individual unit model:** Each unit is one row in the `deployments` table. 345 units at template start.

| Unit Type | Purpose |
|-----------|---------|
| `ground` | Land combat, territory control. RISK dice. |
| `naval` | Sea combat, bombardment, blockade support. |
| `tactical_air` | Air strikes (2-hex range), air defense counter. |
| `strategic_missile` | Long-range strike (range by nuclear tier). Consumed on firing. |
| `air_defense` | Intercepts missiles (50% per AD unit), reduces air strike effectiveness. |

Units have: `unit_id`, `country_code`, `unit_type`, position (`global_row/col` + `theater/row/col`), `unit_status` (active/reserve/destroyed/captured), `embarked_on` (carrier unit for transport).

### Organizations (8+)

International bodies with distinct decision rules:

| Organization | Parallel | Decision Rule | Special |
|-------------|----------|---------------|---------|
| UNSC | UN Security Council | P5 veto | 5 permanent members with veto power |
| NATO+ | NATO | Consensus | Any member can block |
| EU | European Union | Unanimity | Any member can block |
| BRICS+ | BRICS | Consensus | Looser coordination |
| OPEC | OPEC | Consensus | Controls oil production |
| G7 | G7 | Consensus | Major economies |
| Columbia Parliament | US Congress | Majority | Contested swing seat |
| SCO | SCO | Consensus | Security cooperation |

Organizations can hold meetings, pass resolutions, and coordinate actions. Players may propose creating new organizations.

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
- Positive levels = sanctions imposed (S-curve damage model: coverage below 0.3 = minimal, above 0.7 = severe)
- Negative levels = evasion support (helping target country circumvent others' sanctions)
- Sanctions hurt the imposer too (secondary effects on trade)

### Tariffs

Per-country bilateral. Levels 0 to 3:
- Each level increases trade costs for BOTH sides (target suffers more)
- Direct drag on GDP growth

### Agreements

Formal treaties between countries:
- Types: security, trade, basing, technology_sharing, ceasefire, general
- Require countersignature (proposer signs, counterpart must sign to activate)
- Can be public or secret
- Multiple signatories possible

### Transactions

Bilateral asset exchanges:
- One country offers: coins, units, technology, basing rights
- Other country provides: coins, units, technology, basing rights
- Counterpart can accept, decline, or counter-offer
- Can be public or secret

---

## 5. ACTIONS

### The Canonical Action Catalog

**Source of truth:** `MODULES/MODULE_REGISTRY.md`, ACTION_NAMING section.

Every action has: a canonical name, required fields, an engine that processes it, and defined effects.

#### Military (13 actions)

| Action | What it does |
|--------|-------------|
| `ground_attack` | RISK dice combat at adjacent hex. Attacker rolls min(3, alive), defender min(2, alive). Modifiers: AI L4, morale, amphibious, air support. |
| `air_strike` | Per-unit independent rolls. 12% hit (6% if target has air defense). 2-hex range. |
| `naval_combat` | RISK dice at sea. 1v1 paired combat. |
| `naval_bombardment` | Sea → adjacent land. 10% hit per naval unit. |
| `naval_blockade` | Establish/lift blockade at 3 chokepoints (Caribe Passage, Gulf Gate, Formosa Strait). Requires forces at the chokepoint. |
| `launch_missile_conventional` | Two-phase: AD interception (50% per AD unit), then hit roll (75% flat). 4 target types. Range by nuclear tier. Missile consumed. |
| `move_units` | Ground advance to adjacent land hex. Leave 1 behind. Max 3 per move. Processed during Phase B. |
| `basing_rights` | Grant or revoke foreign military access to your territory. |
| `martial_law` | Emergency powers. One-time per country per simulation. 4 eligible countries. |
| `nuclear_test` | Underground or overground. Stability impact. Requires 3-way authorization (HoS + military chief + moderator). |
| `nuclear_launch_initiate` | Begin nuclear launch sequence. 3-way authorization required. |
| `nuclear_authorize` | Co-authorize a nuclear launch (step 2 of the chain). |
| `nuclear_intercept` | Attempt to intercept incoming nuclear strike. |

#### Economic (6 actions)

| Action | What it does |
|--------|-------------|
| `set_budget` | Allocate resources: social spending (0.5-1.5x baseline), military production coins, tech R&D coins. Cutting social spending damages stability. |
| `set_tariffs` | Set tariff level (0-3) against a specific country. Hurts both sides. |
| `set_sanctions` | Set sanction level (-3 to +3) against a specific country. S-curve damage model. |
| `set_opec` | Set OPEC production level (min/low/normal/high/max). Affects global oil price. OPEC members only. |
| `propose_transaction` | Offer bilateral asset exchange (coins, units, tech, basing). |
| `accept_transaction` | Accept, decline, or counter a proposed transaction. |

*Note: Budget, tariffs, sanctions, and OPEC are submitted during Phase A but processed in batch during Phase B by the economic engine.*

#### Diplomatic (6 actions)

| Action | What it does |
|--------|-------------|
| `public_statement` | Attributed public text visible to all. Signaling, threats, reassurance. |
| `declare_war` | Sets bilateral relationship to at_war in both directions. |
| `propose_agreement` | Propose a formal treaty (security, trade, basing, tech sharing, ceasefire). |
| `sign_agreement` | Countersign a proposed agreement to activate it. |
| `call_org_meeting` | Convene an organization meeting with an agenda. |
| `invite_to_meet` | Invite another leader to a bilateral meeting. |

#### Covert (2 actions)

| Action | What it does |
|--------|-------------|
| `covert_operation` | Execute covert op: intelligence (60% success), sabotage (45%), cyber (50%), disinformation (55%), election_meddling (40%). Cards consumed. AI level adds +5% per level. Repeated ops vs same target: -5% success, +10% detection each time. |
| `intelligence` | Dedicated intelligence gathering operation. |

#### Political (6 actions)

| Action | What it does |
|--------|-------------|
| `arrest` | Head of state arrests a team member. Requires moderator confirmation. |
| `assassination` | 1 card per role per game. Domestic 60% / international 20% success. Requires moderator confirmation. |
| `change_leader` | Initiate leadership change. Requires low stability, non-HoS initiator, 3+ team. Three-phase voting process. |
| `reassign_types` | Head of state reassigns military/economic/foreign affairs control to different role. |
| `self_nominate` | Self-nominate for an upcoming election. |
| `cast_vote` | Cast a secret ballot in an election. |

---

## 6. COMMUNICATION

### Bilateral Meetings

The primary diplomatic tool. Private 1-on-1 conversations between leaders.

**For human participants:** Unrestricted. Any format, any number of participants, face-to-face or digital. The simulation does not impose technical limits on human communication.

**For AI participants (current implementation):** 1-on-1 bilateral meetings through the meeting system. Meeting lifecycle:
1. **Invite** — one leader sends invitation with agenda (max 2 active invitations per role, 10-minute expiry)
2. **Accept/Decline** — counterpart responds
3. **Active meeting** — text-based conversation (max 16 turns per meeting)
4. **End** — either participant can end the meeting

*Multilateral AI meetings are planned for future implementation.*

### Public Statements

Attributed text visible to all participants and on the public screen. Used for signaling, threats, reassurance, propaganda.

### Proposals

Transactions and agreements create proposals that require counterpart response. The counterpart can accept, decline, or counter-offer (transactions only).

---

## 7. ROUND LIFECYCLE

### Two Phases

```
PHASE A (Active Round)                    PHASE B (Engine Processing + Movement)
├── All actions available                 ├── Economic engine runs (batched decisions)
├── Free communication                    ├── Political engine runs
├── Negotiations, deals, attacks          ├── Movement orders processed
├── Timed (80 min Round 1, 60 min after)  ├── World state updated
└── Moderator ends Phase A               └── Auto-advances to next round's Phase A
```

**Phase A** — The active play phase. All 33 actions are available. Human participants negotiate freely. AI participants observe, reason, communicate, and act. Four economic policy actions (budget, tariffs, sanctions, OPEC) are submitted during Phase A but queued for Phase B processing. All other actions execute immediately.

**Phase B** — Engine processing. No player actions accepted. The economic engine processes all batched decisions in sequence: oil price → GDP → revenue → budget → inflation → debt → crisis state → stability → war tiredness. Movement orders (`move_units`) are also processed during this phase. Phase B is automatic — moderator triggers it by ending Phase A, and it auto-completes.

### Key Scheduled Events

The template defines scheduled events that create dramatic structure:
- **Round 2:** Columbia mid-term elections (contested parliamentary seat)
- **Round 3-4:** Ruthenia wartime election, UNGA vote forcing public alliance declarations
- **Round 5:** Columbia presidential election — the climactic event

### Moderator Controls

The facilitator (moderator) has controls to:
- Start/pause/resume/end/abort the simulation
- Advance phases, extend time, revert to Phase A
- Toggle auto-approve (skip confirmation queue for actions)
- Toggle auto-attack (immediate combat resolution vs. dice queue)
- Toggle dice mode (physical dice vs. computed)
- Approve/reject pending actions (arrests, assassinations, nuclear launches)
- Restart simulation (full reset to initial state)

---

## 8. ECONOMY

### GDP Model

Additive factor model — GDP growth is the sum of:
- Base growth rate (country-specific)
- Tariff drag (bilateral, hurts both sides)
- Sanctions impact (S-curve: low coverage = minimal, high coverage = severe)
- Oil shock (price deviation from baseline affects oil-dependent economies)
- War damage (direct GDP destruction from combat)
- AI technology boost (higher AI level = growth bonus)
- Momentum (confidence variable, mean-reverting)
- Crisis multiplier (amplifies damage in crisis states)

### Crisis States

Four-state ladder: `normal` → `stressed` → `crisis` → `collapse`

Each state amplifies economic damage and hurts political stability. Transitions driven by GDP contraction, inflation, debt accumulation.

### Budget

Revenue is derived from GDP. Mandatory costs (debt service, maintenance) are subtracted. Remaining is discretionary:
- **Social spending** (0.5-1.5× baseline) — cutting hurts stability and support; increasing boosts both
- **Military production** (coins → new units)
- **Technology R&D** (coins → progress on nuclear/AI tracks)
- Deficit → money printing → inflation spiral

### Oil

Global oil price is determined by OPEC production decisions + blockade effects + demand destruction. Oil price affects all economies — oil producers benefit from high prices, oil consumers suffer.

---

## 9. MILITARY

### Map

**Global map:** 10×20 hex grid (200 hexes). Land and sea hexes.
**Theater maps:** 10×10 hex grids for zoomed-in combat areas.
**Coordinate convention:** (row, col), row first, 1-indexed.

### Combat Types

| Type | Mechanic | Range |
|------|----------|-------|
| Ground | RISK dice (attacker up to 3, defender up to 2, paired highest-to-highest, ties→defender) | Adjacent hex |
| Air strike | Independent rolls per unit, 12% hit (6% if AD present) | 2-hex range |
| Naval | RISK dice at sea | Same hex |
| Naval bombardment | 10% hit per naval unit, sea→adjacent land | Adjacent hex |
| Missile | Two-phase: AD intercept (50%/unit) then hit (75% flat) | Range by tier |

**Modifiers:** AI Level 4 (+1 die), low morale, amphibious penalty, die-hard defense, air support.

### Territory

When ground forces advance into a hex, they capture it. Non-ground enemy units at the captured hex become trophies (captured to reserve). Territory control tracked in `hex_control` table. Must leave 1 unit behind when advancing.

### Nuclear

Three-tier nuclear capability (Level 0-3). R&D investment progresses toward each level.
Nuclear launch is a multi-step chain: Initiate → Authorize (3-way: HoS + military chief + moderator) → Intercept attempt → Resolve.

---

## 10. POLITICS

### Stability

Range 0-1. Affected by:
- Social spending decisions
- War tiredness (increases with ongoing wars)
- Economic crisis
- Martial law (emergency boost, one-time)
- Covert disinformation operations
- Election outcomes

### Elections

Template-scheduled events. Types:
- **Columbia mid-terms** (Round 2) — contested parliamentary seat
- **Ruthenia wartime election** (Round 3-4) — AI-judged based on actual SIM events
- **Columbia presidential election** (Round 5) — weighted votes from team members + 50% AI-generated popular vote

Election process: nominations open → candidates self-nominate → voting period → results.

### Leadership Change

Non-electoral path: if stability falls below threshold, non-HoS roles with 3+ team can initiate removal vote → if successful, election for replacement.

### Covert Operations

Cards-based system. Each role starts with a fixed number of covert cards by type. Cards are consumed permanently when used. Success rates depend on operation type and AI technology level. Detection and attribution are probabilistic.

---

## 11. TECHNOLOGY

### R&D Tracks

Two technology tracks with progression:

| Track | Levels | Effect |
|-------|--------|--------|
| **Nuclear** | 0 → 1 → 2 → 3 | Unlocks nuclear test, then launch capability. Missile range increases with level. |
| **AI** | 0 → 1 → 2 → 3 → 4 → 5 | +5% covert ops success per level. L4: +1 combat die. GDP growth bonus. |

Progress is driven by R&D coin investment each round. Technology can be shared via transactions (technology transfer).

---

## APPENDIX: Reactive and System Actions

Beyond the 33 player-initiated actions, the system has reactive actions that are triggered by game events:

| Action | Trigger |
|--------|---------|
| `release_arrest` | Moderator releases an arrested role |
| `respond_meeting` | Respond to a meeting invitation |
| `withdraw_nomination` | Withdraw from an election |
| `cast_election_vote` | Cast vote in election (variant of cast_vote) |
| `resolve_election` | Moderator resolves election results |
| `ground_move` | Unit repositioning (processed during Phase B) |

These are handled by the action dispatcher but are not player-initiated actions in the traditional sense.

---

*Version 1.0 DRAFT — Requires Marat validation. Built from audit of actual DB schema (54 tables), action dispatcher code, and MODULE_REGISTRY. Design heritage (CONCEPT, SEED, DET) referenced for purpose and intent.*
