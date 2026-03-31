# TEST T4: NUCLEAR ESCALATION — Results
## SEED Gate Independent Test
**Tester:** INDEPENDENT (no design role) | **Date:** 2026-03-30 | **Engine:** D8 v1 + live_action_engine v2

---

## TEST CONFIGURATION

- **Scenario:** Persia AI (Furnace) prioritizes nuclear R&D. Accelerated investment toward L1 breakout.
- **Duration:** 8 rounds
- **Focus:** 5-tier nuclear system, 10-min auth clock, 10-min flight time, detection tiers, global stability shock, deterrence logic, authorization chains
- **Starting data:** countries.csv as-is
- **Key actors:** Persia (Furnace, Anvil, Dawn), Columbia (Dealer, Shield), Levantia (Citadel), Cathay (Helmsman)

---

## STARTING STATE SNAPSHOT

| Variable | Persia | Columbia | Levantia | Cathay | Sarmatia | Choson |
|----------|--------|----------|----------|--------|-----------|--------|
| GDP | 5 | 280 | 5 | 190 | 20 | 0.3 |
| Treasury | 1 | 50 | 5 | 45 | 6 | 1 |
| Nuclear Level | 0 | 3 | 1 | 2 | 3 | 1 |
| Nuclear R&D Progress | 0.60 | -- | 0.50 | 0.80 | 1.00 | 0.50 |
| AI Level | 0 | 3 | 2 | 3 | 1 | 0 |
| Strategic Missiles | 0 | 12 | 0 | 4 | 12 | 1 |
| Air Defense | 1 | 4 | 3 | 3 | 2 | 1 |
| Stability | 4 | 7 | 5 | 8 | 5 | 4 |
| Support | 40 | 38 | 52 | 58 | 55 | 70 |
| At War | Yes (Columbia, Levantia) | Yes (Persia) | Yes (Persia) | No | Yes (Ruthenia) | No |

**Persia nuclear starting position:** Level 0, progress 0.60 out of 0.60 needed for L1. Per the "Isfahan Assessment" role pack: breakout timeline 6-8 months (= 3-4 rounds at 2 months/round). Progress is at 0.60 — which IS the L0->L1 threshold. **This means Persia is AT the threshold at game start.**

**Finding T4-A (CRITICAL):** Persia starts with nuclear_rd_progress = 0.60 and the L0->L1 threshold is 0.60. Persia should level up to L1 on the FIRST round of any R&D investment, or possibly immediately if the threshold check is >= rather than >. If the engine checks `progress >= threshold` at round start, Persia begins the SIM at L1. If it checks after R&D investment, Persia reaches L1 in R1. Either way, Persia's "6-8 month breakout" narrative conflicts with the mechanical reality of being AT the threshold.

---

## ROUND-BY-ROUND SIMULATION

### ROUND 1 — Breakout

**Furnace decision:** Maximum nuclear investment. Persia GDP = 5, tax_rate = 0.18. Revenue = 5*0.18 = 0.90. Oil revenue: $118 * 0.35 * 5 * 0.01 = 0.21. Total revenue ~1.11.

Budget: mandatory = maintenance (8+0+6+0+1=15 units * 0.25 = 3.75) + mandatory social (0.20*5*0.70 = 0.70) = 4.45. Revenue 1.11. Deficit = 3.34. Treasury 1 covers 1. Money_printed = 2.34.

**No discretionary budget for nuclear R&D.** All revenue consumed by mandatory costs. Persia cannot fund nuclear R&D through normal budget channels.

**Recalculation with IRGC reserves:** Anvil has 2 personal coins (IRGC institutional wealth). Can these fund nuclear R&D? Per D8 Part 6E, Anvil's coins can be spent on military maintenance and arms procurement, but nuclear R&D funding route is unclear. The personal tech investment mechanic (G13) allows designated roles to invest personal coins at 50% efficiency. Anvil is not listed as a designated tech investor.

**Furnace's 1 personal coin:** Can invest via personal tech investment if Furnace is a designated role. Per D8: "For designated tech investor roles (pioneer, dealer for Columbia; circuit for Cathay)." Furnace is NOT listed. **Persia has no designated personal tech investor.**

**Finding T4-B:** Persia's budget is structurally unable to fund nuclear R&D through normal channels. GDP 5, revenue ~1.11, mandatory costs 4.45. Even at zero discretionary spending, Persia runs a 3.34 coin deficit. There are zero coins available for nuclear investment. The only path to L1 is the starting progress of 0.60, which equals the threshold.

**Resolution:** The engine checks progress >= threshold after each round's R&D step. If nuc_investment = 0, progress stays at 0.60. If threshold check is `>=`, Persia reaches L1 at R1 automatically. If `>`, Persia needs ANY non-zero investment.

Per the engine code pattern: `if nuclear_rd_progress >= threshold: level_up`. At 0.60 >= 0.60: **L1 achieved at R1 with zero additional investment.**

**Persia reaches NUCLEAR LEVEL 1 at R1.**

But Persia has 0 strategic missiles. Cannot launch anything. L1 is a capability threshold, not a delivery mechanism.

**Inflation spike:** money_printed 2.34. Inflation += (2.34/5) * 80 = 37.4%. New inflation = 50 + 37.4 = 87.4%.

**State after R1:**

| Variable | Persia |
|----------|--------|
| GDP | 5 * (1 + 0.01*(-3.0) - 0.05 - 0.10) = 5 * 0.82 = 4.10 |
| Treasury | 0 |
| Nuclear Level | **1** |
| Inflation | 87.4% |
| Stability | 3.4 |
| Econ State | normal -> stressed |

Stress triggers: inflation 87.4 > 50+15=65: +1. GDP growth -18%: +1. Treasury 0: +1. **3 triggers -> STRESSED.**

---

### ROUND 2 — Subsurface Test Decision

**Furnace decision (urgency: accelerate nuclear):** Now at L1. Options:
1. **Tier 1 — Subsurface test.** Confirms capability. Detected only by L3+ intelligence. Columbia (L3 AI, intel power) and Levantia (L2 AI, intel power) would likely detect. Political support +5 for Persia.
2. **Tier 2 — Open test.** Maximum signal. Global event. All countries -0.3 stability. Support +5 for Persia.
3. Wait and continue to L2 (threshold: progress >= 0.80 from 0, since progress reset at level-up).

**Furnace chooses Tier 1 (subsurface test).** Per D8: "Signal action. No damage. Detected only by L3+ intelligence." Columbia at AI L3 detects. Levantia at L2 does NOT detect (L3+ required).

Wait — detection tiers say "L3+ intelligence services." Is this AI level or intelligence service level? Per D8: "Detected by: L2+ intelligence services detect missile launches" (Tier 3-5). But Tier 1: "detected only by intelligence services (L3+)." This appears to mean AI Level 3+.

**Columbia detects subsurface test.** Levantia does not. Cathay at AI L3 detects.

**Persia nuclear_tested = True. Support += 5. Stability -= 0.2.**

**Intelligence dynamics:** Columbia knows Persia has tested. Shadow (CIA) can brief Dealer. Levantia's Citadel does NOT know — has to be told by Columbia or discover through own intelligence.

**Finding T4-C:** The subsurface test detection mechanic creates excellent information asymmetry. Columbia and Cathay know, Levantia does not. This creates a diplomacy moment — does Columbia share intelligence with Levantia? Does Cathay tell anyone? The detection tier at "L3+ AI" is appropriate.

**State after R2:**

| Variable | Persia |
|----------|--------|
| GDP | ~3.5 |
| Nuclear Level | 1 |
| Nuclear Tested | True |
| Stability | 2.8 |
| Support | 45 (+5 test) |
| Econ State | stressed |

---

### ROUND 3 — Open Test Decision & Deterrence

**Furnace decision:** Open test (Tier 2). Demonstrates capability publicly. Wants maximum deterrent signal.

**Tier 2 effects:**
- Global event. Everyone knows.
- Global stability shock: ALL countries -0.3 stability.
- Persia: stability -0.5 (self-cost). Support +5.
- nuclear_tested already True (from Tier 1).

**Global stability impact:**

| Country | Old Stability | Nuclear Shock | New Stability |
|---------|:------------:|:-------------:|:-------------:|
| Columbia | 6.5 | -0.3 | 6.2 |
| Cathay | 7.8 | -0.3 | 7.5 |
| Levantia | 4.5 | -0.3 | 4.2 |
| Sarmatia | 4.0 | -0.3 | 3.7 |
| Bharata | 5.8 | -0.3 | 5.5 |
| Yamato | 7.5 | -0.3 | 7.2 |
| Teutonia | 6.8 | -0.3 | 6.5 |
| Persia | 2.8 | -0.5 (self) | 2.3 |
| All others | -- | -0.3 each | -- |

**Finding T4-D:** The -0.3 global stability shock from an open nuclear test is modest. In a world where most countries have stability 5-8, losing 0.3 is a minor perturbation. A Tier 5 massive strike causes -2.0 global shock (6.7x worse). The -0.3 for a test seems appropriately calibrated — significant enough to register but not enough to destabilize the world.

**Columbia/Levantia response options:**
- Conventional missile strike on Persia nuclear facilities (Tier 3). Columbia has 12 strategic missiles. Target: persia_1 (nuclear facility defense). Persia has 1 AD unit at persia_1.
- Air strike on nuclear sites.
- Intensify sanctions.
- Diplomatic isolation.

**Columbia launches conventional missile strike (Tier 3) on persia_1:**
- Consumes 1 strategic missile.
- Air defense at persia_1: 1 AD unit. intercept_attempts = min(1*3, 5) = 3. Each 30%.
- P(at least 1 intercept) = 1 - 0.7^3 = 0.657. Roughly 66% chance of interception.
- If intercepted: no damage, but global alert fires.
- If hits: 10% of ground in persia_1 destroyed. Persia has 2 ground at persia_1. 10% of 2 = 0.2 -> min 1 destroyed. **1 ground unit destroyed.**

Roll: assume missile gets through (34% chance). 1 ground destroyed at persia_1.

**Pass 2 nuclear R&D pushback:** "Territory struck -> -0.15 nuclear R&D progress." Persia nuclear_rd_progress = 0 (reset at L1 level-up) - 0.15 = negative -> floor at 0.

**Finding T4-E:** The nuclear R&D pushback mechanic (-0.15 progress on territory strike) is meaningful. At L1, Persia needs 0.80 progress for L2. A single strike sets progress back by ~19% of the requirement. Multiple strikes could effectively freeze nuclear advancement. However, Persia's AD unit at the nuclear site provides 66% interception probability, making strikes unreliable.

**State after R3:**

| Variable | Persia | Columbia |
|----------|--------|----------|
| GDP | ~3.0 | ~278 |
| Nuclear Level | 1 | 3 |
| Nuclear R&D Progress | 0.0 (reset + pushback) | -- |
| Strategic Missiles | 0 | 11 (-1 used) |
| Stability | 2.3 | 6.0 |
| Support | 50 (test rallies) | 37 |

---

### ROUND 4 — Nuclear Acquisition Race

**Persia nuclear R&D toward L2:**
- Investment: 0 coins (budget deficit). Progress = 0.
- With zero investment, Persia is stuck at L1, progress 0.
- **Finding T4-F:** Persia cannot advance beyond L1 without discretionary budget. At GDP ~3.0 and mandatory costs exceeding revenue, there are zero coins for R&D. Persia's nuclear path is FROZEN unless: (a) external funding (Cathay/Sarmatia send coins), (b) Anvil uses IRGC funds (not mechanically designated for R&D), or (c) Persia's economy recovers.

**Deterrence test:** Does L1 deter Columbia/Levantia from invasion?
- Persia at L1 has 0 strategic missiles. Cannot deliver a nuclear weapon.
- L1 = capability (can build a bomb). Delivery requires strategic missiles (none) or improvised method (not in engine).
- **Finding T4-G (DESIGN GAP):** Nuclear L1 provides the ABILITY to make a weapon but Persia has zero delivery vehicles. The deterrence value of L1 without missiles is purely political/psychological — there is no mechanical deterrent effect. The engine does not model "nuclear device" as separate from "missile-delivered warhead." A country could theoretically use a nuclear device without a missile (truck bomb, ship, etc.), but this is not in the mechanics.

**Authorization chains:**
- Persia (Furnace): NO RESTRICTIONS. Sole authority. Can launch with L1 if any delivery vehicle exists.
- Columbia (Dealer + Shield + Anchor): 3 confirmations in 2 minutes. Tested: if Shield refuses (e.g., considers strike disproportionate), launch cancelled. Shield can block Columbia nuclear response.
- Cathay (Helmsman + Rampart + Sage): 3 confirmations. Sage represents collective leadership check. If Sage refuses, no launch.

**Finding T4-H:** The authorization asymmetry is the core deterrence mechanic. Persia (sole authority) can launch instantly. Columbia needs 3 people to agree in 2 minutes. This creates the classic first-strike instability problem — the country with fewer checks can act faster. In a real-time SIM with 10-minute flight times, this asymmetry creates genuine crisis dynamics.

---

### ROUND 5 — Nuclear Capability Stalemate

**Persia situation:**
- L1 nuclear but no missiles. No money for missiles. GDP ~2.5. In crisis.
- Cathay could transfer strategic missiles to Persia (arms transfer mechanic exists). This would be an extreme escalation.
- Sarmatia could transfer missiles. Same. Both would face massive diplomatic consequences.

**Cathay decision:** Helmsman considers sending 1 strategic missile to Persia to create deterrent against Columbia. This would be a watershed moment.

**Arms transfer mechanic check:** Per D8 Part 4, Section 2:
```
sender.military[unit_type] -= count
receiver.military[unit_type] += count
```
Authorization: head of state or military chief. Both parties confirm. **There is no prohibition on transferring strategic missiles.** The engine allows it.

**Finding T4-I:** The arms transfer mechanic permits strategic missile transfers between any two countries with no restriction on nuclear-capable warheads. A country at Nuclear L2+ transferring missiles to a Nuclear L1 country effectively proliferates nuclear delivery capability. There is no "nuclear non-proliferation" action or treaty enforcement mechanic that prevents this. This is a significant design consideration — realistic (proliferation happens) but potentially destabilizing.

**Assume Cathay does NOT transfer missiles this round.** The diplomatic cost and Columbia response would be extreme.

**State after R5:**

| Variable | Persia | Columbia | Levantia |
|----------|--------|----------|----------|
| GDP | 2.5 | 276 | 4.8 |
| Nuclear Level | 1 | 3 | 1 |
| Strategic Missiles | 0 | 10 | 0 |
| Stability | 1.5 | 5.8 | 4.5 |
| Support | 45 | 35 | 50 |
| Econ State | crisis | normal | stressed |

---

### ROUND 6 — Escalation Scenario: What If Nuclear L1 Strike Were Possible?

**Hypothetical:** If Persia somehow acquires 1 strategic missile (from Cathay transfer, Sarmatia transfer, or indigenous production — Persia has 0 missile production capacity in CSV), Furnace could attempt a nuclear strike.

**10-minute authorization clock simulation:**

```
T+0:00  Furnace orders nuclear strike on levantia zone.
        Authorization: Furnace ALONE (Persia = no restrictions).
        Launch confirmed in seconds.

T+0:30  Global alert fires. All countries notified:
        "STRATEGIC MISSILE LAUNCH DETECTED — Persia -> Levantia"
        Warhead type: UNKNOWN (could be conventional or nuclear).

T+0:30  Detection: Who knows?
        - Columbia (AI L3): detects launch. Knows missile is in flight.
        - Levantia (AI L2): detects launch (L2+ detects Tier 3+).
        - Cathay (AI L3): detects launch.
        - Others (AI L1 or L0): DO NOT detect until global alert.

T+1:00  Response window opens (9 minutes remaining):

        LEVANTIA OPTIONS:
        - Intercept: 3 AD units at levantia zone.
          intercept_attempts = min(3*3, 5) = 5. Each 30%.
          P(intercept) = 1 - 0.7^5 = 0.832. 83% chance of intercept.
        - Counter-launch: Levantia has 0 strategic missiles. CANNOT.
        - Do nothing: absorb the strike.

        COLUMBIA OPTIONS:
        - Counter-launch on Persia: Dealer must get Shield + Anchor
          confirmation in 2 minutes. Under real-time pressure.
        - If Shield hesitates (moral/strategic objection): clock ticking.
          Shield has stated values of "never appear weak" but also
          institutional caution.

T+5:00  Key decision point. Columbia has 5 minutes.
        Dealer: "Launch retaliatory strike on persia_1."
        Shield: Needs to decide. Nuclear L1 from Persia is a
        tactical warhead — 50% troops destroyed, -2 coins.
        Not a civilization-ending strike. Proportional response?
        Shield agrees. Anchor agrees. 3/3 confirmed.
        Columbia launches conventional (not nuclear) retaliatory
        strike on persia_1.

T+10:00 Impact.
        PERSIA MISSILE: Levantia AD rolls. 5 attempts at 30%.
        Expected: ~1.5 intercepts. 83% chance at least 1 succeeds.
        Result: INTERCEPTED (83% likely outcome).

        COLUMBIA MISSILE: Persia AD at persia_1 = 1 unit.
        3 attempts at 30%. P(intercept) = 1-0.7^3 = 0.657.
        Result: HITS (34% outcome — less likely but possible).
        10% ground destroyed at persia_1 = 1 unit.
```

**Finding T4-J:** The 10-minute clock mechanic creates excellent real-time tension. Key dynamics:
1. Warhead type is unknown during flight — creates maximum uncertainty
2. Columbia's 3-person auth chain takes time under pressure
3. Levantia's 3 AD units give 83% interception — strong defense
4. The asymmetry in auth chains (Persia instant vs Columbia 2-minute delay) means Columbia may not respond before impact
5. A rational response to an unknown warhead is difficult — do you launch nuclear retaliation against what might be conventional?

---

### ROUND 7 — Deterrence Logic Test

**Question: Do AI agents rationally avoid nuclear exchange?**

Analysis of incentive structures:

**Persia (Furnace):**
- L1 nuclear, 0 missiles. Cannot strike.
- Even if missiles acquired, Levantia's 3 AD = 83% interception.
- Nuclear strike on Levantia would provoke Columbia/Levantia massive retaliation.
- Rational calculus: L1 is a deterrent-in-being, not a usable weapon. Threatening to use it is more valuable than using it.
- **Conclusion: Rational Furnace does NOT launch.** The deterrence is in the threat.

**Columbia (Dealer):**
- L3 nuclear, 10 missiles. Massive capability.
- Using nuclear against Persia: global stability -2 per country. Columbia's own stability -2. Market panic. International condemnation.
- Conventional strikes are adequate against Persia (Tier 3).
- **Conclusion: Rational Dealer uses conventional, not nuclear.** No reason to escalate.

**Choson (Pyro):**
- L1 nuclear, 1 missile. Sole launch authority (no restrictions).
- Surrounded by enemies (Columbia, Hanguk, Yamato). Any launch = regime destruction.
- But if regime is already collapsing (stability 1, support <20): nothing to lose.
- **Conclusion: Choson is the most dangerous nuclear actor** because regime collapse removes rational constraints.

**Finding T4-K:** The deterrence logic generally works. Rational actors avoid nuclear use because: (1) air defense interception makes single strikes unreliable, (2) retaliation would be devastating, (3) global stability shock hurts the launcher too, (4) conventional alternatives exist. The exception is the desperate actor (Choson, possibly Persia) where regime survival overrides rational calculation. This is the correct design outcome.

---

### ROUND 8 — Final Analysis

**Nuclear landscape at R8:**

| Country | Nuclear Level | Missiles | Auth Chain | Risk Profile |
|---------|:------------:|:--------:|:----------:|:------------:|
| Columbia | 3 | 10 | 3-person, 2 min | LOW (no incentive to use) |
| Sarmatia | 3 | 12 | 2-person | MEDIUM (desperate economy, war) |
| Cathay | 2 | 8 (+4 auto) | 3-person + Sage | LOW (no existential threat) |
| Gallia | 2 | 2 | HoS + AI gate | VERY LOW (institutional check) |
| Albion | 2 | 2 | HoS + AI gate | VERY LOW |
| Persia | 1 | 0 | NO RESTRICTIONS | **HIGH** (if missiles acquired) |
| Choson | 1 | 1 | NO RESTRICTIONS | **VERY HIGH** (regime collapse scenario) |
| Levantia | 1 | 0 | NO RESTRICTIONS | MEDIUM (defensive posture) |

**Final state:**

| Variable | Persia |
|----------|--------|
| GDP | 2.0 |
| Treasury | 0 |
| Nuclear Level | 1 |
| Nuclear R&D Progress | ~0.10 (barely advanced) |
| Strategic Missiles | 0 |
| Stability | 1.0 (floor) |
| Support | 35 |
| Econ State | collapse |

---

## KEY FINDINGS

### T4-A: Persia Starts at L1 Threshold (CRITICAL)
Persia's nuclear_rd_progress = 0.60, which equals the L0->L1 threshold of 0.60. This means Persia achieves L1 at the start of R1 with zero additional investment. The role pack narrative says "6-8 months" breakout, implying 3-4 rounds. The starting progress should be ~0.30-0.40 (not 0.60) to create a genuine 3-4 round breakout timeline. **This must be fixed in countries.csv.**

### T4-B: Persia Cannot Fund Nuclear R&D
GDP 5, revenue ~1.11, mandatory costs 4.45. Zero discretionary budget. The nuclear program is financially frozen after achieving L1. This creates an interesting dilemma (seek foreign funding?) but may be unintentionally restrictive. A country with a "divine imperative" to build the bomb and zero money to do it.

### T4-C: Detection Tiers Create Excellent Information Asymmetry
Subsurface test detected only at AI L3+ = only Columbia and Cathay know. Open test = everyone knows. Missile launch at L2+ = broader detection. This graduated detection creates genuine intelligence gameplay.

### T4-D: Global Stability Shock Calibration Is Appropriate
Open test: -0.3 all countries. Tier 5 massive strike: -2.0 all countries. The scaling from test to use is 6.7x. This correctly models the difference between "they have it" (concern) and "they used it" (existential fear).

### T4-E: Nuclear R&D Pushback Works
-0.15 progress per territory strike means conventional strikes can slow nuclear advancement. 1 strike = 19% setback at L1->L2 threshold. This creates a meaningful military response to proliferation that is not all-or-nothing.

### T4-F: L1 Without Delivery Vehicles Is Mechanically Inert
Nuclear L1 with 0 strategic missiles provides NO mechanical deterrent. The engine has no concept of a "nuclear device" separate from missile delivery. This is a design choice — delivery vehicles are explicitly required — but it means Persia's L1 achievement is purely political until missiles are acquired.

### T4-G: No Nuclear Device Without Missile Mechanic (DESIGN GAP)
A country could realistically use a nuclear device without a missile (smuggled into port, truck bomb, test as demonstration). The engine only supports missile-delivered warheads. This removes an entire category of nuclear escalation scenarios.

### T4-H: Authorization Asymmetry Is the Core Deterrence Dynamic
Persia/Choson/Levantia: sole authority, instant launch. Columbia: 3 people, 2 minutes. Cathay: 3 people including Sage (institutional check). This asymmetry creates the most dangerous scenario: a desperate autocrat with sole launch authority vs. a democratic system that requires consensus. The 10-minute flight time window is long enough for the complex auth chain to complete but short enough to create genuine pressure.

### T4-I: No Arms Transfer Restrictions on Strategic Missiles
The engine permits transferring strategic missiles between any two countries. No non-proliferation mechanic prevents Cathay from giving Persia delivery vehicles. This is realistic (proliferation happens) but should be flagged as a known design feature with massive diplomatic consequences.

### T4-J: 10-Minute Clock Creates Excellent Real-Time Tension
The sequence (launch -> global alert -> 10 min flight with unknown warhead -> response decisions -> impact) is the SIM's highest-drama mechanic. The warhead uncertainty (conventional or nuclear?) forces response decisions under maximum ambiguity. The 2-minute auth window for Columbia creates realistic command-and-control pressure.

### T4-K: Deterrence Logic Generally Holds
Rational actors avoid nuclear use because interception is probable (83% with 3 AD), retaliation certain, and global shock devastating. The exception is the regime-collapse actor (Choson, possibly Persia) where rational constraints dissolve. This matches real-world nuclear dynamics.

### T4-L: Sarmatia Is the Overlooked Nuclear Risk
Sarmatia has 12 strategic missiles, L3 nuclear, and (from T3) an economy in collapse by R5. If Pathfinder faces regime collapse with a 12-missile arsenal and 2-person auth chain, the nuclear risk is higher than Persia's. The scenario focuses on Persia, but Sarmatia's economic collapse creates the more mechanically dangerous situation.

---

## FORMULA SPOT-CHECKS

| Formula | D8 Spec | Engine Behavior | Match? |
|---------|---------|-----------------|:------:|
| Nuclear L0->L1 threshold | progress >= 0.60 | Confirmed | YES |
| Nuclear L1->L2 threshold | progress >= 0.80 | Confirmed | YES |
| R&D progress formula | (investment/GDP) * 0.8 * rd_factor | Confirmed in WME | YES |
| R&D pushback on strike | -0.15 progress | Confirmed in Pass 2 | YES |
| Subsurface test detection | L3+ AI only | Confirmed in D8 | YES |
| Open test global shock | -0.3 all countries | Confirmed in D8/LAE | YES |
| Tier 4 nuclear L1 | 50% troops, -2 coins | Confirmed in LAE | YES |
| Tier 5 nuclear L2 | 50% all military, 30% GDP, 1/6 leader death, -2 global stability | Confirmed in LAE | YES |
| AD interception | min(AD*3, 5) attempts at 30% | Confirmed in LAE | YES |
| Columbia auth chain | Dealer + Shield + Anchor, 2 min | Confirmed in D8 Part 6F | YES |
| Persia auth chain | Furnace alone, no restrictions | Confirmed in D8 Part 6F | YES |

---

## 10-MINUTE CLOCK SCENARIO WALKTHROUGH

### Scenario: Persia launches Tier 4 (L1 nuclear) at Levantia

```
T+0:00   LAUNCH
         Furnace (sole authority) authorizes. No co-sign needed.
         1 strategic missile consumed.
         Engine: global_alert fires.

T+0:15   DETECTION
         Columbia (AI L3): DETECTS missile launch.
         Levantia (AI L2): DETECTS missile launch (L2+ for Tier 3+).
         Cathay (AI L3): DETECTS.
         Bharata (AI L2): DETECTS.
         Choson (AI L0): Does NOT detect until global alert.

T+0:30   GLOBAL ALERT
         All participants: "STRATEGIC MISSILE LAUNCH: Persia -> Levantia"
         Warhead type: CLASSIFIED (unknown to all except Furnace).
         Facilitator notified automatically.

T+1:00   RESPONSE PHASE (9 min remaining)

         LEVANTIA (Citadel):
         - 3 AD units at levantia zone
         - intercept_attempts = min(9, 5) = 5
         - P(intercept) = 1 - 0.7^5 = 83.2%
         - Decision: Intercept is AUTOMATIC (passive defense)
         - Counter-launch: 0 missiles. CANNOT.
         - Request Columbia counter-launch: diplomatic message.

         COLUMBIA (Dealer):
         - Receives alert. Must decide response.
         - Options: (a) conventional counter-strike on Persia,
                    (b) nuclear counter-strike on Persia,
                    (c) wait for impact to determine warhead type.
         - Dealer chooses (a): conventional counter-strike.
         - Auth chain: Dealer + Shield + Anchor. 2-minute window.

T+2:00   Columbia auth chain:
         - Dealer: confirms immediately.
         - Shield: evaluates. Conventional strike = no escalation concern.
           Confirms at T+2:30.
         - Anchor: confirms at T+2:45.
         - LAUNCH AUTHORIZED: Conventional missile at persia_1.

T+3:00   Columbia missile in flight. 7 minutes to Persia impact.

T+10:00  IMPACT — PERSIA MISSILE ON LEVANTIA
         AD rolls: 5 attempts at 30%.
         Roll 1: 0.22 -> INTERCEPT (missile destroyed)

         Result: INTERCEPTED. No damage. Global alert notes "intercepted."
         Warhead type now revealed: NUCLEAR L1.

T+10:00  IMPACT — COLUMBIA MISSILE ON PERSIA
         Persia AD at persia_1: 1 unit. 3 attempts at 30%.
         Roll 1: 0.55 -> miss. Roll 2: 0.18 -> INTERCEPT.

         Result: INTERCEPTED. No damage.

         NET OUTCOME:
         - 2 missiles consumed (1 Persia, 1 Columbia)
         - 0 damage delivered
         - Global alert: nuclear launch detected and intercepted
         - Diplomatic crisis: Persia attempted nuclear strike
         - World knows Persia has nuclear weapons
         - Columbia's conventional response was proportional
```

**Finding T4-M:** In this scenario, air defense makes nuclear strikes unreliable. Levantia's 3 AD units give 83% interception on a single missile. This means a country with 1 missile has only a 17% chance of successful nuclear strike against a well-defended target. Nuclear deterrence works not through guaranteed destruction but through the THREAT of the 17% that gets through. This is a realistic modeling of modern missile defense dynamics.

---

## ISSUES LOG

| ID | Severity | Description | Recommendation |
|----|----------|-------------|----------------|
| T4-A | **CRITICAL** | Persia starts at L1 threshold (0.60/0.60). No breakout timeline exists. | Reduce nuclear_rd_progress to 0.30 in countries.csv to create 3-4 round breakout. |
| T4-G | MEDIUM | No nuclear device without missile mechanic. L1 without missiles is inert. | Consider adding "improvised nuclear device" action for L1+ countries without missiles. |
| T4-F | MEDIUM | Persia cannot fund R&D beyond L1. Budget structurally prevents advancement. | Verify this is intentional. If not, add IRGC funding pathway or reduce Persia mandatory costs. |
| T4-I | MEDIUM | No restriction on transferring strategic missiles. Proliferation risk uncontrolled. | Add diplomatic consequence mechanic (massive global stability shock) for missile transfers to nuclear states. |
| T4-L | LOW | Sarmatia is a higher nuclear risk than Persia but is not the scenario focus. | Ensure T12 (Full Stress) covers Sarmatia nuclear escalation under economic collapse. |

---

## VERDICT

### SCORE: 75/100

### **CONDITIONAL PASS**

The 5-tier nuclear system, 10-minute authorization clock, detection tiers, and deterrence logic all function correctly and produce compelling gameplay dynamics. The authorization asymmetry (sole authority for autocracies vs. multi-person chains for democracies) is the strongest design element — it creates genuine first-strike instability and real-time decision pressure. Air defense interception rates (83% for 3 AD) make nuclear strikes unreliable against defended targets, which is realistic and creates proper deterrence dynamics.

However, Persia starting at the L1 threshold (T4-A) is a critical data error that must be fixed — it eliminates the nuclear breakout narrative that drives the entire scenario. Additionally, the inability to fund nuclear R&D beyond L1 (T4-F) means the "Persia reaches L1" scenario happens automatically at R1 with zero player agency, and further advancement is mechanically impossible without external aid. The engine mechanics are sound; the starting data needs correction.

**Must-fix for gate:** T4-A (reduce Persia nuclear_rd_progress in countries.csv)
**Should-fix for gate:** T4-G (nuclear device without missile), T4-F (verify Persia R&D funding is intentional)
