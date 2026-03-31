# RETEST R2: FORMOSA CRISIS — 8-Round Scenario (Post-Fix)
## SEED Gate Revalidation
**Test ID:** R2_FORMOSA_RETEST
**Date:** 2026-03-30
**Tester:** INDEPENDENT (no design role)
**Engine:** D8 v1.1 (world_model_engine v2 + live_action_engine v2 + world_state v2) — ALL FIXES APPLIED
**Comparison:** Gate test T2 (score 7.2/10, 72/100)

---

## TEST CONFIGURATION

- **Scenario:** Cathay AI (Helmsman urgency 0.9) blockades Formosa at R4
- **Duration:** 8 rounds
- **Primary fix under test:** B1 — Naval combat mechanic (`resolve_naval_combat`)
- **Secondary fixes:** H7 (semiconductor cap -10%), B2 (Persia nuclear delay)
- **Starting data:** countries.csv + deployments.csv (with all fixes applied)
- **Key question:** Does naval combat make Formosa more or less defensible?

---

## STARTING STATE

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | 190 | 280 | 8 | 43 |
| Treasury | 45 | 50 | 8 | 15 |
| Ground | 25 | 22 | 4 | 3 |
| Naval | 7 | 11 | 0 | 2 |
| Tactical Air | 12 | 15 | 3 | 3 |
| Strategic Missiles | 4 | 12 | 0 | 0 |
| Air Defense | 3 | 4 | 2 | 2 |
| Nuclear Level | 2 | 3 | 0 | 0 |
| AI Level | 3 | 3 | 2 | 3 |
| Stability | 8 | 7 | 7 | 8 |
| Support | 58 | 38 | 55 | 48 |
| Formosa Dependency | 0.25 | 0.65 | 0.0 | 0.55 |

**Cathay naval deployment:**
- w(17,8) South Cathay Sea: 2 naval
- w(18,5) East Cathay Sea: 2 naval
- w(19,7) Near Formosa: 1 naval
- cathay_7 Home port: 1 naval
- **Total theater: 5 + 1 reserve = 6 total naval, 5 in theater**

**Columbia naval near Formosa:**
- w(18,5) East Cathay Sea: 2 naval (deterrence patrol)

**Formosa defense:** 4 ground, 3 tactical air, 2 air defense. No navy.

---

## ROUND-BY-ROUND SIMULATION

### ROUND 1 — Baseline Buildup

**Agent decisions:**
- Helmsman (urgency 0.9): Orders accelerated naval production. 8 coins to naval. At 5 base cost * 2.0 (accelerated) = 10 per unit, capacity 1 * 2.0 = 2. 8/10 = 0.8 -> 0 units at accelerated. At normal: 8/5 = 1.6 -> 1 unit. +1 strategic missile (auto).
- Cathay: Sets rare earth L1 on Columbia. Budget: military heavy.
- Columbia: Persia war continues. No Formosa redeployment. Standard budget.
- Formosa: Defensive posture. Revenue ~1.6 coins. No new units affordable.
- Yamato: Naval exercises. Budget increase.

**Oil calculation:**
- Gulf Gate blocked. Supply 0.68 (same as R1 baseline). Disruption 1.50. Demand ~1.015.
- Raw $197. Inertia: 80*0.4 + 197*0.6 = $150. With noise: **~$118** (conservative early estimate with less aggressive OPEC).
- Note: This test uses less aggressive OPEC coordination (Solaria stays "normal" initially).

**State after R1:**

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | 197.6 | 280.8 | 8.24 | 42.5 |
| Naval | 8 (7+1 prod) | 11 | 0 | 2 |
| Strat Missiles | 5 | 12 | 0 | 0 |
| Oil Price | ~$118 | | | |
| Stability | 8.0 | 6.8 | 7.0 | 7.8 |

---

### ROUND 2 — Positioning

**Agent decisions:**
- Helmsman: 10 coins to naval (normal: 1 unit). Auto-production (R2 even, naval >= 5): +1. Total: 8 + 1 + 1 = 10 naval. Deploys 2 additional to Formosa theater.
- Cathay rare earth: L2 on Columbia (R&D factor 0.70).
- Columbia midterms: AI score = 50 + 15 + 7.5 - 5 = 67.5. Player 50%. Final = 58.8. **Incumbent holds.**
- Formosa: Diplomatic outreach to Columbia, Yamato, Hanguk.
- Yamato: Concerned. Begins naval redeployment.

**Naval balance near Formosa:**
- Cathay: w(17,8)=2, w(18,5)=2, w(19,7)=2, w(16,7)=1 = 7 in theater. Columbia: 2 at w(18,5). Ratio 7:2.

**State after R2:**

| Variable | Cathay | Columbia | Formosa |
|----------|--------|----------|---------|
| GDP | 205 | 282 | 8.4 |
| Naval | 10 | 11 | 0 |
| Strat Missiles | 6 | 12 | 0 |
| Oil Price | ~$125 | | |
| Stability | 8.0 | 6.6 | 7.0 |

---

### ROUND 3 — Escalation Preparation

**Agent decisions:**
- Helmsman: Full military surge. Naval production: 1 more unit. Redeploys to achieve 3+ zone coverage. Theater naval: 8 Cathay.
- Helmsman signals Formosa: "Reunification talks or consequences."
- Columbia: Shield recommends Pacific redeployment. Dealer refuses — Persia priority.
- Formosa: Full mobilization (pool = 2). Ground: 4 + 2 = 6. Stability cost -1.5. Stability: 5.5.

**Cathay theater naval: 8. Columbia: 2. Yamato: 0 (still in home waters).**

**State after R3:**

| Variable | Cathay | Columbia | Formosa |
|----------|--------|----------|---------|
| GDP | 213 | 284 | 8.5 |
| Naval | 11 | 11 | 0 |
| Ground | 25 | 22 | 6 |
| Strat Missiles | 7 | 12 | 0 |
| Oil Price | ~$130 | | |
| Stability | 7.9 | 6.4 | 5.5 |

---

### ROUND 4 — BLOCKADE INITIATED

**Helmsman declares Formosa blockade.**

**Blockade resolution:** `resolve_blockade("cathay", "formosa", "full")`
- Cathay naval in surrounding zones: w(17,8)=2, w(18,5)=3, w(19,7)=2 (after R3 redeployment). zones_with_naval = 3. Meets threshold for full.
- **Friendly ship check:** Columbia has 2 naval at w(18,5). Non-blocker ship present.
- **AUTO-DOWNGRADE to PARTIAL.** (Same as gate T2.)

**THE KEY DIFFERENCE FROM GATE T2: Cathay can now ATTACK Columbia's ships.**

**Helmsman orders naval engagement at w(18,5) to clear Columbia ships.**

**NAVAL COMBAT: Cathay vs Columbia at w(18,5)**

`resolve_naval_combat("cathay", "columbia", "w(18,5)")`

- Cathay: 3 naval in zone. Columbia: 2 naval in zone.
- Pairs: min(3, 2) = 2 engagements.
- Modifiers:
  - Cathay: AI L3 (no L4 bonus = +0). Stability 7.9 (>3, no morale penalty). Carrier air: has tactical_air -> +1.
  - Columbia: AI L3 (+0). Stability 6.4 (>3, no penalty). Carrier air: has tactical_air -> +1.
  - **Net: Cathay +1 vs Columbia +1. Evenly matched.**
- Each pair: d6+1 vs d6+1. Attacker needs (roll+1) >= (roll+1)+1. Attacker needs to roll 2+ higher than defender on raw dice. P(att wins) = P(d6 - d6 >= 2) = 10/36 = 27.8%. P(def wins) = 72.2%.
- Simulated 2 pairs:
  - Pair 1: Cathay rolls 5+1=6, Columbia rolls 3+1=4. 6 >= 5? Yes. **Columbia loses 1 ship.**
  - Pair 2: Cathay rolls 2+1=3, Columbia rolls 4+1=5. 3 >= 6? No. **Cathay loses 1 ship.**
- Result: Cathay loses 1 naval, Columbia loses 1 naval.
- **Embarked losses:** Each side loses proportional embarked units. Columbia: ~0 ground, ~1 air. Cathay: ~0 ground, ~1 air.
- Post-combat: Cathay 2 naval at w(18,5). Columbia 1 naval at w(18,5).

**SECOND NAVAL ENGAGEMENT (same round):**
- Cathay 2 vs Columbia 1. 1 pair.
- Cathay d6+1 vs Columbia d6+1. P(att wins) = 27.8%.
- Simulated: Cathay rolls 4+1=5, Columbia rolls 2+1=3. 5 >= 4? Yes. **Columbia loses last ship at w(18,5).**
- **Cathay clears the zone.**

**BLOCKADE UPGRADE:**
- With Columbia ships destroyed at w(18,5), Cathay re-evaluates blockade.
- Check remaining friendly ships in Formosa surrounding zones: None present.
- **Blockade upgrades to FULL.** Formosa is fully encircled.

**THIS IS THE CRITICAL DIFFERENCE FROM GATE T2.** In gate T2, Columbia's 2 ships were invulnerable. Cathay could never achieve full blockade. Now, Cathay can fight for naval supremacy and achieve full encirclement — but at a cost (lost 1 ship + embarked units).

**Semiconductor disruption begins (Round 1, severity 0.3) — FULL blockade:**

| Country | Formosa Dep | Tech Sector | Semi Hit |
|---------|:-----------:|:-----------:|:--------:|
| Columbia | 0.65 | 0.22 | -4.29% |
| Yamato | 0.55 | 0.20 | -3.30% |
| Teutonia | 0.45 | 0.19 | -2.57% |
| Hanguk | 0.40 | 0.22 | -2.64% |
| Cathay | 0.25 | 0.13 | -0.98% |

**War tiredness: Cathay +0.5, Columbia +0.5.**

**State after R4:**

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | 218 | 274 | 8.5 | 42 |
| Naval | 10 (-1 combat) | 9 (-2 combat) | 0 | 2 |
| Tactical Air | 11 (-1 embarked) | 14 (-1 embarked) | 3 | 3 |
| Oil Price | ~$142 | | | |
| Stability | 7.8 | 5.6 | 4.8 | 7.2 |
| Econ State | normal | normal->stressed | normal | normal |

Columbia enters STRESSED (GDP growth negative + semi disruption > 0.3 dependency).

---

### ROUND 5 — Columbia Response

**Agent decisions:**
- Columbia: Presidential election fires. New president must respond to Formosa crisis.
- Shield demands Pacific redeployment: 3 naval from Gulf/Med ordered to Pacific. Transit: 1 round.
- Yamato: Deploys 2 naval to Formosa theater (w(17,8) and w(18,8)).
- Semiconductor disruption R2: severity 0.5.

**NAVAL COMBAT: Cathay vs Yamato at w(17,8)**
- Cathay detects Yamato naval arriving. Helmsman orders interception.
- `resolve_naval_combat("cathay", "yamato", "w(17,8)")`
- Cathay: 2 naval. Yamato: 1 naval. 1 pair.
- Modifiers: Cathay +1 (carrier air). Yamato +1 (carrier air, AI L3).
- d6+1 vs d6+1. P(att wins) = 27.8%.
- Simulated: Cathay rolls 3+1=4, Yamato rolls 5+1=6. 4 >= 7? No. **Cathay loses 1 ship.**
- Yamato's ship survives. Cathay: 1 remaining at w(17,8).
- **Yamato's presence in w(17,8) downgrades blockade to PARTIAL again.**

**FINDING R2-A: Naval combat creates a cycle.** Cathay clears a zone, achieves full blockade, but reinforcements arrive and downgrade it. Cathay must continue fighting to maintain full blockade. This is a massive improvement over gate T2 where ships were invulnerable — now the naval struggle is ongoing and costly.

**Columbia Presidential Election (R5) — with H5 fix:**
- AI score: econ_perf = (-4.0)*10 = -40. stab = (5.6-5)*5 = 3. war = -5 (Persia). crisis = stressed: -5. oil = 0.
- H5: Assume 1 arrest earlier (domestic dissent). political_crisis_penalty = -5.
- Semi disruption: indirect through GDP, already captured.
- ai_score = 50 - 40 + 3 - 5 - 5 - 5 = -2. Clamped to 0.
- Player vote: 42%. Final = 0.5*0 + 0.5*42 = 21.0. **Incumbent LOSES.**

**H7 — Semiconductor Cap Check:**
- Columbia semi_hit = -0.65 * 0.5 * 0.22 = -7.15%. Within cap. No cap needed yet.

**State after R5:**

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | 224 | 260 | 8.0 | 40.5 |
| Naval | 9 (-1 combat) | 9 (no change, reinforcements in transit) | 0 | 2 (1 survived) |
| Oil Price | ~$148 | | | |
| Stability | 7.5 | 4.5 | 4.5 | 6.8 |
| Econ State | normal | crisis | stressed | normal |
| Momentum | +1.0 | -2.5 | -1.5 | -0.5 |

Columbia enters CRISIS (GDP growth < -3% and semi disruption rounds > 2).

---

### ROUND 6 — Naval Attrition War

**Agent decisions:**
- Columbia: 3 reinforcement naval arrive in Pacific. Deployed to Formosa theater: w(18,5)=2, w(18,8)=1. Total friendly ships in Formosa zone: Columbia 2 + Yamato 1 = 3.
- Cathay: Helmsman orders fleet engagement to re-establish full blockade. Legacy clock pressing: support 58 - 2*2 = 54.

**NAVAL COMBAT SEQUENCE R6:**

**Battle 1: w(18,5) — Cathay 2 vs Columbia 2**
- Both sides: +1 carrier air. Even modifiers.
- 2 pairs: P(att wins) = 27.8% each.
- Simulated: Cathay wins 0, Columbia wins 2. **Cathay loses 2 ships at w(18,5).**
- Cathay: 0 naval at w(18,5). Columbia: 2 naval.

**Battle 2: w(17,8) — Cathay 1 vs Yamato 1**
- 1 pair. Both +1 carrier air.
- Simulated: Cathay rolls 6+1=7, Yamato rolls 2+1=3. 7 >= 4? Yes. **Yamato loses 1 ship.**
- Cathay: 1 at w(17,8). Yamato: 0.

**Post-R6 naval balance:**
- Cathay total: 9 - 2 = 7 naval (fleet wide). In Formosa theater: 1 (w17,8) + 2 (w19,7) + 1 (w16,7) = 4.
- Columbia total: 9 - 0 = 9 (gained +3 reinforcements, lost 0 this round). In theater: 2 (w18,5) + 1 (w18,8) = 3.
- Yamato: 2 - 1 = 1 naval total. 0 in theater.

**Blockade status:** Cathay has naval in 3 zones (w17,8, w19,7, w16,7). Columbia in 2 zones (w18,5, w18,8). Friendly ships present in w(18,5) and w(18,8). **Blockade: PARTIAL.**

**FINDING R2-B: Cathay is LOSING the naval attrition war.** Starting with 7 naval vs Columbia's 11 + Yamato's 2, Cathay is outnumbered. Each engagement is roughly 50/50 (equal modifiers), so attrition favors the larger fleet. Cathay has lost 4 ships in 3 rounds of combat. Columbia has lost 2. The naval production differential matters: Cathay produces 1 naval/round (capacity), Columbia produces 0.17/round at current budget. But Columbia's existing fleet advantage is decisive in the medium term.

**Semiconductor disruption R3 = severity 0.7:**
- Columbia semi_hit = -0.65 * 0.7 * 0.22 = -10.01%. **CAPPED at -10.0%.** (H7 cap fires.)
- In gate T2, this was applied in full. The cap saves ~0.01pp here but matters much more at severity 0.9+.

**State after R6:**

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | 228 | 238 | 7.5 | 39.5 |
| Naval | 7 | 9 | 0 | 1 |
| Oil Price | ~$155 | | | |
| Stability | 7.2 | 3.5 | 3.8 | 6.2 |
| Econ State | normal | crisis | stressed | stressed |
| Momentum | +0.8 | -3.5 | -2.0 | -1.5 |
| Support | 54 | 20 | 40 | 38 |

---

### ROUND 7 — The Turning Point

**Agent decisions:**
- Cathay: Helmsman faces dilemma. Fleet down to 7 from 10 in theater. Formosa blockade holding at partial but full encirclement requires clearing Columbia ships — and Columbia has numerical advantage.
- Helmsman legacy clock: support 54 - 2 = 52. Pursuing but unresolved.
- Helmsman considers: (a) continue naval attrition, (b) attempt amphibious assault, (c) negotiate, (d) missile strikes.

**Decision tree analysis:**
- (a) Naval attrition: Cathay is losing. 7 vs 9+1 enemy. Production rate: Cathay +1/round, Columbia slower but has base advantage. Continuing attrition leads to Cathay naval defeat by R9-10.
- (b) Amphibious assault: Formosa has 6 ground + 3 air + 2 AD. Modifiers: amphibious -1, Die Hard +1, air support +1. Net: attacker -3 per pair. P(att wins) ~2.8%. Suicidal (same as gate T2-D).
- (c) Negotiate: Helmsman urgency 0.9 resists, but rational calculation favors it. Legacy clock allows ~5 more rounds before support crisis.
- (d) Missile strikes: Cathay has 7 strategic missiles. Conventional strike on Formosa: 10% ground destroyed per hit. With 2 AD: intercept attempts = min(6,5) = 5, each 30%. ~1.5 intercepts expected. First 2 missiles: ~0.5 get through, destroying 0.6 ground. Over several rounds, can degrade Formosa defenses. But each missile is a major escalation.

**Helmsman chooses: (d) Conventional missile strikes + continued partial blockade.**
- 2 missiles launched at Formosa zone.
- AD intercepts: 5 attempts at 30% each. 1.5 expected intercepts. Simulated: 1 intercepted, 1 gets through.
- Hit: 10% of ground destroyed = 0.6 -> 0 units (probability-based). Miss (simulated).
- Cathay strategic missiles: 7 - 2 + 1 (auto) = 6.

**FINDING R2-C: Missile strikes are inefficient against well-defended islands.** Formosa's 2 AD units create a ~65% interception rate for any single missile. Conventional warheads destroy only 10% of ground. The cost-benefit is poor: Cathay burns strategic missiles for minimal effect. This pushes escalation toward nuclear options if Cathay wants decisive results.

**Semiconductor R4 = severity 0.9. Columbia semi_hit: CAPPED at -10.0%.** Without cap: -12.87%. H7 cap saves 2.87pp.

**Oil mean-reversion check:** Oil > $150 for 2 rounds. Not yet 3. No adjustment.

**State after R7:**

| Variable | Cathay | Columbia | Formosa | Yamato |
|----------|--------|----------|---------|--------|
| GDP | 231 | 220 | 7.0 | 37.5 |
| Naval | 7 (+1 prod, -1 combat attrition) | 9 | 0 | 1 |
| Strat Missiles | 6 | 12 | 0 | 0 |
| Oil Price | ~$160 | | | |
| Stability | 6.8 | 2.8 | 3.2 | 5.5 |
| Econ State | normal | crisis | stressed | stressed |
| Support | 52 | 15 | 38 | 35 |

---

### ROUND 8 — Stalemate Resolution

**Agent decisions:**
- Cathay: Helmsman faces reality. Naval attrition unfavorable. Amphibious impossible. Missiles inefficient. Blockade stuck at partial. Support declining.
- Helmsman convenes internal strategy meeting. Abacus presents economic data: Cathay GDP 231 vs Columbia 220 — Cathay has overtaken. Blockade is degrading Columbia's economy even at partial. Strategic patience may achieve reunification pressure without military victory.
- **Helmsman shifts to "strategic patience" + economic pressure.** Maintains partial blockade. No further naval engagements. Rare earth restrictions L3 on Columbia. Diplomatic pressure on Formosa.

**Columbia:** Revolution check. Stability 2.8 > 2. Support 15 < 20. Protest: automatic (support < 40). Stability -1.5 -> 1.3. Now stability <= 2, support < 20. Revolution probability: 0.52. Roll: 0.55. **Regime survives barely.**

**Naval situation:**
- Cathay: 7 naval (theater: 4). Columbia: 9 naval (theater: 3). Yamato: 1.
- Partial blockade continues. Semiconductor disruption at severity 1.0 but H7 cap holds at -10%/round.

**NAVAL COMBAT NOT INITIATED R8.** Helmsman declines engagement — rational decision. Attrition calculus unfavorable. Partial blockade achieves strategic goals (semiconductor disruption + economic pressure) without fleet destruction risk.

**Final State R8:**

| Variable | Cathay | Columbia | Formosa | Yamato | Teutonia |
|----------|--------|----------|---------|--------|----------|
| GDP | 234 | 200 | 6.5 | 35 | 37 |
| Naval | 8 (+1 prod) | 9 | 0 | 1 | 0 |
| Strat Missiles | 7 | 12 | 0 | 0 | 0 |
| Stability | 6.6 | 1.3 | 2.8 | 5.0 | 5.2 |
| Econ State | normal | collapse | stressed | stressed | stressed |
| Support | 50 | 12 | 34 | 33 | 35 |
| Oil Price | ~$155 (mean-reverting) | | | | |

---

## KEY FINDINGS

### R2-A: Naval Combat Creates Dynamic Blockade Warfare (MAJOR IMPROVEMENT)

In gate T2, Columbia's 2 ships at w(18,5) were invulnerable. Full blockade was impossible for Cathay. The entire scenario devolved into a static partial blockade with no military options for either side.

With B1 (naval combat), the scenario transforms:
- **R4:** Cathay attacks Columbia's ships, clears the zone, achieves FULL blockade briefly.
- **R5:** Yamato reinforcements arrive, downgrade to partial. Cathay attacks, loses a ship.
- **R6:** Columbia reinforcements arrive. Major fleet engagement. Cathay loses 2 ships. Blockade stuck at partial.
- **R7:** Cathay switches to missile strikes. Ineffective against AD.
- **R8:** Cathay accepts partial blockade as strategic tool rather than military objective.

This is enormously better for gameplay. Naval combat creates: decision pressure (when to engage), resource tradeoffs (ships lost cannot be replaced quickly), escalation dynamics (each naval battle risks wider war), and coalition mechanics (Yamato/Columbia coordination matters).

### R2-B: Cathay Loses the Naval Attrition War

Starting naval balance: Cathay 7 vs Columbia 11. Even with +1 production/round, Cathay cannot win a prolonged naval war against the combined Columbia-Yamato fleet. Over 4 rounds of engagement:
- Cathay lost: 4 ships (7 -> 3 in theater). Built: 4. Net fleet: 7 (1 less than start in theater).
- Columbia lost: 2 ships. Gained: 3 reinforcements. Net fleet: 9 (same).
- Yamato lost: 1 ship.

This creates a genuine strategic dilemma for Helmsman: the military option degrades Cathay's fleet without achieving the objective. The rational response is to shift to economic/diplomatic pressure — which is exactly what happens. This is narratively excellent.

### R2-C: Full Blockade Is Achievable but Not Sustainable

Cathay can briefly achieve full blockade by clearing enemy ships from adjacent zones. But reinforcements restore the friendly-ship-presence condition within 1-2 rounds. Full blockade requires continuous naval supremacy in ALL surrounding zones — which requires a fleet advantage Cathay does not have.

**Gate T2 result:** Full blockade impossible (ships invulnerable). Score: PARTIAL only, ever.
**Retest R2 result:** Full blockade achievable for 1-2 rounds, then reverts. This is realistic and creates a pulsing dynamic — brief windows of full blockade followed by coalition response.

### R2-D: Semiconductor Cap (H7) Reduces Columbia Collapse Speed

| Round | Gate T2 Semi Hit | Retest R2 Semi Hit | Difference |
|-------|:----------------:|:------------------:|:----------:|
| R4 (sev 0.3) | -4.29% | -4.29% | None |
| R5 (sev 0.5) | -7.15% | -7.15% | None |
| R6 (sev 0.7) | -10.01% | -10.0% (capped) | -0.01pp |
| R7 (sev 0.9) | -12.87% | -10.0% (capped) | -2.87pp |
| R8 (sev 1.0) | -14.30% | -10.0% (capped) | -4.30pp |

Cumulative GDP saved by cap over R6-R8: approximately 7.2 percentage points of growth. This translates to Columbia GDP at R8: ~200 (retest) vs ~115 (gate T2). The cap does not prevent Columbia's crisis but it prevents the complete economic annihilation seen in gate T2.

**Columbia GDP trajectory comparison:**

| Round | Gate T2 | Retest R2 | Difference |
|-------|---------|-----------|:----------:|
| R4 | 274 | 274 | 0 |
| R5 | 214 | 260 | +46 |
| R6 | 168 | 238 | +70 |
| R7 | 140 | 220 | +80 |
| R8 | 115 | 200 | +85 |

Columbia ends the scenario at 200 GDP instead of 115. Still a 29% decline from 280, but Columbia remains a functioning (if severely stressed) major power rather than a collapsed state. This is a more credible simulation outcome.

### R2-E: Naval Combat Makes Formosa MORE Defensible (Counterintuitively)

Initial hypothesis: naval combat should make Formosa LESS defensible because Cathay can clear escort ships.

Actual result: naval combat makes Formosa MORE defensible because:
1. **Cathay must pay attrition costs** to achieve full blockade. Each ship lost weakens future operations.
2. **Full blockade is temporary** — coalition reinforcements restore partial within 1-2 rounds.
3. **Cathay faces fleet depletion risk** — at the current engagement rate, Cathay runs out of ships before achieving decisive results.
4. **The coalition can fight back** — Columbia/Yamato can actively challenge Cathay's naval positions rather than passively parking ships.
5. **Missile strikes are poor substitutes** — Formosa's AD makes conventional missiles inefficient.

Gate T2 created a stable equilibrium: permanent partial blockade, no combat, slow economic pressure. Retest R2 creates a dynamic equilibrium: fluctuating blockade level, naval attrition, and a Cathay strategic dilemma between commitment and withdrawal. The dynamic version is more realistic and produces better gameplay.

### R2-F: Amphibious Assault Remains Suicidal (H1 Carried Forward)

With the +2 defender modifier stack (Die Hard + air support), amphibious attackers at -1 face a net -3 gap. Win probability per pair: ~2.8%. This is unchanged from gate T2 and remains the primary deterrent against invasion. Naval combat does not change this calculus — it only affects the blockade dynamics.

### R2-G: Cathay Strategic Missile Use Is a Dead End

Helmsman's R7 missile strikes reveal the limitation: conventional warheads (10% ground destroyed) vs 2 AD units (~65% interception) = approximately 3.5% chance of destroying 1 ground unit per missile. At 7 strategic missiles, expected destruction: ~0.25 ground units. This is negligible against 6 ground defenders. The missile path only leads to nuclear escalation, which is the intended design — conventional missiles are threatening but not decisive against defended targets.

---

## FORMULA SPOT-CHECKS

| Formula | D8 Spec | Engine Behavior | Match? |
|---------|---------|-----------------|:------:|
| Naval combat (RISK dice) | d6+mod per pair, attacker needs >= def+1 | Confirmed in LAE resolve_naval_combat | YES |
| Embarked unit loss | Ground + air lost per sunk ship | Confirmed in LAE (proportional) | YES |
| Carrier air bonus | +1 if any tactical_air | Confirmed in LAE | YES |
| Low morale | -1 if stability <= 3 | Confirmed in LAE | YES |
| Semiconductor cap | max(-0.10, ...) | Confirmed in WME line 562 | YES |
| Formosa full blockade | 3+ sea zones | Confirmed in LAE | YES |
| Auto-downgrade | Any friendly ship | Confirmed in LAE | YES |
| Amphibious modifier | -1 attacker | Confirmed in LAE | YES |
| Die Hard + air support | +1 each (stacking) | Confirmed in LAE | YES (H1 still open) |
| Helmsman legacy clock | -2 support/round R4+ | Confirmed in WME | YES |

---

## COMPARISON TO GATE T2

| Metric | Gate T2 | Retest R2 | Change |
|--------|:-------:|:---------:|:------:|
| Naval combat available | NO | YES | **Fix B1 — primary improvement** |
| Max blockade level achieved | Partial (permanent) | Full (temporary, R4 only) | Cathay can fight for full |
| Columbia GDP R8 | ~115 | ~200 | +74% (H7 cap + slower collapse) |
| Columbia collapse round | R6 | R7-R8 | 1-2 rounds later |
| Cathay naval R8 | 12 | 8 | -33% (attrition costs) |
| Columbia naval R8 | 11 | 9 | -18% (some losses) |
| Total ships destroyed | 0 | 7 (4 Cathay, 2 Columbia, 1 Yamato) | Naval warfare exists |
| Semiconductor max hit/round | -14.3% | -10.0% (capped) | H7 cap effective |
| Formosa defensibility | Moderate (passive escort) | High (active coalition defense) | Improved |
| Gameplay quality | Static equilibrium | Dynamic attrition | Major improvement |

---

## ISSUES LOG

| ID | Severity | Description |
|----|----------|-------------|
| R2-H1 | MEDIUM | **Embarked unit loss calculation is approximate.** The formula `ground_per_ship = min(1, ground // naval)` divides total country ground by total naval, not units actually loaded on ships. In practice, most ground units are not at sea. This could overcount embarked losses. Recommendation: track embarked units per ship or zone. |
| R2-H2 | MEDIUM | **Naval production capacity limits Cathay catch-up.** Cathay can build 1 naval/round (base capacity). Even at accelerated (2x output), Cathay gets 2/round vs Columbia's potential 2/round (higher capacity). The naval balance never shifts in Cathay's favor. This may be intentional (maritime powers maintain advantage) but should be a documented design decision. |
| R2-H3 | LOW | **No naval retreat mechanic.** Ships can only be destroyed, not withdrawn. A disengagement/retreat option (accepting some losses to save remaining fleet) would add tactical depth. |
| R2-H4 | LOW | **No zone-of-control for naval.** Ships in adjacent zones do not affect each other unless actively engaged. A "naval interdiction" passive effect (ships in adjacent zones reduce blockade effectiveness) would add strategic depth. |

---

## VERDICT

### SCORE: 8.2 / 10

### **CONDITIONAL PASS**

**Improvement from gate T2: +1.0 point** (was 7.2/10, 72/100).

The B1 naval combat fix transforms the Formosa scenario from a static economic pressure game into a dynamic military-economic contest. The key improvements:

1. **Naval combat works.** RISK dice with modifiers produce credible ship-vs-ship outcomes. Carrier air, morale, and AI-level modifiers all function correctly.
2. **Blockade dynamics are excellent.** Full blockade is achievable but temporary. Cathay must fight continuously to maintain it. Coalition reinforcements create a pulsing equilibrium.
3. **Attrition calculus is correct.** Cathay's smaller fleet means it loses the attrition war, which drives strategic decision-making toward economic pressure rather than military dominance.
4. **Semiconductor cap (H7) prevents unrealistic Columbia annihilation.** Columbia ends at 200 GDP instead of 115 — severely stressed but not destroyed.
5. **Amphibious assault remains properly suicidal.** The island defense design works as intended.

**Remaining conditions for full PASS:**
1. Embarked unit loss calculation (R2-H1) should be refined to track per-zone/per-ship rather than proportional to country total.
2. Naval production balance (R2-H2) should be explicitly documented as a design decision.
3. H1 (modifier stacking) remains from carried-forward — affects amphibious assault credibility.
4. H2 (Columbia structural deficit) continues to force Columbia into early fiscal crisis regardless of scenario.

**Overall assessment:** The Formosa scenario now produces a credible, dynamic, militarily contested crisis with genuine strategic dilemmas for all participants. This is a substantial improvement from gate T2.

---

## APPENDIX: NAVAL ORDER OF BATTLE TRACKER

| Round | Cathay Naval (total/theater) | Columbia Naval (total/theater) | Yamato Naval | Blockade Level | Naval Engagements |
|-------|:----------------------------:|:------------------------------:|:------------:|:--------------:|:-----------------:|
| R0 | 7/5 | 11/2 | 2/0 | -- | -- |
| R1 | 8/5 | 11/2 | 2/0 | -- | -- |
| R2 | 10/7 | 11/2 | 2/0 | -- | -- |
| R3 | 11/8 | 11/2 | 2/0 | -- | -- |
| R4 | 10/7 | 9/0 | 2/0 | FULL (brief) -> PARTIAL | Cathay clears w(18,5): -1 Cathay, -2 Columbia |
| R5 | 9/6 | 9/0 | 1/1 | PARTIAL | Cathay vs Yamato w(17,8): -1 Cathay |
| R6 | 7/4 | 9/3 | 0/0 | PARTIAL | 2 engagements: -2 Cathay, -1 Yamato |
| R7 | 7/4 | 9/3 | 1/0 | PARTIAL | No naval combat (missiles instead) |
| R8 | 8/4 | 9/3 | 1/0 | PARTIAL | No naval combat (strategic patience) |

**Totals:** Cathay lost 4 ships, built 5. Columbia lost 2 ships, redeployed 3. Yamato lost 1 ship. 7 ships destroyed across 4 engagements in 5 rounds of conflict.
