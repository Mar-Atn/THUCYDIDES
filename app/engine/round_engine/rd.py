# DEPRECATED (2026-04-06) — being replaced by engines/military.py (unit-level v2) + engines/round_tick.py
# See 3 DETAILED DESIGN/REUNIFICATION_AUDIT_2026-04-06.md. Do not add new logic here.
"""R&D progress increments — Phase 1 MVP.

Nuclear and AI tracks. ``amount`` is in coins; divide by 10 to get
progress increment (0..1 scale). Reaching 1.0 bumps the level and resets
progress.
"""

from __future__ import annotations


def apply_rd_investment(
    country_state: dict,
    domain: str,
    amount: float,
) -> tuple[dict, str]:
    """Apply an R&D investment to a country_state dict.

    Returns ``(new_state, narrative)``.
    """
    if domain not in ("nuclear", "ai"):
        return country_state, f"Unknown R&D domain '{domain}'"

    try:
        amt = float(amount)
    except (TypeError, ValueError):
        return country_state, f"Invalid R&D amount: {amount}"

    if amt <= 0:
        return country_state, f"R&D amount must be positive, got {amt}"

    progress_key = f"{domain}_rd_progress"
    level_key = f"{domain}_level"

    current_progress = float(country_state.get(progress_key) or 0)
    current_level = int(country_state.get(level_key) or 0)

    increment = amt / 10.0
    new_progress = current_progress + increment
    leveled_up = False
    while new_progress >= 1.0:
        current_level += 1
        new_progress -= 1.0
        leveled_up = True

    country_state[progress_key] = round(new_progress, 4)
    country_state[level_key] = current_level

    narrative = (
        f"R&D {domain}: +{increment:.2f} -> progress {new_progress:.2f}, "
        f"level {current_level}" + (" (LEVEL UP)" if leveled_up else "")
    )
    return country_state, narrative
