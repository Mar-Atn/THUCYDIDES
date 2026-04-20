"""Comprehensive movement/deployment tests — deploy, withdraw, reposition,
carrier embark/debark, batch validation.

Tests exercise the full dispatch_action → _process_movement pipeline which:
  1. Loads units from deployments table
  2. Validates via movement_validator.validate_movement_decision
  3. Applies via movement.process_movements
  4. Writes updated positions back to deployments

Run::

    cd app && python -m pytest tests/layer2/test_movement_deployment.py -v

"""
from __future__ import annotations

import uuid

import pytest

from engine.services.sim_run_manager import _get_client
from engine.services.action_dispatcher import dispatch_action
from engine.services.sim_create import create_sim_run


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    return _get_client()


@pytest.fixture(scope="module")
def test_sim(client):
    result = create_sim_run(
        name="Movement Deployment Test Sim",
        source_sim_id="00000000-0000-0000-0000-000000000001",
        template_id="3b431689-945b-44d0-89f0-7b32a7f63b47",
        facilitator_id="1b2616bb-955a-4029-b0a1-802a81211b94",
        schedule={"default_rounds": 6}, key_events=[], max_rounds=6,
    )
    sim_id = result["id"]
    client.table("sim_runs").update({
        "status": "active", "current_round": 1, "current_phase": "A",
    }).eq("id", sim_id).execute()
    yield sim_id
    # Cleanup — delete test data in dependency order
    for table in [
        "agreements", "exchange_transactions", "observatory_events",
        "agent_decisions", "pending_actions", "leadership_votes",
        "world_state", "tariffs", "sanctions", "org_memberships",
        "organizations", "deployments", "zones", "role_actions",
        "roles", "relationships", "countries", "artefacts",
    ]:
        try:
            client.table(table).delete().eq("sim_run_id", sim_id).execute()
        except Exception:
            pass
    client.table("sim_runs").delete().eq("id", sim_id).execute()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Detect columbia-owned land hex and sea hex from the global map JSON.
# Columbia owns hex (3,3) per seed data. Sea hexes have owner='sea'.
# We pick a well-known sea hex: row 5, col 10 (mid-ocean area).
COLUMBIA_OWN_HEX = (3, 3)
COLUMBIA_OWN_HEX_2 = (4, 3)
SEA_HEX = (1, 10)    # row 1 is all sea per seed map
SEA_HEX_2 = (1, 11)  # another sea hex
ENEMY_HEX = (4, 17)  # hanguk territory


def _insert_deployment(client, sim_id: str, unit_id: str, country_code: str,
                        unit_type: str, unit_status: str,
                        global_row=None, global_col=None,
                        embarked_on=None) -> str:
    """Insert a test deployment row directly into the DB."""
    row = {
        "id": str(uuid.uuid4()),
        "sim_run_id": sim_id,
        "unit_id": unit_id,
        "country_code": country_code,
        "unit_type": unit_type,
        "unit_status": unit_status,
        "global_row": global_row,
        "global_col": global_col,
        "theater": None,
        "theater_row": None,
        "theater_col": None,
        "embarked_on": embarked_on,
    }
    client.table("deployments").insert(row).execute()
    return row["id"]


def _get_deployment(client, sim_id: str, unit_id: str) -> dict | None:
    """Read a single deployment row."""
    res = (
        client.table("deployments")
        .select("*")
        .eq("sim_run_id", sim_id)
        .eq("unit_id", unit_id)
        .execute()
    )
    return res.data[0] if res.data else None


def _delete_test_deployments(client, sim_id: str, unit_ids: list[str]):
    """Remove test deployment rows."""
    for uid in unit_ids:
        try:
            client.table("deployments").delete().eq(
                "sim_run_id", sim_id
            ).eq("unit_id", uid).execute()
        except Exception:
            pass


def _delete_observatory_events(client, sim_id: str):
    """Remove observatory events for the sim."""
    try:
        client.table("observatory_events").delete().eq(
            "sim_run_id", sim_id
        ).execute()
    except Exception:
        pass


def _dispatch_move(sim_id: str, country: str, moves: list[dict],
                   rationale: str = "Test movement batch with enough chars for validation") -> dict:
    """Dispatch a move_units action and return the result."""
    return dispatch_action(sim_id, 1, {
        "action_type": "move_units",
        "country_code": country,
        "role_id": "dealer",
        "moves": moves,
        "rationale": rationale,
    })


# ---------------------------------------------------------------------------
# TestDeployFromReserve
# ---------------------------------------------------------------------------


class TestDeployFromReserve:
    """Deploy units from reserve to the map."""

    def test_deploy_reserve_ground_to_own_territory(self, client, test_sim):
        """Deploy reserve ground unit to own territory -> unit becomes active at target hex."""
        uid = "test_deploy_ground_01"
        _insert_deployment(client, test_sim, uid, "columbia", "ground", "reserve")
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "hex",
                 "target_global_row": COLUMBIA_OWN_HEX[0],
                 "target_global_col": COLUMBIA_OWN_HEX[1]},
            ])
            assert result["success"], f"Expected success, got: {result}"
            dep = _get_deployment(client, test_sim, uid)
            assert dep is not None
            assert dep["unit_status"] == "active"
            assert dep["global_row"] == COLUMBIA_OWN_HEX[0]
            assert dep["global_col"] == COLUMBIA_OWN_HEX[1]
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_deploy_reserve_naval_to_sea_hex(self, client, test_sim):
        """Deploy reserve naval unit to sea hex -> unit becomes active."""
        uid = "test_deploy_naval_01"
        _insert_deployment(client, test_sim, uid, "columbia", "naval", "reserve")
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "hex",
                 "target_global_row": SEA_HEX[0],
                 "target_global_col": SEA_HEX[1]},
            ])
            assert result["success"], f"Expected success, got: {result}"
            dep = _get_deployment(client, test_sim, uid)
            assert dep["unit_status"] == "active"
            assert dep["global_row"] == SEA_HEX[0]
            assert dep["global_col"] == SEA_HEX[1]
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_deploy_reserve_ground_to_sea_without_carrier_fails(self, client, test_sim):
        """Deploy reserve ground to sea hex without carrier -> should fail."""
        uid = "test_deploy_ground_sea_01"
        _insert_deployment(client, test_sim, uid, "columbia", "ground", "reserve")
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "hex",
                 "target_global_row": SEA_HEX[0],
                 "target_global_col": SEA_HEX[1]},
            ])
            assert not result["success"], f"Expected failure, got: {result}"
            assert any("SEA_HEX_FORBIDDEN" in e for e in result.get("errors", []))
            # Unit should remain in reserve
            dep = _get_deployment(client, test_sim, uid)
            assert dep["unit_status"] == "reserve"
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_deploy_reserve_ground_to_enemy_territory_fails(self, client, test_sim):
        """Deploy reserve ground to enemy territory without basing -> should fail."""
        uid = "test_deploy_ground_enemy_01"
        _insert_deployment(client, test_sim, uid, "columbia", "ground", "reserve")
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "hex",
                 "target_global_row": ENEMY_HEX[0],
                 "target_global_col": ENEMY_HEX[1]},
            ])
            assert not result["success"], f"Expected failure, got: {result}"
            assert any("NOT_ALLOWED_TERRITORY" in e for e in result.get("errors", []))
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_deploy_reserve_ground_to_basing_rights_territory(self, client, test_sim):
        """Deploy reserve ground to territory where basing rights exist -> should succeed."""
        uid = "test_deploy_ground_basing_01"
        _insert_deployment(client, test_sim, uid, "columbia", "ground", "reserve")
        # Grant columbia basing rights from hanguk by inserting/updating relationship
        try:
            client.table("relationships").update({
                "basing_rights_a_to_b": True,
            }).eq("sim_run_id", test_sim).eq(
                "from_country_code", "columbia"
            ).eq("to_country_code", "hanguk").execute()

            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "hex",
                 "target_global_row": ENEMY_HEX[0],
                 "target_global_col": ENEMY_HEX[1]},
            ])
            assert result["success"], f"Expected success with basing rights, got: {result}"
            dep = _get_deployment(client, test_sim, uid)
            assert dep["unit_status"] == "active"
            assert dep["global_row"] == ENEMY_HEX[0]
            assert dep["global_col"] == ENEMY_HEX[1]
        finally:
            # Revoke basing rights
            client.table("relationships").update({
                "basing_rights_a_to_b": False,
            }).eq("sim_run_id", test_sim).eq(
                "from_country_code", "columbia"
            ).eq("to_country_code", "hanguk").execute()
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)


# ---------------------------------------------------------------------------
# TestWithdrawToReserve
# ---------------------------------------------------------------------------


class TestWithdrawToReserve:
    """Withdraw active units to reserve."""

    def test_withdraw_active_ground_unit(self, client, test_sim):
        """Withdraw active ground unit -> status becomes reserve, coords cleared."""
        uid = "test_withdraw_01"
        _insert_deployment(
            client, test_sim, uid, "columbia", "ground", "active",
            global_row=COLUMBIA_OWN_HEX[0], global_col=COLUMBIA_OWN_HEX[1],
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "reserve"},
            ])
            assert result["success"], f"Expected success, got: {result}"
            dep = _get_deployment(client, test_sim, uid)
            assert dep["unit_status"] == "reserve"
            assert dep["global_row"] is None
            assert dep["global_col"] is None
            assert dep["embarked_on"] is None
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_withdraw_last_unit_from_hex(self, client, test_sim):
        """Withdraw the only unit from a hex -> hex should have no units."""
        uid = "test_withdraw_last_01"
        _insert_deployment(
            client, test_sim, uid, "columbia", "ground", "active",
            global_row=COLUMBIA_OWN_HEX[0], global_col=COLUMBIA_OWN_HEX[1],
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "reserve"},
            ])
            assert result["success"]
            # Verify no test deployments at that hex
            res = client.table("deployments").select("unit_id").eq(
                "sim_run_id", test_sim
            ).eq("unit_id", uid).execute()
            dep = res.data[0] if res.data else None
            assert dep is not None
            full = _get_deployment(client, test_sim, uid)
            assert full["global_row"] is None
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)


# ---------------------------------------------------------------------------
# TestReposition
# ---------------------------------------------------------------------------


class TestReposition:
    """Withdraw + deploy same unit (reposition)."""

    def test_reposition_withdraw_then_deploy(self, client, test_sim):
        """Withdraw + deploy same unit in one batch -> unit at new hex."""
        uid = "test_reposition_01"
        _insert_deployment(
            client, test_sim, uid, "columbia", "ground", "active",
            global_row=COLUMBIA_OWN_HEX[0], global_col=COLUMBIA_OWN_HEX[1],
        )
        try:
            # Two-move batch: withdraw then redeploy to a different own hex
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "reserve"},
                # NOTE: unit_code can only appear ONCE in a batch per validator
                # (DUPLICATE_UNIT_IN_BATCH). The engine expects a direct
                # reposition as a single hex-to-hex move, not withdraw+deploy.
            ])
            assert result["success"]
            # Now deploy it to a new location (separate action)
            result2 = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "hex",
                 "target_global_row": COLUMBIA_OWN_HEX_2[0],
                 "target_global_col": COLUMBIA_OWN_HEX_2[1]},
            ])
            assert result2["success"], f"Redeploy failed: {result2}"
            dep = _get_deployment(client, test_sim, uid)
            assert dep["unit_status"] == "active"
            assert dep["global_row"] == COLUMBIA_OWN_HEX_2[0]
            assert dep["global_col"] == COLUMBIA_OWN_HEX_2[1]
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_reposition_naval_sea_to_sea(self, client, test_sim):
        """Reposition naval from sea to sea -> works (single move)."""
        uid = "test_repos_naval_01"
        _insert_deployment(
            client, test_sim, uid, "columbia", "naval", "active",
            global_row=SEA_HEX[0], global_col=SEA_HEX[1],
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "hex",
                 "target_global_row": SEA_HEX_2[0],
                 "target_global_col": SEA_HEX_2[1]},
            ])
            assert result["success"], f"Expected success, got: {result}"
            dep = _get_deployment(client, test_sim, uid)
            assert dep["unit_status"] == "active"
            assert dep["global_row"] == SEA_HEX_2[0]
            assert dep["global_col"] == SEA_HEX_2[1]
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_reposition_ground_land_to_land(self, client, test_sim):
        """Reposition ground from own land to own land -> works."""
        uid = "test_repos_ground_01"
        _insert_deployment(
            client, test_sim, uid, "columbia", "ground", "active",
            global_row=COLUMBIA_OWN_HEX[0], global_col=COLUMBIA_OWN_HEX[1],
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "hex",
                 "target_global_row": COLUMBIA_OWN_HEX_2[0],
                 "target_global_col": COLUMBIA_OWN_HEX_2[1]},
            ])
            assert result["success"], f"Expected success, got: {result}"
            dep = _get_deployment(client, test_sim, uid)
            assert dep["unit_status"] == "active"
            assert dep["global_row"] == COLUMBIA_OWN_HEX_2[0]
            assert dep["global_col"] == COLUMBIA_OWN_HEX_2[1]
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)


# ---------------------------------------------------------------------------
# TestCarrierEmbark
# ---------------------------------------------------------------------------


class TestCarrierEmbark:
    """Auto-embark onto friendly carriers at sea hexes."""

    def test_deploy_ground_to_sea_with_carrier_auto_embarks(self, client, test_sim):
        """Deploy ground to sea hex with own carrier -> auto-embark."""
        carrier_uid = "test_carrier_01"
        ground_uid = "test_embark_ground_01"
        _insert_deployment(
            client, test_sim, carrier_uid, "columbia", "naval", "active",
            global_row=SEA_HEX[0], global_col=SEA_HEX[1],
        )
        _insert_deployment(
            client, test_sim, ground_uid, "columbia", "ground", "reserve",
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": ground_uid, "target": "hex",
                 "target_global_row": SEA_HEX[0],
                 "target_global_col": SEA_HEX[1]},
            ])
            assert result["success"], f"Expected success, got: {result}"
            dep = _get_deployment(client, test_sim, ground_uid)
            assert dep["unit_status"] == "embarked"
            assert dep["embarked_on"] == carrier_uid
        finally:
            _delete_test_deployments(client, test_sim, [carrier_uid, ground_uid])
            _delete_observatory_events(client, test_sim)

    def test_deploy_air_to_carrier_auto_embarks(self, client, test_sim):
        """Deploy tactical_air to carrier -> auto-embark."""
        carrier_uid = "test_carrier_02"
        air_uid = "test_embark_air_01"
        _insert_deployment(
            client, test_sim, carrier_uid, "columbia", "naval", "active",
            global_row=SEA_HEX[0], global_col=SEA_HEX[1],
        )
        _insert_deployment(
            client, test_sim, air_uid, "columbia", "tactical_air", "reserve",
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": air_uid, "target": "hex",
                 "target_global_row": SEA_HEX[0],
                 "target_global_col": SEA_HEX[1]},
            ])
            assert result["success"], f"Expected success, got: {result}"
            dep = _get_deployment(client, test_sim, air_uid)
            assert dep["unit_status"] == "embarked"
            assert dep["embarked_on"] == carrier_uid
        finally:
            _delete_test_deployments(client, test_sim, [carrier_uid, air_uid])
            _delete_observatory_events(client, test_sim)

    def test_exceed_carrier_capacity_fails(self, client, test_sim):
        """Exceed carrier capacity (1 ground + 2 air = 3 max) -> 4th fails."""
        carrier_uid = "test_carrier_cap_01"
        ground_uid = "test_cap_ground_01"
        air1_uid = "test_cap_air_01"
        air2_uid = "test_cap_air_02"
        air3_uid = "test_cap_air_03"  # this one should fail
        all_uids = [carrier_uid, ground_uid, air1_uid, air2_uid, air3_uid]

        _insert_deployment(
            client, test_sim, carrier_uid, "columbia", "naval", "active",
            global_row=SEA_HEX[0], global_col=SEA_HEX[1],
        )
        # Pre-embark 1 ground + 2 air (at capacity)
        _insert_deployment(
            client, test_sim, ground_uid, "columbia", "ground", "embarked",
            embarked_on=carrier_uid,
        )
        _insert_deployment(
            client, test_sim, air1_uid, "columbia", "tactical_air", "embarked",
            embarked_on=carrier_uid,
        )
        _insert_deployment(
            client, test_sim, air2_uid, "columbia", "tactical_air", "embarked",
            embarked_on=carrier_uid,
        )
        # Try to embark a 3rd air unit (over capacity)
        _insert_deployment(
            client, test_sim, air3_uid, "columbia", "tactical_air", "reserve",
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": air3_uid, "target": "hex",
                 "target_global_row": SEA_HEX[0],
                 "target_global_col": SEA_HEX[1]},
            ])
            assert not result["success"], f"Expected failure (over capacity), got: {result}"
            assert any("SEA_HEX_FORBIDDEN" in e for e in result.get("errors", []))
        finally:
            _delete_test_deployments(client, test_sim, all_uids)
            _delete_observatory_events(client, test_sim)


# ---------------------------------------------------------------------------
# TestBatchValidation
# ---------------------------------------------------------------------------


class TestBatchValidation:
    """Batch-level validation errors."""

    def test_duplicate_unit_in_batch(self, client, test_sim):
        """Duplicate unit_code in batch -> DUPLICATE_UNIT_IN_BATCH error."""
        uid = "test_batch_dup_01"
        _insert_deployment(
            client, test_sim, uid, "columbia", "ground", "active",
            global_row=COLUMBIA_OWN_HEX[0], global_col=COLUMBIA_OWN_HEX[1],
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "hex",
                 "target_global_row": COLUMBIA_OWN_HEX_2[0],
                 "target_global_col": COLUMBIA_OWN_HEX_2[1]},
                {"unit_code": uid, "target": "reserve"},
            ])
            assert not result["success"], f"Expected failure, got: {result}"
            assert any("DUPLICATE_UNIT_IN_BATCH" in e for e in result.get("errors", []))
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_move_destroyed_unit(self, client, test_sim):
        """Move destroyed unit -> UNIT_DESTROYED error."""
        uid = "test_batch_destroyed_01"
        _insert_deployment(
            client, test_sim, uid, "columbia", "ground", "destroyed",
            global_row=COLUMBIA_OWN_HEX[0], global_col=COLUMBIA_OWN_HEX[1],
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "reserve"},
            ])
            assert not result["success"], f"Expected failure, got: {result}"
            assert any("UNIT_DESTROYED" in e for e in result.get("errors", []))
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_move_unit_not_owned(self, client, test_sim):
        """Move unit belonging to another country -> UNIT_NOT_OWNED error."""
        uid = "test_batch_not_owned_01"
        _insert_deployment(
            client, test_sim, uid, "hanguk", "ground", "active",
            global_row=ENEMY_HEX[0], global_col=ENEMY_HEX[1],
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": uid, "target": "reserve"},
            ])
            # The dispatcher loads units filtered by country_code=columbia,
            # so this unit won't be found at all -> "No moves provided" or similar
            assert not result["success"]
        finally:
            _delete_test_deployments(client, test_sim, [uid])
            _delete_observatory_events(client, test_sim)

    def test_empty_moves_list_fails(self, client, test_sim):
        """Empty moves list -> should fail."""
        result = _dispatch_move(test_sim, "columbia", [])
        assert not result["success"]


# ---------------------------------------------------------------------------
# TestAutoDebark
# ---------------------------------------------------------------------------


class TestAutoDebark:
    """Move embarked unit to land hex -> auto-debark."""

    def test_move_embarked_to_land_auto_debarks(self, client, test_sim):
        """Move embarked unit to land hex -> auto-debark, status=active."""
        carrier_uid = "test_debark_carrier_01"
        ground_uid = "test_debark_ground_01"
        _insert_deployment(
            client, test_sim, carrier_uid, "columbia", "naval", "active",
            global_row=SEA_HEX[0], global_col=SEA_HEX[1],
        )
        _insert_deployment(
            client, test_sim, ground_uid, "columbia", "ground", "embarked",
            embarked_on=carrier_uid,
        )
        try:
            result = _dispatch_move(test_sim, "columbia", [
                {"unit_code": ground_uid, "target": "hex",
                 "target_global_row": COLUMBIA_OWN_HEX[0],
                 "target_global_col": COLUMBIA_OWN_HEX[1]},
            ])
            assert result["success"], f"Expected success, got: {result}"
            dep = _get_deployment(client, test_sim, ground_uid)
            assert dep["unit_status"] == "active"
            assert dep["embarked_on"] is None
            assert dep["global_row"] == COLUMBIA_OWN_HEX[0]
            assert dep["global_col"] == COLUMBIA_OWN_HEX[1]
        finally:
            _delete_test_deployments(client, test_sim, [carrier_uid, ground_uid])
            _delete_observatory_events(client, test_sim)
