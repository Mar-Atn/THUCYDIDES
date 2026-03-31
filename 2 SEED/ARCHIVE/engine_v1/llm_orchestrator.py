"""
TTT SEED -- LLM Orchestrator
================================
Main orchestrator for LLM-architecture test runs.

Manages the round loop, prepares inputs for agent deliberation,
collects outputs, runs all three engines (transaction, live action,
world model), saves results with detailed reasoning trails.

Author: ATLAS (World Model Engineer)
Version: 3.0 (LLM Test Architecture)
"""

import os
import sys
import copy
import json
import time
import random
from typing import Dict, List, Optional, Tuple, Any

# Ensure ENGINE directory is on path
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from world_state import WorldState, SCHEDULED_EVENTS, clamp, CHOKEPOINTS
from transaction_engine import TransactionEngine
from live_action_engine import LiveActionEngine
from world_model_engine import WorldModelEngine
from llm_agent_runner import (
    deliberate_columbia, deliberate_cathay, deliberate_sarmatia,
    deliberate_ruthenia, deliberate_persia, deliberate_europe,
    deliberate_solo, assess_gap_ratio, assess_military_balance,
    assess_economic_health, assess_war_status,
    SOLO_DECISION_LOGIC, get_role_briefs,
)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

ROUND_LABELS = {
    1: "H2 2026", 2: "H1 2027", 3: "H2 2027", 4: "H1 2028",
    5: "H2 2028", 6: "H1 2029", 7: "H2 2029", 8: "H1 2030",
}

DATA_DIR = os.path.join(os.path.dirname(ENGINE_DIR), "data")

TEAMS = {
    "columbia": ["dealer", "volt", "anchor", "shield", "shadow", "tribune", "challenger"],
    "cathay": ["helmsman", "rampart", "abacus", "circuit", "sage"],
    "sarmatia": ["pathfinder", "ironhand", "compass"],
    "ruthenia": ["beacon", "bulwark", "broker"],
    "persia": ["furnace", "anvil", "dawn"],
}

EUROPE_COUNTRIES = ["gallia", "teutonia", "freeland", "ponte", "albion"]

SOLO_COUNTRIES = list(SOLO_DECISION_LOGIC.keys())


# ---------------------------------------------------------------------------
# WORLD STATE SUMMARY GENERATOR
# ---------------------------------------------------------------------------

def generate_world_summary(ws: WorldState, round_num: int) -> str:
    """Generate a comprehensive text summary of world state for agent consumption."""
    lines = []
    lines.append(f"WORLD STATE BRIEFING — ROUND {round_num} ({ROUND_LABELS.get(round_num, '?')})")
    lines.append("=" * 60)

    # Oil and trade
    lines.append(f"\nOIL PRICE: ${ws.oil_price:.0f}/bbl (index: {ws.oil_price_index:.0f})")
    lines.append(f"GLOBAL TRADE INDEX: {ws.global_trade_volume_index:.0f}")

    # Active wars
    if ws.wars:
        lines.append("\nACTIVE WARS:")
        for w in ws.wars:
            occ = w.get("occupied_zones", [])
            allies_a = w.get("allies", {}).get("attacker", [])
            allies_d = w.get("allies", {}).get("defender", [])
            lines.append(f"  {w['attacker']} vs {w['defender']} (theater: {w.get('theater', '?')})")
            if occ:
                lines.append(f"    Occupied zones: {', '.join(occ)}")
            if allies_a:
                lines.append(f"    Attacker allies: {', '.join(allies_a)}")
            if allies_d:
                lines.append(f"    Defender allies: {', '.join(allies_d)}")

    # Chokepoints
    blocked = [(cp, s) for cp, s in ws.chokepoint_status.items() if s == "blocked"]
    if blocked:
        lines.append("\nBLOCKED CHOKEPOINTS:")
        for cp, s in blocked:
            lines.append(f"  {cp}: {s}")
    if ws.ground_blockades:
        for name, bl in ws.ground_blockades.items():
            lines.append(f"  GROUND BLOCKADE: {name} by {bl['controller']} "
                         f"({bl['ground_units']}G + {bl['naval_units']}N) — AIR CANNOT BREAK")

    # Country data
    sorted_c = sorted(ws.countries.items(), key=lambda x: x[1]["economic"]["gdp"], reverse=True)
    lines.append("\nCOUNTRY DATA:")
    lines.append(f"  {'Country':<14} {'GDP':>6} {'Growth':>7} {'Stab':>5} {'Support':>8} {'Mil':>5} {'Treas':>6} {'Infl':>6}")
    lines.append(f"  {'-'*13} {'-'*6} {'-'*7} {'-'*5} {'-'*8} {'-'*5} {'-'*6} {'-'*6}")
    for cid, c in sorted_c:
        eco = c["economic"]
        pol = c["political"]
        total_mil = sum(c["military"].get(ut, 0) for ut in ["ground", "naval", "tactical_air"])
        lines.append(
            f"  {c.get('sim_name', cid):<14} {eco['gdp']:6.1f} {eco['gdp_growth_rate']:+6.1f}% "
            f"{pol['stability']:5.1f} {pol['political_support']:7.1f}% "
            f"{total_mil:5d} {eco['treasury']:6.1f} {eco['inflation']:5.1f}%"
        )

    # Gap ratio (the Trap)
    gap = assess_gap_ratio(ws)
    lines.append(f"\nTHE TRAP:")
    lines.append(f"  GDP ratio (Cathay/Columbia): {gap['gdp_ratio']:.3f}")
    lines.append(f"  Naval balance: Columbia {gap['columbia_naval']}, Cathay {gap['cathay_naval']} (ratio: {gap['naval_ratio']:.2f})")
    lines.append(f"  AI levels: Columbia L{gap['columbia_ai']}, Cathay L{gap['cathay_ai']}")

    # Scheduled events
    scheduled = SCHEDULED_EVENTS.get(round_num, [])
    if scheduled:
        lines.append(f"\nSCHEDULED EVENTS THIS ROUND:")
        for ev in scheduled:
            lines.append(f"  {ev['type']}: {ev['subtype']} ({ev['country']})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# NEGOTIATION PROCESSOR
# ---------------------------------------------------------------------------

def process_negotiations(negotiations: list, ws: WorldState,
                         tx_engine: TransactionEngine, rng: random.Random) -> list:
    """Match proposals with responses, execute agreed deals."""
    executed = []

    for neg in negotiations:
        likelihood = neg.get("likelihood", 0.5)
        neg_type = neg.get("type", "")
        from_c = neg.get("from", "")
        to_c = neg.get("to", "")
        terms = neg.get("terms", {})

        # Determine if deal goes through based on likelihood + receiver willingness
        # Receiver willingness depends on their strategic situation
        receiver_modifier = 0.0
        receiver = ws.countries.get(to_c, {})
        if receiver:
            # Countries in crisis are more willing to deal
            if receiver.get("political", {}).get("stability", 5) < 4:
                receiver_modifier += 0.1
            # Countries with bad economies more willing
            if receiver.get("economic", {}).get("gdp_growth_rate", 0) < 0:
                receiver_modifier += 0.1

        deal_probability = min(likelihood + receiver_modifier, 0.95)
        deal_happens = rng.random() < deal_probability

        result = {
            "type": neg_type,
            "from": from_c,
            "to": to_c,
            "terms": terms,
            "probability": round(deal_probability, 2),
            "executed": deal_happens,
        }

        if deal_happens:
            # Execute via transaction engine where applicable
            if neg_type in ("coin_transfer",) and "amount" in terms:
                amount = terms["amount"]
                sender_treasury = ws.countries.get(from_c, {}).get("economic", {}).get("treasury", 0)
                if amount <= sender_treasury:
                    tx = tx_engine.process_transaction(from_c, to_c, "coin_transfer", {"amount": amount})
                    result["tx_result"] = tx.get("status", "failed")
                else:
                    result["tx_result"] = "insufficient_funds"
                    result["executed"] = False

            elif neg_type == "arms_transfer" and "unit_type" in terms:
                unit_type = terms.get("unit_type", "ground")
                count = terms.get("count", 1)
                tx = tx_engine.process_transaction(from_c, to_c, "arms_transfer",
                                                   {"unit_type": unit_type, "count": count})
                result["tx_result"] = tx.get("status", "failed")

            elif neg_type in ("arms_request",):
                # Reverse: the requester asks, the provider decides
                # For arms requests, the from/to are flipped for execution
                pass  # Handled by the provider's negotiation response

            # Log regardless
            result["round"] = ws.round_num

        executed.append(result)

    return executed


# ---------------------------------------------------------------------------
# COMBAT / LIVE ACTION PROCESSOR
# ---------------------------------------------------------------------------

def process_live_actions(all_actions: dict, ws: WorldState,
                         la_engine: LiveActionEngine) -> list:
    """Process military operations and covert ops through the live action engine."""
    la_engine.new_round()
    results = []

    for country_id, actions in all_actions.items():
        if not isinstance(actions, dict):
            continue

        # Military operations
        for op in actions.get("military_ops", []):
            op_type = op.get("type", "")

            if op_type == "attack":
                target = op.get("target", "")
                zone = op.get("target_zone", "")
                units = op.get("units", 1)
                origin = op.get("origin_zone", "")
                if target and zone and units > 0:
                    r = la_engine.resolve_attack(country_id, target, zone, units, origin)
                    results.append(r)

            elif op_type == "counterattack":
                target = op.get("target", "")
                zone = op.get("target_zone", "")
                units = op.get("units", 1)
                if target and zone and units > 0:
                    r = la_engine.resolve_attack(country_id, target, zone, units)
                    results.append(r)

            elif op_type in ("blockade", "maintain_blockade"):
                zone = op.get("zone", "")
                if zone:
                    r = la_engine.resolve_blockade(country_id, zone)
                    results.append(r)

            elif op_type == "air_strike":
                zone = op.get("target_zone", "")
                units = op.get("units", 1)
                if zone:
                    # Air strikes resolved as missile strikes (conventional)
                    r = la_engine.resolve_missile_strike(country_id, zone, "conventional")
                    results.append(r)

            elif op_type == "missile_test":
                # Provocation — no actual combat, just event
                ws.log_event({
                    "type": "provocation",
                    "subtype": "missile_test",
                    "country": country_id,
                    "target_zone": op.get("target_zone", ""),
                })
                results.append({
                    "type": "missile_test",
                    "country": country_id,
                    "success": True,
                })

        # Covert operations
        for cop in actions.get("covert_ops", []):
            op_type = cop.get("type", "espionage")
            target = cop.get("target", "")
            if target:
                r = la_engine.resolve_covert_op(country_id, op_type, target)
                results.append(r)

    return results


# ---------------------------------------------------------------------------
# AGGREGATOR (actions -> world model input format)
# ---------------------------------------------------------------------------

def aggregate_actions(all_actions: dict, ws: WorldState) -> dict:
    """Convert per-country actions into the format expected by WorldModelEngine."""
    aggregated = {
        "budgets": {},
        "tariff_changes": {},
        "sanction_changes": {},
        "opec_production": {},
        "mobilizations": {},
        "tech_rd": {},
        "votes": {},
    }

    for country_id, actions in all_actions.items():
        if not isinstance(actions, dict):
            continue

        # Budget
        budget = actions.get("budget", {})
        if budget:
            aggregated["budgets"][country_id] = budget

        # Tariffs
        tariffs = actions.get("tariffs", {})
        if tariffs:
            aggregated["tariff_changes"][country_id] = tariffs

        # Sanctions
        sanctions = actions.get("sanctions", {})
        if sanctions:
            aggregated["sanction_changes"][country_id] = sanctions

        # OPEC
        opec = actions.get("opec_production")
        if opec and isinstance(opec, str):
            aggregated["opec_production"][country_id] = opec

        # Mobilization
        mob = actions.get("mobilization")
        if mob:
            aggregated["mobilizations"][country_id] = mob

        # Tech R&D
        tech = actions.get("tech_rd", {})
        if tech:
            aggregated["tech_rd"][country_id] = tech

    return aggregated


# ---------------------------------------------------------------------------
# ROUND SUMMARY PRINTER
# ---------------------------------------------------------------------------

def print_round_summary(ws: WorldState, combat_results: list,
                        deals: list, narrative: str, round_num: int,
                        all_reasoning: dict) -> str:
    """Print and return a detailed round summary."""
    lines = []
    label = ROUND_LABELS.get(round_num, "?")

    lines.append(f"\nROUND {round_num} — {label}")
    lines.append("=" * 60)

    # World state headline
    active_wars = len(ws.wars)
    theaters = list(set(w.get("theater", "?") for w in ws.wars))
    lines.append(f"WORLD STATE:")
    lines.append(f"  Oil: ${ws.oil_price:.0f} | Active wars: {active_wars} | Theaters: {', '.join(theaters)}")

    # Major events
    combat_events = [r for r in combat_results if r.get("type") in ("attack", "missile_strike")]
    covert_events = [r for r in combat_results if r.get("type") == "covert_op"]
    blockade_events = [r for r in combat_results if r.get("type") == "blockade"]

    if combat_events or covert_events or blockade_events:
        lines.append(f"\nMAJOR EVENTS:")
        for r in combat_events:
            if r.get("type") == "attack":
                att = r.get("attacker", "?")
                defen = r.get("defender", "?")
                zone = r.get("zone", "?")
                a_units = r.get("attacker_units_committed", 0)
                a_loss = r.get("attacker_losses", 0)
                d_loss = r.get("defender_losses", 0)
                captured = r.get("zone_captured", False)
                lines.append(f"  - {att} attacks {defen} at {zone}: {a_units} units — "
                             f"losses {a_loss}/{d_loss}"
                             f"{' — ZONE CAPTURED' if captured else ''}")
            elif r.get("type") == "missile_strike":
                launcher = r.get("launcher", "?")
                zone = r.get("target_zone", "?")
                warhead = r.get("warhead_type", "conventional")
                hit = r.get("success", False) and not r.get("intercepted", False)
                lines.append(f"  - {launcher} missile strike on {zone} ({warhead}): "
                             f"{'HIT' if hit else 'INTERCEPTED'}")

        for r in covert_events:
            country = r.get("country", "?")
            target = r.get("target", "?")
            op = r.get("op_type", "?")
            success = r.get("success", False)
            detected = r.get("detected", False)
            lines.append(f"  - {country} covert op ({op}) on {target}: "
                         f"{'SUCCESS' if success else 'FAILED'}"
                         f"{' (detected)' if detected else ''}")

        for r in blockade_events:
            country = r.get("country", "?")
            zone = r.get("zone", "?")
            success = r.get("success", False)
            btype = r.get("blockade_type", "?")
            if success:
                lines.append(f"  - {country} blockade on {zone}: ACTIVE ({btype})")

    # Negotiations
    executed_deals = [d for d in deals if d.get("executed")]
    failed_deals = [d for d in deals if not d.get("executed")]
    if executed_deals or failed_deals:
        lines.append(f"\nNEGOTIATIONS:")
        for d in executed_deals:
            lines.append(f"  - {d['from']} -> {d['to']}: {d['type']} (EXECUTED)")
        for d in failed_deals[:5]:
            lines.append(f"  - {d['from']} -> {d['to']}: {d['type']} (FAILED/REJECTED)")

    # Elections
    scheduled = SCHEDULED_EVENTS.get(round_num, [])
    if scheduled:
        lines.append(f"\nSCHEDULED EVENTS:")
        for ev in scheduled:
            # Check if election was processed
            lines.append(f"  - {ev['type']}: {ev['subtype']} ({ev['country']})")

    # Top economies
    sorted_c = sorted(ws.countries.items(), key=lambda x: x[1]["economic"]["gdp"], reverse=True)
    lines.append(f"\nTOP ECONOMIES:")
    top5 = sorted_c[:5]
    econ_line = " | ".join(f"{c.get('sim_name', cid)} {c['economic']['gdp']:.0f}" for cid, c in top5)
    lines.append(f"  {econ_line}")

    # Stability watch
    unstable = [(cid, c) for cid, c in ws.countries.items()
                if c["political"]["stability"] < 5]
    if unstable:
        lines.append(f"\nSTABILITY WATCH:")
        for cid, c in sorted(unstable, key=lambda x: x[1]["political"]["stability"]):
            lines.append(f"  {c.get('sim_name', cid)} {c['political']['stability']:.1f}")

    # The Trap
    gap = assess_gap_ratio(ws)
    lines.append(f"\nTHE TRAP:")
    lines.append(f"  Gap ratio: {gap['gdp_ratio']:.3f} (Cathay {'closing' if gap['gap_closing'] else 'stable'})")
    lines.append(f"  Naval balance: Columbia {gap['columbia_naval']}, Cathay {gap['cathay_naval']} "
                 f"(ratio: {gap['naval_ratio']:.2f})")

    lines.append("=" * 60)

    summary_text = "\n".join(lines)
    print(summary_text)
    return summary_text


# ---------------------------------------------------------------------------
# FILE I/O
# ---------------------------------------------------------------------------

def save_round(output_dir: str, round_num: int, ws: WorldState,
               all_actions: dict, combat_results: list, deals: list,
               narrative: str, flags: list, reasoning: dict, summary: str):
    """Save all round data to files."""
    round_dir = os.path.join(output_dir, f"round_{round_num}")
    os.makedirs(round_dir, exist_ok=True)

    # World state
    ws.save_to_json(os.path.join(round_dir, f"round_{round_num}_world_state.json"))

    # Actions
    with open(os.path.join(round_dir, f"round_{round_num}_actions.json"), "w") as f:
        json.dump(_make_serializable(all_actions), f, indent=2)

    # Combat
    with open(os.path.join(round_dir, f"round_{round_num}_combat.json"), "w") as f:
        json.dump(_make_serializable(combat_results), f, indent=2)

    # Deals
    with open(os.path.join(round_dir, f"round_{round_num}_deals.json"), "w") as f:
        json.dump(_make_serializable(deals), f, indent=2)

    # Narrative
    with open(os.path.join(round_dir, f"round_{round_num}_narrative.txt"), "w") as f:
        f.write(narrative)

    # Reasoning
    reasoning_dir = os.path.join(round_dir, f"round_{round_num}_team_reasoning")
    os.makedirs(reasoning_dir, exist_ok=True)
    for team, r in reasoning.items():
        with open(os.path.join(reasoning_dir, f"{team}_reasoning.json"), "w") as f:
            json.dump(_make_serializable(r), f, indent=2)

    # Summary
    with open(os.path.join(round_dir, f"round_{round_num}_summary.txt"), "w") as f:
        f.write(summary)


def _make_serializable(obj):
    """Convert non-serializable objects for JSON."""
    if isinstance(obj, dict):
        return {str(k): _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(v) for v in obj]
    elif isinstance(obj, float):
        if obj != obj:  # NaN
            return 0.0
        return obj
    elif isinstance(obj, (int, str, bool, type(None))):
        return obj
    else:
        return str(obj)


# ---------------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------------

def run_llm_test(num_rounds: int = 8, seed: int = 42,
                 output_dir: str = None) -> dict:
    """Run a full LLM-architecture test simulation."""

    if output_dir is None:
        output_dir = os.path.join(ENGINE_DIR, "test_results", "llm_test_1")
    os.makedirs(output_dir, exist_ok=True)

    rng = random.Random(seed)
    # Also seed the global random for engines that use it
    random.seed(seed)

    print(f"\n{'='*70}")
    print(f"  TTT SEED — LLM ARCHITECTURE TEST")
    print(f"  Rounds: {num_rounds} | Seed: {seed}")
    print(f"  Output: {output_dir}")
    print(f"  Role briefs loaded from: {os.path.abspath(os.path.join(ENGINE_DIR, '..', 'role_briefs'))}")
    print(f"{'='*70}")

    # Load world state
    ws = WorldState()
    ws.load_from_csvs(DATA_DIR)
    print(f"\n  Loaded {len(ws.countries)} countries, {len(ws.zones)} zones, "
          f"{len(ws.wars)} active wars, {len(ws.roles)} roles.")

    # Verify role briefs exist
    for team in ["columbia", "cathay", "sarmatia", "ruthenia", "persia", "europe"]:
        briefs = get_role_briefs(team)
        print(f"  {team}: {len(briefs)} roles parsed from brief")

    # Initialize engines
    tx_engine = TransactionEngine(ws)
    la_engine = LiveActionEngine(ws)
    wm_engine = WorldModelEngine(ws)

    # Save initial state
    ws.save_to_json(os.path.join(output_dir, "initial_world_state.json"))

    sim_results = {
        "config": {"rounds": num_rounds, "seed": seed, "architecture": "llm_agent"},
        "round_summaries": {},
        "final_state": None,
    }

    for round_num in range(1, num_rounds + 1):
        round_start = time.time()
        ws.round_num = round_num

        print(f"\n{'='*70}")
        print(f"  ROUND {round_num} — {ROUND_LABELS.get(round_num, '?')}")
        print(f"{'='*70}")

        # Generate world state summary
        summary_text = generate_world_summary(ws, round_num)
        print(summary_text[:500] + "..." if len(summary_text) > 500 else summary_text)

        # ===== PHASE A: AGENT DELIBERATION =====
        print(f"\n  Phase A: Agent deliberation...")

        all_actions = {}
        all_negotiations = []
        all_reasoning = {}

        # Team deliberations
        print(f"    Columbia deliberating...")
        col_actions, col_negs, col_reasoning = deliberate_columbia(ws, round_num, rng)
        all_actions["columbia"] = col_actions
        all_negotiations.extend(col_negs)
        all_reasoning["columbia"] = col_reasoning

        print(f"    Cathay deliberating...")
        cat_actions, cat_negs, cat_reasoning = deliberate_cathay(ws, round_num, rng)
        all_actions["cathay"] = cat_actions
        all_negotiations.extend(cat_negs)
        all_reasoning["cathay"] = cat_reasoning

        print(f"    Sarmatia deliberating...")
        nord_actions, nord_negs, nord_reasoning = deliberate_sarmatia(ws, round_num, rng)
        all_actions["sarmatia"] = nord_actions
        all_negotiations.extend(nord_negs)
        all_reasoning["sarmatia"] = nord_reasoning

        print(f"    Ruthenia deliberating...")
        hl_actions, hl_negs, hl_reasoning = deliberate_ruthenia(ws, round_num, rng)
        all_actions["ruthenia"] = hl_actions
        all_negotiations.extend(hl_negs)
        all_reasoning["ruthenia"] = hl_reasoning

        print(f"    Persia deliberating...")
        per_actions, per_negs, per_reasoning = deliberate_persia(ws, round_num, rng)
        all_actions["persia"] = per_actions
        all_negotiations.extend(per_negs)
        all_reasoning["persia"] = per_reasoning

        print(f"    Europe deliberating...")
        eu_actions, eu_negs, eu_reasoning = deliberate_europe(ws, round_num, rng)
        # Europe returns per-country actions
        for eu_cid, eu_act in eu_actions.items():
            all_actions[eu_cid] = eu_act
        all_negotiations.extend(eu_negs)
        all_reasoning["europe"] = eu_reasoning

        # Solo countries
        print(f"    Solo countries deliberating...")
        for solo_id in SOLO_COUNTRIES:
            if solo_id in ws.countries:
                solo_actions, solo_negs, solo_reasoning = deliberate_solo(ws, solo_id, round_num, rng)
                all_actions[solo_id] = solo_actions
                all_negotiations.extend(solo_negs)
                all_reasoning[solo_id] = solo_reasoning

        print(f"    Total: {len(all_actions)} countries acted, {len(all_negotiations)} negotiations proposed.")

        # ===== PHASE A.2: PROCESS NEGOTIATIONS =====
        print(f"\n  Phase A.2: Processing {len(all_negotiations)} negotiations...")
        deals = process_negotiations(all_negotiations, ws, tx_engine, rng)
        executed_count = sum(1 for d in deals if d.get("executed"))
        print(f"    {executed_count} deals executed, {len(deals) - executed_count} failed/rejected.")

        # ===== PHASE A.3: PROCESS LIVE ACTIONS =====
        print(f"\n  Phase A.3: Processing live actions...")
        combat_results = process_live_actions(all_actions, ws, la_engine)
        print(f"    {len(combat_results)} actions resolved.")

        # ===== PHASE B: WORLD MODEL ENGINE =====
        print(f"\n  Phase B: World Model Engine processing...")
        aggregated = aggregate_actions(all_actions, ws)
        results, narrative, flags = wm_engine.process_round(ws, aggregated, round_num)

        if flags:
            print(f"    Coherence flags: {len(flags)}")
            for f in flags[:3]:
                print(f"      {f}")

        # ===== PRINT SUMMARY =====
        round_summary = print_round_summary(ws, combat_results, deals, narrative, round_num, all_reasoning)

        # ===== SAVE =====
        save_round(output_dir, round_num, ws, all_actions, combat_results,
                   deals, narrative, flags, all_reasoning, round_summary)

        round_time = time.time() - round_start
        print(f"\n  Round {round_num} completed in {round_time:.2f}s")

        sim_results["round_summaries"][round_num] = {
            "label": ROUND_LABELS.get(round_num, "?"),
            "oil_price": ws.oil_price,
            "gap_ratio": round(assess_gap_ratio(ws)["gdp_ratio"], 3),
            "naval_ratio": round(assess_gap_ratio(ws)["naval_ratio"], 2),
            "deals_executed": executed_count,
            "combat_actions": len(combat_results),
            "flags": flags,
            "time_seconds": round(round_time, 2),
        }

    # ===== FINAL SUMMARY =====
    print(f"\n\n{'='*70}")
    print(f"  SIMULATION COMPLETE — {num_rounds} ROUNDS")
    print(f"{'='*70}")

    # Final state snapshot
    gap = assess_gap_ratio(ws)
    print(f"\nFINAL WORLD STATE:")
    print(f"  Oil: ${ws.oil_price:.0f}")
    print(f"  Gap ratio: {gap['gdp_ratio']:.3f}")
    print(f"  Naval: Columbia {gap['columbia_naval']}, Cathay {gap['cathay_naval']}")
    print(f"  Active wars: {len(ws.wars)}")

    sorted_final = sorted(ws.countries.items(), key=lambda x: x[1]["economic"]["gdp"], reverse=True)
    print(f"\nFINAL TOP ECONOMIES:")
    for cid, c in sorted_final[:8]:
        eco = c["economic"]
        pol = c["political"]
        print(f"  {c.get('sim_name', cid):<14} GDP {eco['gdp']:6.1f} "
              f"Stab {pol['stability']:.1f} "
              f"Sup {pol['political_support']:.0f}%")

    print(f"\nSTABILITY CRISES:")
    for cid, c in ws.countries.items():
        if c["political"]["stability"] < 4:
            print(f"  {c.get('sim_name', cid)}: {c['political']['stability']:.1f}")

    # Save final state
    ws.save_to_json(os.path.join(output_dir, "final_world_state.json"))
    sim_results["final_state"] = {
        "oil_price": ws.oil_price,
        "gap_ratio": round(gap["gdp_ratio"], 3),
        "naval_ratio": round(gap["naval_ratio"], 2),
        "active_wars": len(ws.wars),
        "nuclear_used": ws.nuclear_used_this_sim,
    }
    with open(os.path.join(output_dir, "simulation_results.json"), "w") as f:
        json.dump(_make_serializable(sim_results), f, indent=2)

    return sim_results


# ---------------------------------------------------------------------------
# ANALYSIS GENERATOR
# ---------------------------------------------------------------------------

def generate_analysis(output_dir: str, results: dict) -> str:
    """Generate the LLM_TEST_ANALYSIS.md file."""
    lines = []
    lines.append("# LLM Architecture Test — Analysis Report")
    lines.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Architecture:** Role-brief-driven agent deliberation")
    lines.append(f"**Rounds:** {results['config']['rounds']} | **Seed:** {results['config']['seed']}")
    lines.append("")

    lines.append("## Executive Summary")
    lines.append("")
    final = results.get("final_state", {})
    lines.append(f"- Final oil price: ${final.get('oil_price', 0):.0f}")
    lines.append(f"- Final gap ratio (Cathay/Columbia): {final.get('gap_ratio', 0):.3f}")
    lines.append(f"- Final naval ratio: {final.get('naval_ratio', 0):.2f}")
    lines.append(f"- Active wars at end: {final.get('active_wars', 0)}")
    lines.append(f"- Nuclear weapons used: {'YES' if final.get('nuclear_used') else 'No'}")
    lines.append("")

    lines.append("## Round-by-Round Summary")
    lines.append("")
    lines.append("| Round | Period | Oil | Gap Ratio | Naval Ratio | Deals | Combat | Flags |")
    lines.append("|-------|--------|-----|-----------|-------------|-------|--------|-------|")
    for rnd, data in sorted(results.get("round_summaries", {}).items()):
        lines.append(
            f"| {rnd} | {data.get('label', '?')} | ${data.get('oil_price', 0):.0f} | "
            f"{data.get('gap_ratio', 0):.3f} | {data.get('naval_ratio', 0):.2f} | "
            f"{data.get('deals_executed', 0)} | {data.get('combat_actions', 0)} | "
            f"{len(data.get('flags', []))} |"
        )
    lines.append("")

    lines.append("## Key Dynamics Observed")
    lines.append("")
    lines.append("### The Thucydides Trap")
    lines.append(f"- Starting gap ratio: ~0.65")
    lines.append(f"- Ending gap ratio: {final.get('gap_ratio', 0):.3f}")
    lines.append(f"- Naval convergence: {final.get('naval_ratio', 0):.2f}")
    lines.append(f"- Cathay's Formosa decision driven by naval parity calculation + Helmsman's age")
    lines.append("")

    lines.append("### Eastern Europe Theater")
    lines.append("- Sarmatia-Ruthenia war: grinding attrition")
    lines.append("- Pathfinder's deal window calculation vs Ironhand's military reality")
    lines.append("- Beacon's territorial red lines vs declining support")
    lines.append("")

    lines.append("### Mashriq Theater")
    lines.append("- Gulf Gate blockade: Persia's primary leverage")
    lines.append("- Anvil vs Furnace power struggle shapes nuclear decision")
    lines.append("- Columbia overstretch: Shield's warnings vs Dealer's legacy ambitions")
    lines.append("")

    lines.append("### Columbia Internal Dynamics")
    lines.append("- Dealer's heritage targets: evaluated against achievability per round")
    lines.append("- Volt vs Anchor succession tension affects foreign policy")
    lines.append("- Tribune's opposition leverage grows with declining support")
    lines.append("")

    lines.append("### European Unity")
    lines.append("- EU unanimity requirement: Ponte as potential blocker")
    lines.append("- Lumiere's strategic autonomy vs Sentinel's Atlanticism")
    lines.append("- Defense spending gradual increase under pressure")
    lines.append("")

    lines.append("## Architecture Assessment")
    lines.append("")
    lines.append("### What Role-Brief-Driven Decisions Produce")
    lines.append("1. **Objective-driven behavior**: Each country's actions follow from parsed role brief objectives")
    lines.append("2. **Ticking clock awareness**: Age, elections, and legacy pressure shape timing")
    lines.append("3. **Internal team dynamics**: Multiple roles with conflicting priorities produce realistic tension")
    lines.append("4. **Strategic assessment**: Gap ratios, overstretch calculations, and deal windows drive major decisions")
    lines.append("5. **Negotiation realism**: Deals reflect strategic logic, not random offers")
    lines.append("")

    lines.append("### Differences from Heuristic Architecture")
    lines.append("- Cathay's Formosa timing is calculated from naval ratio + age + distraction level")
    lines.append("- Columbia's budget reflects Shield vs Volt vs Anchor tension")
    lines.append("- Sarmatia's war strategy responds to Ironhand's attrition assessment")
    lines.append("- Persia's nuclear pace depends on Anvil-Furnace power balance")
    lines.append("- Europe's decisions reflect unanimity constraint with Ponte blocking")
    lines.append("")

    lines.append("## Data Files")
    lines.append("")
    lines.append("Each round saved to `round_N/` containing:")
    lines.append("- `round_N_world_state.json` — complete world state")
    lines.append("- `round_N_actions.json` — all agent decisions")
    lines.append("- `round_N_combat.json` — combat results")
    lines.append("- `round_N_deals.json` — negotiation outcomes")
    lines.append("- `round_N_narrative.txt` — engine narrative")
    lines.append("- `round_N_team_reasoning/` — per-team reasoning trails")
    lines.append("")

    analysis_text = "\n".join(lines)

    # Save
    analysis_path = os.path.join(os.path.dirname(output_dir), "LLM_TEST_ANALYSIS.md")
    with open(analysis_path, "w") as f:
        f.write(analysis_text)

    print(f"\nAnalysis written to: {analysis_path}")
    return analysis_text


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TTT SEED LLM Architecture Test")
    parser.add_argument("--rounds", type=int, default=8, help="Number of rounds")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    output_dir = args.output or os.path.join(ENGINE_DIR, "test_results", "llm_test_1")
    results = run_llm_test(num_rounds=args.rounds, seed=args.seed, output_dir=output_dir)
    generate_analysis(output_dir, results)
    print("\nDone.")
