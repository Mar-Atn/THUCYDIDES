"""Phase 2 — Tool executor: maps tool name to Python function, returns JSON.

Dispatches Managed Agent custom_tool_use events to existing tool
implementations in engine/agents/tools.py. Each tool function is bound
with the agent's country_code, scenario_code, and round_num at session
creation time (closure pattern from leader_round.py).
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from engine.agents import tools as agent_tools
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Dispatches tool calls for a specific agent session.

    Binds country_code, sim_run_id, scenario_code, and round_num at
    creation so the agent doesn't need to pass them.
    """

    def __init__(
        self,
        country_code: str,
        scenario_code: str,
        sim_run_id: str,
        round_num: int = 1,
    ):
        self.country_code = country_code
        self.scenario_code = scenario_code
        self.sim_run_id = sim_run_id
        self.round_num = round_num
        self.call_log: list[dict] = []

    def execute(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return JSON string result.

        Args:
            tool_name: Name of the tool (e.g., 'get_my_country').
            tool_input: Input dict from the agent's tool call.

        Returns:
            JSON string of the tool result.
        """
        start = time.time()
        try:
            result = self._dispatch(tool_name, tool_input)
        except Exception as e:
            logger.exception("Tool %s failed", tool_name)
            result = {"error": f"Tool execution failed: {e}"}

        elapsed_ms = int((time.time() - start) * 1000)
        self.call_log.append({
            "tool": tool_name,
            "input": tool_input,
            "elapsed_ms": elapsed_ms,
            "success": "error" not in result,
        })

        logger.info(
            "Tool %s executed in %dms (success=%s)",
            tool_name, elapsed_ms, "error" not in result,
        )
        return json.dumps(result, default=str)

    def _dispatch(self, tool_name: str, tool_input: dict) -> dict:
        """Route tool name to implementation."""
        cc = self.country_code
        sc = self.scenario_code
        rn = self.round_num

        if tool_name == "get_my_country":
            return self._get_my_country()

        if tool_name == "get_all_countries":
            return agent_tools.get_country_codes_list()

        if tool_name == "get_relationships":
            return agent_tools.get_relationships(cc, sc, rn)

        if tool_name == "get_recent_events":
            return self._get_recent_events(
                event_type=tool_input.get("event_type"),
                limit=tool_input.get("limit", 20),
            )

        if tool_name == "get_my_forces":
            return agent_tools.get_my_forces(cc, sc, rn)

        if tool_name == "get_pending_proposals":
            return self._get_pending_proposals()

        if tool_name == "submit_action":
            action = tool_input.get("action", {})
            return self._submit_action(action)

        if tool_name == "write_notes":
            return self._write_notes(
                key=tool_input.get("key", "notes"),
                content=tool_input.get("content", ""),
            )

        # Fallback: check if it matches an existing tool name directly
        direct_tools = {
            "get_my_identity": lambda: agent_tools.get_my_identity(cc),
            "get_strategic_context": lambda: agent_tools.get_strategic_context(cc, sc, rn),
            "get_economic_state": lambda: agent_tools.get_economic_state(cc, sc, rn),
            "get_political_state": lambda: agent_tools.get_political_state(cc, sc, rn),
            "get_tech_state": lambda: agent_tools.get_tech_state(cc, sc, rn),
            "get_template_info": lambda: agent_tools.get_template_info(),
            "get_organization_memberships": lambda: agent_tools.get_organization_memberships(cc),
            "get_hex_info": lambda: agent_tools.get_hex_info(
                row=tool_input.get("row", 1),
                col=tool_input.get("col", 1),
                scope=tool_input.get("scope", "global"),
                scenario_code=sc,
                round_num=rn,
            ),
            "get_enemy_forces": lambda: agent_tools.get_enemy_forces(
                cc, tool_input.get("enemy_country_code", ""), sc, rn,
            ),
            "read_memory": lambda: agent_tools.read_memory(
                cc, sc, tool_input.get("memory_key", ""),
            ),
            "list_my_memories": lambda: agent_tools.list_my_memories(cc, sc),
            "write_memory": lambda: agent_tools.write_memory(
                cc, sc,
                tool_input.get("memory_key", ""),
                tool_input.get("content", ""),
                tool_input.get("round_num", rn),
            ),
            "commit_action": lambda: agent_tools.commit_action(
                cc, sc, tool_input.get("action", {}), rn,
            ),
        }

        if tool_name in direct_tools:
            return direct_tools[tool_name]()

        return {"error": f"Unknown tool: {tool_name}"}

    def _submit_action(self, action: dict) -> dict:
        """Submit a game action directly using sim_run_id (bypasses scenario_code resolution)."""
        from engine.agents.action_schemas import ACTION_TYPE_TO_MODEL
        try:
            action_type = action.get("action_type")
            if not action_type:
                return {"success": False, "validation_status": "rejected",
                        "validation_notes": "missing 'action_type' in payload"}
            if action_type not in ACTION_TYPE_TO_MODEL:
                return {"success": False, "validation_status": "rejected",
                        "validation_notes": f"unknown action_type '{action_type}'. Valid: {sorted(ACTION_TYPE_TO_MODEL.keys())}"}

            model_cls = ACTION_TYPE_TO_MODEL[action_type]
            try:
                validated = model_cls.model_validate(action)
            except Exception as ve:
                return {"success": False, "validation_status": "rejected",
                        "validation_notes": f"schema validation failed: {ve}"}

            payload_dict = validated.model_dump()
            client = get_client()

            # Get scenario_id from the sim_run
            run = client.table("sim_runs").select("scenario_id").eq("id", self.sim_run_id).limit(1).execute()
            scenario_id = run.data[0]["scenario_id"] if run.data else None

            insert_row = {
                "sim_run_id": self.sim_run_id,
                "scenario_id": scenario_id,
                "country_code": self.country_code,
                "action_type": action_type,
                "action_payload": payload_dict,
                "rationale": payload_dict.get("rationale", ""),
                "validation_status": "passed",
                "round_num": self.round_num,
            }
            ins = client.table("agent_decisions").insert(insert_row).execute()
            row = (ins.data or [{}])[0]
            return {"success": True, "action_id": row.get("id"),
                    "action_type": action_type, "validation_status": "passed"}
        except Exception as e:
            logger.exception("submit_action failed")
            return {"success": False, "validation_status": "rejected",
                    "validation_notes": f"internal error: {e}"}

    def _write_notes(self, key: str, content: str) -> dict:
        """Write a memory note directly using sim_run_id."""
        from datetime import datetime, timezone as tz
        try:
            client = get_client()
            # Get scenario_id from the sim_run
            run = client.table("sim_runs").select("scenario_id").eq("id", self.sim_run_id).limit(1).execute()
            scenario_id = run.data[0]["scenario_id"] if run.data else None

            row = {
                "sim_run_id": self.sim_run_id,
                "scenario_id": scenario_id,
                "country_code": self.country_code,
                "memory_key": key,
                "content": content,
                "round_num": self.round_num,
                "updated_at": datetime.now(tz.utc).isoformat(),
            }
            result = client.table("agent_memories").upsert(
                row, on_conflict="sim_run_id,country_code,memory_key"
            ).execute()
            data = (result.data or [{}])[0]
            return {"success": True, "memory_id": data.get("id"),
                    "memory_key": key, "round_num": self.round_num}
        except Exception as e:
            logger.exception("write_notes failed")
            return {"success": False, "error": str(e)}

    def _get_my_country(self) -> dict:
        """Composite: economic + political + strategic + tech in one call."""
        cc = self.country_code
        sc = self.scenario_code
        rn = self.round_num

        economic = agent_tools.get_economic_state(cc, sc, rn)
        political = agent_tools.get_political_state(cc, sc, rn)
        strategic = agent_tools.get_strategic_context(cc, sc, rn)
        tech = agent_tools.get_tech_state(cc, sc, rn)

        return {
            "country": cc,
            "economic": economic,
            "political": political,
            "strategic": strategic,
            "technology": tech,
        }

    def _get_recent_events(
        self,
        event_type: str | None = None,
        limit: int = 20,
    ) -> dict:
        """Query observatory_events for recent events in this sim."""
        try:
            client = get_client()
            q = (
                client.table("observatory_events")
                .select("*")
                .eq("sim_run_id", self.sim_run_id)
                .order("created_at", desc=True)
                .limit(limit)
            )
            if event_type:
                q = q.eq("event_type", event_type)

            result = q.execute()
            events = result.data or []

            return {
                "sim_run_id": self.sim_run_id,
                "round_num": self.round_num,
                "event_count": len(events),
                "events": [
                    {
                        "event_type": e.get("event_type"),
                        "category": e.get("category"),
                        "summary": e.get("summary"),
                        "country_code": e.get("country_code"),
                        "round_num": e.get("round_num"),
                        "created_at": e.get("created_at"),
                        "payload": e.get("payload"),
                    }
                    for e in events
                ],
            }
        except Exception as e:
            logger.exception("get_recent_events failed")
            return {"error": str(e), "events": []}

    def _get_pending_proposals(self) -> dict:
        """Query pending transactions and agreements awaiting response."""
        try:
            client = get_client()

            # All pending actions for this sim_run
            all_pending = (
                client.table("pending_actions")
                .select("*")
                .eq("sim_run_id", self.sim_run_id)
                .eq("status", "pending")
                .execute()
            )
            rows = all_pending.data or []

            # Split into sent (by us) and received (targeting us via target_info)
            sent = []
            received = []
            for p in rows:
                entry = {
                    "id": p.get("id"),
                    "action_type": p.get("action_type"),
                    "country_code": p.get("country_code"),
                    "target_info": p.get("target_info"),
                    "payload": p.get("payload"),
                    "created_at": p.get("created_at"),
                }
                if p.get("country_code") == self.country_code:
                    sent.append(entry)
                elif self.country_code in (p.get("target_info") or ""):
                    received.append(entry)

            return {
                "country": self.country_code,
                "received": received,
                "sent": sent,
                "received_count": len(received),
                "sent_count": len(sent),
            }
        except Exception as e:
            logger.exception("get_pending_proposals failed")
            return {"error": str(e), "received": [], "sent": []}
