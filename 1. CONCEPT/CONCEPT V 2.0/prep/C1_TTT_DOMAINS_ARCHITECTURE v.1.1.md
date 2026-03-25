# Thucydides Trap SIM — Game Domains Architecture
**Version:** 1.1 | **Date:** 2026-03-20 | **Status:** Conceptual

---

## Overview

The SIM operates across four interconnected domains. Each domain has trackable resources, participant decisions, and AI-calculated consequences. The domains are not independent — every action in one creates ripples in the others. The elegance test: **every mechanic must create a dilemma, not just a calculation.**

Primary gameplay is free-form negotiation and diplomacy. The four domains provide the stakes, constraints, and consequences that give negotiations their weight.

### Design Principles (cross-cutting)

- **Voluntary action, status quo default.** No country is forced to change anything each round. If nothing is submitted, previous settings continue. Game pressure — not game rules — drives action.
- **Simple decisions, complex consequences.** Participants make policy choices (pick a number, check a box, sign a deal). The AI engine calculates the cascading effects across all domains.
- **Graduated complexity by role.** Great powers with multiple roles manage all domains actively. Single-role countries manage selectively. AI-operated countries are handled entirely by AI participants or the AI world model engine.
- **Decision rights are split.** In countries with multiple roles, no single person controls everything. The budget requires the PM; attacks require the president AND/OR defense minister; nuclear launch requires three confirmations. Though leaders can override, or change the subordinates. The split is itself the internal politics mechanic.
- **Spot transactions are irreversible.** Any deal confirmed by two parties executes immediately in the system. No take-backs. Commitment has weight. To revert the actors just need to execute a reverse deal voluntarily.
- **The balance of power is a question, not an answer.** The SIM's central question — has the rising power matched the hegemon? — is never answered by the system. The public dashboard shows raw data (ship counts, GDP, tech investment levels) but not conclusions. Each team's starting brief contains a different intelligence assessment of the same reality. Participants must interpret ambiguous data, seek additional information through intelligence actions and allied sharing, and act on their own judgment. Misperception — two sides acting rationally on different pictures — is the Trap's most dangerous mechanism. Giving participants certainty would break it.

---

## Domain 1 — Military

### What It Represents

The shadow behind every negotiation. Most participants will never command troops to fight, but everyone must think about force — because it's what gives diplomatic positions their credibility. The primary dynamic is deterrence, posture, and deployment — with combat as one possible outcome.

### Trackable Resources

**Four unit types:**

| Type | What it does | Who has it | Notes |
|------|-------------|-----------|-------|
| Ground forces | Territory control, land warfare, border defense | Everyone | The default. Cheap, numerous. Dominant in the European theater. |
| Naval forces | Sea control, blockades, strait access, amphibious operations | ~6-8 countries (Columbia, Cathay, Albion, Yamato, Gallia, Bharata, others) | Required for Taiwan scenario. What makes the Pacific credible. Countries without navies simply don't have these. |
| Air / Missile forces | Long-range strikes, bombing, precision attack, drones | Most countries at varying scale | Required for Iran strike scenario. Drones are the cheap entry point. |
| Air Defense | Protects territory and forces from air/missile attack | Scarce, tradeable, consequential | Possibly modeled as capability tier (none / basic / advanced) rather than unit count. Patriot-to-Ukraine type transfers are major diplomatic events. |

### Deployment and Basing

All units (apart from air/missile forces) are deployed to **theaters** visible on the global map. Redeployment between theaters takes **1 round** — this delay is the core mechanic creating the "overstretched hegemon" problem.

**Own territory:** Free deployment, no permission needed.

**Columbia's base network:** 4-5 global bases (Pacific/Yamato, Europe/Teutonia, Middle East/Gulf, Indian Ocean, possibly Mediterranean). Each requires host consent. Host can renegotiate or revoke. Bases enable instant theater access without transit delay — Columbia's unique structural advantage and diplomatic vulnerability.

**Foreign soil:** Requires explicit host agreement. Negotiated deal — may involve coins, security guarantees, political commitments. Creating a new foreign base is a major diplomatic event.

### Participant Decisions

**Each round (budget cycle):**
- Military budget level (competes with social spending and tech investment)
- Production level for each type of units (ground, naval, air/missiles): normal / accelerated / maximum (higher = more units next round, costs more)
- Unit deployment / redeployment across theaters (movement on the maps) 
- Capacity investment (expand production capacity — the militarize/demilitarize lever)

**Anytime (spot transactions and 'action cards'):**
- Arms transfers (sell or gift any type and wuantity of military units to other countries — public, depletes seller, buyer absorbs slowly) - tranfered units are avaiable for deployment and combat next round. 
- Attack / initiate combat (requires head of state + defense minister authorization)
- Naval blockade (requires naval units in theater) - reduces trade of the blokaded country (0-100% defined depending on context)
- Missile / drone strike (long-range, doesn't require units in theater, requires air/missile capability) - atacks specific area of large world map or specific area of the detailed war maps (Irsan, Ukraine, ) - can destroy military units with pribability, reduce morale in teh country, damage economy - all defined by AI engine with probabilistic outcome (roll dice element when executed)
- Covert operations (sabotage, intelligence, assassination — probabilistic outcomes, AI Engine provides response)
- Nuclear actions (preserved from SIM4 — escalation ladder L1-L3 + real nuclear test option, authorization chain, detection, response window - switch to real time to play 10-20 minutes of atack and response instead of round time ) 
- Basing rights: grant, renegotiate, or revoke (simple Y/N from the hosting country, bylateral, all NATO by default have Y to each other, need explicitely revoke it to stop deployment)
- Terrorsim sponorship available to some actors

### Balancing Mechanics (preventing buy-to-win)

Production capacity limits (factories cap output regardless of budget, growing costs of accelerated production, impact on economy). Absorption limits (foreign-purchased units arrive at reduced effectiveness for 1 round). Seller depletion (selling = losing your own units). Arms trade can be discovered easily by intelligence (intelligence satellites). Massive buildup lowers social score. Sanctions restrict arms trade. Atack less efficient then defence (as in risk), can not win military wars without ground atack. Ground atacks costly and dangerous, politically risky (losses cost domestic support), vulnerable to cheap drones and terrorism.  

### Combat Resolution

**Dice-based with AI-calculated modifiers.** When combat occurs: participants roll dice (drama, transparency, removes moderator blame). AI calculates modifiers: unit count, tech level advantage, morale (from social score), theater-specific factors (naval advantage in Pacific, ground advantage in Europe). Results: casualties, territory changes, cascading effects to economy and social score.

### Theater Activation

The global map starts with **two active theaters** (Eastern Europe and Middle East - Iran). Other theaters (Pacific/Taiwan, Korea, South Asia, Caribbean) activate **dynamically** when military action in that region escalates. Each activated theater gets a zoom-in map with simplified sectors. The number of active theaters at game end is itself a measure of outcome.

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

### Budget Cycle (each round)

Every country submits a budget. The PM / finance minister owns it; head of state can override at political cost.

**Automatic / maintenance:**
- Military unit maintenance (0.5 coins per unit, to be confirmed at resource balancing review)
- Social baseline spending (maintains current stability, can increase to make people happier, or reduce to spare money, at a social score cost)
- Both auto-deduct if no budget submitted — status quo continues

**Deliberate decisions:**
- Military production budget (new units/types, production level - standard/accelerated - at higher per unit costs)
- Social spending (above or below baseline — direct lever on stability index)
- AI R&D government investment (advancing AI level — primarily Columbia and Cathay, but available to EU and Nordostan)
- Capacity investment (expanding production capacity — long-term militarization/demilitarization - new capacity will be added next round, new units - in two rounds)
- International transfers (aid, loans, arms payments, any spot transactions)
- Money printing (create coins from nothing — generates inflation, AI engine tracks cumulative impact, inflation leads to unhappy people)

**Budget deadline is hard.** Miss it and defaults apply. This ensures participants govern their country, not just negotiate.

### The Tarrifs and Sanctions Game

**Tariffs** (unilateral, graduated, continuous):
- Any country can set tariff levels (0-3) against any other country, per economic sector
- Level 0 = free trade. Level 1 = moderate. Level 2 = heavy. Level 3 = prohibitive (near-sanction)
- Unilateral — no coalition needed. This is the weapon you use on allies too
- Retaliation spiral: target can counter-tariff, creating tit-for-tat escalation
- Third-country rerouting: goods flow around tariff walls, benefiting neutral countries
- Tariff revenue accrues to imposer but import costs rise (inflationary)
- AI engine calculates aggregate effects: revenue, costs, rerouting, GDP impact

**Sanctions** (coalition-based, dramatic, binary):
- Counries can sanction any sector of economy of the other contry with Sanctions (prohibiting dealing with the country's relevant economic sector - finance/resources/idustry/technology - one of 4): -3 (actively helping evade) to +3 (maximum sanctions)
- Impact weighted by economy size and the size of coalition supporting sanctions and teh ssize of those helping to avade sanctions
- Cost-to-sanctioner modeled (sanctions hurt the imposer too)
- Secondary sanctions risk for evaders (possible to discover via intelligence)
- Frozen assets mechanic (some assets of Nordostan are held in EU and US)


### Oil / Resource Pricing

A sub-mechanic for resource-producing countries (Solaria, Nordostan, Persia, others in OPEC+).

Each producer sets production level: low / normal / high. AI calculates resulting global price based on total supply vs. demand. High prices benefit producers, hurt importers (Cathay, Teutonia, Bharata — potential social score impact). Classic prisoner's dilemma: cooperate (restrict production, price high) or defect (overproduce, grab market share, crash price). Solaria and Nordostan are in OPEC+ together but are geopolitical adversaries — can they cooperate on oil while competing on everything else?

Iran also has an option to block Ormuz straight by it s military units - and keep the blockade, reducing oil available in markets. Impact on prices of resources, negative for resource consuming nations and negative n volume for local producers in the middl east, while positive for other producers (Russia, Venezuela)

### International Assistance and Loans

Countries can give or lend coins. Gifts are transfers. Loans have negotiated terms (interest, repayment schedule, conditions). But executed fully as simple transactions (bookkeeping and claiming money back is the responsibility tof participants). Default damages creditworthiness. Conditional assistance ("20 coins if you vote with us") creates the dependency/sovereignty dilemma central to swing-state gameplay.

### AI-Derived Indicators (participants see, don't manage)

- **GDP and GDP growth** — calculated from base capacity, sanctions impact, trade flows, war damage, investment, inflation
- **Inflation rate** — driven by money printing, supply disruptions, military spending ratio
- **Financial indexes** (3-4 major markets) — calculated from economic conditions, war risk, sanctions. Decoration/signal unless paired with personal investment mechanic from BATG

All of the above impact the social score/political support.

All reported at round start as part of the "state of the world" briefing.

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

**Political Support (0-100%)** — how secure is the current leader. Behaves differently by regime type:

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

### Elections Mechanic

**Columbia presidential cycle:** Mid-terms in round 2 (if SIM starts 2026). Presidential election in round 5 (close to the end of the simulation). Creates escalating domestic constraint — every decision judged through electoral lens. Loss of Congress restricts budget and policy authority.

**Heartland elections:** Can be triggered by parliament (decision of the 3 participant). Wartime election = dramatic moment. Current president vs. alternatives offering different war/peace visions.

**Other democracies:** Triggered by stability crises (government falls below threshold). For single-role countries, AI generates outcomes: "New government elected with more hawkish/dovish mandate."

### Coups and Revolutions

**Coup (autocracies):** Any internal actor with military/security access can attempt. Probability determined by: stability index, political support level, number of co-conspirators, military units under plotter's control, dice roll with modifiers. Before acknowledgment, president retains all powers and can arrest anyone. 

**Mass protests:** Probable below stability 5, automatic below 3. Paralyze economy, halt military production, further damage stability. Leader responds with concessions (spend coins, stability recovers slowly) or repression (uses military units domestically, stability holds temporarily, political support erodes long-term).

**Revolution:** Automatic when stability hits 1-2 AND political support below 20% (all tresholds - subject to validation after balancing tests). Leader deposed. New leadership emerges. All treaties up for renegotiation.

**AI-operated smaller countries:** AI tracks both dimensions, announces consequences at thresholds. "Protests in Amazonia — government redirecting defense budget." "Military coup in Choson — new general announces policy reversal." Human players must react to these shocks.

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
| 1 | Basic weapons. Can test. Tactical capability | Choson, Bharata, Indistan, Levantia |
| 2 | Reliable arsenal. Tactical and limited strategic capability | Cathay, Albion, Gallia |
| 3 | Full strategic arsenal. Global strike capability. MAD-capable | Columbia, Nordostan |

Actions: test, tactical strike (L1), strike on city (L2), strategic strike (L3), transfer technology to another country, sell weapon. Escalation ladder and authorization chain preserved from SIM4. Proliferation is a diplomatic currency — Nordostan's Level 3 tech is something Cathay and others want.

Countries can invest to advance nuclear level (expensive, slow, internationally provocative). Persia at Level 0 attempting to reach Level 1 is a major plotline.

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

**R&D investment (primarily Columbia and Cathay):**
Allocate coins to tech R&D each round (budget line item). Cumulative investment must reach a threshold to advance one level. From Level 3 to Level 4: investment threshold met triggers a **breakthrough roll** — probabilistic (dice or AI-determined). Success = Level 4 achieved. Failure = coins spent, try again next round. You can't buy breakthroughs, only buy lottery tickets. Advancement of AI technology from stage to stage is costly. Automatic progress (by normal private sector ), can potentially be accelerated by governemnt or extra private expenditure (from individual participants) - but costly and probabilistic outcome. Still takes time. Roll-dice element. Those at lower levels can try to still technology via intelligence operations. Efficiency of such operations attempts is low. Chances relatively low - e.g. 20%.  

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

1. Exact starting values: MU counts, coin reserves, income levels, social scores, tech levels per country
2. Production costs and rates for each unit type
3. Sanctions calculator formula or logic for AI engine (expand from SIM4)
4. Tariff impact calculation model or logic for AI model
5. Tech level investment thresholds and breakthrough probability
6. Combat resolution modifiers by theater type
7. Social score factor weights (how much does each factor move the needle?)
8. Political support calculation model (autocracy vs. democracy formulas)
9. Election mechanics detail (Columbia mid-terms, triggered elections elsewhere)
10. Available actions catalog (full list with costs, avaiability rules, probabilities, consequences)

---

## Changelog

- **v1.1 (2026-03-20):** Added cross-cutting design principle: "The balance of power is a question, not an answer" — information asymmetry as core Trap mechanic.
- **v1.0 (2026-03-19):** Initial four-domain architecture. Military (4 unit types, theater deployment, basing, combat). Economy (coins, budgets, sanctions, tariffs, oil pricing, money printing). Domestic Politics (stability index + political support, elections, coups, regime-type differences). Technology (nuclear L1-3, AI/semiconductor L0-4, Formosa chokepoint, breakthrough mechanic, cyber, AI-enhanced propaganda). Interconnections mapped. Open questions cataloged.
