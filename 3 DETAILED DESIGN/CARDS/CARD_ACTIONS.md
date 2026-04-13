# CARD: ACTION CATALOG

**Source:** CON_C2_ACTION_SYSTEM_v2 + calibration (2026-04-05/06) + Marat review (2026-04-06)
**Rule:** If this card and code disagree, STOP and decide which is right.
**Round Flow:** See `CONTRACT_ROUND_FLOW.md` for Phase A / Phase B / Inter-Round architecture.
**Dispatcher:** All actions route through `engine/services/action_dispatcher.py`.

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

### 1.1 Move Units (CONTRACT_MOVEMENT v1.0) 🔒

**Canonical contract:** `PHASES/UNMANNED_SPACECRAFT/CONTRACT_MOVEMENT.md` (v1.0 LOCKED 2026-04-11). This section summarizes — the contract is authoritative where it conflicts with SEED_D8 Part 6B.

| Field | Value |
|---|---|
| action_type | `move_units` (PLURAL — full replacement for legacy singular `move_unit`) |
| Envelope | `action_type`, `country_code`, `round_num`, `decision` ∈ {`change`, `no_change`}, `rationale` (≥30 chars REQUIRED on both branches), `changes.moves[]` (only when decision=change) |
| Move shape | `unit_code`, `target` ∈ {`hex`, `reserve`}, plus `target_global_row` + `target_global_col` when target=`hex` |
| Who | HoS or military chief (one batch per country per round — last-submission-wins) |
| Timing | Submitted during round N → applied at round-end by `resolve_round(N)` → visible as round N's `unit_states_per_round` snapshot (read as start of round N+1). No transit delay. |
| Three use cases | **Reposition:** active unit → new hex. **Deploy from reserve:** reserve unit → hex (becomes active). **Withdraw to reserve:** active unit → reserve. |
| Two auto-flows | **Embark:** ground/tactical_air moving onto a hex with a friendly naval carrier with capacity → auto-embark. **Debark:** embarked unit's hex target auto-clears `embarked_on` first. |
| Range | UNLIMITED. No hex-distance constraint. Spatial legality is type-based + territory-based. |
| Ground / AD / Strategic Missile | Target hex must NOT be sea. Must be in **own territory**, **basing-rights zone**, OR **previously occupied hex** (≥1 own active unit already there). |
| Tactical Air | Same as ground, PLUS can auto-embark on own naval. |
| Naval | Sea hexes only. Cannot touch land. |
| Carrier capacity | 1 ground + 2 tactical_air per friendly naval (total 3 embarked slots). |
| Batch semantics | Atomic. If any move in the batch is invalid, the entire batch is rejected with all errors reported. Batch-internal state propagates — move #1's new position qualifies move #2's "previously occupied" check. |
| Duplicate unit in batch | Rejected (`DUPLICATE_UNIT_IN_BATCH`). One unit = one move per round. |
| Validator | `engine/services/movement_validator.py:validate_movement_decision(payload, units, zones, basing_rights)` — 17 error codes. |
| Engine | `engine/engines/movement.py:process_movements(moves, country_code, units, zones)` — pure state mutator. |
| Persistence | `country_states_per_round.movement_decision` JSONB audit column (per-round envelope, incl. no_change) + `unit_states_per_round` (outcome — positions/status). |
| Observatory events | `movement_applied` (on valid change), `movement_no_change` (on valid no_change), `movement_rejected` (on invalid). |
| Status | **LIVE** (M1 vertical slice DONE 2026-04-11) |

### 1.2 Declare Martial Law (Conscription)
| Field | Value |
|---|---|
| action_type | `declare_martial_law` |
| Fields | (no parameters — one-off action) |
| Who | HoS |
| Eligible countries | Sarmatia, Ruthenia, Persia, Cathay (all partially mobilized already in current scenario) |
| Mechanic | One-off boost: adds ground units from martial-law pool to reserve (available for deployment next round via `move_units`). Immediate stability and war tiredness cost. Can only be declared ONCE per SIM. |
| Martial-law pool (Template data) | Sarmatia: 10, Ruthenia: 6, Persia: 8, Cathay: 10 |
| Cost | Stability: **-1.0** immediately. War tiredness: **+1.0** immediately. |
| Engine | `services/martial_law_engine.py` + `services/domestic_validator.py` |
| Status | **LIVE — slice locked v1.0 (2026-04-13)** — see `CONTRACT_MARTIAL_LAW.md` |

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

| Engine | `round_engine/resolve_round._process_attack()` + `engines/military.resolve_ground_combat()` (canonical) |
| Status | **LIVE — slice locked v1.0 (M2, 2026-04-12)** — see `CONTRACT_GROUND_COMBAT.md` |

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

| Engine | `engines/military.resolve_air_strike()` (canonical M3) |
| Status | **LIVE — slice locked v1.0 (M3, 2026-04-12)** — see `CONTRACT_AIR_STRIKES.md` |

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
| Engine | `engines/military.resolve_naval_combat()` (canonical M4) |
| Status | **LIVE — slice locked v1.0 (M4, 2026-04-12)** — see `CONTRACT_NAVAL_COMBAT.md` |

### 1.7 Attack — Naval Bombardment (ground target)
| Field | Value |
|---|---|
| action_type | `attack_bombardment` |
| Fields | `naval_unit_codes` (list), `target_row`, `target_col` |
| Who | Military chief |
| Mechanic | Each naval unit fires once. **10%** chance per unit to destroy one random ground unit on target hex. |
| Constraint | Naval must be on sea hex adjacent to target land hex. |
| Engine | `engines/military.resolve_bombardment()` (M5 canonical) |
| Status | **LIVE — slice locked v1.0 (M5, 2026-04-12)** — see `CONTRACT_NAVAL_BOMBARDMENT_BLOCKADE.md` |

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
| Engine | `orchestrators/nuclear_chain.NuclearChainOrchestrator` (M6 canonical) |

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
| Engine | `orchestrators/nuclear_chain.NuclearChainOrchestrator` (M6 canonical) |

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

| Engine | `orchestrators/nuclear_chain.NuclearChainOrchestrator` (M6 canonical — handles full 4-phase chain including voluntary interception) |
| Status | **LIVE — slice locked v1.0 (M6, 2026-04-13)** — see `CONTRACT_NUCLEAR_CHAIN.md` |

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
| Status | **LIVE — slice locked v1.0 (M5, 2026-04-12)** — see `CONTRACT_NAVAL_BOMBARDMENT_BLOCKADE.md` |

### 1.11 Basing Rights
| Field | Value |
|---|---|
| action_type | `basing_rights` |
| Fields | `counterpart_country`, `action` (grant\|revoke) |
| Who | HoS grants. Host can revoke at any time (unilateral). |
| Effect | Counterpart can deploy/move units to host's territory hexes. |
| Tradeable | Yes — can be granted for free or as part of a transaction (like technology, but REVOCABLE). |
| Template data | Initial basing rights map must exist in Template (reflecting real alliance structure — Western Treaty members host Columbia bases, Asian allies, etc.). |
| Engine | `services/basing_rights_engine.py` + `services/basing_rights_validator.py` |
| Status | **LIVE — slice locked v1.0 (2026-04-13)** — see `CONTRACT_BASING_RIGHTS.md` |

---

## 2. ECONOMIC ACTIONS

> **Mandatory Decisions (added 2026-04-08):** Budget, tariffs, sanctions, and OPEC production are MANDATORY per-round decisions, not optional. Each participant must submit these before the round ends. The system prompts participants ~2 minutes before deadline. If not submitted by deadline, previous round's values carry forward as defaults. In unmanned mode, AI agents are explicitly prompted to submit these before committing other actions.

### 2.1 Set Budget — CONTRACT_BUDGET v1.1 (🔒 locked 2026-04-10)
| Field | Value |
|---|---|
| action_type | `set_budget` |
| Who | Finance/PM. HoS can override. Columbia: requires parliamentary co-sign (opposition, if majority). |
| Timing | Mandatory each round (submitted between rounds). **`no_change` is a valid explicit choice; if no decision is submitted at all, previous round's settings carry forward.** |
| Spec | `PHASES/UNMANNED_SPACECRAFT/CONTRACT_BUDGET.md` v1.1 — single source of truth for schema, validation, persistence, engine behavior |

**Decision schema:**

```json
{
  "action_type": "set_budget",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change",
  "rationale": "string, ≥30 chars, required even on no_change",
  "changes": {
    "social_pct": 1.0,
    "production": {
      "ground":            0|1|2|3,
      "naval":             0|1|2|3,
      "tactical_air":      0|1|2|3,
      "strategic_missile": 0|1|2|3,
      "air_defense":       0|1|2|3
    },
    "research": {
      "nuclear_coins": 0,
      "ai_coins":      0
    }
  }
}
```

**The participant sets:**

| Decision | Field | Range | What it does |
|---|---|---|---|
| Social spending | `social_pct` | 0.5–1.5 (continuous slider) | Multiplier on `social_baseline × revenue`. <1.0 = austerity (Δ stability = (social_pct−1.0)×4). >1.0 = generous (Δ stability positive). |
| Production | `production.{branch}` | int 0..3 per branch (all 5 required) | Discrete level per branch. 0=none, 1=normal, 2=accelerated (2×cost, 2×output), 3=maximum (4×cost, 3×output, "emergency gear"). |
| Research | `research.{nuclear,ai}_coins` | int ≥ 0 each (both required) | Direct coin allocation. Progress = (coins/GDP)×0.8 per round. |

**Branch unit costs (level 1, coins per unit):** ground 3, naval 6, tactical_air 5, strategic_missile 8, air_defense 4.
**Strategic_missile and air_defense:** capacity 0 for all countries in v1.1 — schema present, levels accepted, but produces 0 units until capacities are raised in a future template version.

**Calculated automatically by engine** (participant does NOT control these):
- `revenue = GDP × tax_rate + oil_revenue − debt − inflation_erosion − war_damage − sanctions_cost`
- `maintenance = total_units × maintenance_per_unit × 3.0` — paid first, before any participant allocations
- **No percentage caps.** Over-spending feeds the deficit cascade: drain treasury → print money (inflation += printed/GDP × 60.0) → debt += deficit × 0.15. When the cascade can't fully fund military, branch production is scaled proportionally by affordability — not a hard cap.
- `stability_delta = (social_pct − 1.0) × 4.0`, `political_support_delta = (social_pct − 1.0) × 6.0`

See CARD_FORMULAS.md A.6 (Budget Execution) + A.7 (Military Production) for the engine flow, and `CONTRACT_BUDGET.md` for the canonical contract.

**Validation:** all submissions go through `app/engine/services/budget_validator.py` which returns `{valid, errors, warnings, normalized}`. Invalid submissions emit a `budget_rejected` observatory event and the round still completes using the previous round's values.

**Context package** (assembled by `app/engine/services/budget_context.py`): every decision-maker (AI or human) gets the country's economic state, mandatory cost forecast, current budget, and a **dry-run "no-change forecast"** — running the actual engine on a deep-copy to show "what happens if you do nothing." Same engine code as the real round = single source of truth.

**UI note (human participant phase):** the budget submission screen will reuse `build_budget_context` + `dry_run_budget` to show a live preview that updates as the participant adjusts inputs. Same context, different rendering.

| Engine | `engines/economic.calc_budget_execution()` + `calc_military_production()` + `calc_tech_advancement()` |
| Status | ✅ **DONE** end-to-end (CONTRACT v1.1, validator, context+dry-run, persistence, AI acceptance gate). See `CHECKPOINT_BUDGET.md`. |

### 2.2 Set Tariffs — CONTRACT_TARIFFS v1.0 (🔒 locked 2026-04-10)
| Field | Value |
|---|---|
| action_type | `set_tariffs` (plural — one submission carries the country's full intent for the round) |
| Who | HoS or PM. Columbia: PM can override, HoS can override PM. |
| Timing | Mandatory each round (submitted between rounds). **`no_change` is a legitimate explicit choice; if no decision is submitted at all, previous round's tariffs carry forward via the state table.** |
| Spec | `PHASES/UNMANNED_SPACECRAFT/CONTRACT_TARIFFS.md` v1.0 — single source of truth for schema, validation, persistence, engine behavior |

**Decision schema:**

```json
{
  "action_type": "set_tariffs",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change",
  "rationale": "string, ≥30 chars, required even on no_change",
  "changes": {
    "tariffs": {
      "cathay": 3,
      "caribe": 1
    }
  }
}
```

**The participant sets:**

| Field | Shape | Semantics |
|---|---|---|
| `decision` | `"change"` or `"no_change"` | Explicit choice. `no_change` is legitimate. |
| `rationale` | string ≥30 chars | Required in BOTH branches. Forces explicit reasoning. |
| `changes.tariffs` | sparse dict `{target_code: int 0..3}` | Only name targets you want to change. All untouched targets carry forward from the `tariffs` state table. |

**Tariff level scale:**

| Level | Meaning | Effect (CARD_FORMULAS A.3) |
|---|---|---|
| 0 | none / lift | Engine treats as no tariff. Level=0 lifts an existing row. |
| 1 | light | `intensity = 0.33`. Mild GDP drag both sides, small customs revenue. |
| 2 | moderate | `intensity = 0.67`. Significant bilateral disruption + inflation pressure. |
| 3 | heavy / near-embargo | `intensity = 1.00`. Near trade cutoff. Hurts both sides asymmetrically (target ~2× imposer via `TARIFF_IMPOSER_FRACTION = 0.5`). |

**Key:** Tariffs are BILATERAL — set per target country individually. A country can have L0 with allies and L3 with rivals simultaneously. Imposer gets customs revenue but also self-damage (~50% of target damage). Target's vulnerability depends on trade openness + sector mix + imposer's market share.

**Validation:** all submissions go through `app/engine/services/tariff_validator.py` which returns `{valid, errors, warnings, normalized}` with 11 error codes (per CONTRACT §4). Invalid submissions emit a `tariff_rejected` observatory event and the round still completes using previous round's tariffs.

**Persistence:**
- Canonical world state → `tariffs` state table (existing, unchanged)
- Per-round decision audit → `country_states_per_round.tariff_decision` JSONB (new 2026-04-10)

**Context package** (assembled by `app/engine/services/tariff_context.py`): every decision-maker (AI or human) gets the country's economic state, ALL 20 countries with trade rank from `derive_trade_weights()`, current bilateral tariffs in both directions, decision rules with no_change reminder, and the instruction. **Decision-specific context only — cognitive context (identity/memory/goals/world rules) is provided by the AI Participant Module (future), not by this contract.** See `PHASES/UNMANNED_SPACECRAFT/CONTRACT_TARIFFS.md` §3.

**Legacy compatibility:** the singular `set_tariff` and `lift_tariff` actions still work in parallel. New code should use `set_tariffs` (plural).

| Engine | `engines/economic.calc_tariff_coefficient()` — UNCHANGED, behavior locked by L1 regression tests |
| Status | ✅ **DONE** end-to-end (CONTRACT v1.0, validator, context, persistence, AI acceptance gate). See `CHECKPOINT_TARIFFS.md`. |

### 2.3 Set Sanctions — CONTRACT_SANCTIONS v1.0 (🔒 locked 2026-04-10)
| Field | Value |
|---|---|
| action_type | `set_sanctions` (plural — one submission carries the country's full intent for the round) |
| Who | HoS. |
| Timing | Mandatory each round (submitted between rounds). **`no_change` is a legitimate explicit choice; if no decision is submitted at all, previous round's sanctions carry forward via the state table.** |
| Spec | `PHASES/UNMANNED_SPACECRAFT/CONTRACT_SANCTIONS.md` v1.0 — single source of truth for schema, validation, persistence, engine behavior |

**Decision schema:**

```json
{
  "action_type": "set_sanctions",
  "country_code": "columbia",
  "round_num": 3,
  "decision": "change",
  "rationale": "string, ≥30 chars, required even on no_change",
  "changes": {
    "sanctions": {
      "persia":  3,
      "choson":  3,
      "bharata": 0
    }
  }
}
```

**The participant sets:**

| Field | Shape | Semantics |
|---|---|---|
| `decision` | `"change"` or `"no_change"` | Explicit choice. `no_change` is legitimate. |
| `rationale` | string ≥30 chars | Required in BOTH branches. |
| `changes.sanctions` | sparse dict `{target_code: int [-3, +3]}` | Only name targets you want to change. Untouched targets carry forward. |

**Level scale (signed for evasion support):**

| Level | Meaning | Effect |
|---|---|---|
| **+3** | Maximum sanctions | Full intensity — imposer contributes `own_gdp_share × 1.0` to coverage |
| **+2** | Broad sanctions | Strong intensity — contributes `own_gdp_share × 0.67` to coverage |
| **+1** | Targeted sanctions | Mild intensity — contributes `own_gdp_share × 0.33` to coverage |
| **0** | None / lift | No contribution; level=0 lifts any existing row |
| **−1** | Light evasion support | Negative contribution: `−own_gdp_share × 0.33` — reduces coalition coverage |
| **−2** | Moderate evasion support | `−own_gdp_share × 0.67` |
| **−3** | Full evasion support | `−own_gdp_share × 1.0` — Cathay-backing-Sarmatia scenario |

**Coverage formula:**
```
coverage = Σ (actor_gdp_share × level / 3)   for all actors with sanctions on target
coverage = clamp(coverage, 0, 1)             # evasion can cancel but cannot bonus
```

**Per-target max damage ceiling** (sector-derived):
```
max_damage = tec% × 0.25 + svc% × 0.25 + ind% × 0.125 + res% × 0.05
```
- Tech/services-heavy economies top out ~22% one-time GDP loss
- Resource-heavy economies top out ~13-14% one-time GDP loss
- Industrial economies in between

**Final GDP impact:** `damage = max_damage × S_curve(coverage)`. **One-time shock** at imposition, not a recurring drain. Lifting sanctions produces immediate recovery via the same ratio mechanism. See `CARD_FORMULAS.md` A.2 for the full formula and S-curve shape.

**Key strategic dynamics:**
- **Solo action is noise** — at <10% coverage, the S-curve is in its flat tail (Teutonia alone L3 on Sarmatia = 0.40% damage)
- **Coalition tipping point at 0.5-0.6** — crossing from "half the world" to "three quarters" doubles effectiveness
- **Evasion support is strategic** — a country like Cathay (24% of world GDP) can single-handedly cancel or activate a coalition by choosing to evade or join
- **Sanctioning a big rival is free** — no imposer cost in v1.0 (no trade friction, no political cost). The strategic cost is diplomatic, not mechanical.
- **Resource economies are structurally resilient** — oil/gas/minerals find gray-market buyers, max damage capped low by sector weights
- **Target adaptation is NOT modeled** — sanctions produce one-time shocks, not recurring drains; the "sanctions_rounds > 4 diminishing returns" mechanism was dropped 2026-04-10

**Validation:** all submissions go through `app/engine/services/sanction_validator.py` with 11+ error codes including `INVALID_LEVEL` (outside [-3, +3]), `SELF_SANCTION`, `UNKNOWN_TARGET`, etc. Invalid submissions emit `sanction_rejected` observatory events.

**Persistence:**
- Canonical world state → `sanctions` state table (existing, unchanged)
- Per-round decision audit → `country_states_per_round.sanction_decision` JSONB (new 2026-04-10)

**Context package** (assembled by `app/engine/services/sanction_context.py`): economic state, ALL 20 countries with current coalition coverage computed per potential target, current bilateral sanctions both directions, decision rules with no_change reminder, instruction. **Decision-specific context only — cognitive context is provided by the AI Participant Module (future), not by this contract.**

**Legacy compatibility:** the singular `set_sanction` / `impose_sanction` / `lift_sanction` actions still work in parallel. New code should use `set_sanctions` (plural).

| Engine | `engines/economic.calc_sanctions_coefficient()` — REWRITTEN 2026-04-10, regression-locked by L1 tests |
| Status | 🟡 **IN PROGRESS** — Engine + L1 tests DONE; contract / validator / persistence / context / L3 still to ship. See `CHECKPOINT_SANCTIONS.md` when complete. |

### 2.4 Set OPEC Production — CONTRACT_OPEC v1.0 (🔒 locked 2026-04-11)
| Field | Value |
|---|---|
| action_type | `set_opec` (singular — single-value decision, no matrix) |
| Who | HoS of **OPEC+ member countries only** (5 members: Caribe, Mirage, Persia, Sarmatia, Solaria). Non-members rejected with `NOT_OPEC_MEMBER`. |
| Timing | Mandatory each round (submitted between rounds). **`no_change` is a legitimate explicit choice.** If no decision submitted, previous round's value carries forward. |
| Spec | `PHASES/UNMANNED_SPACECRAFT/CONTRACT_OPEC.md` v1.0 |

**Decision schema:**

```json
{
  "action_type": "set_opec",
  "country_code": "solaria",
  "round_num": 3,
  "decision": "change",
  "rationale": "string, ≥30 chars, required even on no_change",
  "changes": {
    "production_level": "min" | "low" | "normal" | "high" | "max"
  }
}
```

**Level scale:**

| Level | Multiplier | World-supply contribution per member |
|---|---|---|
| `min` | 0.70× | `−0.30 × share × 2.0` (aggressive cut) |
| `low` | 0.85× | `−0.15 × share × 2.0` (mild cut) |
| `normal` | 1.00× | 0 (baseline) |
| `high` | 1.15× | `+0.15 × share × 2.0` (mild flood) |
| `max` | 1.30× | `+0.30 × share × 2.0` (aggressive flood) |

Each OPEC+ member decides independently. Effect is on the world oil price via the supply mechanism with a **2× cartel leverage amplifier** applied per-member.

**OPEC+ roster** (5 canonical members from `countries.opec_member = true`):
- **Caribe** (0.8 mbpd) — Venezuela-equivalent, the smallest OPEC+ producer
- **Mirage** (3.5 mbpd) — Gulf producer
- **Persia** (3.5 mbpd) — Persian Gulf producer
- **Sarmatia** (10 mbpd) — OPEC+ (Russia-equivalent, de facto OPEC+ coordination)
- **Solaria** (10 mbpd) — core OPEC producer

**Non-OPEC oil producers** (cannot submit `set_opec`):
- **Columbia** (13 mbpd) — largest producer in the world, free agent
- (Others have 0 mbpd)

**Validation:** all submissions go through `app/engine/services/opec_validator.py` with 9 error codes. Invalid submissions emit `opec_rejected` observatory events.

**Persistence:**
- Live value → `country_states_per_round.opec_production` (existing text column — `min/low/normal/high/max` for members, `"na"` for non-members)
- Per-round decision audit → `country_states_per_round.opec_decision` JSONB (new 2026-04-11)

**Context package** (assembled by `app/engine/services/opec_context.py`): economic state + oil market state + **oil price history for all rounds already played** + **unified oil producers table** with current production levels + chokepoint blockades + sanctions on producers + tariffs on producers + decision rules with no_change reminder. **Decision-specific data only — no commentary, no cognitive context.**

**Legacy compatibility:** old payloads with top-level `production_level` field (no `changes` wrapper) are auto-migrated by the `resolve_round` handler.

| Engine | `engines/economic.calc_oil_price()` — OPEC section UNCHANGED, regression-locked by L1 tests |
| Status | ✅ **DONE** end-to-end (CONTRACT v1.0, validator, context, persistence, AI acceptance gate). See `CHECKPOINT_OPEC.md`. |

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

| Engine | `services/intelligence_engine.py` (comprehensive 9-domain context + LLM) + `services/covert_ops_validator.py` |
| Status | **LIVE — slice locked v1.0 (2026-04-13)** — see `CONTRACT_INTELLIGENCE.md` |

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

| Engine | `services/transaction_engine.py` + `services/transaction_validator.py` (T1 canonical) |
| Status | **LIVE — slice locked v1.0 (T1, 2026-04-13)** — see `CONTRACT_TRANSACTIONS.md` |

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

| Engine | `services/agreement_engine.py` + `services/agreement_validator.py` (T2 canonical) |
| Status | **LIVE — slice locked v1.0 (T2, 2026-04-13)** — see `CONTRACT_AGREEMENTS.md` |

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
| Engine | `services/arrest_engine.py` + `services/run_roles.py` |
| Status | **LIVE — slice locked v1.0 (2026-04-13)** — see `CONTRACT_ARREST.md` |

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

### 6.3 Reassign Powers (replaces Fire/Reassign)
| Field | Value |
|---|---|
| action_type | `reassign_powers` |
| Fields | `power_type` (military\|economic\|foreign_affairs), `new_role` (role_id or null to vacate) |
| Who | **HoS only.** |
| Mechanic | HoS reassigns one of three power categories to a different role within the same country (or vacates the slot, making HoS the sole authority). Immediate. Public — all notified. |
| Engine | `services/power_assignments.py:reassign_power()` + `check_authorization()` |
| Status | **LIVE — slice locked v1.0 (2026-04-13)** — see `CONTRACT_POWER_ASSIGNMENTS.md` |

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

| Engine | `engine/services/protest_engine.execute_mass_protest()` |
| Contract | `CONTRACT_MASS_PROTEST.md` 🔒 |
| Status | **LIVE** |

### 6.6 Elections (Scheduled)
| Field | Value |
|---|---|
| action_type | (automatic — triggered by schedule, not player action) |
| Mechanic | Elections are pre-scheduled in Template data. Engine processes them at the designated round. |

**Schedule (Template v1.0):**

| Round | Election | Country | Trigger | Nominations |
|---|---|---|---|---|
| R2 | Mid-term parliamentary | Columbia | Automatic (scheduled) | R1 |
| R5 | Presidential election | Columbia | Automatic (scheduled) | R4 |
| — | Wartime election | Ruthenia | NOT scheduled. Triggered by: HoS of Ruthenia voluntarily, OR 2+ Ruthenian participants demand it, OR full Ruthenian team consensus. One-off event. | — |

**Result:** 50% participant votes + 50% population votes (AI score). See CARD_FORMULAS.md → B.3 Elections.

| Engine | AI score: `engines/political.process_election()`. Nominations/voting/resolution: `engine/services/election_engine.py` |
| Status | **LIVE** |

### 6.6a Nominate Self for Election
| Field | Value |
|---|---|
| action_type | `submit_nomination` |
| Who | Any Columbia participant (active role) |
| Timing | Exactly 1 round before the election (R1 for R2 midterms, R4 for R5 presidential) |
| Camp | Automatically assigned from role: `president_camp` (dealer, volt, anchor, shadow, shield) or `opposition` (tribune, challenger) |
| Engine | `engine/services/election_engine.submit_nomination()` |
| Contract | `CONTRACT_ELECTIONS.md` 🔒 |
| Status | **LIVE** |

### 6.6b Vote in Election
| Field | Value |
|---|---|
| action_type | `cast_vote` |
| Who | Any Columbia participant (active role) |
| Timing | During the election round |
| Mechanic | Secret ballot — only moderator can see individual votes. One vote per participant per election. Must vote for a nominated candidate. |
| Engine | `engine/services/election_engine.cast_vote()` |
| Contract | `CONTRACT_ELECTIONS.md` 🔒 |
| Status | **LIVE** |

### 6.6c Resolve Election
| Field | Value |
|---|---|
| action_type | (orchestrator-triggered, not player action) |
| Mechanic | Counts participant votes + population votes (AI score distributed by camp). Winner = highest total. For midterms: winner takes contested parliament seat. |
| Engine | `engine/services/election_engine.resolve_election()` |
| Contract | `CONTRACT_ELECTIONS.md` 🔒 |
| Status | **LIVE** |

### 6.7 Call Early Elections
| Field | Value |
|---|---|
| action_type | `call_early_election` |
| Who | HoS (voluntarily) or opposition (if they have parliamentary majority — Columbia only) |
| Mechanic | Triggers election process in the NEXT round. Uses same election engine as scheduled elections. |
| Engine | `engine/services/early_elections_engine.execute_early_elections()` |
| Contract | `CONTRACT_EARLY_ELECTIONS.md` 🔒 |
| Status | **LIVE** |

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
