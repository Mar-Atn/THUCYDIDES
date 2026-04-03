"""AI Participant Test Interface — development tool.

Web-based chat + cognitive block inspector for testing AI agents.
NOT part of the main app. Separate standalone server.

Usage: cd app && PYTHONPATH=. python3 test-interface/server.py
"""

import asyncio
import json
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import io

from engine.agents.leader import LeaderAgent
from engine.agents.profiles import load_all_roles, load_heads_of_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("test-interface")

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
            super().do_GET()
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

        logger.info("Starting full SIM: %d rounds, %d ticks, NOUS=%d",
                     num_rounds, active_loop_ticks, nous_intensity)

        try:
            result = asyncio.run(run_full_sim(
                num_rounds=num_rounds,
                active_loop_ticks=active_loop_ticks,
                nous_intensity=nous_intensity,
            ))
            return {
                "success": True,
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

        logger.info("Running single round %d", round_num)

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
            ))
            return {
                "success": True,
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
    print(f"  POST /api/sim/round                 — run single round")
    print(f"  POST /api/sim/run                   — run full unmanned simulation")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
