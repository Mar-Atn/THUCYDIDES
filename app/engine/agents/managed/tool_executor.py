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

    Binds country_code, sim_run_id, scenario_code, round_num, and
    role_id at creation so the agent doesn't need to pass them.
    """

    def __init__(
        self,
        country_code: str,
        scenario_code: str,
        sim_run_id: str,
        round_num: int = 1,
        role_id: str = "",
    ):
        self.country_code = country_code
        self.scenario_code = scenario_code
        self.sim_run_id = sim_run_id
        self.round_num = round_num
        self.role_id = role_id or f"{country_code}_hos"
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

        # --- New Phase 1B tools (9-16) ---

        if tool_name == "read_notes":
            return self._read_notes(key=tool_input.get("key"))

        if tool_name == "get_country_info":
            return self._get_country_info(
                country_code=tool_input.get("country_code", ""),
            )

        if tool_name == "get_hex_info":
            return agent_tools.get_hex_info(
                row=tool_input.get("row", 1),
                col=tool_input.get("col", 1),
                scope=tool_input.get("scope", "global"),
                scenario_code=sc,
                round_num=rn,
            )

        if tool_name == "get_organizations":
            return agent_tools.get_organization_memberships(cc)

        if tool_name == "get_my_artefacts":
            return self._get_my_artefacts(
                unread_only=tool_input.get("unread_only", False),
            )

        if tool_name == "get_action_rules":
            return self._get_action_rules(
                action_type=tool_input.get("action_type"),
            )

        if tool_name == "request_meeting":
            return self._request_meeting(
                target_country=tool_input.get("target_country", ""),
                agenda=tool_input.get("agenda", ""),
                intent_note=tool_input.get("intent_note", ""),
            )

        if tool_name == "respond_to_invitation":
            return self._respond_to_invitation(
                invitation_id=tool_input.get("invitation_id", ""),
                decision=tool_input.get("decision", "decline"),
                intent_note=tool_input.get("intent_note", ""),
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
        """Submit a game action — validates, records, and EXECUTES through the action dispatcher.

        Flow:
        1. Validate action_type against known schemas
        2. Validate payload with Pydantic model
        3. Record in agent_decisions (audit trail)
        4. Execute through dispatch_action (real game state change)
        """
        from engine.agents.action_schemas import ACTION_TYPE_TO_MODEL
        try:
            # Check sim_run status and phase restrictions
            client = get_client()
            run = client.table("sim_runs").select("status,current_phase").eq("id", self.sim_run_id).limit(1).execute()
            if run.data:
                sim_status = run.data[0].get("status", "")
                current_phase = run.data[0].get("current_phase", "")

                # Block ALL actions during pre_start/setup
                if sim_status in ("setup", "pre_start"):
                    return {"success": False, "validation_status": "rejected",
                            "validation_notes": f"Simulation is in '{sim_status}' state. Actions are only allowed during active rounds. Use observation tools and write_notes to prepare."}

                # Phase-aware action restrictions (M5 SPEC D10 + World Model Section 7)
                PHASE_B_ONLY_ACTIONS = {"set_budget", "set_tariffs", "set_sanctions", "set_opec", "move_units"}
                action_type_check = action.get("action_type", "")

                # Phase A: block batch decisions + move_units (solicited at Phase B)
                if sim_status == "active" and current_phase == "A" and action_type_check in PHASE_B_ONLY_ACTIONS:
                    return {"success": False, "validation_status": "rejected",
                            "validation_notes": f"'{action_type_check}' is submitted during the Phase B solicitation window, not during Phase A. Focus on diplomacy, communication, and strategic actions during Phase A."}

                # Phase B / processing / inter_round: ONLY batch decisions + move_units allowed
                if current_phase in ("B", "inter_round") and action_type_check not in PHASE_B_ONLY_ACTIONS:
                    return {"success": False, "validation_status": "rejected",
                            "validation_notes": f"Phase B is for batch decisions and troop movements only. '{action_type_check}' is not available during Phase B. Wait for the next round's Phase A."}

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

            # Record in agent_decisions (audit trail)
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
            decision_id = (ins.data or [{}])[0].get("id")

            # EXECUTE through action dispatcher — real game state change
            from engine.services.action_dispatcher import dispatch_action
            dispatch_payload = {
                **payload_dict,
                "action_type": action_type,
                "role_id": self.role_id,
                "country_code": self.country_code,
            }

            # Field normalization: Pydantic schema names → dispatcher field names
            # Combat: target_global_row/col → target_row/col
            if "target_global_row" in dispatch_payload and "target_row" not in dispatch_payload:
                dispatch_payload["target_row"] = dispatch_payload["target_global_row"]
            if "target_global_col" in dispatch_payload and "target_col" not in dispatch_payload:
                dispatch_payload["target_col"] = dispatch_payload["target_global_col"]
            # Missile: launcher_unit_code (singular) → attacker_unit_codes (list)
            if "launcher_unit_code" in dispatch_payload and "attacker_unit_codes" not in dispatch_payload:
                dispatch_payload["attacker_unit_codes"] = [dispatch_payload["launcher_unit_code"]]
            # Nuclear authorize: authorize → confirm
            if action_type == "nuclear_authorize" and "authorize" in dispatch_payload and "confirm" not in dispatch_payload:
                dispatch_payload["confirm"] = dispatch_payload["authorize"]
            # move_units: extract moves from changes.moves to top-level
            if action_type == "move_units" and "moves" not in dispatch_payload:
                changes = dispatch_payload.get("changes") or {}
                if isinstance(changes, dict) and "moves" in changes:
                    dispatch_payload["moves"] = changes["moves"]

            result = dispatch_action(
                sim_run_id=self.sim_run_id,
                round_num=self.round_num,
                action=dispatch_payload,
            )

            # Update agent_decisions with dispatch result
            dispatch_success = result.get("success", False)
            try:
                client.table("agent_decisions").update({
                    "validation_status": "executed" if dispatch_success else "dispatch_failed",
                    "validation_notes": result.get("narrative", ""),
                }).eq("id", decision_id).execute()
            except Exception:
                pass  # Non-critical — audit update

            return {
                "success": dispatch_success,
                "action_id": decision_id,
                "action_type": action_type,
                "validation_status": "executed" if dispatch_success else "dispatch_failed",
                "result": result.get("narrative", ""),
            }
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

    # --- New Phase 1B helper methods ---

    def _read_notes(self, key: str | None = None) -> dict:
        """Read a specific memory note by key, or list all keys."""
        try:
            client = get_client()
            if key:
                # Read specific note
                result = (
                    client.table("agent_memories")
                    .select("content,round_num,updated_at,memory_key")
                    .eq("sim_run_id", self.sim_run_id)
                    .eq("country_code", self.country_code)
                    .eq("memory_key", key)
                    .execute()
                )
                if not result.data:
                    return {"exists": False, "memory_key": key, "content": None}
                row = result.data[0]
                return {
                    "exists": True,
                    "memory_key": key,
                    "content": row.get("content"),
                    "round_num": row.get("round_num"),
                    "updated_at": row.get("updated_at"),
                }
            else:
                # List all keys with previews
                result = (
                    client.table("agent_memories")
                    .select("memory_key,content,round_num,updated_at")
                    .eq("sim_run_id", self.sim_run_id)
                    .eq("country_code", self.country_code)
                    .order("updated_at", desc=True)
                    .execute()
                )
                rows = result.data or []
                return {
                    "country": self.country_code,
                    "memory_count": len(rows),
                    "memories": [
                        {
                            "memory_key": r["memory_key"],
                            "round_num": r.get("round_num"),
                            "updated_at": r.get("updated_at"),
                            "preview": (r.get("content") or "")[:200],
                        }
                        for r in rows
                    ],
                }
        except Exception as e:
            logger.exception("read_notes failed")
            return {"error": str(e)}

    def _get_country_info(self, country_code: str) -> dict:
        """Public info about any specific country (GDP, regime, wars, etc.)."""
        if not country_code:
            return {"error": "country_code is required"}
        sc = self.scenario_code
        rn = self.round_num
        try:
            strategic = agent_tools.get_strategic_context(country_code, sc, rn)
            economic = agent_tools.get_economic_state(country_code, sc, rn)
            return {
                "country": country_code,
                "strategic": strategic,
                "economic": economic,
            }
        except Exception as e:
            logger.exception("get_country_info failed for %s", country_code)
            return {"error": str(e)}

    def _get_my_artefacts(self, unread_only: bool = False) -> dict:
        """Query artefacts table for this role's intel/cables."""
        try:
            client = get_client()
            q = (
                client.table("artefacts")
                .select("*")
                .eq("sim_run_id", self.sim_run_id)
                .eq("role_id", self.role_id)
                .order("round_delivered", desc=True)
            )
            if unread_only:
                q = q.eq("is_read", False)
            result = q.execute()
            rows = result.data or []

            artefacts = [
                {
                    "id": a.get("id"),
                    "artefact_type": a.get("artefact_type"),
                    "classification": a.get("classification"),
                    "title": a.get("title"),
                    "subtitle": a.get("subtitle"),
                    "from_entity": a.get("from_entity"),
                    "content_html": a.get("content_html"),
                    "round_delivered": a.get("round_delivered"),
                    "is_read": a.get("is_read"),
                }
                for a in rows
            ]

            # Mark as read
            unread_ids = [a["id"] for a in rows if not a.get("is_read")]
            if unread_ids:
                for aid in unread_ids:
                    try:
                        client.table("artefacts").update({"is_read": True}).eq("id", aid).execute()
                    except Exception:
                        pass  # Best-effort mark-as-read

            return {
                "role_id": self.role_id,
                "artefact_count": len(artefacts),
                "artefacts": artefacts,
            }
        except Exception as e:
            logger.exception("get_my_artefacts failed")
            return {"error": str(e), "artefacts": []}

    def _get_action_rules(self, action_type: str | None = None) -> dict:
        """Return structured info about action types from Pydantic models.

        Also includes current sim phase context so the agent knows
        what's available NOW vs what requires an active round.
        """
        from engine.agents.action_schemas import ACTION_TYPE_TO_MODEL

        # Get current sim phase for context
        phase_context = {}
        try:
            client = get_client()
            run = client.table("sim_runs").select("status,current_phase,current_round").eq("id", self.sim_run_id).limit(1).execute()
            if run.data:
                r = run.data[0]
                sim_status = r.get("status", "")
                actions_allowed = sim_status == "active"
                current_phase = r.get("current_phase", "")
                if actions_allowed and current_phase == "A":
                    phase_note = (
                        "Phase A — all actions available EXCEPT batch decisions (set_budget, set_tariffs, "
                        "set_sanctions, set_opec) and move_units. These will be solicited at the start of Phase B."
                    )
                elif actions_allowed:
                    phase_note = "Actions available. Submit batch decisions or troop movements as requested."
                else:
                    phase_note = "PRE-START: Only observation tools and write_notes available. Actions start once the round begins."
                phase_context = {
                    "sim_status": sim_status,
                    "current_phase": current_phase,
                    "current_round": r.get("current_round"),
                    "actions_allowed": actions_allowed,
                    "batch_actions_phase_b_only": ["set_budget", "set_tariffs", "set_sanctions", "set_opec", "move_units"],
                    "phase_note": phase_note,
                }
        except Exception:
            pass

        if not action_type:
            result = {
                "available_actions": sorted(ACTION_TYPE_TO_MODEL.keys()),
                "hint": "Call get_action_rules with a specific action_type to see required fields.",
            }
            if phase_context:
                result["phase_context"] = phase_context
            return result

        if action_type not in ACTION_TYPE_TO_MODEL:
            return {
                "error": f"Unknown action_type '{action_type}'",
                "available_actions": sorted(ACTION_TYPE_TO_MODEL.keys()),
            }

        model_cls = ACTION_TYPE_TO_MODEL[action_type]
        schema = model_cls.model_json_schema()
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        fields = []
        for field_name, field_info in properties.items():
            entry: dict = {
                "name": field_name,
                "type": field_info.get("type", field_info.get("anyOf", "object")),
                "required": field_name in required,
            }
            if "description" in field_info:
                entry["description"] = field_info["description"]
            if "enum" in field_info:
                entry["allowed_values"] = field_info["enum"]
            if "const" in field_info:
                entry["fixed_value"] = field_info["const"]
            if "default" in field_info:
                entry["default"] = field_info["default"]
            if "minimum" in field_info:
                entry["minimum"] = field_info["minimum"]
            if "maximum" in field_info:
                entry["maximum"] = field_info["maximum"]
            # Pydantic v2 uses ge/le via exclusiveMinimum/exclusiveMaximum or directly
            if "exclusiveMinimum" in field_info:
                entry["exclusive_minimum"] = field_info["exclusiveMinimum"]
            if "exclusiveMaximum" in field_info:
                entry["exclusive_maximum"] = field_info["exclusiveMaximum"]
            fields.append(entry)

        docstring = model_cls.__doc__ or ""

        return {
            "action_type": action_type,
            "description": docstring.strip(),
            "fields": fields,
        }

    def _request_meeting(self, target_country: str, agenda: str, intent_note: str = "") -> dict:
        """Create a meeting invitation to another country's leader.

        The intent_note is stored on the invitation and transferred to
        meeting metadata when the counterpart accepts. The conversation
        avatar uses it as its only guide for the meeting.
        """
        if not target_country:
            return {"error": "target_country is required"}
        if not agenda:
            return {"error": "agenda is required"}

        try:
            from datetime import datetime, timezone, timedelta
            client = get_client()

            # Block meetings outside Phase A
            run = client.table("sim_runs").select("status,current_phase").eq("id", self.sim_run_id).limit(1).execute()
            if run.data:
                _status = run.data[0].get("status", "")
                _phase = run.data[0].get("current_phase", "")
                if _status in ("setup", "pre_start"):
                    return {"success": False, "error": "Simulation hasn't started yet. Meetings are available once the round begins."}
                if _phase in ("B", "inter_round"):
                    return {"success": False, "error": "Meetings are only available during Phase A. Phase B is for batch decisions and troop movements."}

            # Check limit: max 2 active invitations per role
            now_iso = datetime.now(timezone.utc).isoformat()
            active = (
                client.table("meeting_invitations")
                .select("id")
                .eq("sim_run_id", self.sim_run_id)
                .eq("inviter_role_id", self.role_id)
                .eq("status", "pending")
                .gte("expires_at", now_iso)
                .execute()
                .data or []
            )
            if len(active) >= 2:
                return {
                    "success": False,
                    "narrative": "You already have 2 active invitations. Wait for them to expire or be answered.",
                }

            # Look up the HoS role_id for target country from DB
            target_roles = (
                client.table("roles")
                .select("id,positions")
                .eq("sim_run_id", self.sim_run_id)
                .eq("country_code", target_country)
                .eq("status", "active")
                .execute()
                .data or []
            )
            target_role_id = None
            for r in target_roles:
                positions = r.get("positions") or []
                if "head_of_state" in positions:
                    target_role_id = r["id"]
                    break
            if not target_role_id and target_roles:
                target_role_id = target_roles[0]["id"]  # fallback: first active role
            if not target_role_id:
                return {"success": False, "error": f"No active role found for {target_country}"}

            expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

            # Store inviter's intent_note in responses JSONB for transfer to meeting on acceptance
            responses_init = {"_inviter_intent_note": intent_note} if intent_note else {}
            row = {
                "sim_run_id": self.sim_run_id,
                "invitation_type": "one_on_one",
                "inviter_role_id": self.role_id,
                "inviter_country_code": self.country_code,
                "invitee_role_id": target_role_id,
                "message": agenda[:300],
                "expires_at": expires_at,
                "status": "pending",
                "responses": responses_init,
            }
            result = client.table("meeting_invitations").insert(row).execute()
            inv_id = result.data[0]["id"] if result.data else None

            logger.info(
                "[meeting] %s invited %s (id=%s)",
                self.role_id, target_role_id, inv_id,
            )

            # Enqueue event to invitee so they know about the invitation
            if inv_id and target_role_id:
                try:
                    client.table("agent_event_queue").insert({
                        "sim_run_id": self.sim_run_id,
                        "role_id": target_role_id,
                        "tier": 2,
                        "event_type": "meeting_invitation_received",
                        "message": (
                            f"MEETING INVITATION from {self.country_code.upper()}\n\n"
                            f"{self.country_code.upper()} has invited you to a bilateral meeting.\n"
                            f"Agenda: {agenda}\n"
                            f"Invitation ID: {inv_id}\n\n"
                            f"Use respond_to_invitation with invitation_id='{inv_id}' "
                            f"and decision='accept' or 'decline'."
                        ),
                        "metadata": {
                            "invitation_id": inv_id,
                            "inviter_country": self.country_code,
                            "agenda": agenda[:200],
                        },
                    }).execute()
                    logger.info("[meeting] Enqueued invitation event for %s", target_role_id)
                except Exception as eq_err:
                    logger.warning("Failed to enqueue invitation event: %s", eq_err)

            return {
                "success": True,
                "narrative": f"Meeting invitation sent to {target_country}",
                "invitation_id": inv_id,
            }
        except Exception as e:
            logger.exception("request_meeting failed")
            return {"success": False, "error": str(e)}

    def _respond_to_invitation(self, invitation_id: str, decision: str, intent_note: str = "") -> dict:
        """Accept or decline a meeting invitation.

        When accepting, the intent_note is stored in meeting metadata
        alongside the inviter's intent note (from the invitation).
        The conversation avatar uses these as its only guide.
        """
        if not invitation_id:
            return {"error": "invitation_id is required"}
        if decision not in ("accept", "decline"):
            return {"error": "decision must be 'accept' or 'decline'"}

        try:
            from engine.services.meeting_service import create_meeting
            client = get_client()

            inv_rows = (
                client.table("meeting_invitations")
                .select("*")
                .eq("id", invitation_id)
                .limit(1)
                .execute()
                .data
            )
            if not inv_rows:
                return {"success": False, "narrative": "Invitation not found"}
            inv = inv_rows[0]

            if inv["status"] != "pending":
                return {"success": False, "narrative": "Invitation has expired or already been answered"}

            # Update responses
            responses = inv.get("responses") or {}
            responses[self.role_id] = {"response": decision, "message": ""}
            update_payload: dict = {"responses": responses}

            meeting_id = None
            if decision == "accept":
                # If invitation already has a meeting, don't duplicate
                if inv.get("meeting_id"):
                    return {
                        "success": True,
                        "narrative": "Meeting already exists for this invitation.",
                        "meeting_id": inv["meeting_id"],
                    }

                inviter_role_id = inv.get("inviter_role_id", "")
                inviter_country = inv.get("inviter_country_code", "")

                meeting = create_meeting(
                    sim_run_id=self.sim_run_id,
                    invitation_id=invitation_id,
                    participant_a_role_id=inviter_role_id,
                    participant_a_country=inviter_country,
                    participant_b_role_id=self.role_id,
                    participant_b_country=self.country_code,
                    agenda=inv.get("message"),
                    round_num=self.round_num,
                )
                if not meeting.get("id"):
                    return {"success": False, "narrative": "Accepted, but failed to create meeting channel."}
                meeting_id = meeting["id"]
                update_payload["status"] = "accepted"
                update_payload["meeting_id"] = meeting_id

                # Store intent notes in meeting metadata (SPEC 4.2)
                # Inviter's intent from invitation, accepter's intent from this call
                from engine.services.meeting_service import update_meeting_metadata
                intent_metadata = {}
                inviter_intent = (inv.get("responses") or {}).get("_inviter_intent_note", "")
                if inviter_intent:
                    intent_metadata["intent_note_a"] = inviter_intent
                if intent_note:
                    intent_metadata["intent_note_b"] = intent_note
                if intent_metadata:
                    update_meeting_metadata(meeting_id, intent_metadata)

                # Set AI participant(s) to IN_MEETING (SPEC: busy during meeting)
                from engine.agents.managed.event_dispatcher import get_dispatcher, IN_MEETING
                _dispatcher = get_dispatcher(self.sim_run_id)
                if _dispatcher:
                    for _rid in [inviter_role_id, self.role_id]:
                        if _rid in _dispatcher.agents:
                            _dispatcher.set_agent_state(_rid, IN_MEETING)
            else:
                update_payload["status"] = "rejected"

            client.table("meeting_invitations").update(update_payload).eq("id", invitation_id).execute()

            # Enqueue meeting_started events to both participants
            if meeting_id:
                inviter_role_id = inv.get("inviter_role_id", "")
                for notify_role in [inviter_role_id, self.role_id]:
                    if notify_role:
                        try:
                            client.table("agent_event_queue").insert({
                                "sim_run_id": self.sim_run_id,
                                "role_id": notify_role,
                                "tier": 2,
                                "event_type": "meeting_started",
                                "message": (
                                    f"MEETING CONFIRMED — your avatar will handle the conversation.\n"
                                    f"Agenda: {inv.get('message', 'Bilateral discussion')}\n"
                                    f"Participants: {inv.get('inviter_country_code', '')} and {self.country_code}\n\n"
                                    f"Your Intent Note has been delivered to the avatar. "
                                    f"You will receive the full transcript when the meeting ends. "
                                    f"Do NOT send messages directly — the avatar represents you."
                                ),
                                "metadata": {
                                    "meeting_id": meeting_id,
                                    "invitation_id": invitation_id,
                                },
                            }).execute()
                        except Exception as eq_err:
                            logger.warning("Failed to enqueue meeting_started for %s: %s", notify_role, eq_err)

            label = "accepted" if decision == "accept" else "declined"
            result: dict = {"success": True, "narrative": f"You {label} the meeting invitation."}
            if meeting_id:
                result["meeting_id"] = meeting_id
            return result
        except Exception as e:
            logger.exception("respond_to_invitation failed")
            return {"success": False, "error": str(e)}
