# TTT Game Rules Reference

**The Thucydides Trap** -- a geopolitical leadership simulation where participants control countries on the brink of a power transition between an established superpower (Columbia/United States) and a rising challenger (Cathay/China). The simulation runs 6-8 rounds, each representing approximately 6 months of scenario time. Every decision cascades across economic, military, political, and technological domains.

**Source authority:** This document reflects live code as of 2026-04-21. All facts are verified against `action_schemas.py`, engine files, `roles.csv`, `countries.csv`, `map_config.py`, `action_dispatcher.py`, and `SPEC_M4_SIM_RUNNER.md`.

---

## 1. THE WORLD

### Countries (20)

The simulation contains 20 countries, each with a real-world parallel. They are organized into teams and solo players.

**Team countries** (multiple human roles per country):

| Country | Parallel | Regime | Team Size | Notes |
|---------|----------|--------|-----------|-------|
| Columbia | United States | Democracy | 7-9 | Superpower. At war with Persia. GDP 280. |
| Cathay | China | Autocracy | 5 | Rising power. GDP 190. Formosa ambitions. |
| Sarmatia | Russia | Autocracy | 3-4 | At war with Ruthenia. GDP 20. Oil producer (OPEC). |
| Ruthenia | Ukraine | Democracy | 3 | At war with Sarmatia. GDP 2.2. Frontline defender. |
| Persia | Iran | Hybrid | 3 | At war with Columbia and Levantia. GDP 5. Nuclear aspirant (70% progress). |

**European bloc** (team_type=europe, 1 player each except Gallia which has 2 roles):

| Country | Parallel | Notes |
|---------|----------|-------|
| Gallia | France | UNSC veto. Nuclear power (L2). Strategic autonomy. 2 roles. |
| Teutonia | Germany | Largest EU economy (GDP 45). Cathay trade dependency. |
| Freeland | Poland | NATO frontline. 4.8% GDP defense spending. |
| Ponte | Italy | EU swing vote. 137.9% debt-to-GDP. |
| Albion | United Kingdom | NATO but not EU. UNSC veto. Nuclear power (L2). Five Eyes. |

**Solo countries** (1 player each, default AI-operated):

| Country | Parallel | Key Feature |
|---------|----------|-------------|
| Bharata | India | Non-aligned. GDP 42. BRICS+ host. Multi-alignment. |
| Levantia | Israel | At war with Persia. Multi-front. Undeclared nuclear (L1). |
| Formosa | Taiwan | Semiconductor shield. Porcupine strategy. Invasion target. |
| Phrygia | Turkey | NATO member. Bosphorus control. Hedges everyone. |
| Yamato | Japan | Remilitarizing. GDP 43. Latent nuclear capability. |
| Solaria | Saudi Arabia | Oil giant (OPEC). Under Persia missile attack. Vision 2030. |
| Choson | North Korea | Nuclear (L1). Arms dealer. 15K troops in Ruthenia. |
| Hanguk | South Korea | Semiconductor competition. Balance Columbia/Cathay. |
| Caribe | Cuba + Venezuela | Under Columbia blockade. Seeking foreign patrons. |
| Mirage | UAE | Financial hub. Sanctions intermediary. Oil producer (OPEC). |
| Spire (role) | UAE Ruler | (Spire is the role name for Mirage's leader.) |

### Geography

The world map is a **10-row x 20-column hex grid** using pointy-top hexagons with odd-r offset. Coordinates are (row, col), 1-indexed, row first.

Key features:
- **64 land hexes** with canonical ownership, the rest are sea
- **2 theater maps** (10x10 each) for zoomed-in conflict zones: **Eastern Ereb** (Sarmatia-Ruthenia front) and **Mashriq** (Middle East)
- Theater hexes link back to specific global hexes for strategic-level resolution
- **3 chokepoints** that can be blockaded: Caribe Passage (8,4), Gulf Gate (8,12), Formosa Strait (7,17)
- **Nuclear sites** on the map: Persia (7,13), Choson (3,18)

### Unit Types

Five military unit types, each individually tracked (1 row per unit in the database):

| Unit Type | Attack Range | Role |
|-----------|-------------|------|
| Ground | 1 hex (adjacent) | Territory control, blockades, occupation |
| Tactical Air | 2 hexes | Air strikes. 12% hit rate (6% if AD present). Can be downed by AD. |
| Naval | 1 hex (sea) | Sea control, bombardment of adjacent land |
| Strategic Missile | 2-99 hexes (tier-dependent) | Long-range strikes. Consumed on firing. |
| Air Defense | Covers hex + linked theater hexes | Halves air strike effectiveness, intercepts missiles |

Unit statuses: active, reserve, embarked, destroyed.

**Missile range tiers** (based on country nuclear_level):
- T1 (level 0-1): 2 hexes
- T2 (level 2): 4 hexes
- T3 (level 3+): global (99 hexes)

### Rounds and Phases

A simulation runs **6-8 rounds**. Each round has a clear phase structure:

**Phase A: Active Round** (timed, typically 60-80 minutes)
- Free gameplay: discussions, meetings, action submissions
- All actions except unit movement and batch decisions are processed immediately
- Batch decisions (budget, tariffs, sanctions, OPEC production) are submitted during Phase A but queued for Phase B processing
- AI participants are triggered 3 times: phase start, midpoint, and near-end (for regular decision submission)
- Moderator monitors, approves sensitive actions, can pause/extend

**Phase B: Engine Processing** (automated, 5-12 minutes)
- Economic engine runs its full chain (oil price, GDP, revenue, budget, production, tech, inflation, debt, crisis states, momentum, contagion, sanctions, tariffs, dollar credibility), then political engine (stability, elections if scheduled, health events). Results are written, reviewed by moderator, and published.
- Phase B runs FIRST, before the inter-round movement window opens.

**Inter-Round: Unit Movement** (timed, 5-10 minutes, AFTER Phase B completes)
- Military commanders and heads of state reposition forces. Map updates in real-time. Timer-based, moderator can extend.
- Movement happens AFTER the engine tick, so units move based on updated game state.

**Round End:** Inter-round closes, round counter advances, key events for new round triggered, Phase A of next round begins.

---

## 2. ROLES AND POWERS

There are **40 named character roles** across all countries. Each role has a unique character name, specific powers, personal objectives, and a ticking clock that creates urgency.

### Role Types

Roles fall into several categories based on their position within countries:

- **Head of State (is_head_of_state):** Ultimate executive authority. Can authorize attacks, approve nuclear launches, fire team members, sign treaties, set budgets. Examples: Dealer (Columbia), Helmsman (Cathay), Pathfinder (Sarmatia).
- **Military Chief (is_military_chief):** Controls military operations, co-signs orders, can slow-walk commands. Examples: Shield (Columbia SecDef), Rampart (Cathay CMC), Ironhand (Sarmatia General).
- **Diplomats (is_diplomat):** Designated for treaty negotiation and foreign representation. Examples: Anchor (Columbia SecState), Sage (Cathay Elder), Compass (Sarmatia Oligarch), Broker (Ruthenia), Pillar (EU Commissioner), and most solo-country leaders.
- **Intelligence:** Controls covert operations and information flow. Example: Shadow (Columbia CIA Director) with 8 intelligence pool cards.
- **Opposition/Challengers:** Seek to constrain or replace current leadership. Examples: Tribune (Columbia Opposition), Challenger (Columbia Presidential Candidate).
- **Expansion roles:** Optional roles for larger games. Examples: Fixer (Middle East Envoy), Pioneer (Tech Envoy), Ledger (Sarmatia PM).

### Team Countries: Full Rosters

**Columbia (7-9 roles):**
- Dealer (President, age 80, HoS) -- 10% per-round incapacitation risk. Term-limited.
- Volt (Vice President) -- succession candidate, isolationist wing
- Anchor (Secretary of State, diplomat) -- hawkish establishment, Cuba legacy
- Shield (Secretary of Defense, military chief) -- overstretched military, warrior ethos
- Shadow (CIA Director) -- 8 intel cards, 3 sabotage, 3 cyber. Controls information flow.
- Tribune (Opposition Speaker) -- can block budget, launch investigations. Mid-terms Round 2.
- Challenger (Presidential Candidate) -- presidential election Round 5
- Fixer (Middle East Envoy, expansion) -- parallel diplomacy channel
- Pioneer (Tech Envoy, expansion) -- tech tycoon, AI policy

**Cathay (5 roles):**
- Helmsman (Chairman, age 72, HoS + military chief) -- 5-10% incapacitation risk. No successor.
- Rampart (Marshal, military chief) -- co-signature required for military orders. Can slow-walk 1 round.
- Abacus (Premier) -- controls real economic data. Hidden debt crisis ($9-13T). Acting leader if Helmsman incapacitated.
- Circuit (Tech/Industry Minister) -- rare earth weapon. 2 personal coins abroad at risk.
- Sage (Party Elder, diplomat) -- activates when stability < 5 or support < 40%. Party immune system.

**Sarmatia (3-4 roles):**
- Pathfinder (President, age 73, HoS) -- 5-10% incapacitation risk +2%/round. No succession plan.
- Ironhand (General, military chief) -- nuclear co-authorization. Coup potential.
- Compass (Oligarch, diplomat) -- 3 personal coins frozen by Western sanctions. Back-channels.
- Ledger (PM/Technocrat, expansion) -- institutional continuity, real economic data.

**Ruthenia (3 roles):**
- Beacon (President, HoS) -- martial law executive. Corruption scandal.
- Bulwark (General, military chief) -- more popular than president (64-36 runoff). Wartime election candidate.
- Broker (Opposition, diplomat) -- peace negotiation, EU connections.

**Persia (3 roles):**
- Furnace (Supreme Leader, HoS) -- override power costs -5 support -1 stability. Sabotage cards = proxy terrorist attacks.
- Anvil (IRGC Commander, military chief / intelligence) -- IRGC controls 1/3 economy. Can veto military orders 1-round delay. Sabotage cards = proxy attacks. Primary role is military; also has intelligence capabilities.
- Dawn (Reformist) -- represents 60% under-30 population. Activates when stability < 4 or support < 30%.

### Personal Resources

Every role starts with **personal coins** (1-5 depending on role). Some roles have coins frozen abroad (Compass: 3 frozen, Circuit: 2 at risk). Personal coins enable independent deal-making.

Every role starts with a set of **covert operation cards** that are consumed permanently when used:
- Intelligence pool (espionage/intelligence requests)
- Sabotage cards
- Cyber cards
- Disinformation cards
- Election meddling cards
- Assassination cards (1 per eligible role, per game)

Some roles have a **fatherland appeal** flag, enabling nationalist rally effects.

### Parliament Seats

Columbia has a parliament with 5 seats. Mid-term elections in Round 2 can flip control (currently 3-2 for Presidents faction). This affects budget blocking and investigation powers.

---

## 3. ECONOMIC DOMAIN

The economic engine processes in a strict chain -- each step feeds the next.

### Processing Chain (per round, Phase B)

1. **Oil price** (global) -- everything depends on this
2. **GDP growth** per country
3. **Revenue** from GDP
4. **Budget execution** (mandatory costs, deficit, money printing)
5. **Military production** costs and output
6. **Technology R&D** costs
7. **Inflation** update
8. **Debt service** update
9. **Economic state transitions** (crisis ladder)
10. **Momentum** (confidence variable)
11. **Contagion** (crisis spreads to trade partners)
12. **Sanctions** impact
13. **Tariff** impact
14. **Dollar credibility**

### Oil Price

Global oil price starts at $80 base. Driven by supply/demand dynamics:
- OPEC members (4 countries: Mirage, Persia, Sarmatia, Solaria) can set production levels: min (0.7x), low (0.85x), normal (1.0x), high (1.15x), max (1.3x)
- Chokepoint blockades reduce production: Gulf Gate affects Solaria and Mirage (25% partial, 50% full); Caribe Passage affects Caribe
- Demand destruction kicks in after 3 rounds above $100 (4-8% reduction)
- Oil price has soft cap above $200 with diminishing returns
- 30% inertia from previous round price, 70% from formula

### GDP Growth

Additive factor model. Base growth rate (from country data: e.g., Columbia 1.8%, Cathay 4.0%, Bharata 6.5%) is modified by:
- Tariff drag
- Sanctions damage (S-curve model)
- Oil shock (importers hurt by high prices, exporters benefit)
- Semiconductor disruption (Formosa dependency matters)
- War damage
- AI technology boost (L2: +0.5pp, L3: +1.5pp, L4: +3.0pp)
- Momentum (confidence effect)
- Chokepoint blockade disruption
- Bilateral trade dependency drag (e.g., Columbia-Cathay: 15% dependency)

Crisis states multiply the result: normal (1.0x), stressed (0.85x), crisis (0.5x), collapse (0.2x). Negative growth is amplified in crisis: stressed (1.2x), crisis (1.3x), collapse (2.0x).

GDP floor: 0.5 (countries do not reach zero).

### Budget

Each country's budget follows a strict sequence:
- Revenue = GDP x tax rate + oil revenue (if producer) - debt cost - inflation erosion - war damage - sanctions cost
- Mandatory spending = 70% of social baseline (non-negotiable)
- Maintenance = unit count x per-unit cost x 3.0 multiplier
- Discretionary = remaining revenue after mandatory and maintenance
- Players allocate discretionary funds to: social spending (above baseline), military production, R&D, or treasury saving

Social spending has political consequences: spending more than baseline boosts stability and support; cutting below baseline damages both. The effect is linear: 50% cut causes -2 stability delta; 50% increase causes +2.

Military production operates in three tiers:
- Normal: 1x cost, 1x output
- Accelerated: 2x cost, 2x output
- Maximum: 4x cost, 3x output

Standard unit costs: Ground 3 coins, Air Defense 4 coins, Tactical Air 5 coins, Naval 6 coins, Strategic Missile 8 coins.

Deficit spending: countries can draw from treasury. If treasury runs out, money printing occurs, driving inflation (multiplier: 60x the printed amount as inflation points).

### Sanctions (S-Curve Coefficient Model)

Sanctions are directional (country A sanctions country B) with signed levels from -3 to +3. Positive = sanction, negative = evasion support. Coverage is the sum across all sanctioning countries, clamped to [0, 1].

Damage depends on the target's economic sector mix:
- Technology sector: 25% max vulnerability
- Services sector: 25% max vulnerability
- Industry sector: 12.5% max vulnerability
- Resources sector: 5% max vulnerability

The S-curve creates a tipping point around 0.5-0.6 coverage. Below 0.3 coverage, sanctions cause minimal pain. Above 0.7, they bite hard.

Evasion countries (negative sanction levels) can partially cancel sanctions but cannot create positive GDP bonuses.

### Tariffs

Set per bilateral pair. Levels 0-3. Both imposer and target pay costs (trade wars hurt both sides). The target pays more.

### Economic Crisis Ladder

Four states: normal -> stressed -> crisis -> collapse. Transitions are driven by stress triggers (negative GDP growth, high inflation, high debt, war damage). Each state amplifies further damage and imposes stability penalties:
- Stressed: -0.10 stability per round
- Crisis: -0.30 stability per round
- Collapse: -0.50 stability per round

Recovery is possible but slow (requires consecutive positive rounds).

### Contagion

When a major economy (GDP > 30) enters crisis or collapse, trading partners take GDP and momentum hits proportional to bilateral trade weights. This can cascade.

### Market Indexes

Three regional indexes (Wall Street, Europa, Dragon) track weighted baskets of country economic health. When an index drops below 70 it causes stability stress; below 40 causes crisis impact. Each country reads a primary index:
- Wall Street: Columbia (50%), Cathay (15%), Teutonia (10%), Yamato (10%), Albion (10%), Hanguk (5%)
- Europa: Teutonia (30%), Gallia (25%), Freeland (15%), Albion (15%), others
- Dragon: Cathay (50%), Hanguk (15%), Yamato (15%), Bharata (10%), Formosa (10%)

### Dollar Credibility

Tracks the global reserve currency status (starts at 100). Erodes when Columbia prints money (2 points per coin printed). Recovers 1 point per round naturally. Floor: 20, ceiling: 100. Low dollar credibility amplifies global economic instability.

---

## 4. MILITARY DOMAIN

### Combat System

Combat is resolved through **iterative RISK-style dice** for ground engagements and **probability-based rolls** for air and missile strikes.

**Ground Combat:**
- Attacker rolls min(3, attackers_alive) dice, defender rolls min(2, defenders_alive) dice
- Dice sorted descending, modifiers applied to highest die (capped at 6, floored at 1)
- Highest vs highest, second vs second compared -- ties go to defender
- Loop continues until one side has zero units
- Modifiers include: AI level bonus (L4: +1, only if ai_l4_bonus flag set), morale, amphibious penalty, die-hard defense, air support / positional bonus (die-hard and air support do NOT stack -- max of the two applies)
- Moderator can supply physical dice values instead of random rolls

**Air Strikes:**
- Each tactical air unit rolls independently
- Base hit probability: 12% (halved to 6% if target hex has air defense)
- Air defense can down attackers: 15% per shot if AD covers the zone
- Range: 2 hexes from launching position
- Targets prioritize non-AD units; AD units are targeted last

**Naval Combat:**
- RISK dice same as ground combat, fought in sea hexes
- Naval bombardment: ships fire on adjacent land hexes at 10% hit probability per ship

**Missile Strikes:**
- Strategic missiles are consumed on firing (disposable)
- Base hit: 80% (reduced to 30% if AD present in target zone)
- Range depends on missile tier (T1: 2 hexes, T2: 4 hexes, T3: global)
- Conventional and nuclear warhead types

**Territory Occupation:**
- Ground attack victory allows capture of the hex (recorded in hex_control table)
- Non-ground, non-naval enemy units on captured hex become trophies (flipped to attacker's reserve)
- Attacker must leave at least 1 unit behind on captured hex
- Occupied hexes shown with diagonal stripes on the map

**Ground Movement:**
- Advance to adjacent LAND hex (sea hexes filtered out)
- Must leave at least 1 unit behind (max moved = min(3, count-1))
- Authorized by ground_attack permission
- 100% probability (guaranteed movement)
- Embarked units can land

### Blockades

Blockades require **ground forces** at chokepoints (not naval superiority), except for Formosa.

**Standard chokepoints:** Ground forces must be physically present. Air strikes cannot break a blockade -- requires ground invasion or voluntary lift.

**Formosa special rules:** Full blockade requires naval presence in 3+ of 6 surrounding sea zones. Any single friendly ship in any adjacent zone automatically downgrades full to partial blockade.

**Blockade effects on oil:** Gulf Gate blockade reduces Solaria/Mirage production by 25% (partial) or 50% (full). Caribe Passage blockade affects Caribe.

### Basing Rights

Countries can grant or revoke basing rights to foreign militaries. Foreign units with basing agreements are NOT treated as occupiers.

### Nuclear Chain

Nuclear weapons follow a multi-step authorization chain:
1. **Initiate** -- Head of State orders launch
2. **Authorize** -- required co-authorizers confirm (e.g., Ironhand for Sarmatia, Rampart for Cathay)
3. **Intercept** -- target and allied countries with T3+ nuclear capability can attempt interception
4. **Resolve** -- warhead detonates or is intercepted

Nuclear co-authorization: Sarmatia requires both Pathfinder and Ironhand. Cathay requires both Helmsman and Rampart. Military chiefs can refuse or slow-walk.

### Nuclear Tests

A signal action, not required for tech advancement:
- Underground: -0.2 stability to tester only. Less provocative.
- Overground: -0.5 stability to tester, -0.3 stability to ALL countries globally. Maximum signal.
- Both types: +5 political support (nationalist rally) for the testing country.
- Requires at least nuclear level 1.
- Requires 3-way authorization (same as nuclear launch): Head of State + Military Chief + Moderator confirmation.

---

## 5. POLITICAL DOMAIN

### Stability (1-9 scale)

Stability is the core health metric of a country. Calculated each round with additive factors:

**Positive factors:**
- High stability inertia (7-8 range): +0.05
- GDP growth above 2%: up to +0.15
- Social spending above baseline: up to +2.0
- Territory gained: +0.20 per hex
- Democratic resilience for frontline defenders: +0.15
- Autocracy siege resilience (sanctioned autocracies at war): +0.10
- Propaganda boost

**Negative factors:**
- GDP contraction: up to -0.30 (capped)
- Social spending cuts: up to -2.0
- War friction: -0.05 to -0.10 per round (varies by role in conflict)
- Casualties: -0.2 per casualty
- Territory lost: -0.4 per hex
- War tiredness: up to -0.4
- Sanctions: -0.1 per sanction level
- Inflation above baseline: up to -0.50 (capped)
- Economic crisis state: -0.10 (stressed) to -0.50 (collapse)
- Market index stress
- Mobilization: -0.2 per level

**Dampeners:**
- Peaceful, non-sanctioned countries: negative deltas halved
- Autocracies: negative deltas reduced by 25%

Hard floor: 1.0. Hard cap: 9.0.

**Threshold triggers:**
- Below 6: unstable
- Below 5: protests probable
- Below 3: protests automatic
- Below 2: regime collapse risk
- At 1: failed state

### Political Support (5-85% scale)

Tracks how much the populace supports current leadership.

**Democracies/hybrids:** Driven by GDP growth, casualties, stability, economic crisis state, oil price shocks, election proximity effects, war tiredness.

**Autocracies:** Driven by stability, perceived weakness, repression, nationalist rally.

Mean-reversion toward 50% applies to all regime types.

### Elections

Scheduled via the sim configuration (key_events in sim_runs table). Known scheduled elections:
- Columbia mid-terms: Round 2
- Columbia presidential: Round 5/6
- Ruthenia wartime elections: Rounds 2-3

Election resolution: 50% AI-calculated score (based on economic performance, stability, war penalty, crisis, oil) + 50% player vote input. Political crises (arrests, impeachments) penalize the incumbent.

### Health Events

Elderly leaders face per-round incapacitation risk:
- Dealer (Columbia, age 80): 10% per round, medical quality 0.9
- Helmsman (Cathay, age 73): 5-10% per round, medical quality 0.7
- Pathfinder (Sarmatia, age 73): 5-10% per round, medical quality 0.6 (increases +2%/round)

Incapacitation triggers succession mechanics. Death or incapacitation can fundamentally alter a country's trajectory.

### Change of Leader

Replaces the old coup/protest mechanics. Requirements: country stability at or below threshold, initiator is non-HoS, team has 3+ members. Triggers a two-phase process: removal vote, then election vote. Requires moderator confirmation.

### Martial Law

Head of State only. One-time per country per simulation. Activates emergency powers.

### Arrest

Head of State can arrest team members. Temporarily removes target's ability to act. Moderator must confirm.

### Assassination

One card per eligible role per game. Two modes:
- **Domestic:** 60% base hit probability
- **International:** 20% base + country-specific bonuses (Levantia: +30% total 50%, Sarmatia: +10% total 30%)
- If hit lands: 50% kill (target dead, +15 support to target's country via martyr effect), 50% survive (target injured, +10 support martyr effect)
- Detection: domestic 50%, international 40-70% (higher if missed)
- Requires moderator confirmation

---

## 6. DIPLOMATIC DOMAIN

### Transactions

Any country can propose an exchange to another country. Transactions include:
- Offer and request components (coins, resources, political favors)
- Counterpart can accept, decline, or counter-propose
- Public or secret visibility

### Agreements

Formal treaties between countries. Proposed, then signed by counterpart. Types include security agreements, trade deals, basing rights, technology sharing.

Deals with Dawn (Persia reformist) as signatory get +20% credibility bonus.

### Public Statements

Any role can make attributed public statements visible to all participants. Used for signaling, threats, reassurance, or propaganda.

### Organization Meetings

Roles can call meetings of international organizations (NATO, EU, BRICS+, OPEC, etc.). Sets agenda and invites relevant members.

### Meeting System

Roles can invite others to 1-on-1 or group meetings. Maximum 2 active invitations per role. Invitations expire after 10 minutes.

---

## 7. COVERT DOMAIN

Covert operations use **individual card pools** assigned per role (from roles.csv). Each card is consumed permanently -- never recovers.

### Operation Types

| Op Type | Base Success | Base Detection | Base Attribution | Effect on Success |
|---------|-------------|---------------|-----------------|-------------------|
| Espionage/Intelligence | 60% | 30% | 30% | Intel report (85% accuracy if success, 45% if fail -- always returns data) |
| Sabotage | 45% | 40% | 50% | 2% of target GDP damage |
| Cyber | 50% | 35% | 40% | 1% of target GDP damage |
| Disinformation | 55% | 25% | 20% | -0.3 stability, -3.0 support to target |
| Election Meddling | 40% | 45% | 50% | 2-5% support shift against target incumbent |

### Mechanics

- AI level adds +5% success per level
- Repeated ops against same target: -5% success, +10% detection per previous op
- All probabilities clamped to [5%, 95%]
- Detection and attribution are SEPARATE rolls -- target may know something happened but not who did it
- Intelligence requests ALWAYS return an answer. Failed ops return low-accuracy data (+-30% noise). Successful ops return high-accuracy data (+-5% noise). The recipient does NOT know the accuracy level.

### Intelligence Powers

Columbia, Cathay, Levantia, Albion, and Sarmatia have enhanced covert capabilities (up to 3 ops per round vs default 2).

Shadow (Columbia CIA) has the largest card pool: 8 intelligence, 3 sabotage, 3 cyber, 1 disinformation, 1 election meddling, 1 assassination.

### Proxy Operations

For Persia (Furnace and Anvil), sabotage cards represent proxy terrorist attack capabilities via regional militias.
For Solaria (Wellspring), sabotage cards represent proxy attack capability via regional militia/proxy networks.

---

## 8. TECHNOLOGY DOMAIN

### Two R&D Tracks

**Nuclear Technology** (max level 3):
- L0 -> L1 (threshold: 0.60 progress): subsurface test capability
- L1 -> L2 (threshold: 0.80): open test capability
- L2 -> L3 (threshold: 1.00): full strategic nuclear arsenal

**AI Technology** (max level 4):
- L0 -> L1 (threshold: 0.20): basic capability
- L1 -> L2 (threshold: 0.40): +0.5 percentage points GDP growth
- L2 -> L3 (threshold: 0.60): +1.5pp GDP growth, no combat modifier
- L3 -> L4 (threshold: 1.00): +3.0pp GDP growth, +1 combat die modifier (only if ai_l4_bonus flag set at level-up, 50% chance)

### R&D Progress Formula

Progress per round = (investment / GDP) x 0.8 (R&D multiplier) x rare_earth_factor

When progress reaches the threshold for the current level, the country levels up and progress resets to zero.

### Rare Earth Restrictions

Cathay controls rare earths. Each restriction level reduces R&D efficiency by 15%:
- Level 0: 100% efficiency (no restriction)
- Level 1: 85%
- Level 2: 70%
- Level 3: 55%
- Level 4+: 40% (floor)

### Technology Transfer

Allies can share technology. Donor must be at least 1 level ahead. Transfer adds a fixed progress boost:
- Nuclear transfer: +0.20 progress to recipient
- AI transfer: +0.15 progress to recipient

Does not directly level up -- just accelerates progress.

### Starting Technology Levels

| Country | Nuclear | AI | Notes |
|---------|---------|-----|-------|
| Columbia | L3 | L3 | Full nuclear + advanced AI |
| Cathay | L2 | L3 | Near-strategic nuclear |
| Sarmatia | L3 | L1 | Full nuclear, weak AI |
| Gallia | L2 | L2 | Independent nuclear |
| Albion | L2 | L2 | Independent nuclear |
| Levantia | L1 | L2 | Undeclared nuclear |
| Choson | L1 | L0 | Tested nuclear, no AI |
| Bharata | L1 | L2 | Declared nuclear |
| Persia | L0 (70% progress) | L0 | Nuclear aspirant |
| Others | L0 | L0-L3 | Varies (see countries.csv) |

---

## 9. TIME STRUCTURE

### Full Round Timeline

```
ROUND N
  |
  +-- Phase 0: Pre-Start (first round only)
  |     Moderator assigns participants to roles
  |     Oracle intro conversations tracked
  |     "Start Simulation" button
  |
  +-- Phase A: Active Round (60-80 min, configurable)
  |     |  Participants submit actions freely
  |     |  Immediate actions processed in real-time:
  |     |    combat, covert ops, intelligence, transactions,
  |     |    agreements, public statements, arrests, assassinations
  |     |  Batch decisions queued for Phase B:
  |     |    set_budget, set_tariffs, set_sanctions, set_opec
  |     |  AI triggered 3 times: start, midpoint, near-end
  |     |  Moderator confirms sensitive actions (assassination, arrest, change_leader)
  |     |  Timer counts down; OVERTIME shown in red if expired
  |     |  Moderator clicks "End Phase A"
  |
  +-- Phase B: Engine Processing (automated, 5-12 min)
  |     |     1. Economic: oil -> GDP -> revenue -> budget -> production ->
  |     |        tech -> inflation -> debt -> crisis -> momentum ->
  |     |        contagion -> sanctions -> tariffs -> dollar
  |     |     2. Political: stability, elections (if scheduled), health events
  |     |     3. Results written to DB
  |     |     4. Observatory events generated
  |     |     5. Moderator quick review (can adjust)
  |     |     6. Results published to all
  |     |
  +-- Inter-Round: Unit Movement (timed, 5-10 min, AFTER Phase B)
  |           Military commanders reposition forces
  |           Map updates in real-time
  |           Moderator can extend
  |
  +-- Round End
        Inter-round closes
        Round counter advances
        Key events for new round triggered
        --> Phase A of Round N+1
```

### Scheduled Key Events (configurable per sim)

Events are stored in `sim_runs.key_events` (JSONB), configured via the wizard. Examples:
- Columbia mid-term elections (typically Round 2)
- Columbia presidential election (typically Round 5-6)
- Ruthenia wartime elections
- Mandatory meetings, nomination windows

### Timer Mechanics

- Client-side calculation from: `phase_started_at + duration_seconds`
- No drift on refresh (recalculates from stored start time)
- Manual mode (default): timer counts down but does NOT auto-advance. Moderator decides when to move on.
- Automatic mode: timer auto-advances phases when expired. Moderator can still pause/intervene.

### Moderator Controls

The moderator has full control:
- Pause, extend, or end any phase
- Toggle auto-approve (all actions bypass confirmation)
- Toggle auto-attack (combat bypasses confirmation queue)
- Toggle dice mode (physical dice vs automatic rolls)
- Override any country/world state value
- Submit actions as any role (test panel)
- Broadcast announcements to all participants

---

## 10. ACTION QUICK REFERENCE

All actions below are implemented in the engine. Action types match `action_schemas.py` and `action_dispatcher.py`.

### Military Actions

| Action | Schema | Processing | Notes |
|--------|--------|-----------|-------|
| `ground_attack` | AttackDeclarationOrder | Immediate | RISK dice, adjacent hex only |
| `ground_move` | MoveUnitsOrder | Inter-round | Adjacent land hex, leave 1 behind |
| `air_strike` | AttackDeclarationOrder | Immediate | 2-hex range, 12%/6% hit |
| `naval_combat` | AttackDeclarationOrder | Immediate | RISK dice in sea hexes |
| `naval_bombardment` | AttackDeclarationOrder | Immediate | Sea->adjacent land, 10% hit |
| `naval_blockade` | BlockadeOrder | Immediate | Establish/lift/reduce at chokepoint |
| `launch_missile_conventional` | MissileLaunchOrder | Immediate | Missile consumed on fire |
| `basing_rights` | BasingRightsOrder | Immediate | Grant or revoke |
| `martial_law` | MartialLawOrder | Immediate | One-time per country per sim |
| `nuclear_test` | NuclearTestOrder | Immediate | Signal action, stability cost |
| `nuclear_launch_initiate` | MissileLaunchOrder | Chain | Starts multi-step authorization |
| `move_units` | MoveUnitsOrder | Inter-round | Batch movement orders |
| `declare_war` | -- | Immediate | Formal war declaration |

### Economic Actions (Batch -- queued for Phase B)

| Action | Schema | Notes |
|--------|--------|-------|
| `set_budget` | -- | Social spending, military production, R&D allocation |
| `set_tariffs` | TariffOrder | Per-country, levels 0-3 |
| `set_sanctions` | SanctionOrder | Per-country, levels -3 to +3 |
| `set_opec` | -- | Production level: min/low/normal/high/max |
| `rd_investment` | RDInvestmentOrder | Nuclear, AI, or strategic missile track |

### Political Actions

| Action | Schema | Processing | Notes |
|--------|--------|-----------|-------|
| `arrest` | ArrestOrder | Requires confirmation | HoS only, target loses ability to act |
| `release_arrest` | -- | Immediate | Release previously arrested role |
| `assassination` | AssassinationOrder | Requires confirmation | 1 card per role per game |
| `change_leader` | ChangeLeaderOrder | Requires confirmation | Replaces coup + protest mechanics |
| `reassign_types` | ReassignPowersOrder | Immediate | HoS reassigns military/econ/foreign powers |
| `call_early_elections` | CallEarlyElectionsOrder | Immediate | HoS only |
| `self_nominate` | SubmitNominationOrder | Immediate | For upcoming elections |
| `withdraw_nomination` | -- | Immediate | Withdraw from election |
| `cast_vote` / `cast_election_vote` | CastVoteOrder | Immediate | Secret ballot |

### Diplomatic Actions

| Action | Schema | Processing | Notes |
|--------|--------|-----------|-------|
| `public_statement` | PublicStatementOrder | Immediate | Visible to all, attributed |
| `propose_transaction` | TransactionOrder | Immediate | Exchange proposal |
| `respond_exchange` | RespondExchangeOrder | Immediate | Accept/decline/counter a proposed transaction |
| `propose_agreement` | TransactionOrder | Immediate | Formal treaty proposal |
| `sign_agreement` | SignAgreementOrder | Immediate | Countersign a treaty |
| `call_org_meeting` | OrgMeetingOrder | Immediate | NATO, EU, BRICS+, OPEC, etc. |
| `meet_freely` / `invite_to_meet` | -- | Immediate | Handled via meeting/chat system, not a submittable action. See Section 6: Meeting System. |

### Covert Actions

| Action | Schema | Processing | Notes |
|--------|--------|-----------|-------|
| `covert_operation` | CovertOpOrder | Immediate | Espionage, sabotage, cyber, disinfo, election meddling |
| `intelligence` | CovertOpOrder | Immediate | Targeted intelligence request |

### Actions Requiring Moderator Confirmation

- `assassination` -- removes a participant from active play
- `arrest` -- temporarily removes ability to act
- `change_leader` -- changes team leadership
- `nuclear_test` -- 3-way authorization (HoS + Military Chief + Moderator)
- `nuclear_launch_initiate` -- 3-way authorization (HoS + Military Chief + Moderator)
- Combat actions (optional, when auto-attack is OFF): `ground_attack`, `naval_combat`, `air_strike`

Auto-approve mode bypasses the confirmation queue for testing and AI-only runs.

---

*Generated 2026-04-21 from live codebase. Sources: action_schemas.py, economic.py, military.py, political.py, technology.py, action_dispatcher.py, map_config.py, roles.csv, countries.csv, SPEC_M4_SIM_RUNNER.md.*
