"""Central probability and effect constants for all engine actions.

Single source of truth for calibration. Change values here to tune
game balance — no need to edit individual engine files.

Grouped by action domain. Each engine imports what it needs.
"""

# ---------------------------------------------------------------------------
# Assassination (assassination_engine.py)
# ---------------------------------------------------------------------------
ASSASSINATION_SUCCESS = 0.20           # flat 20% for all targets
ASSASSINATION_SUCCESS_LEVANTIA = 0.50  # Levantia bonus (attacker OR target)
ASSASSINATION_ATTRIBUTION = 0.50       # 50% chance attacker is identified
ASSASSINATION_DETECTION = 1.0          # always detected (public knows it happened)
ASSASSINATION_MARTYR_STABILITY = 1.5   # killed target → target country stability boost

# ---------------------------------------------------------------------------
# Sabotage (sabotage_engine.py)
# ---------------------------------------------------------------------------
SABOTAGE_SUCCESS = 0.50
SABOTAGE_DETECTION = 1.0               # always detected (2026-04-20)
SABOTAGE_ATTRIBUTION = 0.50
SABOTAGE_TREASURY_DAMAGE = -1          # coins lost on infrastructure hit
SABOTAGE_NUCLEAR_RD_DAMAGE = 0.30      # 30% R&D progress destroyed
SABOTAGE_MILITARY_DESTROY = 0.50       # 50% chance to destroy 1 random unit

# ---------------------------------------------------------------------------
# Propaganda (propaganda_engine.py)
# ---------------------------------------------------------------------------
PROPAGANDA_SUCCESS = 0.55
PROPAGANDA_DETECTION = 1.0             # always detected (2026-04-20)
PROPAGANDA_ATTRIBUTION = 0.20
PROPAGANDA_STABILITY_EFFECT = 0.3      # stability change per operation

# ---------------------------------------------------------------------------
# Election Meddling (election_meddling_engine.py)
# ---------------------------------------------------------------------------
MEDDLING_SUCCESS = 0.40
MEDDLING_DETECTION = 0.45
MEDDLING_ATTRIBUTION = 0.50
MEDDLING_SUPPORT_SHIFT_MIN = 2         # percent shift on success
MEDDLING_SUPPORT_SHIFT_MAX = 5

# ---------------------------------------------------------------------------
# Martial Law (martial_law_engine.py)
# ---------------------------------------------------------------------------
MARTIAL_LAW_STABILITY_COST = -1.0
MARTIAL_LAW_WAR_TIREDNESS_COST = 1.0
