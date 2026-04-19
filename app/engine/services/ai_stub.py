"""AI Participant Stub — placeholder for M5.

Submits sensible default decisions for all AI-operated roles in a sim.
Uses the same action pipeline as human participants (dispatch_action).
When M5 is built, replace the decision logic here — the contract stays the same.

Contract:
    Input:  sim_run_id, round_num
    Output: list of {role_id, character_name, country_id, actions: [{action_type, success, narrative}]}
    Uses:   action_dispatcher.dispatch_action (same pipeline as human submissions)
"""

import logging
from typing import Any

from engine.services.action_dispatcher import dispatch_action
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def trigger_ai_agents(
    sim_run_id: str,
    round_num: int,
    *,
    country_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Run all AI-operated roles for one round, submitting default decisions.

    Args:
        sim_run_id: Active sim run.
        round_num: Current round number.
        country_codes: Optional filter — only trigger these countries.

    Returns:
        Summary dict with per-agent results and totals.
    """
    client = get_client()

    # 1. Load AI-operated roles with their allowed actions
    query = (
        client.table("roles")
        .select("id, character_name, country_id, positions, position_type, is_ai_operated")
        .eq("sim_run_id", sim_run_id)
        .eq("is_ai_operated", True)
        .eq("status", "active")
    )
    if country_codes:
        query = query.in_("country_id", country_codes)

    roles = query.execute().data or []
    logger.info("AI stub: %d AI roles found for sim %s R%d", len(roles), sim_run_id, round_num)

    if not roles:
        return {"agents": [], "total": 0, "actions_submitted": 0, "errors": 0}

    # 2. Load role_actions for all AI roles (batch)
    role_ids = [r["id"] for r in roles]
    all_ra = (
        client.table("role_actions")
        .select("role_id, action_id")
        .eq("sim_run_id", sim_run_id)
        .in_("role_id", role_ids)
        .execute()
    ).data or []

    # Index: role_id → set of allowed action_ids
    role_action_map: dict[str, set[str]] = {}
    for ra in all_ra:
        role_action_map.setdefault(ra["role_id"], set()).add(ra["action_id"])

    # 3. For each AI role, submit default decisions
    results = []
    total_actions = 0
    total_errors = 0

    for role in roles:
        role_id = role["id"]
        cc = role["country_id"]
        name = role["character_name"]
        # Derive primary position from positions array or fallback to position_type
        positions = role.get("positions") or []
        position = positions[0] if positions else role.get("position_type", "")
        allowed = role_action_map.get(role_id, set())

        actions_taken = []

        # Decide what to submit based on position and available actions
        decisions = _decide_actions(role_id, cc, name, position, allowed, round_num)

        for decision in decisions:
            action_type = decision["action_type"]
            try:
                result = dispatch_action(sim_run_id, round_num, {
                    "action_type": action_type,
                    "role_id": role_id,
                    "country_code": cc,
                    **decision.get("params", {}),
                })
                success = result.get("success", False)
                actions_taken.append({
                    "action_type": action_type,
                    "success": success,
                    "narrative": result.get("narrative", "")[:100],
                })
                total_actions += 1
                if not success:
                    total_errors += 1
            except Exception as e:
                actions_taken.append({
                    "action_type": action_type,
                    "success": False,
                    "narrative": f"Error: {e}",
                })
                total_errors += 1

        results.append({
            "role_id": role_id,
            "character_name": name,
            "country_id": cc,
            "position_type": position,
            "actions": actions_taken,
        })

    logger.info(
        "AI stub complete: %d agents, %d actions, %d errors",
        len(results), total_actions, total_errors,
    )

    return {
        "agents": results,
        "total": len(results),
        "actions_submitted": total_actions,
        "errors": total_errors,
    }


def _decide_actions(
    role_id: str,
    country_code: str,
    name: str,
    position: str,
    allowed: set[str],
    round_num: int,
) -> list[dict]:
    """Decide which actions this AI role submits (stub logic).

    Position-based defaults:
    - head_of_state: set_budget + public_statement
    - economy_officer: set_budget + set_tariffs
    - military_chief: public_statement (no combat in stub)
    - diplomat: public_statement + propose_agreement (if available)
    - security/opposition: public_statement

    Only submits actions the role is actually authorized for.
    """
    decisions: list[dict] = []

    # Everyone makes a public statement
    if "public_statement" in allowed:
        decisions.append({
            "action_type": "public_statement",
            "params": {
                "content": f"{name} ({country_code}): Round {round_num} — monitoring developments closely.",
            },
        })

    # Head of State: set budget
    if position == "head_of_state" and "set_budget" in allowed:
        decisions.append({
            "action_type": "set_budget",
            "params": {
                "social_pct": 0.20,
                "military_coins": 0,
                "tech_coins": 0,
            },
        })

    # Economy officer: set budget + tariffs
    if position == "economy_officer":
        if "set_budget" in allowed:
            decisions.append({
                "action_type": "set_budget",
                "params": {
                    "social_pct": 0.20,
                    "military_coins": 0,
                    "tech_coins": 0,
                },
            })
        if "set_tariffs" in allowed:
            # Maintain current tariffs (no changes)
            decisions.append({
                "action_type": "set_tariffs",
                "params": {},  # Empty = maintain status quo
            })

    # OPEC members: set production
    if "set_opec" in allowed:
        decisions.append({
            "action_type": "set_opec",
            "params": {"production_level": "maintain"},
        })

    return decisions
