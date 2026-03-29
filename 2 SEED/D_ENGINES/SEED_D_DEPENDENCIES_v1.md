# TTT World Model -- Key Dependencies & Feedback Loops
## Calibration Reference Document v1

**Purpose:** This document defines 25 critical dependencies with feedback loops that the TTT world model engine MUST correctly simulate. Each dependency specifies the causal chain, feedback mechanism, stabilizer, observable behavior, and failure mode. This is the calibration reference -- we test the engine against these dependencies.

**Engine reference:** `world_model_engine.py` v2 (three-pass architecture with chained feedback loops)

**Authors:** KEYNES (economist), CLAUSEWITZ (military strategist), MACHIAVELLI (political scientist)

---

# ECONOMIC DEPENDENCIES (1-8)

---

## Dependency 1: Oil Price Shock -> GDP Contraction

**Domain:** Economic
**Causal chain:** Chokepoint blockade or OPEC restriction -> Oil supply reduction -> Oil price spike -> GDP contraction for importers, windfall for producers -> Reduced global demand -> Price moderation
**Feedback loop:** GDP contraction reduces aggregate demand, which feeds back into the oil price formula via the demand variable (`demand -= 0.05` for crisis, `-0.10` for collapse in major economies). Lower demand moderates price, which reduces the GDP hit on the next round.
**Stabilizer:** Three mechanisms prevent runaway: (1) Soft price cap -- asymptotic formula above $200 (`200 + 50*(1 - exp(-(raw-200)/100))`), theoretical max around $250. (2) Demand destruction -- crisis/collapse in major economies reduces demand by 5-10%. (3) GDP floor at 0.5 coins prevents total annihilation.
**Observable:** Oil at $150 should produce GDP contraction of 2-4% for major importers (Columbia, Cathay, Ponte, Vinland). Oil at $200+ should produce 4-8% contraction for importers while Nordostan, Persia, and Saudara see GDP growth of 1-3% above baseline. After 2-3 rounds of high oil, demand destruction should start pulling the price back toward $150-180 even without supply-side changes.
**Failure mode:** If the engine is wrong, we would see: (a) oil at $200+ with no GDP impact on importers (missing oil_shock term in `_calc_gdp_growth`), (b) oil price spiraling infinitely above $250 (broken soft cap), (c) oil producer GDP declining despite high prices (oil_revenue calculation wrong), or (d) oil price never falling back after demand destruction (demand-side feedback not connected to economic states).

---

## Dependency 2: Sanctions -> GDP Erosion -> Budget Crisis

**Domain:** Economic
**Causal chain:** Sanctions imposed (L1-L3) -> Trade disruption proportional to coalition coverage and trade weight -> GDP reduction (`sanctions_hit = -damage * 2.0`) -> Revenue declines (GDP * tax_rate falls) -> Budget deficit -> Treasury depletion -> Money printing -> Inflation -> Further revenue erosion via `inflation_revenue_erosion`
**Feedback loop:** GDP erosion reduces tax revenue, forcing deficit spending. Deficit -> debt burden (15% of deficit becomes permanent). Debt service eats future revenue, creating a self-reinforcing fiscal squeeze. Inflation from money printing erodes revenue further (`inflation_delta * 0.03 * gdp / 100`).
**Stabilizer:** (1) Sanctions effectiveness requires coalition coverage >= 60% of trade weight; below that, effectiveness drops to 30%. (2) Diminishing returns after 4 rounds -- sanctions_hit multiplied by 0.70 adaptation factor. (3) AI adjustment pass adds 2% GDP recovery for countries adapting after 4+ rounds. (4) Total sanctions damage capped at 50% (`min(total_damage, 0.50)`).
**Observable:** L2 sanctions from a broad coalition (Columbia + allies, coverage > 60%) on Nordostan should produce 3-6% GDP contraction per round for the first 4 rounds, then slow to 2-4% as adaptation kicks in. Nordostan's treasury should deplete within 2-3 rounds, triggering money printing. Inflation should spike 10-20% above baseline. By round 5-6, the sanctions regime should be visibly less effective (adaptation).
**Failure mode:** (a) Sanctions producing identical GDP damage in round 6 as in round 1 (adaptation not working). (b) Unilateral sanctions (single country, low trade weight) producing devastating damage (effectiveness multiplier not applied). (c) Sanctioned country's treasury never depleting because revenue calculation ignores sanctions cost. (d) No inflation spike despite money printing (broken inflation chain).

---

## Dependency 3: Money Printing -> Inflation -> Stability Erosion

**Domain:** Economic
**Causal chain:** Budget deficit exceeds treasury -> Money printed to cover gap -> Inflation spikes (80x multiplier: `money_printed / gdp * 80.0`) -> Inflation delta above baseline erodes revenue (`inflation_delta * 0.03 * gdp / 100`) -> Further deficit -> More printing -> Higher inflation -> Stability penalty from inflation friction (`(inflation_delta - 3) * 0.05` plus `(inflation_delta - 20) * 0.03` for severe inflation) -> Crisis state escalation
**Feedback loop:** Inflation -> revenue erosion -> larger deficit -> more printing -> more inflation. This is the classic hyperinflation spiral. Each round of printing makes the next round's deficit worse.
**Stabilizer:** (1) Natural inflation decay of 15% per round (`prev * 0.85`). (2) GDP floor at 0.5 coins. (3) Inflation hard cap at 500%. (4) If the country stops printing (e.g., cuts spending or receives aid), inflation decays naturally.
**Observable:** A country printing 10% of its GDP should see inflation jump by approximately 8 percentage points (80 * 0.10 = 8). If sustained, compound effects should push inflation above 30% within 3 rounds. At inflation delta > 20, the combined stability penalty should be -0.85 to -1.35 per round (0.05 * 17 + 0.03 * variable), which at sustained levels pushes stability below 5 within 2-3 rounds.
**Failure mode:** (a) Country printing money with no inflation increase (broken 80x multiplier). (b) Inflation rising but stability unaffected (inflation friction not connected to stability formula). (c) Hyperinflation spiral with no decay -- inflation at 200%+ with no mechanism to come down even after printing stops (broken 0.85 decay). (d) Revenue erosion formula using absolute inflation instead of delta from baseline, unfairly penalizing countries with naturally higher baseline inflation.

---

## Dependency 4: Debt Accumulation -> Interest Burden -> Fiscal Death Spiral

**Domain:** Economic
**Causal chain:** Deficit in round N -> 15% becomes permanent debt burden -> Debt service subtracts from revenue in round N+1 -> Larger deficit in round N+1 -> More debt -> Compound accumulation
**Feedback loop:** Debt service is subtracted directly from revenue: `revenue = base_rev + oil_rev - debt - inflation_erosion - war_damage - sanc_cost`. Each round's deficit adds 15% to permanent debt burden. By round 4-5, debt service can consume 20-30% of revenue for heavily indebted countries, creating an inescapable fiscal trap.
**Stabilizer:** (1) The debt burden grows linearly with deficits, not exponentially (no compound interest on debt itself -- it is `deficit * 0.15` added flat). (2) Countries can run surpluses to rebuild treasury. (3) GDP growth can outpace debt accumulation if the economy recovers. (4) Spending cuts reduce deficits.
**Observable:** A country running a deficit of 5 coins per round accumulates debt burden of 0.75 coins/round (5 * 0.15). After 4 rounds: 3.0 coins permanent debt service. For a country with GDP 30 and tax rate 0.20 (revenue ~6.0), that 3.0 debt service consumes 50% of revenue -- clearly visible fiscal stress. By round 6-7, the debt service should be large enough to guarantee perpetual deficits even with austerity.
**Failure mode:** (a) Debt burden not persisting between rounds (reset bug). (b) Debt growing faster than linear -- compound interest applied to debt itself creating instant death spirals. (c) Revenue formula not subtracting debt burden, so countries accumulate debt with no consequence. (d) No mechanism for debt reduction (countries can never recover).

---

## Dependency 5: Semiconductor Disruption -> Tech-Dependent GDP Crash

**Domain:** Economic
**Causal chain:** Formosa blockade or invasion -> Semiconductor supply cut -> GDP contraction proportional to `formosa_dependency * severity * tech_sector_pct` -> Severity ramps with duration (0.3, 0.5, 0.7, 0.9, 1.0 over rounds) -> Countries with high dependency and high tech sector hit hardest -> After 3+ rounds with dependency > 0.5, triggers crisis state
**Feedback loop:** Semiconductor disruption -> GDP contraction -> crisis state -> crisis GDP multiplier (0.5 in crisis, 0.2 in collapse) -> further GDP contraction -> tech sector shrinks as a share of economy -> slightly reduces future semiconductor hit (but this is a weak stabilizer).
**Stabilizer:** (1) Severity ramps gradually, not instant maximum (stockpile buffer for first round at 0.3 severity). (2) After blockade lifts, `formosa_disruption_rounds` resets to 0. (3) Alternative suppliers implicit in the severity cap at 1.0 (never exceeds total dependency). (4) GDP floor at 0.5.
**Observable:** Cathay (formosa_dependency likely high, tech sector ~25%) should see 3-7% GDP hit in round 1 of Formosa blockade, escalating to 8-15% by round 3. Columbia (formosa_dependency moderate, tech sector ~30%) should see 2-5% initial hit, escalating to 5-10%. Countries with zero formosa_dependency (Persia, Saudara) should be unaffected directly. After 3 rounds of disruption with dependency > 0.5, the crisis state trigger fires, compounding damage via crisis multiplier.
**Failure mode:** (a) All countries equally affected regardless of dependency value (dependency not used in formula). (b) Full damage from round 1 with no stockpile buffer (severity not ramping). (c) Damage persisting after blockade lifts (disruption_rounds not resetting). (d) Tech-light economies (resources-heavy) being devastated by semiconductor disruption (tech_sector_pct not applied).

---

## Dependency 6: Oil Producer Windfall -> War Funding (Nordostan Enrichment Paradox)

**Domain:** Economic / Cross-domain
**Causal chain:** War disrupts oil supply (Gulf Gate blockade, sanctions on producers) -> Oil price spikes -> Oil producers receive windfall (`oil_revenue = price * resource_pct * gdp * 0.01`) -> Windfall funds military production and war effort -> More war -> More disruption -> Higher prices -> More windfall
**Feedback loop:** This is the Nordostan Enrichment Paradox -- the war that Nordostan wages creates the oil price spike that funds Nordostan's war. Sanctions on Nordostan reduce supply further, driving prices higher, partially offsetting the sanctions' intended economic damage. Oil revenue adds directly to revenue, cushioning the budget from sanctions damage.
**Stabilizer:** (1) Oil revenue formula uses `resource_pct * gdp * 0.01`, so as sanctions reduce GDP, the base for oil revenue shrinks. (2) Sanctions on oil producers reduce supply by 8% per producer, but this is a fixed number that does not scale. (3) Demand destruction from high prices eventually moderates the windfall. (4) Coalition sanctions reduce trade (export markets), partially negating the revenue benefit.
**Observable:** With oil at $150 and Nordostan resources sector at ~30% of economy, oil revenue should be approximately `150 * 0.30 * GDP * 0.01`. For Nordostan GDP ~15 coins: `150 * 0.30 * 15 * 0.01 = 6.75 coins` oil revenue. This is enough to offset a significant portion of sanctions damage and fund continued military production of 1-2 units per round. The paradox should be visible: sanctioning Nordostan drives up oil prices, which partially funds Nordostan's war chest.
**Failure mode:** (a) Oil revenue not calculated for producers (missing flag check). (b) Oil revenue not added to the revenue formula, so windfall has no budget impact. (c) Revenue so large it completely negates sanctions, making sanctions pointless (formula too generous). (d) Non-oil-producers receiving oil revenue (flag error).

---

## Dependency 7: Economic Crisis Contagion

**Domain:** Economic
**Causal chain:** Major economy (GDP > 30 coins) enters crisis or collapse -> Trade partners with bilateral trade weight > 10% absorb GDP hit (`severity * trade_weight * 0.02`) -> Partners lose momentum (-0.3) -> Partner economies may enter stressed state -> If partner is also a major economy, secondary contagion wave possible
**Feedback loop:** Crisis in Country A hits Country B via trade links. If B enters crisis, it hits Country C. Cascade potential exists but is limited by trade weight thresholds (> 10%) and the MAJOR_ECONOMY_THRESHOLD (GDP > 30). Small economies do not generate contagion.
**Stabilizer:** (1) Trade weight threshold of 10% limits contagion to genuine trade partners. (2) GDP threshold of 30 coins limits contagion sources to major economies. (3) Hit is proportional to trade weight, so distant partners barely affected. (4) Severity is 1.0 for crisis, 2.0 for collapse -- graduated response. (5) Contagion is applied AFTER per-country GDP calculations, so it does not double-count.
**Observable:** If Columbia (GDP ~90) enters crisis, Ponte (high trade weight with Columbia) should see 0.5-2% GDP reduction from contagion alone, plus momentum drop of -0.3. Cathay should also be hit but less severely (lower trade weight). If both Columbia and Cathay enter crisis simultaneously, small trade-dependent countries like Formosa and Vinland should see compounding contagion from multiple sources.
**Failure mode:** (a) Contagion applied to ALL countries regardless of trade weight (threshold ignored). (b) Small economies generating contagion waves (GDP threshold not checked). (c) Contagion cascading infinitely within a single round (contagion triggering more contagion in same processing step). (d) No contagion at all despite major economy collapse (step 11 skipped or trade weights broken).

---

## Dependency 8: OPEC Prisoner's Dilemma

**Domain:** Economic / Political
**Causal chain:** OPEC members set production to "low" -> Supply decreases by 6% per member -> Oil price rises -> All producers benefit -> Temptation to defect: one member sets "high" production -> Supply increases by 6% -> Price drops -> Defector gains market share but group loses -> If multiple defect, price crashes -> Re-cooperate
**Feedback loop:** Cooperation yields high prices (collective benefit) but each member has incentive to defect for individual gain. Defection, if widespread, crashes prices, forcing re-cooperation. Classic iterated prisoner's dilemma.
**Stabilizer:** (1) Each OPEC member's production decision has symmetric impact: `supply -= 0.06` for low, `supply += 0.06` for high. (2) With multiple OPEC members, collective restriction can move supply by 12-18%, producing significant price changes. (3) The oil price floor at $30 prevents total price collapse. (4) War premium (+5% per active war, capped at 15%) provides a baseline price support.
**Observable:** If all OPEC members restrict production (low), supply drops by ~18% (3 members * 6%), which should push oil from $80 base to approximately $97-100. If one defects to "high" while others stay "low", net supply change is approximately -6% (still elevated), so defector gains volume at only slightly lower price. If all defect to "high", supply increases by 18%, pushing price toward $65-68. The oscillation between cooperation and defection should produce oil price volatility of $20-40 between rounds.
**Failure mode:** (a) OPEC production decisions having no effect on oil price (supply variable not used in price formula). (b) A single member's decision dominating the entire price (6% impact too large relative to other factors). (c) No mechanism for OPEC members to coordinate (game design issue, not engine bug). (d) Production changes applying to non-OPEC members.

---

# MILITARY DEPENDENCIES (9-14)

---

## Dependency 9: Naval Buildup -> Parity Crossing -> Strategic Window

**Domain:** Military
**Causal chain:** Cathay starts with 7 naval, Columbia with 11 -> Cathay builds +1 naval per round (production capacity) -> Columbia auto-produces +1 per 2 rounds (maintenance replacement for naval >= 5) -> Parity crossing occurs around round 4-5 if Columbia does not actively invest in naval production -> Parity creates strategic window for Cathay to consider Formosa blockade -> Blockade triggers semiconductor crisis
**Feedback loop:** As Cathay approaches naval parity, Columbia faces a choice: divert budget to naval production (reducing other spending) or accept parity crossing. If Columbia diverts spending, it weakens other theaters. If it does not, Cathay achieves local naval superiority in the Western Pacific.
**Stabilizer:** (1) Columbia's auto-production of +1 per 2 rounds prevents free decline. (2) Naval production costs (5 coins per unit) limit maximum buildup rate for both sides. (3) Budget constraints -- naval investment competes with ground, air, social, and tech spending. (4) Economic crisis reduces available budget for military production.
**Observable:** Starting positions: Columbia 11 naval, Cathay 7. With no active naval investment from either side, Columbia grows to ~13 by round 4 (auto +1 per 2 rounds), Cathay grows to ~11 (active +1 per round from production capacity). Parity is NOT reached passively -- Cathay needs to actively invest coins. With active investment (accelerated tier at 2x cost), Cathay could reach 11-13 by round 3-4, achieving local parity. The strategic window opens when Cathay naval >= Columbia Pacific fleet (subset of total).
**Failure mode:** (a) Cathay naval never increasing despite production orders (production capacity not applied). (b) Columbia auto-production firing every round instead of every 2 rounds (round_num % 2 check wrong). (c) Naval production ignoring budget constraints (units produced without coin expenditure). (d) Parity crossing having no strategic consequence (blockade feasibility not linked to naval ratio).

---

## Dependency 10: Overstretch -> Forced Redeployment -> Theater Vulnerability

**Domain:** Military
**Causal chain:** Country commits forces to multiple theaters (e.g., Columbia in Mashriq AND Pacific) -> Total forces split across zones -> Strength in each theater falls below defensive threshold -> Enemy exploits weakness in one theater -> Country forced to redeploy from another theater -> Vacated theater becomes vulnerable -> Cascading theater losses
**Feedback loop:** Redeployment from Theater A to Theater B creates vulnerability in Theater A. If enemy attacks Theater A, country must either accept losses or redeploy again, creating oscillation. Each redeployment costs a round of tempo.
**Stabilizer:** (1) Production capacity allows force regeneration over time. (2) Naval and air mobility enable rapid redeployment (but costs a round). (3) Alliance partners can hold theaters while primary country redeploys. (4) Nuclear deterrence prevents total exploitation of vulnerability (Dependency 14).
**Observable:** Columbia starts with ~18 ground, 11 naval, 6 tactical air spread across Mashriq and home. If Columbia commits 8+ ground to Mashriq and 4+ naval to Pacific blockade support, remaining forces (6 ground, 7 naval) become thin. An attack on a third theater (e.g., Caribbean) should force impossible choices. War zones count (`_count_war_zones`) should show 2+ occupied zones, producing war_hit of -6%+ GDP.
**Failure mode:** (a) Forces being usable in multiple theaters simultaneously without redeployment (zone system not enforced). (b) Redeployment being instantaneous with no round cost. (c) War in multiple theaters not producing compounding GDP damage (war_hit formula only counting one war). (d) Allies not being able to fill gaps (alliance mechanics missing).

---

## Dependency 11: Blockade -> Economic Attrition -> Treasury Depletion -> Blockade Unsustainable

**Domain:** Military / Economic
**Causal chain:** Country establishes naval blockade -> Blockade costs money (naval maintenance + operational costs) -> Target economy contracts but slowly -> Blockader's treasury depletes over time -> Eventually blockade becomes economically unsustainable -> Blockade lifted -> Target economy begins recovery
**Feedback loop:** Blockade hurts the target but also costs the blockader. As blockader's treasury depletes and economy stresses (from war costs, reduced trade), pressure mounts to lift the blockade. If target can outlast the blockader's treasury, the blockade fails.
**Stabilizer:** (1) Blockade effectiveness is significant (`-40% * blockade_fraction` GDP hit to target) -- it does work. (2) But naval maintenance costs (0.3 coins per unit per round) drain the blockader. (3) War premium on oil (+5% per war) hurts the blockader if they are an oil importer. (4) War tiredness erodes blockader's political support.
**Observable:** A Cathay blockade of Formosa should cost approximately 2-3 naval units * 0.3 = 0.6-0.9 coins/round in maintenance alone, plus operational costs. Meanwhile, Formosa's economy contracts by 15-25% per round (high blockade fraction + semiconductor disruption). But Cathay also suffers from trade disruption (Malacca blockade_fraction hits Cathay at 2x). After 4-5 rounds, both sides should be visibly economically degraded, creating mutual pressure for resolution.
**Failure mode:** (a) Blockade having zero economic cost to the blockader (maintenance not calculated for deployed naval units). (b) Blockade effect being permanent even after lifted (blockade_fraction not zeroing). (c) Blockade instantly destroying target economy in one round (no graduated attrition). (d) Blockader's economy completely unaffected by their own war.

---

## Dependency 12: War Attrition -> Military Degradation -> Ceasefire Pressure

**Domain:** Military / Political
**Causal chain:** Active combat -> Casualties each round -> Military strength degrades -> War_hit on GDP increases with occupied zones and infra damage -> War tiredness increases (+0.15 to +0.20 per round for first 3 rounds, then +0.075 to +0.10 due to society adaptation) -> War tiredness erodes stability (`min(war_tiredness * 0.04, 0.4)`) and political support (`(war_tiredness - 2) * 1.0` for democracies) -> Election pressure -> Leadership change -> Ceasefire
**Feedback loop:** War -> casualties -> war tiredness -> stability drop -> political pressure -> potential leadership change -> ceasefire. The feedback runs through the political system: extended wars create irresistible pressure for peace, especially in democracies.
**Stabilizer:** (1) Society adaptation halves war tiredness growth after 3+ rounds. (2) War tiredness cap at 10.0. (3) War tiredness stability penalty capped at -0.4. (4) Autocracies feel less pressure (stability penalty dampened by 0.75 multiplier). (5) Rally-around-the-flag effect provides initial support boost (diminishing: `max(10 - war_duration * 3, 0)`).
**Observable:** In the Nordostan-Heartland war (started round -4), Heartland's war tiredness should be at 1.0-1.6 by round 0 (pre-existing war). By round 3, war tiredness should reach 2.0-2.5, at which point stability penalty is -0.08 to -0.10 per round and political support drops by 0.5-1.0 per round. By the Heartland election (round 3-4), war tiredness should be a major factor in election outcome. Rally effect should be near zero by round 3 (10 - 7*3 < 0). For democracies, war tiredness above 4 should make re-election nearly impossible.
**Failure mode:** (a) War tiredness never increasing (update function skipped). (b) War tiredness increasing linearly forever without adaptation (society adaptation not applied). (c) Autocracies feeling identical war tiredness pressure as democracies (resilience multiplier missing). (d) Rally-around-flag never decaying, permanently offsetting war tiredness.

---

## Dependency 13: Amphibious Impossibility -> Blockade-Only Option -> Economic Warfare

**Domain:** Military / Strategic
**Causal chain:** Cathay cannot achieve 3:1 force ratio needed for amphibious assault on Formosa -> Only viable military option is naval blockade -> Blockade cuts semiconductor supply (tech_impact 0.50 from Taiwan Strait) -> Global semiconductor crisis -> Economic warfare replaces kinetic warfare -> Countries dependent on Formosa chips suffer GDP contraction -> Political pressure on all affected countries
**Feedback loop:** Blockade -> semiconductor crisis -> economic damage to tech-dependent countries (including Cathay itself via formosa_dependency) -> political pressure on Cathay to lift blockade -> but lifting blockade = strategic defeat -> Cathay trapped in costly blockade or accepts loss of face. Meanwhile, semiconductor disruption damages Columbia's allies, potentially fracturing the alliance.
**Stabilizer:** (1) Cathay itself has formosa_dependency, so it suffers from its own blockade. (2) Blockade costs money (Dependency 11). (3) Duration-scaling severity (0.3 to 1.0) gives time for diplomatic resolution. (4) Alternative semiconductor suppliers implicit in severity cap.
**Observable:** Formosa has approximately 3-4 ground units and limited naval. Cathay has 7 naval, growing. Cathay ground forces are large but cannot project across the strait without massive naval superiority and air dominance. The engine should show that blockade is the only viable option (combat resolution should show amphibious assault failing). Once blockade is established, semiconductor disruption should cascade: round 1 severity 0.3, round 2 severity 0.5, round 3 severity 0.7. Countries with formosa_dependency > 0.5 should enter stressed/crisis state by round 3 of blockade.
**Failure mode:** (a) Amphibious assault succeeding with less than 3:1 ratio (combat engine too permissive). (b) Formosa blockade not triggering semiconductor disruption (formosa_disrupted check broken). (c) Semiconductor damage hitting all countries equally regardless of dependency (dependency value ignored). (d) Cathay suffering zero self-damage from its own blockade of Formosa (formosa_dependency not applied to Cathay).

---

## Dependency 14: Nuclear Deterrence -> Escalation Ceiling

**Domain:** Military / Strategic
**Causal chain:** Country possesses nuclear weapons (nuclear_level >= 2) -> Direct great-power invasion becomes existentially dangerous -> Conventional war limited to proxy conflicts and economic warfare -> Escalation ceiling prevents total war -> Conflicts channeled into sanctions, blockades, and proxy theaters
**Feedback loop:** Nuclear deterrence creates stability through fear. But it also creates "stability-instability paradox": because total war is prevented, limited provocations (proxy wars, blockades, sanctions) become more likely. More provocations -> more tension -> but never crossing nuclear threshold.
**Stabilizer:** (1) `nuclear_used_this_sim` flag tracks if nuclear weapons have been used -- this is a one-way door. (2) Nuclear use should trigger catastrophic stability, GDP, and political consequences. (3) AI combat bonus from nuclear level provides conventional advantage without use. (4) Mutual deterrence: both Columbia and Cathay have nuclear capability.
**Observable:** Columbia and Cathay both have nuclear_level 2+. Despite growing tensions and naval parity crossing, neither should initiate direct invasion of the other's homeland. Conflicts should remain in proxy theaters (Mashriq, Eastern Ereb) or economic (sanctions, blockades). If a player orders nuclear use, `nuclear_used_this_sim` should flip to True and catastrophic consequences should follow across all domains.
**Failure mode:** (a) AI recommending direct great-power invasion as if nuclear weapons do not exist (deterrence not factored into strategic calculus). (b) Nuclear weapons being used with no consequence tracking (flag not set). (c) Nuclear deterrence preventing ALL conflict including proxy wars (over-deterrence). (d) Countries without nuclear capability being treated as if they have it.

---

# POLITICAL DEPENDENCIES (15-20)

---

## Dependency 15: War Tiredness -> Stability Erosion -> Election Pressure

**Domain:** Political
**Causal chain:** Extended war -> War tiredness accumulates (+0.15 to +0.20 per round) -> Stability penalty (`war_tiredness * 0.04`, capped at -0.40) -> Political support drops for democracies (`(war_tiredness - 2) * 1.0` per round once tiredness > 2) -> Election approaches (Columbia midterms round 2, presidential round 5; Heartland rounds 3-4) -> Incumbent penalized by AI score formula (`war_penalty -5.0` per active war) -> Leadership change -> Policy shift
**Feedback loop:** War -> tiredness -> stability erosion -> support erosion -> election loss -> new leader may negotiate ceasefire -> ceasefire reduces tiredness (decays at 20% per round when not at war) -> stability recovers. The democratic cycle provides a self-correcting mechanism for ending unpopular wars.
**Stabilizer:** (1) Society adaptation halves tiredness growth after 3 rounds. (2) War tiredness decays when peace resumes (0.80 multiplier per round). (3) Rally-around-the-flag provides initial counter-boost. (4) Social spending can partially offset stability erosion. (5) Democratic wartime resilience bonus (+0.15 stability for frontline democracies).
**Observable:** In the Columbia-Persia war, Columbia's war tiredness should hit 0.30-0.45 by round 2 (midterm election). Combined with war_penalty (-5.0), economic performance, and stability, the midterm AI score should be 5-10 points below baseline. By round 5 (presidential), war tiredness at 1.0-1.5 should produce significant electoral headwinds. If Heartland's war tiredness reaches 2.5+ by round 3, the Heartland election should strongly favor the challenger.
**Failure mode:** (a) War tiredness never affecting elections (election formula not including war_penalty). (b) War tiredness resetting to zero each round instead of accumulating. (c) War tiredness affecting autocracies identically to democracies (regime type not checked in support formula). (d) Leadership change after election having no policy consequence (cosmetic only).

---

## Dependency 16: Economic Crisis -> Stability Crisis -> Regime Vulnerability

**Domain:** Political / Economic
**Causal chain:** GDP contraction -> Economic state escalates (normal -> stressed -> crisis -> collapse) -> Crisis stability penalty applied (-0.10/-0.30/-0.50 per round for stressed/crisis/collapse) -> Stability drops below thresholds (protest_probable at 5, protest_automatic at 3, regime_collapse_risk at 2) -> Protest risk and coup risk flags activate -> Regime status changes to "unstable" or "crisis" -> Capital flight (Pass 2: 3-8% GDP hit when stability < 3-4) -> Further GDP decline -> Deeper crisis
**Feedback loop:** Economic crisis -> stability drop -> capital flight -> worse economic crisis -> further stability drop. This is the vicious cycle that turns economic problems into political crises. The Pass 2 capital flight mechanism creates the key feedback: stability < 3 triggers 3-8% GDP hit (8% for democracies, 3% for autocracies), which worsens the economic state, which further reduces stability.
**Stabilizer:** (1) Peaceful non-sanctioned dampening: if not at war and not under heavy sanctions, negative stability delta is halved. (2) Autocracy resilience: negative delta multiplied by 0.75. (3) Stability floor at 1.0. (4) GDP floor at 0.5 coins. (5) Recovery is possible but slow (2-3 rounds of positive indicators needed for upward state transition).
**Observable:** A country with GDP growth of -5% should enter "stressed" state (2+ stress triggers likely: negative growth + potential treasury depletion). After 2 rounds of continued stress, "crisis" state follows. Crisis state applies 0.5x GDP multiplier, amplifying contraction. Stability should drop by 0.3-0.5 per round during crisis. If stability falls below 3, capital flight of 3-8% should be visible in Pass 2 adjustments. Below stability 2, regime_collapse_risk flag activates.
**Failure mode:** (a) Economic crisis having no stability impact (CRISIS_STABILITY_PENALTY not applied). (b) Capital flight not triggering in Pass 2 despite low stability (threshold check wrong). (c) Crisis state not applying GDP multiplier (CRISIS_GDP_MULTIPLIER missing from GDP calculation). (d) Instant recovery from collapse to normal in one round (recovery_rounds requirement bypassed).

---

## Dependency 17: Ceasefire -> Stability Recovery -> Momentum Boost

**Domain:** Political / Economic
**Causal chain:** Ceasefire declared -> War ends -> War tiredness begins decaying (0.80 multiplier per round) -> Stability erosion from war friction stops -> Ceasefire rally: momentum boost of +1.5 (Pass 2) -> GDP recovery begins -> Positive GDP growth -> Stability improves -> Political support recovers -> But recovery is SLOW (hysteresis)
**Feedback loop:** Peace -> momentum boost -> better GDP growth -> better stability -> better political support -> continued peace. The positive cascade is real but asymmetric: destruction is fast, recovery is slow. Momentum builds at max +0.3/round but crashes at up to -2.0/round.
**Stabilizer:** (1) Momentum cap at +5.0 prevents unlimited optimism. (2) Recovery requires sustained positive indicators (2-3 rounds for state transition upward). (3) Debt burden accumulated during war does not disappear -- it continues to drain revenue even after peace. (4) Infrastructure damage persists until rebuilt.
**Observable:** After a ceasefire, the first round should show: momentum jump of +1.5, war tiredness beginning to decay (from X to X*0.8), war friction on stability stopping. GDP growth should improve by 1-2% within 2 rounds (momentum effect of +1.5 * 0.01 = +1.5%). Economic state transition from crisis to stressed should take 2 rounds of positive indicators. Full recovery from collapse to normal should take 6-8 rounds (3 rounds collapse->crisis, 2 rounds crisis->stressed, 2 rounds stressed->normal).
**Failure mode:** (a) No ceasefire rally in momentum (Pass 2 detection of war->peace transition broken). (b) Instant recovery -- economic state jumping from collapse to normal in one round (recovery_rounds check absent). (c) War tiredness not decaying after peace (decay multiplier not applied when not at war). (d) Debt burden magically disappearing upon ceasefire (no mechanism for this, which is correct).

---

## Dependency 18: Autocratic Resilience -> Sanctions Absorption -> Prolonged Conflict

**Domain:** Political
**Causal chain:** Autocracy faces sanctions + war -> Stability erosion is DAMPENED (negative delta * 0.75) -> Siege resilience bonus (+0.10 stability per round for autocracies at war under heavy sanctions) -> Slower political collapse -> Can absorb more economic pain before regime crisis -> Conflict continues longer than democratic counterpart would tolerate
**Feedback loop:** Sanctions -> economic pain -> but autocratic resilience absorbs it -> war continues -> more sanctions -> more pain -> but regime still holds. The pressure builds invisibly until a tipping point. When the autocracy finally breaks (stability < 2), it breaks catastrophically -- no election mechanism for gradual policy change, only coup or collapse.
**Stabilizer:** (1) Resilience delays but does not prevent collapse -- stability still declines, just slower. (2) Capital flight is lower for autocracies (3% vs 8% for democracies when stability < 3) but still exists. (3) Coup risk activates at stability < 6, adding an invisible threat. (4) No election mechanism means no gradual pressure release -- it is all-or-nothing.
**Observable:** Compare Nordostan (autocracy) vs. hypothetical democracy under identical sanctions. Nordostan should lose stability at approximately 75% the rate of a democracy (0.75 multiplier on negative delta). Additionally, siege resilience bonus of +0.10 partially offsets war + sanctions friction. Net: Nordostan should sustain 4-6 rounds of heavy sanctions before reaching stability 3-4 (danger zone), whereas a democracy would reach it in 2-3 rounds. But when Nordostan finally breaks, it should go from "functional" to "collapse" rapidly because there is no election safety valve.
**Failure mode:** (a) Autocratic resilience multiplier not applied (regime type check missing). (b) Siege resilience bonus too large, making autocracies invulnerable to sanctions (bonus should be small: +0.10 vs. much larger negative pressures). (c) Autocracies and democracies collapsing at identical rates (no regime differentiation). (d) Autocracies having elections (regime type not checked in election processing).

---

## Dependency 19: Democratic Accountability -> Election-Driven Policy Shifts

**Domain:** Political
**Causal chain:** Economic pain (oil shock, war costs, sanctions blowback) -> GDP contraction -> Political support drops -> Election approaches (scheduled events: Columbia midterms R2, Heartland wartime R3-4, Columbia presidential R5) -> AI election score penalizes incumbent for economic crisis (-5/-15/-25 for stressed/crisis/collapse), oil shock (-(oil_price - 150) * 0.1), and war (-5.0 per active war) -> Incumbent loses -> New leader may change policy
**Feedback loop:** Economic pain -> voter anger -> incumbent loses -> new leader changes policy (ceasefire, sanctions adjustment, spending reallocation) -> economic recovery -> voter satisfaction -> new leader retains power. The electoral cycle forces democratic responsiveness to material conditions.
**Stabilizer:** (1) Elections are at FIXED rounds (not triggered by events), creating predictable pressure points. (2) AI score is 50% weight, player vote is 50% -- player agency preserved. (3) Mean-reversion in support toward 50% (`-(old_sup - 50) * 0.05`). (4) Rally-around-flag can boost support early in war.
**Observable:** Columbia midterms (round 2): if Columbia is in "stressed" economic state with oil at $175 and an active war, AI score should be approximately: `50 + (gdp_growth * 10) + (stability - 5) * 5 - 5 (war) - 5 (stressed) - 2.5 (oil)` = roughly 30-35. With player vote at 50-50, incumbent score would be ~40-42, meaning incumbent LOSES the midterms. Columbia presidential (round 5): by this point, cumulative war tiredness and economic damage should make re-election extremely difficult unless ceasefire + recovery has occurred.
**Failure mode:** (a) Elections not firing at scheduled rounds (SCHEDULED_EVENTS not checked). (b) Crisis penalty not applied in election formula (crisis_penalty variable always zero). (c) Oil penalty not applied to oil importers in elections (oil_penalty always zero). (d) Election results having no mechanical consequence (parliament composition, leader change cosmetic only).

---

## Dependency 20: Alliance Fracture -> Individual Deals -> System Fragmentation

**Domain:** Political / Strategic
**Causal chain:** Alliance members under differential pressure (Ponte suffers from oil shock, Vinland from semiconductor disruption, Saudara from trade loss) -> Members cut individual deals with adversaries (Ponte trades with Cathay, Saudara reduces sanctions) -> Sanctions coalition coverage drops below 60% -> Sanctions effectiveness collapses to 30% (`effectiveness = 0.3 if coalition_coverage < 0.6`) -> Adversary's GDP recovers -> Alliance purpose undermined -> Further defections
**Feedback loop:** Alliance fracture -> reduced sanctions effectiveness -> adversary recovers -> alliance looks futile -> more defections -> complete fragmentation. The 60% coalition coverage threshold creates a cliff: sanctions are either effective (>60%) or largely useless (<60%), creating strong incentive to defect once the coalition appears shaky.
**Stabilizer:** (1) Large coalitions have buffer -- losing one small member may not drop below 60%. (2) Bilateral trade weights mean some members are more important than others for sanctions effectiveness. (3) Adversary recovery takes time (2-3 rounds for state transition up), giving alliance time to re-coalesce. (4) Alliance obligations (org_memberships, treaties) create institutional friction against defection.
**Observable:** The sanctions coalition against Nordostan likely includes Columbia, Ponte, Vinland, and possibly others. If the coalition trade weight with Nordostan totals 65%, losing Ponte (trade weight ~15%) drops coalition to 50%, crossing the 60% threshold. Sanctions damage should visibly drop by approximately 70% in the next round (from effectiveness 1.0 to 0.3). This cliff effect should be dramatic and observable in Nordostan's GDP trajectory.
**Failure mode:** (a) Coalition coverage not calculated correctly (trade weights not summed). (b) Effectiveness always at 1.0 regardless of coalition size (threshold check missing). (c) No cliff effect -- linear degradation instead of binary threshold (formula changed). (d) Individual country leaving sanctions having no effect on coalition coverage (bilateral sanctions tracked independently without coalition logic).

---

# CROSS-DOMAIN DEPENDENCIES (21-25)

---

## Dependency 21: Military Overstretch + Economic Crisis = Strategic Retreat

**Domain:** Cross-domain (Military + Economic + Political)
**Causal chain:** Country fights in multiple theaters -> Military maintenance costs escalate (0.3 coins per unit * many units) -> Economic crisis simultaneously hits GDP and revenue -> Budget cannot cover maintenance + war costs + social spending -> Forced austerity: cut social spending OR military -> Cutting social spending crashes stability -> Cutting military weakens war effort -> War losses -> War tiredness -> Political support drops -> Forced withdrawal from least vital theater
**Feedback loop:** Overstretch + crisis creates a reinforcing doom loop. Each round without relief makes the next round worse: debt accumulates, maintenance costs persist, GDP shrinks, revenue shrinks, deficit grows, money printing inflates, inflation erodes revenue further. The only exit is withdrawing from a theater, which concedes strategic position but relieves fiscal pressure.
**Observable:** Columbia with 30+ total military units pays ~9 coins/round maintenance. If GDP drops to 70 (from 90 baseline) and revenue falls to ~12 (GDP * 0.18 tax - debt - inflation erosion), mandatory costs (maintenance 9 + social baseline ~17.5) = 26.5 far exceed revenue of 12. Deficit of ~14.5 coins per round. Treasury depletes in 1-2 rounds. Money printing commences. This fiscal crisis should be VISIBLE: treasury = 0, inflation spiking, economic state escalating to stressed/crisis.
**Failure mode:** (a) Military maintenance not subtracted from budget (mandatory costs ignored). (b) Countries able to maintain unlimited armies at zero cost. (c) Deficit spending with no inflation consequence (money printing chain broken). (d) Social spending cuts having no stability impact (social_ratio check absent).

---

## Dependency 22: Tech Race + Rare Earth Restrictions = R&D Arms Race

**Domain:** Cross-domain (Technology + Economic + Strategic)
**Causal chain:** Cathay and Columbia compete for AI technology supremacy (AI levels: Columbia L2, Cathay L3 at start) -> R&D investment required (coins / GDP * 0.8 multiplier) -> Cathay imposes rare earth restrictions on Columbia -> Columbia R&D slowed by 15% per restriction level (floor 40%) -> Columbia falls further behind in AI -> AI level provides GDP boost (L3: +15%, L4: +30%) and combat bonus -> Technology gap becomes strategic advantage
**Feedback loop:** Tech investment -> AI level up -> GDP boost from tech -> more revenue for further tech investment -> faster advancement. The rich-get-richer dynamic in technology. But rare earth restrictions act as friction: restricted countries must invest more for the same progress.
**Stabilizer:** (1) R&D thresholds increase with each level (L1: 0.20, L2: 0.40, L3: 0.60, L4: 1.00) -- diminishing returns on R&D investment. (2) Rare earth restriction floor at 40% (never completely blocks R&D). (3) Economic crisis reduces available R&D budget. (4) Brain drain (Pass 2) reduces R&D progress for democracies in crisis (-0.02 per round).
**Observable:** Columbia at AI L2 with progress 0.80 needs to reach threshold 0.60 (already past it -- should level up to L3). With rare earth restrictions at level 2, Columbia's R&D factor drops to 0.70. An investment of 5 coins against GDP 90 yields: `(5/90) * 0.8 * 0.70 = 0.031` progress per round. To advance from L3 to L4 (threshold 1.00), Columbia needs approximately 32 rounds at this rate -- very slow. Without restrictions (factor 1.0), it would take approximately 22 rounds. The 10-round delay is strategically significant.
**Failure mode:** (a) Rare earth restrictions having no effect on R&D (rare_earth_factor always 1.0). (b) AI level bonuses not applied to GDP (AI_LEVEL_TECH_FACTOR not used in GDP formula). (c) R&D progress resetting between rounds (not persisted in state). (d) Both sides reaching L4 simultaneously regardless of investment (threshold-based progression broken).

---

## Dependency 23: Formosa Blockade = Simultaneous Military + Economic + Political Crisis

**Domain:** Cross-domain (the Big One)
**Causal chain:** Cathay initiates Formosa blockade ->
  MILITARY: Naval forces deployed, Taiwan Strait blocked, combat possible ->
  ECONOMIC: Semiconductor supply disrupted (tech_impact 0.50), all dependent economies hit, oil price +10% (formosa disruption), trade volume reduced ->
  POLITICAL: War declared (stability hit), war tiredness begins accumulating, Columbia faces decision to intervene (overstretch risk), global alliance pressure ->
  CASCADING: Semiconductor disruption -> tech-dependent GDP crash (Dependency 5) -> economic crisis for multiple countries -> contagion (Dependency 7) -> election pressure in democracies (Dependency 19) -> potential alliance fracture (Dependency 20)
**Feedback loop:** The Formosa blockade is the scenario where multiple dependencies fire simultaneously and reinforce each other. Semiconductor disruption hits GDP, which hits revenue, which hits military spending, which weakens the response capacity, which prolongs the blockade, which deepens the semiconductor disruption. Meanwhile, political pressure from economic pain forces democratic leaders to either escalate (risking nuclear confrontation) or negotiate (conceding strategic position).
**Stabilizer:** (1) Duration-scaling semiconductor severity (0.3 to 1.0) provides a 1-2 round window for diplomacy. (2) Cathay self-damage from its own blockade. (3) Nuclear deterrence prevents escalation to total war. (4) Economic attrition limits blockade sustainability. (5) Alliance response (if coordinated) can apply counter-pressure through sanctions on Cathay.
**Observable:** Round 1 of Formosa blockade: oil +10%, semiconductor severity 0.3, Columbia/Cathay/Ponte GDP hit 1-3%, momentum crash -0.5 for dependent countries. Round 2: severity 0.5, GDP hit 3-6%, stress triggers accumulating. Round 3: severity 0.7, GDP hit 5-10%, crisis state likely for high-dependency countries, contagion firing, election pressure visible. Round 4+: severity 0.9-1.0, full economic crisis across tech-dependent world, political pressure overwhelming, ceasefire or escalation decision forced.
**Failure mode:** (a) Formosa blockade not triggering semiconductor disruption (missing link between blockade status and formosa_disrupted). (b) Only direct participants affected, no global cascade. (c) No escalation over time (duration-scaling absent). (d) Political consequences not materializing despite severe economic damage (stability/support formulae not connected to semiconductor crisis).

---

## Dependency 24: Peace Deal = Economic Recovery + Military Drawdown + Political Legitimacy

**Domain:** Cross-domain (the Positive Cascade)
**Causal chain:** Ceasefire/peace treaty signed ->
  ECONOMIC: Momentum boost +1.5 (Pass 2), war_hit on GDP stops, sanctions may be lifted -> Revenue improves -> Budget surplus possible -> Treasury rebuilds -> Inflation decays (0.85 per round) -> Economic state begins recovering (stressed -> normal in 4+ rounds) ->
  MILITARY: War costs stop, maintenance returns to peacetime levels, units can be demobilized -> Budget freed for civilian spending ->
  POLITICAL: War tiredness decays (0.80 per round), stability improves, political support recovers, election prospects improve -> Leadership legitimized by peace
**Feedback loop:** Peace -> recovery -> stability -> confidence -> GDP growth -> more recovery. The positive cascade mirrors the negative one but is SLOWER (asymmetric by design). Recovery from crisis takes 2 rounds per state level; recovery from collapse takes 3 rounds just to reach crisis. Total recovery from collapse to normal: 7+ rounds.
**Stabilizer:** (1) Debt burden persists after peace -- accumulated war debt continues to drain revenue. (2) Infrastructure damage persists until rebuilt. (3) War tiredness decays at 20% per round, not instantly. (4) Momentum builds slowly (+0.3 max per round upward) vs. crash speed (-2.0 per round downward). (5) Lost territory/units are not recovered automatically.
**Observable:** After ceasefire in the Nordostan-Heartland war: Heartland should see momentum jump +1.5 in first round of peace. GDP growth should improve by ~1.5% within 2 rounds. War tiredness should decay from (e.g.) 3.0 to 2.4 to 1.92 to 1.54 over 3 rounds. Stability should improve by 0.1-0.2 per round once war friction stops. But debt burden and inflation legacy should keep the economy in "stressed" state for 2-4 rounds after ceasefire. Full recovery to pre-war baseline GDP should take 5-8 rounds -- much longer than it took to destroy.
**Failure mode:** (a) No peace dividend (ceasefire rally missing in Pass 2). (b) Instant full recovery (crisis state jumping to normal without recovery_rounds). (c) Debt burden disappearing upon peace (no mechanism for this, and none should exist). (d) Symmetric recovery speed -- rebuilding as fast as destroying (momentum should build at +0.3 max but crash at -2.0).

---

## Dependency 25: The Thucydides Trap Itself

**Domain:** Cross-domain (the Structural Dynamic)
**Causal chain:** Rising power (Cathay) approaches parity with established power (Columbia) across multiple dimensions ->
  NAVAL: Cathay builds toward naval parity (7 -> 11+ over 4 rounds) ->
  TECHNOLOGY: Cathay at AI L3 (Columbia L2), closing gap in tech GDP bonus ->
  ECONOMIC: Cathay GDP large and growing (base growth rate likely 4-6%), Columbia GDP largest but slower growth (2-3%) ->
  POLITICAL: Cathay autocratic (can absorb short-term pain for long-term strategy), Columbia democratic (constrained by elections at R2 and R5) ->
  STRATEGIC: As parity approaches, Columbia faces "now or never" window -- if it does not act before Cathay achieves superiority, it loses the option to act ->
  RESPONSE: Columbia overreacts with preemptive containment (sanctions, naval buildup, alliance strengthening) -> Cathay interprets containment as aggression -> Escalation spiral -> Potential conflict over Formosa, South China Sea, or trade
**Feedback loop:** The Thucydides Trap is itself a feedback loop: fear of rising power -> containment -> adversary interprets as hostile -> counter-buildup -> original fear confirmed -> more containment -> escalation. Each action taken to prevent war makes war more likely.
**Stabilizer:** (1) Nuclear deterrence caps escalation (Dependency 14). (2) Economic interdependence (contagion means conflict hurts both sides). (3) Democratic accountability constrains Columbia's aggression (elections punish wars). (4) Cathay's autocratic patience (can wait rather than force confrontation). (5) Diplomatic channels (treaties, organizations, back-channel deals).
**Observable:** Over the 5-round simulation, the following trajectory should be visible:
  - Round 0-1: Tension builds. Cathay naval approaches 8-9. Columbia considers sanctions/tariffs on Cathay. Trade friction begins.
  - Round 2-3: Pressure points emerge. Cathay may consider Formosa blockade if naval reaches 10+. Columbia faces midterm election pressure. Proxy wars (Mashriq, Eastern Ereb) absorb attention and resources.
  - Round 3-4: Strategic window opens or closes. If Cathay reaches naval parity AND Columbia is overstretched in Mashriq, the Formosa scenario becomes possible. If Columbia has invested in naval buildup, the window closes and competition shifts to economic/technological.
  - Round 5: Resolution or continuation. Democratic accountability (Columbia presidential election) forces a reckoning. The simulation should demonstrate that the Thucydides Trap dynamic is emergent from the individual dependencies, not hardcoded.

  The ENTIRE simulation should show the parity-fear-escalation dynamic playing out through the interconnection of all 24 preceding dependencies. Naval buildup (9) creates the military precondition. Economic interdependence (7) creates the mutual cost. Nuclear deterrence (14) channels competition into economic warfare (11, 13). Democratic accountability (19) constrains one side. Autocratic resilience (18) advantages the other. The trap is not in any single dependency but in their interaction.
**Failure mode:** (a) No visible parity trend -- Cathay staying permanently weaker with no catch-up mechanism. (b) Conflict erupting in round 1 before tension has built (no gradual escalation). (c) Dependencies operating in isolation -- oil price shock having no connection to military positioning, elections having no connection to war decisions. (d) Deterministic outcome -- the trap always producing war OR always producing peace, regardless of player decisions. The correct behavior is that the trap creates PRESSURE toward conflict, but player agency can navigate around it. (e) Columbia and Cathay coexisting without any visible tension despite structural incentives for competition.

---

# DEPENDENCY INTERACTION MATRIX

The following pairs of dependencies MUST interact correctly in the engine:

| Dependency A | Dependency B | Interaction |
|---|---|---|
| 1 (Oil shock) | 6 (Producer windfall) | Same oil price feeds opposite effects: importers hurt, producers benefit |
| 2 (Sanctions) | 8 (OPEC dilemma) | Sanctions on oil producers reduce supply, which raises price, which partially funds the sanctioned producer |
| 3 (Money printing) | 4 (Debt spiral) | Money printing covers deficit but creates inflation; debt accumulation creates permanent revenue drain |
| 5 (Semiconductor) | 13 (Amphibious impossibility) | Blockade is the only viable Formosa military option, and it triggers semiconductor crisis |
| 7 (Contagion) | 23 (Formosa blockade) | Formosa blockade triggers semiconductor crisis in multiple countries, creating contagion cascade |
| 9 (Naval buildup) | 25 (Thucydides trap) | Naval parity crossing is the key military trigger for the broader Thucydides dynamic |
| 10 (Overstretch) | 21 (Strategic retreat) | Overstretch creates the military precondition; economic crisis provides the fiscal trigger for retreat |
| 12 (War attrition) | 15 (War tiredness) | Military degradation and political fatigue are parallel tracks that converge at ceasefire pressure |
| 16 (Econ crisis -> stability) | 19 (Elections) | Economic crisis feeds directly into election outcomes via crisis_penalty and oil_penalty |
| 18 (Autocratic resilience) | 20 (Alliance fracture) | Autocratic resilience prolongs conflict, which increases pressure on democratic alliance members to defect |
| 17 (Ceasefire recovery) | 24 (Peace deal cascade) | Ceasefire triggers the positive cascade but recovery is asymmetrically slow |

---

# ENGINE FORMULA QUICK REFERENCE

For calibration testing, the key formulas and their locations in `world_model_engine.py`:

| Variable | Formula | Line (approx) |
|---|---|---|
| Oil price | `base * (demand/supply) * disruption * (1 + war_premium)` with soft cap above $200 | 371-378 |
| GDP growth | Additive factors * crisis_multiplier | 472-478 |
| Oil shock (importers) | `-0.02 * (oil_price - 100) / 50` when oil > $100 | 432 |
| Oil shock (producers) | `+0.01 * (oil_price - 80) / 50` when oil > $80 | 436 |
| Semiconductor hit | `-dep * severity * tech_sector_pct`, severity ramps 0.3 + 0.2*rounds | 447-448 |
| Sanctions hit | `-sanctions_damage * 2.0`, diminishing at 0.70 after 4 rounds | 417-423 |
| Revenue | `GDP * tax_rate + oil_rev - debt - inflation_erosion - war_damage - sanc_cost` | 542 |
| Money printing inflation | `money_printed / gdp * 80.0` | 596, 731 |
| Debt accumulation | `deficit * 0.15` per round, permanent | 599, 746 |
| Inflation decay | `prev * 0.85` natural, 80x spike from printing | 727-731 |
| Crisis GDP multiplier | normal=1.0, stressed=0.85, crisis=0.5, collapse=0.2 | 63-68 |
| Crisis stability penalty | normal=0, stressed=-0.10, crisis=-0.30, collapse=-0.50 | 71-75 |
| Momentum limits | +0.3/round build, -2.0/round crash, range [-5, +5] | 862-891 |
| Contagion hit | `severity * trade_weight * 0.02` for trade_weight > 0.10 | 925-926 |
| War tiredness growth | Defender +0.20, attacker +0.15, ally +0.10; halves after 3 rounds | 1800-1815 |
| Stability autocracy resilience | `delta *= 0.75` when negative | 1065-1066 |
| Sanctions effectiveness threshold | 1.0 if coalition >= 60% trade weight, 0.3 otherwise | 1624 |
| Election crisis penalty | stressed=-5, crisis=-15, collapse=-25 | 1178-1183 |
| Capital flight (Pass 2) | 8% GDP (democracy) or 3% GDP (autocracy) when stability < 3 | 1294-1295 |

---

# CALIBRATION TEST PROTOCOL

For each dependency, run the engine with controlled inputs and verify:

1. **Direction test:** Does the output move in the correct direction? (e.g., high oil -> lower GDP for importers)
2. **Magnitude test:** Is the magnitude within the specified range? (e.g., oil at $200 -> 4-8% GDP contraction)
3. **Feedback test:** Does the feedback loop engage? (e.g., GDP contraction -> demand destruction -> oil price moderation)
4. **Stabilizer test:** Does the runaway prevention work? (e.g., oil price stays below $250 due to soft cap)
5. **Interaction test:** Do interacting dependencies produce the correct combined effect? (e.g., sanctions + oil shock producing compounding damage, not independent damage)
6. **Asymmetry test:** Is destruction faster than recovery? (momentum crash -2.0 vs. build +0.3; downward state transitions immediate vs. upward requiring 2-3 rounds)
7. **Regime test:** Do autocracies and democracies respond differently? (resilience multiplier, election pressure, capital flight rates)

---

*Document version: 1.0*
*Engine version: world_model_engine.py v2 (SEED)*
*Last updated: 2026-03-28*
