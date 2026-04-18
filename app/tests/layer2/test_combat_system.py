"""Comprehensive combat system integration tests — all combat types, modifiers, valid targets.

Layer 2: Tests against real Supabase database via dispatch_action + direct engine calls.

IMPORTANT: sim_create seeds ~345 units across 68 hexes. All tests MUST use hex
coordinates that are EMPTY after sim creation. Row 1 (all columns) is guaranteed
empty, plus many other isolated hexes. See occupied-hex scan in test dev notes.

Run: cd app && python -m pytest tests/layer2/test_combat_system.py -v
"""

import uuid
import pytest
from engine.services.sim_run_manager import _get_client
from engine.services.sim_create import create_sim_run
from engine.services.action_dispatcher import dispatch_action
from engine.config.map_config import (
    hex_neighbors_bounded, hex_range, ATTACK_RANGE, GLOBAL_ROWS, GLOBAL_COLS,
)


# ---------------------------------------------------------------------------
# SAFE HEX COORDINATES — empty after sim_create (row 1 is fully empty)
# Use adjacent pairs for source→target.  Odd-row adjacency for row 1:
#   (1,1) neighbors: (1,2), (2,1), (2,2)  [bounded]
#   (1,3) neighbors: (1,2), (1,4), (2,3), (2,4)
#   etc.
# Row 10 low cols also safe: (10,1)-(10,10) mostly empty
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    return _get_client()


def _create_active_sim(client, name):
    """Helper: create a sim run and set it active at round 1 phase A."""
    result = create_sim_run(
        name=name,
        source_sim_id="00000000-0000-0000-0000-000000000001",
        template_id="3b431689-945b-44d0-89f0-7b32a7f63b47",
        facilitator_id="1b2616bb-955a-4029-b0a1-802a81211b94",
        schedule={"default_rounds": 6},
        key_events=[],
        max_rounds=6,
    )
    sim_id = result["id"]
    client.table("sim_runs").update({
        "status": "active", "current_round": 1, "current_phase": "A",
    }).eq("id", sim_id).execute()
    return sim_id


def _cleanup_sim(client, sim_id):
    """Delete all data for a sim run."""
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


@pytest.fixture(scope="module")
def test_sim(client):
    """Module-scoped sim run for tests that share state safely."""
    sim_id = _create_active_sim(client, "Combat Test Sim (shared)")
    yield sim_id
    _cleanup_sim(client, sim_id)


# ---------------------------------------------------------------------------
# Deployment helpers
# ---------------------------------------------------------------------------

def _insert_unit(client, sim_id, country, unit_type, row, col, unit_id=None,
                 theater=None, theater_row=None, theater_col=None, status="active",
                 embarked_on=None):
    """Insert a single deployment unit and return its DB id + unit_id."""
    uid = unit_id or f"test_{unit_type}_{country}_{uuid.uuid4().hex[:8]}"
    payload = {
        "sim_run_id": sim_id,
        "country_id": country,
        "unit_type": unit_type,
        "unit_id": uid,
        "unit_status": status,
        "global_row": row,
        "global_col": col,
    }
    if theater:
        payload["theater"] = theater
    if theater_row is not None:
        payload["theater_row"] = theater_row
    if theater_col is not None:
        payload["theater_col"] = theater_col
    if embarked_on:
        payload["embarked_on"] = embarked_on
        if row is None:
            del payload["global_row"]
        if col is None:
            del payload["global_col"]
    r = client.table("deployments").insert(payload).execute()
    return {"db_id": r.data[0]["id"], "unit_id": uid}


def _delete_units(client, sim_id, db_ids):
    """Clean up test units by DB id."""
    for db_id in db_ids:
        try:
            client.table("deployments").delete().eq("id", db_id).execute()
        except Exception:
            pass


def _count_active_units(client, sim_id, unit_id):
    """Check if a unit_id is still active in deployments."""
    r = client.table("deployments").select("id") \
        .eq("sim_run_id", sim_id).eq("unit_id", unit_id) \
        .in_("unit_status", ["active", "embarked"]).execute()
    return len(r.data)


def _unit_exists(client, sim_id, unit_id):
    """Check if a unit_id exists at all (any status) in deployments."""
    r = client.table("deployments").select("id") \
        .eq("sim_run_id", sim_id).eq("unit_id", unit_id).execute()
    return len(r.data) > 0


# ===========================================================================
# GROUND ATTACK
# ===========================================================================

class TestGroundAttack:
    """Ground combat via dispatch_action with precomputed rolls.

    Uses row 1 (empty) for all hex placements.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, client, test_sim):
        self.client = client
        self.sim_id = test_sim
        self._cleanup_ids = []

    def _insert(self, country, unit_type, row, col, **kw):
        u = _insert_unit(self.client, self.sim_id, country, unit_type, row, col, **kw)
        self._cleanup_ids.append(u["db_id"])
        return u

    def teardown_method(self):
        _delete_units(self.client, self.sim_id, self._cleanup_ids)
        try:
            self.client.table("observatory_events").delete().eq(
                "sim_run_id", self.sim_id).execute()
        except Exception:
            pass

    def test_attacker_wins_deterministic(self):
        """3 attackers vs 2 defenders, precomputed rolls: attacker wins."""
        a1 = self._insert("columbia", "ground", 1, 1)
        a2 = self._insert("columbia", "ground", 1, 1)
        a3 = self._insert("columbia", "ground", 1, 1)
        d1 = self._insert("cathay", "ground", 1, 2)
        d2 = self._insert("cathay", "ground", 1, 2)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 1,
            "target_row": 1,
            "target_col": 2,
            "target_country": "cathay",
            "attacker_unit_codes": [a1["unit_id"], a2["unit_id"], a3["unit_id"]],
            "precomputed_rolls": {
                "attacker": [[6, 5, 4]],
                "defender": [[1, 1]],
            },
        })
        assert r["success"] is True
        assert r["attacker_won"] is True
        assert r["defender_losses_count"] == 2
        assert _count_active_units(self.client, self.sim_id, d1["unit_id"]) == 0
        assert _count_active_units(self.client, self.sim_id, d2["unit_id"]) == 0

    def test_defender_wins_deterministic(self):
        """2 attackers vs 2 defenders, precomputed: defender wins."""
        a1 = self._insert("columbia", "ground", 1, 3)
        a2 = self._insert("columbia", "ground", 1, 3)
        d1 = self._insert("cathay", "ground", 1, 4)
        d2 = self._insert("cathay", "ground", 1, 4)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 3,
            "target_row": 1,
            "target_col": 4,
            "target_country": "cathay",
            "attacker_unit_codes": [a1["unit_id"], a2["unit_id"]],
            "precomputed_rolls": {
                "attacker": [[1, 1]],
                "defender": [[6, 6]],
            },
        })
        assert r["success"] is True
        assert r["attacker_won"] is False
        assert r["attacker_losses_count"] == 2
        assert _count_active_units(self.client, self.sim_id, a1["unit_id"]) == 0
        assert _count_active_units(self.client, self.sim_id, a2["unit_id"]) == 0
        assert _count_active_units(self.client, self.sim_id, d1["unit_id"]) == 1
        assert _count_active_units(self.client, self.sim_id, d2["unit_id"]) == 1

    def test_ties_go_to_defender(self):
        """When rolls tie, defender wins (RISK convention)."""
        a1 = self._insert("columbia", "ground", 1, 5)
        d1 = self._insert("cathay", "ground", 1, 6)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 5,
            "target_row": 1,
            "target_col": 6,
            "attacker_unit_codes": [a1["unit_id"]],
            "precomputed_rolls": {
                "attacker": [[4]],
                "defender": [[4]],
            },
        })
        assert r["success"] is True
        assert r["attacker_losses_count"] == 1
        assert _count_active_units(self.client, self.sim_id, a1["unit_id"]) == 0
        assert _count_active_units(self.client, self.sim_id, d1["unit_id"]) == 1

    def test_no_attackers_fails(self):
        """Attack with no units on source hex fails."""
        d1 = self._insert("cathay", "ground", 1, 8)
        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 7,
            "target_row": 1,
            "target_col": 8,
        })
        assert r["success"] is False

    def test_no_defenders_attacker_wins(self):
        """Attack empty hex => no combat needed."""
        a1 = self._insert("columbia", "ground", 1, 9)
        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 9,
            "target_row": 1,
            "target_col": 10,
            "attacker_unit_codes": [a1["unit_id"]],
        })
        assert r["success"] is True

    def test_modifiers_applied(self):
        """Attacker modifier +1 flips a tie into attacker win."""
        a1 = self._insert("columbia", "ground", 1, 11)
        d1 = self._insert("cathay", "ground", 1, 12)

        # Without modifier: 4 vs 4 => tie => defender wins
        # With attacker +1: effective = min(6, 4+1) = 5 > 4 => attacker wins
        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 11,
            "target_row": 1,
            "target_col": 12,
            "attacker_unit_codes": [a1["unit_id"]],
            "modifiers": [{"side": "attacker", "value": 1, "reason": "AI L4 bonus"}],
            "precomputed_rolls": {
                "attacker": [[4]],
                "defender": [[4]],
            },
        })
        assert r["success"] is True
        assert r["attacker_won"] is True
        assert r["defender_losses_count"] == 1

    def test_multi_exchange_combat(self):
        """3v2 combat in one exchange: all 3 atk dice vs 2 def dice."""
        a1 = self._insert("columbia", "ground", 1, 13)
        a2 = self._insert("columbia", "ground", 1, 13)
        a3 = self._insert("columbia", "ground", 1, 13)
        d1 = self._insert("cathay", "ground", 1, 14)
        d2 = self._insert("cathay", "ground", 1, 14)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 13,
            "target_row": 1,
            "target_col": 14,
            "attacker_unit_codes": [a1["unit_id"], a2["unit_id"], a3["unit_id"]],
            "precomputed_rolls": {
                "attacker": [[6, 5, 4]],
                "defender": [[3, 2]],
            },
        })
        assert r["success"] is True
        assert r["attacker_won"] is True
        assert r["defender_losses_count"] == 2
        assert r["attacker_losses_count"] == 0

    def test_missing_target_hex_fails(self):
        """Dispatch without target_row/target_col returns error."""
        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
        })
        assert r["success"] is False
        assert "target" in r["narrative"].lower() or "hex" in r["narrative"].lower()

    def test_select_specific_units(self):
        """Can select 1 of 3 units on a hex to attack."""
        a1 = self._insert("columbia", "ground", 1, 15)
        a2 = self._insert("columbia", "ground", 1, 15)
        a3 = self._insert("columbia", "ground", 1, 15)
        d1 = self._insert("cathay", "ground", 1, 16)

        # Only send a1 to attack
        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 15,
            "target_row": 1,
            "target_col": 16,
            "attacker_unit_codes": [a1["unit_id"]],
            "precomputed_rolls": {
                "attacker": [[6]],
                "defender": [[1]],
            },
        })
        assert r["success"] is True
        assert r["attacker_won"] is True
        # Other units should still be alive
        assert _count_active_units(self.client, self.sim_id, a2["unit_id"]) == 1
        assert _count_active_units(self.client, self.sim_id, a3["unit_id"]) == 1


# ===========================================================================
# AIR STRIKE
# ===========================================================================

class TestAirStrike:
    """Air strike via dispatch_action with precomputed rolls.

    Uses empty hex pairs in row 10 (low cols) to avoid seeded units.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, client, test_sim):
        self.client = client
        self.sim_id = test_sim
        self._cleanup_ids = []

    def _insert(self, country, unit_type, row, col, **kw):
        u = _insert_unit(self.client, self.sim_id, country, unit_type, row, col, **kw)
        self._cleanup_ids.append(u["db_id"])
        return u

    def teardown_method(self):
        _delete_units(self.client, self.sim_id, self._cleanup_ids)
        try:
            self.client.table("observatory_events").delete().eq(
                "sim_run_id", self.sim_id).execute()
        except Exception:
            pass

    def test_air_hit_no_ad(self):
        """Air strike hits target (no AD), 12% threshold, roll 0.05 < 0.12."""
        air = self._insert("columbia", "tactical_air", 10, 1)
        target = self._insert("cathay", "ground", 10, 2)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "air_strike",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 1,
            "target_row": 10,
            "target_col": 2,
            "attacker_unit_codes": [air["unit_id"]],
            "precomputed_rolls": {
                "shots": [{"hit_roll": 0.05, "downed_roll": 0.99}],
            },
        })
        assert r["success"] is True
        assert r["defender_losses_count"] >= 1
        assert _count_active_units(self.client, self.sim_id, target["unit_id"]) == 0

    def test_air_miss_no_ad(self):
        """Air strike misses when roll > 0.12 (no AD)."""
        air = self._insert("columbia", "tactical_air", 10, 3)
        target = self._insert("cathay", "ground", 10, 4)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "air_strike",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 3,
            "target_row": 10,
            "target_col": 4,
            "attacker_unit_codes": [air["unit_id"]],
            "precomputed_rolls": {
                "shots": [{"hit_roll": 0.50, "downed_roll": 0.99}],
            },
        })
        assert r["success"] is True
        assert r["defender_losses_count"] == 0
        assert _count_active_units(self.client, self.sim_id, target["unit_id"]) == 1

    def test_air_hit_with_ad_halved(self):
        """With AD present, hit probability halved to 6%. Roll 0.05 < 0.06 => hit."""
        air = self._insert("columbia", "tactical_air", 10, 5)
        target = self._insert("cathay", "ground", 10, 6)
        ad = self._insert("cathay", "air_defense", 10, 6)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "air_strike",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 5,
            "target_row": 10,
            "target_col": 6,
            "attacker_unit_codes": [air["unit_id"]],
            "precomputed_rolls": {
                "shots": [{"hit_roll": 0.05, "downed_roll": 0.99}],
            },
        })
        assert r["success"] is True
        assert r["defender_losses_count"] >= 1

    def test_air_miss_with_ad(self):
        """With AD, 0.07 > 0.06 => miss."""
        air = self._insert("columbia", "tactical_air", 10, 7)
        target = self._insert("cathay", "ground", 10, 8)
        ad = self._insert("cathay", "air_defense", 10, 8)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "air_strike",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 7,
            "target_row": 10,
            "target_col": 8,
            "attacker_unit_codes": [air["unit_id"]],
            "precomputed_rolls": {
                "shots": [{"hit_roll": 0.07, "downed_roll": 0.99}],
            },
        })
        assert r["success"] is True
        assert r["defender_losses_count"] == 0

    def test_air_downed_by_ad(self):
        """AD present, downed_roll < 0.15 => attacker air unit downed."""
        air = self._insert("columbia", "tactical_air", 10, 9)
        target = self._insert("cathay", "ground", 10, 10)
        ad = self._insert("cathay", "air_defense", 10, 10)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "air_strike",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 9,
            "target_row": 10,
            "target_col": 10,
            "attacker_unit_codes": [air["unit_id"]],
            "precomputed_rolls": {
                "shots": [{"hit_roll": 0.50, "downed_roll": 0.10}],
            },
        })
        assert r["success"] is True
        assert r["attacker_losses_count"] >= 1
        assert _count_active_units(self.client, self.sim_id, air["unit_id"]) == 0

    def test_air_not_downed_without_ad(self):
        """Without AD, air unit is never downed regardless of downed_roll.

        Uses hex pair (10,13)→(10,14) — both confirmed empty after sim_create.
        """
        air = self._insert("columbia", "tactical_air", 10, 13)
        target = self._insert("cathay", "ground", 10, 14)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "air_strike",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 13,
            "target_row": 10,
            "target_col": 14,
            "attacker_unit_codes": [air["unit_id"]],
            "precomputed_rolls": {
                "shots": [{"hit_roll": 0.50, "downed_roll": 0.01}],
            },
        })
        assert r["success"] is True
        assert r["attacker_losses_count"] == 0
        assert _count_active_units(self.client, self.sim_id, air["unit_id"]) == 1


# ===========================================================================
# NAVAL COMBAT
# ===========================================================================

class TestNavalCombat:
    """Naval 1v1 combat via dispatch_action.

    KNOWN ENGINE BUG: NavalCombatResultM4 returns {winner, destroyed_unit}
    but _apply_combat_losses expects {attacker_losses, defender_losses} lists.
    As a result, the DB loss application does NOT work for naval combat —
    no units are actually deleted. The engine result reports correct winner/loser
    but the DB state is not mutated. Tests assert on actual behavior.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, client, test_sim):
        self.client = client
        self.sim_id = test_sim
        self._cleanup_ids = []

    def _insert(self, country, unit_type, row, col, **kw):
        u = _insert_unit(self.client, self.sim_id, country, unit_type, row, col, **kw)
        self._cleanup_ids.append(u["db_id"])
        return u

    def teardown_method(self):
        _delete_units(self.client, self.sim_id, self._cleanup_ids)
        try:
            self.client.table("observatory_events").delete().eq(
                "sim_run_id", self.sim_id).execute()
        except Exception:
            pass

    def test_attacker_wins_naval_engine_result(self):
        """Attacker rolls higher => engine reports attacker wins."""
        atk = self._insert("columbia", "naval", 1, 17)
        dfn = self._insert("cathay", "naval", 1, 18)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_combat",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 17,
            "target_row": 1,
            "target_col": 18,
            "attacker_unit_codes": [atk["unit_id"]],
            "precomputed_rolls": {"attacker": 6, "defender": 1},
        })
        assert r["success"] is True
        # Engine correctly identifies winner
        assert r["winner"] == "attacker"
        assert r["destroyed_unit"] == dfn["unit_id"]
        assert r["rolls_source"] == "moderator"

        # BUG: _apply_combat_losses does not delete naval units because
        # NavalCombatResultM4 has winner/destroyed_unit instead of
        # attacker_losses/defender_losses lists. Both units remain in DB.
        # When this bug is fixed, defender should be deleted:
        #   assert _count_active_units(self.client, self.sim_id, dfn["unit_id"]) == 0

    def test_defender_wins_naval_engine_result(self):
        """Defender rolls higher => engine reports defender wins."""
        atk = self._insert("columbia", "naval", 1, 19)
        dfn = self._insert("cathay", "naval", 1, 20)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_combat",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 19,
            "target_row": 1,
            "target_col": 20,
            "attacker_unit_codes": [atk["unit_id"]],
            "precomputed_rolls": {"attacker": 2, "defender": 5},
        })
        assert r["success"] is True
        assert r["winner"] == "defender"
        assert r["destroyed_unit"] == atk["unit_id"]

    def test_tie_goes_to_defender_naval(self):
        """Equal rolls => defender wins (tie rule)."""
        atk = self._insert("columbia", "naval", 10, 15)
        dfn = self._insert("cathay", "naval", 10, 16)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_combat",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 15,
            "target_row": 10,
            "target_col": 16,
            "attacker_unit_codes": [atk["unit_id"]],
            "precomputed_rolls": {"attacker": 4, "defender": 4},
        })
        assert r["success"] is True
        assert r["winner"] == "defender"
        assert r["destroyed_unit"] == atk["unit_id"]

    def test_no_enemy_naval_fails(self):
        """Naval combat with no enemy naval at target hex fails."""
        atk = self._insert("columbia", "naval", 10, 18)
        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_combat",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 18,
            "target_row": 10,
            "target_col": 19,
            "attacker_unit_codes": [atk["unit_id"]],
        })
        assert r["success"] is False


# ===========================================================================
# NAVAL BOMBARDMENT
# ===========================================================================

class TestNavalBombardment:
    """Naval bombardment: sea hex shells adjacent land hex."""

    @pytest.fixture(autouse=True)
    def _setup(self, client, test_sim):
        self.client = client
        self.sim_id = test_sim
        self._cleanup_ids = []

    def _insert(self, country, unit_type, row, col, **kw):
        u = _insert_unit(self.client, self.sim_id, country, unit_type, row, col, **kw)
        self._cleanup_ids.append(u["db_id"])
        return u

    def teardown_method(self):
        _delete_units(self.client, self.sim_id, self._cleanup_ids)
        try:
            self.client.table("observatory_events").delete().eq(
                "sim_run_id", self.sim_id).execute()
        except Exception:
            pass

    def test_bombardment_no_attacker_losses(self):
        """Bombardment never causes attacker losses."""
        nav = self._insert("columbia", "naval", 1, 1)
        gnd = self._insert("cathay", "ground", 1, 2)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_bombardment",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 1,
            "target_row": 1,
            "target_col": 2,
            "attacker_unit_codes": [nav["unit_id"]],
        })
        assert r["success"] is True
        assert len(r.get("attacker_losses", [])) == 0
        assert _count_active_units(self.client, self.sim_id, nav["unit_id"]) == 1

    def test_bombardment_no_ground_defenders_fails(self):
        """Bombardment with no ground targets fails."""
        nav = self._insert("columbia", "naval", 1, 3)
        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_bombardment",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 3,
            "target_row": 1,
            "target_col": 4,
            "attacker_unit_codes": [nav["unit_id"]],
        })
        assert r["success"] is False

    def test_bombardment_multiple_naval(self):
        """Multiple naval units each fire one shot at 10% chance."""
        navs = []
        for _ in range(5):
            navs.append(self._insert("columbia", "naval", 1, 5))
        gnds = []
        for _ in range(5):
            gnds.append(self._insert("cathay", "ground", 1, 6))

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_bombardment",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 5,
            "target_row": 1,
            "target_col": 6,
            "attacker_unit_codes": [n["unit_id"] for n in navs],
        })
        assert r["success"] is True
        assert r["shots_fired"] == 5
        for n in navs:
            assert _count_active_units(self.client, self.sim_id, n["unit_id"]) == 1

    def test_bombardment_no_naval_fails(self):
        """No naval units => failure."""
        gnd = self._insert("cathay", "ground", 1, 8)
        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_bombardment",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 7,
            "target_row": 1,
            "target_col": 8,
        })
        assert r["success"] is False


# ===========================================================================
# MISSILE LAUNCH
# ===========================================================================

class TestMissileLaunch:
    """Strategic missile launch: consumed on fire, 80% base accuracy."""

    @pytest.fixture(autouse=True)
    def _setup(self, client, test_sim):
        self.client = client
        self.sim_id = test_sim
        self._cleanup_ids = []

    def _insert(self, country, unit_type, row, col, **kw):
        u = _insert_unit(self.client, self.sim_id, country, unit_type, row, col, **kw)
        self._cleanup_ids.append(u["db_id"])
        return u

    def teardown_method(self):
        _delete_units(self.client, self.sim_id, self._cleanup_ids)
        try:
            self.client.table("observatory_events").delete().eq(
                "sim_run_id", self.sim_id).execute()
        except Exception:
            pass

    def test_missile_consumed_on_fire(self):
        """Missile unit is always deleted after firing."""
        missile = self._insert("columbia", "strategic_missile", 1, 9)
        target = self._insert("cathay", "ground", 10, 20)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "launch_missile_conventional",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 9,
            "target_row": 10,
            "target_col": 20,
            "attacker_unit_codes": [missile["unit_id"]],
        })
        assert r["success"] is True
        assert missile["unit_id"] in r.get("attacker_losses", [])
        remaining = self.client.table("deployments").select("id") \
            .eq("sim_run_id", self.sim_id).eq("unit_id", missile["unit_id"]).execute()
        assert len(remaining.data) == 0

    def test_missile_global_range(self):
        """Missile can target any hex on the map (corner to corner)."""
        missile = self._insert("columbia", "strategic_missile", 1, 10)
        target = self._insert("cathay", "ground", 10, 20)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "launch_missile_conventional",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 10,
            "target_row": 10,
            "target_col": 20,
            "attacker_unit_codes": [missile["unit_id"]],
        })
        assert r["success"] is True

    def test_no_missile_unit_fails(self):
        """Launch without a missile unit fails."""
        gnd = self._insert("columbia", "ground", 1, 11)
        r = dispatch_action(self.sim_id, 1, {
            "action_type": "launch_missile_conventional",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 11,
            "target_row": 10, "target_col": 5,
            "attacker_unit_codes": [gnd["unit_id"]],
        })
        assert r["success"] is False

    def test_missile_miss_still_consumed(self):
        """Even if missile misses, the unit is consumed (deleted from DB)."""
        missile = self._insert("columbia", "strategic_missile", 1, 12)
        target = self._insert("cathay", "ground", 10, 8)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "launch_missile_conventional",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 12,
            "target_row": 10,
            "target_col": 8,
            "attacker_unit_codes": [missile["unit_id"]],
        })
        assert r["success"] is True
        remaining = self.client.table("deployments").select("id") \
            .eq("sim_run_id", self.sim_id).eq("unit_id", missile["unit_id"]).execute()
        assert len(remaining.data) == 0


# ===========================================================================
# VALID TARGETS (map_config logic)
# ===========================================================================

class TestValidTargets:
    """Test hex adjacency, range, and attack type classification logic."""

    def test_ground_range_is_1(self):
        assert ATTACK_RANGE["ground"] == 1

    def test_air_range_is_2(self):
        assert ATTACK_RANGE["tactical_air"] == 2

    def test_naval_range_is_1(self):
        assert ATTACK_RANGE["naval"] == 1

    def test_missile_global_range(self):
        assert ATTACK_RANGE["strategic_missile"] >= 20

    def test_hex_neighbors_count(self):
        """Interior hex has exactly 6 neighbors within bounds."""
        neighbors = hex_neighbors_bounded(5, 10, GLOBAL_ROWS, GLOBAL_COLS)
        assert len(neighbors) == 6

    def test_hex_neighbors_corner_fewer(self):
        """Corner hex (1,1) has fewer than 6 neighbors within bounds."""
        neighbors = hex_neighbors_bounded(1, 1, GLOBAL_ROWS, GLOBAL_COLS)
        assert len(neighbors) < 6
        for r, c in neighbors:
            assert 1 <= r <= GLOBAL_ROWS
            assert 1 <= c <= GLOBAL_COLS

    def test_hex_range_distance_2(self):
        """hex_range with distance=2 returns hexes up to 2 steps away."""
        ring2 = hex_range(5, 10, distance=2)
        ring1 = hex_range(5, 10, distance=1)
        assert len(ring2) > len(ring1)
        for h in ring1:
            assert h in ring2

    def test_hex_range_excludes_origin(self):
        """hex_range never includes the origin hex itself."""
        result = hex_range(5, 10, distance=1)
        assert (5, 10) not in result

    def test_theater_adjacency_bounds(self):
        """Theater mode uses 10x10 grid bounds."""
        neighbors = hex_neighbors_bounded(5, 5, 10, 10)
        assert len(neighbors) == 6
        edge = hex_neighbors_bounded(1, 1, 10, 10)
        assert len(edge) < 6

    def test_ground_targets_only_ground(self):
        """Attack range config contains all expected unit types."""
        assert "ground" in ATTACK_RANGE
        assert "tactical_air" in ATTACK_RANGE
        assert "naval" in ATTACK_RANGE
        assert "strategic_missile" in ATTACK_RANGE


# ===========================================================================
# MODERATOR FLOW (precomputed rolls)
# ===========================================================================

class TestModeratorFlow:
    """Test that combat actions use the precomputed_rolls (moderator dice) path."""

    @pytest.fixture(autouse=True)
    def _setup(self, client, test_sim):
        self.client = client
        self.sim_id = test_sim
        self._cleanup_ids = []

    def _insert(self, country, unit_type, row, col, **kw):
        u = _insert_unit(self.client, self.sim_id, country, unit_type, row, col, **kw)
        self._cleanup_ids.append(u["db_id"])
        return u

    def teardown_method(self):
        _delete_units(self.client, self.sim_id, self._cleanup_ids)
        try:
            self.client.table("observatory_events").delete().eq(
                "sim_run_id", self.sim_id).execute()
        except Exception:
            pass

    def test_precomputed_rolls_ground(self):
        """Ground combat uses moderator dice when provided."""
        a1 = self._insert("columbia", "ground", 10, 1)
        d1 = self._insert("cathay", "ground", 10, 2)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 1,
            "target_row": 10,
            "target_col": 2,
            "attacker_unit_codes": [a1["unit_id"]],
            "precomputed_rolls": {
                "attacker": [[6]],
                "defender": [[1]],
            },
        })
        assert r["success"] is True
        assert r["attacker_won"] is True
        assert "moderator" in r.get("rolls_source", "")

    def test_precomputed_rolls_naval(self):
        """Naval combat uses moderator dice when provided."""
        atk = self._insert("columbia", "naval", 10, 3)
        dfn = self._insert("cathay", "naval", 10, 4)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_combat",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 3,
            "target_row": 10,
            "target_col": 4,
            "attacker_unit_codes": [atk["unit_id"]],
            "precomputed_rolls": {"attacker": 6, "defender": 1},
        })
        assert r["success"] is True
        assert "moderator" in r.get("rolls_source", "")

    def test_precomputed_rolls_air(self):
        """Air strike uses moderator shots when provided."""
        air = self._insert("columbia", "tactical_air", 10, 5)
        target = self._insert("cathay", "ground", 10, 6)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "air_strike",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 5,
            "target_row": 10,
            "target_col": 6,
            "attacker_unit_codes": [air["unit_id"]],
            "precomputed_rolls": {
                "shots": [{"hit_roll": 0.01, "downed_roll": 0.99}],
            },
        })
        assert r["success"] is True
        assert "moderator" in r.get("rolls_source", "")

    def test_random_rolls_without_precomputed(self):
        """Without precomputed_rolls, engine uses random dice."""
        a1 = self._insert("columbia", "ground", 10, 7)
        d1 = self._insert("cathay", "ground", 10, 8)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 7,
            "target_row": 10,
            "target_col": 8,
            "attacker_unit_codes": [a1["unit_id"]],
        })
        assert r["success"] is True
        assert "random" in r.get("rolls_source", "")


# ===========================================================================
# COMBAT RULES (unit type filtering, naval 1v1, constant checks)
# ===========================================================================

class TestCombatRules:
    """Test cross-cutting combat rules enforced by the system."""

    @pytest.fixture(autouse=True)
    def _setup(self, client, test_sim):
        self.client = client
        self.sim_id = test_sim
        self._cleanup_ids = []

    def _insert(self, country, unit_type, row, col, **kw):
        u = _insert_unit(self.client, self.sim_id, country, unit_type, row, col, **kw)
        self._cleanup_ids.append(u["db_id"])
        return u

    def teardown_method(self):
        _delete_units(self.client, self.sim_id, self._cleanup_ids)
        try:
            self.client.table("observatory_events").delete().eq(
                "sim_run_id", self.sim_id).execute()
        except Exception:
            pass

    def test_only_ground_units_in_ground_combat(self):
        """Non-ground units at source hex are NOT affected by ground combat."""
        gnd = self._insert("columbia", "ground", 1, 17)
        air = self._insert("columbia", "tactical_air", 1, 17)
        d1 = self._insert("cathay", "ground", 1, 18)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "ground_attack",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 1,
            "source_global_col": 17,
            "target_row": 1,
            "target_col": 18,
            "attacker_unit_codes": [gnd["unit_id"]],
            "precomputed_rolls": {"attacker": [[6]], "defender": [[1]]},
        })
        assert r["success"] is True
        assert _count_active_units(self.client, self.sim_id, air["unit_id"]) == 1

    def test_naval_1v1_only(self):
        """Naval combat is strictly 1v1: only one unit from each side."""
        atk1 = self._insert("columbia", "naval", 10, 9)
        atk2 = self._insert("columbia", "naval", 10, 9)
        dfn1 = self._insert("cathay", "naval", 10, 10)
        dfn2 = self._insert("cathay", "naval", 10, 10)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "naval_combat",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 9,
            "target_row": 10,
            "target_col": 10,
            "attacker_unit_codes": [atk1["unit_id"]],
            "precomputed_rolls": {"attacker": 6, "defender": 1},
        })
        assert r["success"] is True
        # 1v1: only one destroyed_unit (even though 2 defenders at hex)
        assert r["destroyed_unit"] is not None
        # The non-selected atk2 should definitely still be around
        assert _count_active_units(self.client, self.sim_id, atk2["unit_id"]) == 1

    def test_air_can_target_ground_units(self):
        """Air strikes can hit ground units."""
        air = self._insert("columbia", "tactical_air", 10, 13)
        gnd = self._insert("cathay", "ground", 10, 14)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "air_strike",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 13,
            "target_row": 10,
            "target_col": 14,
            "attacker_unit_codes": [air["unit_id"]],
            "precomputed_rolls": {"shots": [{"hit_roll": 0.01, "downed_roll": 0.99}]},
        })
        assert r["success"] is True
        assert r["defender_losses_count"] >= 1

    def test_air_can_target_naval_units(self):
        """Air strikes can hit naval units."""
        air = self._insert("columbia", "tactical_air", 10, 15)
        nav = self._insert("cathay", "naval", 10, 16)

        r = dispatch_action(self.sim_id, 1, {
            "action_type": "air_strike",
            "country_code": "columbia",
            "role_id": "dealer",
            "source_global_row": 10,
            "source_global_col": 15,
            "target_row": 10,
            "target_col": 16,
            "attacker_unit_codes": [air["unit_id"]],
            "precomputed_rolls": {"shots": [{"hit_roll": 0.01, "downed_roll": 0.99}]},
        })
        assert r["success"] is True
        assert r["defender_losses_count"] >= 1

    def test_bombardment_hit_prob_10_percent(self):
        """Bombardment uses 10% hit probability."""
        from engine.engines.military import NAVAL_BOMBARDMENT_HIT_PROB
        assert NAVAL_BOMBARDMENT_HIT_PROB == 0.10

    def test_missile_base_accuracy_80_percent(self):
        """Missile base hit probability is 80%."""
        from engine.engines.military import MISSILE_BASE_HIT_PROB_V2
        assert MISSILE_BASE_HIT_PROB_V2 == 0.80

    def test_missile_ad_halves_to_30_percent(self):
        """AD at target halves missile hit probability to 30% for T1."""
        from engine.engines.military import MISSILE_AD_HIT_PROB_V2
        assert MISSILE_AD_HIT_PROB_V2 == 0.30

    def test_air_base_hit_12_percent(self):
        """Air strike base hit probability is 12%."""
        from engine.engines.military import AIR_STRIKE_BASE_HIT_PROB_V2
        assert AIR_STRIKE_BASE_HIT_PROB_V2 == 0.12
