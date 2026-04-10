# CARD: FORMULA REFERENCE — Complete Engine Specification

**Source:** `engines/economic.py` (2011 lines) + `engines/political.py` (836 lines) + `engines/technology.py` (357 lines)
**Calibrated:** Sessions 2026-04-02/03 (15 parameter reviews, 104 formula changes)
**SEED fidelity:** Compared against SEED_D8_ENGINE_FORMULAS_v1.md — **98% EXACT match** (see Appendix F)
**Rule:** These are the CURRENT canonical numbers extracted from code. If code differs from this card, investigate.

---

## PROCESSING ORDER (per round, after agent decisions resolved)

```
Step 0:   Apply submitted actions (tariffs, sanctions, OPEC, blockades)
Step 1:   Oil price
Step 2:   Sanctions coefficient (per country)
Step 3:   Tariff coefficient (per country)
Step 4:   GDP growth (per country)
Step 5:   Revenue (per country)
Step 6:   Budget execution (per country)
Step 7:   Military production (per country)
Step 8:   Technology advancement (per country)
Step 9:   Inflation update (per country)
Step 10:  Debt service (per country)
Step 11:  Economic state transition (per country)
Step 12:  Momentum / confidence (per country)
Step 13:  Contagion (crisis spreads to trade partners)
Step 14:  Dollar credibility
Step 15:  Market indexes (3 regional)
Step 16:  Stability (per country)
Step 17:  Political support (per country)
Step 18:  War tiredness (per country)
Step 19:  Threshold flags (protest/coup risk)
Step 20:  Elections (scheduled rounds only)
Step 21:  Revolution check (if stability ≤ 2)
Step 22:  Health events (elderly leaders)
Step 23:  Capitulation check
```

---

## A. ECONOMIC ENGINE

### A.1 OIL PRICE

**Constants:**
| Name | Value | Notes |
|---|---|---|
| OIL_BASE_PRICE | 80.0 | Starting reference |
| OIL_PRICE_FLOOR | 15.0 | Absolute minimum |
| OIL_SOFT_CAP_THRESHOLD | 200.0 | Asymptotic above this |
| OIL_INERTIA_PREVIOUS | 0.3 | 30% carry from last round |
| OIL_INERTIA_FORMULA | 0.7 | 70% from new calculation |
| OIL_SUPPLY_DEMAND_EXPONENT | 2.5 | Non-linear S/D sensitivity |
| OIL_BLOCKADE_PARTIAL | 0.25 | 25% production loss |
| OIL_BLOCKADE_FULL | 0.50 | 50% production loss |
| OPEC multipliers | min=0.70, low=0.85, normal=1.00, high=1.15, max=1.30 | |

**Supply:**
```
supply = 1.0
  + OPEC production adjustment (per member: share × (multiplier-1) × 2.0)
  - sanctions on producers (L2+: -10% × share)
  - Gulf Gate blockade (partial -25%, full -50% of Solaria+Mirage production)
  - Caribe passage blockade (same logic for Caribe)
  floor at 0.3
```

**Demand:**
```
demand = 1.0
  - stressed/crisis/collapse countries reduce demand (-3%/-6%/-10% if GDP>20)
  + global avg GDP growth effect: (avg_growth - 2%) × 0.03
  - demand destruction if price > $100 for 3+ rounds: 5% compound per round
  floor at 0.4
```

**War premium:** +5% per active war involving gulf countries, cap 15%

**Formula:**
```
ratio = demand / supply
raw_price = 80 × (ratio ^ 2.5) × (1 + war_premium)
If raw_price > 200: soft_cap → 200 + 50 × (1 - e^(-(raw-200)/100))
price = prev_price × 0.3 + formula_price × 0.7   (inertia)
```

**Oil revenue to producers:**
```
oil_revenue = price × effective_mbpd × 0.009
(blockaded producers get reduced effective_mbpd)
```

---

### A.2 SANCTIONS COEFFICIENT (CONTRACT_SANCTIONS v1.0, 🔒 locked 2026-04-10)

**Authoritative spec:** `PHASES/UNMANNED_SPACECRAFT/CONTRACT_SANCTIONS.md` v1.0.
**Engine math rewritten 2026-04-10** — the old model (with trade_openness + global 0.87 ceiling + sector_vulnerability multiplier) is replaced by a simpler sector-derived ceiling model. Regression guards in `app/tests/layer1/test_sanctions_engine.py`.

**Key constants:**
- `SANCTIONS_WEIGHT_TEC = 0.25` (technology sector max vulnerability)
- `SANCTIONS_WEIGHT_SVC = 0.25` (services sector max vulnerability)
- `SANCTIONS_WEIGHT_IND = 0.125` (industry sector max vulnerability)
- `SANCTIONS_WEIGHT_RES = 0.05` (resources sector max vulnerability — structurally resilient)
- `SANCTIONS_FLOOR = 0.15` (safety rail on coefficient; mostly unreachable given sector weights cap max_damage ≈ 0.22)
- S-curve: see below

**Per-country max damage ceiling (derived from sector mix):**
```
max_damage = tec% × 0.25  +  svc% × 0.25  +  ind% × 0.125  +  res% × 0.05
```

Tech/services-heavy economies top out ~22% GDP loss. Resource-heavy economies top out ~13-14%. Industrial economies in between. No global constant — each country has its own ceiling.

**Coverage — signed for evasion support:**
```
coverage = Σ (actor_gdp_share × level / 3)   where level ∈ [-3, +3]
           # positive level = sanctioning, negative level = evasion support
coverage = clamp(coverage, 0, 1)
           # evasion can cancel sanctions but cannot produce a GDP bonus
```

**S-curve (new steeper shape with tipping point at 0.5-0.6 coverage):**

| coverage | effectiveness |
|---|---|
| 0.0 | 0.00 |
| 0.1 | 0.05 |
| 0.2 | 0.10 |
| 0.3 | 0.15 |
| 0.4 | 0.25 |
| 0.5 | 0.35 |
| 0.6 | 0.55 ← tipping-point jump |
| 0.7 | 0.65 |
| 0.8 | 0.75 |
| 0.9 | 0.90 |
| 1.0 | 1.00 |

**Final formula:**
```
damage      = max_damage × effectiveness
coefficient = max(SANCTIONS_FLOOR, 1.0 - damage)
```

**Semantics:**
- `coefficient = 1.0` — no sanctions active
- `coefficient < 1.0` — multiplies target GDP via ratio rule in `calc_gdp_growth` (one-time shock at imposition, not recurring drain)
- No temporal adaptation, no compounding, no imposer cost, no evasion benefit (all dropped 2026-04-10 per CONTRACT_SANCTIONS v1.0)
- Lifting sanctions = immediate recovery via the same ratio rule

**Canonical calibration anchors** (Sarmatia under various coalitions, locked in L1 tests):
| Scenario | coefficient | GDP loss |
|---|---|---|
| Clean world | 1.0000 | 0.00% |
| Teutonia alone L3 | 0.9960 | 0.40% |
| Columbia alone L3 | 0.9714 | 2.86% |
| Real DB starting (12 actors incl. Cathay L-1 evasion) | 0.9490 | 5.10% |
| Starting + Cathay flips L-1 → L+2 | 0.9028 | 9.72% |

**Related effects (separate mechanisms, unchanged):**
- Target revenue cost (calc_revenue): `Σ level × bilateral_weight × 0.015 × gdp` subtracted from target's revenue per round
- Oil producer supply effect (calc_oil_price): L2+ sanctions on oil producers reduce effective world supply by 10% × producer's share

---

### A.3 TARIFF COEFFICIENT (CONTRACT_TARIFFS v1.0, 🔒 locked 2026-04-10)

**Authoritative spec:** `PHASES/UNMANNED_SPACECRAFT/CONTRACT_TARIFFS.md` v1.0.
**Engine math UNCHANGED** — the tariff slice locks a contract around existing behavior and pins the constants as regression guards in `app/tests/layer1/test_tariff_engine.py`.

**Key constants:** TARIFF_K = 0.54, TARIFF_IMPOSER_FRACTION = 0.50, TARIFF_REVENUE_RATE = 0.075, TARIFF_INFLATION_RATE = 12.5, coefficient floor = 0.80.

**Decision schema** (set by participant):
```
set_tariffs: {
  decision: "change" | "no_change",
  changes: { tariffs: { <target>: int 0..3 } }  // SPARSE — only changed targets
}
```

Level 0 means lift. Untouched targets carry forward via the `tariffs` state table. `no_change` is a legitimate explicit choice.

**Formula (per country, per round):**
```
For each bilateral tariff I impose (target_id, level > 0):
  intensity            = level / 3.0
  target_market_share  = target_starting_gdp / total_starting_gdp
  my_exposure          = (|my_trade_balance| + 0.25 × my_gdp) / my_gdp
  target_exposure      = (|target_trade_balance| + 0.25 × target_gdp) / target_gdp

  self_damage          = target_share × my_exposure × intensity × 0.54 × 0.50
  customs_revenue     += target_gdp × target_exposure × intensity × 0.075
  inflation_add       += intensity × target_share × 12.5
  total_gdp_hit       += self_damage

For each bilateral tariff imposed on me by imposer_id (level > 0):
  intensity            = level / 3.0
  imposer_share        = imposer_starting_gdp / total_starting_gdp
  target_damage        = imposer_share × my_exposure × intensity × 0.54
  total_gdp_hit       += target_damage

coefficient = max(0.80, 1.0 - total_gdp_hit)
```

**Asymmetry:** target eats ~2× the damage the imposer eats (via `TARIFF_IMPOSER_FRACTION = 0.5`). Regression-tested in `test_tariff_engine.py::TestImposerVsTargetAsymmetry`.

---

### A.4 GDP GROWTH

**Key constants:**
| Name | Value |
|---|---|
| GDP_FLOOR | 0.5 |
| AI growth bonus | L0-L1: 0%, L2: +0.5%, L3: +1.5%, L4: +3.0% |
| Crisis GDP multiplier | normal: 1.0, stressed: 0.85, crisis: 0.50, collapse: 0.20 |
| Crisis negative amplifier | normal: 1.0, stressed: 1.2, crisis: 1.3, collapse: 2.0 |

**Formula:**
```
base_growth = structural_rate / 100 / 2   (per round = half annual)
shock_absorb = clamp(GDP/80, 0.5, 1.0)   (small economies absorb less)

Oil shock (importers): -2% × (price_delta/50) × import_exposure
Oil shock (producers): +1% × (price_delta/50) × resource_pct × 3
Semiconductor disruption: -dependency × severity × tech_pct   (cap -10%)
War damage: -(war_zones × 3% + infra_damage × 5%)
Tech boost: AI_factor × maturity × GDP_scale
Blockade hit: -blockade_fraction × 40%

negative_shocks × shock_absorb → dampened
If negative: × crisis_amplifier.  If positive: × crisis_multiplier.

effective_growth = base_growth + dampened_cyclical
new_GDP = old_GDP × (1 + effective_growth) × sanction_ratio × tariff_ratio
new_GDP = max(0.5, new_GDP)
```

---

### A.5 REVENUE

```
revenue = GDP × tax_rate
         + oil_revenue
         - debt_burden
         - inflation_erosion: max(0, infl-starting) × 0.03 × GDP/100
         - war_damage: infra × 0.02 × GDP
         - sanctions_cost: Σ(level × bilateral_weight × 0.015 × GDP)
         = max(0, revenue)
```

---

### A.6 BUDGET EXECUTION (CONTRACT_BUDGET v1.1, 🔒 locked 2026-04-10)

**Authoritative spec:** `PHASES/UNMANNED_SPACECRAFT/CONTRACT_BUDGET.md` v1.1.

**Constants:** MAINTENANCE_MULTIPLIER = 3.0, MONEY_PRINTING_INFLATION_MULT = 60.0, DEFICIT_TO_DEBT = 0.15, SOCIAL_STABILITY_MULT = 4.0, SOCIAL_SUPPORT_MULT = 6.0, RD_MULTIPLIER = 0.8.

**Decision schema** (set by participant):
```
social_pct  : float in [0.5, 1.5]                      (continuous slider)
production  : {ground, naval, tactical_air,
               strategic_missile, air_defense} → int 0..3   (per-branch level)
research    : {nuclear_coins: int>=0, ai_coins: int>=0}     (absolute coins)
```

**Production level expansion** (per branch, level → multipliers):

| Level | Cost mult | Output mult | Note |
|---|---|---|---|
| 0 | 0× | 0× | none |
| 1 | 1× | 1× | normal |
| 2 | 2× | 2× | accelerated |
| 3 | 4× | 3× | maximum (emergency gear, deliberately inefficient) |

**Branch standard costs** (coins per unit at level 1): ground 3, naval 6, tactical_air 5, strategic_missile 8, air_defense 4.
**Strategic_missile and air_defense capacity = 0 for ALL countries in v1.1** (schema is forward-compatible; raising capacity is a pure data change).

**Engine flow (per country, per round):**
```
maintenance     = total_units × maintenance_per_unit × MAINTENANCE_MULTIPLIER
social_spending = social_baseline × revenue × social_pct
mil_spending    = Σ_branch (cap[branch] × unit_cost[branch] × cost_mult[level[branch]])
research_total  = nuclear_coins + ai_coins
total_spending  = maintenance + social_spending + mil_spending + research_total

# No percentage caps (removed 2026-04-10). Over-spending feeds the deficit cascade.
If total_spending > revenue:
  deficit → draw treasury → if insufficient: print money
  money_printed → inflation += (printed / GDP) × MONEY_PRINTING_INFLATION_MULT
  debt += deficit × DEFICIT_TO_DEBT
  # When the cascade can't fund full mil_spending, branch production is scaled
  # proportionally by affordability — NOT a hard cap, just available coins.
Else:
  treasury += surplus

# Social side-effects (linear deviation from 1.0):
stability_delta        = (social_pct - 1.0) × SOCIAL_STABILITY_MULT
political_support_delta = (social_pct - 1.0) × SOCIAL_SUPPORT_MULT

# R&D progress (per domain):
progress_delta = (coins / GDP) × RD_MULTIPLIER × rare_earth_factor
```

---

### A.7 MILITARY PRODUCTION (per CONTRACT_BUDGET v1.1 §6.2)

```
For each of 5 branches:
  units_produced = capacity[branch] × output_mult[level[branch]]
  coins_spent    = capacity[branch] × unit_cost[branch] × cost_mult[level[branch]]

# Scaling: when affordability < requested mil_spending, produced units are
# proportionally reduced. This is the deficit cascade in action — NOT a
# hard percentage cap.

Special:
  Cathay +1 strategic_missile/round (template flag).
  Naval auto +1/2 rounds if fleet ≥ 5 (only when no naval production this round).
```

---

### A.8 INFLATION

```
excess = max(0, prev_inflation - baseline)
new_excess = excess × 0.85   (15% natural decay)
new_excess += money_printed_effect
new_inflation = baseline + new_excess   (clamp [0, 500])
```

---

### A.9 ECONOMIC STATE TRANSITIONS

**Stress triggers (≥2 = stressed):** oil>150 & importer, inflation>baseline+15, growth<-1%, treasury≤0, stability<4, Formosa disrupted
**Crisis triggers (≥2 = crisis):** oil>200 & importer, inflation>baseline+30, growth<-3%, treasury≤0 & debt>10%GDP, Formosa 3+ rounds

**State machine:** normal ↔ stressed ↔ crisis ↔ collapse
- Down: fast (≥2 triggers). Up: slow (0-1 triggers for 2-3 consecutive rounds).

---

### A.10 MOMENTUM

```
Boosts: growth>2% (+0.15), normal state (+0.15), stability>6 (+0.15). Cap +0.30.
Crashes: crisis (-1.0), collapse (-2.0), growth<-2% (-0.5), oil>200 (-0.5), new war (-1.0)
Decay: -10% per round toward zero.
Range: [-5, +5]
```

---

### A.11 CONTAGION

```
If major economy (GDP≥30) enters crisis/collapse:
  For each trade partner with weight > 10%:
    partner_GDP × (1 - severity × weight × 0.02)
    partner_momentum -= 0.3
  severity: crisis=1.0, collapse=2.0
```

---

### A.12 DOLLAR CREDIBILITY

```
If Columbia prints money: credibility -= printed × 2.0
Else: credibility += 1.0 (recovery)
Range: [20, 100]
```

---

### A.13 MARKET INDEXES

Three regional indexes: Wall Street, Europa, Dragon. Each = weighted health score of component countries.

**Health score per country:** 100 base + GDP_growth_effect + inflation_penalty + sanctions_penalty + crisis_penalty + war_penalty + oil_shock + debt_ratio
**Index:** weighted_sum × 0.30 + previous × 0.70 (70% inertia). Range [0, 200].
**Market stress:** index<40 → -0.30 stability; index<70 → -0.10.

---

## B. POLITICAL ENGINE

### B.1 STABILITY (range 1.0–9.0)

```
delta = 0
+ positive inertia: +0.05 if stability 7-9
+ GDP growth > 2%: +min((growth-2)×0.08, 0.15)
+ GDP growth < -2%: +max(growth×0.15, -0.30)
+ social spending ≥ 100%: +0.05 (≥110%: +0.10)
+ social spending 70-85%: -0.15
+ social spending < 70%: -0.30
- war friction: -0.05 to -0.10 per round + casualties×0.2 + territory_lost×0.4
- war tiredness > threshold: -min(tiredness×0.04, 0.4)
+ defender democratic resilience: +0.15
- sanctions: -0.1 × level (diminishes after 4 rounds)
- inflation delta > 3: -(delta-3)×0.05; > 20: additional -(delta-20)×0.03; cap -0.50
- crisis state: stressed -0.10, crisis -0.30, collapse -0.50
- market stress: -0.10 or -0.30
- mobilization: -0.2 per level

Dampening:
  If NOT at war AND NOT heavy sanctions: negative delta × 0.5 (peacetime muting)
  If autocracy: negative delta × 0.75 (resilience)
  If autocracy + war + sanctions: +0.10 (siege adaptation)

new_stability = clamp(old + delta, 1.0, 9.0)
```

---

### B.2 POLITICAL SUPPORT (range 5.0–85.0)

**Democracy/Hybrid:**
```
delta = (growth - 2.0) × 0.8
      - casualties × 3.0
      + (stability - 6.0) × 0.5
      + crisis penalty: stressed -2, crisis -5, collapse -10
      + oil shock penalty (importers, if price>150): -(price-150)×0.05
      + election proximity penalties
      - war tiredness >2: -(tiredness-2) × 1.0
      - mean reversion: -(support-50) × 0.05
```

**Autocracy:**
```
delta = (stability - 6.0) × 0.8
      - perceived_weakness × 5.0
      + repression_effect
      + nationalist_rally
      - mean reversion
```

---

### B.3 WAR TIREDNESS (range 0–10)

```
At war: +0.20 (defender), +0.15 (attacker), +0.10 (ally)
  After 3 rounds: growth halves (adaptation)
Peace: decay × 0.80 per round (20% recovery)
```

---

### B.4 ELECTIONS

**Scheduled:** Columbia midterms R2, Ruthenia wartime R3-4, Columbia presidential R5.

```
ai_score = 50 + growth×10 + (stability-5)×5 - wars×5 - crisis_penalty + foreign_policy
final_pct = 50% × ai_score + 50% × player_vote
incumbent_wins = (final_pct ≥ 50)
```

---

### B.5 REVOLUTION

```
Trigger: stability ≤ 2 AND support < 20%
probability = 30% + (20-support)/100 + (3-stability)×10%
```

---

### B.6 HEALTH EVENTS (Elderly Leaders)

```
Eligible: Dealer (80, medical 0.9), Helmsman (73, 0.7), Pathfinder (73, 0.6)
After round 2: prob = (3% + (age-70)×1%) × (1 - medical×0.5)
If triggered: 15% death, 85% incapacitated 1-2 rounds
```

---

### B.7 COUP

```
Base: 15%. +25% if protest, +15% if stability<3, +10% if support<30%. Clamp [0,90%].
Success: new leader, old arrested, stability -2.
Failure: plotters exposed, stability -1.
```

---

### B.8 ASSASSINATION

```
Domestic: 30% base. International: 20% (Levantia: 50%). Detection: 100%. Attribution: 50%.
If hit: 50/50 kill vs survive. Martyr: +15 (kill) or +10 (survive) support.
Detection: domestic 50%. International: miss 70%, hit 40%.
```

### B.9 STATE TRANSITIONS

Two independent state machines running per country:

**Economic state** (determined by engine, affects GDP multiplier):
```
         ≥2 stress triggers          ≥2 crisis triggers        3 rounds of crisis
NORMAL ──────────────────→ STRESSED ──────────────────→ CRISIS ──────────────→ COLLAPSE
  ↑     0 triggers, 2 rounds   ↑    ≤1 trigger, 2 rounds  ↑   0 triggers, 3 rounds
  └─────────────────────────────┘────────────────────────────┘───────────────────────┘

Stress triggers (≥2 = stressed): oil>150 & importer, inflation>baseline+15,
  growth<-1%, treasury≤0, stability<4, Formosa disrupted.
Crisis triggers (≥2 = crisis): oil>200 & importer, inflation>baseline+30,
  growth<-3%, treasury≤0 & debt>10%GDP, Formosa 3+ rounds.
Down: fast (immediate on trigger count). Up: slow (2-3 consecutive rounds clear).
```

**Diplomatic state** — canonical 8-state bilateral relationship model (updated 2026-04-08):

| State | Meaning | Transitions |
|---|---|---|
| **allied** | Formal alliance, mutual defense | → friendly (dissolved) |
| **friendly** | Positive, cooperation | → allied (treaty), → neutral (drift) |
| **neutral** | No alignment | → friendly (cooperation), → tense (friction) |
| **tense** | Friction, diplomatic pressure | → hostile (escalation), → neutral (de-escalation) |
| **hostile** | Antagonism, sanctions | → military_conflict (attack), → tense (de-escalation) |
| **military_conflict** | Active combat — STICKY | → armistice (ceasefire), → peace (treaty) ONLY |
| **armistice** | Ceasefire signed | → peace (treaty), → military_conflict (breach) |
| **peace** | War formally ended | → friendly (over time), → neutral |

```
           one side attacks the other             ceasefire signed           peace treaty
... ──→ hostile ────────────────────→ military_conflict ─────────→ armistice ──────────→ peace
                                           ↑                         │
                                           │     breach (attack)     │
                                           ←────────────────────────←┘ (auto + all notified)
                                           │
                                           │    capitulation
                                           └──────────────────→ peace
```

**Key rules:**
- `military_conflict` is STICKY — only exits via signed agreement (armistice or peace treaty). No automatic cooling.
- Armistice breach → auto-return to `military_conflict` + global notification.
- War is DETECTED from combat, not declared. Public war declarations are optional political theater, not a game mechanic.
- DB dual-column: `relationship` = starting/reference value (template); `status` = live engine state (8-state model above). Engine reads `status`.

**Political stability thresholds** (triggers domestic events):
```
8-10: Stable (no risk)
6-7:  Strained (coup risk flag raised)
4-5:  Crisis (protest risk)
2-3:  Severe crisis (automatic protest risk, revolution possible)
1:    Failed state (revolution likely, capitulation check)
```

---

## C. TECHNOLOGY ENGINE

### C.1 R&D ADVANCEMENT

```
progress = (investment / GDP) × 0.8 × rare_earth_factor
Nuclear thresholds: L0→L1: 0.60, L1→L2: 0.80, L2→L3: 1.00
AI thresholds: L0→L1: 0.20, L1→L2: 0.40, L2→L3: 0.60, L3→L4: 1.00
```

### C.2 RARE EARTH RESTRICTIONS

```
R&D penalty: -15% per restriction level. Floor: 40% (max -60%).
```

### C.3 AI BENEFITS

| Level | GDP growth bonus | Combat die bonus |
|---|---|---|
| L0-L1 | 0% | 0 |
| L2 | +0.5% | 0 |
| L3 | +1.5% | +1 |
| L4 | +3.0% | +2 (50% chance flag set at level-up) |

**Deliberate deviation from SEED:** SEED spec says L0-L3 = 0, L4 probabilistic. We keep the code values (L2: +0.5%, L3: +1.5%, L4: +3.0% fixed) because: (1) no NOUS/Pass 2 exists yet to grant probabilistic bonuses, (2) values are small but make AI R&D investment meaningful, (3) combat bonuses (+1/+2) are unchanged. Decision: Marat 2026-04-07.

### C.4 TECH TRANSFER

```
Donor must be ≥1 level ahead. Nuclear: +0.20 progress. AI: +0.15 progress.
```

### C.5 PRIVATE AI INVESTMENT

```
Personal coins invested at 50% efficiency (0.4 multiplier vs government's 0.8).
MATCHING BONUS (hidden mechanic): if BOTH private AND government invest in AI
in the same round → combined effect is 2× on AI progress speed.
This synergy is hinted in role briefings, not publicly documented.
```

### C.6 NUCLEAR TECH CONFIRMATION

```
R&D progression: invest → progress fills → threshold reached → status: "ready for test"
  → successful test → tier CONFIRMED → weapons unlocked

Test success probability:
  Below T2: 70%
  T2 and above: 95%
All Template-customizable.

Countries with pre-defined nuclear levels in Template (Columbia T3, Sarmatia T3,
Cathay T3, etc.) are CONFIRMED by default — no test needed.
```

---

## D. COMBAT PROBABILITIES

Full mechanics in CARD_ACTIONS.md. This section: canonical numbers only.

### D.1 Ground Combat (RISK dice, iterative)

```
Attacker: min(3, N_attackers) dice
Defender: min(2, N_defenders) dice
Compare highest vs highest, second vs second. Ties → defender.
Loop until one side has 0 units.
Chain attack: after winning, can attack next adjacent hex (leave ≥1 behind).
```

**Dice modifiers (applied to highest die per side per exchange):**

| Modifier | Side | Value | Condition | Applies to |
|---|---|---|---|---|
| AI L4 | Either | +1 | ai_level==4 AND 50% flag set | Ground + Naval |
| Low morale | Either | -1 | Stability ≤ 3 | Ground + Naval |
| Die Hard terrain | Defender | +1 | Hex has die_hard flag | Ground only |
| Air support | Defender | +1 | Defender has tactical_air on hex | Ground only |
| Amphibious | Attacker | -1 | Attack crosses sea→land | Ground only |

**Die Hard + Air support STACK** (max positional bonus = +2).

**Win rates (single 1v1 comparison):**

| Scenario | Attacker wins |
|---|---|
| No modifiers | 42% |
| Defender +1 | 28% |
| Defender +2 (die hard + air) | 17% |
| Attacker -1 (amphibious) vs +2 | 8% |
| Attacker +1 (AI L4) vs no modifier | 58% |

### D.2 Air Strike

```
Per attacking air unit, resolved in sequence:
1. If AD covers target zone → 15% chance attacker is DOWNED (unit destroyed, attack fails)
2. If not downed → roll for hit:
     No AD: 12%
     AD present: 6% (halved)
3. On hit → one defender unit destroyed (prefer non-AD)

Range: ≤2 hexes from launcher. Template-customizable.
No air superiority bonus. No clamp.
All probabilities Template-customizable.
```

### D.3 Naval Combat (1v1 dice)

```
One ship vs one ship. Each rolls 1d6 + modifiers. Higher wins. Ties → defender.
Loser destroyed. No movement after attack. Ships stay where they are.
Modifiers: AI L4 (+1) and low morale (-1) only. No fleet advantage bonus.
To destroy a fleet: attack multiple times.
```

### D.4 Naval Bombardment

```
Each naval unit fires once per round at adjacent land hex.
10% chance per unit to destroy one random ground unit on target hex.
No AD interaction for bombardment.
Template-customizable.
```

### D.5 Ballistic Missile (Conventional)

```
Range: T1: ≤2 hex. T2: ≤4 hex. T3: global. Template-customizable.
Missile consumed on launch (disposable).

AD interception: each AD covering target hex rolls 50% to stop the missile.
  If stopped → missile destroyed, no effect.
  If not stopped → roll for hit:

Target choice determines effect:
  Military units: 70% hit → destroy 1 unit
  Infrastructure: 70% hit → -2% target GDP
  Nuclear site: 70% hit → halve nuclear R&D progress
  AD unit: 40% hit → targeted AD destroyed

All probabilities Template-customizable.
```

### D.6 Nuclear Missile

```
Same missile units as conventional. Warhead choice at launch.
Requires CONFIRMED nuclear tier + 3-way authorization.

Range: T1: ≤2 hex. T2: ≤4 hex. T3: global (same as conventional).

Interception:
  T1 (midrange): local AD rolls 50% per unit (same as conventional)
  T2/T3 (strategic): T3+ nations voluntarily decide to intercept (10 min window)
    Each T3+ nation: 25% per AD unit they own
    Target country own AD: automatic 50% per unit
  Launcher does NOT learn who intercepted.

Hit: 80% base (no AD halving for T2/T3 — interception replaces it).

On hit:
  50% of ALL military on target hex destroyed (including own if present)
  30% × (1 / target_country_hex_count) of target GDP destroyed
  If hex has nuclear site → site automatically destroyed (100%)
  Canonical nuclear site hexes: Persia (7,13), Choson (3,18). Source: sim_templates.map_config.nuclear_sites + map_config.py::NUCLEAR_SITES.

T3 salvo aggregate (if ≥1 nuclear hit in salvo of 3+ missiles):
  Global stability: -1.5
  Target country stability: -2.5
  Leader death roll: 1/6 (target nation, single roll per salvo)

All Template-customizable.
```

### D.7 Nuclear Test

```
Underground:
  Success: below T2: 70%, T2+: 95%
  Alert: T3+ countries only
  Stability: global -0.2

Surface:
  Success: below T2: 70%, T2+: 95%
  Alert: GLOBAL (all countries) + 10 min real-time
  Economic: -5% own GDP
  Stability: global -0.4, adjacent hex countries -0.6 additional

Both: political support +5 (nationalist rally). On success: tier CONFIRMED.
All Template-customizable.
```

### D.8 Blockade Economic Impact

```
Gulf Gate / Caribe Passage:
  Partial: -25% affected producers' oil export volume
  Full: -50% affected producers' oil export volume
  → reduced supply → oil price rises via supply/demand (ratio^2.5)
  → affected producers lose oil revenue
  → importers pay more → GDP drag + inflation

Formosa Strait:
  Partial:
    Formosa GDP: -10%
    All countries GDP: -10% × country's tech sector size
    AI R&D progress: FROZEN globally (no country advances this round)
  Full:
    Formosa GDP: -20%
    All countries GDP: -20% × country's tech sector size
    AI R&D progress: FROZEN globally

All Template-customizable.
```

### D.9 Covert Operations

| Op | Success | Effect on success | Detection | Attribution |
|---|---|---|---|---|
| Intelligence | always returns report | LLM report, 10-30% noise (complexity-scaled) | 30% | 30% |
| Sabotage | 50% | infrastructure: -1 coin / nuclear: -30% progress / military: 50% destroy 1 unit | 50% | 50% |
| Propaganda | 55% | ±0.3 stability (own or foreign, boost or destabilize) | 25% | 20% |
| Election meddling | 40% | ±2-5% political support for chosen candidate | 45% | 50% |

Modifiers: AI level +5%/level, repeated ops -5% success +10% detection. Clamp [5%, 95%].

### D.10 Domestic Political

```
Assassination:
  Domestic: 30%
  International: 20% (Levantia: 50%)
  Detection: 100% (always known). Attribution: 50%.
  On hit: 50/50 kill vs survive. Martyr: +15 (kill) / +10 (survive) support.

Coup:
  Base: 15%. +25% protest, +15% stability<3, +5% stability 3-4, +10% support<30%.
  Clamp [0%, 90%].
  Success: initiator → HoS, old HoS arrested, stability -2.
  Failure: both exposed, stability -1.

Mass Protest (elite-led revolution):
  Trigger: stability ≤ 2 AND support < 20%.
  Probability: 30% + (20-support)/100 + (3-stability)×10%. Clamp [15%, 80%].
  Success: regime change, leader takes power, stability +1, support +20.
  Failure: leader imprisoned, stability -0.5, support -5.

All Template-customizable.
```

---

## E. ALL CONSTANTS TABLE

### Economic Engine

| Constant | Value | Domain |
|---|---|---|
| OIL_BASE_PRICE | 80.0 | Oil |
| OIL_PRICE_FLOOR | 15.0 | Oil |
| OIL_SOFT_CAP | 200.0 | Oil |
| OIL_INERTIA (prev/new) | 0.3 / 0.7 | Oil |
| OIL_S_D_EXPONENT | 2.5 | Oil |
| OIL_BLOCKADE partial/full | 0.25 / 0.50 | Oil |
| SANCTIONS_MAX_DAMAGE | 0.87 | Sanctions |
| TARIFF_K | 0.54 | Tariffs |
| TARIFF_IMPOSER_FRACTION | 0.50 | Tariffs |
| TARIFF_REVENUE_RATE | 0.075 | Tariffs |
| TARIFF_INFLATION_RATE | 12.5 | Tariffs |
| MAINTENANCE_MULTIPLIER | 3.0 | Budget |
| MONEY_PRINTING_INFL_MULT | 60.0 | Budget |
| DEFICIT_TO_DEBT_RATE | 0.15 | Budget |
| INFLATION_DECAY | 0.85 | Inflation |
| GDP_FLOOR | 0.5 | GDP |
| MOMENTUM range | [-5, +5] | Confidence |
| CONTAGION_THRESHOLD | GDP ≥ 30 | Contagion |
| DOLLAR_CRED erosion/recovery | 2.0 / 1.0 | Dollar |
| DOLLAR_CRED range | [20, 100] | Dollar |
| MARKET_INDEX inertia | 0.70 prev | Markets |

### Political Engine

| Constant | Value | Domain |
|---|---|---|
| STABILITY range | [1.0, 9.0] | Stability |
| SUPPORT range | [5.0, 85.0] | Support |
| WAR_TIREDNESS range | [0, 10] | War tiredness |
| COUP base prob | 15% | Coup |
| ASSASSINATION domestic | 30% | Assassination |
| ASSASSINATION international | 20% (Levantia: 50%) | Assassination |
| ASSASSINATION detection | 100% | Assassination |
| ASSASSINATION attribution | 50% | Assassination |
| MASS_PROTEST base prob | 30% | Revolution |
| MASS_PROTEST clamp | [15%, 80%] | Revolution |

### Technology Engine

| Constant | Value | Domain |
|---|---|---|
| RD_MULTIPLIER | 0.8 | R&D |
| PRIVATE_INVESTMENT_MULT | 0.4 (50% of govt) | R&D |
| PRIVATE_GOVT_MATCH_BONUS | 2.0× speed | R&D (hidden) |
| RARE_EARTH_PENALTY | -15%/level, floor 40% | R&D |
| NUCLEAR_TEST_SUCCESS below T2 | 70% | Nuclear |
| NUCLEAR_TEST_SUCCESS T2+ | 95% | Nuclear |
| NUCLEAR_TEST_STABILITY underground | -0.2 global | Nuclear |
| NUCLEAR_TEST_STABILITY surface | -0.4 global, -0.6 adjacent | Nuclear |
| NUCLEAR_TEST_GDP_COST surface | -5% own GDP | Nuclear |

### Combat

| Constant | Value | Domain |
|---|---|---|
| AIR_STRIKE base hit | 12% | Air |
| AIR_STRIKE with AD | 6% | Air |
| AIR_STRIKE attacker downed by AD | 15% | Air |
| AIR_STRIKE range | ≤2 hex | Air |
| MISSILE_CONV hit | 70% | Missile |
| MISSILE_CONV AD intercept per unit | 50% | Missile |
| MISSILE_CONV range | T1:≤2, T2:≤4, T3:global | Missile |
| MISSILE_NUC hit | 80% | Nuclear missile |
| MISSILE_AD_target hit | 40% | Missile vs AD |
| T3_INTERCEPTION per AD unit | 25% | Nuclear interception |
| BOMBARDMENT per unit | 10% | Naval |
| NUC_DAMAGE military on hex | 50% destroyed | Nuclear |
| NUC_DAMAGE GDP per hex | 30% / hex_count | Nuclear |
| T3_SALVO global stability | -1.5 | Nuclear salvo |
| T3_SALVO target stability | -2.5 | Nuclear salvo |
| T3_SALVO leader death | 1/6 | Nuclear salvo |

### Blockade Impact

| Constant | Value | Domain |
|---|---|---|
| GULF/CARIBE partial production loss | 25% | Blockade |
| GULF/CARIBE full production loss | 50% | Blockade |
| FORMOSA partial GDP (Formosa) | -10% | Blockade |
| FORMOSA full GDP (Formosa) | -20% | Blockade |
| FORMOSA partial GDP (all, ×tech_sector) | -10% × tech_size | Blockade |
| FORMOSA full GDP (all, ×tech_sector) | -20% × tech_size | Blockade |
| FORMOSA AI progress freeze | global, any blockade level | Blockade |

### Covert Ops

| Constant | Value | Domain |
|---|---|---|
| INTELLIGENCE detection/attribution | 30% / 30% | Covert |
| SABOTAGE success | 50% | Covert |
| SABOTAGE detection/attribution | 50% / 50% | Covert |
| PROPAGANDA success | 55% | Covert |
| PROPAGANDA detection/attribution | 25% / 20% | Covert |
| PROPAGANDA effect | ±0.3 stability | Covert |
| ELECTION_MEDDLING success | 40% | Covert |
| ELECTION_MEDDLING detection/attribution | 45% / 50% | Covert |
| COVERT AI level bonus | +5%/level | Covert |
| COVERT repeated ops penalty | -5% success, +10% detection | Covert |

---

## F. SEED FIDELITY REPORT

Comparison of implemented code against SEED_D8_ENGINE_FORMULAS_v1.md (the canonical formula spec designed and calibrated in sessions 2026-04-02/03).

### Overall: 98% EXACT match

| Domain | Status | Confidence |
|---|---|---|
| Oil price | **EXACT** | 100% |
| GDP growth | **1 inconsistency** (see below) | 95% |
| Revenue | **EXACT** | 100% |
| Budget / inflation / debt | **EXACT** | 100% |
| Political (stability/elections/coups) | **EXACT** | 100% |
| Transactions | **EXACT** | 100% |
| Live action / covert ops | **EXACT** | 100% |
| Processing order | **EXACT** | 100% |
| Market indexes | **PARTIAL** — constants defined, stability integration incomplete | 85% |

All F1-F104 calibration changes (104 formula adjustments from 15 parameter reviews) were faithfully ported. Oil inertia 0.3/0.7, price floor $15, OPEC 2× lever, tariff K=0.54, sanctions S-curve, maintenance 3× multiplier, money printing 60×, inflation decay 0.85, deficit-to-debt 0.15 — all match exactly.

### Two issues found

**Issue 1: AI_LEVEL_TECH_FACTOR (INCONSISTENCY)**

| AI Level | SEED spec (F1-F104) | Code | Delta |
|---|---|---|---|
| L0 | 0% | 0% | match |
| L1 | 0% | 0% | match |
| L2 | **0%** | **+0.3%** | code adds unspecified boost |
| L3 | **0%** | **+1.0%** | code adds unspecified boost |
| L4 | probabilistic (AI Pass 2) | **+2.5% flat** | code is deterministic, spec is probabilistic |

SEED explicitly says "L0-L3 = 0, L4 probabilistic (delegated to AI Pass 2)." Code gives L2-L3 small GDP boosts that weren't in the spec.

**Decision needed:** Either update code to match SEED (remove L2-L3 boosts), or update SEED to document this calibration choice. [M] Marat to decide.

**Issue 2: Market index → stability integration (PARTIAL)**

Market index constants (Wall Street, Europa, Dragon with component weights) are fully defined in economic.py. The `calc_stability()` function accepts `market_stress` as an input parameter. But the orchestrator doesn't compute regional indexes and pass them through yet.

**Impact:** Market crashes don't currently affect country stability. Low priority — the economic engine's direct GDP/inflation effects already drive stability. Market stress would add a secondary channel.

### Everything else: EXACT

Oil price (supply/demand/blockade/war premium/soft cap/inertia), GDP (structural/cyclical/shocks/crisis amplifier), revenue (tax+oil-debt-inflation-war-sanctions), budget (maintenance×3/social/military/tech/deficit cascade), inflation (decay/money printing/oil/tariff), debt service, economic state transitions, momentum, contagion, dollar credibility, stability (GDP/social/war/sanctions/inflation/crisis factors + autocracy resilience + peacetime dampening), political support (democracy/autocracy split), war tiredness (attack/defend/adaptation/decay), elections (Columbia/Ruthenia), revolution, health events, coups, assassinations — all match the SEED F1-F104 spec exactly.
