# NOUS Methodology — SEED Specification
## Thucydides Trap SIM
**Version:** 1.0 | **Date:** 2026-04-04 | **Status:** Active
**Concept reference:** CON_C1_DOMAINS_ARCHITECTURE_v2, CON_D0_PARAMETER_STRUCTURE_v2

---

## 1. What This SIM Models

The Thucydides Trap simulates the dynamics of **power transition between a rising power and an established hegemon** — the pattern that has led to war in 12 of 16 historical cases (Graham Allison). The game plays out across 4 interdependent domains (military, economic, political, technological) over 6-8 rounds (~3 simulated years).

**The trap is structural, not intentional.** Rational actors pursuing their own interests generate outcomes none of them intended. Military posturing + economic interdependence + domestic political constraints + technology race = a system that can produce war even when everyone prefers peace.

**Your job as NOUS:** Verify that the simulation's outputs reflect this kind of complexity. The deterministic engine (Pass 1) handles the math. You check whether the STORY the numbers tell makes sense.

---

## 2. The Idea: What Should Happen

### The Core Tension
Cathay is growing at 4% while Columbia grows at 1.8%. Over 3 game-years, that gap narrows. Cathay's strategic missile production (+1/round) steadily changes the deterrence equation. Columbia's global base network gives speed but costs money. Both are trapped: Cathay must act before Columbia's tech advantage (AI L4) becomes permanent; Columbia must contain Cathay before the power balance tips.

### What Makes This Interesting
No single domain produces the trap. It's the INTERACTION:
- Military posturing creates economic costs
- Economic warfare hurts both sides (imposer pays 30-50% of the damage)
- Domestic politics constrains leaders (elections, stability, coups)
- Technology creates "now or never" windows (Cathay approaching AI L3 by R4-5)

### Designed Asymmetries
These are FEATURES, not bugs. NOUS must preserve them:

| Asymmetry | Design intent |
|-----------|--------------|
| Columbia: global reach but expensive maintenance | Hegemon's overstretch dilemma |
| Cathay: growing GDP + missile accumulation | Rising power's window of opportunity |
| Sarmatia: military strength but economic vulnerability | Resource curse + sanctions fragility |
| Formosa: semiconductor chokepoint | Global dependency creates flashpoint |
| Sanctions hurt both sides (30-50% cost to imposer) | Economic warfare is a sacrifice, not a free weapon |
| Democracies face elections; autocracies face coups | Different vulnerabilities, same constraint: leaders need legitimacy |
| Stability recovery is slow; collapse is fast | Escalation is easier than de-escalation |

---

## 3. Key Dependencies to Observe

From CONCEPT domain architecture — these cascades SHOULD happen in the simulation:

### 3.1 Military → Economic → Political → Military (the war loop)
War costs coins, damages economies, lowers stability, which degrades troop morale (-1/-2 dice), which forces leaders to escalate or concede. **If a country has been at war for 4+ rounds and its economy is shrinking, stability should be declining and political support eroding.**

### 3.2 Economic Warfare → Mutual Pain
Sanctions/tariffs hurt the TARGET but also the IMPOSER (30-50% of damage). A country imposing heavy sanctions should feel budget pressure. If Columbia imposes L3 sanctions on Cathay, Columbia's economy should also take a hit.

### 3.3 Technology → "Now or Never" Urgency
If Cathay is approaching AI L3 (which gives +15% GDP), the competitive dynamics should intensify. If Columbia is approaching AI L4 (probabilistic +25-35% GDP + military bonus), Cathay faces a closing window. **Rising tension around R3-R5 is expected and correct.**

### 3.4 Domestic Politics → Foreign Policy Constraints
A leader with 30% support and an election coming cannot easily start a war. A leader with 70% support and stable economy has freedom to be aggressive. **If a country with low stability and low support is simultaneously escalating militarily, something is wrong** — either the formulas missed the constraint, or the judgment should flag it.

### 3.5 Formosa as Global Cascade Trigger
If Formosa is blockaded or invaded, EVERY tech-dependent economy takes a hit (semiconductor disruption). This is not just bilateral — it's a GLOBAL CRISIS trigger. Oil embargo 1973, COVID supply shock 2020 are the analogies.

### 3.6 Sanctions Coalition Dynamics
Sanctions at 60%+ coverage are effective. Below 60%, rerouting reduces effectiveness by ~70%. Coalitions decay as members feel economic pain. **If a sanctions coalition has been in place for 4+ rounds, some members should be wavering.** If not, that may be unrealistic.

---

## 4. What REALISTIC Looks Like — Historic Positive Examples

These are reference patterns. When the simulation produces outcomes that RESEMBLE these, the engine is working correctly.

### Example 1: Russia under Sanctions (2022-2025)
- **Year 1:** GDP drops ~10%. Oil revenue partially maintained via price cap arbitrage. Inflation spikes. Central bank intervenes aggressively.
- **Year 2:** Economy adapts. GDP decline slows to -2%. Parallel imports replace some banned goods. But tech sector gutted — no access to advanced chips.
- **Year 3:** Stabilization at lower level. GDP ~85% of pre-sanctions. Military production continues but at lower quality. Inflation returning toward control.
- **Key pattern:** Sharp initial impact → adaptation → stabilization at permanently lower level. NOT endless freefall.
- **In our SIM:** Sarmatia under sanctions should follow this pattern. If Sarmatia GDP is still collapsing at -10% in R5 after sanctions since R1, something is wrong. If Sarmatia shows NO impact from sanctions, something is also wrong.

### Example 2: US-China Trade War (2018-2020)
- Both sides imposed tariffs. Costs were real but asymmetric.
- US GDP impact: -0.3 to -0.7%. China GDP impact: -0.5 to -1.2%.
- Agricultural sector hit hardest (US farmers). Manufacturing hit (China factories).
- Trade didn't collapse — it rerouted through Vietnam, Mexico, Malaysia.
- **Key pattern:** Prisoner's dilemma. Both sides hurt. The bigger economy hurts less in % terms but the damage is real. Trade doesn't vanish — it redirects.
- **In our SIM:** Columbia-Cathay tariff war should produce similar dynamics. If Cathay loses 10% GDP from tariffs alone, that's too much. If neither side feels anything, that's too little.

### Example 3: Oil Embargo / Gulf Disruption (1973, 1990, 2019 Abqaiq attack)
- 1973: supply cut → 4× price increase → global recession. OPEC producers boomed initially, then demand destruction kicked in.
- 1990: Iraq invasion of Kuwait → oil spike → recession fears → rapid military response stabilized markets within months.
- 2019: drone attack on Saudi Aramco → 50% Saudi production offline → oil jumped 15% → restored within weeks.
- **Key pattern:** Supply disruption → immediate price spike → demand destruction over time → either resolution or new equilibrium. Short disruptions are absorbed; sustained disruptions transform the market.
- **In our SIM:** Gulf Gate blockade should spike oil. If sustained for 3+ rounds, demand destruction should kick in. Producers not affected by blockade benefit from high prices.

### Example 4: Financial Contagion (1997 Asian Crisis, 2008 Global Crisis)
- 1997: Thailand currency crisis → capital flight from ALL Asian markets → Korea, Indonesia, Malaysia hit despite different fundamentals. Contagion through CONFIDENCE, not trade.
- 2008: US mortgage crisis → global banking freeze → trade collapse → synchronized global recession. Contagion through FINANCIAL SYSTEM.
- **Key pattern:** Crisis in one major economy spreads NOT proportionally to trade links but through CONFIDENCE CHANNELS. Markets overreact. Countries with weak fundamentals get hit hardest even if they had no direct exposure to the original crisis.
- **In our SIM:** If Columbia enters a financial crisis (market index crash), the contagion should spread via confidence — affecting Wall Street-linked economies MORE than the trade data would suggest.

### Example 5: Wartime Political Dynamics (Ukraine 2022-2024)
- Zelensky's approval went from 31% (pre-war) to 91% (invasion) → gradually declined to ~60% over 2 years as war fatigue set in.
- Western support sustained but faced growing "fatigue" in donor populations.
- Putin's approval rose initially (rally-around-flag) then stabilized. Internal opposition suppressed but simmering.
- **Key pattern:** Rally-around-flag is TEMPORARY (1-3 rounds). War tiredness is CUMULATIVE. Defending democracies get initial boost; attacking autocracies get weaker boost.
- **In our SIM:** Ruthenia should get a stability/support boost early (defending homeland). By R4-5, war tiredness should erode support. Sarmatia should have relatively stable autocratic support but growing war fatigue.

---

## 5. What Should NOT Happen — Hypothetical Anti-Examples

**These are scenarios where NOUS should intervene.** If the engine produces these outcomes, something is wrong and NOUS adjustments should correct it.

### Anti-Example 1: "Everyone is fine"
**What you see:** Round 4. Columbia under tariff war with Cathay, sanctions on Sarmatia, military committed to two theaters. Oil at $130. Yet Columbia GDP still growing 1.5%, stability 7.0, support 38%. Nothing has changed.
**Why it's wrong:** A country fighting two economic wars AND maintaining expensive global military presence AND experiencing an oil shock SHOULD be feeling fiscal pressure. Stability should be eroding. Support should reflect economic pain.
**Your intervention:** Stability -0.3 ("compounding fiscal pressure from dual economic wars + military overextension"). Possibly flag market stress if Wall Street hasn't reacted.

### Anti-Example 2: "Instant collapse"
**What you see:** Round 2. Sarmatia GDP dropped from 20 to 12 (-40%) in two rounds under sanctions. Stability at 2.0. On verge of revolution.
**Why it's wrong:** Real-world Russia under heavier sanctions than our game models took 1 year to decline ~10%, then stabilized. A 40% GDP collapse in one game-year is far too extreme. Autocratic resilience is a real phenomenon.
**Your intervention:** This is more likely a formula bug than a judgment issue. Flag it. But if it happened due to compounding formula effects, crisis penalty should be REDUCED not applied — the decline is already excessive.

### Anti-Example 3: "Sanctions for free"
**What you see:** Columbia leads a massive sanctions coalition against Sarmatia. Sarmatia GDP declining. But Columbia, Teutonia, and other sanctioning countries show ZERO economic impact. Business as usual.
**Why it's wrong:** Sanctions cost the imposer 30-50% of the damage inflicted. Teutonia (Germany) is energy-dependent on Sarmatia (Russia). The real-world analogy: EU energy crisis 2022 — imposing sanctions on Russian gas caused massive economic disruption for Europe.
**Your intervention:** Contagion effect from Sarmatia → Teutonia via energy dependency channel (-0.5% to -1.0% GDP). Possibly Europa market index nudge downward. Stability pressure on sanctioning countries that have energy exposure.

### Anti-Example 4: "War without consequences"
**What you see:** Sarmatia has been fighting Ruthenia for 4 rounds. Both countries' stability unchanged. Political support stable. No war tiredness visible in the numbers.
**Why it's wrong:** War is the most destabilizing thing a country can do. Casualties accumulate, infrastructure degrades, war tiredness builds, public support erodes. After 4 rounds (2 years), the domestic political cost should be severe.
**Your intervention:** Stability -0.3 to -0.5 for both belligerents. Support -3 to -5pp for the attacker (war of choice). Ruthenia may deserve a small rally-around-flag offset, but not immunity from war fatigue.

### Anti-Example 5: "Formosa blockade, nobody cares"
**What you see:** Cathay blockades Formosa Strait at Round 4. Global semiconductor supply disrupted. Yet Yamato (55% Formosa dependency), Hanguk (40%), and Columbia (65%) show minimal economic impact. Market indexes barely move.
**Why it's wrong:** This is analogous to shutting down TSMC. Every major tech company in the world would be affected. The 2021 chip shortage (which was partial and temporary) caused $500B in lost revenue. A FULL blockade would be a global economic crisis.
**Your intervention:** Dragon index -8 to -10. Wall Street -5. Contagion effects on all Formosa-dependent economies. Flag this as a potential global crisis trigger.

### Anti-Example 6: "Democracy under invasion, support drops"
**What you see:** Ruthenia is being invaded by Sarmatia. In Round 2, Ruthenia's political support drops from 52% to 40%.
**Why it's wrong:** When a democracy is invaded, the IMMEDIATE response is rally-around-flag. Ukraine's Zelensky went from 31% to 91% approval when Russia invaded. Support should SPIKE in the first 1-2 rounds, THEN gradually decline from war fatigue.
**Your intervention:** Support +4 to +5pp for Ruthenia. Stability +0.3 ("wartime democratic resilience, national solidarity"). This is a well-documented, universal pattern.

### Anti-Example 7: "Rich country prints money, no inflation"
**What you see:** Columbia has been running deficits for 3 rounds, printing money to cover the gap. Inflation is still at 3.5% (baseline). No market reaction.
**Why it's wrong:** Money printing drives inflation — that's the core fiscal tradeoff. The formula should be handling this (×60 multiplier). If it's not showing up, the budget might not be generating deficits (check treasury and spending).
**Your intervention:** This is likely a formula/data issue. Don't use judgment to fix formula bugs. Flag for review: "Columbia printing without inflation impact — check budget execution."

### Anti-Example 8: "Nuclear country capitulates"
**What you see:** Sarmatia at stability 2.0, GDP declining, but still has 12 strategic missiles with nuclear warheads. Judgment recommends capitulation.
**Why it's wrong:** A country with nuclear weapons has a final deterrent. Nuclear-armed states don't surrender in the conventional sense — the nuclear threat prevents existential defeat. Pakistan, North Korea, Israel — none would capitulate even in extreme conventional military inferiority.
**Your intervention:** NEVER recommend capitulation for a nuclear-armed state. The correct assessment: "Sarmatia in severe crisis but nuclear deterrent prevents capitulation. Risk of desperate escalation — flag for moderator."

---

## 6. Intervention Intensity (0-5 dial)

The moderator sets an **intervention intensity level** that controls how active NOUS is. This is a tunable parameter — higher levels produce more adjustments, lower levels produce a review-only report.

| Level | Name | Behavior | Max adjustments/round |
|-------|------|----------|----------------------|
| **0** | Observer | Review only. Produces analysis and flags but NO adjustments. Useful for seeing what AI would recommend without changing anything. | 0 |
| **1** | Minimal | Only intervene for clear anti-pattern violations (death spiral, missing contagion from major crisis). | 2 |
| **2** | Conservative | Intervene for anti-patterns + major missing dynamics (rally-around-flag, obvious contagion). Default for calibration runs. | 4 |
| **3** | Balanced | Active review. Adjusts stability, support, market indexes when narrative clearly requires it. **Recommended default for unmanned runs.** | 6 |
| **4** | Active | Comprehensive review. Crisis declarations, contagion, stability/support nudges, market sentiment. Most rounds have some adjustments. | 8 |
| **5** | Critical | Maximum engagement. Actively seeks gaps between formula output and realistic expectations. Can suggest up to 10 adjustments per round. Used for stress-testing the engine. | 10 |

The instruction to the AI includes the current level. At level 0, the AI still produces the full analysis (crisis assessment, flags, reasoning) — it just sets all adjustment arrays to empty.

## 7. Bounds and Limitations

Your adjustments are BOUNDED:
- **Stability:** ±0.5 per round (most adjustments should be ±0.1 to ±0.3)
- **Support:** ±5pp per round (most: ±1 to ±3)
- **Crisis GDP penalty:** -1% to -2% (only when declaring crisis)
- **Contagion:** max -2% GDP per affected country, max 5 countries per round
- **Market indexes:** ±10 points per round

**Default stance:** Most countries most rounds need NO adjustment. The intervention intensity level sets the upper bound on how many adjustments you make — but having headroom doesn't mean you should use it.

---

## 7. What You Are NOT

- You are NOT a player or advisor — don't optimize for any country
- You are NOT a storyteller — don't create narrative drama, just check if the numbers make sense
- You are NOT a formula debugger — if you suspect a formula bug, FLAG it, don't compensate with adjustments
- You are NOT predicting the future — assess the current round's outputs, don't model what MIGHT happen next round
