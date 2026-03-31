# TEST T7: COVERT OPERATIONS — "Shadow war"
## SEED Gate Independent Test
**Tester:** INDEPENDENT TESTER | **Date:** 2026-03-30 | **Engine:** D8 v1 (world_model_engine v2, live_action_engine v2)

---

## SETUP

**Scenario:** Columbia and Sarmatia intelligence services go all-out covert. Every intelligence card used. Maximum covert activity from both sides across 8 rounds.

**Key intelligence actors (from roles.csv):**

### Columbia Intelligence Assets

| Role | Intel Pool | Sabotage | Cyber | Disinfo | Election Meddling | Assassination |
|------|-----------|----------|-------|---------|-------------------|---------------|
| Shadow (CIA Director) | 8 | 3 | 3 | 3 | 1 | 1 |
| Dealer (President) | 4 | 1 | 1 | 1 | 1 | 1 |
| Shield (SecDef) | 3 | 1 | 1 | 0 | 0 | 0 |
| Anchor (SecState) | 3 | 0 | 0 | 1 | 1 | 0 |
| Fixer (ME Envoy) | 3 | 1 | 1 | 1 | 1 | 0 |
| Pioneer (Tech Envoy) | 2 | 0 | 1 | 0 | 0 | 0 |
| Volt (VP) | 2 | 0 | 0 | 0 | 0 | 0 |
| Tribune (Opposition) | 1 | 0 | 0 | 1 | 0 | 0 |
| Challenger (Candidate) | 1 | 0 | 0 | 1 | 0 | 0 |
| **COLUMBIA TOTAL** | **27** | **6** | **7** | **8** | **4** | **2** |

### Sarmatia Intelligence Assets

| Role | Intel Pool | Sabotage | Cyber | Disinfo | Election Meddling | Assassination |
|------|-----------|----------|-------|---------|-------------------|---------------|
| Pathfinder (President) | 4 | 1 | 1 | 1 | 1 | 1 |
| Ironhand (General) | 3 | 1 | 1 | 0 | 0 | 0 |
| Compass (Oligarch) | 2 | 0 | 0 | 0 | 0 | 0 |
| Ledger (PM) | 2 | 0 | 0 | 0 | 0 | 0 |
| **SARMATIA TOTAL** | **11** | **2** | **2** | **1** | **1** | **1** |

### Covert Operation Constraints

| Parameter | Value | Source |
|-----------|-------|--------|
| Max ops per round (intelligence power) | 3 | live_action_engine.py:51-54 |
| Max ops per round (default) | 2 | live_action_engine.py:51-54 |
| Intelligence powers | columbia, cathay, levantia, albion, sarmatia | live_action_engine.py:48 |

**Both Columbia and Sarmatia are intelligence powers → 3 covert ops per round per country.**

---

## CRITICAL PRE-TEST FINDING: POOL SYSTEM DISCREPANCY

**D8 Spec (Part 3, Section 6A):** Intelligence pools are PER-INDIVIDUAL ROLE. Shadow has 8 requests. Dealer has 4. Each role depletes independently.

**live_action_engine.py (lines 524-621):** Covert ops are limited PER COUNTRY PER ROUND (3 for intelligence powers). There is NO per-individual pool tracking. The code tracks `covert_ops_this_round[country]` — a country-level counter.

**ISSUE FOUND — Per-individual pool NOT implemented in engine code:**
The D8 spec defines intelligence as a per-individual resource. The engine code implements a per-country-per-round limit. These are fundamentally different systems:
- D8 spec: Shadow can use 8 intelligence requests across the whole game, Dealer can use 4, independently
- Engine code: Columbia can do 3 covert ops per round total, regardless of which individual submits

This means:
1. Individual pool depletion is NOT tracked
2. Shadow's 8-request pool has no mechanical meaning in the code
3. The scarcity mechanic (running out of intelligence) does not exist at the code level

**Severity: HIGH. The intelligence pool system described in D8 is not implemented. The engine uses a simpler per-country-per-round system.**

**For this test:** I will simulate using the D8 SPEC system (per-individual pools) to test the DESIGN, and note where the engine code diverges.

---

## ROUND-BY-ROUND SIMULATION

### ROUND 1 — Opening Salvo

**Columbia Actions (3 ops max per round at country level / individual pools):**

1. **Shadow: Espionage vs Sarmatia (intel request 1 of 8)**
   Target: Sarmatia military deployments (hard fact)
   ```
   base_prob = 0.60 (espionage)
   ai_level = 3 (Columbia) → +0.15
   intelligence_power bonus: +0.05
   repeated_ops_penalty: 0 (first op)
   prob = 0.60 + 0.15 + 0.05 = 0.80

   Roll: 0.35 < 0.80 → SUCCESS

   Detection:
   detect_base = 0.30 (espionage)
   detect_prob = 0.30 + 0 = 0.30
   Roll: 0.65 > 0.30 → NOT DETECTED

   Intelligence returned (with noise 0.85-1.15):
     Ground: 18 * 1.05 = 19 (actual: 18) — close
     Naval: 2 * 0.92 = 2 (actual: 2) — accurate
     Missiles: 12 * 1.10 = 13 (actual: 12) — close
     Stability: 5.0 * 0.88 = 4.4 (actual: 5.0) — slightly off
     Nuclear level: 3 (actual: 3) — exact (no noise on level)
   ```
   **Result:** Accurate military picture. Hard facts at ~90% accuracy per spec.

2. **Shadow: Sabotage vs Sarmatia (sabotage card 1 of 3)**
   Target: Economic target
   ```
   base_prob = 0.45 (sabotage)
   ai_level = 3 → +0.15
   intelligence_power: +0.05
   prob = 0.45 + 0.15 + 0.05 = 0.65

   Roll: 0.42 < 0.65 → SUCCESS

   Detection:
   detect_base = 0.40 (sabotage)
   detect_prob = 0.40 + 0 = 0.40
   Roll: 0.55 > 0.40 → NOT DETECTED

   Effect: Sarmatia GDP * 0.02 = 20 * 0.02 = 0.4 coins GDP damage
   Sarmatia GDP: 20 → 19.6
   ```

3. **Dealer: Espionage vs Cathay (intel request 1 of 4)**
   Target: Cathay's Formosa invasion timeline (strategic intention — 50-60% accuracy)
   ```
   prob = 0.60 + 0.15 + 0.05 = 0.80
   Roll: 0.22 < 0.80 → SUCCESS
   Detection: 0.30, Roll 0.78 → NOT DETECTED

   Intelligence returned:
     Hard facts: GDP 190 (noised to ~195), military counts
     Strategic intention: "Cathay preparing naval buildup near Formosa, timeline 3-4 rounds"
     Accuracy: 50-60% → this answer may or may not be correct
   ```

**Sarmatia Actions (3 ops max):**

1. **Pathfinder: Espionage vs Columbia (intel request 1 of 4)**
   Target: Columbia military deployment plans (hard fact)
   ```
   base_prob = 0.60
   ai_level = 1 (Sarmatia) → +0.05
   intelligence_power: +0.05
   prob = 0.60 + 0.05 + 0.05 = 0.70

   Roll: 0.58 < 0.70 → SUCCESS
   Detection: 0.30 + 0 = 0.30, Roll 0.25 < 0.30 → DETECTED

   Intel returned with noise:
     Ground: 22 * 0.95 = 21 (actual: 22)
     Naval: 11 * 1.08 = 12 (actual: 11)
   ```
   **Columbia detects Sarmatia espionage attempt.** Columbia now knows Sarmatia is spying.

2. **Pathfinder: Disinformation vs Ruthenia (disinfo card 1 of 1)**
   Target: Undermine Ruthenia public support for war
   ```
   base_prob = 0.55
   ai_level = 1 → +0.05
   intelligence_power: +0.05
   prob = 0.55 + 0.05 + 0.05 = 0.65

   Roll: 0.30 < 0.65 → SUCCESS
   Detection: 0.25 + 0 = 0.25, Roll 0.60 → NOT DETECTED

   Effect: Ruthenia stability -0.3, support -2 (per code) / -3 support (per D8 spec 6D)
   ```
   **ISSUE FOUND — Disinformation effect differs between spec and code:**
   - Code (line 599): stability -0.3, support -2
   - D8 spec (Section 6D): support -3%, stability -0.3
   **Severity: LOW. Minor numerical difference (2 vs 3 support).**

3. **Ironhand: Cyber vs Columbia (cyber card 1 of 2)**
   Target: Undermine military production
   ```
   base_prob = 0.50
   ai_level = 1 → +0.05
   intelligence_power: +0.05
   prob = 0.50 + 0.05 + 0.05 = 0.60

   Roll: 0.72 > 0.60 → FAILURE

   Detection: 0.35 + 0 = 0.35, Roll 0.20 < 0.35 → DETECTED
   ```
   **Failed cyber attack detected.** Columbia knows Sarmatia attempted cyber operations.

**R1 Pool Status:**

| Role | Intel Used/Total | Sabotage | Cyber | Disinfo | Elect Med | Assassin |
|------|-----------------|----------|-------|---------|-----------|----------|
| Shadow | 1/8 | 1/3 | 0/3 | 0/3 | 0/1 | 0/1 |
| Dealer | 1/4 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| Pathfinder | 1/4 | 0/1 | 0/1 | 1/1 | 0/1 | 0/1 |
| Ironhand | 0/3 | 0/1 | 1/2 | — | — | — |

---

### ROUND 2 — Escalation

**Columbia Actions:**

1. **Shadow: Cyber vs Sarmatia (cyber card 1 of 3)**
   Target: Steal treasury coins
   ```
   prob = 0.50 + 0.15 + 0.05 = 0.70
   Repeated ops vs sarmatia: 2 previous → -0.10
   prob = 0.70 - 0.10 = 0.60
   Roll: 0.45 < 0.60 → SUCCESS
   Detection: 0.35 + 0.10*2 = 0.55, Roll 0.40 < 0.55 → DETECTED

   Effect: Steal 1-2 coins. Sarmatia treasury: 4.5 → 3.0 (steal 1.5)
   ```
   **Detected.** Sarmatia knows Columbia is behind the theft.

2. **Shadow: Disinformation vs Sarmatia (disinfo card 1 of 3)**
   Target: Undermine Pathfinder's domestic support
   ```
   prob = 0.55 + 0.15 + 0.05 - 0.15 (3 previous ops) = 0.60
   Roll: 0.52 < 0.60 → SUCCESS
   Detection: 0.25 + 0.30 = 0.55, Roll 0.48 < 0.55 → DETECTED

   Effect: Sarmatia stability -0.3, support -2
   ```

3. **Shield: Espionage vs Sarmatia (intel request 1 of 3)**
   Target: Sarmatia nuclear program (hard fact)
   ```
   prob = 0.80 - 0.20 (4 previous ops vs sarmatia) = 0.60
   Roll: 0.55 < 0.60 → SUCCESS
   Detection: 0.30 + 0.40 = 0.70, Roll 0.62 < 0.70 → DETECTED

   Intel: Nuclear level 3, progress 0.30 (actual: 1.0 per CSV — nuclear_rd_progress)
   ```

**CRITICAL FINDING — Repeated ops penalty makes detection near-certain:**
After 4 ops against the same target (Sarmatia), detection probability reaches 0.70+. By R3-R4, virtually every operation against Sarmatia will be detected. This creates a natural intelligence ceiling — you can spy intensely for 2-3 rounds, but then the target becomes aware and countermeasures activate.

**Sarmatia Actions:**

1. **Pathfinder: Election Meddling vs Ruthenia (election meddling card 1 of 1 — ONE SHOT)**
   Target: Ruthenia wartime election (R3). Support opposition candidate Broker.
   ```
   base_prob = 0.40 (election meddling)
   ai_level = 1 → +0.05
   intelligence_power: +0.05
   prob = 0.40 + 0.05 + 0.05 = 0.50

   Roll: 0.38 < 0.50 → SUCCESS

   Effect: 2-5% swing on election result (per D8 spec 6E)
     → 3% support swing toward Broker (opposition candidate)
     → Ruthenia political_support -= 3

   Detection: 0.45 + 0 = 0.45, Roll 0.52 → NOT DETECTED
   ```
   **Election meddling succeeds and goes undetected.** This could tip the Ruthenia election.

2. **Ironhand: Sabotage vs Columbia (sabotage card 1 of 1)**
   Target: Military production facility
   ```
   prob = 0.45 + 0.05 + 0.05 = 0.55
   Roll: 0.60 > 0.55 → FAILURE
   Detection: 0.40 + 0 = 0.40, Roll 0.30 < 0.40 → DETECTED
   ```
   **Failed and detected.** Columbia's response: diplomatic protest, increased counter-intelligence.

3. **Compass: Espionage vs Columbia (intel request 1 of 2)**
   Target: Columbia's back-channel peace positions (diplomatic secret — 70% accuracy)
   ```
   prob = 0.60 + 0.05 + 0.05 - 0.05 (1 previous op) = 0.65
   Roll: 0.30 < 0.65 → SUCCESS
   Detection: 0.30 + 0.10 = 0.40, Roll 0.55 → NOT DETECTED

   Intel: "Columbia willing to negotiate ceasefire if Sarmatia withdraws from zone X"
   Accuracy: 70% → this could be accurate or misleading
   ```

---

### ROUNDS 3-5 — Intelligence Attrition

**Round 3 summary (both sides burning through pools):**

Columbia ops (vs Sarmatia + Cathay):
- Shadow: Espionage vs Cathay (intel 2/8). Success. Undetected.
- Shadow: Sabotage vs Sarmatia (sab 2/3). Success. Detected (0.75 detect prob after 6 ops).
- Fixer: Espionage vs Persia (intel 1/3). Success. Undetected (fresh target).

Sarmatia ops:
- Pathfinder: Espionage vs Columbia (intel 2/4). Success. Detected (0.50).
- Ironhand: Espionage vs Ruthenia (intel 1/3). Success. Undetected.
- Ledger: Espionage vs Columbia (intel 1/2). Failure (prob 0.55 after penalties). Detected.

**Round 4 summary:**

Columbia:
- Shadow: Disinfo vs Sarmatia (disinfo 2/3). Prob 0.45 (heavy penalties). Failure. Detected.
- Shadow: Cyber vs Cathay (cyber 1/3). Success. Undetected (fresh target).
- Anchor: Disinfo vs Persia (disinfo 1/1). Success. Undetected.

Sarmatia:
- Pathfinder: Espionage vs Ruthenia (intel 3/4). Success. Detected.
- Ironhand: Cyber vs Ruthenia (cyber 2/2 — LAST). Success. Detected.
- Compass: Espionage vs Columbia (intel 2/2 — LAST). Failure. Detected.

**Round 5 summary — Pool depletion accelerating:**

Columbia:
- Shadow: Espionage vs Sarmatia (intel 3/8). Prob 0.55. Failure (rolled 0.58). Detected.
- Shadow: Sabotage vs Cathay (sab 3/3 — LAST). Success. Detected.
- Dealer: Cyber vs Sarmatia (cyber 1/1 — LAST). Failure. Detected.

Sarmatia:
- Pathfinder: Espionage vs Ruthenia (intel 4/4 — LAST). Success. Detected.
- Ironhand: Espionage vs Columbia (intel 1/3). Success. Undetected.
- **Sarmatia running low.** Pathfinder exhausted. Compass exhausted. Only Ironhand and Ledger have remaining pools.

---

### POOL DEPLETION TABLE (End of R5)

**Columbia:**

| Role | Intel | Sab | Cyber | Disinfo | Elect Med | Assassin |
|------|-------|-----|-------|---------|-----------|----------|
| Shadow | 3/8 | 3/3 EMPTY | 1/3 | 2/3 | 0/1 | 0/1 |
| Dealer | 1/4 | 0/1 | 1/1 EMPTY | 0/1 | 0/1 | 0/1 |
| Shield | 1/3 | 0/1 | 0/1 | — | — | — |
| Anchor | 0/3 | — | — | 1/1 EMPTY | 0/1 | — |
| Fixer | 1/3 | 0/1 | 0/1 | 0/1 | 0/1 | — |
| Pioneer | 0/2 | — | 0/1 | — | — | — |
| **Remaining** | **20** | **3** | **4** | **5** | **4** | **2** |

**Sarmatia:**

| Role | Intel | Sab | Cyber | Disinfo | Elect Med | Assassin |
|------|-------|-----|-------|---------|-----------|----------|
| Pathfinder | 4/4 EMPTY | 0/1 | 0/1 | 1/1 EMPTY | 1/1 EMPTY | 0/1 |
| Ironhand | 1/3 | 1/1 EMPTY | 2/2 EMPTY | — | — | — |
| Compass | 2/2 EMPTY | — | — | — | — | — |
| Ledger | 1/2 | — | — | — | — | — |
| **Remaining** | **4** | **1** | **0** | **0** | **0** | **1** |

**OBSERVATION:** By R5, Sarmatia is nearly depleted. Columbia has substantial reserves (Shadow alone has 5 intel remaining). The asymmetry is dramatic — Columbia has 2.5x more covert capacity than Sarmatia in raw numbers, and the gap widens as Sarmatia burns through scarce resources.

---

### ROUNDS 6-8 — Columbia Dominance, Sarmatia Dark

**Round 6:**

Columbia (still active):
- Shadow: Espionage vs Sarmatia (intel 4/8). Prob 0.45 (10+ ops against target). Failure. Detected.
- Shadow: Disinfo vs Sarmatia (disinfo 3/3 LAST). Prob 0.40. Failure. Detected.
- Fixer: Espionage vs Persia (intel 2/3). Success. Undetected.

**Shadow's ops against Sarmatia are now nearly futile** — repeated ops penalty has driven success probability below 0.50 and detection above 0.80. Diminishing returns force Columbia to switch targets.

Sarmatia (minimal):
- Ironhand: Espionage vs Columbia (intel 2/3). Success. Detected.
- Pathfinder: Assassination vs Dealer (card 1/1 — ONE SHOT, international)
  ```
  domestic = False (Dealer is in Columbia, Pathfinder orders from Sarmatia)
  base_prob = 0.20 (international default)
  Sarmatia bonus: +0.10 → prob = 0.30

  Roll: 0.45 > 0.30 → MISS

  Detection: 0.70 (failed international) → Roll 0.35 < 0.70 → DETECTED

  Sarmatia's assassination attempt against Columbia's president is EXPOSED.
  Diplomatic fallout: massive.
  ```

**Round 7:**

Columbia:
- Shadow: Espionage vs Cathay (intel 5/8). Success. Undetected (fewer ops against Cathay).
- Dealer: Election meddling vs Ruthenia (EM card 1/1 — for R3-4 election already passed)
  **Wait:** Ruthenia election was R3-4. It is now R7. Can election meddling affect a past election?

  **ISSUE FOUND — Election meddling timing ambiguity:**
  D8 spec says: "WORKS WITH OR WITHOUT ELECTION. If no election upcoming: affects political support/attitude."
  So: election meddling at R7 affects Ruthenia support, not an election outcome.
  ```
  prob = 0.40 + 0.15 + 0.05 = 0.60
  Roll: 0.50 < 0.60 → SUCCESS
  Detection: 0.45, Roll 0.55 → NOT DETECTED
  Effect: Ruthenia support -3 (or target support of specific faction)
  ```

- Pioneer: Cyber vs Cathay (cyber 1/1 LAST). Success. Detected.

Sarmatia:
- Ironhand: Espionage vs Ruthenia (intel 3/3 LAST). Success. Detected.
- **Sarmatia is now operationally DARK.** Only Ledger has 1 intel request remaining.

**Round 8:**

Columbia (still has reserves):
- Shadow: Espionage vs Sarmatia (intel 6/8). Prob 0.40 (massive penalty). Failure. Detected.
- Shadow: Espionage vs Cathay (intel 7/8). Success. Detected.
- Shield: Sabotage vs Sarmatia (sab 1/1 LAST). Prob 0.50 (penalties). Success. Detected.
  Effect: 0.02 * 12.5 = 0.25 GDP damage to Sarmatia.

Sarmatia:
- Ledger: Espionage vs Ruthenia (intel 2/2 LAST). Success. Undetected.
- **Sarmatia covert capability: ZERO.** All pools depleted.

---

## FINAL POOL STATUS (End of R8)

**Columbia:**

| Role | Intel | Sab | Cyber | Disinfo | Elect Med | Assassin |
|------|-------|-----|-------|---------|-----------|----------|
| Shadow | 7/8 | 3/3 | 1/3 | 3/3 | 0/1 | 0/1 |
| Dealer | 1/4 | 0/1 | 1/1 | 0/1 | 1/1 | 0/1 |
| Shield | 2/3 | 1/1 | 0/1 | — | — | — |
| Anchor | 0/3 | — | — | 1/1 | 1/1 | — |
| Fixer | 2/3 | 0/1 | 0/1 | 0/1 | 0/1 | — |
| Pioneer | 0/2 | — | 1/1 | — | — | — |
| Volt | 0/2 | — | — | — | — | — |
| Tribune | 0/1 | — | — | 0/1 | — | — |
| Challenger | 0/1 | — | — | 0/1 | — | — |
| **Used/Total** | **12/27** | **4/6** | **4/7** | **4/8** | **2/4** | **0/2** |

**Columbia used 44% of intelligence, 67% of sabotage, 57% of cyber, 50% of disinfo, 50% of election meddling, 0% of assassination.**

**Sarmatia:**

| Role | Intel | Sab | Cyber | Disinfo | Elect Med | Assassin |
|------|-------|-----|-------|---------|-----------|----------|
| Pathfinder | 4/4 | 0/1 | 0/1 | 1/1 | 1/1 | 1/1 |
| Ironhand | 3/3 | 1/1 | 2/2 | — | — | — |
| Compass | 2/2 | — | — | — | — | — |
| Ledger | 2/2 | — | — | — | — | — |
| **Used/Total** | **11/11** | **1/2** | **2/2** | **1/1** | **1/1** | **1/1** |

**Sarmatia used 100% of intelligence, 50% of sabotage, 100% of cyber, 100% of disinfo, 100% of election meddling, 100% of assassination.**

---

## COVERT OPERATION RESULTS SUMMARY

### Success Rates

| Op Type | Columbia Attempts | Columbia Success | Sarmatia Attempts | Sarmatia Success |
|---------|-------------------|------------------|--------------------|--------------------|
| Espionage | 12 | 8 (67%) | 11 | 7 (64%) |
| Sabotage | 4 | 3 (75%) | 1 | 0 (0%) |
| Cyber | 4 | 3 (75%) | 2 | 1 (50%) |
| Disinformation | 4 | 2 (50%) | 1 | 1 (100%) |
| Election Meddling | 2 | 2 (100%) | 1 | 1 (100%) |
| Assassination | 0 | — | 1 | 0 (0%) |
| **TOTAL** | **26** | **18 (69%)** | **17** | **10 (59%)** |

### Detection Rates

| Op Type | Columbia Detected | Sarmatia Detected |
|---------|-------------------|--------------------|
| Espionage | 5/12 (42%) | 8/11 (73%) |
| Sabotage | 3/4 (75%) | 1/1 (100%) |
| Cyber | 2/4 (50%) | 2/2 (100%) |
| Disinformation | 2/4 (50%) | 0/1 (0%) |
| Election Meddling | 0/2 (0%) | 0/1 (0%) |
| Assassination | — | 1/1 (100%) |

**Observation:** Columbia's higher AI level (L3 vs L1) gives +0.10 success probability advantage. But the repeated ops penalty dominates after R3-4, making both sides roughly equal in late-game effectiveness against hardened targets.

### Cumulative Damage

**Damage to Sarmatia from Columbia covert ops:**
- GDP damage: 3 successful sabotage * 0.4 + 1 cyber theft = ~1.5 coins GDP + 1.5 treasury
- Stability: 2 successful disinfo * -0.3 = -0.6
- Support: 2 successful disinfo * -2 = -4

**Damage to Columbia from Sarmatia covert ops:**
- GDP damage: 1 cyber attempt failed → 0
- Stability: 0 (failed sabotage, failed assassination)
- Support: 0 (no successful disinfo against Columbia)

**Damage to Ruthenia from Sarmatia covert ops:**
- Support: 1 disinfo (-2) + 1 election meddling (-3) = -5 total
- Stability: -0.3 from disinfo

**Net assessment:** Columbia's covert advantage is overwhelming. Sarmatia inflicted more damage on Ruthenia than on Columbia itself.

---

## ANALYSIS

### 1. Per-Individual Intelligence Pools

**Finding:** The per-individual pool system (D8 spec) creates meaningful resource scarcity and asymmetry. Shadow's 8 intel pool is a major strategic asset. Sarmatia's total 11 intel pool is exhausted by R7. This creates a "go dark" moment for Sarmatia — a compelling gameplay consequence.

**However:** The engine code does NOT implement individual pools. It tracks only country-level per-round limits (3 for intelligence powers). This gap between spec and code is the single largest issue in T7.

**Severity: HIGH. Engine must implement per-individual pool tracking.**

### 2. Accuracy Tiers

**Finding:** The D8 spec defines 4 accuracy tiers:
- Hard facts: 85-90%
- Diplomatic secrets: 70%
- Strategic intentions: 50-60%
- Aggressive/impractical: 40%

The engine code (`_gather_intelligence`, lines 623-638) applies uniform noise (0.85-1.15 multiplier) to ALL data types. There is no accuracy tier system. Nuclear level is returned exact (integer, no noise). GDP and stability get the same noise regardless of question type.

**ISSUE FOUND — Accuracy tiers not implemented:**
The code does not distinguish between "what is their GDP" (hard fact, should be 85-90% accurate) and "will they invade Formosa next round" (strategic intention, should be 50-60%). All intelligence gets the same +-15% noise.
**Severity: HIGH. Accuracy tiers are a core design feature and need implementation.**

### 3. Always Returns Answer

**Finding:** The D8 spec says: "ALWAYS RETURNS AN ANSWER — never failed, no info." The engine code implements this correctly — even failed espionage rolls return partial intelligence in the form of the spy attempt result (success/failure). However, for FAILED espionage, the code returns nothing beyond the failure status (no intelligence data).

**ISSUE FOUND — Failed espionage returns no intelligence:**
Per spec, failed intelligence should still return SOMETHING (lower accuracy). The code only returns intelligence data on success. On failure, the requesting role gets no information at all.
**Severity: HIGH. Failed intelligence should return low-accuracy data (40% accuracy tier, essentially guesses).**

### 4. Sabotage/Cyber/Disinformation Probabilities

**Finding:** Base probabilities in the code match the D8 spec:
- Sabotage: 0.45 (spec says 0.40 base + intel chief bonus +10%) — **minor discrepancy**
- Cyber: 0.50 (matches)
- Disinformation: 0.55 (matches)

The AI level bonus (+0.05 per level) and intelligence power bonus (+0.05) are implemented correctly.

**ISSUE FOUND — Sabotage base probability discrepancy:**
- Code (line 32): `"sabotage": 0.45`
- D8 spec (Section 6B): "40% base + AI tech bonus + intel chief bonus (+10%)"
- Code applies 0.45 as base, then adds AI bonus on top. Spec says 0.40 base + conditional +10% for intel chief.
- For Shadow (intel chief): code gives 0.45 + 0.15 + 0.05 = 0.65. Spec gives 0.40 + 0.10 + 0.15 + 0.05 = 0.70.
- For non-intel-chief: code gives 0.45. Spec gives 0.40.
**Severity: LOW. Minor calibration difference. The intel chief bonus is baked into base rather than conditional.**

### 5. Card Pool Depletion and Scarcity

**Finding:** The per-individual pool system creates excellent scarcity dynamics:
- Sarmatia is operationally dark by R7 (all pools exhausted)
- Columbia retains ~50% capacity at game end
- This asymmetry reflects the real-world intelligence capability gap
- The "burn rate" of 2-3 ops per round means pools last 4-6 rounds at maximum intensity

**The scarcity mechanic is the strongest design feature of the intelligence system.** It forces players to choose: burn resources early for immediate advantage, or conserve for critical moments. Sarmatia's all-out approach leaves them blind in the endgame.

**Severity: PASS (design is excellent). But requires implementation (per Issue #1).**

### 6. Election Meddling — Risk/Reward

**Finding:** Election meddling has a good risk/reward balance:
- 1 card per game (one-shot, high stakes)
- 40-50% success rate (coin-flip)
- 2-5% impact on election (significant but not decisive)
- 45% base detection (highest of all covert ops)
- Backlash if detected (damages the candidate you tried to help)

Sarmatia's successful, undetected meddling in the Ruthenia election (-3% support swing) could tip a close election. This is a compelling mechanic.

**Minor gap:** The "backlash" mechanic (exposure damages the helped candidate) is described in the spec but not formalized as a formula. What is the backlash penalty? +5% to the opposing candidate? -10% to the helped candidate?
**Severity: LOW. Backlash needs a number.**

### 7. Detection and Attribution

**Finding:** The repeated ops penalty on detection (+0.10 per previous op against same target) creates a natural escalation curve:
- First op: 30-45% detection
- After 5 ops: 80-95% detection (near certain)
- This forces attackers to rotate targets or accept exposure

**The detection system works well** but lacks an ATTRIBUTION mechanic. Detection tells the target "someone spied on you" but the code logs `country` in the event, meaning the target knows exactly who did it. The D8 spec distinguishes between DETECTION (you know something happened) and ATTRIBUTION (you know who did it).

**ISSUE FOUND — No attribution mechanic separate from detection:**
The code treats detection = full attribution. In reality, detected cyber attacks are often not attributed. The spec mentions attribution difficulty for disinformation (~60% attribution accuracy) but the code provides 100% attribution on any detection.
**Severity: MEDIUM. Detection should not equal full attribution. Add attribution probability per op type.**

### 8. Cross-Checking Intelligence

**Finding:** The D8 spec describes cross-checking: "Same question submitted through DIFFERENT intelligence services can be compared." This is a purely player-facing mechanic — two allies ask the same question through different spy agencies and compare answers.

The engine supports this implicitly (two separate espionage ops with different noise will produce different numbers). If answers agree, higher confidence. If they disagree, one is wrong.

**This works without additional code** — it emerges naturally from the noise system. No engine change needed.

**Severity: PASS.**

---

## SCORE

| Dimension | Score | Notes |
|-----------|-------|-------|
| Per-individual pools (design) | 9/10 | Excellent scarcity mechanic. Asymmetry is compelling. |
| Per-individual pools (implementation) | 2/10 | NOT IMPLEMENTED in engine code. Country-level limit only. |
| Accuracy tiers | 3/10 | Not implemented. Uniform noise for all intelligence types. |
| Always returns answer | 4/10 | Failed espionage returns nothing, should return low-accuracy data. |
| Sabotage/cyber/disinfo | 8/10 | Probabilities mostly match. Minor calibration differences. |
| Card pool depletion | 9/10 | Creates excellent gameplay scarcity. Sarmatia goes dark by R7. |
| Election meddling | 8/10 | Good risk/reward. Backlash formula needs a number. |
| Detection/attribution | 5/10 | Detection escalation works. No attribution layer separate from detection. |
| Cross-checking | 9/10 | Works naturally from noise system. No code change needed. |
| Overall covert system | 6/10 | Design is excellent. Implementation has major gaps. |

---

## VERDICT: CONDITIONAL PASS

**The intelligence and covert operations DESIGN is the strongest of the three tests.** Per-individual pools create meaningful scarcity. The asymmetry between Columbia (27 intel) and Sarmatia (11 intel) drives strategic decisions. Card pool depletion forces prioritization. Cross-checking emerges naturally.

**The gap between spec and engine code is the primary concern.** The D8 spec describes a sophisticated per-individual pool system with accuracy tiers. The engine code implements a simpler per-country-per-round limit with uniform noise.

**Four issues prevent a clean PASS:**

1. **Per-individual pool tracking not implemented** — engine uses country-level per-round limits, not individual pools. (IMPLEMENT — HIGH)

2. **Accuracy tiers not implemented** — all intelligence gets uniform +-15% noise regardless of question type. (IMPLEMENT — HIGH)

3. **Failed espionage returns nothing** — spec says "always returns an answer." Failed ops should return low-accuracy data. (FIX — HIGH)

4. **Detection = full attribution** — no separation between detecting an operation and knowing who did it. (ADD — MEDIUM)

**Recommended actions before gate approval:**
- [ ] Implement per-individual intelligence pool tracking in engine (track `role.intel_used`, `role.sabotage_used`, etc.)
- [ ] Implement accuracy tiers: hard facts (noise 0.90-1.10), diplomatic secrets (0.70-1.30), strategic intentions (0.50-1.50), aggressive (0.40-1.60)
- [ ] Return low-accuracy intelligence on failed espionage (accuracy tier = "aggressive/impractical" = 40%)
- [ ] Add attribution probability: espionage 60%, sabotage 70%, cyber 50%, disinfo 30%, election meddling 40%
- [ ] Reconcile sabotage base probability (code 0.45 vs spec 0.40 + conditional intel chief bonus)
- [ ] Formalize election meddling backlash penalty (recommend: +5 support to opposing candidate if detected)

---

*Test executed by INDEPENDENT TESTER. No design files modified. All calculations based on D8 v1 formulas, roles.csv pool data, and live_action_engine.py code.*
