"""Budget decision validator — CONTRACT_BUDGET v1.1.

Pure validator for `set_budget` action payloads. No DB, no LLM, no side effects.
See `PHASES/UNMANNED_SPACECRAFT/CONTRACT_BUDGET.md` §4 for the authoritative rules.

Used by:
- AI skill harness (validates LLM-produced budget JSON before persistence)
- Human budget UI (validates form submission before POST)
- Test fixtures (asserts scripted budgets conform to schema)

The validator collects ALL errors (does not stop at first) and returns a single
report. If valid, a `normalized` copy of the decision is returned with cleaned
types (ints as ints, float social_pct, trimmed rationale) and no extra fields.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# SCHEMA CONSTANTS — keep in lock-step with CONTRACT_BUDGET v1.1 §2
# ---------------------------------------------------------------------------

REQUIRED_PRODUCTION_BRANCHES: set[str] = {
    "ground",
    "naval",
    "tactical_air",
    "strategic_missile",
    "air_defense",
}

REQUIRED_RESEARCH_FIELDS: set[str] = {"nuclear_coins", "ai_coins"}

ALLOWED_TOP_FIELDS: set[str] = {
    "action_type",
    "country_code",
    "round_num",
    "decision",
    "rationale",
    "changes",
}

ALLOWED_CHANGE_FIELDS: set[str] = {"social_pct", "production", "research"}

SOCIAL_PCT_MIN = 0.5
SOCIAL_PCT_MAX = 1.5
PRODUCTION_LEVEL_MIN = 0
PRODUCTION_LEVEL_MAX = 3
RATIONALE_MIN_CHARS = 30


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _is_real_int(value: Any) -> bool:
    """True if value is an int and NOT a bool (bool is a subclass of int)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_real_number(value: Any) -> bool:
    """True if value is int or float, excluding bool."""
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float))


# ---------------------------------------------------------------------------
# MAIN VALIDATOR
# ---------------------------------------------------------------------------


def validate_budget_decision(payload: dict) -> dict:
    """Validate a budget decision against CONTRACT_BUDGET v1.1.

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
    # STRUCTURAL VALIDATION (§4.1)
    # -----------------------------------------------------------------------

    # action_type
    action_type = payload.get("action_type")
    if action_type != "set_budget":
        errors.append(
            f"INVALID_ACTION_TYPE: got {action_type!r}, must be 'set_budget'"
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
    # RANGE VALIDATION (§4.2)
    # Runs whenever a `changes` object is present, so that a payload with both
    # structural errors (e.g. wrong decision) and range errors still reports
    # ALL of them in one pass. The engine never consumes `changes` unless
    # decision=='change', so extra validation here is harmless.
    # -----------------------------------------------------------------------

    normalized_changes: dict | None = None

    if changes_present:
        if not isinstance(changes, dict):
            errors.append(
                f"MISSING_CHANGES: 'changes' must be dict, got {type(changes).__name__}"
            )
        else:
            normalized_changes = {}

            # unknown fields inside changes
            for key in changes.keys():
                if key not in ALLOWED_CHANGE_FIELDS:
                    errors.append(
                        f"UNKNOWN_FIELD: changes.{key!r} not allowed "
                        f"(expected {sorted(ALLOWED_CHANGE_FIELDS)})"
                    )

            # ---- social_pct ----
            social_pct = changes.get("social_pct")
            if not _is_real_number(social_pct):
                errors.append(
                    f"INVALID_SOCIAL_PCT: got {social_pct!r} "
                    f"({type(social_pct).__name__}), must be float in "
                    f"[{SOCIAL_PCT_MIN}, {SOCIAL_PCT_MAX}]"
                )
            elif not (SOCIAL_PCT_MIN <= float(social_pct) <= SOCIAL_PCT_MAX):
                errors.append(
                    f"INVALID_SOCIAL_PCT: got {social_pct}, must be float in "
                    f"[{SOCIAL_PCT_MIN}, {SOCIAL_PCT_MAX}]"
                )
            else:
                normalized_changes["social_pct"] = float(social_pct)

            # ---- production ----
            production = changes.get("production")
            if not isinstance(production, dict):
                errors.append(
                    f"MISSING_PRODUCTION_BRANCH: 'production' must be dict, "
                    f"got {type(production).__name__}"
                )
            else:
                normalized_production: dict[str, int] = {}

                # missing branches
                for branch in REQUIRED_PRODUCTION_BRANCHES:
                    if branch not in production:
                        errors.append(f"MISSING_PRODUCTION_BRANCH: {branch}")

                # unknown branches
                for branch in production.keys():
                    if branch not in REQUIRED_PRODUCTION_BRANCHES:
                        errors.append(
                            f"UNKNOWN_FIELD: production.{branch!r} not allowed"
                        )

                # level range + type
                for branch, level in production.items():
                    if branch not in REQUIRED_PRODUCTION_BRANCHES:
                        continue
                    if not _is_real_int(level):
                        errors.append(
                            f"INVALID_PRODUCTION_LEVEL: {branch}={level!r} "
                            f"({type(level).__name__}), must be int in "
                            f"[{PRODUCTION_LEVEL_MIN}, {PRODUCTION_LEVEL_MAX}]"
                        )
                    elif not (PRODUCTION_LEVEL_MIN <= level <= PRODUCTION_LEVEL_MAX):
                        errors.append(
                            f"INVALID_PRODUCTION_LEVEL: {branch}={level}, "
                            f"must be int in "
                            f"[{PRODUCTION_LEVEL_MIN}, {PRODUCTION_LEVEL_MAX}]"
                        )
                    else:
                        normalized_production[branch] = int(level)

                if len(normalized_production) == len(REQUIRED_PRODUCTION_BRANCHES):
                    normalized_changes["production"] = normalized_production

            # ---- research ----
            research = changes.get("research")
            if not isinstance(research, dict):
                errors.append(
                    f"INVALID_RESEARCH_COINS: 'research' must be dict, "
                    f"got {type(research).__name__}"
                )
            else:
                normalized_research: dict[str, int] = {}

                # unknown research fields
                for key in research.keys():
                    if key not in REQUIRED_RESEARCH_FIELDS:
                        errors.append(
                            f"UNKNOWN_FIELD: research.{key!r} not allowed"
                        )

                for rf in REQUIRED_RESEARCH_FIELDS:
                    if rf not in research:
                        errors.append(
                            f"INVALID_RESEARCH_COINS: missing research.{rf}, "
                            f"must be int >= 0"
                        )
                        continue
                    val = research[rf]
                    if not _is_real_int(val):
                        errors.append(
                            f"INVALID_RESEARCH_COINS: {rf}={val!r} "
                            f"({type(val).__name__}), must be int >= 0"
                        )
                    elif val < 0:
                        errors.append(
                            f"INVALID_RESEARCH_COINS: {rf}={val}, must be int >= 0"
                        )
                    else:
                        normalized_research[rf] = int(val)

                if len(normalized_research) == len(REQUIRED_RESEARCH_FIELDS):
                    normalized_changes["research"] = normalized_research

    # -----------------------------------------------------------------------
    # BUILD NORMALIZED OUTPUT
    # -----------------------------------------------------------------------

    normalized: dict | None = None
    if not errors:
        normalized = {
            "action_type": "set_budget",
            "decision": decision,
            "rationale": rationale_trimmed,
        }
        if "country_code" in payload:
            normalized["country_code"] = payload["country_code"]
        if "round_num" in payload:
            normalized["round_num"] = payload["round_num"]

        if decision == "change" and normalized_changes is not None:
            # Ensure normalized_changes has exactly the 3 fields (social/prod/research)
            if (
                "social_pct" in normalized_changes
                and "production" in normalized_changes
                and "research" in normalized_changes
            ):
                normalized["changes"] = {
                    "social_pct": normalized_changes["social_pct"],
                    "production": normalized_changes["production"],
                    "research": normalized_changes["research"],
                }
            else:
                # Defensive: shouldn't reach here if errors is empty
                normalized = None

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "normalized": normalized,
    }
