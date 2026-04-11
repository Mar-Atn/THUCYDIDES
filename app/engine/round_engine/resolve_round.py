# DEPRECATED (2026-04-06) — being replaced by engines/military.py (unit-level v2) + engines/round_tick.py
# See 3 DETAILED DESIGN/REUNIFICATION_AUDIT_2026-04-06.md. Do not add new logic here.
"""Round resolver — main orchestrator.

Pulls committed ``agent_decisions`` for a scenario+round, applies them
in priority order, writes new per-round snapshots, combat log entries,
and activity events.

Resolution order (per OBSERVATORY_SPEC §Combat Engine):
    1. Diplomatic      (log only)
    2. Movement + mobilization
    3. Ranged strikes  (air, missile)
    4. Ground combat
    5. Naval engagements
    6. R&D increments
    7. Sanctions/tariffs  (upsert to state tables + log events)

NOTE: The table originally named ``combat_results`` already existed in
the DB with a different schema. The Observatory uses
``observatory_combat_results`` instead.
"""

from __future__ import annotations

import logging
from typing import Optional

from engine.config.map_config import (
    global_hex_for_theater_cell,
    is_theater_link_hex,
    theater_for_global_hex,
)
from engine.services.supabase import get_client
from engine.engines.movement import process_movements as movement_process
from engine.round_engine import combat as combat_mod
from engine.round_engine import rd as rd_mod
from engine.services.movement_data import (
    build_units_dict_from_rows,
    load_basing_rights,
    load_global_grid_zones,
)
from engine.services.movement_validator import validate_movement_decision

logger = logging.getLogger(__name__)

# Action categories — determines processing order
ATTACK_ACTIONS = {"declare_attack"}
BOMBARDMENT_ACTIONS = {"naval_bombardment"}
COMMUNICATION_ACTIONS = {
    "public_statement", "call_org_meeting",
    "diplomatic_move",  # legacy — agents may still use this; treat as public_statement
}
MOVEMENT_ACTIONS = {"move_units"}  # CONTRACT_MOVEMENT v1.0 — plural
RD_ACTIONS = {"rd_investment"}
ECONOMIC_ACTIONS = {
    "set_sanction", "set_sanctions", "set_tariff", "set_tariffs",
    "set_budget", "set_opec",
    "impose_sanction", "impose_tariff", "lift_sanction", "lift_tariff",
}
BLOCKADE_ACTIONS = {"declare_blockade"}
COVERT_ACTIONS = {"covert_op"}
NUCLEAR_ACTIONS = {"nuclear_test"}
TRANSACTION_ACTIONS = {"propose_transaction", "propose_agreement"}
NAVAL_ATTACK_ACTIONS = {"attack_naval"}
MARTIAL_LAW_ACTIONS = {"declare_martial_law"}
BASING_RIGHTS_ACTIONS = {"basing_rights"}


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------


def _resolve_scenario_id(client, scenario_code: str) -> str:
    """Accept either a UUID or a scenario ``code`` like 'start_one'."""
    try:
        # If it looks like a UUID (length 36 + hyphens), trust it
        if len(scenario_code) == 36 and scenario_code.count("-") == 4:
            return scenario_code
    except Exception:
        pass
    res = (
        client.table("sim_scenarios")
        .select("id")
        .eq("code", scenario_code)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise ValueError(f"Scenario not found: {scenario_code}")
    return res.data[0]["id"]


def _load_unit_state(
    client, scenario_id: str, round_num: int
) -> dict[str, dict]:
    """Load unit_states_per_round snapshot into a dict keyed by unit_code.

    If no snapshot exists for ``round_num``, falls back to the most
    recent prior round.
    """
    res = (
        client.table("unit_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", round_num)
        .execute()
    )
    rows = res.data or []
    if not rows:
        res = (
            client.table("unit_states_per_round")
            .select("*")
            .eq("scenario_id", scenario_id)
            .lte("round_num", round_num)
            .order("round_num", desc=True)
            .limit(10_000)
            .execute()
        )
        # Group to latest row per unit_code
        latest: dict[str, dict] = {}
        for row in res.data or []:
            uc = row["unit_code"]
            if uc not in latest:
                latest[uc] = row
        return {uc: dict(row) for uc, row in latest.items()}
    return {row["unit_code"]: dict(row) for row in rows}


def _load_country_state(
    client, scenario_id: str, round_num: int
) -> dict[str, dict]:
    """Load country state for this round, falling back to previous round if not yet created."""
    res = (
        client.table("country_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", round_num)
        .execute()
    )
    if res.data:
        return {row["country_code"]: dict(row) for row in res.data}
    # Fall back to previous round (current round snapshot not yet written)
    prev = (
        client.table("country_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", round_num - 1)
        .execute()
    )
    if prev.data:
        logger.info("[resolve] No state for R%d, falling back to R%d (%d rows)",
                     round_num, round_num - 1, len(prev.data))
        return {row["country_code"]: dict(row) for row in prev.data}
    return {}


def _load_decisions(
    client, scenario_id: str, round_num: int
) -> list[dict]:
    """Load committed decisions for this scenario + round (uses new round_num column)."""
    res = (
        client.table("agent_decisions")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", round_num)
        .execute()
    )
    return res.data or []


# ---------------------------------------------------------------------------
# Main resolve_round
# ---------------------------------------------------------------------------


def resolve_round(scenario_code: str, round_num: int) -> dict:
    """Resolve a round end-to-end. Returns a summary dict."""
    client = get_client()
    scenario_id = _resolve_scenario_id(client, scenario_code)

    # Mark round as resolving
    client.table("round_states").upsert(
        {
            "scenario_id": scenario_id,
            "round_num": round_num,
            "status": "resolving",
        },
        on_conflict="scenario_id,round_num",
    ).execute()

    # Load prior state
    prev_round = round_num - 1
    unit_state = _load_unit_state(client, scenario_id, prev_round)
    country_state = _load_country_state(client, scenario_id, prev_round)
    decisions = _load_decisions(client, scenario_id, round_num)

    logger.info(
        "resolve_round: scenario=%s round=%d decisions=%d units=%d countries=%d",
        scenario_code, round_num, len(decisions), len(unit_state), len(country_state),
    )

    events: list[dict] = []
    combats: list[dict] = []
    narratives: list[str] = []
    exchange_txns: list[dict] = []  # collected here, batch-written at end

    # --- 1. Public statements + org meetings (logged, visible to all) ------
    for d in decisions:
        if d["action_type"] in COMMUNICATION_ACTIONS:
            payload = d.get("action_payload") or {}
            content = payload.get("content") or payload.get("agenda") or ""
            events.append({
                "scenario_id": scenario_id,
                "round_num": round_num,
                "event_type": d["action_type"],
                "country_code": d["country_code"],
                "summary": f"{d['country_code']}: {content[:120]}",
                "payload": payload,
            })

    # --- 2. Movement (CONTRACT_MOVEMENT v1.0) -----------------------------
    # Last-submission-wins: collect all move_units decisions per country and
    # use only the LAST one in document order (matches the upsert intent).
    move_decisions_by_country: dict[str, dict] = {}
    for d in decisions:
        if d["action_type"] in MOVEMENT_ACTIONS:
            move_decisions_by_country[d["country_code"]] = d

    if move_decisions_by_country:
        # Lazy-load shared context dicts (zones + basing) once per round
        _zones = load_global_grid_zones()
        _basing = load_basing_rights(client)

        for cc, d in move_decisions_by_country.items():
            payload = d.get("action_payload") or {}
            full_payload = {
                "action_type": "move_units",
                "country_code": cc,
                "round_num": round_num,
                "decision": payload.get("decision", "change"),
                "rationale": payload.get(
                    "rationale",
                    "no rationale provided — placeholder for backward "
                    "compatibility with pre-v1.0 move_units payloads",
                ),
            }
            if "changes" in payload:
                full_payload["changes"] = payload["changes"]

            _units_dict = build_units_dict_from_rows(list(unit_state.values()))
            result = validate_movement_decision(
                full_payload, _units_dict, _zones, _basing,
            )
            if not result["valid"]:
                logger.warning(
                    "[resolve R%d] invalid move_units from %s: %s",
                    round_num, cc, result["errors"],
                )
                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "movement_rejected",
                    "country_code": cc,
                    "summary": (
                        f"{cc} move_units rejected: "
                        f"{result['errors'][0] if result['errors'] else 'invalid'}"
                    ),
                    "payload": {
                        "errors": result["errors"],
                        "original": payload,
                    },
                })
                continue

            normalized = result["normalized"]

            # 1. Always write the per-round audit record (incl. no_change).
            #    The country snapshot for this round is written at the end
            #    of resolve_round; we ensure the row exists by upserting.
            try:
                client.table("country_states_per_round").upsert(
                    {
                        "scenario_id": scenario_id,
                        "round_num": round_num,
                        "country_code": cc,
                        "movement_decision": normalized,
                    },
                    on_conflict="scenario_id,round_num,country_code",
                ).execute()
            except Exception as e:
                logger.warning(
                    "[resolve R%d] movement_decision write failed for %s: %s",
                    round_num, cc, e,
                )

            # 2. On change, mutate unit_state via the engine.
            if normalized["decision"] == "change":
                moves = normalized.get("changes", {}).get("moves", [])
                # Mutate unit_state (the dict resolve_round persists later).
                # The validator's view (_units_dict) was a per-call snapshot,
                # so we run process_movements directly against unit_state.
                apply_results = movement_process(
                    moves, cc, unit_state, _zones,
                )
                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "movement_applied",
                    "country_code": cc,
                    "summary": (
                        f"{cc} move_units applied: {len(moves)} moves"
                    ),
                    "payload": {
                        "moves_count": len(moves),
                        "results": apply_results,
                    },
                })
                logger.info(
                    "[resolve R%d] %s move_units change (%d moves applied)",
                    round_num, cc, len(moves),
                )
            else:
                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "movement_no_change",
                    "country_code": cc,
                    "summary": f"{cc} move_units no_change",
                    "payload": {"rationale": normalized.get("rationale")},
                })
                logger.info(
                    "[resolve R%d] %s move_units no_change (audit persisted)",
                    round_num, cc,
                )

    # --- 3-5. Combat (ranged, ground, naval) ------------------------------
    attacks = [d for d in decisions if d["action_type"] in ATTACK_ACTIONS]
    for d in attacks:
        _process_attack(d, unit_state, scenario_id, round_num, combats, events)

    # --- 6. R&D increments ------------------------------------------------
    for d in decisions:
        if d["action_type"] in RD_ACTIONS:
            cc = d["country_code"]
            payload = d["action_payload"] or {}
            domain = payload.get("domain", "nuclear")
            amount = payload.get("amount", 0)
            if cc not in country_state:
                continue
            country_state[cc], narr = rd_mod.apply_rd_investment(
                country_state[cc], domain, amount
            )
            narratives.append(narr)
            events.append({
                "scenario_id": scenario_id,
                "round_num": round_num,
                "event_type": "rd_investment",
                "country_code": cc,
                "summary": narr,
                "payload": payload,
            })

    # --- 6b. Naval bombardment (CARD_ACTIONS 1.6, 10% per unit) -------------
    for d in decisions:
        if d["action_type"] in BOMBARDMENT_ACTIONS:
            payload = d["action_payload"] or {}
            cc = d["country_code"]
            b_tgt_row = payload.get("target_global_row")
            b_tgt_col = payload.get("target_global_col")
            naval_codes = payload.get("naval_unit_codes") or []

            naval_units = [unit_state[c] for c in naval_codes
                          if c in unit_state and unit_state[c].get("status") != "destroyed"]

            # Find ground defenders on target hex
            ground_targets = [
                u for u in unit_state.values()
                if u.get("global_row") == b_tgt_row and u.get("global_col") == b_tgt_col
                and u.get("country_code") != cc
                and u.get("status") != "destroyed"
                and u.get("unit_type") in ("ground", "armor")
            ]

            destroyed = []
            for nu in naval_units:
                if not ground_targets:
                    break
                if _rng.random() < 0.10:  # 10% per unit per CARD_FORMULAS D.4
                    victim = _rng.choice(ground_targets)
                    destroyed.append(victim["unit_code"])
                    _apply_losses(unit_state, [], [victim["unit_code"]])
                    ground_targets = [g for g in ground_targets if g["unit_code"] != victim["unit_code"]]

            events.append({
                "scenario_id": scenario_id, "round_num": round_num,
                "event_type": "naval_bombardment",
                "country_code": cc,
                "summary": f"{cc} naval bombardment at ({b_tgt_row},{b_tgt_col}): "
                           f"{len(naval_units)} shots, {len(destroyed)} destroyed",
                "payload": {**payload, "destroyed": destroyed},
            })

    # --- 7. Economic actions (sanctions/tariffs/budget/OPEC) ---------------
    # ARCHITECTURE (2026-04-08): Write to DB STATE TABLES so engine reads
    # from canonical state, not from agent_decisions.
    # Flow: Participant -> resolve_round WRITES state table -> engine READS state table.
    from engine.config.settings import Settings
    _sim_run_id = Settings().default_sim_id

    for d in decisions:
        if d["action_type"] not in ECONOMIC_ACTIONS:
            continue
        cc = d["country_code"]
        payload = d.get("action_payload") or {}
        atype = d["action_type"]

        # --- Upsert sanctions state table ---
        if atype in ("set_sanction", "impose_sanction"):
            target = payload.get("target_country", "")
            level = payload.get("level", 1)
            if target:
                try:
                    client.table("sanctions").upsert({
                        "sim_run_id": _sim_run_id,
                        "imposer_country_id": cc,
                        "target_country_id": target,
                        "level": level,
                        "notes": f"Set by {cc} in round {round_num}",
                    }, on_conflict="sim_run_id,imposer_country_id,target_country_id").execute()
                    logger.info("[resolve R%d] %s sanctions on %s -> level %d (state table updated)",
                                round_num, cc, target, level)
                except Exception as e:
                    logger.warning("[resolve R%d] sanctions upsert failed %s->%s: %s",
                                   round_num, cc, target, e)

        elif atype == "lift_sanction":
            target = payload.get("target_country", "")
            if target:
                try:
                    client.table("sanctions").upsert({
                        "sim_run_id": _sim_run_id,
                        "imposer_country_id": cc,
                        "target_country_id": target,
                        "level": 0,
                        "notes": f"Lifted by {cc} in round {round_num}",
                    }, on_conflict="sim_run_id,imposer_country_id,target_country_id").execute()
                    logger.info("[resolve R%d] %s lifts sanctions on %s (state table updated)",
                                round_num, cc, target)
                except Exception as e:
                    logger.warning("[resolve R%d] sanctions lift failed %s->%s: %s",
                                   round_num, cc, target, e)

        # --- set_sanctions (plural): CONTRACT_SANCTIONS v1.0 — validate, persist
        # decision audit, upsert sanctions state table for each (target, level)
        # in the sparse changes.sanctions dict. Levels are signed [-3, +3]:
        # negative levels = evasion support.
        elif atype == "set_sanctions":
            from engine.services.sanction_validator import validate_sanctions_decision

            full_payload = {
                "action_type": "set_sanctions",
                "country_code": cc,
                "round_num": round_num,
                "decision": payload.get("decision", "change"),
                "rationale": payload.get(
                    "rationale",
                    "no rationale provided — placeholder for backward "
                    "compatibility with pre-v1.0 set_sanctions payloads",
                ),
            }
            if "changes" in payload:
                full_payload["changes"] = payload["changes"]

            result = validate_sanctions_decision(full_payload)
            if not result["valid"]:
                logger.warning(
                    "[resolve R%d] invalid set_sanctions from %s: %s",
                    round_num, cc, result["errors"],
                )
                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "sanction_rejected",
                    "country_code": cc,
                    "summary": (
                        f"{cc} sanctions decision rejected: "
                        f"{result['errors'][0] if result['errors'] else 'invalid'}"
                    ),
                    "payload": {
                        "errors": result["errors"],
                        "original": payload,
                    },
                })
                continue

            normalized = result["normalized"]

            # 1. Always write the per-round audit record (incl. no_change)
            try:
                client.table("country_states_per_round").update({
                    "sanction_decision": normalized,
                }).eq("scenario_id", scenario_id) \
                  .eq("round_num", round_num) \
                  .eq("country_code", cc).execute()
            except Exception as e:
                logger.warning(
                    "[resolve R%d] sanction_decision write failed for %s: %s",
                    round_num, cc, e,
                )

            # 2. On change, upsert the sanctions state table for each entry.
            #    Signed levels: negative = evasion support. Carry-forward for
            #    untouched targets is implicit.
            if normalized["decision"] == "change":
                sanctions_dict = normalized.get("changes", {}).get("sanctions", {})
                for target, level in sanctions_dict.items():
                    try:
                        client.table("sanctions").upsert({
                            "sim_run_id": _sim_run_id,
                            "imposer_country_id": cc,
                            "target_country_id": target,
                            "level": int(level),
                            "notes": "",  # CONTRACT_SANCTIONS v1.0 §5: notes cleared
                        }, on_conflict="sim_run_id,imposer_country_id,target_country_id").execute()
                    except Exception as e:
                        logger.warning(
                            "[resolve R%d] set_sanctions upsert failed %s->%s: %s",
                            round_num, cc, target, e,
                        )
                logger.info(
                    "[resolve R%d] %s set_sanctions change (%d targets, audit persisted)",
                    round_num, cc, len(sanctions_dict),
                )
            else:
                logger.info(
                    "[resolve R%d] %s set_sanctions no_change (audit persisted)",
                    round_num, cc,
                )

        # --- Upsert tariffs state table ---
        elif atype in ("set_tariff", "impose_tariff"):
            target = payload.get("target_country", "")
            level = payload.get("level", 1)
            if target:
                try:
                    client.table("tariffs").upsert({
                        "sim_run_id": _sim_run_id,
                        "imposer_country_id": cc,
                        "target_country_id": target,
                        "level": level,
                        "notes": f"Set by {cc} in round {round_num}",
                    }, on_conflict="sim_run_id,imposer_country_id,target_country_id").execute()
                    logger.info("[resolve R%d] %s tariff on %s -> level %d (state table updated)",
                                round_num, cc, target, level)
                except Exception as e:
                    logger.warning("[resolve R%d] tariff upsert failed %s->%s: %s",
                                   round_num, cc, target, e)

        elif atype == "lift_tariff":
            target = payload.get("target_country", "")
            if target:
                try:
                    client.table("tariffs").upsert({
                        "sim_run_id": _sim_run_id,
                        "imposer_country_id": cc,
                        "target_country_id": target,
                        "level": 0,
                        "notes": f"Lifted by {cc} in round {round_num}",
                    }, on_conflict="sim_run_id,imposer_country_id,target_country_id").execute()
                    logger.info("[resolve R%d] %s lifts tariff on %s (state table updated)",
                                round_num, cc, target)
                except Exception as e:
                    logger.warning("[resolve R%d] tariff lift failed %s->%s: %s",
                                   round_num, cc, target, e)

        # --- set_tariffs (plural): CONTRACT_TARIFFS v1.0 — validate, persist
        # decision audit, upsert tariffs state table for each (target, level)
        # in the sparse changes.tariffs dict.
        elif atype == "set_tariffs":
            from engine.services.tariff_validator import validate_tariffs_decision

            full_payload = {
                "action_type": "set_tariffs",
                "country_code": cc,
                "round_num": round_num,
                "decision": payload.get("decision", "change"),
                "rationale": payload.get(
                    "rationale",
                    "no rationale provided — placeholder for backward "
                    "compatibility with pre-v1.0 set_tariffs payloads",
                ),
            }
            if "changes" in payload:
                full_payload["changes"] = payload["changes"]

            result = validate_tariffs_decision(full_payload)
            if not result["valid"]:
                logger.warning(
                    "[resolve R%d] invalid set_tariffs from %s: %s",
                    round_num, cc, result["errors"],
                )
                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "tariff_rejected",
                    "country_code": cc,
                    "summary": (
                        f"{cc} tariff decision rejected: "
                        f"{result['errors'][0] if result['errors'] else 'invalid'}"
                    ),
                    "payload": {
                        "errors": result["errors"],
                        "original": payload,
                    },
                })
                continue

            normalized = result["normalized"]

            # 1. Always write the per-round audit record (incl. no_change)
            try:
                client.table("country_states_per_round").update({
                    "tariff_decision": normalized,
                }).eq("scenario_id", scenario_id) \
                  .eq("round_num", round_num) \
                  .eq("country_code", cc).execute()
            except Exception as e:
                logger.warning(
                    "[resolve R%d] tariff_decision write failed for %s: %s",
                    round_num, cc, e,
                )

            # 2. On change, upsert the tariffs state table for each entry.
            #    Carry-forward for untouched targets is implicit.
            if normalized["decision"] == "change":
                tariffs_dict = normalized.get("changes", {}).get("tariffs", {})
                for target, level in tariffs_dict.items():
                    try:
                        client.table("tariffs").upsert({
                            "sim_run_id": _sim_run_id,
                            "imposer_country_id": cc,
                            "target_country_id": target,
                            "level": int(level),
                            "notes": f"set_tariffs by {cc} in round {round_num}",
                        }, on_conflict="sim_run_id,imposer_country_id,target_country_id").execute()
                    except Exception as e:
                        logger.warning(
                            "[resolve R%d] set_tariffs upsert failed %s->%s: %s",
                            round_num, cc, target, e,
                        )
                logger.info(
                    "[resolve R%d] %s set_tariffs change (%d targets, audit persisted)",
                    round_num, cc, len(tariffs_dict),
                )
            else:
                logger.info(
                    "[resolve R%d] %s set_tariffs no_change (audit persisted)",
                    round_num, cc,
                )

        # --- set_budget: validate via CONTRACT_BUDGET v1.1 validator, then
        # inject the new schema (social_pct, production, research) into the
        # country_state dict so the snapshot writer persists it on this round.
        elif atype == "set_budget":
            from engine.services.budget_validator import validate_budget_decision

            full_payload = {
                "action_type": "set_budget",
                "country_code": cc,
                "round_num": round_num,
                "decision": payload.get("decision", "change"),
                "rationale": payload.get(
                    "rationale",
                    "no rationale provided — legacy format placeholder for "
                    "backward compatibility with pre-v1.1 set_budget payloads",
                ),
            }
            if "changes" in payload:
                full_payload["changes"] = payload["changes"]
            elif full_payload["decision"] == "change":
                # Backward-compat: fields directly on payload (only if they
                # match the new schema). If only legacy fields are present
                # (military_coins/tech_coins), we cannot construct a valid
                # new-schema payload — validation will fail and the decision
                # is logged as rejected. Callers should migrate to v1.1.
                inferred: dict = {}
                for k in ("social_pct", "production", "research"):
                    if k in payload:
                        inferred[k] = payload[k]
                if inferred:
                    full_payload["changes"] = inferred

            result = validate_budget_decision(full_payload)
            if not result["valid"]:
                logger.warning(
                    "[resolve R%d] invalid budget from %s: %s",
                    round_num, cc, result["errors"],
                )
                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "budget_rejected",
                    "country_code": cc,
                    "summary": (
                        f"{cc} budget decision rejected: "
                        f"{result['errors'][0] if result['errors'] else 'invalid'}"
                    ),
                    "payload": {
                        "errors": result["errors"],
                        "original": payload,
                    },
                })
                continue

            normalized = result["normalized"]
            if normalized["decision"] == "no_change":
                # Carry forward last round's budget. country_state[cc] was
                # loaded from prev_round by _load_country_state, so the
                # values are already present and will be persisted by the
                # snapshot writer via _COUNTRY_COLS.
                logger.info(
                    "[resolve R%d] %s budget: no_change (carry forward)",
                    round_num, cc,
                )
            else:
                changes = normalized["changes"]
                if cc in country_state:
                    country_state[cc]["budget_social_pct"] = changes["social_pct"]
                    country_state[cc]["budget_production"] = changes["production"]
                    country_state[cc]["budget_research"] = changes["research"]
                    logger.info(
                        "[resolve R%d] %s budget: social=%.2f prod=%s research=%s",
                        round_num, cc,
                        changes["social_pct"],
                        changes["production"],
                        changes["research"],
                    )

        # --- set_opec: CONTRACT_OPEC v1.0 — validate, persist decision audit,
        # update opec_production column for the actor (OPEC+ members only).
        elif atype == "set_opec":
            from engine.services.opec_validator import validate_opec_decision

            full_payload = {
                "action_type": "set_opec",
                "country_code": cc,
                "round_num": round_num,
                "decision": payload.get("decision", "change"),
                "rationale": payload.get(
                    "rationale",
                    "no rationale provided — placeholder for backward "
                    "compatibility with pre-v1.0 set_opec payloads",
                ),
            }
            if "changes" in payload:
                full_payload["changes"] = payload["changes"]
            elif full_payload["decision"] == "change" and "production_level" in payload:
                # Backward-compat: old payloads had production_level at top level
                full_payload["changes"] = {
                    "production_level": payload["production_level"],
                }

            result = validate_opec_decision(full_payload)
            if not result["valid"]:
                logger.warning(
                    "[resolve R%d] invalid set_opec from %s: %s",
                    round_num, cc, result["errors"],
                )
                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "opec_rejected",
                    "country_code": cc,
                    "summary": (
                        f"{cc} OPEC decision rejected: "
                        f"{result['errors'][0] if result['errors'] else 'invalid'}"
                    ),
                    "payload": {
                        "errors": result["errors"],
                        "original": payload,
                    },
                })
                continue

            normalized = result["normalized"]

            # 1. Always write the per-round audit record (incl. no_change)
            try:
                client.table("country_states_per_round").update({
                    "opec_decision": normalized,
                }).eq("scenario_id", scenario_id) \
                  .eq("round_num", round_num) \
                  .eq("country_code", cc).execute()
            except Exception as e:
                logger.warning(
                    "[resolve R%d] opec_decision write failed for %s: %s",
                    round_num, cc, e,
                )

            # 2. On change, update the live opec_production column.
            #    On no_change, the column carries forward by inaction.
            if normalized["decision"] == "change":
                new_level = normalized["changes"]["production_level"]
                try:
                    client.table("country_states_per_round").update({
                        "opec_production": new_level,
                    }).eq("scenario_id", scenario_id) \
                      .eq("round_num", round_num) \
                      .eq("country_code", cc).execute()
                except Exception as e:
                    logger.warning(
                        "[resolve R%d] opec_production write failed for %s: %s",
                        round_num, cc, e,
                    )
                # Also mirror into country_state dict so the same-round engine
                # tick (if run sequentially) reads the new value.
                if cc in country_state:
                    country_state[cc]["opec_production"] = new_level
                logger.info(
                    "[resolve R%d] %s OPEC change -> %s (audit + live value persisted)",
                    round_num, cc, new_level,
                )
            else:
                logger.info(
                    "[resolve R%d] %s OPEC no_change (audit persisted, live value unchanged)",
                    round_num, cc,
                )

        # Log all economic actions as observatory events
        events.append({
            "scenario_id": scenario_id, "round_num": round_num,
            "event_type": atype,
            "country_code": cc,
            "summary": f"{cc} -> {atype}",
            "payload": payload,
        })

    # --- 8. Blockade declarations (CARD_ACTIONS 1.10) -----------------------
    for d in decisions:
        if d["action_type"] in BLOCKADE_ACTIONS:
            payload = d["action_payload"] or {}
            cc = d["country_code"]
            zone_id = payload.get("zone_id", "")
            action = payload.get("action", "establish")
            level = payload.get("level", "full")

            # Upsert blockade state table (like sanctions/tariffs)
            if action == "lift":
                summary = f"{cc} lifts blockade at {zone_id}"
                try:
                    client.table("blockades").upsert({
                        "sim_run_id": _sim_run_id,
                        "zone_id": zone_id,
                        "imposer_country_id": cc,
                        "status": "lifted",
                        "level": level,
                        "established_round": round_num,
                        "lifted_round": round_num,
                        "notes": f"Lifted by {cc} in round {round_num}",
                    }, on_conflict="sim_run_id,zone_id,imposer_country_id").execute()
                    logger.info("[resolve R%d] %s lifts blockade at %s (state table updated)",
                                round_num, cc, zone_id)
                except Exception as e:
                    logger.warning("[resolve R%d] blockade lift upsert failed %s at %s: %s",
                                   round_num, cc, zone_id, e)
            else:
                summary = f"{cc} {'establishes' if action == 'establish' else action} {level} blockade at {zone_id}"
                try:
                    client.table("blockades").upsert({
                        "sim_run_id": _sim_run_id,
                        "zone_id": zone_id,
                        "imposer_country_id": cc,
                        "status": "active",
                        "level": level,
                        "established_round": round_num,
                        "notes": f"Established by {cc} in round {round_num}",
                    }, on_conflict="sim_run_id,zone_id,imposer_country_id").execute()
                    logger.info("[resolve R%d] %s establishes %s blockade at %s (state table updated)",
                                round_num, cc, level, zone_id)
                except Exception as e:
                    logger.warning("[resolve R%d] blockade upsert failed %s at %s: %s",
                                   round_num, cc, zone_id, e)

            events.append({
                "scenario_id": scenario_id, "round_num": round_num,
                "event_type": "blockade_declared",
                "country_code": cc,
                "summary": summary,
                "payload": {**payload, "action": action, "level": level},
            })

    # --- 9. Covert operations (CARD_ACTIONS 4.1-4.4) ------------------------
    import random as _rng
    for d in decisions:
        if d["action_type"] in COVERT_ACTIONS:
            payload = d["action_payload"] or {}
            cc = d["country_code"]
            op_type = payload.get("op_type", "intelligence")
            target = payload.get("target_country", "")

            # Probabilities per CARD_FORMULAS D.9
            PROBS = {"intelligence": 1.0, "sabotage": 0.50, "propaganda": 0.55, "election_meddling": 0.40}
            DETECT = {"intelligence": 0.30, "sabotage": 0.50, "propaganda": 0.25, "election_meddling": 0.45}
            ATTRIB = {"intelligence": 0.30, "sabotage": 0.50, "propaganda": 0.20, "election_meddling": 0.50}

            success = _rng.random() < PROBS.get(op_type, 0.50)
            detected = _rng.random() < DETECT.get(op_type, 0.30)
            attributed = detected and _rng.random() < ATTRIB.get(op_type, 0.30)

            effect = {}
            if op_type == "intelligence":
                success = True  # always returns a report
                question = payload.get("question", "General intelligence briefing")
                report = _generate_intelligence_report(
                    cc, target, question, country_state, unit_state, round_num)
                effect = {"report": report}
                # Persist report to agent's memory
                try:
                    from engine.agents import tools as agent_tools
                    existing = agent_tools.read_memory(
                        country_code=cc, scenario_code="start_one",
                        memory_key="intelligence_reports",
                    )
                    prev = existing.get("content", "") if existing.get("exists") else ""
                    new_content = f"{prev}\n\n[R{round_num}] Re: {target} — {report}".strip()
                    agent_tools.write_memory(
                        country_code=cc, scenario_code="start_one",
                        memory_key="intelligence_reports", content=new_content,
                        round_num=round_num,
                    )
                except Exception:
                    pass
            elif op_type == "sabotage" and success and target in country_state:
                tgt_type = payload.get("target_type", "infrastructure")
                if tgt_type == "infrastructure":
                    country_state[target]["treasury"] = max(0, country_state[target].get("treasury", 0) - 1)
                    effect = {"treasury_loss": 1}
                elif tgt_type == "nuclear_tech":
                    # -30% nuclear R&D progress (handled by engine tick reading this event)
                    effect = {"nuclear_progress_reduction": 0.30}
                elif tgt_type == "military":
                    effect = {"military_unit_risk": 0.50}  # 50% to destroy 1 unit — deferred
            elif op_type == "propaganda" and success and target in country_state:
                intent = payload.get("intent", "destabilize")
                delta = 0.3 if intent == "boost" else -0.3
                country_state[target]["stability"] = max(1, min(9, country_state[target].get("stability", 5) + delta))
                effect = {"stability_delta": delta}
            elif op_type == "election_meddling" and success and target in country_state:
                delta = -_rng.randint(2, 5)
                country_state[target]["political_support"] = max(5, country_state[target].get("political_support", 50) + delta)
                effect = {"support_delta": delta}

            events.append({
                "scenario_id": scenario_id, "round_num": round_num,
                "event_type": "covert_op",
                "country_code": cc,
                "summary": f"{cc} covert {op_type} vs {target}: "
                           f"{'success' if success else 'failed'}"
                           f"{', DETECTED' if detected else ''}"
                           f"{', ATTRIBUTED to ' + cc if attributed else ''}",
                "payload": {**payload, "success": success, "detected": detected,
                           "attributed": attributed, "effect": effect},
            })

    # --- 10. Nuclear tests (CARD_ACTIONS 1.9a/1.9b) -------------------------
    for d in decisions:
        if d["action_type"] in NUCLEAR_ACTIONS:
            payload = d["action_payload"] or {}
            cc = d["country_code"]
            test_type = payload.get("test_type", "underground")

            # Apply stability impact per CARD_FORMULAS D.7
            if test_type == "surface":
                # Surface: global -0.4, adjacent countries -0.6, own GDP -5%
                for c_code, c_state in country_state.items():
                    stab = c_state.get("stability", 5)
                    c_state["stability"] = max(1, stab - 0.4)
                if cc in country_state:
                    gdp = country_state[cc].get("gdp", 0)
                    country_state[cc]["gdp"] = round(gdp * 0.95, 2)
                alert = "GLOBAL ALERT"
            else:
                # Underground: global -0.2
                for c_code, c_state in country_state.items():
                    stab = c_state.get("stability", 5)
                    c_state["stability"] = max(1, stab - 0.2)
                alert = "T3+ ALERT"

            events.append({
                "scenario_id": scenario_id, "round_num": round_num,
                "event_type": "nuclear_test",
                "country_code": cc,
                "summary": f"{alert}: {cc} conducts {test_type} nuclear test",
                "payload": payload,
            })

    # --- 11. Transactions + Agreements (CARD_ACTIONS 5.1/5.2) ---------------
    for d in decisions:
        if d["action_type"] in TRANSACTION_ACTIONS:
            payload = d["action_payload"] or {}
            cc = d["country_code"]
            counterpart = payload.get("counterpart_country", "")

            if d["action_type"] == "propose_agreement":
                # Write to agreements table
                try:
                    client.table("agreements").insert({
                        "scenario_id": scenario_id,
                        "round_num": round_num,
                        "agreement_name": payload.get("agreement_name", "Untitled"),
                        "agreement_type": payload.get("agreement_type", "custom"),
                        "signatories": payload.get("signatories", [cc, counterpart]),
                        "visibility": payload.get("visibility", "public"),
                        "terms": payload.get("terms", ""),
                        "status": "proposed",
                    }).execute()
                except Exception as e:
                    logger.warning("agreement insert failed: %s", e)

                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "agreement_proposed",
                    "country_code": cc,
                    "summary": f"{cc} proposes {payload.get('agreement_type','agreement')} "
                               f"with {counterpart}",
                    "payload": payload,
                })
            else:
                # Exchange transaction — collect for batch write at end of resolve
                exchange_txns.append({
                    "scenario_id": scenario_id,
                    "round_num": round_num,
                    "proposer": cc,
                    "counterpart": counterpart,
                    "offer": payload.get("offer") or {},
                    "request": payload.get("request") or {},
                    "terms": payload.get("terms", ""),
                    "status": "proposed",
                })

                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "transaction_proposed",
                    "country_code": cc,
                    "summary": f"{cc} proposes exchange with {counterpart}",
                    "payload": payload,
                })

    # --- 12. Naval attack 1v1 (CARD_ACTIONS 1.5) ----------------------------
    for d in decisions:
        if d["action_type"] in NAVAL_ATTACK_ACTIONS:
            payload = d["action_payload"] or {}
            cc = d["country_code"]
            att_code = payload.get("attacker_unit_code", "")
            tgt_code = payload.get("target_unit_code", "")
            att_unit = unit_state.get(att_code)
            tgt_unit = unit_state.get(tgt_code)
            if not att_unit or not tgt_unit:
                events.append({"scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "attack_invalid", "country_code": cc,
                    "summary": f"{cc} naval attack invalid (units not found)",
                    "payload": payload})
                continue
            # 1v1 dice: each rolls 1d6, higher wins, ties → defender
            a_roll = _rng.randint(1, 6)
            d_roll = _rng.randint(1, 6)
            if a_roll > d_roll:
                _apply_losses(unit_state, [], [tgt_code])
                winner = "attacker"
            else:
                _apply_losses(unit_state, [att_code], [])
                winner = "defender"
            combats.append(_combat_row(
                scenario_id, round_num, "naval", cc, tgt_unit.get("country_code", "?"),
                att_unit.get("global_row"), att_unit.get("global_col"),
                [att_code], [tgt_code], [a_roll], [d_roll],
                [att_code] if winner == "defender" else [],
                [tgt_code] if winner == "attacker" else [],
                f"Naval 1v1: {att_code} ({a_roll}) vs {tgt_code} ({d_roll}) → {winner} wins",
            ))

    # --- 13. Martial law (CARD_ACTIONS 1.2) --------------------------------
    MARTIAL_LAW_POOLS = {"sarmatia": 10, "ruthenia": 6, "persia": 8, "cathay": 10}
    for d in decisions:
        if d["action_type"] in MARTIAL_LAW_ACTIONS:
            cc = d["country_code"]
            pool = MARTIAL_LAW_POOLS.get(cc, 0)
            if pool <= 0:
                events.append({"scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "martial_law_invalid", "country_code": cc,
                    "summary": f"{cc} cannot declare martial law (not eligible or pool=0)",
                    "payload": {}})
                continue
            # Add ground units to reserve (unit_codes generated)
            added = []
            for i in range(pool):
                new_code = f"{cc}_ml_{round_num}_{i}"
                unit_state[new_code] = {
                    "unit_code": new_code, "country_code": cc, "unit_type": "ground",
                    "status": "reserve", "global_row": None, "global_col": None,
                    "theater": None, "theater_row": None, "theater_col": None,
                    "embarked_on": None, "notes": f"{cc.title()} martial law conscript",
                }
                added.append(new_code)
            # Stability -1, war tiredness +1
            if cc in country_state:
                country_state[cc]["stability"] = max(1, country_state[cc].get("stability", 5) - 1)
                country_state[cc]["war_tiredness"] = min(10, country_state[cc].get("war_tiredness", 0) + 1)
            # Zero out the pool (one-off)
            MARTIAL_LAW_POOLS[cc] = 0
            events.append({"scenario_id": scenario_id, "round_num": round_num,
                "event_type": "martial_law", "country_code": cc,
                "summary": f"{cc} declares martial law: +{len(added)} ground reserves, stability -1, war tiredness +1",
                "payload": {"units_added": added, "pool_used": pool}})

    # --- 14. Basing rights (CARD_ACTIONS 1.11) -----------------------------
    for d in decisions:
        if d["action_type"] in BASING_RIGHTS_ACTIONS:
            payload = d["action_payload"] or {}
            cc = d["country_code"]
            counterpart = payload.get("counterpart_country", "")
            action = payload.get("action", "grant")
            try:
                if action == "grant":
                    client.table("relationships").update(
                        {"basing_rights_a_to_b": True}
                    ).eq("from_country_id", cc).eq("to_country_id", counterpart).execute()
                elif action == "revoke":
                    client.table("relationships").update(
                        {"basing_rights_a_to_b": False}
                    ).eq("from_country_id", cc).eq("to_country_id", counterpart).execute()
            except Exception as e:
                logger.warning("basing rights update failed: %s", e)
            events.append({"scenario_id": scenario_id, "round_num": round_num,
                "event_type": "basing_rights", "country_code": cc,
                "summary": f"{cc} {action}s basing rights to {counterpart}",
                "payload": payload})

    # --- Persist new snapshots -------------------------------------------
    _write_unit_snapshot(client, scenario_id, round_num, unit_state)
    _write_country_snapshot(client, scenario_id, round_num, country_state)
    _write_combats(client, combats)
    _write_events(client, events)
    _write_exchange_transactions(client, exchange_txns)

    # Mark round complete
    client.table("round_states").upsert(
        {
            "scenario_id": scenario_id,
            "round_num": round_num,
            "status": "completed",
        },
        on_conflict="scenario_id,round_num",
    ).execute()

    return {
        "scenario_id": scenario_id,
        "round_num": round_num,
        "decisions_processed": len(decisions),
        "combats": len(combats),
        "events": len(events),
        "exchange_transactions": len(exchange_txns),
        "narratives": narratives,
    }


# ---------------------------------------------------------------------------
# Attack processor
# ---------------------------------------------------------------------------


def _process_attack(
    decision: dict,
    unit_state: dict[str, dict],
    scenario_id: str,
    round_num: int,
    combats: list[dict],
    events: list[dict],
) -> None:
    """Process a declare_attack decision with RISK chain mechanic.

    Per CARD_ACTIONS 1.3 (2026-04-07):
    - Attacker selects ground units from source hex → attack adjacent hex
    - Iterative RISK dice until one side zero
    - If attacker wins: survivors move onto captured hex, trophies captured
    - CHAIN: if ≥2 units on captured hex and adjacent enemy hex exists,
      auto-continue (leave ≥1 behind each hop)
    - Air strikes resolved BEFORE ground (separate from chain)
    """
    payload = decision["action_payload"] or {}
    attacker_country = decision["country_code"]
    attacker_codes = payload.get("attacker_unit_codes") or []
    tgt_row = payload.get("target_global_row")
    tgt_col = payload.get("target_global_col")

    attacker_units = [unit_state[c] for c in attacker_codes if c in unit_state
                      and unit_state[c].get("status") != "destroyed"]
    if not attacker_units:
        events.append({
            "scenario_id": scenario_id, "round_num": round_num,
            "event_type": "attack_invalid", "country_code": attacker_country,
            "summary": f"{attacker_country} attack had no valid attacker units",
            "payload": payload,
        })
        return

    # Separate air units (ranged — resolved separately, no chain)
    air_units = [u for u in attacker_units if u.get("unit_type") == "tactical_air"]
    missile_units = [u for u in attacker_units if u.get("unit_type") == "strategic_missile"]
    ground_units = [u for u in attacker_units if u.get("unit_type") in ("ground", "armor")]

    # --- RANGED STRIKES FIRST (air + missiles, before ground) ---
    _resolve_ranged_strikes(
        air_units, missile_units, attacker_country, tgt_row, tgt_col,
        unit_state, scenario_id, round_num, combats, events,
    )

    # --- GROUND ATTACK WITH CHAIN ---
    if not ground_units:
        return  # only ranged strikes, no ground assault

    _resolve_ground_chain(
        ground_units, attacker_country, tgt_row, tgt_col,
        unit_state, scenario_id, round_num, combats, events,
    )

    # Old inline ranged/ground/naval code removed 2026-04-07.
    # Now handled by _resolve_ranged_strikes() + _resolve_ground_chain() above.


def _generate_intelligence_report(
    requester_cc: str, target_cc: str, question: str,
    country_state: dict, unit_state: dict, round_num: int,
) -> str:
    """Generate an LLM-powered intelligence report (CARD_ACTIONS 4.1).

    Uses real world state + mandated noise injection (10-30%).
    Returns 1-2 paragraph report.
    """
    try:
        import asyncio
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        # Build context from real data
        target_state = country_state.get(target_cc, {})
        target_units = [u for u in unit_state.values()
                       if u.get("country_code") == target_cc and u.get("status") != "destroyed"]
        ground = sum(1 for u in target_units if u.get("unit_type") == "ground")
        naval = sum(1 for u in target_units if u.get("unit_type") == "naval")
        air = sum(1 for u in target_units if u.get("unit_type") == "tactical_air")
        missiles = sum(1 for u in target_units if u.get("unit_type") == "strategic_missile")
        ad = sum(1 for u in target_units if u.get("unit_type") == "air_defense")

        context = (
            f"REAL DATA on {target_cc} (Round {round_num}):\n"
            f"GDP: {target_state.get('gdp', '?')}, Treasury: {target_state.get('treasury', '?')}, "
            f"Stability: {target_state.get('stability', '?')}, Support: {target_state.get('political_support', '?')}\n"
            f"Military: {ground} ground, {naval} naval, {air} air, {missiles} missiles, {ad} AD\n"
            f"Nuclear level: {target_state.get('nuclear_level', '?')}, "
            f"AI level: {target_state.get('ai_level', '?')}\n"
        )

        prompt = (
            f"You are an intelligence analyst preparing a CLASSIFIED report for {requester_cc}.\n\n"
            f"QUESTION FROM LEADERSHIP: {question}\n\n"
            f"AVAILABLE INTELLIGENCE:\n{context}\n\n"
            f"INSTRUCTIONS:\n"
            f"- Write a 1-2 paragraph intelligence report answering the question.\n"
            f"- Use the real data as your base, but INJECT 10-30% misleading information.\n"
            f"- Simple questions (specific facts): ~10% noise. Complex questions (broad analysis): ~30% noise.\n"
            f"- Noise means: slightly wrong numbers, plausible but false assessments, omissions.\n"
            f"- The requester does NOT know the noise level.\n"
            f"- Use SIM names only (no real-world names).\n"
            f"- Be concise and professional."
        )

        response = asyncio.run(call_llm(
            use_case=LLMUseCase.AGENT_REFLECTION,
            messages=[{"role": "user", "content": prompt}],
            system="You are a senior intelligence analyst. Write a classified briefing. Be concise.",
            max_tokens=400,
            temperature=0.7,
        ))
        return response.text
    except Exception as e:
        logger.warning("Intelligence report generation failed: %s", e)
        return f"Intelligence report on {target_cc}: data collection in progress. Preliminary assessment suggests heightened activity in the region. Further analysis required."


def _resolve_ranged_strikes(
    air_units, missile_units, attacker_country, tgt_row, tgt_col,
    unit_state, scenario_id, round_num, combats, events,
):
    """Resolve air strikes + missile strikes against target hex."""
    defender_units = [
        u for u in unit_state.values()
        if u.get("global_row") == tgt_row and u.get("global_col") == tgt_col
        and u.get("country_code") != attacker_country
        and u.get("status") != "destroyed"
    ]
    if not defender_units:
        return
    defender_country = defender_units[0].get("country_code")
    defender_ad = _ad_units_in_zone(unit_state, defender_country, tgt_row, tgt_col)

    AIR_STRIKE_MAX_RANGE = 2
    for au in air_units:
        au_r, au_c = au.get("global_row"), au.get("global_col")
        if au_r is not None and au_c is not None:
            dist = _hex_distance(au_r, au_c, tgt_row, tgt_col)
            if dist > AIR_STRIKE_MAX_RANGE:
                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "attack_out_of_range", "country_code": attacker_country,
                    "summary": f"{au['unit_code']} air strike OUT OF RANGE ({dist} hex)",
                    "payload": {"unit": au["unit_code"], "distance": dist},
                })
                continue
        sr = combat_mod.resolve_air_strike(au, defender_units, defender_ad)
        combats.append(_combat_row(
            scenario_id, round_num, "air", attacker_country, defender_country,
            tgt_row, tgt_col, [au["unit_code"]], [u["unit_code"] for u in defender_units],
            [], [], [], sr.defender_losses, sr.narrative,
        ))
        _apply_losses(unit_state, [], sr.defender_losses)
        defender_units = [u for u in defender_units if u["unit_code"] not in sr.defender_losses]
        if not defender_units:
            return

    for mu in missile_units:
        if not defender_units:
            return
        tgt = defender_units[0]
        sr = combat_mod.resolve_missile_strike(mu, tgt, defender_ad)
        combats.append(_combat_row(
            scenario_id, round_num, "missile", attacker_country, defender_country,
            tgt_row, tgt_col, [mu["unit_code"]], [tgt["unit_code"]],
            [], [], [], sr.defender_losses, sr.narrative,
        ))
        _apply_losses(unit_state, [], sr.defender_losses)
        # Missile consumed (disposable)
        _apply_losses(unit_state, [mu["unit_code"]], [])
        defender_units = [u for u in defender_units if u["unit_code"] not in sr.defender_losses]


def _resolve_ground_chain(
    ground_units, attacker_country, tgt_row, tgt_col,
    unit_state, scenario_id, round_num, combats, events,
    max_chain=10,
):
    """RISK ground attack with chain mechanic (CARD_ACTIONS 1.3).

    After winning a hex, surviving attackers move forward. If ≥2 units
    on captured hex and adjacent enemy hex exists, auto-continue
    (leaving ≥1 behind each hop). Chain stops when:
    - All attackers dead
    - Hit defended hex and lost
    - < 2 units remaining (can't leave 1 behind + attack with 1)
    - No more adjacent enemy hexes
    - max_chain reached (safety)
    """
    current_attackers = list(ground_units)
    current_tgt_row, current_tgt_col = tgt_row, tgt_col
    chain_step = 0

    while current_attackers and chain_step < max_chain:
        chain_step += 1

        # Find defenders (ground only — per CARD_ACTIONS, naval doesn't defend land)
        defender_ground = [
            u for u in unit_state.values()
            if u.get("global_row") == current_tgt_row
            and u.get("global_col") == current_tgt_col
            and u.get("country_code") != attacker_country
            and u.get("status") != "destroyed"
            and u.get("unit_type") in ("ground", "armor")
        ]

        # Trophies: non-ground enemy units on hex
        trophies = [
            u for u in unit_state.values()
            if u.get("global_row") == current_tgt_row
            and u.get("global_col") == current_tgt_col
            and u.get("country_code") != attacker_country
            and u.get("status") != "destroyed"
            and u.get("unit_type") not in ("ground", "armor")
        ]

        if not defender_ground:
            # Undefended — occupy + capture trophies
            captured = _capture_trophies(unit_state, trophies, attacker_country)
            _move_attackers_forward(unit_state, current_attackers, current_tgt_row, current_tgt_col)
            events.append({
                "scenario_id": scenario_id, "round_num": round_num,
                "event_type": "occupation",
                "country_code": attacker_country,
                "summary": f"{attacker_country} occupies ({current_tgt_row},{current_tgt_col})"
                           + (f", captured {len(captured)} trophies" if captured else ""),
                "payload": {"hex": [current_tgt_row, current_tgt_col], "trophies": captured},
            })
        else:
            # Defended — RISK combat
            defender_country = defender_ground[0].get("country_code", "?")

            # Build hex_context modifiers (SEED ACTION REVIEW 2026-03-30)
            hex_context = _build_ground_modifiers(
                attacker_country, defender_country, current_tgt_row, current_tgt_col,
                unit_state, current_attackers,
            )

            cr = combat_mod.resolve_ground_combat(current_attackers, defender_ground, hex_context)
            _apply_losses(unit_state, cr.attacker_losses, cr.defender_losses)

            combats.append(_combat_row(
                scenario_id, round_num, "ground", attacker_country, defender_country,
                current_tgt_row, current_tgt_col,
                [u["unit_code"] for u in current_attackers],
                [u["unit_code"] for u in defender_ground],
                cr.attacker_rolls, cr.defender_rolls,
                cr.attacker_losses, cr.defender_losses, cr.narrative,
            ))

            if not cr.success:
                # Attack failed — chain stops
                return

            # Won! Move survivors forward + capture trophies
            surviving = [u for u in current_attackers
                         if u["unit_code"] not in set(cr.attacker_losses)]
            captured = _capture_trophies(unit_state, trophies, attacker_country)
            _move_attackers_forward(unit_state, surviving, current_tgt_row, current_tgt_col)
            current_attackers = surviving

            if captured:
                events.append({
                    "scenario_id": scenario_id, "round_num": round_num,
                    "event_type": "trophies_captured",
                    "country_code": attacker_country,
                    "summary": f"{attacker_country} captured {len(captured)} units at ({current_tgt_row},{current_tgt_col})",
                    "payload": {"trophies": captured},
                })

        # --- CHAIN CHECK: can we continue? ---
        # Need ≥2 units to chain (leave 1 behind + attack with ≥1)
        if len(current_attackers) < 2:
            return

        # Leave 1 behind on captured (foreign) hex
        left_behind = current_attackers.pop()  # last unit stays
        # (unit is already at the captured hex from _move_attackers_forward)

        # Find next adjacent enemy hex to chain into
        neighbors = _hex_neighbors(current_tgt_row, current_tgt_col)
        next_target = None
        for nr, nc in neighbors:
            # Is there an enemy unit here?
            enemy_here = any(
                u.get("global_row") == nr and u.get("global_col") == nc
                and u.get("country_code") != attacker_country
                and u.get("status") != "destroyed"
                for u in unit_state.values()
            )
            if enemy_here:
                next_target = (nr, nc)
                break

        if next_target is None:
            return  # no adjacent enemy — chain ends

        current_tgt_row, current_tgt_col = next_target
        # Continue chain with remaining attackers (minus the one left behind)


def _build_ground_modifiers(
    attacker_country, defender_country, tgt_row, tgt_col,
    unit_state, attacker_units,
) -> dict:
    """Build hex_context modifiers for ground combat per SEED/CARD_ACTIONS."""
    ctx: dict = {}

    # Die hard: check if target hex has die_hard flag (from map data)
    # For now: check if any unit on hex has "die_hard" in notes or hex is in known die_hard list
    # TODO: read from map grid data properly
    # Simplified: check map_config for die_hard hexes when available

    # Air support: defender has tactical_air on the hex
    def_air = any(
        u.get("global_row") == tgt_row and u.get("global_col") == tgt_col
        and u.get("country_code") == defender_country
        and u.get("unit_type") == "tactical_air"
        and u.get("status") != "destroyed"
        for u in unit_state.values()
    )
    if def_air:
        ctx["air_support"] = True

    # Amphibious: attacker source hex is sea, target is land
    # Simplified check: if any attacker was on a sea hex (embarked)
    for au in attacker_units:
        if au.get("embarked_on"):
            ctx["amphibious"] = True
            break

    # AI L4 + morale: need country state data
    # These require access to country_states which we don't have here
    # TODO: pass country_states into _process_attack and read stability + ai_level
    # For now: omitted (will wire in next iteration)

    return ctx


def _apply_losses(
    unit_state: dict[str, dict],
    attacker_losses: list[str],
    defender_losses: list[str],
) -> None:
    for code in list(attacker_losses) + list(defender_losses):
        if code in unit_state:
            unit_state[code]["status"] = "destroyed"


def _hex_distance(r1: int, c1: int, r2: int, c2: int) -> int:
    """Hex distance on pointy-top odd-r offset grid (1-indexed).

    Converts to cube coords then uses standard hex distance.
    """
    def _to_cube(row: int, col: int) -> tuple[int, int, int]:
        # 1-indexed odd-r offset -> cube
        # Flip parity because 1-indexed even == 0-indexed odd
        is_odd_row_0idx = ((row - 1) % 2) == 1
        x = (col - 1) - ((row - 1) - (1 if is_odd_row_0idx else 0)) // 2
        z = row - 1
        y = -x - z
        return (x, y, z)
    a = _to_cube(r1, c1)
    b = _to_cube(r2, c2)
    return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) // 2


def _hex_neighbors(row: int, col: int) -> list[tuple[int, int]]:
    """Return 6 pointy-top odd-r offset neighbors (1-indexed).

    Matches the frontend's ``getAdjacencies`` in map.js (odd/even row
    deltas are flipped for 1-indexed).
    """
    even_row = (row % 2 == 0)  # 1-indexed: even row == odd in 0-indexed
    if even_row:
        deltas = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
    else:
        deltas = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    return [(row + dr, col + dc) for dr, dc in deltas]


def _adjacent_naval_defenders(
    unit_state: dict[str, dict],
    defender_country: str,
    tgt_row: int,
    tgt_col: int,
) -> list[dict]:
    """Return active naval units owned by ``defender_country`` on any
    of the 6 hex-neighbours of the target.

    Rule (Marat 2026-04-05): naval can fight back against ground attacks
    if adjacent. Strength is equal to ground (1 die per unit).
    """
    neighbors = set(_hex_neighbors(tgt_row, tgt_col))
    out: list[dict] = []
    for u in unit_state.values():
        if u.get("country_code") != defender_country:
            continue
        if u.get("unit_type") != "naval":
            continue
        if u.get("status") == "destroyed":
            continue
        pos = (u.get("global_row"), u.get("global_col"))
        if pos in neighbors:
            out.append(u)
    return out


def _capture_trophies(
    unit_state: dict[str, dict],
    trophies: list[dict],
    new_owner: str,
) -> list[str]:
    """Flip ownership of captured units to ``new_owner`` and send them
    to reserve. Preserves unit_type. Returns the list of captured codes."""
    out: list[str] = []
    for u in trophies:
        code = u["unit_code"]
        # find in unit_state
        live = unit_state.get(code)
        if live is None or live.get("status") == "destroyed":
            continue
        live["country_code"] = new_owner
        live["status"] = "reserve"
        live["global_row"] = None
        live["global_col"] = None
        live["theater"] = None
        live["theater_row"] = None
        live["theater_col"] = None
        live["embarked_on"] = None
        out.append(code)
    return out


def _move_attackers_forward(
    unit_state: dict[str, dict],
    attackers: list[dict],
    tgt_row: int,
    tgt_col: int,
) -> None:
    """Relocate all surviving attackers onto the captured target hex.
    (Phase 1: moves them all forward. Chaining support — leaving ≥1 on
    source intermediate hops — is Phase 2.)"""
    for u in attackers:
        live = unit_state.get(u["unit_code"])
        if live is None or live.get("status") == "destroyed":
            continue
        live["global_row"] = tgt_row
        live["global_col"] = tgt_col
        # Land-attacker onto land -> clear any theater coords
        live["theater"] = None
        live["theater_row"] = None
        live["theater_col"] = None


def _ad_units_in_zone(
    unit_state: dict[str, dict],
    defender_country: str,
    tgt_global_row: int,
    tgt_global_col: int,
) -> list[dict]:
    """Return all active AD units owned by ``defender_country`` that
    cover the target zone.

    Zone definition (Marat, 2026-04-05):
      * Zone = the global hex (tgt_global_row, tgt_global_col) PLUS
        every theater hex that links to it.
      * An AD unit covers the zone if it is located on the zone's global
        hex OR on any theater hex that links to the zone's global hex.

    Implementation:
      1. The "zone key" is the global hex (tgt_global_row, tgt_global_col).
      2. For each defender AD unit:
         - If its ``global_row/col`` equals the zone key -> covers.
         - If it's on a theater hex, map that theater hex back to its
           global anchor via ``global_hex_for_theater_cell`` and compare.
    """
    zone_key = (tgt_global_row, tgt_global_col)
    ad: list[dict] = []
    for u in unit_state.values():
        if u.get("country_code") != defender_country:
            continue
        if u.get("unit_type") != "air_defense":
            continue
        if u.get("status") == "destroyed":
            continue
        # Case A: AD on the target global hex itself
        if (u.get("global_row"), u.get("global_col")) == zone_key:
            ad.append(u)
            continue
        # Case B: AD on a theater hex that maps back to the target zone
        t_name = u.get("theater")
        t_row = u.get("theater_row")
        t_col = u.get("theater_col")
        if t_name and t_row is not None and t_col is not None:
            # Need cell owner to resolve theater->global; use the AD's own country
            mapped = global_hex_for_theater_cell(t_name, t_row, t_col, defender_country)
            if mapped == zone_key:
                ad.append(u)
                continue
        # Case C (safety net): if the target IS a theater-link hex and the
        # AD sits on the SAME theater (even if its cell owner doesn't map
        # back by the rule above), still treat as zone-covering. This
        # guards against edge cases in the mapping table.
        linked_theater = theater_for_global_hex(tgt_global_row, tgt_global_col)
        if linked_theater and t_name == linked_theater:
            ad.append(u)
    return ad


def _combat_row(
    scenario_id, round_num, combat_type, attacker_country, defender_country,
    loc_row, loc_col, attacker_units, defender_units,
    attacker_rolls, defender_rolls, attacker_losses, defender_losses, narrative,
) -> dict:
    return {
        "scenario_id": scenario_id,
        "round_num": round_num,
        "combat_type": combat_type,
        "attacker_country": attacker_country,
        "defender_country": defender_country,
        "location_global_row": loc_row,
        "location_global_col": loc_col,
        "attacker_units": attacker_units,
        "defender_units": defender_units,
        "attacker_rolls": attacker_rolls,
        "defender_rolls": defender_rolls,
        "attacker_losses": attacker_losses,
        "defender_losses": defender_losses,
        "narrative": narrative,
    }


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


_UNIT_COLS = {
    "scenario_id", "round_num", "unit_code", "country_code", "unit_type",
    "global_row", "global_col", "theater", "theater_row", "theater_col",
    "embarked_on", "status", "notes",
}
_COUNTRY_COLS = {
    "scenario_id", "round_num", "country_code", "gdp", "treasury", "inflation",
    "stability", "political_support", "war_tiredness",
    "nuclear_level", "nuclear_rd_progress", "ai_level", "ai_rd_progress",
    "budget_social_pct", "budget_production", "budget_research",
    "budget_military_coins", "budget_tech_coins",  # deprecated, kept for migration
    "opec_production",
    "sanctions_coefficient", "tariff_coefficient",
}


def _write_unit_snapshot(client, scenario_id, round_num, unit_state):
    rows = []
    for uc, u in unit_state.items():
        row = {k: u.get(k) for k in _UNIT_COLS if k in u}
        row["scenario_id"] = scenario_id
        row["round_num"] = round_num
        row["unit_code"] = uc
        rows.append(row)
    if not rows:
        return
    # batch in chunks of 200
    for i in range(0, len(rows), 200):
        client.table("unit_states_per_round").upsert(
            rows[i:i+200], on_conflict="scenario_id,round_num,unit_code"
        ).execute()


def _write_country_snapshot(client, scenario_id, round_num, country_state):
    rows = []
    # Integer columns in country_states_per_round — must be int, not float
    INT_COLS = {"stability", "political_support", "war_tiredness", "nuclear_level", "ai_level"}
    for cc, c in country_state.items():
        row = {k: c.get(k) for k in _COUNTRY_COLS if k in c}
        # Ensure integer columns are actually int (engine may produce floats)
        for col in INT_COLS:
            if col in row and row[col] is not None:
                row[col] = int(round(float(row[col])))
        row["scenario_id"] = scenario_id
        row["round_num"] = round_num
        row["country_code"] = cc
        rows.append(row)
    if not rows:
        return
    client.table("country_states_per_round").upsert(
        rows, on_conflict="scenario_id,round_num,country_code"
    ).execute()


def _write_combats(client, combats):
    if not combats:
        return
    client.table("observatory_combat_results").insert(combats).execute()


def _write_events(client, events):
    if not events:
        return
    client.table("observatory_events").insert(events).execute()


def _write_exchange_transactions(client, txns: list[dict]):
    """Batch-write exchange_transactions rows, deduplicating against existing."""
    if not txns:
        return
    # Dedup: check which proposer+counterpart pairs already exist for this round
    sample = txns[0]
    scenario_id = sample["scenario_id"]
    round_num = sample["round_num"]
    try:
        existing = client.table("exchange_transactions") \
            .select("proposer, counterpart") \
            .eq("scenario_id", scenario_id) \
            .eq("round_num", round_num) \
            .execute()
        existing_pairs = {(r["proposer"], r["counterpart"]) for r in (existing.data or [])}
    except Exception as e:
        logger.warning("exchange_transactions dedup query failed: %s", e)
        existing_pairs = set()

    to_insert = [t for t in txns
                 if (t["proposer"], t["counterpart"]) not in existing_pairs]
    if not to_insert:
        logger.info("exchange_transactions: all %d already exist, skipping", len(txns))
        return

    try:
        client.table("exchange_transactions").insert(to_insert).execute()
        logger.info("exchange_transactions: inserted %d rows", len(to_insert))
    except Exception as e:
        logger.error("exchange_transactions batch insert failed: %s", e)
        # Fallback: insert one-by-one so partial success is possible
        inserted = 0
        for t in to_insert:
            try:
                client.table("exchange_transactions").insert(t).execute()
                inserted += 1
            except Exception as e2:
                logger.error("exchange_transaction single insert failed for %s->%s: %s",
                             t["proposer"], t["counterpart"], e2)
        logger.info("exchange_transactions: fallback inserted %d/%d", inserted, len(to_insert))
