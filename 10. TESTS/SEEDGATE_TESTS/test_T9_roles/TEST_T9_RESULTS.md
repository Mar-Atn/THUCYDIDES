# TEST T9: ROLE ENGAGEMENT
## SEED Gate Test Results
**Tester:** INDEPENDENT (TESTER agent) | **Date:** 2026-03-30 | **Engine:** D8 v1 formulas + live action engine + web app spec (31 actions)

---

## VERDICT: CONDITIONAL PASS

**8 of 10 tracked non-HoS roles produce at least 1 meaningful mechanical action per round. Two roles (Dawn, Sage) have conditional activation that may leave them idle for multiple rounds.**

---

## METHODOLOGY

For each tracked role, I assessed:
1. **Available mechanical actions** (from roles.csv powers + web app spec 31 actions)
2. **Engine effect** (does the action change a world state variable?)
3. **Round-by-round engagement** (is there something to DO each round?)
4. **Minimum meaningful actions per round** (target: at least 1)

"Meaningful mechanical action" = an action that changes at least one engine variable (GDP, stability, support, military count, treasury, intel pool, etc.) OR creates an irreversible game state change (arrest, treaty, election result).

---

## ROLE-BY-ROLE ANALYSIS

### 1. TRIBUNE (Columbia -- Congressional Opposition Leader)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Block budget (#1 variant) | Parliament vote 3-2 after midterms | Blocks presidential budget allocation | 1/round (if majority) |
| Launch investigation (#25 variant) | Political action | -support for target, can produce intel | 1/round |
| Impeachment (#25) | Parliament vote, requires majority | Removes president if successful | 1/game (practical) |
| Public statement (#29) | Moderator-facilitated speech | Shapes narrative, election impact | Any time |
| Midterm campaign (R2) | Election mechanic | Flips Seat 5, changes parliament majority | 1/game |
| Disinformation card (#17) | 1 card | -3% support, -0.3 stability to target | 1/game |
| Protest stimulation card (#24) | 1 card | +20% protest probability | 1/game |

**Round-by-round assessment:**

| Round | Primary Action | Engine Effect | Idle? |
|-------|---------------|---------------|-------|
| R1 | Campaign for midterms, public statements, investigation | Narrative pressure, support erosion | NO |
| R2 | MIDTERM ELECTION. If won: parliament flips 3-2 opposition | Budget block power activated | NO |
| R3 | Block budget (if majority). Investigation. | Budget denied = fiscal crisis for Dealer | NO |
| R4 | Impeachment attempt (if conditions met) | Constitutional crisis | NO |
| R5 | Presidential election campaign | Election outcome | NO |
| R6-8 | Continue blocking, investigating, or governing if new president | Ongoing | NO |

**Verdict: PASS.** Tribune has mechanical actions every round. The midterm election is a genuine turning point. Budget blocking after R2 is a powerful mechanical lever -- it forces Dealer to negotiate or use emergency powers. Investigation produces narrative pressure. Impeachment is the nuclear option.

**Minimum actions/round: 1-2. Peak at R2 (election) and R4 (impeachment).**

---

### 2. CHALLENGER (Columbia -- Opposition Presidential Candidate)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Campaign (#29 public statement) | Shapes voter perception | Election formula player component | Any time |
| Foreign outreach (meetings) | Meet foreign leaders "if elected" | Creates commitments, hedging behavior | Any time |
| Public statement (#29) | Physical speech | Narrative, voter perception | Any time |
| Disinformation card (#17) | 1 card | -3% support, -0.3 stability | 1/game |
| Protest stimulation (#24) | 1 card | +20% protest probability | 1/game |
| Election vote | 1 vote in all elections | Direct input to election outcome | Per election |

**Round-by-round assessment:**

| Round | Primary Action | Engine Effect | Idle? |
|-------|---------------|---------------|-------|
| R1 | Campaign, foreign meetings, build coalition | Narrative only -- no direct engine variable | MARGINAL |
| R2 | Midterm support, foreign outreach | Narrative + vote contribution | MARGINAL |
| R3 | Intensify campaign, foreign meetings | Commitments shape post-R5 world | MARGINAL |
| R4 | Pre-election positioning | Narrative | MARGINAL |
| R5 | PRESIDENTIAL ELECTION | Direct engine effect: leadership change | NO |
| R6-8 | If won: full presidential powers. If lost: irrelevant. | Full or zero | DEPENDS |

**Verdict: CONDITIONAL PASS.** Challenger's mechanical impact is concentrated at R5 (election). Rounds 1-4 are campaign/narrative work with limited direct engine effect. The foreign outreach creates "commitments" but these are narrative, not mechanical. Challenger's engagement depends heavily on how foreign leaders respond to meetings.

**Concern:** Challenger has no mechanical action that changes a world state variable in R1-R4. The role is a political campaigner in a SIM with strong mechanical emphasis. Risk of player feeling like a spectator watching engine outputs they cannot influence.

**Minimum actions/round: 0-1 mechanical, 1-2 narrative. Adequate for experienced roleplayers, potentially frustrating for mechanically-oriented players.**

**Recommendation:** Consider giving Challenger 1 intelligence request (from roles.csv: intelligence_pool = 1). This provides at least one mechanical action per game. Also, Challenger's "alternative policy" power could be formalized: if Challenger publicly commits to a foreign policy position (e.g., "I will cut Ruthenia aid"), foreign AI agents should factor this into their calculations, creating indirect engine effects.

---

### 3. DAWN (Persia -- Reformist Leader)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Public appeal (#29) | Statement | Shapes perception, credibility bonus | Any time |
| Western contact (meetings) | Diplomatic meetings | Deals with Dawn as signatory get +20% credibility | Any time |
| Reform proposal | Narrative action | No direct engine effect | Any time |
| Protest stimulation (#24) | 1 card | +20% protest probability | 1/game |
| Diplomatic credibility bonus | Passive | +20% to agreements Dawn signs | Passive |

**Activation condition (from roles.csv):** "Activates when stability < 4 or support < 30%"

**Round-by-round assessment:**

| Round | Primary Action | Engine Effect | Idle? |
|-------|---------------|---------------|-------|
| R1 | Persia stability 4, support 40%. BELOW activation threshold (stability < 4? No, = 4. Support < 30%? No, = 40%) | **NOT YET ACTIVATED** | YES |
| R2 | If Persia deteriorates (war with Columbia, bombing): stability likely drops below 4 | Activates. Public appeal, meetings. | MARGINAL |
| R3 | Active. Western contact for sanctions relief. | +20% credibility on deals | NO |
| R4 | Active. Reform proposals. Diplomatic channel. | Indirect engine (sanctions relief = GDP boost) | NO |
| R5-8 | Active. Peace negotiation channel. | Credibility bonus on agreements | NO |

**Verdict: CONDITIONAL PASS.** Dawn has a delayed activation mechanic. If Persia's stability stays at or above 4, Dawn is mechanically dormant. Given that Persia starts at stability 4 with GDP -3.0% growth and 50% inflation, the activation threshold should be hit by R2 in most scenarios.

**Concern:** R1 is likely completely idle for Dawn. With Persia starting at stability 4.0 (exactly at threshold, not below), and support at 40% (above 30%), Dawn's activation condition is NOT met at game start. The player sits with no mechanical actions for an entire round.

**Minimum actions/round: 0 (R1), 1-2 (R2+). Below target for R1.**

**Recommendation:**
1. Lower Dawn's activation threshold to stability <= 5 or support <= 40% (from < 4 or < 30%). This activates Dawn from R1 given Persia's starting conditions.
2. OR: Give Dawn a pre-activation action -- "diplomatic outreach to the West" that costs personal coins and establishes back-channel contacts. Even if Dawn cannot sign deals, she can build relationships.

---

### 4. SAGE (Cathay -- Party Elder)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Party conference (convene) | Requires activation: stability < 5 or support < 40% | Can challenge Helmsman's authority | Conditional |
| Informal counsel | Narrative -- advise Helmsman | No direct engine effect | Any time |
| Succession mechanism | If Helmsman incapacitated | Influences succession | Conditional |
| Legitimacy challenge | Political action | Triggers power struggle | Conditional |

**Activation condition:** "Activates when stability < 5 or support < 40%"

**Round-by-round assessment:**

| Round | Cathay State | Sage Active? | Available Actions | Idle? |
|-------|-------------|-------------|-------------------|-------|
| R1 | Stability 8, support 58% | NO | Informal counsel only (narrative) | YES |
| R2 | Stability ~7.5, support ~55% | NO | Informal counsel | YES |
| R3 | Stability ~7, support ~52% | NO | Informal counsel | YES |
| R4 | If Cathay enters Formosa crisis: stability may drop | MAYBE | Party conference if stability < 5 | DEPENDS |
| R5-8 | If major crisis: yes. If not: no. | MAYBE | Depends entirely on Helmsman's decisions | DEPENDS |

**Verdict: CONDITIONAL PASS (BORDERLINE FAIL).** Sage's activation threshold (stability < 5 or support < 40%) is unlikely to be hit before R4-5 unless Cathay suffers a catastrophic crisis. Cathay starts at stability 8 and support 58%. Even with Formosa crisis, stability is unlikely to drop below 5 in fewer than 3-4 rounds (autocracy resilience multiplier reduces negative shocks by 25%).

**The core problem:** Sage is designed as a "circuit breaker" -- a role that activates only when the system is stressed. This is good design for the SIM but bad design for the PLAYER. A human sitting in the room for 3+ hours with nothing mechanical to do is a failed player experience.

**Minimum actions/round: 0 mechanical (R1-3), 0-1 (R4+). Below target.**

**Recommendation (IMPORTANT):**
1. Give Sage a pre-activation diplomatic role: Sage is listed as is_diplomat=true in roles.csv. Formalize this -- Sage can conduct back-channel diplomacy with any country, representing Cathay's "institutional" position (which may differ from Helmsman's). This creates tension and gameplay from R1.
2. Give Sage 1 intelligence request per game (currently intel_pool = 1 in roles.csv). Use it for party loyalty intelligence.
3. Consider lowering activation threshold to stability < 7 or support < 50%. Cathay starts at 8/58, so one bad round could activate Sage's formal powers.

---

### 5. BROKER (Ruthenia -- Opposition Politician)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Back-channel diplomacy (meetings) | Meet EU leaders, Sarmatia contacts | Creates peace frameworks | Any time |
| EU track negotiation | Diplomatic action | Can advance EU accession (narrative -> engine via treaty) | Any time |
| Public statement (#29) | Campaign speech | Shapes voter perception | Any time |
| Election candidacy (R3-4) | Election mechanic | Direct engine effect | 1/game |
| Protest stimulation (#24) | 1 card | +20% protest probability | 1/game |
| Personal wealth deployment | Spend personal coins (4) | Fund campaigns, humanitarian projects | Any time |
| Intelligence request | 1 request (intel_pool=1) | Information | 1/game |

**Round-by-round assessment:**

| Round | Primary Action | Engine Effect | Idle? |
|-------|---------------|---------------|-------|
| R1 | Meet EU leaders (Lumiere, Forge, Pillar, Ponte). Build peace framework. | Treaties/agreements have engine effect | NO |
| R2 | Continue EU diplomacy. Negotiate Ponte veto. Spend coins on campaign. | Coin transactions = engine effect | NO |
| R3 | ELECTION. Stand as candidate. | Direct engine effect | NO |
| R4 | If elected: executive powers. If not: continue diplomacy. | Full or partial | NO |
| R5-8 | Diplomatic channel regardless of election outcome | Ongoing | NO |

**Verdict: PASS.** Broker has mechanical actions every round. Personal coins (4, highest on the team) enable economic gameplay. EU diplomacy creates treaty/agreement engine events. Election provides a major mechanical moment. Even if Broker loses the election, the back-channel diplomat role continues.

**Minimum actions/round: 1-2. Strong engagement throughout.**

---

### 6. VOLT (Columbia VP)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Parliamentary vote | 1 of 5 seats | Budget/treaty ratification | Per vote |
| Become Acting President | If Dealer incapacitated (10%/round after R2) | FULL executive powers | Conditional |
| Diplomatic missions | If Dealer delegates | Treaty negotiation | Conditional |
| Election vote | All elections | Direct input | Per election |
| Succession lobbying | Narrative/political | Shapes R5 nomination | Ongoing |

**Round-by-round assessment:**

| Round | Primary Action | Engine Effect | Idle? |
|-------|---------------|---------------|-------|
| R1 | Parliamentary vote. Succession lobbying. Business roundtable meetings. | 1 vote = engine effect. Lobbying = narrative. | MARGINAL |
| R2 | Parliamentary vote (midterms). Campaign positioning. | Vote + narrative | MARGINAL |
| R3 | Parliamentary vote. Possible Acting President if Dealer incapacitated. | Vote. Possible full powers. | NO |
| R4 | Parliamentary vote. Pre-election positioning. | Vote. | MARGINAL |
| R5 | PRESIDENTIAL ELECTION. | Direct engine effect | NO |
| R6-8 | If president: full powers. If not: VP role continues. | Full or limited | DEPENDS |

**Verdict: PASS.** Volt has a guaranteed mechanical action every round (parliamentary vote). The 10% incapacitation chance for Dealer creates a genuine succession mechanic. Personal coins (5) enable political operations. The succession race with Anchor provides narrative engagement.

**However:** Volt's engagement quality varies. Parliamentary vote is guaranteed but may feel routine. The role's richness depends on Dealer's health events and the succession dynamics.

**Minimum actions/round: 1 (vote). Peak during incapacitation or election.**

---

### 7. CIRCUIT (Cathay -- Tech/Industry Chief)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Tech investment (personal coins) | Personal tech investment (G13 mechanic) | ai_rd_progress += (investment/GDP)*0.4 | Any round |
| Rare earth weapon recommendation | Advise Helmsman on restrictions | Restriction level affects target R&D efficiency | Indirect |
| Cyber operations (#16) | 2 cards (from roles.csv: cyber_cards=2) | Steal coins, reduce production, undermine GDP | 2/game |
| Foreign business meetings | Meet foreign tech/business contacts | Narrative + potential deals | Any time |
| Escape planning (personal) | Protect personal assets abroad (2 coins at risk) | Personal coin management | Ongoing |

**Round-by-round assessment:**

| Round | Primary Action | Engine Effect | Idle? |
|-------|---------------|---------------|-------|
| R1 | Personal tech investment. Rare earth policy advice. Foreign contacts. | ai_rd_progress change + rare earth mechanic | NO |
| R2 | Continue tech investment. Cyber op (if authorized). | ai_rd_progress + potential cyber effect | NO |
| R3 | Tech investment. Asset protection decisions. | Engine + personal management | NO |
| R4 | If Formosa crisis: rare earth weapon becomes critical. Cyber ops. | Major engine effect via rare earth | NO |
| R5-8 | Ongoing tech management. Second cyber card. | Engine effects | NO |

**Verdict: PASS.** Circuit has mechanical actions every round through personal tech investment and rare earth policy. Cyber operations (2 cards) provide direct engine intervention. The personal assets abroad (2 coins) create an internal tension mechanic. Rare earth restrictions directly affect other countries' R&D efficiency (-15% per level, floor 40%).

**Minimum actions/round: 1-2. Solid engagement.**

---

### 8. SHADOW (Columbia -- CIA Director)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Intelligence requests (#14) | 8 requests per game | Information (always returns answer) | ~1/round |
| Sabotage (#15) | 3 cards | Destroy 1-2 units OR -2% GDP OR -0.1 R&D | 3/game |
| Cyber attack (#16) | 3 cards | Steal 1-2 coins OR -1 production OR -1% GDP | 3/game |
| Disinformation (#17) | 1 card | -3% support, -0.3 stability | 1/game |
| Election meddling (#18) | 1 card | 2-5% election swing | 1/game |
| Assassination (#22) | 1 card | Kill/injure target | 1/game |
| Intelligence briefing control | Choose what Dealer sees | Information asymmetry -- shapes presidential decisions | Every round |
| Presidential Daily Brief curation | Selective truth | Indirect engine effect via Dealer's actions | Every round |

**Round-by-round assessment:**

| Round | Primary Action | Engine Effect | Idle? |
|-------|---------------|---------------|-------|
| R1 | Intelligence request. Brief Dealer (selectively). Possible sabotage/cyber. | Information + potential direct effect | NO |
| R2 | Intelligence request. Covert op. Brief curation. | Multiple effects | NO |
| R3 | Intelligence request. Election meddling (Ruthenia election). | Intel + election impact | NO |
| R4 | Intelligence request. Sabotage/cyber. | Direct engine effect | NO |
| R5 | Intelligence request. Possible assassination. Election meddling (Columbia). | Multiple critical effects | NO |
| R6-8 | Remaining intel + covert cards. | Ongoing | NO |

**Verdict: STRONG PASS.** Shadow is the most mechanically rich non-HoS role in the game. 8 intelligence requests + 3 sabotage + 3 cyber + 1 disinformation + 1 election meddling + 1 assassination = 17 one-shot mechanical actions across 8 rounds. Plus the ongoing intelligence briefing control mechanic. The information asymmetry (controlling what Dealer sees) is a powerful indirect engine lever.

**Minimum actions/round: 2-3. Highest engagement of any non-HoS role.**

---

### 9. SHIELD (Columbia -- Secretary of Defense)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Co-authorize military attack (#7) | Required co-signature with Dealer | Enables/blocks combat | Per attack |
| Deploy forces (#13) | Operational command | Unit positioning | Per round |
| Military operations management | Overstretch assessment | Shapes military posture | Ongoing |
| Co-authorize nuclear launch (#11) | Required confirmation | Nuclear authorization chain | Conditional |
| Sabotage card (#15) | 1 card | Direct engine effect | 1/game |
| Cyber card (#16) | 1 card | Direct engine effect | 1/game |
| Intelligence requests (#14) | 3 requests | Information | 3/game |
| Veto military action (refuse co-signature) | Block Dealer's attack order | Prevents combat action | Any time |

**Round-by-round assessment:**

| Round | Primary Action | Engine Effect | Idle? |
|-------|---------------|---------------|-------|
| R1 | Deploy forces. Co-authorize Persia operations. Overstretch assessment. | Unit deployment = engine state change | NO |
| R2 | Deployment decisions. Co-authorization decisions. Intel request. | Multiple | NO |
| R3 | Force management. Possible refusal of escalation order. | Engine effect via veto or action | NO |
| R4 | Critical if Cathay blockades Formosa: Pacific redeployment decisions. | Major engine effect | NO |
| R5-8 | Ongoing military management + covert ops cards. | Engine effects | NO |

**Verdict: PASS.** Shield has mechanical actions every round through force deployment and co-authorization. The veto power (refusing to co-sign an attack) is a powerful negative mechanic -- it creates genuine tension with Dealer. Intelligence requests (3) and covert ops cards (sabotage + cyber) provide additional direct engine effects.

**Minimum actions/round: 1-2. Engagement peaks during military crises.**

---

### 10. IRONHAND (Sarmatia -- Marshal/Chief of General Staff)

**Available mechanical actions:**
| Action | Mechanic | Engine Effect | Frequency |
|--------|----------|---------------|-----------|
| Military operations (#7, #8, #9) | Execute Pathfinder's orders | Combat resolution | Per order |
| Nuclear co-authorization (#11) | Required co-signature | Nuclear launch enable/block | Conditional |
| Honest assessment (sealed memo) | Private report to Pathfinder | Shapes presidential decisions | Per round |
| Slow-walk orders | 1-round delay on implementation | Delays engine effect | Any time |
| Coup potential (#23) | Co-conspirator with Compass | Regime change | 1/game |
| Intelligence requests (#14) | 3 requests | Information | 3/game |
| Sabotage card (#15) | 1 card | Direct engine effect | 1/game |
| Cyber card (#16) | 1 card | Direct engine effect | 1/game |

**Round-by-round assessment:**

| Round | Primary Action | Engine Effect | Idle? |
|-------|---------------|---------------|-------|
| R1 | Execute Ruthenia operations. Honest assessment. | Combat + information | NO |
| R2 | Continue operations. Slow-walk if disagree with orders. | Engine effect (delayed) | NO |
| R3 | Military ops. Intel request. Possible coup plotting with Compass. | Multiple effects | NO |
| R4 | Critical military decisions (offensive or defend). Nuclear question. | Major engine effects | NO |
| R5-8 | Ongoing military management + covert cards. | Engine effects | NO |

**Verdict: PASS.** Ironhand has mechanical actions every round. The nuclear co-authorization is the ultimate leverage point -- Pathfinder cannot launch nuclear weapons without Ironhand's consent. The slow-walk mechanic creates subtle power. Coup potential with Compass provides a dramatic option. Military operations provide direct engine effects.

**Minimum actions/round: 1-2. Strong engagement, especially during military crises.**

---

## SUMMARY TABLE

| Role | Country | Mechanical Actions/Round | Engine Effect | Verdict |
|------|---------|:------------------------:|:-------------:|---------|
| Tribune | Columbia | 1-2 | YES (budget block, investigation, impeachment) | PASS |
| Challenger | Columbia | 0-1 mechanical, 1-2 narrative | LIMITED (election R5 only) | CONDITIONAL |
| Dawn | Persia | 0 (R1), 1-2 (R2+) | CONDITIONAL (activation threshold) | CONDITIONAL |
| Sage | Cathay | 0 (R1-3), 0-1 (R4+) | CONDITIONAL (activation threshold) | CONDITIONAL (BORDERLINE FAIL) |
| Broker | Ruthenia | 1-2 | YES (coins, diplomacy, election) | PASS |
| Volt | Columbia | 1 | YES (vote, possible Acting President) | PASS |
| Circuit | Cathay | 1-2 | YES (tech investment, rare earth, cyber) | PASS |
| Shadow | Columbia | 2-3 | YES (intel, covert ops, briefing control) | STRONG PASS |
| Shield | Columbia | 1-2 | YES (co-auth, deploy, covert ops) | PASS |
| Ironhand | Sarmatia | 1-2 | YES (military ops, nuclear co-auth, slow-walk) | PASS |

---

## KEY FINDINGS

### FINDING 1: Columbia Non-HoS Roles Are Well-Designed
Tribune, Shadow, Shield, and Volt all have distinct mechanical levers that create genuine intra-team tension. Shadow is the standout -- 17 one-shot actions across 8 rounds, plus ongoing briefing control. Tribune's budget-blocking power (post-midterms) creates a constitutional crisis mechanic. Shield's co-authorization veto is powerful.

### FINDING 2: Challenger Needs Mechanical Weight
Challenger has the weakest mechanical profile of all tracked roles. Campaign speeches and foreign outreach are narrative actions without direct engine effect until R5. For 4 rounds, the player is essentially a political campaigner in a wargame.

### FINDING 3: Conditional Activation Roles (Dawn, Sage) Risk Player Frustration
Both Dawn and Sage have activation thresholds that may not be met for multiple rounds. Sage is the worst case -- Cathay starts at stability 8 / support 58%, far from the activation threshold. A player assigned Sage could sit for 3-4 rounds with only "informal counsel" (narrative) as their action.

### FINDING 4: The Action Review Additions Work
Post-action-review tools (impeachment, court, protest stimulation, intelligence pools per individual) successfully distribute mechanical power to non-HoS roles. The 31-action system provides broad coverage.

### FINDING 5: Information Asymmetry Is a Powerful Mechanic
Shadow's briefing control and Ironhand's honest assessment/slow-walk create genuine information asymmetry within teams. This is a design strength -- it makes non-HoS roles matter because they control what the HoS knows and how orders are implemented.

---

## ISSUES LOG

| # | Severity | Issue | Recommendation |
|---|----------|-------|----------------|
| T9-1 | MEDIUM | Sage has 0 mechanical actions R1-3 (possibly R1-5). Player frustration risk. | Lower activation threshold to stability < 7 or support < 50%. Give pre-activation diplomatic role. |
| T9-2 | MEDIUM | Dawn has 0 mechanical actions R1. Activation threshold barely missed at start. | Lower threshold to stability <= 5 or support <= 40%. Or give pre-activation diplomatic action. |
| T9-3 | MEDIUM | Challenger has limited mechanical weight R1-4. Narrative-heavy role in mechanical SIM. | Add 1 intelligence request. Formalize "alternative policy" commitments as engine inputs for AI agents. |
| T9-4 | LOW | Volt's parliamentary vote may feel routine. Engagement depends on Dealer's health. | Consider giving Volt a "policy brief" power -- publish analysis that shifts support by 1-2%. |
| T9-5 | INFO | Shadow has the highest action density of any non-HoS role (17 one-shots + ongoing). Risk of overwhelming the player. | Consider facilitator guidance for Shadow player (pace covert ops across rounds). |

---

## FINAL VERDICT

**CONDITIONAL PASS**

8 of 10 roles produce at least 1 meaningful mechanical action per round. The action review additions (impeachment, intelligence pools, protest cards, co-authorization) successfully distribute mechanical power to non-HoS roles.

**Conditions for PASS:**
1. Address Sage activation threshold (T9-1) -- ensure the player has something to do from R1
2. Address Dawn activation threshold (T9-2) -- ensure activation from R1 given Persia's starting conditions
3. Review Challenger's mechanical weight (T9-3) -- at minimum add 1 intelligence request

**No conditions for:**
- Volt (T9-4) -- adequate as-is
- Shadow (T9-5) -- strong design, facilitator manages pacing
