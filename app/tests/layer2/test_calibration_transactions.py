"""Layer 2: Calibration tests — verify transactions ACTUALLY EXECUTE.

Not "did a row appear" — but "did the ASSETS actually change hands?"

PART A: Pure execution tests (L1 — no DB, no LLM)
PART B: Persistence tests (L2 — real DB, rounds 84-85)
PART C: Validation tests (L1 — no DB)

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_calibration_transactions.py -v -s

"""
from __future__ import annotations

import logging
import pytest

from engine.agents.transactions import (
    TransactionProposal,
    execute_transaction,
    validate_assets,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# HELPERS — mock country + proposal builders
# ===========================================================================

def _country(
    treasury: float = 100.0,
    mil_ground: int = 10,
    mil_naval: int = 5,
    mil_tactical_air: int = 4,
    nuclear_rd_progress: float = 0.0,
    ai_rd_progress: float = 0.0,
) -> dict:
    """Create a minimal country dict for testing."""
    return {
        "treasury": treasury,
        "mil_ground": mil_ground,
        "mil_naval": mil_naval,
        "mil_tactical_air": mil_tactical_air,
        "nuclear_rd_progress": nuclear_rd_progress,
        "ai_rd_progress": ai_rd_progress,
    }


def _proposal(
    txn_type: str = "coin_transfer",
    proposer_cid: str = "alpha",
    counterpart_cid: str = "beta",
    gives: dict | None = None,
    receives: dict | None = None,
    status: str = "accepted",
) -> TransactionProposal:
    """Create a TransactionProposal for testing."""
    return TransactionProposal(
        type=txn_type,
        proposer_country_id=proposer_cid,
        counterpart_country_id=counterpart_cid,
        terms={
            "gives": gives or {},
            "receives": receives or {},
        },
        status=status,
    )


# ===========================================================================
# PART A: Pure execution tests (L1 — no DB, no LLM)
# ===========================================================================

class TestA1CoinTransferExact:
    """A1. Coin transfer — exact amounts, conservation check."""

    def test_coin_transfer_exact(self):
        countries = {
            "columbia": {"treasury": 100.0},
            "cathay": {"treasury": 50.0},
        }
        proposal = _proposal(
            txn_type="coin_transfer",
            proposer_cid="columbia",
            counterpart_cid="cathay",
            gives={"coins": 25},
        )
        result = execute_transaction(proposal, countries)

        print(f"  columbia treasury: {countries['columbia']['treasury']} (expected 75.0)")
        print(f"  cathay treasury:   {countries['cathay']['treasury']} (expected 75.0)")
        print(f"  result: {result}")

        assert result["success"] is True
        assert countries["columbia"]["treasury"] == pytest.approx(75.0), \
            f"columbia treasury should be 75.0, got {countries['columbia']['treasury']}"
        assert countries["cathay"]["treasury"] == pytest.approx(75.0), \
            f"cathay treasury should be 75.0, got {countries['cathay']['treasury']}"

        # CONSERVATION: total unchanged
        total = countries["columbia"]["treasury"] + countries["cathay"]["treasury"]
        print(f"  total coins: {total} (expected 150.0)")
        assert total == pytest.approx(150.0), \
            f"CONSERVATION VIOLATION: total coins {total} != 150.0"


class TestA2CoinTransferInsufficientClamped:
    """A2. Coin transfer — insufficient funds, clamped to available."""

    def test_coin_transfer_clamped(self):
        countries = {
            "alpha": {"treasury": 10.0},
            "beta": {"treasury": 50.0},
        }
        proposal = _proposal(
            txn_type="coin_transfer",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"coins": 50},
        )
        result = execute_transaction(proposal, countries)

        print(f"  alpha treasury: {countries['alpha']['treasury']} (expected 0.0)")
        print(f"  beta treasury:  {countries['beta']['treasury']} (expected 60.0)")
        print(f"  errors: {result['errors']}")

        assert result["success"] is True
        assert countries["alpha"]["treasury"] == pytest.approx(0.0), \
            f"alpha treasury should be 0.0, got {countries['alpha']['treasury']}"
        assert countries["beta"]["treasury"] == pytest.approx(60.0), \
            f"beta treasury should be 60.0 (50+10), got {countries['beta']['treasury']}"
        assert len(result["errors"]) >= 1, "Should have 'Reduced coins' error"

        # CONSERVATION
        total = countries["alpha"]["treasury"] + countries["beta"]["treasury"]
        assert total == pytest.approx(60.0), \
            f"CONSERVATION VIOLATION: total {total} != 60.0"


class TestA3ArmsSaleUnitsAndCoins:
    """A3. Arms sale — units + coins swap, conservation of both."""

    def test_arms_sale_conservation(self):
        countries = {
            "alpha": _country(treasury=100.0, mil_ground=10),
            "beta": _country(treasury=50.0, mil_ground=2),
        }
        proposal = _proposal(
            txn_type="arms_sale",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"ground_units": 3},
            receives={"coins": 6},
        )
        result = execute_transaction(proposal, countries)

        print(f"  alpha ground: {countries['alpha']['mil_ground']} (expected 7)")
        print(f"  beta ground:  {countries['beta']['mil_ground']} (expected 5)")
        print(f"  alpha treasury: {countries['alpha']['treasury']} (expected 106)")
        print(f"  beta treasury:  {countries['beta']['treasury']} (expected 44)")
        print(f"  result: {result}")

        # Units moved
        assert countries["alpha"]["mil_ground"] == 7, \
            f"alpha ground should be 7, got {countries['alpha']['mil_ground']}"
        assert countries["beta"]["mil_ground"] == 5, \
            f"beta ground should be 5, got {countries['beta']['mil_ground']}"

        # Coins moved (counterpart pays proposer)
        assert countries["alpha"]["treasury"] == pytest.approx(106.0), \
            f"alpha treasury should be 106, got {countries['alpha']['treasury']}"
        assert countries["beta"]["treasury"] == pytest.approx(44.0), \
            f"beta treasury should be 44, got {countries['beta']['treasury']}"

        # CONSERVATION: total ground units unchanged
        total_ground = countries["alpha"]["mil_ground"] + countries["beta"]["mil_ground"]
        assert total_ground == 12, \
            f"CONSERVATION VIOLATION: total ground {total_ground} != 12"

        # CONSERVATION: total coins unchanged
        total_coins = countries["alpha"]["treasury"] + countries["beta"]["treasury"]
        assert total_coins == pytest.approx(150.0), \
            f"CONSERVATION VIOLATION: total coins {total_coins} != 150.0"


class TestA4ArmsGiftNoCoins:
    """A4. Arms gift — units move, no coins change."""

    def test_arms_gift_no_coins(self):
        countries = {
            "alpha": _country(treasury=100.0, mil_naval=8),
            "beta": _country(treasury=50.0, mil_naval=3),
        }
        proposal = _proposal(
            txn_type="arms_gift",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"naval_units": 2},
        )
        result = execute_transaction(proposal, countries)

        print(f"  alpha naval: {countries['alpha']['mil_naval']} (expected 6)")
        print(f"  beta naval:  {countries['beta']['mil_naval']} (expected 5)")
        print(f"  alpha treasury: {countries['alpha']['treasury']} (expected 100)")
        print(f"  beta treasury:  {countries['beta']['treasury']} (expected 50)")

        assert result["success"] is True
        assert countries["alpha"]["mil_naval"] == 6
        assert countries["beta"]["mil_naval"] == 5

        # NO treasury change
        assert countries["alpha"]["treasury"] == pytest.approx(100.0), \
            f"alpha treasury changed! {countries['alpha']['treasury']}"
        assert countries["beta"]["treasury"] == pytest.approx(50.0), \
            f"beta treasury changed! {countries['beta']['treasury']}"

        # CONSERVATION: total naval unchanged
        total_naval = countries["alpha"]["mil_naval"] + countries["beta"]["mil_naval"]
        assert total_naval == 11, \
            f"CONSERVATION VIOLATION: total naval {total_naval} != 11"


class TestA5TechTransferNuclear:
    """A5. Tech transfer — nuclear. Sender keeps, receiver gains."""

    def test_tech_nuclear_replicable(self):
        countries = {
            "alpha": _country(nuclear_rd_progress=0.5),
            "beta": _country(nuclear_rd_progress=0.1),
        }
        proposal = _proposal(
            txn_type="tech_transfer",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"tech_nuclear": 2},
        )
        result = execute_transaction(proposal, countries)

        # Boost = min(0.3, 2 * 0.1) = 0.2
        expected_boost = 0.2
        expected_beta = 0.1 + expected_boost

        print(f"  alpha nuclear_rd_progress: {countries['alpha']['nuclear_rd_progress']} (expected 0.5 UNCHANGED)")
        print(f"  beta nuclear_rd_progress:  {countries['beta']['nuclear_rd_progress']} (expected {expected_beta})")

        assert result["success"] is True
        # Sender UNCHANGED (replicable — sender keeps)
        assert countries["alpha"]["nuclear_rd_progress"] == pytest.approx(0.5), \
            f"SENDER nuclear_rd_progress changed! {countries['alpha']['nuclear_rd_progress']}"
        # Receiver gains boost
        assert countries["beta"]["nuclear_rd_progress"] == pytest.approx(expected_beta), \
            f"beta nuclear_rd_progress should be {expected_beta}, got {countries['beta']['nuclear_rd_progress']}"


class TestA6TechTransferAI:
    """A6. Tech transfer — AI. Same replicable pattern."""

    def test_tech_ai_replicable(self):
        countries = {
            "alpha": _country(ai_rd_progress=0.6),
            "beta": _country(ai_rd_progress=0.0),
        }
        proposal = _proposal(
            txn_type="tech_transfer",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"tech_ai": 3},
        )
        result = execute_transaction(proposal, countries)

        # Boost = min(0.3, 3 * 0.1) = 0.3
        expected_boost = 0.3

        print(f"  alpha ai_rd_progress: {countries['alpha']['ai_rd_progress']} (expected 0.6 UNCHANGED)")
        print(f"  beta ai_rd_progress:  {countries['beta']['ai_rd_progress']} (expected {expected_boost})")

        assert result["success"] is True
        assert countries["alpha"]["ai_rd_progress"] == pytest.approx(0.6), \
            f"SENDER ai_rd_progress changed! {countries['alpha']['ai_rd_progress']}"
        assert countries["beta"]["ai_rd_progress"] == pytest.approx(expected_boost), \
            f"beta ai_rd_progress should be {expected_boost}, got {countries['beta']['ai_rd_progress']}"


class TestA7TechTransferCapped:
    """A7. Tech transfer — cap at 0.3 even for high level sharing."""

    def test_tech_nuclear_capped(self):
        """Level 5 shared: min(0.3, 5*0.1) = 0.3, not 0.5."""
        countries = {
            "alpha": _country(nuclear_rd_progress=0.8),
            "beta": _country(nuclear_rd_progress=0.1),
        }
        proposal = _proposal(
            txn_type="tech_transfer",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"tech_nuclear": 5},
        )
        result = execute_transaction(proposal, countries)

        print(f"  beta nuclear_rd_progress: {countries['beta']['nuclear_rd_progress']} (expected 0.4 = 0.1 + capped 0.3)")

        assert result["success"] is True
        assert countries["beta"]["nuclear_rd_progress"] == pytest.approx(0.4), \
            f"Should cap at +0.3, got {countries['beta']['nuclear_rd_progress']}"


class TestA8CombinedTransaction:
    """A8. Combined transaction — coins + tech in one go."""

    def test_combined_coins_and_tech(self):
        """Tech transfer with coins: proposer gives coins AND tech."""
        countries = {
            "alpha": _country(treasury=100.0, nuclear_rd_progress=0.5),
            "beta": _country(treasury=50.0, nuclear_rd_progress=0.0),
        }
        # Tech transfer gives tech — coins would be in a coin_transfer type
        # Since the system processes by type, we test tech_transfer with both
        # tech_nuclear and tech_ai in gives
        proposal = _proposal(
            txn_type="tech_transfer",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"tech_nuclear": 2, "tech_ai": 1},
        )
        result = execute_transaction(proposal, countries)

        print(f"  beta nuclear_rd_progress: {countries['beta']['nuclear_rd_progress']} (expected 0.2)")
        print(f"  beta ai_rd_progress: {countries['beta']['ai_rd_progress']} (expected 0.1)")
        print(f"  result changes: {result['changes']}")

        assert result["success"] is True
        assert countries["beta"]["nuclear_rd_progress"] == pytest.approx(0.2)
        assert countries["beta"]["ai_rd_progress"] == pytest.approx(0.1)
        assert len(result["changes"]) == 2, \
            f"Expected 2 changes (nuclear + AI), got {len(result['changes'])}"


class TestA9RejectedNoChanges:
    """A9. Rejected transaction — NO changes to any country state."""

    def test_rejected_no_changes(self):
        countries = {
            "alpha": _country(treasury=100.0, mil_ground=10),
            "beta": _country(treasury=50.0, mil_ground=5),
        }
        # Snapshot before
        alpha_before = dict(countries["alpha"])
        beta_before = dict(countries["beta"])

        proposal = _proposal(
            txn_type="coin_transfer",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"coins": 25},
            status="rejected",
        )
        result = execute_transaction(proposal, countries)

        print(f"  result: {result}")
        print(f"  alpha unchanged: {countries['alpha'] == alpha_before}")
        print(f"  beta unchanged:  {countries['beta'] == beta_before}")

        assert result["success"] is False
        assert countries["alpha"] == alpha_before, \
            f"REJECTED transaction modified alpha! {countries['alpha']}"
        assert countries["beta"] == beta_before, \
            f"REJECTED transaction modified beta! {countries['beta']}"


class TestA10FailedValidationNoChanges:
    """A10. Failed validation — NO changes."""

    def test_failed_validation_no_changes(self):
        countries = {
            "alpha": _country(treasury=100.0, mil_ground=10),
            "beta": _country(treasury=50.0, mil_ground=5),
        }
        alpha_before = dict(countries["alpha"])
        beta_before = dict(countries["beta"])

        proposal = _proposal(
            txn_type="arms_sale",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"ground_units": 3},
            receives={"coins": 6},
            status="failed_validation",
        )
        result = execute_transaction(proposal, countries)

        print(f"  result: {result}")

        assert result["success"] is False
        assert countries["alpha"] == alpha_before, \
            "failed_validation modified alpha!"
        assert countries["beta"] == beta_before, \
            "failed_validation modified beta!"


# ===========================================================================
# PART B: Persistence tests (L2 — real DB)
# ===========================================================================

SCENARIO_CODE = "start_one"
TEST_ROUND_B = 84
TEST_ROUNDS_B = [84, 85]


def _get_scenario_id(client) -> str:
    res = client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute()
    assert res.data, f"Scenario '{SCENARIO_CODE}' not found"
    return res.data[0]["id"]


def _cleanup_persistence_test(client, scenario_id: str) -> None:
    """Remove test rows for rounds 84-85."""
    for rn in TEST_ROUNDS_B:
        client.table("country_states_per_round").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("exchange_transactions").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()


@pytest.fixture(scope="class")
def db_client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="class")
def db_scenario_id(db_client):
    return _get_scenario_id(db_client)


@pytest.fixture(scope="class")
def seed_baseline(db_client, db_scenario_id):
    """Seed R83 baseline from R0, run coin transfer, persist, yield, cleanup."""
    _cleanup_persistence_test(db_client, db_scenario_id)

    prev_round = TEST_ROUND_B - 1  # 83

    # Clone R0 baseline into R83
    r0 = db_client.table("country_states_per_round") \
        .select("*").eq("scenario_id", db_scenario_id).eq("round_num", 0).execute()
    if not r0.data:
        pytest.skip("No R0 baseline data in country_states_per_round")

    for row in r0.data:
        nr = {k: v for k, v in row.items() if k != "id"}
        nr["round_num"] = prev_round
        db_client.table("country_states_per_round").insert(nr).execute()

    # Read treasuries before transaction for 2 test countries
    country_a = "columbia"
    country_b = "cathay"
    a_row = db_client.table("country_states_per_round").select("treasury") \
        .eq("scenario_id", db_scenario_id).eq("round_num", prev_round) \
        .eq("country_code", country_a).limit(1).execute()
    b_row = db_client.table("country_states_per_round").select("treasury") \
        .eq("scenario_id", db_scenario_id).eq("round_num", prev_round) \
        .eq("country_code", country_b).limit(1).execute()

    a_treasury_before = a_row.data[0]["treasury"] if a_row.data else 0
    b_treasury_before = b_row.data[0]["treasury"] if b_row.data else 0

    # Execute a coin transfer in memory
    countries = {
        country_a: {"treasury": float(a_treasury_before)},
        country_b: {"treasury": float(b_treasury_before)},
    }
    transfer_amount = 5.0
    proposal = _proposal(
        txn_type="coin_transfer",
        proposer_cid=country_a,
        counterpart_cid=country_b,
        gives={"coins": transfer_amount},
    )
    exec_result = execute_transaction(proposal, countries)

    # Persist using the same function full_round_runner uses
    from engine.agents.full_round_runner import _persist_transaction_state_changes
    _persist_transaction_state_changes(
        SCENARIO_CODE, TEST_ROUND_B,
        country_a, country_b,
        countries[country_a], countries[country_b],
    )

    yield {
        "country_a": country_a,
        "country_b": country_b,
        "a_treasury_before": float(a_treasury_before),
        "b_treasury_before": float(b_treasury_before),
        "transfer_amount": transfer_amount,
        "exec_result": exec_result,
        "countries_after": countries,
    }

    # Cleanup
    _cleanup_persistence_test(db_client, db_scenario_id)
    # Also clean up R83 baseline
    db_client.table("country_states_per_round").delete() \
        .eq("scenario_id", db_scenario_id).eq("round_num", prev_round).execute()


class TestB1CoinTransferPersisted:
    """B1. Verify execute_transaction changes are written to DB."""

    def test_treasury_changed_in_db(self, db_client, db_scenario_id, seed_baseline):
        info = seed_baseline
        a_cc = info["country_a"]
        b_cc = info["country_b"]
        transfer = info["transfer_amount"]

        # Read R84 from DB
        a_row = db_client.table("country_states_per_round").select("treasury") \
            .eq("scenario_id", db_scenario_id).eq("round_num", TEST_ROUND_B) \
            .eq("country_code", a_cc).limit(1).execute()
        b_row = db_client.table("country_states_per_round").select("treasury") \
            .eq("scenario_id", db_scenario_id).eq("round_num", TEST_ROUND_B) \
            .eq("country_code", b_cc).limit(1).execute()

        assert a_row.data, f"No R{TEST_ROUND_B} row for {a_cc}"
        assert b_row.data, f"No R{TEST_ROUND_B} row for {b_cc}"

        a_treasury_db = float(a_row.data[0]["treasury"])
        b_treasury_db = float(b_row.data[0]["treasury"])
        a_expected = info["a_treasury_before"] - transfer
        b_expected = info["b_treasury_before"] + transfer

        print(f"  {a_cc} DB treasury: {a_treasury_db} (expected {a_expected})")
        print(f"  {b_cc} DB treasury: {b_treasury_db} (expected {b_expected})")

        assert a_treasury_db == pytest.approx(a_expected, abs=0.01), \
            f"{a_cc} treasury in DB: {a_treasury_db} != expected {a_expected}"
        assert b_treasury_db == pytest.approx(b_expected, abs=0.01), \
            f"{b_cc} treasury in DB: {b_treasury_db} != expected {b_expected}"


class TestB2ConservationInDB:
    """B2. Conservation check across DB after transaction."""

    def test_total_coins_conserved_in_db(self, db_client, db_scenario_id, seed_baseline):
        info = seed_baseline
        a_cc = info["country_a"]
        b_cc = info["country_b"]

        a_row = db_client.table("country_states_per_round").select("treasury") \
            .eq("scenario_id", db_scenario_id).eq("round_num", TEST_ROUND_B) \
            .eq("country_code", a_cc).limit(1).execute()
        b_row = db_client.table("country_states_per_round").select("treasury") \
            .eq("scenario_id", db_scenario_id).eq("round_num", TEST_ROUND_B) \
            .eq("country_code", b_cc).limit(1).execute()

        a_db = float(a_row.data[0]["treasury"])
        b_db = float(b_row.data[0]["treasury"])
        original_total = info["a_treasury_before"] + info["b_treasury_before"]
        db_total = a_db + b_db

        print(f"  original total: {original_total}")
        print(f"  DB total:       {db_total}")

        assert db_total == pytest.approx(original_total, abs=0.02), \
            f"CONSERVATION VIOLATION in DB: {db_total} != {original_total}"


class TestB3MultipleTransactionsSameRound:
    """B3. Multiple transactions in the same round — no interference."""

    @pytest.fixture(scope="class")
    def multi_txn_setup(self, db_client, db_scenario_id):
        """Execute 3 coin transfers, persist all, yield, cleanup."""
        round_num = 85
        prev_round = 84

        # Cleanup first
        for rn in [prev_round, round_num]:
            db_client.table("country_states_per_round").delete() \
                .eq("scenario_id", db_scenario_id).eq("round_num", rn).execute()

        # Clone R0 into R84
        r0 = db_client.table("country_states_per_round") \
            .select("*").eq("scenario_id", db_scenario_id).eq("round_num", 0).execute()
        if not r0.data:
            pytest.skip("No R0 baseline data")

        for row in r0.data:
            nr = {k: v for k, v in row.items() if k != "id"}
            nr["round_num"] = prev_round
            db_client.table("country_states_per_round").insert(nr).execute()

        # Get initial treasuries for 3 countries
        treasuries = {}
        for cc in ["columbia", "cathay", "albion"]:
            row = db_client.table("country_states_per_round").select("treasury") \
                .eq("scenario_id", db_scenario_id).eq("round_num", prev_round) \
                .eq("country_code", cc).limit(1).execute()
            treasuries[cc] = float(row.data[0]["treasury"]) if row.data else 0.0

        from engine.agents.full_round_runner import _persist_transaction_state_changes

        # Transaction 1: columbia -> cathay, 3 coins
        countries_1 = {
            "columbia": {"treasury": treasuries["columbia"]},
            "cathay": {"treasury": treasuries["cathay"]},
        }
        execute_transaction(_proposal(
            txn_type="coin_transfer", proposer_cid="columbia",
            counterpart_cid="cathay", gives={"coins": 3},
        ), countries_1)
        _persist_transaction_state_changes(
            SCENARIO_CODE, round_num, "columbia", "cathay",
            countries_1["columbia"], countries_1["cathay"],
        )
        # Update running totals
        treasuries["columbia"] = countries_1["columbia"]["treasury"]
        treasuries["cathay"] = countries_1["cathay"]["treasury"]

        # Transaction 2: cathay -> albion, 2 coins
        countries_2 = {
            "cathay": {"treasury": treasuries["cathay"]},
            "albion": {"treasury": treasuries["albion"]},
        }
        execute_transaction(_proposal(
            txn_type="coin_transfer", proposer_cid="cathay",
            counterpart_cid="albion", gives={"coins": 2},
        ), countries_2)
        _persist_transaction_state_changes(
            SCENARIO_CODE, round_num, "cathay", "albion",
            countries_2["cathay"], countries_2["albion"],
        )
        treasuries["cathay"] = countries_2["cathay"]["treasury"]
        treasuries["albion"] = countries_2["albion"]["treasury"]

        # Transaction 3: albion -> columbia, 1 coin
        countries_3 = {
            "albion": {"treasury": treasuries["albion"]},
            "columbia": {"treasury": treasuries["columbia"]},
        }
        execute_transaction(_proposal(
            txn_type="coin_transfer", proposer_cid="albion",
            counterpart_cid="columbia", gives={"coins": 1},
        ), countries_3)
        _persist_transaction_state_changes(
            SCENARIO_CODE, round_num, "albion", "columbia",
            countries_3["albion"], countries_3["columbia"],
        )
        treasuries["albion"] = countries_3["albion"]["treasury"]
        treasuries["columbia"] = countries_3["columbia"]["treasury"]

        yield {
            "round_num": round_num,
            "expected_treasuries": treasuries,
        }

        # Cleanup
        for rn in [prev_round, round_num]:
            db_client.table("country_states_per_round").delete() \
                .eq("scenario_id", db_scenario_id).eq("round_num", rn).execute()

    def test_all_three_reflected(self, db_client, db_scenario_id, multi_txn_setup):
        info = multi_txn_setup
        rn = info["round_num"]
        expected = info["expected_treasuries"]

        for cc, exp_val in expected.items():
            row = db_client.table("country_states_per_round").select("treasury") \
                .eq("scenario_id", db_scenario_id).eq("round_num", rn) \
                .eq("country_code", cc).limit(1).execute()
            assert row.data, f"No R{rn} row for {cc}"
            db_val = float(row.data[0]["treasury"])
            print(f"  {cc} DB: {db_val}, expected: {exp_val}")
            assert db_val == pytest.approx(exp_val, abs=0.02), \
                f"{cc} treasury mismatch: DB={db_val}, expected={exp_val}"


# ===========================================================================
# PART C: Validation tests (L1 — no DB)
# ===========================================================================

class TestC1ValidateAssetsCoins:
    """C1. validate_assets — proposer cannot afford coins."""

    def test_insufficient_coins(self):
        country = _country(treasury=10.0)
        ok, errs = validate_assets(country, {"coins": 50})

        print(f"  ok: {ok}, errors: {errs}")

        assert ok is False
        assert len(errs) == 1
        assert "insufficient coins" in errs[0]

    def test_sufficient_coins(self):
        country = _country(treasury=100.0)
        ok, errs = validate_assets(country, {"coins": 50})
        assert ok is True
        assert errs == []

    def test_exact_coins(self):
        country = _country(treasury=50.0)
        ok, errs = validate_assets(country, {"coins": 50})
        assert ok is True
        assert errs == []


class TestC2ValidateAssetsUnits:
    """C2. validate_assets — unit check."""

    def test_insufficient_ground(self):
        country = _country(mil_ground=2)
        ok, errs = validate_assets(country, {"ground_units": 5})

        print(f"  ok: {ok}, errors: {errs}")

        assert ok is False
        assert "insufficient ground_units" in errs[0]

    def test_insufficient_naval(self):
        country = _country(mil_naval=1)
        ok, errs = validate_assets(country, {"naval_units": 3})
        ok2, _ = validate_assets(country, {"naval_units": 1})

        assert ok is False
        assert ok2 is True

    def test_insufficient_air(self):
        country = _country(mil_tactical_air=0)
        ok, errs = validate_assets(country, {"air_units": 1})
        assert ok is False
        assert "insufficient air_units" in errs[0]

    def test_multiple_insufficient(self):
        """Country lacks both coins and units — should report both errors."""
        country = _country(treasury=5.0, mil_ground=1)
        ok, errs = validate_assets(country, {"coins": 20, "ground_units": 5})

        print(f"  ok: {ok}, errors: {errs}")

        assert ok is False
        assert len(errs) == 2, f"Expected 2 errors, got {len(errs)}: {errs}"


class TestC3DoubleSpendPrevention:
    """C3. Double-spend — two transactions depleting same treasury."""

    def test_double_spend_clamped(self):
        """Country has 10 coins. Two transactions each giving 8.
        First succeeds with 8, second gets clamped to 2."""
        countries = {
            "alpha": _country(treasury=10.0),
            "beta": _country(treasury=0.0),
            "gamma": _country(treasury=0.0),
        }

        # First transaction: alpha -> beta, 8 coins
        p1 = _proposal(
            txn_type="coin_transfer",
            proposer_cid="alpha",
            counterpart_cid="beta",
            gives={"coins": 8},
        )
        r1 = execute_transaction(p1, countries)

        print(f"  After txn 1: alpha={countries['alpha']['treasury']}, beta={countries['beta']['treasury']}")

        assert r1["success"] is True
        assert countries["alpha"]["treasury"] == pytest.approx(2.0)
        assert countries["beta"]["treasury"] == pytest.approx(8.0)

        # Second transaction: alpha -> gamma, 8 coins (but only 2 left)
        p2 = _proposal(
            txn_type="coin_transfer",
            proposer_cid="alpha",
            counterpart_cid="gamma",
            gives={"coins": 8},
        )
        r2 = execute_transaction(p2, countries)

        print(f"  After txn 2: alpha={countries['alpha']['treasury']}, gamma={countries['gamma']['treasury']}")
        print(f"  txn 2 errors: {r2['errors']}")

        assert r2["success"] is True  # clamped but executed
        assert countries["alpha"]["treasury"] == pytest.approx(0.0), \
            f"alpha should be 0 after double-spend, got {countries['alpha']['treasury']}"
        assert countries["gamma"]["treasury"] == pytest.approx(2.0), \
            f"gamma should get 2 (clamped), got {countries['gamma']['treasury']}"
        assert len(r2["errors"]) >= 1, "Should have clamping error"

        # CONSERVATION: total across all 3 countries = original 10
        total = (countries["alpha"]["treasury"] +
                 countries["beta"]["treasury"] +
                 countries["gamma"]["treasury"])
        assert total == pytest.approx(10.0), \
            f"CONSERVATION VIOLATION: total {total} != 10.0"

    def test_validate_catches_double_spend(self):
        """validate_assets should flag insufficient after first spend."""
        country = _country(treasury=10.0)
        # Simulate first spend reducing treasury
        country["treasury"] -= 8  # now 2

        ok, errs = validate_assets(country, {"coins": 8})
        print(f"  After first spend, validate 8 more: ok={ok}, errs={errs}")

        assert ok is False
        assert "insufficient coins" in errs[0]
