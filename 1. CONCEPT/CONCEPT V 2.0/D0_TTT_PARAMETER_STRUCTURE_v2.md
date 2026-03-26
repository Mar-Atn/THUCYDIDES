# Thucydides Trap SIM — Parameter Structure
**Code:** D0 | **Version:** 1.1 | **Date:** 2026-03-25 | **Status:** Conceptual — parameter identification and classification (reviewed)

---

## Purpose

This document identifies and classifies **every parameter** that must be defined before the SIM can run. It answers: *what exactly do we need to specify, and when does each parameter get set?*

This is a CONCEPT-phase document. It names and organizes parameters — it does not assign specific values. Values come in the SEED phase (D1–D5 documents).

---

## Three-Block Classification

Every parameter belongs to exactly one of three blocks, based on **when it is set** and **who sets it**.

### Block A — SEED DESIGN
*Set once during scenario design. Canonical. Defines the scenario itself.*

These are the "written play" — the specific numerical and structural choices that make THIS scenario (the Thucydides Trap, H2 2026 – H1/H2 2029) what it is. If you change a Seed parameter, you have a different scenario. Authored by the design team. Frozen before any SIM runs.

**Examples:** Columbia starts with GDP X, Nuclear L3, 10 strategic missiles. Cathay's economy is 45% Industry. Ground unit production costs Y coins. Stability threshold for protests is 5.

### Block B — SCENARIO CONFIGURATION
*Adjusted by moderator when preparing a specific scenario variant. Adapts the Seed to context.*

These parameters don't change the scenario's story — they change how it's delivered. Group size, round timing, difficulty tuning, which optional roles are active, how many rounds to plan for. A moderator might run the same Seed with 27 participants in a single day, or with 36 participants over two days — both are valid configurations of the same scenario.

**Examples:** 31 participants, two-day format, 7 rounds planned, Fixer and Pioneer active, Bharata and Phrygia human-played, covert ops delay set to 2 minutes.

### Block C — SIM-RUN PRESET
*Set immediately before launch. Maps the abstract scenario to the specific session.*

The final step: assigning real humans to roles, confirming AI participant assignments, setting the communication infrastructure, final moderator preferences. This is the "cast list" and "stage directions" for opening night.

**Examples:** "Maria plays Dealer, Alex plays Helmsman, Bharata is AI-operated, Round 1 starts at 10:15."

---

## Parameter Tables

Parameters are organized by **domain** (cross-cutting, then Military, Economy, Domestic Politics, Technology) and within each domain by **level** (World → Country → Role/Individual). Each parameter is tagged with its block (A/B/C).

### Notation
- **Block:** A = Seed Design, B = Scenario Config, C = SIM-Run Preset
- **Granularity:** W = World-level, K = per-Country, R = per-Role/Individual, Z = per-Zone/Theater
- **Source doc:** Reference to the concept file that defines this parameter

---

## 0 — Structural / Cross-Cutting Parameters

These define the game's skeleton — what exists, how time works, what the rules are.

### 0.1 — Country & Organization Structure (source: B1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 0.1.1 | Country roster | W | A | Which countries exist in this scenario (currently 21) |
| 0.1.2 | Country SIM names | K | A | Fictional name mapping (Columbia, Cathay, etc.) |
| 0.1.3 | Country brief description | K | A | Narrative identity of each country: structural function (hegemon, challenger, swing state...), real-world parallel, key tensions, geopolitical position |
| 0.1.4 | Organization roster | W | A | Standing organizations at game start (NATO, EU, UNSC, BRICS+, OPEC+, G7, Columbia Parliament) |
| 0.1.5 | Organization membership | per-org | A | Which countries belong to which organizations |
| 0.1.6 | Organization decision rules | per-org | A | Consensus, majority, veto rules per organization |
| 0.1.7 | Active expansion roles | W | B | Which optional roles are activated (Fixer, Pioneer, Sol, Ledger) |
| 0.1.8 | Solo country assignment mode | K | C | Per solo country: human-played or AI-operated (depends on actual participant pool) |
| 0.1.9 | Optional structural roles | W | B | Whether Dove, Veritas, or other structural roles are included |

### 0.2 — Role Architecture (source: B2)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 0.2.1 | Role definitions (structured) | R | A | Each role requires these specific fields: |
| 0.2.1a | — Character name | R | A | SIM name (Dealer, Helmsman, etc.) |
| 0.2.1b | — Title | R | A | Functional title (President, Chairman, etc.) |
| 0.2.1c | — Country | R | A | Which country this role belongs to |
| 0.2.1d | — Faction / camp | R | A | Internal alignment (e.g., President's camp, Opposition, Reformist) |
| 0.2.1e | — Base / optional flag | R | A | Whether this role is in the base roster or expansion set |
| 0.2.1f | — Core interests & ambitions | R | A | What this character wants, fears, and is tempted by |
| 0.2.1g | — Specific rights & powers | R | A | What actions this role can uniquely perform |
| 0.2.1h | — Starting resources | R | A | Personal coins, assets, special starting information (if any) |
| 0.2.1i | — Key relationships | R | A | Critical allies, adversaries, dependencies within and across teams |
| 0.2.2 | Authorization chains | per-action | A | Which roles must approve which actions (e.g., nuclear launch = HoS + DefMin + 1 more) |
| 0.2.3 | Organization voting rights | per-org × R | A | Vote weight per role in each organization they participate in (Columbia Parliament seats, EU votes, UNSC vetoes, etc.) |
| 0.2.4 | Human-to-role assignment | R | C | Which specific person plays which role |

### 0.3 — Time Structure (source: C3)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 0.3.1 | Scenario time span | W | A | Start and end dates in scenario time (H2 2026 – H1/H2 2029) |
| 0.3.2 | Time per round | W | A | Each round = 1 half-year (6 months) |
| 0.3.3 | Scheduled events | per-round | A | Which events anchor to which scenario times (mid-terms R2, UNGA R3, presidential R5) |
| 0.3.4 | Planned round count | W | B | 6, 7, or 8 rounds |
| 0.3.5 | Round length schedule | per-round | B | Customizable set: minutes per round for Phase A negotiation (e.g., 80/75/65/60/55/45, compressing over time) |
| 0.3.6 | Deployment window duration | W | B | Minutes for Phase C deployment (default: 5) |
| 0.3.7 | Overnight rules (two-day) | W | B | Structure of overnight period, what's permitted |
| 0.3.8 | Moderator flex authority | W | B | Whether/how moderator can extend or compress rounds in real-time |

### 0.4 — Map & Geography (source: C4)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 0.4.1 | Global map design | W | A | Map projection, centering, visual style |
| 0.4.2 | Theater definitions | Z | A | Which potential theaters exist (Eastern Ereb, Taiwan Strait, Mashriq, Caribbean, Thule, Korea) |
| 0.4.3 | Zone count per theater | Z | A | Number of zones in each theater map (Eastern Europe: 12–20, Taiwan: 3–4, etc.) |
| 0.4.4 | Zone adjacency rules | Z | A | Which zones are adjacent to which (determines attack/movement options) |
| 0.4.5 | Chokepoint definitions | Z | A | Which sea zones are chokepoints, what they control |
| 0.4.6 | Active theaters at start | W | A | Which theaters are active at game start (Eastern Ereb + Mashriq) |
| 0.4.7 | Theater activation triggers | Z | A | What causes a dormant theater to activate (first military action in region) |
| 0.4.8 | Map display format | W | B | Physical wall map, digital screen, hybrid — and which screens show what |

### 0.5 — Action System (source: C2)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 0.5.1 | Action catalog | W | A | Complete list of available actions (~30), categorized by engine |
| 0.5.2 | Action authorization requirements | per-action | A | Which roles required to initiate/confirm each action |
| 0.5.3 | Action timing rules | per-action | A | Real-time vs. submitted; which engine processes |
| 0.5.4 | Transaction irreversibility rule | W | A | All confirmed transactions are irreversible |
| 0.5.5 | Default continuation rule | W | A | If no submission, previous round's settings continue |
| 0.5.6 | Budget submission deadline | W | A | Hard deadline = end of round |
| 0.5.7 | Role-specific exclusive actions | R | A | Special capabilities per role (Shadow: selective briefing; Tribune: investigation; etc.) |

### 0.6 — Engine Architecture (source: E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 0.6.1 | Processing system definitions | W | A | Three engines + persistent DB — their responsibilities and interfaces |
| 0.6.2 | World Model processing sequence | W | A | 8-step batch processing order |
| 0.6.3 | Output structure (World/Country/Individual) | W | A | What data the engine produces at each level |
| 0.6.4 | Rollback capability | W | A | Any round can be restored from DB |
| 0.6.5 | Moderator review step | W | A | Step 7: moderator can adjust any calculated value before publish |
| 0.6.6 | Narrative generation scope | W | A | What the AI generates: world narrative, country briefings, clock updates, risk flags |

---

## 1 — Military Domain Parameters

### 1.1 — Unit Types & Properties (source: C1, C2)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 1.1.1 | Unit type definitions | W | A | Five types: ground, naval, tactical air/missiles, strategic missiles, air defense |
| 1.1.2 | Unit producibility | per-type | A | Which types can be produced (ground, naval, tactical: yes; strategic missiles: Cathay only +1/round; air defense: no) |
| 1.1.3 | Unit range/adjacency rules | per-type | A | Ground/naval: adjacent zones. Tactical: adjacent to own forces/bases. Strategic: global. Air defense: deployed zone. |
| 1.1.4 | Air defense absorption capacity | W | A | Strikes absorbed per air defense unit before overflow (default: 3) |
| 1.1.5 | Amphibious assault ratio | W | A | Standard: 3:1 force ratio required. Formosa-specific: 4:1. Naval superiority prerequisite. Pre-landing bombardment can reduce defenders. |
| 1.1.6 | Transfer effectiveness penalty | W | A | Transferred units at reduced effectiveness for N rounds (default: 1) |
| 1.1.7 | Naval bombardment probability | W | A | Chance per naval unit per round of destroying one ground unit (default: 10%) |
| 1.1.8 | Redeployment transit time | W | A | Long-distance redeployment takes N rounds (default: 1) |
| 1.1.9 | Attack garrison rule | W | A | Attacker must leave at least 1 ground unit in the zone from which they attack (as in RISK) |

### 1.2 — Starting Military Forces (source: D1 — to be created in SEED)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 1.2.1 | Starting ground units | K | A | Number of ground units per country at game start |
| 1.2.2 | Starting naval units | K | A | Number of naval units per country |
| 1.2.3 | Starting tactical air/missile units | K | A | Number of tactical units per country |
| 1.2.4 | Starting strategic missiles | K | A | Fixed allocation per country (Columbia ~10, Nordostan ~10, Cathay ~3+, Gallia ~2, Albion ~2) |
| 1.2.5 | Starting air defense units | K | A | Fixed allocation per country (non-producible, scarce) |
| 1.2.6 | Starting unit deployment | K×Z | A | Which units deployed in which zones at game start |
| 1.2.7 | Columbia base network | Z | A | Location of Columbia's 4-5 global bases (Pacific/Yamato, Ereb/Teutonia, Mashriq/Gulf, Indian Ocean, Mediterranean?) |
| 1.2.8 | Starting basing rights | K×K | A | Which countries host which countries' forces at start |
| 1.2.9 | Starting war status | K×K | A | Which countries are at war at game start (Nordostan vs. Heartland, potentially Persia-related) |

### 1.3 — Production & Maintenance (source: C1, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 1.3.1 | Production cost per unit type | K × per-type | A | Coins per unit produced, per country (country-specific — Columbia pays more) |
| 1.3.2 | Production tier multipliers | W | A | Normal: 1× cost per unit / 1× output. Accelerated: 2× cost per unit / 2× output (4× total). Maximum: 4× cost per unit / 3× output (12× total). |
| 1.3.3 | Production capacity ceiling | K × per-type | A | Maximum units per type per round per country (even at maximum tier) |
| 1.3.4 | Maintenance cost per unit type | K × per-type | A | Coins per existing unit per round (country-specific) |
| 1.3.5 | Unit degradation without maintenance | W | A | What happens to unfunded units (reduced effectiveness, attrition rate) |
| 1.3.6 | Mobilization pool | K | A | Reserve manpower available per country at each mobilization level |
| 1.3.7 | Mobilization social cost | per-level | A | Stability penalty per mobilization level (partial / general / total) |
| 1.3.8 | Strategic missile production rate | W | A | Cathay: +1/round if funded. Others: 0. |

### 1.4 — Combat Resolution (source: C2, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 1.4.1 | Combat model | W | A | RISK-model: dice per unit pair, attacker loses ties (defender advantage) |
| 1.4.2 | Morale modifier rules | W | A | Stability-derived morale: what stability ranges give what combat modifiers |
| 1.4.3 | Tech combat modifier | per-level | A | AI/Semiconductor level effects on combat (L4: +2 dice modifier) |
| 1.4.4 | First-deployment penalty | W | A | Newly deployed units' reduced effectiveness in first round |
| 1.4.5 | Theater-specific modifiers | Z | A | Any terrain/theater bonuses (e.g., amphibious penalty, urban defense bonus) |
| 1.4.6 | Nuclear warhead effects (L1 tactical) | W | A | 50% troops in zone destroyed, economy -2 coins, air defense can intercept |
| 1.4.7 | Nuclear warhead effects (L2 strategic) | W | A | 30% economic capacity destroyed, 50% military destroyed, leader survival 1/6 |
| 1.4.8 | Nuclear retaliation window | W | A | Duration for other nuclear powers to respond (default: 5 minutes real-time) |
| 1.4.9 | Strategic missile execution window | W | A | Real-time window from launch to impact (default: 10 minutes) |
| 1.4.10 | Assassination base probability | W | A | 50% success ± modifiers |
| 1.4.11 | Assassination detection probability | W | A | 60–80% detection range |

### 1.5 — Covert Operations (source: C2, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 1.5.1 | Covert ops types | W | A | Intelligence, sabotage, cyber attack, disinformation, election meddling |
| 1.5.2 | Base success probabilities | per-op-type | A | Starting probability for each covert op type |
| 1.5.3 | Detection probability base | per-op-type | A | Base chance of attribution per op type |
| 1.5.4 | Detection escalation rate | W | A | How repeated ops against same target increase detection chance |
| 1.5.5 | Intelligence power bonus | K | A | Enhanced success rate for intelligence powers (Columbia, Cathay, Levantia) |
| 1.5.6 | Covert ops per-round limit | K | A | Max operations per country per round (default: 2 most, 3 intelligence powers) |
| 1.5.7 | Covert ops absolute pool | K | A | Total ops available per country across entire SIM |
| 1.5.8 | Covert ops result delay | W | B | Moderator-configurable delay (default: instant, can set 0–N minutes) |

---

## 2 — Economic Domain Parameters

### 2.1 — Country Economic Profile (source: C1, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 2.1.1 | Starting GDP | K | A | Absolute GDP value per country at game start |
| 2.1.2 | Base GDP growth rate | K | A | Natural growth rate per country before modifiers (%) |
| 2.1.3 | Economic sector structure | K | A | GDP composition: % Resources, % Industry, % Services, % Technology per country |
| 2.1.4 | Tax structure / revenue extraction rate | K | A | What fraction of GDP becomes state revenue |
| 2.1.5 | Starting treasury (reserves) | K | A | Coins in state treasury at game start |
| 2.1.6 | Starting inflation rate | K | A | Inflation level at game start per country |
| 2.1.7 | Starting trade balance | K | A | Net trade position per country |
| 2.1.8 | Oil producer status | K | A | Which countries are oil/resource producers (Solaria, Nordostan, Persia, Mirage, Caribe) |
| 2.1.9 | Formosa semiconductor dependency | K | A | Per country: degree of dependency on Formosa chip imports (% of tech sector) |

### 2.2 — Budget Mechanics (source: C1, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 2.2.1 | Budget category structure | W | A | Categories: social spending, ground production, naval production, tactical air production, strategic missile production, tech R&D (nuclear + AI), reserves |
| 2.2.2 | Social spending baseline | K | A | Required social spending as % of GDP per country (below = stability hit) |
| 2.2.3 | Social spending diminishing returns | W | A | Formula for how above-baseline social spending produces diminishing stability gains |
| 2.2.4 | Revenue formula | W | A | Revenue = f(GDP, tax_rate, trade_income, oil_revenue) - sanctions_cost - inflation_erosion - war_damage |
| 2.2.5 | Deficit rules | W | A | Options when overspent: cut spending, print money (inflation), draw reserves. Zero reserves + deficit = crisis. |
| 2.2.6 | Money printing inflation rate | W | A | How much inflation each unit of printed money generates |
| 2.2.7 | Inflation natural decay rate | W | A | How quickly inflation decreases if printing stops |
| 2.2.8 | Economic crisis auto-cut sequence | W | A | What gets cut automatically: production first, then social spending, then unit attrition |
| 2.2.9 | Columbia budget approval rule | W | A | Requires parliamentary majority (3 of 5 seats) |

### 2.3 — Trade & Sanctions Mechanics (source: C1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 2.3.1 | Tariff scale | W | A | Level 0–3 per sector per target |
| 2.3.2 | Tariff impact formula | W | A | How tariffs affect: revenue to imposer, import cost inflation, GDP impact, rerouting |
| 2.3.3 | Sanctions scale | W | A | Level -3 to +3 per type (financial, resources, industrial, technology) per target |
| 2.3.4 | Sanctions impact formula | W | A | Impact weighted by: economy sizes, coalition size, evader support, sector exposure |
| 2.3.5 | Sanctions cost-to-imposer formula | W | A | How sanctions hurt the country imposing them |
| 2.3.6 | Secondary sanctions detection | W | A | Probability of discovering sanctions evasion (via intelligence) |
| 2.3.7 | EU collective tariff rule | W | A | EU tariffs require member consensus |
| 2.3.8 | Starting tariff levels | K×K×sector | A | Initial tariff positions for all country pairs × 4 sectors |
| 2.3.9 | Starting sanctions levels | K×K×type | A | Initial sanctions positions for all country pairs × 4 types |
| 2.3.10 | Frozen assets (starting) | K | A | Specific frozen asset amounts (e.g., Nordostan assets held in Columbia/EU) |
| 2.3.11 | Export restriction mechanics | W | A | How restricting strategic goods (semiconductors, rare earths) affects target and imposer |

### 2.4 — Oil / Resource Pricing (source: C1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 2.4.1 | Starting oil price | W | A | Global oil price at game start |
| 2.4.2 | Oil price model | W | A | Price = f(total OPEC+ production decisions, supply disruptions, demand, blockades) |
| 2.4.3 | OPEC+ production options | W | A | Low / normal / high — per member |
| 2.4.4 | Starting OPEC+ production levels | K | A | Initial production setting per OPEC+ member |
| 2.4.5 | Gulf Gate blockade impact | W | A | Effect on oil supply/price when Strait of Gulf Gate is blocked |
| 2.4.6 | Oil revenue formula | K | A | How oil price translates to revenue for each producer |

### 2.5 — Financial Markets & Indicators (source: C1, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 2.5.1 | Financial market indexes | W | A | Three indexes: Columbia, Cathay, Europe — AI-derived signal indicators |
| 2.5.2 | Starting index values | per-index | A | Initial financial market index levels |
| 2.5.3 | GDP growth AI adjustment range | W | A | Bounded AI adjustment for market conditions (default: ±5%). *Calibrate during engine development — defines AI authority scope.* |
| 2.5.4 | Global trade volume index | W | A | Aggregate trade health indicator |
| 2.5.5 | Formosa disruption economic impact | W | A | Effect on tech-dependent economies when Formosa supply interrupted (drop 1 tech level, stockpile depletion in 1–2 rounds) |

### 2.6 — Personal Wealth (source: B2, C1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 2.6.1 | Starting personal coins | R | A | Initial personal wealth for roles with personal funds (~8–12 roles: oligarchs, business figures, Gulf royals, envoys) |

---

## 3 — Domestic Politics Domain Parameters

### 3.1 — Political State (source: C1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 3.1.1 | Starting stability index | K | A | Stability (1–10) per country at game start |
| 3.1.2 | Starting political support | K | A | Political support (0–100%) per country at game start |
| 3.1.3 | Starting Dem/Rep split (Columbia) | K | A | Democrat/Republican popular opinion split (e.g., 48/52) |
| 3.1.4 | Starting war tiredness | K | A | Cumulative war fatigue level per country (non-zero for Nordostan, Heartland) |
| 3.1.5 | Regime type | K | A | Autocracy vs. democracy — determines how political support works |
| 3.1.6 | Starting troop morale modifier | K | A | Derived from stability at game start |

### 3.2 — Stability Mechanics (source: C1, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 3.2.1 | Stability factor weights | W | A | Relative weights for: social budget, casualties, territory, sanctions pain, inflation, mobilization, war fatigue, sabotage, GDP trend |
| 3.2.2 | Stability threshold: strained | W | A | Below 6–7: cracks showing, morale softens |
| 3.2.3 | Stability threshold: crisis | W | A | Below 4–5: protests probable, morale -1, brain drain, capital flight |
| 3.2.4 | Stability threshold: severe crisis | W | A | Below 2–3: protests automatic, economy halved, morale -2, coup risk spikes, production stops |
| 3.2.5 | Stability threshold: failed state | W | A | At 1: government loses control, military may fracture |
| 3.2.6 | Stability recovery rate | W | A | How quickly stability recovers with sustained investment (inertial) |
| 3.2.7 | War fatigue accumulation rate | W | A | How war tiredness grows per round of active conflict |
| 3.2.8 | War fatigue morale effect | W | A | How cumulative war tiredness translates to troop morale penalty |
| 3.2.9 | AI qualitative adjustment range (stability) | W | A | How much AI can adjust the deterministic stability calculation |

### 3.3 — Political Support Mechanics (source: C1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 3.3.1 | Support factor weights (autocracies) | W | A | Weights for: military outcomes, perceived weakness, economic failure, repression effect, nationalism |
| 3.3.2 | Support factor weights (democracies) | W | A | Weights for: same + scandals, broken promises, media scrutiny, approaching elections |
| 3.3.3 | Propaganda effectiveness | W | A | Base support boost per coin spent on propaganda |
| 3.3.4 | Propaganda diminishing returns | W | A | How effectiveness decreases with repeated use |
| 3.3.5 | "Sacred war" rally effect | W | A | Temporary support boost magnitude and duration (fades after 1–2 rounds) |
| 3.3.6 | Repression short-term effect (autocracies) | W | A | Immediate protest suppression + stability floor |
| 3.3.7 | Repression long-term erosion (autocracies) | W | A | Gradual support decline from sustained repression |
| 3.3.8 | AI-enhanced propaganda multiplier | per-level | A | How AI tech level amplifies propaganda effectiveness (L2+, L3+ substantially more effective) |
| 3.3.9 | Dem/Rep shift formula (Columbia) | W | A | What inputs move the Dem/Rep popular opinion split |

### 3.4 — Elections (source: C1, C3, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 3.4.1 | Columbia mid-terms timing | W | A | Round 2 (H2 2026) |
| 3.4.2 | Columbia mid-terms formula | W | A | Team votes + AI popular vote (50% weight); factors: economic conditions, presidential approval, Dem/Rep split |
| 3.4.3 | Columbia presidential timing | W | A | Nominations Round 4, election Round 5 (H1 2028) |
| 3.4.4 | Columbia presidential formula | W | A | Team votes (weighted: Fixer/Pioneer = 2, others = 1) + AI popular vote (50%); campaign speeches + debate factored |
| 3.4.5 | Heartland wartime election timing | W | A | Round 3–4 |
| 3.4.6 | Heartland election AI factors | W | A | Territory held, economy, casualties, Western support, campaign quality |
| 3.4.7 | Other democracy election triggers | W | A | Stability below threshold triggers government fall / snap election |

### 3.5 — Coups & Revolutions (source: C1, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 3.5.1 | Coup threshold | K | A | % of team that must independently submit (default: >30%) |
| 3.5.2 | Coup window duration | W | A | How long the invisible window stays open for co-conspirators |
| 3.5.3 | Coup probability factors | W | A | Stability, political support, military control, conspirator count, regime type |
| 3.5.4 | Mass protest thresholds | W | A | Probable below stability 5, automatic below 3 |
| 3.5.5 | Revolution conditions | W | A | Stability 1–2 AND political support below 20% |
| 3.5.6 | Coup attempt minimum team sizes | K | A | Columbia 3+, Cathay 2+, Nordostan 2+, Persia 2+ |

---

## 4 — Technology Domain Parameters

### 4.1 — Nuclear Track (source: C1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 4.1.1 | Nuclear level definitions (L0–L3) | W | A | Capabilities at each level (L1: basic weapons; L2: reliable arsenal; L3: full strategic, MAD-capable) |
| 4.1.2 | Starting nuclear levels | K | A | Per country (L3: Columbia, Nordostan. L2: Cathay, Albion, Gallia. L1: Choson, Bharata, Levantia. L0: Persia, all others) |
| 4.1.3 | Nuclear R&D progress (starting) | K | A | % toward next level (e.g., Cathay at 80% toward L3, Persia at 60% toward L1) |
| 4.1.4 | Nuclear advancement threshold | per-level | A | Cumulative R&D investment needed to reach next level |
| 4.1.5 | Nuclear test success probability | K | A | Probability of successful nuclear test by tech level and investment |

### 4.2 — AI / Semiconductor Track (source: C1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 4.2.1 | AI/Semiconductor level definitions (L0–L4) | W | A | Capabilities and effects at each level (L0: none. L1: basic. L2: advanced, +5% GDP. L3: frontier, +15% GDP. L4: breakthrough, +30% GDP, +2 dice) |
| 4.2.2 | Starting AI/Semiconductor levels | K | A | Per country (L3: Columbia, Yamato. L2: Cathay, Teutonia, Albion, Bharata, Levantia, Hanguk. L1: most. L0: Choson, Caribe) |
| 4.2.3 | AI R&D progress (starting) | K | A | % toward next level (e.g., Cathay at 70% toward L3, Columbia at 85% toward L4) |
| 4.2.4 | AI advancement threshold | per-level | A | Cumulative R&D investment needed to reach next level |
| 4.2.5 | Breakthrough probability mechanics | W | A | Whether advancement at high levels is deterministic (threshold) or probabilistic |
| 4.2.6 | Tech GDP productivity multiplier | per-level | A | GDP boost per AI level (+5%, +15%, +30%) |
| 4.2.7 | Tech military modifier | per-level | A | Combat bonus per AI level (L4: +2 dice) |
| 4.2.8 | Formosa supply disruption effect | W | A | Countries drop 1 effective tech level; stockpile depletion timeline (1–2 rounds) |
| 4.2.9 | Alternative fabrication cost & time | W | A | Investment and time to build non-Formosa chip fabrication (3–4 rounds minimum) |

### 4.3 — Tech Transfer & Restrictions (source: C1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 4.3.1 | Tech transfer mechanic | W | A | Replicable: receiver gains, sender keeps. Effective next round. |
| 4.3.2 | Export restriction impact formula | W | A | How restrictions slow target advancement + cost imposer revenue |
| 4.3.3 | Rare earth restriction mechanics | W | A | Cathay's counter-weapon: restrict minerals essential for tech manufacturing |
| 4.3.4 | Starting export restrictions | K×K | A | Any export restrictions already in place at game start |
| 4.3.5 | Personal tech investment rules | R | A | How Pioneer, Circuit can supplement government R&D with personal investment |

---

## 5 — Information & Visibility Parameters

### 5.1 — Information Asymmetry (source: A2, C1, E1)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 5.1.1 | Public dashboard contents | W | A | What all participants can see: raw data (unit counts, GDP, tech investment levels) but NOT conclusions about power balance |
| 5.1.2 | Country-private information | K | A | What each country sees about itself that others don't (exact reserves, R&D progress %, covert op results) |
| 5.1.3 | Intelligence-accessible information | W | A | What can be obtained through espionage (probabilistic, may be inaccurate) |
| 5.1.4 | Strategic missile warhead secrecy | W | A | Warhead type (conventional/nuclear) unknown to target until detonation |
| 5.1.5 | Cathay opacity rule | K | A | Internal Cathay communications private; external through Helmsman |
| 5.1.6 | Starting intelligence assessments | K | A | Each team's brief contains a different assessment of the power balance (deliberately divergent) |
| 5.1.7 | Covert ops result visibility | W | A | Results visible only to initiator; detection triggers broader visibility |

---

## 6 — Moderator & System Parameters

### 6.1 — Moderator Controls (source: E1, C3)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 6.1.1 | Moderator override scope | W | B | Which calculated values the moderator can adjust (Step 7: any value) |
| 6.1.2 | Moderator event injection | W | B | Whether moderator can introduce overnight events, surprise developments |
| 6.1.3 | Covert ops delay setting | W | B | Global delay for covert op results (0 = instant, up to N minutes) |
| 6.1.4 | AI aggressiveness tuning | K | B | Per AI-operated country: how aggressive/cautious the AI behaves |
| 6.1.5 | Difficulty scaling | W | B | Global adjustments for participant experience level (e.g., starting economic conditions more/less forgiving) |
| 6.1.6 | Round extension/compression authority | W | B | Real-time flex: moderator can add/subtract 10–15 min during a round |

### 6.2 — SIM-Run Configuration (source: all)

| # | Parameter | Granularity | Block | Description |
|---|-----------|:-----------:|:-----:|-------------|
| 6.2.1 | Human-to-role mapping | R | C | Specific person assigned to each human role |
| 6.2.2 | AI-to-solo mapping | K | C | Confirmation of which solo countries are AI-operated |
| 6.2.3 | Communication channel setup | W | C | Platform for in-game messaging (web app, Telegram, physical notes) |
| 6.2.4 | Physical room layout | W | C | Table assignments, meeting room allocation, map display location |
| 6.2.5 | Moderator team assignments | W | C | Which moderators handle which functions (engine, narrative, live action) |
| 6.2.6 | Technical infrastructure check | W | C | Web app access confirmed, screens working, internet connectivity |

---

## Parameter Count Summary

| Domain | Block A (Seed) | Block B (Scenario) | Block C (Run) | Total |
|--------|:-----------:|:------------------:|:-------------:|:-----:|
| 0 — Structural / Cross-cutting | 29 | 8 | 3 | 40 |
| 1 — Military | 39 | 1 | 0 | 40 |
| 2 — Economy | 31 | 0 | 0 | 31 |
| 3 — Domestic Politics | 25 | 0 | 0 | 25 |
| 4 — Technology | 19 | 0 | 0 | 19 |
| 5 — Information | 7 | 0 | 0 | 7 |
| 6 — Moderator & System | 0 | 6 | 6 | 12 |
| **TOTAL** | **150** | **15** | **9** | **174** |

---

## Key Observations

**1. The Seed is massive.** ~150 parameters define the scenario. This is expected — the Seed IS the scenario. Most of these are per-country values (21 countries × multiple indicators), making the actual data volume much larger than the parameter count suggests. Structured .csv files will be essential.

**2. Scenario Configuration is lean.** ~15 parameters let a moderator adapt the same scenario to different contexts. This is correct — the moderator adjusts delivery, not content.

**3. SIM-Run is operational.** ~9 parameters are pure logistics. This is a checklist, not a design challenge.

**4. Three parameter types within Seed:**
- **Structural rules** (the "how"): combat model, budget mechanics, formula structures. These are game-design decisions. (~50 parameters)
- **Starting values** (the "what"): GDP, units, tech levels, stability scores. These are scenario-authoring decisions. (~70 parameters, but many are K-level, meaning 21+ data points each)
- **Formula coefficients** (the "how much"): weights, thresholds, multipliers. These bridge design and calibration. (~30 parameters, many needing playtest tuning)

**5. The critical SEED deliverables** for the next phase:
- **D1 — Country Starting Profiles:** GDP, sector structure, treasury, units, tech levels, stability, political support — the complete starting snapshot per country (~50 parameters × 21 countries)
- **D2 — Economic Model Coefficients:** Revenue formula, tariff impact, sanctions impact, oil pricing, inflation — the economic engine's tuning (~25 parameters)
- **D3 — Military Balance Tables:** Production costs, maintenance costs, capacity ceilings, combat modifiers — the military engine's tuning (~20 parameters)
- **D4 — Political Model Coefficients:** Stability weights, support factors, election formulas, coup probabilities — the political engine's tuning (~20 parameters)
- **D5 — Role Starting Conditions:** Personal wealth, exclusive powers quantified, role-specific starting information — the individual-level setup (~15 parameters × ~35 roles)

---

## Parameters Requiring Special Attention in SEED

The cross-check against concept files identified parameters where the CONCEPT documents use qualitative language ("e.g.", "approximately", "TBC") instead of firm definitions. These must be resolved in SEED:

1. **Arrest mechanics** — duration and scope of restriction not yet defined (how many rounds? what actions blocked?)
2. **Assassination survival** — human player vs. AI-operated leader: same survival roll, or different?
3. **Formosa disruption timeline** — "1–2 rounds" stockpile depletion needs a firm number or a formula
4. **Landing operation penalty** — RESOLVED: 3:1 standard, 4:1 Formosa. Naval superiority prerequisite.
5. **AI popular vote formulas** — the 50% AI component in Columbia elections needs an actual calculation model
6. **Rare earth restriction mechanics** — marked "TBC" in C1, needs full specification
7. **Propaganda coin-to-support conversion** — qualitative ("diminishing returns") needs a curve

These are design decisions, not calibration — they affect how the game plays, not just how precisely it's tuned. They should be resolved in early SEED work before the calibration parameters (formula weights, cost tables) are set.

---

## Relationship to Checklist

This document maps to **Section D: Starting Scenario** in the Concept Checklist. It does NOT replace the D1–D5 documents — it provides the complete inventory of what those documents must contain.

| Checklist item | Covered by |
|----------------|------------|
| D1 — Country starting profiles | Parameters: 1.2.x, 2.1.x, 3.1.x, 4.1.2–3, 4.2.2–3, 2.6.1 |
| D2 — Economic balance | Parameters: 2.2.x, 2.3.x, 2.4.x, 2.5.x |
| D3 — Military balance | Parameters: 1.2.x, 1.3.x, 1.4.x |
| D4 — Political starting positions | Parameters: 3.1.x, 3.2.x, 3.3.x, 3.4.x, 3.5.x |
| D5 — Role briefs | Parameters: 0.2.x, 2.6.x, 5.1.6 |

---

## Changelog

- **v1.1 (2026-03-25):** Review pass. Removed derived/redundant parameters (team vs. solo classification, team sizes — folded into role definitions via base/optional flag). Expanded role definition (0.2.1) into specific sub-fields (a–i). Reframed vote weights as organization-linked (0.2.3). Removed non-parameters (dramatic arc, delivery format, session start time, world update duration, break schedule). Corrected 1.1.9 to RISK attack garrison rule. Moved solo country assignment to Block C. Removed premature parameters (personal wealth mechanics, press assignment, briefing distribution). Marked 2.5.3 for engine-development calibration. 174 parameters.
- **v1.0 (2026-03-25):** Initial parameter identification. 183 parameters classified across 3 blocks and 7 domains. Parameter count summary. Key observations. SEED deliverable roadmap (D1–D5). Checklist cross-reference.
