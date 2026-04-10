"""Tariff decision validator — CONTRACT_TARIFFS v1.0.

Pure validator for `set_tariffs` action payloads. No DB, no LLM, no side effects.
See `PHASES/UNMANNED_SPACECRAFT/CONTRACT_TARIFFS.md` §4 for the authoritative rules.

Used by:
- AI skill harness (validates LLM-produced tariff JSON before persistence)
- Human tariff UI (validates form submission before POST) — future
- Test fixtures (asserts scripted decisions conform to schema)
- resolve_round.py set_tariffs handler (gates writes to the tariffs state table)

The validator collects ALL errors (does not stop at first) and returns a single
report. If valid, a `normalized` copy of the decision is returned with cleaned
types (ints as ints, lowercased country codes, trimmed strings) and no extra fields.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# SCHEMA CONSTANTS — keep in lock-step with CONTRACT_TARIFFS v1.0 §2 + §4
# ---------------------------------------------------------------------------

#: Canonical 20-country roster. Sourced from the `countries` table on
#: 2026-04-10. Validator rejects any target outside this set with
#: UNKNOWN_TARGET. Update this constant if the country list changes.
CANONICAL_COUNTRIES: frozenset[str] = frozenset({
    "albion", "bharata", "caribe", "cathay", "choson", "columbia",
    "formosa", "freeland", "gallia", "hanguk", "levantia", "mirage",
    "persia", "phrygia", "ponte", "ruthenia", "sarmatia", "solaria",
    "teutonia", "yamato",
})

ALLOWED_TOP_FIELDS: frozenset[str] = frozenset({
    "action_type",
    "country_code",
    "round_num",
    "decision",
    "rationale",
    "changes",
})

ALLOWED_CHANGE_FIELDS: frozenset[str] = frozenset({"tariffs"})

LEVEL_MIN = 0
LEVEL_MAX = 3
RATIONALE_MIN_CHARS = 30


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _is_real_int(value: Any) -> bool:
    """True if value is an int and NOT a bool (bool is a subclass of int)."""
    return isinstance(value, int) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# MAIN VALIDATOR
# ---------------------------------------------------------------------------


def validate_tariffs_decision(payload: dict) -> dict:
    """Validate a tariff decision against CONTRACT_TARIFFS v1.0.

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
    if action_type != "set_tariffs":
        errors.append(
            f"INVALID_ACTION_TYPE: got {action_type!r}, must be 'set_tariffs'"
        )

    # country_code (the imposer)
    imposer_raw = payload.get("country_code")
    imposer: str | None = None
    if isinstance(imposer_raw, str) and imposer_raw.strip():
        imposer = imposer_raw.strip().lower()

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
    # CHANGES VALIDATION (§4)
    # Runs whenever a `changes` object is present, so a payload with both
    # structural errors and content errors reports ALL of them in one pass.
    # -----------------------------------------------------------------------

    normalized_tariffs: dict[str, int] | None = None

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

            tariffs = changes.get("tariffs")
            if not isinstance(tariffs, dict):
                errors.append(
                    f"MISSING_CHANGES: 'changes.tariffs' must be dict, "
                    f"got {type(tariffs).__name__}"
                )
            else:
                if len(tariffs) == 0:
                    errors.append(
                        "EMPTY_CHANGES: decision='change' with empty tariffs dict — "
                        "use decision='no_change' instead"
                    )

                normalized_tariffs = {}
                for target_raw, level_raw in tariffs.items():
                    # target country code
                    if not isinstance(target_raw, str) or not target_raw.strip():
                        errors.append(
                            f"UNKNOWN_TARGET: target key must be non-empty string, "
                            f"got {target_raw!r}"
                        )
                        continue
                    target = target_raw.strip().lower()

                    if target not in CANONICAL_COUNTRIES:
                        errors.append(
                            f"UNKNOWN_TARGET: {target!r} is not in the canonical "
                            f"country roster ({len(CANONICAL_COUNTRIES)} countries)"
                        )
                        # still validate level so we report all errors

                    if imposer is not None and target == imposer:
                        errors.append(
                            f"SELF_TARIFF: imposer {imposer!r} cannot tariff itself"
                        )

                    # level
                    if not _is_real_int(level_raw):
                        errors.append(
                            f"INVALID_LEVEL: tariffs[{target!r}] must be int in "
                            f"[{LEVEL_MIN}, {LEVEL_MAX}], got {level_raw!r} "
                            f"({type(level_raw).__name__})"
                        )
                        continue
                    if not (LEVEL_MIN <= level_raw <= LEVEL_MAX):
                        errors.append(
                            f"INVALID_LEVEL: tariffs[{target!r}] = {level_raw}, "
                            f"must be in [{LEVEL_MIN}, {LEVEL_MAX}]"
                        )
                        continue

                    # only normalize entries that pass every check
                    if (
                        target in CANONICAL_COUNTRIES
                        and (imposer is None or target != imposer)
                    ):
                        normalized_tariffs[target] = int(level_raw)

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
        "action_type": "set_tariffs",
        "country_code": imposer,
        "round_num": payload.get("round_num"),
        "decision": decision,
        "rationale": rationale_trimmed,
    }
    if decision == "change":
        normalized["changes"] = {"tariffs": normalized_tariffs or {}}

    return {
        "valid": True,
        "errors": [],
        "warnings": warnings,
        "normalized": normalized,
    }
