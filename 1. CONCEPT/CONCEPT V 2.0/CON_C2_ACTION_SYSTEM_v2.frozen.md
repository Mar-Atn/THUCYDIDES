# Thucydides Trap SIM — Action System
> **RECONCILIATION NOTE (2026-04-07):** This document is the original CONCEPT design.
> Mechanics, probabilities, and action counts have been calibrated during BUILD.
> For CURRENT canonical values, see: `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` + `CARD_FORMULAS.md`
> Changes: 51 actions consolidated to 32. Nuclear model simplified (binary warhead + T1-T3 tiers).
> Combat probabilities recalibrated. "Espionage" renamed to "Intelligence" throughout.

**Code:** C2 | **Version:** 3.0 | **Date:** 2026-03-21 | **Status:** Aligned with E1 Engine Architecture v0.7

---

## Design Principle

Actions are **role-specific features in the web app**. Each player sees only the actions available to their role. Authorization chains are enforced digitally. The permission structure IS the decision rights architecture made interactive.

**Three processing systems handle actions** (see E1 Engine Architecture):
- **Transaction (Market) Engine** — bilateral transfers, both parties confirm, instant, no calculation
- **Live Action Engine** — unilateral actions requiring calculation (dice, probability, AI), instant resolution with universal mechanic (AI probability → visual dice/fortune wheel → result)
- **World Model Engine** — batch processing between rounds, calculates cumulative consequences

**Two timing modes:**
- **Real-time** — executes immediately during the round. Participants see results and react.
- **Submitted** — collected during the round, processed by World Model Engine between rounds.

---

## 1 — Military Actions (8)

### 1.1 Deploy / redeploy units
**Timing:** After World Model processing, 5-minute deployment window before next round starts.
**Initiator:** Military chief or head of state.
Assign newly available units (produced, mobilized, arrived from transit) to zones on the map. Deployment is instant to any allowed location (own territory, controlled territory, allied territory with basing agreement). Units deployed this round can attack adjacent zones starting next round — creating an effective 1-round delay for force projection. Ships carry 1 ground unit + 2 air units (own country only). Strategic missiles cannot embark. Naval cannot deploy into active blockades. Must leave at least 1 ground unit in any controlled zone.

### 1.2 Arms transfer
**Timing:** Real-time (Transaction (Market) Engine).
**Initiator:** Head of state or military chief. **Confirms:** Recipient accepts.
Sell or gift units of any type to another country or individual. Exclusive transfer — sender loses, receiver gains. Transferred units have reduced effectiveness for 1 round. All five unit types tradeable.

### 1.3 Mobilization
**Timing:** Submitted anytime during round. Executed by World Model Engine between rounds.
**Initiator:** Head of state. Unilateral.
Three levels: partial / general / total. Social cost proportional to level (applied in political state update). Mobilized units available for deployment window after processing.

### 1.4 Attack (ground-to-ground / naval-to-naval)
**Timing:** Real-time (Live Action Engine). Universal resolution mechanic.
**Initiator:** Head of state. **Confirms:** Military chief.
RISK-model combat. Attacker selects units from one zone to attack adjacent zone. Dice roll per unit pair — highest wins, attacker loses ties (defender advantage). Morale modifier and first-round-of-deployment modifier apply. Must leave at least 1 unit in origin zone and in any newly captured zone. Amphibious assault (sea to land): requires 3:1 force ratio after modifiers (4:1 for Formosa). Naval superiority in the sea zone is prerequisite. Pre-landing bombardment can reduce defender count. See C1 for full rules.

### 1.5 Naval blockade
**Timing:** Real-time (Live Action Engine).
**Initiator:** Head of state. **Confirms:** Military chief. Requires at least 1 naval unit in the sea zone.
Chokepoint/zone status changes on map immediately. Trade flow disruption flag raised. Economic cascade calculated by World Model Engine between rounds. Blockade holds until naval unit removed.

### 1.6 Tactical air/missile strike
**Timing:** Real-time (Live Action Engine). Universal resolution mechanic.
**Initiator:** Head of state. **Confirms:** Military chief.
Disposable — consumed on use. Can target any zone adjacent to own forces, bases, or naval units. Can target naval units in adjacent waters. Air defense in target zone absorbs up to 3 (configurable) incoming strikes per air defense unit before remaining strikes resolve.
> **BUILD UPDATE:** Air strike hit probability calibrated to 12% base / 6% with AD. 15% chance attacker downed by AD. See CARD_ACTIONS 1.4 + CARD_FORMULAS D.2.

### 1.7 Strategic missile launch
**Timing:** Real-time (Live Action Engine). GLOBAL ALERT triggered.
**Initiator:** Head of state. **Confirms:** Military chief. Nuclear warhead authorization: always requires 3 confirmations (HoS + military chief + one additional authority), all within 2 min. In smaller teams, AI military advisor provides the missing confirmation and may refuse if strategically irrational.
Can target ANY zone on the global map. Disposable — consumed on use. Warhead type (conventional or nuclear, if L1+) chosen at launch — UNKNOWN to target. Global alert to all participants: "strategic missile launch detected." 10-minute real-time execution window. Air defense attempts interception.

**Nuclear warhead (L1 tactical):** 50% troops in zone destroyed. Economy -2 coins. Air defense CAN intercept.
**Nuclear warhead (L2 strategic):** 30% economic capacity destroyed. 50% military destroyed. Leader survival 1/6. Air defense reduces but cannot guarantee block.
5-minute retaliation window. Global stability shock.
> **BUILD UPDATE:** Nuclear warhead types simplified to binary (conventional | nuclear). Tier system (T1 midrange / T2 strategic / T3 salvo) replaces L1/L2. See CARD_ACTIONS 1.8-1.9.

### 1.8 Nuclear test
**Timing:** Real-time (Live Action Engine). Universal resolution mechanic.
**Initiator:** Head of state. **Confirms:** Military chief.
L1+ countries only. No military outcome. Probability based on tech level. Persia L0 success → L1.

### Naval bombardment (inherent capability, not separate action)
Each naval unit adjacent to land can bombard once per round. 10% chance per unit of destroying one random ground unit. Resolved by Live Action Engine on request.

---

## 2 — Economic Actions (5)

### 2.1 Submit national budget
**Timing:** Submitted during round. Processed by World Model Engine.
**Initiator:** PM / finance authority. Head of state can override. Columbia: requires parliamentary majority (3 of 5 seats).

Allocates discretionary budget (revenue minus mandatory maintenance) across: social spending (baseline = % of GDP), ground production, naval production, tactical air production, strategic missile production (Cathay only), tech R&D (nuclear + AI/semiconductor), reserves.

Production tiers: Normal (1× cost per unit for 1× output), Accelerated (2× cost per unit for 2× output; total 4×), Maximum (4× cost per unit for 3× output; total 12×). Deficit: cut, print money (inflation), or draw reserves. Zero reserves + deficit = economic crisis.

### 2.2 Set tariff levels
**Timing:** Submitted. **Initiator:** Head of state or PM.
Rate 0-3 per sector (resources, industry, services, tech) per target. Double-edged: revenue for imposer, import cost inflation. EU tariffs collective.

### 2.3 Set sanctions position
**Timing:** Submitted. **Initiator:** Head of state.
Scale -3 to +3 per type (financial, resources, industrial, technology) per target. Coalition sanctions more effective. EU requires consensus.

### 2.4 Set OPEC+ production level
**Timing:** Submitted. **Initiator:** Cartel members only.
Low / normal / high. Oil price from combined decisions. Prisoner's dilemma.

### 2.5 Export restrictions
**Timing:** Submitted. **Initiator:** Head of state.
Restrict strategic goods (semiconductors, rare earths) to specific targets. Slows target, costs imposer.

---

## 3 — Transactions (Market Engine — real-time)

Bilateral. Both parties confirm. Immediate. Irreversible (except basing rights). Atomic one-sided records. Individuals can transact same as countries.

| # | Transaction | Mechanic |
|---|-------------|----------|
| 3.1 | **Coin transfer** | Exclusive. Any actor → any actor. Balance check. |
| 3.2 | **Technology transfer** | Replicable — receiver gains, sender keeps. Irreversible. |
| 3.3 | **Treaty / agreement** | Plain text, any signatories. Stored, not enforced. |

> **SEED DECISION (2026-03-27):** Ceasefire and peace agreements use the standard
> transaction engine "agreement" type. Any participant can propose any deal as free text
> (ceasefire, peace treaty, territorial settlement, alliance, trade deal). The other side
> can amend, reject, accept, or counter-propose. No special mechanics — just the standard
> agreement transaction with:
> - Agreement name (e.g., "Ruthenia-Sarmatia Ceasefire")
> - Free text terms
> - Required signatories (both HoS must confirm)
> - When both HoS sign a ceasefire: engine updates war_status, combat pauses between
>   those countries, territory frozen at current lines
> - Breach (attacking after ceasefire): automatic re-declaration of war + diplomatic
>   penalty (all other countries notified)
| 3.4 | **Organization creation** | Heads of state. NAME + MEMBERS + PURPOSE. |
| 3.5 | **Basing rights** | Replicable. Uniquely REVOCABLE by host. |

---

## 4 — Domestic / Political Actions (5 + elections)

| # | Action | Timing | Resolution |
|---|--------|--------|------------|
| 4.1 | **Arrest** | Real-time | Instant. Target restricted. Own soil only. |
| 4.2 | **Fire / reassign** | Real-time | Instant. Target loses powers, stays in game. |
| 4.3 | **Propaganda** | Real-time | Coins spent. Diminishing/negative returns if overused. AI tech L3+ auto-boosts. |
| 4.4 | **Assassination** | Real-time | Universal mechanic. 50% ± modifiers. Detection 60-80%. Survival dice for human targets. |
> **BUILD UPDATE:** Probabilities recalibrated: domestic 30%, international 20%, Levantia 50%. Detection 100%, attribution 50%. See CARD_ACTIONS 6.2.
| 4.5 | **Coup attempt** | Real-time | Multi-step: X-min window, >30% team independently submit, AI probability, fortune wheel. |

**Elections** (scheduled, processed by World Model Engine):
- Columbia mid-terms (Round 2): team votes + AI popular vote (50%)
- Columbia presidential (Round 5): nominations R4, speeches + debate, weighted votes + AI (50%)
- Ruthenia wartime (Round 3-4): AI judges on gameplay outcomes

---

## 5 — Covert Operations (AI-mediated, real-time)

Free-text requests interpreted by AI against actual DB world state. Limited per round per country. Detection probability escalates with repeated ops. Moderator-adjustable delay (default instant).

| # | Operation | Input | Output to initiator |
|---|-----------|-------|---------------------|
| 5.1 | **Intelligence** | Written question | Probabilistic answer (may be accurate, partial, or wrong) |
| 5.2 | **Sabotage** | Target + description | Success/failure + outcome description |
| 5.3 | **Cyber attack** | Target + description | Success/failure + disruption description |
| 5.4 | **Disinformation** | Target + narrative | "Operation executed" + vague indicator |
| 5.5 | **Election meddling** | Target + candidate + approach | "Operation executed successfully" (effect hidden) |

---

## 6 — Other Actions (2)

### 6.1 Public statement
**Timing:** Real-time. Any participant. No authorization.
Plain text logged. Covers territorial claims, war declarations, peace offers, speeches, anything.

### 6.2 Call organization meeting
**Timing:** Real-time. Any member of any org they belong to.
Suggest time and venue. UNSC, EU, NATO, Parliament, BRICS+, OPEC+, player-created orgs. No enforcement.

---

## Military Unit Types

| Type | Producible | Range | Key mechanic |
|------|:---------:|-------|-------------|
| Ground | Yes (budget) | Adjacent | RISK combat, territory control |
| Naval | Yes (budget) | Adjacent sea | Blockade, bombardment (10%), sea combat |
| Tactical air/missiles | Yes (budget) | Adjacent to forces | Disposable strike |
| Strategic missiles | Cathay +1/round only | Global | Warhead unknown to target. Scarce. |
| Air defense | Not producible | Deployed zone | Absorbs up to 3 strikes/unit |

---

## Role-Specific Exclusive Actions

| Role | Exclusive capability |
|------|---------------------|
| Shadow (Columbia CIA) | Selective intelligence briefing. Higher covert op success. |
| Tribune (Columbia Congress) | Block budget (if majority). Investigation. Impeachment. |
| Fixer (Columbia Envoy) | Independent Middle East channel. Personal deal-making. |
| Pioneer (Columbia Envoy) | Tech/business channel to Cathay. Thule portfolio. Media manipulation. Independent tech investment. Semi-unaccountable — personal business empire creates conflicts of interest. |
| Circuit (Cathay Tech) | Rare earth restrictions. Cyber ops. Independent contacts. |
| Sage (Cathay Elder) | Legitimize transitions. Grows powerful as Helmsman weakens. |
| Compass (Sarmatia Oligarch) | Personal transactions. Independent back-channels. |
| Anvil (Persia IRGC) | Military + economy control. Kingmaker. |
| Dawn (Persia Reformist) | Represents the street. Power in crisis. |
| Veritas (Press) | Publish. Investigate. Public information monopoly. |

---

## Action Summary (~30 actions)

| Category | Count | System |
|----------|:-----:|--------|
| Military | 8 | Mixed: Market + Live Action + World Model |
| Economic | 5 | World Model (submitted) |
| Transactions | 5 | Market Engine (real-time) |
| Domestic + Elections | 5 + elections | Live Action + World Model |
| Covert | 5 | Live Action (AI-mediated) |
| Other | 2 | Real-time (logged) |

---

## BUILD Reconciliation Notes (2026-04-13)

> This section documents how BUILD implementation diverged from or refined the original CONCEPT design.
> CONCEPT remains frozen as the design heritage record. For current canonical values, see references below.

- BUILD consolidated the action catalog from 51 concept actions to 32 SEED actions to **25 implemented with locked contracts**.
- 28 locked CONTRACT documents specify every action (probabilities, schemas, invariants).
- All 25 action types route through a central **Action Dispatcher** with typed Pydantic schemas.
- Actions split into 3 dispatch categories: Immediate (Phase A), Batch (Phase B), Movement (Inter-Round).
- 6 action categories: Military (7), Covert (4), Domestic/Political (8), Transactions (4), Economic/Regular (4), Communications (2).
- Key simplifications from CONCEPT: mobilization replaced by martial law (one-off), cyber merged with sabotage, export restrictions merged with sanctions.
- Canonical action catalog: `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md`

---

## Changelog

- **v3.0 (2026-03-21):** Full alignment with E1 Engine Architecture v0.7. Restructured by processing system. Military production absorbed into budget. Five unit types with unified strategic missiles (warhead unknown). Asset seizure parked. Print money in budget deficit rules. Respond to crisis removed. Covert ops AI-mediated with election meddling. Territorial claim → Public statement. Council session → Call any org meeting. Deployment post-processing window.
- **v2.0 (2026-03-20):** Revision for concept documents A1-C4. 31 actions.
- **v1.0 (2026-03-19):** Initial. 28 actions.


<!-- CM-006: Deployment rules updated 2026-03-30. Transit delay removed (instant deployment). Ship capacity formalized (1 ground + 2 air). Naval blockade restriction added. Approved by Marat. -->
