"""Layer 1 tests — Sprint 1 Foundation.

Tests config loading, DB connectivity, LLM service, and API endpoints.
Run: cd app && PYTHONPATH=. pytest tests/layer1/test_foundation.py -v
"""

import pytest
from fastapi.testclient import TestClient

from engine.config import settings
from engine.config.settings import LLMUseCase, LLMModelConfig, LLMProvider
from engine.main import app
from engine.models.db import Country, Role, Zone, WorldState, SimRun
from engine.models.api import APIResponse

SIM_ID = "00000000-0000-0000-0000-000000000001"
client = TestClient(app)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestConfig:
    def test_settings_load(self):
        assert settings.supabase_url.startswith("https://")
        assert settings.has_anthropic
        assert settings.has_gemini
        assert settings.default_sim_id == SIM_ID

    def test_llm_model_config_all_use_cases(self):
        for use_case in LLMUseCase:
            config = LLMModelConfig.get(use_case)
            assert "primary" in config
            assert "fallback" in config
            assert "max_tokens" in config
            assert config["primary"]["provider"] in (LLMProvider.ANTHROPIC, LLMProvider.GEMINI)

    def test_settings_get_llm_config(self):
        config = settings.get_llm_config(LLMUseCase.QUICK_SCAN)
        assert "provider" in config
        assert "model" in config
        assert "max_tokens" in config


# ---------------------------------------------------------------------------
# DB Models
# ---------------------------------------------------------------------------

class TestModels:
    def test_country_model(self):
        c = Country(id="test", sim_run_id=SIM_ID, sim_name="Test", regime_type="democracy", team_type="solo")
        assert c.gdp == 0
        assert c.stability == 5
        assert c.nuclear_level == 0

    def test_role_model(self):
        r = Role(id="test", sim_run_id=SIM_ID, character_name="Test", country_code="test")
        assert r.status == "active"
        assert r.powers == []

    def test_world_state_model(self):
        w = WorldState(sim_run_id=SIM_ID)
        assert w.oil_price == 80.0
        assert w.nuclear_used_this_sim is False


# ---------------------------------------------------------------------------
# API Endpoints (integration — hits live Supabase)
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["db"] == "connected"

    def test_health_checks_llm(self):
        r = client.get("/health")
        data = r.json()
        assert data["data"]["llm_anthropic"] in ("ok", "unavailable")
        assert data["data"]["llm_gemini"] in ("ok", "unavailable")


class TestCountryEndpoints:
    def test_list_countries(self):
        r = client.get(f"/api/sim/{SIM_ID}/countries")
        assert r.status_code == 200
        data = r.json()
        assert data["data"]["count"] == 20

    def test_get_columbia(self):
        r = client.get(f"/api/sim/{SIM_ID}/country/columbia")
        assert r.status_code == 200
        c = r.json()["data"]
        assert c["sim_name"] == "Columbia"
        assert c["gdp"] == 280.0
        assert c["regime_type"] == "democracy"
        assert c["nuclear_level"] == 3

    def test_get_cathay(self):
        r = client.get(f"/api/sim/{SIM_ID}/country/cathay")
        assert r.status_code == 200
        c = r.json()["data"]
        assert c["gdp"] == 190.0
        assert c["mil_ground"] == 25

    def test_country_not_found(self):
        r = client.get(f"/api/sim/{SIM_ID}/country/atlantis")
        assert r.status_code == 404


class TestRoleEndpoints:
    def test_list_all_roles(self):
        r = client.get(f"/api/sim/{SIM_ID}/roles")
        assert r.status_code == 200
        assert r.json()["meta"]["count"] == 40

    def test_filter_by_country(self):
        r = client.get(f"/api/sim/{SIM_ID}/roles", params={"country_code": "persia"})
        data = r.json()
        assert data["meta"]["count"] == 3
        names = {role["id"] for role in data["data"]}
        assert names == {"furnace", "anvil", "dawn"}


class TestWorldStateEndpoint:
    def test_get_world_state(self):
        r = client.get(f"/api/sim/{SIM_ID}/world")
        assert r.status_code == 200
        w = r.json()["data"]
        assert w["round_num"] == 0
        assert w["oil_price"] == 80.0
        assert len(w["wars"]) == 3
        assert w["formosa_blockade"] is False


class TestZoneEndpoints:
    def test_list_zones(self):
        r = client.get(f"/api/sim/{SIM_ID}/zones")
        assert r.status_code == 200
        assert r.json()["meta"]["count"] == 57

    def test_filter_by_theater(self):
        r = client.get(f"/api/sim/{SIM_ID}/zones", params={"theater": "mashriq"})
        data = r.json()
        assert data["meta"]["count"] > 0
        for zone in data["data"]:
            assert zone["theater"] == "mashriq"


class TestDeploymentEndpoints:
    def test_list_deployments(self):
        r = client.get(f"/api/sim/{SIM_ID}/deployments")
        assert r.status_code == 200
        assert r.json()["meta"]["count"] == 146

    def test_filter_by_country(self):
        r = client.get(f"/api/sim/{SIM_ID}/deployments", params={"country_code": "columbia"})
        data = r.json()
        assert data["meta"]["count"] > 20  # Columbia has many deployments


class TestLLMEndpoint:
    def test_llm_responds(self):
        r = client.post("/api/test/llm", json={"prompt": "What is 2+2? Just the number."})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "4" in data["data"]["response_text"]

    def test_llm_health(self):
        r = client.get("/api/llm/health")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "anthropic" in data
        assert "gemini" in data
