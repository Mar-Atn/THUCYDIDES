"""Layer 1: Transaction execution pure-function tests.

No DB, no LLM. Tests execute_transaction, validate_assets, _are_at_war
against TRANSACTION_LOGIC.md and SEED E5 Section 7.
Run: cd app && PYTHONPATH=. pytest tests/layer1/test_transactions.py -v
"""
import pytest
from engine.agents.transactions import (
    TransactionProposal,
    execute_transaction,
    validate_assets,
    _are_at_war,
)


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
# execute_transaction TESTS
# ===========================================================================

class TestExecuteTransaction:
    """Tests for execute_transaction (coin, arms, tech, treaties)."""

    # --- 1. Coin transfer basic ---
    def test_coin_transfer_basic(self):
        """Proposer has 100 treasury, transfers 20 coins.
        Verify proposer=80, counterpart increased by 20."""
        countries = {
            "alpha": _country(treasury=100),
            "beta": _country(treasury=50),
        }
        p = _proposal(txn_type="coin_transfer", gives={"coins": 20})
        result = execute_transaction(p, countries)

        assert result["success"] is True
        assert countries["alpha"]["treasury"] == pytest.approx(80.0)
        assert countries["beta"]["treasury"] == pytest.approx(70.0)
        assert len(result["changes"]) >= 1

    # --- 2. Coin transfer insufficient (clamped) ---
    def test_coin_transfer_insufficient(self):
        """Proposer has 10, tries to transfer 20. Should clamp to 10."""
        countries = {
            "alpha": _country(treasury=10),
            "beta": _country(treasury=50),
        }
        p = _proposal(txn_type="coin_transfer", gives={"coins": 20})
        result = execute_transaction(p, countries)

        # Clamped: success is True because changes were made
        assert result["success"] is True
        assert countries["alpha"]["treasury"] == pytest.approx(0.0)
        assert countries["beta"]["treasury"] == pytest.approx(60.0)
        assert len(result["errors"]) >= 1  # "Reduced coins" error

    # --- 3. Arms sale (units for coins) ---
    def test_arms_sale(self):
        """Proposer gives 3 ground units, receives 6 coins.
        Verify: proposer ground -3, counterpart ground +3,
        proposer treasury +6, counterpart treasury -6."""
        countries = {
            "alpha": _country(treasury=100, mil_ground=10),
            "beta": _country(treasury=50, mil_ground=2),
        }
        p = _proposal(
            txn_type="arms_sale",
            gives={"ground_units": 3},
            receives={"coins": 6},
        )
        result = execute_transaction(p, countries)

        assert result["success"] is True
        assert countries["alpha"]["mil_ground"] == 7
        assert countries["beta"]["mil_ground"] == 5
        assert countries["alpha"]["treasury"] == pytest.approx(106.0)
        assert countries["beta"]["treasury"] == pytest.approx(44.0)

    # --- 4. Arms gift (no coins) ---
    def test_arms_gift(self):
        """Proposer gives 2 naval units. No coins exchanged."""
        countries = {
            "alpha": _country(treasury=100, mil_naval=5),
            "beta": _country(treasury=50, mil_naval=3),
        }
        p = _proposal(
            txn_type="arms_gift",
            gives={"naval_units": 2},
        )
        result = execute_transaction(p, countries)

        assert result["success"] is True
        assert countries["alpha"]["mil_naval"] == 3
        assert countries["beta"]["mil_naval"] == 5
        # Treasury unchanged
        assert countries["alpha"]["treasury"] == pytest.approx(100.0)
        assert countries["beta"]["treasury"] == pytest.approx(50.0)

    # --- 5. Tech transfer: nuclear ---
    def test_tech_transfer_nuclear(self):
        """Share nuclear tech level 2. Counterpart gains +0.2 progress (min(0.3, 2*0.1))."""
        countries = {
            "alpha": _country(),
            "beta": _country(nuclear_rd_progress=0.1),
        }
        p = _proposal(
            txn_type="tech_transfer",
            gives={"tech_nuclear": 2},
        )
        result = execute_transaction(p, countries)

        assert result["success"] is True
        assert countries["beta"]["nuclear_rd_progress"] == pytest.approx(0.3)
        assert len(result["changes"]) >= 1

    # --- 6. Tech transfer: AI ---
    def test_tech_transfer_ai(self):
        """Share AI tech level 3. Counterpart gains +0.3 progress (min(0.3, 3*0.1))."""
        countries = {
            "alpha": _country(),
            "beta": _country(ai_rd_progress=0.0),
        }
        p = _proposal(
            txn_type="tech_transfer",
            gives={"tech_ai": 3},
        )
        result = execute_transaction(p, countries)

        assert result["success"] is True
        assert countries["beta"]["ai_rd_progress"] == pytest.approx(0.3)

    # --- 7. Not accepted proposal ---
    def test_execute_not_accepted(self):
        """Rejected proposal returns success=False with error."""
        countries = {
            "alpha": _country(),
            "beta": _country(),
        }
        p = _proposal(status="rejected")
        result = execute_transaction(p, countries)

        assert result["success"] is False
        assert "Transaction not accepted" in result["errors"]

    # --- 8. Unknown country ---
    def test_execute_unknown_country(self):
        """Country not in countries dict returns success=False."""
        countries = {"alpha": _country()}  # beta missing
        p = _proposal()
        result = execute_transaction(p, countries)

        assert result["success"] is False
        assert "Country not found" in result["errors"]

    # --- 9. Treaty types: no mutation of treasury/units ---
    def test_treaty_types_no_mutation(self):
        """ceasefire/alliance/etc produce changes list but don't mutate treasury/units."""
        for treaty_type in ["ceasefire", "peace_treaty", "alliance", "trade_agreement",
                            "sanctions_coordination", "basing_rights"]:
            countries = {
                "alpha": _country(treasury=100, mil_ground=10),
                "beta": _country(treasury=50, mil_ground=5),
            }
            p = _proposal(txn_type=treaty_type)
            result = execute_transaction(p, countries)

            assert result["success"] is True, f"Failed for {treaty_type}"
            assert len(result["changes"]) >= 1, f"No changes for {treaty_type}"
            # Treasury and units unchanged
            assert countries["alpha"]["treasury"] == pytest.approx(100.0), f"Treasury mutated for {treaty_type}"
            assert countries["alpha"]["mil_ground"] == 10, f"Units mutated for {treaty_type}"
            assert countries["beta"]["treasury"] == pytest.approx(50.0), f"Treasury mutated for {treaty_type}"

    # --- 10. Arms sale: insufficient units (clamped) ---
    def test_arms_sale_insufficient_units(self):
        """Proposer has 1 ground unit but tries to give 5. Should clamp to 1."""
        countries = {
            "alpha": _country(treasury=100, mil_ground=1),
            "beta": _country(treasury=50, mil_ground=3),
        }
        p = _proposal(
            txn_type="arms_sale",
            gives={"ground_units": 5},
            receives={"coins": 10},
        )
        result = execute_transaction(p, countries)

        assert result["success"] is True
        assert countries["alpha"]["mil_ground"] == 0  # clamped from 5 to 1
        assert countries["beta"]["mil_ground"] == 4   # received 1
        assert len(result["errors"]) >= 1  # "Reduced ground_units"


# ===========================================================================
# validate_assets TESTS
# ===========================================================================

class TestValidateAssets:
    """Tests for validate_assets — pre-execution asset sufficiency check."""

    # --- 11. Sufficient coins ---
    def test_validate_sufficient_coins(self):
        """Country has 50 treasury, gives 30 coins -> (True, [])."""
        ok, errs = validate_assets(_country(treasury=50), {"coins": 30})
        assert ok is True
        assert errs == []

    # --- 12. Insufficient coins ---
    def test_validate_insufficient_coins(self):
        """Country has 10, gives 30 -> (False, ["insufficient coins..."])."""
        ok, errs = validate_assets(_country(treasury=10), {"coins": 30})
        assert ok is False
        assert len(errs) == 1
        assert "insufficient coins" in errs[0]

    # --- 13. Sufficient units ---
    def test_validate_sufficient_units(self):
        """Country has 5 ground, gives 3 -> True."""
        ok, errs = validate_assets(_country(mil_ground=5), {"ground_units": 3})
        assert ok is True
        assert errs == []

    # --- 14. Tech always valid ---
    def test_validate_tech_always_valid(self):
        """Tech transfer always valid (replicable, no depletion check)."""
        ok, errs = validate_assets(_country(treasury=0, mil_ground=0), {"tech_nuclear": 5, "tech_ai": 3})
        assert ok is True
        assert errs == []


# ===========================================================================
# _are_at_war TESTS
# ===========================================================================

class TestAreAtWar:
    """Tests for _are_at_war helper."""

    # --- 15. Countries on opposite sides ---
    def test_at_war_true(self):
        """Countries on opposite sides of a war -> True."""
        wars = [{"belligerents_a": ["alpha", "gamma"], "belligerents_b": ["beta", "delta"]}]
        assert _are_at_war("alpha", "beta", wars) is True

    # --- 16. Countries not in any war ---
    def test_at_war_false(self):
        """Countries not in any war -> False."""
        wars = [{"belligerents_a": ["gamma"], "belligerents_b": ["delta"]}]
        assert _are_at_war("alpha", "beta", wars) is False

    # --- 17. Same side ---
    def test_at_war_same_side(self):
        """Both countries on same side -> False."""
        wars = [{"belligerents_a": ["alpha", "beta"], "belligerents_b": ["gamma"]}]
        assert _are_at_war("alpha", "beta", wars) is False

    # --- Bonus: empty wars list ---
    def test_at_war_empty_wars(self):
        """No wars at all -> False."""
        assert _are_at_war("alpha", "beta", []) is False

    # --- Bonus: reversed sides ---
    def test_at_war_reversed(self):
        """alpha in b_set, beta in a_set -> still True."""
        wars = [{"belligerents_a": ["beta"], "belligerents_b": ["alpha"]}]
        assert _are_at_war("alpha", "beta", wars) is True
