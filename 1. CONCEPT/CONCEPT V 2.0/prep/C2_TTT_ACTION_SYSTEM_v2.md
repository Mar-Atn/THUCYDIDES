# Thucydides Trap SIM — Action System
**Code:** C2 | **Version:** 2.0 | **Date:** 2026-03-20 | **Status:** Conceptual

---

## Design Principle

Actions are **role-specific features in the web app**. Each player sees only the actions available to their role. Authorization chains are enforced digitally — a nuclear strike requires confirmations in the app before executing. The permission structure IS the decision rights architecture made interactive.

**Three categories:**
- **Routine** — submitted each round during budget/decision phase. Default = status quo.
- **Anytime** — triggered during negotiation phase. Creates unpredictable drama.
- **Escalatory** — high-consequence, often irreversible. Requires multi-role authorization. Triggers AI world model cascades.

**Authorization mechanic:** Some actions require a second role to confirm. The initiator submits; the confirmer gets a real-time notification with countdown. Denied or timed out = action fails.

---

## 1 — Military Actions (9)

### 1.1 Deploy / redeploy units — Routine
**Initiator:** Defense minister or military chief. **Confirms:** Head of state.
Move units between theaters on the global map. Arrival takes 1 round (the transit delay creates the overstretched hegemon problem). Visible to all — redeployment signals intent. Minimum homeland garrison required.

### 1.2 Set military production level — Routine
**Initiator:** Defense minister, within approved budget. **Confirms:** PM/budget authority.
Normal / accelerated / maximum. Higher levels cost more coins + social score impact. Capped by production capacity.

### 1.3 Arms transfer — Anytime
**Initiator:** Head of state. **Confirms:** Defense minister (units leave their forces).
Sell or gift units to another country. Automatically public (intelligence satellites). Seller depleted. Buyer absorbs at reduced effectiveness for 1 round. May violate sanctions. Advanced systems create ongoing maintenance dependency on manufacturer.

### 1.4 Mobilization — Anytime (escalatory)
**Initiator:** Head of state. Unilateral.
Three levels: partial / general / total. Social score hit proportional to level. Available to countries at war or facing declared threat.

### 1.5 Attack — Escalatory
**Initiator:** Head of state orders. **Confirms:** Military chief executes.
Conventional military attack — ground, naval, or air. Scale determined by committed units. Activates theater zoom-in if not active. Dice-based combat with AI-calculated modifiers (units, tech level, morale, theater advantages). A large-scale concentrated attack IS an invasion — no separate action needed.

### 1.6 Naval blockade — Escalatory
**Initiator:** Head of state. **Confirms:** Military chief (requires naval units in theater).
Block maritime trade through chokepoint or around territory. Distinct from attack — economic warfare through military means. The Formosa blockade scenario requires this separate from invasion. AI calculates trade disruption and economic cascade.

### 1.7 Missile / drone strike — Escalatory
**Initiator:** Head of state. **Confirms:** Military chief.
Long-range precision strike. Does NOT require units in theater. Targets: military bases, infrastructure, nuclear facilities, leadership compounds. The Levantia-strikes-Persia scenario lives here.

### 1.8 Nuclear test — Escalatory
**Initiator:** Head of state. **Confirms:** Military chief.
No physical damage. Global social score impact. Diplomatic crisis. For Persia at Level 0: successful test = Level 1 advancement — a world-changing event.

### 1.9 Nuclear strike — Escalatory (two levels)
**Initiator:** Head of state (10 min visible preparation — detected by all nuclear powers' intelligence). **Confirms:** Defense minister/+ one more dedicated officia (e.g. VP) BOTH must confirm within 2 min. Either can deny.

**L1 Tactical:** Troops, installations, terrain. 50% troops in target zone destroyed. Economy -2 coins. Global social score shock. 5-min response window for other nuclear powers. Good Chances of interception in case area is protected with air defense. 

**L2 Strategic:** Cities, economic infrastructure. 30% economic capacity destroyed. 50% military in zone destroyed. Leader death 1/6 dice. Near-certain retaliation. Air defse only can reduce damage but can not garantee the atack will be blocked. 

---

## 2 — Economic Actions (7)

### 2.1 Submit national budget — Routine
**Initiator:** PM / finance authority. **Confirms:** Head of state can override. Columbia: requires parliamentary majority (3 of 5 seats).
Allocates coins across: military maintenance (auto-deducted), military production, social spending (above/below baseline), tech R&D investment, capacity investment, international transfers. Miss the deadline = defaults apply.

In Columbia specifically: budget submitted by Shield/economic officials, must pass parliament (Dealer's Seat 1 + Volt's Seat 2 + allies need majority). Tribune (Seat 3) and Challenger (Seat 4) can block if they hold 3 of 5 seats post-mid-terms.

### 2.2 Set tariff levels — Routine or Anytime
**Initiator:** Head of state or PM. Unilateral.
Rate 0-3 per economic sector per target country. 0 = free trade, 3 = near-prohibitive. AI calculates: revenue, import cost inflation, GDP impact, third-country rerouting. Can be announced dramatically mid-round. Retaliation likely.

In The Union (EU): trade tariffs are collective — EU members must agree on external tariff position through consensus.

### 2.3 Set sanctions position — Routine
**Initiator:** Head of state.
Scale -3 (actively helping evade) to +3 (maximum) per type (financial, resources, industrial, technology) per target. AI calculates weighted impact. Sanctions pressure neutrals as much as punish targets.

EU collective sanctions require Union consensus. The Seven (G7) coordination adds weight but is non-binding.

### 2.4 Asset seizure — Escalatory (Anytime)
**Initiator:** Head of state of country holding assets. Unilateral sovereign decision.
Freeze or seize foreign government/individual assets. Irreversible. Damages financial system credibility globally. Generates coins for seizer at enormous diplomatic cost.

### 2.5 Print money — Anytime
**Initiator:** PM. **Confirms:** Head of state.
Create coins from nothing. AI tracks cumulative inflation. Tempting short-term, toxic long-term. Currency crisis possible if overdone.

### 2.6 Transfer coins — Anytime (any spot transaction - buy, sell, gift, loan)
**Initiator:** Any actor with coins (state treasury or personal wealth).
Transfer to any other actor. Immediate, irreversible. Covers: aid, payments, bribes, loans (write terms in a treaty). Can be public or private (intelligence may detect large transfers).

### 2.7 Set OPEC+ production level — Routine (Cartel members only)
**Initiator:** Head of state / PM of Solaria, Nordostan, Persia, Mirage.
Low / normal / high. AI calculates global oil price from all producers combined. Prisoner's dilemma: cooperate or defect.

---

## 3 — Technology Actions (2)

### 3.1 Export restrictions — Anytime
**Initiator:** Head of state (Tech Level 2+ countries, or countries controlling critical resources).
Restrict exports of strategic goods (semiconductors, chip equipment, rare earths, advanced materials, AI components, energy tech) to a specific target. AI calculates: target slowdown, imposer revenue loss, rerouting. Mutual vulnerability (Cathay rare earths vs. Columbia chips) creates negotiation leverage.

### 3.2 Technology transfer — Anytime (spot transaction)
**Initiator:** Head of state. **Confirms:** Recipient agrees.
Share nuclear or AI/semiconductor technology for coins or concessions. Recipient advances one level. Massive diplomatic consequences — proliferation concerns, alliance reactions.

---

## 4 — Domestic / Political Actions (7)

### 4.1 Arrest — Anytime
**Initiator:** Head of state or security authority. Unilateral on own soil.
Detain any person physically present in your country. Target player restricted until released. If foreign national: international crisis. The defining autocratic power. Available to all countries but primarily relevant for Nordostan (Pathfinder), Cathay (Helmsman), Persia (Furnace/Anvil).

### 4.2 Fire / reassign — Anytime
**Initiator:** Head of state. Unilateral.
Remove any subordinate from role. They lose official powers but STAY in the game — with knowledge, connections, and a grievance. Politically costly.

### 4.3 Propaganda campaign — Anytime
**Initiator:** Head of state or designated official. Costs coins.
Standard: temporary political support boost, diminishing returns. "Sacred war" declaration: major one-time boost to stability + support, but commits to conflict narrative — retreat becomes politically catastrophic.

### 4.4 Assassination — Anytime (escalatory)
**Initiator:** Head of state or intelligence chief.
Two variants:
- **Domestic:** Target a political rival within your own country. Available to autocracies. The Navalny scenario.
- **International:** Target a foreign actor. The Soleimani scenario.

**Probabilistic:** Success probability 50% base, modified by target security level. Detection probability high (60-80%). If detected: extreme consequences (domestic = martyr effect + international condemnation; international = possible military retaliation + UNSC session). If target is a human player: survival by dice (1/6 death if high security, 1/3 moderate, 1/2 low). "Dead" players get reassigned as successors — nobody sits out permanently.

Cost: coins + possible political support hit even if undetected. Crossing a moral threshold that other actions don't. The decision is tracked in the behavioral data.

### 4.5 Coup attempt — Escalatory
**Initiator:** Any internal actor with military/security access. Requires co-conspirator.
Probability = f(stability index, political support, co-conspirators, military units under plotters' control, dice). Head of state retains powers UNTIL coup acknowledged — can arrest suspects beforehand. Applicable: Nordostan (Ironhand + Compass vs. Pathfinder), Cathay (Rampart + others vs. Helmsman — legitimized by Sage), Persia (Anvil as kingmaker).

### 4.6 Call elections — Anytime (democracies)
**Initiator:** Head of state (voluntary) or parliament/congress (forced when support drops below threshold).

**Columbia mid-terms (Round 2):** One parliamentary seat contested. Campaign speeches by Tribune (opposition) and Dealer (defense). All 9 team members vote + AI popular vote (50% weight based on economic conditions and presidential approval). Result: majority holds or flips. Hostile Congress = Tribune gains budget veto and investigation powers.

**Columbia presidential election (Round 5):** Nominations in Round 4 (candidates declare, brief speeches). General election at start of Round 5: campaign speeches (3 min each), brief debate, then votes (team members vote with weights: Fixer and Pioneer = 2 votes each, others = 1) + AI popular vote (50%). If Challenger wins: full power transfer. Former president stays as opposition.

**Heartland wartime election (Round 3-4):** Three candidates (Beacon, Bulwark, Broker). AI judges based on territory, economy, casualties, Western support, campaign quality. Winner becomes president.

**Other democracies:** Triggered when stability drops below threshold. AI generates outcome.

### 4.7 Respond to crisis — Reactive (triggered by AI)
Not a player-initiated action — a forced CHOICE when the AI engine triggers a domestic crisis (protests, economic shock, institutional failure).

When stability drops below 5: protests PROBABLE (AI rolls). Below 3: protests AUTOMATIC. The affected head of state must choose:
- **Concessions:** Spend coins, redirect budget to social needs. Stability recovers slowly. Looks weak.
- **Repression:** Use military/security units domestically. Stability holds temporarily. Long-term support erosion. International condemnation. Requires domestic military units.
- **Nationalist rally:** Propaganda + external threat emphasis. Temporary boost. Commits to escalation narrative.

In Persia specifically: if protests erupt, Dawn (reformist) gains influence — represents the street. Furnace and Anvil must decide: repress (Furnace's instinct) or accommodate (Anvil's pragmatism)?

---

## 5 — Covert Operations (1 action, sub-menu)

### 5.1 Covert operations — Anytime
**Initiator:** Intelligence chief (Shadow in Columbia) or head of state. Tech Level 1+ required.

Sub-options (gated by tech level):
- **Espionage** (Level 1+): Steal information about military deployments, economic data, nuclear program status. AI determines what is discovered.
- **Sabotage** (Level 2+): Damage infrastructure, military equipment, specific facilities (nuclear centrifuges — Stuxnet scenario). Physical damage without attribution.
- **Cyber attack** (Level 2+): Disrupt digital infrastructure, financial systems, military comms, elections. Deniable but attributable.
- **Disinformation** (Level 2+): Target another country's stability/political support through AI-enhanced information warfare. More effective than conventional propaganda. Risk: attribution, retaliation, blowback.

All covert ops are probabilistic. AI determines success/failure and detection/attribution. Repeated operations against same target increase detection probability.

---

## 6 — Diplomatic Actions (5)

### 6.1 Public speech — Anytime or Scheduled
**Initiator:** Any head of state or designated speaker. 2-3 minutes.
Address the room. Creates public commitments. Affects political support. Press amplifies.

Scheduled speech moments: Assembly (UNGA) addresses, campaign speeches before elections, emergency declarations. Campaign debates at Columbia and Heartland elections.

### 6.2 Sign treaty / agreement — Anytime (agreement - Any text signed by two or more sides)
**Initiator:** Any two+ heads of state or authorized representatives.
Content freely negotiated: peace terms, alliances, trade arrangements, secret protocols any thing (including - scede terriotory - e.g. allow Columbia to take control over Thule?)

In Columbia: major treaties require parliamentary ratification (3 of 5 seats).

### 6.3 Transactions. Coins vs. any tradeable asset or right (all atefacts in the sim should have an indication, if they are tradeable or not)
Transactions: basing rights, military units of any type, loans, direct economic subsidies, nuclear weapons, technologies. Immediate and binding. Breach = reputational cost (no automatic penalty — no international court). The universal bilateral action.

### 6.4 Call Council emergency session — Anytime
**Initiator:** Any P5 member (Columbia, Cathay, Nordostan, Gallia, Albion).
All P5 must attend. Resolutions proposed and voted. Any P5 vetoes. The act of calling it IS a political signal.

### 6.5 Create organization — Anytime
**Initiator:** Any group of 2+ countries.
Declare a new organization — alliance, trade bloc, security pact, currency union. Define membership and decision rules. Announce publicly. AI engine recognizes and tracks. The most consequential organization in the SIM might be one that didn't exist at game start. Examples: a new Pacific security pact, a BRICS currency union becoming operational, a European defense alliance separate from Western Treaty (NATO).

---

## Role-Specific Exclusive Actions

Beyond the standard actions, certain roles have capabilities nobody else possesses:

| Role | Exclusive capability | Why it matters |
|------|---------------------|---------------|
| Shadow (Columbia CIA) | Selective intelligence briefing — chooses what president sees. Higher covert op success probability. Can attribute cyber attacks. | Information as power. The only role controlling what the president knows. |
| Tribune (Columbia Congress) | Block budget (if majority). Launch investigation (damages target's political support). Initiate impeachment. Legislate sanctions (harder to reverse than executive). | Negative power — can't initiate but can block everything. Dominant after hostile mid-terms. |
| Spark (Columbia Tycoon) | Media manipulation (affects any country's political support). Independent tech investment. Back-channel meetings without government knowledge. | Unaccountable. Nobody can stop them. No authorization needed for anything. |
| Fixer (Columbia Envoy) | Independent Middle East diplomatic channel. Personal deal-making outside official State Dept channels. | Shadow diplomacy that may contradict Anchor's negotiations. |
| Pioneer (Columbia Envoy) | Independent tech/business channel to Cathay. Thule portfolio. | Maintains contacts official policy has severed. |
| Circuit (Cathay Tech) | Rare earth export restrictions. Independent international tech contacts. Cyber operations execution. | Controls Cathay's tech counter-weapons. Has external channels Helmsman may not know about. |
| Sage (Cathay Elder) | Legitimize leadership transition. No formal power — but can distinguish "course correction" from "coup." | The succession question personified. Grows powerful only as Helmsman weakens. |
| Compass (Nordostan Oligarch) | Personal coin transactions. Independent back-channels. Bribe foreign actors. | Operates entirely through personal channels. Can explore deals government can't officially pursue. |
| Anvil (Persia IRGC) | Controls IRGC military AND 30-40% of economy. Can support or undermine either Furnace or Dawn. | The kingmaker. Military + economic power in one role. |
| Dawn (Persia Reformist) | Represents the street — gains influence when protests erupt. International credibility with Western reformers. | No power in stability. Enormous power in crisis. The population's voice. |
| Veritas (Press) | Publish stories. Investigate secrets. Monopoly on public information channel. | The only actor who makes private actions public. |

---

## Action Count Summary

| Category | Actions | Count |
|----------|---------|:-----:|
| Military | Deploy · Production · Arms transfer · Mobilization · Attack · Blockade · Missile strike · Nuclear test · Nuclear strike (L1/L2) | 9 |
| Economic | Budget · Tariffs · Sanctions · Asset seizure · Print money · Transfer coins · OPEC+ production | 7 |
| Technology | Export restrictions · Technology transfer | 2 |
| Domestic | Arrest · Fire/reassign · Propaganda · Assassination · Coup attempt · Call elections · Respond to crisis | 7 |
| Covert | Covert operations (espionage / sabotage / cyber / disinformation) | 1 |
| Diplomatic | Speech · Sign treaty · Call Council session · Create organization · Territorial claim | 5 |
| **Total** | | **31** |

---

## Typical Round by Country Type

**Country at peace (e.g., Solaria):** 2-4 actions. Budget, OPEC+ production, maybe tariffs, maybe a deal.

**Country in economic war (e.g., Columbia vs. Cathay):** 5-8 actions. Budget, tariffs, sanctions, export restrictions, transfers, treaty, speech, possibly covert cyber.

**Country at war (e.g., Nordostan):** 8-12 actions. Budget, production at max, deploy, attack, mobilization, propaganda, sanctions response, diplomacy (treaty with Cathay, Council session), possibly assassination or covert ops.

**Country in crisis (e.g., Heartland):** 6-10 actions. Budget under pressure, arms received, election campaign, speeches, deployment, peace negotiations, respond to crisis.

**Country at nuclear threshold (e.g., Persia):** 4-8 actions. Nuclear program investment (budget), sanctions response, diplomatic engagement (Dawn), proxy operations (Furnace), IRGC business management (Anvil), possibly nuclear test if threshold reached.

---

## Changelog

- **v2.0 (2026-03-20):** Full revision for consistency with concept documents A1-C4. Added: Respond to crisis (4.7), Create organization (6.4), Territorial claim (6.5). Expanded: elections mechanic (4.6) to detail Columbia mid-terms, presidential election with parliamentary votes and weights, Heartland wartime election. Updated all organization references to SIM names (Western Treaty, The Union, The Council, The Cartel, The Seven, Columbia Parliament). Added Persia-specific mechanics. Role-specific exclusive actions table updated for all 6 teams including Sage, Anvil, Dawn, Fixer, Pioneer. 31 total actions (up from 28 — added 3 diplomatic/domestic actions, net of prior consolidations).
- **v1.0 (2026-03-19):** Initial action system. 28 actions across 6 categories.
