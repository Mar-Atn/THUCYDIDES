"""Domain lookup tools for AI participants.

Each tool queries live game state (``unit_states_per_round`` /
``country_states_per_round``) when ``scenario_code`` and ``round_num`` are
provided, falling back to seed tables (``layout_units``, ``sim_templates``,
``countries``) when no live snapshot exists (e.g. round 0 or before the
first engine tick).

Design note: ``country_code``, ``scenario_code``, and ``round_num`` are
passed explicitly at the Python API level. In the tool-use wrapper
(see ``leader_round.py``) they are bound as closures based on the calling
agent's identity and the current round, so the LLM does not need to supply
them.
"""
from __future__ import annotations

import logging
from typing import Optional

from engine.config.map_config import (
    is_theater_link_hex,
    theater_for_global_hex,
    in_global_bounds,
    in_theater_bounds,
)
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_sim_run_id_cached(scenario_code: str) -> Optional[str]:
    """Map scenario code -> sim_run_id (legacy archived run for that scenario).

    F1 (2026-04-11): live-state queries key by sim_run_id, not scenario_id.
    For pre-F1 callers that only have a scenario code, we resolve to the
    archived legacy run.
    """
    try:
        from engine.services.sim_run_manager import resolve_sim_run_id
        return resolve_sim_run_id(scenario_code)
    except Exception:
        return None


def _load_live_units(
    scenario_code: str, round_num: int, *, country_code: Optional[str] = None,
) -> Optional[list[dict]]:
    """Load unit rows from unit_states_per_round for the given round.

    Returns None if no live snapshot exists (caller should fall back to seed).
    If ``country_code`` is given, filters to that country only.
    """
    sim_run_id = _resolve_sim_run_id_cached(scenario_code)
    if not sim_run_id:
        return None
    client = get_client()
    q = (
        client.table("unit_states_per_round")
        .select("*")
        .eq("sim_run_id", sim_run_id)
        .eq("round_num", round_num)
    )
    if country_code:
        q = q.eq("country_code", country_code)
    res = q.execute()
    if res.data:
        return res.data
    return None


def _load_live_country_state(
    scenario_code: str, round_num: int, country_code: str,
) -> Optional[dict]:
    """Load a single country row from country_states_per_round.

    Returns None if no live snapshot exists (caller should fall back to seed).
    """
    sim_run_id = _resolve_sim_run_id_cached(scenario_code)
    if not sim_run_id:
        return None
    client = get_client()
    res = (
        client.table("country_states_per_round")
        .select("*")
        .eq("sim_run_id", sim_run_id)
        .eq("round_num", round_num)
        .eq("country_code", country_code)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None


def _resolve_layout_id(layout_code: str) -> Optional[str]:
    """Map human-readable layout code -> layout_id UUID."""
    client = get_client()
    result = (
        client.table("unit_layouts")
        .select("id")
        .eq("code", layout_code)
        .execute()
    )
    if not result.data:
        return None
    return result.data[0]["id"]


def _unit_to_dict(row: dict) -> dict:
    """Trim a layout_units DB row to agent-facing fields."""
    return {
        "unit_code": row["unit_code"],
        "unit_type": row["unit_type"],
        "status": row["status"],
        "global_row": row.get("global_row"),
        "global_col": row.get("global_col"),
        "theater": row.get("theater"),
        "theater_row": row.get("theater_row"),
        "theater_col": row.get("theater_col"),
        "embarked_on": row.get("embarked_on"),
        "notes": row.get("notes"),
    }


# ---------------------------------------------------------------------------
# Tool 1: my forces
# ---------------------------------------------------------------------------

def get_my_forces(
    country_code: str,
    scenario_code: str = "start_one",
    round_num: Optional[int] = None,
    layout_code: str = "template_v1_0_default",
) -> dict:
    """Return the country's complete force disposition.

    Reads from ``unit_states_per_round`` (live state) when scenario_code
    and round_num are provided. Falls back to ``layout_units`` (seed) if
    no live snapshot exists.

    Returns:
        dict with total_units, by_status, by_type, by_global_hex, by_theater_cell,
        and a ``units`` list containing every unit.
    """
    try:
        rows = None
        source = "seed"

        # Try live state first
        if round_num is not None and scenario_code:
            live = _load_live_units(scenario_code, round_num, country_code=country_code)
            if live:
                rows = live
                source = "live"

        # Fallback to seed layout_units
        if rows is None:
            layout_id = _resolve_layout_id(layout_code)
            if not layout_id:
                return {"error": f"Unknown layout code: {layout_code}"}
            client = get_client()
            result = (
                client.table("layout_units")
                .select("*")
                .eq("layout_id", layout_id)
                .eq("country_code", country_code)
                .execute()
            )
            rows = result.data or []

        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_global_hex: dict[str, list[str]] = {}
        by_theater_cell: dict[str, dict[str, list[str]]] = {}
        units: list[dict] = []

        for r in rows:
            u = _unit_to_dict(r)
            units.append(u)
            by_status[u["status"]] = by_status.get(u["status"], 0) + 1
            by_type[u["unit_type"]] = by_type.get(u["unit_type"], 0) + 1

            if u["global_row"] is not None and u["global_col"] is not None:
                key = f"({u['global_row']},{u['global_col']})"
                by_global_hex.setdefault(key, []).append(u["unit_code"])

            if u["theater"] and u["theater_row"] is not None:
                t = by_theater_cell.setdefault(u["theater"], {})
                key = f"({u['theater_row']},{u['theater_col']})"
                t.setdefault(key, []).append(u["unit_code"])

        return {
            "country": country_code,
            "source": source,
            "round_num": round_num,
            "total_units": len(rows),
            "by_status": by_status,
            "by_type": by_type,
            "by_global_hex": by_global_hex,
            "by_theater_cell": by_theater_cell,
            "units": units,
        }
    except Exception as e:
        logger.exception("get_my_forces failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 2: hex info
# ---------------------------------------------------------------------------

def get_hex_info(
    row: int,
    col: int,
    scope: str = "global",
    scenario_code: str = "start_one",
    round_num: Optional[int] = None,
    layout_code: str = "template_v1_0_default",
) -> dict:
    """Return info about a specific hex: who is there, any theater link.

    Reads from ``unit_states_per_round`` (live) when scenario_code and
    round_num are provided. Falls back to ``layout_units`` (seed).

    Args:
        row, col: 1-indexed coordinates.
        scope: 'global' or a theater name (e.g. 'mashriq', 'eastern_ereb').
    """
    try:
        all_rows = None
        source = "seed"

        # Try live state first
        if round_num is not None and scenario_code:
            live = _load_live_units(scenario_code, round_num)
            if live:
                all_rows = live
                source = "live"

        if scope == "global":
            if not in_global_bounds(row, col):
                return {"error": f"({row},{col}) is out of global bounds (1..10 x 1..20)"}

            if all_rows is not None:
                # Filter live rows by global coords
                matching = [r for r in all_rows
                            if r.get("global_row") == row and r.get("global_col") == col]
            else:
                # Fallback to seed
                layout_id = _resolve_layout_id(layout_code)
                if not layout_id:
                    return {"error": f"Unknown layout code: {layout_code}"}
                client = get_client()
                result = (
                    client.table("layout_units")
                    .select("*")
                    .eq("layout_id", layout_id)
                    .eq("global_row", row)
                    .eq("global_col", col)
                    .execute()
                )
                matching = result.data or []

            units = [_unit_to_dict(r) for r in matching]
            linked_theater = theater_for_global_hex(row, col)
            return {
                "coords": {"row": row, "col": col},
                "scope": "global",
                "source": source,
                "units_present": units,
                "unit_count": len(units),
                "is_theater_link_hex": is_theater_link_hex(row, col),
                "linked_theater": linked_theater,
            }

        # theater scope
        if not in_theater_bounds(scope, row, col):
            return {"error": f"({row},{col}) is out of bounds for theater {scope}"}

        if all_rows is not None:
            matching = [r for r in all_rows
                        if r.get("theater") == scope
                        and r.get("theater_row") == row
                        and r.get("theater_col") == col]
        else:
            layout_id = _resolve_layout_id(layout_code)
            if not layout_id:
                return {"error": f"Unknown layout code: {layout_code}"}
            client = get_client()
            result = (
                client.table("layout_units")
                .select("*")
                .eq("layout_id", layout_id)
                .eq("theater", scope)
                .eq("theater_row", row)
                .eq("theater_col", col)
                .execute()
            )
            matching = result.data or []

        units = [_unit_to_dict(r) for r in matching]
        return {
            "coords": {"row": row, "col": col},
            "scope": scope,
            "source": source,
            "units_present": units,
            "unit_count": len(units),
        }
    except Exception as e:
        logger.exception("get_hex_info failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 3: enemy forces
# ---------------------------------------------------------------------------

def get_enemy_forces(
    country_code: str,
    enemy_country_code: str,
    scenario_code: str = "start_one",
    round_num: Optional[int] = None,
    layout_code: str = "template_v1_0_default",
) -> dict:
    """Return observable forces of ``enemy_country_code``.

    Reads from ``unit_states_per_round`` (live) when scenario_code and
    round_num are provided. Falls back to ``layout_units`` (seed).

    SCOPING: Only returns data for countries the requester is at war with
    or that are publicly observable (full map visibility, no fog of war).
    Reserves are not observable regardless.

    Information scoping (2026-04-08): any country's ACTIVE unit positions
    are visible to all (leaders get military briefings). But this tool is
    named "enemy" forces — we restrict to actual adversaries to maintain
    the semantic intent. Agents can use get_hex_info() for general map queries.
    """
    if enemy_country_code == country_code:
        return {"error": "Cannot spy on your own forces — use get_my_forces()"}

    try:
        rows = None
        source = "seed"

        # Try live state first
        if round_num is not None and scenario_code:
            live = _load_live_units(scenario_code, round_num, country_code=enemy_country_code)
            if live:
                # Filter to active + embarked only (reserves not observable)
                rows = [r for r in live if r.get("status") in ("active", "embarked")]
                source = "live"

        # Fallback to seed
        if rows is None:
            layout_id = _resolve_layout_id(layout_code)
            if not layout_id:
                return {"error": f"Unknown layout code: {layout_code}"}
            client = get_client()
            result = (
                client.table("layout_units")
                .select("*")
                .eq("layout_id", layout_id)
                .eq("country_code", enemy_country_code)
                .in_("status", ["active", "embarked"])
                .execute()
            )
            rows = result.data or []

        units = [_unit_to_dict(r) for r in rows]

        by_type: dict[str, int] = {}
        by_global_hex: dict[str, list[str]] = {}
        by_theater_cell: dict[str, dict[str, list[str]]] = {}
        for u in units:
            by_type[u["unit_type"]] = by_type.get(u["unit_type"], 0) + 1
            if u["global_row"] is not None:
                key = f"({u['global_row']},{u['global_col']})"
                by_global_hex.setdefault(key, []).append(u["unit_code"])
            if u["theater"]:
                t = by_theater_cell.setdefault(u["theater"], {})
                key = f"({u['theater_row']},{u['theater_col']})"
                t.setdefault(key, []).append(u["unit_code"])

        return {
            "observer": country_code,
            "target": enemy_country_code,
            "source": source,
            "observable_units": len(units),
            "note": "Active + embarked only. Reserves are not observable.",
            "by_type": by_type,
            "by_global_hex": by_global_hex,
            "by_theater_cell": by_theater_cell,
            "units": units,
        }
    except Exception as e:
        logger.exception("get_enemy_forces failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 4: strategic context
# ---------------------------------------------------------------------------

def get_strategic_context(
    country_code: str,
    scenario_code: str = "start_one",
    round_num: Optional[int] = None,
    template_code: str = "ttt_v1_0",
) -> dict:
    """Return strategic context: regime, GDP, treasury, wars, stability.

    Reads from ``country_states_per_round`` (live) when scenario_code and
    round_num are provided. Falls back to seed tables.
    """
    try:
        client = get_client()

        # Always load template for at_war_with and metadata
        tpl_result = (
            client.table("sim_templates")
            .select("default_country_stats")
            .eq("code", template_code)
            .execute()
        )
        if not tpl_result.data:
            return {"error": f"Unknown template: {template_code}"}
        stats_blob = (tpl_result.data[0].get("default_country_stats") or {}).get(country_code)
        if not stats_blob:
            return {"error": f"No stats for country {country_code} in template {template_code}"}

        # Try live state first
        live = None
        source = "seed"
        if round_num is not None and scenario_code:
            live = _load_live_country_state(scenario_code, round_num, country_code)
            if live:
                source = "live"

        # countries table for sim_name / parallel (static metadata)
        c_result = (
            client.table("countries")
            .select("sim_name,parallel,regime_type,gdp,treasury,stability,war_tiredness,inflation,mil_ground,mil_naval,mil_tactical_air,mil_strategic_missiles,mil_air_defense,nuclear_level")
            .eq("id", country_code)
            .execute()
        )
        country_row = c_result.data[0] if c_result.data else {}

        # Priority: live > country_row > stats_blob
        def pick(key, default=0):
            if live and live.get(key) is not None:
                return live[key]
            v = country_row.get(key)
            if v is not None:
                return v
            return stats_blob.get(key, default)

        at_war_with = stats_blob.get("at_war_with", []) or []
        return {
            "country": country_code,
            "source": source,
            "name": country_row.get("sim_name"),
            "parallel": country_row.get("parallel"),
            "regime_type": pick("regime_type", None),
            "gdp": float(pick("gdp") or 0),
            "treasury": float(pick("treasury") or 0),
            "inflation": float(pick("inflation") or 0),
            "stability": float(pick("stability") or 0),
            "war_tiredness": float(pick("war_tiredness") or 0),
            "at_war_with": at_war_with,
            "at_war": len(at_war_with) > 0,
            "military_totals": {
                "ground": country_row.get("mil_ground") or stats_blob.get("mil_ground"),
                "naval": country_row.get("mil_naval") or stats_blob.get("mil_naval"),
                "tactical_air": country_row.get("mil_tactical_air") or stats_blob.get("mil_tactical_air"),
                "strategic_missiles": country_row.get("mil_strategic_missiles") or stats_blob.get("mil_strategic_missiles"),
                "air_defense": country_row.get("mil_air_defense") or stats_blob.get("mil_air_defense"),
            },
            "nuclear_level": pick("nuclear_level", None),
        }
    except Exception as e:
        logger.exception("get_strategic_context failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 5: template info
# ---------------------------------------------------------------------------

def get_template_info(template_code: str = "ttt_v1_0") -> dict:
    """Return template metadata: name, version, theaters, round counts, orgs."""
    try:
        client = get_client()
        result = (
            client.table("sim_templates")
            .select("code,name,version,status,description,allowed_round_counts,allowed_theaters,organizations")
            .eq("code", template_code)
            .execute()
        )
        if not result.data:
            return {"error": f"Unknown template: {template_code}"}
        row = result.data[0]
        orgs = row.get("organizations") or {}
        org_summary = {
            code: {
                "name": meta.get("name"),
                "description": meta.get("description"),
            }
            for code, meta in orgs.items()
        }
        return {
            "code": row["code"],
            "name": row["name"],
            "version": row["version"],
            "status": row["status"],
            "description": row.get("description"),
            "allowed_round_counts": row.get("allowed_round_counts"),
            "allowed_theaters": row.get("allowed_theaters"),
            "organizations": org_summary,
        }
    except Exception as e:
        logger.exception("get_template_info failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 6: relationships
# ---------------------------------------------------------------------------

def get_relationships(
    country_code: str,
    scenario_code: str = "start_one",
    round_num: Optional[int] = None,
    template_code: str = "ttt_v1_0",
) -> dict:
    """Return bilateral relationships for this country.

    Reads from the live ``relationships`` table (status column) first.
    Falls back to ``sim_templates.default_country_stats`` if no
    relationships rows exist.
    """
    try:
        client = get_client()

        # Try live relationships table first
        rels = (
            client.table("relationships")
            .select("from_country_code, to_country_code, status, relationship")
            .or_(f"from_country_code.eq.{country_code},to_country_code.eq.{country_code}")
            .execute()
        )
        if rels.data:
            at_war_with: list[str] = []
            at_war_from: list[str] = []
            allies: list[str] = []
            for r in rels.data:
                status = r.get("status", "")
                frm = r.get("from_country_code", "")
                to = r.get("to_country_code", "")
                other = to if frm == country_code else frm
                if status == "military_conflict":
                    if frm == country_code:
                        at_war_with.append(other)
                    else:
                        at_war_from.append(other)
                elif status in ("alliance", "allied"):
                    allies.append(other)
            return {
                "country": country_code,
                "source": "live",
                "at_war_with": at_war_with,
                "at_war_from": at_war_from,
                "allies": allies,
            }

        # Fallback to seed data from sim_templates
        tpl_result = (
            client.table("sim_templates")
            .select("default_country_stats")
            .eq("code", template_code)
            .execute()
        )
        if not tpl_result.data:
            return {"error": f"Unknown template: {template_code}"}
        all_stats = tpl_result.data[0].get("default_country_stats") or {}

        self_stats = all_stats.get(country_code)
        if self_stats is None:
            return {"error": f"No stats for country {country_code} in template {template_code}"}

        at_war_with = list(self_stats.get("at_war_with") or [])
        at_war_from_list: list[str] = []
        for other_code, other_stats in all_stats.items():
            if other_code == country_code:
                continue
            other_wars = (other_stats or {}).get("at_war_with") or []
            if country_code in other_wars:
                at_war_from_list.append(other_code)

        return {
            "country": country_code,
            "source": "seed",
            "at_war_with": at_war_with,
            "at_war_from": at_war_from_list,
        }
    except Exception as e:
        logger.exception("get_relationships failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 7: organization memberships
# ---------------------------------------------------------------------------

def get_organization_memberships(
    country_code: str,
    template_code: str = "ttt_v1_0",
) -> dict:
    """Return international organizations this country belongs to.

    Also returns the full catalog of organizations so the agent knows
    what exists. If the template's default memberships are empty, the
    response notes that and returns all orgs anyway.
    """
    try:
        client = get_client()
        result = (
            client.table("sim_templates")
            .select("organizations")
            .eq("code", template_code)
            .execute()
        )
        if not result.data:
            return {"error": f"Unknown template: {template_code}"}
        orgs = result.data[0].get("organizations") or {}

        memberships: list[str] = []
        catalog: dict[str, dict] = {}
        any_members = False
        for org_code, meta in orgs.items():
            members = (meta or {}).get("default_members") or []
            if members:
                any_members = True
            catalog[org_code] = {
                "name": (meta or {}).get("name"),
                "description": (meta or {}).get("description"),
                "default_members": members,
            }
            if country_code in members:
                memberships.append(org_code)

        response = {
            "country": country_code,
            "memberships": memberships,
            "organizations_catalog": catalog,
        }
        if not any_members:
            response["note"] = "default memberships not yet populated in template"
        return response
    except Exception as e:
        logger.exception("get_organization_memberships failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 8: country codes list
# ---------------------------------------------------------------------------

def get_country_codes_list(template_code: str = "ttt_v1_0") -> dict:
    """Return the list of valid country codes with SIM names and real-world parallels.

    This is the "who's who" reference — call this to avoid hallucinating
    country codes or SIM names.
    """
    try:
        client = get_client()
        tpl_result = (
            client.table("sim_templates")
            .select("default_country_stats")
            .eq("code", template_code)
            .execute()
        )
        if not tpl_result.data:
            return {"error": f"Unknown template: {template_code}"}
        all_stats = tpl_result.data[0].get("default_country_stats") or {}

        codes = sorted(all_stats.keys())

        # Try to enrich with sim_name from countries table
        c_result = (
            client.table("countries")
            .select("id,sim_name,parallel")
            .in_("id", codes)
            .execute()
        )
        name_lookup = {r["id"]: r for r in (c_result.data or [])}

        countries: list[dict] = []
        for code in codes:
            stats = all_stats.get(code) or {}
            row = name_lookup.get(code, {})
            countries.append({
                "country_code": code,
                "sim_name": row.get("sim_name") or stats.get("sim_name"),
                "parallel": row.get("parallel") or stats.get("parallel"),
            })

        return {
            "template": template_code,
            "total": len(countries),
            "country_codes": codes,
            "countries": countries,
        }
    except Exception as e:
        logger.exception("get_country_codes_list failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 9: economic state
# ---------------------------------------------------------------------------

def get_economic_state(
    country_code: str,
    scenario_code: str = "start_one",
    round_num: Optional[int] = None,
    template_code: str = "ttt_v1_0",
) -> dict:
    """Return economic state with annotations for risks and constraints.

    Reads from ``country_states_per_round`` (live) when scenario_code and
    round_num are provided. Falls back to seed tables.
    """
    try:
        client = get_client()
        tpl_result = (
            client.table("sim_templates")
            .select("default_country_stats")
            .eq("code", template_code)
            .execute()
        )
        if not tpl_result.data:
            return {"error": f"Unknown template: {template_code}"}
        stats = (tpl_result.data[0].get("default_country_stats") or {}).get(country_code)
        if not stats:
            return {"error": f"No stats for country {country_code}"}

        # Try live state first
        live = None
        source = "seed"
        if round_num is not None and scenario_code:
            live = _load_live_country_state(scenario_code, round_num, country_code)
            if live:
                source = "live"

        c_result = (
            client.table("countries")
            .select(
                "gdp,treasury,inflation,trade_balance,debt_burden,tax_rate,"
                "sector_resources,sector_industry,sector_services,sector_technology,"
                "oil_producer,opec_member,oil_production_mbpd,formosa_dependency"
            )
            .eq("id", country_code)
            .execute()
        )
        row = c_result.data[0] if c_result.data else {}

        # Priority: live > country_row > stats_blob
        def pick(key, default=0):
            if live and live.get(key) is not None:
                return live[key]
            v = row.get(key)
            if v is None:
                v = stats.get(key, default)
            return v

        gdp = float(pick("gdp") or 0)
        treasury = float(pick("treasury") or 0)
        inflation = float(pick("inflation") or 0)
        debt_burden = float(pick("debt_burden") or 0)
        trade_balance = float(pick("trade_balance") or 0)
        formosa_dep = float(pick("formosa_dependency") or 0)

        annotations: list[str] = []
        if inflation > 30:
            annotations.append("hyperinflation risk")
        elif inflation > 10:
            annotations.append("high inflation")
        if treasury <= 1:
            annotations.append("treasury near-empty — cannot sustain spending")
        elif treasury < 10:
            annotations.append("treasury constrained")
        if debt_burden > 0.8:
            annotations.append("debt crisis risk")
        if trade_balance < -10:
            annotations.append("severe trade deficit")
        if formosa_dep > 0.3:
            annotations.append("high Formosa/Taiwan semiconductor dependency")

        return {
            "country": country_code,
            "source": source,
            "gdp": gdp,
            "treasury": treasury,
            "inflation": inflation,
            "trade_balance": trade_balance,
            "debt_burden": debt_burden,
            "tax_rate": float(pick("tax_rate") or 0),
            "sectors": {
                "resources": pick("sector_resources"),
                "industry": pick("sector_industry"),
                "services": pick("sector_services"),
                "technology": pick("sector_technology"),
            },
            "oil_producer": bool(pick("oil_producer", False)),
            "opec_member": bool(pick("opec_member", False)),
            "oil_production_mbpd": float(pick("oil_production_mbpd") or 0),
            "formosa_dependency": formosa_dep,
            "annotations": annotations,
        }
    except Exception as e:
        logger.exception("get_economic_state failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 10: political state
# ---------------------------------------------------------------------------

def get_political_state(
    country_code: str,
    scenario_code: str = "start_one",
    round_num: Optional[int] = None,
    template_code: str = "ttt_v1_0",
) -> dict:
    """Return political state with annotations for fragility and vulnerability.

    Reads from ``country_states_per_round`` (live) when scenario_code and
    round_num are provided. Falls back to seed tables.
    """
    try:
        client = get_client()
        tpl_result = (
            client.table("sim_templates")
            .select("default_country_stats")
            .eq("code", template_code)
            .execute()
        )
        if not tpl_result.data:
            return {"error": f"Unknown template: {template_code}"}
        stats = (tpl_result.data[0].get("default_country_stats") or {}).get(country_code)
        if not stats:
            return {"error": f"No stats for country {country_code}"}

        # Try live state first
        live = None
        source = "seed"
        if round_num is not None and scenario_code:
            live = _load_live_country_state(scenario_code, round_num, country_code)
            if live:
                source = "live"

        c_result = (
            client.table("countries")
            .select(
                "stability,political_support,war_tiredness,regime_type,"
                # DEPRECATED 2026-04-15: dem_rep_split removed — parliament simplified to 3 seats
                # "dem_rep_split_dem,dem_rep_split_rep,"
                "team_type,team_size_min,team_size_max"
            )
            .eq("id", country_code)
            .execute()
        )
        row = c_result.data[0] if c_result.data else {}

        # Priority: live > country_row > stats_blob
        def pick(key, default=None):
            if live and live.get(key) is not None:
                return live[key]
            v = row.get(key)
            if v is None:
                v = stats.get(key, default)
            return v

        stability = float(pick("stability") or 0)
        support = float(pick("political_support") or 0)
        war_tiredness = float(pick("war_tiredness") or 0)

        annotations: list[str] = []
        if stability < 3:
            annotations.append("regime at collapse risk")
        elif stability < 5:
            annotations.append("fragile")
        if war_tiredness > 6:
            annotations.append("war-exhausted population")
        elif war_tiredness > 3:
            annotations.append("war-weary")
        if support < 30:
            annotations.append("leader highly vulnerable")
        elif support < 40:
            annotations.append("leader vulnerable")

        return {
            "country": country_code,
            "source": source,
            "stability": stability,
            "political_support": support,
            "war_tiredness": war_tiredness,
            "regime_type": pick("regime_type"),
            # DEPRECATED 2026-04-15: dem_rep_split removed — parliament simplified to 3 seats
            # "dem_rep_split": {
            #     "dem": pick("dem_rep_split_dem", 0),
            #     "rep": pick("dem_rep_split_rep", 0),
            # },
            "team_type": pick("team_type"),
            "team_size_min": pick("team_size_min"),
            "team_size_max": pick("team_size_max"),
            "annotations": annotations,
        }
    except Exception as e:
        logger.exception("get_political_state failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 11: tech state
# ---------------------------------------------------------------------------

def get_tech_state(
    country_code: str,
    scenario_code: str = "start_one",
    round_num: Optional[int] = None,
    template_code: str = "ttt_v1_0",
) -> dict:
    """Return tech state (nuclear, AI, missiles) with tier annotations.

    Reads from ``country_states_per_round`` (live) when scenario_code and
    round_num are provided. Falls back to seed tables.
    """
    try:
        client = get_client()
        tpl_result = (
            client.table("sim_templates")
            .select("default_country_stats")
            .eq("code", template_code)
            .execute()
        )
        if not tpl_result.data:
            return {"error": f"Unknown template: {template_code}"}
        stats = (tpl_result.data[0].get("default_country_stats") or {}).get(country_code)
        if not stats:
            return {"error": f"No stats for country {country_code}"}

        # Try live state first
        live = None
        source = "seed"
        if round_num is not None and scenario_code:
            live = _load_live_country_state(scenario_code, round_num, country_code)
            if live:
                source = "live"

        c_result = (
            client.table("countries")
            .select(
                "nuclear_level,nuclear_rd_progress,ai_level,ai_rd_progress,"
                "strategic_missile_growth"
            )
            .eq("id", country_code)
            .execute()
        )
        row = c_result.data[0] if c_result.data else {}

        # Priority: live > country_row > stats_blob
        def pick(key, default=0):
            if live and live.get(key) is not None:
                return live[key]
            v = row.get(key)
            if v is None:
                v = stats.get(key, default)
            return v

        nuc_level = int(pick("nuclear_level") or 0)
        ai_level = int(pick("ai_level") or 0)

        annotations: list[str] = []
        if nuc_level >= 2:
            annotations.append("strategic nuclear power")
        elif nuc_level == 1:
            annotations.append("nascent nuclear capability")
        if ai_level >= 3:
            annotations.append("tech leader (AI)")
        elif ai_level >= 2:
            annotations.append("advanced AI capability")

        return {
            "country": country_code,
            "source": source,
            "nuclear_level": nuc_level,
            "nuclear_rd_progress": float(pick("nuclear_rd_progress") or 0),
            "ai_level": ai_level,
            "ai_rd_progress": float(pick("ai_rd_progress") or 0),
            "strategic_missile_growth": int(pick("strategic_missile_growth") or 0),
            "annotations": annotations,
        }
    except Exception as e:
        logger.exception("get_tech_state failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 12: my identity (canonical HoS role from DB)
# ---------------------------------------------------------------------------

def get_my_identity(country_code: str) -> dict:
    """Return canonical HoS role data from the ``roles`` table.

    Returns character_name, title, parallel, objectives, powers.
    Picks the first is_head_of_state row for this country.
    """
    try:
        client = get_client()
        result = (
            client.table("roles")
            .select(
                "character_name,title,parallel,objectives,powers,country_code"
            )
            .eq("is_head_of_state", True)
            .eq("country_code", country_code)
            .limit(1)
            .execute()
        )
        if not result.data:
            return {"error": f"No head-of-state role found for {country_code}"}
        row = result.data[0]
        return {
            "country_code": country_code,
            "character_name": row.get("character_name"),
            "title": row.get("title"),
            "parallel": row.get("parallel"),
            "objectives": row.get("objectives") or [],
            "powers": row.get("powers") or [],
        }
    except Exception as e:
        logger.exception("get_my_identity failed")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool 13: commit_action (WRITE) — Stage 4
# ---------------------------------------------------------------------------

from engine.agents.action_schemas import ACTION_TYPE_TO_MODEL  # noqa: E402


def _validate_unit_code(country_code: str, unit_code: str,
                        layout_code: str = "template_v1_0_default") -> Optional[str]:
    """Return None if unit belongs to country, else a warning message."""
    try:
        layout_id = _resolve_layout_id(layout_code)
        if not layout_id:
            return f"unknown layout '{layout_code}'"
        client = get_client()
        result = (
            client.table("layout_units")
            .select("unit_code,country_code")
            .eq("layout_id", layout_id)
            .eq("unit_code", unit_code)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return f"unknown unit_code '{unit_code}'"
        if rows[0].get("country_code") != country_code:
            return (
                f"unit '{unit_code}' belongs to "
                f"{rows[0].get('country_code')} not {country_code}"
            )
        return None
    except Exception as e:
        return f"unit validation error: {e}"


def _validate_coords(payload: dict) -> list[str]:
    """Return a list of coord-range warnings for a payload."""
    warnings: list[str] = []
    gr = payload.get("target_global_row")
    gc = payload.get("target_global_col")
    if gr is not None and gc is not None:
        if not in_global_bounds(int(gr), int(gc)):
            warnings.append(
                f"global coords ({gr},{gc}) out of range (1..10 x 1..20)"
            )
    th = payload.get("target_theater")
    tr = payload.get("target_theater_row")
    tc = payload.get("target_theater_col")
    if th and tr is not None and tc is not None:
        if not in_theater_bounds(th, int(tr), int(tc)):
            warnings.append(
                f"theater coords ({tr},{tc}) out of range for {th}"
            )
    return warnings


def commit_action(
    country_code: str,
    scenario_code: str,
    action: dict,
    round_num: int | None = None,
) -> dict:
    """Commit an action to the DB for this round.

    Args:
        country_code: the committing country
        scenario_code: scenario code (e.g. 'start_one')
        action: dict containing action_type + payload matching action_schemas

    Writes to ``agent_decisions``. Returns
    ``{success, action_id, validation_status, validation_notes, action_type}``.

    Validation philosophy: WARN on minor issues (unit ownership drift,
    coord drift) but still commit. REJECT on structural errors (unknown
    action_type, Pydantic validation failure).
    """
    try:
        action_type = action.get("action_type")
        if not action_type:
            return {
                "success": False,
                "validation_status": "rejected",
                "validation_notes": "missing 'action_type' in payload",
            }
        if action_type not in ACTION_TYPE_TO_MODEL:
            return {
                "success": False,
                "validation_status": "rejected",
                "validation_notes": (
                    f"unknown action_type '{action_type}'. "
                    f"Valid: {sorted(ACTION_TYPE_TO_MODEL.keys())}"
                ),
            }

        # Pydantic validation
        model_cls = ACTION_TYPE_TO_MODEL[action_type]
        try:
            validated = model_cls.model_validate(action)
        except Exception as ve:
            return {
                "success": False,
                "validation_status": "rejected",
                "validation_notes": f"schema validation failed: {ve}",
            }

        payload_dict = validated.model_dump()
        warnings: list[str] = []

        # Light validations that only warn
        if action_type == "move_units":
            # CONTRACT_MOVEMENT v1.0 — full validation lives in
            # engine/services/movement_validator.py. The harness skips
            # per-unit warning here because moves are batched.
            pass
        if action_type == "declare_attack":
            for uc in payload_dict.get("attacker_unit_codes", []):
                uw = _validate_unit_code(country_code, uc)
                if uw:
                    warnings.append(uw)

        warnings.extend(_validate_coords(payload_dict))

        validation_status = "warned" if warnings else "passed"
        validation_notes = "; ".join(warnings) if warnings else None

        # Resolve sim_run_id (F1) + denormed scenario_id
        from engine.services.sim_run_manager import (
            resolve_sim_run_id, get_scenario_id_for_run,
        )
        client = get_client()
        try:
            sim_run_id = resolve_sim_run_id(scenario_code)
        except ValueError:
            return {
                "success": False,
                "validation_status": "rejected",
                "validation_notes": f"Cannot resolve '{scenario_code}' to a sim_run",
            }
        scenario_id = get_scenario_id_for_run(sim_run_id)

        rationale = payload_dict.get("rationale", "")

        insert_row = {
            "sim_run_id": sim_run_id,
            "scenario_id": scenario_id,
            "country_code": country_code,
            "action_type": action_type,
            "action_payload": payload_dict,
            "rationale": rationale,
            "validation_status": validation_status,
            "validation_notes": validation_notes,
            "round_num": round_num,
        }
        ins = (
            client.table("agent_decisions")
            .insert(insert_row)
            .execute()
        )
        row = (ins.data or [{}])[0]
        return {
            "success": True,
            "action_id": row.get("id"),
            "action_type": action_type,
            "validation_status": validation_status,
            "validation_notes": validation_notes,
            "warnings": warnings,
        }
    except Exception as e:
        logger.exception("commit_action failed")
        return {
            "success": False,
            "validation_status": "rejected",
            "validation_notes": f"internal error: {e}",
        }


# ---------------------------------------------------------------------------
# Tools 14-16: persistent agent memory (Stage 5)
# ---------------------------------------------------------------------------

def _resolve_sim_run_id(scenario_code: str) -> Optional[str]:
    """Map scenario code to sim_run_id (legacy archived run for the scenario).

    F1: agent_memories is now keyed by sim_run_id. Pre-F1 callers still pass
    a scenario code and get the archived legacy run.
    """
    try:
        from engine.services.sim_run_manager import resolve_sim_run_id as _r
        return _r(scenario_code)
    except Exception:
        return None


def read_memory(
    country_code: str,
    scenario_code: str,
    memory_key: str,
) -> dict:
    """Return content of a single memory row for this agent.

    Returns {exists: bool, content: str|None, round_num: int|None, updated_at: str|None}.
    """
    try:
        sim_run_id = _resolve_sim_run_id(scenario_code)
        if not sim_run_id:
            return {"error": f"Unknown scenario: {scenario_code}"}
        client = get_client()
        result = (
            client.table("agent_memories")
            .select("content,round_num,updated_at")
            .eq("sim_run_id", sim_run_id)
            .eq("country_code", country_code)
            .eq("memory_key", memory_key)
            .execute()
        )
        if not result.data:
            return {"exists": False, "content": None, "memory_key": memory_key}
        row = result.data[0]
        return {
            "exists": True,
            "memory_key": memory_key,
            "content": row.get("content"),
            "round_num": row.get("round_num"),
            "updated_at": row.get("updated_at"),
        }
    except Exception as e:
        logger.exception("read_memory failed")
        return {"error": str(e)}


def list_my_memories(
    country_code: str,
    scenario_code: str,
) -> dict:
    """Return all memory keys for this agent + timestamps + previews (first 200 chars)."""
    try:
        sim_run_id = _resolve_sim_run_id(scenario_code)
        if not sim_run_id:
            return {"error": f"Unknown scenario: {scenario_code}"}
        client = get_client()
        result = (
            client.table("agent_memories")
            .select("memory_key,content,round_num,updated_at")
            .eq("sim_run_id", sim_run_id)
            .eq("country_code", country_code)
            .order("updated_at", desc=True)
            .execute()
        )
        rows = result.data or []
        memories = [
            {
                "memory_key": r["memory_key"],
                "round_num": r.get("round_num"),
                "updated_at": r.get("updated_at"),
                "preview": (r.get("content") or "")[:200],
            }
            for r in rows
        ]
        return {
            "country": country_code,
            "scenario": scenario_code,
            "memory_count": len(memories),
            "memories": memories,
        }
    except Exception as e:
        logger.exception("list_my_memories failed")
        return {"error": str(e)}


def write_memory(
    country_code: str,
    scenario_code: str,
    memory_key: str,
    content: str,
    round_num: Optional[int] = None,
) -> dict:
    """UPSERT a memory row for this agent. Returns {success, memory_id}."""
    try:
        from engine.services.sim_run_manager import (
            resolve_sim_run_id, get_scenario_id_for_run,
        )
        try:
            sim_run_id = resolve_sim_run_id(scenario_code)
        except ValueError:
            return {"success": False, "error": f"Unknown scenario: {scenario_code}"}
        scenario_id = get_scenario_id_for_run(sim_run_id)
        if not memory_key or not isinstance(memory_key, str):
            return {"success": False, "error": "memory_key is required"}
        if content is None:
            return {"success": False, "error": "content is required"}
        from datetime import datetime, timezone
        client = get_client()
        row = {
            "sim_run_id": sim_run_id,
            "scenario_id": scenario_id,
            "country_code": country_code,
            "memory_key": memory_key,
            "content": content,
            "round_num": round_num,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        # UPSERT on composite unique constraint (F1: now keyed by sim_run_id)
        result = (
            client.table("agent_memories")
            .upsert(row, on_conflict="sim_run_id,country_code,memory_key")
            .execute()
        )
        data = (result.data or [{}])[0]
        return {
            "success": True,
            "memory_id": data.get("id"),
            "memory_key": memory_key,
            "round_num": round_num,
        }
    except Exception as e:
        logger.exception("write_memory failed")
        return {"success": False, "error": str(e)}


__all__ = [
    "get_my_forces",
    "get_hex_info",
    "get_enemy_forces",
    "get_strategic_context",
    "get_template_info",
    "get_relationships",
    "get_organization_memberships",
    "get_country_codes_list",
    "get_economic_state",
    "get_political_state",
    "get_tech_state",
    "get_my_identity",
    "commit_action",
    "read_memory",
    "list_my_memories",
    "write_memory",
]
