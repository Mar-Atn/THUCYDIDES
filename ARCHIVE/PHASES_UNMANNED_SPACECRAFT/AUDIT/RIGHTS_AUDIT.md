# RIGHTS AUDIT — Role Data & Enforcement

**Date:** 2026-04-08
**Auditor:** BACKEND agent
**DB project:** lukcymegoldprbovglmn

---

## 1. WHAT EXISTS AND IS CORRECT

### 1.1 Personal Coins
- All 40 roles have a `personal_coins` value. Range: 1-5. Distribution is plausible:
  - 5 coins: Helmsman, Dealer, Wellspring, Compass (4 roles — top leaders / oligarchs)
  - 4 coins: Spire, Pioneer, Pathfinder (3 roles)
  - 3 coins: 12 roles (mostly HoS of smaller countries + key ministers)
  - 2 coins: 16 roles (deputies, diplomats, mid-tier)
  - 1 coin: 4 roles (Pyro, Dawn, Bulwark, Havana — low-resource actors)
- `personal_coins_notes` populated for 3 roles with frozen/at-risk coin notes (Compass, Circuit, Anvil). Correct per design.

### 1.2 Powers
- All 40 roles have a `powers` array with at least 1 entry (verified: all 40 have `array_length > 0`).
- Powers are narrative/descriptive strings (e.g., `set_tariffs`, `authorize_attack`, `nuclear_authority`).
- Powers are exposed to AI agents via `world_context.py::_build_powers()` — injected into the LLM prompt as "Your Powers" section.

### 1.3 Covert Op Cards
- 31 of 40 roles have at least one covert card (sabotage, cyber, disinfo, election_meddling, assassination, or protest_stim).
- 9 roles have zero covert cards but still have intelligence_pool > 0 (can do espionage): Sage(1), Volt(2), Sentinel(4), Pillar(2), Ponte(4), Beacon(4), Bulwark(3), Compass(2), Ledger(2).
- Shadow (Columbia CIA) has the most cards: intelligence 8, sabotage 3, cyber 3, disinfo 3, election_meddling 1, assassination 1. Correct — he is the intel director.
- Citadel (Levantia/Israel) has high assassination cards (2). Correct per design (Mossad parallel).

### 1.4 Fatherland Appeal
- 20 roles have `fatherland_appeal = 1` — exactly one per country (all HoS). Correct.

### 1.5 Other Role Fields (all 40/40)
- `objectives[]`: all 40 populated
- `ticking_clock`: all 40 populated
- `is_head_of_state`, `is_military_chief`, `is_diplomat`: boolean flags present

### 1.6 Covert Op Engine (military.py)
- `resolve_covert_op()` checks `remaining = getattr(inp.role, card_field, 0)` — refuses if zero.
- Returns `card_consumed=True` and `card_field` name when a card is used.
- The engine function is PURE (no DB writes). It signals what to decrement.

### 1.7 Personal Coin Check (technology.py)
- `resolve_personal_tech_investment()` checks `personal_coins < investment_amount` — refuses if insufficient.
- Returns `coins_spent` amount. Engine is PURE — signals what to deduct.

---

## 2. WHAT EXISTS BUT IS NOT ENFORCED

### 2.1 Card Consumption — NOT PERSISTED TO DB
**CRITICAL.** The engine `resolve_covert_op()` returns `card_consumed=True` and `card_field="sabotage_cards"`, but:
- **No code anywhere writes `UPDATE roles SET sabotage_cards = sabotage_cards - 1`.**
- The `resolve_round.py` covert op handler (line 335-406) does NOT even call `resolve_covert_op()` — it has its own inline probability logic that **completely ignores card pools**.
- The `full_round_runner.py` never decrements card counts after covert ops.
- **Result:** Cards are infinite. A role can sabotage every round without limit.

### 2.2 Personal Coin Deduction — NOT PERSISTED TO DB
**CRITICAL.** `resolve_personal_tech_investment()` returns `coins_spent`, but:
- **No code writes `UPDATE roles SET personal_coins = personal_coins - coins_spent`.**
- `full_round_runner.py` does NOT process personal coin changes.
- **Result:** Personal coins are infinite. A tycoon can invest every round without limit.

### 2.3 Powers — NOT ENFORCED BY ENGINE
**HIGH.** The `powers[]` array is included in the AI prompt (so the LLM _knows_ its powers), but:
- **No code in `resolve_round.py` checks whether the submitting role has the power to perform the action.**
- **No code in `agents/tools.py` validates `powers[]` before `commit_action`.**
- **No code in `agents/leader_round.py` filters the action space by powers.**
- The engine trusts the AI agent to self-police. In unmanned mode this may work passably (LLM reads its powers). But there is zero guardrail — an agent can submit `authorize_attack` even if its powers do not include it.

### 2.4 Covert Op Card Map — Incomplete
`COVERT_CARD_FIELD_MAP` in `military.py` is missing two card types:
- `"assassination"` -> `"assassination_cards"` (NOT MAPPED)
- `"protest_stim"` -> `"protest_stim_cards"` (NOT MAPPED)

Both fall through to the default `"intelligence_pool"`, which means assassination and protest_stim ops would incorrectly consume intelligence pool instead of their own card type.

### 2.5 resolve_round.py Covert Handler — Stale / Diverged
The covert op handler in `resolve_round.py` (lines 335-406):
- Uses hardcoded probabilities that differ from `engines/military.py` constants
- Does NOT check per-role card pools at all
- Does NOT call the canonical `resolve_covert_op()` function
- Maps `"propaganda"` instead of `"disinformation"` (naming mismatch)
- This is the code path actually used in the current full_round_runner flow

---

## 3. WHAT IS MISSING ENTIRELY

### 3.1 `permitted_actions` Column — DOES NOT EXIST
CARD_TEMPLATE.md (line 71) specifies: `permitted_actions[] (list of action_types this role can invoke)`.
**The column does not exist in the `roles` table.** This is a design-to-DB gap.

The `powers[]` array contains narrative power labels (`set_tariffs`, `authorize_attack`) which partially overlap with action_types (`set_tariff`, `attack_ground`) but use **different naming** and are **not a formal mapping**. There is no lookup table or code that maps `power -> action_type`.

### 3.2 Card Decrement Persistence Layer
No function exists to write card consumption back to DB. Needed:
```python
async def decrement_role_card(role_id: str, card_field: str, amount: int = 1):
    """UPDATE roles SET {card_field} = {card_field} - {amount} WHERE id = {role_id}"""
```

### 3.3 Coin Deduction Persistence Layer
No function exists to write coin spending back to DB. Needed:
```python
async def deduct_personal_coins(role_id: str, amount: float):
    """UPDATE roles SET personal_coins = personal_coins - {amount} WHERE id = {role_id}"""
```

### 3.4 Intelligence Pool Per-Round Budget
`intelligence_pool` is described as "per round" in CARD_TEMPLATE.md (line 69). The DB stores a single integer. There is no mechanism to:
- Reset intelligence_pool usage each round
- Track how many intel ops were used THIS round vs total pool

This means `intelligence_pool = 4` should allow 4 intel ops PER ROUND, but the current engine treats it as a total pool (decrements permanently like other cards). Design intent is ambiguous — needs Marat decision.

### 3.5 protest_stim_cards Not in CovertOpInput Model
The `CovertOpRole` dataclass in `military.py` (line 241-245) lists `sabotage_cards`, `cyber_cards`, `disinfo_cards`, `assassination_cards` but **not `protest_stim_cards`**. The protest_stim card type cannot be validated by the pure engine even if wired.

---

## 4. RECOMMENDED FIXES (PRIORITIZED)

### P0 — Must fix before next test run

1. **Add card decrement to full_round_runner.py** — After `resolve_round` processes a covert op, write `UPDATE roles SET {card_field} = {card_field} - 1 WHERE id = {role_id}`. This is the #1 resource integrity gap.

2. **Add coin deduction to full_round_runner.py** — After personal tech investment, write `UPDATE roles SET personal_coins = personal_coins - {amount} WHERE id = {role_id}`.

3. **Add missing card types to COVERT_CARD_FIELD_MAP** — Add `"assassination": "assassination_cards"` and `"protest_stim": "protest_stim_cards"`.

4. **Add `protest_stim_cards` to CovertOpRole dataclass** in `military.py`.

### P1 — Should fix this sprint

5. **Migrate resolve_round.py covert handler to use `resolve_covert_op()`** — Eliminate the inline duplicate logic. The canonical function in `engines/military.py` has correct probabilities and card checking.

6. **Add `permitted_actions` column to roles table** — Populate from CARD_ACTIONS.md role authorization table. Use action_type values (not narrative power names).

7. **Add action authorization check in tools.py `commit_action()`** — Before accepting an action, verify `action_type in role.permitted_actions`. Reject with clear error if unauthorized.

### P2 — Should fix before Marat demo

8. **Clarify intelligence_pool semantics with Marat** — Is it per-round (resets) or per-SIM (consumed)? Current DB/code treats it as per-SIM. CARD_TEMPLATE says "per round".

9. **Create powers-to-action-types mapping table** — Either in DB or code, formalize which `powers[]` entries authorize which `action_type` values. Currently there is no mapping, only LLM honor system.

---

## SUMMARY TABLE

| Data Element | In DB? | In Engine? | Enforced? | Persisted? |
|---|---|---|---|---|
| personal_coins | YES (40/40) | YES (technology.py checks) | YES (refuses if insufficient) | **NO** (never decremented) |
| powers[] | YES (40/40) | YES (in LLM prompt) | **NO** (no code check) | n/a |
| permitted_actions[] | **NO** (column missing) | NO | NO | NO |
| sabotage_cards | YES (20 roles) | YES (military.py checks) | YES (refuses if zero) | **NO** (never decremented) |
| cyber_cards | YES (21 roles) | YES | YES | **NO** |
| disinfo_cards | YES (17 roles) | YES | YES | **NO** |
| election_meddling_cards | YES (12 roles) | YES | YES | **NO** |
| assassination_cards | YES (10 roles) | **PARTIAL** (not in card map) | **NO** | **NO** |
| protest_stim_cards | YES (4 roles) | **NO** (not in model or map) | **NO** | **NO** |
| intelligence_pool | YES (40/40) | YES | YES (but per-SIM, design says per-round) | **NO** |
| fatherland_appeal | YES (20 HoS) | In prompt only | **NO** | n/a |
| objectives[] | YES (40/40) | In prompt | n/a | n/a |
| ticking_clock | YES (40/40) | In prompt | n/a | n/a |
