"""FastAPI entry point — TTT Engine API.

Health check, SIM state queries, auth admin endpoints, LLM test endpoint.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    yield
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


@app.get("/api/sim/{sim_id}/map/units")
async def get_map_units(sim_id: str):
    """Get deployments for the map renderer — coordinates stored directly on each unit.

    Returns {units: [...]} with global_row/global_col and theater coordinates.
    No zone_id lookup needed — coordinates are canonical on each deployment row.
    """
    from engine.services.supabase import get_client
    client = get_client()

    deps = client.table("deployments") \
        .select("unit_id, country_id, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, unit_status") \
        .eq("sim_run_id", sim_id) \
        .execute().data or []

    units = [{
        "unit_id": d.get("unit_id", ""),
        "country_id": d["country_id"],
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

@app.get("/api/sim/{sim_id}/state", response_model=APIResponse)
async def get_sim_state(sim_id: str, user: AuthUser = Depends(get_current_user)):
    """Get current simulation runtime state (round, phase, timer)."""
    from engine.services.sim_run_manager import get_timer_info
    try:
        return APIResponse(data=get_timer_info(sim_id))
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
    try:
        run = get_state(sim_id)
        phase = run["current_phase"]
        if phase == "A":
            state = end_phase_a(sim_id)
            # Trigger Phase B engine processing
            round_num = run["current_round"]
            logger.info("Sim %s Phase A ended → triggering Phase B engines for R%d", sim_id, round_num)
            try:
                await _run_phase_b(sim_id, round_num)
                # Auto-advance to inter_round after engines complete
                state = end_phase_b(sim_id)
                logger.info("Sim %s Phase B complete → inter_round", sim_id)
            except Exception as e:
                logger.exception("Phase B engine failed for sim %s R%d: %s", sim_id, round_num, e)
                # Stay in processing state so moderator can retry or skip
                return APIResponse(
                    success=False,
                    data=state,
                    error=f"Phase B engines failed: {e}. Sim is in processing state — click Next Phase to skip to inter-round.",
                )
        elif phase == "B":
            state = end_phase_b(sim_id)
        elif phase == "inter_round":
            state = advance_round(sim_id)
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
    body: dict = {},
    user: AuthUser = Depends(require_moderator),
):
    """Set automatic/manual mode and dice mode. Accepts JSON body."""
    from engine.services.sim_run_manager import set_mode
    auto_advance = body.get("auto_advance", False)
    auto_approve = body.get("auto_approve", False)
    dice_mode = body.get("dice_mode", False)
    try:
        state = set_mode(sim_id, auto_advance=auto_advance, auto_approve=auto_approve)
        from engine.services.supabase import get_client
        get_client().table("sim_runs").update({"dice_mode": dice_mode}).eq("id", sim_id).execute()
        state["dice_mode"] = dice_mode
        logger.info("Sim %s mode: auto_advance=%s auto_approve=%s dice_mode=%s by %s",
                     sim_id, auto_advance, auto_approve, dice_mode, user.id)
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
    try:
        state = restart_simulation(sim_id)
        logger.info("Sim %s RESTARTED (full cleanup) by %s", sim_id, user.id)
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
    "assassination", "arrest", "change_leader",
}

# Combat actions that use dice (queue when dice_mode is on)
COMBAT_DICE_ACTIONS = {
    "ground_attack", "air_strike", "naval_combat",
    "naval_bombardment", "naval_blockade", "launch_missile_conventional",
}

ACTION_CATEGORIES: dict[str, str] = {
    # Military
    "ground_attack": "military",
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
    "propose_transaction": "economic",
    "accept_transaction": "economic",
    # Diplomatic
    "propose_agreement": "diplomatic",
    "sign_agreement": "diplomatic",
    "public_statement": "diplomatic",
    "call_org_meeting": "diplomatic",
    "meet_freely": "diplomatic",
    # Covert
    "covert_operation": "covert",
    "intelligence": "covert",
    # Political
    "arrest": "political",
    "assassination": "political",
    "change_leader": "political",
    "reassign_types": "political",
    "self_nominate": "political",
    "cast_vote": "political",
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

    if run["status"] not in ("active", "processing", "inter_round"):
        raise HTTPException(
            status_code=400,
            detail=f"Sim is '{run['status']}' — actions only allowed when active",
        )

    current_phase = run.get("current_phase", "")

    # 2. Validate role exists in this sim
    client = get_client()
    role_check = (
        client.table("roles")
        .select("id, character_name, country_id, position_type")
        .eq("sim_run_id", sim_id)
        .eq("id", body.role_id)
        .execute()
    )
    if not role_check.data:
        raise HTTPException(status_code=400, detail=f"Role '{body.role_id}' not found in sim")

    role = role_check.data[0]

    # 3. Validate role has this action type (check role_actions table)
    action_check = (
        client.table("role_actions")
        .select("id")
        .eq("sim_run_id", sim_id)
        .eq("role_id", body.role_id)
        .eq("action_id", body.action_type)
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

    # 4a. Check if action requires moderator confirmation
    auto_approve = run.get("auto_approve", False)
    if body.action_type in ACTIONS_REQUIRING_CONFIRMATION and not auto_approve:
        # Queue for moderator approval instead of immediate dispatch
        target = body.params.get("target_role", body.params.get("target_country", ""))
        target_info = f"{role['character_name']} → {target}" if target else role["character_name"]

        client.table("pending_actions").insert({
            "sim_run_id": sim_id,
            "round_num": round_num,
            "action_type": body.action_type,
            "role_id": body.role_id,
            "country_code": body.country_code,
            "target_info": target_info,
            "payload": action_payload,
            "status": "pending",
        }).execute()

        write_event(
            client, sim_id, scenario_id, round_num,
            body.country_code, body.action_type,
            f"PENDING: {body.action_type} by {role['character_name']} — awaiting moderator approval",
            {"action": action_payload, "status": "pending"},
            phase=current_phase, category=category, role_name=role["character_name"],
        )

        logger.info("Action %s by %s queued for confirmation", body.action_type, role["character_name"])
        return APIResponse(data={
            "success": True,
            "status": "pending",
            "narrative": f"{body.action_type} submitted — awaiting moderator approval",
        })

    # 4b. Check if combat action needs physical dice input
    dice_mode = run.get("dice_mode", False)
    if body.action_type in COMBAT_DICE_ACTIONS and dice_mode:
        target_info = f"{role['character_name']}: {body.action_type}"

        client.table("pending_actions").insert({
            "sim_run_id": sim_id,
            "round_num": round_num,
            "action_type": body.action_type,
            "role_id": body.role_id,
            "country_code": body.country_code,
            "target_info": target_info,
            "payload": {**action_payload, "_requires_dice": True},
            "status": "pending",
        }).execute()

        write_event(
            client, sim_id, scenario_id, round_num,
            body.country_code, body.action_type,
            f"DICE NEEDED: {body.action_type} by {role['character_name']} — moderator must input dice rolls",
            {"action": action_payload, "status": "awaiting_dice"},
            phase=current_phase, category=category, role_name=role["character_name"],
        )

        logger.info("Combat %s by %s queued for dice input", body.action_type, role["character_name"])
        return APIResponse(data={
            "success": True,
            "status": "awaiting_dice",
            "narrative": f"{body.action_type} submitted — moderator must input dice rolls",
        })

    # 5. Immediate dispatch (no confirmation needed)
    try:
        result = dispatch_action(sim_id, round_num, action_payload)
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
    user: AuthUser = Depends(require_moderator),
    precomputed_rolls: Optional[dict] = None,
):
    """Approve a pending action — dispatches it to the engine.

    For combat actions with dice_mode, pass precomputed_rolls:
      {"attacker": [[5,3,2], [6,4]], "defender": [[6,2], [4,1]]}
    """
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

    try:
        result = dispatch_action(sim_id, round_num, payload)
    except Exception as e:
        logger.exception("Confirmed action dispatch failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Engine error: {e}")

    client.table("pending_actions").update({
        "status": "approved",
        "resolved_at": "now()",
        "resolved_by": user.id,
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
    role_id: str = "", vote: str = "",
    user: AuthUser = Depends(get_current_user),
):
    """Cast a vote in an active leadership change."""
    from engine.services.change_leader import cast_leader_vote
    if not role_id or not vote:
        raise HTTPException(status_code=400, detail="role_id and vote are required")
    result = cast_leader_vote(sim_id, vote_id, role_id, vote)
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
