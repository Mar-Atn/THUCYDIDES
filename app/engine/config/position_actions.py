"""Position-based action rules engine.

Source of truth: MODULES/M9_SIM_SETUP/DESIGN_ACTIONS_TAB.md (approved 2026-04-19)
Companion doc: MODULES/M6_HUMAN_INTERFACE/DESIGN_POSITIONS_AND_ACTIONS.md

Defines what PROACTIVE actions are available to each role based on:
  1. Universal actions (Layer 1) — all roles get these
  2. Position actions (Layer 2) — based on positions held
  3. Dynamic conditions — based on country state (nuclear, OPEC, etc.)

REACTIVE actions (nuclear_authorize, nuclear_intercept, accept_transaction,
sign_agreement, cast_vote, cast_election_vote, accept_meeting) are NOT
computed here — they are handled at runtime by their respective engines
and appear in "Actions Expected Now" when triggered.

Org-based actions (call_org_meeting, publish_org_decision) are NOT
computed here — they are added by position_helpers.py which has access
to org_memberships data.

The role_actions table is a CACHE of computed permissions.
Source of truth: positions[] + country state → available actions.
"""

from typing import Optional

# ---------------------------------------------------------------------------
# Layer 1: Universal actions (available to ALL roles regardless of position)
# ---------------------------------------------------------------------------
UNIVERSAL_ACTIONS: set[str] = {
    "public_statement",
    "invite_to_meet",
    "change_leader",
}

# ---------------------------------------------------------------------------
# Layer 2: Position-based actions (baseline per position)
# Reactive actions are EXCLUDED — they are computed at runtime.
# ---------------------------------------------------------------------------
POSITION_ACTIONS: dict[str, set[str]] = {
    "head_of_state": {
        # Political
        "declare_war",
        "arrest",
        "reassign_types",
        "martial_law",
        # Economic
        "set_budget",
        "set_tariffs",
        "set_sanctions",
        # set_opec added dynamically (OPEC members only)
        # Military
        "ground_attack",
        "air_strike",
        "naval_combat",
        "naval_bombardment",
        "launch_missile_conventional",
        "naval_blockade",
        "move_units",
        "ground_move",
        # Nuclear (dynamic — gated on nuclear level)
        # nuclear_test added dynamically (nuclear_level >= 1)
        # nuclear_launch_initiate added dynamically (nuclear_confirmed)
        # Diplomatic
        "propose_transaction",
        "propose_agreement",
        "basing_rights",
    },
    "military": {
        # Combat
        "ground_attack",
        "air_strike",
        "naval_combat",
        "naval_bombardment",
        "launch_missile_conventional",
        "naval_blockade",
        "move_units",
        "ground_move",
        # Covert
        "intelligence",
        "covert_operation",
        "assassination",
    },
    "economy": {
        "set_budget",
        "set_tariffs",
        "set_sanctions",
        # set_opec added dynamically (OPEC members only)
    },
    "diplomat": {
        "propose_transaction",
        "propose_agreement",
        "basing_rights",
        "intelligence",
    },
    "security": {
        "intelligence",
        "covert_operation",
        "assassination",
        "arrest",
    },
    "opposition": {
        "intelligence",
    },
}

# ---------------------------------------------------------------------------
# Dynamic condition constants
# ---------------------------------------------------------------------------

# Countries eligible for martial_law
MARTIAL_LAW_ELIGIBLE: set[str] = {"sarmatia", "ruthenia", "persia", "cathay"}

# OPEC+ member countries
OPEC_MEMBERS: set[str] = {"caribe", "mirage", "persia", "sarmatia", "solaria"}

# Columbia-specific election actions (added for Columbia opposition roles)
COLUMBIA_ELECTION_ACTIONS: set[str] = {"self_nominate"}

# ---------------------------------------------------------------------------
# Intelligence & Covert Ops limits per SIM (not per round)
# When position is reassigned, remaining quota transfers to new holder.
# ---------------------------------------------------------------------------
INTEL_LIMITS: dict[Optional[str], dict[str, int]] = {
    "security": {"intelligence": 5, "covert_operation": 5, "assassination": 3},
    "military": {"intelligence": 5, "covert_operation": 5, "assassination": 2},
    "diplomat": {"intelligence": 1},
    "opposition": {"intelligence": 2},
    None: {},  # citizen with no position — 0 intelligence
}

# ---------------------------------------------------------------------------
# Org-based actions — applied by position_helpers.py, not compute_actions()
# ---------------------------------------------------------------------------
ORG_MEMBER_ACTIONS: set[str] = {"call_org_meeting"}
ORG_CHAIRMAN_ACTIONS: set[str] = {"publish_org_decision"}

# ---------------------------------------------------------------------------
# Reactive actions — NEVER stored in role_actions, computed at runtime
# ---------------------------------------------------------------------------
REACTIVE_ACTIONS: set[str] = {
    "nuclear_authorize",
    "nuclear_intercept",
    "accept_transaction",
    "sign_agreement",
    "cast_vote",
    "cast_election_vote",
    "accept_meeting",
}

# Nuclear authorize: 2 roles per country, derived from position priority
AUTHORIZE_PRIORITY: list[str] = ["military", "security", "diplomat", "economy", "opposition"]


def compute_actions(
    positions: list[str],
    country_code: str,
    country_state: dict,
) -> set[str]:
    """Compute the proactive action set for a role.

    Does NOT include:
    - Reactive actions (nuclear_authorize, accept_transaction, etc.)
    - Org-based actions (call_org_meeting, publish_org_decision)
    These are added by position_helpers.py which has DB access.

    Args:
        positions: List of position strings (e.g. ['head_of_state', 'security']).
                   Empty list = unpositioned citizen.
        country_code: Country ID (e.g. 'columbia', 'persia').
        country_state: Dict with keys: nuclear_level, nuclear_confirmed.

    Returns:
        Set of action IDs the role is authorized to proactively perform.
    """
    actions = set(UNIVERSAL_ACTIONS)

    nuclear_level = int(country_state.get("nuclear_level", 0) or 0)
    nuclear_confirmed = bool(country_state.get("nuclear_confirmed", False))

    if not positions:
        # Citizen with no position — universal actions only, no intelligence
        return actions

    # Add position-based actions for each held position
    for pos in positions:
        pos_actions = POSITION_ACTIONS.get(pos, set())
        actions.update(pos_actions)

    # --- Dynamic conditions ---

    has_hos = "head_of_state" in positions
    has_economy = "economy" in positions

    # Nuclear: test requires nuclear_level >= 1, HoS only
    if has_hos and nuclear_level >= 1:
        actions.add("nuclear_test")

    # Nuclear: launch requires nuclear_confirmed, HoS only
    if has_hos and nuclear_confirmed:
        actions.add("nuclear_launch_initiate")

    # OPEC: set_opec for HoS or economy in OPEC member countries
    if country_code in OPEC_MEMBERS and (has_hos or has_economy):
        actions.add("set_opec")

    # Martial law: remove for non-eligible countries
    if "martial_law" in actions and country_code not in MARTIAL_LAW_ELIGIBLE:
        actions.discard("martial_law")

    # Columbia: opposition gets election actions
    if country_code == "columbia" and "opposition" in positions:
        actions.update(COLUMBIA_ELECTION_ACTIONS)

    return actions


# ---------------------------------------------------------------------------
# Utility: check positions with legacy field fallback
# ---------------------------------------------------------------------------

_LEGACY_POSITION_MAP: dict[str, str] = {
    "head_of_state": "head_of_state",
    "military_chief": "military",
    "economy_officer": "economy",
    "diplomat": "diplomat",
    "security": "security",
    "opposition": "opposition",
}


def has_position(role: dict, position: str) -> bool:
    """Check if a role holds a given position.

    Uses the positions array (primary) with fallback to legacy fields.
    """
    positions = role.get("positions")
    if positions is not None and isinstance(positions, list):
        return position in positions

    # Fallback to legacy boolean fields
    if position == "head_of_state":
        return bool(role.get("is_head_of_state"))
    if position == "military":
        return bool(role.get("is_military_chief"))
    if position == "economy":
        return bool(role.get("is_economy_officer"))
    if position == "diplomat":
        return bool(role.get("is_diplomat"))
    if position == "security":
        return role.get("position_type") == "security"
    if position == "opposition":
        return role.get("position_type") == "opposition"

    return False


def get_positions(role: dict) -> list[str]:
    """Get a role's positions list with legacy fallback."""
    positions = role.get("positions")
    if positions is not None and isinstance(positions, list):
        return list(positions)

    # Derive from legacy fields
    result = []
    if role.get("is_head_of_state"):
        result.append("head_of_state")
    if role.get("is_military_chief"):
        result.append("military")
    if role.get("is_economy_officer"):
        result.append("economy")
    if role.get("is_diplomat"):
        result.append("diplomat")
    if role.get("position_type") == "security":
        result.append("security")
    if role.get("position_type") == "opposition":
        result.append("opposition")
    return result
