# AUDIT: AI Agent Schema vs Engine Contract — All 33 Actions

**Date:** 2026-04-25
**Purpose:** Meticulous comparison of what AI agents submit vs what the engine processes.
**Methodology:** Traced every `.get()` call in engine code against Pydantic schema fields.

---

## CRITICAL MISMATCHES (Actions silently fail or produce wrong results)

### 1. set_budget — Military & Tech fields completely ignored

| Layer | Field | Value |
|-------|-------|-------|
| **Schema** (BudgetOrder) | `social_pct` | ✅ Matches |
| **Schema** | `military_coins: float` | Agent sends: `2.0` |
| **Schema** | `tech_coins: float` | Agent sends: `1.5` |
| **Engine** (economic.py:1317) | `budget.get("social_pct", 1.0)` | ✅ Reads correctly |
| **Engine** (economic.py:1327) | `budget.get("production", {})` | ❌ Gets `{}` — `military_coins` ignored |
| **Engine** (economic.py:1332) | `budget.get("research", {})` | ❌ Gets `{}` — `tech_coins` ignored |
| **Engine expects** | `production: {ground: level, naval: level, tactical_air: level, strategic_missile: level, air_defense: level}` | Per-branch production levels (0-4) |
| **Engine expects** | `research: {nuclear_coins: int, ai_coins: int}` | Split R&D allocation |

**Impact:** Zero military production, zero R&D progress for ALL AI countries. Only `social_pct` works.

**Fix needed:** Change BudgetOrder to match engine format:
```python
class BudgetOrder(BaseModel):
    social_pct: float = Field(1.0, ge=0.5, le=1.5)
    production: dict = Field(default_factory=dict)  # {ground: 0-4, naval: 0-4, ...}
    research: dict = Field(default_factory=dict)     # {nuclear_coins: int, ai_coins: int}
    rationale: str
```

### 2. set_opec — Field name mismatch

| Layer | Field | Value |
|-------|-------|-------|
| **Schema** (SetOpecOrder) | `production: str` | Agent sends: `"normal"` |
| **Phase B collection** (main.py:1137) | `payload.get("production_level", "maintain")` | ❌ Reads `production_level`, not `production` |

**Impact:** OPEC production always defaults to "maintain" regardless of AI decision.

**Fix needed:** Change main.py:1137 to read `payload.get("production", payload.get("production_level", "maintain"))`

### 3. launch_missile_conventional — Missing target_type

| Layer | Field |
|-------|-------|
| **Schema** (MissileLaunchOrder) | `launcher_unit_code`, `target_global_row`, `target_global_col`, `rationale` |
| **Engine** (action_dispatcher combat) | Reads `action.get("target_type")` for military/infrastructure/nuclear_site/AD selection |
| **World Model** | "4 target choices (military, infrastructure, nuclear_site, AD)" |

**Impact:** AI cannot specify what to target with missiles. Engine defaults.

**Fix needed:** Add `target_type: Literal["military", "infrastructure", "nuclear_site", "ad"] = "military"` to MissileLaunchOrder.

### 4. nuclear_test — Missing test_type

| Layer | Field |
|-------|-------|
| **Schema** (NuclearTestOrder) | Only `rationale` |
| **Engine** (_execute_nuclear_test) | Reads `action.get("test_type", "underground")` |
| **World Model** | "Underground (-0.2 stability) or surface (-0.4 global, -0.6 adjacent, -5% GDP)" |

**Impact:** AI can only do underground tests (default). Cannot choose surface test.

**Fix needed:** Add `test_type: Literal["underground", "surface"] = "underground"` to NuclearTestOrder.

### 5. naval_blockade — Missing operation and level

| Layer | Field |
|-------|-------|
| **Schema** (BlockadeOrder) | `zone_id`, `imposer_units`, `rationale` |
| **Engine** (action_dispatcher:124-137) | Reads `operation` (establish/lift/reduce), `zone_id`, `level` (full/partial) |

**Impact:** AI cannot lift or reduce blockades — only establish. Cannot specify partial blockade.

**Fix needed:** Add `operation: Literal["establish", "lift", "reduce"] = "establish"` and `level: Literal["full", "partial"] = "full"` to BlockadeOrder.

### 6. call_org_meeting — Field name mismatches

| Layer | Schema Field | Engine Reads |
|-------|-------------|-------------|
| Schema | `organization_code` | Engine reads `org_id` and `org_name` |
| Schema | `agenda` | Engine reads `message` |
| Missing | — | Engine reads `invitation_type` (defaults to "one_on_one", should be "organization") |

**Impact:** Org meeting may not route correctly. Agenda not passed to invitation.

**Fix needed:** Dispatcher normalization: `organization_code` → `org_id`, `agenda` → `message`, set `invitation_type = "organization"`.

---

## HIGH PRIORITY (Missing optional fields)

### 7. nuclear_launch_initiate — Missing missiles field

| Layer | Field |
|-------|-------|
| **Schema** | `target_country`, `target_global_row`, `target_global_col`, `rationale` |
| **Engine** (nuclear_chain) | Also reads `action.get("missiles", [])` — list of missile unit codes |

**Impact:** Agent can't specify which missiles to launch. Engine defaults to empty list, may use all available.

### 8. sign_agreement — Missing confirm/comments

| Layer | Field |
|-------|-------|
| **Schema** | `agreement_id`, `rationale` |
| **Engine** (action_dispatcher:330-339) | Also reads `confirm` (bool, default True), `comments` (str, default "") |

**Impact:** Agent can sign but cannot decline via submit_action (always defaults to confirm=True). Low severity since agents can simply not call sign_agreement to decline.

---

## HANDLED BY NORMALIZATION (Working but architecturally inconsistent)

| Action | Schema Field | Engine Field | Normalization Location |
|--------|-------------|-------------|----------------------|
| All combat (5 types) | `target_global_row/col` | `target_row/col` | tool_executor.py:272-275 |
| launch_missile | `launcher_unit_code` | `attacker_unit_codes` (list) | tool_executor.py:277-278 |
| nuclear_authorize | `authorize` | `confirm` | tool_executor.py:280-281 |
| move_units | `changes.moves` (nested) | `moves` (top-level) | tool_executor.py:283-285 |
| propose_transaction | `counterpart_country` | `counterpart_country_code` | action_dispatcher.py:268 |
| propose_agreement | `counterpart_country` | `counterpart_country_code` + `signatories` | action_dispatcher.py:300-305 |
| reassign_types | `power_type` | `position` (mapped) | action_dispatcher.py:224-226 |

---

## VERIFIED CORRECT (No mismatches)

| Action | Schema Fields | Engine Reads | Status |
|--------|--------------|-------------|--------|
| ground_attack | attacker_unit_codes, target_global_row/col | target_row/col (normalized) | ✅ |
| ground_move | same as above | same | ✅ |
| air_strike | same | same | ✅ |
| naval_combat | same | same | ✅ |
| naval_bombardment | same | same | ✅ |
| basing_rights | operation, guest_country, zone_id | same fields | ✅ |
| martial_law | rationale only | rationale only | ✅ |
| nuclear_intercept | nuclear_action_id, intercept | same fields | ✅ |
| set_tariffs | target_country, level | `payload.get("target_country")`, `payload.get("level")` | ✅ |
| set_sanctions | target_country, sanction_type, level | `payload.get("target_country")`, `payload.get("level")` | ✅ |
| declare_war | target_country | `action.get("target_country")` | ✅ |
| public_statement | content | `action.get("content")` | ✅ |
| covert_operation | op_type, target_country, target_type, intent, content | all matched | ✅ |
| intelligence | op_type, question, target_country | all matched | ✅ |
| arrest | target_role | `action.get("target_role")` | ✅ |
| assassination | target_role, domestic | same fields | ✅ |
| change_leader | rationale | rationale only | ✅ |
| self_nominate | election_type, election_round | same fields | ✅ |
| cast_vote | election_type, candidate_role_id | same fields | ✅ |
| accept_transaction | transaction_id, response, counter_offer | same fields | ✅ |
| propose_transaction | counterpart_country, offer, request | normalized to counterpart_country_code | ✅ |
| propose_agreement | counterpart_country, agreement_name, type, visibility, terms | normalized | ✅ |

---

## GAME RULES CONTEXT INACCURACIES

| # | What Agent Is Told | Correct Value | Source |
|---|-------------------|---------------|--------|
| 1 | AI GDP bonus: L2=+0.5%, L3=+1.5%, L4=+3.0% | L2=+0.3%, L3=+1.0%, L4=+2.5% | economic.py:95 |
| 2 | Missile hit: 80% (30% if AD) | 75% hit, 50% AD intercept per unit (two-phase) | World Model + military.py |
| 3 | Missing: combat modifiers | AI L4 +1 die, low morale -1, die-hard +1 def, air support +1, amphibious -1 | World Model Section 5 |

---

## CONTEXT ASSEMBLY GAPS

| Component | What M5 SPEC Requires | What Code Provides | Gap |
|-----------|----------------------|-------------------|-----|
| Round number | Agent knows current round | Set at init, synced in auto-pulse (now fixed) | ✅ Fixed |
| Economic state | GDP, treasury, stability | In character brief (system_prompt.py) | ✅ |
| Relationships | Wars, alliances | In db_context.py starting situation | ✅ |
| Available actions | From role_actions table | NOT included in prompt | ❌ Missing |
| Per-pulse meta | Pulse N/M, resource dashboard | build_meta_context() exists but NOT called | ❌ Missing |

---

## SUMMARY: Required Fixes

### Schema Changes (action_schemas.py):
1. **BudgetOrder** — replace `military_coins`/`tech_coins` with `production: dict` + `research: dict`
2. **SetOpecOrder** — no change needed (fix in main.py instead)
3. **MissileLaunchOrder** — add `target_type`
4. **NuclearTestOrder** — add `test_type`
5. **BlockadeOrder** — add `operation`, `level`
6. **NuclearLaunchOrder** — add `missiles: list[str]`
7. **SignAgreementOrder** — add `confirm: bool`, `comments: str`

### Engine/Dispatcher Fixes:
8. **main.py:1137** — read `production` not just `production_level` for set_opec
9. **action_dispatcher** — normalize call_org_meeting fields
10. **game_rules_context.py** — fix AI GDP bonuses, missile probabilities, add combat modifiers

### Context Assembly:
11. Add available actions from role_actions to agent context
12. Integrate per-pulse meta context into event delivery
