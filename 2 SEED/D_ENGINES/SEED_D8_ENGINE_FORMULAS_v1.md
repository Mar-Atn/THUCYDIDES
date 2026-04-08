# TTT SEED D8 -- Engine Formula Documentation v1

> **RECONCILIATION NOTE (2026-04-07):** This document is the SEED formula specification.
> 98% of formulas match the implemented code exactly (verified 2026-04-06).
> For CURRENT canonical values including BUILD calibration changes, see:
> `PHASES/UNMANNED_SPACECRAFT/CARD_FORMULAS.md`
> Key deltas: AI_LEVEL_TECH_FACTOR L2-L3 given small GDP boosts (deliberate deviation).
> Combat probabilities recalibrated (air strike 12%/6%, assassination 30%/20%).

> **Calibration History:** Updated 2026-04-03 to reflect 104 formula changes from supervised parameter review (F1-F104). Code in `app/engine/engines/` is the authoritative source.

## AUDIT REFERENCE SPECIFICATION

**Purpose:** This document formalizes every formula, mechanic, and state variable in the TTT engine code as a readable, auditable specification. If there is ever a question about how the engine works, this document is the definitive answer.

**Engine files covered:**
- `world_model_engine.py` (v2.0 -- three-pass architecture with feedback loops)
- `live_action_engine.py` (v2.0 -- real-time unilateral actions)
- `transaction_engine.py` (v2.0 -- bilateral transfers)
- `world_state.py` (v2.0 -- shared state model)

**Document version:** 1.2
**Date:** 2026-04-03

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
| 2 | GDP growth | Per country | Oil price delta, sanctions coefficient, tariffs (prisoner's dilemma), war, tech (L4 only), maturity, shock absorption |
| 3 | Revenue | Per country | GDP (from step 2), tax rate, oil revenue, debt, inflation |
| 4 | Budget execution | Per country | Revenue (from step 3), mandatory costs, player allocations |
| 5 | Military production | Per country | Budget (from step 4), production capacity, costs |
| 6 | Technology advancement | Per country | R&D investment, rare earth restrictions |
| 7 | Inflation update | Per country | Money printed (from step 4), GDP |
| 8 | Debt service update | Per country | Deficit (from step 4) |
| 9 | Economic state transitions | Per country | DELEGATED TO AI PASS 2 (crisis state determined by AI, not formula ladder) |
| 10 | Momentum update | Per country | REMOVED from deterministic engine. AI Pass 2 handles. |
| 11 | Contagion | Cross-country | DELEGATED TO AI PASS 2. |
| 12 | Stability update | Per country | GDP growth, social spending, war, inflation delta, regime modifiers, market stress |
| 13 | Political support update | Per country | GDP growth, stability, inflation, regime type |
| -- | Post-steps | Various | Revolution check, health events, market indexes (3 regional), Helmsman legacy, capitulation, elections |

## 1.3 What Is Deterministic vs. AI-Assisted vs. Coherence-Checked

| Category | Examples | Nature |
|----------|----------|--------|
| **Deterministic** | Oil price, GDP, revenue, budget, inflation, debt, stability, political support, market indexes | Pure formulas. Same inputs always produce same outputs. No volatility noise. |
| **AI-Assisted** (Pass 2) | Crisis state (replaces formula ladder), momentum, contagion, market panic, capital flight, ceasefire rally, sanctions adaptation, brain drain, rally-around-flag, capitulation | AI decides crisis state with -1% to -2% GDP penalty. Momentum and contagion delegated entirely. ±0.5 stability, ±5pp support adjustments. |
| **Coherence-Checked** (Pass 3) | GDP growth during crisis forced negative, collapse with high stability flagged, oil shock on growing importers corrected | Auto-fixes implausible states. |

## 1.4 Engine Version History

| Version | Changes |
|---------|---------|
| **v1** | Basic linear model. No feedback loops. No crisis states. |
| **v2** | Feedback loop architecture. Crisis escalation ladder. Momentum. Contagion. Asymmetric recovery. Soft oil cap. Semiconductor duration-scaling. Sanctions diminishing returns. |
| **v2.5 (Cal fixes)** | Cal-1: Oil price inertia (60/40 blend). Cal-2: Sanctions multiplier 2.0 to 1.5; diminishing returns 0.70 to 0.60. Cal-3: Tech boost on growth rate not GDP multiplier. Cal-4: Inflation stability friction capped at -0.50/round. |
| **v3.0 (F1-F104)** | 104 formula changes from supervised parameter review. Oil: floor $15, inertia 30/70, no volatility, demand destruction >$100/3rds, exponent 2.5, OPEC weighted, Gulf-only war premium, mbpd oil revenue. GDP: immutable base, delta-only factors, maturity dampener, shock absorption. Sanctions: complete rebuild as GDP coefficient model (S-curve 0.2→5% to 0.8→80%, MAX_DAMAGE 0.87). Tariffs: prisoner's dilemma model. Budget: social % of GDP, maintenance x3, debt escalating interest. Inflation: printing x60, oil ±3pp/$50. Crisis/momentum/contagion: delegated to AI Pass 2. Market indexes: 3 regional (Wall Street, Europa, Dragon). Stability/support simplified. Elections: base from political_support. Revolution: coup 25%. Tech: L0-L3 no GDP boost, L4 probabilistic. |

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
- OPEC production decisions (per member: "min", "low", "normal", "high", "max") -- weighted by production share with 2x lever
- Sanctions on oil producers (sarmatia, persia) at L2+
- Chokepoint blockade status (Gulf Gate only for war premium)
- Economic states of all countries (demand side)
- GDP growth rates of all countries (demand elasticity)
- Gulf-region wars only (war premium)
- Previous round oil price (inertia)
- Oil above $100 duration counter (demand destruction after 3 rounds)

**Formula:**

```
SUPPLY SIDE (F1-F104: OPEC weighted by production share with 2× lever):
  supply = 1.0
  For each OPEC member:
    weight = member_production_share * 2.0  (production share × 2× lever)
    if decision == "min":  supply -= 0.12 * weight
    if decision == "low":  supply -= 0.06 * weight
    if decision == "high": supply += 0.06 * weight
    if decision == "max":  supply += 0.12 * weight
  For each oil producer (sarmatia, persia):
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

DEMAND DESTRUCTION (F1-F104: >$100 for 3 rounds, exponent 2.5):
  if oil_above_100_rounds >= 3:
    destruction = ((oil_price - 100) / 100) ^ 2.5
    demand *= (1 - destruction)
    demand = max(0.4, demand)

WAR PREMIUM (F1-F104: Gulf-only):
  war_premium = 0.0
  For each active war in Gulf region ONLY:
    war_premium += 0.05
  war_premium = min(war_premium, 0.15)

RAW PRICE:
  raw_price = 80 * (demand / supply) * disruption * (1 + war_premium)

SOFT CAP (asymptotic above $200):
  if raw_price <= 200:
    formula_price = raw_price
  else:
    formula_price = 200 + 50 * (1 - e^(-(raw_price - 200) / 100))
  Theoretical maximum: ~$250

FLOOR (F1-F104: $15, was $30):
  formula_price = max(15, formula_price)

INERTIA (F1-F104: 30/70 blend, was 40/60):
  price = previous_price * 0.30 + formula_price * 0.70

NO VOLATILITY (F1-F104: removed gaussian noise)

FLOOR (final):
  price = max(15, price)
```

**Plain English:** Oil price is driven by supply (OPEC decisions weighted by production share with 2x lever, and sanctions on producers), demand (economic health of major economies), disruption (chokepoint blockades), and Gulf-region war risk only. The price moves 70% toward the new equilibrium each round and 30% sticky from the previous price. Above $200, an asymptotic formula prevents runaway. If oil stays above $100 for three or more rounds, demand destruction kicks in with a 2.5 exponent. Volatility noise has been removed for determinism. Floor is $15.

**Oil Revenue to Producers (F1-F104: mbpd-based formula):**
```
For each oil-producing country:
  oil_revenue = oil_price * country.mbpd * 0.009
  (mbpd = millions of barrels per day, from country data)
```

**Output:** `ws.oil_price`, `ws.oil_price_index` (= price / 80 * 100), per-country `oil_revenue`

**Feedback loops:** Oil price feeds GDP (Step 2) via oil_shock. GDP contraction reduces demand, which moderates oil price next round. Oil revenue feeds budget (Step 4), allowing producers to fund military operations despite sanctions.

**Calibration notes:**
- Inertia blend: 30% previous / 70% new (F1-F104, was 40/60)
- Gulf Gate disruption: +50% (reduced from +80% in v1)
- Soft cap formula: `200 + 50 * (1 - exp(-(raw - 200) / 100))`
- No volatility (removed, was gaussian sigma 0.05)
- Demand destruction: >$100 for 3 rounds, exponent 2.5 (was >$150, linear)
- Floor: $15 (was $30)
- OPEC: weighted by production share with 2x lever (was uniform)
- War premium: Gulf-region wars only (was all wars)
- Oil revenue: mbpd-based `price × mbpd × 0.009` (was GDP-biased)

**Engine location:** `world_model_engine.py:337-474`

---

#### 2. GDP Growth (Per Country)

**Purpose:** Calculates each country's GDP growth rate by summing all additive factors, then applying the crisis state multiplier. GDP is the foundation -- it feeds revenue, budget capacity, military spending power, and political support.

**Inputs:**
- Immutable `gdp_growth_base` (from country data, halved for 6-month rounds)
- Tariff impact (prisoner's dilemma model)
- Sanctions damage (GDP coefficient model)
- Oil price DELTA from starting state (from Step 1)
- Formosa disruption status and duration
- War zones occupied and infrastructure damage
- AI technology level (L0-L3 = 0 boost, L4 probabilistic)
- Maturity dampener (for developed economies)
- Shock absorption (for small economies)
- Blockade fraction
- Bilateral trade dependency
- Crisis state penalty from AI Pass 2 (-1% to -2%)

**Formula:**

```
base_growth = country.gdp_growth_base / 2  (F1-F104: IMMUTABLE base, halved for 6-month rounds)

TARIFF HIT (F1-F104: Complete rebuild — prisoner's dilemma model):
  Imposer hit:
    tariff_hit_imposer = -(imposer_market_power × target_trade_exposure × K)
    where K = 0.54 (calibrated constant)
  Target hit:
    tariff_hit_target = -(target_trade_exposure × imposer_market_power × K)
  Asymmetric: large economy imposing on small = small hurt more, large hurt less
  Customs revenue: imposer gains tariff_revenue = tariff_rate × bilateral_trade_value
  Tariff inflation: applied as LEVEL (not cumulative across rounds)

SANCTIONS HIT (F1-F104: Complete rebuild — GDP coefficient model):
  Recomputed every round (no compounding).
  GDP coefficient range: 0.50 to 1.0 (where 1.0 = no damage, 0.50 = max damage)

  Step A: Calculate coverage
    coverage = SUM over all sanctioning countries of:
      (sanctioner_GDP_share × sanctions_level / 3)

  Step B: Map coverage to effectiveness via S-curve (F1-F104 recalibrated):
    coverage 0.0 →  0% effectiveness
    coverage 0.2 →  5% effectiveness
    coverage 0.4 → 25% effectiveness
    coverage 0.5 → 40% effectiveness
    coverage 0.7 → 70% effectiveness
    coverage 0.8 → 80% effectiveness
    Interpolate linearly between points.
    MAX_DAMAGE = 0.87 (GDP coefficient floor = 0.13)

  Step C: Apply sector vulnerability
    effectiveness *= sector_vulnerability_weight (per target country)

  Step D: GDP coefficient
    gdp_coefficient = 1.0 - (effectiveness * MAX_DAMAGE)
    gdp_coefficient = max(0.13, gdp_coefficient)

  Step E: No compounding — coefficient is absolute, not additive to previous round
  Step F: Lifting sanctions = immediate recovery (coefficient returns toward 1.0)

  No adaptation over time (removed — recomputation handles it).
  No dollar credibility modifier (removed from sanctions).

  Coalition dynamics: West alone ≈ coverage 0.3-0.5 (modest).
  Add swing states (Bharata, Phrygia) ≈ 0.6-0.7 (serious).
  Cathay joins coalition ≈ 0.8-0.9 (devastating).

OIL SHOCK (F1-F104: delta-only — only CHANGES from starting oil price count):
  oil_delta = current_oil_price - starting_oil_price
  If oil importer and oil_delta > 0:
    oil_shock = -0.02 * oil_delta / 50
  If oil producer and oil_delta > 0:
    oil_shock = +0.01 * oil_delta / 50
  If oil_delta <= 0: no shock (return to baseline = no effect)

SEMICONDUCTOR DISRUPTION (duration-scaling — unchanged):
  If Formosa disrupted and country has formosa_dependency > 0:
    severity = min(1.0, 0.3 + 0.2 * max(0, disruption_rounds - 1))
      Round 1: 0.3, Round 2: 0.5, Round 3: 0.7, Round 4: 0.9, Round 5+: 1.0
    tech_sector_pct = sector_technology / 100
    semi_hit = -formosa_dependency * severity * tech_sector_pct

WAR DAMAGE (unchanged):
  war_zones = count of occupied zones in wars involving this country
  infra_damage = occupied_zones * 0.05 per zone (for defenders), capped at 1.0
  war_hit = -(war_zones * 0.03 + infra_damage * 0.05)

TECH FACTOR (F1-F104: L0-L3 = 0, L4 probabilistic):
  AI Level 0:   +0.0pp
  AI Level 1:   +0.0pp
  AI Level 2:   +0.0pp
  AI Level 3:   +0.0pp
  AI Level 4:   probabilistic boost (determined by AI Pass 2)

MOMENTUM EFFECT (F1-F104: REMOVED from deterministic engine):
  Momentum is zeroed in Pass 1. AI Pass 2 handles momentum adjustments.

MATURITY DAMPENER (F1-F104: NEW):
  For developed economies (GDP per capita above threshold):
    growth *= maturity_factor  (reduces base growth for rich countries)

SHOCK ABSORPTION (F1-F104: NEW):
  For small economies (GDP < threshold):
    negative_shocks *= absorption_factor  (small economies absorb shocks less)

BLOCKADE HIT (unchanged):
  blockade_frac = trade-weighted chokepoint disruption fraction
  blockade_hit = -blockade_frac * 0.4

BILATERAL DEPENDENCY (unchanged):
  For each bilateral pair (e.g., columbia-cathay: 15% exposure):
    if partner_growth < 0:
      bilateral_drag += partner_growth * exposure_weight
  bilateral_drag /= 100  (convert to decimal)

AGGREGATE RAW GROWTH:
  raw_growth = base_growth + tariff_hit + sanctions_coefficient_effect + oil_shock
               + semi_hit + war_hit + tech_boost
               + blockade_hit + bilateral_drag

CRISIS PENALTY (F1-F104: delegated to AI Pass 2):
  AI Pass 2 determines crisis state and applies -1% to -2% GDP penalty.
  No deterministic crisis multiplier ladder.

NEW GDP:
  new_gdp = old_gdp * (1 + raw_growth) * sanctions_gdp_coefficient
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

**Feedback loops:** GDP feeds revenue (Step 3), which feeds budget (Step 4), which feeds military capacity, money printing, and inflation. GDP growth feeds stability (Step 12) and political support (Step 13). GDP contraction feeds demand destruction in oil price (Step 1 next round). Crisis state is now determined by AI Pass 2 (not formula ladder).

**Calibration notes:**
- Base growth: immutable `gdp_growth_base`, halved for 6-month rounds (F1-F104)
- Delta-only factors: oil/sanctions/tariffs only count CHANGES from starting state (F1-F104)
- Sanctions: GDP coefficient model 0.50-1.0, no compounding (F1-F104)
- Tariffs: prisoner's dilemma, K=0.54 (F1-F104)
- Tech boost: L0-L3 = 0, L4 probabilistic (F1-F104, was L2:+0.5, L3:+1.5, L4:+3.0)
- Momentum: removed from deterministic engine (F1-F104)
- Crisis multiplier: removed, delegated to AI Pass 2 (F1-F104)
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

oil_revenue = oil_price × country.mbpd × 0.009  (F1-F104: mbpd-based)

debt_service = total_debt × interest_rate  (F1-F104: escalating interest, see Step 8)

inflation_erosion:
  inflation_delta = max(0, current_inflation - starting_inflation)
  inflation_erosion = inflation_delta * 0.03 * GDP / 100

war_damage_cost:
  infra_damage = occupied_zones * 0.05 (capped at 1.0)
  war_damage = infra_damage * 0.02 * GDP

sanctions_cost_on_revenue:
  (F1-F104: sanctions now handled via GDP coefficient in Step 2,
   but remaining direct revenue costs from trade disruption):
  For each sanctioner with sanctions on this country:
    sanc_cost += level * bilateral_trade_weight * 0.015 * GDP

TOTAL REVENUE:
  revenue = base_revenue + oil_revenue - debt_service - inflation_erosion
            - war_damage - sanctions_cost
  revenue = max(0, revenue)
```

**Plain English:** Revenue starts as GDP times tax rate, plus oil windfall (now mbpd-based). Then subtract: (1) debt service with escalating interest rates, (2) inflation erosion based on how far inflation has risen above baseline, (3) war damage costs proportional to occupied territory, and (4) remaining sanctions trade disruption costs. Revenue cannot go below zero.

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
MANDATORY COSTS (F1-F104: maintenance ×3, social as % of GDP × revenue):
  maintenance = total_units * maintenance_cost_per_unit * 3  (F1-F104: ×3 multiplier)
    total_units = ground + naval + tactical_air + strategic_missiles + air_defense
  social_spending = social_pct * revenue  (F1-F104: percentage of GDP applied to revenue)
    where social_pct varies by country type:
      Developed (Columbia, Teutonia, etc.): 15%
      EU members: 20%
      Others: 10%
  mandatory = maintenance + social_spending

DISCRETIONARY:
  discretionary = max(revenue - mandatory, 0)
  military_budget = min(player_military_allocation, discretionary)
  remaining = discretionary - military_budget
  tech_budget = min(player_tech_allocation, remaining)

TOTAL SPENDING:
  total = social_spending + military_budget + tech_budget + maintenance

DEFICIT HANDLING (F1-F104: 50/50 borrowed/printed split):
  If total_spending > revenue:
    deficit = total_spending - revenue
    borrowed = deficit * 0.50  (F1-F104: half is borrowed)
    printed = deficit * 0.50   (F1-F104: half is printed)
    If treasury >= borrowed:
      treasury -= borrowed
    Else:
      printed += borrowed - treasury
      treasury = 0
    money_printed = printed
    inflation += (money_printed / GDP) * 60.0  (F1-F104: 60x multiplier, was 80x)
  Else:
    surplus = revenue - total_spending
    treasury += surplus
    inflation -= 1.0  (F1-F104: surplus reduces inflation by 1pp/round)

OIL REVENUE (F1-F104: mbpd-based, moved from Step 1 for clarity):
  oil_revenue = oil_price × country.mbpd × 0.009

DEBT (F1-F104: % of GDP with escalating interest):
  debt_as_pct_of_gdp = total_debt / GDP
  base_interest = 3%
  If debt_as_pct_of_gdp > 100%:
    excess_pct = (debt_as_pct_of_gdp - 100%) / 20%
    interest_rate = base_interest + (1% × excess_pct)  (escalating: +1% per 20% over 100%)
  debt_service = total_debt × interest_rate

SOCIAL SPENDING RATIO (tracked for stability):
  actual_social_ratio = social_spending / GDP
```

**Plain English:** The government must pay military maintenance (at 3x the per-unit rate) and social spending (a percentage of revenue that varies by country type: 15% developed, 20% EU, 10% others). After that, remaining revenue funds military production and tech R&D. If spending exceeds revenue, the deficit is split 50/50 between borrowing and money printing. Money printing spikes inflation at a 60x multiplier. Surpluses reduce inflation by 1pp/round. Debt accrues escalating interest: 3% base rate, plus 1% for every 20% of GDP above 100% debt-to-GDP ratio.

**Output:** `deficit`, `money_printed`, `new_treasury`, social/military/tech budgets

**Feedback loops:** Money printing feeds inflation (Step 7). Deficit feeds debt burden (Step 8). Debt burden with escalating interest reduces next round's revenue (Step 3). This creates the classic fiscal squeeze, but the 50/50 split and escalating interest replace the old permanent debt accumulation.

**Calibration notes:**
- Money printing inflation multiplier: 60x (F1-F104, was 80x)
- Deficit split: 50% borrowed / 50% printed (F1-F104, was all-or-nothing)
- Social spending: % of GDP × revenue (developed 15%, EU 20%, others 10%) (F1-F104)
- Maintenance: ×3 multiplier (F1-F104, was 1x)
- Oil revenue: mbpd-based `price × mbpd × 0.009` (F1-F104)
- Debt: % of GDP with escalating interest 3% base + 1% per 20% over 100% (F1-F104)
- Surplus: -1pp inflation/round (F1-F104, was no effect)

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

NUCLEAR R&D (F1-F104: Persia starts at 70%. Sabotage -15-20%, bombing -25%):
  progress = (nuc_investment / GDP) * 0.8 * rd_factor
  nuclear_rd_progress += progress
  Thresholds for level-up:
    L0 -> L1: progress >= 0.60
    L1 -> L2: progress >= 0.80
    L2 -> L3: progress >= 1.00
  On level-up: progress resets to 0

  PERSIA SPECIAL (F1-F104): Starts at 70% progress toward L1.
  SABOTAGE EFFECT (F1-F104): Successful sabotage reduces nuclear progress by 15-20%.
  BOMBING EFFECT (F1-F104): Successful bombing reduces nuclear progress by 25%.

AI R&D (F1-F104: Only Columbia + Cathay compete. L4 achievable R7-8 with private investment):
  RESTRICTION: Only Columbia and Cathay can advance AI R&D competitively.
  Other countries can receive tech transfers but cannot independently research.

  speed_multiplier = {normal: 1, accelerated: 2, maximum: 3}[selected_speed]
  cost_this_round = ai_budget_allocation * speed_multiplier
  progress = (cost_this_round / GDP) * 0.8 * rd_factor

  AI PRIVATE INVESTMENT MATCHING (hidden mechanic):
    For AI track ONLY: private sector automatically matches government investment 1:1
    effective_progress = progress * 2.0  (for AI track)
    This is NOT visible to the investing country.
    Other countries can discover it via espionage.
    Nuclear track does NOT get private matching.
    L4 achievable by R7-8 with sustained private investment.

  ai_rd_progress += effective_progress

  Thresholds for level-up (HIDDEN from participants -- they see progress bar, not threshold):
    L0 -> L1: progress >= 0.20
    L1 -> L2: progress >= 0.40
    L2 -> L3: progress >= 0.60
    L3 -> L4: progress >= 1.00
  On level-up: progress resets to 0

  GDP BOOST FROM AI LEVELS (F1-F104: L0-L3 = 0, L4 probabilistic):
    L0-L3: NO GDP boost (was L2:+0.5pp, L3:+1.5pp)
    L4: probabilistic boost determined by AI Pass 2 (was fixed +3.0pp)

ACCELERATION COSTS:
  Normal (1×): standard cost per progress point
  Accelerated (2×): double the budget allocation consumed, double the progress
  Maximum (3×): triple cost, triple progress
  Participants choose speed each round. Higher speed = faster progress but drains budget.
  Breakthrough threshold is intentionally hidden — creates uncertainty and tension.

PERSONAL TECH INVESTMENT (G13):
  For designated tech investor roles (pioneer, dealer for Columbia; circuit for Cathay):
    If role has tech_investment_this_round > 0 and sufficient personal_coins:
      personal_coins -= investment
      progress_boost = (investment / GDP) * 0.4  (50% of normal R&D efficiency)
      ai_rd_progress += progress_boost
```

**Plain English:** R&D investment is converted to progress proportional to investment divided by GDP, multiplied by the R&D multiplier (0.8) and rare earth factor. Only Columbia and Cathay compete in AI R&D; other countries can receive tech transfers. Countries can accelerate R&D at 2x or 3x cost for proportionally faster progress. For AI technology specifically, private sector investment automatically matches government spending -- a hidden mechanic that doubles AI progress (discoverable via espionage). L4 is achievable by R7-8 with sustained private investment. AI levels L0-L3 provide NO GDP boost; L4 provides a probabilistic boost determined by AI Pass 2.

> **BUILD DEVIATION:** Code implements L2: +0.5%, L3: +1.5%, L4: +3.0% fixed. SEED spec said L0-L3 = 0. Kept as deliberate decision (Marat 2026-04-07) because NOUS/Pass 2 not yet available. Persia starts nuclear R&D at 70% progress toward L1. Sabotage reduces nuclear progress by 15-20%, bombing by 25%. Rare earth restrictions from Cathay reduce R&D efficiency. Technology levels advance when accumulated progress crosses a HIDDEN threshold, then progress resets.

**Output:** Updated `nuclear_level`, `nuclear_rd_progress`, `ai_level`, `ai_rd_progress`

**Feedback loops:** Higher AI level feeds GDP growth (via tech_boost in Step 2). Higher GDP means more revenue for R&D investment. Rare earth restrictions create friction in this feedback loop. Private investment matching creates asymmetry between AI and nuclear tracks.

**Calibration notes:**
- R&D multiplier: 0.8 (increased from 0.5)
- AI private matching: 2× effective progress (hidden)
- Rare earth penalty: 15% per level, floor 40%
- Personal investment efficiency: 50% of government R&D (multiplier 0.4 vs 0.8)
- Acceleration: 2× or 3× cost for proportional speed increase

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

MONEY PRINTING SPIKE (F1-F104: 60x, was 80x):
  if money_printed > 0 and GDP > 0:
    new_excess += (money_printed / GDP) * 60.0

OIL IMPACT (F1-F104: NEW — ±3pp per $50):
  oil_delta = current_oil_price - starting_oil_price
  oil_inflation = (oil_delta / 50) * 3.0  (±3pp per $50 change)
  new_excess += max(0, oil_inflation)  (only positive oil changes add inflation)

TARIFF INFLATION (F1-F104: NEW — applied as level, not cumulative):
  tariff_inflation = current_tariff_level_effect  (level-based, not accumulated)
  new_excess += tariff_inflation

SURPLUS EFFECT (F1-F104: NEW):
  If running budget surplus: new_excess -= 1.0  (surplus reduces inflation 1pp/round)

NEW INFLATION:
  new_inflation = baseline + new_excess
  new_inflation = clamp(new_inflation, 0, 500)  (hard cap at 500%)
```

**Plain English:** Inflation has two components. Structural inflation (the starting baseline) never decays. Excess inflation above baseline decays by 15% per round. Money printing adds excess at 60x multiplier (was 80x). Oil price changes add ±3pp per $50 deviation from starting price. Tariff levels contribute to inflation as a level (not cumulative). Budget surpluses reduce inflation by 1pp/round. The hard cap is 500%.

**Output:** `country.economic.inflation`

**Feedback loops:** Inflation feeds inflation erosion in revenue (Step 3), which increases deficit, which causes more printing, which increases inflation further. Inflation also feeds stability via inflation friction (Step 12) and political support.

**Calibration notes:**
- Natural decay: 15% of excess per round (multiplier 0.85)
- Money printing multiplier: 60x (F1-F104, was 80x)
- Oil inflation: ±3pp per $50 deviation (F1-F104, new)
- Tariff inflation: level-based, not cumulative (F1-F104, new)
- Surplus: -1pp/round (F1-F104, new)
- Hard cap: 500%
- Only EXCESS above baseline decays (structural baseline persists)

**Engine location:** `world_model_engine.py:854-880`

---

#### 8. Debt Service Update

**Purpose:** Tracks debt as percentage of GDP with escalating interest rates. Higher debt-to-GDP ratios incur progressively worse interest costs.

**Inputs:**
- Current total debt
- GDP (for debt-to-GDP ratio)
- Deficit from this round (from Step 4)

**Formula (F1-F104: complete rebuild -- % of GDP with escalating interest):**

```
If deficit > 0:
  total_debt += deficit

debt_to_gdp = total_debt / GDP

BASE INTEREST:
  interest_rate = 0.03  (3% base)

ESCALATING INTEREST (above 100% debt-to-GDP):
  If debt_to_gdp > 1.0:
    excess_brackets = (debt_to_gdp - 1.0) / 0.20  (one bracket per 20% over 100%)
    interest_rate += 0.01 * excess_brackets  (+1% per bracket)

DEBT SERVICE:
  debt_service = total_debt * interest_rate

SURPLUS DEBT REDUCTION:
  If surplus > 0:
    total_debt -= surplus  (surpluses reduce debt)
    total_debt = max(0, total_debt)
```

**Plain English:** Debt is tracked as total debt with a debt-to-GDP ratio. Interest starts at 3% but escalates: at 120% debt-to-GDP the rate is 4%, at 140% it is 5%, at 160% it is 6%, etc. This creates accelerating fiscal pressure without the old permanent-drag model. Surpluses can reduce total debt. The escalating interest makes high debt increasingly dangerous but recoverable.

**Output:** `country.economic.debt_burden`, `country.economic.total_debt`

**Feedback loops:** Debt service reduces revenue (Step 3 next round). Higher debt-to-GDP means higher interest, which means larger debt service, which means larger deficits. But surpluses and GDP growth can reverse the spiral.

**Engine location:** `world_model_engine.py:886-893`

---

#### 9. Economic State / Crisis (DELEGATED TO AI PASS 2)

**Purpose:** Determines economic crisis state. **F1-F104: DELEGATED TO AI PASS 2.** The 4-state ladder (normal/stressed/crisis/collapse), all triggers, and all multipliers have been REMOVED from the deterministic engine. AI Pass 2 now decides crisis state based on holistic assessment.

**Previous formula:** REMOVED. The stress triggers, crisis triggers, downward/upward transition rules, and recovery timers are no longer in the deterministic engine.

**Current implementation:**
```
AI Pass 2 evaluates overall economic health (GDP growth, inflation, debt, war,
sanctions, oil) and assigns crisis state.

GDP PENALTY from crisis state (applied by AI Pass 2):
  normal:   0%
  stressed: -1% GDP
  crisis:   -1.5% GDP
  collapse: -2% GDP

No deterministic trigger counts, no recovery timers, no crisis_rounds tracking.
AI has full discretion within the -1% to -2% GDP penalty range.
```

**Plain English:** Crisis state is now an AI judgment call, not a formula. The AI evaluates the full economic picture and assigns a state with a corresponding GDP penalty. This replaces the rigid trigger-counting system with contextual intelligence.

**Output:** `country.economic.economic_state` (set by AI Pass 2)

**Engine location:** AI Pass 2 (was `world_model_engine.py:899-988`)

---

#### 10. Momentum (REMOVED FROM DETERMINISTIC ENGINE)

**F1-F104: REMOVED.** Momentum is no longer computed in the deterministic Pass 1. AI Pass 2 handles all momentum/confidence effects as part of its holistic adjustment.

**Previous formula:** REMOVED. The positive signal caps, negative signal crashes, and asymmetric build/destroy rates are no longer in the deterministic engine.

**Current implementation:**
```
Momentum variable is zeroed in Pass 1.
AI Pass 2 may adjust GDP and stability based on its assessment of
economic confidence, but this is part of the AI's holistic adjustment
(capped at 30% of previous GDP total).
```

**Output:** `country.economic.momentum` (set to 0 in Pass 1, adjusted by AI Pass 2)

**Engine location:** AI Pass 2 (was `world_model_engine.py:994-1048`)

---

#### 11. Contagion (DELEGATED TO AI PASS 2)

**F1-F104: DELEGATED TO AI PASS 2.** The deterministic contagion formula has been removed. AI Pass 2 now handles cross-country economic spillover effects as part of its holistic adjustment.

**Previous formula:** REMOVED. The trade-weight-based GDP hits and momentum drops are no longer computed deterministically.

**Current implementation:**
```
AI Pass 2 evaluates cross-country economic conditions and applies
contagion effects where appropriate. This is part of the AI's holistic
adjustment (capped at 30% of previous GDP total per country).
```

**Plain English:** Contagion is now an AI judgment. The AI can identify when a major economy's distress should spill over to trade partners, but the mechanism is contextual rather than formulaic.

**Output:** AI Pass 2 adjustments to partner GDP

**Engine location:** AI Pass 2 (was `world_model_engine.py:1054-1090`)

---

#### 12. Market Indexes (F1-F104: 3 Regional Indexes)

**Purpose:** Tracks financial market health via 3 regional indexes computed from component country health. Market stress feeds into stability.

**F1-F104: Complete rebuild.** Replaced per-country market index with 3 regional indexes.

**3 Regional Indexes:**

```
WALL STREET INDEX:
  Components: Columbia, Albion, Freeland
  Computed from weighted average of component country health:
    health = f(GDP_growth, inflation_delta, economic_state, stability)
  Each component weighted by GDP share within the index

EUROPA INDEX:
  Components: Teutonia, Gallia, other EU members
  Same health computation, GDP-weighted

DRAGON INDEX:
  Components: Cathay, Hanguk, Yamato, Bharata
  Same health computation, GDP-weighted

HEALTH COMPUTATION (per component country):
  health = base_100
  GDP growth > 2%:        +3
  GDP growth < -2%:       -5
  economic state crisis:  -8
  economic state collapse:-15
  inflation > baseline+20:-5
  stability < 4:          -3

INDEX VALUE:
  index = weighted_average(component_health_scores)
  index = clamp(index, 0, 100)

CONSEQUENCES (feed into stability, Step 12):
  Market stress from regional index feeds stability as a modifier.
  If relevant_regional_index < 30: stability -= 0.3 (market stress)
  If relevant_regional_index < 20: stability -= 0.5 (market crisis)
```

**Engine location:** `world_model_engine.py:1783-1825`

---

#### 13. Dollar Credibility (REMOVED)

**F1-F104: REMOVED.** Dollar credibility has been removed from the engine. Sanctions effectiveness is now determined solely by the GDP coefficient model (see Step 2, Sanctions Hit) without a dollar credibility modifier.

**Previous formula:** REMOVED. The money-printing erosion, natural recovery, and sanctions effectiveness scaling are no longer in the engine.

**Rationale:** The sanctions rebuild as a GDP coefficient model makes dollar credibility redundant. Sanctions effectiveness is determined by coalition coverage and S-curve mapping, not by Columbia's fiscal behavior.

---

#### 14. Stability Update (F1-F104: Simplified)

**Purpose:** The master formula that determines political stability. Stability below thresholds triggers protests, coups, and regime collapse. **F1-F104: Simplified.** Removed sanctions friction and crisis penalty (both delegated to AI Pass 2). Added market stress from regional indexes. AI Pass 2 adds ±0.5.

**Inputs:**
- GDP growth rate
- Social spending ratio
- War status (frontline, primary, ally)
- Casualties, territory changes
- War tiredness
- Inflation delta from baseline
- Market stress (from regional indexes)
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

WAR FRICTION (unchanged):
  If frontline defender:  delta -= 0.10
  If primary combatant:   delta -= 0.08
  If ally:                delta -= 0.05
  delta -= casualties * 0.2
  delta -= territory_lost * 0.4
  delta += territory_gained * 0.15
  delta -= min(war_tiredness * 0.04, 0.40)  (capped)
  If frontline democracy/hybrid: delta += 0.15  (wartime democratic resilience)

SANCTIONS FRICTION: REMOVED (F1-F104: delegated to AI Pass 2)

INFLATION FRICTION (Cal-4: capped at -0.50):
  inflation_delta = current_inflation - starting_inflation
  If delta > 3:  friction -= (inflation_delta - 3) * 0.05
  If delta > 20: friction -= (inflation_delta - 20) * 0.03
  friction = max(friction, -0.50)
  delta += friction

CRISIS STATE PENALTY: REMOVED (F1-F104: delegated to AI Pass 2)

MARKET STRESS (F1-F104: NEW — from regional indexes):
  relevant_index = regional index for this country's region
  If relevant_index < 30: delta -= 0.3  (market stress)
  If relevant_index < 20: delta -= 0.5  (market crisis, replaces <30 penalty)

MOBILIZATION — FINITE DEPLETABLE POOL (unchanged):
  Each country has a mobilization_pool (integer). Once used, units NEVER recover.
  Two options:
    Partial mobilization: deploys HALF of remaining pool (rounded down).
      units_mobilized = floor(mobilization_pool / 2)
      mobilization_pool -= units_mobilized
    Full mobilization: deploys ALL remaining pool.
      units_mobilized = mobilization_pool
      mobilization_pool = 0

  Stability cost varies by country context:
    Democracy at peace:     -1.5 stability
    Democracy at war:       -0.5 stability
    Autocracy (any):        -0.3 stability
    Under active invasion:  -0.2 stability

  Columbia special: mobilization requires parliament approval (narrative, no mechanic).
  Ruthenia and Sarmatia start with PARTIALLY DEPLETED pools (see starting values table below).

  delta -= stability_cost_from_mobilization (per above table)

MILITIA / VOLUNTEER CALL (unchanged):
  Available when: home territory occupied OR at war AND under bombardment
  Produces: 1-3 militia ground units (based on GDP: max(1, min(3, GDP/30)))
  Combat effectiveness: 0.5× (militia units get -1 dice modifier)
  Stability cost: -0.3

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

AI PASS 2 ADJUSTMENT (F1-F104: NEW):
  AI Pass 2 applies ±0.5 stability adjustment based on holistic assessment.

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

#### 15. Political Support Update (F1-F104: Updated)

**Purpose:** Tracks how much the population supports the current leadership. Different formulas for democracies vs. autocracies. **F1-F104: Added inflation impact, GDP for autocracies. Removed crisis penalties. AI Pass 2 adds ±5pp.**

**Inputs:**
- GDP growth rate, stability, casualties
- Inflation (NEW)
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
  Crisis penalty: REMOVED (F1-F104: delegated to AI Pass 2)
  Inflation impact (F1-F104: NEW):
    inflation_delta = current_inflation - starting_inflation
    If inflation_delta > 5: delta -= (inflation_delta - 5) * 0.3
  Oil shock (importers, oil > $150):
    delta -= (oil_price - 150) * 0.05
  Election proximity:
    Columbia: -1.0 at R1, -2.0 at R4
    Ruthenia: -1.5 at R2 and R3
  War tiredness (if > 2):
    delta -= (war_tiredness - 2) * 1.0

AUTOCRACY (F1-F104: added GDP effect):
  delta += (stability - 6.0) * 0.8
  delta += (gdp_growth - 1.0) * 0.5  (F1-F104: NEW — GDP matters for autocracies too)
  delta -= perceived_weakness * 5.0
  delta += repression_effect
  delta += nationalist_rally

ALL REGIMES:
  Mean-reversion toward 50%:
    delta -= (old_support - 50) * 0.05

AI PASS 2 ADJUSTMENT (F1-F104: NEW):
  AI Pass 2 applies ±5pp support adjustment based on holistic assessment.

REVOLUTION CHECK (F1-F104: updated threshold):
  Revolution triggers when: stability <= 2 AND political_support < 20%

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
| 3 | Ruthenia wartime | ruthenia |
| 4 | Ruthenia wartime runoff | ruthenia |
| 5 | Columbia presidential | columbia |

**AI Incumbent Score Formula (F1-F104: base from political_support, not 50):**

```
base = political_support  (F1-F104: starts from current support, was hardcoded 50)
econ_perf = gdp_growth * 10.0
stab_factor = (stability - 5) * 5.0
war_penalty = -5.0 per active war involving this country
oil_penalty (importers, oil > $150):
  -(oil_price - 150) * 0.1

ai_score = clamp(base + econ_perf + stab_factor + war_penalty + oil_penalty, 0, 100)
  (NOTE: crisis_penalty removed — crisis state delegated to AI Pass 2)

COLUMBIA MIDTERMS (F1-F104: 7+7 voters):
  14 total voters: 7 human participants + 7 AI voters
  AI voters vote based on ai_score
  Human participants vote freely

COLUMBIA PRESIDENTIAL (F1-F104: with spoiler candidate):
  Includes spoiler/third-party candidate mechanic
  Spoiler draws votes from both sides based on dissatisfaction

RUTHENIA (F1-F104: 3+2 voters, forced by any 2 players):
  5 total voters: 3 human participants + 2 AI voters
  Election can be FORCED by any 2 players agreeing to call it

FINAL RESULT:
  final_incumbent = 0.5 * ai_score + 0.5 * player_incumbent_pct
  incumbent_wins = final_incumbent >= 50.0
```

**Consequences:**
- Columbia midterms loss: Parliament shifts to opposition majority
- Ruthenia election loss: Beacon loses, Bulwark becomes president
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
| sarmatia | pathfinder | 73 | 0.6 |

**Formula:**

```
base_prob = 0.03 + (age - 70) * 0.01
prob = base_prob * (1 - medical_quality * 0.5)

Example probabilities:
  Columbia (80, 0.9): 0.13 * 0.55 = 7.15% per round
  Cathay (73, 0.7):   0.06 * 0.65 = 3.90% per round
  Sarmatia (73, 0.6): 0.06 * 0.70 = 4.20% per round

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

#### 1. Ground Attack (Updated 2026-03-30 per action review — MAJOR REVISION)

**Purpose:** Resolves military engagements between countries in contested zones. Moderator MUST be present. Both commanders must be available in real-time.

**Mechanics:**

```
COMBAT RESOLUTION:
  NO fog of war — all units visible. Modifiers HIDDEN until after roll.
  Real dice or app dice. Both sides roll. Moderator inputs results.

  pairs = min(attacker_units, defender_ground)
  For each pair:
    attacker_roll = 1d6 + attacker_modifiers
    defender_roll = 1d6 + defender_modifiers
    Attacker needs >= defender + 1 to win (attacker_roll >= defender_roll + 1)
    Ties = DEFENDER HOLDS (defender wins ties)

MODIFIERS (integers only):
  AI Level 4:       +0 to +1 (random, determined ONCE when L4 first reached, fixed thereafter)
  Low morale:       -1 (if country stability <= 3)
  Die Hard:         +1 defender (designated Die Hard units only)
  Amphibious:       -1 attacker (attacking from sea to land)
  Air support:      +1 defender (binary yes/no — any air units in zone = +1, no scaling)
  Fatherland appeal: +1 one-time card. 60% chance of success. If used, risk of -1 stability
                     2 rounds later (delayed political cost)

  REMOVED from previous version:
    - Naval support modifier
    - Militia combat modifier
    - Home territory bonus
    - Capital/core zone bonus
    - Scaled air support (was +0.5 per air unit)
    - Morale formula (replaced by simple Low morale threshold)

SHIPS AS TRANSPORT:
  Ships carry 1 ground unit + up to 2 air units.
  Transport between rounds (Phase B).
  Can attack adjacent land zone from ship position (amphibious).

AMPHIBIOUS ASSAULT:
  -1 modifier to attacker (replaces old 3:1 ratio requirement).
  No force ratio requirement — modifier handles the penalty.

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

#### 2. Blockade (F1-F104: Ship OR ground can block. Full/partial choice.)

**Purpose:** Establishes control over chokepoints and sea zones. **F1-F104: Ship OR ground can block.** Full/partial is a player choice.

**Mechanics:**

```
BLOCKADE ESTABLISHMENT (F1-F104: ship OR ground):
  Chokepoint blockade can be established by:
    - Ground forces on the shore/chokepoint zone, OR
    - Naval units in the adjacent sea zone
  Player chooses full or partial blockade.

  Two levels for ALL blockades:
    PARTIAL blockade: reduces trade throughput by 50%
    FULL blockade: reduces trade throughput by 100%

FORMOSA SPECIAL CASE:
  Partial blockade: Control of Formosa Strait zone only (1 zone).
  Full blockade: Control of 3+ sea zones around the island (encirclement).

  DEBLOCKING FORMOSA:
    1 friendly ship arriving at ANY adjacent sea zone → instant downgrade from
    Full to Partial blockade. Ship doesn't fight — mere presence suffices.
    Breaking full blockade entirely: destroy ALL military units at chokepoint
    zones, OR blocker lifts voluntarily.

BREAKING ANY BLOCKADE:
  Destroy ALL ground units at the chokepoint zone (ground attack required).
  OR blocker lifts voluntarily.
  Air strikes alone CANNOT break a ground blockade.
```

**Naval Bombardment (separate action — no change):**
```
  Requires naval units in sea zone adjacent to target land zone
  Each naval unit: 10% chance of destroying one enemy ground unit
  Applied to all non-friendly ground units in target zone
```

**Engine location:** `live_action_engine.py:215-279` (blockade), `live_action_engine.py:854-901` (bombardment)

---

#### 3. Strategic Missile / Nuclear Strike (Updated 2026-03-30 per action review — 5-tier system + 10-minute clock)

**Purpose:** Launch strategic missiles at any zone. Five escalation tiers from test to massive nuclear strike. SIM enters SPECIAL MODE during nuclear events with a 10-minute real-time clock.

**5-Tier Escalation System:**

```
TIER 1 — SUBSURFACE NUCLEAR TEST:
  Signal action. Confirms capability. Detected only by intelligence services (L3+).
  No damage. Political/diplomatic consequences only.
  Sets nuclear_tested = True.
  Political support boost: +5 (nationalist rally).
  Stability cost to tester: -0.2.

TIER 2 — OPEN NUCLEAR TEST:
  Global event. Everyone knows immediately.
  No damage. Maximum political signal.
  Global stability shock: all countries -0.3 stability.
  Stability cost to tester: -0.5 (self-cost on top of global).
  Political support boost: +5 (nationalist rally).
  Sets nuclear_tested = True.

TIER 3 — CONVENTIONAL MISSILE STRIKE:
  Consumes 1 strategic missile.
  10% of enemy ground units in zone destroyed (minimum 1).
  Global alert fires. Detected by all.

TIER 4 — SINGLE NUCLEAR STRIKE:
  Consumes 1 strategic missile. Requires nuclear_level >= 1.
  Sets nuclear_used_this_sim = True.
  50% of enemy ground troops in zone destroyed.
  -2 coins from target country treasury.
  Affected countries logged.
  TRIGGERS 10-MINUTE AUTHORIZATION CLOCK (see below).

TIER 5 — MASSIVE NUCLEAR STRIKE:
  Consumes multiple strategic missiles. Requires nuclear_level >= 2.
  Sets nuclear_used_this_sim = True.
  50% of ALL military units (ground, naval, tactical_air) in zone destroyed.
  30% of target country economic capacity destroyed (GDP *= 0.70).
  Leader survival: 1/6 chance of death (dies on roll of 1).
  GLOBAL STABILITY SHOCK: every country loses 2 stability points.
  TRIGGERS 10-MINUTE AUTHORIZATION CLOCK (see below).

AIR DEFENSE INTERCEPTION (Tiers 3-5):
  total_AD = sum of all air_defense units in target zone (excluding launcher)
  intercept_attempts = min(total_AD * 3, 5)
  Each attempt: 30% chance of interception
  If intercepted: missile destroyed, no damage, but global alert still fires

10-MINUTE CLOCK MECHANIC (Tiers 4-5):
  SIM enters SPECIAL MODE on nuclear launch.
  Phase 1 — Authorization (see Part 6F for per-country chains).
  Phase 2 — 10-minute flight time after successful launch.
  During flight time:
    Nuclear or conventional? UNKNOWN until impact. Nobody knows warhead type.
    Detected by: L2+ intelligence services detect missile launches.
  Response options during flight (target and allies):
    - Intercept: coalition air defense (if available at target zone)
    - Counter-launch: launch own missiles in retaliation
    - Massive counter-attack: full nuclear response
    - Do nothing: absorb the strike
  After 10 minutes: impact. Warhead type revealed. Effects applied.

DETECTION TIERS:
  Subsurface test: detected by L3+ intelligence only.
  Open test: detected by everyone (global event).
  Missile launches (Tier 3-5): detected by L2+ intelligence services.

GLOBAL ALERT:
  Every missile launch (Tier 3+) generates a global_alert event.
  Logged regardless of interception outcome.
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

**(Updated 2026-03-30 per action review)** Now covered as Tier 1 (subsurface) and Tier 2 (open) in the 5-tier missile/nuclear system above (Section 3). See Tier 1 and Tier 2 for complete formulas. Retained here for backward reference.

**Engine location:** `live_action_engine.py:907-959`

---

#### 6. Intelligence System (Updated 2026-03-30 per action review — MAJOR REVISION, renamed from "Covert Operations")

**Purpose:** Intelligence requests and covert operations. Intelligence is now a per-individual resource pool, not a per-country limit.

---

**6A. Intelligence Requests**

```
POOL: Per INDIVIDUAL role (not per country). Pool sizes vary by role type:
  Intelligence chief:    6-8 requests per game
  Head of State:         3-4 requests per game
  Military chief:        2-3 requests per game
  Foreign affairs:       2-3 requests per game
  Other roles with access: 1-2 requests per game

ACCESS: ANY role with intelligence access can submit requests (not just HoS/intel chief).

ALWAYS RETURNS AN ANSWER — never "failed, no info."

ACCURACY TIERS:
  Hard facts (GDP, military count, sanctions level):     85-90% accuracy
  Diplomatic secrets (private agreements, intentions):   70% accuracy
  Strategic intentions (what will they do next round?):  50-60% accuracy
  Aggressive/impractical requests (e.g., "will they use nukes?"): 40% accuracy

WRONG ANSWERS LOOK IDENTICAL TO RIGHT ONES. No way to tell from the report itself.

DELIVERY: Reports arrive in 5-10 minutes as styled classified artefacts.

CROSS-CHECKING: Same question submitted through DIFFERENT intelligence services
  (e.g., Columbia CIA + Albion MI6) can be compared. If answers agree, higher confidence.
  If they disagree, one is wrong — but which one?

TRADEABLE: Intelligence requests can be sold/traded between roles as a service.
  Pay someone to use their pool on your behalf.
```

---

**6B. Sabotage**

```
POOL: 2-3 cards per game per eligible role (separate from intelligence pool)
TARGET TYPES: Military target / Economic target / Technology target
SUCCESS: 40% base + AI tech bonus (+5% per AI level) + intel chief bonus (+10%)
RESULT: Success/failure only — binary outcome.
  Military target: destroy 1-2 units
  Economic target: -2% GDP
  Technology target: -0.1 R&D progress (AI or nuclear)
ATTRIBUTION: Results revealed publicly at Phase B world update (no attribution).
  Hidden unless discovered through intelligence request or leak.
```

---

**6B-2. Proxy Terrorist Attack (replaces Sabotage for Persia roles + Solaria)**

```
PURPOSE: Replaces sabotage mechanic for Persia roles (Furnace, Anvil) and Solaria (Wellspring).
  These countries use proxy/militia networks instead of direct sabotage operations.
  Same underlying mechanic as Sabotage but flavored as proxy terrorism.

POOL:
  Furnace: 2 cards per game
  Anvil: 3 cards per game
  Wellspring: 1 card per game

DETECTION: 30% base (lower than sabotage — proxy attacks are harder to attribute)
TARGET TYPES: Military target / Economic target / Infrastructure target
SUCCESS: 40% base + intel chief bonus (+10%)
RESULT: Success/failure — binary outcome.
  Military target: destroy 1-2 units
  Economic target: -2% GDP
  Infrastructure target: -0.5 stability in target country

ATTRIBUTION: Results revealed publicly at Phase B world update.
  30% detection probability (vs. 40% for standard sabotage).
  If detected: -5% political support for sponsoring country, diplomatic crisis event.

NOTE: Proxy attack cards replace sabotage_cards for these roles in roles.csv.
  These roles do NOT have standard sabotage — proxy attack IS their sabotage equivalent.
```

---

**6C. Cyber Attack**

```
POOL: 2-3 cards per game per eligible role
SUCCESS: 50% base. AI tech level critical (+10% per AI level).
EFFECTS (choose one):
  Steal coins: 1-2 coins from target treasury
  Reduce military production: -1 production capacity next round
  Undermine GDP: -1% GDP
LOW IMPACT, SCARCE CARDS. Harassment tool, not decisive weapon.
```

---

**6D. Disinformation**

```
POOL: 2-3 cards per game per eligible role
SUCCESS: 55% base (easiest covert op)
EFFECTS:
  Target political support: -3%
  Target stability: -0.3
ATTRIBUTION: Very hard to trace (~60% attribution accuracy even with investigation).
  Best covert op for deniability.
```

---

**6E. Election Meddling**

```
POOL: 1 card per game (one-shot)
WORKS WITH OR WITHOUT ELECTION:
  If election upcoming: affects vote outcome (2-5% swing)
  If no election: affects political support/attitude of target country
CHOOSE: Target country + who to support/work against
IMPACT: 2-5% on election result or political support
RISK: Exposure damages the candidate you tried to help (backlash effect).
  Detection probability: 45% base + 10% per previous op against same target.
```

**Engine location:** `live_action_engine.py:463-577`

---

#### 7. Arrest (Updated 2026-03-30 per action review — SIMPLIFIED)

**Purpose:** Immediately arrest a role on your own soil. Removes them from active play. Moderator must be present.

**Mechanics:**
```
REQUIREMENTS:
  Target role must be in arresting country (own soil only)
  Order submitted in app, moderator executes physically

EFFECTS:
  Role status set to "arrested"
  Target is OUT OF PLAY until released.

  NO stability or support cost. Pure player-removal mechanic.

  Democracy: AI Court convenes between rounds (see Court mechanic, Part 6H).
    Arrested player can submit arguments. Court can order release.
  Autocracy: Indefinite detention. No court. Only HoS can release.
```

**Engine location:** `live_action_engine.py:583-627`

---

#### 8. Fire/Reassign (Updated 2026-03-30 per action review — no cost)

**Purpose:** Head of state removes a subordinate from their position. Instant power removal. Moderator must be present.

**Mechanics:**
```
EFFECTS:
  Target role status: "fired"
  All powers removed (powers = [])
  Person STAYS IN PLAY (unlike arrest — they can still talk, negotiate, plot).
  NO stability or support cost.

COLUMBIA SPECIAL:
  Parliament must CONFIRM the firing.
  Parliament can BLOCK the firing.
  If blocked: replacement serves as "Acting" official (reduced powers).
```

**Engine location:** `live_action_engine.py:965-1017`

---

#### 9. Propaganda (Updated 2026-03-30 per action review — diminishing returns emphasis)

**Purpose:** Spend coins to boost political support. Diminishing returns like a drug — first dose is powerful, repeated use less so.

**Formula:**
```
actual_spent = min(coins_requested, treasury)
treasury -= actual_spent

BASE EFFECT:
  1 coin: +2-3% political support
  Cap: +10% total from propaganda (hard cap across all rounds)

AI TECH BONUS:
  If AI level >= 3: boost *= 1.5  (50% more effective)

OVERSATURATION (diminishing returns):
  Track total_propaganda_spent across all rounds.
  Each subsequent use is less effective:
    1st use: full effect
    2nd use: 80% effect
    3rd use: 60% effect
    4th+ use: 40% effect

political_support += boost  (clamped 0-100)
```

**Engine location:** `live_action_engine.py:633-685`

---

#### 10. Assassination (Updated 2026-03-30 per action review — per-country probabilities)

**Purpose:** Attempt to kill a specific role. 1 card per game per eligible role. No AI or intel modifiers — raw probability only.

**Formula:**
```
POOL: 1 card per game per eligible role

SUCCESS PROBABILITY (varies by target location):
  Domestic assassination: 60% hit
  International assassination (default): 20% hit
  International — Levantia: 50% hit (Mossad capability)
  International — Sarmatia: 30% hit

  NO AI or intelligence modifiers. Raw probability only.

HIT RESOLUTION (if assassination "succeeds"):
  50/50 kill or survive:
    Die roll 1-3: target KILLED
    Die roll 4-6: target SURVIVES (injured + martyr effect)

MARTYR EFFECT (if target dies OR survives injured):
  Target's country: +15 political support (sympathy/rally)

INTERNATIONAL EXPOSURE:
  If international assassination FAILS: higher chance of being revealed.
  Detection: 70% for failed international (vs 40% for domestic).
```

**Engine location:** `live_action_engine.py:691-751`

---

#### 11. Coup Attempt (Updated 2026-03-30 per action review — trust mechanic)

**Purpose:** Forcible seizure of power. Any two roles within the same country can attempt. The TRUST MECHANIC is the real game.

**Formula:**
```
INITIATION:
  Any role names a co-conspirator from the same country.
  5-minute window for co-conspirator response.

CO-CONSPIRATOR OPTIONS:
  1. ACCEPT — coup proceeds to probability check
  2. REJECT SILENTLY — coup fails, no one else knows (initiator exposed to co-conspirator only)
  3. BETRAY — initiator is ARRESTED IMMEDIATELY. Co-conspirator gains trust with ruler.

IF BOTH ACCEPT — PROBABILITY CHECK (F1-F104: base 25%, was 15%):
  prob = 0.25 (F1-F104: base — was 0.15)
  If active protest underway:  prob += 0.25 (protest as cover/catalyst)
  If stability < 5:           prob += (5 - stability) * 0.05
  If support < 40:            prob += (40 - support) / 100 * 0.15
  prob = clamp(prob, 0.25, 0.85)

  NOTE: Military chief NOT required (was required before).
  Trust between players IS the mechanic. No special role bonuses.

IF SUCCESSFUL:
  Old head of state: status = "arrested", is_head_of_state = False
  Initiator becomes new head of state
  Stability: -2
  Political support: -15

IF FAILED:
  Both plotters: EXPOSED. Ruler and world learn their identities.
  Both plotters: status = "arrested" (at ruler's discretion)
  Stability: -1
```

**Engine location:** `live_action_engine.py:757-848`

---

#### 12. Protest (Updated 2026-03-30 per action review — automatic + stimulated)

**Purpose:** Protests can be AUTOMATIC (engine checks conditions each round) or STIMULATED (one-time card). Public event visible to all.

**Automatic Protests (F1-F104: auto-trigger from conditions):**
```
Protests auto-trigger based on political conditions.
Engine checks political_support each round:
  Support > 60%:   protest FIZZLES (no effect)
  Support 40-60%:  MODEST protest. Stability -0.5.
  Support < 40%:   MASSIVE protest. Stability -1.5. Coup bonus +25%.

Automatic protests are a PUBLIC EVENT — all countries see it.
```

**Stimulated Protest (1-time card, covert action):**
```
POOL: 1 card per game per eligible role
EFFECT: +20% probability of protest occurring next round in target country.
  Stacks with automatic conditions.
```

**Elite-Led Protest (revolution mechanic — F1-F104: revolution = player leads, capitulation to AI Pass 2):**
```
Triggered when: stability <= 2 AND support < 20 (revolution check)
An elite participant can CHOOSE to lead the protest.
Revolution requires a PLAYER to lead it (not automatic).
Capitulation decisions delegated to AI Pass 2.

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

#### 5a. Bilateral Relationship Status — 8-State Model (added 2026-04-08)

The `relationships` table tracks bilateral state with two columns:
- **`relationship`** — starting/reference value (frozen per template)
- **`status`** — live engine state (updated during play). Engine reads `status` for all war/peace checks.

**Canonical 8-state enum for `status`:**

| State | Meaning | Transitions |
|---|---|---|
| **allied** | Formal alliance, mutual defense | → friendly (dissolved) |
| **friendly** | Positive, no formal treaty | → allied (treaty), → neutral (drift) |
| **neutral** | No alignment | → friendly (cooperation), → tense (friction) |
| **tense** | Friction, pressure | → hostile (escalation), → neutral (de-escalation) |
| **hostile** | Antagonism, sanctions | → military_conflict (attack), → tense (de-escalation) |
| **military_conflict** | Active combat — STICKY | → armistice (ceasefire), → peace (treaty) ONLY |
| **armistice** | Ceasefire signed | → peace (treaty), → military_conflict (breach) |
| **peace** | War formally ended | → friendly (over time), → neutral |

**Key rules:**
- `military_conflict` is STICKY — only exits via signed agreement.
- Armistice breach → auto-return to `military_conflict` + global notification.
- War is DETECTED from combat, not declared.
- Ceasefire/peace agreements (§5 above) update `status` from `military_conflict` → `armistice` or `peace`.

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
| opec_production | string | min/low/normal/high/max | From CSV | Step 0 |
| formosa_dependency | float | 0-1 | From CSV | -- |
| debt_burden | float | 0+ | From CSV (0) | Step 8 |
| social_spending_baseline | float | 0-1 | From CSV | -- |
| oil_revenue | float | 0+ | 0 | Step 1 |
| inflation_revenue_erosion | float | 0+ | 0 | Step 3 |
| economic_state | string | normal/stressed/crisis/collapse | "normal" | AI Pass 2 (F1-F104: delegated) |
| momentum | float | -5.0 to +5.0 | 0 | AI Pass 2 (F1-F104: removed from Pass 1) |
| crisis_rounds | int | 0+ | 0 | AI Pass 2 (F1-F104: delegated) |
| recovery_rounds | int | 0+ | 0 | AI Pass 2 (F1-F104: delegated) |
| sanctions_rounds | int | 0+ | 0 | Step 0 |
| formosa_disruption_rounds | int | 0+ | 0 | Step 0 |
| market_index | int | 0-100 | 50 | 3 regional indexes: Wall Street, Europa, Dragon (F1-F104) |
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
| mobilization_pool | int | 0+ | Per country (see Part 6G) | Mobilization (finite, depletable) |

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
| oil_price | float | 15+ (F1-F104, was 30+) | 80.0 | Step 1 |
| oil_price_index | float | 0+ | 100.0 | Step 1 |
| global_trade_volume_index | float | 0+ | 100.0 | -- |
| nuclear_used_this_sim | bool | -- | False | Nuclear strike |
| dollar_credibility | float | -- | -- | REMOVED (F1-F104) |
| formosa_blockade | bool | -- | False | Blockade actions |
| formosa_resolved | bool | -- | False | Treaty/agreement |
| oil_above_100_rounds | int | 0+ | 0 | Step 1 (F1-F104: was oil_above_150_rounds) |

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
| Oil floor | $15 (F1-F104, was $30) | WME:432 | Minimum oil price |
| Oil inertia blend | 30/70 (old/new) (F1-F104, was 40/60) | WME:437 | How fast oil price adjusts |
| Oil volatility | REMOVED (F1-F104) | -- | No random noise |
| Oil demand destruction trigger | 3 rounds > $100 (F1-F104, was >$150) | WME:448 | Exponent 2.5 (was linear) |
| Oil OPEC weighting | production share × 2× lever (F1-F104) | WME:354 | Weighted by production share |
| Oil war premium | Gulf-region wars only (F1-F104) | WME:419 | Was all wars |
| Oil revenue formula | price × mbpd × 0.009 (F1-F104) | WME:new | mbpd-based, was GDP-biased |
| OPEC supply impact | min:-0.12, low:-0.06, high:+0.06, max:+0.12 × production_share × 2 (F1-F104) | WME:354 | Weighted by production share with 2× lever |
| Sanctions supply impact | -0.08 per L2+ producer | WME:362 | Supply reduction from sanctions |
| Gulf Gate disruption | +0.50 | WME:371 | Oil disruption multiplier |
| Formosa disruption (oil) | +0.10 | WME:375 | Oil disruption multiplier |
| War premium | +0.05 per war, max 0.15 | WME:419-420 | Oil risk premium |
| Sanctions model | GDP coefficient 0.50-1.0 (F1-F104: complete rebuild) | WME:new | Recomputed every round, no compounding |
| Sanctions S-curve | 0.2→5%, 0.4→25%, 0.5→40%, 0.7→70%, 0.8→80% (F1-F104) | WME:new | Recalibrated coverage-to-effectiveness |
| Sanctions MAX_DAMAGE | 0.87 (F1-F104) | WME:new | GDP coefficient floor = 0.13 |
| Sanctions sector vulnerability | per-country weighting (F1-F104) | WME:new | Sector-specific damage |
| Sanctions lifting | immediate recovery (F1-F104) | WME:new | Coefficient returns toward 1.0 |
| Dollar credibility | REMOVED (F1-F104) | -- | No longer modifies sanctions |
| Tariff model | prisoner's dilemma: imposer_market_power × target_trade_exposure × K(0.54) (F1-F104) | WME:new | Asymmetric, with customs revenue |
| Oil importer shock | -2% per $50 above $100 | WME:534 | GDP contraction from oil |
| Oil producer benefit | +1% per $50 above $80 | WME:538 | GDP boost from oil |
| Semiconductor severity ramp | 0.3, 0.5, 0.7, 0.9, 1.0 | WME:548 | Duration-scaling disruption |
| Crisis GDP multiplier | REMOVED (F1-F104: delegated to AI Pass 2) | -- | Was direction-aware multiplier ladder |
| GDP floor | 0.5 coins | WME:595 | Minimum GDP |
| Money printing inflation multiplier | 60x (F1-F104, was 80x) | WME:721,876 | How aggressively printing causes inflation |
| Inflation natural decay | 0.85 on excess | WME:872 | 15% decay per round |
| Inflation oil impact | ±3pp per $50 (F1-F104, new) | WME:new | Oil price change → inflation |
| Inflation tariff | level-based, not cumulative (F1-F104, new) | WME:new | Tariff level → inflation |
| Inflation surplus effect | -1pp/round (F1-F104, new) | WME:new | Surplus reduces inflation |
| Inflation hard cap | 500% | WME:879 | Maximum inflation |
| Deficit split | 50% borrowed / 50% printed (F1-F104) | WME:new | Was all-or-nothing |
| Debt model | % of GDP, escalating interest (F1-F104) | WME:new | 3% base + 1% per 20% over 100% |
| Social spending | % of GDP × revenue: dev 15%, EU 20%, other 10% (F1-F104) | WME:new | Was 70/30 mandatory/discretionary |
| Maintenance multiplier | ×3 (F1-F104) | WME:new | Was ×1 |
| R&D multiplier | 0.8 | WME:90 | Base R&D efficiency |
| Rare earth penalty | 15% per level | WME:2161 | R&D slowdown per restriction level |
| Rare earth floor | 40% | WME:2162 | Minimum R&D factor |
| AI tech GDP boost | L0-L3: 0, L4: probabilistic (F1-F104) | WS:39 | Was L2:+0.5, L3:+1.5, L4:+3.0 |
| AI combat bonus | L4: +0 or +1 (random, fixed once) | WS:40 | Determined once when L4 reached (updated 2026-03-30) |
| Momentum | REMOVED from Pass 1, AI Pass 2 handles (F1-F104) | -- | Was max +0.3/-5.0 per round |
| Contagion | DELEGATED to AI Pass 2 (F1-F104) | -- | Was severity × weight × 0.02 |
| Market indexes | 3 regional: Wall Street, Europa, Dragon (F1-F104, new) | WME:new | Component country health → stability |
| Stability range | 1.0-9.0 | WME:1224 | Hard bounds |
| Stability GDP cap | -0.30/round | WME:1125 | Max contraction penalty |
| Inflation friction cap | -0.50/round | WME:1194 | Cal-4 cap |
| Crisis state | DELEGATED to AI Pass 2, -1% to -2% GDP penalty (F1-F104) | -- | Was 4-state ladder with trigger counts |
| Market stress on stability | index<30: -0.3, index<20: -0.5 (F1-F104, new) | WME:new | Regional index → stability |
| Autocracy resilience | 0.75x on negative delta | WME:1217 | 25% resistance |
| Siege resilience | +0.10 | WME:1221 | For sanctioned autocracies at war |
| Peaceful dampening | 0.5x on negative delta | WME:1212 | Peacetime stability resilience |
| War tiredness growth | Defender:+0.20, Attacker:+0.15, Ally:+0.10 | WME:2200-2204 | Per round |
| War tiredness adaptation | 0.5x after 3+ rounds at war | WME:2215 | Society gets used to war |
| War tiredness decay | 0.80x per round at peace | WME:2219 | 20% decay when not at war |
| War tiredness cap | 10.0 | WME:2217 | Maximum |
| Political support range | 5.0-85.0 | WME:1293 | Bounds |
| Election AI/player weight | 50/50 | WME:1346 | Blend for final result |
| Election base | from political_support (F1-F104, was hardcoded 50) | WME:1329 | AI incumbent score starts from support |
| Election Columbia midterms | 7+7 voters (F1-F104) | WME:new | 7 human + 7 AI voters |
| Election Ruthenia | 3+2 voters, forced by any 2 players (F1-F104) | WME:new | 3 human + 2 AI voters |
| Capital flight (democracy, stab<3) | 8% GDP | WME:1445 | Pass 2 adjustment |
| Capital flight (autocracy, stab<3) | 3% GDP | WME:1445 | Pass 2 adjustment |
| Ceasefire rally | +1.5 momentum | WME:1473 | Pass 2 adjustment |
| Pass 2 GDP adjustment cap | 30% of previous GDP | WME:1577 | Maximum total AI adjustment |
| Amphibious penalty | -1 attacker modifier | LAE:57-58 | Replaces old 3:1 ratio (updated 2026-03-30) |
| Combat dice | 1d6 + modifiers, attacker needs >= def+1 | LAE:167-168 | RISK-style, defender wins ties (updated 2026-03-30) |
| Intelligence pool | Per-individual (6-8 intel chief, 3-4 HoS, 2-3 military) | LAE:497-501 | Per game, not per round (updated 2026-03-30) |
| Sabotage success | 40% base + AI + intel bonuses | LAE:new | 2-3 cards per game (updated 2026-03-30) |
| Cyber success | 50% base + AI tech critical | LAE:new | 2-3 cards per game (updated 2026-03-30) |
| Disinformation success | 55% base | LAE:new | 2-3 cards, easiest covert op (updated 2026-03-30) |
| Election meddling | 1 card per game, 2-5% impact | LAE:new | Risk of backlash (updated 2026-03-30) |
| Assassination domestic | 60% hit | LAE:708 | No modifiers, raw probability (updated 2026-03-30) |
| Assassination international | 20% default, Levantia 50%, Sarmatia 30% | LAE:708 | Per-country (updated 2026-03-30) |
| Assassination survival | 50% (4-6 on d6) | LAE:727 | Even if assassination "succeeds" |
| Coup base probability | 25% (F1-F104, was 15%) | LAE:791 | + protest +25%, + low stability/support |
| Propaganda cap | +10 support max | LAE:661 | Before AI tech multiplier |
| Propaganda AI L3+ multiplier | 1.5x | LAE:665 | 50% more effective |
| Maintenance cost per unit | 0.3 coins × 3 = 0.9 effective (F1-F104) | WS:206 | ×3 multiplier applied |
| Nuclear Persia start | 70% progress toward L1 (F1-F104) | WME:new | Near-threshold |
| Nuclear sabotage | -15-20% progress (F1-F104) | WME:new | Sabotage reduces nuclear progress |
| Nuclear bombing | -25% progress (F1-F104) | WME:new | Bombing reduces nuclear progress |
| AI R&D restriction | Columbia + Cathay only (F1-F104) | WME:new | Others via tech transfer only |
| AI Pass 2 stability | ±0.5 (F1-F104, new) | WME:Pass2 | AI holistic adjustment |
| AI Pass 2 support | ±5pp (F1-F104, new) | WME:Pass2 | AI holistic adjustment |
| Helmsman legacy penalty (pursuing) | -2 support/round | WME:1927 | After R4, if pursuing Formosa and failing |
| Helmsman legacy penalty (passive) | -1 support/round | WME:1934 | After R6, if not pursuing at all |
| Health event base probability | 3% + 1% per year over 70 | WME:2285 | Reduced by medical quality |
| Health event death rate | 15% of events | WME:2295 | When event triggers |

*WME = world_model_engine.py, WS = world_state.py, LAE = live_action_engine.py, TE = transaction_engine.py*

---

# PART 6B: UNIT MOVEMENT & REDEPLOYMENT RULES

## When deployment happens

Phase B (combined world update + deployment). Production and mobilization run FIRST (instant), then deployment window opens while World Model Engine processes in parallel. No units are lost during world model processing — combat only happens in Phase A.

## Movement rules by unit type

### Naval units (ships)
- **Range:** Global — any unblocked sea zone anywhere in the world
- **Blocking:** Cannot move THROUGH a zone where enemy has naval superiority (blockade)
- **Chokepoints:** If a chokepoint is blocked (e.g., Gulf Gate), ships cannot transit through it
- **Speed:** Arrives immediately (same Phase B)
- **No basing needed:** Ships operate from sea zones, not from foreign territory

### Ground units
- **Own territory:** Move to any zone in your own country — immediate
- **Allied territory (military alliance):** Move to any zone in an allied country's territory — members of Western Treaty (NATO) can deploy to each other's territory by default
- **Basing rights territory:** Move to the specific zone where basing rights have been granted (per C6 basing rights transaction)
- **Foreign theater (long-distance):** Move to any valid destination above, but if crossing more than one zone from current position to a different theater — **no transit delay (instant deployment)** (submitted in Phase B of Round N, arrives at start of Phase B Round N+1)
- **Cannot deploy to:** Enemy territory (must attack, not deploy), neutral territory without basing rights, sea zones

### Tactical air units (drones/UAVs)
- **Range:** Same theater — can operate from any zone within the theater they're deployed in
- **Redeployment:** Can be moved to a different theater, subject to same rules as ground units (instant)
- **No basing needed for own territory**

### Air defense units
- **Stationary:** Defend the zone they're placed in
- **Redeployment:** Can be moved like ground units (own/allied territory, instant deployment)

### Strategic missiles
- **Not deployed to zones:** Remain in home country (launch sites)
- **Global range:** Can strike any target from home territory
- **Not moved:** Cannot be redeployed

## Transit mechanics

- Units in transit are **not available for combat** during the transit round
- Transit is committed — cannot be cancelled once submitted
- Arriving units appear at the start of the next Phase B (available for deployment)
- If basing rights are revoked while units are in transit TO that zone, units arrive but are immediately "stranded" (reduced effectiveness, can only defend, must redeploy next round)

## Authorization

| Action | Authorization required |
|--------|:---------------------:|
| Deploy within own territory | Military Chief OR Head of State |
| Deploy to allied territory | Military Chief OR Head of State |
| Deploy to basing rights zone | Military Chief OR Head of State |
| Long-distance redeployment | Military Chief OR Head of State |

## Constraints

- Must leave at least 1 ground unit in any CONTROLLED zone (cannot abandon territory)
- Cannot deploy more units than are available (produced + mobilized + arrived)
- New production available at start of Phase B (before deployment window opens)

---

# PART 6C: TACTICAL AIR COMBAT SYSTEM

## Overview

Tactical air units (drones, UAVs, strike aircraft) are a DEPLETABLE resource. They can strike enemy zones, support ground defense, and operate from ships — but they can be shot down by air defense and destroyed on the ground.

## 1. Air Strike Action

```
inputs:
  country: str         -- attacking country
  target_zone: str     -- zone to strike (must be within range)

range:
  Global map: adjacent hexes only (1 hex)
  Theater map: 2 hexes deep (can reach behind front line)

step 1 — AIR DEFENSE INTERCEPTION (defender rolls per incoming):
  AD units in the target zone's COVERAGE AREA intercept incoming air units.
  Coverage area: the target hex + all adjacent hexes (global) or all theater hexes
  within the corresponding global hex.

  Each AD unit processes intercepts sequentially with DEGRADING effectiveness:
    attempt 1: 95% interception chance
    attempt 2: 80%
    attempt 3: 75%
    attempt 4: 70%
    attempt 5: 65%
    attempt 6+: 60% (floor)

  Formula: intercept_rate = max(0.60, 0.95 - (attempt - 1) * 0.10)
    where attempt 1→2 drops 0.15, then 0.05 per subsequent

  INTERCEPTED AIR UNITS ARE DESTROYED. Shot down. Permanently lost.

  Multiple AD units: each AD unit gets its own interception sequence.
  So 2 AD units vs 6 incoming air: AD-1 intercepts #1 (95%), #2 (80%), #3 (75%).
  AD-2 intercepts #4 (95%), #5 (80%), #6 (75%).
  (Each AD unit resets its sequence.)

step 2 — SURVIVING AIR UNITS STRIKE:
  Each air unit that survives interception strikes:
    15% chance of destroying one enemy ground unit in target zone

step 3 — SURVIVING AIR UNITS RETURN:
  Air units that were NOT intercepted return to their base zone. Not consumed.

output:
  air_sent: int
  intercepted_destroyed: int
  strikes_landed: int (survived units that attempted strike)
  ground_units_destroyed: int
  air_units_returned: int (air_sent - intercepted_destroyed)

authorization: Head of State + Military Chief (co-sign)
```

### Worked Example

Columbia has 8 tactical air in the Persia theater. Strikes Persia home zone.
Persia has 1 air defense unit covering the zone.

```
AD-1 intercepts:
  #1: 95% → roll 0.42 → INTERCEPTED (air unit destroyed)
  #2: 80% → roll 0.88 → MISSED (air unit survives)
  #3: 75% → roll 0.31 → INTERCEPTED (destroyed)
  #4: 70% → roll 0.72 → MISSED (survives)
  #5: 65% → roll 0.50 → INTERCEPTED (destroyed)
  #6: 60% → roll 0.15 → INTERCEPTED (destroyed)
  #7: 60% → roll 0.67 → MISSED (survives)
  #8: 60% → roll 0.91 → MISSED (survives)

Result: 4 intercepted (destroyed), 4 survived.
4 surviving air units strike at 15% each:
  → expected ~0.6 ground units destroyed

Columbia loses 4 air units permanently. Persia loses ~0-1 ground unit.
Air strikes against defended zones are EXPENSIVE.
```

## 2. Air Support for Ground Defense (Updated 2026-03-30 per action review — simplified to binary)

Air units stationed in the same zone as ground units provide a **passive defense bonus**:

```
Air support: +1 defender (binary yes/no).
  ANY air units present in the zone = +1 to defender dice.
  No scaling — 1 air unit gives the same bonus as 6 air units.
  This replaces the old +0.5 per air unit scaled system.
```

Air units providing defense support are NOT consumed and do NOT participate in the attack.

## 3. Air Units on Ships (Carrier-Based)

```
rules:
  - Air units CAN be stationed with naval units (representing carrier aircraft)
  - Cannot exist at sea WITHOUT ships (must be attached to naval units)
  - Max 2 air units per naval unit (carrier capacity)
  - Can strike adjacent COASTAL zones from sea position
  - Same strike mechanics as land-based (interception, 15% hit)

vulnerability:
  - If the naval group is attacked (naval combat), stationed air units face
    destruction: 30% chance per air unit of being destroyed when host ships
    take losses
```

## 4. Vulnerability When Stationed (Ground Attack on Airfields)

```
When a zone containing air units is ATTACKED (ground combat or enemy air strike):
  Each air unit in the zone has a 20% chance of being destroyed ("caught on the ground")
  This is resolved BEFORE the air units can provide defense support
  Represents: bombing airfields, destroying parked aircraft, carrier strikes on ports

Formula: for each stationed_air_unit:
  if random() < 0.20: destroy unit (removed from count)
```

## 5. Air Defense Coverage

```
One AD unit covers:
  Global map: its own hex + all adjacent hexes
  Theater map: all theater hexes within the corresponding global hex area

This means:
  - A single AD unit in a capital zone protects a wide area
  - Attacking from range (2 hexes on theater map) still faces interception
  - Multiple AD units in adjacent zones do NOT stack coverage — each zone's AD
    handles interception for attacks on that zone's coverage area
```

## Balance Summary

| Situation | Attacker sends 6 air | Expected outcome |
|-----------|:-------------------:|-----------------|
| vs. 0 AD | 0 lost, 6 strike → ~0.9 ground destroyed | Air dominance — devastating over multiple rounds |
| vs. 1 AD | ~3-4 lost, 2-3 strike → ~0.4 ground destroyed | Costly but viable |
| vs. 2 AD | ~4-5 lost, 1-2 strike → ~0.2 ground destroyed | Very expensive — don't do this often |
| vs. 3 AD | ~5-6 lost, 0-1 strike → ~0.1 ground destroyed | Suicide mission — invest in AD removal first |

**Key design insight:** Air units are powerful against UNDEFENDED targets but extremely costly against defended ones. This creates a real arms race: invest in air to project power, invest in AD to deny it. Both are produced from the same budget.

# PART 6D: SUCCESSION CHAINS

When a Head of State is killed or incapacitated:

| Country | Successor | Mechanic |
|---------|-----------|----------|
| Columbia | Volt (VP) | Automatic. Same participant, gains HoS powers. |
| Cathay | Sage (Party Elder) | Automatic. Acting Chairman. Collective leadership asserts. |
| Sarmatia | Ironhand (General) | Military succession. Acting President. |
| Ruthenia | Bulwark (if active), else Broker | Next most senior active role. |
| Persia | Anvil selects | Kingmaker mechanic. Anvil chooses (Dawn, NPC, or himself). Political event. |
| Solo countries | Facilitator assigns | AI control or new participant. |

Successor inherits HoS authorization chain position. Original role removed from play (dead) or reduced (incapacitated/arrested).

**Co-authorization fallback:** If a required co-authorizer (e.g., Military Chief) is dead/arrested, the Head of State acts alone for that action type until a replacement is appointed via "Fire/Reassign" action.

# PART 6E: IRGC INSTITUTIONAL RESERVES (Persia Special)

Anvil's personal_coins (2 coins in roles.csv) represent IRGC institutional wealth, NOT personal savings. These can be spent on:
- Military maintenance (supplementing state treasury)
- Arms procurement (personal transactions)
- Sanctions evasion operations (narrative effect via facilitator)
- Bribes / kingmaking (personal transfers to other roles)

The state treasury (1 coin for Persia) and IRGC reserves (2 coins for Anvil) are separate pools. Furnace controls the state budget; Anvil controls IRGC funds. This creates a parallel economy within Persia — one of the team's key dynamics.

# PART 6F: NUCLEAR LAUNCH AUTHORIZATION

Authorization varies by country, reflecting real command structures:

**(Updated 2026-03-30 per action review — 10-minute authorization clock integrated with 5-tier system)**

### Columbia (3 confirmations, 2-minute window)
1. **Dealer** (President) — initiates
2. **Shield** (Secretary of Defense) — co-signs
3. **Anchor** (Secretary of State) — third confirmation

All three must confirm within 2 minutes. If any fails → launch CANCELLED. Can be re-initiated.
If Shield or Anchor is dead/arrested, any other active Columbia team member substitutes.

### Cathay (3 confirmations, 2-minute window)
1. **Helmsman** (Chairman) — initiates
2. **Rampart** (PLA Marshal) — co-signs
3. **Sage** (Party Elder) — third confirmation

Same 2-minute rule. Sage represents the collective leadership check.

### European nuclear powers — Gallia, Albion (AI confirmation gate)
1. **Head of State** — initiates with written justification
2. **AI confirmation gate** — the system evaluates the justification against the current strategic context. Low probability of approval unless existential threat is demonstrated. The AI acts as the institutional/parliamentary check that real nuclear states have.
3. If AI rejects, the launch is BLOCKED. Leader can appeal to facilitator for override.

This mechanic prevents casual nuclear use by European powers while preserving the option under genuine existential threat.

### Sarmatia (2 confirmations)
1. **Pathfinder** (President) — initiates
2. **Ironhand** (General) — co-signs

Two-person rule. Simpler chain reflecting centralized command.

### Choson, Persia, Levantia — NO RESTRICTIONS
Head of State alone can launch if they have nuclear capability (Level 1+).
- **Pyro** (Choson) — sole authority
- **Furnace** (Persia) — sole authority (if Persia reaches L1)
- **Citadel** (Levantia) — sole authority (undeclared L1)

These countries have autocratic/wartime command structures with no institutional checks on nuclear use. This creates the most dangerous escalation dynamics in the SIM — a desperate leader with sole launch authority.

### All launches
- Facilitator AUTOMATICALLY notified of any nuclear launch initiation
- Global alert pushed to ALL participants and public display
- Facilitator can OVERRIDE (block) any launch before execution if deemed necessary for game balance

---

# PART 6G: MOBILIZATION POOL STARTING VALUES (Added 2026-03-30 per action review)

Each country has a finite, non-recoverable mobilization pool. Values below represent starting game state.

| Country | Pool Size | Already Used | Remaining at Game Start | Notes |
|---------|-----------|-------------|------------------------|-------|
| Columbia | 12 | 0 | 12 | Requires parliament approval (narrative) |
| Cathay | 15 | 0 | 15 | Largest pool |
| Sarmatia | 10 | 5 | 5 | Partially mobilized (ongoing war) |
| Ruthenia | 8 | 4 | 4 | Partially mobilized (ongoing war) |
| Bharata | 8 | 0 | 8 | |
| Persia | 6 | 0 | 6 | |
| Gallia | 4 | 0 | 4 | |
| Teutonia | 4 | 0 | 4 | |
| Phrygia | 4 | 0 | 4 | |
| Freeland | 3 | 0 | 3 | |
| Albion | 3 | 0 | 3 | |
| Yamato | 3 | 0 | 3 | |
| Hanguk | 3 | 0 | 3 | |
| Formosa | 2 | 0 | 2 | |
| Choson | 2 | 0 | 2 | |
| Levantia | 2 | 0 | 2 | |
| Sogdiana | 1 | 0 | 1 | |
| Mashriq | 1 | 0 | 1 | |
| Asu | 1 | 0 | 1 | |
| Srivijaya | 1 | 0 | 1 | |
| Nesia | 1 | 0 | 1 | |

**Mobilization options:**
- **Partial:** Deploy floor(remaining / 2) units. Pool reduced by that amount.
- **Full:** Deploy ALL remaining units. Pool goes to 0.
- **Never recovers.** Once used, gone for the rest of the SIM.

---

# PART 6H: COURT MECHANIC (Added 2026-03-30 per action review)

Standard judicial process available to ALL democracies.

```
INITIATION:
  Any participant in a democracy can COMPLAIN to the court.
  Submit complaint with written arguments (free text).

PROCESS:
  1. Complaint submitted with arguments (plaintiff).
  2. 10-minute response window for defendant to submit counter-arguments.
  3. AI Court asks 1-2 clarifying questions (optional, if ambiguous).
  4. AI Court renders verdict.
  5. Moderator enforces verdict.

AI COURT DECISION LOGIC:

  The Court is an LLM call with the following prompt structure:

  SYSTEM PROMPT:
    "You are an independent, objective court of law in a democratic country.
     You evaluate disputes based on:
     1. LEGALITY — does the action comply with the country's constitutional rules?
        (Head of State powers, parliamentary authority, authorization chains)
     2. EVIDENCE — what evidence and arguments did each side present?
        Stronger, more specific arguments win over vague claims.
     3. PROPORTIONALITY — was the action proportionate to the stated justification?
        Arresting opposition for 'treason' requires evidence of actual treason.
     4. COMMON SENSE — would a reasonable, objective judge find this justified?

     You may ask ONE clarifying question to either party if their position is
     ambiguous. Then you must decide.

     Your verdict must be ONE of:
     - UPHELD (action stands — e.g., arrest was legal)
     - OVERTURNED (action reversed — e.g., person released, official restored)
     - GUILTY (in criminal cases)
     - NOT GUILTY (in criminal cases)
     - DISMISSED (complaint has no legal basis)

     Provide your verdict in one sentence, followed by a brief reasoning (2-3 sentences).
     Be decisive. Do not hedge. Courts decide."

  USER PROMPT:
    "COUNTRY: [country name] (democracy)
     PLAINTIFF: [role name] — [their arguments, 2-3 sentences]
     DEFENDANT: [role name] — [their arguments, 2-3 sentences]
     CURRENT STATE: stability [X], support [Y]%, active wars: [list]
     RELEVANT RULES: [extracted from role powers, authorization chains]

     Render your verdict."

  The AI's natural reasoning produces fair, contextual decisions. No formula needed —
  the quality of arguments matters. A lazy one-sentence complaint loses to a
  well-reasoned defense. This rewards participants who think like real lawyers.

  BIAS: None intentional. The AI judge has no loyalty to any side. However, the
  SYSTEM PROMPT emphasizes legality and evidence — so arbitrary actions by
  autocratic-minded leaders in democracies will tend to be overturned.

USE CASES:
  - Challenge an arrest (plaintiff = arrested person, defendant = HoS)
  - Challenge a firing (plaintiff = fired person, defendant = HoS)
  - Constitutional dispute (e.g., "President exceeded authority")
  - Contract/agreement dispute (e.g., "They violated our treaty")
  - Impeachment proceedings (formal process, see Impeachment section)

ENFORCEMENT:
  Court verdict is BINDING within the country.
  Moderator enforces immediately.
  No appeal (single instance).

AVAILABILITY:
  Columbia: Full court system. Independent judiciary.
  Ruthenia: Limited court (can be overridden by President with -0.5 stability cost).
  Autocracies: No court system. HoS decision is final.
```

---

# PART 6I: IMPEACHMENT (Added 2026-03-30 per action review)

Available in Columbia and Ruthenia only.

```
COLUMBIA IMPEACHMENT:
  Initiation: Any parliament member can initiate.
  Process: Parliament VOTES (real participants, not AI).
    Majority required (3 of 5 seats).
  Both sides submit positions (prosecutor + defendant). Takes 1 round to resolve.
  If passed: Leader REMOVED from executive power.
    Removed leader stays in play but loses HoS powers.
    Succession chain activates (see Part 6D).

RUTHENIA IMPEACHMENT:
  Initiation: Any team member can initiate.
  Process: 2 real participant votes needed + AI emulates remaining team members.
    AI default: loyal to president (votes against impeachment unless conditions extreme).
    AI override conditions: stability < 3 AND support < 25 → AI votes FOR impeachment.
  Both sides submit positions. Takes 1 round to resolve.
  If passed: Leader REMOVED from executive power.
    Removed leader stays in play but loses HoS powers.
    Succession chain activates (see Part 6D).
```

---

# PART 6J: NAVAL COMBAT (ship vs ship)

*(Added 2026-03-30)*

## resolve_naval_combat (Live Action Engine)

Ship-to-ship battle in a sea zone. Same RISK dice as ground combat but simpler — no terrain, no Die Hard. Open sea.

```
inputs:
  attacker: str         -- attacking country
  defender: str         -- defending country
  sea_zone: str         -- where the battle happens

modifiers (integers, same as ground):
  AI L4 bonus:    +1 if country has ai_l4_bonus flag
  Low morale:     -1 if stability <= 3
  Carrier air:    +1 if country has tactical_air embarked on ships (yes/no)

  No terrain. No Die Hard. No amphibious. Open sea = clean fight.

resolution:
  Pairs matched (min of attacker ships, defender ships)
  Each pair: attacker rolls 1d6 + mods, defender rolls 1d6 + mods
  Attacker needs >= defender + 1 to win pair
  Ties = defender holds (same as ground)
  Loser of each pair loses 1 ship

CRITICAL — embarked units go down with the ship:
  Each sunk ship loses ALL embarked units:
    - Up to 1 ground unit (transport)
    - Up to 5 tactical air units (carrier)
  These are permanently destroyed. Not recovered.

  This makes naval losses VERY costly — you don't just lose a ship,
  you lose everything on it. A fleet defeat can wipe out an
  expeditionary force in one battle.

output:
  attacker_losses: int (ships sunk)
  defender_losses: int (ships sunk)
  embarked_units_lost: per side (ground + air destroyed)
```

### Worked Example

Columbia (4 ships, 2 with ground troops, 2 with 3 air each) attacks Cathay (3 ships, 1 with 4 air) in Formosa Strait.

Columbia modifiers: AI L3 (no L4 bonus = +0), stability 7 (+0), carrier air (+1) = **+1**
Cathay modifiers: AI L3 (no L4 bonus = +0), stability 8 (+0), carrier air (+1) = **+1**

3 pairs (limited by Cathay's 3 ships):

| Pair | Columbia (1d6+1) | Cathay (1d6+1) | Result |
|:----:|:---:|:---:|--------|
| 1 | 5+1=6 | 3+1=4 | 6 >= 5 → Columbia wins. Cathay loses 1 ship + 4 embarked air. |
| 2 | 2+1=3 | 4+1=5 | 3 < 5 → Cathay wins. Columbia loses 1 ship + 1 embarked ground. |
| 3 | 4+1=5 | 4+1=5 | Equal → defender holds. Columbia loses 1 ship + 3 embarked air. |

Result: Columbia loses 2 ships (+ 1 ground + 3 air). Cathay loses 1 ship (+ 4 air).
Cathay holds the strait with 2 remaining ships. Columbia retreats with 2 ships.

**The embarked losses are devastating.** Columbia lost not just 2 ships but also a ground unit and 3 air units — an entire carrier air group gone. Naval warfare is high-stakes.

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
| **Naval combat (fleet battles)** | **Implemented (2026-03-30)** | RISK dice in sea zones. Sunk ship = all embarked units (1 ground + up to 2 air) also lost. Same modifiers as ground (AI L4, morale, carrier air). See Part 6J below. |
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

*End of Engine Formula Documentation v1.1*
*Updated 2026-03-30 per action review — see changelog for full list of changes.*
*This document is the AUDIT REFERENCE for all TTT engine mechanics.*
