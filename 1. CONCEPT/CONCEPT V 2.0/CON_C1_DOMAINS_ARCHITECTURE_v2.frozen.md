# Thucydides Trap SIM — Game Domains Architecture
**Version:** 2.0 | **Date:** 2026-03-21 | **Status:** Aligned with E1 Engine Architecture v0.7

---

## Overview

The SIM operates across four interconnected domains. Each domain has trackable resources, participant decisions, and AI-calculated consequences. The domains are not independent — every action in one creates ripples in the others. The elegance test: **every mechanic must create a dilemma, not just a calculation.**

Primary gameplay is free-form negotiation and diplomacy. The four domains provide the stakes, constraints, and consequences that give negotiations their weight.

### Design Principles (cross-cutting)

- **Voluntary action, status quo default.** No country is forced to change anything each round. If nothing is submitted, previous settings continue. Game pressure — not game rules — drives action.
- **Simple decisions, complex consequences.** Participants make policy choices (pick a number, check a box, sign a deal). The AI engine calculates the cascading effects across all domains.
- **Graduated complexity by role.** Great powers with multiple roles manage all domains actively. Single-role countries manage selectively. AI-operated countries are handled entirely by AI participants or the AI world model engine.
- **Decision rights are split.** In countries with multiple roles, no single person controls everything. The budget requires the PM; attacks require the president AND/OR defense minister; nuclear launch always requires 3 confirmations (head of state + military chief + one additional authority, all within 2 minutes); in smaller teams, an AI military advisor provides the missing confirmation and may refuse if strategically irrational. Though leaders can override, or change the subordinates. The split is itself the internal politics mechanic.
- **Spot transactions are irreversible.** Any deal confirmed by two parties executes immediately in the system. No take-backs. Commitment has weight. To revert the actors just need to execute a reverse deal voluntarily.
- **The balance of power is a question, not an answer.** The SIM's central question — has the rising power matched the hegemon? — is never answered by the system. The public dashboard shows raw data (ship counts, GDP, tech investment levels) but not conclusions. Each team's starting brief contains a different intelligence assessment of the same reality. Participants must interpret ambiguous data, seek additional information through intelligence actions and allied sharing, and act on their own judgment. Misperception — two sides acting rationally on different pictures — is the Trap's most dangerous mechanism. Giving participants certainty would break it.

---

## Domain 1 — Military

### What It Represents

The shadow behind every negotiation. Most participants will never command troops to fight, but everyone must think about force — because it's what gives diplomatic positions their credibility. The primary dynamic is deterrence, posture, and deployment — with combat as one possible outcome.

### Trackable Resources

**Five unit types:**

| Type | What it does | Producible | Notes |
|------|-------------|:----------:|-------|
| Ground forces | Territory control, land warfare, border defense | Yes (budget) | The default. RISK-model combat. Dominant in European theater. |
| Naval forces | Sea control, blockades, coastal bombardment (10%/unit), amphibious ops | Yes (budget) | Required for Formosa scenario. ~6-8 countries have significant navies. |
| Tactical air / missiles | Short-range strikes, battlefield support, drones | Yes (budget) | Adjacent to own forces/bases only. Disposable — consumed on use. |
| Strategic missiles | Long-range precision strike, global reach. **Warhead type (conventional or nuclear) chosen at launch — unknown to target.** | Cathay only (+1/round if funded) | Fixed starting allocation per country (Columbia ~10, Nordostan ~10, Cathay ~3+growing, Gallia ~2, Albion ~2). Only countries with nuclear L1+ can choose nuclear warhead. Global alert on launch. 10-min real-time execution window. |
| Air defense | Protects zones from incoming air/missile strikes. Absorbs up to 3 strikes per unit. | Not producible | Fixed starting allocation. Scarce, tradeable. Deployment to zones is a major strategic decision. |

### Deployment and Basing

All units (apart from air/missile forces) are deployed to **theaters** visible on the global map. Redeployment between theaters takes **1 round** — this delay is the core mechanic creating the "overstretched hegemon" problem.

**Own territory:** Free deployment, no permission needed.

**Columbia's base network:** 4-5 global bases (Pacific/Yamato, Ereb/Teutonia, Mashriq/Gulf, Indian Ocean, possibly Mediterranean). Each requires host consent. Host can renegotiate or revoke. Bases enable instant theater access without transit delay — Columbia's unique structural advantage and diplomatic vulnerability.

**Foreign soil:** Requires explicit host agreement. Negotiated deal — may involve coins, security guarantees, political commitments. Creating a new foreign base is a major diplomatic event.

### Participant Decisions

**Each round (budget cycle — submitted, processed between rounds):**
- National budget allocation: social spending, military production by unit type (ground, naval, tactical air), strategic missile production (Cathay only), tech R&D, reserves
- Production tiers per unit type: Normal (1× cost per unit for 1× output), Accelerated (2× cost per unit for 2× output; total cost 4×), Maximum (4× cost per unit for 3× output; total cost 12×)
- Mobilization level (partial / general / total — submitted anytime, executed between rounds)
- Tariffs and sanctions (separate submissions)

**Real-time during rounds (Market Engine):**
- Arms transfers (sell or gift any type and quantity of military units — transferred units have reduced effectiveness for 1 round)
- Basing rights: grant or revoke

**Real-time during rounds (Live Action Engine):**
- Attack / initiate combat (RISK model — head of state + military chief authorization)
- Naval blockade (requires naval units in zone)
- Tactical air/missile strike (adjacent to own forces, disposable)
- Strategic missile launch (global range, warhead type private, global alert triggered)
- Nuclear test (L1+ countries, probabilistic success)

**After World Model processing (5-minute deployment window):**
- Deploy newly available units (produced, mobilized, arrived) to zones on map

### Balancing Mechanics

Production capacity limits (each country has maximum units per type per round). Accelerated/maximum production follows an escalating cost-per-unit curve (1×/2×/4× per unit for 1×/2×/3× output; total cost 1×/4×/12×). Surge production is available but ruinously expensive. Country-specific maintenance costs (Columbia pays more per unit than Cathay/Nordostan). Absorption limits (transferred units at reduced effectiveness for 1 round). Seller depletion (selling = losing your own units). Strategic missiles and air defense are non-producible scarce resources (except Cathay's +1/round). Attack less efficient than defense (RISK model — attacker loses ties). Landing operations severely penalized. Ground attacks costly and politically risky (casualties cost domestic support).

### Combat Resolution

**RISK-model with universal resolution mechanic.** All probabilistic combat actions follow the same pattern: AI calculates probability → key factors displayed → visual dice/fortune wheel → result with narrative. Ground/naval combat: dice per unit pair, attacker loses ties. Modifiers: tech level, morale (from stability), theater-specific factors, first-deployment penalty, landing penalty. Results: casualties by unit type, territory changes. Cascading effects (GDP damage, stability impact) calculated by World Model Engine between rounds.

**Amphibious assault rules:**
- Standard amphibious: 3:1 force ratio required (after all modifiers). Below 3:1, assault automatically fails.
- Naval superiority prerequisite: no uncontested enemy naval units may remain in the sea zone before landing operations can begin.
- Formosa-specific: 4:1 force ratio required (terrain, decades of defensive preparation, strait width).
- Pre-landing bombardment: naval units (10% chance per unit of destroying one defender) and tactical air strikes can reduce defender count before the ratio check.

### Theater Activation

> **SEED DECISION (2026-03-27):** Theater activation limited to Eastern Ereb. Other theaters use global hexes.

The global map starts with **two active theaters** (Eastern Ereb and Mashriq - Persia). Other theaters (Pacific/Taiwan, Korea, South Asia, Caribbean) activate **dynamically** when military action in that region escalates. Each activated theater gets a zoom-in map with simplified sectors. The number of active theaters at game end is itself a measure of outcome.

### Connections to Other Domains

→ **Economy:** Military budget competes with social spending. Arms production and maintenance cost coins. War destroys economic capacity. Blockades disrupt trade. Arms sales generate revenue.
→ **Domestic Politics:** Casualties lower stability. Mobilization lowers stability. Wars can temporary boost political support. War fatigue gradually depletes support and unit's morale. Victories temporarily boost political support. Low stability = low troop morale (combat penalty).
→ **Technology:** Available technologies (Nuclear, Naval unit production, Rockets, AI) are essential part of the military might. Can be sold/bought from the country that owns it. Will start to be available for production with 2 rounds dealay. But units can be used next round. AI resaching certain level can provide combat modifiers (+1/+2 on dice). 

---

## Domain 2 — Economy

### What It Represents

**Economic power IS the primary great-power competition**. Tariffs, sanctions, currency architecture, energy pricing, tech restrictions — these are the weapons most countries actually use.

### Trackable Resources

**Coins** — the universal hard currency. Digital. Realistic - like a real currency. Every transaction tracked. State treasuries and personal wealth (available for all roles, avalable from start and actively played by certain roles: oligarchs, business figures, Gulf royals — ~8-12 roles). Spot transactions are immediate and irreversible.

**Economic structure** — each country has a fixed profile showing GDP composition across four sectors: Resources, Industry, Services, Technology. Participants don't manage sector allocation — the profile determines how specific sanctions, tariffs, and shocks affect them. E.g., Nordostan is Resources-heavy (vulnerable to energy sanctions), Cathay is Industry-heavy (vulnerable to tariffs), Columbia is Services/Tech-heavy (vulnerable to financial counter-measures).

### Budget Cycle (each round — submitted, processed by World Model Engine)

Every country submits a budget. The PM / finance minister owns it; head of state can override. Columbia: requires parliamentary majority (3 of 5 seats).

**Revenue** (calculated by engine — not a participant decision):
Revenue = f(GDP, tax_rate, trade_income, oil_revenue) - sanctions_cost - inflation_erosion - war_damage. See E1.2 for full formula.

**Mandatory costs (auto-deducted):**
- Military maintenance: existing units × country-specific cost per type (Columbia pays more per unit than Cathay/Nordostan — advanced equipment, higher wages)
- Remainder = discretionary budget

**Allocation decisions:**
- Social spending (baseline = % of GDP; below → stability hit; above → diminishing boost)
- Ground unit production (Normal: 1× cost per unit for 1× output. Accelerated: 2× cost per unit for 2× output; total cost 4×. Maximum: 4× cost per unit for 3× output; total cost 12×.)
- Naval unit production (same tiered structure)
- Tactical air/missile production (same)
- Strategic missile production (Cathay ONLY: +1/round if funded)
- Tech R&D (split: nuclear R&D + AI/semiconductor R&D — accelerates progress toward pre-set breakthrough thresholds)
- Reserves (savings)

**Deficit rules:** If allocation exceeds revenue: cut spending, print money (adds to cumulative inflation), or draw from reserves. Reserves at zero + deficit = economic crisis (engine auto-cuts production, then social spending, then unit attrition).

**Debt service:** Cumulative deficits create a growing debt burden. Each round of deficit spending adds approximately 10-15% of the deficit amount as permanent "debt service" to next round's mandatory costs. Countries that print money AND run deficits get hit twice (inflation + debt service). Some countries start with pre-existing debt burden (notably Ponte/Italy), making them budget-constrained from Round 1.

**Budget deadline is hard.** Miss it and defaults apply (previous round continues).

### The Tarrifs and Sanctions Game

**Tariffs** (unilateral, graduated, continuous):
- Any country can set tariff levels (0-3) against any other country, per economic sector
- Level 0 = free trade. Level 1 = moderate. Level 2 = heavy. Level 3 = prohibitive (near-sanction)
- Unilateral — no coalition needed. This is the weapon you use on allies too
- Retaliation spiral: target can counter-tariff, creating tit-for-tat escalation
- Third-country rerouting: goods flow around tariff walls, benefiting neutral countries
- Tariff revenue accrues to imposer but import costs rise (inflationary)
- AI engine calculates aggregate effects: revenue, costs, rerouting, GDP impact
- **Net cost to imposer:** Tariff revenue offsets approximately 60-80% of the GDP cost imposed on imports (tariffs are net-negative for the imposer's economy — you collect revenue but consumers and businesses pay more than you collect)
- **Third-country rerouting:** A portion of tariffed trade redirects through third countries, benefiting neutral parties and diluting the tariff's impact over time

**Sanctions** (coalition-based, dramatic, binary):
- Counries can sanction any sector of economy of the other contry with Sanctions (prohibiting dealing with the country's relevant economic sector - finance/resources/idustry/technology - one of 4): -3 (actively helping evade) to +3 (maximum sanctions)
- Impact weighted by economy size and the size of coalition supporting sanctions and teh ssize of those helping to avade sanctions
- Cost-to-sanctioner modeled (sanctions hurt the imposer too)
- Secondary sanctions risk for evaders (possible to discover via intelligence)
- Frozen assets mechanic (some assets of Nordostan are held in EU and US)
- **Cost-to-sanctioner:** Sanctions cost the imposer proportionally to bilateral trade exposure with the target. Approximately 30-50% of the GDP damage inflicted on the target rebounds to the imposer as lost trade, supply chain disruption, and price inflation. Sanctions are a sacrifice, not a free weapon.
- **Coalition threshold:** Below approximately 60% of the target's trade-GDP coverage enforcing sanctions, effectiveness drops by approximately 70% due to rerouting through non-sanctioning countries. Sanctions without a broad coalition are performative, not punitive.
- **Financial sanctions (SWIFT/reserves freeze):** Dramatically more powerful than trade sanctions — can cripple a target's economy within 1 round. But carry a "dollar weaponization" cost: each use accelerates de-dollarization pressure among targets and observers.


### Oil / Resource Pricing

A sub-mechanic for resource-producing countries (Solaria, Nordostan, Persia, others in OPEC+).

Each producer sets production level: low / normal / high. AI calculates resulting global price based on total supply vs. demand. High prices benefit producers, hurt importers (Cathay, Teutonia, Bharata — potential stability impact). Classic prisoner's dilemma: cooperate (restrict production, price high) or defect (overproduce, grab market share, crash price). Solaria and Nordostan are in OPEC+ together but are geopolitical adversaries — can they cooperate on oil while competing on everything else?

Iran also has an option to block Ormuz straight by it s military units - and keep the blockade, reducing oil available in markets. Impact on prices of resources, negative for resource consuming nations and negative n volume for local producers in the middl east, while positive for other producers (Russia, Venezuela)

### International Assistance and Loans

Countries can give or lend coins. Gifts are transfers. Loans have negotiated terms (interest, repayment schedule, conditions). But executed fully as simple transactions (bookkeeping and claiming money back is the responsibility tof participants). Default damages creditworthiness. Conditional assistance ("20 coins if you vote with us") creates the dependency/sovereignty dilemma central to swing-state gameplay.

### Economic Indicators (calculated by World Model Engine — see E1.2)

- **GDP and GDP growth %** — deterministic formula with bounded AI adjustment (±5%). Inputs: base growth, tariffs, sanctions, war damage, blockades, tech productivity, inflation. Transparent breakdown shown to participants with "market conditions" wrapping AI adjustment.
- **Inflation rate** — cumulative from money printing + import cost inflation + supply disruptions. Natural slow decay if printing stops.
- **Oil price** — from OPEC+ production decisions + supply disruption + demand.
- **Financial market indexes** (3: Columbia, Cathay, Europe) — AI-derived from GDP, trade, conflict, confidence. When an index drops below a crisis threshold, it triggers capital flight costing 5-10% of GDP growth for one round. Non-linear — markets tolerate gradual decline but panic at sharp drops.
- **Trade balance** per country — from tariffs, sanctions, blockades, sector structure.
- **Revenue** for next round — derived from GDP, tax rate, trade, oil, minus sanctions/inflation.

All updated each round as part of World Model Engine Step 2 output.

### Connections to Other Domains

→ **Military:** Budget competes. Arms cost coins. War destroys capacity. Blockades disrupt trade. Investment can expand military production capacity. 
→ **Domestic Politics:** Economic hardship lowers stability. Inflation lowers stability. Sanctions pain creates political pressure. Social spending is a direct stability lever.
→ **Technology:** AI breakthrough can provide GDP growth multiplier. Tech sanctions restrict economic growth. Semiconductor disruption (Tawan blocade) crashes tech-dependent economies.

---

## Domain 3 — Domestic Politics

### What It Represents

The constraint that makes the Trap work. Every foreign policy decision has a domestic cost or benefit. Leaders can't just "do the rational thing" — they face populations, elites, oppositions, and elections that punish concession and reward toughness. This domain is what makes the SIM a leadership experience, not just a strategy game.

### Two Dimensions

**Stability Index (1-10)** — the health of society. Are people fed, employed, safe? Are institutions functioning? This is the SIM4 social score's successor. It's inertial: sustained pressure to push down, sustained investment to recover.

| Range | Condition | Consequences |
|-------|-----------|-------------|
| 8-10 | Stable | Leader has freedom of action |
| 6-7 | Strained | Cracks showing. Troop morale softens |
| 4-5 | Crisis | Protests likely. Troop morale penalty (-1 dice). Brain drain. Capital flight |
| 2-3 | Severe crisis | Protests automatic. Economy halved. Troop morale -2. Coup probability spikes. Military production stops |
| 1 | Failed state | Government loses control. Military may fracture |

**Political Support (0-100%)** — how secure is the current leader. Behaves differently by regime type. Columbia-specific: additionally tracks Democrat/Republican popular opinion split (e.g., 48/52) that shifts based on economic conditions, war outcomes, and presidential performance — feeds directly into election AI voting component.

| | Autocracies | Democracies |
|--|-------------|-------------|
| What it measures | Elite loyalty (security services, military, inner circle) | Public approval (polling) |
| Main threat | Coup (sudden, violent) | Election defeat (scheduled, legitimate) |
| Drops from | Military defeat, perceived weakness, economic failure | Same, plus scandals, broken promises |
| Boostable by | Repression (short-term), nationalism, victory | Economic growth, diplomatic success, popular policy |
| Special vulnerability | Succession uncertainty, warlord independence | Mid-term elections, media scrutiny |

### The Four Quadrants

High stability + High support = **Freedom** (leader can take risks).
High stability + Low support = **Vulnerability** (society is fine, leader is in trouble — drives aggressive foreign policy to boost support).
Low stability + High support = **Fragile grip** (rally-around-flag holding things together — peace may actually destabilize, creating perverse incentive to continue conflict).
Low stability + Low support = **Collapse zone** (coup, revolution, or electoral wipeout imminent — desperate leaders take extreme risks).

### What Moves the Dimensions

**Stability factors** (AI-calculated each round): social budget vs. baseline, military casualties, territory lost/gained, sanctions impact on economy, inflation, mobilization, war fatigue (cumulative), peace/ceasefire recovery, enemy sabotage, refugee flows, GDP growth/decline.

**Political support factors** (AI-calculated, differs by regime type): stability trend, military victories/defeats, "sacred war" / nationalist rally (temporary boost, diminishing returns, fades after 1-2 rounds), successful diplomacy, concessions (dangerous in autocracies, ambiguous in democracies), repression (autocracies: short-term stabilizer, long-term erosion), propaganda (effective in autocracies, partial in democracies), corruption exposure, approaching elections (amplifies everything in democracies).

### Leader Personal Dimension

Three mechanics add a personal layer to leadership decisions:

**Legacy objectives (private):** Key leaders receive private victory conditions that may conflict with national interest. Helmsman must resolve Formosa. Pathfinder must secure territorial gain or great-power recognition. Dealer must win re-election. These are PRIVATE — not visible to teammates or opponents.

**Succession anxiety (autocracies):** When an autocratic leader's political support drops below 30%, a succession clock starts. Each consecutive round below threshold increases internal pressure mechanically (subordinates receive independent information, back-channels activate, emergency convening powers unlock). At 3 consecutive rounds, a forced leadership challenge triggers.

**Health events:** Leaders aged 70+ (Helmsman 73, Pathfinder 73, Dealer 80) face a 5-10% chance per round of temporary incapacitation lasting 1 round. Cathay: Abacus acts (orderly, opaque). Nordostan: power vacuum (chaotic). Columbia: Volt acts (constitutional, transparent).

### Elections Mechanic

**Columbia mid-terms (Round 2):** One parliamentary seat contested. All team members vote + AI popular vote (50% weight based on economic conditions, presidential approval, Dem/Rep split). Result: majority holds or flips. Hostile Congress = Tribune gains budget veto and investigation powers.

**Columbia presidential (Round 5):** Nominations in Round 4 (candidates declare, brief speeches). General election: campaign speeches + debate. Team votes (Fixer/Pioneer = 2 votes each, others = 1) + AI popular vote (50%). Winner gains all executive powers. Former president stays as opposition.

**Heartland wartime (Round 3-4):** Three candidates (Beacon, Bulwark, Broker). AI judges based on territory held, economy, casualties, Western support, campaign quality. Winner becomes president.

**Other democracies:** Triggered by stability crises (government falls below threshold). AI generates outcomes for single-role countries.

### Coups and Revolutions

**Coup (multi-step, real-time via Live Action Engine):**
1. Any team member submits "coup attempt" to system
2. X-minute window opens (invisible to others)
3. Other team members must INDEPENDENTLY submit — no system signalling
4. Threshold: >30% of team (Columbia 3+, Cathay 2+, Nordostan 2+, Persia 2+)
5. If threshold not met → fails, initiators exposed globally
6. If met → AI assesses probability (stability, leader support, military control, conspirator count, regime type)
7. Universal resolution mechanic: probability displayed → fortune wheel → result
8. Success: new leadership. Failure: conspirators exposed, arrests likely.

Intelligence operations can uncover coup preparations — probabilistic, no guarantee.

**Mass protests:** Probable below stability 5, automatic below 3. Leader responds with concessions (coins), repression (military units domestically), or nationalist rally (propaganda). In Persia: protests empower Dawn (reformist).

**Revolution:** When stability 1-2 AND political support below 20%. Leader deposed. New leadership. All treaties up for renegotiation.

### Participant Actions

| Action | Effect | Cost / Risk |
|--------|--------|-------------|
| Increase social spending | Stability up (slowly) | Coins — competes with military and tech |
| Propaganda / nationalist rally | Support up temporarily, possible stability boost. "Sacred war" = major short-term rally | Coins. Fades after 1-2 rounds. Diminishing returns with overuse |
| Repression (autocracies) | Suppresses protests, stability floor | Requires security units. International condemnation. Long-term support erosion |
| Call elections (democracies) | Resets mandate if won | Risk of losing. Consumes attention |
| Purge / arrest opponents (autocracies) | Removes conspirators | May arrest wrong person. Signals insecurity |
| Fire subordinate | Removes obstacle | Fired player becomes opposition with a grievance |
| Public speech / address nation | Support boost if well-received | Creates public commitments that constrain future action |
| AI-enhanced propaganda (when AI reaches certain level)| Substantially more effective manipulation of social media, information space | Target country's stability/support harder to maintain. Hidden costs: international exposure risk, ethical threshold crossing, potential blowback |

### Connections to Other Domains

→ **Military:** Low stability = troop morale penalty. Casualties lower stability. Mobilization lowers stability. Victories boost support temporarily.
→ **Economy:** Economic hardship lowers stability. Social spending is a direct stability lever. Inflation erodes stability. Budget tradeoff: guns vs. butter.
→ **Technology:** AI-enhanced propaganda amplifies information warfare. Tech leadership boosts national pride (support). Tech sanctions that visibly damage economy lower stability.

---

## Domain 4 — Technology

### What It Represents

A capability race, not a resource to manage each round. A few countries invest heavily, most countries choose whose tech ecosystem to join, and breakthroughs create sudden shifts that reshape all other domains. Technology is the new axis of great-power competition — distinct from military confrontation but deeply connected to it.

### Two Tech Tracks

**Nuclear (Level 1-3)** — preserved from SIM4.

The existential dimension. Deterrence, escalation, proliferation.

| Level | Capability | Starting countries |
|-------|-----------|-------------------|
| 1 | Basic weapons. Can test. Tactical capability | Choson, Bharata, Levantia |
| 2 | Reliable arsenal. Tactical and limited strategic capability | Cathay, Albion, Gallia |
| 3 | Full strategic arsenal. Global strike capability. MAD-capable | Columbia, Nordostan |

Actions: Nuclear test (L1+ countries, probabilistic success). Strategic missile launch with nuclear warhead (warhead type unknown to target — see Military domain). Technology transfer. Proliferation is a diplomatic currency.

**Advancement:** Pre-set in scenario. Reaching a new nuclear level is VERY DIFFICULT during the SIM's 3-4 year timeframe. Example starting positions: Cathay at 80% toward next level (achievable Round 3-4 with sustained R&D). Persia at 60% toward L1 (possible but uncertain). Most countries: no advancement possible. R&D investment accelerates progress; sabotage/export restrictions can set back.

**AI / Semiconductors (Level 0-4)** — new for this SIM.

The competitive advantage dimension.

| Level | Capability | Starting countries | Effects |
|-------|-----------|-------------------|---------|
| 0 | None | Choson, Caribe | No domestic tech. Fully dependent on imports |
| 1 | Basic | Most countries | Commercial AI. Basic cyber (defensive). Basic drones. Can operate purchased advanced systems. Small economic productivity boost |
| 2 | Advanced | Cathay, Teutonia, Albion, Bharata, Levantia, Hanguk | Domestic AI industry. Effective cyber offense. Can produce some advanced military systems. Meaningful economic boost (+5% GDP). Can impose tech export controls. Semiconductor consumer — dependent on external fabrication |
| 3 | Frontier | Columbia, Yamato | Cutting-edge AI. Full military applications (autonomous weapons, AI-enhanced intelligence). Major economic boost (+15% GDP). Semiconductor producer/designer. Can impose export controls that bite. AI-enhanced propaganda substantially more effective |
| 4 | Breakthrough | Nobody at start | AGI-adjacent. Transformative military advantage (+2 dice modifier). Economic dominance (+30% GDP). Near-total information advantage. Achieved only through sustained investment + breakthrough roll |


### The Semiconductor Chokepoint (Formosa)

Formosa fabricates the majority of advanced semiconductors. This is a hard dependency.

**While Formosa operates normally:** All Level 2+ countries maintain their effective capability.

**If Formosa is blockaded or invaded:** All countries dependent on Formosa imports effectively drop 1 tech level for military and economic purposes. Stockpiles deplete in 1-2 rounds, making the drop permanent until Formosa resumes or alternative fabrication is built (massive investment, 3-4 rounds minimum).

This makes the Taiwan question a technology and economic crisis, not just a military one. A Chinese blockade of Formosa would crash the global tech stack.

### Participant Decisions

**R&D investment (budget line item):**
Allocate coins to tech R&D each round (split: nuclear R&D + AI/semiconductor R&D). Investment accelerates progress toward pre-set breakthrough thresholds. Advancement is VERY DIFFICULT — specific countries are pre-set in scenario config as "close to breakthrough" (e.g., Cathay 70% toward next AI level, Columbia 85%). Most countries cannot advance during the SIM. R&D investment is necessary but not sufficient — export restrictions, Formosa disruption, and sabotage can set progress back. Personal tech investments by participants (Pioneer, Circuit) can supplement government R&D.

**Tech export controls:**
Any country with advanced level of AI technology can restrict technology exports to any target. Slows target's advancement, costs imposer trade revenue. AI calculates impact and rerouting. Columbia pressuring Formosa and Yamato to cut chip sales to Cathay = the real-world dynamic modeled directly.

**Counter-restrictions (TBC):**
Cathay controls rare earth minerals essential for all tech manufacturing. Can restrict exports to Columbia and allies. Mutual vulnerability creates the possibility of negotiated restraint. (TBC)

**Technology transfer:**
Sell or share tech for coins or political concessions. Legitimate transfers (Columbia sells military AI to allies) are routine. Controversial transfers (Cathay shares drone tech with Nordostan) trigger diplomatic consequences. Proliferation risk parallels nuclear. Technlogy becomes effective next quarter. 

**AI-enhanced propaganda (Level 2+):**
Countries with AI capability can target other countries' domestic politics — amplifying disinformation, manipulating social media, undermining trust in institutions. Substantially more effective than traditional propaganda. Lowers target's stability index and/or political support. Risk: attribution and international backlash. Hidden cost: normalizes information warfare, may invite retaliation against own society.

### AI Engine Role

Track cumulative R&D investment per country. Calculate tech restriction impacts (target slowdown, imposer revenue loss, rerouting). Resolve breakthrough attempts (probabilistic, based on investment + talent base + input access). Generate tech events ("semiconductor shortage," "cyber attack attributed to X"). Apply cascading effects: GDP multiplier, military combat modifiers, intelligence visibility, cyber capability access. Monitor Formosa supply chain status.

### Connections to Other Domains

→ **Military:** Nuclear - most powerful weapon. AI level 4 - can enhance military capabilities of all units.
→ **Economy:** AI level 4 can be GDP productivity multiplier. Tech sanctions restrict growth. Semiconductor disruption crashes dependent economies. R&D investment competes for coins.
→ **Domestic Politics:** AI-enhanced propaganda targets adversary's stability and support. Tech leadership boosts national pride. Tech failure or dependence creates anxiety. Formosa crisis would trigger economic shock → stability impact globally.

---

## Domain Interconnections Summary

The domains form a feedback system where every action cascades:

**Military action → Economic cost → Domestic pressure → Political constraint on future military action.** A war costs coins, damages economies, lowers stability, which constrains the leader's ability to continue the war. The vicious cycle participants must manage.

**Economic warfare → Domestic pain (both sides) → Political pressure to escalate OR de-escalate.** Sanctions hurt the target but also the imposer. Tariffs raise costs at home. The economic war generates domestic pressure that either forces compromise or drives escalation.

**Technology advantage → Economic growth → Military superiority → Greater political freedom of action.** The tech leader gets richer, stronger, and more domestically secure — widening the gap. This is what creates the "now or never" urgency for the lagging power: act before the gap becomes insurmountable.

**Domestic crisis → Desperate foreign policy → Escalation → Wider crisis.** A leader facing collapse at home may provoke an external crisis to rally support (wag the dog). Or may make concessions that adversaries exploit. Internal instability in one country becomes a global risk.

**The Thucydides Trap emerges from all four domains interacting simultaneously.** No single domain produces the Trap. It's the combination: military posturing + economic interdependence + domestic political constraints + technology race = a system where rational actors pursuing their own interests collectively generate outcomes none of them intended.

---

## Open Questions for Detailed Design

Most questions from v1.1 are now addressed in E1 Engine Architecture v0.7. Remaining:

1. Exact starting values per country (MU counts, coins, income, tech levels) — deferred to scenario configuration (D1-D5)
2. Combat resolution modifier values by theater type — to be calibrated in playtesting
3. Stability Index factor weights — to be calibrated (SIM4 social score values as starting point, AI adjustment for qualitative factors)
4. Covert operations probability calibration — to be tested

---

## Changelog

- **v2.0 (2026-03-21):** Aligned with E1 Engine Architecture v0.7. Military: 5 unit types (added strategic missiles with unified nuclear warhead unknown to target, air defense as deployable unit). Budget: production tiers (1×/4×/9×), capacity investment removed, country-specific maintenance costs. Economy: GDP formula reference, financial indexes, revenue formula. Politics: simplified to Stability + Political Support only, Columbia Dem/Rep split added. Tech: pre-set advancement model. Elections: detailed mechanics from E1. Coup: multi-step mechanic. Most open questions resolved by E1 specs.
- **v1.1 (2026-03-20):** Added information asymmetry principle.
- **v1.0 (2026-03-19):** Initial four-domain architecture.
