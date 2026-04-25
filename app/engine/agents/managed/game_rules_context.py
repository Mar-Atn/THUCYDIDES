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
- `launch_missile_conventional` — conventional missile strike. Consumed on firing. Range: T1=2 hex, T2=4 hex, T3=global. 80% hit (30% if AD present).
- `basing_rights` — grant or revoke foreign military basing
- `martial_law` — HoS only, one-time per country per SIM. Emergency powers.
- `nuclear_test` — underground (-0.2 stability) or overground (-0.5 self, -0.3 global). +5 support. Requires 3-way auth: HoS + Military Chief + Moderator.
- Nuclear launch: initiate → co-authorize → intercept attempt → resolve. Same 3-way auth.

**ECONOMIC (batch — queued for Phase B engine processing):**
- `set_budget` — social spending (0.5-1.5× baseline), military production, tech R&D allocation. Cutting social spending damages stability/support; increasing boosts both.
- `set_tariffs` — per-country, levels 0-3. Hurts BOTH sides (target more).
- `set_sanctions` — per-country, levels -3 to +3. S-curve damage model — coverage below 0.3 = minimal, above 0.7 = severe. Negative = evasion support.
- `set_opec` — production level: min/low/normal/high/max. Affects global oil price. OPEC members only.
- R&D investment is part of `set_budget` — use `tech_coins` field to allocate to nuclear/AI/missile.

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

**Ground:** RISK dice — attacker rolls min(3, alive), defender rolls min(2, alive). Dice sorted, paired highest-to-highest. Ties → defender wins. Modifiers: AI L4 (+1 die), morale, amphibious penalty, die-hard defense, air support.
**Air:** Each unit rolls independently. 12% hit (6% if AD present). AD fires back at 15%.
**Naval:** RISK dice at sea. Bombardment: 10% hit on adjacent land.
**Missiles:** 80% hit (30% if AD). Consumed on firing.
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
- AI: L0→L1→L2→L3→L4. Each level gives GDP boost (L2: +0.5pp, L3: +1.5pp, L4: +3.0pp) and L4 may give +1 combat die.
- Cathay controls rare earths — each restriction level reduces R&D efficiency by 15%.
- Tech transfer: donor 1+ level ahead gives +0.20 nuclear / +0.15 AI progress boost.

### Stability & Political Survival

- Stability 1-9 scale. Below 5 = protests, below 3 = automatic protests, below 2 = regime collapse risk.
- Support 5-85%. Drives elections and leadership challenges.
- Elderly leaders face per-round incapacitation risk (Dealer 10%, Helmsman/Pathfinder 5-10%).
- Elections: 50% AI-calculated + 50% player vote. Columbia mid-terms R2, presidential R5-6.

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
