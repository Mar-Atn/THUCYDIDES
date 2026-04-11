"""OPEC production decision validator — CONTRACT_OPEC v1.0.

Pure validator for `set_opec` action payloads. No DB, no LLM, no side effects.
See `PHASES/UNMANNED_SPACECRAFT/CONTRACT_OPEC.md` §4 for the authoritative rules.

Used by:
- AI skill harness (validates LLM-produced OPEC JSON before persistence)
- Human OPEC UI (validates form submission before POST) — future
- Test fixtures (asserts scripted decisions conform to schema)
- resolve_round.py set_opec handler (gates writes to country_states_per_round)

The validator collects ALL errors (does not stop at first) and returns a single
report. Only OPEC+ members can submit; non-members are rejected with
NOT_OPEC_MEMBER. Single-value enum decision: production_level ∈ {min, low,
normal, high, max}.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# SCHEMA CONSTANTS — keep in lock-step with CONTRACT_OPEC v1.0
# ---------------------------------------------------------------------------

#: Canonical OPEC+ roster. Sourced from countries.opec_member = true
#: as of 2026-04-10 (after Caribe/Venezuela was corrected to TRUE).
#: Must be kept in sync with engine/agents/full_round_runner.py:OPEC_MEMBERS.
CANONICAL_OPEC_MEMBERS: frozenset[str] = frozenset({
    "caribe", "mirage", "persia", "sarmatia", "solaria",
})

VALID_PRODUCTION_LEVELS: frozenset[str] = frozenset({
    "min", "low", "normal", "high", "max",
})

ALLOWED_TOP_FIELDS: frozenset[str] = frozenset({
    "action_type",
    "country_code",
    "round_num",
    "decision",
    "rationale",
    "changes",
})

ALLOWED_CHANGE_FIELDS: frozenset[str] = frozenset({"production_level"})

RATIONALE_MIN_CHARS = 30


# ---------------------------------------------------------------------------
# MAIN VALIDATOR
# ---------------------------------------------------------------------------


def validate_opec_decision(payload: dict) -> dict:
    """Validate an OPEC production decision against CONTRACT_OPEC v1.0.

    Args:
        payload: the decision dict submitted by participant (AI or human)

    Returns:
        {
            "valid":      bool,
            "errors":     list[str],      # error codes with messages
            "warnings":   list[str],      # soft warnings (non-blocking)
            "normalized": dict | None     # sanitized decision if valid, else None
        }
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return {
            "valid": False,
            "errors": [f"INVALID_PAYLOAD: expected dict, got {type(payload).__name__}"],
            "warnings": [],
            "normalized": None,
        }

    # -----------------------------------------------------------------------
    # STRUCTURAL VALIDATION (§4)
    # -----------------------------------------------------------------------

    # action_type
    action_type = payload.get("action_type")
    if action_type != "set_opec":
        errors.append(
            f"INVALID_ACTION_TYPE: got {action_type!r}, must be 'set_opec'"
        )

    # country_code — must be an OPEC+ member
    actor_raw = payload.get("country_code")
    actor: str | None = None
    if isinstance(actor_raw, str) and actor_raw.strip():
        actor = actor_raw.strip().lower()
        if actor not in CANONICAL_OPEC_MEMBERS:
            errors.append(
                f"NOT_OPEC_MEMBER: {actor!r} is not in the OPEC+ roster "
                f"({sorted(CANONICAL_OPEC_MEMBERS)})"
            )
    else:
        errors.append(
            f"NOT_OPEC_MEMBER: country_code missing or not a string, "
            f"got {actor_raw!r}"
        )

    # decision
    decision = payload.get("decision")
    if decision not in ("change", "no_change"):
        errors.append(
            f"INVALID_DECISION: got {decision!r}, must be 'change' or 'no_change'"
        )

    # rationale
    rationale = payload.get("rationale")
    rationale_trimmed = ""
    if not isinstance(rationale, str):
        errors.append(
            f"RATIONALE_TOO_SHORT: got {type(rationale).__name__}, "
            f"must be str >= {RATIONALE_MIN_CHARS} chars"
        )
    else:
        rationale_trimmed = rationale.strip()
        if len(rationale_trimmed) < RATIONALE_MIN_CHARS:
            errors.append(
                f"RATIONALE_TOO_SHORT: {len(rationale_trimmed)} chars, "
                f"must be >= {RATIONALE_MIN_CHARS}"
            )

    # changes presence rules
    changes = payload.get("changes")
    changes_present = "changes" in payload and changes is not None

    if decision == "change" and not changes_present:
        errors.append("MISSING_CHANGES: decision='change' requires 'changes' object")
    if decision == "no_change" and changes_present:
        errors.append(
            "UNEXPECTED_CHANGES: decision='no_change' must not include 'changes'"
        )

    # unknown top-level fields
    for field_name in payload.keys():
        if field_name not in ALLOWED_TOP_FIELDS:
            errors.append(f"UNKNOWN_FIELD: top-level field {field_name!r} not allowed")

    # -----------------------------------------------------------------------
    # CHANGES VALIDATION
    # -----------------------------------------------------------------------

    normalized_level: str | None = None

    if changes_present:
        if not isinstance(changes, dict):
            errors.append(
                f"MISSING_CHANGES: 'changes' must be dict, got {type(changes).__name__}"
            )
        else:
            # unknown fields inside changes
            for key in changes.keys():
                if key not in ALLOWED_CHANGE_FIELDS:
                    errors.append(
                        f"UNKNOWN_FIELD: changes.{key!r} not allowed "
                        f"(expected {sorted(ALLOWED_CHANGE_FIELDS)})"
                    )

            level_raw = changes.get("production_level")
            if not isinstance(level_raw, str):
                errors.append(
                    f"INVALID_LEVEL: production_level must be a string, "
                    f"got {type(level_raw).__name__}"
                )
            else:
                level = level_raw.strip().lower()
                if level not in VALID_PRODUCTION_LEVELS:
                    errors.append(
                        f"INVALID_LEVEL: {level!r} not in "
                        f"{sorted(VALID_PRODUCTION_LEVELS)}"
                    )
                else:
                    normalized_level = level

    # -----------------------------------------------------------------------
    # BUILD NORMALIZED OUTPUT
    # -----------------------------------------------------------------------

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "normalized": None,
        }

    normalized: dict = {
        "action_type": "set_opec",
        "country_code": actor,
        "round_num": payload.get("round_num"),
        "decision": decision,
        "rationale": rationale_trimmed,
    }
    if decision == "change":
        normalized["changes"] = {"production_level": normalized_level}

    return {
        "valid": True,
        "errors": [],
        "warnings": warnings,
        "normalized": normalized,
    }
