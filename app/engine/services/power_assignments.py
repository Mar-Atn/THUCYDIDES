"""Power Assignments — authorization backbone of the SIM.

Determines WHO can do WHAT on behalf of each country:

  Military:        move_units, attack_*, blockade, launch_missile, martial_law
  Economic:        set_budget, set_tariffs, set_sanctions, set_opec, propose_transaction (country assets)
  Foreign Affairs: propose_agreement, propose_transaction (deals), sign agreements

HoS is IMPLICIT — always authorized for everything. Not stored in the table.
A "vacant" assignment (assigned_role_id = NULL) means HoS is sole authority.

Functions:
  seed_defaults(sim_run_id)           — populate from canonical starting table
  check_authorization(role_id, action_type, sim_run_id) → {authorized, reason}
  reassign_power(sim_run_id, country, power_type, new_role, by_role) → {success}
  get_assignments(sim_run_id, country?) → list
"""

from __future__ import annotations

from engine.services.common import get_scenario_id, write_event

import logging
from typing import Optional

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Canonical starting assignments (Template v1.0)
# ---------------------------------------------------------------------------

#: Default power assignments for multi-role countries.
#: Single-HoS countries have no entries → HoS holds all powers.
DEFAULT_ASSIGNMENTS: list[dict] = [
    # Columbia
    {"country_code": "columbia", "power_type": "military",        "assigned_role_id": "shield"},
    {"country_code": "columbia", "power_type": "economic",        "assigned_role_id": "volt"},
    {"country_code": "columbia", "power_type": "foreign_affairs",  "assigned_role_id": "anchor"},
    # Cathay
    {"country_code": "cathay",   "power_type": "military",        "assigned_role_id": "rampart"},
    {"country_code": "cathay",   "power_type": "economic",        "assigned_role_id": "abacus"},
    {"country_code": "cathay",   "power_type": "foreign_affairs",  "assigned_role_id": "sage"},
    # Sarmatia
    {"country_code": "sarmatia", "power_type": "military",        "assigned_role_id": "ironhand"},
    {"country_code": "sarmatia", "power_type": "economic",        "assigned_role_id": "compass"},
    {"country_code": "sarmatia", "power_type": "foreign_affairs",  "assigned_role_id": "compass"},
    # Ruthenia
    {"country_code": "ruthenia", "power_type": "military",        "assigned_role_id": "bulwark"},
    {"country_code": "ruthenia", "power_type": "economic",        "assigned_role_id": "broker"},
    {"country_code": "ruthenia", "power_type": "foreign_affairs",  "assigned_role_id": None},  # HoS holds
    # Persia
    {"country_code": "persia",   "power_type": "military",        "assigned_role_id": "anvil"},
    {"country_code": "persia",   "power_type": "economic",        "assigned_role_id": None},   # HoS holds
    {"country_code": "persia",   "power_type": "foreign_affairs",  "assigned_role_id": "dawn"},
]

#: Which action_types require which power_type
ACTION_TO_POWER: dict[str, str] = {
    # Military
    "move_units": "military",
    "attack_ground": "military",
    "attack_air": "military",
    "attack_naval": "military",
    "attack_bombardment": "military",
    "launch_missile": "military",
    "blockade": "military",
    "martial_law": "military",
    "basing_rights": "military",
    # Economic
    "set_budget": "economic",
    "set_tariffs": "economic",
    "set_sanctions": "economic",
    "set_opec": "economic",
    # Foreign Affairs
    "propose_agreement": "foreign_affairs",
    # Transactions: depends on content — simplified to foreign_affairs
    "propose_transaction": "foreign_affairs",
}

#: Actions that ANY role can do (no power assignment needed)
UNRESTRICTED_ACTIONS: frozenset[str] = frozenset({
    "public_statement",
    "covert_op",       # card-gated, not power-gated
    "intelligence",
    "sabotage",
    "propaganda",
    "election_meddling",
    "assassination",    # card-gated
    "mass_protest",     # card-gated
    "nuclear_test",     # goes through 3-way authorization chain
    "intercept_nuclear",
})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def seed_defaults(sim_run_id: str) -> int:
    """Populate power_assignments for a new sim_run from the canonical defaults.

    Returns the number of rows inserted.
    """
    client = get_client()
    rows = [
        {**a, "sim_run_id": sim_run_id, "assigned_round": 0}
        for a in DEFAULT_ASSIGNMENTS
    ]
    if not rows:
        return 0
    try:
        client.table("power_assignments").upsert(
            rows, on_conflict="sim_run_id,country_code,power_type"
        ).execute()
        logger.info("[powers] seeded %d default assignments for run %s", len(rows), sim_run_id)
        return len(rows)
    except Exception as e:
        logger.warning("power_assignments seed failed: %s", e)
        return 0


def check_authorization(
    role_id: str,
    action_type: str,
    sim_run_id: str,
    country_code: str,
    roles: dict[str, dict] | None = None,
) -> dict:
    """Check if a role is authorized to perform an action.

    Returns ``{authorized: bool, reason: str}``.

    Authorization logic:
    1. If action is unrestricted → authorized
    2. If role is HoS of the country → authorized (always)
    3. If action maps to a power_type → check power_assignments table
    4. If the role is assigned that power → authorized
    5. If no one is assigned (vacant) → only HoS can act → unauthorized
    """
    # Unrestricted actions
    if action_type in UNRESTRICTED_ACTIONS:
        return {"authorized": True, "reason": "unrestricted action"}

    # HoS check
    from engine.config.position_actions import has_position
    if roles:
        role_info = roles.get(role_id) or {}
        if has_position(role_info, "head_of_state") and role_info.get("country_code") == country_code:
            return {"authorized": True, "reason": "HoS — inherent authority"}

    # Power assignment check
    power_type = ACTION_TO_POWER.get(action_type)
    if not power_type:
        # Unknown action type — default to authorized (don't block novel actions)
        return {"authorized": True, "reason": "no power mapping — default allow"}

    client = get_client()
    try:
        res = client.table("power_assignments").select("assigned_role_id") \
            .eq("sim_run_id", sim_run_id) \
            .eq("country_code", country_code) \
            .eq("power_type", power_type) \
            .limit(1).execute()

        if not res.data:
            # No assignment row → only HoS can act
            return {"authorized": False,
                    "reason": f"no {power_type} assignment for {country_code} — only HoS can act"}

        assigned = res.data[0].get("assigned_role_id")
        if assigned is None:
            # Vacant — only HoS
            return {"authorized": False,
                    "reason": f"{power_type} is vacant (HoS-only) in {country_code}"}

        if assigned == role_id:
            return {"authorized": True,
                    "reason": f"{role_id} holds {power_type} power for {country_code}"}

        return {"authorized": False,
                "reason": f"{power_type} power assigned to {assigned}, not {role_id}"}

    except Exception as e:
        logger.warning("authorization check failed: %s — defaulting to allow", e)
        return {"authorized": True, "reason": "auth check failed — default allow"}


def reassign_power(
    sim_run_id: str,
    country_code: str,
    power_type: str,
    new_role_id: Optional[str],
    by_role_id: str,
    round_num: int,
    roles: dict[str, dict] | None = None,
) -> dict:
    """HoS reassigns a power to a different role (or vacates it).

    ``new_role_id = None`` means HoS takes it back (vacates the slot).

    Returns ``{success, previous_role, new_role, message}``.
    """
    # Only HoS can reassign
    if roles:
        role_info = roles.get(by_role_id) or {}
        if not has_position(role_info, "head_of_state"):
            return {"success": False, "message": f"{by_role_id} is not HoS — cannot reassign powers"}
        if role_info.get("country_code") != country_code:
            return {"success": False, "message": f"{by_role_id} is not HoS of {country_code}"}

    if power_type not in ("military", "economic", "foreign_affairs"):
        return {"success": False, "message": f"invalid power_type: {power_type}"}

    client = get_client()

    # Get current assignment
    res = client.table("power_assignments").select("assigned_role_id") \
        .eq("sim_run_id", sim_run_id) \
        .eq("country_code", country_code) \
        .eq("power_type", power_type) \
        .limit(1).execute()

    previous_role = res.data[0]["assigned_role_id"] if res.data else None

    # Upsert new assignment
    client.table("power_assignments").upsert({
        "sim_run_id": sim_run_id,
        "country_code": country_code,
        "power_type": power_type,
        "assigned_role_id": new_role_id,
        "assigned_by_role": by_role_id,
        "assigned_round": round_num,
    }, on_conflict="sim_run_id,country_code,power_type").execute()

    # Write events
    scenario_id = get_scenario_id(client, sim_run_id)
    new_label = new_role_id or "(vacant — HoS holds)"
    prev_label = previous_role or "(vacant)"
    write_event(client, sim_run_id, scenario_id, round_num, country_code,
                "power_reassigned",
                f"{country_code} {power_type} power: {prev_label} → {new_label} (by {by_role_id})",
                {"power_type": power_type, "previous": previous_role,
                 "new": new_role_id, "by": by_role_id})

    logger.info("[powers] %s %s: %s → %s (by %s)",
                country_code, power_type, previous_role, new_role_id, by_role_id)

    return {"success": True, "previous_role": previous_role,
            "new_role": new_role_id, "message": f"{power_type} reassigned"}


def get_assignments(
    sim_run_id: str,
    country_code: Optional[str] = None,
) -> list[dict]:
    """Return all power assignments, optionally filtered by country."""
    client = get_client()
    q = client.table("power_assignments").select("*").eq("sim_run_id", sim_run_id)
    if country_code:
        q = q.eq("country_code", country_code)
    return q.order("country_code").execute().data or []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


