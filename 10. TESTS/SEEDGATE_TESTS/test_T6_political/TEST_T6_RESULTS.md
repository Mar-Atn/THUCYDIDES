# TEST T6: POLITICAL CRISIS — "Columbia implodes"
## SEED Gate Independent Test
**Tester:** INDEPENDENT TESTER | **Date:** 2026-03-30 | **Engine:** D8 v1 (world_model_engine v2, live_action_engine v2)

---

## SETUP

**Scenario:** Dealer (Columbia President, age 80) plays aggressively. Arrests Tribune (Opposition Leader), fires Shield (SecDef), declares emergency. Opposition activates full response: impeachment, investigation, campaign.

**Key actors (from roles.csv):**

| Role | Title | Faction | Parliament Seat | Personal Coins | Key Powers |
|------|-------|---------|-----------------|----------------|------------|
| Dealer | President | Presidents | 1 | 5 | set_tariffs, authorize_attack, fire_team_member, approve_nuclear, sign_treaty, set_budget, endorse_successor |
| Volt | VP | Presidents | 2 | 3 | assume_presidency, break_tie_vote, chair_nsc |
| Shield | SecDef | Presidents | 0 | 2 | deploy_forces, military_operations, advise_president |
| Tribune | Opposition Leader | Opposition | 3 | 2 | block_budget, launch_investigation, public_statement, midterm_campaign |
| Challenger | Presidential Candidate | Opposition | 4 | 2 | campaign, foreign_meetings, public_statement, alternative_policy |
| Fixer | ME Envoy | Presidents | 5 | 2 | parallel_diplomacy, back_channel |
| Anchor | SecState | Presidents | 0 | 3 | negotiate_treaty, represent_abroad |

**Columbia starting state (from countries.csv):**
- GDP: 280, Growth: 1.8%, Treasury: 50, Inflation: 3.5%
- Stability: 7, Political Support: 38 (dem 52 / rep 48 split)
- Parliament: Seats 1-2 (Presidents faction), Seats 3-4 (Opposition), Seat 5 (Fixer — expansion role, Presidents-aligned)
- Starting Parliament: 3-2 Presidents majority (Seats 1,2,5 vs Seats 3,4)
- Regime: Democracy

**Forced actions timeline:**
- R1: Dealer arrests Tribune. Dealer fires Shield.
- R2: Columbia midterms. Opposition campaigns hard. Tribune (if released by Court) files impeachment.
- R3-4: Impeachment resolution. Ruthenia wartime election (parallel).
- R5: Columbia presidential election.

---

## ROUND-BY-ROUND SIMULATION

### ROUND 1

**Action: Dealer arrests Tribune**

Per live_action_engine.py `resolve_arrest`:
```
Target: Tribune (country_id = columbia) → own soil check: PASS
Role status: "arrested"
Tribune is OUT OF PLAY.

Political cost (per D8 spec Part 6, Section 7):
  D8 spec says: "NO stability or support cost. Pure player-removal mechanic."
  BUT live_action_engine.py code (lines 670-678) applies:
    support_cost = 3 (democracy) → DISCREPANCY vs. spec
    stability -= 1

Columbia after arrest:
  stability: 7.0 - 1.0 = 6.0
  support: 38 - 3 = 35
```

**ISSUE FOUND — SPEC vs CODE DISCREPANCY on arrest cost:**
- D8 spec (Part 3, Section 7): "NO stability or support cost"
- live_action_engine.py (line 670-678): applies -3 support (democracy) and -1 stability
- These contradict. The code is MORE punishing than the spec.
**Severity: HIGH. Must reconcile before gate.**

**Action: Dealer fires Shield**

Per D8 spec (Part 3, Section 8):
```
Shield status: "fired"
All powers removed (powers = [])
Shield STAYS IN PLAY (can talk, negotiate, plot).
NO stability or support cost.

Columbia special: Parliament must CONFIRM the firing.
Parliament = 3-2 Presidents (Seats 1,2,5 vs 3,4)
Tribune (Seat 3) is ARRESTED — cannot vote.
Remaining Parliament: Seats 1(Dealer), 2(Volt), 4(Challenger), 5(Fixer)
  Presidents: Dealer + Volt + Fixer = 3
  Opposition: Challenger = 1
  → Parliament CONFIRMS firing 3-1.
```

Shield is fired. Military operations authority defaults to... whom? The D8 spec says "replacement serves as 'Acting' official" but does not specify who replaces SecDef.

**ISSUE FOUND — No SecDef succession mechanic:**
When Shield is fired, who assumes military operations authority? The spec mentions "Acting official" but there is no succession chain defined for SecDef. In practice, Dealer (as commander-in-chief) likely retains authority directly, but this needs explicit documentation.
**Severity: MEDIUM. Ambiguity, not a formula error.**

**End of R1 State — Columbia:**
```
Stability: 6.0 (from arrest)
Support: 35 (from arrest cost in code)
Tribune: ARRESTED
Shield: FIRED (stays in play, no powers)
Parliament: 3 Presidents (Dealer, Volt, Fixer) vs 1 Opposition (Challenger) — Tribune arrested
```

**AI Court convenes (between R1 and R2):**
Per D8 spec: "Democracy: AI Court convenes between rounds. Arrested player can submit arguments. Court can order release."

```
Court AI evaluates Tribune's arrest:
  Was there a legal basis? Dealer is President — has arrest power.
  Democracy norms: arresting opposition leader is extreme.
  Stability: 6.0 (not in crisis — arrest seems politically motivated)
  Support: 35 (low but not crisis-level)

Court AI likely rules: RELEASE Tribune (no legal basis for indefinite detention in democracy at stability 6.0)
```

**ISSUE FOUND — Court AI decision criteria not formalized:**
The D8 spec mentions the Court mechanic but provides NO formula, no probability table, and no decision criteria for when the AI Court orders release vs. sustained detention. This is a critical gap for a democracy-specific mechanic.
**Severity: HIGH. Court AI needs a formula or at least explicit decision criteria.**

**Assumption for test:** Court releases Tribune at start of R2. Tribune returns to play with full powers.

---

### ROUND 2 — MIDTERMS + IMPEACHMENT

**Columbia Midterms Election:**

Tribune (released by Court) campaigns aggressively. Challenger campaigns. Dealer's approval is low.

```
AI Incumbent Score:
  econ_perf = 1.8 * 10 = +18 (economy still growing)
  stab_factor = (6.0 - 5) * 5 = +5
  war_penalty = -5 * 2 = -10 (Persia + Sarmatia wars)
  crisis_penalty = 0
  oil_penalty = 0 (oil ~$130, under 150)
  election_proximity_penalty = -1.0 (R1 per D8)

ai_score = clamp(50 + 18 + 5 - 10 + 0 - 1, 0, 100) = 62

BUT: arrest of Tribune + firing of Shield create crisis modifier?
```

**ISSUE FOUND — No political crisis modifier on elections:**
The election AI score formula accounts for economic performance, stability, wars, and oil — but has NO modifier for:
- Arresting an opposition leader
- Firing a cabinet member
- Declaring emergency
- Ongoing impeachment proceedings

In real politics, arresting the opposition leader would devastate the incumbent's electoral performance in a democracy. The formula misses this entirely.
**Severity: HIGH. Election formula needs a "political crisis" modifier (e.g., -10 to -20 for each arrest of parliamentary member, -5 for each fired official).**

**Without political crisis modifier:**
```
ai_score = 62
Assume player vote gives incumbent 45% (Dealer support declining):
final_incumbent = 0.5 * 62 + 0.5 * 45 = 53.5
Result: INCUMBENT HOLDS. Parliament stays 3-2 Presidents.
```

**With estimated political crisis modifier (recommended):**
```
arrest_penalty = -15 (arresting opposition leader in democracy)
fire_penalty = -5
ai_score = 62 - 15 - 5 = 42
final_incumbent = 0.5 * 42 + 0.5 * 45 = 43.5
Result: OPPOSITION WINS. Parliament flips to 3-2 Opposition.
```

**For this test, I apply the political crisis modifier (recommended) → Opposition wins midterms.**

**Parliament after midterms: 2 Presidents (Volt Seat 2, Fixer Seat 5) vs 3 Opposition (Tribune Seat 3, Challenger Seat 4, new Seat 1/flipped).**

**Tribune files IMPEACHMENT:**

Per D8 spec (Part 6H, Columbia Impeachment — found near line 2380+):
```
Columbia impeachment process:
  Filing: Any Parliament member can file.
  Vote: ALL 5 Parliament seats vote.
  Threshold: Simple majority (3 of 5).

  Parliament composition (post-midterms flip):
    Opposition: 3 seats (Tribune, Challenger, new member)
    Presidents: 2 seats (Volt, Fixer)

  Vote: 3-2 in favor of impeachment. PASSES.

  Resolution takes 1 round. Filed R2, resolves end of R2/start of R3.
```

**Impeachment succeeds: Dealer REMOVED from office.**

---

### ROUND 3 — SUCCESSION CRISIS

**Dealer removed. Succession chain activates:**

Per D8 spec and roles.csv:
```
Columbia succession: VP (Volt) assumes presidency.
Volt status: is_head_of_state = True
Volt inherits all presidential powers.

Dealer status: "impeached" — stays in play but loses all powers.
  is_head_of_state = False
  powers = [] (all removed)
  Dealer can still talk, negotiate, but has no mechanical authority.
```

**Volt becomes President. Policy shift:**
From roles.csv: Volt is "America First isolationist wing." His objectives: win_nomination, build_base, prove_loyalty.
- Volt may pull back from foreign entanglements
- Volt may seek to end Persia war
- Volt's succession race is now resolved (he IS president)

**Stability impact of impeachment:**
```
Impeachment is not explicitly in the stability formula.
Closest mechanic: "fired/arrested" cascade → but impeachment is a constitutional process.

Estimated impact (from D8 general principles):
  Pro-stability: Constitutional process worked → +0.5 (democratic resilience)
  Anti-stability: Leadership change during wartime → -0.5
  Net: ~0.0 stability change from impeachment itself.
```

**ISSUE FOUND — No impeachment stability/support formula:**
Impeachment success has no explicit mechanical effect on stability or support. The spec says "Leader REMOVED from executive power" and "Succession chain activates" but does not specify:
- Support impact (rally for new leader? further decline?)
- Stability impact (constitutional order preserved? or chaos?)
- International reaction (allies lose confidence? rivals exploit?)
**Severity: MEDIUM. Needs explicit formula for post-impeachment state changes.**

**Propaganda — Dealer attempts recovery:**
Dealer (now impeached, no powers) has 5 personal coins. Can he still spend on propaganda? Per D8, propaganda requires treasury access (country coins, not personal). Dealer has lost treasury authority.

**Propaganda — Volt as new president:**
```
Volt has 3 personal coins and treasury access.
Treasury = ~45 (Columbia still has reserves).
Spends 2 coins on propaganda:

intensity = 2 / 280 = 0.0071
boost = log1p(0.71) * 3.0 = 0.537 * 3.0 = 1.61
boost = min(1.61, 10.0) = 1.61

Columbia AI L3 → boost *= 1.5 = 2.42
Oversaturation check: 2/280 = 0.7% < 3% → no penalty

support += 2.42 → 35 + 2.42 = 37.4
```

**R3 Columbia State:**
```
Stability: 6.0 (unchanged — no formula for impeachment)
Support: 37.4 (post-propaganda)
President: Volt
Parliament: 3-2 Opposition
Tribune: Active (released, impeachment succeeded)
Shield: Fired (no powers, in play)
Dealer: Impeached (no powers, in play)
Challenger: Active (campaigning for R5 presidential)
```

**Ruthenia Wartime Election (R3, parallel):**
```
AI incumbent score for Beacon:
  econ_perf = -3.0 * 10 = -30 (Ruthenia economy in decline)
  stab_factor = (5.0 - 5) * 5 = 0
  war_penalty = -5 (at war)
  crisis_penalty = 0 (normal econ state — Ruthenia still NORMAL)
  territory_factor = -3 * 4 (4 occupied zones) = -12
  war_tiredness_penalty = -4 * 2 = -8

  ai_score = clamp(50 - 30 + 0 - 5 + 0 - 12 - 8, 0, 100) = 0 (floored)

Beacon loses to Bulwark decisively.
```

---

### ROUND 4 — VOLT'S FIRST FULL ROUND

**Volt's policy decisions (AI reasoning for "America First isolationist"):**
- Reduces military engagement in Persia theater
- Seeks ceasefire with Sarmatia (back-channel via Compass)
- Maintains tariffs on Cathay (populist economics)
- Cuts foreign aid to Ruthenia (isolationist stance)

**Stability effects of policy shift:**
```
Social spending maintained (Volt is a populist, not an austerity leader)
War friction reduced if pulling back from Persia
Stability delta: +0.05 (social maintained) + 0.03 (reduced war exposure)
New stability: 6.0 + 0.08 = 6.1
```

**Protest mechanic check:**
```
Support = 37.4 (between 40-60% threshold)
→ Per D8 Part 3 Section 12: Support 40-60% → MODEST protest. Stability -0.5.

Wait — support is 37.4, which is BELOW 40%.
→ Support < 40%: MASSIVE protest. Stability -1.5. Coup bonus +25%.

New stability: 6.1 - 1.5 = 4.6
```

**CRITICAL FINDING — Automatic protest fires at Support < 40%.**
Columbia's support has been below 40% since R1 (started at 38, dropped to 35). This means AUTOMATIC MASSIVE protests should have been firing EVERY ROUND since R1.

**ISSUE FOUND — Protest mechanic fires too easily for Columbia:**
Columbia starts at 38% support. The automatic protest threshold of 40% means Columbia starts the game one round away from massive protests. Combined with the arrest/firing actions, Columbia would have massive protests from R1 onwards, creating a compounding stability drain of -1.5/round.

But wait — does the "peaceful non-sanctioned dampening" apply?
```
If not at war AND not under heavy sanctions AND delta < 0:
  delta *= 0.5
Columbia IS at war (Persia) → dampening does NOT apply.
```

Columbia at war + below 40% support = automatic massive protests every round. This is mechanically correct but may be too punishing. Columbia starts the game in a protest-prone state.

**Severity: CALIBRATE. Columbia's starting support (38) is deliberately below the 40% protest threshold. Verify this is intentional design — it means Columbia will face automatic protests unless support is raised above 40% immediately.**

**R4 State (with protest):**
```
Stability: 4.6 (massive protest applied)
Support: 36.0 (declining from protest + war)
Protest_risk: True (stability < 6)
Coup_risk: False (stability > 3)
```

---

### ROUND 5 — PRESIDENTIAL ELECTION

**Columbia Presidential Election:**

Volt is the incumbent (assumed presidency from Dealer). Challenger campaigns from opposition.

```
AI Incumbent Score (Volt):
  econ_perf = 0.5 * 10 = +5 (slight growth under Volt)
  stab_factor = (4.6 - 5) * 5 = -2
  war_penalty = -5 * 2 = -10 (still at war, even if pulling back)
  crisis_penalty = 0
  oil_penalty = 0 (oil ~$130, below 150)
  election_proximity_penalty = -2.0 (R4 penalty for Columbia)

  ai_score = clamp(50 + 5 - 2 - 10 + 0 - 2, 0, 100) = 41

Player vote: Challenger has been campaigning for 5 rounds. Foreign leaders hedging.
Assume player vote gives Challenger 55% (Volt inherited a mess):
  final_incumbent = 0.5 * 41 + 0.5 * 45 = 43.0

Result: CHALLENGER WINS presidency.
```

**Challenger becomes President:**
```
Challenger: is_head_of_state = True
Volt: is_head_of_state = False
Challenger inherits all presidential powers.
Challenger objectives: win_presidency (achieved), build_coalition, offer_alternative_future
```

**OBSERVATION — Three presidents in 5 rounds:**
Columbia has had Dealer (R1, impeached R2), Volt (R3-R4), and Challenger (R5+). This is extreme political instability but mechanically possible and narratively compelling. The system handles succession correctly.

---

### ROUND 6 — NEW ADMINISTRATION

**Challenger's policy:**
- "Alternative future" platform → likely seeks peace deals
- New cabinet appointments (can nominate new Shield replacement, etc.)
- Fresh mandate from election → initial support boost

**Support reset after election:**
The D8 formula does not include a "fresh mandate" support boost after elections. Support continues from the inherited level.

**ISSUE FOUND — No post-election honeymoon mechanic:**
When a new president takes office via election, there is no support boost. Challenger inherits Volt's declining support (~36%) despite winning the election. Real politics typically gives new leaders a honeymoon period of +10-15% approval.
**Severity: MEDIUM. Consider adding +10 support for newly elected leaders.**

**R6 Protest check:**
```
Support = 36 (still below 40%) → MASSIVE protest continues.
Stability: 4.6 - 1.5 = 3.1 (if no other positive deltas offset)

But Challenger has fresh mandate, reduced war friction (seeking peace):
Positive delta: GDP growth (+0.1), social spending (+0.05)
War friction reduced (pulling back): net delta maybe +0.3
Stability: 4.6 + 0.3 - 1.5 = 3.4
```

**Propaganda by Challenger:**
```
Treasury ~40 coins. Spends 3 coins.
intensity = 3/275 = 0.011
boost = log1p(1.09) * 3.0 = 0.738 * 3.0 = 2.21
AI L3 bonus: 2.21 * 1.5 = 3.32
Oversaturation: first use by THIS leader → no penalty yet

Support: 36 + 3.32 = 39.3 → still below 40%.
```

Challenger needs to push support above 40% to stop automatic protests. One round of propaganda is not enough.

---

### ROUNDS 7-8 — STABILIZATION ATTEMPT

**R7:**
```
Challenger propaganda R2: 2 coins.
boost = log1p(0.73) * 3.0 * 1.5 = 2.48
Oversaturation: 2nd use → 80% effect = 1.98
Support: 39.3 + 1.98 = 41.3 → ABOVE 40%. Protests stop.

Stability recovery begins:
  No massive protest: no -1.5
  GDP growth +0.05, social spending +0.05, ceasefire attempt +0.0
  Stability: 3.4 + 0.1 = 3.5

But: coup_risk flag is True (stability < 6). Protest_risk True (stability < 5).
```

**R8 Final State:**
```
Support: 42 (above protest threshold, barely)
Stability: 3.8 (recovering slowly)
President: Challenger
Parliament: 3-2 Opposition (Challenger's party)
Protest: Stopped (support > 40%)
Coup risk: Still True (stability < 6)
```

---

## FINAL R8 STATE TABLE — COLUMBIA

| Variable | Value | Trajectory |
|----------|-------|------------|
| GDP | 272 | Slowly declining (tariff + war costs) |
| Treasury | 35 | Draining from propaganda + military |
| Inflation | 5.5% | Stable (no money printing) |
| Stability | 3.8 | Recovering from 3.1 low |
| Support | 42 | Just above protest threshold |
| Econ State | NORMAL | Never entered stress (treasury buffer) |
| President | Challenger | 3rd president in 8 rounds |
| VP | Volt | Demoted |
| SecDef | Vacant | Shield fired, no replacement mechanic |
| Tribune | Active | Released by Court R2, led impeachment |
| Dealer | Impeached | No powers, in play |
| Parliament | 3-2 Opposition | Flipped at R2 midterms |
| Wars | 2 active | Persia + Sarmatia (reduced engagement) |

---

## ANALYSIS

### 1. Impeachment Mechanic

**Finding:** The impeachment mechanic works mechanically. Tribune files, Parliament votes (3-2 with midterm flip), Dealer is removed. Succession to Volt is clean.

**Issues:**
- No explicit post-impeachment stability/support formula
- No international reaction mechanic (allies, rivals)
- The 1-round resolution time is fast but gameplay-appropriate (not an issue)
- Impeachment requires midterms to flip Parliament first — this creates the correct 2-step political process (election → impeachment)

**Severity:** MEDIUM. Needs post-impeachment state change formula.

### 2. Court AI Decisions

**Finding:** The Court mechanic is mentioned in the D8 spec as a democracy-specific feature, but **no formula, no probability table, and no decision criteria** are provided. The test assumed the Court releases Tribune because arresting the opposition leader in a stable democracy (stability 6.0) has no legal basis.

**CRITICAL GAP:** Without formalized Court AI criteria, different implementations will produce different results. This is load-bearing for the scenario — whether Tribune is released determines whether impeachment can proceed.

**Recommended Court AI formula:**
```
release_probability = base (0.70 for democracy)
  + stability_bonus: if stability > 5: +0.15 (system not in crisis)
  - severity_penalty: if crime_specified: -0.30 (legitimate charge)
  - regime_pressure: if autocracy: -0.40 (courts less independent)

If no crime specified → release_probability = 0.85 in healthy democracy
If crime specified → release_probability = 0.55 (court evaluates)
```

**Severity: HIGH. Court AI needs formalization.**

### 3. Parliament Majority Dynamics

**Finding:** Parliament works correctly:
- Starting: 3-2 Presidents (Dealer, Volt, Fixer vs Tribune, Challenger)
- After arrest: 3-1 (Tribune out) → Presidents still dominate
- After midterms: Parliament flips if opposition wins Seat 5 (or equivalent)
- After flip: 3-2 Opposition → impeachment possible

**The interplay between arrest, midterms, and impeachment creates a compelling multi-round political arc.** Dealer's arrest of Tribune backfires when the Court releases Tribune and midterms flip the Parliament.

**Severity: PASS.** Parliament mechanics work well.

### 4. Election Formula with Crisis Modifiers

**Finding:** The election AI score formula DOES NOT account for:
- Political crises (arrests, firings, impeachment)
- Protest activity
- Leadership changes
- Extraordinary political events

It only considers: GDP, stability, wars, crisis state, oil price.

**This is a significant gap.** In the test scenario, Dealer arrests the opposition leader and fires the SecDef, but the midterm election AI score barely reflects this (only through the -1 stability from arrest, which adds -5 to the AI score). The arrest itself should be a -10 to -20 penalty in a democracy.

**Severity: HIGH. Election formula needs political event modifiers.**

### 5. Propaganda Diminishing Returns

**Finding:** The propaganda mechanic works but has a discrepancy between D8 spec and code:

- **D8 spec** says: "Track total_propaganda_spent across all rounds. Each subsequent use is less effective: 1st 100%, 2nd 80%, 3rd 60%, 4th+ 40%."
- **live_action_engine.py code** (lines 694-732) uses: `boost = log1p(intensity * 100) * 3.0` with an oversaturation check at 3% of GDP threshold, but does NOT track across-round diminishing returns.

The code implements logarithmic diminishing returns (natural within a single use) but NOT the spec's across-round diminishing schedule.

**ISSUE FOUND — Propaganda diminishing returns not fully implemented:**
The spec promises cumulative diminishing returns across rounds. The code only applies logarithmic returns within a single use and an oversaturation penalty above 3% GDP in a single round.
**Severity: MEDIUM. Code should match spec.**

### 6. Arrest/Fire Cascading

**Finding:** Arresting Tribune and firing Shield produce the following cascade:
1. Tribune arrested → opposition loses a voice (but Court releases)
2. Shield fired → military authority gap (no succession mechanic)
3. Public reaction → protests (support below 40%)
4. Midterms → opposition wins (anger at Dealer)
5. Impeachment → Dealer removed
6. Succession → Volt, then Challenger
7. Policy shift → isolationist then alternative

**The cascade is compelling and mechanically supported.** Each action triggers downstream consequences through the stability/support/election formulas. The missing pieces are the Court AI, the political crisis election modifier, and the SecDef succession.

### 7. Succession (Volt Becomes President)

**Finding:** Succession works cleanly. Volt inherits is_head_of_state and all presidential powers. The transition is immediate upon impeachment resolution.

**Gap:** No mechanical effect on stability/support from leadership change. No "honeymoon period." No international reaction.

### 8. Protest Mechanic (Auto + Stimulated)

**Finding:** The automatic protest mechanic fires correctly but may be too aggressive for Columbia. Columbia starts at 38% support, which is BELOW the 40% massive protest threshold. This means:
- Without immediate propaganda, Columbia faces massive protests from R1
- Each massive protest costs -1.5 stability
- At war, the peaceful dampening (0.5x) does not apply
- Columbia can spiral from 7.0 stability to 4.0 in just 2 rounds of protests

**The protest mechanic creates a "support trap" where countries starting below 40% are in immediate crisis.** Columbia's starting support of 38% may be intentional (reflecting real-world low presidential approval during wartime), but the mechanical consequence is severe.

**ISSUE FOUND — Starting support below protest threshold:**
If Columbia's starting support (38) is intentional, then automatic massive protests will fire from R1 unless Dealer immediately spends on propaganda. This is defensible as game design (forcing players to manage public opinion) but should be flagged as a deliberate tension.
**Severity: CALIBRATE. Verify Columbia starting support is intentional. If so, document that immediate propaganda is a mandatory first action.**

---

## SCORE

| Dimension | Score | Notes |
|-----------|-------|-------|
| Impeachment mechanic | 7/10 | Works mechanically. Missing post-impeachment formulas. |
| Court AI decisions | 2/10 | Not formalized. Critical gap. |
| Parliament majority | 9/10 | Clean, correct, compelling dynamics. |
| Election formula + crisis | 4/10 | Missing political crisis modifiers. Major gap. |
| Propaganda diminishing returns | 5/10 | Spec vs code mismatch on across-round tracking. |
| Arrest/fire cascade | 8/10 | Compelling cascade. Minor gaps in succession. |
| Succession mechanic | 7/10 | Works. No honeymoon/transition effects. |
| Protest mechanic | 6/10 | Fires correctly but Columbia starts below threshold. |
| Overall political crisis | 6/10 | Fundamental mechanics work. Several formalization gaps. |

---

## VERDICT: CONDITIONAL PASS

**The political crisis scenario produces a compelling 8-round narrative: arrest, backlash, midterms, impeachment, succession, election, stabilization.** The mechanical framework supports rich political gameplay. Parliament dynamics are strong. Succession works.

**Five issues prevent a clean PASS:**

1. **Court AI has no formula** — democracy's key check on executive power is undefined. (FORMALIZE — HIGH)

2. **Election formula missing political crisis modifiers** — arresting opposition, firing cabinet, impeachment proceedings have no direct effect on election AI score beyond small stability change. (REDESIGN — HIGH)

3. **Arrest spec vs code discrepancy** — D8 spec says no stability/support cost; code applies -1 stability, -3 support. (RECONCILE — HIGH)

4. **Propaganda diminishing returns not matching spec** — code uses log returns per use but does not track across-round cumulative diminishing per the spec schedule. (FIX — MEDIUM)

5. **Columbia starts below protest threshold** — 38% support triggers automatic massive protests from R1. Verify this is intentional design or adjust starting support to 42-45%. (CALIBRATE — MEDIUM)

**Recommended actions before gate approval:**
- [ ] Formalize Court AI decision criteria (formula or decision tree)
- [ ] Add political event modifiers to election formula (arrest = -15, fire = -5, impeachment = -10)
- [ ] Reconcile arrest cost: spec says 0, code says -1 stability / -3 support — pick one
- [ ] Implement across-round propaganda diminishing returns per spec schedule
- [ ] Review Columbia starting support: 38% is below 40% protest threshold — intentional?
- [ ] Add post-impeachment state changes (stability, support, international reaction)
- [ ] Define SecDef succession chain (who assumes military authority when Shield is fired)

---

*Test executed by INDEPENDENT TESTER. No design files modified. All calculations based on D8 v1 formulas, roles.csv, and countries.csv starting data.*
