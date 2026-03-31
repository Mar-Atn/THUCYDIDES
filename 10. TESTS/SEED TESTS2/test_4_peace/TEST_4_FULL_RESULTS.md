# TEST 4: PEACE NEGOTIATION — FULL RESULTS (8 Rounds)
## SEED TESTS2 | Thucydides Trap SIM
**Date:** 2026-03-27 | **Tester:** TESTER-ORCHESTRATOR

---

## TEST PARAMETERS

**Objective:** Test the ceasefire mechanic. Can Sarmatia and Ruthenia reach a deal? What terms emerge? Does the ceasefire transaction work?

**Setup Overrides (deviations from Test 1 baseline):**
- Sarmatia: Compass back-channel VERY ACTIVE (increased deal-seeking). Pathfinder more open to framework.
- Columbia: Dealer pushing HARD for Ruthenia deal (personal legacy obsession).
- Persia: Dawn given more room by Anvil (Anvil calculates deal is closer).

**Starting State:** Identical to Test 1 R1 world state (post-R1 engine results applied).

**Ceasefire Mechanic Under Test:**
- Transaction type: `agreement` with subtype `ceasefire` or `peace`
- Both HoS must sign
- Engine removes war from `ws.wars` list
- Territory freezes at current lines
- Breach = automatic re-declaration + diplomatic penalty

---

## ROUND 1 (H1 2026) — OPENING POSITIONS

### Starting Conditions (Post-Test 1 R1)
| Metric | Sarmatia | Ruthenia |
|--------|-----------|-----------|
| GDP | 20.15 | 2.25 |
| Stability | 4.90 | 4.62 |
| Support | 54% | 50% |
| Treasury | ~0 | ~2 |
| Ground forces | 11 front + reserves | 5 front + 3 reserve |
| Territory | ~40% Ruthenia occupied (4 oblasts claimed, ~65-70% controlled) | Defending remaining 60% |

### Negotiation Track

**Dealer --> Pathfinder (via Riyadh back-channel):**
"I want a deal. Ruthenia is Europe's problem. I need something for television — a ceremony, a handshake, Pathfinder and Dealer on the White House lawn. Your troops stay where they are. We call it a 'security arrangement.' Sanctions unwind over 18 months. NATO stays out of Ruthenia. What do you say?"

**Pathfinder --> Dealer (via same channel):**
"I respect a man who makes deals. I am ready. But I need REAL recognition — not an arrangement, sovereignty over the annexed territories. And NATO membership for Ruthenia is the red line. Kill the membership process or there is no deal."

**Compass (independently) --> Albion financial contacts:**
"If framework announced in 60 days, what is the sanctions relief timeline? What assets unfreeze first? I need specifics."

**Beacon --> Dealer (direct request):**
"Ruthenia is prepared to discuss security architecture for durable peace. Floor: EU membership, Western security forces on soil, no sovereignty concessions."

**Dealer response to Beacon:** Delayed 48 hours. Then: "I hear you. We're looking at all the options."

### Analysis R1
- **Gap identified:** Pathfinder demands sovereignty recognition over all four oblasts + no NATO for Ruthenia. Beacon demands no territorial concessions + EU membership + Western troops. These positions are maximalist on both sides.
- **Dealer's position:** Indifferent to Ruthenia's demands. Wants the photo op. Will sacrifice Ruthenia's interests for his legacy deal.
- **Compass's angle:** Purely financial. Working sanctions relief timeline before any framework exists. Building the business case for peace.
- **Ruthenia not at the table.** Dealer is negotiating FOR Ruthenia WITHOUT Ruthenia. Beacon is demanding to be included but has zero leverage to force it.

### Military Actions
- Sarmatia: Donetsk concentration continues. Gains ruthenia_15. Grinds forward.
- Ruthenia: Defensive hold. Drone strikes on logistics (4 rail corridors).
- No escalation from either side. Both signaling "reasonableness" for the diplomatic audience.

### Engine Results R1
(Identical to Test 1 R1 — see engine_results_r1.md)

---

## ROUND 2 (H2 2026) — BACK-CHANNEL INTENSIFIES

### Key Events
- **Columbia midterm election** this round.
- Oil at $198 (down from $237 due to partial Gulf Gate breach).
- Sarmatia treasury at zero. Running on Cathay credit.

### Negotiation Track

**Dealer --> Pathfinder (direct phone call, Anchor excluded):**
"Here's my offer. I call it the Columbia Peace Framework. Five points: (1) Ceasefire at current lines. (2) 'Special administrative zones' — your people run them, international observers monitor. Not sovereignty recognition, not NOT sovereignty recognition. Ambiguous. (3) Ruthenia renounces NATO membership for 20 years. (4) Sanctions phased out over 24 months. (5) Dealer-Pathfinder summit for signing. Historic. Two leaders who ended a war."

**Pathfinder response (24-hour delay, Compass consulted):**
"The framework has potential. I have concerns: (a) 'Special administrative zones' must include clear language that these are Sarmatia sovereign territory under a transitional arrangement. Not ambiguous — specific. (b) 20 years is not enough. Permanent NATO exclusion. (c) Sanctions relief begins upon ceasefire, not 24 months. (d) EU membership for Ruthenia must be explicitly excluded from the framework. I will not sign a deal that opens the EU door."

**Compass --> Geneva channel (unauthorized, expanding his mandate):**
"The President will accept less than he says. 'Sovereign territory under transitional arrangement' is the language that works internally. I can sell: current lines frozen, special status, NATO moratorium 25 years, sanctions immediate partial relief. He needs the word 'sovereignty' in the text. You need the word 'transitional' in the text. Both words in the same sentence. I have done this before."

**Beacon (learning about the back-channel through Mariner's intelligence):**
FURIOUS. Direct call to Dealer: "You are negotiating away my country without my consent. No framework has legitimacy without Ruthenia's signature. I will go public."

**Dealer to Beacon:** "Relax. This is a framework. You'll be at the table. But you need to be realistic. The war cannot go on forever. Your people are dying. I'm trying to save them."

**Beacon (privately to Broker):** "He is selling us. Prepare the EU track. If Columbia abandons us, Europe is our only anchor."

### Columbia Midterm Election
**AI Score:**
- Columbia: GDP growth 1.81%, stability 6.95, 1 active war (Persia)
- econ_perf = 1.81 * 10 = 18.1
- stab_factor = (6.95 - 5) * 5 = 9.75
- war_penalty = -5 * 1 = -5
- ai_score = clamp(50 + 18.1 + 9.75 - 5, 0, 100) = 72.85

**Player votes (simulated):** Tribune + Challenger campaign hard. Persia war + $198 oil + overstretch narrative. incumbent_pct = 42%.

**Final:** 0.5 * 72.85 + 0.5 * 42 = 57.4%. **Incumbent wins.** Dealer's camp retains 3-2 majority. Tribune's investigation continues but lacks teeth without majority.

### European Reaction
- **Forge (Teutonia):** Cautiously supportive of any ceasefire framework. Privately: "If this ends the energy crisis, we accept imperfect terms."
- **Sentinel (Freeland):** OPPOSED. "Any deal that rewards Sarmatia's aggression guarantees they invade again in 10 years. We will be the next target."
- **Lumiere (Gallia):** "France must be at the table. No deal without European security guarantee architecture."
- **Mariner (Albion):** Shares Dealer-Pathfinder back-channel details with Beacon. Opposes any deal without Ruthenia consent but works the process.
- **Ponte:** "If sanctions are lifted and energy prices drop, I support whatever framework achieves that."

### Military Actions
- Sarmatia: Continued Donetsk grinding. Gains partial control of ruthenia_16. But Zaporizhzhia front thinned — Ruthenia drone strikes disrupting 2 of 4 rail corridors. Supply strain.
- Ruthenia: Receives 1 AD unit from Columbia. Drone campaign intensified.
- Choson: 3rd wave arrives (2 ground units, per R1 transaction). Deployed to rear security.

### Engine Results R2
| Country | GDP | Stability | Support | Treasury | Key |
|---------|-----|-----------|---------|----------|-----|
| Columbia | 290.2 | 6.90 | 38% | ~40 | Midterms won, Persia war continues |
| Sarmatia | 20.3 | 4.80 | 53% | ~0 (Cathay credit) | Treasury empty, Donetsk gains |
| Ruthenia | 2.30 | 4.45 | 48% | ~2 | Stability falling, election pressure |
| Oil Price | $189 | — | — | — | Declining on partial Gulf Gate + expectations |

---

## ROUND 3 (H1 2027) — RUTHENIA ELECTION + FRAMEWORK EMERGES

### Key Events
- **Ruthenia wartime election** (first round) this round.
- Sarmatia approaching 3 years of war. Economy sustained only by Cathay.
- Dealer pushing framework hard — wants announcement before end of round.

### Negotiation Track

**Dealer circulates "Columbia Peace Framework v2" to Pathfinder AND Beacon:**

> **THE COLUMBIA FRAMEWORK FOR EASTERN EUROPEAN SECURITY**
> 1. Immediate ceasefire at current lines of contact.
> 2. Occupied territories designated "Special Security Zones" under international monitoring.
>    - Existing administrations remain in place (de facto Sarmatia governance).
>    - International observers (UN-mandated, no NATO personnel).
>    - Legal status to be determined by "comprehensive settlement" within 10 years.
> 3. Ruthenia commits to non-alignment for 25 years — no NATO membership application.
> 4. Sanctions phase-out: 30% immediate upon ceasefire, 70% over 36 months tied to compliance.
> 5. EU membership for Ruthenia: not addressed (explicitly excluded from framework scope).
> 6. Security guarantees: G7 "enhanced partnership" with Ruthenia (deliberately vague — NOT Article 5).
> 7. POW exchange within 30 days.
> 8. Dealer-Pathfinder-Beacon trilateral summit for signing.

**Pathfinder's response:**
"Points 1-2: Acceptable with modifications. 'Special Security Zones' must include referendum provision — the people choose. We know how they will choose. Point 3: 25 years insufficient. 40 years. Point 4: Acceptable. Point 5: EU membership IS a security matter. Must be explicitly prohibited or framework is meaningless — EU mutual defense clause replicates NATO Article 5. Point 6: No foreign security guarantees on Ruthenia soil. G7 partnership is propaganda. Point 7: Acceptable. Point 8: Acceptable — I want the summit."

**Beacon's response:**
"REJECTED. (1) No ceasefire that freezes occupation. My territory is not a 'zone.' (2) No NATO renunciation. (3) The 'comprehensive settlement in 10 years' is a fiction — Sarmatia will never negotiate return. (4) 'Enhanced partnership' is worth less than the paper it is written on. Budapest Memorandum was worth nothing. (5) I need TROOPS, not WORDS. European security forces on my soil. (6) If EU is excluded from scope, Ruthenia rejects the entire framework."

**Broker (shadow diplomacy, separate from Beacon):**
Contact to Forge and Pillar: "Beacon will reject anything. I would not. If I win the election, I bring a framework Europe can support: ceasefire at current lines, EU fast-track, European security force, face-saving language for Sarmatia. My price: EU membership by 2029."

**Compass --> Geneva channel:**
"The referendum language is Pathfinder's minimum. He needs to show his people they 'chose' Sarmatia. Give us the word 'referendum.' We both know it means nothing with Sarmatia troops present. But it gives him the domestic narrative."

### Ruthenia Wartime Election (Round 3 — First Round)

**AI Score (Ruthenia):**
- GDP growth 2.36%, stability 4.45, 1 active war (Sarmatia)
- econ_perf = 2.36 * 10 = 23.6
- stab_factor = (4.45 - 5) * 5 = -2.75
- war_penalty = -5 * 1 = -5
- territory_factor = -3 * 4 = -12 (4 occupied zones)
- war_tiredness = -2 * 2.5 = -5 (estimated war tiredness)
- ai_score = clamp(50 + 23.6 - 2.75 - 5 - 12 - 5, 0, 100) = 48.85

**Player votes (simulated):** Bulwark's campaign ("properly resourced, we can do more") gaining traction. Broker's EU membership pitch resonating. incumbent_pct = 38%.

**Final:** 0.5 * 48.85 + 0.5 * 38 = 43.4%. **Incumbent loses first round.** Beacon and Bulwark proceed to runoff (Round 4).

**Impact:** Beacon's authority is now contested. Foreign leaders begin hedging — taking calls from both Bulwark and Broker. Dealer privately considers: "Do I wait for the new leader or push the deal now while Beacon is still in office and desperate?"

### Persia Track (Parallel)

**Dawn --> Lumiere (Gallia):**
"Framework proposal: (a) 72-hour ceasefire renewable, (b) Gulf Gate partial reopening — civilian tankers under IAEA escort, (c) nuclear transparency protocol for sanctions relief, (d) human rights dialogue channel."

**Anvil (giving Dawn more room, per setup override):**
"Dawn may negotiate the blockade adjustment. Civilian tankers only. IRGC retains military control of chokepoint. Partial reopening is not surrender — it is pricing. Tell the French: this costs sanctions relief on oil exports. If Columbia wants the strait open, they pay."

**Lumiere --> Dawn:** "France accepts the framework basis. Propose Geneva for talks. Can you deliver Anvil?"
**Dawn:** "Anvil is with me on the economics. The blockade costs us both. I can deliver a partial opening."

### Military Actions R3
- Sarmatia: Donetsk advance slows. Supply disruption from drone strikes. Net gain: partial ruthenia_17. Zaporizhzhia front static.
- Ruthenia: Defensive hold. Receives additional Storm Shadow from Albion. Uses 2 on Sarmatia logistics hubs (rail junction at Belgorod equivalent).
- Sarmatia casualties: -2 ground (11 -> 9 front). Ruthenia: -1 ground (5 -> 4 front).

### Engine Results R3
| Country | GDP | Stability | Support | Treasury | Key |
|---------|-----|-----------|---------|----------|-----|
| Sarmatia | 20.4 | 4.65 | 51% | ~0 | Grinding, broke, support eroding |
| Ruthenia | 2.35 | 4.20 | 43% | ~2 | Election lost R1, authority crumbling |
| Oil Price | $175 | — | — | — | Declining on partial Gulf Gate + Persia talks |

---

## ROUND 4 (H2 2027) — RUTHENIA RUNOFF + CRISIS POINT

### Key Events
- **Ruthenia wartime election RUNOFF** this round.
- Dealer escalates pressure on Beacon: "Sign the framework or I cut all aid."
- Sarmatia approaching fiscal collapse — 4 rounds of deficit.

### Negotiation Track

**Dealer to Beacon (ultimatum):**
"The framework is on the table. You sign or Bulwark signs. Either way, there is a deal. If you sign now, you are the peace president. If you wait and lose, Bulwark signs it and you are the man who prolonged the war for nothing."

**Beacon's agonized deliberation:**
- Broker: "Sign a modified version. Add EU membership. You survive."
- Bulwark: "Do not sign under duress. If I win, I negotiate from military strength."
- Beacon: "I will not sign a document that gives away our territory. I will not be the man who signed the surrender."

**Beacon REJECTS the framework again.** Public statement: "Ruthenia will not accept a peace dictated by others. Our people did not fight and die for 'special security zones.' We fight for our land, our sovereignty, our future in Europe."

**Pathfinder (to Compass):**
"Beacon is finished. Wait for the new one. The election changes nothing for us — whoever wins Ruthenia needs peace more than we do. Our position improves with time."

**Compass:** "No, it does not. Treasury is zero. Cathay credit is not infinite. Helmsman is already signaling: 'resolve this or we recalibrate.' He does not want to bankroll a frozen conflict. The new Ruthenia leader — whoever it is — will be more flexible. Push Dealer for the summit NOW, before his own election cycle paralyzes him."

### Ruthenia Wartime Runoff (Round 4)

**AI Score (Ruthenia, R4):**
- GDP growth ~2.0%, stability 4.20, 1 war
- econ_perf = 20.0
- stab_factor = (4.20 - 5) * 5 = -4.0
- war_penalty = -5
- territory_factor = -3 * 4 = -12
- war_tiredness = -2 * 3.0 = -6
- ai_score = clamp(50 + 20 - 4 - 5 - 12 - 6, 0, 100) = 43.0

**Player votes (simulated):** Bulwark's message — "I can fight better AND negotiate from strength" — resonates. Beacon's rejection of the framework seen as stubbornness, not principle. incumbent_pct = 35%.

**Final:** 0.5 * 43.0 + 0.5 * 35 = 39.0%. **Beacon loses.** Bulwark becomes president of Ruthenia.

**Transition mechanics:**
- Bulwark gains all presidential powers (Section 4 of Beacon's role).
- Beacon loses executive authority. Retains personal coins and can still act as political figure.
- Military morale bonus: +1 modifier under Bulwark (per role brief).
- Foreign leaders immediately request bilaterals with Bulwark.

**Bulwark's opening statement as president:**
"Ruthenia fights. That has not changed. What changes is how we fight and what we fight for. I will negotiate — but I negotiate as a soldier who knows the cost of war, not as a politician who fears the cost of peace. No deal without security guarantees. No deal without a path to Europe. But I am open to a ceasefire that stops the killing while we build the architecture of real peace."

### European Reaction to Bulwark
- **Sentinel:** Relieved. "A military president who understands defense."
- **Forge:** Cautiously optimistic. "Bulwark will negotiate. That is progress."
- **Lumiere:** Immediately proposes Franco-British-Ruthenia security triangle.
- **Mariner:** Offers 5,000-troop ceasefire monitoring commitment. "If Bulwark signs, we deploy."

### Persia Track R4

**Dawn-Lumiere Geneva talks produce "Geneva Protocol Draft":**
- 72-hour ceasefire (renewable)
- Gulf Gate: 2 civilian tanker corridors under IAEA escort (8 hours/day)
- Nuclear: IAEA inspections of Fordow (surviving facility) in exchange for medical sanctions relief
- Prisoner exchange framework

**Anvil approves conditionally:** "The tanker corridors earn revenue. The IAEA inspection buys time — they see what we show them. Medical sanctions relief is humanitarian cover for economic reopening. This is good business."

**Furnace objects:** "IAEA inspection is surrender. The fatwa declared nuclear deterrence wajib."

**Anvil to Furnace:** "The fatwa declared nuclear deterrence obligatory. It did not say when. We continue developing. The inspections show them the old damage. They see what we want them to see. The fatwa is fulfilled in spirit. Revenue flows. We survive."

**Furnace reluctantly approves the Geneva Protocol** — his first major concession. Dawn gains standing.

### Military Actions R4
- Sarmatia: Offensive tempo reduced. Cannot sustain momentum with zero treasury. Supply issues from drone strikes. Net: no territorial gain this round.
- Ruthenia: Bulwark orders selective counterattack — 2 ground units probe Zaporizhzhia front. Sarmatia, weakened, loses 1 ground. **First Ruthenia territorial recovery** — partial recapture of ruthenia_14.
- Casualties: Sarmatia -1 ground (9 -> 8 front). Ruthenia -0 (probing attack succeeded).

### Engine Results R4
| Country | GDP | Stability | Support | Treasury | Key |
|---------|-----|-----------|---------|----------|-----|
| Sarmatia | 20.2 | 4.50 | 49% | ~0 | Stalled, support falling, Zaporizhzhia loss |
| Ruthenia | 2.40 | 4.35 | 55% (Bulwark) | ~2 | New president rally, morale boost |
| Oil Price | $162 | — | — | — | Geneva Protocol optimism |

---

## ROUND 5 (H1 2028) — THE DEAL COMES TOGETHER

### Key Events
- **Columbia presidential election** this round.
- Sarmatia's Zaporizhzhia setback + fiscal collapse creates urgency.
- Bulwark's election provides fresh mandate.
- Persia Geneva Protocol functioning — tanker corridors open, oil declining.

### Negotiation Track

**Bulwark --> Dealer (direct):**
"I am not Beacon. I do not reject frameworks. I negotiate them. Here is what I need to sign:
(1) Ceasefire at current lines — acceptable as INTERIM measure, not permanent settlement.
(2) 'Interim security administration' — not 'special zones.' Language matters. Status determined by internationally supervised process within 5 years, not 10.
(3) NATO: I accept a moratorium on membership APPLICATION — 15 years. But Ruthenia retains the right to ASPIRE. And the moratorium does not apply to EU membership.
(4) EU membership track proceeds independently.
(5) European security force — minimum 10,000 troops (Gallia, Albion, Freeland contributions) deployed along ceasefire line.
(6) Sanctions relief tied to compliance — 30-60-36 structure works.
(7) POW exchange + humanitarian corridors + missing persons mechanism."

**Dealer's reaction:** "This I can work with. The security force is Europe's problem, not mine. NATO moratorium — Pathfinder needs longer but 15 is a start. EU track — I don't care about the EU. Let the Europeans deal with their club. Get me the summit."

**Pathfinder's response to Bulwark's terms (via Compass, Geneva channel):**
"The new Ruthenia president is more realistic. But:
(a) 'Interim security administration' is acceptable language.
(b) 5-year settlement timeline too short. 15 years.
(c) NATO moratorium must be 30 years minimum.
(d) EU membership IS a security matter. Mutual defense clause = NATO by another name. Must be addressed.
(e) NO European security force. Foreign troops on Sarmatia's claimed territory is unacceptable.
(f) Referendum provision must be included in any settlement process."

**Compass (private assessment to Pathfinder):**
"Sir, the gap is narrowing. The real issues are: (1) European troops — Bulwark will not sign without them, you will not sign with them. This is the hardest problem. (2) EU membership — you are right that the mutual defense clause replicates NATO. But blocking EU membership is a bridge too far for European support. (3) Settlement timeline — 5 vs 15, we can split at 8-10. Recommendation: accept European MONITORING force (observers, not troops — no weapons, no mandate), concede EU track 'without prejudice to security framework,' and demand 10-year settlement with referendum. This gives us the substance. They get the optics."

**Pathfinder (after 48 hours):**
"I will consider the monitoring force distinction. But it must be civilian, not military. No uniforms. No weapons. No European flags on my territory. Compass — draft the language. Keep it vague."

### Columbia Presidential Election (Round 5)

**AI Score (Columbia):**
- GDP growth ~1.7%, stability 6.80, 1 war (Persia — reduced tempo)
- econ_perf = 17.0
- stab_factor = (6.80 - 5) * 5 = 9.0
- war_penalty = -5
- ai_score = clamp(50 + 17 + 9 - 5, 0, 100) = 71.0

**Player votes (simulated):** Dealer's peace framework narrative helps. Oil down to $162. But overstretch, Persia war fatigue, Tribune's investigation. Volt vs Challenger. Dealer endorses Volt. incumbent_pct = 48%.

**Final:** 0.5 * 71.0 + 0.5 * 48 = 59.5%. **Incumbent camp wins.** Volt becomes president.

**Volt's pivot:** "I will complete the peace framework. But my priority is Cathay competition, not European security architecture. Europe must lead on the Ruthenia file. I give you 90 days to close the deal or I move on."

### Persia Track R5

**Geneva Protocol upgraded to "Geneva Accord":**
- Full ceasefire in effect (Columbia stops strikes, Persia stops missiles)
- Gulf Gate: 2 permanent tanker corridors (16 hours/day)
- IAEA enhanced inspections at Fordow + Isfahan
- Medical + food sanctions lifted
- Oil sanctions: partial relief (Persia can export to non-Western markets at reduced volume)
- **NOT a peace treaty** — "cessation of hostilities framework"

**Transaction processed:**
```
Type: agreement
Subtype: ceasefire
Sender: columbia
Receiver: persia
Signatories: [columbia, persia, levantia]
Name: "Geneva Accord on Cessation of Hostilities"
```

**Engine effect:** War `columbia-persia` removed from `ws.wars`. Persia missile strikes stop. Columbia air strikes stop. Gulf Gate partially open. Oil price drops further.

**Levantia (Citadel):** FURIOUS. "The nuclear program is 60% degraded, not eliminated. We stop now and they rebuild. This is a mistake." But Citadel cannot continue without Columbia air support. Accepts under protest.

### Military Actions R5
- Sarmatia: Minimal offensive activity. Treasury empty. Consolidation of held territory.
- Ruthenia (Bulwark): Continues selective probes on Zaporizhzhia front. Sarmatia's thinned lines give way at ruthenia_18. **Second territorial recovery.**
- Net position: Sarmatia now holds ~38% (down from ~42% peak).

### Engine Results R5
| Country | GDP | Stability | Support | Treasury | Key |
|---------|-----|-----------|---------|----------|-----|
| Columbia | 295.5 | 6.85 | 48% (Volt) | ~42 | New president, Persia ceasefire |
| Sarmatia | 20.0 | 4.35 | 47% | ~0 | Losing ground, broke, support collapsing |
| Ruthenia | 2.50 | 4.50 | 58% (Bulwark) | ~3 | Territory recovered, morale up |
| Persia | 5.10 | 4.20 | 42% | ~1 | Geneva Accord, economy stabilizing |
| Oil Price | $138 | — | — | — | Geneva Accord, Gulf Gate partial opening |

---

## ROUND 6 (H2 2028) — NEGOTIATION CLIMAX

### Key Events
- Volt gives 90-day deadline.
- Sarmatia's fiscal crisis now existential — 5 rounds of deficit.
- Ruthenia gaining ground. Momentum shift.
- Persia ceasefire holding (engine confirmed: no war in wars list).

### Negotiation Track

**"Riyadh Framework" summit — Dealer's final push before leaving office + Volt's deadline:**

Participants: Volt (Columbia), Pathfinder (Sarmatia), Bulwark (Ruthenia), Lumiere (Gallia), Forge (Teutonia), Mariner (Albion).

**Pathfinder arrives with revised position (Compass's fingerprints):**
1. Ceasefire at current lines (accepts Ruthenia recovery of ruthenia_14 and ruthenia_18).
2. "Interim administrative arrangements" — existing authorities remain, international civilian monitoring mission (OSCE-type, no weapons).
3. Settlement process within 10 years, including "consultative mechanisms reflecting the will of local populations" (avoids the word 'referendum' directly but everyone knows).
4. NATO moratorium: 20 years on membership application. Ruthenia retains aspiration language.
5. EU membership: "proceeds on its own merits, without prejudice to the security framework" (Compass's language — ambiguous enough for both sides).
6. Sanctions: 30% immediate, remainder over 36 months.
7. POW exchange within 30 days. Missing persons mechanism.

**Bulwark's response:**
"Close. But:
(a) 'Consultative mechanisms' is referendum by another name under occupation. The process must include displaced persons voting. 5 million Rutheniaers cannot be excluded from deciding their own territory's fate.
(b) NATO moratorium: I accept 20 years. But moratorium begins from SIGNING, not from today.
(c) European security force: I need 5,000 uniformed personnel along the ceasefire line. Not civilian monitors — military observers with sidearms and mandate to report violations. Non-negotiable.
(d) EU membership explicit support from all signatories.
(e) Demilitarized zone 15km on each side of ceasefire line."

**Pathfinder (visibly angry):**
"Military observers ARE troops. I said no European uniforms on my territory. And displaced persons voting — you want 5 million refugees to vote in our territory? This is a mechanism to reverse the outcome. Unacceptable."

**Volt (mediating, impatient):**
"Split it. 3,000 EU-mandated monitors in civilian dress with communications equipment. Not armed. Mandate: ceasefire verification only. Displaced persons: participate in settlement process through a commission, not a vote. Pathfinder gets no European military. Bulwark gets international presence. Nobody gets everything."

**Compass (back-channel to Bulwark's advisor):**
"3,000 monitors in civilian dress is fine. It is a face-saving formula. Everyone knows they report to Brussels. The word 'civilian' is for Pathfinder's domestic audience. The presence is for yours."

**Bulwark (after consultation with Lumiere and Mariner):**
"I can accept 3,000 EU civilian monitors with communications equipment and a reporting mandate to the OSCE. IF: (a) Gallia and Albion provide a bilateral security guarantee — Article 42.7 EU mutual defense clause commitment. (b) EU membership candidacy status confirmed at signing. (c) Demilitarized zone 10km."

**Pathfinder:**
"Demilitarized zone acceptable at 5km. No bilateral security guarantees — these replicate NATO. Candidacy status is an EU internal matter — I will not sign a document that includes it."

### STALEMATE ON THREE ISSUES:
1. **European security guarantee** — Bulwark demands it, Pathfinder rejects anything resembling collective defense.
2. **EU candidacy at signing** — Bulwark wants it in the document, Pathfinder wants it excluded.
3. **DMZ width** — minor (5 vs 10 km), bridgeable.

### Lumiere's Intervention
"A separate document. The peace framework stands alone — signed by Sarmatia, Ruthenia, Columbia. On the same day, in a separate ceremony, the EU issues a declaration on Ruthenia candidacy. Pathfinder does not sign the EU document. The EU does not sign the peace framework. Both happen. Both are real. Neither is formally linked."

**Forge backs this.** Mariner backs this. Volt does not care.

**Pathfinder (to Compass, privately):**
"The French are clever. Two documents, one day. I can live with this — I do not sign anything with the EU. My signature is on the peace framework only. What they do with their club is their affair. But: no Article 42.7 language in any document I sign or that references documents I sign."

**Compass:** "We can construct this. The peace framework mentions no EU. The EU declaration mentions no peace framework. Parallel processes, same day. I will draft."

### Persia Track R6
Geneva Accord holding. Oil continuing to drop. Dawn's profile rising domestically. Anvil satisfied — IRGC revenue recovering through partial oil exports. Furnace increasingly marginalized.

### Military Actions R6
- **Both sides observe informal ceasefire** on Zaporizhzhia front during Riyadh talks. Donetsk front reduced to minimal activity.
- No significant territorial changes.
- War tiredness: Sarmatia 3.5, Ruthenia 3.0.

### Engine Results R6
| Country | GDP | Stability | Support | Treasury | Key |
|---------|-----|-----------|---------|----------|-----|
| Sarmatia | 19.8 | 4.25 | 45% | ~0 | Approaching political danger zone |
| Ruthenia | 2.55 | 4.60 | 60% (Bulwark) | ~3 | Bulwark momentum |
| Oil Price | $125 | — | — | — | Persia accord + peace expectations |

---

## ROUND 7 (H1 2029) — THE CEASEFIRE

### Key Events
- Sarmatia support at 45% — approaching instability threshold (40%).
- Pathfinder's domestic window closing. Compass privately: "Sign now or lose the option."
- Volt's patience exhausted. "Close or I redirect to Cathay competition."
- Lumiere's two-document formula accepted by all parties.

### The Signing

**"Riyadh Peace Framework" — Final Terms:**

> **FRAMEWORK FOR PEACE AND SECURITY IN EASTERN EUROPE**
>
> Signed by: Sarmatia (Pathfinder), Ruthenia (Bulwark), Columbia (Volt)
> Witnessed by: Gallia (Lumiere), Teutonia (Forge), Albion (Mariner)
>
> **Article 1: Ceasefire.** Immediate and comprehensive ceasefire along current lines of contact, effective upon signing. All offensive military operations cease within 24 hours.
>
> **Article 2: Interim Administrative Arrangements.** Territories currently under Sarmatia administration shall maintain existing governance structures under international civilian monitoring. 3,000 EU-mandated civilian monitors deployed within 60 days. Monitor mandate: ceasefire verification and humanitarian reporting to OSCE.
>
> **Article 3: Settlement Process.** Comprehensive settlement to be negotiated within 10 years from signing. Process to include consultative mechanisms reflecting the will of affected populations, including provisions for displaced persons participation through an international commission.
>
> **Article 4: Security Architecture.** Ruthenia commits to a 20-year moratorium on NATO membership application, commencing from date of signing. Both parties commit to confidence-building measures and military transparency.
>
> **Article 5: Demilitarized Zone.** 7.5 km demilitarized zone on each side of the ceasefire line. Monitored by civilian observation mission.
>
> **Article 6: Sanctions.** Signatory states commit to phased sanctions adjustment: 30% upon ceasefire verification (60 days), remainder over 36 months tied to compliance benchmarks.
>
> **Article 7: Prisoners and Missing Persons.** Full POW exchange within 30 days. International Commission on Missing Persons established.
>
> **Article 8: Dispute Resolution.** Ceasefire violations reported to Joint Monitoring Commission (3 Sarmatia + 3 Ruthenia + 3 international). Verified breach triggers automatic review at UNSC.

**Parallel EU Declaration (same day, separate ceremony):**

> The European Council confirms Ruthenia's candidate status and commits to opening all remaining accession negotiation clusters within 12 months. The path to full EU membership proceeds on its own merits and timeline.

### TRANSACTION PROCESSED

```
Type: agreement
Subtype: ceasefire
Sender: sarmatia
Receiver: ruthenia
Signatories: [sarmatia, ruthenia]
Name: "Riyadh Framework for Peace and Security in Eastern Europe"
Details:
  - text: [full framework text]
  - witnesses: [columbia, gallia, teutonia, albion]
  - dmz_km: 7.5
  - monitors: 3000
  - nato_moratorium_years: 20
  - settlement_years: 10
  - sanctions_immediate_pct: 30
  - sanctions_remaining_months: 36
```

**Engine execution:**
1. Transaction validated: both HoS confirmed (Pathfinder + Bulwark).
2. Agreement stored in `ws.treaties` with subtype "ceasefire."
3. War lookup: `ws.wars` scanned for sarmatia-ruthenia conflict.
4. War found: attacker=sarmatia, defender=ruthenia, allies={attacker: [choson]}.
5. Signatories [sarmatia, ruthenia] — sarmatia on attacker side, ruthenia on defender side. **Match found.**
6. War REMOVED from `ws.wars`.
7. Event logged: `{type: "ceasefire", agreement_id: "agreement_X", ended_war: {...}, signatories: [sarmatia, ruthenia]}`
8. `wars_ended: 1` in execution_details.

**Verification:** `len(ws.wars)` reduced by 1. Eastern Ereb Theater war no longer active. Combat resolution engine will skip Sarmatia-Ruthenia pairs in future rounds.

### Reactions

**Pathfinder (public):** "Sarmatia has secured peace with honor. The territories are under our administration. The West has acknowledged reality. NATO expansion is halted for a generation. This is victory."

**Bulwark (public):** "The killing stops today. Ruthenia's path to Europe is confirmed. Our sovereignty is not conceded — it is defended through law, through institutions, through the presence of international monitors. This is the beginning, not the end."

**Volt (public):** "Columbia brokered the most significant peace agreement in a generation. We now turn our full attention to the defining challenge: ensuring Columbia leads in the competition with Cathay."

**Sentinel (Freeland):** "We note the agreement. Freeland's defense posture remains unchanged. NATO's eastern border is Freeland, and Freeland is ready."

**Helmsman (Cathay):** "We welcome peace. We note that the agreement demonstrates the value of dialogue over confrontation. Perhaps other disputes can be resolved similarly." (Subtext: Formosa.)

**Beacon (former president):** "History will judge whether this peace serves the living or betrays the dead. I pray it is the former."

### Engine Results R7
| Country | GDP | Stability | Support | Treasury | Key |
|---------|-----|-----------|---------|----------|-----|
| Sarmatia | 20.5 | 5.10 (+0.85) | 52% (+7) | ~1 (sanctions starting) | **Peace dividend: stability + support spike** |
| Ruthenia | 2.65 | 5.30 (+0.70) | 63% (Bulwark) | ~3 | **Peace dividend: stability + support spike** |
| Oil Price | $108 | — | — | — | War premium gone, Gulf Gate opening |

**Stability bounce:**
- Sarmatia: War friction removed (+0.15), sanctions relief expectation (+0.20), peace announcement (+0.50). Total: +0.85.
- Ruthenia: War friction removed (+0.20), EU candidacy confirmed (+0.15), peace hope (+0.35). Total: +0.70.
- Both countries cross back above 5.0 — exiting danger zone.

**Support bounce:**
- Pathfinder: "Victory" narrative + peace rally. +7 points.
- Bulwark: "Peace president" + EU track. +3 points (already high).

---

## ROUND 8 (H2 2029) — POST-CEASEFIRE

### Ceasefire Compliance Test

**Monitoring deployment:** 3,000 EU civilian monitors begin deployment. Gallia contributes 1,200, Teutonia 800, Freeland 400, others 600.

**Sarmatia compliance:** DMZ observed. Troop pullback from 7.5km zone. BUT: Sarmatia security forces (not military) remain in occupied zones. Monitoring mission reports "governance activities inconsistent with interim administration" — construction of permanent infrastructure, population registration, currency introduction.

**Ruthenia response:** Files complaint with Joint Monitoring Commission. "Sarmatia is consolidating permanent control under the guise of interim administration."

**Sarmatia response:** "Interim administration requires functioning governance. Schools, hospitals, currency — these serve the population. This is not a violation."

**DESIGN NOTE:** The ceasefire mechanic works correctly — war is removed, combat stops. But the POLITICAL compliance question is not mechanically enforced. The "settlement process within 10 years" has no enforcement mechanism. The monitors report but cannot compel. This is realistic but creates a FROZEN CONFLICT by design — exactly the outcome Pathfinder wanted and Beacon feared.

### Sanctions Relief Test

**30% immediate relief processed:**
- Sarmatia sanctions reduced from L3 to L2 (partial).
- Revenue boost: +2 coins from resumed limited trade.
- Cathay discount on energy normalized (no longer emergency pricing).
- Frozen asset discussion opened (Compass's priority).

### Persia Geneva Accord — Continued

**Holding.** Tanker corridors functioning. Oil exports recovering. IAEA inspections proceeding (seeing what Anvil wants them to see). Dawn's domestic position strengthened. Furnace increasingly ceremonial.

**No formal peace treaty yet** — just cessation of hostilities. The nuclear question deferred. Levantia seething. Anvil content.

### Military Posture Shift

**Sarmatia:** Begins slow drawdown. 2 ground units rotated out of Ruthenia (8 -> 6 on front equivalent, now behind DMZ). Maintenance costs drop. Treasury begins recovering.

**Ruthenia:** Bulwark maintains defensive posture. Does NOT demobilize. Redirects 1 ground to rear training (quality over quantity). Receives EU-funded equipment modernization.

**Columbia:** Rebalances to Pacific. 2 naval units redeployed from Mediterranean to East Cathay Sea. Cathay naval ratio: 9/11 = 0.818 (Columbia now 11 operational naval units with Persia commitment reduced).

### Engine Results R8
| Country | GDP | Stability | Support | Treasury | Key |
|---------|-----|-----------|---------|----------|-----|
| Sarmatia | 21.5 | 5.30 | 54% | ~3 | Recovering. Sanctions relief flowing. |
| Ruthenia | 2.80 | 5.55 | 61% | ~4 | Strongest position since war began |
| Columbia | 302.0 | 7.10 | 50% (Volt) | ~45 | Pacific rebalance |
| Cathay | 215.5 | 8.10 | 59% | ~48 | GDP ratio now 0.714 — closing |
| Oil Price | $98 | — | — | — | Approaching pre-crisis levels |

---

# POST-TEST ANALYSIS

## A. CEASEFIRE MECHANIC — FUNCTIONAL ASSESSMENT

### What Worked

1. **Transaction engine correctly processes ceasefire.** The `agreement` type with subtype `ceasefire` executes cleanly:
   - Both HoS confirmation required and enforced.
   - War identified by matching signatories to attacker/defender sides.
   - War removed from `ws.wars` list.
   - Event logged with full details.
   - `wars_ended` count returned in execution details.
   - Subsequent rounds correctly skip combat resolution for the ended war.

2. **Stability and support formulas respond appropriately.** War friction penalty removed immediately. Peace dividend visible in both countries' metrics. The formulas do not need modification — the existing war_friction term removal IS the peace dividend.

3. **Oil price responds to peace.** War premium drops, speculation reduces, supply normalizes. The oil formula's `war_premium = min(0.30, 0.10 * active_wars)` correctly decreases when wars end.

### What Is Missing or Broken

4. **DESIGN HOLE: No breach/violation mechanic exists.** The brief says "Breach = automatic re-declaration + diplomatic penalty" but the transaction engine has NO code for this. There is no:
   - Violation detection mechanism
   - Automatic re-declaration trigger
   - Diplomatic penalty function
   - DMZ enforcement check
   - Compliance monitoring system

   **Recommendation:** Add a `check_agreement_compliance()` method to the transaction engine that:
   - Accepts a list of violation reports per round
   - If a verified violation is confirmed by the Joint Monitoring Commission (player vote or moderator decision), triggers:
     - Automatic war re-declaration (add war back to `ws.wars`)
     - Diplomatic penalty: -2 stability for violator, -1 for all signatories
     - Sanctions snap-back to pre-ceasefire levels
   - This requires a `violations` field in the agreement data structure

5. **DESIGN HOLE: Territory freeze is not mechanically enforced.** The ceasefire says "current lines" but the engine has no mechanism to:
   - Record the ceasefire line positions
   - Prevent territory changes in occupied zones
   - Distinguish between military and civilian/administrative actions in occupied territory

   **Recommendation:** When a ceasefire is signed, store `ceasefire_line: {zones_attacker: [...], zones_defender: [...]}` in the agreement. The combat engine should refuse to process any military action in the DMZ or across the ceasefire line while the agreement is active.

6. **DESIGN HOLE: Sanctions relief schedule is not automated.** The agreement specifies 30-60-36 phased relief but this must be manually applied each round. No automated schedule exists.

   **Recommendation:** Add a `scheduled_effects` list to the agreement data structure:
   ```python
   "scheduled_effects": [
       {"round_offset": 1, "effect": "sanctions_reduce", "target": "sarmatia", "from": "L3", "to": "L2"},
       {"round_offset": 6, "effect": "sanctions_reduce", "target": "sarmatia", "from": "L2", "to": "L1"},
       ...
   ]
   ```
   The world model engine checks active agreements each round and applies scheduled effects.

7. **DESIGN HOLE: Choson's status in the ceasefire is undefined.** Choson has 2-4 ground units fighting alongside Sarmatia but is not a signatory. The ceasefire mechanic checks `allies.attacker` list and finds Choson — but the code only checks if SIGNATORIES are on opposing sides. Choson continues to be at war with Ruthenia unless separately addressed.

   **Recommendation:** Either (a) require all belligerents including allies to sign, or (b) add a `covers_allies: true` flag to the ceasefire that extends cessation of hostilities to named allies. Current code does not handle this.

8. **DESIGN HOLE: POW exchange has no mechanic.** The agreement mentions it but there is no prisoner system in the world state. This is acceptable for the SIM's abstraction level — POW exchange is narrative, not mechanical.

## B. NEGOTIATION REALISM — ASSESSMENT

### What Produced Realistic Dynamics

9. **The 7-round negotiation arc is realistic.** The progression from maximalist positions (R1) through gradual convergence (R3-R6) to agreement (R7) mirrors real peace processes. No shortcut was possible — the positions had to evolve through pressure, elections, military realities, and mediator creativity.

10. **Dealer's personal involvement both helped and complicated.** Helped: forced pace, provided great-power pressure, created diplomatic infrastructure. Complicated: bypassed Ruthenia, created legitimacy crisis, prioritized photo op over substance. This dual effect is precisely what the role design intended.

11. **Compass's back-channel produced the most creative language.** "Sovereignty" + "transitional" in the same sentence. "Consultative mechanisms" instead of "referendum." "Civilian monitors" who report to Brussels. Compass is the negotiation's real author — the oligarch-fixer archetype works.

12. **Ruthenia's election was the forcing function.** Beacon's rigid position blocked the deal. Bulwark's election unlocked it — not because Bulwark was willing to concede more, but because he was willing to negotiate differently. The election mechanic works as intended: it changes the dynamics without predetermining the outcome.

13. **Lumiere's two-document formula resolved the EU deadlock.** A genuinely creative solution that a good player would find. The SIM design should ensure this kind of creative problem-solving is rewarded — it was the breakthrough moment.

### What Was Unrealistic or Forced

14. **Pathfinder conceded too much too fast under this setup.** The setup override (more open to framework) combined with fiscal pressure produced a Pathfinder who accepted civilian monitors and EU candidacy — both of which the real-world parallel would likely reject absolutely. Without the setup override, this deal probably does not happen in 8 rounds.

   **Assessment:** This is a DESIGN FEATURE, not a flaw. The test was designed to explore whether a deal IS POSSIBLE. The answer: yes, but only under favorable conditions (deal-seeking Sarmatia, legacy-obsessed Columbia president, military-realist Ruthenia leader). Under baseline conditions, the war likely freezes into a permanent stalemate — which is also a realistic outcome.

15. **European security guarantee was too easily resolved.** In reality, 3,000 unarmed civilian monitors is not a security guarantee. Bulwark accepted it because the EU mutual defense clause (Article 42.7) provides the real guarantee — but this was handled through the separate EU declaration, which Pathfinder did not sign or acknowledge. The gap between what Ruthenia NEEDS (armed deterrence) and what it GOT (civilian monitors) is a potential design tension worth exploiting in playtesting.

16. **Cathay was too passive.** Helmsman should be more actively trying to shape the peace terms — every ceasefire in Europe frees Columbia's attention for the Pacific. Cathay has an interest in a PROLONGED European war, not a quick peace. Future tests should model Cathay's spoiler potential.

## C. ENGINE DESIGN RECOMMENDATIONS

### Priority 1 (Must-Fix for Seed)

| # | Issue | Fix |
|---|-------|-----|
| 1 | No breach/violation mechanic | Add `check_agreement_compliance()` to transaction engine |
| 2 | No territory freeze enforcement | Store `ceasefire_line` in agreement, enforce in combat engine |
| 3 | Choson ally status undefined in ceasefire | Add `covers_allies` flag or require all-party signature |

### Priority 2 (Should-Fix for Seed)

| # | Issue | Fix |
|---|-------|-----|
| 4 | No automated sanctions schedule | Add `scheduled_effects` to agreement data structure |
| 5 | No ceasefire stability bonus in formula | Add explicit `peace_dividend` term to stability formula (currently emergent from war_friction removal — but a one-time signing bonus would be more realistic) |
| 6 | No diplomatic penalty for agreement rejection | If one party rejects after negotiation, should there be a reputation/support cost? Currently zero cost to reject. |

### Priority 3 (Nice-to-Have for Detailed Design)

| # | Issue | Fix |
|---|-------|-----|
| 7 | No DMZ mechanic | Define DMZ zones in world state, prevent unit deployment |
| 8 | No monitor deployment mechanic | EU monitors as a deployable unit type (non-combat) |
| 9 | No formal peace treaty vs ceasefire distinction | Ceasefire = temporary, peace = permanent. Different engine effects. |

## D. PERSIA CEASEFIRE — SEPARATE FINDINGS

The Persia track produced a "cessation of hostilities" (not a full ceasefire/peace) that:
- Correctly processed through the transaction engine as subtype "ceasefire"
- Removed the columbia-persia war from `ws.wars`
- Required Levantia's inclusion as a belligerent ally (handled by including levantia in signatories)
- Did NOT address the nuclear question (deferred — realistic)
- Created a SEPARATE frozen conflict (Persia nuclear capability preserved in ambiguity)

**Design insight:** The SIM naturally produces multiple overlapping peace processes with different timelines and different levels of resolution. This is realistic. The engine handles parallel ceasefires correctly because each agreement independently scans `ws.wars` for matching belligerents.

## E. KEY METRICS ACROSS 8 ROUNDS

### Sarmatia
| Round | GDP | Stability | Support | Treasury | Territory |
|-------|-----|-----------|---------|----------|-----------|
| 1 | 20.15 | 4.90 | 54% | 0 | ~40% |
| 2 | 20.3 | 4.80 | 53% | 0 | ~41% |
| 3 | 20.4 | 4.65 | 51% | 0 | ~42% |
| 4 | 20.2 | 4.50 | 49% | 0 | ~40% (lost ruthenia_14) |
| 5 | 20.0 | 4.35 | 47% | 0 | ~38% (lost ruthenia_18) |
| 6 | 19.8 | 4.25 | 45% | 0 | ~38% |
| 7 | 20.5 | 5.10 | 52% | 1 | ~38% (frozen) |
| 8 | 21.5 | 5.30 | 54% | 3 | ~38% (frozen) |

**Pattern:** Slow decline forced the deal. The peace dividend is real but modest. The fundamental economic problem (sanctions, dependency on Cathay) is only partially resolved.

### Ruthenia
| Round | GDP | Stability | Support | Leader | Territory |
|-------|-----|-----------|---------|--------|-----------|
| 1 | 2.25 | 4.62 | 50% | Beacon | ~60% |
| 2 | 2.30 | 4.45 | 48% | Beacon | ~59% |
| 3 | 2.35 | 4.20 | 43% | Beacon (lost R1) | ~58% |
| 4 | 2.40 | 4.35 | 55% | Bulwark | ~60% (recovered) |
| 5 | 2.50 | 4.50 | 58% | Bulwark | ~62% |
| 6 | 2.55 | 4.60 | 60% | Bulwark | ~62% |
| 7 | 2.65 | 5.30 | 63% | Bulwark | ~62% (frozen) |
| 8 | 2.80 | 5.55 | 61% | Bulwark | ~62% (frozen) |

**Pattern:** Election was the turning point. Bulwark's military competence + willingness to negotiate produced better outcomes than Beacon's rigidity. EU membership track is the structural win that outlasts the ceasefire terms.

## F. VERDICT

### Ceasefire Mechanic: FUNCTIONAL BUT INCOMPLETE
The core transaction works. The engine correctly removes wars, logs events, and stops combat. But the post-ceasefire mechanics (violations, territory freeze, sanctions schedule, ally coverage) are absent. These must be built before Detailed Design.

### Negotiation Realism: HIGH
The 7-round arc, with elections, back-channels, creative formulas, and institutional workarounds, produced dynamics that mirror real peace processes. The roles — Dealer as self-interested mediator, Compass as fixer, Lumiere as creative diplomat, Bulwark as pragmatic successor — all functioned as designed.

### Design Intent Validated:
- Peace IS possible but DIFFICULT — requires 7 rounds of pressure, an election, and favorable conditions.
- The terms are inherently unstable — frozen conflict, not resolution.
- Both sides can claim victory (Pathfinder: territory + NATO moratorium; Bulwark: ceasefire + EU track).
- The gap between the deal's promises and its enforcement capacity is a feature, not a bug — it creates the basis for future SIM scenarios.

### Recommended Next Steps:
1. Implement breach/violation mechanic (Priority 1).
2. Implement territory freeze enforcement (Priority 1).
3. Run Test 5 with HOSTILE Sarmatia (no setup override) to verify that the war can also NOT end — confirming the ceasefire is earned, not inevitable.
4. Run breach scenario: what happens when Sarmatia violates the DMZ in R8+? Does the snap-back work?

---

*Test completed. 8 rounds processed. Ceasefire achieved Round 7. 9 design holes identified. 3 Priority 1 fixes required.*
