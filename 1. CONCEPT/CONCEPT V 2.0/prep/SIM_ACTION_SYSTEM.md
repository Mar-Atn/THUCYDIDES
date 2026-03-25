# Thucydides Trap SIM — Action System
**Version:** 1.0 | **Date:** 2026-03-19 | **Status:** Conceptual

---

## Design Principle

In SIM4, actions were physical cards brought to SIM officers. In this SIM, actions are **role-specific features in the web app**. Each player sees only the actions available to their role. Authorization chains are enforced digitally — a nuclear strike requires two confirmations in the app before executing. The permission structure IS the decision rights architecture made interactive.

**Every action on this list passes three tests:**
1. Creates a distinct dilemma no other action covers
2. Will actually be used during 6-8 rounds
3. Cannot be folded into another action without losing something

### Three categories

**Routine** — submitted each round as part of the budget cycle. Default = status quo if not submitted.

**Anytime** — triggered whenever a player decides, during the negotiation phase. Creates unpredictable drama.

**Escalatory** — high-consequence, often irreversible. Requires multi-role authorization. Triggers AI world model cascades, possible theater activation, global reactions.

### Authorization mechanic

Some actions require a second (or third) role to confirm before executing. The initiator submits via the app; the confirmer receives a real-time notification with a countdown. If denied or timed out, the action fails. This creates genuine drama — the confirmer may be in another meeting, may need to consult, may face an agonizing decision with a ticking clock.

---

## Military Actions (9)

### Deploy / redeploy units — Routine
**Who:** Defense Minister / Military Chief initiates. Head of State authorizes.
**What:** Move military units between theaters on the global map.
**Consequences:** Arrival takes 1 round (the transit delay is the core "overstretched hegemon" mechanic). Movement is visible to all — redeployment signals intent. Minimum homeland garrison required.

### Set military production level — Routine
**Who:** Defense Minister, within the budget approved by PM / Congress.
**What:** Normal / accelerated / maximum. Determines how many new units are produced next round.
**Consequences:** Higher levels cost more coins. Maximum production hits social score (society feels the strain). Production is capped by capacity — you can't produce more than your factories allow regardless of budget.

### Arms transfer — Anytime
**Who:** Head of State initiates. Defense Minister confirms (units leave their forces).
**What:** Sell or gift military units to another country.
**Consequences:** Transfer is automatically public (intelligence satellites detect major movements). Seller is depleted. Buyer absorbs at reduced effectiveness for 1 round. May violate sanctions. Creates dependency — advanced systems need ongoing maintenance from the manufacturer. One of the SIM's most consequential bilateral actions (Patriot-to-Heartland equivalent).

### Mobilization — Anytime (escalatory)
**Who:** Head of State. Unilateral.
**What:** Three levels: partial / general / total. Drafts citizens into military service.
**Consequences:** New units available next round from population. Social score hit proportional to level (partial: -0.5, general: -1, total: -2). Only available to countries at war or facing declared imminent threat. Can be combined with production for rapid buildup — but the social cost is severe.

### Attack — Escalatory
**Who:** Head of State orders. Military Chief executes. Both must confirm in the app.
**What:** Conventional military attack — ground assault, naval engagement, or air campaign. Scale is determined by the number of units committed.
**Consequences:** Activates theater zoom-in map if not already active. Combat resolution: dice-based with AI-calculated modifiers (unit count, tech level, morale from social score, theater advantages). Results: casualties on both sides, possible territory changes, cascade to economy and social score. A large-scale attack with concentrated forces IS an invasion — no separate "invasion" action needed; scale determines what it is.

### Naval blockade — Escalatory
**Who:** Head of State orders. Military Chief executes. Requires naval units deployed in the relevant theater.
**What:** Block maritime trade through a chokepoint or around a territory.
**Consequences:** Distinct from attack — it's economic warfare through military means. Trade flows disrupted. Economic consequences calculated by AI (importers/exporters affected, rerouting, price impacts). Can be challenged militarily by the target or its allies. The Formosa blockade scenario requires this as separate from invasion — you can blockade without invading.

### Missile / drone strike — Escalatory
**Who:** Head of State orders. Military Chief executes.
**What:** Long-range precision strike against specific targets (military bases, infrastructure, nuclear facilities, leadership compounds). Does NOT require units deployed in the target theater.
**Consequences:** Requires air/missile capability (most countries at Level 1+ tech). Damage is targeted, not territorial. Can trigger theater activation. Highly escalatory but lower commitment than a ground attack. The Israel-strikes-Iran's-nuclear-facilities scenario lives here.

### Nuclear test — Escalatory
**Who:** Head of State initiates. Military Chief confirms.
**What:** Detonate a nuclear device at a test site. No physical damage to others.
**Consequences:** Signals nuclear capability. Global social score impact (-0.3 to -0.6 across all countries). Diplomatic crisis. UNSC emergency session likely triggered. NPT violation for non-nuclear states (triggers framework consequences). For Persia at Level 0, a successful test = advancement to Level 1 — a world-changing event.

### Nuclear strike — Escalatory (two levels)
**Who:** Head of State initiates with 10-minute visible preparation (detected by intelligence services of all nuclear powers). Defense Minister / Military Chief must BOTH confirm within 2 minutes of launch order. If either denies, the strike is aborted.
**What:**
- **L1 Tactical:** Strike against troops, military installations, or empty terrain. Demonstrates willingness to use nuclear weapons. Forces enemy to recalculate.
- **L2 Strategic:** Strike against cities, economic infrastructure, population centers. Civilization-level consequences.

**Consequences (L1):** 50% of troops in target zone destroyed. Economy -2 coins for target. Social score shock globally. Response window: other nuclear powers have 5 minutes to decide whether to retaliate.

**Consequences (L2):** 30% of target's economic capacity destroyed. 50% of military in target zone destroyed. Each leader physically present in target country: 1/6 death probability (dice). Near-certain retaliation. Potential civilization-ending escalation spiral.

---

## Economic Actions (7)

### Submit national budget — Routine
**Who:** PM / Finance Minister submits. Head of State can override. Congress (Columbia) can modify or block.
**What:** Allocates coins across budget lines each round: military maintenance (auto-deducted), military production, social spending (above or below baseline), tech R&D investment, capacity investment (expand production), international transfers. If not submitted by deadline, defaults apply (last round's allocation continues, auto-maintenance deducted).
**Consequences:** The budget IS the country's strategic priorities made concrete. Every coin spent on military production is a coin not spent on social stability. The budget fight between PM and Head of State (or President and Congress) is the core internal politics mechanic for most countries.

### Set tariff levels — Routine or Anytime
**Who:** Head of State or PM. Unilateral.
**What:** Set tariff rate (0-3) against any other country, per economic sector. Level 0 = free trade. Level 3 = near-prohibitive.
**Consequences:** AI calculates: tariff revenue for imposer, increased import costs (inflationary), GDP impact on both sides, third-country rerouting (neutral countries benefit from redirected trade). Can be announced dramatically mid-round for political effect. Retaliation spiral likely — target can counter-tariff.

### Set sanctions position — Routine
**Who:** Head of State.
**What:** Position scale -3 (actively helping evade) to +3 (maximum sanctions) per sanctions type per target country. Types: financial, resource exports, industrial imports, technology.
**Consequences:** AI calculates weighted impact based on economy size (SIM4 formula, expanded). Sanctions bite the target but also cost the imposer. Designed to pressure neutrals as much as punish targets — visible to all, creates pressure on swing states. EU sanctions are a meeting outcome where members align their individual positions.

### Asset seizure — Escalatory (Anytime)
**Who:** Head of State of the country holding the assets.
**What:** Freeze or seize foreign government/individual assets held in your financial system.
**Consequences:** Sovereign decision but deeply consequential. Damages global financial system credibility ("if they can seize our reserves, nowhere is safe"). Irreversible — once seized, the relationship is fundamentally altered. Generates coins for the seizer but at enormous diplomatic cost. The "$300 billion frozen Russian reserves" question.

### Print money — Anytime
**Who:** PM initiates. Head of State confirms.
**What:** Create coins from nothing. Specified amount.
**Consequences:** Coins appear immediately. AI tracks cumulative money printing — generates inflation that compounds each round. Inflation lowers stability (population feels the pinch). Tempting as a short-term fix, toxic long-term. Currency crisis possible if overdone.

### Transfer coins — Anytime (spot transaction)
**Who:** Any actor with coins (state treasury or personal wealth).
**What:** Transfer any number of coins to any other actor. State-to-state, state-to-individual, individual-to-individual.
**Consequences:** Immediate and irreversible. Covers: foreign aid, arms payments, bribes, loans (write terms in a treaty), humanitarian assistance, personal deals. Can be public (announced) or private (but intelligence may detect large transfers). The universal economic transaction.

### Set OPEC+ production level — Routine (oil producers only)
**Who:** Head of State / PM of oil-producing countries (Solaria, Nordostan, Persia, Mirage).
**What:** Low / normal / high production.
**Consequences:** AI calculates global oil price from all producers' decisions combined. Classic prisoner's dilemma: cooperate (restrict, price high) or defect (overproduce, grab market share). High prices benefit producers, hurt importers (Cathay, Teutonia, Bharata — social score impact). Coordination is voluntary — no enforcement.

---

## Technology Actions (2)

### Export restrictions — Anytime
**Who:** Head of State (Tech Level 2+ countries, or countries controlling critical resources).
**What:** Restrict exports of strategic goods to a specific target country. Covers: semiconductors, chip manufacturing equipment, rare earths, advanced materials, AI components, energy technology.
**Consequences:** Slows target's tech advancement. Costs imposer trade revenue (AI calculates). Target may develop alternatives over time (expensive, slow). Mutual vulnerability: Cathay restricts rare earths, Columbia restricts chips — both suffer. Creates leverage for negotiated restraint. One action with flexible targeting — the commodity and target are parameters.

### Technology transfer — Anytime (spot transaction)
**Who:** Head of State of the providing country. Recipient agrees.
**What:** Share technology capability — nuclear technology (advances recipient's nuclear level) or AI/semiconductor technology (advances recipient's tech level). For coins, political concessions, or alliance commitments.
**Consequences:** Recipient advances one level in the transferred domain. Massive diplomatic consequences — proliferation concerns, alliance reactions. The "Nordostan shares nuclear tech with Persia" or "Columbia shares AI capability with Yamato" scenarios. Legitimate transfers are routine; controversial transfers trigger crises.

---

## Domestic / Political Actions (6)

### Arrest — Anytime (autocracies primarily, but any country can detain foreign nationals)
**Who:** Head of State or Security Chief. Unilateral on own soil.
**What:** Detain any person physically present in your country — own officials, foreign diplomats, visiting leaders, oligarchs, press.
**Consequences:** Target player is restricted (can't attend meetings, can't execute their role functions) until released. If own official: removes them from power but they stay in the game with a grievance. If foreign national: international crisis, possible hostage negotiation. The defining power of autocratic regimes — and the most dramatic physical action in the SIM. Proven SIM4 highlight.

### Fire / reassign — Anytime
**Who:** Head of State. Unilateral.
**What:** Remove any subordinate from their role. They lose all official powers associated with that role.
**Consequences:** The fired player REMAINS in the game — with knowledge, connections, and a grudge. They become opposition, potential coup conspirator, or defector. Politically costly: demonstrates instability, may lose a competent operator, creates an enemy. A vacant role can be filled by appointing someone else (including a player who currently holds a different role). In Columbia, the president can fire anyone; Congress cannot block it.

### Propaganda campaign — Anytime
**Who:** Head of State or designated official. Costs coins.
**What:** Standard propaganda: spend coins, boost political support temporarily. "Sacred war" declaration: major one-time boost to both stability and support, but commits the country to a conflict narrative (making peace harder later).
**Consequences:** Standard propaganda: +5-10% political support, fades after 1-2 rounds, diminishing returns with repeated use. Sacred war: +15-20% support, +1 stability, but the narrative locks you in — backing down after declaring sacred war is politically catastrophic. Coins spent are gone regardless.

### Assassination — Anytime (escalatory)
**Who:** Head of State or Intelligence Chief initiates. Requires deliberate decision in the app.
**What:** Order the killing of a specific target. Two variants:
- **Domestic:** Targeting a political rival, opposition figure, or inconvenient person within your own country. The Navalny scenario. Available to autocracies.
- **International:** Targeting a foreign actor — a leader, military commander, intelligence chief, or other significant figure in another country. The Soleimani scenario.

**Consequences:** Probabilistic outcome — dice/AI determines success AND detection.

Success probability: base 50%, modified by target's security level (heads of state are harder to kill), intelligence capability, and whether target is on own soil or abroad.

Detection probability: high (60-80%). Even "successful" operations are often attributed. If detected:
- *Domestic assassination:* Social score penalty. International condemnation. Personal sanctions risk. Opposition may rally rather than collapse — the martyr effect. But the immediate political threat is eliminated.
- *International assassination:* Extreme diplomatic consequences. Possible military retaliation. UNSC emergency session. Freezing of all bilateral relationships. May trigger counter-assassination attempts.

If the target is a human player: survival determined by dice (1/6 death probability if security is high, 1/3 if moderate, 1/2 if low). If the player "dies," they are removed from their current role — but the moderator can assign them a successor role (a new leader emerges, an opposition figure rises, etc.). No human player sits out permanently.

**Cost:** Coins (intelligence operation costs). Possible political support hit even if undetected (rumor and suspicion circulate). The decision to order a killing is tracked by the system — it becomes part of the participant's behavioral data.

**Why this exists as a distinct action:** Ordering someone's death is qualitatively different from any other decision in the SIM. It crosses a moral threshold that sanctions, tariffs, and even conventional military action don't. Participants who choose it should feel the weight. It should never be casual. The app should present it with appropriate gravity — not buried in a sub-menu, but not the first thing you see either. A deliberate choice that says something about the leader making it.

### Coup attempt — Escalatory
**Who:** Any internal actor with military or security access. Requires at least one co-conspirator (another internal role who agrees to support).
**What:** Attempt to overthrow the head of state.
**Consequences:** Probability = function of: stability index, political support, number of co-conspirators, military units under plotters' control, random element (dice). The President retains all powers UNTIL the coup is acknowledged by the moderator — meaning they can arrest anyone they suspect before the outcome is determined. If successful: plotters take power, all treaties and policies are renegotiable. If failed: conspirators face arrest, exile, or execution. The Oligarch can fund a coup without directly participating (coins lower the threshold). Proven SIM4 highlight — the latent threat of a coup shapes all autocratic behavior.

### Call elections — Anytime (democracies)
**Who:** Head of State (voluntary) or Parliament/Congress (forced, when political support drops below threshold).
**What:** Trigger a presidential or parliamentary election.
**Consequences:** In Columbia: political support score determines whether the incumbent survives. Below 40% = likely loss. 40-60% = contested (dice element). Above 60% = comfortable win. If lost, a new president takes over (possibly the VP, possibly an opposition figure). In Heartland: three human candidates compete, AI judges based on gameplay outcomes (territory, economy, casualties, support). In other democracies: AI generates election outcome based on conditions. Elections reset the mandate — a fresh start or a devastating rejection.

---

## Covert Operations (1 action, sub-menu)

### Covert operations — Anytime
**Who:** Intelligence Chief or Head of State. Tech Level 1+ required for basic operations; Level 2+ for advanced; Level 3+ for precision.
**What:** A single action with multiple target types:
- **Espionage:** Steal information about another country's military deployments, economic data, diplomatic negotiations, or nuclear program. AI determines what is discovered.
- **Sabotage:** Damage infrastructure, military equipment, supply chains, or specific facilities (e.g., nuclear centrifuges — the Stuxnet scenario). Physical damage without military attribution.
- **Cyber attack:** Disrupt digital infrastructure, financial systems, military communications, or elections. Requires Tech Level 2+. Deniable but increasingly attributable. Can target another country's stability or political support.
- **Disinformation campaign:** Target another country's domestic politics through AI-enhanced information warfare. Requires Tech Level 2+. Degrades target's stability and/or political support. More effective than conventional propaganda. Risk: attribution, retaliation, blowback.

**Consequences:** All covert operations are probabilistic. AI determines: success/failure, detection/attribution, collateral effects. If detected: diplomatic crisis proportional to the operation's severity. If undetected: effects apply silently. Repeated operations against the same target increase detection probability (the target's intelligence adapts).

---

## Diplomatic Actions (3)

### Public speech — Anytime or Scheduled
**Who:** Any head of state or designated speaker. 2-3 minutes.
**What:** Address the room — all participants hear. Can be a policy declaration, a threat, a peace offer, a campaign speech, a eulogy, an accusation. The press is always present.
**Consequences:** Creates public commitments that constrain future action ("I will never abandon Heartland" — now the press holds you to it). Affects political support: a well-received speech boosts support; a badly received one damages it. Campaign speeches before elections directly affect the outcome. One of the SIM's highest-engagement mechanics — the room goes silent when a leader speaks.

### Sign treaty / agreement — Anytime (spot transaction)
**Who:** Any two (or more) heads of state or authorized representatives.
**What:** A written agreement between parties. Content is freely negotiated — can cover anything: peace terms, alliance commitments, basing rights, arms deals, loan terms, trade arrangements, non-aggression pacts, technology sharing, sanctions coordination, secret protocols.
**Consequences:** Immediate and binding between signatories. Breach has reputational consequences (loss of credibility, reduced trust in future negotiations) but no automatic mechanical penalty — there is no court that enforces treaties. Agreements can be public (announced to all) or secret (known only to signatories — but intelligence may discover them, and the press may publish them). The universal bilateral action.

### Call UNSC emergency session — Anytime
**Who:** Any P5 member (Columbia, Cathay, Nordostan, Gallia, Albion).
**What:** Convene the UN Security Council to address a crisis.
**Consequences:** All P5 members must attend (brief interruption of whatever they're doing — the UNSC summons are mandatory). Resolutions can be proposed and voted. Any P5 member vetoes. The act of calling a session IS a political move — it signals crisis, forces public confrontation, and puts every P5 member on record. Even a vetoed resolution reveals who stands where.

---

## Summary: 28 Actions

| Category | Actions | Count |
|----------|---------|:-----:|
| Military | Deploy · Production level · Arms transfer · Mobilization · Attack · Naval blockade · Missile/drone strike · Nuclear test · Nuclear strike (L1/L2) | 9 |
| Economic | Budget · Tariffs · Sanctions · Asset seizure · Print money · Transfer coins · OPEC+ production | 7 |
| Technology | Export restrictions · Technology transfer | 2 |
| Domestic | Arrest · Fire/reassign · Propaganda · Assassination · Coup attempt · Call elections | 6 |
| Covert | Covert operations (espionage / sabotage / cyber / disinformation) | 1 |
| Diplomatic | Public speech · Sign treaty · Call UNSC session | 3 |
| **Total** | | **28** |

### What a typical round looks like by action count

**A country at peace (e.g., Solaria):** 2-4 actions per round. Submit budget. Set OPEC+ production. Maybe adjust tariffs. Maybe sign a deal. Occasionally a speech.

**A country in economic warfare (e.g., Columbia vs. Cathay):** 5-8 actions. Budget. Tariffs. Sanctions. Export restrictions. Transfer coins (aid to allies). Sign treaty. Speech. Maybe a covert cyber operation.

**A country at war (e.g., Nordostan):** 8-12 actions. Budget. Production at maximum. Deploy units. Attack. Mobilization. Propaganda. Sanctions response. Diplomacy (treaty with Cathay, UNSC session). Possibly: assassination, covert ops against Heartland.

**A country in crisis (e.g., Heartland):** 6-10 actions. Budget under pressure. Arms transfers received. Election campaign. Public speeches. Military deployment. Peace negotiations (treaty). Covert ops (intelligence gathering).

---

## Changelog

- **v1.0 (2026-03-19):** Initial action system. 28 distinct actions across 6 categories. Derived from SIM4 action cards (expanded, consolidated, adapted for web app). Nuclear ladder simplified to 2 levels. Covert ops consolidated as single action with sub-menu. Assassination preserved as distinct action (domestic + international) with probabilistic outcomes and moral weight. Personal sanctions cut (absorbed by country-level sanctions). Proxies cut (better as AI world model flavor). International debt cut (no financial market mechanic). Budget absorbs social spending, tech R&D, capacity investment as line items.
