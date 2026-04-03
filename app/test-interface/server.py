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
    print(f"  GET  /api/agent/state?role_id=X     — get cognitive state")
    print(f"  GET  /api/agent/history?role_id=X   — get state history")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
