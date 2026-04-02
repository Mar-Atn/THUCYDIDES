# Calibration Change Log
**Purpose:** Track ALL changes to data, formulas, and assumptions during parameter review.
**After review completes:** Reconcile every change against CONCEPT → SEED → DET → CSV → DB → Code.
**Rule:** Nothing is "done" until this log is empty (all items reconciled).

---

## Format per entry
```
[ID] WHAT changed | WHERE (file:line) | OLD value | NEW value | WHY | RECONCILE: [list of files to update]
```

---

## CHANGES FROM CALIBRATION CYCLES (Runs #001-#010)

### Data Changes

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| D1 | Persia gdp_growth_base | -3.0 | 0.5 | IMF projects near-zero, -3 caused instant collapse | countries.csv, DET_B3_SEED_DATA.sql, DB |
| D2 | ALL maintenance_per_unit | flat 0.15-0.50 | SIPRI-calibrated 0.006-0.153 | Military spending was 7-531% of GDP | countries.csv, DET_B3_SEED_DATA.sql, DB |

### Formula Changes

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F1 | Sanctions constants | MAX_DAMAGE=0.50, MULTIPLIER=1.5 | MAX_DAMAGE=0.15, MULTIPLIER=0.15 | Was 10-75x too aggressive vs real-world | economic.py, SEED engine docs |
| F2 | GDP base rate | Used `gdp_growth_rate` (result) | Uses `gdp_growth_base` (structural, immutable) | Feedback loop bug: result overwrote base each round | economic.py, orchestrator.py |
| F3 | GDP base halved | `rate / 100` | `rate / 100 / 2` | Rounds are 6 months, rates are annual | economic.py |
| F4 | Social spending model | 70/30 mandatory/discretionary split, ratio-based penalty | Flat coins (% of revenue), decision-based penalty (100%=no effect) | Old model caused universal stability drain from structural budget deficits | economic.py, political.py |
| F5 | Momentum | Active (0-5 scale, +0.01/point to GDP) | REMOVED | Caused runaway compounding. AI Pass 2 will handle confidence. | economic.py |
| F6 | AI Tech Factor | {0:0, 2:0.5%, 3:1.5%, 4:3.0%} | {0:0, 2:0.3%, 3:1.0%, 4:2.5%} | L4 now probabilistic 1.5-3.5%. Also +1 troops at 30% chance. | economic.py |
| F7 | GDP-scaled dampener | None | maturity × GDP-size dampener on tech/momentum | Large mature economies were getting same bonus as emerging | economic.py |
| F8 | Shock absorption | None | Small economies (GDP<80) absorb 40-50% of negative shocks | Tariffs/oil were devastating small economies disproportionately | economic.py |
| F9 | Oil/Sanctions/Tariffs: delta-only | Full impact every round | Only CHANGES from starting state affect GDP | Base rate already includes starting conditions (double-counting fix) | economic.py, orchestrator.py |
| F10 | Momentum decay | None (one-way ratchet) | 10% natural decay toward zero | Was accumulating to ceiling for all prosperous countries | economic.py (now moot — F5 removed it) |
| F11 | Social ratio units fix | `social_spending / gdp` | `social_baseline_pct × social_pct` | Units mismatch caused stability formula to always see underfunding | economic.py |
| F12 | Orchestrator persistence bug | Wrote `gdp_growth_rate` to `gdp_growth_base` | Writes actual `gdp_growth_base` | Corrupted structural rate after each round | orchestrator.py |

### Architecture Changes

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| A1 | Social spending model | % of GDP, mandatory/discretionary split | Flat coins = baseline% × revenue, player sets 50-150% | Cleaner model per Marat's design. Government spends from revenue, not GDP. | SEED engine docs, DET specs |
| A2 | Factor application model | All factors apply at full magnitude every round | Delta-only: oil/sanctions/tariffs only count CHANGES from starting state | Eliminates double-counting with base rate | SEED engine docs, DET specs |
| A3 | Momentum removed | Confidence variable in GDP formula | Delegated to AI Pass 2 | Better handled by AI judgment than formula | SEED engine docs |
| A4 | AI L4 probabilistic | Fixed 3.0% boost | 1.5-3.5% rolled once + 30% chance military bonus | Uncertainty adds gameplay value | SEED engine docs, technology.py |

### Parameter Review Changes (Cal-10: GDP + Oil review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F13 | Oil disruption model | Flat multiplier (+50% Gulf Gate) | Supply reduction: Gulf Gate blocks Solaria+Mirage (25%/50%), Caribe Passage blocks Caribe | Marat: actual supply reduction, not abstract multiplier | economic.py, SEED docs |
| F14 | Oil war premium | 5% per any war, max 15% | 5% per Gulf-region war only | Non-Gulf wars don't affect oil | economic.py |
| F15 | Oil inertia | 40/60 (sticky/formula) | 30/70 (more responsive) | Marat: respond faster to changes | economic.py |
| F16 | Oil price floor | $30 | $15 | Marat: lower floor | economic.py |
| F17 | Oil volatility | ±5% gaussian/round | Removed | Marat: irrelevant at 6-month granularity | economic.py |
| F18 | Oil demand destruction | >$150 for 3 rounds → -8% | >$100 for 3 rounds → -4% to -8% (linear $100-$150) | More gradual, earlier onset | economic.py |
| F19 | Oil supply/demand curve | Linear (demand/supply) | Non-linear (demand/supply)^1.5 | Tight markets amplify disruptions | economic.py |
| F20 | OPEC weights | Flat 20% per member | Weighted by actual production share (resource% × GDP) | Marat: actual production share | economic.py |
| F21 | Oil GDP shock | Flat ±2%/$50, same for all | Scaled by resource sector size (producers) and import exposure (importers) | Marat: Saudi more affected than Columbia | economic.py |
| D3 | Chokepoint starting state | Gulf Gate contested, Caribe open | Caribe Passage partial blockade by Columbia (starting) | Marat: Columbia has ship there | world_state seed data |
| F22 | Oil demand destruction | Fixed -8% after 3 rounds >$150 | Cumulative 5%/round on DEMAND variable after 3 rounds >$100. Counter persists via opec_production JSONB. | Marat: demand should spiral down under sustained high prices | economic.py, orchestrator.py |
| F23 | Oil demand destruction counter | Hardcoded to 0 each round | Persisted in world_state.opec_production._oil_above_threshold_rounds | Bug: counter reset every round, destruction never fired | orchestrator.py (lines 152, 264) |
| F24 | Oil supply/demand exponent | 1.0 (linear) | 2.5 (non-linear) | Marat: tight markets should amplify disruptions | economic.py |
| F25 | OPEC cartel leverage | 1.0× weight | 2.0× amplifier on production decisions | OPEC decisions have outsized market impact | economic.py |
| F26 | Sanctions GDP multiplier | 0.15 | 1.0 | Delta-only makes higher multiplier safe | economic.py |
| F27 | Sector-based sanctions vulnerability | None (flat trade_openness only) | Resources reduce vulnerability, services/tech increase it | Marat: commodities exporters less vulnerable | economic.py |
| F28 | Sanctions fade-out | Binary: 40% reduction after 4 rounds | Gradual: -10%/round after 3 rounds, floor 60% | Marat: gradual not sudden | economic.py |
| F29 | Sanctions LIFTING = recovery boost | Delta produces tiny positive effect | 4-round recovery schedule (40/30/20/10% of lifted damage) | Marat: lifting = releasing pent-up potential, mirror of imposing | economic.py |
| D4 | DB columns for sanctions persistence | None | sanctions_coefficient column added (others deprecated) | Required for coefficient model | DB schema, models/db.py, orchestrator.py |

### Sanctions Clean Rebuild (Cal-11b: Parameter #3 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F30 | Sanctions model architecture | Growth rate modifier (delta from baseline, compounding) | **GDP coefficient multiplier** (0.50-1.0, level adjustment, no compounding) | Marat: "sanctions are a choke, not a spiral" | economic.py (complete rewrite) |
| F31 | calc_sanctions_impact → calc_sanctions_coefficient | Returns (damage, costs) tuple | Returns single coefficient float | Cleaner API, no dead code | economic.py |
| F32 | Coefficient application | sanctions_hit added to growth rate | `GDP_actual = GDP_after_growth × (new_coeff / old_coeff)` | Level shift not rate modifier | economic.py (calc_gdp_growth) |
| F33 | Coefficient computation | Only on sanctions change, with persistence bugs | **Recomputed every round** from current sanctions state | Marat: simpler, handles adaptation naturally | economic.py (process_economy) |
| F34 | S-curve reshaped | (0.3→10%, 0.5→20%, 0.7→60%) | **(0.2→5%, 0.4→25%, 0.5→40%, 0.7→70%, 0.8→80%)** | Higher effectiveness at partial coverage (~40% at 0.50) | economic.py |
| F35 | MAX_DAMAGE | 0.15 → 0.50 → 0.58 → **0.87** | **0.87** (1.5× from 0.58) | Marat: full world sanctions must be powerful | economic.py |
| F36 | Dollar credibility impact on sanctions | Scaled sanctions by dollar_credibility/100 | **Removed** | Marat: remove this element | economic.py |
| F37 | Imposer cost | Computed but never applied | **NOT IMPLEMENTED** — noted for future | Gap: sanctioning currently free for imposer | TODO |

### Tariff Clean Rebuild (Cal-11c: Parameter #4 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F38 | Tariff model architecture | Growth rate modifier (delta, capped) | **GDP coefficient** (same pattern as sanctions) | Consistent architecture, no compounding, clean | economic.py (complete rewrite) |
| F39 | calc_tariff_impact → calc_tariff_coefficient | Old bilateral cost calc | New: market_power × trade_exposure × K model | Prisoner's dilemma: big economy bullying small = asymmetric | economic.py |
| F40 | Tariff formula logic | Bilateral trade weight proxy | **Imposer market_power × target trade_exposure × K × imposer_fraction(0.5)**. Target: imposer_market_power × my_exposure × K. Bigger imposer = bigger hit on target. | economic.py |
| F41 | TARIFF_K constant | N/A | **0.54** (calibrated: Columbia L3 on Cathay = ~4-6% GDP hit) | Matches real-world US-China trade war | economic.py |
| F42 | Trade exposure formula | (abs(trade_bal) + 0.15×GDP) / GDP | **(abs(trade_bal) + 0.25×GDP) / GDP** — higher baseline | Marat: Columbia must be more vulnerable to retaliation | economic.py |
| F43 | Tariff inflation | Added every round (compounding bug) | **Level-based**: only CHANGE in tariff inflation applied | Fixed compounding inflation bug | economic.py |
| F44 | Tariff customs revenue | Not tracked | **revenue = target_GDP × target_exposure × intensity × 0.075** added to treasury | Imposer gets customs income | economic.py |
| F45 | L0 initialize_sim() | R1 special handling inside process_round | **Standalone function** — computes all starting coefficients before R1 | Eliminates R1 jump bug, all rounds identical | orchestrator.py |

### Budget & Treasury (Cal-12: Parameter #5 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F46 | Oil revenue formula | `oil_price × resource% × GDP × 0.01` (GDP-biased) | `oil_price × oil_production_mbpd × 0.009` (production-based) | Sarmatia/Solaria produce similar to Columbia but got 3× less revenue | economic.py, countries.csv |
| D5 | oil_production_mbpd field | None | New DB column: Columbia 13, Sarmatia 10, Solaria 10, Persia 3.5, Mirage 3.5, Caribe 0.8 | Real-world production data in million bpd | DB schema, models/db.py |
| D6 | debt_ratio field | debt_burden in flat coins (wrong values) | New DB column: % of GDP. Columbia 125%, Yamato 130%, Ponte 130%, Cathay 55%, Sarmatia 25%, etc. | Match real-world debt/GDP ratios | DB schema, models/db.py |
| D7 | Cathay tax_rate | 20% | 25% | Marat: increase Cathay govt budget | countries.csv, DB |
| D8 | Columbia debt_ratio | ~2% (wrong) | 125% | Match real US debt | DB |
| F47 | Debt service formula | Flat debt_burden deducted | debt_service = debt_amount × interest_rate. Rate: 3%/yr base, +1% per 20% over 100% debt/GDP | Realistic: high debt = higher interest = debt spiral | economic.py |
| F48 | Sanctions cost in revenue | Deducted from revenue | **REMOVE** (double-counting with sanctions coefficient) | Already captured by GDP coefficient | economic.py |
| F49 | Inflation/war erosion in revenue | Deducted from revenue | **REMOVE** (to be handled separately in inflation parameter) | Simplify revenue to pure arithmetic | economic.py |
| F50 | Tech R&D costs | % of remaining budget | **Decision-based**: AI standard=6 coins, accelerated=12. Nuclear: 2% GDP standard, 5% accelerated | Player decision, not automatic | economic.py |
| TODO | Caribe GDP | 2.0 | TBD — adjust slightly later | Marat noted for future | countries.csv |
| TODO | Military production levels | Default standard | War countries: accelerated ground+air. Cathay: ground standard, naval+air accelerated. Others: standard or none. | Need to set per country | Starting data |
| D9 | Treasury starting values | Col 50, Cat 45, Sar 6 | **Col 30, Cat 50, Sar 18** | Columbia prints instead of saves. Sarmatia has sovereign fund. | DB, countries.csv |
| D10 | Social spending model | % of revenue | **% of GDP** (developed 15%, EU 20%, others 10%, Choson 5%) | More realistic, creates real budget pressure | economic.py, countries.csv |
| F51 | Maintenance multiplier | ×1 (SIPRI-calibrated) | **×3** | Creates budget tension for all countries | economic.py |
| F52 | Money printing action | Automatic on deficit | **NEW: Player action, once/round, 3% of GDP → treasury + inflation boost** | Strategic choice: print = instant cash + inflation | NEW mechanic to implement |
| F53 | Cathay mil production | All accelerated | **Ground standard, naval+air accelerated** | Marat: ground to standard | Starting data |
| F54 | Tech investment | Auto from budget | **Only Columbia+Cathay invest in AI. Others: nuclear if applicable, or none.** | Too expensive and too late for others | Starting data |
| D11 | Tax rates adjusted | Hanguk 26%, Bharata 18%, Formosa 20%, Levantia 32% | **Hanguk 36%, Bharata 28%, Formosa 40%, Levantia 52%** | Budget balance — these countries couldn't afford basic spending | DB, countries.csv |
| D12 | Levantia maintenance | ×3 standard | **÷2 from ×3** (effective ×1.5) | Wartime economy, more efficient per-unit costs | DB, countries.csv |
| D13 | Ruthenia+Choson production costs | Standard | **÷3** (conscript armies, cheaper production) | Budget balance — tiny economies can't afford standard costs | Starting data |
| D14 | Treasuries | Levantia 5, Formosa 8 | **Levantia 10, Formosa 15** | More runway for small wartime/threatened economies | DB, countries.csv |

### Inflation (Cal-13: Parameter #6 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F55 | Inflation drivers | Only money printing | **Money printing + oil price changes + tariff inflation + deficit pressure** | Marat: balanced budget→normalize, deficit+tariffs+oil→spike | economic.py |
| F56 | Deficit handling | 100% to debt or printing | **50% borrowed (→debt), 50% printed (→inflation)** | Marat: split deficit half/half | economic.py |
| F57 | Money printing multiplier | 80 | **60** (reduced 25%) | Marat: slightly less inflationary per coin printed | economic.py |
| F58 | Oil→inflation | None | **+3pp per $50 increase (importers), -1.5pp (producers)** | Oil shocks drive consumer prices | economic.py |
| F59 | Surplus→deflation | None | **-1pp per round if surplus** | Fiscal discipline reduces inflation | economic.py |
| F60 | Inflation→stability/support | Indirect through crisis state | **Direct: people react to inflation ABOVE their R0 level** | Marat: inflation above normal = political cost | political.py |

### Crisis State (Cal-14: Parameter #7 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F61 | Crisis state system | 4-state ladder (normal/stressed/crisis/collapse) with trigger formulas, aggressive multipliers (×0.5/×2.0), recovery rounds | **DELEGATED TO AI PASS 2.** AI decides crisis state. Simple penalty: -1% to -2% GDP growth when compounding negative events. | Marat: "keep ideology, AI decides, simple penalty, reasonably predictable" | economic.py (remove trigger/multiplier machinery) |
| F62 | Crisis GDP multipliers | Stressed ×0.85/×1.2, Crisis ×0.5/×1.3, Collapse ×0.2/×2.0 | **Removed.** Replaced by flat -1% to -2% penalty from AI judgment. | Multipliers were too aggressive, caused irrecoverable spirals | economic.py |
| F63 | Crisis triggers | 6 stress triggers, 5 crisis triggers (formula-based) | **Removed.** AI uses same indicators but applies judgment, not thresholds. | Formula triggers fired too easily with new budget mechanics | economic.py |

### Stability (Cal-15: Parameter #8 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F64 | Stability formula simplified | 12+ factors including sanctions friction + crisis penalty | **Removed: sanctions friction, crisis state penalty.** Keep: GDP growth, social spending, war, inflation delta, regime modifiers. AI Pass 2 adjusts ±0.5. | Double-counting with coefficient model. Simpler = more predictable. | political.py |
| F65 | Financial markets → stability | Market index directly mutates GDP/support | **3 indexes (Columbia, EU, Cathay) feed into stability as input.** Market crash = -0.15 stability/round. | Cleaner architecture, no hidden side effects | political.py, economic.py |
| F66 | Stability actions | Propaganda_boost exists but no formal actions | **3 player actions: Repression (autocracy, free, -support), Propaganda (1-2 coins, +stability+support), Social boost (budget decision).** | Players need levers to fight decline | Action system (future) |

### Political Support (Cal-16: Parameter #9 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F67 | Support formula simplified | Crisis state penalties (2/5/10pp) | **Removed crisis penalties** (delegated to AI Pass 2) | Consistent with crisis state removal | political.py |
| F68 | Inflation → support | Not in formula | **Added: -0.3pp per 1pp inflation above R0 (democracy), -0.2pp (autocracy)** | Marat: people react to inflation above normal | political.py |
| F69 | GDP for autocracies | Only stability-driven | **Added: (gdp_growth - 1.0) × 0.5** | Economy matters for autocracies too, just less | political.py |
| F70 | AI Pass 2 adjustment | None | **±5pp per round** | Events, scandals, leadership changes | political.py |
| F71 | Stability+Support dual tracking | Both exist | **Confirmed: keep both.** Stability = system resilience. Support = leader popularity. Revolution = BOTH low (stab ≤ 2 AND sup < 20%). | Different things: France can be stable with unpopular leader | — |

### Elections (Cal-17: Parameter #10 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F72 | Election base score | Starts at 50, ignores political_support | **Starts at political_support level.** Incumbent at 30% support starts at 30, not 50. | Support IS the foundation of elections | political.py |
| F73 | Crisis penalty in elections | Fixed -5/-15/-25 from crisis state | **Removed** (AI Pass 2 handles) | Consistent with crisis delegation | political.py |
| F74 | Columbia midterms mechanic | Formula-only | **7 players vote + 7 AI votes. Binary party vote. AI based on support + economy + events.** | Real player agency + AI uncertainty | political.py |
| F75 | Columbia presidential mechanic | Formula-only | **Players + AI vote for candidates. 2-way or 3-way. Spoiler effect: independent splits closest party.** | Third-party drama: Anchor/Pioneer running independent can hand election to opposition | political.py |
| F76 | Ruthenia election trigger | Scheduled R3/R4 only | **Scheduled OR forced by any 2 of 3 players at any round.** No AI in trigger decision. | Constant threat to Beacon. Political coup mechanic. | political.py |
| F77 | Ruthenia election voting | Formula-only | **3 players + 2 AI voters. AI: war performance + tiredness + economy + military hero bonus + ±10 random.** | 5 total votes, every vote crucial | political.py |
| F78 | AI citizen voters | Mechanical formula | **OPTION: AI Pass 2 roleplays individual citizen voters with visible reasoning.** Election night drama. | Fun factor. LLM explains each vote decision. | Future AI implementation |

### Revolution/Coups (Cal-18: Parameter #11 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F79 | Protests vs Revolution | "Revolution" auto-triggers | **Protests auto-trigger** (stab≤2, sup<20%). Becomes **Revolution only if a player leads it.** | Marat: protests are spontaneous, revolution requires leadership choice | political.py |
| F80 | Coup base probability | 15% | **25%** | Still risky but more viable when attempted | political.py |
| F81 | Assassination country bonus | Levantia hardcoded +30% | **General intelligence capability modifier** (not country-specific stereotype) | Cleaner design | political.py |
| F82 | Capitulation | Formula: crisis_state + crisis_rounds≥3 | **Delegated to AI Pass 2** | Judgment call, not threshold | political.py |

### Combat (Cal-19: Parameter #12 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F83 | Reserve mechanic | Not defined | **Units can go to reserve (off-map). Visible to own leaders only. Deploy between rounds to own/allied territory. 1 round delay.** | Logistics depth + intelligence gameplay | military.py, action system |
| F84 | AD coverage | Not defined | **Own zone 100%, adjacent zones 50%. Theater maps: 1 AD unit = entire theater covered.** | Spatial air defense logic | military.py |
| F85 | Transfer rules | Not defined | **Agree during round → reserve. Deploy between rounds. Own territory, allied bases, own ships.** | Movement logistics | military.py, action system |
| F86 | Selling/transfer source | Not defined | **From reserve OR any position (can pull from front line).** | Flexibility for arms deals | action system |
| F87 | Air strike casualties | Not defined | **Random selection among all units in target zone.** Equal probability. | Simple, fair, dramatic | military.py |
| F88 | Missile production | Not in budget | **Standard: 1 missile, 2 coins, next round. Accelerated: 2 missiles, 8 coins, next round. Default: Cathay only. Others L1+ CAN but must decide.** | Strategic weapons production as budget decision | economic.py, military.py |
| F89 | AD production | Not defined | **No production. Existing units only. Move/transfer.** | Simplicity — AD is scarce strategic asset | — |
| F90 | Naval production | Only Cathay+Yamato | **Cathay ×2 (default). Columbia/Yamato/Albion: CAN but NOT default (0.5/rnd std, 1/rnd accel). Bharata: 0.5/rnd.** | Realistic shipbuilding rates | military.py |
| F91 | Mobilization pools | Most at 0 | **Sarmatia: 12 ground. Ruthenia: 5 ground. Persia: 4. Cathay: 3. Choson: 2.** Finite, depletable, never recovers. No cost (Marat). | War reserves — ~50% mobilized at start for war countries | DB, countries.csv |
| D15 | Mobilization pool values | 0 for most | **Sarmatia 12, Ruthenia 5, Persia 5.** Others 0. No stability cost. Finite, never recovers. | War reserves | DB |

### Blockades & Covert (Cal-20: Parameter #13 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F92 | Blockade — who can block | Ground forces at chokepoint only | **Any ship OR ground unit in adjacent zone can blockade any chokepoint.** Full/partial = blocker's choice. Enemy ship in adjacent/same → full becomes partial. | More flexible, realistic | military.py |
| F93 | Sabotage target types | -2% GDP (flat) | **3 target types: military (destroy unit), economic (destroy coins), infrastructure (ongoing GDP damage).** | SEED spec had this — more tactical depth | military.py |
| F94 | Assassination | In Revolution parameter (#11) | **Moved to Covert Ops. Uses card system. Domestic 60%/International 20% + intel modifier.** | Belongs with other covert ops | military.py |
| F95 | Proxy terrorist attack | Same as sabotage | **Same mechanic, 30% detection (lower), -5% support if caught. Persia (Furnace 2, Anvil 3), Solaria (Wellspring 1), Mirage (Spire 1).** | Deniable warfare — Gulf states have limited proxy capability too | military.py, roles.csv |

### Tech R&D (Cal-21: Parameter #14 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| D16 | Columbia AI progress | 80% toward L4 | **50% toward L4** | Marat: L4 achievable at R7-8, not sooner | DB, countries.csv |
| D17 | Cathay AI progress | 10% toward L4 | **30% toward L4** | Marat: Cathay is closer than 10% | DB, countries.csv |
| D18 | Persia nuclear progress | 30% toward L1 | **70% toward L1** (threshold 60% — already past!) | Marat: Persia on the brink. L1 at game start or R1. | DB, countries.csv |
| F96 | AI private investment | Auto 1:1 matching (SEED) | **Role action: Pioneer (Columbia) / Circuit (Cathay) invest personal coins into AI program.** Not automatic. Player choice. | Marat: not auto, but substantial acceleration option | technology.py, action system |
| F97 | AI L4 timeline | Unreachable in 8 rounds | **Achievable R7-8 with govt accelerated + private investment.** Only Columbia and Cathay competitive. | Creates meaningful AI race with real stakes | technology.py |
| F98 | AI tech factors | L2:0.3%, L3:1.0%, L4:2.5% | **L0-L3: none (already accounted in GDP). L4: probabilistic 1.5-3.5% GDP + 30% chance +1 all troops.** | Marat: no AI GDP boost until L4, then big probabilistic impact | economic.py, technology.py |
| F99 | Nuclear sabotage (covert) | Not defined | **Covert action (sabotage card): nuclear progress -15-20%. Standard detection/attribution.** | Levantia/Columbia can delay Persia's program covertly | military.py |
| F100 | Nuclear bombing (military) | Not defined | **Air strike action (declared): nuclear progress -25%. AD intercepts apply. Automatic attribution + diplomatic cost.** | Open military option, bigger impact, bigger consequences | military.py |
| F101 | No new AI competitors | Multiple countries at L2 | **Only Columbia + Cathay invest in AI. Others too expensive, too late.** | Marat: two-horse race | technology.py |

### Contagion & Bilateral (Cal-22: Parameter #15 review with Marat)

| ID | What | Old | New | Why | Files to reconcile |
|----|------|-----|-----|-----|-------------------|
| F102 | Contagion mechanism | Formula-based contagion spread | **Delegated to AI Pass 2.** No formula-based contagion. AI moderator decides when crisis spreads based on narrative + trade links. | Marat: "A + C" — AI judgment better than brittle formula triggers | economic.py (remove), orchestrator.py |
| F103 | Financial market indexes | Not implemented | **3 indexes: Columbia (Wall Street), EU (Europa), Cathay (Dragon).** Feed into stability. Computed from GDP growth + deficit + war + sanctions of component countries. | Marat approved as structured input for AI Pass 2 stability assessment | economic.py, orchestrator.py |
| F104 | Bilateral dependency | trade_matrix-based formula | **Removed as separate formula.** Trade exposure already captured in tariff/sanctions coefficients. Remaining bilateral effects → AI Pass 2. | Simplification — avoid double-counting with tariff model | economic.py |

### Key tariff numbers (Cal-11c final):
- Columbia L3 on Cathay (unilateral): Columbia -1.4%, Cathay -4.4%
- Cathay retaliates L3: Columbia additional -2.9%, Cathay additional -1.7%
- Full trade war (all major economies): Columbia -5.7%, Cathay -10.3%, Teutonia -4.2%
- Free trade: Cathay +14% boost, Columbia +9% boost

### Key sanctions numbers (Cal-11b final):
- Sarmatia (resources-heavy) current coalition: coeff **0.900** (10% GDP suppression)
- Sarmatia full world L3: coeff **0.821** (18% suppression)
- Persia full world L3: coeff **0.800** (20% suppression)
- Sanctions lifted: coefficient rises → GDP recovers proportionally
- Tech/services economy (Formosa) under full sanctions: ~45% suppression

---

## RECONCILIATION CHECKLIST (do after all 15 parameters reviewed)

### Source Files to Update

| File | What needs updating | Priority |
|------|-------------------|----------|
| `2 SEED/C_MECHANICS/C4_DATA/countries.csv` | D1-D18: All data changes applied | ✅ DONE (2026-04-03) |
| `2 SEED/D_ENGINES/SEED_D8_ENGINE_FORMULAS_v1.md` | F1-F104: All formula changes | ✅ DONE (2026-04-03) |
| `2 SEED/D_ENGINES/world_state.py` | Constants + market_indexes + oil_production_mbpd | ✅ DONE (2026-04-03) |
| `3 DETAILED DESIGN/DET_B1_DATABASE_SCHEMA.sql` | oil_production_mbpd, coefficients, market_indexes | ✅ DONE (2026-04-03) |
| `3 DETAILED DESIGN/DET_C1_SYSTEM_CONTRACTS.md` | Processing steps, momentum/contagion delegation | ✅ DONE (2026-04-03) |
| `3 DETAILED DESIGN/DET_F5_ENGINE_API.md` | Pass 2 scope, coefficient docs | ✅ DONE (2026-04-03) |
| Supabase DB | Migration needed: oil_production_mbpd, market_indexes | PENDING |
| `app/engine/engines/economic.py` | Source of truth. ×3 maint, mbpd oil, market indexes | ✅ DONE |
| `app/engine/engines/political.py` | Source of truth. Market stress in stability. | ✅ DONE |
| `app/engine/engines/orchestrator.py` | Source of truth. oil_production_mbpd mapping. | ✅ DONE |
| `app/engine/models/db.py` | oil_production_mbpd, market_indexes, removed dead fields | ✅ DONE |
| `app/tests/layer1/test_engines.py` | Fixed stale tests, added market index tests | ✅ DONE (78 pass) |

### Integrity Checks
- [x] All constants in code match documented values
- [x] CSV matches documented values (D1-D18 applied)
- [x] SEED engine docs updated to current formula logic
- [x] Layer 1 tests pass with final values (78/78)
- [x] DET specs updated to current architecture
- [x] Dead code removed (TRADE_PARTNER_WEIGHTS, sanctions_damage param, starting_* fields)
- [ ] Supabase DB migration (oil_production_mbpd, market_indexes columns)
- [ ] DET_B3_SEED_DATA.sql regenerated from CSV
