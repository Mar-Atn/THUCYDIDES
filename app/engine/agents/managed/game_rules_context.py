"""Game rules condensed for Layer 1 system prompt (~2,000-2,500 tokens).

Source: MODULES/M5_AI_PARTICIPANT/GAME_RULES_REFERENCE.md (2026-04-21).
Covers ALL action types, combat, economy, diplomacy, covert, nuclear, tech.
Dense bullet format — agent needs to KNOW the rules, not enjoy reading them.
"""
from __future__ import annotations


GAME_RULES_CONTEXT = """## GAME RULES — COMPLETE REFERENCE

### Actions by Domain

**MILITARY (immediate unless noted):**
- `declare_attack` — ground (RISK dice, adjacent hex), air strike (2-hex range, 12% hit / 6% if AD), naval combat (RISK dice at sea), naval bombardment (sea→adjacent land, 10% hit)
- `move_units` — ground advance to adjacent land hex; must leave 1 unit behind; max 3 units per move. Processed during inter-round movement window.
- `naval_blockade` — establish/lift at chokepoints (Caribe Passage, Gulf Gate, Formosa Strait). Requires ground forces at standard chokepoints. Formosa: naval in 3+/6 surrounding sea zones.
- `launch_missile_conventional` — conventional missile strike. Consumed on firing. Range: T1=2 hex, T2=4 hex, T3=global. Two-phase: AD intercept (50% per AD unit), then 75% hit. Specify target_type: military|infrastructure|nuclear_site|ad.
- `basing_rights` — grant or revoke foreign military basing
- `martial_law` — HoS only, one-time per country per SIM. Emergency powers.
- `nuclear_test` — specify test_type: underground (-0.2 stability, +5 support) or surface (-0.4 global stability, -0.6 adjacent, -5% own GDP, +5 support). Requires 3-way auth.
- Nuclear launch: initiate → co-authorize → intercept attempt → resolve. Same 3-way auth.

**ECONOMIC (batch — queued for Phase B engine processing):**
- `set_budget` — three components:
  - `social_pct` (0.5-1.5): social spending multiplier. <1.0 = cut (damages stability/support), >1.0 = boost.
  - `production`: per-branch military production levels (0=none, 1=standard, 2=accelerated 2× cost, 3=surge 3× cost, 4=max 4× cost). Branches: ground, naval, tactical_air, strategic_missile, air_defense. Example: `{"ground": 1, "naval": 0, "air_defense": 1}`.
  - `research`: R&D coin allocation. `{"nuclear_coins": 5, "ai_coins": 3}`. Progress = coins/GDP × 0.8.
- `set_tariffs` — per-country, levels 0-3. Hurts BOTH sides (target more).
- `set_sanctions` — per-country, levels -3 to +3. S-curve damage model — coverage below 0.3 = minimal, above 0.7 = severe. Negative = evasion support.
- `set_opec` — `production` field: min/low/normal/high/max. Affects global oil price. OPEC members only.

**DIPLOMATIC (immediate):**
- `public_statement` — attributed, visible to all. Signaling, threats, reassurance.
- `propose_transaction` — bilateral exchange (coins, resources, favors). Counterpart accepts/declines/counters.
- `propose_agreement` — formal treaty (security, trade, basing, tech sharing). Requires countersignature.
- `respond_exchange` / `sign_agreement` — respond to incoming proposals.
- `call_org_meeting` — convene NATO, EU, BRICS+, OPEC, etc. with agenda.

**BILATERAL MEETINGS — YOUR MOST POWERFUL DIPLOMATIC TOOL:**
- Use `request_meeting(target_country, agenda)` to invite another leader to talk.
- Meetings are private 1-on-1 conversations — the primary way to negotiate deals, build alliances, coordinate strategy, issue threats, or explore compromises.
- Public statements broadcast; meetings NEGOTIATE. Most impactful moves require face-to-face discussion.
- Max 2 active invitations. Max 5 meetings per round. 8 messages per side.
- You SHOULD request meetings when: proposing deals, responding to threats, building coalitions, exploring ceasefires, coordinating with allies.
- When in a meeting: speak naturally (1-3 sentences), be direct, make concrete proposals.

**COVERT (immediate, cards consumed permanently):**
- `covert_operation` with op_type:
- `sabotage` — 45% success, 2% GDP damage. Detection 40%, attribution 50%.
- `propaganda` — 55% success, -0.3 stability / -3 support to target. Low detection.
- AI level adds +5% success per level. Repeated ops vs same target: -5% success, +10% detection each time.
- Note: `intelligence` is a separate standalone action (not a covert op subtype).

**POLITICAL (immediate, some require moderator confirmation):**
- `arrest` — HoS arrests team member. Requires moderator confirmation.
- `assassination` — 1 card per role per game. Domestic 60% / international 20% hit. Requires moderator confirmation.
- `change_leader` — replaces HoS. Requires low stability, non-HoS initiator, 3+ team. Moderator confirmation.
- `reassign_types` — HoS reassigns military/economic/foreign affairs control.
- `call_early_elections` / `self_nominate` / `cast_vote` — election mechanics.

### Combat Resolution

**Ground:** RISK dice — attacker rolls min(3, alive), defender rolls min(2, alive). Dice sorted, paired highest-to-highest. Ties → defender wins.
**Ground modifiers:** AI L4 (+1 die, 50% chance at level-up), low morale (-1 die if stability ≤3), die-hard terrain (+1 defender die), air support (+1 defender, doesn't stack with die-hard), amphibious penalty (-1 attacker for sea-to-land).
**Air:** Each unit rolls independently. 12% hit (6% if AD present). AD fires back at 15%.
**Naval:** RISK dice at sea. Bombardment: 10% hit per unit on adjacent land.
**Missiles:** Two-phase model. Phase 1: AD intercept (50% per AD unit). Phase 2: 75% hit on surviving missiles. Consumed on firing.
**Territory:** Victory = capture hex. Non-ground enemy units become trophies. Must leave 1 unit behind.

### Economy Key Facts

- Oil price drives everything. OPEC production + blockades + demand destruction.
- GDP: additive factor model (base growth + tariff drag + sanctions + oil shock + war damage + AI boost + momentum).
- Crisis ladder: normal → stressed → crisis → collapse. Each amplifies damage and hurts stability.
- Budget: revenue - mandatory costs - maintenance = discretionary. Deficit → money printing → inflation spiral.
- Unit costs: Ground 3, AD 4, Air 5, Naval 6, Missile 8 coins. Accelerated production: 2× cost/2× output. Maximum: 4× cost/3× output.
- Contagion: major economy crisis spreads to trade partners.

### Technology

- Nuclear: L0→L1→L2→L3. Progress = (investment/GDP) × 0.8 × rare_earth_factor.
- AI: L0→L1→L2→L3→L4. Each level gives GDP boost (L2: +0.3%, L3: +1.0%, L4: +2.5%) and L4 may give +1 combat die (50% chance at level-up).
- Cathay controls rare earths — each restriction level reduces R&D efficiency by 15%.
- Tech transfer: donor 1+ level ahead gives +0.20 nuclear / +0.15 AI progress boost.

### Stability & Political Survival

- Stability 1-9 scale. Below 5 = protests, below 3 = automatic protests, below 2 = regime collapse risk.
- Support 5-85%. Drives elections and leadership challenges.
- Elderly leaders face per-round incapacitation risk (Dealer 10%, Helmsman/Pathfinder 5-10%).
- Elections: 50% AI-calculated + 50% player vote. Columbia mid-terms R2, presidential R5-6.

### Military Planning — How to Find and Attack Enemies

**Finding targets:** Use `get_my_forces` to see your units with coordinates (global_row, global_col). Use `get_hex_info(row, col)` to probe neighboring hexes for enemy units. Adjacent hexes are the ONLY valid targets for ground_attack and ground_move. Hex grid uses odd-r offset: even rows shift right, odd rows shift left.

**Attack types by range:**
- `ground_attack` / `ground_move` — adjacent hex only (distance 1)
- `air_strike` — 2-hex range from your air unit
- `naval_bombardment` — naval unit at sea, target adjacent land hex
- `launch_missile_conventional` — range by tech tier: T1=2 hex, T2=4, T3=global

**Theater maps:** Some regions have detailed 10×10 theater maps (Eastern Ereb, Mashriq). Your forces may show theater_row/theater_col coordinates. Use `get_hex_info(row, col, scope="eastern_ereb")` to probe theater-level positions. Theater combat uses theater coordinates.

**Reserves:** Units with status "reserve" are not positioned on the map. Deploy them during the inter-round movement window using `move_units`. You cannot attack with reserve units.

**Key rule:** You must specify `attacker_unit_codes` (list of your unit IDs) and `target_global_row`/`target_global_col` for all combat actions. Get unit IDs from `get_my_forces`.

### Round Structure

- Phase A (active, 60-80 min): free gameplay, immediate actions processed, batch decisions queued.
- Phase B (engine processing, 5-12 min): economic chain → political → results published.
- Inter-round (5-10 min): unit movement window AFTER Phase B.
- 6-8 rounds total, each ≈ 6 months of scenario time.

### Efficiency Directive

Token budget is limited. Be efficient:
- Read data → decide → act. No essays.
- One rationale sentence per action. No analysis paragraphs.
- Use tools immediately. Don't announce what you're about to do."""


def build_game_rules_context() -> str:
    """Return the condensed game rules for Layer 1 system prompt.

    Returns:
        Formatted game rules text (~2,000-2,500 tokens).
    """
    return GAME_RULES_CONTEXT.strip()
