# TTT Engine -- Formula Specifications
**Version:** 1.0 | **Date:** 2026-03-25 | **Status:** Implemented in engine.py

---

## Three-Pass Architecture

The engine processes each round in three sequential passes:

**Pass 1 -- Deterministic.** Pure mathematical formulas calculate direct effects from player actions and current world state. Every formula is transparent and auditable. Players can predict outcomes if they know the inputs.

**Pass 2 -- AI Contextual Adjustment.** Receives the mechanical results from Pass 1 plus round history and context. Produces bounded adjustments (maximum +/-30% from formula base) with mandatory one-sentence justifications. In the test implementation, this uses heuristic rules rather than LLM calls. Upgradeable to real AI later.

**Pass 3 -- Coherence Check.** A separate review of the adjusted world state. Flags logical contradictions (e.g., negative GDP, stability/support divergence, country at war with zero military). Generates a narrative summary. Does NOT change any numbers.

```
Actions + World State
        |
        v
  [PASS 1: DETERMINISTIC]
  All formulas applied.
  New world state calculated.
        |
        v
  [PASS 2: AI ADJUSTMENT]
  Heuristic rules review results.
  Bounded adjustments (+/-30%).
  Each adjustment justified.
        |
        v
  [PASS 3: COHERENCE CHECK]
  Contradictions flagged.
  Narrative generated.
  Numbers NOT changed.
        |
        v
  Final World State + Report
```

---

## Formula 1: GDP Growth (Multiplicative Factor Model)

### Mathematical Notation

```
growth_rate = base_growth_rate / 100

tariff_factor    = max(0.5, 1.0 - net_tariff_cost / GDP)
sanctions_factor = max(0.5, 1.0 - sanctions_damage)
war_factor       = max(0.5, 1.0 - war_zones * 0.02 - infra_damage * 0.05)
tech_factor      = 1.0 + AI_TECH_BONUS[ai_level]
inflation_factor = max(0.5, 1.0 - inflation_pct / 100 * 0.015)
blockade_factor  = max(0.5, 1.0 - trade_disrupted * 0.4)

combined = tariff_factor * sanctions_factor * war_factor
         * tech_factor * inflation_factor * blockade_factor

new_GDP = old_GDP * (1 + growth_rate * combined)
new_GDP = max(new_GDP, 0.01)
```

### AI Tech Bonus Table

| AI Level | GDP Bonus |
|:--------:|:---------:|
| 0 | +0% |
| 1 | +0% |
| 2 | +5% |
| 3 | +15% |
| 4 | +30% |

### Input Variables

| Variable | Source | Type |
|----------|--------|------|
| `base_growth_rate` | countries.json: `economic.gdp_growth_rate` | Percentage |
| `GDP` | Previous round's GDP | Coins |
| `net_tariff_cost` | Formula 3 output | Coins |
| `sanctions_damage` | Formula 2 output | Fraction (0-1) |
| `war_zones` | Count of occupied zones from wars list | Integer |
| `infra_damage` | Derived from occupied zone count | Fraction (0-1) |
| `ai_level` | `technology.ai_level` | 0-4 |
| `inflation_pct` | `economic.inflation` | Percentage |
| `trade_disrupted` | Derived from blocked chokepoints | Fraction (0-1) |

### Output Variables

| Variable | Destination |
|----------|-------------|
| `new_GDP` | `economic.gdp` |
| `growth_pct` | `economic.gdp_growth_rate` |

### Edge Cases

- All factors floored at 0.5 (no single factor can halve GDP in one round)
- GDP floored at 0.01 (cannot reach zero)
- Negative base growth rates are valid (wartime contraction)

---

## Formula 2: Sanctions Impact

### Mathematical Notation

```
For each sanctioner S imposing sanctions on target T:
    bilateral_weight = trade_weight[S][T]
    raw_impact = sanctions_level * bilateral_weight * 0.03

coalition_coverage = SUM(trade_weight[S][T]) for all sanctioners
effectiveness = 1.0 if coalition_coverage >= 0.6 else 0.3

total_damage = SUM(raw_impacts) * effectiveness
total_damage = min(total_damage, 0.50)

cost_to_sanctioner = sanctions_level * bilateral_weight * 0.012
```

### Input Variables

| Variable | Source |
|----------|--------|
| `sanctions_level` | bilateral.json: `sanctions[S][T]` (scale -3 to +3, only positive levels impose) |
| `bilateral_weight` | Derived from GDP and sector complementarity |

### Output Variables

| Variable | Destination |
|----------|-------------|
| `total_damage` | Fed into GDP formula as `sanctions_factor` |
| `cost_to_sanctioner` | Applied to each sanctioner's GDP |

### Key Mechanics

- Coalition threshold at 60% trade coverage for full effectiveness
- Below 60%: sanctions are only 30% effective (rerouting via non-sanctioning countries)
- Damage capped at 50% of target GDP
- Cost to sanctioner is ~40% of damage inflicted (0.012/0.03 ratio)
- Negative sanctions levels (-1 to -3) indicate active evasion support, not damage

---

## Formula 3: Tariff Impact

### Mathematical Notation

```
For each tariff pair (imposer I, target T):
    tariff_cost = level * trade_weight * 0.04 * imposer_GDP
    revenue_collected = tariff_cost * 0.70
    net_cost_to_imposer = tariff_cost * 0.30 * (1 - level * 0.15)
    cost_to_target = tariff_cost * 0.50 * (1 - level * 0.15)

    rerouting = level * 0.15  (reduces impact over time)
```

### Input Variables

| Variable | Source |
|----------|--------|
| `tariff_level` | bilateral.json: `tariffs[imposer][target]` (0-3) |
| `trade_weight` | Derived bilateral trade weight |
| `GDP` | Country GDP |

### Output Variables

| Variable | Destination |
|----------|-------------|
| `net_gdp_cost` | Fed into GDP formula as part of `tariff_factor` |
| `revenue_collected` | Added to imposer's revenue |

### Key Mechanics

- Tariffs are NET-NEGATIVE for the imposer (revenue offsets 60-80% of cost, not 100%)
- 15% rerouting per tariff level dilutes impact over time
- Level 3 (prohibitive) approaches sanction-like effects
- Both imposer and target bear costs

---

## Formula 4: Stability Index (1-10 scale)

### Mathematical Notation

```
delta  = (social_spending_ratio - baseline) * 5
delta -= casualties * 0.3
delta -= territory_lost * 0.5
delta += territory_gained * 0.3
delta -= (sanctions_pain / GDP) * 2
delta -= inflation_pct * 0.001
delta -= mobilization_level * 0.2
delta -= war_tiredness * 0.15
delta += propaganda_boost

new_stability = clamp(old_stability + delta, 1, 10)
```

### Input Variables

| Variable | Source |
|----------|--------|
| `social_spending_ratio` | Budget submission or default baseline |
| `baseline` | `economic.social_spending_baseline` |
| `casualties` | Combat results (unit losses this round) |
| `territory_lost` | Zone captures against this country |
| `territory_gained` | Zones captured by this country |
| `sanctions_pain` | sanctions_damage * GDP |
| `inflation_pct` | `economic.inflation` |
| `mobilization_level` | 0/1/2/3 for none/partial/general/total |
| `war_tiredness` | `political.war_tiredness` (cumulative) |
| `propaganda_boost` | From propaganda spending (diminishing returns) |

### Output Variables

| Variable | Destination |
|----------|-------------|
| `new_stability` | `political.stability` |

### Threshold Consequences

| Stability | Condition | Effect |
|:---------:|-----------|--------|
| 8-10 | Stable | Full freedom of action |
| 6-7 | Strained | Troop morale softens |
| 4-5 | Crisis | Protests likely. Morale -1 dice. Capital flight |
| 2-3 | Severe | Protests automatic. Economy halved. Morale -2. Coup risk spikes |
| 1 | Failed | Government loses control |

---

## Formula 5: Political Support (0-100%)

### Mathematical Notation -- Democracy

```
delta  = (gdp_growth - 2.0) * 3
delta -= casualties * 2
delta += (stability - 5) * 2
delta += election_proximity_modifier
delta += rally_effect

new_support = clamp(old_support + delta, 0, 100)
```

### Mathematical Notation -- Autocracy

```
delta  = (stability - 5) * 3
delta -= perceived_weakness * 5
delta += repression_effect
delta += nationalist_rally

new_support = clamp(old_support + delta, 0, 100)
```

### Key Difference

- **Democracies** are driven by economic performance and public outcomes
- **Autocracies** are driven by perceived strength and elite loyalty
- Below 30% support for 3 consecutive rounds triggers succession challenge (autocracies) or electoral defeat (democracies)

---

## Formula 6: Oil Price

### Mathematical Notation

```
base_price = 80

For each OPEC+ member:
    production = share * multiplier[level]
    (low=0.80, normal=1.00, high=1.20)

total_production = SUM(member_production)
supply_ratio = total_production / baseline_supply

demand_factor = 1.0 + weighted_avg_gdp_growth * 0.5

disruption = 1.0 + hormuz_blocked * 0.35 + other_disruptions * 0.10

oil_price = base_price * (demand_factor / supply_ratio) * disruption
oil_price = clamp(oil_price, 20, 300)
```

### OPEC+ Production Shares

| Member | Share |
|--------|:-----:|
| Solaria | 35% |
| Sarmatia | 30% |
| Persia | 15% |
| Mirage | 15% |
| Caribe | 5% |

### Disruption Sources

| Event | Oil Price Multiplier |
|-------|:--------------------:|
| Hormuz blocked | +35% |
| Each other disruption | +10% |

---

## Formula 7: Combat Resolution (RISK Model)

### Mathematical Notation

```
pairs = min(attacker_units, defender_units)

For each pair i:
    a_roll = d6 + attacker_tech + attacker_morale
    d_roll = d6 + defender_tech + defender_morale + terrain
    if a_roll > d_roll: defender loses 1 unit
    else: attacker loses 1 unit  (defender wins ties)
```

### Modifiers

| Modifier | Source | Range |
|----------|--------|:-----:|
| Tech bonus | AI level: L3=+1, L4=+2 | 0 to +2 |
| Morale | (stability - 5) * 0.5 | -2 to +2.5 |
| Terrain | Theater/capital defense bonus | 0 to +2 |

### Special Rules

- Amphibious assault requires 3:1 ratio (4:1 for Formosa)
- Naval superiority prerequisite for landing
- Transferred units have -1 modifier for 1 round
- Defender ALWAYS wins ties (attacker disadvantage)

---

## Formula 8: Revenue

### Mathematical Notation

```
revenue = GDP * tax_rate
        + oil_revenue (producers only)
        - sanctions_cost
        - inflation_erosion
        - war_damage
        - debt_burden

oil_revenue = GDP * resource_sector_share * (oil_price/80 - 1) * 0.3
inflation_erosion = inflation_pct/100 * 0.02 * GDP
war_damage = infra_damage * 0.02 * GDP
```

---

## Formula 9: Budget Execution

### Processing Order

1. Calculate mandatory costs (maintenance + debt burden)
2. Subtract mandatory from revenue = discretionary budget
3. Allocate discretionary: social, military, tech, reserves
4. If deficit: draw from reserves or print money (adds inflation)
5. If reserves exhausted: economic crisis (forced cuts)

### Maintenance

```
maintenance = total_units * maintenance_cost_per_unit
```

---

## Formula 10: Military Production

### Production Tiers

| Tier | Cost per Unit | Output Multiplier | Total Cost for Max Output |
|------|:------------:|:-----------------:|:-------------------------:|
| Normal | 1x | 1x | 1x |
| Accelerated | 2x | 2x | 4x |
| Maximum | 4x | 3x | 12x |

### Formula

```
units_produced = min(coins / (unit_cost * tier_cost), capacity * tier_output)
```

---

## Formula 11: Technology Advancement

### Mathematical Notation

```
progress_increment = (rd_investment / GDP) * 0.5
new_progress = old_progress + progress_increment

if new_progress >= threshold[current_level]:
    level += 1
    progress = 0.0
```

### Nuclear Thresholds

| Current Level | Progress Required |
|:------------:|:-----------------:|
| L0 -> L1 | 0.60 |
| L1 -> L2 | 0.80 |
| L2 -> L3 | 1.00 |

### AI/Semiconductor Thresholds

| Current Level | Progress Required |
|:------------:|:-----------------:|
| L0 -> L1 | 0.20 |
| L1 -> L2 | 0.40 |
| L2 -> L3 | 0.60 |
| L3 -> L4 | 1.00 |

### Special: Cathay Strategic Missiles

Cathay produces +1 strategic missile per round if funded (hardcoded).

---

## Formula 12: Inflation

### Mathematical Notation

```
new_inflation = old_inflation * 0.85          (15% natural decay)
new_inflation += (money_printed / GDP) * 50   (printing adds inflation)

revenue_erosion = inflation/100 * 0.02 * GDP  (applied in revenue formula)
```

### Bounds

- Minimum: 0%
- Maximum: 500% (hyperinflation cap)
- Natural decay means inflation recedes if money printing stops

---

## Formula 13: Debt Service

### Mathematical Notation

```
if deficit > 0:
    new_debt_burden = old_debt_burden + deficit * 0.12

debt_burden is auto-deducted from revenue as mandatory cost each round
```

### Key Mechanic

- 12% of each deficit becomes a permanent annual cost
- Compounding: sustained deficits create ever-growing mandatory spending
- Countries that print money AND run deficits get hit twice (inflation + debt)
- Some countries start with pre-existing debt (e.g., Ponte: 8 coins)

---

## Formula 14: Financial Crisis

### Mathematical Notation

```
market_index = 50 + gdp_growth * 5 + (stability - 5) * 5 - inflation * 0.5
market_index = clamp(market_index, 0, 100)

if market_index < 30:
    severity = (30 - market_index) / 30
    capital_flight = severity * 0.10 * GDP
    GDP -= capital_flight
    treasury -= capital_flight * 0.5
```

### Trigger Conditions

- Sharp GDP decline + low stability + high inflation
- Non-linear: markets tolerate gradual decline but panic at sharp drops
- Capital flight costs up to 10% of GDP in one round

---

## Formula 15: Election (Columbia)

### Mathematical Notation

```
ai_incumbent_score = 50
                   + gdp_growth_trend * 10
                   + (stability - 5) * 5
                   + war_outcome_sum
                   + scandal_factor

final_incumbent_pct = 0.5 * ai_score + 0.5 * player_votes
incumbent_wins = (final_incumbent_pct >= 50)
```

### Election Types

| Election | Round | Special Rules |
|----------|:-----:|---------------|
| Columbia Midterms | 2 | 1 congressional seat. Team votes + 50% AI popular vote |
| Columbia Presidential | 5 | Nominations R4. Speeches + debate. Weighted votes + 50% AI |
| Ruthenia Wartime | 3-4 | AI judges based on war performance, economy, Western support |

---

## Formula 16: Coup Probability

### Mathematical Notation

```
base = 0.05
if stability < 5: base += (5 - stability) * 0.05
if support < 40:  base += (40 - support) / 100 * 0.15
if military_chief_opposed: base += 0.10

probability = clamp(base, 0, 0.95)
```

### Trigger

- Requires >30% of team to independently submit coup attempt
- If threshold met: probability evaluated via fortune wheel
- Failure: conspirators exposed, arrests follow

---

## Pass 2: AI Adjustment Rules (Heuristic Test Implementation)

| Condition | Adjustment | Bound |
|-----------|------------|:-----:|
| Major war defeat (zone fully lost) | GDP -5% to -15% | Max 30% |
| Sanctions damage > 10% | GDP -5% additional | Max 30% |
| Tech breakthrough (AI or nuclear level-up) | GDP +5% | Max 30% |
| First military engagement | Support +10 (rally) | Diminishing by round |
| War duration > 3 rounds | Fatigue accelerates +50% | Cumulative |
| Stability < 4 | GDP -3% (capital flight) | Max 30% |

All adjustments include a mandatory one-sentence justification string.

---

## Pass 3: Coherence Check Rules

| Check | Flag Condition |
|-------|---------------|
| Negative GDP | Any country GDP < 0 |
| Stability/support divergence | Stability <= 2 AND support > 70 |
| Zero military in war | Country at war with 0 ground+naval+air units |
| Nuclear without shock | Nuclear used but country stability > 6 |
| Unusual inverse | Stability >= 8 AND support < 20 |

Pass 3 generates a ~200-word narrative summary covering:
- Global GDP and oil price
- Active conflicts
- Top 5 economies with growth and stability
- Crisis warnings (low stability, high inflation)
- Blocked chokepoints
- Technology leaders

---

## Data Sources

| File | Contains |
|------|---------|
| `countries.json` | All country attributes: economic, military, political, technology |
| `bilateral.json` | Tariff levels (0-3) and sanction levels (-3 to +3) for all pairs |
| `deployments.json` | Unit-by-unit placement on map zones |

---

## Changelog

- **v1.0 (2026-03-25):** Initial implementation. All 16 formulas implemented. Three-pass architecture operational. Tested with Round 1 processing of 20 countries.
