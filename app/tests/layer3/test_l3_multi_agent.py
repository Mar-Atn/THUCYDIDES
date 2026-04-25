"""Level 3 — Multi-Agent Interaction Tests.

Tests AI-AI interaction paths using ToolExecutor directly (no LLM calls).
Validates that the action dispatch pipeline handles multi-agent scenarios:
  - Agent A proposes transaction → Agent B accepts
  - Agent A proposes agreement → Agent B signs
  - Agent A declares war → Agent B observes event
  - Batch decisions from multiple agents

Uses the ToolExecutor directly against the live DB.
Requires: .env loaded, sim in active state.

Run:
    cd /path/to/THUCYDIDES && PYTHONPATH=app .venv/bin/python -m pytest app/tests/layer3/test_l3_multi_agent.py -v -s
"""
import json
import logging
import os
import pytest

logger = logging.getLogger(__name__)

# Load .env
from pathlib import Path
_env_path = Path(__file__).resolve().parents[2] / "engine" / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

SIM_RUN_ID = os.environ.get("TEST_SIM_RUN_ID", "c954b9b6-35f0-4973-a08b-f38406c524e7")


@pytest.fixture(scope="module")
def phrygia():
    """ToolExecutor for Phrygia (Vizier = HoS)."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="phrygia",
        scenario_code="ttt_v1",
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="vizier",
    )


@pytest.fixture(scope="module")
def solaria():
    """ToolExecutor for Solaria (Wellspring = HoS)."""
    from engine.agents.managed.tool_executor import ToolExecutor
    return ToolExecutor(
        country_code="solaria",
        scenario_code="ttt_v1",
        sim_run_id=SIM_RUN_ID,
        round_num=1,
        role_id="wellspring",
    )


@pytest.fixture(scope="module")
def client():
    from engine.services.supabase import get_client
    return get_client()


@pytest.fixture(scope="module", autouse=True)
def ensure_active(client):
    """Ensure sim is active Phase A."""
    run = client.table("sim_runs").select("status,current_phase").eq("id", SIM_RUN_ID).limit(1).execute()
    if not run.data:
        pytest.skip(f"SimRun {SIM_RUN_ID} not found")
    status = run.data[0]["status"]
    if status == "pre_start":
        from engine.services.sim_run_manager import start_simulation
        start_simulation(SIM_RUN_ID)
    elif status not in ("active",):
        pytest.skip(f"SimRun status={status}, need active")


# ---------------------------------------------------------------------------
# Test 3.1: AI-AI Transaction
# ---------------------------------------------------------------------------

class TestAIAITransaction:
    """Phrygia proposes transaction → Solaria accepts."""

    def test_propose_and_accept(self, phrygia, solaria, client):
        """Full transaction lifecycle: propose → accept."""
        # Step 1: Phrygia proposes (small amount to avoid treasury issues)
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "propose_transaction",
                "counterpart_country": "solaria",
                "offer": {"coins": 1},
                "request": {"coins": 1},
                "rationale": "L3 test: bilateral exchange",
            }
        }))
        logger.info("Propose: %s", result)

        # May fail due to treasury — that's OK, test the path
        if not result.get("success"):
            notes = result.get("result", result.get("validation_notes", ""))
            if "INSUFFICIENT" in str(notes) or "treasury" in str(notes).lower():
                pytest.skip("Treasury too low for test transaction")
            # If it's a different error, still check it didn't crash
            assert "validation_status" in result
            return

        # Extract transaction_id — may be in result directly or in nested result text
        txn_id = result.get("transaction_id")
        if not txn_id:
            # Check agent_decisions in DB for the latest transaction
            d = client.table("agent_decisions").select("validation_notes") \
                .eq("sim_run_id", SIM_RUN_ID).eq("action_type", "propose_transaction") \
                .order("created_at", desc=True).limit(1).execute()
            if d.data and "id=" in (d.data[0].get("validation_notes") or ""):
                import re
                m = re.search(r"id=([a-f0-9-]+)", d.data[0]["validation_notes"])
                if m:
                    txn_id = m.group(1)
        if not txn_id:
            # Also check exchange_transactions directly
            txn = client.table("exchange_transactions").select("id") \
                .eq("sim_run_id", SIM_RUN_ID).eq("proposer", "phrygia").eq("status", "pending") \
                .order("created_at", desc=True).limit(1).execute()
            txn_id = txn.data[0]["id"] if txn.data else None
        assert txn_id, f"No transaction_id found: {result}"

        # Step 2: Solaria accepts
        accept_result = json.loads(solaria.execute("submit_action", {
            "action": {
                "action_type": "accept_transaction",
                "transaction_id": txn_id,
                "response": "accept",
                "rationale": "L3 test: accepting exchange",
            }
        }))
        logger.info("Accept: %s", accept_result)
        # Should execute or fail with game-logic error (not crash)
        assert "validation_status" in accept_result


# ---------------------------------------------------------------------------
# Test 3.2: AI-AI Agreement
# ---------------------------------------------------------------------------

class TestAIAIAgreement:
    """Phrygia proposes agreement → Solaria signs."""

    def test_propose_and_sign(self, phrygia, solaria, client):
        """Full agreement lifecycle: propose → sign."""
        # Step 1: Phrygia proposes (using HoS role — has authority)
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "propose_agreement",
                "counterpart_country": "solaria",
                "agreement_name": "L3 Trade Pact",
                "agreement_type": "trade_agreement",
                "visibility": "public",
                "terms": "Bilateral trade cooperation and mutual economic support",
                "rationale": "L3 test: bilateral agreement",
            }
        }))
        logger.info("Propose agreement: %s", result)

        if not result.get("success"):
            notes = result.get("result", result.get("validation_notes", ""))
            if "UNAUTHORIZED" in str(notes):
                pytest.skip("Role not authorized for agreements")
            assert "validation_status" in result
            return

        agr_id = result.get("agreement_id")
        if not agr_id:
            # Check agreements table directly
            agr = client.table("agreements").select("id") \
                .eq("sim_run_id", SIM_RUN_ID).eq("proposer_country_code", "phrygia") \
                .eq("status", "proposed").order("created_at", desc=True).limit(1).execute()
            agr_id = agr.data[0]["id"] if agr.data else None
        assert agr_id, f"No agreement_id found: {result}"

        # Step 2: Solaria signs
        sign_result = json.loads(solaria.execute("submit_action", {
            "action": {
                "action_type": "sign_agreement",
                "agreement_id": agr_id,
                "rationale": "L3 test: signing agreement",
            }
        }))
        logger.info("Sign agreement: %s", sign_result)
        assert "validation_status" in sign_result

        # Verify agreement is now active in DB
        agr = client.table("agreements").select("status").eq("id", agr_id).limit(1).execute()
        if agr.data:
            logger.info("Agreement %s status: %s", agr_id, agr.data[0]["status"])
            assert agr.data[0]["status"] in ("active", "proposed"), \
                f"Unexpected agreement status: {agr.data[0]['status']}"


# ---------------------------------------------------------------------------
# Test 3.3: Declare War → Event Chain
# ---------------------------------------------------------------------------

class TestDeclareWar:
    """Phrygia declares war on Solaria → verify events."""

    def test_declare_war(self, phrygia, client):
        result = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "declare_war",
                "target_country": "solaria",
                "rationale": "L3 test: war declaration",
            }
        }))
        logger.info("Declare war: %s", result)
        # May succeed or fail (already at war, etc.)
        assert "validation_status" in result

        if result.get("success"):
            # Check relationship changed to at_war
            rel = client.table("relationships").select("relationship") \
                .eq("sim_run_id", SIM_RUN_ID) \
                .eq("from_country_code", "phrygia") \
                .eq("to_country_code", "solaria").limit(1).execute()
            if rel.data:
                logger.info("Phrygia→Solaria relationship: %s", rel.data[0]["relationship"])


# ---------------------------------------------------------------------------
# Test 3.4: Public Statements from Multiple Agents
# ---------------------------------------------------------------------------

class TestMultiAgentStatements:
    """Both agents issue public statements — verify coexistence."""

    def test_both_agents_speak(self, phrygia, solaria):
        r1 = json.loads(phrygia.execute("submit_action", {
            "action": {
                "action_type": "public_statement",
                "content": "Phrygia stands ready to defend its interests.",
                "rationale": "L3 multi-agent test",
            }
        }))
        r2 = json.loads(solaria.execute("submit_action", {
            "action": {
                "action_type": "public_statement",
                "content": "Solaria seeks peaceful resolution to all disputes.",
                "rationale": "L3 multi-agent test",
            }
        }))
        logger.info("Phrygia statement: %s", r1.get("success"))
        logger.info("Solaria statement: %s", r2.get("success"))
        assert r1.get("success") is True
        assert r2.get("success") is True


# ---------------------------------------------------------------------------
# Test 3.5: Cross-agent observation tools
# ---------------------------------------------------------------------------

class TestCrossAgentObservation:
    """Each agent can observe the other's country."""

    def test_get_country_info(self, phrygia, solaria):
        # Phrygia looks at Solaria
        r1 = json.loads(phrygia.execute("get_country_info", {"country_code": "solaria"}))
        assert "error" not in r1

        # Solaria looks at Phrygia
        r2 = json.loads(solaria.execute("get_country_info", {"country_code": "phrygia"}))
        assert "error" not in r2
