"""Nuclear Decision Chain Orchestrator — CONTRACT_NUCLEAR_CHAIN v1.0.

Manages the 4-phase state machine for nuclear actions:

  INITIATE → AUTHORIZE → ALERT + INTERCEPT → RESOLVE

This is the first multi-step chained decision in the SIM. Unlike all
other actions (single decision → engine resolves), nuclear involves
multiple actors across multiple phases with timer-gated transitions.

In unmanned mode, ``run_unmanned()`` executes the full chain synchronously:
AI officers are called immediately for authorization + interception
decisions, no timer waits.

Usage::

    from engine.orchestrators.nuclear_chain import NuclearChainOrchestrator

    orch = NuclearChainOrchestrator()
    result = orch.run_unmanned(decision_payload, sim_run_id, round_num)
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from engine.services.supabase import get_client
from engine.services.nuclear_validator import (
    validate_nuclear_test,
    validate_nuclear_launch,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Authorization role mapping (CONTRACT_NUCLEAR_CHAIN v1.0 §8)
# ---------------------------------------------------------------------------

#: Multi-role countries: HoS initiates, these 2 authorize.
AUTHORIZATION_ROLES: dict[str, tuple[str, str]] = {
    "columbia": ("shield", "shadow"),
    "cathay": ("rampart", "abacus"),
    "sarmatia": ("ironhand", "compass"),
    "ruthenia": ("bulwark", "broker"),
    "persia": ("anvil", "dawn"),
}

#: All other countries use 1 AI Officer (single-HoS = 2-way auth).

# Nuclear test success probabilities (CARD_FORMULAS D.7)
TEST_SUCCESS_BELOW_T2 = 0.70
TEST_SUCCESS_T2_PLUS = 0.95

# Nuclear launch constants (CARD_FORMULAS D.6)
NUCLEAR_HIT_PROB = 0.80
TARGET_AD_INTERCEPT_PROB = 0.50  # target's own AD
T3_INTERCEPT_PROB_PER_AD = 0.25  # other T3+ countries
MILITARY_DESTROY_PCT = 0.50
GDP_DAMAGE_BASE_PCT = 0.30
SALVO_GLOBAL_STABILITY = -1.5
SALVO_TARGET_STABILITY = -2.5
LEADER_DEATH_PROB = 1.0 / 6.0

# Nuclear site hexes (CARD_FORMULAS D.6)
NUCLEAR_SITE_HEXES: dict[str, tuple[int, int]] = {
    "persia": (7, 13),
    "choson": (3, 18),
}

# Test stability/GDP costs (CARD_FORMULAS D.7)
TEST_STABILITY_UNDERGROUND = -0.2
TEST_STABILITY_SURFACE_GLOBAL = -0.4
TEST_STABILITY_SURFACE_ADJACENT = -0.6
TEST_GDP_SURFACE = -0.05  # -5% own GDP
TEST_SUPPORT_BOOST = 5.0


class NuclearChainOrchestrator:
    """Manages the 4-phase nuclear decision chain."""

    def __init__(self):
        self.client = get_client()

    # ------------------------------------------------------------------
    # Phase 1: Initiation
    # ------------------------------------------------------------------

    def initiate(
        self,
        decision: dict,
        sim_run_id: str,
        round_num: int,
        initiator_role_id: str = "hos",
    ) -> dict:
        """Validate and create a nuclear_actions record.

        Returns ``{action_id, status, errors}`` or raises on DB failure.
        """
        action_type = decision.get("action_type")
        country_code = decision.get("country_code")

        # Load world state for validation
        units, cs, zones = self._load_validation_context(sim_run_id, round_num)

        # Validate
        if action_type == "nuclear_test":
            report = validate_nuclear_test(decision, units, cs, zones)
        elif action_type == "launch_missile" and (decision.get("changes") or {}).get("warhead") == "nuclear":
            report = validate_nuclear_launch(decision, units, cs, zones)
        else:
            return {"action_id": None, "status": "rejected",
                    "errors": [f"Invalid nuclear action_type: {action_type}"]}

        if not report["valid"]:
            return {"action_id": None, "status": "rejected", "errors": report["errors"]}

        normalized = report["normalized"]

        # Determine authorizers
        auth1, auth2 = self._get_authorizers(country_code)

        # Load timer config from sim_runs.schedule
        schedule = {}
        try:
            run = self.client.table("sim_runs").select("schedule").eq("id", sim_run_id).limit(1).execute()
            schedule = (run.data[0].get("schedule") or {}) if run.data else {}
        except Exception:
            pass
        auth_timer = schedule.get("nuclear_auth_timer_sec", 600)

        # Create nuclear_actions record
        row = {
            "sim_run_id": sim_run_id,
            "round_num": round_num,
            "action_type": "nuclear_test" if action_type == "nuclear_test" else "nuclear_launch",
            "country_code": country_code,
            "initiator_role_id": initiator_role_id,
            "payload": normalized,
            "status": "awaiting_authorization",
            "authorizer_1_role": auth1,
            "authorizer_2_role": auth2,
            "timer_started_at": datetime.now(timezone.utc).isoformat(),
            "timer_duration_sec": auth_timer,
        }
        res = self.client.table("nuclear_actions").insert(row).execute()
        action_id = res.data[0]["id"]

        logger.info("[nuclear] initiated %s by %s — action_id=%s, authorizers=%s/%s",
                     row["action_type"], country_code, action_id, auth1, auth2)

        return {"action_id": action_id, "status": "awaiting_authorization", "errors": []}

    # ------------------------------------------------------------------
    # Phase 2: Authorization
    # ------------------------------------------------------------------

    def submit_authorization(
        self,
        action_id: str,
        role_id: str,
        confirm: bool,
        rationale: str = "",
    ) -> dict:
        """Submit one authorizer's response. Returns updated status."""
        action = self._get_action(action_id)
        if action["status"] != "awaiting_authorization":
            return {"status": action["status"], "note": "not awaiting authorization"}

        response = "confirm" if confirm else "reject"
        update: dict = {}

        if action["authorizer_1_role"] == role_id or (action["authorizer_1_role"] == "ai_officer" and action["authorizer_1_response"] is None):
            update["authorizer_1_response"] = response
            update["authorizer_1_rationale"] = rationale
        elif action["authorizer_2_role"] == role_id or (action["authorizer_2_role"] == "ai_officer" and action["authorizer_2_response"] is None and action.get("authorizer_1_response") is not None):
            update["authorizer_2_response"] = response
            update["authorizer_2_rationale"] = rationale
        else:
            # This authorizer isn't expected — could be 2nd AI officer call
            if action["authorizer_2_role"] and action["authorizer_2_response"] is None:
                update["authorizer_2_response"] = response
                update["authorizer_2_rationale"] = rationale
            else:
                return {"status": action["status"], "note": f"unexpected role_id {role_id}"}

        # Check for rejection
        if response == "reject":
            update["status"] = "cancelled"
            self.client.table("nuclear_actions").update(update).eq("id", action_id).execute()
            logger.info("[nuclear] CANCELLED by %s (rejected)", role_id)
            return {"status": "cancelled", "rejected_by": role_id}

        self.client.table("nuclear_actions").update(update).eq("id", action_id).execute()

        # Refresh and check if all confirmed
        action = self._get_action(action_id)
        auth1_ok = action.get("authorizer_1_response") == "confirm"
        auth2_ok = action.get("authorizer_2_response") == "confirm" or action.get("authorizer_2_role") is None

        if auth1_ok and auth2_ok:
            if action["action_type"] == "nuclear_launch":
                # Nuclear launch: transition to interception phase with timer + auto-pause sim
                sim_run_id = action["sim_run_id"]
                schedule = {}
                try:
                    run = self.client.table("sim_runs").select("schedule").eq("id", sim_run_id).limit(1).execute()
                    schedule = (run.data[0].get("schedule") or {}) if run.data else {}
                except Exception:
                    pass
                flight_timer = schedule.get("nuclear_flight_timer_sec", 600)

                self.client.table("nuclear_actions").update({
                    "status": "awaiting_interception",
                    "timer_started_at": datetime.now(timezone.utc).isoformat(),
                    "timer_duration_sec": flight_timer,
                }).eq("id", action_id).execute()

                # Auto-pause the sim (Phase 3 = dramatic moment)
                try:
                    self.client.table("sim_runs").update({
                        "status": "paused",
                    }).eq("id", sim_run_id).execute()
                    logger.info("[nuclear] SIM auto-paused for nuclear launch flight phase")
                except Exception as e:
                    logger.warning("[nuclear] auto-pause failed: %s", e)

                # Generate classified artefacts for T3+ countries
                self._generate_launch_artefacts(action)

                logger.info("[nuclear] AUTHORIZED → awaiting_interception (flight timer=%ds)", flight_timer)
                return {"status": "awaiting_interception"}
            else:
                self.client.table("nuclear_actions").update({"status": "authorized"}).eq("id", action_id).execute()
                logger.info("[nuclear] AUTHORIZED — all authorizers confirmed")
                return {"status": "authorized"}

        return {"status": "awaiting_authorization", "confirmed_so_far": [role_id]}

    # ------------------------------------------------------------------
    # Phase 3: Interception (launches only)
    # ------------------------------------------------------------------

    def submit_interception(
        self,
        action_id: str,
        country_code: str,
        intercept: bool,
        rationale: str = "",
    ) -> dict:
        """Submit one T3+ country's interception decision."""
        action = self._get_action(action_id)
        if action["status"] != "awaiting_interception":
            return {"status": action["status"]}

        responses = action.get("interception_responses") or {}
        responses[country_code] = {"intercept": intercept, "rationale": rationale}
        self.client.table("nuclear_actions").update(
            {"interception_responses": responses}
        ).eq("id", action_id).execute()

        return {"status": "awaiting_interception", "recorded": country_code}

    # ------------------------------------------------------------------
    # Phase 4: Resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        action_id: str,
        precomputed_rolls: dict | None = None,
    ) -> dict:
        """Run engine calculations and persist outcomes."""
        action = self._get_action(action_id)
        atype = action["action_type"]
        payload = action["payload"]
        sim_run_id = action["sim_run_id"]
        round_num = action["round_num"]
        cc = action["country_code"]

        if atype == "nuclear_test":
            result = self._resolve_test(action, precomputed_rolls)
        else:
            result = self._resolve_launch(action, precomputed_rolls)

        # Update nuclear_actions record
        self.client.table("nuclear_actions").update({
            "status": "resolved",
            "resolution": result,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", action_id).execute()

        # Write audit JSONB
        audit_col = "nuclear_test_decision" if atype == "nuclear_test" else "nuclear_launch_decision"
        try:
            self.client.table("countries").update({
                audit_col: {"payload": payload, "resolution": result},
            }).eq("sim_run_id", sim_run_id) \
              .eq("id", cc).execute()
        except Exception as e:
            logger.debug("nuclear audit write failed: %s", e)

        # Write observatory events (only on successful resolution, not cancelled)
        if result.get("outcome") not in ("rejected", "cancelled"):
            self._write_events(action, result)

        # Auto-resume sim after nuclear launch resolution (was paused in Phase 3)
        if atype == "nuclear_launch":
            try:
                self.client.table("sim_runs").update({
                    "status": "active",
                }).eq("id", sim_run_id).eq("status", "paused").execute()
                logger.info("[nuclear] SIM auto-resumed after launch resolution")
            except Exception as e:
                logger.warning("[nuclear] auto-resume failed: %s", e)

        logger.info("[nuclear] RESOLVED %s for %s — %s", atype, cc, result.get("outcome"))
        return result

    # ------------------------------------------------------------------
    # Unmanned full chain (synchronous, AI calls inline)
    # ------------------------------------------------------------------

    def run_unmanned(
        self,
        decision: dict,
        sim_run_id: str,
        round_num: int,
        initiator_role_id: str = "hos",
        precomputed_rolls: dict | None = None,
    ) -> dict:
        """Execute the full 4-phase chain synchronously.

        AI officers are called immediately for authorization +
        interception. No timer waits. Returns the resolution dict.
        """
        # Phase 1: Initiate
        init_result = self.initiate(decision, sim_run_id, round_num, initiator_role_id)
        if init_result["status"] == "rejected":
            return {"outcome": "rejected", "errors": init_result["errors"]}
        action_id = init_result["action_id"]

        # Phase 2: Authorization (AI officers)
        action = self._get_action(action_id)
        auth_roles = [action["authorizer_1_role"]]
        if action.get("authorizer_2_role"):
            auth_roles.append(action["authorizer_2_role"])

        for role in auth_roles:
            confirm, rationale = self._ai_authorize(action, role)
            result = self.submit_authorization(action_id, role, confirm, rationale)
            if result.get("status") == "cancelled":
                return {"outcome": "cancelled", "cancelled_by": role, "rationale": rationale}

        # Refresh status
        action = self._get_action(action_id)
        if action["status"] != "authorized":
            return {"outcome": "authorization_incomplete", "status": action["status"]}

        # Phase 3: Interception (launches only)
        if action["action_type"] == "nuclear_launch":
            self.client.table("nuclear_actions").update(
                {"status": "awaiting_interception"}
            ).eq("id", action_id).execute()

            launcher_cc = action["country_code"]
            t3_countries = self._get_interceptor_countries(sim_run_id, round_num, exclude=launcher_cc)
            for t3_cc in t3_countries:
                intercept, rationale = self._ai_intercept(action, t3_cc)
                self.submit_interception(action_id, t3_cc, intercept, rationale)

        # Phase 4: Resolve
        return self.resolve(action_id, precomputed_rolls)

    # ------------------------------------------------------------------
    # Artefact generation
    # ------------------------------------------------------------------

    def _generate_launch_artefacts(self, action: dict) -> None:
        """Insert classified artefacts for T3+ countries' HoS and military roles on launch authorization."""
        import uuid

        sim_run_id = action["sim_run_id"]
        round_num = action["round_num"]
        launcher = action["country_code"]
        payload = action.get("payload") or {}
        missiles = payload.get("changes", {}).get("missiles", [])
        targets_desc = ", ".join(
            f"({m.get('target_global_row')},{m.get('target_global_col')})" for m in missiles
        )

        try:
            t3_countries = self._get_interceptor_countries(sim_run_id, round_num, exclude=launcher)
            if not t3_countries:
                return

            from engine.config.position_actions import has_position
            roles_rows = self.client.table("roles").select(
                "id, country_id, positions, position_type"
            ).eq("sim_run_id", sim_run_id).eq("status", "active").in_(
                "country_id", t3_countries
            ).execute().data or []

            target_role_ids = [
                r["id"] for r in roles_rows
                if has_position(r, "head_of_state") or has_position(r, "military")
            ]

            if not target_role_ids:
                return

            artefacts = []
            for rid in target_role_ids:
                artefacts.append({
                    "id": f"nuke_launch_{launcher}_{round_num}_{rid}_{uuid.uuid4().hex[:8]}",
                    "sim_run_id": sim_run_id,
                    "role_id": rid,
                    "artefact_type": "classified_report",
                    "title": "NUCLEAR LAUNCH ALERT",
                    "subtitle": f"Ballistic missile launch detected from {launcher.upper()}",
                    "classification": "TOP SECRET — FLASH",
                    "from_entity": "Global Monitoring Systems",
                    "date_label": f"Round {round_num}",
                    "content_html": (
                        f"<p>Global early warning systems have detected a <strong>nuclear ballistic missile launch</strong> "
                        f"originating from <strong>{launcher.upper()}</strong>.</p>"
                        f"<p><strong>Missiles launched:</strong> {len(missiles)}</p>"
                        f"<p><strong>Target coordinates:</strong> {targets_desc}</p>"
                        f"<p>Interception window is now open. Your air defense systems "
                        f"can attempt interception (25% success per AD unit).</p>"
                        f"<p class='text-red-500'><strong>IMMEDIATE ACTION REQUIRED</strong></p>"
                    ),
                    "round_delivered": round_num,
                    "is_read": False,
                })

            if artefacts:
                self.client.table("artefacts").insert(artefacts).execute()
                logger.info("[nuclear] Generated %d launch artefacts for T3+ countries", len(artefacts))

        except Exception as e:
            logger.warning("Nuclear launch artefact generation failed: %s", e)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_action(self, action_id: str) -> dict:
        res = self.client.table("nuclear_actions").select("*").eq("id", action_id).limit(1).execute()
        if not res.data:
            raise ValueError(f"nuclear_action {action_id} not found")
        return res.data[0]

    def _get_authorizers(self, country_code: str) -> tuple[str, Optional[str]]:
        """Return (auth1_role, auth2_role) for the country."""
        if country_code in AUTHORIZATION_ROLES:
            return AUTHORIZATION_ROLES[country_code]
        # Single-HoS country: 1 AI Officer
        return ("ai_officer", None)

    def _load_validation_context(self, sim_run_id: str, round_num: int):
        """Load units, country_state, zones for validator calls."""
        units_rows = self.client.table("deployments").select("*") \
            .eq("sim_run_id", sim_run_id).execute().data or []
        # Live table — no dedup needed, one row per unit
        units: dict[str, dict] = {}
        for r in units_rows:
            uid = r.get("unit_id")
            if uid:
                units[uid] = r

        cs_rows = self.client.table("countries").select("*") \
            .eq("sim_run_id", sim_run_id).execute().data or []
        cs: dict[str, dict] = {}
        for r in cs_rows:
            cc = r.get("id")
            if cc and cc not in cs:
                cs[cc] = r

        # Zones from unit positions (simplified — matches M2/M3 pattern)
        zones: dict[tuple[int, int], dict] = {}
        for u in units.values():
            r, c = u.get("global_row"), u.get("global_col")
            if r is not None and c is not None:
                zones.setdefault((r, c), {"type": "land", "owner": u.get("country_id")})

        return units, cs, zones

    def _get_interceptor_countries(self, sim_run_id: str, round_num: int, exclude: str) -> list[str]:
        """Return country_codes with nuclear_level >= 2 and confirmed (eligible to intercept)."""
        cs_rows = self.client.table("countries").select(
            "id,nuclear_level,nuclear_confirmed"
        ).eq("sim_run_id", sim_run_id).execute().data or []
        return [
            r["id"] for r in cs_rows
            if int(r.get("nuclear_level", 0) or 0) >= 2
            and r.get("nuclear_confirmed")
            and r["id"] != exclude
        ]

    # ------------------------------------------------------------------
    # AI Officer calls (one-off LLM decisions)
    # ------------------------------------------------------------------

    def _ai_authorize(self, action: dict, role: str) -> tuple[bool, str]:
        """Ask an AI officer whether to authorize. Returns (confirm, rationale)."""
        try:
            from engine.services.llm import call_llm
            from engine.config.settings import LLMUseCase

            payload = action["payload"]
            atype = action["action_type"]
            cc = action["country_code"]

            prompt = (
                f"You are {role} of {cc.upper()}, reviewing a nuclear authorization request.\n\n"
                f"PROPOSED ACTION: {atype}\n"
                f"DETAILS: {payload}\n\n"
                f"As a senior official, do you CONFIRM or REJECT this nuclear action?\n"
                f"Consider: strategic necessity, risks, international consequences.\n\n"
                f"Respond with JSON ONLY:\n"
                f'{{"confirm": true|false, "rationale": "string >= 30 chars"}}'
            )

            from engine.agents.decisions import _parse_json
            raw = asyncio.run(call_llm(
                use_case=LLMUseCase.AGENT_DECISION,
                messages=[{"role": "user", "content": prompt}],
                system="You are a senior military/intelligence official deciding on nuclear authorization. Be concise.",
                max_tokens=200,
                temperature=0.3,
            ))
            parsed = _parse_json(raw.text)
            if parsed and isinstance(parsed.get("confirm"), bool):
                return parsed["confirm"], parsed.get("rationale", "AI officer decision")
        except Exception as e:
            logger.warning("[nuclear] AI authorize call failed: %s — defaulting to confirm", e)

        # Fallback: confirm (in unmanned mode, don't block the chain)
        return True, f"AI officer {role} auto-confirms nuclear authorization (fallback)"

    def _ai_intercept(self, action: dict, country_code: str) -> tuple[bool, str]:
        """Ask a T3+ country's AI whether to intercept. Returns (intercept, rationale)."""
        try:
            from engine.services.llm import call_llm
            from engine.config.settings import LLMUseCase

            launcher = action["country_code"]
            payload = action["payload"]
            missiles = payload.get("changes", {}).get("missiles", [])
            targets = [f"({m['target_global_row']},{m['target_global_col']})" for m in missiles]

            prompt = (
                f"You are the head of state of {country_code.upper()}, a T3 nuclear power.\n\n"
                f"NUCLEAR LAUNCH DETECTED:\n"
                f"  Launcher: {launcher.upper()}\n"
                f"  Missiles: {len(missiles)}\n"
                f"  Targets: {', '.join(targets)}\n\n"
                f"You can attempt INTERCEPTION with your AD units (25% success per unit).\n"
                f"WARNING: Intercepting reveals your capability and sides you against {launcher}.\n\n"
                f"Do you attempt interception? Respond with JSON ONLY:\n"
                f'{{"intercept": true|false, "rationale": "string >= 30 chars"}}'
            )

            from engine.agents.decisions import _parse_json
            raw = asyncio.run(call_llm(
                use_case=LLMUseCase.AGENT_DECISION,
                messages=[{"role": "user", "content": prompt}],
                system="You are a nuclear power deciding whether to intercept incoming missiles. Be concise.",
                max_tokens=200,
                temperature=0.3,
            ))
            parsed = _parse_json(raw.text)
            if parsed and isinstance(parsed.get("intercept"), bool):
                return parsed["intercept"], parsed.get("rationale", "AI decision")
        except Exception as e:
            logger.warning("[nuclear] AI intercept call failed for %s: %s — defaulting to intercept", country_code, e)

        # Fallback: always intercept
        return True, f"{country_code} auto-intercepts (fallback)"

    # ------------------------------------------------------------------
    # Engine resolution
    # ------------------------------------------------------------------

    def _resolve_test(self, action: dict, precomputed_rolls: dict | None = None) -> dict:
        """Phase 4 for nuclear_test: success roll + stability + GDP + confirmation."""
        payload = action["payload"]
        cc = action["country_code"]
        sim_run_id = action["sim_run_id"]
        round_num = action["round_num"]
        test_type = payload["changes"]["test_type"]

        # Get nuclear level
        cs = self.client.table("countries").select("nuclear_level") \
            .eq("sim_run_id", sim_run_id).eq("id", cc) \
            .limit(1).execute().data
        nuc_level = int((cs[0] if cs else {}).get("nuclear_level", 1) or 1)

        # Success probability
        success_prob = TEST_SUCCESS_T2_PLUS if nuc_level >= 2 else TEST_SUCCESS_BELOW_T2
        pre = precomputed_rolls or {}
        roll = pre.get("test_success_roll", random.random())
        success = roll < success_prob

        result: dict = {
            "outcome": "test_success" if success else "test_failure",
            "test_type": test_type,
            "success_probability": success_prob,
            "success_roll": round(roll, 4),
            "success": success,
            "nuclear_level": nuc_level,
            "stability_effects": {},
            "gdp_effects": {},
            "support_effects": {cc: TEST_SUPPORT_BOOST},
        }

        # Stability effects
        if test_type == "underground":
            result["stability_effects"]["global"] = TEST_STABILITY_UNDERGROUND
            result["alert_scope"] = "t3_only"
        else:
            result["stability_effects"]["global"] = TEST_STABILITY_SURFACE_GLOBAL
            result["stability_effects"]["adjacent_countries"] = TEST_STABILITY_SURFACE_ADJACENT
            result["gdp_effects"][cc] = TEST_GDP_SURFACE
            result["alert_scope"] = "all_countries"

        # On success: confirm tier
        if success:
            try:
                self.client.table("countries").update({
                    "nuclear_confirmed": True,
                }).eq("sim_run_id", sim_run_id) \
                  .eq("id", cc).execute()
                result["tier_confirmed"] = True
            except Exception as e:
                logger.warning("nuclear_confirmed update failed: %s", e)
                result["tier_confirmed"] = False

        return result

    def _resolve_launch(self, action: dict, precomputed_rolls: dict | None = None) -> dict:
        """Phase 4 for nuclear_launch: interception → hit → damage."""
        payload = action["payload"]
        cc = action["country_code"]
        sim_run_id = action["sim_run_id"]
        round_num = action["round_num"]
        missiles = payload["changes"]["missiles"]
        interception_responses = action.get("interception_responses") or {}

        pre = precomputed_rolls or {}

        # Load target country AD counts (for auto-interception)
        units_rows = self.client.table("deployments").select(
            "unit_id,country_id,unit_type,unit_status,global_row,global_col"
        ).eq("sim_run_id", sim_run_id).execute().data or []

        # Determine target countries
        target_hexes = [(m["target_global_row"], m["target_global_col"]) for m in missiles]
        target_countries = set()
        for u in units_rows:
            if u.get("global_row") is not None:
                for tr, tc in target_hexes:
                    if u["global_row"] == tr and u.get("global_col") == tc and u["country_id"] != cc:
                        target_countries.add(u["country_id"])

        # Count AD per intercepting entity
        ad_by_country: dict[str, int] = {}
        for u in units_rows:
            if (u.get("unit_type") or "").lower() == "air_defense" and (u.get("unit_status") or "").lower() == "active":
                c = u["country_id"]
                ad_by_country[c] = ad_by_country.get(c, 0) + 1

        # --- INTERCEPTION ---
        surviving_missiles = list(range(len(missiles)))
        interception_log: list[dict] = []

        # Target country auto-interception (50% per AD)
        for tgt_cc in target_countries:
            ad_count = ad_by_country.get(tgt_cc, 0)
            pre_tgt = (pre.get("interception_rolls") or {}).get("target_ad") or []
            for i in range(ad_count):
                if not surviving_missiles:
                    break
                roll = pre_tgt[i] if i < len(pre_tgt) else random.random()
                if roll < TARGET_AD_INTERCEPT_PROB:
                    destroyed_idx = surviving_missiles.pop(0)
                    interception_log.append({
                        "interceptor": tgt_cc, "type": "target_ad",
                        "ad_roll": round(roll, 4), "success": True,
                        "missile_destroyed": missiles[destroyed_idx]["missile_unit_code"],
                    })

        # T3+ voluntary interception (25% per AD)
        for t3_cc, resp in interception_responses.items():
            if not resp.get("intercept"):
                continue
            ad_count = ad_by_country.get(t3_cc, 0)
            pre_t3 = (pre.get("interception_rolls") or {}).get(t3_cc) or []
            for i in range(ad_count):
                if not surviving_missiles:
                    break
                roll = pre_t3[i] if i < len(pre_t3) else random.random()
                if roll < T3_INTERCEPT_PROB_PER_AD:
                    destroyed_idx = surviving_missiles.pop(0)
                    interception_log.append({
                        "interceptor": t3_cc, "type": "t3_voluntary",
                        "ad_roll": round(roll, 4), "success": True,
                        "missile_destroyed": missiles[destroyed_idx]["missile_unit_code"],
                    })

        # --- HIT ROLLS for surviving missiles ---
        hit_rolls_pre = pre.get("hit_rolls") or []
        hits: list[dict] = []
        misses: list[dict] = []

        for idx in surviving_missiles:
            m = missiles[idx]
            roll = hit_rolls_pre[len(hits) + len(misses)] if (len(hits) + len(misses)) < len(hit_rolls_pre) else random.random()
            if roll < NUCLEAR_HIT_PROB:
                hits.append({"missile": m["missile_unit_code"],
                             "target": (m["target_global_row"], m["target_global_col"]),
                             "hit_roll": round(roll, 4)})
            else:
                misses.append({"missile": m["missile_unit_code"],
                               "target": (m["target_global_row"], m["target_global_col"]),
                               "hit_roll": round(roll, 4)})

        # --- DAMAGE per hit ---
        damage_log: list[dict] = []
        destroyed_units: list[str] = []
        for h in hits:
            tr, tc = h["target"]
            # Military on target hex: 50% destroyed
            hex_units = [u for u in units_rows
                         if u.get("global_row") == tr and u.get("global_col") == tc
                         and (u.get("unit_status") or "").lower() == "active"]
            n_destroy = max(1, int(len(hex_units) * MILITARY_DESTROY_PCT))
            random.shuffle(hex_units)
            for u in hex_units[:n_destroy]:
                destroyed_units.append(u["unit_id"])
            # Nuclear site check
            site_destroyed = False
            for site_cc, (sr, sc) in NUCLEAR_SITE_HEXES.items():
                if (tr, tc) == (sr, sc):
                    site_destroyed = True
            damage_log.append({
                "target_hex": [tr, tc],
                "military_destroyed": n_destroy,
                "nuclear_site_destroyed": site_destroyed,
            })

        # --- Mark all launched missiles as consumed ---
        consumed_missiles = [m["missile_unit_code"] for m in missiles]

        # --- T3 SALVO AGGREGATE ---
        is_salvo = len(missiles) >= 3 and len(hits) >= 1
        salvo_effects: dict = {}
        leader_death_roll = None
        if is_salvo:
            salvo_effects["global_stability"] = SALVO_GLOBAL_STABILITY
            salvo_effects["target_stability"] = SALVO_TARGET_STABILITY
            ld_roll = pre.get("leader_death_roll", random.random())
            leader_death_roll = round(ld_roll, 4)
            salvo_effects["leader_death_roll"] = leader_death_roll
            salvo_effects["leader_killed"] = ld_roll < LEADER_DEATH_PROB

        # --- Apply unit losses to DB (delete from deployments) ---
        try:
            for uid in destroyed_units + consumed_missiles:
                self.client.table("deployments").delete() \
                    .eq("sim_run_id", sim_run_id) \
                    .eq("unit_id", uid).execute()
        except Exception as e:
            logger.warning("nuclear unit loss persistence failed: %s", e)

        result = {
            "outcome": "nuclear_launch_resolved",
            "missiles_launched": len(missiles),
            "missiles_intercepted": len(interception_log),
            "missiles_surviving": len(surviving_missiles),
            "hits": len(hits),
            "misses": len(misses),
            "interception_log": interception_log,
            "hit_details": hits,
            "miss_details": misses,
            "damage_log": damage_log,
            "destroyed_units": destroyed_units,
            "consumed_missiles": consumed_missiles,
            "salvo_effects": salvo_effects,
            "alert_scope": "all_countries",
        }
        return result

    # ------------------------------------------------------------------
    # Event writing
    # ------------------------------------------------------------------

    def _write_events(self, action: dict, result: dict) -> None:
        """Write observatory_events for the resolved nuclear action."""
        sim_run_id = action["sim_run_id"]
        round_num = action["round_num"]
        cc = action["country_code"]
        atype = action["action_type"]

        # Look up scenario_id
        scenario_id = None
        try:
            run = self.client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
            if run.data and run.data[0].get("scenario_id"):
                scenario_id = run.data[0]["scenario_id"]
        except Exception:
            pass

        if not scenario_id:
            logger.debug("nuclear event write skipped — no scenario_id for run %s", sim_run_id)
            return

        base = {
            "sim_run_id": sim_run_id,
            "scenario_id": scenario_id,
            "round_num": round_num,
            "country_code": cc,
        }

        events = []

        if atype == "nuclear_test":
            test_label = "SURFACE" if result.get("test_type") == "surface" else "UNDERGROUND"
            outcome = "SUCCESSFUL" if result.get("success") else "FAILED"
            events.append({
                **base,
                "event_type": "nuclear_test",
                "category": "military",
                "summary": f"☢ {cc.upper()} conducts {test_label} nuclear test — {outcome}",
                "payload": result,
            })
        else:
            launched = result.get("missiles_launched", 0)
            intercepted = result.get("missiles_intercepted", 0)
            hits = result.get("hits", 0)
            parts = [f"☢ NUCLEAR STRIKE — {cc.upper()} launches {launched} missile{'s' if launched != 1 else ''}"]
            if intercepted > 0:
                parts.append(f"{intercepted} intercepted")
            if hits > 0:
                # Get target country names from hit_details
                target_hexes = [h.get("target") for h in result.get("hit_details", []) if h.get("target")]
                target_countries = set()
                for th in target_hexes:
                    from engine.config.map_config import hex_owner
                    owner = hex_owner(th[0], th[1])
                    if owner != "sea":
                        target_countries.add(owner.upper())
                targets_str = ", ".join(sorted(target_countries)) if target_countries else "unknown"
                parts.append(f"{hits} hit{'s' if hits != 1 else ''} on {targets_str}")
            else:
                parts.append("ALL INTERCEPTED — no impacts")
            events.append({
                **base,
                "event_type": "nuclear_launch",
                "category": "military",
                "summary": " — ".join(parts),
                "payload": result,
            })

        if events:
            try:
                self.client.table("observatory_events").insert(events).execute()
            except Exception as e:
                logger.warning("nuclear event write failed: %s", e)

        # Write combat results row
        try:
            combat_row = {
                "sim_run_id": sim_run_id,
                "scenario_id": scenario_id,
                "round_num": round_num,
                "combat_type": atype,
                "attacker_country": cc,
                "defender_country": ", ".join(sorted({h["target_hex"][0] for h in result.get("damage_log", [])} if result.get("damage_log") else set())) if atype == "nuclear_launch" else cc,
                "location_global_row": action["payload"]["changes"].get("target_global_row") or (result.get("hit_details", [{}])[0].get("target", [None, None])[0] if result.get("hit_details") else None),
                "location_global_col": action["payload"]["changes"].get("target_global_col") or (result.get("hit_details", [{}])[0].get("target", [None, None])[1] if result.get("hit_details") else None),
                "attacker_units": [m["missile_unit_code"] for m in action["payload"]["changes"].get("missiles", [])] if atype == "nuclear_launch" else [],
                "defender_units": result.get("destroyed_units", []),
                "attacker_rolls": result.get("hit_details", []),
                "defender_rolls": result.get("interception_log", []),
                "attacker_losses": result.get("consumed_missiles", []),
                "defender_losses": result.get("destroyed_units", []),
                "modifier_breakdown": result.get("salvo_effects") or result.get("stability_effects") or [],
                "narrative": result.get("outcome", ""),
            }
            self.client.table("observatory_combat_results").insert(combat_row).execute()
        except Exception as e:
            logger.warning("nuclear combat_results write failed: %s", e)
