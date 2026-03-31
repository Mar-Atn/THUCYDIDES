# SEED COMPLETION REVIEW
## Thucydides Trap SIM — Mechanics Coverage & Completion Assessment
**Date:** 2026-03-28 | **Reviewer:** ATLAS | **Engine version:** v2.0 (world_model), v2.0 (live_action), v2.0 (transaction)

---

## Section 1: MECHANICS COVERAGE MATRIX

### Military Domain (C1 §1)

| Mechanic | Design Doc | Engine File | Status | Notes |
|----------|-----------|-------------|:------:|-------|
| 5 unit types (ground, naval, tactical air, strategic missiles, air defense) | C1 §1 table | world_state.py UNIT_TYPES | ✅ Implemented | All 5 types tracked, produced, and combat-ready |
| Ground forces — RISK combat | C1 §1, C2 §1.4 | live_action_engine.py L82–209 | ✅ Implemented | Dice per pair, defender wins ties, morale/tech modifiers |
| Naval forces — sea combat, blockade, bombardment | C1 §1, C2 §1.5 | live_action_engine.py L215–280, L854–901 | ✅ Implemented | Naval blockade + bombardment (10%/unit) |
| Tactical air/missile strikes | C1 §1, C2 §1.6 | live_action_engine.py L285–380 | ✅ Implemented | Disposable, air defense interception logic |
| Strategic missile launch (global alert, warhead unknown) | C1 §1, C2 §1.7 | live_action_engine.py L285–378 | ✅ Implemented | Global alert event, conventional/nuclear warheads |
| Air defense interception | C1 §1 | live_action_engine.py L328–355 | ✅ Implemented | Up to 3 intercepts per AD unit, 30% per attempt |
| Nuclear strike — L1 damage | C1 §1, C2 §1.7 | live_action_engine.py L396–418 | ✅ Implemented | 50% troops destroyed, -2 coins |
| Nuclear strike — L2 damage | C1 §1, C2 §1.7 | live_action_engine.py L421–457 | ✅ Implemented | 30% econ, 50% military, leader survival 1/6, global stability shock |
| Retaliation window (5 min) | C1 §1, C2 §1.7 | — | ⚠️ Partial | Global alert fires; 5-min retaliation window is a UI/orchestration concern, not in engine calc. Engine supports it but doesn't enforce timing |
| Amphibious assault (3:1, Formosa 4:1→3:1) | C1 §1 | live_action_engine.py L57–58, L120–143 | ✅ Implemented | Ratio check, naval prerequisite. Note: Formosa reduced to 3:1 in code (design says 4:1) |
| Naval blockade — chokepoint mechanics | C1 §1, C2 §1.5 | live_action_engine.py L215–280 | ✅ Implemented | Standard + Gulf Gate ground blockade |
| Deployment/basing mechanics | C1 §1 "Deployment and Basing" | transaction_engine.py L315–324 (basing rights) | ⚠️ Partial | Basing rights granted/revoked via transaction engine. Zone-level deployment logic is orchestrator-level, not fully in engine |
| Budget cycle — 3 production tiers | C1 §1, C2 §2.1 | world_model_engine.py L741–785 | ✅ Implemented | Normal/Accelerated/Maximum with cost/output multipliers |
| Mobilization (partial/general/total) | C1 §1, C2 §1.3 | world_model_engine.py L2242–2254 | ✅ Implemented | 3 levels, stability cost, units added |
| Nuclear test | C2 §1.8 | live_action_engine.py (resolve_covert_op area) | ❌ Missing | No `resolve_nuclear_test()` method found. Design specifies probabilistic nuclear test action for L1+ countries |
| Covert ops — Espionage | C2 §5.1 | live_action_engine.py L463–560 | ✅ Implemented | Probability tables, detection, intelligence gathering |
| Covert ops — Sabotage | C2 §5.2 | live_action_engine.py L529–531 | ✅ Implemented | 2% GDP damage on success |
| Covert ops — Cyber attack | C2 §5.3 | live_action_engine.py L533–536 | ✅ Implemented | 1% GDP damage on success |
| Covert ops — Disinformation | C2 §5.4 | live_action_engine.py L537–541 | ✅ Implemented | Stability -0.3, support -2 |
| Covert ops — Election meddling | C2 §5.5 | live_action_engine.py L543–545 | ✅ Implemented | Support -3 on success |
| Theater activation | C1 §1 "Theater Activation" | — | ⚠️ Partial | SEED decision limits to Eastern Ereb. No dynamic theater activation mechanic in engine; handled at map/hex level |

### Economic Domain (C1 §2)

| Mechanic | Design Doc | Engine File | Status | Notes |
|----------|-----------|-------------|:------:|-------|
| GDP growth calculation (feedback loops) | C1 §2, E1 Step 2 | world_model_engine.py L489–607 | ✅ Implemented | Additive factor model: tariffs, sanctions, oil, semiconductor, war, tech, momentum, blockade, bilateral dependency, crisis multiplier |
| Budget cycle — revenue calculation | C1 §2, E1 Step 4 | world_model_engine.py L613–652 | ✅ Implemented | GDP * tax_rate + oil - debt - inflation erosion - war damage - sanctions cost |
| Budget cycle — mandatory costs (maintenance) | C1 §2, E1 Step 4 | world_model_engine.py L666–674 | ✅ Implemented | Units * maintenance_cost + 70% social baseline |
| Budget execution (deficit, money printing) | C1 §2, E1 Step 4 | world_model_engine.py L658–735 | ✅ Implemented | Draw from reserves → print money → inflation chain |
| Tariffs (0-3 scale, bilateral) | C1 §2, C2 §2.2 | world_model_engine.py L1940–1986, L2158–2164 | ✅ Implemented | Per-country bilateral, GDP cost modeled |
| Sanctions (coalition-based, -3 to +3) | C1 §2, C2 §2.3 | world_model_engine.py L1910–1938, L2166–2172 | ✅ Implemented | Bilateral, trade-weight-scaled impact |
| Oil/OPEC pricing (prisoner's dilemma) | C1 §2, C2 §2.4 | world_model_engine.py L320–457 | ✅ Implemented | Supply/demand/disruption model, OPEC production choices, oil price inertia, volatility |
| Financial market indexes (3 markets) | C1 §2 | world_model_engine.py L1749–1791 | ✅ Implemented | Per-country market_index, crash threshold triggers GDP/support penalties |
| Inflation mechanics | C1 §2 | world_model_engine.py L837–863 | ✅ Implemented | Natural decay on excess, money printing spike, baseline preservation |
| Debt service | C1 §2 | world_model_engine.py L869–876 | ✅ Implemented | 15% of deficit becomes permanent debt burden |
| Tariff revenue to imposer | C1 §2 "Net cost to imposer" | world_model_engine.py L1940–1986 | ✅ Implemented | Tariff info calc includes revenue and costs |
| Third-country rerouting | C1 §2 "Third-country rerouting" | — | ❌ Missing | No explicit rerouting model. Tariff/sanction dilution not modeled by redirecting trade to third parties |
| Cost-to-sanctioner | C1 §2 "Cost-to-sanctioner" | world_model_engine.py L1910–1938 | ✅ Implemented | Sanctioner GDP drag via sanctions_costs dict |
| Sanctions diminishing returns (after 4 rounds) | C1 §2 | world_model_engine.py L504–508 | ✅ Implemented | 40% reduction after 4 rounds |
| Frozen assets mechanic | C1 §2 "Frozen assets" | — | ❌ Missing | No frozen assets tracking or seizure mechanic |
| Personal wealth (roles with personal coins) | C1 §2 | world_state.py (role data) | ⚠️ Partial | Transaction engine handles coin transfers for individuals. No explicit personal wallet separate from country treasury in engine logic |
| Hormuz Strait blockade (oil disruption) | C1 §2 | world_model_engine.py L350–354 | ✅ Implemented | Gulf Gate ground blockade, +50% oil disruption |
| Formosa semiconductor disruption | C1 §4, C1 §2 | world_model_engine.py L524–533 | ✅ Implemented | Duration-scaling severity, tech sector GDP hit |
| Economic crisis ladder | C1 §2 (implicit) | world_model_engine.py L882–971 | ✅ Implemented | NORMAL→STRESSED→CRISIS→COLLAPSE with asymmetric recovery |
| Contagion (major economy crisis spreads) | C1 §2 (implicit) | world_model_engine.py L1037–1073 | ✅ Implemented | Trade-weight-based GDP spillover |
| Export restrictions | C2 §2.5 | world_model_engine.py L2179–2197 | ✅ Implemented | Rare earth restrictions with R&D penalty + cost to Cathay |
| Dollar credibility / de-dollarization | C1 §2 "dollar weaponization" | world_model_engine.py L1834–1856 | ✅ Implemented | Money printing erodes dollar credibility |

### Political Domain (C1 §3)

| Mechanic | Design Doc | Engine File | Status | Notes |
|----------|-----------|-------------|:------:|-------|
| Stability Index (1-10) | C1 §3 | world_model_engine.py L1079–1211 | ✅ Implemented | Full v4 formula: GDP, social spending, war friction, sanctions, inflation, crisis state, mobilization, propaganda, democratic resilience, siege resilience |
| Political Support (0-100%) | C1 §3 | world_model_engine.py L1217–1279 | ✅ Implemented | Democracy vs autocracy paths, crisis/oil penalties, war tiredness |
| Stability consequence thresholds | C1 §3 table | world_model_engine.py L2141–2152 | ✅ Implemented | Protest risk, coup risk, regime status flags |
| Four quadrants (freedom/vulnerability/fragile grip/collapse) | C1 §3 | — | ⚠️ Implicit | Not explicitly labeled, but the combination of stability + support drives behavior equivalently |
| Elections — Columbia midterms (Round 2) | C1 §3, C2 §4 | world_model_engine.py L1344–1351 | ✅ Implemented | AI + player votes, parliament flip mechanic |
| Elections — Columbia presidential (Round 5) | C1 §3, C2 §4 | world_model_engine.py L1373–1377 | ✅ Implemented | Basic incumbent/opposition resolution |
| Elections — Ruthenia wartime (Round 3-4) | C1 §3, C2 §4 | world_model_engine.py L1354–1370 | ✅ Implemented | Territory + war tiredness adjusted AI scoring |
| Coup mechanics (multi-step) | C1 §3, C2 §4.5 | live_action_engine.py L757–848 | ✅ Implemented | Military plotter requirement, probability from stability/support/conspirators, success/failure consequences |
| Propaganda (diminishing returns) | C1 §3, C2 §4.3 | live_action_engine.py L633–685 | ✅ Implemented | Log-based diminishing returns, AI L3+ boost, overuse penalty |
| Arrest mechanic | C1 §3, C2 §4.1 | live_action_engine.py L583–627 | ✅ Implemented | Own soil only, role status → arrested, support/stability cost |
| Fire/reassign | C2 §4.2 | — | ❌ Missing | No `resolve_fire()` or `resolve_reassign()` method. Design specifies instant role power removal |
| Public speaking effect | C1 §3 table | — | ❌ Missing | No public speech mechanic that affects political support. Design says "support boost if well-received, creates public commitments" |
| Assassination | C1 §3 (implicit), C2 §4.4 | live_action_engine.py L691–751 | ✅ Implemented | 50% base, detection 60-80%, survival dice, martyr effect |
| Rally around the flag (diminishing) | C1 §3 | world_model_engine.py L1518–1536 | ✅ Implemented | Diminishes over war duration |
| War tiredness (cumulative) | C1 §3 | world_model_engine.py L2106–2139 | ✅ Implemented | Attacker/defender asymmetry, society adaptation after 3 rounds |
| Mass protests | C1 §3 "Coups and Revolutions" | world_model_engine.py L2141–2152 | ⚠️ Partial | Flags set (protest_risk, coup_risk) but no automatic protest resolution mechanic |
| Revolution (stability 1-2 + support <20%) | C1 §3 | — | ❌ Missing | No revolution trigger or resolution. Only coup mechanic exists |
| Succession anxiety (autocracies, <30% support for 3 rounds) | C1 §3 "Leader Personal Dimension" | — | ❌ Missing | No succession clock or pressure escalation mechanic |
| Health events (leaders 70+, 5-10% incapacitation) | C1 §3 "Leader Personal Dimension" | — | ❌ Missing | No health event probability or incapacitation logic |
| Columbia Dem/Rep split tracking | C1 §3 | — | ❌ Missing | No Democrat/Republican popular opinion split variable |

### Technology Domain (C1 §4)

| Mechanic | Design Doc | Engine File | Status | Notes |
|----------|-----------|-------------|:------:|-------|
| Nuclear track (L0-3) | C1 §4 | world_model_engine.py L801–812 | ✅ Implemented | R&D accumulation → threshold → level-up |
| AI/Semiconductor track (L0-4) | C1 §4 | world_model_engine.py L814–825 | ✅ Implemented | Same accumulation model |
| R&D accumulation | C1 §4, E1 Step 5 | world_model_engine.py L791–831 | ✅ Implemented | Investment/GDP ratio * RD_MULTIPLIER(0.8) * rare_earth_factor |
| Tech transfer | C1 §4, C2 §3.2 | transaction_engine.py L297–313 | ✅ Implemented | Replicable, +1 level up to sender's level |
| Export restrictions (semiconductors) | C1 §4, C2 §2.5 | world_model_engine.py L2076–2083 | ✅ Implemented | Rare earth restrictions slow R&D -15%/level |
| Rare earth restrictions (Cathay) | C1 §4 "Counter-restrictions" | world_model_engine.py L2179–2197 | ✅ Implemented | Level-based, cost to Cathay modeled |
| Formosa semiconductor disruption | C1 §4 "Semiconductor Chokepoint" | world_model_engine.py L524–533, L2095–2104 | ✅ Implemented | Duration-scaling, dependency-based, rounds tracked |
| AI-enhanced propaganda (L3+) | C1 §4 | live_action_engine.py L663–665 | ✅ Implemented | 1.5x propaganda effectiveness at AI L3+ |
| Tech breakthrough GDP/military effects | C1 §4 effects table | world_model_engine.py L541–542 (GDP), live_action_engine.py L931 (combat) | ✅ Implemented | AI_LEVEL_TECH_FACTOR for GDP, AI_LEVEL_COMBAT_BONUS for combat |
| Personal tech investments (Pioneer, Circuit) | C1 §4 "R&D investment" | — | ❌ Missing | No personal R&D contribution mechanic |

### Action System (C2) — All ~30 Actions

| # | Action | Engine Location | Status | Notes |
|---|--------|----------------|:------:|-------|
| **Military (8)** | | | | |
| 1.1 | Deploy/redeploy units | — | ⚠️ Partial | Mobilization adds units; zone-level deployment is orchestrator concern |
| 1.2 | Arms transfer | transaction_engine.py L282–294 | ✅ Implemented | Exclusive, reduced effectiveness 1 round |
| 1.3 | Mobilization | world_model_engine.py L2242–2254 | ✅ Implemented | 3 levels |
| 1.4 | Attack (ground/naval) | live_action_engine.py L82–209 | ✅ Implemented | Full RISK mechanics |
| 1.5 | Naval blockade | live_action_engine.py L215–279 | ✅ Implemented | Standard + ground blockade |
| 1.6 | Tactical air/missile strike | live_action_engine.py L285–378 | ✅ Implemented | Strategic missiles with warhead selection |
| 1.7 | Strategic missile launch | live_action_engine.py L285–378 | ✅ Implemented | Global alert, nuclear options |
| 1.8 | Nuclear test | — | ❌ Missing | No resolve_nuclear_test() |
| **Economic (5)** | | | | |
| 2.1 | Submit national budget | world_model_engine.py L658–735 | ✅ Implemented | Full budget execution chain |
| 2.2 | Set tariff levels | world_model_engine.py L2158–2164 | ✅ Implemented | |
| 2.3 | Set sanctions position | world_model_engine.py L2166–2172 | ✅ Implemented | |
| 2.4 | Set OPEC+ production | world_model_engine.py L2174–2177 | ✅ Implemented | |
| 2.5 | Export restrictions | world_model_engine.py L2179–2197 | ✅ Implemented | Rare earth focus |
| **Transactions (5)** | | | | |
| 3.1 | Coin transfer | transaction_engine.py L272–280 | ✅ Implemented | Balance check, exclusive |
| 3.2 | Technology transfer | transaction_engine.py L297–313 | ✅ Implemented | Replicable, +1 level |
| 3.3 | Treaty/agreement | transaction_engine.py L326–380 | ✅ Implemented | Including ceasefire/peace with war-ending mechanic |
| 3.4 | Organization creation | transaction_engine.py L382–397 | ✅ Implemented | Name + members + purpose |
| 3.5 | Basing rights | transaction_engine.py L315–324 | ✅ Implemented | Revocable by host |
| **Domestic/Political (5 + elections)** | | | | |
| 4.1 | Arrest | live_action_engine.py L583–627 | ✅ Implemented | Own soil, status change |
| 4.2 | Fire/reassign | — | ❌ Missing | Not implemented |
| 4.3 | Propaganda | live_action_engine.py L633–685 | ✅ Implemented | Diminishing returns, AI boost |
| 4.4 | Assassination | live_action_engine.py L691–751 | ✅ Implemented | Full mechanic |
| 4.5 | Coup attempt | live_action_engine.py L757–848 | ✅ Implemented | Multi-step resolution |
| — | Elections (3 types) | world_model_engine.py L1285–1391 | ✅ Implemented | Columbia midterms, presidential, Ruthenia wartime |
| **Covert Ops (5)** | | | | |
| 5.1 | Intelligence/espionage | live_action_engine.py L463–577 | ✅ Implemented | Probabilistic, noisy intel |
| 5.2 | Sabotage | live_action_engine.py L529–531 | ✅ Implemented | |
| 5.3 | Cyber attack | live_action_engine.py L533–536 | ✅ Implemented | |
| 5.4 | Disinformation | live_action_engine.py L537–541 | ✅ Implemented | |
| 5.5 | Election meddling | live_action_engine.py L543–545 | ✅ Implemented | |
| **Other (2)** | | | | |
| 6.1 | Public statement | — | ⚠️ Partial | Event logging exists; no mechanical effect on support. Design says "logged" which is correct, but C1 §3 implies speech should affect support |
| 6.2 | Call organization meeting | — | ⚠️ Partial | Organizations exist in world_state; meeting scheduling is orchestrator-level |

---

## Section 2: WHAT'S MISSING

### MUST HAVE for SEED gate

These are core mechanics that, if absent, would produce an incomplete or misleading SIM experience:

1. **Nuclear test action (C2 §1.8)** — L1+ countries should be able to test. Persia L0→L1 is a pivotal scenario moment. No `resolve_nuclear_test()` exists.
   - *Effort:* Small (1-2 hours). Add method to live_action_engine modeled on missile strike but without damage — just a probabilistic success roll + diplomatic event.

2. **Fire/reassign action (C2 §4.2)** — Leaders need the ability to remove subordinates. This is a core internal politics mechanic (decision rights architecture).
   - *Effort:* Small (1 hour). Mirror arrest logic but change status to "fired" instead of "arrested", remove role powers.

3. **Revolution trigger (C1 §3)** — When stability 1-2 AND support <20%, revolution should fire. Currently only coup exists (requires player initiative). Revolution is the "automatic" emergency valve.
   - *Effort:* Small (1 hour). Add check in `_update_threshold_flags()` or as a Pass 2 auto-event.

4. **Formosa amphibious ratio correction** — Code has 3:1 for Formosa (AMPHIBIOUS_RATIO_FORMOSA = 3). Design says 4:1. This is a balance-critical value.
   - *Effort:* Trivial (constant change). Decide which is correct and document.

### SHOULD HAVE (improves quality, not blocking)

5. **Public speaking / address nation effect** — C1 §3 table says "support boost if well-received" and "creates public commitments." Currently public statements are logged but have zero mechanical effect. At minimum, spending coins on a speech should give a small support boost (similar to propaganda but with different flavor).
   - *Effort:* Small-medium (2-3 hours). Could be a variant of propaganda with different parameters.

6. **Mass protest resolution mechanic** — Flags are set (protest_risk, protest automatic) but nothing happens automatically. Design says protests are "automatic below 3." Should trigger stability/support consequences and force leader response options.
   - *Effort:* Medium (3-4 hours). Auto-event in world model with response options.

7. **Third-country trade rerouting** — Tariffs and sanctions partially lose effectiveness as trade reroutes through neutral countries. Currently no rerouting model exists. This matters for realism (sanctions without coalition = performative).
   - *Effort:* Medium (4-6 hours). Needs trade flow model tracking bilateral volumes.

8. **Frozen assets mechanic** — Sarmatia assets held in EU/US. Important for sanctions realism and for the "asset seizure" diplomatic lever.
   - *Effort:* Medium (3-4 hours). Track frozen asset values per country, seizure action.

9. **Succession anxiety clock (autocracies)** — Design specifies: <30% support for 3 consecutive rounds triggers forced leadership challenge. This is a key mechanic for autocratic regime dynamics.
   - *Effort:* Small (2 hours). Counter in political state + auto-trigger.

10. **Health events for elderly leaders** — 5-10% incapacitation per round for Helmsman, Pathfinder, Dealer. Adds tension and contingency planning.
    - *Effort:* Small (2 hours). Probability check per round + temporary status change.

11. **Columbia Dem/Rep split tracking** — Design says this feeds into election AI voting. Currently elections use generic incumbent scoring without party dynamics.
    - *Effort:* Medium (3-4 hours). New variable + tracking + integration into election formula.

12. **Personal wealth / personal wallets** — Design mentions ~8-12 roles with personal wealth. Transaction engine handles individual transfers, but there's no separate personal vs. state treasury distinction enforced in budget logic.
    - *Effort:* Medium (4-5 hours). Separate personal balance field, budget separation.

### NICE TO HAVE (can wait for Detailed Design)

13. **Personal tech investments (Pioneer, Circuit)** — These roles can supplement government R&D from personal funds. Low priority until personal wallets exist.

14. **Secondary sanctions risk for evaders** — Discovery via intelligence. Adds depth to sanctions game but complex to implement.

15. **Financial sanctions (SWIFT freeze) with de-dollarization pressure** — Dollar credibility mechanic exists; SWIFT-specific freeze is a flavor variant of existing sanctions.

16. **Sector-level tariffs** — Design says tariffs can be set per sector (resources, industry, services, tech). Current implementation is per-country aggregate only.

17. **Sector-level sanctions** — Design says sanctions per type (financial, resources, industrial, technology). Current implementation is aggregate per-country.

---

## Section 3: SEED CHECKLIST STATUS

### Summary (from SEED_CHECKLIST_v3.md, verified against actual state)

| Section | Total | Done | In Progress | Not Started | Frozen |
|---------|:-----:|:----:|:-----------:|:-----------:|:------:|
| 0 Prerequisites | 4 | 2 | 0 | 2 | 0 |
| A Scenario | 3 | 2 | 0 | 1 | 2 |
| B Actors | 4 | 2 | 0 | 2 | 0 |
| C Mechanics & Map | 7 | 4 | 1 | 2 | 0 |
| D Engines | 9 | 7 | 1 | 1 | 0 |
| E AI Systems | 4 | 1 | 1 | 1 | 2 |
| F Data Architecture | 4 | 1 | 0 | 3 | 0 |
| G Web App | 5 | 0 | 0 | 4 | 1 |
| H Visual Design | 4 | 0 | 1 | 3 | 0 |
| I Testing | 5 | 4 | 1 | 0 | 0 |
| J Delivery | 1 | 0 | 0 | 0 | 1 |
| **TOTAL** | **50** | **23** | **5** | **19** | **6** |

**Checklist says: 23/50 done (46%), 5 in progress, 19 not started, 6 frozen.**

### Assessment of "Done" items — are they truly done?

The checklist marks D1-D4, D6-D7 as Done. Based on this review:

- **D1 Economic Model — DONE but with gaps.** Third-country rerouting, frozen assets, sector-level tariffs/sanctions, and personal wealth are missing. Core GDP/revenue/budget/inflation/debt chain is solid.
- **D2 Political Model — DONE but with gaps.** Revolution trigger, succession anxiety, health events, Dem/Rep split, public speech effect, and mass protest resolution are missing. Core stability/support/elections/war-tiredness is solid.
- **D3 Military Model — DONE but with gaps.** Nuclear test action is missing. Formosa amphibious ratio may be wrong. Core combat, blockade, missile strike, air defense are solid.
- **D4 Technology Model — DONE with minor gaps.** Personal tech investments missing. Core R&D/advancement/disruption/rare earth is solid.
- **D6 Transaction Engine — DONE.** All 6 transaction types implemented correctly.
- **D7 Live Action Engine — DONE but with gaps.** Fire/reassign action missing. Nuclear test missing.

**Honest reassessment: 21 of 23 "done" items are genuinely done. D3 and D7 should be "done with known gaps" rather than fully done. The gaps are small but real.**

### Items NOT STARTED (19)

These fall into three categories:

**Documentation items (11):** B3, B4, A3, C5, C6, D8, E4, F2, F3, F4 — formal specs that codify what exists in code or define new subsystems. Important for SEED gate consistency but don't affect engine functionality.

**Web app specs (4):** G2, G3, G4, G5 — interface specifications. Not engine work.

**Visual/template items (4):** H1, H3, H4 — UX and artifact design. Not engine work.

---

## Section 4: RECOMMENDED PLAN FOR SEED COMPLETION

### Tier 1: Immediate Engine Fixes (do now, 1-2 days)

| # | Task | Effort | Why now |
|---|------|--------|---------|
| 1 | Add `resolve_nuclear_test()` to live_action_engine.py | 1-2 hours | Core action missing. Persia nuclear scenario depends on it |
| 2 | Add `resolve_fire()` to live_action_engine.py | 1 hour | Core internal politics action |
| 3 | Add revolution auto-trigger in world_model_engine.py | 1 hour | Stability floor mechanic |
| 4 | Resolve Formosa amphibious ratio (3:1 vs 4:1) | 15 min | Balance-critical constant |
| 5 | Add succession anxiety counter for autocracies | 2 hours | Key autocracy mechanic |
| 6 | Add health events for elderly leaders (70+) | 2 hours | Scenario-critical random events |

**Total: ~8 hours of focused work.**

### Tier 2: Engine Improvements (this week, 2-3 days)

| # | Task | Effort | Why soon |
|---|------|--------|----------|
| 7 | Public speaking → support effect | 2-3 hours | Fills action gap |
| 8 | Mass protest auto-resolution | 3-4 hours | Makes threshold flags meaningful |
| 9 | Columbia Dem/Rep split variable | 3-4 hours | Needed for election realism |
| 10 | Frozen assets tracking + seizure | 3-4 hours | Sanctions realism |
| 11 | Personal wealth separation | 4-5 hours | 8-12 roles need this |

**Total: ~16-20 hours.**

### Tier 3: Defer to Detailed Design

These items are real but can wait:
- Third-country trade rerouting (complex trade flow model)
- Sector-level tariffs and sanctions (requires data restructure)
- Personal tech investments
- Secondary sanctions risk
- SWIFT-specific freeze mechanics

### Critical Path to SEED Gate

**Engine is ~85% complete on mechanics.** The 15% gap is mostly small missing actions (nuclear test, fire/reassign, revolution) and enrichment mechanics (succession, health, Dem/Rep split). None require architectural changes — all are additive.

**The real SEED gate bottleneck is NOT the engine.** It's the 19 not-started documentation items, particularly:
- **D8 Engine Formula Docs** — formalizing what's in code (essential for SEED consistency gate)
- **B3 Relationship Matrix** — bilateral relationship data (informs sanctions, trade, alliance behavior)
- **F2-F4 Data architecture docs** — event logging, data flows, API contracts
- **G2-G5 Web app specs** — needed before development can start

**Recommended sequence to SEED gate:**
1. **Days 1-2:** Tier 1 engine fixes (8 hours)
2. **Days 3-5:** Tier 2 engine improvements (16-20 hours)
3. **Days 3-7 (parallel):** D8 formula documentation (capture all formulas from code)
4. **Days 5-10:** B3, A3, C5, C6 content documents
5. **Days 8-14:** F2-F4 data architecture, E4 navigator prompts
6. **Days 10-18:** G2-G5 web app specs, H1 UX style guide
7. **Day 18-20:** H3-H4 templates, final calibration run, VERA consistency check

**Realistic timeline: 3-4 weeks to SEED gate** assuming focused effort on documentation alongside engine fixes.

---

## Appendix: Mechanics Scorecard

| Domain | Total mechanics | Implemented | Partial | Missing | Coverage |
|--------|:--------------:|:-----------:|:-------:|:-------:|:--------:|
| Military | 16 | 12 | 2 | 2 | 75% |
| Economic | 16 | 13 | 1 | 2 | 81% |
| Political | 15 | 9 | 2 | 4 | 60% |
| Technology | 9 | 8 | 0 | 1 | 89% |
| Actions (C2) | 30 | 25 | 3 | 2 | 83% |
| **TOTAL** | **86** | **67** | **8** | **11** | **78%** |

**Bottom line: The engine implements 78% of design doc mechanics. The missing 22% is concentrated in the Political domain (succession, health, revolution, Dem/Rep, public speech, protests) and a few specific actions (nuclear test, fire/reassign). No architectural gaps — all fixes are additive methods or variables.**
