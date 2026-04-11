"""Layer 2 — Movement context assembler (CONTRACT_MOVEMENT v1.0 §3).

Step 5 of the M1 movement vertical slice. Verifies that
``engine.services.movement_context.build_movement_context`` produces the
correct decision-specific context payload for a movement decision-maker.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_movement_context.py -v -s
"""
from __future__ import annotations

import logging

import pytest

from engine.services.movement_context import build_movement_context
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
TEST_COUNTRY = "columbia"
TEST_ROUND = 60  # not seeded — falls back to round 0


@pytest.fixture(scope="module")
def client():
    return get_client()


@pytest.fixture(scope="module")
def ctx(client):
    return build_movement_context(TEST_COUNTRY, SCENARIO_CODE, TEST_ROUND)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_context_has_economic_state(ctx):
    eco = ctx["economic_state"]
    assert "gdp" in eco
    assert "treasury" in eco
    assert "stability" in eco
    assert "at_war" in eco
    assert "at_war_with" in eco
    assert isinstance(eco["at_war_with"], list)


def test_context_has_my_units(ctx):
    my_units = ctx["my_units"]
    assert isinstance(my_units, list)
    assert len(my_units) > 0, "Columbia should have units"
    sample = my_units[0]
    for k in ("unit_code", "unit_type", "status"):
        assert k in sample


def test_context_has_own_territory(ctx):
    own = ctx["own_territory"]
    assert isinstance(own, list)
    assert len(own) > 0, "Columbia should own at least one zone"
    sample = own[0]
    assert "zone_id" in sample
    assert "ownership" in sample


def test_context_has_basing_rights(ctx):
    rights = ctx["basing_rights_i_have"]
    assert isinstance(rights, list)
    # Columbia may have zero entries; that's OK. We just confirm shape.
    if rights:
        assert "grantor" in rights[0]


def test_context_has_previously_occupied_hexes(ctx):
    pohs = ctx["previously_occupied_hexes"]
    assert isinstance(pohs, list)
    # Columbia has many active units across multiple hexes
    assert len(pohs) >= 1
    sample = pohs[0]
    assert "global_row" in sample
    assert "global_col" in sample


def test_context_has_world_zone_map(ctx):
    zmap = ctx["world_zone_map"]
    assert isinstance(zmap, list)
    assert len(zmap) == 57, f"expected 57 zones, got {len(zmap)}"
    sample = zmap[0]
    for k in (
        "zone_id", "theater", "owner", "controlled_by",
        "is_chokepoint", "die_hard",
    ):
        assert k in sample


def test_context_has_zone_adjacency(ctx):
    adj = ctx["zone_adjacency"]
    assert isinstance(adj, list)
    assert len(adj) > 0, "expected non-empty zone adjacency edges"
    sample = adj[0]
    assert "zone_a" in sample
    assert "zone_b" in sample


def test_context_has_decision_rules_with_no_change_reminder(ctx):
    rules = ctx["decision_rules"]
    assert isinstance(rules, str)
    assert "no_change" in rules
    assert "legitimate" in rules.lower()
    assert "carrier capacity" in rules.lower() or "Carrier capacity" in rules
    assert ">=30" in rules or "30 char" in rules.lower() or "30" in rules


def test_context_has_recent_combat_events(ctx):
    rce = ctx["recent_combat_events"]
    assert isinstance(rce, list)
    # Combat history may be empty for round 60 — just shape.


def test_context_has_instruction(ctx):
    inst = ctx["instruction"]
    assert isinstance(inst, str)
    assert "CHANGE" in inst.upper() or "change" in inst
    assert "rationale" in inst.lower()
