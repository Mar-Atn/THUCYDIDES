# SEED GATE — Test Scenarios (Merged)
## Team Scenarios + Tester Scenarios = 12 Comprehensive Tests
**Date:** 2026-03-30

---

## Merge Logic

Team proposed 8 scenarios. Tester proposed 10 (G1-G10). After deduplication:
- Team S1 (Baseline) = Tester G6 → **MERGED as T1**
- Team S2 (Formosa) covers Tester G1 (Combat) + G2 (Blockade) → **MERGED as T2**
- Team S3 (Sanctions) = Tester G7 → **MERGED as T3**
- Team S4 (Nuclear) = Tester G3 → **MERGED as T4**
- Team S5 (Economic) = new, no tester equivalent → **T5**
- Team S6 (Political) = Tester G5 → **MERGED as T6**
- Team S7 (Covert) = Tester G4 → **MERGED as T7**
- Team S8 (Ruthenia) = Tester G8 (Militia) → **MERGED as T8**
- Tester G9 (Role Engagement) = unique → **T9**
- Tester G10 (Timing) = unique → **T10**

Plus 2 additional cross-cutting tests:
- **T11: CONSISTENCY CHECK** (automated CSV + formula validation)
- **T12: FULL STRESS** (everything breaks at once — Formosa + nuclear + oil + political crisis simultaneously)

**Total: 12 tests, 8 rounds each (except T10 at 4 rounds, T11 automated)**

---

## T1: BASELINE — "Let the world run" (8 rounds)
**Source:** Team S1 + Tester G6

**Setup:** No tweaks. All 37 roles as independent AI agents. Standard starting data. v4 engine with all fixes.

**Watch for:**
- Credible geopolitical narrative over 8 rounds
- Structural clocks: Sarmatia economic decline, Columbia election (R2, R5), Cathay naval crossover
- Oil price trajectory ($137 R1 with inertia → ?)
- Stability: Ruthenia >2.5 R8, Sarmatia >3.0 R8 (with siege resilience)
- Elections firing correctly at R2, R3-4, R5
- Gap ratio closing (0.68 → ?)
- At least 1 ceasefire attempt
- ALL 31 action types available and functional

**Agents:** 37 independent (1 per role)

---

## T2: FORMOSA CRISIS — "Cathay goes for it at R4" (8 rounds)
**Source:** Team S2 + Tester G1 (Combat) + G2 (Blockade)

**Setup:** Cathay AI instructed to attempt Formosa blockade at R4. Helmsman urgency 0.9. All other countries play naturally.

**Watch for:**
- **Revised combat mechanics:** Ground attack with simplified modifiers, dice-based resolution
- **Amphibious assault:** -1 modifier + Die Hard + air support. Is invasion realistically hard?
- **Blockade:** Ground-forces-only for Gulf Gate, partial/full for Formosa (3-zone encirclement)
- **5-level OPEC:** Does oil respond to Formosa crisis?
- **Semiconductor disruption:** Ramping severity 0.3→1.0. GDP cascade on dependent countries.
- **Naval crossover:** When does Cathay achieve superiority? Does Columbia redeploy?
- **Coalition response:** Do allies mobilize?

**Agents:** 37 independent

---

## T3: SANCTIONS STRESS — "Maximum pressure on Sarmatia" (8 rounds)
**Source:** Team S3 + Tester G7

**Setup:** Western coalition at L3 sanctions from R1. Focus on economic warfare dynamics.

**Watch for:**
- **S-curve formula:** Does 60% coalition coverage threshold work? Below 60% → 30% effectiveness?
- **Adaptation after 4 rounds:** Does sanctions damage diminish (0.60 adaptation factor)?
- **Imposer cost:** Does Teutonia feel the pain of sanctioning a trade partner?
- **Cathay lifeline:** Does Cathay become Sarmatia's economic support? At what cost?
- **Swing states:** Do Bharata, Phrygia face realistic pressure to choose sides?
- **Sarmatia economic clock:** Treasury depletion timeline. Money printing → inflation → crisis state cascade.
- **Dollar credibility:** Any BRICS+ currency dynamics?

**Agents:** 37 independent

---

## T4: NUCLEAR ESCALATION — "Persia reaches L1" (8 rounds)
**Source:** Team S4 + Tester G3

**Setup:** Persia AI prioritizes nuclear R&D. Accelerated investment. Test the full 5-tier nuclear system.

**Watch for:**
- **5-tier nuclear system:** L0→L1 progression, test (subsurface), conventional missile use, nuclear threat
- **10-minute authorization clock:** Does it create decision pressure?
- **10-minute flight time:** Interception window mechanics
- **Detection tiers:** Who knows what about Persia's program? Intelligence accuracy.
- **Global stability shock:** When nuclear test happens, how does world react?
- **Deterrence logic:** Do AI agents rationally avoid nuclear exchange?
- **Authorization chain:** Furnace alone (no restrictions in Persia) vs Columbia (HoS + military + 1)

**Agents:** 37 independent

---

## T5: ECONOMIC WARFARE — "Oil shock + tariff war" (8 rounds)
**Source:** Team S5 (unique)

**Setup:** Wellspring sets OPEC to MIN from R1. Columbia sets L3 tariffs on Cathay. Cathay retaliates. Maximum economic stress.

**Watch for:**
- **5-level oil production:** MIN vs MAX. Does the formula produce credible $200+ spike?
- **Per-sector tariffs:** Cathay targeting Columbia tech, Columbia targeting Cathay industry. Does granularity matter?
- **Bilateral trade damage:** Both sides hurt. Asymmetric impact based on trade dependence.
- **Oil demand destruction:** At $200+ oil, does GDP contraction reduce demand → price moderation?
- **Inflation cascading:** Oil + tariffs + sanctions → compound inflation for importers
- **Financial crisis triggers:** Do any major economies enter "stressed" or "crisis" state from economic warfare alone?
- **BRICS+ currency:** Does economic pressure drive petroyuan adoption?

**Agents:** 37 independent

---

## T6: POLITICAL CRISIS — "Columbia implodes" (8 rounds)
**Source:** Team S6 + Tester G5

**Setup:** Dealer plays aggressively — arrests Tribune, fires Shield, declares emergency. Columbia opposition activated.

**Watch for:**
- **Impeachment mechanic:** Tribune files, Parliament votes, does it succeed?
- **Court (AI judge):** Does the democratic court system work for contested actions?
- **Parliament majority dynamics:** Midterm R2 flips Seat 5. Budget blocked by opposition.
- **Election formula:** 50/50 AI+player. Does it respond to crisis conditions?
- **Propaganda diminishing returns:** Does repeated propaganda become less effective?
- **Arrest/fire cascade:** When Dealer arrests Tribune, what happens to opposition? Rally effect?
- **Succession:** If impeachment succeeds, Volt becomes president. Policy shift.
- **Protest mechanic:** Auto-protest at low stability + stimulated protest by opposition.

**Agents:** 37 independent

---

## T7: COVERT OPERATIONS — "Shadow war" (8 rounds)
**Source:** Team S7 + Tester G4

**Setup:** Columbia and Sarmatia intelligence services go all-out covert. All intelligence cards used. Maximum covert activity.

**Watch for:**
- **Per-individual intelligence pools:** Shadow (8 intel + 3 sabotage + 3 cyber). Correct depletion?
- **Intelligence accuracy tiers:** Does quality of answer depend on target difficulty + source quality?
- **Always returns answer:** Even failed intelligence gives SOMETHING (lower accuracy). Does this work?
- **Sabotage/cyber/disinformation:** Probability formulas. GDP damage. Stability impact.
- **Election meddling:** Risk/reward for interfering in Ruthenia election.
- **Card pool depletion:** After using all cards, intelligence is gone. Does this create scarcity dynamics?
- **Detection and attribution:** When ops are detected, does the target country react?
- **Cross-checking:** Can a country verify intelligence by asking multiple sources?

**Agents:** 37 independent

---

## T8: RUTHENIA SURVIVAL — "Can Ruthenia last 6 rounds?" (8 rounds)
**Source:** Team S8 + Tester G8 (Militia)

**Setup:** Focus on Ruthenia's extreme fiscal/military pressure. Test new militia mechanic.

**Watch for:**
- **Fiscal model:** Treasury 5 coins, maintenance 4.2/round, GDP 2.2. Without aid → collapse R2.
- **Aid dependency:** Columbia sends 3 coins. Is this enough? Is it gameplay (player decides amount)?
- **Mobilization pool:** 4 remaining uses. Finite. Depletes. When to use?
- **Militia/volunteer call:** New mechanic from CM-001. Can militia defend when regulars depleted?
- **Wartime election (R3-4):** Beacon vs Bulwark. Territory held, economy, casualties → formula.
- **Three-way political dynamics:** Beacon (resist), Bulwark (fight harder), Broker (negotiate).
- **Die Hard zone:** Does holding Die Hard position produce gameplay value?
- **EU peace track:** Can Broker's diplomacy produce a ceasefire before military collapse?

**Agents:** 37 independent

---

## T9: ROLE ENGAGEMENT — "Do non-HoS roles matter?" (8 rounds)
**Source:** Tester G9 (unique)

**Setup:** Standard baseline BUT with specific focus on tracking what non-HoS roles actually DO.

**Watch for:**
- **Tribune:** Can they block budget? File impeachment? Run investigation? Actual mechanical impact.
- **Challenger:** Campaign speeches. Foreign outreach. Creates commitments. Any engine effect?
- **Dawn (Persia reformist):** Reform proposals. Diplomatic meetings. Youth engagement. Mechanical weight?
- **Sage (Cathay elder):** Party meeting. Succession influence. Activation threshold. Real power?
- **Broker (Ruthenia politician):** Back-channel deals. EU track. Electoral alternative. Meaningful?
- **Volt (Columbia VP):** Succession positioning. Acting president if Dealer incapacitated. Policy shift?
- **Circuit (Cathay tech):** Tech investment decisions. Rare earth recommendations. Personal escape planning.
- **Shadow (CIA):** Intelligence briefings. Covert ops. What Dealer doesn't know. Information asymmetry.

**Key question:** After the action review gave non-HoS roles new tools (impeachment, court, protest, intelligence pools), do they now produce **at least 1 meaningful mechanical action per round**?

**Agents:** 37 independent

---

## T10: TIMING FEASIBILITY — "Can we run 8 rounds in a day?" (4 rounds)
**Source:** Tester G10 (unique)

**Setup:** Run 4 rounds with REALISTIC timing. Count every action, every transaction, every meeting. How long does Phase A take?

**Watch for:**
- **Action volume per round:** With 37 agents × 31 action types, how many actions per round?
- **Phase A duration:** Design says 45-80 min. With this action volume, is that realistic?
- **Phase B duration:** Production + deployment + world model. How long with the merged B/C phase?
- **Meeting volume:** How many bilateral meetings requested? How many can happen in 45 min?
- **Bottlenecks:** Where does the flow break? Facilitator overload? Engine processing time? Communication queue?
- **Compression:** R7-8 designed as faster (40-45 min). Is this feasible given action volume?

**Agents:** 37 independent (but tracking ALL timing metrics)

---

## T11: CONSISTENCY CHECK (automated, no agents)
**Source:** Tester pre-flight check

**Automated validation:**
- CSV cross-validation (all IDs match across 10 files)
- Formula spot-checks (D8 vs actual engine code, 10 key formulas)
- Authority chain verification (31 actions × authorization rules)
- Role powers → action mapping
- Military unit counts (deployments.csv totals vs countries.csv)
- Zone adjacency completeness
- Relationship matrix coverage (all 37 roles)

**Output:** CONSISTENCY_CHECK.md with PASS/FAIL per check

---

## T12: FULL STRESS — "Everything breaks at once" (8 rounds)
**Source:** New (Tester addition)

**Setup:** Maximum simultaneous crises:
- R1: Gulf Gate blockade active (Persia). Cathay begins Formosa encirclement.
- R2: Columbia midterms + Dealer arrests Tribune + Oil spike from dual blockade
- R3: Persia nuclear test. Ruthenia election. Cathay purge lifts.
- R4: Cathay blockades Formosa. Sarmatia offensive. Columbia impeachment.
- R5: Columbia presidential election under triple crisis. Nuclear escalation risk.
- R6-8: Resolution or collapse.

**Watch for:**
- **Can the engine handle 5+ simultaneous crises without producing absurd results?**
- **Do feedback loops compound correctly or create instability?**
- **Does the world model remain internally consistent under maximum stress?**
- **Is there a natural stabilization mechanism, or does everything spiral?**

**Agents:** 37 independent

---

## EXECUTION ORDER

1. **T11** (Consistency Check) — 30 min, automated. Must pass before running agent tests.
2. **T1** (Baseline) — the control. Everything compares to this.
3. **T2** (Formosa) + **T3** (Sanctions) + **T4** (Nuclear) — parallel, focused military/economic tests
4. **T5** (Economic) + **T6** (Political) + **T7** (Covert) — parallel, focused domain tests
5. **T8** (Ruthenia) + **T9** (Role Engagement) — parallel, gameplay tests
6. **T10** (Timing) — standalone feasibility check
7. **T12** (Full Stress) — the final crash test, runs last

**Total: 12 tests. ~90 rounds simulated. 37 agents per test (except T10, T11).**
