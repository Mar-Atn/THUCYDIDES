# CARD: ACTION CATALOG

**Source:** CON_C2_ACTION_SYSTEM_v2 + calibration (2026-04-05/06) + Marat review (2026-04-06)
**Rule:** If this card and code disagree, STOP and decide which is right.

---

## COORDINATES

See **CARD_ARCHITECTURE.md → Coordinate Contract** for the full specification.

**Summary:** Every unit on the map has global coordinates. Units on global hexes linked to a local theater map also have local coordinates. Attack/movement validation checks adjacency in both spaces — passes if either is valid.

---

## ROLE AUTHORIZATION

Most actions are role-specific. Key roles and their action rights:

| Role type | Can do |
|---|---|
| **Head of State (HoS)** | Submit budget, tariffs, sanctions, OPEC (if member), attacks, blockade, nuclear auth, treaties, propaganda, arrest, fire/appoint, some covert ops, one-off deals/trades, agreements |
| **Military Chief or Similar** | Attack, deploy, mobilize, naval ops, air/missile strikes, nuclear — confirms, some covert ops |
| **Finance / PM or Similar** | Submit budget (HoS can override). Sanctions. Tariffs. Sign agreements on behalf of country. |
| **Intelligence Director or Similar** | Covert ops (intelligence, sabotage, cyber, disinfo, election meddling). Limited by card pool. |
| **Foreign Affairs Minister / Sec of State or Similar** | Sign treaties and agreements. Deals on behalf of the country. |
| **Opposition Leader** | Must co-sign budget (if majority). Some internal politics cards. |
| **Businessman / Tycoon** | Private investment in AI technology development. Personal transactions. |

Overlapping rights between roles are intentional — creates realistic tension (HoS can deploy, military chief can too, they override each other — actors sort it out).

**Co-sign rules (minimal by design):**
- Budget (Columbia only): must be co-approved by opposition if they hold parliamentary majority
- Nuclear launch: **3-way** confirmation (HoS + military chief + 1 additional authority)

**Special role powers:**
Most covert operations and domestic political actions are distributed as a limited number of individual **action cards** — consumable resources the participant uses to get intended results (+ unintended consequences calculated by engines).

Initial resource pools per role (intelligence cards, sabotage cards, personal coins, etc.) defined in Template → `roles` table. See CARD_TEMPLATE.md.

---

## 1. MILITARY ACTIONS

### 1.1 Move / Deploy / Withdraw
| Field | Value |
|---|---|
| action_type | `move_unit` |
| Fields | `unit_code`, `target_global_row`, `target_global_col` (or `target: "reserve"` to withdraw) |
| Who | HoS or military chief |
| Timing | Between rounds (deployment phase). No intra-round movement except attack advance (surviving attackers move onto captured hex). |
| Three use cases | **Reposition:** active unit → different hex. **Deploy from reserve:** reserve unit → hex (becomes active). **Withdraw to reserve:** active unit → reserve (invisible, cannot be used next round). |
| Range | No range limit during deployment phase. All units can be relocated globally to any suitable hex. |
| Ground/AD/Missile constraints | Cannot move to sea hex. Must target: own territory, country with granted basing rights, or previously occupied hex (must have ≥1 own military unit already there). |
| Air constraints | Same as ground. Can also be loaded onto own naval unit (max 2 air per ship). |
| Naval constraints | Cannot move to land hex. Sea hexes only. |
| Embark | Ground units can load onto own naval (max 1 ground + 2 air per ship). Move with the ship. If ship destroyed → embarked units destroyed. |
| Engine infers | Unit type from `unit_code`, current status (active/reserve/embarked), validates constraints accordingly. If target is a linked hex, engine auto-sets theater coords. |
| Engine | `round_engine/movement.resolve_movement()` + `resolve_mobilization()` |
| Status | **LIVE** |

### 1.2 Declare Martial Law (Conscription)
| Field | Value |
|---|---|
| action_type | `declare_martial_law` |
| Fields | (no parameters — one-off action) |
| Who | HoS |
| Eligible countries | Sarmatia, Ruthenia, Persia, Cathay (all partially mobilized already in current scenario) |
| Mechanic | One-off boost: adds ground units from mobilization pool to reserve (available for deployment next round via `move_unit`). Immediate stability and war tiredness cost. Can only be declared ONCE per SIM. |
| Mobilization pool (Template data) | Sarmatia: 10, Ruthenia: 6, Persia: 8, Cathay: 10 |
| Cost | Stability: **-1.0** immediately. War tiredness: **+1.0** immediately. |
| Engine | `engines/military.resolve_mobilization()` |
| Status | **STUB** — engine exists, needs wiring + template data |

### 1.3 Attack — Ground
| Field | Value |
|---|---|
| action_type | `attack_ground` |
| Fields | `attacker_unit_codes` (list), `target_global_row`, `target_global_col` |
| Who | HoS initiates + military chief confirms |

**RISK mechanic (faithful to classic):**
1. Attacker selects any number of ground units from ONE source hex to attack adjacent hex. Must leave **≥1 ground unit on every occupied foreign hex** (own territory can be emptied).
2. Attacker rolls **min(3, attacking_units)** dice. Defender rolls **min(2, defending_ground_units)** dice.
3. Compare highest vs highest, second vs second. **Ties → defender wins.**
4. Each losing comparison = one unit destroyed from that side.
5. **Iterative** — repeat until all defenders dead OR attacker chooses to stop (in unmanned mode: loop until one side zero).
6. If attacker wins: **ALL surviving attackers move onto captured hex.**
7. **Chain attack:** from the newly captured hex, if attacker has ≥2 units, they can immediately attack another adjacent hex (leaving ≥1 behind). Repeats until stopped by defenders, lack of units, or end of chain.

**Defenders:** ground units on target hex only. Naval does NOT participate in ground combat (separate action: naval bombardment or naval attack).

**Trophies:** non-ground units on captured hex (tactical_air, air_defense, strategic_missile) → captured, become attacker's reserve, original type preserved.

**Undefended hex:** if target has no ground units, attacker occupies without dice. Trophies captured. Chain can continue.

**Occupied territory tracking:** captured hex becomes `occupied_by: attacker` while `owner` remains original country. Relevant for peace negotiations, stability calculations, victory conditions.

**Dice modifiers (SEED ACTION REVIEW 2026-03-30, updated 2026-04-07):**

Applied to **ground combat and naval combat** (both use RISK dice). NOT applied to air strikes, missiles, or bombardment (those use probability rolls).

| Modifier | Side | Value | Condition | Applies to |
|---|---|---|---|---|
| AI L4 bonus | Either | +1 | ai_level==4 AND got 50% random flag at level-up | Ground + Naval |
| Low morale | Either | -1 | Country stability ≤ 3 | Ground + Naval |
| Die Hard terrain | Defender | +1 | Hex has die_hard flag | Ground only |
| Air support | Defender | +1 | Defender has ANY tactical_air on hex | Ground only |
| Amphibious assault | Attacker | -1 | Attack crosses sea→land | Ground only |

**Die Hard + Air support stack** (max positional bonus = +2).

Modifiers applied to the **highest die** of each side per exchange. Integer only — no fractional modifiers.

**Approximate win rates (single 1v1 comparison):**

| Scenario | Attacker wins |
|---|---|
| No modifiers | 42% |
| Defender +1 (die hard OR air) | 28% |
| Defender +2 (die hard + air) | 17% |
| Attacker -1 (amphibious) vs no modifier | 28% |
| Attacker -1 vs defender +2 | 8% |
| Attacker +1 (AI L4) vs no modifier | 58% |

| Engine | `round_engine/resolve_round._process_attack()` + `combat.resolve_ground_combat()` |
| Status | **LIVE** (chain mechanic needs implementation) |

### 1.4 Attack — Air Strike
| Field | Value |
|---|---|
| action_type | `attack_air` |
| Fields | `attacker_unit_codes` (list of tactical_air), `target_global_row`, `target_global_col` |
| Who | HoS + military chief |
| Range | **≤2 hexes** from launcher position. Template-customizable. |
| AD zone | Global hex + all linked theater hexes. |

**Resolution per attacking air unit:**
1. If AD covers target zone: **15% chance attacker is downed** (air unit destroyed, attack fails for this unit).
2. If not downed (or no AD): roll for hit.

| Parameter | Value | Notes |
|---|---|---|
| Hit probability (no AD) | **12%** | Template-customizable |
| Hit probability (AD covers zone) | **6%** (halved) | Template-customizable |
| Attacker downed by AD | **15%** (if AD present) | Template-customizable |

**On hit:** one defender unit destroyed (prefer non-AD target).
**On downed:** attacking air unit destroyed. No hit resolved for that unit.
**All probabilities are Template-customizable** — stored as coefficients, not hardcoded.

| Engine | `round_engine/combat.resolve_air_strike()` |
| Status | **LIVE** (needs attacker-downed mechanic added) |

### 1.5 Attack — Naval vs Naval
| Field | Value |
|---|---|
| action_type | `attack_naval` |
| Fields | `attacker_unit_code` (single naval), `target_unit_code` (single enemy naval) |
| Who | Military chief |
| Mechanic | One-on-one battle. Each side rolls 1d6 + modifiers. Higher wins (ties → defender). Loser destroyed. No movement after — ships stay where they are. |
| Constraint | Attacker must be on same or adjacent sea hex as target. |
| Modifiers | AI L4: +1 (either side). Low morale: -1 (stability ≤ 3, either side). Same as ground. |
| No fleet advantage | No batching. Each naval attack is one ship vs one ship. To destroy a fleet, attack multiple times. |
| Engine | `round_engine/combat.resolve_naval()` |
| Status | **LIVE** (needs simplification from current batch mechanic) |

### 1.7 Attack — Naval Bombardment (ground target)
| Field | Value |
|---|---|
| action_type | `attack_bombardment` |
| Fields | `naval_unit_codes` (list), `target_row`, `target_col` |
| Who | Military chief |
| Mechanic | Each naval unit fires once. **10%** chance per unit to destroy one random ground unit on target hex. |
| Constraint | Naval must be on sea hex adjacent to target land hex. |
| Engine | `engines/military.resolve_naval_bombardment_units()` |
| Status | **STUB** — logged, not processed |

### 1.8 Ballistic Missile Launch

**Common rules (conventional AND nuclear):**
- Same physical `strategic_missile` unit is used for both warhead types. Warhead choice is made at launch.
- Only **deployed missiles** (active on map) can fire. Reserve missiles cannot.
- **One missile unit consumed per launch** (disposable). Unit destroyed after firing regardless of outcome.
- Range depends on country's nuclear tech level: **T1: ≤2 hexes. T2: ≤4 hexes. T3: global (any hex).** Template-customizable.

#### 1.8a Conventional Warhead
| Field | Value |
|---|---|
| action_type | `launch_missile` |
| Fields | `missile_unit_code`, `warhead: "conventional"`, `target_global_row, target_global_col`, `target_choice` (military\|infrastructure\|nuclear_site\|ad) |
| Who | HoS + military chief |

**Targeting:**

Any hex on the map. Target hex can have nothing, military units, or a **nuclear site** (Persia, Choson — placed in Template data). Attacker chooses what to aim at:

| Target choice | Available when | Hit probability | Effect on hit |
|---|---|---|---|
| **Military units** | Units on hex | **70%** | Destroy one unit on hex |
| **Infrastructure** | Any hex of a country | **70%** | 2% GDP damage to target country |
| **Nuclear site** | Hex has nuclear site | **70%** | Halve target's nuclear R&D progress toward next level |
| **AD unit** | AD on hex | **40%** | Targeted AD unit destroyed |

**AD interception of conventional missiles:**
Each AD unit covering the target hex has a **50%** chance of stopping an incoming missile (one attempt per AD unit per missile). Resolved BEFORE the hit roll.

**Resolution order:**
1. Each AD on hex rolls 50% to intercept
2. If intercepted → missile destroyed, no effect
3. If not intercepted → missile rolls for hit (70%, or 40% if targeting AD)
4. If hit → apply chosen damage

All probabilities Template-customizable.

**Nuclear site hexes** (Template v1.0): Persia (specific hex TBD), Choson (specific hex TBD). Stored in Template data as `nuclear_site_hex` per country. Other countries use abstract targeting (no specific hex needed).

**No 3-way authorization** — conventional missiles are not nuclear. Standard HoS + military chief.

| Engine | `engines/military.resolve_missile_strike_units()` |
| Status | **DONE** (code needs abstract targeting added) |

---

### 1.9 Nuclear Program (Tests + Nuclear Launch)

**Prerequisite:** Country must have nuclear capability tier T1+ (achieved via R&D investment → threshold reached → **test required to confirm and unlock**).

**All nuclear actions require 3-way authorization:** HoS + military chief + 1 additional authority.

#### Nuclear Tech Progression (see also CARD_FORMULAS.md → Technology)

```
R&D investment → progress fills → threshold reached → status: "ready for test"
  → successful test → tier CONFIRMED → weapons at this tier unlocked
```

Countries with **pre-defined nuclear levels** in Template data (e.g. Columbia T3, Sarmatia T3, Cathay T3) are **confirmed by default** — no test needed. Testing is only required for countries that DEVELOP new tiers during the SIM via R&D.

#### 1.9a Underground Nuclear Test
| Field | Value |
|---|---|
| action_type | `nuclear_test` |
| Fields | `test_type: "underground"`, `target_global_row, target_global_col` (own territory hex) |
| Who | 3-way authorization |
| Purpose | Confirm nuclear capability at current tech level. Required to unlock weapons use. |
| Success probability | Below T2: **70%**. T2 and above: **95%**. Template-customizable. |
| On success | Nuclear tier CONFIRMED — weapons at this tier unlocked for use. |
| On failure | Test fails — no confirmation. Can retry next round. R&D progress NOT lost. |
| Alert | **Only T3+ countries** receive alert: "Underground nuclear test detected at (row, col)." Other countries unaware. |
| Stability | Global: **-0.2** (all countries). Template-customizable. |
| Engine | `engines/military.resolve_nuclear_test()` |

#### 1.9b Surface Nuclear Test
| Field | Value |
|---|---|
| action_type | `nuclear_test` |
| Fields | `test_type: "surface"`, `target_global_row, target_global_col` (own territory hex) |
| Who | 3-way authorization |
| Purpose | Same as underground — confirms nuclear tier. More visible, more consequences. |
| Success probability | Same as underground (70% / 95%). |
| On success | Nuclear tier CONFIRMED. |
| Alert | **GLOBAL alert** — all countries notified. 10 minutes real-time play triggered. |
| Economic cost | **-5% own GDP** (pollution/contamination). Template-customizable. |
| Stability | Global: **-0.4** (all countries). Adjacent hexes to explosion: **-0.6** additional to those countries' stability. Template-customizable. |
| Engine | `engines/military.resolve_nuclear_test()` |

#### 1.9c Nuclear Missile Launch
| Field | Value |
|---|---|
| action_type | `launch_missile` |
| Fields | `missile_unit_code(s)`, `warhead: "nuclear"`, `target_global_row, target_global_col` per missile |
| Who | **3-way authorization** (HoS + military chief + 1 additional) |
| Constraint | Country must have CONFIRMED nuclear tier. Same missile units as conventional (see 1.8 common rules). |

**Tier determines capability** (same tier/range logic as conventional missiles — nuclear warhead does not change delivery capability, only the payload):

| Tier | Range | Missiles per launch | Requirement |
|---|---|---|---|
| **T1** | Mid-range (≤2 hexes) | 1 missile | Confirmed T1 |
| **T2** | Strategic (≤4 hexes) | 1 missile | Confirmed T2 |
| **T3** | Strategic (global — any hex) | **3+ missiles** (nuclear salvo — up to all available) | Confirmed T3 |

**Resolution per missile:**

1. **T3+ interception** (T2/T3 launches only): every T3+ nation (except launcher) auto-rolls 25% per AD unit they own. Each success destroys 1 missile. Resolved first.
2. **Local AD interception** (T1 launches only): each AD covering target hex rolls **50%** to stop the missile. If stopped → missile destroyed.
3. **Hit roll** (surviving missiles): **80%** base. Template-customizable.
4. **On hit:**
   - **50% of all military units on target hex destroyed** (including attacker's own if present)
   - **30% × (1 / target_country_hex_count) of target GDP destroyed**
   - If target hex has a **nuclear site** → **site automatically destroyed** (100%)
   - All Template-customizable

**T3 Nuclear Salvo aggregate effects** (applied once per salvo if ≥1 nuclear hit lands):
- Global stability: **-1.5**
- Target country stability: **-2.5**
- Leader death roll: **1/6 chance** (target nation HoS, single roll per salvo)
- All Template-customizable

**Global alert:** All countries notified immediately on any nuclear launch. 10 minutes real-time play.

#### 1.9d T3 Nuclear Interception (Decision-based)
| Field | Value |
|---|---|
| action_type | `intercept_nuclear` |
| Fields | `target_missile_salvo_id` (the incoming launch) |
| Who | T3+ countries only. Decision by HoS or military chief. |

**Mechanic:**
- **Target country's own AD:** fires automatically (no decision needed). Each AD unit on the target hex rolls **50%** to stop one missile.
- **Other T3+ countries:** have **10 minutes real-time** to decide whether to attempt interception. This is a VOLUNTARY DECISION — intercepting reveals your capability and is a political act (siding with the target against the launcher).
- Each T3+ country that chooses to intercept rolls **25% per active AD unit** they own. Each success destroys 1 incoming missile.
- **Launcher does NOT learn who intercepted.** Only T3+ nations see launch telemetry (launcher + target).

| Engine | `engines/military.resolve_nuclear_salvo_interception()` |
| Status | **DONE** (code needs voluntary decision mechanic added) |

### 1.10 Naval Blockade
| Field | Value |
|---|---|
| action_type | `blockade` |
| Fields | `zone_id` (chokepoint), `action` (establish\|lift\|partial_lift), `level` (partial\|full) |
| Who | HoS + military chief |

---

#### Caribe Passage Blockade

**Establish:** Any naval unit at the Caribe choke hex can declare blockade (full or partial).

**Partial lift (by another country):** Station a naval unit on any hex adjacent to Caribe (country land hex) and declare partial lift → blockade becomes partial.

**Full lift:** Either blocker decides to lift, OR all blocking naval units destroyed at the choke hex.

**Insisting on full blockade:** All opposing naval units that declared partial lift must be removed from adjacent hexes (destroyed or withdrawn).

**Economic impact:** Reduces Caribe oil export volume. Partial: **-25%**. Full: **-50%**. Reduced supply → oil price rise via supply/demand formula. Template-customizable.

---

#### Gulf Gate Blockade

**Establish:** A naval unit at the Gulf Gate choke hex OR any ground unit on adjacent land hexes (Persia or Mirage territory) can unilaterally declare blockade (full or partial).

**Full lift:** Either blocker decides to lift, OR destroy ALL blocking units — both ground (on adjacent land hexes) AND naval (in choke hex) of the blocking country.

**Key difference from Caribe:** Ground forces can maintain the blockade. Air cannot break a ground blockade — requires ground invasion of the adjacent hex to remove.

**Economic impact:** Reduces oil export volume for Solaria, Mirage. Persia also affected if blocker ≠ Persia. Partial: **-25%**. Full: **-50%**. Same supply/demand cascade. Template-customizable.

---

#### Formosa Strait Blockade

**Establish:** Any naval unit at the Formosa Strait choke hex can declare blockade (full or partial).

**Partial override (by another country):** Any naval unit of another nation on any hex adjacent to Formosa land hex can declare partial lift → blockade becomes partial.

**Full lift:** Destroy all blocking naval units of the blocking country in the choke hex, OR blocker decides to lift.

**Insisting on full blockade against resistance:** Must ensure no naval units of opposing countries remain in any of the 6 hexes surrounding Formosa's land hex (destroyed or withdrawn).

**Economic impact — Formosa Strait is THE semiconductor chokepoint:**

| Effect | Partial blockade | Full blockade |
|---|---|---|
| Formosa GDP | **-10%** | **-20%** |
| All countries GDP | **-10% × country's tech sector size** | **-20% × country's tech sector size** |
| AI R&D progress | **Frozen globally** (no country can advance AI this round) | **Frozen globally** |

All values Template-customizable.

---

#### Economic Cascade (all blockades — implemented in economic engine)

```
1. Blockade declared → affected producers' effective oil production reduced
2. Reduced supply → oil price rises (supply/demand ratio ^ 2.5)
3. Affected producers lose oil revenue (price × reduced_mbpd × 0.009)
4. Oil importers pay more → GDP drag + inflation pressure
5. If price stays above $100 for 3+ rounds → demand destruction kicks in (5%/round)
```

| Engine | `engines/military.resolve_blockade()` + `engines/economic.calc_oil_price()` |
| Status | **LIVE** (oil cascade implemented, blockade resolution needs update to match these mechanics) |

### 1.11 Basing Rights
| Field | Value |
|---|---|
| action_type | `basing_rights` |
| Fields | `counterpart_country`, `action` (grant\|revoke) |
| Who | HoS grants. Host can revoke at any time (unilateral). |
| Effect | Counterpart can deploy/move units to host's territory hexes. |
| Tradeable | Yes — can be granted for free or as part of a transaction (like technology, but REVOCABLE). |
| Template data | Initial basing rights map must exist in Template (reflecting real alliance structure — Western Treaty members host Columbia bases, Asian allies, etc.). |
| Engine | Relationship state update |
| Status | **ABSENT** |

---

## 2. ECONOMIC ACTIONS

### 2.1 Set Budget
| Field | Value |
|---|---|
| action_type | `set_budget` |
| Who | Finance/PM. HoS can override. Columbia: requires parliamentary co-sign (opposition, if majority). |
| Timing | Mandatory each round (submitted between rounds). **If no decision submitted, previous round's settings carry forward (status quo).** |

**The participant sets:**

| Decision | Field | Range | What it does |
|---|---|---|---|
| Social spending | `social_pct` | 0.5–1.5 | Multiplier on social baseline × revenue. <1.0 = austerity (stability risk). >1.0 = generous (stability boost). |
| Military: ground | `ground_coins` + `ground_tier` | coins ≥0, tier: normal\|accelerated\|maximum | Coins + production speed for ground units |
| Military: naval | `naval_coins` + `naval_tier` | same | Coins + production speed for naval units |
| Military: air | `air_coins` + `air_tier` | same | Coins + production speed for tactical air units |
| Tech: nuclear R&D | `nuclear_coins` | ≥0 | Investment in nuclear technology |
| Tech: AI R&D | `ai_coins` | ≥0 | Investment in AI technology |

**Production tiers** (per unit type — speed vs cost tradeoff):

| Tier | Cost multiplier | Output multiplier | Example |
|---|---|---|---|
| normal | 1× | 1× | 3 coins → 1 ground unit |
| accelerated | 2× | 2× | 6 coins → 2 ground units |
| maximum | 4× | 3× | 12 coins → 3 ground units |

**Calculated automatically by engine** (participant does NOT control these):
- Revenue = GDP × tax_rate + oil_revenue − debt − inflation_erosion − war_damage − sanctions_cost
- Military maintenance = total_units × unit_cost × 3.0 (MAINTENANCE_MULTIPLIER) — **automatic, always paid first**
- Military spending capped at 40% of remaining after fixed costs
- Tech spending capped at 30% of remaining after military
- Deficit cascade: spending > revenue → draw treasury → if insufficient → print money (inflation += printed/GDP × 60.0, debt += deficit × 0.15)

See CARD_FORMULAS.md → A.5 Revenue, A.6 Budget Execution, A.7 Military Production for full formulas.

**UI note (human participant phase):** Budget submission screen must show a real-time preview — estimated revenue, maintenance cost, spending total, deficit/surplus, expected unit production, R&D progress, and stability impact — updating as the participant adjusts inputs. All estimates based on current-round data (actual outcomes may differ due to events resolved after submission).

| Engine | `engines/economic.calc_revenue()` + `calc_budget_execution()` + `calc_military_production()` |
| Status | **DONE** (engine fully calibrated), **PARTIAL** (agents don't submit every round yet) |

### 2.2 Set Tariff
| Field | Value |
|---|---|
| action_type | `set_tariff` |
| Fields | `target_country`, `level` (0–3) |
| Who | HoS or PM. Can change any time during round. |
| Timing | Takes effect at next between-rounds engine tick. Previous settings carry forward if unchanged. |

| Level | Meaning | Effect |
|---|---|---|
| L0 | Free trade | No tariff |
| L1 | Light | Mild GDP drag on both sides, small customs revenue for imposer |
| L2 | Moderate | Significant bilateral trade disruption + inflation pressure |
| L3 | Heavy / embargo | Near trade cutoff. Hurts both sides asymmetrically (target more, imposer less). |

**Key:** Tariffs are BILATERAL — set per target country individually. A country can have L0 with allies and L3 with rivals simultaneously. Imposer gets customs revenue but also self-damage (50% of target damage). Target's vulnerability depends on trade openness + sector mix. See CARD_FORMULAS.md → A.3 Tariff Coefficient.

| Engine | `engines/economic.calc_tariff_coefficient()` |
| Status | **LIVE** |

### 2.3 Set Sanction
| Field | Value |
|---|---|
| action_type | `set_sanction` |
| Fields | `target_country`, `level` (0–3) |
| Who | HoS. Can change any time during round. |
| Timing | Takes effect at next engine tick. Previous settings carry forward if unchanged. |

| Level | Meaning | Effect |
|---|---|---|
| L0 | None | No sanctions |
| L1 | Targeted | Mild GDP suppression on target |
| L2 | Broad | Significant damage. Oil producers lose export access. |
| L3 | Maximum | Near-total economic isolation. Devastating if coalition is large. |

**Key:** Sanctions are COALITION-BASED — effectiveness depends on what fraction of world GDP is sanctioning the target (S-curve: 40% coverage → 40% effectiveness, 80% → 80%). Imposing countries also suffer (trade disruption, lost export markets — cost depends on bilateral trade weight). Target adapts over time (diminishing returns after 4 rounds). Tech/services economies more vulnerable than resource economies. See CARD_FORMULAS.md → A.2 Sanctions Coefficient.

| Engine | `engines/economic.calc_sanctions_coefficient()` |
| Status | **LIVE** |

### 2.4 Set OPEC Production
| Field | Value |
|---|---|
| action_type | `set_opec` |
| Fields | `production` (min\|low\|normal\|high\|max) |
| Who | HoS of OPEC member countries only. Previous setting carries forward if unchanged. |

| Level | Multiplier | Effect |
|---|---|---|
| min | 0.70× | Cut production 30% → oil price rises |
| low | 0.85× | Mild cut → moderate price rise |
| normal | 1.00× | Baseline production |
| high | 1.15× | Increased output → price drops |
| max | 1.30× | Flood the market → significant price drop |

Each OPEC member decides independently. Combined effect is weighted by each member's share of global production (with 2× amplifier for cartel leverage). See CARD_FORMULAS.md → A.1 Oil Price.

| Engine | `engines/economic.calc_oil_price()` |
| Status | **LIVE** |

---

## 3. TECHNOLOGY

R&D investment happens via two channels: government budget (section 2.1) and private investment (below). Nuclear R&D progression requires a successful test to confirm each new tier (see 1.9a/1.9b). See CARD_FORMULAS.md → C. Technology for thresholds and formulas.

### 3.1 Private AI Investment
| Field | Value |
|---|---|
| action_type | `private_investment` |
| Fields | `amount` (personal coins), `domain`: ai only |
| Who | Businessman/Tycoon roles only. Uses personal coin balance. |
| Mechanic | Personal coins invested in AI R&D at 50% efficiency (0.4 multiplier vs government's 0.8). |
| **Matching bonus (hidden):** | If BOTH private AND government invest in AI in the same round, combined effect is **2× on AI progress speed**. This synergy is NOT publicly documented — hinted in relevant role briefings only. |
| Engine | `engines/technology.calc_personal_tech_investment()` + matching logic |
| Status | **STUB** (engine function exists, matching bonus needs implementation) |

---

## 4. COVERT OPERATIONS

**General mechanic:** Some roles have a pre-set number of operation "cards" per type. Each use consumes one card. Cards cannot be transferred or sold. Once depleted, that operation type is unavailable for the rest of the SIM.

**Intelligence powers** (higher card pools): Columbia, Cathay, Levantia, Albion, Sarmatia.
**Max ops per round:** default 2, intelligence powers 3.
**Card pools defined in Template** → `roles` table per role.

**Probability modifiers (all ops):**
- AI tech level: +5% success per level
- Repeated ops against same target: -5% success, +10% detection per prior op this SIM
- All probabilities clamped to [5%, 95%] and Template-customizable

---

### 4.1 Intelligence
| Field | Value |
|---|---|
| action_type | `covert_op` |
| Fields | `op_type: "intelligence"`, `question` (free text — the intelligence assignment) |
| Card pool | `intelligence_pool` (per round, replenishes) |
| Detection | **30%**. Attribution: **30%**. Target country may learn someone asked about them. |

**Mechanic:** No probability roll. The system ALWAYS returns a short intelligence report (1-2 paragraphs, max one page). The report is produced by LLM analysis of ALL actual SIM data + run events, with **mandatory noise injection:**

| Question complexity | Noise level | Examples |
|---|---|---|
| Simple, specific | ~10% noise | "Who launched the missile last round?" "Does Persia have nuclear capability?" |
| Moderate | ~20% noise | "How long until Persia reaches nuclear T1?" "What is Cathay's military posture near Formosa?" |
| Complex, broad | ~30% noise | "Give me detailed data on all military and economic parameters of the world" "What are Sarmatia's strategic intentions?" |

**Noise = potential false information** — not just missing data, but actively misleading elements mixed with truth. The LLM judges question complexity based on scope and specificity, using examples as guidance.

**The requester does NOT know the noise level.** They receive the report and must judge its reliability themselves — just like real intelligence.

### 4.2 Sabotage / Terrorism
| Field | Value |
|---|---|
| action_type | `covert_op` |
| Fields | `op_type: "sabotage"`, `target_country`, `target_type` (infrastructure\|nuclear_tech\|military) |
| Card pool | `sabotage_cards` (per SIM, consumable) |
| Success | **50%**. Template-customizable. |
| Detection | **50%**. If detected AND attributed → target country leader learns full details (who attacked, what was targeted). |

**Effect on success (by target type):**

| Target type | Effect |
|---|---|
| **Infrastructure** | **-1 coin** from target country treasury |
| **Nuclear technology** | **-30% progress** of current nuclear tech development stage |
| **Military** | **50% chance** to destroy one random military unit of target country |

Engine calculates the outcome. AI generates a narrative of what happened (explosion, fire, equipment failure, etc.). All values Template-customizable.

### 4.3 Propaganda / Disinformation
| Field | Value |
|---|---|
| action_type | `covert_op` |
| Fields | `op_type: "propaganda"`, `target` (country code — can be OWN country or foreign), `intent` (boost\|destabilize), `content` (free text narrative) |
| Card pool | `disinfo_cards` (per SIM, consumable) |
| Success | **55%** base |

**Two modes:**

| Intent | Target | Effect on success |
|---|---|---|
| **boost** | Own country | Own stability **+0.3** |
| **destabilize** | Foreign country | Target stability **-0.3** |
| **destabilize** | Own country | Own stability **-0.3** (deliberately destabilize own regime — useful for opposition/coup setup) |

Diminishing returns: each successive use against same target in the SIM reduces effect by 50%. AI L3+ boosts effectiveness by +0.1.

**Widely distributed:** Many roles have propaganda/disinfo cards — tycoons, politicians, opposition leaders, intelligence directors, not just HoS. One of the most common covert action types across the role roster.

| Detection | **25%**. Attribution: **20%**. |

### 4.4 Election Meddling
| Field | Value |
|---|---|
| action_type | `covert_op` |
| Fields | `op_type: "election_meddling"`, `target_country`, `candidate`, `direction` (boost\|undermine) |
| Card pool | `election_meddling_cards` (per SIM, consumable) |
| Success | **40%** base. Effect: **+2-5% support** for chosen candidate (if boost) or **-2-5%** (if undermine). Template-customizable. |
| Timing | Can ONLY be used when elections are scheduled next round AND candidates are known. |
| Who has cards | Distributed to select roles both inside and outside the target country (Columbia and Ruthenia have elections — meddling cards held by domestic opposition + foreign intelligence roles). |
| Detection | **45%**. Attribution: **50%**. |

---

**Summary of covert ops (4 types):**

| Op | Cards | Success | Effect | Detection / Attribution |
|---|---|---|---|---|
| Intelligence | per round (replenishes) | always returns report | LLM report with 10-30% noise | 30% / 30% |
| Sabotage | per SIM (consumable) | 50% | target choice: -1 coin OR -30% nuclear progress OR 50% destroy 1 unit | 50% / 50% |
| Propaganda | per SIM (consumable), widely distributed | 55% | ±0.3 stability (own or foreign, boost or destabilize) | 25% / 20% |
| Election meddling | per SIM (consumable), election round only | 40% | ±2-5% support for chosen candidate | 45% / 50% |

| Engine | `engines/military.resolve_covert_op()` |
| Status | **STUB** — framework exists, outcomes need wiring to world state |

---

## 5. TRANSACTIONS

Two distinct types: **exchanges** (transfer of assets) and **agreements** (written commitments).

### 5.1 Exchange Transactions
| Field | Value |
|---|---|
| action_type | `propose_transaction` |
| Fields | `counterpart` (country or individual role), `offer` (what I give), `request` (what I want) |
| Who | Countries (represented by authorized officials — HoS, FM, military chief) OR individuals (representing themselves, using personal assets) |
| Mechanic | Either side proposes, indicating the other side. Counterpart: **accept** (deal done), **decline**, or **counter-offer** (new terms back). Once accepted — deal is **recorded, irreversible, and immediately executed** (coins move, units change ownership, rights transfer). **Validation:** engine confirms both sides have the offered assets (sufficient coins, units exist and are available). If assets not confirmed — deal cannot be completed. |

**Tradeable assets (and ONLY these):**

| Asset | Transfer type | Notes |
|---|---|---|
| **Coins** | Exclusive (sender loses, receiver gains) | From country treasury or personal wallet. Balance check enforced. |
| **Military units** | Exclusive (sender loses, receiver gains) | Any of 5 types. Transferred units go to receiver's **reserve** (deployable next round). Reduced effectiveness for 1 round after transfer. |
| **Basing rights** | Replicable (host keeps sovereignty) | Grant counterpart permission to deploy on your territory. **Revocable** by host at any time. |
| **Technology** | Replicable (sender keeps, receiver gains) | Share nuclear or AI R&D progress. **Irreversible** — cannot be taken back. Receiver gets progress boost (see CARD_FORMULAS → C.4). |

**Any combination is valid.** Examples:
- 3 coins for 1 missile unit — accepted
- Basing rights for 1 AD unit — accepted
- Basing rights for nuclear tech T1 — accepted
- 20 coins + basing rights for 5 ground units — accepted
- Coins for coins (currency exchange between personal wallets) — valid

**NOT tradeable via exchange:** covert op cards (non-transferable), territory (use agreements), promises/commitments (use agreements), sanctions/tariff coordination (use agreements).

| Engine | `agents/transactions.py` (propose/evaluate/execute) |
| Status | **STUB** — code exists, not in round flow |

### 5.2 Agreements
| Field | Value |
|---|---|
| action_type | `propose_agreement` |
| Fields | `signatories` (list of countries), `agreement_name`, `agreement_type`, `visibility` (public\|secret), `terms` (free text) |
| Who | Country authorized officials only (HoS, FM, PM — as defined in role authorization per Template). |
| Parties | **Bilateral** (2 countries) or **multilateral** (3+). Each signatory must confirm. |

**Agreement types** (pre-defined list + participants can create new types):

| Type | Special mechanic |
|---|---|
| `armistice` | Engine-enforced: combat stops, territory frozen at current lines. Temporary — can expire or be breached. Breach = auto re-declaration + all notified. |
| `peace_treaty` | Engine-enforced: war formally ended. Permanent. |
| `trade_agreement` | Recorded. Participants expected to adjust tariffs accordingly. |
| `military_alliance` | Recorded. Coordination commitment — allies decide when to act. |
| `mutual_defense` | Recorded. "Attack on one = attack on all" pledge. No auto-enforcement. |
| `arms_control` | Recorded. Nuclear/missile limits (e.g. Persia caps at T1, missile freeze). |
| `non_aggression` | Recorded. "We won't attack each other." Breach = all notified. |
| `sanctions_coordination` | Recorded. "We both sanction X at level Y." |
| `organization_creation` | Creates new org: NAME + MEMBERS + PURPOSE. |
| *(custom)* | Participants can name any type. Free text terms. Recorded. |

**Visibility:**
- **Public:** all countries can see the agreement name, type, signatories, and full terms.
- **Secret:** only signatories see the agreement. Others unaware it exists. Can be revealed later (voluntarily or via intelligence).

**Mechanic:** Proposer drafts name + type + terms + required signatories. Each signatory confirms or declines. Once all confirm → agreement is **recorded and active**. No engine enforcement except ceasefire and peace treaty — all other agreements rely on trust.

| Engine | `agents/transactions.py` |
| Status | **STUB** — code exists, ceasefire/peace engine mechanics need wiring |

---

## 6. DOMESTIC / POLITICAL

### 6.1 Arrest
| Field | Value |
|---|---|
| action_type | `arrest` |
| Fields | `target_role` (the person to arrest) |
| Who | Any authority figure (HoS, military chief, intelligence) on own soil. |
| Constraint | Target must be physically on the arresting country's soil (in SIM terms: in the same room/space). |
| Execution | **Moderator-confirmed only.** Moderator verifies the target is on the arresting country's soil, then executes. |
| Effect | Arrested actor is **inactive** — moved to a dedicated holding space until end of round. Cannot attend meetings, make decisions, or communicate. Released at round end. |
| Engine | State change on role (status: active → arrested → active at round end) |
| Status | **ABSENT** |

### 6.2 Assassination
| Field | Value |
|---|---|
| action_type | `assassination` |
| Fields | `target_role`, `domestic` (bool) |
| Who | Card-based (assassination_cards, per SIM, consumable). |
| Execution | **Moderator-confirmed only.** Moderator rolls, confirms result, and makes public announcement. |

| Scenario | Success probability |
|---|---|
| Domestic | **30%** |
| International (default) | **20%** |
| International (Levantia) | **50%** |

| Detection | **100%** — everyone knows an attempt was made. |
| Attribution | **50%** — publicly known who ordered it (50% chance). |

**Outcome if successful:** 50/50 kill vs survive-injured. Martyr effect: +15 political support (kill) or +10 (survive) for the target's country. All Template-customizable.

| Engine | `engines/military.resolve_assassination()` |
| Status | **DONE** (engine needs probability update), **ABSENT** (agent schema) |

### 6.3 Fire / Reassign
| Field | Value |
|---|---|
| action_type | `fire_role` |
| Fields | `target_role` (must be a direct report) |
| Who | Any role with authority over the target (HoS fires ministers, military chief reassigns officers, etc.) |
| Mechanic | Target loses current powers. Stays in game (can be reassigned to another position, or remains powerless). **Must be public** — all participants notified. |
| Status | **ABSENT** |

*(Domestic propaganda covered by covert ops 4.3 — Propaganda/Disinformation with target: own country, intent: boost.)*

### 6.4 Coup Attempt
| Field | Value |
|---|---|
| action_type | `coup_attempt` |
| Fields | `initiator_role`, `co_conspirator_role` |
| Who | Any two roles within the SAME country. Both must independently agree to participate. |
| Execution | **Moderator-confirmed.** Moderator verifies both conspirators, rolls, announces result. |

**Probability:**
| Factor | Modifier |
|---|---|
| Base | **15%** |
| Active protest in the country | +25% |
| Stability < 3 | +15% |
| Stability 3-4 | +5% |
| Political support < 30% | +10% |
| Clamp | [0%, 90%] |

**Success:** Initiator becomes HoS. Old HoS arrested. Stability **-2**. World notified.
**Failure:** Both conspirators exposed/arrested. Stability **-1**. World notified.

All Template-customizable.

| Engine | `engines/military.resolve_coup()` (SEED, exact match) |
| Status | **DONE** (engine), **ABSENT** (agent schema) |

### 6.5 Lead Mass Protest (Revolution)
| Field | Value |
|---|---|
| action_type | `lead_protest` |
| Fields | `leader_role` |
| Who | Any elite role in the country (opposition leader, military chief, etc.). Can only be attempted when stability ≤ 2 AND support < 20% (engine flags protest_risk). |

**Probability:** 30% base + (20 - support)/100 + (3 - stability) × 10%. Clamp [15%, 80%].

**Success:** Regime change — protest leader becomes HoS. Old HoS deposed. Stability **+1** (new hope). Political support **+20** (fresh mandate).
**Failure:** Protest crushed. Leader imprisoned. Stability **-0.5**. Support **-5** (fear).

| Engine | SEED `live_action_engine.resolve_protest_action()` |
| Status | **DONE** (SEED code), **ABSENT** (not ported to BUILD yet) |

### 6.6 Elections (Scheduled)
| Field | Value |
|---|---|
| action_type | (automatic — triggered by schedule, not player action) |
| Mechanic | Elections are pre-scheduled in Template data. Engine processes them at the designated round. |

**Schedule (Template v1.0):**

| Round | Election | Country | Trigger |
|---|---|---|---|
| R2 | Mid-term parliamentary | Columbia | Automatic (scheduled) |
| R5 | Presidential election | Columbia | Automatic (scheduled) |
| — | Wartime election | Ruthenia | NOT scheduled. Triggered by: HoS of Ruthenia voluntarily, OR 2+ Ruthenian participants demand it, OR full Ruthenian team consensus. One-off event. |

**Result:** 50% AI score (based on GDP growth, stability, war outcomes, foreign policy) + 50% player voting/campaign. Incumbent wins if final score ≥ 50%. See CARD_FORMULAS.md → B.3 Elections.

| Engine | `engines/political.process_election()` (SEED, exact match) |
| Status | **DONE** (engine), **PARTIAL** (not wired into round flow) |

### 6.7 Call Early Elections
| Field | Value |
|---|---|
| action_type | `call_early_election` |
| Who | HoS (voluntarily) or opposition (if they have parliamentary majority — Columbia only) |
| Mechanic | Triggers election process in the NEXT round. Uses same election engine as scheduled elections. |
| Status | **ABSENT** |

---

## 7. COMMUNICATIONS

### 7.1 Bilateral Meetings
| Field | Value |
|---|---|
| action_type | (handled by active loop, not commit_action) |
| Who | Any participant, any time, with any other participant (AI or human). |
| Mechanic | One participant initiates, the other accepts or declines. 8-turn conversation max. Intent notes prepared privately before. Memory reflection after. |
| Multilateral note | Multilateral meetings (3+ participants) are a future capability. For now, bilateral only. Complex negotiations happen through sequential bilateral meetings. |
| Engine | `agents/conversations.run_bilateral()` |
| Status | **DONE** (code), **ABSENT** (not wired into round flow — Priority 1 for Sprint B) |

### 7.2 Organization Meetings
| Field | Value |
|---|---|
| action_type | `call_org_meeting` |
| Fields | `organization_code`, `agenda` (free text) |
| Who | Any member of the organization |
| Organizations | Western Treaty (NATO), Eastern Pact (BRICS), EU, UNSC, OPEC+, player-created orgs |
| Mechanic | Multi-party meeting. Suggest time + venue. No enforcement. |
| Status | **STUB** |

### 7.3 Public Statement
| Field | Value |
|---|---|
| action_type | `public_statement` |
| Fields | `content` (short free text message) |
| Who | Any participant. Any time. No authorization needed. |
| Mechanic | Broadcast to all via public information interface. Attributed to the author. Logged permanently. Covers: war declarations, peace offers, threats, ultimatums, speeches, claims, denials — anything the participant wants the world to hear. |
| Status | **LIVE** |

### Pre-seeded meetings (Template data)

The first 1-2 rounds include **3-4 pre-scheduled meetings** seeded in Template data to kickstart the simulation and give participants immediate engagement. These are set with agenda, location, and participants. Examples for Template v1.0:

- UNSC urgent session — Persia nuclear crisis (R1)
- OPEC+ extraordinary meeting — oil production response (R1)
- Peace talks in Phrygia — Ruthenia, Columbia, Sarmatia representatives (R1-R2)
- Bilateral summit — Columbia-Cathay (R1)

The exact list is part of the **scenario configuration** (can vary per event). Format: `{round, meeting_type, organization_or_bilateral, participants, agenda, location}`.

---

## ACTION → CONSEQUENCE CHAINS

Each action triggers immediate + deferred engine effects. Key cascades:

| Action | Immediate (Phase A) | Deferred (Phase B engine tick) |
|---|---|---|
| **Ground attack** | Dice → casualties, territory changes, trophies captured | War tiredness ↑, stability ↓, GDP ↓ (infrastructure damage), political support shift |
| **Air strike** | Hit/miss + possible attacker downed | — |
| **Nuclear launch** | Interception rolls → hit → 50% military destroyed | GDP ↓ (30%/hex), global stability -1.5, target stability -2.5, leader death roll |
| **Blockade (Gulf Gate)** | Oil export volume reduced (25%/50%) | Oil price ↑ → importer GDP ↓ + inflation ↑, producer revenue ↓ |
| **Blockade (Formosa)** | Semiconductor supply cut | All countries GDP ↓ (×tech sector), AI R&D frozen globally |
| **Set tariff L3** | — | Target GDP ↓ (K=0.54 × exposure), imposer GDP ↓ (50% of target), customs revenue ↑, inflation ↑ |
| **Set sanction L3** | — | Target GDP ↓ (S-curve × coverage), imposer trade disruption, target adapts over rounds |
| **Budget: austerity (social<0.7)** | — | Stability **-0.30**, treasury saved |
| **Budget: deficit spending** | — | Money printed → inflation ↑ (×60 multiplier), debt ↑ (×0.15) |
| **Sabotage (nuclear site)** | 50% success: -30% nuclear progress | If detected+attributed: diplomatic consequences |
| **Ceasefire signed** | Combat stops, territory frozen | War tiredness starts decaying (-20%/round) |
| **Martial law** | +troops to reserve | Stability **-1.0**, war tiredness **+1.0** |

**Cascade example:** Sarmatia blockades Gulf Gate → Solaria/Mirage oil exports -50% → global oil supply drops → price rises to ~$130 → Columbia (importer) GDP drag -2% → Columbia revenue drops → budget deficit → money printing → inflation → stability -0.15 → political support drops → election pressure on Dealer.

---

## SUMMARY

### Action count by category

| Category | Actions | Description |
|---|---|---|
| 1. Military | 11 | Move/deploy, martial law, ground attack, air strike, naval combat, bombardment, conventional missile, nuclear program (test+launch+interception), blockade, basing rights |
| 2. Economic | 4 | Budget, tariffs, sanctions, OPEC production |
| 3. Technology | 1 | Private AI investment (govt R&D is in budget) |
| 4. Covert | 4 | Intelligence, sabotage, propaganda, election meddling |
| 5. Transactions | 2 | Exchange (assets) + Agreements (written commitments) |
| 6. Domestic/Political | 7 | Arrest, assassination, fire, coup, mass protest, scheduled elections, early elections |
| 7. Communications | 3 | Bilateral meetings, org meetings, public statement |
| **TOTAL** | **32** | |

### Implementation status

| Status | Count | Meaning |
|---|---|---|
| **LIVE** | 8 | Running in test harness now |
| **DONE** | 6 | Engine code exists and tested, not wired into round flow |
| **STUB** | 12 | Logged/framework exists, needs engine wiring |
| **ABSENT** | 6 | Not yet coded |
