"""AI Participant Test Interface — development tool.

Web-based chat + cognitive block inspector for testing AI agents.
NOT part of the main app. Separate standalone server.

Usage: cd app && PYTHONPATH=. python3 test-interface/server.py
"""

import asyncio
import csv
import json
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional
import io

from engine.agents.leader import LeaderAgent
from engine.agents.profiles import load_all_roles, load_heads_of_state
from engine.config import map_config as _map_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("test-interface")

# Paths to SEED data for the map viewer
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_SEED_MAP_DIR = os.path.join(_REPO_ROOT, "2 SEED", "C_MECHANICS", "C1_MAP")
_SEED_DATA_DIR = os.path.join(_REPO_ROOT, "2 SEED", "C_MECHANICS", "C4_DATA")

_MAP_FILES = {
    "global": os.path.join(_SEED_MAP_DIR, "SEED_C1_MAP_GLOBAL_STATE_v4.json"),
    "eastern_ereb": os.path.join(_SEED_MAP_DIR, "SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json"),
    "mashriq": os.path.join(_SEED_MAP_DIR, "SEED_C3_THEATER_MASHRIQ_STATE_v1.json"),
}

# Global agent storage
_agents: dict[str, LeaderAgent] = {}


def get_or_create_agent(role_id: str) -> LeaderAgent:
    """Get existing agent or create a new one (sync init)."""
    if role_id not in _agents:
        agent = LeaderAgent(role_id)
        agent.initialize_sync()
        _agents[role_id] = agent
        logger.info("Initialized agent: %s", agent)
    return _agents[role_id]


# Live bilateral turn storage for polling
_live_bilateral: dict = {"turns": [], "status": "idle", "phase": ""}

# Observatory runtime state (in-memory, local to this process).
# Real start/pause/resume will be wired to the round runner by BACKEND agent.
_observatory_runtime: dict = {
    "status": "idle",          # idle | running | paused | finished
    "current_round": 0,
    "total_rounds": 6,
    "speed_sec": 15,
    "scenario": "start_one",
    "started_at": None,
    "last_event_at": None,
}


def _supabase_or_none():
    """Return a Supabase client or None if unavailable (envs missing, etc)."""
    try:
        from engine.services.supabase import get_client  # lazy import
        return get_client()
    except Exception as e:  # pragma: no cover
        logger.debug("Supabase unavailable: %s", e)
        return None


def initialize_with_llm(role_id: str) -> LeaderAgent:
    """Initialize agent with LLM-generated identity."""
    agent = LeaderAgent(role_id)
    try:
        asyncio.run(agent.initialize())
    except Exception as e:
        logger.warning("LLM init failed (%s), falling back to sync: %s", role_id, e)
        agent.initialize_sync()
    _agents[role_id] = agent
    return agent


class TestInterfaceHandler(SimpleHTTPRequestHandler):
    """HTTP handler for test interface."""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._serve_html()
        elif path == "/map" or path == "/map.html":
            self._serve_template("map.html")
        elif path == "/map/geography" or path == "/map_viewer" or path == "/map_viewer.html":
            self._serve_template("map_viewer.html")
        elif path == "/map/deployments" or path == "/map_deployments" or path == "/map_deployments.html":
            self._serve_template("map_deployments.html")
        elif path == "/observatory" or path == "/observatory.html":
            self._serve_template("observatory.html")
        elif path == "/api/observatory/state":
            self._json_response(self._observatory_state())
        elif path == "/api/observatory/realtime_config":
            self._json_response(self._observatory_realtime_config())
        elif path == "/api/observatory/units":
            params = parse_qs(parsed.query)
            rnd = params.get("round", [""])[0]
            scenario = params.get("scenario", ["start_one"])[0]
            sim_run_id = params.get("sim_run_id", [""])[0] or None
            self._json_response(self._observatory_units(rnd, scenario, sim_run_id))
        elif path == "/api/observatory/countries":
            params = parse_qs(parsed.query)
            rnd = params.get("round", [""])[0]
            scenario = params.get("scenario", ["start_one"])[0]
            sim_run_id = params.get("sim_run_id", [""])[0] or None
            self._json_response(self._observatory_countries(rnd, scenario, sim_run_id))
        elif path == "/api/observatory/events":
            params = parse_qs(parsed.query)
            limit = int(params.get("limit", ["50"])[0] or "50")
            scenario = params.get("scenario", ["start_one"])[0]
            sim_run_id = params.get("sim_run_id", [""])[0] or None
            self._json_response(self._observatory_events(limit, scenario, sim_run_id))
        elif path == "/api/observatory/combats":
            params = parse_qs(parsed.query)
            rnd = params.get("round", [""])[0]
            scenario = params.get("scenario", ["start_one"])[0]
            sim_run_id = params.get("sim_run_id", [""])[0] or None
            self._json_response(self._observatory_combats(rnd, scenario, sim_run_id))
        elif path == "/api/observatory/blockades":
            params = parse_qs(parsed.query)
            rnd = params.get("round", [""])[0]
            scenario = params.get("scenario", ["start_one"])[0]
            sim_run_id = params.get("sim_run_id", [""])[0] or None
            self._json_response(self._observatory_blockades(rnd, scenario, sim_run_id))
        elif path == "/api/observatory/global-series":
            params = parse_qs(parsed.query)
            scenario = params.get("scenario", ["start_one"])[0]
            sim_run_id = params.get("sim_run_id", [""])[0] or None
            self._json_response(self._observatory_global_series(scenario, sim_run_id))
        elif path == "/api/observatory/sim_runs":
            self._json_response(self._observatory_sim_runs())
        elif path == "/api/observatory/available-rounds":
            params = parse_qs(parsed.query)
            scenario = params.get("scenario", ["start_one"])[0]
            sim_run_id = params.get("sim_run_id", [""])[0] or None
            self._json_response(self._observatory_available_rounds(scenario, sim_run_id))
        elif path == "/api/observatory/movement-context":
            params = parse_qs(parsed.query)
            country = params.get("country", [""])[0]
            try:
                round_num = int(params.get("round", ["0"])[0])
            except ValueError:
                round_num = 0
            scenario = params.get("scenario", ["start_one"])[0]
            sim_run_id = params.get("sim_run_id", [""])[0] or None
            self._json_response(
                self._observatory_movement_context(country, round_num, scenario, sim_run_id)
            )
        elif path == "/api/map/global":
            self._serve_map_json("global")
        elif path == "/api/map/theater/eastern_ereb":
            self._serve_map_json("eastern_ereb")
        elif path == "/api/map/theater/mashriq":
            self._serve_map_json("mashriq")
        elif path == "/api/map/deployments":
            self._json_response(self._get_deployments())
        elif path == "/api/map/units":
            self._json_response(self._get_units())
        elif path == "/api/map/layouts":
            self._json_response(self._list_layouts())
        elif path == "/api/map/layouts/load":
            params = parse_qs(parsed.query)
            name = params.get("name", [""])[0]
            self._json_response(self._load_layout(name))
        elif path == "/api/map/countries":
            self._json_response(self._get_countries())
        elif path == "/api/config":
            self._json_response(self._get_config())
        elif path == "/api/roles":
            self._json_response(self._get_roles())
        elif path == "/api/agent/bilateral/live":
            params = parse_qs(parsed.query)
            since = int(params.get("since", ["0"])[0])
            self._json_response({
                "status": _live_bilateral["status"],
                "phase": _live_bilateral["phase"],
                "turns": _live_bilateral["turns"][since:],
                "total_turns": len(_live_bilateral["turns"]),
            })
        elif path == "/api/agent/state":
            params = parse_qs(parsed.query)
            role_id = params.get("role_id", [""])[0]
            self._json_response(self._get_agent_state(role_id))
        elif path == "/api/agent/history":
            params = parse_qs(parsed.query)
            role_id = params.get("role_id", [""])[0]
            self._json_response(self._get_agent_history(role_id))
        elif path.startswith("/static/"):
            self._serve_static(path)
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        if path == "/api/agent/init":
            self._json_response(self._init_agent(body))
        elif path == "/api/agent/chat":
            self._json_response(self._chat(body))
        elif path == "/api/agent/start_conversation":
            self._json_response(self._start_conversation(body))
        elif path == "/api/agent/end_conversation":
            self._json_response(self._end_conversation(body))
        elif path == "/api/agent/decide":
            self._json_response(self._decide(body))
        elif path == "/api/agent/bilateral":
            self._json_response(self._bilateral(body))
        elif path == "/api/sim/run":
            self._json_response(self._run_sim(body))
        elif path == "/api/sim/round":
            self._json_response(self._run_single_round(body))
        elif path == "/api/sim/cleanup":
            self._json_response(self._cleanup_test_runs(body))
        elif path == "/api/map/units/save":
            self._json_response(self._save_units_edited(body))
        elif path == "/api/map/save_geography":
            self._json_response(self._save_geography(body))
        elif path == "/api/observatory/start":
            self._json_response(self._observatory_start(body))
        elif path == "/api/observatory/pause":
            self._json_response(self._observatory_pause(body))
        elif path == "/api/observatory/resume":
            self._json_response(self._observatory_resume(body))
        elif path == "/api/observatory/rewind":
            self._json_response(self._observatory_rewind(body))
        elif path == "/api/observatory/stop":
            self._json_response(self._observatory_stop(body))
        elif path == "/api/observatory/speed":
            self._json_response(self._observatory_speed(body))
        elif path == "/api/observatory/reset":
            self._json_response(self._observatory_reset(body))
        else:
            self.send_error(404)

    def _json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _get_roles(self):
        """List all available roles."""
        roles = load_all_roles()
        return {
            "heads_of_state": [
                {"id": r["id"], "name": r["character_name"], "title": r["title"],
                 "country": r["country_id"], "parallel": r.get("parallel", "")}
                for r in roles.values() if r["is_head_of_state"]
            ],
            "other_roles": [
                {"id": r["id"], "name": r["character_name"], "title": r["title"],
                 "country": r["country_id"]}
                for r in roles.values() if not r["is_head_of_state"]
            ],
        }

    def _init_agent(self, body):
        """Initialize an agent."""
        role_id = body.get("role_id", "")
        use_llm = body.get("use_llm", False)

        if use_llm:
            agent = initialize_with_llm(role_id)
        else:
            agent = get_or_create_agent(role_id)

        return {
            "success": True,
            "agent": agent.info(),
            "cognitive_state": agent.get_cognitive_state(),
        }

    def _chat(self, body):
        """Chat with an agent."""
        role_id = body.get("role_id", "")
        message = body.get("message", "")
        use_llm = body.get("use_llm", False)

        agent = get_or_create_agent(role_id)

        if use_llm:
            try:
                response = asyncio.run(agent.chat(message))
            except Exception as e:
                response = f"[LLM error: {e}]\n{agent.chat_sync(message)}"
        else:
            response = agent.chat_sync(message)

        return {
            "response": response,
            "agent": agent.info(),
            "cognitive_state": agent.get_cognitive_state(),
        }

    def _start_conversation(self, body):
        """Start a new conversation with an agent."""
        role_id = body.get("role_id", "")
        counterpart = body.get("counterpart", "human_operator")
        agent = get_or_create_agent(role_id)
        agent.start_conversation(counterpart)
        return {
            "success": True,
            "status": agent.status,
            "message": f"Conversation started with {agent.role.get('character_name', role_id)}",
        }

    def _end_conversation(self, body):
        """End conversation and trigger reflection."""
        role_id = body.get("role_id", "")
        if role_id not in _agents:
            return {"error": f"Agent {role_id} not initialized"}
        agent = _agents[role_id]

        try:
            result = asyncio.run(agent.end_conversation())
        except Exception as e:
            result = {"updated": [], "error": str(e)}

        return {
            "success": True,
            "reflection": result,
            "agent": agent.info(),
            "cognitive_state": agent.get_cognitive_state(),
        }

    def _decide(self, body):
        """Test a specific decision type for an agent."""
        from engine.agents.decisions import (
            decide_budget, decide_tariffs, decide_sanctions,
            decide_opec, decide_military, decide_covert,
            decide_political, decide_active_loop,
        )

        role_id = body.get("role_id", "")
        decision_type = body.get("decision_type", "budget")
        round_context = body.get("round_context", {})

        if role_id not in _agents:
            agent = get_or_create_agent(role_id)
        else:
            agent = _agents[role_id]

        cognitive_blocks = agent._get_cognitive_blocks()

        # Build minimal round_context from country data if not provided
        if not round_context:
            round_context = {
                "economic": {
                    "gdp": agent.country.get("gdp", 0),
                    "treasury": agent.country.get("treasury", 0),
                    "inflation": agent.country.get("inflation", 0),
                    "debt_burden": agent.country.get("debt_burden", 0),
                    "tax_rate": agent.country.get("tax_rate", 0.24),
                    "social_baseline": agent.country.get("social_baseline", 0.30),
                    "maintenance_cost": agent.country.get("maintenance_per_unit", 0.05),
                },
                "political": {
                    "stability": agent.country.get("stability", 5),
                    "political_support": agent.country.get("political_support", 50),
                },
                "oil_price": 80,
                "bilateral": {"tariffs": {}, "sanctions": {}, "trade": {}},
                "wars": [],
                "military": {
                    "units": {},
                    "zones": {},
                    "reserves": {},
                    "enemy_visible": {},
                },
                "recent_events": [],
                "pending_conversations": [],
            }
            # Add at_war info
            at_war = agent.country.get("at_war_with", "")
            if at_war:
                round_context["wars"] = [{"belligerents_a": [agent.country["id"]], "belligerents_b": [at_war]}]

        dispatch = {
            "budget": lambda: decide_budget(cognitive_blocks, agent.country, round_context),
            "tariffs": lambda: decide_tariffs(cognitive_blocks, agent.country, round_context),
            "sanctions": lambda: decide_sanctions(cognitive_blocks, agent.country, round_context),
            "opec": lambda: decide_opec(cognitive_blocks, agent.country, round_context),
            "military": lambda: decide_military(cognitive_blocks, agent.country, round_context),
            "covert": lambda: decide_covert(cognitive_blocks, agent.country, agent.role, round_context),
            "political": lambda: decide_political(cognitive_blocks, agent.country, round_context),
            "active_loop": lambda: decide_active_loop(cognitive_blocks, agent.country, agent.role, round_context),
        }

        if decision_type not in dispatch:
            return {"error": f"Unknown decision type: {decision_type}. Valid: {list(dispatch.keys())}"}

        try:
            result = asyncio.run(dispatch[decision_type]())
        except Exception as e:
            logger.error("Decision failed: %s", e, exc_info=True)
            return {"error": str(e), "decision_type": decision_type}

        return {
            "success": True,
            "decision_type": decision_type,
            "result": result,
            "agent": agent.info(),
            "cognitive_state": agent.get_cognitive_state(),
        }

    def _bilateral(self, body):
        """Run a bilateral conversation between two agents."""
        from engine.agents.conversations import ConversationEngine

        role_a = body.get("role_a", "")
        role_b = body.get("role_b", "")
        max_turns = body.get("max_turns", 8)
        topic = body.get("topic", "")
        use_llm = body.get("use_llm", True)

        if not role_a or not role_b:
            return {"error": "Both role_a and role_b are required"}
        if role_a == role_b:
            return {"error": "Cannot have bilateral conversation with self"}
        if not use_llm:
            return {"error": "Bilateral conversations require LLM (use_llm must be true)"}

        # Initialize agents if needed (with LLM for bilateral)
        if role_a not in _agents:
            _agents[role_a] = initialize_with_llm(role_a)
        if role_b not in _agents:
            _agents[role_b] = initialize_with_llm(role_b)

        agent_a = _agents[role_a]
        agent_b = _agents[role_b]

        # Reset live state for polling
        _live_bilateral["turns"] = []
        _live_bilateral["status"] = "running"
        _live_bilateral["phase"] = "generating intent notes..."

        def on_turn(turn_data):
            _live_bilateral["turns"].append(turn_data)
            _live_bilateral["phase"] = f"turn {turn_data['turn']}: {turn_data['speaker_name']}"

        engine = ConversationEngine()
        try:
            _live_bilateral["phase"] = "generating intent notes..."
            result = asyncio.run(engine.run_bilateral(
                agent_a, agent_b, max_turns=max_turns, topic=topic,
                on_turn=on_turn,
            ))
            _live_bilateral["status"] = "complete"
            _live_bilateral["phase"] = "done"
        except Exception as e:
            logger.error("Bilateral failed: %s", e, exc_info=True)
            return {"error": str(e)}

        return {
            "success": True,
            "transcript": result.transcript,
            "turns": result.turns,
            "ended_by": result.ended_by,
            "intent_notes": result.intent_notes,
            "reflections": result.reflections,
            "agents": {
                role_a: {
                    "info": agent_a.info(),
                    "cognitive_state": agent_a.get_cognitive_state(),
                },
                role_b: {
                    "info": agent_b.info(),
                    "cognitive_state": agent_b.get_cognitive_state(),
                },
            },
        }

    def _run_sim(self, body):
        """Run a full unmanned simulation."""
        from engine.agents.runner import run_full_sim

        num_rounds = body.get("num_rounds", 1)
        active_loop_ticks = body.get("active_loop_ticks", 1)
        nous_intensity = body.get("nous_intensity", 0)
        persist = bool(body.get("persist", False))

        logger.info("Starting full SIM: %d rounds, %d ticks, NOUS=%d, persist=%s",
                     num_rounds, active_loop_ticks, nous_intensity, persist)

        sim_run_id: str | None = None
        if persist:
            try:
                from engine.agents.persistence import create_test_sim_run
                sim_run_id = create_test_sim_run(
                    name="full_sim", max_rounds=num_rounds,
                )
                logger.info("Persist enabled: sim_run_id=%s", sim_run_id)
            except Exception as e:
                logger.error("Could not create test sim_run: %s", e)

        try:
            result = asyncio.run(run_full_sim(
                num_rounds=num_rounds,
                active_loop_ticks=active_loop_ticks,
                nous_intensity=nous_intensity,
                sim_run_id=sim_run_id,
            ))
            return {
                "success": True,
                "sim_run_id": sim_run_id,
                "summary": result.summary(),
                "num_rounds": result.num_rounds,
                "total_duration": result.total_duration_seconds,
                "rounds": [
                    {
                        "round_num": r.round_num,
                        "summary": r.summary(),
                        "duration": r.duration_seconds,
                        "actions_count": sum(len(v) for v in r.actions_taken.values()),
                        "conversations_count": len(r.conversations),
                        "transactions_count": len(r.transactions),
                        "log": r.log[-10:],  # last 10 log entries
                    }
                    for r in result.rounds
                ],
                "agents": result.agents,
            }
        except Exception as e:
            logger.error("SIM run failed: %s", e, exc_info=True)
            return {"error": str(e)}

    def _run_single_round(self, body):
        """Run a single round with existing or new agents."""
        from engine.agents.runner import (
            run_round, load_countries_from_csv, _build_default_world_state,
        )

        round_num = body.get("round_num", 1)
        active_loop_ticks = body.get("active_loop_ticks", 1)
        nous_intensity = body.get("nous_intensity", 0)
        persist = bool(body.get("persist", False))

        logger.info("Running single round %d (persist=%s)", round_num, persist)

        sim_run_id: str | None = None
        if persist:
            try:
                from engine.agents.persistence import create_test_sim_run
                sim_run_id = create_test_sim_run(
                    name="single_round", max_rounds=1,
                )
                logger.info("Persist enabled: sim_run_id=%s", sim_run_id)
            except Exception as e:
                logger.error("Could not create test sim_run: %s", e)

        # Use existing agents or initialize new ones
        if not _agents:
            # Initialize all heads of state
            from engine.agents.profiles import load_heads_of_state
            heads = load_heads_of_state()
            for role_id in heads:
                agent = LeaderAgent(role_id)
                agent.initialize_sync()
                _agents[role_id] = agent

        countries = load_countries_from_csv()
        world_state = _build_default_world_state(round_num)

        try:
            result = asyncio.run(run_round(
                round_num=round_num,
                agents=_agents,
                countries=countries,
                world_state=world_state,
                active_loop_ticks=active_loop_ticks,
                nous_intensity=nous_intensity,
                sim_run_id=sim_run_id,
            ))
            if sim_run_id:
                try:
                    from engine.agents.persistence import mark_sim_run_complete
                    mark_sim_run_complete(sim_run_id, current_round=round_num)
                except Exception as e:
                    logger.warning("mark_sim_run_complete failed: %s", e)
            return {
                "success": True,
                "sim_run_id": sim_run_id,
                "summary": result.summary(),
                "round_num": result.round_num,
                "duration": result.duration_seconds,
                "actions_count": sum(len(v) for v in result.actions_taken.values()),
                "conversations_count": len(result.conversations),
                "transactions_count": len(result.transactions),
                "mandatory_count": len(result.mandatory_inputs),
                "log": result.log,
            }
        except Exception as e:
            logger.error("Round failed: %s", e, exc_info=True)
            return {"error": str(e)}

    def _cleanup_test_runs(self, body):
        """Delete test sim_runs older than N hours (default 24)."""
        from engine.agents.persistence import delete_test_runs
        hours = int(body.get("older_than_hours", 24))
        try:
            deleted = delete_test_runs(older_than_hours=hours)
            return {"success": True, "deleted": deleted, "older_than_hours": hours}
        except Exception as e:
            logger.error("Cleanup failed: %s", e, exc_info=True)
            return {"error": str(e)}

    def _get_agent_state(self, role_id):
        """Get current cognitive state."""
        if role_id not in _agents:
            return {"error": f"Agent {role_id} not initialized"}
        return _agents[role_id].get_cognitive_state()

    def _get_agent_history(self, role_id):
        """Get cognitive state version history."""
        if role_id not in _agents:
            return {"error": f"Agent {role_id} not initialized"}
        return {"history": _agents[role_id].get_state_history()}

    def _serve_static(self, url_path):
        """Serve static files with no-cache headers (prevents dev stale cache)."""
        rel = url_path.lstrip("/")  # "static/map.js"
        path = os.path.join(_THIS_DIR, rel)
        if not os.path.exists(path) or not os.path.isfile(path):
            self.send_error(404)
            return
        # Basic MIME type detection
        ext = os.path.splitext(path)[1].lower()
        ctype = {
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".html": "text/html; charset=utf-8",
            ".json": "application/json",
            ".svg": "image/svg+xml",
            ".png": "image/png",
        }.get(ext, "application/octet-stream")
        with open(path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_template(self, name):
        """Serve a template HTML file by name."""
        path = os.path.join(_THIS_DIR, "templates", name)
        if not os.path.exists(path):
            self.send_error(404, f"Template not found: {name}")
            return
        with open(path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def _serve_map_json(self, key):
        """Load a SEED map JSON file and return it."""
        path = _MAP_FILES.get(key)
        if not path or not os.path.exists(path):
            self.send_error(404, f"Map file not found: {key}")
            return
        try:
            with open(path) as f:
                data = json.load(f)
            self._json_response(data)
        except Exception as e:
            logger.error("Failed to load map %s: %s", key, e)
            self.send_error(500, str(e))

    def _get_deployments(self):
        """DEPRECATED compat shim: aggregates unit coords into legacy-shape rows.

        Produces {country_id, unit_type, count, global_row, global_col} rows
        plus a per-hex index keyed by "row,col". Reserves/embarked skipped.
        """
        path = os.path.join(_SEED_DATA_DIR, "units.csv")
        if not os.path.exists(path):
            return {"rows": [], "by_hex": {}, "error": "units.csv not found"}
        agg: dict[tuple[str, str, int, int], int] = {}
        with open(path) as f:
            for r in csv.DictReader(f):
                country = (r.get("country_id") or "").strip()
                utype = (r.get("unit_type") or "").strip()
                status = (r.get("status") or "active").strip()
                if status != "active":
                    continue
                try:
                    gr = int((r.get("global_row") or "").strip())
                    gc = int((r.get("global_col") or "").strip())
                except ValueError:
                    continue
                if not country or not utype:
                    continue
                agg[(country, utype, gr, gc)] = agg.get((country, utype, gr, gc), 0) + 1
        rows = []
        by_hex: dict[str, list[dict]] = {}
        for (country, utype, gr, gc), count in sorted(agg.items()):
            row = {
                "country_id": country,
                "unit_type": utype,
                "count": count,
                "global_row": gr,
                "global_col": gc,
                "notes": "",
            }
            rows.append(row)
            by_hex.setdefault(f"{gr},{gc}", []).append(row)
        return {"rows": rows, "by_hex": by_hex}

    def _get_units(self):
        """Return individual unit entities from units.csv (coordinate schema).

        Returns {units: [...], by_country: {...}, by_hex_summary: {...}}.
        Each unit dict has columns: unit_id, country_id, unit_type,
        global_row, global_col, theater, theater_row, theater_col,
        embarked_on, status, notes. Reserves / embarked units have
        empty coord fields.
        """
        path = os.path.join(_SEED_DATA_DIR, "units.csv")
        if not os.path.exists(path):
            return {"units": [], "by_country": {}, "by_hex_summary": {},
                    "error": "units.csv not found"}
        units: list[dict] = []
        by_country: dict[str, dict[str, int]] = {}
        by_hex_summary: dict[str, dict[str, int]] = {}

        def _toi(s):
            v = (s or "").strip()
            if not v:
                return None
            try:
                return int(v)
            except ValueError:
                return None

        with open(path) as f:
            for r in csv.DictReader(f):
                uid = (r.get("unit_id") or "").strip()
                if not uid:
                    continue
                u = {
                    "unit_id": uid,
                    "country_id": (r.get("country_id") or "").strip(),
                    "unit_type": (r.get("unit_type") or "").strip(),
                    "global_row": _toi(r.get("global_row")),
                    "global_col": _toi(r.get("global_col")),
                    "theater": (r.get("theater") or "").strip(),
                    "theater_row": _toi(r.get("theater_row")),
                    "theater_col": _toi(r.get("theater_col")),
                    "embarked_on": (r.get("embarked_on") or "").strip(),
                    "status": (r.get("status") or "active").strip(),
                    "notes": (r.get("notes") or "").strip(),
                }
                units.append(u)
                c, t = u["country_id"], u["unit_type"]
                if c and t:
                    by_country.setdefault(c, {})
                    by_country[c][t] = by_country[c].get(t, 0) + 1
                if u["global_row"] is not None and u["global_col"] is not None:
                    key = f"{u['global_row']},{u['global_col']}"
                    by_hex_summary.setdefault(key, {})
                    by_hex_summary[key][t] = by_hex_summary[key].get(t, 0) + 1
        return {
            "units": units,
            "by_country": by_country,
            "by_hex_summary": by_hex_summary,
            "total": len(units),
        }

    def _save_units_edited(self, body):
        """Write an edited units roster to a named layout file.

        Writes to units_layouts/ subdirectory as <name>.csv. Never touches units.csv.
        Expects body = {"name": "my_layout", "units": [...]}
        """
        import datetime, re
        units = body.get("units") or []
        name = (body.get("name") or "").strip()
        if not isinstance(units, list):
            return {"success": False, "error": "units must be a list"}
        if not name:
            return {"success": False, "error": "layout name required"}
        # sanitize name: alphanumeric + underscore + dash, max 64 chars
        safe = re.sub(r"[^A-Za-z0-9_\- ]", "", name).strip().replace(" ", "_")[:64]
        if not safe:
            return {"success": False, "error": "invalid layout name"}
        layouts_dir = os.path.join(_SEED_DATA_DIR, "units_layouts")
        os.makedirs(layouts_dir, exist_ok=True)
        out_path = os.path.join(layouts_dir, f"{safe}.csv")
        columns = ["unit_id", "country_id", "unit_type",
                   "global_row", "global_col", "theater",
                   "theater_row", "theater_col",
                   "embarked_on", "status", "notes"]
        try:
            with open(out_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                for u in units:
                    row = {}
                    for k in columns:
                        v = u.get(k)
                        row[k] = "" if v is None else v
                    writer.writerow(row)
        except Exception as e:
            logger.exception("save layout failed")
            return {"success": False, "error": str(e)}
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        logger.info("Saved %d units to %s", len(units), out_path)
        return {
            "success": True,
            "name": safe,
            "path": out_path,
            "count": len(units),
            "timestamp": ts,
        }

    def _save_geography(self, body):
        """Save updated map geography to the template's map_config in Supabase.

        Also saves the JSON file locally for backup.
        Expects body = {"grid": [...], "chokepoints": {...}, "dieHards": {...}}
        """
        try:
            grid = body.get("grid")
            chokepoints = body.get("chokepoints", {})
            die_hards = body.get("dieHards", {})
            nuclear_sites = body.get("nuclearSites", {})

            if not grid:
                return {"error": "No grid data provided"}

            # 1. Save to local JSON file (backup)
            import json
            map_path = os.path.join(os.path.dirname(__file__),
                "..", "..", "2 SEED", "C_MECHANICS", "C1_MAP", "SEED_C1_MAP_GLOBAL_STATE_v4.json")
            with open(map_path) as f:
                existing = json.load(f)
            existing["grid"] = grid
            existing["chokepoints"] = chokepoints
            existing["dieHards"] = die_hards
            existing["nuclearSites"] = nuclear_sites
            with open(map_path, "w") as f:
                json.dump(existing, f, indent=2)

            # 2. Save to Supabase template map_config
            from supabase import create_client
            url = os.environ.get("SUPABASE_URL", "")
            key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
            if not url or not key:
                return jsonify({"error": "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars required"}), 500
            client = create_client(url, key)

            # Get current map_config
            tpl = client.table("sim_templates").select("map_config").limit(1).execute()
            if tpl.data:
                map_config = tpl.data[0].get("map_config", {})
                if isinstance(map_config, dict) and "global" in map_config:
                    map_config["global"]["grid"] = grid
                    map_config["global"]["chokepoints"] = chokepoints
                    map_config["global"]["die_hards"] = die_hards
                    map_config["global"]["nuclear_sites"] = nuclear_sites
                    client.table("sim_templates").update({"map_config": map_config}).eq("id", tpl.data[0].get("id", "")).execute()

            # 3. Save color changes to countries table
            color_changes = body.get("colorChanges", {})
            if color_changes:
                for cid, colors in color_changes.items():
                    update = {}
                    if "color_map" in colors:
                        update["color_map"] = colors["color_map"]
                    if update:
                        client.table("countries").update(update).eq(
                            "id", cid).eq("sim_run_id", "00000000-0000-0000-0000-000000000001").execute()

            return {"status": "ok", "message": "Geography saved to template and local JSON"}
        except Exception as e:
            return {"error": str(e)}

    def _list_layouts(self):
        """List saved layout files in units_layouts/ directory."""
        layouts_dir = os.path.join(_SEED_DATA_DIR, "units_layouts")
        if not os.path.exists(layouts_dir):
            return {"layouts": []}
        layouts = []
        for fname in sorted(os.listdir(layouts_dir)):
            if not fname.endswith(".csv"):
                continue
            path = os.path.join(layouts_dir, fname)
            try:
                mtime = os.path.getmtime(path)
                with open(path) as f:
                    row_count = sum(1 for _ in f) - 1  # minus header
                layouts.append({
                    "name": fname[:-4],
                    "count": max(0, row_count),
                    "modified": mtime,
                })
            except Exception:
                continue
        layouts.sort(key=lambda x: x["modified"], reverse=True)
        return {"layouts": layouts}

    def _load_layout(self, name):
        """Load a named layout file and return its units."""
        import re
        safe = re.sub(r"[^A-Za-z0-9_\- ]", "", name or "").strip().replace(" ", "_")
        if not safe:
            return {"success": False, "error": "invalid name"}
        path = os.path.join(_SEED_DATA_DIR, "units_layouts", f"{safe}.csv")
        if not os.path.exists(path):
            return {"success": False, "error": "layout not found"}
        try:
            units = []
            with open(path) as f:
                reader = csv.DictReader(f)
                for r in reader:
                    # convert int fields
                    for k in ("global_row", "global_col", "theater_row", "theater_col"):
                        v = r.get(k, "")
                        r[k] = int(v) if v not in ("", None) else None
                    units.append(r)
            return {"success": True, "name": safe, "units": units, "count": len(units)}
        except Exception as e:
            logger.exception("load layout failed")
            return {"success": False, "error": str(e)}

    def _get_config(self):
        """Return central map config — mirrors app/engine/config/map_config.py."""
        return {
            "version": _map_config.MAP_CONFIG_VERSION,
            "global_rows": _map_config.GLOBAL_ROWS,
            "global_cols": _map_config.GLOBAL_COLS,
            "theaters": _map_config.THEATERS,
            "theater_names": _map_config.THEATER_NAMES,
            "countries": _map_config.COUNTRY_CODES,
            "unit_types": _map_config.UNIT_TYPES,
            "unit_statuses": _map_config.UNIT_STATUSES,
            "theater_link_hexes": {
                f"{r},{c}": t
                for (r, c), t in _map_config.theater_link_hexes().items()
            },
        }

    def _get_countries(self):
        """Parse countries.csv — return id, name, colors (map+ui+light) from UX style."""
        path = os.path.join(_SEED_DATA_DIR, "countries.csv")
        countries = {}
        if os.path.exists(path):
            with open(path) as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = (r.get("id") or "").strip()
                    if not cid:
                        continue
                    countries[cid] = {
                        "id": cid,
                        "name": (r.get("sim_name") or cid).strip(),
                        "parallel": (r.get("parallel") or "").strip(),
                        "regime": (r.get("regime_type") or "").strip(),
                        "home_zones": [
                            z.strip() for z in (r.get("home_zones") or "").split(",")
                            if z.strip()
                        ],
                        "at_war_with": [
                            z.strip() for z in (r.get("at_war_with") or "").split(",")
                            if z.strip()
                        ],
                    }
        # Unified dual palette from SEED_H1_UX_STYLE_v2.md
        palette = {
            "columbia": {"ui": "#3A6B9F", "map": "#9AB5D0", "light": "#E8EFF6"},
            "cathay":   {"ui": "#C4A030", "map": "#E8D5A3", "light": "#F8F2E5"},
            "sarmatia": {"ui": "#A06060", "map": "#D4A5A5", "light": "#F5EAEA"},
            "ruthenia": {"ui": "#5A9A5A", "map": "#A5C8A5", "light": "#EBF3EB"},
            "persia":   {"ui": "#9A7040", "map": "#C8A57A", "light": "#F2EBE0"},
            "gallia":   {"ui": "#4A6FA0", "map": "#A5B8D4", "light": "#EBF0F6"},
            "teutonia": {"ui": "#3A8A7A", "map": "#8AB5AA", "light": "#E8F2EF"},
            "thule":    {"ui": "#3A8A7A", "map": "#8AB5AA", "light": "#E8F2EF"},
            "albion":   {"ui": "#4A7A8F", "map": "#8AA5B5", "light": "#E8EFF3"},
            "freeland": {"ui": "#5A80A0", "map": "#A0B8C8", "light": "#EBF1F5"},
            "ponte":    {"ui": "#6A9A8A", "map": "#A5C8B8", "light": "#EBF3EF"},
            "bharata":  {"ui": "#B87850", "map": "#D4B5A5", "light": "#F5EDE5"},
            "formosa":  {"ui": "#B89048", "map": "#DCC5A0", "light": "#F5EEE0"},
            "yamato":   {"ui": "#5A7A9B", "map": "#A5B5C8", "light": "#EBF0F5"},
            "hanguk":   {"ui": "#4A8FA8", "map": "#A5C8D4", "light": "#E8F1F5"},
            "phrygia":  {"ui": "#8A6A48", "map": "#B5A08A", "light": "#F0EBE5"},
            "solaria":  {"ui": "#A89030", "map": "#C8B896", "light": "#F3F0E5"},
            "mirage":   {"ui": "#A88050", "map": "#D4BFA5", "light": "#F5EEE5"},
            "levantia": {"ui": "#9A9A40", "map": "#D4D4A5", "light": "#F3F3E8"},
            "choson":   {"ui": "#5A5A5A", "map": "#8A8A8A", "light": "#EFEFEF"},
            "caribe":   {"ui": "#3A7AAA", "map": "#8AACCC", "light": "#E8F0F6"},
            "sogdiana": {"ui": "#8A8A60", "map": "#C8C8A5", "light": "#F0F0E8"},
            "horn":     {"ui": "#8A7A68", "map": "#B5A896", "light": "#F0ECE8"},
            "sea":      {"ui": "#2a4a6a", "map": "#2a4a6a", "light": "#2a4a6a"},
        }
        # Try loading colors from Supabase template (canonical source)
        try:
            from supabase import create_client
            url = os.environ.get("SUPABASE_URL", "")
            key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars required")
            client = create_client(url, key)
            rows = client.table("countries").select("id, color_ui, color_map, color_light").eq(
                "sim_run_id", "00000000-0000-0000-0000-000000000001").execute().data
            for row in (rows or []):
                cid = row["id"]
                if row.get("color_map") and row["color_map"] != '#AAAAAA':
                    palette[cid] = {"ui": row["color_ui"], "map": row["color_map"], "light": row["color_light"]}
        except Exception as e:
            pass  # Fall back to hardcoded palette

        # merge palette onto countries
        for cid, colors in palette.items():
            countries.setdefault(cid, {"id": cid, "name": cid.title(), "home_zones": []})
            countries[cid]["colors"] = colors
        return {"countries": countries, "palette": palette}

    # -----------------------------------------------------------------
    # Observatory: data + controls
    # -----------------------------------------------------------------

    def _observatory_realtime_config(self):
        """Return Supabase URL + publishable anon key for browser Realtime subscription.

        Only the anon (publishable) key is sent to the browser. RLS governs access.
        Returns empty strings if env not configured; the UI falls back to polling.
        """
        try:
            from engine.config.settings import settings as _s
            url = getattr(_s, "supabase_url", "") or ""
            anon = getattr(_s, "supabase_anon_key", "") or ""
        except Exception as e:
            logger.debug("realtime_config lookup failed: %s", e)
            url, anon = "", ""
        return {"supabase_url": url, "supabase_anon_key": anon}

    def _observatory_state(self):
        """Return current runtime state (round, status, speed)."""
        state = dict(_observatory_runtime)
        # Try to enrich with latest round_states row from DB (best-effort).
        sb = _supabase_or_none()
        if sb is not None:
            try:
                res = (
                    sb.table("round_states")
                    .select("round_num,status,started_at,completed_at")
                    .order("round_num", desc=True)
                    .limit(1)
                    .execute()
                )
                if res.data:
                    latest = res.data[0]
                    state["db_latest_round"] = latest.get("round_num")
                    state["db_latest_status"] = latest.get("status")
            except Exception as e:
                logger.debug("round_states query failed: %s", e)
                state["db_latest_round"] = None
        else:
            state["db_latest_round"] = None
        return state

    def _resolve_observatory_run(self, scenario: str, sim_run_id: Optional[str]) -> Optional[str]:
        """Return the sim_run_id to use for Observatory filters.

        If ``sim_run_id`` is explicit (from the selector), use it.
        Otherwise resolve ``scenario`` to its legacy archived run.
        Returns None if nothing resolves (Observatory data endpoints
        should then treat the result as empty / fallback to seed CSVs).
        """
        if sim_run_id:
            return sim_run_id
        try:
            from engine.services.sim_run_manager import resolve_sim_run_id
            return resolve_sim_run_id(scenario)
        except Exception:
            return None

    def _observatory_sim_runs(self):
        """Return visible sim_runs for the Observatory selector dropdown.

        Lists runs with status ``visible_for_review`` (plus the singular
        ``archived`` legacy bucket) so facilitators can browse any test
        run that opted to persist its data after completing.
        """
        sb = _supabase_or_none()
        if sb is None:
            return {"runs": [], "source": "unavailable"}
        try:
            res = (
                sb.table("sim_runs")
                .select("id,name,description,status,current_round,max_rounds,scenario_id,seed,created_at,finalized_at")
                .in_("status", ["visible_for_review", "archived"])
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )
            runs = res.data or []
            # Enrich each run with scenario_code for UX
            scen_ids = {r["scenario_id"] for r in runs if r.get("scenario_id")}
            code_by_id: dict[str, str] = {}
            if scen_ids:
                try:
                    scens = (
                        sb.table("sim_scenarios")
                        .select("id,code")
                        .in_("id", list(scen_ids))
                        .execute()
                    )
                    code_by_id = {s["id"]: s["code"] for s in (scens.data or [])}
                except Exception as e:
                    logger.debug("sim_scenarios lookup failed: %s", e)
            for r in runs:
                r["scenario_code"] = code_by_id.get(r.get("scenario_id", ""), "")
            return {"runs": runs, "source": "db"}
        except Exception as e:
            logger.debug("sim_runs query failed: %s", e)
            return {"runs": [], "source": "error", "error": str(e)}

    def _observatory_available_rounds(self, scenario: str, sim_run_id: Optional[str] = None):
        """Return the sorted list of round_num values present for the run.

        Used by the MAPS-tab round scrubber so it knows what rounds to render.
        Queries ``country_states_per_round`` (20 rows/round, well under any
        pagination cap) instead of ``unit_states_per_round`` (345 rows/round
        which can blow past the Supabase Python client's 1000-row default).
        """
        sb = _supabase_or_none()
        if sb is None:
            return {"rounds": [], "source": "none"}
        run_id = self._resolve_observatory_run(scenario, sim_run_id)
        if not run_id:
            return {"rounds": [], "source": "no_run"}
        try:
            res = (
                sb.table("country_states_per_round")
                .select("round_num")
                .eq("sim_run_id", run_id)
                .execute()
            )
            rounds = sorted({r["round_num"] for r in (res.data or [])})
            return {"rounds": rounds, "source": "db", "sim_run_id": run_id}
        except Exception as e:
            logger.debug("available_rounds query failed: %s", e)
            return {"rounds": [], "source": "error", "error": str(e)}

    def _observatory_movement_context(
        self, country: str, round_num: int, scenario: str, sim_run_id: Optional[str] = None,
    ):
        """Return the AI movement context dict — exactly what build_movement_context()
        produces. Used by the Observatory's "context" inspector button.
        """
        if not country:
            return {"error": "country query param required"}
        try:
            from engine.services.movement_context import build_movement_context
            ctx = build_movement_context(
                country_code=country,
                scenario_code=scenario,
                round_num=round_num,
                sim_run_id=sim_run_id,
            )
            return ctx
        except Exception as e:
            logger.warning("movement_context build failed: %s", e)
            return {"error": str(e)}

    def _observatory_units(self, round_num: str, scenario: str, sim_run_id: Optional[str] = None):
        """Units at a given round from unit_states_per_round. Falls back to units.csv at round 0."""
        sb = _supabase_or_none()
        rnd_int = None
        try:
            rnd_int = int(round_num) if round_num not in ("", None) else None
        except ValueError:
            rnd_int = None

        run_id = self._resolve_observatory_run(scenario, sim_run_id)

        if sb is not None and rnd_int is not None and run_id:
            try:
                res = (
                    sb.table("unit_states_per_round")
                    .select("*")
                    .eq("sim_run_id", run_id)
                    .eq("round_num", rnd_int)
                    .execute()
                )
                data = res.data or []
                if data:
                    return {"round": rnd_int, "scenario": scenario, "sim_run_id": run_id, "units": data, "source": "db"}
            except Exception as e:
                logger.debug("unit_states_per_round query failed: %s", e)

        # Fallback: seed units.csv (round 0 baseline)
        baseline = self._get_units()
        return {
            "round": rnd_int or 0,
            "scenario": scenario,
            "sim_run_id": run_id,
            "units": baseline.get("units", []),
            "source": "seed_csv",
        }

    def _observatory_countries(self, round_num: str, scenario: str, sim_run_id: Optional[str] = None):
        """Country states at round N from country_states_per_round. Falls back to countries.csv."""
        sb = _supabase_or_none()
        rnd_int = None
        try:
            rnd_int = int(round_num) if round_num not in ("", None) else None
        except ValueError:
            rnd_int = None

        run_id = self._resolve_observatory_run(scenario, sim_run_id)

        if sb is not None and rnd_int is not None and run_id:
            try:
                res = (
                    sb.table("country_states_per_round")
                    .select("*")
                    .eq("sim_run_id", run_id)
                    .eq("round_num", rnd_int)
                    .execute()
                )
                data = res.data or []
                if data:
                    return {"round": rnd_int, "scenario": scenario, "sim_run_id": run_id, "countries": data, "source": "db"}
            except Exception as e:
                logger.debug("country_states_per_round query failed: %s", e)

        # Fallback: build minimal state from countries.csv baseline
        baseline = []
        path = os.path.join(_SEED_DATA_DIR, "countries.csv")
        if os.path.exists(path):
            with open(path) as f:
                for r in csv.DictReader(f):
                    cid = (r.get("id") or "").strip()
                    if not cid or cid == "sea":
                        continue

                    def _num(k, default=0.0):
                        v = (r.get(k) or "").strip()
                        try:
                            return float(v) if v else default
                        except ValueError:
                            return default

                    def _int(k, default=0):
                        v = (r.get(k) or "").strip()
                        try:
                            return int(float(v)) if v else default
                        except ValueError:
                            return default

                    baseline.append({
                        "country_code": cid,
                        "gdp": _num("gdp"),
                        "treasury": _num("treasury"),
                        "inflation": _num("inflation"),
                        "stability": _int("stability", 5),
                        "political_support": _int("political_support", 50),
                        "war_tiredness": _int("war_tiredness", 0),
                        "nuclear_level": _int("nuclear_level", 0),
                        "ai_level": _int("ai_level", 0),
                    })
        return {
            "round": rnd_int or 0,
            "scenario": scenario,
            "countries": baseline,
            "source": "seed_csv",
        }

    def _observatory_combats(self, round_num: str, scenario: str, sim_run_id: Optional[str] = None):
        """Combat log for a given round from observatory_combat_results."""
        sb = _supabase_or_none()
        rnd_int = None
        try:
            rnd_int = int(round_num) if round_num not in ("", None) else None
        except ValueError:
            rnd_int = None
        if sb is None:
            return {"round": rnd_int or 0, "scenario": scenario, "combats": [], "source": "none"}
        run_id = self._resolve_observatory_run(scenario, sim_run_id)
        try:
            q = sb.table("observatory_combat_results").select("*")
            if run_id:
                q = q.eq("sim_run_id", run_id)
            if rnd_int is not None:
                q = q.eq("round_num", rnd_int)
            try:
                res = q.order("id", desc=False).execute()
            except Exception:
                res = q.execute()
            return {"round": rnd_int or 0, "scenario": scenario, "sim_run_id": run_id, "combats": res.data or [], "source": "db"}
        except Exception as e:
            logger.debug("observatory_combat_results query failed: %s", e)
            return {"round": rnd_int or 0, "scenario": scenario, "combats": [], "source": "error", "error": str(e)}

    def _observatory_global_series(self, scenario: str, sim_run_id: Optional[str] = None):
        """Return global_state_per_round for all rounds of a run/scenario.

        Payload: {"rounds": [{round_num, oil_price, stock_index,
        bond_yield, gold_price}, ...], ... }.
        """
        sb = _supabase_or_none()
        if sb is None:
            return {"rounds": [], "source": "none", "scenario": scenario}
        run_id = self._resolve_observatory_run(scenario, sim_run_id)
        if not run_id:
            return {"rounds": [], "source": "no_run", "scenario": scenario}
        try:
            res = (
                sb.table("global_state_per_round")
                .select("round_num, oil_price, stock_index, bond_yield, gold_price, notes")
                .eq("sim_run_id", run_id)
                .order("round_num", desc=False)
                .execute()
            )
            # Supabase numeric -> strings; cast to float for UI
            rounds = []
            for row in (res.data or []):
                rounds.append({
                    "round_num": row["round_num"],
                    "oil_price": float(row["oil_price"]),
                    "stock_index": float(row["stock_index"]),
                    "bond_yield": float(row["bond_yield"]),
                    "gold_price": float(row["gold_price"]),
                    "notes": row.get("notes"),
                })
            return {"rounds": rounds, "source": "db", "scenario": scenario}
        except Exception as e:
            logger.debug("observatory_global_series query failed: %s", e)
            return {"rounds": [], "source": "error", "error": str(e), "scenario": scenario}

    def _observatory_blockades(self, round_num: str, scenario: str, sim_run_id: Optional[str] = None):
        """Return active blockades from the `blockades` state table.

        Reads from the canonical `blockades` table (not agent_decisions).
        Architecture fix: V-7 (2026-04-08). F1 (2026-04-12): now scoped to
        the resolved Observatory run instead of a hard-coded default sim id.
        """
        sb = _supabase_or_none()
        if sb is None:
            return {"blockades": [], "source": "none", "scenario": scenario}
        run_id = self._resolve_observatory_run(scenario, sim_run_id)
        if not run_id:
            return {"blockades": [], "source": "no_run", "scenario": scenario}
        try:
            res = sb.table("blockades").select("*") \
                .eq("sim_run_id", run_id) \
                .eq("status", "active").execute()
            blockades = []
            for row in (res.data or []):
                blockades.append({
                    "zone_id": row.get("zone_id", ""),
                    "imposer_country_id": row.get("imposer_country_id", ""),
                    "level": row.get("level", "full"),
                    "status": row.get("status", "active"),
                    "established_round": row.get("established_round"),
                    "notes": row.get("notes", ""),
                })
            return {
                "blockades": blockades,
                "source": "db",
                "scenario": scenario,
                "round": round_num,
            }
        except Exception as e:
            logger.debug("observatory_blockades query failed: %s", e)
            return {"blockades": [], "source": "error", "error": str(e), "scenario": scenario}

    def _observatory_events(self, limit: int, scenario: str, sim_run_id: Optional[str] = None):
        """Return most recent N events from observatory_events for the resolved run."""
        sb = _supabase_or_none()
        if sb is None:
            return {"events": [], "source": "none", "scenario": scenario}
        run_id = self._resolve_observatory_run(scenario, sim_run_id)
        try:
            q = sb.table("observatory_events").select("*")
            if run_id:
                q = q.eq("sim_run_id", run_id)
            res = (
                q.order("created_at", desc=True)
                 .limit(max(1, min(limit, 500)))
                 .execute()
            )
            return {"events": res.data or [], "source": "db", "scenario": scenario, "sim_run_id": run_id}
        except Exception as e:
            logger.debug("observatory_events query failed: %s", e)
            return {"events": [], "source": "error", "error": str(e), "scenario": scenario}

    def _observatory_start(self, body: dict):
        """Start the auto-advance round loop in a background thread."""
        import datetime, threading, asyncio
        if _observatory_runtime["status"] == "running":
            return {"success": False, "reason": "already running", "state": dict(_observatory_runtime)}
        scenario = body.get("scenario", _observatory_runtime["scenario"])
        total_rounds = int(body.get("total_rounds", _observatory_runtime["total_rounds"]))
        run_name = (body.get("run_name") or "").strip() or (
            "Run " + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        )
        speed_sec = _observatory_runtime.get("speed_sec", 15)
        start_round = int(_observatory_runtime.get("current_round", 0)) + 1

        # Clear any previous stop flag
        from engine.agents.full_round_runner import set_global_stop
        set_global_stop(False)

        _observatory_runtime["status"] = "running"
        _observatory_runtime["scenario"] = scenario
        _observatory_runtime["total_rounds"] = total_rounds
        _observatory_runtime["run_name"] = run_name
        _observatory_runtime["started_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        _observatory_runtime["_pause_event"] = threading.Event()
        _observatory_runtime["_pause_event"].set()  # start unpaused
        _observatory_runtime["_stop"] = False

        def _loop():
            from engine.agents.full_round_runner import run_full_round
            for rnum in range(start_round, total_rounds + 1):
                if _observatory_runtime.get("_stop"):
                    break
                # Wait while paused
                _observatory_runtime["_pause_event"].wait()
                if _observatory_runtime.get("_stop"):
                    break
                logger.info("[observatory] starting round %d", rnum)
                try:
                    result = asyncio.run(run_full_round(scenario, rnum))
                    _observatory_runtime["current_round"] = rnum
                    _observatory_runtime["last_event_at"] = datetime.datetime.utcnow().isoformat()
                    logger.info("[observatory] round %d done: %s", rnum, result.get("summary", ""))
                except Exception as e:
                    logger.exception("[observatory] round %d failed: %s", rnum, e)
                    _observatory_runtime["status"] = "error"
                    _observatory_runtime["error"] = str(e)
                    return
                # Auto-advance delay (respects pause)
                slept = 0
                while slept < _observatory_runtime.get("speed_sec", speed_sec):
                    if _observatory_runtime.get("_stop"):
                        break
                    _observatory_runtime["_pause_event"].wait()
                    import time as _t
                    _t.sleep(1)
                    slept += 1
            if _observatory_runtime["status"] == "running":
                _observatory_runtime["status"] = "finished"

        t = threading.Thread(target=_loop, daemon=True, name="observatory-loop")
        t.start()
        _observatory_runtime["_thread"] = t
        logger.info("Observatory loop started: scenario=%s, rounds=%d-%d", scenario, start_round, total_rounds)
        return {"success": True, "state": {k: v for k, v in _observatory_runtime.items() if not k.startswith("_")}}

    def _observatory_pause(self, body: dict):
        status = _observatory_runtime["status"]
        if status in ("running",):
            # Set "pausing" — the loop thread will see the cleared event
            # after the current round finishes and switch to "paused".
            _observatory_runtime["status"] = "paused"
            ev = _observatory_runtime.get("_pause_event")
            if ev:
                ev.clear()
            logger.info("Observatory paused (was %s). Takes effect after current round/agent.", status)
        elif status in ("paused",):
            logger.info("Observatory already paused.")
        else:
            logger.info("Observatory pause ignored (status=%s).", status)
        return {"success": True, "state": {k: v for k, v in _observatory_runtime.items() if not k.startswith("_")}}

    def _observatory_resume(self, body: dict):
        status = _observatory_runtime["status"]
        if status in ("paused",):
            _observatory_runtime["status"] = "running"
            ev = _observatory_runtime.get("_pause_event")
            if ev:
                ev.set()
            logger.info("Observatory resumed (was %s).", status)
        else:
            logger.info("Observatory resume ignored (status=%s).", status)
        return {"success": True, "state": {k: v for k, v in _observatory_runtime.items() if not k.startswith("_")}}

    def _observatory_stop(self, body: dict):
        """Hard stop — sets global flag so pending agents skip, loop exits."""
        from engine.agents.full_round_runner import set_global_stop
        set_global_stop(True)
        _observatory_runtime["_stop"] = True
        _observatory_runtime["status"] = "finished"
        # Unblock pause event so the loop thread can exit
        ev = _observatory_runtime.get("_pause_event")
        if ev:
            ev.set()
        logger.info("Observatory STOPPED (global flag set).")
        return {"success": True, "state": {k: v for k, v in _observatory_runtime.items() if not k.startswith("_")}}

    def _observatory_rewind(self, body: dict):
        to_round = int(body.get("to_round", 0))
        _observatory_runtime["current_round"] = max(0, to_round)
        logger.info("Observatory rewind to round=%d (stub).", to_round)
        # TODO: set read-cursor; do not mutate DB
        return {"success": True, "stub": True, "state": dict(_observatory_runtime)}

    def _observatory_reset(self, body: dict):
        """Wipe all round data for a scenario and restart from round 0 (fresh Template snapshot).

        Deletes: round_states (>=1), unit_states_per_round (>=1), country_states_per_round (>=1),
                 observatory_events (all), agent_decisions (all for scenario), agent_memories (all).
        Preserves: round 0 snapshot (canonical Template default).
        """
        try:
            from engine.services.supabase import get_client
        except Exception as e:
            return {"success": False, "error": f"supabase unavailable: {e}"}

        scenario_code = body.get("scenario", _observatory_runtime.get("scenario", "start_one"))

        # Stop any running loop first
        _observatory_runtime["_stop"] = True
        ev = _observatory_runtime.get("_pause_event")
        if ev: ev.set()  # wake up paused loops so they can check _stop
        _observatory_runtime["status"] = "idle"
        _observatory_runtime["current_round"] = 0
        _observatory_runtime["started_at"] = None
        _observatory_runtime["run_name"] = None
        _observatory_runtime["last_event_at"] = None

        client = get_client()
        # Resolve scenario_id
        scen = client.table("sim_scenarios").select("id").eq("code", scenario_code).limit(1).execute()
        if not scen.data:
            return {"success": False, "error": f"scenario '{scenario_code}' not found"}
        scenario_id = scen.data[0]["id"]

        wipe_counts = {}
        try:
            # Delete in order respecting FKs
            r = client.table("round_states").delete().eq("scenario_id", scenario_id).gte("round_num", 1).execute()
            wipe_counts["round_states"] = len(r.data or [])
            r = client.table("unit_states_per_round").delete().eq("scenario_id", scenario_id).gte("round_num", 1).execute()
            wipe_counts["unit_states"] = len(r.data or [])
            r = client.table("country_states_per_round").delete().eq("scenario_id", scenario_id).gte("round_num", 1).execute()
            wipe_counts["country_states"] = len(r.data or [])
            r = client.table("observatory_events").delete().eq("scenario_id", scenario_id).execute()
            wipe_counts["events"] = len(r.data or [])
            r = client.table("observatory_combat_results").delete().eq("scenario_id", scenario_id).execute()
            wipe_counts["combats"] = len(r.data or [])
            r = client.table("agent_decisions").delete().eq("scenario_id", scenario_id).execute()
            wipe_counts["agent_decisions"] = len(r.data or [])
            r = client.table("agent_memories").delete().eq("scenario_id", scenario_id).execute()
            wipe_counts["agent_memories"] = len(r.data or [])
        except Exception as e:
            logger.exception("reset: wipe failed")
            return {"success": False, "error": f"wipe failed: {e}", "partial": wipe_counts}

        logger.info("Observatory RESET scenario=%s wiped=%s", scenario_code, wipe_counts)
        return {
            "success": True,
            "scenario": scenario_code,
            "wiped": wipe_counts,
            "state": {k: v for k, v in _observatory_runtime.items() if not k.startswith("_")},
        }

    def _observatory_speed(self, body: dict):
        try:
            sec = int(body.get("speed_sec", 15))
        except (TypeError, ValueError):
            sec = 15
        _observatory_runtime["speed_sec"] = max(1, min(sec, 120))
        logger.info("Observatory speed=%ds", _observatory_runtime["speed_sec"])
        return {"success": True, "state": dict(_observatory_runtime)}

    def _serve_html(self):
        """Serve the main HTML page."""
        html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
        if os.path.exists(html_path):
            with open(html_path) as f:
                content = f.read()
        else:
            content = FALLBACK_HTML

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode())

    def log_message(self, format, *args):
        """Suppress default request logging."""
        pass


FALLBACK_HTML = """<!DOCTYPE html>
<html><body><h1>Test Interface</h1><p>templates/index.html not found. Using fallback.</p></body></html>"""


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    os.chdir(os.path.dirname(__file__))
    server = HTTPServer(("localhost", port), TestInterfaceHandler)
    print(f"Test Interface running at http://localhost:{port}")
    print(f"API endpoints:")
    print(f"  GET  /api/roles                    — list all roles")
    print(f"  POST /api/agent/init               — initialize agent")
    print(f"  POST /api/agent/chat               — chat with agent")
    print(f"  POST /api/agent/decide              — test decision (budget/tariffs/sanctions/opec/military/covert/political/active_loop)")
    print(f"  POST /api/agent/bilateral           — bilateral conversation between two agents")
    print(f"  GET  /api/agent/state?role_id=X     — get cognitive state")
    print(f"  GET  /api/agent/history?role_id=X   — get state history")
    print(f"  POST /api/sim/round                 — run single round (persist:bool)")
    print(f"  POST /api/sim/run                   — run full unmanned simulation (persist:bool)")
    print(f"  POST /api/sim/cleanup               — delete old test sim_runs")
    print(f"  GET  /observatory                   — Observatory monitoring UI")
    print(f"  GET  /api/observatory/state         — runtime state")
    print(f"  GET  /api/observatory/units?round=N — units at round N")
    print(f"  GET  /api/observatory/countries?round=N — country states at round N")
    print(f"  GET  /api/observatory/events?limit=N — event log (most recent)")
    print(f"  GET  /api/observatory/combats?round=N — combat log for round N")
    print(f"  POST /api/observatory/start|pause|resume|rewind|speed — controls (stub)")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
