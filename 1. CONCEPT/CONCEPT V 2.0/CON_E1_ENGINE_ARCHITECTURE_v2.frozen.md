# Thucydides Trap SIM — Engine Architecture
**Code:** E1 | **Version:** 0.3 | **Date:** 2026-03-21 | **Status:** Working concept for element-by-element discussion

---

## Architecture Overview

The SIM runs on **three separate processing systems** plus a **persistent database**. Each system has a single responsibility. All write to and read from the same DB.

```
┌─────────────────────────────────────────────────────────────┐
│                     PERSISTENT DATABASE                      │
│  Complete world state · All events · All transactions ·      │
│  Full history · Rollback capability                          │
└──────┬──────────────┬──────────────┬────────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│ TRANSACTION  │  │ LIVE ACTION  │  │   WORLD MODEL        │
│ (MARKET)     │  │   ENGINE     │  │   ENGINE             │
│  ENGINE      │  │              │  │                      │
│              │  │ Real-time    │  │ End-of-round batch   │
│ Live market  │  │ unilateral   │  │ processing           │
│ during       │  │ actions      │  │                      │
│ rounds       │  │ during       │  │ Reads full state     │
│              │  │ rounds       │  │ from DB → processes  │
│ BILATERAL:   │  │              │  │ → writes new state   │
│ Both parties │  │ UNILATERAL:  │  │ to DB                │
│ confirm.     │  │ One party    │  │                      │
│ No calc.     │  │ decides.     │  │ Economics, politics, │
│ Pure data    │  │ Fast calc    │  │ production, tech,    │
│ transfer.    │  │ (dice +      │  │ narratives           │
│              │  │ modifiers).  │  │                      │
│ Coins, arms, │  │ Probabilistic│  │ AI-assisted +        │
│ tech,        │  │ outcome.     │  │ deterministic        │
│ treaties,    │  │              │  │ formulas             │
│ basing       │  │ Combat,      │  │                      │
│ rights,      │  │ covert ops,  │  │                      │
│ org creation │  │ domestic     │  │                      │
│              │  │ actions      │  │                      │
└──────────────┘  └──────────────┘  └──────────────────────┘
```

**Database principle:** ALL world states and ALL events are saved. Any round can be restored. Any decision can be reviewed. Any calculation can be rolled back and rerun. The DB is the single source of truth.

---

## System 1: Transaction (Market) Engine (live, during rounds)

Handles all bilateral resource transfers and agreements. Operates continuously during rounds. Both parties must confirm. Pure data operations — no calculation, no AI reasoning. No dice.

### Defining characteristic: BILATERAL — requires confirmation from all parties.

### What it processes:

| Transaction type | Transfer mechanic | Validation |
|-----------------|-------------------|------------|
| Coin transfer | Exclusive (sender loses, receiver gains) | Sufficient balance check |
| Arms transfer | Exclusive (units change ownership, reduced effectiveness 1 round) | Units exist, authorization chain |
| Technology transfer | Replicable (receiver gains level, sender keeps) | Sender has tech, authorization |
| Basing rights | Replicable (access granted, sovereignty retained) | Authorization chain |
| Treaty / agreement | Stored in register, not enforced | All signatories confirm |
| Organization creation | New entity created with declared rules | All founding members confirm |

### Rules:
- Immediate execution on confirmation from all required parties
- Irreversible (to reverse, execute a new opposite transaction voluntarily)
- All transactions logged with timestamp, parties, terms
- Authorization chains enforced (e.g., arms transfer needs head of state + defense minister)

---

## System 2: Live Action Engine (real-time, during rounds)

Handles all unilateral actions that require calculation — dice rolls, probability resolution, modifier application. One party decides (with internal authorization chain). Result delivered instantly (or with moderator-configurable delay for covert ops).

### Defining characteristic: UNILATERAL — one actor decides, engine calculates outcome.

### 2a. Combat Actions

| Action | Instant outcome | Deferred to World Model |
|--------|----------------|------------------------|
| **Attack** (ground/naval/air) | Dice + modifiers → casualties by unit type, territory control changes. Map updated immediately. | GDP impact from destroyed infrastructure, stability impact from casualties, morale effects, alliance reactions |
| **Naval blockade** | Chokepoint status changes on map. Trade flow disruption flag raised. | Full economic cascade (trade disruption → GDP → revenue), oil price impact |
| **Missile / drone strike** | Target damage calculated (dice + air defense interception probability). Collateral damage. Map updated. | Economic damage quantified, stability impact, diplomatic cascade |
| **Nuclear test** | Success/failure resolved. If Persia L0→L1: advancement confirmed. | Global stability shock, diplomatic crisis, alliance recalculations |
| **Nuclear strike** | L1 or L2 damage resolved. Interception by air defense. Retaliation window opens (5 min for other nuclear powers). Leader survival dice. | Full economic destruction quantified, global stability recalculation, long-term effects |

### 2b. Covert Operations

| Action | Instant outcome | Deferred to World Model |
|--------|----------------|------------------------|
| **Espionage** | Success/failure dice. If success: intelligence obtained, delivered to initiator. | If detected: diplomatic consequences |
| **Sabotage** | Success/failure dice. If success: target facility/infrastructure damaged. | Economic damage quantified in batch |
| **Cyber attack** | Success/failure dice. If success: target systems disrupted. | Economic/military disruption quantified in batch |
| **Disinformation** | Success/failure dice. If success: target stability/support affected. | Full political impact quantified in batch |

**Covert ops rules:**
- Results delivered to initiator instantly by default. Moderator can configure delay (0 to N minutes) per operation.
- Limited per round per country (configurable — e.g., 2 for most, 3 for intelligence powers like Columbia, Cathay, Levantia).
- Detection/attribution probability: separate dice roll. Repeated ops against same target increase detection chance.
- Limited absolute pool per SIM (configurable — prevents unlimited espionage across all rounds).

### 2c. Domestic Actions

| Action | Instant outcome | Deferred to World Model |
|--------|----------------|------------------------|
| **Arrest** | Target participant restricted immediately. | Political support impact, diplomatic consequences (if foreign national) |
| **Fire / reassign** | Target loses role powers immediately. Player stays in game. | Political cost calculated |
| **Propaganda campaign** | Coins spent immediately. Campaign flag raised. | Political support boost calculated (diminishing returns) in batch |
| **Assassination attempt** | Success/failure dice (50% base ± modifiers). Detection dice (60-80%). If target is human player: survival dice. Results reported to initiator and (if detected) to target/world. | Martyr effect on political support, international condemnation, alliance stress |
| **Coup attempt** | Probability = f(stability, political support, co-conspirators, military units under plotters). Success/failure resolved. If success: new leader immediately. | Full political restructuring, loyalty shifts, stability recalculation, international recognition |

### 2d. Other Live Actions

| Action | Instant outcome | Deferred to World Model |
|--------|----------------|------------------------|
| **Call organization meeting** | Meeting scheduled, members notified. Any member can call for any org they belong to (UNSC, EU, NATO, Columbia Parliament, BRICS+, etc.). | Meeting outcomes logged for narrative context |
| **Public statement** | Statement logged, visible to all parties. | Diplomatic consequences in batch |

### Authorization rules (enforced by Live Action Engine):
- Combat: Head of state orders → military chief confirms
- Nuclear strike: Always 3 confirmations — head of state + military chief + one additional authority, within 2 min. In smaller teams, AI military advisor provides the missing confirmation and may refuse if strategically irrational.
- Covert ops: Intelligence chief or head of state
- Arrest: Head of state or security authority (on own soil only)
- Assassination: Head of state or intelligence chief
- Coup: Any internal actor + at least one co-conspirator with military/security access

---

## System 3: World Model Engine (batch, between rounds)

The core. Reads the complete world state from DB (including all real-time events that occurred during the round), processes all cumulative effects, calculates the new world state, and writes it back to DB.

**Receives from DB:**
- Previous world state (all indicators, resources, settings)
- All transactions executed during the round (from Transaction (Market) Engine)
- All combat outcomes (from Live Action Engine)
- All covert operation outcomes (from Live Action Engine)
- All domestic action outcomes (from Live Action Engine)
- All submitted settings (budget, tariffs, sanctions, export restrictions, OPEC+ production)
- All mobilization orders submitted
- All organization meetings held and decisions taken
- All speeches and public commitments (for AI narrative context)

**Produces to DB:**
- Complete new world state (World level + Country level + Individual level)
- Generated narratives
- Moderator summary report

---

### INPUTS TO WORLD MODEL ENGINE

Everything below is READ FROM DB at the start of batch processing. The engine does not receive inputs directly from participants — it reads what happened.

#### I1. Submitted Settings (collected during round, processed now)

| Setting | Submitted by | Structure |
|---------|-------------|-----------|
| **National budget** | PM / finance authority. Head of state can override. Columbia: requires parliamentary majority vote. | Allocation as % across: social spending, military production (by unit type: land, naval, air/missile, nuclear), tech R&D investment, reserves. Total constrained by available revenue. |
| **Tariff levels** | Head of state or PM | By target country × by sector (resources, industry, services, tech). Level 0-3 each. |
| **Sanctions position** | Head of state | By target country × by type (financial, resources, industrial, technology). Level -3 to +3 each. |
| **Export restrictions** | Head of state | By target country × by resource/tech type. Binary (restricted / unrestricted) or graded. |
| **OPEC+ production level** | Head of state / PM (Cartel members only) | Low / normal / high. |
| **Mobilization orders** | Head of state. Submitted anytime during round. | Level: partial / general / total. Executed NOW (between rounds). New units available for deployment before next round starts. |

#### I2. Combat Outcomes (already resolved by Live Action Engine)

Read from DB: all attack results, blockade effects, strike damage, nuclear events. The World Model Engine processes the SECONDARY effects — not the combat itself.

#### I3. Transaction Records (already executed by Transaction (Market) Engine)

Read from DB: all coin movements, arms transfers, tech transfers, treaties signed, organizations created. The World Model Engine incorporates these into the new state.

#### I4. Domestic Action Outcomes (already resolved by Live Action Engine)

| Action | What was already resolved (by Live Action Engine) | What World Model processes (secondary effects) |
|--------|--------------------------------------------------|----------------------------------------------|
| **Arrest** | Target restricted | Impact on political support, diplomatic consequences if foreign national |
| **Fire / reassign** | Target lost powers | Political cost, team dynamics shift |
| **Propaganda campaign** | Coins spent, campaign active | Political support boost calculated (diminishing returns). "Sacred war" variant locks escalation narrative. |
| **Assassination attempt** | Success/failure/detection already determined | Full consequence cascade: martyr effect on political support, international condemnation, alliance stress |
| **Coup attempt** | Success/failure already determined, new leader active if successful | Full political restructuring: loyalty shifts, stability impact, international recognition questions |

#### I5. Covert Operation Outcomes (already resolved by Live Action Engine)

| Operation | What was already resolved | What World Model processes |
|-----------|--------------------------|--------------------------|
| **Espionage** | Intelligence obtained or failed. Detection status known. | If detected: diplomatic consequences quantified |
| **Sabotage** | Facility/infrastructure damage determined | Economic damage quantified for GDP calculation |
| **Cyber attack** | System disruption determined | Economic/military disruption quantified |
| **Disinformation** | Campaign success/failure determined | Stability/political support impact quantified |

#### I6. Other Round Events

| Event | Source |
|-------|--------|
| Organization meetings held and decisions taken | Logged by facilitator or participants |
| Elections conducted (if scheduled this round) | Human votes + AI popular vote calculation |
| Public commitments made (speeches, declarations) | Logged as text for AI narrative context |
| Public statements made | Logged as diplomatic events |

---

### PROCESSING SEQUENCE

```
DB (complete round state) → READ
         │
         ▼
┌─────────────────────────────────────────────┐
│ STEP 1: VALIDATE & LOCK                     │
│                                              │
│ • Check all submitted settings for           │
│   authorization and consistency              │
│ • Resolve conflicts (two people submitted    │
│   different budgets → head of state          │
│   override rule applies)                     │
│ • Flag missing submissions → apply defaults  │
│   (previous round's settings continue)       │
│ • Lock: no more inputs accepted              │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ STEP 2: ECONOMIC STATE UPDATE               │
│ (AI-assisted)                                │
│                                              │
│ INPUTS:                                      │
│ • Previous GDP and growth rate per country   │
│ • Tariff levels (all bilateral pairs)        │
│ • Sanctions positions (all bilateral pairs)  │
│ • Export restrictions                        │
│ • OPEC+ production decisions → oil price     │
│ • Combat damage to infrastructure            │
│ • Blockade effects on trade flows            │
│ • Sabotage/cyber damage                      │
│ • Money printing (inflation)                 │
│ • Treaty-based trade arrangements            │
│ • Tech level effects on productivity         │
│                                              │
│ CALCULATES:                                  │
│ • New oil price (from OPEC+ decisions +      │
│   supply disruption + demand)                │
│ • Trade flow changes (tariff + sanctions +   │
│   blockade effects, by sector)               │
│ • Sanctions impact per country per sector    │
│ • GDP growth/contraction per country         │
│ • New GDP level per country                  │
│ • Inflation rate per country                 │
│ • Trade balance per country                  │
│                                              │
│ METHOD: Deterministic base formulas for      │
│ direct effects (tariff → revenue, sanctions  │
│ → sector damage). AI reasoning for second-   │
│ order effects (confidence shocks, market     │
│ sentiment, rerouting, capital flight).        │
│                                              │
│ OUTPUTS TO DB:                               │
│ • Updated economic indicators per country:   │
│   GDP, GDP growth %, inflation, trade        │
│   balance, oil price (global), sector        │
│   performance (4 sectors per country)        │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ STEP 3: POLITICAL STATE UPDATE              │
│ (AI-assisted)                                │
│                                              │
│ INPUTS:                                      │
│ • Previous stability index per country       │
│ • Previous political support per country     │
│ • Economic performance (from Step 2)         │
│ • Combat outcomes (casualties, territory)    │
│ • War tiredness (cumulative, per country)    │
│ • Social budget as % of baseline             │
│ • Mobilization level and its social cost     │
│ • Propaganda campaigns executed              │
│ • Assassination/coup outcomes                │
│ • Disinformation attacks received            │
│ • Sanctions pain felt by population          │
│ • Election results (if held this round)      │
│ • Significant diplomatic events              │
│   (alliances broken, treaties violated,      │
│   territory claimed/lost)                    │
│                                              │
│ CALCULATES:                                  │
│ • New Stability Index per country (1-10)     │
│ • New Political Support per country (0-100%) │
│ • Threshold checks:                          │
│   - Below 6: unstable (coup risk x2)        │
│   - Below 5: mass protest probable           │
│   - Below 4: protests automatic              │
│   - Below 3: regime collapse risk            │
│ • War tiredness accumulation                 │
│ • Troop morale modifier (from stability)     │
│                                              │
│ METHOD: SIM4 formula as base (war tiredness  │
│ + budget impact + combat losses + territory  │
│ changes = deterministic component). AI       │
│ reasoning for qualitative factors (public    │
│ mood from economic decline trajectory,       │
│ rally-around-flag effects, regime type       │
│ differences in resilience, leadership        │
│ credibility, cumulative fatigue vs. one-off  │
│ shocks).                                     │
│                                              │
│ OUTPUTS TO DB:                               │
│ • Updated political indicators per country:  │
│   Stability Index, Political Support,        │
│   war tiredness level, troop morale          │
│   modifier, threshold flags (protest/coup    │
│   risk active)                               │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ STEP 4: REVENUE & MILITARY PRODUCTION       │
│ (pure calculation)                           │
│                                              │
│ INPUTS:                                      │
│ • New GDP per country (from Step 2)          │
│ • Tax structure per country (fixed attribute)│
│ • Oil revenue (for producers, from oil price)│
│ • Sanctions cost on revenue                  │
│ • Trade income/tariff revenue                │
│ • Inflation erosion on purchasing power      │
│                                              │
│ CALCULATES:                                  │
│ a) REVENUE for next round per country:       │
│    Revenue = f(GDP, tax_structure,            │
│    trade_income, oil_revenue)                │
│    - sanctions_cost - inflation_tax          │
│    - war_damage_to_capacity                  │
│                                              │
│ b) BUDGET EXECUTION this round:              │
│    • Auto-deduct military maintenance        │
│      (existing units × maintenance cost      │
│      per type: land, naval, air, nuclear)    │
│    • Execute social spending allocation      │
│    • Execute military production:            │
│      - Land units produced = f(budget        │
│        allocated, production capacity,       │
│        production cost per unit)             │
│      - Naval units: same                     │
│      - Air/missile units: same               │
│      - Nuclear: same (if tech level allows)  │
│    • Execute tech R&D allocation             │
│    • Calculate surplus/deficit               │
│    • Update reserves (previous + revenue     │
│      - total spending = new reserves)        │
│    • If deficit > reserves: CRISIS           │
│      (forced cuts or money printing)         │
│                                              │
│ c) MOBILIZATION EXECUTION:                   │
│    • Mobilized units added to available pool │
│    • Social cost already applied in Step 3   │
│                                              │
│ d) UNIT MAINTENANCE CHECK:                   │
│    • Units without maintenance funding       │
│      degrade (reduced effectiveness or       │
│      attrition)                              │
│                                              │
│ METHOD: Pure arithmetic. No AI. Transparent  │
│ formulas. Participants should be able to     │
│ predict: "if I allocate X coins to naval     │
│ production, I get Y ships."                  │
│                                              │
│ OUTPUTS TO DB:                               │
│ • Revenue for next round per country         │
│ • Budget execution report (what was spent)   │
│ • New unit counts by type per country        │
│   (existing ± combat losses ± production     │
│   ± transfers ± mobilization ± attrition)    │
│ • Available units for deployment (flagged    │
│   for participant deployment window)         │
│ • Reserve levels per country                 │
│ • Budget deficit % per country               │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ STEP 5: TECHNOLOGY ADVANCEMENT & IMPACT     │
│ (AI-assisted)                                │
│                                              │
│ INPUTS:                                      │
│ • Previous tech levels per country           │
│   (Nuclear L0-3, AI/Semiconductor L0-4)     │
│ • R&D budget allocated (from Step 4)         │
│ • Tech transfers received this round         │
│ • Export restrictions affecting inputs       │
│ • Formosa semiconductor supply status        │
│   (normal / disrupted / destroyed)           │
│ • Sabotage/cyber damage to tech facilities   │
│ • Personal tech investments by participants  │
│   (Pioneer, Circuit — if any)                │
│                                              │
│ CALCULATES:                                  │
│ • R&D progress accumulation per country      │
│   per tech domain                            │
│ • Threshold check: has any country reached   │
│   next level? (deterministic: cumulative     │
│   investment reaches threshold)              │
│ • Breakthrough events: if Level 3+ AI        │
│   reached by anyone → global impact          │
│   assessment                                 │
│ • Impact of tech level on military           │
│   effectiveness (modifier for next round's   │
│   combat)                                    │
│ • Impact of tech level on economic           │
│   productivity (feeds back to GDP in next    │
│   round's Step 2)                            │
│ • Impact of Formosa disruption on global     │
│   tech progress (slows everyone dependent    │
│   on semiconductor imports)                  │
│                                              │
│ METHOD: Deterministic accumulation (R&D      │
│ spending adds to progress bar). AI reasoning │
│ for impact assessment (what does a tech      │
│ breakthrough MEAN for the power balance,     │
│ for military effectiveness, for economic     │
│ competitiveness).                            │
│                                              │
│ OUTPUTS TO DB:                               │
│ • Updated tech levels per country            │
│ • R&D progress bars per country per domain   │
│ • Tech breakthrough events (if any)          │
│ • Military tech modifiers for next round     │
│ • Economic productivity modifiers            │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ STEP 6: NARRATIVE GENERATION                │
│ (AI-generated)                               │
│                                              │
│ INPUTS:                                      │
│ • Complete new world state (Steps 2-5)       │
│ • All events from the round (combat,         │
│   transactions, diplomatic actions,          │
│   speeches, covert ops)                      │
│ • Previous round's narrative (continuity)    │
│ • Structural clocks status:                  │
│   - Power balance trajectory                 │
│   - Cathay military capability curve         │
│   - Sarmatia economic reserves countdown    │
│   - Columbia election countdown              │
│   - Persia nuclear program progress          │
│                                              │
│ GENERATES:                                   │
│ • World-level narrative: "state of the       │
│   world" briefing summarizing the round's    │
│   key developments and their significance    │
│ • Country-level briefings: economic and      │
│   military situation per country, tailored   │
│   to that country's perspective              │
│ • Structural clock updates: where does the   │
│   power balance stand now? Which attractors  │
│   are heating up?                            │
│ • Risk flags: situations approaching         │
│   critical thresholds (stability below 4,    │
│   reserves near zero, tech parity            │
│   approaching, military balance shifting)    │
│                                              │
│ NOTE: Could be integrated into Steps 2, 3,   │
│ and 5 rather than separate. Each AI-assisted │
│ step could generate its narrative component  │
│ as it processes. Separate step allows for    │
│ cross-domain narrative coherence.            │
│                                              │
│ OUTPUTS TO DB:                               │
│ • World narrative text                       │
│ • Country briefing texts (per country)       │
│ • Clock status indicators                    │
│ • Risk flags                                 │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ STEP 7: MODERATOR REVIEW                    │
│                                              │
│ • AI generates summary report for moderator: │
│   key changes, risk flags, narrative draft,  │
│   any anomalies detected                     │
│ • AI performs sense-making check:             │
│   "do these outputs look internally          │
│   consistent? any contradictions?"           │
│ • Moderator can adjust any calculated value  │
│ • Moderator can modify narrative             │
│ • Moderator approves final output package    │
│                                              │
│ OUTPUTS TO DB:                               │
│ • Final approved world state                 │
│ • Final approved narratives                  │
│ • Moderator adjustments logged               │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ STEP 8: PUBLISH                             │
│                                              │
│ • New world state written to DB as           │
│   "Round N+1 initial state"                  │
│ • All outputs delivered to participants      │
│   (delivery mechanism = interface concern,   │
│   not engine concern)                        │
│ • Round N archived                           │
│                                              │
│ FOLLOWED BY:                                 │
│ ┌─────────────────────────────────────────┐ │
│ │ DEPLOYMENT WINDOW (5 minutes)           │ │
│ │                                         │ │
│ │ Participants with appropriate rights     │ │
│ │ (military chief / head of state) can    │ │
│ │ deploy newly available units:           │ │
│ │ • Newly produced units                  │ │
│ │ • Newly mobilized units                 │ │
│ │ • Units that arrived from previous      │ │
│ │   round's movement orders               │ │
│ │                                         │ │
│ │ Deployment = assign units to theaters/  │ │
│ │ zones on the map. Takes effect          │ │
│ │ immediately (units are already in-      │ │
│ │ country). Long-distance redeployment    │ │
│ │ (to foreign theaters) still takes 1     │ │
│ │ round transit.                          │ │
│ │                                         │ │
│ │ After deployment window: Round N+1      │ │
│ │ begins.                                 │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

### OUTPUT STRUCTURE (what the World Model Engine writes to DB)

All outputs organized by level. No visibility/interface logic — just data.

#### Level 1: World State

| Indicator | Type | Source step |
|-----------|------|:----------:|
| Global oil price | Number | 2 |
| Global trade volume index | Number | 2 |
| Active theaters count | Number | From Live Action Engine | **SEED DECISION (2026-03-27):** Only Eastern Ereb has a detailed theater map. Other theaters resolved at global hex level. |
| Chokepoint status (per chokepoint: open/contested/blocked) | Enum | From Live Action Engine |
| Power balance indicators (aggregate military, economic, tech comparisons) | Composite index | 2,4,5 |
| Structural clock positions (Formosa capability, Columbia election, Sarmatia reserves, Persia nuclear) | Progress bars | 2,3,4,5 |
| World narrative text | Text | 6 |
| Risk flags | List | 6 |

#### Level 2: Country State (per country)

| Indicator | Type | Source step |
|-----------|------|:----------:|
| **Economic** | | |
| GDP | Number | 2 |
| GDP growth rate (% this round) | Number | 2 |
| Inflation rate | Number | 2 |
| Trade balance | Number | 2 |
| Sector performance (resources, industry, services, tech) | 4 numbers | 2 |
| Revenue (available for next round's budget) | Number | 4 |
| Reserves (treasury) | Number | 4 |
| Budget deficit/surplus % | Number | 4 |
| Sanctions cost absorbed this round | Number | 2 |
| | | |
| **Military** | | |
| Land units (count) | Number | 4 |
| Naval units (count) | Number | 4 |
| Air/missile units (count) | Number | 4 |
| Nuclear capability (count, if any) | Number | 4 |
| Units available for deployment (newly produced + mobilized + arrived) | Numbers by type | 4 |
| Unit deployment map (which units in which zones) | Map data | From deployment window |
| Military production capacity by type (ceiling) | Reference data | Static attribute |
| Troop morale modifier | Number | 3 |
| | | |
| **Political** | | |
| Stability Index (1-10) | Number | 3 |
| Political Support (0-100%) | Number | 3 |
| War tiredness (cumulative) | Number | 3 |
| Threshold flags: protest risk, coup risk, election triggered | Booleans | 3 |
| Regime status (stable / unstable / crisis) | Enum | 3 |
| | | |
| **Technology** | | |
| Nuclear tech level (L0-3) | Number | 5 |
| AI/Semiconductor tech level (L0-4) | Number | 5 |
| R&D progress (% toward next level, per domain) | Numbers | 5 |
| Tech breakthrough flag (if level-up occurred) | Boolean | 5 |
| | | |
| **Diplomatic** | | |
| War status (at war with: list of countries) | List | Event-driven |
| Peace status (peace treaty with: list) | List | Event-driven |
| Organization memberships | List | Event-driven |
| Active treaties (register) | List | Market Engine |
| | | |
| **Narrative** | | |
| Country briefing text | Text | 6 |

#### Level 3: Individual State (per participant, where applicable)

| Indicator | Type | Source |
|-----------|------|--------|
| Personal coin balance (for roles with personal wealth) | Number | Market Engine |
| Personal resource ownership (tech, other assets) | List | Market Engine |
| Role status (active / fired / arrested / dead / successor) | Enum | Live Action Engine |
| Covert operation results (for initiator only) | Text | Live Action Engine |

---

### ACTIONS TIMING SUMMARY

| Action | When executed | Resolution | Secondary effects |
|--------|-------------|------------|-------------------|
| **Coin transfer** | Real-time | Instant (Market Engine) | — |
| **Arms transfer** | Real-time | Instant (Market Engine) | Reduced effectiveness 1 round |
| **Technology transfer** | Real-time | Instant (Market Engine) | — |
| **Treaty / agreement** | Real-time | Instant (Market Engine) | — |
| **Basing rights** | Real-time | Instant (Market Engine) | — |
| **Organization creation** | Real-time | Instant (Market Engine) | — |
| **Organization meeting call** | Real-time | Instant (any member can call for any org they belong to) | — |
| **Attack** | Real-time | Live Action Engine (instant dice + map) | Economic/political in batch |
| **Naval blockade** | Real-time | Live Action Engine (instant map change) | Economic cascade in batch |
| **Missile/drone strike** | Real-time | Live Action Engine (instant resolution) | Economic/political in batch |
| **Nuclear test** | Real-time | Live Action Engine (instant) | Diplomatic/political in batch |
| **Nuclear strike** | Real-time | Live Action Engine (instant, retaliation window) | Everything in batch |
| **Arrest** | Real-time | Live Action Engine (instant) | Political impact in batch |
| **Fire / reassign** | Real-time | Live Action Engine (instant) | Political impact in batch |
| **Propaganda** | Real-time | Live Action Engine (coins spent) | Political support in batch |
| **Assassination** | Real-time | Live Action Engine (dice: success/detection) | Full cascade in batch |
| **Coup attempt** | Real-time | Live Action Engine (dice: success/failure) | Full restructuring in batch |
| **Espionage** | Real-time | Live Action Engine (results, moderator-adjustable delay) | — |
| **Sabotage** | Real-time | Live Action Engine (results, moderator-adjustable delay) | Economic damage in batch |
| **Cyber attack** | Real-time | Live Action Engine (results, moderator-adjustable delay) | System disruption in batch |
| **Disinformation** | Real-time | Live Action Engine (results, moderator-adjustable delay) | Stability impact in batch |
| **Mobilization** | Submitted anytime | Executed in batch (Step 4) | Units available after processing |
| **National budget** | Submitted during round | Executed in batch (Step 4) | All budget consequences in batch |
| **Tariff levels** | Submitted during round | Applied in batch (Step 2) | Economic cascade in batch |
| **Sanctions position** | Submitted during round | Applied in batch (Step 2) | Economic cascade in batch |
| **Export restrictions** | Submitted during round | Applied in batch (Step 2/5) | Trade/tech impact in batch |
| **OPEC+ production** | Submitted during round | Applied in batch (Step 2) | Oil price in batch |
| **Public statement** | Real-time | Live Action Engine (logged) | Diplomatic consequences in batch |
| **Military deployment** | After batch processing | 5-min deployment window | Units placed on map |

---

### KEY DESIGN DECISIONS TO DISCUSS ELEMENT BY ELEMENT

Each of the following needs detailed specification. We should work through them one by one:

**E1.1** — National budget structure: exact categories, constraints, relationship between revenue and spending ceiling, deficit rules, money printing mechanics

**E1.2** — Economic model: GDP calculation formula, tariff impact formula, sanctions impact formula (by sector), trade flow model, inflation mechanics, oil price model

**E1.3** — Stability Index model: what inputs, what weights, how to combine deterministic base with AI qualitative assessment, threshold consequences, regime-type differences

**E1.4** — Military production model: production capacity tables by country by unit type, cost per unit by type, maintenance cost, mobilization pool, unit degradation without maintenance

**E1.5** — Technology model: R&D investment → progress accumulation → level thresholds, breakthrough mechanics, impact on military and economic effectiveness, Formosa chokepoint

**E1.6** — Combat resolution model: dice mechanics, modifiers (tech, morale, terrain, unit type matchups), casualty calculation, territory control rules, nuclear mechanics

**E1.7** — Covert operations model: probability tables, detection mechanics, limits per round, impact quantification

**E1.8** — Narrative generation: what context the AI receives, what it produces, quality controls, moderator interface

**E1.9** — Election mechanics: Columbia mid-terms, Columbia presidential, Ruthenia wartime — vote calculation, AI popular vote formula, campaign mechanics

**E1.10** — Transaction (Market) Engine: validation rules, authorization chains, conflict resolution, rollback capability

**E1.11** — Live Action Engine: combat resolution model + covert ops probability tables + domestic action mechanics, unified under one real-time processing system

---

## Changelog

- **v0.3 (2026-03-21):** Renamed three systems: Transaction (Market) Engine, Live Action Engine, World Model Engine. Live Action Engine now explicitly covers combat + covert ops + domestic actions (all unilateral, all requiring calculation). Covert ops rules (limits per round, moderator-adjustable delay, detection probability escalation) added to Live Action Engine. Authorization chains detailed per action type. All references updated throughout.
- **v0.2 (2026-03-21):** Major restructure. Three separate systems + persistent DB. Removed AI country decisions from engine (AI participants use same mechanics as humans). Removed visibility/interface concerns from engine scope. Budget restructured to include military production by unit type. All combat actions moved to real-time. Covert ops moved to real-time with moderator-adjustable delay. Mobilization: submitted anytime, executed in batch. Deployment window added after batch processing. Processing sequence reduced to 8 steps. Output structured as World/Country/Individual levels to DB. 10 detailed design elements identified for element-by-element discussion.
- **v0.1 (2026-03-21):** First draft with 13-step processing and 4-layer output model.


<!-- CM-006: Deployment rules updated 2026-03-30. Transit delay removed (instant deployment). Ship capacity formalized (1 ground + 2 air). Naval blockade restriction added. Approved by Marat. -->
