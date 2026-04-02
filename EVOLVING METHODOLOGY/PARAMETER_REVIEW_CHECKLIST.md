# Supervised Parameter Review — Checklist
**Purpose:** Review every game parameter with Marat. For each: show data, dependencies, formula, test behavior. Validate or adjust.
**Method:** One parameter at a time. Show → Discuss → Decide → Quick test if changed.

---

## Parameters to Review (15 core systems)

### ECONOMIC (7 parameters)

| # | Parameter | What it models | Key formula location |
|---|-----------|---------------|---------------------|
| 1 | **GDP Growth** | How economies grow/shrink each round | economic.py: calc_gdp_growth() |
| 2 | **Oil Price** | Global oil market with supply/demand/disruption | economic.py: calc_oil_price() |
| 3 | **Sanctions Impact** | How sanctions reduce target's GDP | economic.py: calc_sanctions_impact() (S-curve) |
| 4 | **Tariff Impact** | How tariffs affect trade and GDP | economic.py: calc_tariff_impact() |
| 5 | **Budget & Treasury** | Revenue, spending, deficit, money printing | economic.py: calc_budget_execution() |
| 6 | **Inflation** | Money printing → inflation → erosion | economic.py: calc_inflation() |
| 7 | **Momentum & Crisis** | Economic confidence, crisis ladder | economic.py: update_momentum(), update_economic_state() |

### POLITICAL (4 parameters)

| # | Parameter | What it models | Key formula location |
|---|-----------|---------------|---------------------|
| 8 | **Stability** | Regime stability (1-10), affected by war/economy/social | political.py: calc_stability() |
| 9 | **Political Support** | Public approval, drives elections | political.py: calc_political_support() |
| 10 | **Elections** | Columbia midterms/presidential, Ruthenia wartime | political.py: process_election() |
| 11 | **Revolution & Coups** | When regimes fall | political.py: check_revolution(), resolve_coup() |

### MILITARY (2 parameters)

| # | Parameter | What it models | Key formula location |
|---|-----------|---------------|---------------------|
| 12 | **Combat Resolution** | RISK dice + modifiers for ground/naval/air | military.py: resolve_attack() |
| 13 | **Blockades & Covert Ops** | Chokepoint control, intelligence operations | military.py: resolve_blockade(), resolve_covert_op() |

### TECHNOLOGY (1 parameter)

| # | Parameter | What it models | Key formula location |
|---|-----------|---------------|---------------------|
| 14 | **Nuclear & AI R&D** | Progression toward nuclear/AI capability | technology.py: calc_tech_advancement() |

### CROSS-CUTTING (1 parameter)

| # | Parameter | What it models | Key formula location |
|---|-----------|---------------|---------------------|
| 15 | **Contagion & Bilateral** | How crises spread between trade partners | economic.py: apply_contagion(), bilateral_dependency() |

---

## For Each Parameter, Review:

### A. Starting Data
- Current values in countries.csv / seed data
- Real-world reference (what should these be?)
- Are proportions between countries correct?

### B. Design Dependencies (from CONCEPT & SEED)
- What SHOULD affect this parameter? (design intent)
- What SHOULD this parameter affect downstream?
- Any design constraints (e.g., "no country eliminated before R4")

### C. Current Formula
- Exact calculation (show the code)
- Constants and their values
- Known calibration changes from 8 cycles

### D. Test Behavior
- How did it behave in Run #008?
- Which countries are correct? Which are off?
- Sensitivity: what input changes have the biggest effect?

### E. Decision
- [ ] Approved as-is
- [ ] Adjust constants (specify which, to what)
- [ ] Adjust formula (specify how)
- [ ] Adjust starting data (specify which countries)
- [ ] Flag for AI Pass 2 adjustment (better handled by judgment than formula)

---

## Review Progress

| # | Parameter | Status | Notes |
|---|-----------|--------|-------|
| 1 | GDP Growth | ✅ | Approved. Delta-only factors, no momentum, reduced tech, maturity dampener. Changes: F1-F12, D1-D2, A1-A4 |
| 2 | Oil Price | ✅ | Approved. Non-linear S/D (exp 2.5), OPEC weighted by share (2× lever), Gulf/Caribe blockade = supply reduction, Gulf-only war premium, cumulative demand destruction (5%/rnd), inertia 30/70, floor $15. Changes: F13-F25, D3 |
| 3 | Sanctions | ✅ | **CLEAN REBUILD.** GDP coefficient model (0.50-1.0). Recomputed every round. S-curve reshaped. MAX_DAMAGE=0.87. Sector vulnerability. No compounding. Lifting = automatic recovery. Dollar credibility removed. Imposer cost: TODO. Changes: F30-F37 |
| 4 | Tariffs | ✅ | **CLEAN REBUILD.** GDP coefficient model (same as sanctions). Prisoner's dilemma: imposer_market_power × target_exposure × K. Asymmetric (big bullies small cheaply). Customs revenue to treasury. Inflation as level. L0 init function. K=0.54, trade_exposure baseline 0.25. Changes: F38-F45 |
| 5 | Budget | ✅ | Clean arithmetic. Oil: mbpd-based. Debt: % of GDP with escalating interest (3%+1%/20% over 100%). Social: % of GDP (EU 20%, developed 15%, others 10%). Maint ×3. Print money action (3% GDP + inflation). Balanced all 20 countries. Changes: F46-F54, D5-D14 |
| 6 | Inflation | ✅ | Drivers: printing (×60), oil (±3pp/$50), tariffs (level), deficit (50/50 debt/print). Decay 15% of excess. Surplus bonus -1pp/round. Affects stability+support via delta from R0 baseline. Formosa treasury→15. Changes: F55-F60 |
| 7 | Momentum/Crisis | ✅ | Momentum: already removed (Cal-8→AI Pass 2). Crisis state: **delegated to AI Pass 2.** Remove 4-state ladder, triggers, multipliers. AI decides crisis, applies -1% to -2% GDP penalty. Simple, predictable, judgment-based. Changes: F61-F63 |
| 8 | Stability | ✅ | Simplified: GDP growth + social spending + war + inflation delta + regime modifiers. Removed sanctions friction + crisis penalty (handled elsewhere). Financial markets (3 indexes) feed in. AI Pass 2 adjusts ±0.5. Player actions: repression, propaganda, social boost. Changes: F64-F66 |
| 9 | Political Support | ✅ | Democracy: GDP + stability + inflation delta + casualties + war tiredness. Autocracy: stability + GDP + inflation + repression/nationalism. Removed crisis penalties. Added inflation impact. AI Pass 2 ±5pp. Revolution = stab≤2 AND sup<20%. Changes: F67-F71 |
| 10 | Elections | ✅ | Columbia midterms: 7 players + 7 AI, party vote. Presidential: candidates + spoiler mechanic. Ruthenia: 3 players + 2 AI, forced by any 2 players. Base = support level. AI citizen voters option (LLM roleplay). Changes: F72-F78 |
| 11 | Revolution/Coups | ✅ | Protests auto-trigger (stab≤2, sup<20%). Revolution = player leads protests (choice). Coup base 25% (was 15%). Assassination: intelligence modifier not country-specific. Capitulation → AI Pass 2. Health events: Dealer 7%, Helmsman 4%, Pathfinder 4%. Changes: F79-F82 |
| 12 | Combat | ✅ | RISK dice + modifiers approved. Reserve mechanic (off-map, deploy between rounds). AD: own zone 100%, adjacent 50%, theater-wide with 1 unit. Transfer: via reserve, deploy between rounds. Air casualties: random unit. Missile production: Cathay default, others can decide. Standard 2 coins, accelerated 8 coins. Changes: F83-F88 |
| 13 | Blockades/Covert | ✅ | Blockade: ship OR adjacent ground can block any chokepoint. Full/partial choice, enemy ship downgrades. Covert: 6 types (espionage, sabotage, cyber, disinfo, election, assassination). Sabotage has 3 targets (military/economic/infra). Proxy attacks = Persia deniable variant. 3 rolls per op. Changes: F92-F95 |
| 14 | Nuclear/AI R&D | ✅ | AI: Columbia 50%, Cathay 30% toward L4. L4 achievable R7-8 with private investment (Pioneer/Circuit role action). L0-L3: no GDP boost. L4: probabilistic. Nuclear: Persia at 70% (L1 at start). Sabotage -15-20%, bombing -25% on nuclear progress. Only Columbia+Cathay compete on AI. Changes: D16-D18, F96-F101 |
| 15 | Contagion | ✅ | Approved. Contagion → AI Pass 2 (no formula). Financial market indexes (Columbia/EU/Cathay) feed stability. Bilateral dependency removed (captured in tariff/sanctions coefficients). Changes: F102-F104 |
