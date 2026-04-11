"""Layer 1 — movement engine pin tests per CONTRACT_MOVEMENT v1.0 §6.

Validates ``engine.engines.movement.process_movements``: the pure
state-mutation pass that the validated batch flows through. Fixture style
mirrors test_movement_validator.py.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer1/test_movement_engine.py -v
"""
from __future__ import annotations

import pytest

from engine.engines.movement import (
    CARRIER_CAPACITY_AIR,
    CARRIER_CAPACITY_GROUND,
    process_movements,
)

# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _unit(
    code: str,
    country: str,
    unit_type: str,
    status: str = "active",
    row: int | None = 5,
    col: int | None = 5,
    theater: str | None = "asu",
    embarked_on: str | None = None,
) -> dict:
    return {
        "unit_code": code,
        "country_code": country,
        "unit_type": unit_type,
        "status": status,
        "global_row": row,
        "global_col": col,
        "theater": theater,
        "theater_row": 3 if row is not None else None,
        "theater_col": 3 if col is not None else None,
        "embarked_on": embarked_on,
    }


def _zone(zone_id: str, row: int, col: int, owner: str = "columbia") -> dict:
    return {
        "id": zone_id, "global_row": row, "global_col": col,
        "owner": owner, "controlled_by": owner, "type": "land",
    }


@pytest.fixture
def units():
    return {
        "col_g_001": _unit("col_g_001", "columbia", "ground", row=5, col=5),
        "col_g_002": _unit("col_g_002", "columbia", "ground", row=5, col=5),
        "col_g_099": _unit("col_g_099", "columbia", "ground",
                            status="reserve", row=None, col=None, theater=None),
        "col_ta_003": _unit("col_ta_003", "columbia", "tactical_air", row=5, col=5),
        "col_n_010": _unit("col_n_010", "columbia", "naval", row=6, col=6),
        "col_ta_emb": _unit(
            "col_ta_emb", "columbia", "tactical_air",
            status="embarked", row=None, col=None,
            theater=None, embarked_on="col_n_010",
        ),
    }


@pytest.fixture
def zones():
    return {
        (5, 5): _zone("z55", 5, 5),
        (5, 6): _zone("z56", 5, 6),
        (6, 6): _zone("zsea", 6, 6, owner="sea"),
        (3, 12): _zone("z312", 3, 12, owner="sarmatia"),  # eastern_ereb anchor
    }


# ===========================================================================
# 1. Reposition
# ===========================================================================


class TestReposition:
    def test_active_unit_moves_to_new_hex(self, units, zones):
        moves = [{"unit_code": "col_g_001", "target": "hex",
                  "target_global_row": 5, "target_global_col": 6}]
        results = process_movements(moves, "columbia", units, zones)
        u = units["col_g_001"]
        assert u["global_row"] == 5
        assert u["global_col"] == 6
        assert u["status"] == "active"
        assert results[0]["action"] == "reposition"


# ===========================================================================
# 2. Deploy from reserve
# ===========================================================================


class TestDeployFromReserve:
    def test_reserve_unit_activates_and_takes_position(self, units, zones):
        moves = [{"unit_code": "col_g_099", "target": "hex",
                  "target_global_row": 5, "target_global_col": 6}]
        results = process_movements(moves, "columbia", units, zones)
        u = units["col_g_099"]
        assert u["status"] == "active"
        assert (u["global_row"], u["global_col"]) == (5, 6)
        assert results[0]["action"] == "deploy"


# ===========================================================================
# 3. Withdraw to reserve
# ===========================================================================


class TestWithdrawToReserve:
    def test_active_unit_withdraws(self, units, zones):
        moves = [{"unit_code": "col_g_001", "target": "reserve"}]
        results = process_movements(moves, "columbia", units, zones)
        u = units["col_g_001"]
        assert u["status"] == "reserve"
        assert u["global_row"] is None
        assert u["global_col"] is None
        assert u["theater"] is None
        assert u["embarked_on"] is None
        assert results[0]["action"] == "withdraw"


# ===========================================================================
# 4. Auto-embark
# ===========================================================================


class TestAutoEmbark:
    def test_ground_onto_friendly_carrier_embarks(self, units, zones):
        # col_n_010 is at (6, 6). Ground unit moves to (6, 6) → embark.
        moves = [{"unit_code": "col_g_001", "target": "hex",
                  "target_global_row": 6, "target_global_col": 6}]
        results = process_movements(moves, "columbia", units, zones)
        u = units["col_g_001"]
        assert u["status"] == "embarked"
        assert u["embarked_on"] == "col_n_010"
        assert u["global_row"] is None
        assert u["global_col"] is None
        assert results[0]["action"] == "embark"
        assert results[0]["carrier"] == "col_n_010"

    def test_tactical_air_onto_carrier_embarks(self, units, zones):
        moves = [{"unit_code": "col_ta_003", "target": "hex",
                  "target_global_row": 6, "target_global_col": 6}]
        process_movements(moves, "columbia", units, zones)
        u = units["col_ta_003"]
        assert u["status"] == "embarked"
        assert u["embarked_on"] == "col_n_010"

    def test_carrier_capacity_constants(self):
        assert CARRIER_CAPACITY_GROUND == 1
        assert CARRIER_CAPACITY_AIR == 2


# ===========================================================================
# 5. Debark + move (embarked unit gets repositioned)
# ===========================================================================


class TestDebarkAndMove:
    def test_embarked_unit_moves_to_land_hex(self, units, zones):
        # col_ta_emb is embarked on col_n_010. Order: move to (5, 6).
        # Should debark, become active, take position (5, 6).
        moves = [{"unit_code": "col_ta_emb", "target": "hex",
                  "target_global_row": 5, "target_global_col": 6}]
        results = process_movements(moves, "columbia", units, zones)
        u = units["col_ta_emb"]
        assert u["status"] == "active"
        assert u["embarked_on"] is None
        assert (u["global_row"], u["global_col"]) == (5, 6)
        assert results[0]["action"] == "debark"


# ===========================================================================
# 6. Atomic batch — multiple moves applied in order
# ===========================================================================


class TestAtomicBatch:
    def test_multiple_moves_applied_in_order(self, units, zones):
        moves = [
            {"unit_code": "col_g_001", "target": "hex",
             "target_global_row": 5, "target_global_col": 6},
            {"unit_code": "col_g_002", "target": "reserve"},
            {"unit_code": "col_g_099", "target": "hex",
             "target_global_row": 5, "target_global_col": 6},
        ]
        results = process_movements(moves, "columbia", units, zones)
        assert len(results) == 3
        assert units["col_g_001"]["global_row"] == 5
        assert units["col_g_001"]["global_col"] == 6
        assert units["col_g_002"]["status"] == "reserve"
        assert units["col_g_099"]["status"] == "active"
        assert (units["col_g_099"]["global_row"], units["col_g_099"]["global_col"]) == (5, 6)


# ===========================================================================
# 7. Theater auto-derivation
# ===========================================================================


class TestTheaterAutoDerivation:
    def test_global_anchor_hex_sets_theater(self, units, zones):
        # (3, 12) is an eastern_ereb anchor per map_config
        moves = [{"unit_code": "col_g_099", "target": "hex",
                  "target_global_row": 3, "target_global_col": 12}]
        process_movements(moves, "columbia", units, zones)
        u = units["col_g_099"]
        assert u["theater"] == "eastern_ereb"

    def test_non_anchor_hex_sets_theater_none(self, units, zones):
        moves = [{"unit_code": "col_g_001", "target": "hex",
                  "target_global_row": 5, "target_global_col": 6}]
        process_movements(moves, "columbia", units, zones)
        assert units["col_g_001"]["theater"] is None
