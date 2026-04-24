"""FastAPI entry point — TTT Engine API.

Health check, SIM state queries, auth admin endpoints, LLM test endpoint.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine.auth.models import AuthUser
from engine.auth.dependencies import get_current_user, require_moderator
from engine.config import settings
from engine.models.api import (
    APIResponse, HealthStatus, LLMTestRequest, LLMTestResponse, CountryListResponse,
    ActionSubmission, SimRunCreateRequest,
)
from engine.services import supabase as db
from engine.services import llm
from engine.config.settings import LLMUseCase

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("TTT Engine starting — env=%s", settings.app_env)
    logger.info("Supabase: %s", settings.supabase_url)
    logger.info("Anthropic: %s", "configured" if settings.has_anthropic else "NOT configured")
    logger.info("Gemini: %s", "configured" if settings.has_gemini else "NOT configured")

    import asyncio

    # No auto-reconnect on server startup.
    # After server restart, moderator must click "Initialize AI Agents" again.
    # This prevents stale/archived sessions from being reused.
    logger.info("Server started. AI agents require manual initialization via dashboard.")

    yield

    # Shutdown all dispatchers on exit
    from engine.agents.managed.event_dispatcher import _dispatchers
    for d in list(_dispatchers.values()):
        try:
            await d.stop()
        except Exception:
            pass
    logger.info("TTT Engine shutting down")


app = FastAPI(
    title="Thucydides Trap Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", response_model=APIResponse)
async def health():
    """Infrastructure health check."""
    db_ok = await db.check_connection()
    anthropic_ok = await llm.check_anthropic()
    gemini_ok = await llm.check_gemini()

    status = HealthStatus(
        status="ok" if db_ok else "degraded",
        db="connected" if db_ok else "error",
        llm_anthropic="ok" if anthropic_ok else "unavailable",
        llm_gemini="ok" if gemini_ok else "unavailable",
        sim_id=settings.default_sim_id,
        version="0.1.0",
    )
    return APIResponse(success=db_ok, data=status.model_dump())


# ---------------------------------------------------------------------------
# SIM state endpoints
# ---------------------------------------------------------------------------

@app.get("/api/sim/{sim_id}/countries", response_model=APIResponse)
async def get_countries(sim_id: str):
    """Get all countries for a SIM run."""
    countries = await db.get_countries(sim_id)
    if not countries:
        raise HTTPException(status_code=404, detail=f"No countries found for SIM {sim_id}")
    return APIResponse(
        data=CountryListResponse(
            sim_id=sim_id,
            count=len(countries),
            countries=[c.model_dump() for c in countries],
        ).model_dump()
    )


@app.get("/api/sim/{sim_id}/country/{country_id}", response_model=APIResponse)
async def get_country(sim_id: str, country_id: str):
    """Get a single country's full state."""
    country = await db.get_country(sim_id, country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")
    return APIResponse(data=country.model_dump())


@app.get("/api/sim/{sim_id}/roles", response_model=APIResponse)
async def get_roles(sim_id: str, country_id: Optional[str] = None):
    """Get roles, optionally filtered by country."""
    roles = await db.get_roles(sim_id, country_id)
    return APIResponse(data=[r.model_dump() for r in roles], meta={"count": len(roles)})


@app.get("/api/sim/{sim_id}/zones", response_model=APIResponse)
async def get_zones(sim_id: str, theater: Optional[str] = None):
    """Get map zones, optionally filtered by theater."""
    zones = await db.get_zones(sim_id, theater)
    return APIResponse(data=[z.model_dump() for z in zones], meta={"count": len(zones)})


@app.get("/api/sim/{sim_id}/deployments", response_model=APIResponse)
async def get_deployments(
    sim_id: str,
    country_id: Optional[str] = None,
    global_row: Optional[int] = None,
    global_col: Optional[int] = None,
):
    """Get military deployments with optional filters (by country, hex coordinates)."""
    deployments = await db.get_deployments(sim_id, country_id, global_row, global_col)
    return APIResponse(data=[d.model_dump() for d in deployments], meta={"count": len(deployments)})


@app.get("/api/sim/{sim_id}/units/my")
async def get_my_units(
    sim_id: str,
    country: str,
    user: AuthUser = Depends(get_current_user),
):
    """Get all units for a country grouped by status — active, reserve, embarked.

    Used by the move_units UI to show available units for deployment/reposition.
    """
    from engine.services.supabase import get_client
    client = get_client()

    deps = client.table("deployments") \
        .select("unit_id, country_code, unit_type, unit_status, global_row, global_col, "
                "theater, theater_row, theater_col, embarked_on") \
        .eq("sim_run_id", sim_id) \
        .eq("country_code", country) \
        .neq("unit_status", "destroyed") \
        .execute().data or []

    active = []
    reserve = []
    embarked = []
    for d in deps:
        item = {
            "unit_id": d["unit_id"],
            "unit_type": d["unit_type"],
            "status": d["unit_status"],
            "global_row": d.get("global_row"),
            "global_col": d.get("global_col"),
            "theater": d.get("theater"),
            "theater_row": d.get("theater_row"),
            "theater_col": d.get("theater_col"),
            "embarked_on": d.get("embarked_on"),
        }
        if d["unit_status"] == "active":
            active.append(item)
        elif d["unit_status"] == "reserve":
            reserve.append(item)
        elif d["unit_status"] == "embarked":
            embarked.append(item)

    return {
        "active": active,
        "reserve": reserve,
        "embarked": embarked,
        "total": len(deps),
    }


@app.get("/api/sim/{sim_id}/map/units")
async def get_map_units(sim_id: str):
    """Get deployments for the map renderer — coordinates stored directly on each unit.

    Returns {units: [...]} with global_row/global_col and theater coordinates.
    No zone_id lookup needed — coordinates are canonical on each deployment row.
    """
    from engine.services.supabase import get_client
    client = get_client()

    deps = client.table("deployments") \
        .select("unit_id, country_code, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, unit_status") \
        .eq("sim_run_id", sim_id) \
        .execute().data or []

    units = [{
        "unit_id": d.get("unit_id", ""),
        "country_code": d["country_code"],
        "unit_type": d["unit_type"],
        "global_row": d.get("global_row"),
        "global_col": d.get("global_col"),
        "theater": d.get("theater"),
        "theater_row": d.get("theater_row"),
        "theater_col": d.get("theater_col"),
        "embarked_on": d.get("embarked_on"),
        "status": d.get("unit_status", "active"),
        "count": 1,
    } for d in deps]

    active = sum(1 for u in units if u["status"] == "active")
    mapped = sum(1 for u in units if u["global_row"] is not None)
    return {"units": units, "count": len(units), "active": active, "mapped": mapped}


@app.get("/api/sim/{sim_id}/map/hex-control")
async def get_hex_control(sim_id: str):
    """Get all occupied hexes for the map renderer.

    Returns list of hexes where controlled_by differs from owner.
    Used by map-core.js to render occupation stripes.
    """
    from engine.services.supabase import get_client
    client = get_client()
    rows = client.table("hex_control") \
        .select("global_row, global_col, theater, theater_row, theater_col, owner, controlled_by") \
        .eq("sim_run_id", sim_id) \
        .not_.is_("controlled_by", "null") \
        .execute().data or []
    return {"hexes": rows, "count": len(rows)}


@app.get("/api/sim/{sim_id}/map/blockades")
async def get_map_blockades(sim_id: str):
    """Get active blockades for map rendering. Public — no auth needed."""
    from engine.services.supabase import get_client
    from engine.config.map_config import CHOKEPOINTS
    client = get_client()
    blockades = client.table("blockades").select("zone_id, imposer_country_code, level") \
        .eq("sim_run_id", sim_id).eq("status", "active").execute().data or []
    result = []
    for b in blockades:
        cp = CHOKEPOINTS.get(b["zone_id"])
        if cp:
            result.append({
                "zone_id": b["zone_id"],
                "name": cp["name"],
                "hex": list(cp["hex"]),
                "imposer": b["imposer_country_code"],
                "level": b["level"],
            })
    return {"blockades": result, "count": len(result)}


@app.get("/api/sim/{sim_id}/map/combat-events")
async def get_map_combat_events(sim_id: str, round_num: int = 1):
    """Get combat events with hex coordinates for blast markers on the map."""
    from engine.services.supabase import get_client
    client = get_client()

    COMBAT_TYPES = {'ground_attack', 'ground_move', 'air_strike', 'naval_combat', 'naval_bombardment', 'launch_missile_conventional', 'nuclear_test', 'nuclear_launch'}

    evts = client.table("observatory_events") \
        .select("event_type, payload, country_code") \
        .eq("sim_run_id", sim_id) \
        .eq("round_num", round_num) \
        .execute().data or []

    # Batch-load theater coords for all deployments in this sim (avoids N+1 per event)
    deps = client.table("deployments") \
        .select("global_row, global_col, theater, theater_row, theater_col") \
        .eq("sim_run_id", sim_id) \
        .execute().data or []
    # Index: (global_row, global_col, theater) → (theater_row, theater_col)
    theater_coord_map: dict[tuple, tuple] = {}
    for d in deps:
        key = (d.get("global_row"), d.get("global_col"), d.get("theater"))
        if d.get("theater_row") is not None and d.get("theater_col") is not None:
            theater_coord_map[key] = (d["theater_row"], d["theater_col"])

    combat = []
    seen_hexes = set()
    for e in evts:
        if e["event_type"] not in COMBAT_TYPES:
            continue
        p = e.get("payload") or {}

        # Nuclear launch: markers come from hit_details, not generic coords
        if e["event_type"] == "nuclear_launch":
            hit_details = p.get("hit_details") or []
            for hit in hit_details:
                target = hit.get("target")
                if target and len(target) >= 2:
                    hit_hex = (target[0], target[1])
                    if hit_hex not in seen_hexes:
                        seen_hexes.add(hit_hex)
                        combat.append({
                            "event_type": "nuclear_launch",
                            "combat_type": "nuclear_launch",
                            "global_row": target[0],
                            "global_col": target[1],
                            "theater": None,
                            "theater_row": None,
                            "theater_col": None,
                        })
            continue

        # Target coords can be at payload root, in action, or in result
        action = p.get("action", {})
        result = p.get("result", {})
        tr = p.get("target_row") or action.get("target_row") or result.get("target_global_row")
        tc = p.get("target_col") or action.get("target_col") or result.get("target_global_col")
        theater = p.get("theater") or action.get("theater")
        if tr is None or tc is None:
            continue
        hex_key = (tr, tc)
        if hex_key in seen_hexes:
            continue  # One marker per hex
        seen_hexes.add(hex_key)

        # Theater coords: from action payload first, then deployment lookup
        theater_row = action.get("target_theater_row")
        theater_col = action.get("target_theater_col")
        if theater and not theater_row:
            cached = theater_coord_map.get((tr, tc, theater))
            if cached:
                theater_row, theater_col = cached

        entry = {
            "event_type": e["event_type"],
            "global_row": tr,
            "global_col": tc,
            "theater": theater,
            "theater_row": theater_row,
            "theater_col": theater_col,
        }
        # Nuclear test: pass combat_type + test_type so map renders ☢ for surface tests
        if e["event_type"] == "nuclear_test":
            entry["combat_type"] = "nuclear_test"
            entry["test_type"] = p.get("test_type", "underground")
        # nuclear_launch is handled above (early continue), should not reach here
        combat.append(entry)

    return {"events": combat, "count": len(combat)}


def _append_targets(targets: list, utype: str, enemies: list, row: int, col: int, theater_info: dict, is_sea: bool = False):
    """Append valid attack targets based on attacker unit type."""
    if utype == "ground":
        if is_sea:
            return  # ground cannot enter sea hexes
        ground_enemies = [e for e in enemies if e["unit_type"] == "ground"]
        non_ground = [e for e in enemies if e["unit_type"] != "ground" and e["unit_type"] != "naval"]  # can't capture naval
        if ground_enemies:
            # Contested — ground combat (non-ground captured on victory)
            targets.append({"row": row, "col": col, **theater_info, "attack_type": "ground_attack", "enemies": enemies})
        elif non_ground:
            # Undefended — walk in, capture non-ground units as trophies
            targets.append({"row": row, "col": col, **theater_info, "attack_type": "ground_move", "enemies": non_ground})
    elif utype == "tactical_air":
        targets.append({"row": row, "col": col, **theater_info, "attack_type": "air_strike", "enemies": enemies})
    elif utype == "naval":
        naval = [e for e in enemies if e["unit_type"] == "naval"]
        ground = [e for e in enemies if e["unit_type"] == "ground"]
        if naval:
            targets.append({"row": row, "col": col, **theater_info, "attack_type": "naval_combat", "enemies": naval})
        if ground:
            targets.append({"row": row, "col": col, **theater_info, "attack_type": "naval_bombardment", "enemies": ground})
    elif utype == "strategic_missile":
        from engine.config.map_config import NUCLEAR_SITES
        nuc_site = any(pos == (row, col) for pos in NUCLEAR_SITES.values())
        targets.append({"row": row, "col": col, **theater_info, "attack_type": "launch_missile_conventional", "enemies": enemies, "has_nuclear_site": nuc_site})


@app.get("/api/sim/{sim_id}/attack/valid-targets")
async def get_valid_attack_targets(
    sim_id: str,
    unit_id: str,
    theater: Optional[str] = None,
    user: AuthUser = Depends(get_current_user),
):
    """Return hexes a unit can attack, plus units at source hex for selection.

    When ``theater`` is provided, adjacency is computed in theater coordinates
    (10x10 grid) instead of global coordinates. This is required for theater-level
    combat where multiple theater cells map to the same global hex.

    For ground/naval/air: returns reachable hexes that contain enemy units.
    For naval: also distinguishes naval_combat vs bombardment targets.
    For strategic_missile: all hexes with enemy units (global range).

    Response: {source, unit, attack_type, targets: [{row, col, enemies: [...]}]}
    """
    from engine.services.supabase import get_client
    from engine.config.map_config import hex_range, ATTACK_RANGE, is_sea_hex

    client = get_client()

    # Load the selected unit (active or embarked)
    dep = client.table("deployments") \
        .select("*") \
        .eq("sim_run_id", sim_id) \
        .eq("unit_id", unit_id) \
        .in_("unit_status", ["active", "embarked"]) \
        .limit(1).execute().data
    if not dep:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found or not active/embarked")
    unit = dep[0]

    utype = unit["unit_type"]
    country = unit["country_code"]
    src_row = unit.get("global_row")
    src_col = unit.get("global_col")

    # Embarked units: resolve position from carrier
    if src_row is None or src_col is None:
        carrier_id = unit.get("embarked_on")
        if carrier_id:
            carrier = client.table("deployments") \
                .select("global_row,global_col") \
                .eq("sim_run_id", sim_id) \
                .eq("unit_id", carrier_id) \
                .eq("unit_status", "active") \
                .limit(1).execute().data
            if carrier:
                src_row = carrier[0]["global_row"]
                src_col = carrier[0]["global_col"]
    if src_row is None or src_col is None:
        raise HTTPException(status_code=400, detail="Unit has no map position (and no carrier found)")

    # Get attack range and compute reachable hexes (pure math, instant)
    attack_range = ATTACK_RANGE.get(utype, 1)
    # Missile range depends on country's nuclear_level
    if utype == "strategic_missile":
        from engine.config.map_config import missile_range
        nuc_data = client.table("countries").select("nuclear_level").eq("sim_run_id", sim_id).eq("id", country).limit(1).execute().data
        nuc_level = nuc_data[0].get("nuclear_level", 0) if nuc_data else 0
        attack_range = missile_range(nuc_level)
    from engine.config.map_config import THEATERS

    use_theater = theater and unit.get("theater") == theater and unit.get("theater_row") is not None

    if use_theater:
        t_row = unit["theater_row"]
        t_col = unit["theater_col"]
        t_info = THEATERS.get(theater, {"rows": 10, "cols": 10})
        reachable = hex_range(t_row, t_col, attack_range, t_info["rows"], t_info["cols"])
    else:
        reachable = hex_range(src_row, src_col, attack_range)

    # Load enemies — filter by theater or sim, then intersect with reachable set in Python
    sel_cols = "unit_id, country_code, unit_type, global_row, global_col, theater, theater_row, theater_col"
    reachable_set = set(reachable)
    if use_theater:
        all_in_theater = client.table("deployments").select(sel_cols) \
            .eq("sim_run_id", sim_id).eq("theater", theater) \
            .neq("country_code", country).eq("unit_status", "active") \
            .execute().data or []
        all_enemies = [e for e in all_in_theater if (e.get("theater_row"), e.get("theater_col")) in reachable_set]
    else:
        all_in_sim = client.table("deployments").select(sel_cols) \
            .eq("sim_run_id", sim_id) \
            .neq("country_code", country).eq("unit_status", "active") \
            .execute().data or []
        all_enemies = [e for e in all_in_sim if (e.get("global_row"), e.get("global_col")) in reachable_set]

    # For ground units: also load own units at reachable hexes (to exclude own-occupied hexes for advance)
    own_hexes: set[tuple[int, int]] = set()
    if utype == "ground":
        if use_theater:
            own_in_theater = client.table("deployments").select("theater_row, theater_col") \
                .eq("sim_run_id", sim_id).eq("theater", theater) \
                .eq("country_code", country).eq("unit_status", "active").execute().data or []
            own_hexes = {(u["theater_row"], u["theater_col"]) for u in own_in_theater if u.get("theater_row")}
        else:
            own_in_sim = client.table("deployments").select("global_row, global_col") \
                .eq("sim_run_id", sim_id).eq("country_code", country).eq("unit_status", "active").execute().data or []
            own_hexes = {(u["global_row"], u["global_col"]) for u in own_in_sim if u.get("global_row")}

    # Group enemies by hex
    targets = []
    if use_theater:
        enemy_by_hex: dict[tuple[int, int], list[dict]] = {}
        for e in all_enemies:
            enemy_by_hex.setdefault((e.get("theater_row", 0), e.get("theater_col", 0)), []).append(e)
        for r, c in reachable:
            enemies_here = enemy_by_hex.get((r, c), [])
            theater_info = {"theater": theater, "theater_row": r, "theater_col": c}
            if enemies_here:
                sample = enemies_here[0]
                g_row = sample.get("global_row", src_row)
                g_col = sample.get("global_col", src_col)
                _append_targets(targets, utype, enemies_here, g_row, g_col, theater_info, is_sea=is_sea_hex(r, c, theater))
            elif utype == "ground" and (r, c) not in own_hexes and not is_sea_hex(r, c, theater):
                # Empty land hex — ground can advance (no combat)
                targets.append({"row": src_row, "col": src_col, **theater_info, "attack_type": "ground_move", "enemies": []})
            elif utype == "strategic_missile" and not is_sea_hex(r, c, theater):
                from engine.config.map_config import NUCLEAR_SITES
                # Theater: need to resolve global coords for nuclear site check
                nuc_site = False  # theater hexes don't have direct nuclear site mapping yet
                targets.append({"row": src_row, "col": src_col, **theater_info, "attack_type": "launch_missile_conventional", "enemies": [], "has_nuclear_site": nuc_site})
    else:
        enemy_by_hex = {}
        for e in all_enemies:
            enemy_by_hex.setdefault((e.get("global_row", 0), e.get("global_col", 0)), []).append(e)
        for r, c in reachable:
            enemies_here = enemy_by_hex.get((r, c), [])
            if enemies_here:
                sample = enemies_here[0]
                theater_info = {}
                if sample.get("theater"):
                    theater_info = {"theater": sample["theater"], "theater_row": sample.get("theater_row"), "theater_col": sample.get("theater_col")}
                _append_targets(targets, utype, enemies_here, r, c, theater_info, is_sea=is_sea_hex(r, c))
            elif utype == "ground" and (r, c) not in own_hexes and not is_sea_hex(r, c):
                # Empty land hex — ground can advance
                targets.append({"row": r, "col": c, "attack_type": "ground_move", "enemies": []})
            elif utype == "strategic_missile" and not is_sea_hex(r, c):
                from engine.config.map_config import hex_owner as get_hex_owner, NUCLEAR_SITES
                owner = get_hex_owner(r, c)
                if owner != "sea" and owner != country:
                    nuc_site = any(pos == (r, c) for pos in NUCLEAR_SITES.values())
                    targets.append({"row": r, "col": c, "attack_type": "launch_missile_conventional", "enemies": [], "has_nuclear_site": nuc_site})

    # Friendlies at source (single query)
    if use_theater:
        friendlies_at_source = client.table("deployments") \
            .select("unit_id, unit_type") \
            .eq("sim_run_id", sim_id).eq("country_code", country) \
            .eq("theater", theater).eq("theater_row", t_row).eq("theater_col", t_col) \
            .in_("unit_status", ["active", "embarked"]) \
            .execute().data or []
    else:
        friendlies_at_source = client.table("deployments") \
            .select("unit_id, unit_type") \
            .eq("sim_run_id", sim_id).eq("country_code", country) \
            .eq("global_row", src_row).eq("global_col", src_col) \
            .in_("unit_status", ["active", "embarked"]) \
            .execute().data or []

    # Check which units at source already attacked this round (naval/air: once per round)
    units_attacked_this_round: list[str] = []
    if utype in ("naval", "tactical_air"):
        run_data = client.table("sim_runs").select("current_round").eq("id", sim_id).limit(1).execute().data
        current_round = run_data[0]["current_round"] if run_data else 0
        combat_types = ["naval_combat", "naval_bombardment"] if utype == "naval" else ["air_strike"]
        combat_evts = client.table("observatory_events") \
            .select("payload") \
            .eq("sim_run_id", sim_id).eq("round_num", current_round) \
            .eq("country_code", country) \
            .in_("event_type", combat_types) \
            .execute().data or []
        for evt in combat_evts:
            action = (evt.get("payload") or {}).get("action", {})
            codes = action.get("attacker_unit_codes") or []
            code = action.get("attacker_unit_code")
            if code: codes = [code] if isinstance(code, str) else codes
            units_attacked_this_round.extend(codes)
        units_attacked_this_round = list(set(units_attacked_this_round))

    return {
        "source": {"row": src_row, "col": src_col,
                   "theater": unit.get("theater"), "theater_row": unit.get("theater_row"), "theater_col": unit.get("theater_col")},
        "unit": {"unit_id": unit["unit_id"], "unit_type": utype, "country_code": country},
        "friendlies_at_source": friendlies_at_source,
        "units_attacked_this_round": units_attacked_this_round,
        "targets": targets,
    }


@app.get("/api/sim/{sim_id}/attack/preview")
async def get_attack_preview(
    sim_id: str,
    attacker_unit_ids: str,
    target_row: int,
    target_col: int,
    attack_type: str,
    user: AuthUser = Depends(get_current_user),
):
    """Return combat modifiers and estimated win probability for a planned attack.

    Query params:
        attacker_unit_ids: comma-separated unit_ids (e.g. "sar_g_15,sar_g_16")
        target_row, target_col: target hex (1-indexed)
        attack_type: ground_attack | air_strike | naval_combat | naval_bombardment | launch_missile_conventional
    """
    from engine.services.supabase import get_client

    client = get_client()
    unit_ids = [u.strip() for u in attacker_unit_ids.split(",") if u.strip()]

    # Load attacker units (active or embarked)
    atk_deps = client.table("deployments").select("unit_id,country_code,unit_type,global_row,global_col") \
        .eq("sim_run_id", sim_id).in_("unit_status", ["active", "embarked"]).in_("unit_id", unit_ids).execute().data or []
    if not atk_deps:
        raise HTTPException(status_code=404, detail="Attacker units not found")

    attacker_country = atk_deps[0]["country_code"]
    atk_count = len(atk_deps)

    # Load defender units at target hex
    def_deps = client.table("deployments").select("unit_id,country_code,unit_type,global_row,global_col") \
        .eq("sim_run_id", sim_id).eq("global_row", target_row).eq("global_col", target_col) \
        .eq("unit_status", "active").neq("country_code", attacker_country).execute().data or []

    # Filter by attack type
    if attack_type == "ground_attack":
        def_ground = [d for d in def_deps if d["unit_type"] == "ground"]
        def_count = len(def_ground)
    elif attack_type == "naval_combat":
        def_naval = [d for d in def_deps if d["unit_type"] == "naval"]
        def_count = len(def_naval)
    elif attack_type == "air_strike":
        def_count = len(def_deps)  # air can hit anything
    else:
        def_count = len(def_deps)

    # Load country data for modifiers
    atk_country = client.table("countries").select("stability,ai_level,nuclear_level") \
        .eq("sim_run_id", sim_id).eq("id", attacker_country).limit(1).execute().data
    atk_stability = atk_country[0]["stability"] if atk_country else 5.0
    atk_ai = atk_country[0].get("ai_level", 0) if atk_country else 0

    defender_countries = list(set(d["country_code"] for d in def_deps))
    def_stability = 5.0
    def_ai = 0
    if defender_countries:
        def_country = client.table("countries").select("stability,ai_level") \
            .eq("sim_run_id", sim_id).eq("id", defender_countries[0]).limit(1).execute().data
        if def_country:
            def_stability = def_country[0]["stability"]
            def_ai = def_country[0].get("ai_level", 0)

    # Check for air defense at target hex
    ad_at_target = [d for d in def_deps if d["unit_type"] == "air_defense"]
    has_ad = len(ad_at_target) > 0

    # Build modifier breakdown
    modifiers = {"attacker": [], "defender": []}
    atk_total = 0
    def_total = 0

    if attack_type in ("ground_attack", "naval_combat"):
        # AI L4 bonus
        if atk_ai >= 4:
            modifiers["attacker"].append({"label": "AI Level 4", "value": +1})
            atk_total += 1
        if def_ai >= 4:
            modifiers["defender"].append({"label": "AI Level 4", "value": +1})
            def_total += 1
        # Low morale
        if atk_stability <= 3:
            modifiers["attacker"].append({"label": "Low morale (stability ≤3)", "value": -1})
            atk_total -= 1
        if def_stability <= 3:
            modifiers["defender"].append({"label": "Low morale (stability ≤3)", "value": -1})
            def_total -= 1
        # Die hard / air support (ground only, simplified — would need zone data)
        if attack_type == "ground_attack":
            # Check for defender air at target
            def_air_at_target = [d for d in def_deps if d["unit_type"] == "tactical_air"]
            if def_air_at_target:
                modifiers["defender"].append({"label": "Air support", "value": +1})
                def_total += 1

    # Estimate win probability
    win_pct = 50  # base
    if attack_type == "ground_move":
        win_pct = 100  # unopposed advance
    elif attack_type == "ground_attack" and def_count == 0:
        win_pct = 100  # no defenders
    elif attack_type == "ground_attack":
        # RISK dice: documented rates from contract
        # No mods: ~42% attacker. Def+1: ~28%. Def+2: ~17%. Atk-1 + Def+2: ~8%
        net_mod = atk_total - def_total  # positive favors attacker
        base_rates = {0: 42, 1: 55, 2: 65, -1: 28, -2: 17, -3: 8}
        win_pct = base_rates.get(net_mod, max(5, min(85, 42 + net_mod * 13)))
        # Adjust for unit count advantage
        if atk_count > def_count:
            win_pct = min(90, win_pct + (atk_count - def_count) * 8)
        elif def_count > atk_count:
            win_pct = max(5, win_pct - (def_count - atk_count) * 10)
    elif attack_type == "air_strike":
        hit_pct = 6 if has_ad else 12  # per aircraft
        downed_pct = 15 if has_ad else 0
        win_pct = min(95, hit_pct * atk_count)
        modifiers["attacker"].append({"label": f"Hit chance per aircraft", "value": f"{hit_pct}%"})
        if has_ad:
            modifiers["attacker"].append({"label": f"Downed chance per aircraft", "value": f"-{downed_pct}%"})
            modifiers["defender"].append({"label": "Air Defense present", "value": "halves hit rate"})
    elif attack_type == "naval_combat":
        # 1v1 dice — ~42% attacker without mods
        net_mod = atk_total - def_total
        base_rates = {0: 42, 1: 58, -1: 28, 2: 72, -2: 17}
        win_pct = base_rates.get(net_mod, max(5, min(85, 42 + net_mod * 15)))
    elif attack_type == "naval_bombardment":
        win_pct = min(95, 10 * atk_count)
        modifiers["attacker"].append({"label": "Hit chance per naval unit", "value": "10%"})

    return {
        "attack_type": attack_type,
        "attacker": {"country": attacker_country, "units": atk_count, "modifier_total": atk_total},
        "defender": {"countries": defender_countries, "units": def_count, "modifier_total": def_total},
        "modifiers": modifiers,
        "win_probability": win_pct,
        "has_air_defense": has_ad,
    }


@app.get("/api/sim/{sim_id}/world", response_model=APIResponse)
async def get_world_state(sim_id: str, round_num: Optional[int] = None):
    """Get world state snapshot."""
    world = await db.get_world_state(sim_id, round_num)
    if not world:
        raise HTTPException(status_code=404, detail="World state not found")
    return APIResponse(data=world.model_dump())


@app.get("/api/sim/{sim_id}/relationships", response_model=APIResponse)
async def get_relationships(sim_id: str, country_id: Optional[str] = None):
    """Get bilateral relationships."""
    rels = await db.get_relationships(sim_id, country_id)
    return APIResponse(data=[r.model_dump() for r in rels], meta={"count": len(rels)})


@app.get("/api/sim/{sim_id}/sanctions", response_model=APIResponse)
async def get_sanctions(sim_id: str):
    """Get all active sanctions."""
    sanctions = await db.get_sanctions(sim_id)
    return APIResponse(data=[s.model_dump() for s in sanctions], meta={"count": len(sanctions)})


@app.get("/api/sim/{sim_id}/organizations", response_model=APIResponse)
async def get_organizations(sim_id: str):
    """Get all organizations and memberships."""
    orgs = await db.get_organizations(sim_id)
    memberships = await db.get_org_memberships(sim_id)
    return APIResponse(
        data={
            "organizations": [o.model_dump() for o in orgs],
            "memberships": [m.model_dump() for m in memberships],
        },
        meta={"org_count": len(orgs), "membership_count": len(memberships)},
    )


# ---------------------------------------------------------------------------
# LLM test endpoint
# ---------------------------------------------------------------------------

@app.post("/api/test/llm", response_model=APIResponse)
async def test_llm(request: LLMTestRequest):
    """Test LLM connectivity. Sends a prompt and returns the response."""
    try:
        result = await llm.call_llm(
            use_case=LLMUseCase.QUICK_SCAN,
            messages=[{"role": "user", "content": request.prompt}],
        )
        return APIResponse(
            data=LLMTestResponse(
                provider=result.provider,
                model=result.model,
                response_text=result.text,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
            ).model_dump()
        )
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@app.get("/api/llm/health", response_model=APIResponse)
async def llm_health():
    """Get LLM provider health statistics."""
    return APIResponse(data=llm.get_health_stats())


# ---------------------------------------------------------------------------
# Auth endpoints (M10.1)
# ---------------------------------------------------------------------------

@app.get("/api/auth/me", response_model=APIResponse)
async def get_me(user: AuthUser = Depends(get_current_user)):
    """Get current user's profile."""
    return APIResponse(data=user.model_dump())


@app.get("/api/admin/users", response_model=APIResponse)
async def list_users(user: AuthUser = Depends(require_moderator)):
    """List all registered users. Moderator only."""
    from supabase import create_client

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    result = (
        client.table("users")
        .select("id, email, display_name, system_role, status, data_consent, created_at, last_login_at")
        .order("created_at", desc=True)
        .execute()
    )
    return APIResponse(
        data=result.data,
        meta={"count": len(result.data)},
    )


@app.post("/api/admin/users/{user_id}/approve", response_model=APIResponse)
async def approve_user(
    user_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Approve a pending moderator. Moderator only."""
    from supabase import create_client

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    # Verify user exists and is pending
    check = (
        client.table("users")
        .select("id, status, system_role")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="User not found")
    if check.data["status"] != "pending_approval":
        raise HTTPException(status_code=400, detail="User is not pending approval")

    # Approve
    result = (
        client.table("users")
        .update({"status": "active"})
        .eq("id", user_id)
        .execute()
    )
    logger.info("User %s approved by moderator %s", user_id, user.id)
    return APIResponse(data={"approved": True, "user_id": user_id})


@app.post("/api/admin/users/{user_id}/suspend", response_model=APIResponse)
async def suspend_user(
    user_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Suspend a user. Moderator only."""
    from supabase import create_client

    if user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    result = (
        client.table("users")
        .update({"status": "suspended"})
        .eq("id", user_id)
        .execute()
    )
    logger.info("User %s suspended by moderator %s", user_id, user.id)
    return APIResponse(data={"suspended": True, "user_id": user_id})


# ---------------------------------------------------------------------------
# M9/M4: SimRun Creation (full data inheritance)
# ---------------------------------------------------------------------------

@app.post("/api/sim/create", response_model=APIResponse)
async def create_sim_run(body: SimRunCreateRequest, user: AuthUser = Depends(require_moderator)):
    """Create a new SimRun with full data inheritance from source sim.

    Copies all 11 game tables (countries, roles, zones, deployments, etc.)
    from the source sim and applies wizard customizations (active/AI flags).
    """
    from engine.services.sim_create import create_sim_run as do_create
    try:
        result = do_create(
            name=body.name,
            source_sim_id=body.source_sim_id,
            template_id=body.template_id,
            facilitator_id=user.id,
            schedule=body.schedule,
            key_events=body.key_events,
            max_rounds=body.max_rounds,
            description=body.description,
            logo_url=body.logo_url,
            role_customizations=[rc.model_dump() for rc in body.role_customizations],
        )
        logger.info("SimRun created: %s by %s", result["id"], user.id)
        return APIResponse(data=result)
    except Exception as e:
        logger.exception("SimRun creation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# M4: Sim Runner — Facilitator Control Endpoints
# ---------------------------------------------------------------------------

_state_cache: dict[str, tuple[float, dict]] = {}

@app.get("/api/sim/{sim_id}/blockades", response_model=APIResponse)
async def get_blockades(sim_id: str, country: Optional[str] = None, user: AuthUser = Depends(get_current_user)):
    """Return all active blockades and per-chokepoint capability for the user's country."""
    from engine.services.supabase import get_client
    from engine.services.blockade_engine import get_blockade_status, _qualifying_units
    from engine.config.map_config import CHOKEPOINTS

    client = get_client()

    # Resolve user's country (from query param or user_id lookup)
    user_country = country
    if not user_country:
        role = client.table("roles").select("country_code") \
            .eq("sim_run_id", sim_id).eq("user_id", user.id) \
            .limit(1).execute().data
        user_country = role[0]["country_code"] if role else None

    active_blockades = get_blockade_status(sim_id)

    # Build per-chokepoint info
    chokepoints = []
    for cp_id, cp in CHOKEPOINTS.items():
        entry: dict = {
            "id": cp_id,
            "name": cp["name"],
            "hex": list(cp["hex"]),
            "ground_ok": cp["ground_ok"],
            "blockade": None,
            "can_establish": False,
        }
        # Check if there's an active blockade here
        for b in active_blockades:
            if b["zone_id"] == cp_id:
                entry["blockade"] = {
                    "imposer": b["imposer_country_code"],
                    "level": b["level"],
                    "established_round": b["established_round"],
                }
                break
        # Check if user's country can establish here
        if user_country and not entry["blockade"]:
            units = _qualifying_units(client, sim_id, user_country, cp_id)
            entry["can_establish"] = len(units["naval"]) > 0 or len(units["ground"]) > 0
        chokepoints.append(entry)

    return APIResponse(data={
        "blockades": active_blockades,
        "chokepoints": chokepoints,
        "user_country": user_country,
    })


@app.get("/api/sim/{sim_id}/state", response_model=APIResponse)
async def get_sim_state(sim_id: str):
    """Get current simulation runtime state (round, phase, timer). Public — cached 5s."""
    import time
    now = time.time()
    cached = _state_cache.get(sim_id)
    if cached and now - cached[0] < 5:
        return APIResponse(data=cached[1])
    from engine.services.sim_run_manager import get_timer_info
    try:
        data = get_timer_info(sim_id)
        _state_cache[sim_id] = (now, data)
        return APIResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/sim/{sim_id}/pre-start", response_model=APIResponse)
async def sim_pre_start(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """Move sim from setup → pre_start (participant assignment phase)."""
    from engine.services.sim_run_manager import start_pre_start
    try:
        state = start_pre_start(sim_id)
        logger.info("Sim %s → pre_start by %s", sim_id, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/start", response_model=APIResponse)
async def sim_start(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """Start the simulation — Round 1 Phase A begins."""
    from engine.services.sim_run_manager import start_simulation
    try:
        state = start_simulation(sim_id)
        logger.info("Sim %s STARTED by %s", sim_id, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/phase/end", response_model=APIResponse)
async def sim_end_phase(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """End current phase and advance to next.

    Phase A → Processing (Phase B): triggers engine pipeline automatically.
    Phase B → Inter-Round: manual advance (moderator reviews results first).
    Inter-Round → Next Round Phase A: advances round counter.
    """
    from engine.services.sim_run_manager import (
        end_phase_a, end_phase_b, advance_round, get_state,
    )
    import asyncio
    try:
        run = await asyncio.to_thread(get_state, sim_id)
        phase = run["current_phase"]
        if phase == "A":
            state = await asyncio.to_thread(end_phase_a, sim_id)
            # Trigger Phase B engine processing
            round_num = run["current_round"]
            logger.info("Sim %s Phase A ended → triggering Phase B engines for R%d", sim_id, round_num)
            try:
                await _run_phase_b(sim_id, round_num)
                # Auto-advance to inter_round after engines complete
                state = await asyncio.to_thread(end_phase_b, sim_id)
                logger.info("Sim %s Phase B complete → inter_round", sim_id)
            except Exception as e:
                logger.exception("Phase B engine failed for sim %s R%d: %s", sim_id, round_num, e)
                return APIResponse(
                    success=False,
                    data=state,
                    error=f"Phase B engines failed: {e}. Sim is in processing state — click Next Phase to skip to inter-round.",
                )
        elif phase == "B":
            state = await asyncio.to_thread(end_phase_b, sim_id)
        elif phase == "inter_round":
            state = await asyncio.to_thread(advance_round, sim_id)
        else:
            raise ValueError(f"Cannot end phase '{phase}'")
        logger.info("Sim %s phase %s ended by %s", sim_id, phase, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def _run_phase_b(sim_id: str, round_num: int) -> None:
    """Run Phase B engine pipeline: collect batch decisions → run orchestrator → write events.

    Calls the orchestrator's process_round() which handles:
    - Economic engine (11 steps: oil → GDP → revenue → budget → inflation → debt → crisis)
    - Political engine (stability, war tiredness, elections, revolutions)
    - Persistence to countries + world_state tables
    """
    from engine.engines.orchestrator import process_round
    from engine.services.common import write_event
    from engine.services.supabase import get_client

    client = get_client()

    # 1. Collect batch decisions (set_budget, set_tariffs, set_sanctions, set_opec)
    batch_rows = client.table("agent_decisions") \
        .select("*") \
        .eq("sim_run_id", sim_id) \
        .eq("round_num", round_num) \
        .in_("action_type", ["set_budget", "set_tariffs", "set_sanctions", "set_opec"]) \
        .is_("processed_at", "null") \
        .execute().data or []

    # Convert batch decisions to the actions dict format orchestrator expects
    actions: dict = {
        "tariff_changes": {},
        "sanction_changes": {},
        "opec_production": {},
        "budget_decisions": {},
        "blockade_changes": {},
    }
    for row in batch_rows:
        payload = row.get("action_payload", {})
        cc = row.get("country_code", "")
        at = row.get("action_type", "")

        if at == "set_tariffs" and isinstance(payload, dict):
            target = payload.get("target_country", "")
            level = payload.get("level", 0)
            if target:
                actions["tariff_changes"].setdefault(cc, {})[target] = level
        elif at == "set_sanctions" and isinstance(payload, dict):
            target = payload.get("target_country", "")
            level = payload.get("level", 0)
            if target:
                actions["sanction_changes"].setdefault(cc, {})[target] = level
        elif at == "set_opec" and isinstance(payload, dict):
            level = payload.get("production_level", "maintain")
            actions["opec_production"][cc] = level
        elif at == "set_budget" and isinstance(payload, dict):
            actions["budget_decisions"][cc] = payload

    logger.info("Phase B: %d batch decisions collected for sim %s R%d", len(batch_rows), sim_id, round_num)

    # 2. Run the orchestrator
    result = await process_round(sim_id, round_num, actions)

    # 3. Mark batch decisions as processed
    for row in batch_rows:
        client.table("agent_decisions").update({
            "processed_at": "now()",
        }).eq("id", row["id"]).execute()

    # 4. Write summary observatory event
    run = client.table("sim_runs").select("scenario_id").eq("id", sim_id).single().execute()
    scenario_id = run.data.get("scenario_id") if run.data else None

    # Economic summary
    oil_price = result.economic.oil_price.price if result.economic else 0
    summary_lines = [f"Round {round_num} engines complete. Oil: ${oil_price:.0f}."]

    for cid in sorted(result.stability.keys())[:5]:
        sr = result.stability[cid]
        summary_lines.append(f"{cid}: stability {sr.new_stability:.1f}")

    if result.capitulation_flags:
        summary_lines.append(f"CAPITULATION: {', '.join(result.capitulation_flags)}")

    for cid, el in result.elections.items():
        summary_lines.append(f"ELECTION {cid}: {'incumbent wins' if el.incumbent_wins else 'incumbent loses'}")

    write_event(
        client, sim_id, scenario_id, round_num,
        "", "phase_b_complete", " | ".join(summary_lines),
        {"oil_price": oil_price, "log_lines": len(result.log)},
        phase="B", category="system",
    )

    # Expire pending transactions at end of round
    try:
        expired = client.table("exchange_transactions").update({"status": "expired"}) \
            .eq("sim_run_id", sim_id).eq("status", "pending").execute()
        if expired.data:
            logger.info("Expired %d pending transactions at end of R%d", len(expired.data), round_num)
    except Exception as e:
        logger.warning("Transaction cleanup failed: %s", e)

    logger.info("Phase B complete for sim %s R%d: %s", sim_id, round_num, summary_lines[0])


@app.post("/api/sim/{sim_id}/phase/extend", response_model=APIResponse)
async def sim_extend_phase(sim_id: str, minutes: int = 5, user: AuthUser = Depends(require_moderator)):
    """Extend current phase by N minutes."""
    from engine.services.sim_run_manager import extend_phase
    try:
        state = extend_phase(sim_id, additional_seconds=minutes * 60)
        logger.info("Sim %s extended +%dm by %s", sim_id, minutes, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/pause", response_model=APIResponse)
async def sim_pause(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """Pause the simulation."""
    from engine.services.sim_run_manager import pause_simulation
    try:
        state = pause_simulation(sim_id)
        logger.info("Sim %s PAUSED by %s", sim_id, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/resume", response_model=APIResponse)
async def sim_resume(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """Resume a paused simulation."""
    from engine.services.sim_run_manager import resume_simulation
    try:
        state = resume_simulation(sim_id)
        logger.info("Sim %s RESUMED by %s", sim_id, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/end", response_model=APIResponse)
async def sim_end(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """End the simulation gracefully."""
    from engine.services.sim_run_manager import end_simulation
    try:
        state = end_simulation(sim_id)
        logger.info("Sim %s ENDED by %s", sim_id, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/abort", response_model=APIResponse)
async def sim_abort(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """Abort the simulation (emergency stop)."""
    from engine.services.sim_run_manager import abort_simulation
    try:
        state = abort_simulation(sim_id)
        logger.info("Sim %s ABORTED by %s", sim_id, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/mode", response_model=APIResponse)
async def sim_set_mode(
    sim_id: str,
    request: Request,
    user: AuthUser = Depends(require_moderator),
):
    """Set automatic/manual mode and dice mode. Accepts JSON body."""
    from engine.services.sim_run_manager import set_mode
    try:
        body = await request.json()
    except Exception:
        body = {}
    auto_advance = body.get("auto_advance", False)
    auto_approve = body.get("auto_approve", False)
    dice_mode = body.get("dice_mode", False)
    auto_attack = body.get("auto_attack", False)
    try:
        state = set_mode(sim_id, auto_advance=auto_advance, auto_approve=auto_approve)
        from engine.services.supabase import get_client
        get_client().table("sim_runs").update({
            "dice_mode": dice_mode,
            "auto_attack": auto_attack,
        }).eq("id", sim_id).execute()
        state["dice_mode"] = dice_mode
        state["auto_attack"] = auto_attack
        logger.info("Sim %s mode: auto_advance=%s auto_approve=%s dice_mode=%s auto_attack=%s by %s",
                     sim_id, auto_advance, auto_approve, dice_mode, auto_attack, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/phase/back", response_model=APIResponse)
async def sim_go_back(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """Go back to Phase A of the current round."""
    from engine.services.sim_run_manager import go_back_to_phase_a
    try:
        state = go_back_to_phase_a(sim_id)
        logger.info("Sim %s went BACK to Phase A by %s", sim_id, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/restart", response_model=APIResponse)
async def sim_restart(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """Restart simulation from beginning. Deletes all runtime data."""
    from engine.services.sim_run_manager import restart_simulation
    from engine.agents.managed.event_dispatcher import cleanup_sim_ai_state
    import asyncio
    try:
        # Clean up AI state first (dispatcher, sessions, queue)
        ai_summary = await cleanup_sim_ai_state(
            sim_run_id=sim_id,
            clear_memories=True,
            clear_decisions=True,
        )
        logger.info("Sim %s AI cleanup: %s", sim_id, ai_summary)

        state = await asyncio.to_thread(restart_simulation, sim_id)
        logger.info("Sim %s RESTARTED (full cleanup) by %s", sim_id, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/restart-round", response_model=APIResponse)
async def sim_restart_round(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """Restart the current round — clean slate for this round only."""
    from engine.services.sim_run_manager import restart_current_round
    import asyncio
    try:
        state = await asyncio.to_thread(restart_current_round, sim_id)
        logger.info("Sim %s ROUND RESTARTED by %s", sim_id, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/sim/{sim_id}/rollback", response_model=APIResponse)
async def sim_rollback(sim_id: str, target_round: int = 1, user: AuthUser = Depends(require_moderator)):
    """Roll back to the start of a specific round. Deletes data for rounds after target."""
    from engine.services.sim_run_manager import rollback_to_round
    try:
        state = rollback_to_round(sim_id, target_round)
        logger.info("Sim %s ROLLED BACK to R%d by %s", sim_id, target_round, user.id)
        return APIResponse(data=state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# M4/M5: AI Agent Trigger
# ---------------------------------------------------------------------------

@app.post("/api/sim/{sim_id}/ai/trigger", response_model=APIResponse)
async def trigger_ai(sim_id: str, user: AuthUser = Depends(require_moderator)):
    """Trigger all AI-operated roles to submit their decisions.

    Uses the M5 stub (default decisions) until the full AI module is built.
    AI agents use the same action pipeline as human participants.
    """
    from engine.services.sim_run_manager import get_state
    from engine.services.ai_stub import trigger_ai_agents
    from engine.services.common import write_event
    from engine.services.supabase import get_client

    try:
        run = get_state(sim_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"SimRun {sim_id} not found")

    if run["status"] not in ("active",):
        raise HTTPException(status_code=400, detail=f"Sim is '{run['status']}' — AI trigger only in active phase")

    round_num = run["current_round"]
    logger.info("AI trigger for sim %s R%d by %s", sim_id, round_num, user.id)

    result = trigger_ai_agents(sim_run_id=sim_id, round_num=round_num)

    # Write observatory event
    client = get_client()
    scenario_id = run.get("scenario_id")
    write_event(
        client, sim_id, scenario_id, round_num,
        "", "ai_triggered", f"AI agents triggered: {result['total']} agents, {result['actions_submitted']} actions, {result['errors']} errors",
        {"agents": len(result["agents"]), "actions": result["actions_submitted"]},
        phase=run.get("current_phase", "A"),
        category="system",
    )

    return APIResponse(data=result)


# ---------------------------------------------------------------------------
# M4: Action Submission Pipeline
# ---------------------------------------------------------------------------

# Action type → category mapping (matches role_actions.action_id values in DB)
# Actions requiring moderator confirmation before execution
ACTIONS_REQUIRING_CONFIRMATION = {
    "assassination", "arrest",
}

# Combat actions that use dice (queue when dice_mode is on)
COMBAT_DICE_ACTIONS = {
    "ground_attack", "air_strike", "naval_combat",
    "naval_bombardment", "launch_missile_conventional",
}

ACTION_CATEGORIES: dict[str, str] = {
    # Military
    "ground_attack": "military",
    "ground_move": "military",
    "air_strike": "military",
    "naval_combat": "military",
    "naval_bombardment": "military",
    "naval_blockade": "military",
    "launch_missile_conventional": "military",
    "nuclear_test": "military",
    "nuclear_launch_initiate": "military",
    "nuclear_authorize": "military",
    "nuclear_intercept": "military",
    "basing_rights": "military",
    "martial_law": "military",
    "move_units": "military",
    # Economic
    "set_budget": "economic",
    "set_tariffs": "economic",
    "set_sanctions": "economic",
    "set_opec": "economic",
    "propose_transaction": "diplomatic",
    "accept_transaction": "diplomatic",
    # Diplomatic
    "propose_agreement": "diplomatic",
    "sign_agreement": "diplomatic",
    "public_statement": "diplomatic",
    "call_org_meeting": "diplomatic",
    "meet_freely": "diplomatic",
    "set_meetings": "diplomatic",
    "invite_to_meet": "diplomatic",
    "respond_meeting": "diplomatic",
    # Covert
    "covert_operation": "covert",
    "intelligence": "covert",
    # Political
    "arrest": "political",
    "release_arrest": "political",
    "assassination": "political",
    "change_leader": "political",
    "reassign_types": "political",
    "self_nominate": "political",
    "cast_vote": "political",
    # Diplomatic — war
    "declare_war": "diplomatic",
}


@app.post("/api/sim/{sim_id}/action", response_model=APIResponse)
async def submit_action(
    sim_id: str,
    body: ActionSubmission,
    user: AuthUser = Depends(get_current_user),
):
    """Submit a game action during Phase A.

    Validates: sim is active, phase allows actions, role exists.
    Dispatches to the action engine and writes an observatory event.
    """
    from engine.services.sim_run_manager import get_state
    from engine.services.action_dispatcher import dispatch_action
    from engine.services.common import get_scenario_id, write_event
    from engine.services.supabase import get_client

    # 1. Validate sim state
    try:
        run = get_state(sim_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"SimRun {sim_id} not found")

    # Reactive actions are NOT stored in role_actions — they are computed at runtime
    # by their respective engines. They bypass the role_actions permission check.
    # Some (nuclear chain) are also allowed when sim is paused (flight phase).
    REACTIVE_ACTIONS = {
        "nuclear_authorize", "nuclear_intercept",
        "accept_transaction", "sign_agreement",
        "cast_vote", "cast_election_vote", "accept_meeting",
        "release_arrest",
        "withdraw_nomination", "resolve_election",
        "respond_meeting",
    }
    PAUSED_ALLOWED = {"nuclear_authorize", "nuclear_intercept"}
    if run["status"] not in ("active", "processing", "inter_round"):
        if not (run["status"] == "paused" and body.action_type in PAUSED_ALLOWED):
            raise HTTPException(
                status_code=400,
                detail=f"Sim is '{run['status']}' — actions only allowed when active",
            )

    current_phase = run.get("current_phase", "")

    # Phase B (inter_round): only move_units allowed
    INTER_ROUND_ALLOWED = {"move_units"}
    if run["status"] == "inter_round" and body.action_type not in INTER_ROUND_ALLOWED:
        raise HTTPException(
            status_code=400,
            detail="Only unit movements are allowed during the inter-round phase",
        )

    # 2. Validate role exists in this sim
    # Moderator actions (resolve_election) use role_id='moderator' — skip role validation
    MODERATOR_ACTIONS = {"resolve_election"}
    client = get_client()

    if body.role_id == "moderator" and body.action_type in MODERATOR_ACTIONS:
        role = {"id": "moderator", "character_name": "Moderator", "country_code": body.country_code,
                "positions": [], "position_type": "moderator"}
    else:
        role_check = (
            client.table("roles")
            .select("id, character_name, country_code, positions, position_type")
            .eq("sim_run_id", sim_id)
            .eq("id", body.role_id)
            .execute()
        )
        if not role_check.data:
            raise HTTPException(status_code=400, detail=f"Role '{body.role_id}' not found in sim")

        role = role_check.data[0]

    # 3. Validate role has this action type (check role_actions table)
    # Reactive actions bypass role_actions — their authorization is handled
    # at runtime by their respective engines (nuclear chain, transaction, etc.)
    if body.action_type not in REACTIVE_ACTIONS:
        # ground_move is authorized by ground_attack permission (same capability)
        check_action = body.action_type
        if check_action == "ground_move":
            check_action = "ground_attack"
        action_check = (
            client.table("role_actions")
            .select("id")
            .eq("sim_run_id", sim_id)
            .eq("role_id", body.role_id)
            .eq("action_id", check_action)
            .execute()
        )
        if not action_check.data:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{body.role_id}' is not authorized for action '{body.action_type}'",
            )

    # 4. Build action payload
    action_payload = {
        "action_type": body.action_type,
        "role_id": body.role_id,
        "country_code": body.country_code,
        **body.params,
    }

    round_num = run.get("current_round", 0)
    category = ACTION_CATEGORIES.get(body.action_type, "system")
    scenario_id = run.get("scenario_id")

    # 4a. Check limited action usage (arrest, intelligence, covert_operation, assassination)
    from engine.config.position_actions import LIMITED_ACTIONS
    if body.action_type in LIMITED_ACTIONS:
        from engine.services.position_helpers import check_and_decrement_usage
        usage = check_and_decrement_usage(client, sim_id, body.role_id, body.action_type)
        if not usage["allowed"]:
            raise HTTPException(status_code=400, detail=usage["message"])
        # Include remaining count in response for UI
        action_payload["_uses_remaining"] = usage["remaining"]

    # 4b. Compute combat modifiers (needed for both pending and immediate paths)
    if body.action_type in ("ground_attack", "naval_combat"):
        tr = body.params.get("target_row")
        tc = body.params.get("target_col")
        if tr is not None and tc is not None:
            def_deps = client.table("deployments").select("id,country_code,unit_type") \
                .eq("sim_run_id", sim_id).eq("global_row", int(tr)).eq("global_col", int(tc)) \
                .eq("unit_status", "active") \
                .neq("country_code", body.country_code).execute().data or []
            def_ground = [d for d in def_deps if d["unit_type"] == "ground"]
            action_payload["_defender_ground_count"] = len(def_ground)
            # Compute modifiers
            def_countries = list(set(d["country_code"] for d in def_deps))
            atk_c = client.table("countries").select("stability,ai_level") \
                .eq("sim_run_id", sim_id).eq("id", body.country_code).limit(1).execute().data
            def_c = client.table("countries").select("stability,ai_level") \
                .eq("sim_run_id", sim_id).eq("id", def_countries[0]).limit(1).execute().data if def_countries else []
            mods_atk, mods_def = [], []
            atk_ai = atk_c[0].get("ai_level", 0) if atk_c else 0
            atk_stab = atk_c[0].get("stability", 5) if atk_c else 5
            def_ai = def_c[0].get("ai_level", 0) if def_c else 0
            def_stab = def_c[0].get("stability", 5) if def_c else 5
            if atk_ai >= 4: mods_atk.append({"label": "AI L4", "value": +1})
            if atk_stab <= 3: mods_atk.append({"label": "Low morale", "value": -1})
            if def_ai >= 4: mods_def.append({"label": "AI L4", "value": +1})
            if def_stab <= 3: mods_def.append({"label": "Low morale", "value": -1})
            def_air = [d for d in def_deps if d["unit_type"] == "tactical_air"]
            if def_air: mods_def.append({"label": "Air support", "value": +1})
            action_payload["_modifiers"] = {"attacker": mods_atk, "defender": mods_def}
            action_payload["_atk_mod_total"] = sum(m["value"] for m in mods_atk)
            action_payload["_def_mod_total"] = sum(m["value"] for m in mods_def)
            # Engine format: [{side, value, reason}]
            engine_mods = []
            for m in mods_atk:
                engine_mods.append({"side": "attacker", "value": m["value"], "reason": m["label"]})
            for m in mods_def:
                engine_mods.append({"side": "defender", "value": m["value"], "reason": m["label"]})
            action_payload["modifiers"] = engine_mods

    # 4b. Check if action requires moderator confirmation
    auto_approve = run.get("auto_approve", False)
    auto_attack = run.get("auto_attack", False)
    needs_confirmation = (
        (body.action_type in ACTIONS_REQUIRING_CONFIRMATION and not auto_approve)
        or (body.action_type in COMBAT_DICE_ACTIONS and not auto_attack)
    )
    if needs_confirmation:
        changes = body.params.get("changes", {}) or {}
        target = changes.get("target_role") or body.params.get("target_role", body.params.get("target_country", ""))
        if body.action_type in COMBAT_DICE_ACTIONS:
            tr = body.params.get("target_row", "?")
            tc = body.params.get("target_col", "?")
            target_info = f"{role['character_name']} ({body.country_code}) → ({tr},{tc})"
        else:
            # Resolve target character name if possible
            target_name = target
            if target:
                t_data = client.table("roles").select("character_name").eq("sim_run_id", sim_id).eq("id", target).limit(1).execute().data
                if t_data:
                    target_name = t_data[0]["character_name"]
            target_info = f"{role['character_name']} → {target_name}" if target else role["character_name"]

        pa_result = client.table("pending_actions").insert({
            "sim_run_id": sim_id,
            "round_num": round_num,
            "action_type": body.action_type,
            "role_id": body.role_id,
            "country_code": body.country_code,
            "target_info": target_info,
            "payload": action_payload,
            "status": "pending",
        }).execute()
        pa_id = pa_result.data[0]["id"] if pa_result.data else None

        write_event(
            client, sim_id, scenario_id, round_num,
            body.country_code, body.action_type,
            f"PENDING: {body.action_type} by {role['character_name']} — awaiting moderator approval",
            {"action": action_payload, "status": "pending"},
            phase=current_phase, category=category, role_name=role["character_name"],
        )

        logger.info("Action %s by %s queued for confirmation (pa=%s)", body.action_type, role["character_name"], pa_id)
        return APIResponse(data={
            "success": True,
            "status": "pending",
            "pending_action_id": pa_id,
            "narrative": f"{body.action_type} submitted — awaiting moderator approval",
        })

    # 4b. Check if combat action needs physical dice input
    # Only ground_attack and naval_combat use dice. Only when auto_attack is OFF.
    dice_mode = run.get("dice_mode", False)
    DICE_COMBAT_TYPES = {"ground_attack", "naval_combat"}
    if body.action_type in DICE_COMBAT_TYPES and dice_mode and not auto_attack:
        target_info = f"{role['character_name']}: {body.action_type}"

        pa_result2 = client.table("pending_actions").insert({
            "sim_run_id": sim_id,
            "round_num": round_num,
            "action_type": body.action_type,
            "role_id": body.role_id,
            "country_code": body.country_code,
            "target_info": target_info,
            "payload": {**action_payload, "_requires_dice": True},
            "status": "pending",
        }).execute()
        pa_id2 = pa_result2.data[0]["id"] if pa_result2.data else None

        write_event(
            client, sim_id, scenario_id, round_num,
            body.country_code, body.action_type,
            f"DICE NEEDED: {body.action_type} by {role['character_name']} — moderator must input dice rolls",
            {"action": action_payload, "status": "awaiting_dice"},
            phase=current_phase, category=category, role_name=role["character_name"],
        )

        logger.info("Combat %s by %s queued for dice input (pa=%s)", body.action_type, role["character_name"], pa_id2)
        return APIResponse(data={
            "success": True,
            "status": "awaiting_dice",
            "pending_action_id": pa_id2,
            "narrative": f"{body.action_type} submitted — moderator must input dice rolls",
        })

    # 5. Immediate dispatch (no confirmation needed)
    # Run in thread to avoid blocking the async event loop (sync DB + engine calls)
    import asyncio
    try:
        result = await asyncio.to_thread(dispatch_action, sim_id, round_num, action_payload)
    except Exception as e:
        logger.exception("Action dispatch failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Engine error: {e}")

    summary = result.get("narrative", f"{body.action_type} by {role['character_name']}")
    write_event(
        client, sim_id, scenario_id, round_num,
        body.country_code, body.action_type, summary,
        {"action": action_payload, "result": result},
        phase=current_phase, category=category, role_name=role["character_name"],
    )

    logger.info(
        "Action %s by %s (%s) in sim %s R%d — %s",
        body.action_type, role["character_name"], body.country_code,
        sim_id, round_num, "OK" if result.get("success") else "FAILED",
    )

    return APIResponse(data=result)


# ---------------------------------------------------------------------------
# M4: Pending Action Confirmation
# ---------------------------------------------------------------------------

@app.get("/api/sim/{sim_id}/pending", response_model=APIResponse)
async def get_pending_actions(sim_id: str, user: AuthUser = Depends(get_current_user)):
    """Get all pending actions for a sim."""
    from engine.services.supabase import get_client
    client = get_client()
    rows = (
        client.table("pending_actions")
        .select("*")
        .eq("sim_run_id", sim_id)
        .eq("status", "pending")
        .order("submitted_at", desc=False)
        .execute()
    ).data or []
    return APIResponse(data=rows, meta={"count": len(rows)})


@app.post("/api/sim/{sim_id}/pending/{action_id}/confirm", response_model=APIResponse)
async def confirm_pending_action(
    sim_id: str, action_id: str,
    request: Request,
    user: AuthUser = Depends(require_moderator),
):
    """Approve a pending action — dispatches it to the engine.

    For combat actions with dice_mode, pass body:
      {"precomputed_rolls": {"attacker": [[5,3,2], [6,4]], "defender": [[6,2], [4,1]]}}
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    precomputed_rolls = body.get("precomputed_rolls") if body else None
    from engine.services.action_dispatcher import dispatch_action
    from engine.services.common import write_event
    from engine.services.supabase import get_client
    from engine.services.sim_run_manager import get_state

    client = get_client()

    pa = client.table("pending_actions").select("*").eq("id", action_id).eq("sim_run_id", sim_id).execute()
    if not pa.data:
        raise HTTPException(status_code=404, detail="Pending action not found")
    pending = pa.data[0]

    if pending["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Action already {pending['status']}")

    payload = pending["payload"]
    round_num = pending["round_num"]

    # Inject moderator dice values if provided (physical dice mode)
    if precomputed_rolls:
        payload["precomputed_rolls"] = precomputed_rolls
    # Remove internal flag
    payload.pop("_requires_dice", None)

    import asyncio
    try:
        result = await asyncio.to_thread(dispatch_action, sim_id, round_num, payload)
    except Exception as e:
        logger.exception("Confirmed action dispatch failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Engine error: {e}")

    client.table("pending_actions").update({
        "status": "approved",
        "resolved_at": "now()",
        "resolved_by": user.id,
        "result": result,
    }).eq("id", action_id).execute()

    run = get_state(sim_id)
    category = ACTION_CATEGORIES.get(pending["action_type"], "system")
    write_event(
        client, sim_id, run.get("scenario_id"), round_num,
        pending["country_code"], pending["action_type"],
        f"APPROVED: {pending['action_type']} — {pending['target_info']}",
        {"action": payload, "result": result, "approved_by": user.id},
        phase=run.get("current_phase", "A"),
        category=category, role_name=pending.get("role_id"),
    )

    logger.info("Pending action %s approved by %s", action_id, user.id)
    return APIResponse(data=result)


@app.get("/api/sim/{sim_id}/pending/{action_id}/status", response_model=APIResponse)
async def get_pending_action_status(
    sim_id: str, action_id: str,
    user: AuthUser = Depends(get_current_user),
):
    """Get status + result of a pending action. Used by participant poller."""
    from engine.services.supabase import get_client
    client = get_client()
    pa = client.table("pending_actions").select("status,result") \
        .eq("id", action_id).eq("sim_run_id", sim_id).limit(1).execute()
    if not pa.data:
        raise HTTPException(status_code=404, detail="Pending action not found")
    return APIResponse(data=pa.data[0])


@app.post("/api/sim/{sim_id}/pending/{action_id}/reject", response_model=APIResponse)
async def reject_pending_action(
    sim_id: str, action_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Reject a pending action — not executed."""
    from engine.services.common import write_event
    from engine.services.supabase import get_client
    from engine.services.sim_run_manager import get_state

    client = get_client()

    pa = client.table("pending_actions").select("*").eq("id", action_id).eq("sim_run_id", sim_id).execute()
    if not pa.data:
        raise HTTPException(status_code=404, detail="Pending action not found")
    pending = pa.data[0]

    if pending["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Action already {pending['status']}")

    client.table("pending_actions").update({
        "status": "rejected",
        "resolved_at": "now()",
        "resolved_by": user.id,
    }).eq("id", action_id).execute()

    run = get_state(sim_id)
    category = ACTION_CATEGORIES.get(pending["action_type"], "system")
    write_event(
        client, sim_id, run.get("scenario_id"), pending["round_num"],
        pending["country_code"], pending["action_type"],
        f"REJECTED: {pending['action_type']} — {pending['target_info']}",
        {"action": pending["payload"], "rejected_by": user.id},
        phase=run.get("current_phase", "A"),
        category=category, role_name=pending.get("role_id"),
    )

    logger.info("Pending action %s rejected by %s", action_id, user.id)
    return APIResponse(data={"status": "rejected", "action_id": action_id})


# ---------------------------------------------------------------------------
# M4: Leadership Change Voting
# ---------------------------------------------------------------------------

@app.get("/api/sim/{sim_id}/leadership-votes", response_model=APIResponse)
async def get_leadership_votes(sim_id: str, user: AuthUser = Depends(get_current_user)):
    """Get active leadership change votes for a sim."""
    from engine.services.supabase import get_client
    client = get_client()
    rows = (
        client.table("leadership_votes")
        .select("*")
        .eq("sim_run_id", sim_id)
        .eq("status", "voting")
        .order("created_at", desc=False)
        .execute()
    ).data or []
    return APIResponse(data=rows, meta={"count": len(rows)})


@app.post("/api/sim/{sim_id}/leadership-votes/{vote_id}/cast", response_model=APIResponse)
async def cast_leadership_vote(
    sim_id: str, vote_id: str,
    request: Request,
    user: AuthUser = Depends(get_current_user),
):
    """Cast a vote in an active leadership change."""
    from engine.services.change_leader import cast_leader_vote
    body = await request.json()
    role_id = body.get("role_id", "")
    vote = body.get("vote", "")
    if not role_id or not vote:
        raise HTTPException(status_code=400, detail="role_id and vote are required")
    result = cast_leader_vote(sim_id, vote_id, role_id, vote)
    # Auto-resolve if majority achieved
    if result.get("success"):
        from engine.services.change_leader import _check_auto_resolve
        auto = _check_auto_resolve(sim_id, vote_id)
        if auto:
            result["auto_resolved"] = True
            result["resolution"] = auto
    return APIResponse(data=result)


@app.post("/api/sim/{sim_id}/leadership-votes/{vote_id}/resolve", response_model=APIResponse)
async def resolve_leadership_vote(
    sim_id: str, vote_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Resolve a leadership change vote (moderator closes voting)."""
    from engine.services.change_leader import resolve_leader_vote
    result = resolve_leader_vote(sim_id, vote_id)
    logger.info("Leadership vote %s resolved by %s: %s", vote_id, user.id, result.get("outcome"))
    return APIResponse(data=result)


# ---------------------------------------------------------------------------
# Action usage — check remaining uses for limited actions
# ---------------------------------------------------------------------------

@app.get("/api/sim/{sim_id}/action-usage/{role_id}/{action_id}")
async def get_action_usage_endpoint(
    sim_id: str, role_id: str, action_id: str,
    user: AuthUser = Depends(get_current_user),
):
    """Get remaining uses for a limited action."""
    from engine.services.position_helpers import get_action_usage
    from engine.services.supabase import get_client
    result = get_action_usage(get_client(), sim_id, role_id, action_id)
    return APIResponse(data=result)


# ---------------------------------------------------------------------------
# Positions & Actions — recompute role_actions from positions
# ---------------------------------------------------------------------------

@app.post("/api/sim/{sim_id}/recompute-actions", response_model=APIResponse)
async def recompute_actions(
    sim_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Recompute all role_actions from positions + country state.

    Preserves manual_override rows. Used by Template Editor Actions tab.
    """
    from engine.services.position_helpers import recompute_all_role_actions
    from engine.services.supabase import get_client
    client = get_client()
    result = recompute_all_role_actions(client, sim_id)
    logger.info("Recomputed actions for %s by %s: +%d -%d",
                sim_id, user.id, result["total_added"], result["total_removed"])
    return APIResponse(data=result)


# ---------------------------------------------------------------------------
# M4: Nuclear Chain Management
# ---------------------------------------------------------------------------

@app.get("/api/sim/{sim_id}/nuclear", response_model=APIResponse)
async def get_nuclear_actions(sim_id: str, user: AuthUser = Depends(get_current_user)):
    """Get active nuclear actions for a sim."""
    from engine.services.supabase import get_client
    client = get_client()
    rows = (
        client.table("nuclear_actions")
        .select("*")
        .eq("sim_run_id", sim_id)
        .in_("status", ["awaiting_authorization", "authorized", "awaiting_interception"])
        .order("created_at", desc=False)
        .execute()
    ).data or []
    return APIResponse(data=rows, meta={"count": len(rows)})


@app.get("/api/sim/{sim_id}/nuclear/active", response_model=APIResponse)
async def get_active_nuclear_action(sim_id: str, user: AuthUser = Depends(get_current_user)):
    """Get active nuclear action (if any) for global banner + interception decisions.

    Returns the nuclear_actions row where status is one of the active states,
    plus timer configuration from sim_runs.schedule.
    """
    from engine.services.supabase import get_client
    client = get_client()

    rows = (
        client.table("nuclear_actions")
        .select("*")
        .eq("sim_run_id", sim_id)
        .in_("status", ["awaiting_authorization", "authorized", "awaiting_interception"])
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    ).data or []

    if not rows:
        return APIResponse(data=None, meta={"active": False})

    action = rows[0]

    # Load timer config from sim_runs.schedule
    run_rows = client.table("sim_runs").select("schedule").eq("id", sim_id).limit(1).execute().data or []
    schedule = (run_rows[0].get("schedule") or {}) if run_rows else {}
    action["nuclear_auth_timer_sec"] = schedule.get("nuclear_auth_timer_sec", 600)
    action["nuclear_flight_timer_sec"] = schedule.get("nuclear_flight_timer_sec", 600)

    return APIResponse(data=action, meta={"active": True})


@app.post("/api/sim/{sim_id}/nuclear/{action_id}/resolve", response_model=APIResponse)
async def resolve_nuclear_action(
    sim_id: str, action_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Resolve a nuclear action (moderator triggers resolution after authorization/interception)."""
    from engine.orchestrators.nuclear_chain import NuclearChainOrchestrator
    orch = NuclearChainOrchestrator()
    result = orch.resolve(action_id)
    logger.info("Nuclear action %s resolved by %s", action_id, user.id)
    return APIResponse(data=result)


# ---------------------------------------------------------------------------
# M5 Spike: AI Agent observation endpoint
# ---------------------------------------------------------------------------

@app.get("/api/sim/{sim_id}/agent-log", response_model=APIResponse)
async def get_agent_log(
    sim_id: str,
    country_code: Optional[str] = None,
    limit: int = 50,
):
    """Return AI agent log entries from observatory_events.

    Filters to event_type='ai_agent_log' for this sim_run.
    Optional: filter by country_code.
    """
    from engine.services.supabase import get_client
    client = get_client()
    q = (
        client.table("observatory_events")
        .select("*")
        .eq("sim_run_id", sim_id)
        .eq("event_type", "ai_agent_log")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if country_code:
        q = q.eq("country_code", country_code)
    result = q.execute()
    return APIResponse(data=result.data or [], meta={"count": len(result.data or [])})


# ---------------------------------------------------------------------------
# Meeting chat endpoints
# ---------------------------------------------------------------------------

class MeetingMessageRequest(BaseModel):
    """POST body for sending a meeting message."""
    role_id: str
    country_code: str
    content: str


class MeetingEndRequest(BaseModel):
    """POST body for ending a meeting."""
    role_id: str


@app.get("/api/sim/{sim_id}/meetings/active/{role_id}", response_model=APIResponse)
async def get_active_meetings_endpoint(
    sim_id: str,
    role_id: str,
    user: AuthUser = Depends(get_current_user),
):
    """List active meetings for a role."""
    from engine.services.meeting_service import get_active_meetings
    meetings = get_active_meetings(sim_run_id=sim_id, role_id=role_id)
    return APIResponse(data=meetings, meta={"count": len(meetings)})


@app.get("/api/sim/{sim_id}/meetings/{meeting_id}", response_model=APIResponse)
async def get_meeting_detail(
    sim_id: str,
    meeting_id: str,
    user: AuthUser = Depends(get_current_user),
):
    """Get meeting details + all messages."""
    from engine.services.meeting_service import get_meeting
    result = get_meeting(meeting_id)
    if not result:
        raise HTTPException(status_code=404, detail="Meeting not found")
    # Verify the meeting belongs to this sim
    if result["meeting"].get("sim_run_id") != sim_id:
        raise HTTPException(status_code=404, detail="Meeting not found in this SIM")
    return APIResponse(data=result)


@app.post("/api/sim/{sim_id}/meetings/{meeting_id}/message", response_model=APIResponse)
async def send_meeting_message(
    sim_id: str,
    meeting_id: str,
    body: MeetingMessageRequest,
    user: AuthUser = Depends(get_current_user),
):
    """Send a message in a meeting."""
    from engine.services.meeting_service import send_message, get_meeting

    # Verify meeting belongs to this sim
    meeting_data = get_meeting(meeting_id)
    if not meeting_data or meeting_data["meeting"].get("sim_run_id") != sim_id:
        raise HTTPException(status_code=404, detail="Meeting not found in this SIM")

    result = send_message(
        meeting_id=meeting_id,
        role_id=body.role_id,
        country_code=body.country_code,
        content=body.content,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["narrative"])

    # Enqueue chat event for AI counterpart via unified dispatcher
    meeting = meeting_data["meeting"]
    other_role_id = (
        meeting["participant_b_role_id"]
        if meeting["participant_a_role_id"] == body.role_id
        else meeting["participant_a_role_id"]
    )

    from engine.agents.managed.event_dispatcher import get_dispatcher
    dispatcher = get_dispatcher(sim_id)
    if dispatcher:
        # Build conversation context (last 6 messages)
        from engine.services.supabase import get_client as _get_db
        _db = _get_db()
        all_msgs = (
            _db.table("meeting_messages")
            .select("role_id,content")
            .eq("meeting_id", meeting_id)
            .order("created_at")
            .execute()
        )
        chat_lines = []
        for m in all_msgs.data or []:
            chat_lines.append(f'{m["role_id"]}: "{m["content"]}"')
        chat_text = "\n".join(chat_lines[-6:])

        dispatcher.enqueue(
            role_id=other_role_id,
            tier=2,
            event_type="chat_message",
            message=(
                f"MEETING CONVERSATION:\n{chat_text}\n\n"
                f"Reply in 1-3 sentences. Stay in character. "
                f"Do NOT call any tools — just respond with your words directly."
            ),
            metadata={"meeting_id": meeting_id, "sender": body.role_id},
        )

    return APIResponse(data=result)


@app.post("/api/sim/{sim_id}/meetings/{meeting_id}/end", response_model=APIResponse)
async def end_meeting_endpoint(
    sim_id: str,
    meeting_id: str,
    body: MeetingEndRequest,
    user: AuthUser = Depends(get_current_user),
):
    """End a meeting."""
    from engine.services.meeting_service import end_meeting, get_meeting

    # Verify meeting belongs to this sim
    meeting_data = get_meeting(meeting_id)
    if not meeting_data or meeting_data["meeting"].get("sim_run_id") != sim_id:
        raise HTTPException(status_code=404, detail="Meeting not found in this SIM")

    result = end_meeting(meeting_id=meeting_id, role_id=body.role_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["narrative"])

    # Set both meeting participants back to IDLE in the dispatcher
    from engine.agents.managed.event_dispatcher import get_dispatcher, IDLE
    dispatcher = get_dispatcher(sim_id)
    if dispatcher:
        meeting = meeting_data["meeting"]
        for rid in (meeting.get("participant_a_role_id"), meeting.get("participant_b_role_id")):
            if rid and rid in dispatcher.agents:
                dispatcher.set_agent_state(rid, IDLE)

    return APIResponse(data=result)


# ---------------------------------------------------------------------------
# M5 AI Orchestrator — Managed Agent control endpoints
# ---------------------------------------------------------------------------


class AIInitRequest(BaseModel):
    """Request body for AI agent initialization."""
    role_ids: list[str] | None = None
    assertiveness: int = 5
    pulses_per_round: int = 8
    model: str = "claude-sonnet-4-6"
    auto_advance: bool = False
    round_duration_seconds: int = 300


class AIRunRoundRequest(BaseModel):
    """Request body for running a round."""
    round_num: int | None = None  # None = use current_round from sim_run


class AIPulseRequest(BaseModel):
    """Request body for sending a single pulse."""
    pulse_num: int = 1


class AICriticalInterruptRequest(BaseModel):
    """Request body for critical interrupt."""
    role_ids: list[str]
    message: str


@app.post("/api/sim/{sim_id}/ai/initialize", response_model=APIResponse)
async def ai_initialize(
    sim_id: str,
    body: AIInitRequest,
    user: AuthUser = Depends(require_moderator),
):
    """Initialize all AI agents for a simulation.

    Creates managed agent sessions via the EventDispatcher (single execution
    path) for each AI-operated role. Init messages are enqueued as Tier 2
    events and delivered by the dispatcher loop.
    """
    from engine.agents.managed.event_dispatcher import (
        create_dispatcher, get_dispatcher, remove_dispatcher,
    )

    # Check if dispatcher already exists with agents
    existing_d = get_dispatcher(sim_id)
    if existing_d and existing_d.agents:
        return APIResponse(
            success=False,
            data={"error": "AI agents already initialized for this sim. Shut down first."},
        )

    # Create dispatcher (single owner of sessions, queue, delivery)
    if existing_d:
        remove_dispatcher(sim_id)
    dispatcher = create_dispatcher(sim_id)

    # Run initialization in background — session creation takes time
    import asyncio
    async def _run_init():
        try:
            result = await dispatcher.initialize_all_agents(
                role_ids=body.role_ids,
                model=body.model,
            )

            # Start the dispatch loop (delivers enqueued init events)
            await dispatcher.start()

            logger.info(
                "AI initialized for sim %s: %d agents, dispatcher started by %s",
                sim_id, result.get("agents_initialized", 0), user.id,
            )
        except Exception as e:
            logger.error("AI initialization failed for sim %s: %s", sim_id, e)

    asyncio.create_task(_run_init())

    return APIResponse(data={
        "status": "initializing",
        "message": "AI agent initialization started in background. Check /ai/status for progress.",
        "sim_run_id": sim_id,
    })


@app.post("/api/sim/{sim_id}/ai/run-round", response_model=APIResponse)
async def ai_run_round(
    sim_id: str,
    body: AIRunRoundRequest,
    user: AuthUser = Depends(require_moderator),
):
    """Run a round pulse for all AI agents via the unified dispatcher.

    Enqueues a round_pulse event (Tier 3) for each registered agent.
    The dispatcher loop delivers them normally. Returns agent status.
    """
    from engine.agents.managed.event_dispatcher import get_dispatcher

    dispatcher = get_dispatcher(sim_id)
    if not dispatcher or not dispatcher.agents:
        raise HTTPException(status_code=404, detail="No AI dispatcher for this sim. Call /ai/initialize first.")

    # Determine round number
    round_num = body.round_num
    if round_num is None:
        from engine.services.sim_run_manager import get_state
        try:
            run = get_state(sim_id)
            round_num = run.get("current_round", 1)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"SimRun {sim_id} not found")

    # Enqueue round pulse events for all agents
    enqueued = 0
    for role_id in dispatcher.agents:
        dispatcher.enqueue(
            role_id=role_id,
            tier=3,
            event_type="round_pulse",
            message=(
                f"Round {round_num} update. Assess your situation, check intelligence, "
                f"and take strategic actions. Use your tools to gather information and act."
            ),
            metadata={"round_num": round_num},
        )
        enqueued += 1

    logger.info(
        "AI round %d: enqueued %d round_pulse events for sim %s by %s",
        round_num, enqueued, sim_id, user.id,
    )
    return APIResponse(data={
        "round_num": round_num,
        "agents_pulsed": enqueued,
        "status": "round_pulse_enqueued",
        "message": f"Enqueued round {round_num} pulse for {enqueued} agents. Dispatcher delivers them.",
    })


@app.post("/api/sim/{sim_id}/ai/send-pulse", response_model=APIResponse)
async def ai_send_pulse(
    sim_id: str,
    body: AIPulseRequest,
    user: AuthUser = Depends(require_moderator),
):
    """Send a single pulse to all eligible AI agents via the unified dispatcher.

    Enqueues a manual_pulse event (Tier 3) for each idle agent.
    The dispatcher loop delivers them normally.
    """
    from engine.agents.managed.event_dispatcher import get_dispatcher, IDLE

    dispatcher = get_dispatcher(sim_id)
    if not dispatcher or not dispatcher.agents:
        raise HTTPException(status_code=404, detail="No AI dispatcher for this sim. Call /ai/initialize first.")

    enqueued = 0
    for role_id in dispatcher.agents:
        if dispatcher.agent_states.get(role_id) == IDLE:
            dispatcher.enqueue(
                role_id=role_id,
                tier=3,
                event_type="manual_pulse",
                message=(
                    f"Pulse #{body.pulse_num}. Review your situation and take any actions "
                    f"you deem necessary. Use your tools to gather information and act."
                ),
                metadata={"pulse_num": body.pulse_num},
            )
            enqueued += 1

    return APIResponse(data={
        "pulse_num": body.pulse_num,
        "agents_pulsed": enqueued,
        "total_agents": len(dispatcher.agents),
    })


@app.get("/api/sim/{sim_id}/ai/status", response_model=APIResponse)
async def ai_status(
    sim_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Get all AI agent states, costs, queue depths, and activity summary.

    No auto-reconnect. If the server restarted, the moderator must click
    Initialize again. This prevents stale session conflicts.
    """
    from engine.agents.managed.event_dispatcher import get_dispatcher

    dispatcher = get_dispatcher(sim_id)

    if not dispatcher:
        return APIResponse(data={
            "sim_run_id": sim_id, "round_num": 0,
            "total_agents": 0, "agents_idle": 0, "agents_frozen": 0,
            "agents_in_meeting": 0, "agents_acting": 0,
            "total_input_tokens": 0, "total_output_tokens": 0,
            "total_cost_usd": 0, "agents": [], "not_initialized": True,
        })

    return APIResponse(data=await dispatcher.get_status())


@app.post("/api/sim/{sim_id}/ai/freeze/{role_id}", response_model=APIResponse)
async def ai_freeze_agent(
    sim_id: str,
    role_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Freeze one AI agent — stops receiving events from the dispatcher."""
    from engine.agents.managed.event_dispatcher import get_dispatcher, FROZEN

    dispatcher = get_dispatcher(sim_id)
    if not dispatcher:
        raise HTTPException(status_code=404, detail="No AI dispatcher active for this sim.")

    if role_id not in dispatcher.agents:
        raise HTTPException(status_code=400, detail=f"Agent {role_id} not found")

    prev_state = dispatcher.agent_states.get(role_id, "UNKNOWN")
    dispatcher.set_agent_state(role_id, FROZEN)

    # Also freeze in session manager (DB status)
    ctx = dispatcher.agents[role_id]
    dispatcher.session_manager.freeze_session(ctx)

    return APIResponse(data={
        "success": True, "role_id": role_id,
        "state": FROZEN, "previous_state": prev_state,
    })


@app.post("/api/sim/{sim_id}/ai/resume/{role_id}", response_model=APIResponse)
async def ai_resume_agent(
    sim_id: str,
    role_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Resume one frozen AI agent — receives batched events at next dispatch."""
    from engine.agents.managed.event_dispatcher import get_dispatcher, FROZEN, IDLE

    dispatcher = get_dispatcher(sim_id)
    if not dispatcher:
        raise HTTPException(status_code=404, detail="No AI dispatcher active for this sim.")

    if role_id not in dispatcher.agents:
        raise HTTPException(status_code=400, detail=f"Agent {role_id} not found")

    if dispatcher.agent_states.get(role_id) != FROZEN:
        raise HTTPException(
            status_code=400,
            detail=f"Agent {role_id} is not frozen (state: {dispatcher.agent_states.get(role_id)})",
        )

    dispatcher.set_agent_state(role_id, IDLE)

    # Also resume in session manager (DB status)
    ctx = dispatcher.agents[role_id]
    dispatcher.session_manager.resume_session(ctx)

    queue_depth = await dispatcher.get_queue_depth(role_id)
    return APIResponse(data={
        "success": True, "role_id": role_id,
        "state": IDLE, "queue_depth": queue_depth,
    })


@app.post("/api/sim/{sim_id}/ai/freeze-all", response_model=APIResponse)
async def ai_freeze_all(
    sim_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Freeze all AI agents — global pause, humans continue."""
    from engine.agents.managed.event_dispatcher import get_dispatcher, FROZEN

    dispatcher = get_dispatcher(sim_id)
    if not dispatcher:
        raise HTTPException(status_code=404, detail="No AI dispatcher active for this sim.")

    frozen_count = 0
    for rid in list(dispatcher.agents.keys()):
        if dispatcher.agent_states.get(rid) != FROZEN:
            dispatcher.set_agent_state(rid, FROZEN)
            ctx = dispatcher.agents[rid]
            dispatcher.session_manager.freeze_session(ctx)
            frozen_count += 1

    return APIResponse(data={"frozen_count": frozen_count})


@app.post("/api/sim/{sim_id}/ai/resume-all", response_model=APIResponse)
async def ai_resume_all(
    sim_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Resume all frozen AI agents."""
    from engine.agents.managed.event_dispatcher import get_dispatcher, FROZEN, IDLE

    dispatcher = get_dispatcher(sim_id)
    if not dispatcher:
        raise HTTPException(status_code=404, detail="No AI dispatcher active for this sim.")

    resumed_count = 0
    for rid in list(dispatcher.agents.keys()):
        if dispatcher.agent_states.get(rid) == FROZEN:
            dispatcher.set_agent_state(rid, IDLE)
            ctx = dispatcher.agents[rid]
            dispatcher.session_manager.resume_session(ctx)
            resumed_count += 1

    return APIResponse(data={"resumed_count": resumed_count})


@app.post("/api/sim/{sim_id}/ai/interrupt", response_model=APIResponse)
async def ai_critical_interrupt(
    sim_id: str,
    body: AICriticalInterruptRequest,
    user: AuthUser = Depends(require_moderator),
):
    """Send a critical interrupt to specific agents via the event queue.

    Enqueues Tier 1 (critical) events — delivered within 3 seconds.
    """
    from engine.agents.managed.event_dispatcher import get_dispatcher

    dispatcher = get_dispatcher(sim_id)
    if not dispatcher:
        raise HTTPException(status_code=404, detail="No AI dispatcher active for this sim.")

    enqueued = []
    for rid in body.role_ids:
        if rid in dispatcher.agents:
            dispatcher.enqueue(
                role_id=rid,
                tier=1,
                event_type="critical_interrupt",
                message=body.message,
            )
            enqueued.append(rid)

    return APIResponse(data={
        "enqueued": len(enqueued),
        "role_ids": enqueued,
    })


@app.post("/api/sim/{sim_id}/ai/shutdown", response_model=APIResponse)
async def ai_shutdown(
    sim_id: str,
    user: AuthUser = Depends(require_moderator),
):
    """Shut down the AI dispatcher — archive all sessions."""
    from engine.agents.managed.event_dispatcher import get_dispatcher, remove_dispatcher

    dispatcher = get_dispatcher(sim_id)

    if not dispatcher:
        raise HTTPException(status_code=404, detail="No AI system active for this sim.")

    await dispatcher.shutdown()
    remove_dispatcher(sim_id)

    return APIResponse(data={"status": "shutdown", "sim_run_id": sim_id})


class AIRestartRequest(BaseModel):
    """Request body for AI restart — configurable cleanup."""
    clear_memories: bool = False
    clear_decisions: bool = False


@app.post("/api/sim/{sim_id}/ai/restart", response_model=APIResponse)
async def ai_restart(
    sim_id: str,
    body: AIRestartRequest | None = None,
    user: AuthUser = Depends(require_moderator),
):
    """Clean up ALL AI state for a sim. Called on SIM restart or manual reset.

    1. Stops dispatcher if running
    2. Archives all Anthropic sessions
    3. Sets ai_agent_sessions status='archived'
    4. Clears unprocessed events from agent_event_queue
    5. Clears observatory AI agent logs
    6. Optionally clears agent_memories (if clear_memories=true)
    7. Optionally clears agent_decisions (if clear_decisions=true)

    After this, the moderator can click "Initialize AI Agents" again.
    """
    from engine.agents.managed.event_dispatcher import cleanup_sim_ai_state

    req = body or AIRestartRequest()
    summary = await cleanup_sim_ai_state(
        sim_run_id=sim_id,
        clear_memories=req.clear_memories,
        clear_decisions=req.clear_decisions,
    )
    logger.info("AI restart for sim %s by %s: %s", sim_id, user.id, summary)
    return APIResponse(data=summary)


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    workers = int(os.environ.get("WEB_CONCURRENCY", 4))
    reload = os.environ.get("ENGINE_RELOAD", "").lower() in ("1", "true")

    uvicorn.run(
        "engine.main:app",
        host="0.0.0.0",
        port=port,
        workers=1 if reload else workers,  # reload requires single process
        reload=reload,
        log_level="info",
    )
