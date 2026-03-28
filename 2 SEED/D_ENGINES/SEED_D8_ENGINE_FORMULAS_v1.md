# TTT SEED D8 -- Engine Formula Documentation v1

## AUDIT REFERENCE SPECIFICATION

**Purpose:** This document formalizes every formula, mechanic, and state variable in the TTT engine code as a readable, auditable specification. If there is ever a question about how the engine works, this document is the definitive answer.

**Engine files covered:**
- `world_model_engine.py` (v2.0 -- three-pass architecture with feedback loops)
- `live_action_engine.py` (v2.0 -- real-time unilateral actions)
- `transaction_engine.py` (v2.0 -- bilateral transfers)
- `world_state.py` (v2.0 -- shared state model)

**Document version:** 1.0
**Date:** 2026-03-28

---

# PART 1: ARCHITECTURE OVERVIEW

## 1.1 Three-Pass Processing Model

The World Model Engine processes between-round updates in three sequential passes.

**Pass 1 -- Deterministic (Chained).** Pure mathematical formulas. Each step uses the output of the previous step. No randomness, no AI discretion. This is the core simulation. All 14 steps execute in a fixed order -- the output of Step 1 (oil price) feeds Step 2 (GDP), which feeds Step 3 (revenue), and so on.

**Pass 2 -- AI Contextual Adjustment.** Heuristic adjustments that simulate market psychology, capital flight, ceasefire rallies, sanctions adaptation, brain drain, and rally-around-the-flag effects. Currently implemented as aggressive rule-based heuristics; architecture is structured for future upgrade to LLM-based calls. Total GDP adjustment from Pass 2 is capped at 30% of previous-round GDP per country.

**Pass 3 -- Coherence Check and Narrative.** Reviews the world state for implausible combinations (e.g., GDP growth during economic collapse, high stability during collapse). Auto-fixes HIGH severity contradictions. Generates a round briefing narrative.

## 1.2 Processing Sequence (14 Chained Steps)

| Step | Name | Scope | What It Needs |
|------|------|-------|---------------|
| 0 | Apply submitted actions | Global | Tariffs, sanctions, OPEC, rare earth, blockades |
| 1 | Oil price | Global | Supply, demand, disruption, war premium |
| 2 | GDP growth | Per country | Oil price, sanctions, tariffs, war, tech, momentum, crisis state |
| 3 | Revenue | Per country | GDP (from step 2), tax rate, oil revenue, debt, inflation |
| 4 | Budget execution | Per country | Revenue (from step 3), mandatory costs, player allocations |
| 5 | Military production | Per country | Budget (from step 4), production capacity, costs |
| 6 | Technology advancement | Per country | R&D investment, rare earth restrictions |
| 7 | Inflation update | Per country | Money printed (from step 4), GDP |
| 8 | Debt service update | Per country | Deficit (from step 4) |
| 9 | Economic state transitions | Per country | All economic indicators from steps 1-8 |
| 10 | Momentum update | Per country | GDP growth, economic state, oil, war, disruptions |
| 11 | Contagion | Cross-country | Economic states, trade weights |
| 12 | Stability update | Per country | GDP growth, social spending, war, sanctions, inflation, crisis state |
| 13 | Political support update | Per country | GDP growth, stability, casualties, crisis state, oil price |
| -- | Post-steps | Various | Revolution check, health events, market index, Helmsman legacy, capitulation, elections |

## 1.3 What Is Deterministic vs. AI-Assisted vs. Coherence-Checked

| Category | Examples | Nature |
|----------|----------|--------|
| **Deterministic** | Oil price, GDP, revenue, budget, inflation, debt, economic state, momentum, contagion, stability, political support | Pure formulas. Same inputs always produce same outputs (except 5% oil volatility noise). |
| **AI-Assisted** (Pass 2) | Market panic (5% GDP hit on crisis entry), capital flight (3-8% GDP), ceasefire rally (+1.5 momentum), sanctions adaptation (+2% GDP), brain drain (-0.02 AI R&D), rally-around-flag (diminishing) | Heuristic rules simulating behavioral/psychological effects. |
| **Coherence-Checked** (Pass 3) | GDP growth during crisis forced negative, collapse with high stability flagged, oil shock on growing importers corrected | Auto-fixes implausible states. |

## 1.4 Engine Version History

| Version | Changes |
|---------|---------|
| **v1** | Basic linear model. No feedback loops. No crisis states. |
| **v2** | Feedback loop architecture. Crisis escalation ladder. Momentum. Contagion. Asymmetric recovery. Soft oil cap. Semiconductor duration-scaling. Sanctions diminishing returns. |
| **v2.5 (Cal fixes)** | Cal-1: Oil price inertia (60/40 blend). Cal-2: Sanctions multiplier 2.0 to 1.5; diminishing returns 0.70 to 0.60. Cal-3: Tech boost on growth rate not GDP multiplier. Cal-4: Inflation stability friction capped at -0.50/round. |

---

# PART 2: WORLD MODEL ENGINE (Between-Round Processing)

## Step 0: Apply Submitted Actions

**Purpose:** Load all player decisions into the world state before formula processing begins.

Actions applied (in order):
1. Tariff changes -- `_apply_tariff_changes` (line 2377)
2. Sanction changes -- `_apply_sanction_changes` (line 2398)
3. OPEC production changes -- `_apply_opec_changes` (line 2406)
4. Rare earth restrictions -- `_apply_rare_earth_changes` (line 2411)
5. Blockade changes -- `_apply_blockade_changes` (line 2442)
6. Sanctions duration tracking -- `_update_sanctions_rounds` (line 2165)
7. Formosa disruption duration tracking -- `_update_formosa_disruption_rounds` (line 2175)

---

#### 1. Oil Price (Global)

**Purpose:** Determines the global oil price, which cascades into GDP (importers hurt, producers benefit), revenue (oil windfall), and political support (voter anger at gas prices). Oil is the single most impactful global variable.

**Inputs:**
- Base price: $80 (hardcoded)
- OPEC production decisions (per member: "low", "normal", "high")
- Sanctions on oil producers (nordostan, persia) at L2+
- Chokepoint blockade status (Gulf Gate, Formosa, Suez, Malacca, etc.)
- Economic states of all countries (demand side)
- GDP growth rates of all countries (demand elasticity)
- Number of active wars (war premium)
- Previous round oil price (inertia)
- Oil above $150 duration counter (mean-reversion pressure)

**Formula:**

```
SUPPLY SIDE:
  supply = 1.0
  For each OPEC member:
    if decision == "low":  supply -= 0.06
    if decision == "high": supply += 0.06
  For each oil producer (nordostan, persia):
    if sanctions_level >= 2: supply -= 0.08
  supply = max(0.5, supply)

DISRUPTION SIDE:
  disruption = 1.0
  if Gulf Gate blocked:     disruption += 0.50
  if Formosa blocked:       disruption += 0.10
  if Suez blocked:          disruption += 0.15
  if Malacca blocked:       disruption += 0.20
  other chokepoints:        disruption += 0.05 each

DEMAND SIDE:
  demand = 1.0
  For each country with GDP > 20:
    if stressed:  demand -= 0.03
    if crisis:    demand -= 0.06
    if collapse:  demand -= 0.10
  For each major economy (GDP > 30) with growth < -2%:
    demand -= 0.02
  Global GDP growth elasticity:
    demand += (avg_gdp_growth - 2.0) * 0.03
  demand = max(0.6, demand)

WAR PREMIUM:
  war_premium = num_active_wars * 0.05
  war_premium = min(war_premium, 0.15)

RAW PRICE:
  raw_price = 80 * (demand / supply) * disruption * (1 + war_premium)

SOFT CAP (asymptotic above $200):
  if raw_price <= 200:
    formula_price = raw_price
  else:
    formula_price = 200 + 50 * (1 - e^(-(raw_price - 200) / 100))
  Theoretical maximum: ~$250

FLOOR:
  formula_price = max(30, formula_price)

INERTIA (Cal-1):
  price = previous_price * 0.4 + formula_price * 0.6

VOLATILITY:
  price *= (1 + gaussian_noise(0, 0.05))

MEAN-REVERSION (if oil > $150 for 3+ consecutive rounds):
  price *= 0.92  (demand destruction accelerates)

FLOOR (final):
  price = max(30, price)
```

**Plain English:** Oil price is driven by supply (OPEC decisions and sanctions on producers), demand (economic health of major economies), disruption (chokepoint blockades), and war risk. The price moves 60% toward the new equilibrium each round and 40% sticky from the previous price. Above $200, an asymptotic formula prevents runaway -- the theoretical ceiling is around $250. If oil stays above $150 for three or more rounds, an 8% demand destruction penalty kicks in.

**Oil Revenue to Producers:**
```
For each oil-producing country:
  resource_pct = sector_resources / 100
  oil_revenue = price * resource_pct * GDP * 0.01
  Columbia special: oil_revenue = min(oil_revenue, GDP * 0.15)
```

**Output:** `ws.oil_price`, `ws.oil_price_index` (= price / 80 * 100), per-country `oil_revenue`

**Feedback loops:** Oil price feeds GDP (Step 2) via oil_shock. GDP contraction reduces demand, which moderates oil price next round. Oil revenue feeds budget (Step 4), allowing producers to fund military operations despite sanctions.

**Calibration notes:**
- Inertia blend: 40% previous / 60% new (Cal-1 v3)
- Gulf Gate disruption: +50% (reduced from +80% in v1)
- Soft cap formula: `200 + 50 * (1 - exp(-(raw - 200) / 100))`
- Volatility: gaussian noise with sigma = 0.05
- Mean-reversion: 0.92 multiplier after 3 rounds above $150

**Engine location:** `world_model_engine.py:337-474`

---

#### 2. GDP Growth (Per Country)

**Purpose:** Calculates each country's GDP growth rate by summing all additive factors, then applying the crisis state multiplier. GDP is the foundation -- it feeds revenue, budget capacity, military spending power, and political support.

**Inputs:**
- Base growth rate (from country data, typically 2-6%)
- Tariff impact (from `_calc_tariff_impact`)
- Sanctions damage (from `_calc_sanctions_impact`)
- Oil price (from Step 1)
- Formosa disruption status and duration
- War zones occupied and infrastructure damage
- AI technology level
- Economic momentum
- Blockade fraction
- Bilateral trade dependency
- Economic state (crisis multiplier)

**Formula:**

```
base_growth = country.gdp_growth_rate / 100  (as decimal)

TARIFF HIT:
  tariff_hit = -(net_tariff_cost / GDP) * 1.5

SANCTIONS HIT (Cal-2: reduced from 2.0 to 1.5):
  sanctions_hit = -sanctions_damage * 1.5
  If sanctions_rounds > 4:
    sanctions_hit *= 0.60  (40% less effective -- adaptation)

OIL SHOCK:
  If oil importer and oil_price > $100:
    oil_shock = -0.02 * (oil_price - 100) / 50
  If oil producer and oil_price > $80:
    oil_shock = +0.01 * (oil_price - 80) / 50

SEMICONDUCTOR DISRUPTION (duration-scaling):
  If Formosa disrupted and country has formosa_dependency > 0:
    severity = min(1.0, 0.3 + 0.2 * max(0, disruption_rounds - 1))
      Round 1: 0.3, Round 2: 0.5, Round 3: 0.7, Round 4: 0.9, Round 5+: 1.0
    tech_sector_pct = sector_technology / 100
    semi_hit = -formosa_dependency * severity * tech_sector_pct

WAR DAMAGE:
  war_zones = count of occupied zones in wars involving this country
  infra_damage = occupied_zones * 0.05 per zone (for defenders), capped at 1.0
  war_hit = -(war_zones * 0.03 + infra_damage * 0.05)

TECH FACTOR (Cal-3: applied to growth rate, not GDP multiplier):
  AI Level 0-1: +0.0pp
  AI Level 2:   +0.5pp  (+0.005)
  AI Level 3:   +1.5pp  (+0.015)
  AI Level 4:   +3.0pp  (+0.030)

MOMENTUM EFFECT:
  momentum_effect = momentum * 0.01  (range: -5% to +5%)

BLOCKADE HIT:
  blockade_frac = trade-weighted chokepoint disruption fraction
  blockade_hit = -blockade_frac * 0.4

BILATERAL DEPENDENCY:
  For each bilateral pair (e.g., columbia-cathay: 15% exposure):
    if partner_growth < 0:
      bilateral_drag += partner_growth * exposure_weight
  bilateral_drag /= 100  (convert to decimal)

AGGREGATE RAW GROWTH:
  raw_growth = base_growth + tariff_hit + sanctions_hit + oil_shock
               + semi_hit + war_hit + tech_boost + momentum_effect
               + blockade_hit + bilateral_drag

CRISIS MULTIPLIER (direction-aware, FIX 9):
  If raw_growth < 0 (contraction):
    normal:   effective_growth = raw_growth * 1.0
    stressed: effective_growth = raw_growth * 1.2  (20% worse)
    crisis:   effective_growth = raw_growth * 1.3  (30% worse)
    collapse: effective_growth = raw_growth * 2.0  (twice as bad)
  If raw_growth >= 0 (growth):
    normal:   effective_growth = raw_growth * 1.0
    stressed: effective_growth = raw_growth * 0.85
    crisis:   effective_growth = raw_growth * 0.5
    collapse: effective_growth = raw_growth * 0.2

NEW GDP:
  new_gdp = old_gdp * (1 + effective_growth)
  new_gdp = max(0.5, new_gdp)  (floor at 0.5 coins)
```

**Bilateral Dependency Pairs (hardcoded):**

| From | To | Exposure |
|------|----|----------|
| columbia | cathay | 15% |
| cathay | columbia | 12% |
| teutonia | cathay | 10% |
| cathay | teutonia | 8% |
| yamato | cathay | 8% |
| hanguk | cathay | 10% |

**Output:** `country.economic.gdp`, `country.economic.gdp_growth_rate`

**Feedback loops:** GDP feeds revenue (Step 3), which feeds budget (Step 4), which feeds military capacity, money printing, and inflation. GDP growth feeds stability (Step 12), political support (Step 13), and momentum (Step 10). GDP contraction feeds demand destruction in oil price (Step 1 next round) and crisis state transitions (Step 9).

**Calibration notes:**
- Sanctions multiplier: 1.5 (Cal-2, was 2.0)
- Sanctions adaptation: 60% effectiveness after 4 rounds (Cal-2, was 70%)
- Tech boost: additive to growth rate, not multiplicative to GDP (Cal-3)
- GDP floor: 0.5 coins

**Engine location:** `world_model_engine.py:506-624`

---

#### 3. Revenue (Per Country)

**Purpose:** Calculates how much money the government actually has to spend this round. Revenue is derived from GDP but reduced by debt service, inflation erosion, war damage, and sanctions costs.

**Inputs:**
- GDP (from Step 2)
- Tax rate (from country data)
- Oil revenue (calculated in Step 1)
- Debt burden (accumulated from previous rounds)
- Inflation (current) and starting inflation (baseline)
- Infrastructure damage from war
- Sanctions levels from all sanctioners and trade weights

**Formula:**

```
base_revenue = GDP * tax_rate

oil_revenue = (set in Step 1, stored in country.economic.oil_revenue)

debt_service = country.economic.debt_burden  (permanent, accumulated)

inflation_erosion:
  inflation_delta = max(0, current_inflation - starting_inflation)
  inflation_erosion = inflation_delta * 0.03 * GDP / 100

war_damage_cost:
  infra_damage = occupied_zones * 0.05 (capped at 1.0)
  war_damage = infra_damage * 0.02 * GDP

sanctions_cost_on_revenue:
  For each sanctioner with sanctions on this country:
    sanc_cost += level * bilateral_trade_weight * 0.015 * GDP

TOTAL REVENUE:
  revenue = base_revenue + oil_revenue - debt_service - inflation_erosion
            - war_damage - sanctions_cost
  revenue = max(0, revenue)
```

**Plain English:** Revenue starts as GDP times tax rate, plus any oil windfall. Then subtract four drains: (1) permanent debt burden from past deficits, (2) inflation erosion based on how far inflation has risen above the country's structural baseline, (3) war damage costs proportional to occupied territory, and (4) sanctions costs proportional to the sanctioner's trade weight and sanction level. Revenue cannot go below zero.

**Output:** Revenue value used in Step 4 (budget execution)

**Feedback loops:** Revenue feeds budget execution. If revenue falls short of mandatory costs, deficits occur, leading to money printing (Step 4), which increases inflation (Step 7), which increases inflation erosion in the revenue formula next round -- a self-reinforcing fiscal squeeze.

**Engine location:** `world_model_engine.py:630-669`

---

#### 4. Budget Execution (Per Country)

**Purpose:** Determines how the government spends its revenue, handles deficits through treasury drawdown or money printing, and tracks the consequences. This is where fiscal death spirals originate.

**Inputs:**
- Revenue (from Step 3)
- Player budget allocations (social, military, tech)
- Military unit counts (for maintenance costs)
- GDP (for social spending baseline)
- Treasury (reserves)

**Formula:**

```
MANDATORY COSTS:
  maintenance = total_units * maintenance_cost_per_unit  (default 0.3/unit)
    total_units = ground + naval + tactical_air + strategic_missiles + air_defense
  social_baseline = social_spending_baseline * GDP
    mandatory_social = social_baseline * 0.70  (70% is mandatory -- FIX 10)
    discretionary_social_pool = social_baseline * 0.30  (30% player can cut)
  mandatory = maintenance + mandatory_social

DISCRETIONARY:
  discretionary = max(revenue - mandatory, 0)
  social_extra = min(player_social_allocation, discretionary)
  remaining = discretionary - social_extra
  military_budget = min(player_military_allocation, remaining)
  remaining -= military_budget
  tech_budget = min(player_tech_allocation, remaining)

TOTAL SPENDING:
  total = mandatory_social + social_extra + military_budget + tech_budget + maintenance

DEFICIT HANDLING:
  If total_spending > revenue:
    deficit = total_spending - revenue
    If treasury >= deficit:
      treasury -= deficit  (draw from reserves)
    Else:
      money_printed = deficit - treasury
      treasury = 0
      inflation += (money_printed / GDP) * 80.0  (aggressive: 80x multiplier)
      debt_burden += deficit * 0.15  (15% of deficit becomes permanent)
  Else:
    surplus = revenue - total_spending
    treasury += surplus

SOCIAL SPENDING RATIO (tracked for stability):
  actual_social_ratio = (mandatory_social + social_extra) / GDP
```

**Plain English:** The government must pay military maintenance and 70% of social spending no matter what. After that, whatever revenue remains is split among additional social spending, military production, and tech R&D based on player choices. If spending exceeds revenue, the treasury is drawn down first. When the treasury hits zero, the shortfall is covered by money printing, which immediately spikes inflation (80x multiplier) and adds 15% of the deficit as permanent debt burden.

**Output:** `deficit`, `money_printed`, `new_treasury`, social/military/tech budgets

**Feedback loops:** Money printing feeds inflation (Step 7). Deficit feeds debt burden (Step 8). Debt burden reduces next round's revenue (Step 3). This creates the classic hyperinflation spiral: deficit causes printing, printing causes inflation, inflation erodes revenue, lower revenue causes larger deficit.

**Calibration notes:**
- Money printing inflation multiplier: 80x
- Debt burden accumulation: 15% of deficit
- Social spending split: 70% mandatory / 30% discretionary (FIX 10)
- Maintenance cost default: 0.3 coins per unit per round

**Engine location:** `world_model_engine.py:675-752`

---

#### 5. Military Production and Maintenance

**Purpose:** Converts budget allocations into military units, handles auto-production for countries at war, and manages the Cathay strategic missile growth.

**Inputs:**
- Military budget allocations (per unit type: coins and tier)
- Production capacity (per unit type)
- Production costs (per unit type)
- Production tier (normal/accelerated/maximum)
- Round number (for naval auto-production timing)
- War status (for ground auto-production)

**Formula:**

```
PLAYER-ORDERED PRODUCTION:
  For each unit type (ground, naval, tactical_air):
    effective_cost = base_cost * PRODUCTION_TIER_COST[tier]
    effective_capacity = base_capacity * PRODUCTION_TIER_OUTPUT[tier]
    units_produced = min(coins_allocated / effective_cost, effective_capacity)
    military[unit_type] += units_produced

PRODUCTION TIER COSTS AND OUTPUTS:
  | Tier        | Cost Multiplier | Output Multiplier |
  |-------------|-----------------|-------------------|
  | normal      | 1.0x            | 1.0x              |
  | accelerated | 2.0x            | 2.0x              |
  | maximum     | 4.0x            | 3.0x              |

NAVAL AUTO-PRODUCTION:
  If naval >= 5 AND round_num is even AND no naval was produced this round:
    naval += 1  (maintenance replacement)

CATHAY STRATEGIC MISSILE GROWTH:
  If country is cathay and strategic_missile_growth > 0:
    strategic_missiles += 1  (automatic each round)

AUTO-PRODUCTION FOR WAR COUNTRIES (FIX 4):
  If country is at war AND has ground production capacity AND treasury >= cost:
    ground += 1
    treasury -= ground_production_cost
```

**Output:** Updated military unit counts, adjusted treasury

**Feedback loops:** Military production drains treasury. More units means higher maintenance next round. Countries at war auto-produce to sustain combat operations, but this drains treasury faster.

**Engine location:** `world_model_engine.py:758-802` (player production), `world_model_engine.py:1831-1850` (auto-production)

---

#### 6. Technology Advancement

**Purpose:** Processes R&D investment into progress toward technology level thresholds. Includes rare earth impact on R&D efficiency and personal tech investment from role characters.

**Inputs:**
- Nuclear and AI R&D investment (coins)
- GDP (as denominator for R&D efficiency)
- Current nuclear/AI levels and progress
- Rare earth restriction level on this country
- Personal tech investments from roles (Pioneer, Circuit, Dealer)

**Formula:**

```
RARE EARTH IMPACT:
  If country has rare earth restrictions:
    rd_factor = 1.0 - (restriction_level * 0.15)
    rd_factor = max(0.40, rd_factor)  (floor: 40% efficiency)
  Else:
    rd_factor = 1.0

NUCLEAR R&D:
  progress = (nuc_investment / GDP) * 0.8 * rd_factor
  nuclear_rd_progress += progress
  Thresholds for level-up:
    L0 -> L1: progress >= 0.60
    L1 -> L2: progress >= 0.80
    L2 -> L3: progress >= 1.00
  On level-up: progress resets to 0

AI R&D:
  progress = (ai_investment / GDP) * 0.8 * rd_factor
  ai_rd_progress += progress
  Thresholds for level-up:
    L0 -> L1: progress >= 0.20
    L1 -> L2: progress >= 0.40
    L2 -> L3: progress >= 0.60
    L3 -> L4: progress >= 1.00
  On level-up: progress resets to 0

PERSONAL TECH INVESTMENT (G13):
  For designated tech investor roles (pioneer, dealer for Columbia; circuit for Cathay):
    If role has tech_investment_this_round > 0 and sufficient personal_coins:
      personal_coins -= investment
      progress_boost = (investment / GDP) * 0.4  (50% of normal R&D efficiency)
      ai_rd_progress += progress_boost
```

**Plain English:** R&D investment is converted to progress proportional to investment divided by GDP, multiplied by the R&D multiplier (0.8) and rare earth factor. Rare earth restrictions from Cathay reduce the target country's R&D efficiency by 15% per restriction level, with a floor of 40%. Technology levels advance when accumulated progress crosses the threshold, then progress resets. Individual role characters can also invest personal coins in R&D at half efficiency.

**Output:** Updated `nuclear_level`, `nuclear_rd_progress`, `ai_level`, `ai_rd_progress`

**Feedback loops:** Higher AI level feeds GDP growth (via tech_boost in Step 2). Higher GDP means more revenue for R&D investment. Rare earth restrictions create friction in this feedback loop.

**Calibration notes:**
- R&D multiplier: 0.8 (increased from 0.5)
- Rare earth penalty: 15% per level, floor 40%
- Personal investment efficiency: 50% of government R&D (multiplier 0.4 vs 0.8)

**Engine location:** `world_model_engine.py:808-848` (R&D), `world_model_engine.py:2156-2163` (rare earth), `world_model_engine.py:2328-2358` (personal investment)

---

#### 7. Inflation Update

**Purpose:** Calculates new inflation level. Structural (baseline) inflation persists; only crisis-induced excess inflation decays naturally. Money printing spikes inflation aggressively.

**Inputs:**
- Previous inflation
- Starting (baseline) inflation
- Money printed this round (from Step 4)
- GDP

**Formula:**

```
excess = max(0, previous_inflation - baseline_inflation)

DECAY (on excess only):
  new_excess = excess * 0.85  (15% natural decay per round)

MONEY PRINTING SPIKE:
  if money_printed > 0 and GDP > 0:
    new_excess += (money_printed / GDP) * 80.0

NEW INFLATION:
  new_inflation = baseline + new_excess
  new_inflation = clamp(new_inflation, 0, 500)  (hard cap at 500%)
```

**Plain English:** Inflation has two components. Structural inflation (the starting baseline) never decays -- it represents the country's normal price environment. Excess inflation above that baseline decays by 15% per round naturally. Money printing adds to excess inflation at an aggressive 80x multiplier: printing 10% of GDP adds 8 percentage points of inflation. The inflation hard cap is 500%.

**Output:** `country.economic.inflation`

**Feedback loops:** Inflation feeds inflation erosion in revenue (Step 3), which increases deficit, which causes more printing, which increases inflation further. Inflation also feeds stability via inflation friction (Step 12).

**Calibration notes:**
- Natural decay: 15% of excess per round (multiplier 0.85)
- Money printing multiplier: 80x
- Hard cap: 500%
- Only EXCESS above baseline decays (structural baseline persists)

**Engine location:** `world_model_engine.py:854-880`

---

#### 8. Debt Service Update

**Purpose:** Converts deficits into permanent debt burden. Debt burden is subtracted from future revenue, creating a compound fiscal trap.

**Inputs:**
- Current debt burden (accumulated)
- Deficit from this round (from Step 4)

**Formula:**

```
If deficit > 0:
  new_debt = old_debt + deficit * 0.15
Else:
  new_debt = old_debt  (debt never decreases automatically)
new_debt = max(0, new_debt)
```

**Plain English:** Each round's deficit adds 15% of itself to permanent debt burden. A country running a 5-coin deficit per round accumulates 0.75 coins/round in debt service. After 4 rounds: 3.0 coins of permanent drag on revenue. Debt is never automatically reduced -- it persists as a permanent drain.

**Output:** `country.economic.debt_burden`

**Feedback loops:** Debt reduces revenue (Step 3 next round), which increases deficits, which adds more debt. This is the fiscal death spiral. The only way out is running surpluses or growing GDP faster than debt accumulates.

**Engine location:** `world_model_engine.py:886-893`

---

#### 9. Economic State Transitions (Crisis Ladder)

**Purpose:** Manages the four-state crisis ladder: NORMAL, STRESSED, CRISIS, COLLAPSE. Downward transitions are immediate; upward transitions require sustained positive indicators over multiple rounds.

**Inputs:**
- Oil price, oil importer status
- Inflation vs. baseline
- GDP growth rate
- Treasury level, debt burden
- Political stability
- Formosa disruption status and dependency

**Formula:**

```
STRESS TRIGGERS (count):
  oil_price > 150 AND oil importer?          +1
  inflation > baseline + 15?                  +1
  GDP growth < -1%?                           +1
  treasury <= 0?                              +1
  stability < 4?                              +1
  formosa_disrupted AND dependency > 0.3?     +1

CRISIS TRIGGERS (count):
  oil_price > 200 AND oil importer?           +1
  inflation > baseline + 30?                  +1
  GDP growth < -3%?                           +1
  treasury <= 0 AND debt > GDP * 10%?         +1
  disruption_rounds >= 3 AND dep > 0.5?       +1

DOWNWARD TRANSITIONS (immediate):
  normal -> stressed:  if stress_triggers >= 2
  stressed -> crisis:  if crisis_triggers >= 2 (resets crisis_rounds to 0)
  crisis -> collapse:  if crisis_rounds >= 3 AND crisis_triggers >= 2

UPWARD TRANSITIONS (slow):
  collapse -> crisis:  if crisis_triggers == 0 for 3 consecutive rounds
  crisis -> stressed:  if stress_triggers <= 1 for 2 consecutive rounds
  stressed -> normal:  if stress_triggers == 0 for 2 consecutive rounds

RECOVERY RESET:
  If conditions worsen during attempted recovery: recovery_rounds = 0
```

**Plain English:** The economy escalates through four states. Two or more stress triggers push a country from normal to stressed. Two or more crisis triggers push from stressed to crisis. After 3 rounds in crisis with triggers still active, collapse follows. Recovery is deliberately slow: collapse to crisis takes 3 clean rounds, crisis to stressed takes 2, stressed to normal takes 2. Total recovery from collapse to normal: minimum 7 rounds.

**Output:** `country.economic.economic_state`, `crisis_rounds`, `recovery_rounds`

**Feedback loops:** Crisis state amplifies GDP contraction (via crisis multiplier in Step 2), reduces stability (Step 12), and triggers capital flight (Pass 2). This creates a reinforcing doom loop that is hard to escape.

**Engine location:** `world_model_engine.py:899-988`

---

#### 10. Momentum Update (Confidence)

**Purpose:** Tracks economic confidence. Builds slowly, crashes fast. The asymmetry is a core design principle: it takes much longer to build confidence than to destroy it.

**Inputs:**
- GDP growth rate
- Economic state
- Political stability
- Oil price (for importers)
- Formosa disruption
- War entry/exit status (transition detection)

**Formula:**

```
POSITIVE SIGNALS (capped at +0.3/round):
  GDP growth > 2%:     +0.15
  economic state == normal:  +0.15
  stability > 6:       +0.15
  boost = min(0.3, total_positive)

NEGATIVE SIGNALS (NO cap -- crashes are fast):
  economic state == crisis:   -1.0
  economic state == collapse: -2.0
  GDP growth < -2%:           -0.5
  oil_price > $200 (importer):-0.5
  formosa_disrupted (dep>0.3):-0.5
  just entered war this round:-1.0

NEW MOMENTUM:
  momentum = clamp(old + boost + crash, -5.0, +5.0)
```

**Plain English:** Confidence builds at most +0.3 per round but can crash by up to -5.0 per round. A country entering collapse loses -2.0 in one round; recovering to that same level takes at least 7 rounds of perfect conditions (+0.3 max per round). This asymmetry means destruction is approximately 7x faster than recovery.

**Output:** `country.economic.momentum`

**Feedback loops:** Momentum feeds GDP growth (Step 2) via `momentum * 0.01` (up to +/-5% GDP growth effect). Positive momentum improves GDP, which improves stability, which improves momentum further. Negative momentum does the reverse.

**Engine location:** `world_model_engine.py:994-1048`

---

#### 11. Contagion (Cross-Country)

**Purpose:** When major economies enter crisis or collapse, their trade partners absorb GDP hits and momentum drops. Prevents any major economy from collapsing in isolation.

**Inputs:**
- Economic states of all countries
- GDP of all countries (MAJOR_ECONOMY_THRESHOLD = 30.0)
- Trade weights between country pairs (derived from GDP and sector complementarity)

**Formula:**

```
For each country in crisis or collapse with GDP >= 30:
  severity = 1.0 (crisis) or 2.0 (collapse)
  For each trade partner with bilateral_trade_weight > 0.10:
    GDP_hit = severity * trade_weight * 0.02
    partner.GDP *= (1 - GDP_hit)
    partner.GDP = max(0.5, partner.GDP)
    partner.momentum -= 0.3
```

**Plain English:** If a major economy (GDP >= 30 coins) enters crisis, each of its significant trade partners (>10% bilateral trade weight) loses a small percentage of GDP and takes a momentum hit. Collapse is twice as severe as crisis. Small economies do not generate contagion. Contagion is applied after per-country GDP calculations to avoid double-counting.

**Output:** Partner GDP reductions, partner momentum drops

**Feedback loops:** Contagion can cascade: if the contagion hit pushes a second major economy into crisis, that economy generates its own contagion wave in the next round.

**Engine location:** `world_model_engine.py:1054-1090`

---

#### 12. Financial Market Index (Per Country)

**Purpose:** Tracks financial market confidence per country (0-100 scale). Market crashes have mechanical consequences on GDP growth and political support.

**Inputs:**
- GDP growth rate, economic state, stability
- Inflation delta
- Oil price
- Trade partner market indices

**Formula:**

```
POSITIVE DRIVERS:
  GDP growth > 2%:        +3
  economic state normal:   +1
  stability > 6:           +1

NEGATIVE DRIVERS:
  economic state crisis:   -8
  economic state collapse: -15
  inflation > baseline+20: -5
  oil_price > 180:         -3

PARTNER CONTAGION:
  For each trade partner with market_index < 30:
    index -= 3 * partner_weight

BOUNDS:
  market_index = clamp(index, 0, 100)

CONSEQUENCES:
  If market_index < 20: GDP growth -= 3.0%, political support -= 5
  If market_index < 30: GDP growth -= 1.0%, political support -= 2
```

**Trade Partner Weights (hardcoded):**

| Country | Partners (weight) |
|---------|-------------------|
| columbia | cathay(0.6), teutonia(0.3), yamato(0.3), hanguk(0.2), albion(0.2) |
| cathay | columbia(0.6), teutonia(0.4), yamato(0.3), hanguk(0.4), bharata(0.2) |
| teutonia | cathay(0.4), columbia(0.3), gallia(0.3), albion(0.2), freeland(0.2) |
| yamato | columbia(0.3), cathay(0.4), hanguk(0.3) |
| hanguk | cathay(0.5), columbia(0.3), yamato(0.3) |
| bharata | columbia(0.2), cathay(0.3) |

**Engine location:** `world_model_engine.py:1783-1825`

---

#### 13. Dollar Credibility

**Purpose:** Columbia money printing weakens the dollar, making Columbia-imposed sanctions less effective. Creates a trade-off: printing money to fund wars undermines the sanctions weapon.

**Inputs:**
- Columbia's money printed this round
- Current dollar credibility (0-100)

**Formula:**

```
If Columbia printed money this round:
  credibility -= money_printed * 2
Else:
  credibility = min(100, credibility + 1)  (slow natural recovery)

credibility = max(20, credibility)  (floor at 20)

EFFECT ON SANCTIONS:
  In _calc_sanctions_impact:
    total_damage *= dollar_credibility / 100
```

**Plain English:** Each coin Columbia prints erodes dollar credibility by 2 points. Dollar credibility scales sanctions effectiveness linearly. At 50% credibility, all sanctions are half as effective. The floor is 20% (sanctions never become completely useless). Natural recovery is +1 per round when not printing.

**Output:** `ws.dollar_credibility`

**Engine location:** `world_model_engine.py:1868-1886`

---

#### 14. Stability Update (v4 Formula)

**Purpose:** The master formula that determines political stability -- the single most important political variable. Stability below thresholds triggers protests, coups, and regime collapse.

**Inputs:**
- GDP growth rate
- Social spending ratio vs. baseline
- War status (frontline, primary, ally)
- Casualties, territory changes
- War tiredness
- Sanctions level and duration
- Inflation delta from baseline
- Economic state (crisis penalty)
- Mobilization level
- Propaganda boost
- Regime type (democracy/autocracy/hybrid)
- Current stability level

**Formula:**

```
delta = 0.0

POSITIVE INERTIA (only at high stability):
  If 7 <= stability < 9: delta += 0.05

GDP GROWTH (capped contraction penalty):
  If growth > 2%: delta += min((growth - 2) * 0.08, 0.15)
  If growth < -2%: delta += max(growth * 0.15, -0.30)  (cap at -0.30)

SOCIAL SPENDING:
  effectiveness = 1.5 if at_war else 1.0
  If social_ratio >= baseline:     delta += 0.05 * effectiveness
  If social_ratio >= baseline - 5%: delta -= 0.05
  If below that:                   delta -= shortfall * 3

WAR FRICTION:
  If frontline defender:  delta -= 0.10
  If primary combatant:   delta -= 0.08
  If ally:                delta -= 0.05
  delta -= casualties * 0.2
  delta -= territory_lost * 0.4
  delta += territory_gained * 0.15
  delta -= min(war_tiredness * 0.04, 0.40)  (capped)
  If frontline democracy/hybrid: delta += 0.15  (wartime democratic resilience)

SANCTIONS FRICTION:
  delta -= 0.1 * sanctions_level * (0.70 if sanctions_rounds > 4 else 1.0)
  If heavy sanctions (L2+):
    delta -= abs(sanctions_pain / GDP) * 0.8

INFLATION FRICTION (Cal-4: capped at -0.50):
  inflation_delta = current_inflation - starting_inflation
  If delta > 3:  friction -= (inflation_delta - 3) * 0.05
  If delta > 20: friction -= (inflation_delta - 20) * 0.03
  friction = max(friction, -0.50)
  delta += friction

CRISIS STATE PENALTY:
  normal:   +0.00
  stressed: -0.10
  crisis:   -0.30
  collapse: -0.50

MOBILIZATION:
  delta -= mobilization_level * 0.2

PROPAGANDA:
  delta += propaganda_boost

PEACEFUL NON-SANCTIONED DAMPENING:
  If not at war AND not under heavy sanctions AND delta < 0:
    delta *= 0.5  (halved -- peacetime stability is resilient)

AUTOCRACY RESILIENCE:
  If autocracy AND delta < 0:
    delta *= 0.75  (25% more resistant to negative shocks)

SIEGE RESILIENCE:
  If autocracy AND at war AND under heavy sanctions:
    delta += 0.10  (institutional adaptation to siege conditions)

FINAL:
  new_stability = clamp(old_stability + delta, 1.0, 9.0)
```

**Stability Thresholds:**

| Threshold | Stability | Effect |
|-----------|-----------|--------|
| Unstable | < 6 | Coup risk flag activates |
| Protest probable | < 5 | Protest risk flag activates |
| Protest automatic | < 3 | Regime status set to "crisis" |
| Regime collapse risk | < 2 | Revolution check (with support < 20) |
| Failed state | < 1 | (floor -- stability cannot drop below 1.0) |

**Output:** `country.political.stability`

**Feedback loops:** Stability feeds capital flight (Pass 2: 3-8% GDP hit below stability 3), regime status flags, revolution triggers, election outcomes, and political support. Low stability pushes toward crisis state, which further reduces stability.

**Engine location:** `world_model_engine.py:1096-1228`

---

#### 15. Political Support Update

**Purpose:** Tracks how much the population supports the current leadership. Different formulas for democracies vs. autocracies.

**Inputs:**
- GDP growth rate, stability, casualties
- Economic state
- Oil price (for importers)
- Election proximity
- War tiredness
- Regime type

**Formula:**

```
DEMOCRACY / HYBRID:
  delta += (gdp_growth - 2.0) * 0.8
  delta -= casualties * 3.0
  delta += (stability - 6.0) * 0.5
  Crisis penalty:
    stressed: -2.0, crisis: -5.0, collapse: -10.0
  Oil shock (importers, oil > $150):
    delta -= (oil_price - 150) * 0.05
  Election proximity:
    Columbia: -1.0 at R1, -2.0 at R4
    Heartland: -1.5 at R2 and R3
  War tiredness (if > 2):
    delta -= (war_tiredness - 2) * 1.0

AUTOCRACY:
  delta += (stability - 6.0) * 0.8
  delta -= perceived_weakness * 5.0
  delta += repression_effect
  delta += nationalist_rally

ALL REGIMES:
  Mean-reversion toward 50%:
    delta -= (old_support - 50) * 0.05

BOUNDS:
  new_support = clamp(old_support + delta, 5.0, 85.0)
```

**Output:** `country.political.political_support`

**Engine location:** `world_model_engine.py:1234-1296`

---

#### 16. Elections (3 Types)

**Purpose:** Scheduled elections that determine leadership changes, parliament composition, and policy shifts. Elections use a 50/50 blend of AI score and player votes.

**Schedule:**

| Round | Election | Country |
|-------|----------|---------|
| 2 | Columbia midterms | columbia |
| 3 | Heartland wartime | heartland |
| 4 | Heartland wartime runoff | heartland |
| 5 | Columbia presidential | columbia |

**AI Incumbent Score Formula:**

```
econ_perf = gdp_growth * 10.0
stab_factor = (stability - 5) * 5.0
war_penalty = -5.0 per active war involving this country
crisis_penalty:
  stressed: -5, crisis: -15, collapse: -25
oil_penalty (importers, oil > $150):
  -(oil_price - 150) * 0.1

ai_score = clamp(50 + econ_perf + stab_factor + war_penalty + crisis_penalty + oil_penalty, 0, 100)

HEARTLAND SPECIAL:
  territory_factor = -3 per occupied zone (defender)
  ai_score_adjusted = clamp(ai_score + territory_factor - war_tiredness * 2, 0, 100)

FINAL RESULT:
  final_incumbent = 0.5 * ai_score + 0.5 * player_incumbent_pct
  incumbent_wins = final_incumbent >= 50.0
```

**Consequences:**
- Columbia midterms loss: Parliament shifts to 3-2 opposition majority
- Heartland election loss: Beacon loses, Bulwark becomes president
- Columbia presidential loss: New president installed

**Engine location:** `world_model_engine.py:1302-1408`

---

#### 17. Helmsman Legacy Clock

**Purpose:** Cathay's leader (Helmsman) faces political pressure tied to the Formosa question. If Cathay is actively pursuing Formosa and failing, support erodes; if the window closes without action, milder pressure applies.

**Inputs:**
- Round number (activates at R4+)
- Formosa resolved status
- Cathay's active pursuit status (blockade, naval deployment near Formosa, war with Formosa)

**Formula:**

```
If round < 4: no effect
If formosa_resolved: no effect

Active pursuit detection:
  formosa_strait in active_blockades, OR
  taiwan_strait in active_blockades, OR
  formosa_blockade flag, OR
  war involving formosa, OR
  cathay naval deployed near Formosa zones

If pursuing AND unresolved (R4+):
  political_support -= 2.0  (aggressive: failing at key national priority)

If NOT pursuing AND unresolved (R6+):
  political_support -= 1.0  (mild: window closing without action)
```

**Engine location:** `world_model_engine.py:1892-1938`

---

#### 18. Health Events (Elderly Leaders)

**Purpose:** Leaders aged 70+ face probabilistic health events after Round 2. Creates succession crises.

**Inputs:**
- Round number (activates after R2)
- Leader age and medical care quality

**Elderly Leaders:**

| Country | Role | Age | Medical Quality |
|---------|------|-----|----------------|
| columbia | dealer | 80 | 0.9 |
| cathay | helmsman | 73 | 0.7 |
| nordostan | pathfinder | 73 | 0.6 |

**Formula:**

```
base_prob = 0.03 + (age - 70) * 0.01
prob = base_prob * (1 - medical_quality * 0.5)

Example probabilities:
  Columbia (80, 0.9): 0.13 * 0.55 = 7.15% per round
  Cathay (73, 0.7):   0.06 * 0.65 = 3.90% per round
  Nordostan (73, 0.6): 0.06 * 0.70 = 4.20% per round

If health event triggers:
  15% chance: Death (role status = "dead", succession crisis)
  85% chance: Incapacitated for 1-2 rounds (reduced capacity, deputy acts)
```

**Engine location:** `world_model_engine.py:2262-2322`

---

#### 19. Revolution Check

**Purpose:** When stability hits 1-2 AND political support is below 20%, mass protests erupt automatically. An elite participant can choose to lead the protest for a chance at regime change.

**Trigger:**
```
stability <= 2 AND political_support < 20
```

**Protest Severity:**
```
severity = "severe" if stability <= 1, else "major"
```

**Base Success Probability (if elite leads):**
```
prob = 0.30 + (20 - support) / 100 + (3 - stability) * 0.10
prob = clamp(prob, 0.15, 0.80)
```

**Resolution:** Handled by `resolve_protest_action` in the Live Action Engine. See Part 3, item 12.

**Engine location:** `world_model_engine.py:2225-2256`

---

#### 20. Narrative Generation

**Purpose:** Generates a human-readable round briefing summarizing global GDP, oil price, crisis states, active conflicts, top economies, key warnings, and blocked chokepoints.

**Output:** Text string delivered to all players as the round briefing.

**Engine location:** `world_model_engine.py:1703-1765`

---

## Pass 2: AI Contextual Adjustments

These adjustments fire after Pass 1 for each country. Total GDP adjustment is capped at 30% of previous-round GDP.

| Adjustment | Trigger | Effect | Line |
|------------|---------|--------|------|
| Market panic | Just entered crisis/collapse | -5% GDP | 1433-1441 |
| Capital flight (severe) | Stability < 3 | -8% GDP (democracy) or -3% GDP (autocracy) | 1444-1454 |
| Capital flight (mild) | Stability < 4 | -3% GDP (non-autocracy) or -1% GDP (autocracy) | 1455-1466 |
| Ceasefire rally | Was at war, now not | +1.5 momentum | 1470-1479 |
| Sanctions adaptation | sanctions_rounds > 4 | +2% GDP | 1482-1493 |
| Brain drain | Democracy in crisis/collapse | -0.02 AI R&D progress | 1496-1505 |
| War loss shock | Zone captured by enemy | -8% to -15% GDP (random) | 1507-1520 |
| Nuclear R&D pushback | Territory struck | -0.15 nuclear R&D progress | 1522-1537 |
| Tech breakthrough optimism | AI or nuclear level-up | +5% GDP, +0.5 momentum | 1539-1550 |
| Rally around the flag | At war | +max(10 - war_duration * 3, 0) support (diminishing, capped at 30% of current) | 1552-1570 |

---

# PART 3: LIVE ACTION ENGINE (Real-Time During Rounds)

---

#### 1. Ground/Naval Combat (RISK Dice)

**Purpose:** Resolves military engagements between countries in contested zones.

**Mechanics:**

```
COMBAT RESOLUTION:
  pairs = min(attacker_units, defender_ground)
  For each pair:
    attacker_roll = 1d6 + attacker_modifiers
    defender_roll = 1d6 + defender_modifiers
    If attacker_roll > defender_roll: defender loses 1 unit
    Else: attacker loses 1 unit  (DEFENDER WINS TIES)

MODIFIERS:
  Tech bonus (AI level):
    L0-L1: +0, L2: +0, L3: +1, L4: +2
  Morale (from stability):
    morale = max((stability - 5) * 0.5, -2)
  Terrain (defender only):
    home zone: +1
    capital/core zone: +2
  Amphibious penalty (attacker only):
    -1 if amphibious assault

AMPHIBIOUS ASSAULT REQUIREMENTS:
  Force ratio: 3:1 (attacker needs 3x defender's ground units)
  Formosa zone (g_formosa): also 3:1 (reduced from 4:1)
  Naval superiority required in intervening sea zones

UNCONTESTED CAPTURE:
  If defender_ground == 0: zone captured automatically, no combat

ZONE CAPTURE:
  If defender_remaining <= 0 AND attacker_remaining > 0:
    zone ownership transfers to attacker

WAR TIREDNESS:
  Both attacker and defender: +0.5 per combat engagement

LOSSES APPLIED:
  Deducted from both zone forces and country military totals
```

**Engine location:** `live_action_engine.py:82-209`

---

#### 2. Naval Blockade

**Purpose:** Establishes control over chokepoints and sea zones. Two types: naval (requires ships) and ground-based (Gulf Gate special mechanic).

**Mechanics:**

```
GULF GATE GROUND BLOCKADE (special):
  If zone == "cp_gulf_gate" AND country has ground >= 1 on that zone:
    Ground-based blockade established
    AIR STRIKES CANNOT BREAK THIS -- requires ground invasion
    Sets chokepoint_status["gulf_gate_ground"] = "blocked"

STANDARD NAVAL BLOCKADE:
  Requires at least 1 naval unit in the target zone
  Sets chokepoint_status for matching chokepoint to "blocked"
  If zone is not a chokepoint: zone_control blockade
```

**Naval Bombardment (separate action):**
```
  Requires naval units in sea zone adjacent to target land zone
  Each naval unit: 10% chance of destroying one enemy ground unit
  Applied to all non-friendly ground units in target zone
```

**Engine location:** `live_action_engine.py:215-279` (blockade), `live_action_engine.py:854-901` (bombardment)

---

#### 3. Strategic Missile Strike

**Purpose:** Launch strategic missiles at any zone. Three warhead types with escalating consequences. Global alert fires on every launch.

**Mechanics:**

```
PREREQUISITES:
  Launcher must have strategic_missiles > 0
  Nuclear warheads require nuclear_level >= 1
  Consumes 1 missile on launch (even if intercepted)

AIR DEFENSE INTERCEPTION:
  total_AD = sum of all air_defense units in target zone (excluding launcher)
  intercept_attempts = min(total_AD * 3, 5)
  Each attempt: 30% chance of interception
  If intercepted: missile destroyed, no damage, but global alert still fires

WARHEAD TYPES:

  Conventional:
    10% of enemy ground units in zone destroyed (minimum 1)

  Nuclear L1 (tactical):
    Sets nuclear_used_this_sim = True
    50% of enemy ground troops destroyed
    -2 coins from target country treasury
    Affected countries logged

  Nuclear L2 (strategic):
    Sets nuclear_used_this_sim = True
    50% of ALL military units (ground, naval, tactical_air) in zone destroyed
    30% of target country economic capacity destroyed (GDP *= 0.70)
    Leader survival: 1/6 chance of death (dies on roll of 1)
    GLOBAL STABILITY SHOCK: every country loses 2 stability points

GLOBAL ALERT:
  Every missile launch generates a global_alert event
  Logged regardless of interception outcome
```

**Engine location:** `live_action_engine.py:285-457`

---

#### 4. Air Defense Interception

**Purpose:** Passive defense against incoming missiles. Integrated into the missile strike resolution.

**Formula:**
```
intercept_attempts = min(total_AD_units * 3, 5)  (max 5 attempts)
Each attempt: 30% success rate
If any attempt succeeds: missile destroyed
```

**Engine location:** `live_action_engine.py:328-341`

---

#### 5. Nuclear Test

**Purpose:** Signal action confirming nuclear capability. Makes deterrent credible. Not required for tech advancement but has diplomatic consequences.

**Types:**

```
UNDERGROUND:
  Stability cost to tester: -0.2
  Global event logged (detected by intelligence)
  Political support boost: +5 (nationalist rally)
  Sets nuclear_tested = True

OVERGROUND:
  Global stability shock: all countries -0.3 stability
  Stability cost to tester: -0.5 (self-cost on top of global)
  Political support boost: +5 (nationalist rally)
  Sets nuclear_tested = True

PREREQUISITES:
  nuclear_level >= 1
```

**Engine location:** `live_action_engine.py:907-959`

---

#### 6. Covert Operations (5 Types)

**Purpose:** Intelligence actions with success and detection probabilities. Limited per round.

**Base Probability Tables:**

| Operation | Success Base | Detection Base |
|-----------|-------------|----------------|
| Espionage | 60% | 30% |
| Sabotage | 45% | 40% |
| Cyber | 50% | 35% |
| Disinformation | 55% | 25% |
| Election meddling | 40% | 45% |

**Modifiers:**

```
SUCCESS PROBABILITY:
  prob = base + (AI_level * 0.05)
  If intelligence power: +0.05
  Per previous op against same target: -0.05
  prob = clamp(prob, 0.05, 0.95)

DETECTION PROBABILITY:
  detect_prob = detection_base + (prev_ops_against_target * 0.10)
  detect_prob = clamp(detect_prob, 0.10, 0.90)

LIMITS PER ROUND:
  Default countries: 2 ops per round
  Intelligence powers: 3 ops per round
  Intelligence powers: columbia, cathay, levantia, albion, nordostan
```

**Effects on Success:**

| Operation | Effect |
|-----------|--------|
| Espionage | Returns partial intelligence (GDP, stability, military estimates with +/-15% noise) |
| Sabotage | 2% GDP damage to target |
| Cyber | 1% GDP damage to target |
| Disinformation | -0.3 stability, -2 political support |
| Election meddling | -3 political support |

**Engine location:** `live_action_engine.py:463-577`

---

#### 7. Arrest

**Purpose:** Immediately arrest a role on your own soil. Removes them from active play.

**Mechanics:**
```
REQUIREMENTS:
  Target role must be in arresting country (own soil only)

EFFECTS:
  Role status set to "arrested"
  Political support cost:
    Democracy: -3
    Non-democracy: -5 (costlier -- seen as authoritarian)
  Stability cost: -1 (all regimes)
```

**Engine location:** `live_action_engine.py:583-627`

---

#### 8. Fire/Reassign

**Purpose:** Head of state removes a subordinate from their position. Instant power removal.

**Mechanics:**
```
EFFECTS:
  Target role status: "fired"
  All powers removed (powers = [])
  Political support cost: -3
  Stability cost: -0.3

COLUMBIA SPECIAL:
  Parliament must confirm replacement
  If not confirmed: replacement serves as "Acting" official
```

**Engine location:** `live_action_engine.py:965-1017`

---

#### 9. Propaganda

**Purpose:** Spend coins to boost political support. Subject to diminishing returns.

**Formula:**
```
actual_spent = min(coins_requested, treasury)
treasury -= actual_spent

intensity = actual_spent / GDP
boost = ln(1 + intensity * 100) * 3.0
boost = min(boost, 10.0)  (hard cap)

AI TECH BONUS:
  If AI level >= 3: boost *= 1.5

OVERSATURATION PENALTY:
  If actual_spent / GDP > 3%: boost *= 0.5  (halved effectiveness)

political_support += boost  (clamped 0-100)
```

**Engine location:** `live_action_engine.py:633-685`

---

#### 10. Assassination

**Purpose:** Attempt to kill a specific role. High detection probability.

**Formula:**
```
SUCCESS:
  prob = 0.50
  If intelligence power: +0.10
  AI level bonus: +0.03 per level
  Roll: random < prob

SURVIVAL (if assassination "succeeds"):
  Target survives on die roll of 4-6 (50% survival)
  Target dies on roll of 1-3

DETECTION:
  Always 60-80% probability (random uniform)

MARTYR EFFECT (if target dies):
  Target's country: +15 political support
```

**Engine location:** `live_action_engine.py:691-751`

---

#### 11. Coup Attempt

**Purpose:** Forcible seizure of power. Requires at least one plotter with military access.

**Formula:**
```
REQUIREMENTS:
  At least one plotter must be military_chief

SUCCESS PROBABILITY:
  prob = 0.05 (base)
  If stability < 5: prob += (5 - stability) * 0.05
  If support < 40:  prob += (40 - support) / 100 * 0.15
  Per plotter:       prob += 0.05
  If military chief: prob += 0.10
  prob = clamp(prob, 0.0, 0.85)

IF SUCCESSFUL:
  Old head of state: status = "arrested", is_head_of_state = False
  First military plotter becomes new head of state
  Stability: -2
  Political support: -15

IF FAILED:
  All plotters: status = "arrested"
  Stability: -1
```

**Engine location:** `live_action_engine.py:757-848`

---

#### 12. Protest Action (Elite-Led)

**Purpose:** An elite participant leads mass protests. Triggered when revolution check fires (stability <= 2, support < 20), but can also be initiated as an action.

**Formula:**
```
prob = 0.30 + (20 - support) / 100 + max(0, (3 - stability)) * 0.10
prob = clamp(prob, 0.15, 0.80)

IF SUCCESSFUL:
  Old HoS: status = "deposed", is_head_of_state = False
  Protest leader becomes new head of state
  Stability: +1.0 (new hope)
  Political support: +20 (fresh mandate)

IF FAILED:
  Protest leader: status = "imprisoned"
  Stability: -0.5 (more repression)
  Political support: -5 (fear, not loyalty)
```

**Engine location:** `live_action_engine.py:1023-1089`

---

# PART 4: TRANSACTION ENGINE (Real-Time Bilateral)

All transactions require confirmation from both parties. Proposer auto-confirms. Execution is immediate upon double confirmation. All transactions are logged.

---

#### 1. Coin Transfer

**Properties:** Exclusive (sender loses, receiver gains). Requires positive balance. Authorization: head of state. Not reversible.

**Validation:** Amount must be positive. Sender treasury must cover amount.

**Execution:**
```
sender.treasury -= amount
receiver.treasury += amount
```

**Engine location:** `transaction_engine.py:26-31, 272-280`

---

#### 2. Arms Transfer

**Properties:** Exclusive. Requires sufficient units. Authorization: head of state or military chief. Not reversible.

**Mechanics:**
```
sender.military[unit_type] -= count
receiver.military[unit_type] += count
Reduced effectiveness for 1 round (until round_num + 1)
```

**Engine location:** `transaction_engine.py:32-38, 282-294`

---

#### 3. Technology Transfer

**Properties:** Replicable (receiver gains, sender keeps). No balance required. Authorization: head of state.

**Mechanics:**
```
Domains: "ai" or "nuclear"
If sender_level > receiver_level:
  receiver_level = min(receiver_level + 1, sender_level)  (grants +1 level, not full sender level)
Else:
  No advancement
```

**Engine location:** `transaction_engine.py:39-44, 296-313`

---

#### 4. Basing Rights

**Properties:** Replicable. No balance required. Authorization: head of state. UNIQUELY REVERSIBLE by host (unilateral revocation).

**Mechanics:**
```
Stored as: host, guest, zone, granted_round, revoked status
Revocation: host calls revoke_basing_rights (unilateral, no confirmation needed)
```

**Engine location:** `transaction_engine.py:45-50, 315-324, 419-434`

---

#### 5. Treaty/Agreement

**Properties:** Not exclusive. No balance required. Authorization: head of state.

**Treaty:** Stored but NOT mechanically enforced. Political/narrative significance only.

**Agreement:** Has mechanical effects based on subtype.

**Agreement Subtypes:**
```
"ceasefire" or "peace":
  Ends active war between signatories on opposing sides
  War removed from ws.wars list
  Ceasefire event logged

"trade", "alliance", "general":
  Stored for reference, no automatic mechanical effect
```

**Engine location:** `transaction_engine.py:51-63, 326-380`

---

#### 6. Organization Creation

**Properties:** Not exclusive. No balance required. Authorization: head of state.

**Mechanics:**
```
Creates new organization with:
  - Name, purpose, decision_rule (default: consensus)
  - Initial members: sender + receiver
  - Registered in ws.organizations and ws.org_memberships
```

**Engine location:** `transaction_engine.py:64-71, 382-397`

---

#### 7. Personal Transfer (Role-to-Role, Role-to-Country)

**Purpose:** Transfer coins between individual role wallets, or between role wallets and country treasuries.

**Mechanics:**
```
from_type: 'role' (personal wallet) or 'country' (state treasury)
to_type: 'role' or 'country'

Debit source, credit destination
Rollback on destination failure
No authorization check beyond existence
```

**Engine location:** `transaction_engine.py:438-514`

---

# PART 5: STATE VARIABLES REFERENCE

## Per-Country Economic Variables

| Variable | Type | Range | Starting Value | Updated By |
|----------|------|-------|----------------|------------|
| gdp | float | 0.5+ | From CSV | Step 2, Pass 2, Step 11 (contagion) |
| gdp_growth_rate | float | unbounded | From CSV | Step 2 |
| sectors.resources | float | 0-100 | From CSV | -- |
| sectors.industry | float | 0-100 | From CSV | -- |
| sectors.services | float | 0-100 | From CSV | -- |
| sectors.technology | float | 0-100 | From CSV | -- |
| tax_rate | float | 0-1 | From CSV | -- |
| treasury | float | 0+ | From CSV | Step 4, transactions, combat |
| inflation | float | 0-500 | From CSV | Step 7 |
| starting_inflation | float | 0+ | From CSV | Never (baseline reference) |
| trade_balance | float | unbounded | From CSV | -- |
| oil_producer | bool | -- | From CSV | -- |
| opec_member | bool | -- | From CSV | -- |
| opec_production | string | low/normal/high | From CSV | Step 0 |
| formosa_dependency | float | 0-1 | From CSV | -- |
| debt_burden | float | 0+ | From CSV (0) | Step 8 |
| social_spending_baseline | float | 0-1 | From CSV | -- |
| oil_revenue | float | 0+ | 0 | Step 1 |
| inflation_revenue_erosion | float | 0+ | 0 | Step 3 |
| economic_state | string | normal/stressed/crisis/collapse | "normal" | Step 9 |
| momentum | float | -5.0 to +5.0 | 0 | Step 10, Pass 2 |
| crisis_rounds | int | 0+ | 0 | Step 9 |
| recovery_rounds | int | 0+ | 0 | Step 9 |
| sanctions_rounds | int | 0+ | 0 | Step 0 |
| formosa_disruption_rounds | int | 0+ | 0 | Step 0 |
| market_index | int | 0-100 | 50 | Market index update |
| money_printed_this_round | float | 0+ | 0 | Step 4 |
| _actual_social_ratio | float | 0-1 | -- | Step 4 |

## Per-Country Military Variables

| Variable | Type | Range | Starting Value | Updated By |
|----------|------|-------|----------------|------------|
| ground | int | 0+ | From CSV | Step 5, combat, transfers |
| naval | int | 0+ | From CSV (overrides for columbia:11, cathay:7) | Step 5, combat, transfers |
| tactical_air | int | 0+ | From CSV | Step 5, combat |
| strategic_missiles | int | 0+ | From CSV | Step 5 (cathay +1/round), strikes |
| air_defense | int | 0+ | From CSV | -- |
| production_costs.ground | float | -- | From CSV (default 3) | -- |
| production_costs.naval | float | -- | From CSV (default 5) | -- |
| production_costs.tactical_air | float | -- | From CSV (default 4) | -- |
| production_capacity.ground | int | -- | From CSV | -- |
| production_capacity.naval | int | -- | From CSV | -- |
| production_capacity.tactical_air | int | -- | From CSV | -- |
| maintenance_cost_per_unit | float | -- | From CSV (default 0.3) | -- |
| strategic_missile_growth | int | -- | From CSV | -- |
| mobilization_pool | int | 0+ | 0 | Mobilization |

## Per-Country Political Variables

| Variable | Type | Range | Starting Value | Updated By |
|----------|------|-------|----------------|------------|
| stability | float | 1.0-9.0 | From CSV | Step 12 (stability), combat, covert ops, nuclear |
| political_support | float | 5.0-85.0 | From CSV | Step 13, Pass 2, elections, combat, covert ops, propaganda |
| dem_rep_split.dem | float | -- | From CSV | Elections |
| dem_rep_split.rep | float | -- | From CSV | Elections |
| war_tiredness | float | 0-10 | From CSV (0) | War tiredness update |
| regime_type | string | democracy/autocracy/hybrid | From CSV | -- |
| regime_status | string | stable/unstable/crisis | "stable" | Threshold flags |
| protest_risk | bool | -- | False | Threshold flags |
| coup_risk | bool | -- | False | Threshold flags |

## Per-Country Technology Variables

| Variable | Type | Range | Starting Value | Updated By |
|----------|------|-------|----------------|------------|
| nuclear_level | int | 0-3 | From CSV | Step 6 |
| nuclear_rd_progress | float | 0+ | From CSV | Step 6, Pass 2 (pushback) |
| nuclear_tested | bool | -- | True if nuclear_level >= 1 | Nuclear test |
| ai_level | int | 0-4 | From CSV (cathay override: 3) | Step 6 |
| ai_rd_progress | float | 0+ | From CSV (overrides: columbia 0.80, cathay 0.10) | Step 6, Pass 2 (brain drain) |

## Global Variables

| Variable | Type | Range | Starting Value | Updated By |
|----------|------|-------|----------------|------------|
| round_num | int | 0+ | 0 | Orchestrator |
| oil_price | float | 30+ | 80.0 | Step 1 |
| oil_price_index | float | 0+ | 100.0 | Step 1 |
| global_trade_volume_index | float | 0+ | 100.0 | -- |
| nuclear_used_this_sim | bool | -- | False | Nuclear strike |
| dollar_credibility | float | 20-100 | 100.0 | Dollar credibility update |
| formosa_blockade | bool | -- | False | Blockade actions |
| formosa_resolved | bool | -- | False | Treaty/agreement |
| oil_above_150_rounds | int | 0+ | 0 | Step 1 |

## Per-Role Variables

| Variable | Type | Range | Starting Value | Updated By |
|----------|------|-------|----------------|------------|
| status | string | active/arrested/fired/dead/imprisoned/incapacitated/deposed | "active" | Various actions |
| is_head_of_state | bool | -- | From CSV | Elections, coups, protests |
| is_military_chief | bool | -- | From CSV | Fire/reassign |
| personal_coins | float | 0+ | From CSV | Personal transfers, tech investment |
| powers | list | -- | From CSV | Fire (emptied) |
| age | int | -- | From CSV | Health events |

---

# PART 6: KEY PARAMETERS TABLE

| Parameter | Value | Location | What It Affects |
|-----------|-------|----------|-----------------|
| Oil base price | $80 | WME:347 | Starting point for oil price calculation |
| Oil soft cap start | $200 | WME:426 | Asymptotic formula begins |
| Oil soft cap max | ~$250 | WME:429 | Theoretical ceiling |
| Oil floor | $30 | WME:432 | Minimum oil price |
| Oil inertia blend | 40/60 (old/new) | WME:437 | How fast oil price adjusts |
| Oil volatility sigma | 0.05 | WME:441 | Random noise on oil |
| Oil mean-reversion trigger | 3 rounds > $150 | WME:448 | When demand destruction accelerates |
| Oil mean-reversion multiplier | 0.92 | WME:449 | 8% downward pressure |
| OPEC supply impact | +/-0.06 per member | WME:354 | Per-member supply shift |
| Sanctions supply impact | -0.08 per L2+ producer | WME:362 | Supply reduction from sanctions |
| Gulf Gate disruption | +0.50 | WME:371 | Oil disruption multiplier |
| Formosa disruption (oil) | +0.10 | WME:375 | Oil disruption multiplier |
| War premium | +0.05 per war, max 0.15 | WME:419-420 | Oil risk premium |
| Sanctions GDP multiplier | 1.5 | WME:519 | How sanctions damage converts to GDP hit |
| Sanctions adaptation factor | 0.60 after 4 rounds | WME:524 | Diminishing sanctions effectiveness |
| Sanctions coalition threshold | 60% trade weight | WME:1965 | Above = full effectiveness, below = 30% |
| Sanctions damage cap | 50% | WME:1970 | Maximum sanctions damage |
| Oil importer shock | -2% per $50 above $100 | WME:534 | GDP contraction from oil |
| Oil producer benefit | +1% per $50 above $80 | WME:538 | GDP boost from oil |
| Semiconductor severity ramp | 0.3, 0.5, 0.7, 0.9, 1.0 | WME:548 | Duration-scaling disruption |
| Crisis GDP multiplier (growth) | normal:1.0, stressed:0.85, crisis:0.5, collapse:0.2 | WME:69-74 | Dampens positive growth |
| Crisis GDP amplifier (contraction) | normal:1.0, stressed:1.2, crisis:1.3, collapse:2.0 | WME:584-589 | Amplifies negative growth |
| GDP floor | 0.5 coins | WME:595 | Minimum GDP |
| Money printing inflation multiplier | 80x | WME:721,876 | How aggressively printing causes inflation |
| Inflation natural decay | 0.85 on excess | WME:872 | 15% decay per round |
| Inflation hard cap | 500% | WME:879 | Maximum inflation |
| Debt accumulation rate | 15% of deficit | WME:724,892 | Permanent debt burden per round |
| R&D multiplier | 0.8 | WME:90 | Base R&D efficiency |
| Rare earth penalty | 15% per level | WME:2161 | R&D slowdown per restriction level |
| Rare earth floor | 40% | WME:2162 | Minimum R&D factor |
| AI tech GDP boost | L2:+0.5pp, L3:+1.5pp, L4:+3.0pp | WS:39 | Added to GDP growth rate |
| AI combat bonus | L3:+1, L4:+2 | WS:40 | Added to combat dice rolls |
| Momentum build rate | max +0.3/round | WME:1015 | Slow confidence building |
| Momentum crash rate | up to -5.0/round | WME:1017-1035 | Fast confidence destruction |
| Momentum range | -5.0 to +5.0 | WME:1037 | Confidence bounds |
| Contagion GDP threshold | 30.0 coins | WME:84 | Only major economies generate contagion |
| Contagion trade weight threshold | 10% | WME:1067 | Only significant trade partners affected |
| Contagion hit formula | severity * weight * 0.02 | WME:1071 | GDP reduction to partner |
| Stability range | 1.0-9.0 | WME:1224 | Hard bounds |
| Stability GDP cap | -0.30/round | WME:1125 | Max contraction penalty |
| Inflation friction cap | -0.50/round | WME:1194 | Cal-4 cap |
| Crisis stability penalty | stressed:-0.10, crisis:-0.30, collapse:-0.50 | WME:76-81 | Per round |
| Autocracy resilience | 0.75x on negative delta | WME:1217 | 25% resistance |
| Siege resilience | +0.10 | WME:1221 | For sanctioned autocracies at war |
| Peaceful dampening | 0.5x on negative delta | WME:1212 | Peacetime stability resilience |
| War tiredness growth | Defender:+0.20, Attacker:+0.15, Ally:+0.10 | WME:2200-2204 | Per round |
| War tiredness adaptation | 0.5x after 3+ rounds at war | WME:2215 | Society gets used to war |
| War tiredness decay | 0.80x per round at peace | WME:2219 | 20% decay when not at war |
| War tiredness cap | 10.0 | WME:2217 | Maximum |
| Political support range | 5.0-85.0 | WME:1293 | Bounds |
| Election AI/player weight | 50/50 | WME:1346 | Blend for final result |
| Election crisis penalty | stressed:-5, crisis:-15, collapse:-25 | WME:1329-1334 | On AI incumbent score |
| Capital flight (democracy, stab<3) | 8% GDP | WME:1445 | Pass 2 adjustment |
| Capital flight (autocracy, stab<3) | 3% GDP | WME:1445 | Pass 2 adjustment |
| Ceasefire rally | +1.5 momentum | WME:1473 | Pass 2 adjustment |
| Pass 2 GDP adjustment cap | 30% of previous GDP | WME:1577 | Maximum total AI adjustment |
| Amphibious ratio | 3:1 | LAE:57-58 | Attacker needs 3x defenders |
| Combat dice | 1d6 + modifiers | LAE:167-168 | RISK-style |
| Covert op success modifier | +5% per AI level, +5% intelligence power | LAE:497-501 | Added to base probability |
| Covert op detection escalation | +10% per previous op against same target | LAE:520 | Repeated ops more detectable |
| Assassination base probability | 50% | LAE:708 | Before modifiers |
| Assassination survival | 50% (4-6 on d6) | LAE:727 | Even if assassination "succeeds" |
| Coup base probability | 5% | LAE:791 | Before stability/support modifiers |
| Propaganda cap | +10 support max | LAE:661 | Before AI tech multiplier |
| Propaganda AI L3+ multiplier | 1.5x | LAE:665 | 50% more effective |
| Maintenance cost per unit | 0.3 coins | WS:206 | Default per-unit per-round |
| Dollar credibility erosion | -2 per coin printed | WME:1876 | Per round |
| Dollar credibility recovery | +1 per round (not printing) | WME:1879 | Slow recovery |
| Dollar credibility floor | 20 | WME:1881 | Sanctions never fully useless |
| Helmsman legacy penalty (pursuing) | -2 support/round | WME:1927 | After R4, if pursuing Formosa and failing |
| Helmsman legacy penalty (passive) | -1 support/round | WME:1934 | After R6, if not pursuing at all |
| Health event base probability | 3% + 1% per year over 70 | WME:2285 | Reduced by medical quality |
| Health event death rate | 15% of events | WME:2295 | When event triggers |

*WME = world_model_engine.py, WS = world_state.py, LAE = live_action_engine.py, TE = transaction_engine.py*

---

# PART 7: KNOWN LIMITATIONS AND DEFERRED MECHANICS

## Not in the Engine

| Mechanic | Status | Reason |
|----------|--------|--------|
| **Infrastructure damage tracking** | Simplified | Infra damage is approximated by counting occupied zones (0.05 per zone). No per-zone infrastructure state. |
| **Explicit trade flows** | Derived | Trade weights are derived from GDP and sector complementarity, not tracked as explicit bilateral flows. |
| **Supply chain modeling** | Abstracted | Semiconductor disruption uses a single `formosa_dependency` parameter per country. No modeling of individual supply chains. |
| **Currency exchange rates** | Not modeled | Dollar credibility is a simplified proxy. No explicit FX market. |
| **Domestic politics detail** | Simplified | No modeling of legislature dynamics, party politics, or coalition governments beyond Columbia's parliament 3-2 split mechanic. |
| **Climate/environment** | Not included | Outside simulation scope. |
| **Population/demographics** | Not modeled | No population variable. GDP per capita is not tracked. |
| **Technology diffusion** | Simplified | Technology transfer grants exactly +1 level. No gradual diffusion or spillover effects. |
| **Alliance mechanics** | Stored, not enforced | Treaties and organization memberships are tracked but have no automatic mechanical enforcement. Alliance obligations are political, not mechanical. |
| **Intelligence fog of war** | Partial | Espionage returns noisy estimates (+/-15%). No systematic information hiding between players -- deferred to orchestrator/moderator. |
| **Refugee flows** | Not modeled | War and collapse do not generate refugee movements that affect neighboring countries. |
| **Cyber warfare (strategic)** | Simplified | Cyber is one of five covert op types with a flat 1% GDP damage. No modeling of critical infrastructure vulnerability. |
| **Naval combat (fleet battles)** | Not separate | Naval combat is folded into the general RISK dice system. No separate fleet engagement mechanic. |
| **Air superiority** | Implicit | Tactical air units are counted but there is no separate air superiority phase. Air defense only intercepts missiles. |
| **Occupation governance** | Not modeled | Capturing a zone transfers ownership but there are no occupation costs, resistance, or governance mechanics. |
| **Territory liberation** | Manual | No automatic reconquest mechanic. Players must order attacks to retake zones. |
| **Humanitarian crises** | Not modeled | Economic collapse does not generate humanitarian emergencies with mechanical consequences. |
| **Media/public opinion detail** | Propaganda only | Public opinion is modeled as a single `political_support` number. No media ecosystem or information environment simulation. |
| **Personal relationship modifiers** | Stored only | Relationships between roles are loaded from CSV but do not mechanically affect negotiations or actions. |
| **Tariff retaliation automation** | Not automatic | Countries do not automatically retaliate against tariffs. Retaliation is a player decision. |
| **Debt restructuring** | Not possible | No mechanism for debt forgiveness, restructuring, or default. Debt burden is permanent. |

## Simplifications That May Need Revision

1. **Bilateral dependency pairs are hardcoded** (line 482-489). Only 6 pairs are modeled. Trade weight derivation covers all pairs but bilateral dependency is limited to hardcoded majors.

2. **Trade partner weights for market index are hardcoded** (line 1773-1781). Only 6 countries have specific partner weights.

3. **Elderly leader health events are hardcoded** to three specific leaders (line 2273-2277). Adding new elderly leaders requires code changes.

4. **Tech investor roles are hardcoded** (line 2334-2337). Only pioneer/dealer (Columbia) and circuit (Cathay) can make personal tech investments.

5. **Chokepoint-to-blockade mapping is hardcoded** (line 2432-2440). Adding new chokepoints requires code changes.

6. **Columbia oil revenue cap** at 15% of GDP is a special case (line 460-462). No other country has a similar cap.

---

*End of Engine Formula Documentation v1*
*This document is the AUDIT REFERENCE for all TTT engine mechanics.*
