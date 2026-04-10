"""Sanction decision validator — CONTRACT_SANCTIONS v1.0.

Pure validator for `set_sanctions` action payloads. No DB, no LLM, no side effects.
See `PHASES/UNMANNED_SPACECRAFT/CONTRACT_SANCTIONS.md` §4 for the authoritative rules.

Used by:
- AI skill harness (validates LLM-produced sanctions JSON before persistence)
- Human sanctions UI (validates form submission before POST) — future
- Test fixtures (asserts scripted decisions conform to schema)
- resolve_round.py set_sanctions handler (gates writes to the sanctions state table)

The validator collects ALL errors (does not stop at first) and returns a single
report. If valid, a `normalized` copy of the decision is returned with cleaned
types (ints as ints, lowercased country codes, trimmed strings) and no extra fields.

Signed level support: sanctions levels are int in [-3, +3]. Negative levels are
evasion support (subtract from coalition coverage). Positive levels are active
sanctions.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# SCHEMA CONSTANTS — keep in lock-step with CONTRACT_SANCTIONS v1.0 §2 + §4
# ---------------------------------------------------------------------------

#: Canonical 20-country roster. Sourced from the `countries` table 2026-04-10.
#: Validator rejects any target outside this set with UNKNOWN_TARGET.
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

ALLOWED_CHANGE_FIELDS: frozenset[str] = frozenset({"sanctions"})

LEVEL_MIN = -3   # signed — negative = evasion support
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


def validate_sanctions_decision(payload: dict) -> dict:
    """Validate a sanctions decision against CONTRACT_SANCTIONS v1.0.

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
    if action_type != "set_sanctions":
        errors.append(
            f"INVALID_ACTION_TYPE: got {action_type!r}, must be 'set_sanctions'"
        )

    # country_code (the actor — may be sanctioner or evasion supporter)
    actor_raw = payload.get("country_code")
    actor: str | None = None
    if isinstance(actor_raw, str) and actor_raw.strip():
        actor = actor_raw.strip().lower()

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
    # Runs whenever a `changes` object is present — accumulates all errors
    # in one pass.
    # -----------------------------------------------------------------------

    normalized_sanctions: dict[str, int] | None = None

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

            sanctions = changes.get("sanctions")
            if not isinstance(sanctions, dict):
                errors.append(
                    f"MISSING_CHANGES: 'changes.sanctions' must be dict, "
                    f"got {type(sanctions).__name__}"
                )
            else:
                if len(sanctions) == 0:
                    errors.append(
                        "EMPTY_CHANGES: decision='change' with empty sanctions dict — "
                        "use decision='no_change' instead"
                    )

                normalized_sanctions = {}
                for target_raw, level_raw in sanctions.items():
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

                    if actor is not None and target == actor:
                        errors.append(
                            f"SELF_SANCTION: actor {actor!r} cannot sanction itself"
                        )

                    # level — signed [-3, +3]
                    if not _is_real_int(level_raw):
                        errors.append(
                            f"INVALID_LEVEL: sanctions[{target!r}] must be int in "
                            f"[{LEVEL_MIN}, {LEVEL_MAX}], got {level_raw!r} "
                            f"({type(level_raw).__name__})"
                        )
                        continue
                    if not (LEVEL_MIN <= level_raw <= LEVEL_MAX):
                        errors.append(
                            f"INVALID_LEVEL: sanctions[{target!r}] = {level_raw}, "
                            f"must be in [{LEVEL_MIN}, {LEVEL_MAX}]"
                        )
                        continue

                    # only normalize entries that pass every check
                    if (
                        target in CANONICAL_COUNTRIES
                        and (actor is None or target != actor)
                    ):
                        normalized_sanctions[target] = int(level_raw)

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
        "action_type": "set_sanctions",
        "country_code": actor,
        "round_num": payload.get("round_num"),
        "decision": decision,
        "rationale": rationale_trimmed,
    }
    if decision == "change":
        normalized["changes"] = {"sanctions": normalized_sanctions or {}}

    return {
        "valid": True,
        "errors": [],
        "warnings": warnings,
        "normalized": normalized,
    }
