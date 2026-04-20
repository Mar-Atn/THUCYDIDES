"""Intelligence Engine — LLM-powered intelligence reports.

The intelligence system is the SIM's "oracle": it has access to ALL world
state and can answer any question. The LLM receives comprehensive real
data and injects 10-30% noise to simulate realistic intelligence
(not omniscient — plausible but partially misleading).

The key architectural challenge is building a context that's:
- COMPREHENSIVE enough to answer any question about any domain
- COMPACT enough to fit in a single LLM call (~20-30KB)
- STRUCTURED so the LLM can reason about it

Data domains accessed:
  - All 20 countries: GDP, treasury, stability, support, nuclear, AI levels
  - Military: unit counts per country per branch + key deployments
  - Relationships: wars, alliances, tensions
  - Agreements: active public + secret (intelligence sees ALL)
  - Recent events: last 3 rounds of significant actions
  - Transactions: recent exchange history
  - Nuclear state: who has what tier, tests conducted
  - Blockades: active chokepoint blockades
  - Basing rights: who deploys where
"""

from __future__ import annotations

import logging
from typing import Optional

from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


def generate_intelligence_report(
    sim_run_id: str,
    round_num: int,
    question: str,
    requester_country: str,
    requester_role: str = "",
) -> dict:
    """Generate an intelligence report answering any question about the SIM world.

    Loads comprehensive world state, calls LLM with noise injection
    instructions, returns the report.

    Returns ``{success, report, question, round_num}``.
    """
    client = get_client()

    # Build comprehensive context
    context = _build_full_world_context(client, sim_run_id, round_num)

    # Call LLM
    report_text = _call_intelligence_llm(question, context, requester_country)

    # Write event (report delivered to requester)
    scenario_id = _get_scenario_id(client, sim_run_id)
    _write_event(client, sim_run_id, scenario_id, round_num, requester_country,
                 "intelligence_report_received",
                 f"{requester_country} receives intelligence report: '{question[:80]}'",
                 {"question": question, "requester_role": requester_role,
                  "report_length": len(report_text)})

    # Create artefact — classified report delivered to requester's Confidential tab
    try:
        import uuid
        client.table("artefacts").insert({
            "id": f"intel_{uuid.uuid4().hex[:12]}",
            "sim_run_id": sim_run_id,
            "role_id": requester_role,
            "artefact_type": "intelligence_report",
            "classification": "CONFIDENTIAL",
            "title": f"Intelligence Report — R{round_num}",
            "subtitle": question[:100],
            "from_entity": "Intelligence Directorate",
            "content_html": (
                f"<p><strong>CLASSIFIED — INTELLIGENCE BRIEFING</strong></p>"
                f"<p><em>RE: {question}</em></p>"
                f"<hr/>"
                f"{''.join(f'<p>{para.strip()}</p>' for para in report_text.split(chr(10)) if para.strip())}"
            ),
            "round_delivered": round_num,
            "is_read": False,
        }).execute()
    except Exception as e:
        logger.warning("[intelligence] artefact creation failed: %s", e)

    logger.info("[intelligence] report generated for %s (%s): '%s' (%d chars)",
                requester_country, requester_role, question[:60], len(report_text))

    return {
        "success": True,
        "report": report_text,
        "question": question,
        "round_num": round_num,
        "narrative": f"Intelligence report delivered to your Confidential tab.",
    }


# ---------------------------------------------------------------------------
# Comprehensive world context builder
# ---------------------------------------------------------------------------


def _build_full_world_context(client, sim_run_id: str, round_num: int) -> str:
    """Build a comprehensive text summary of ALL world state for the LLM.

    Organized by domain. Formatted for maximum information density
    while staying under ~25KB. The LLM uses this to answer ANY question.
    """
    sections = []

    # 0. GAME MECHANICS & RULES (for analysis, never disclose formulas)
    sections.append(_section_rules())

    # 1. ALL COUNTRIES — economic + political + tech snapshot
    sections.append(_section_countries(client, sim_run_id, round_num))

    # 2. MILITARY — unit counts per country per branch
    sections.append(_section_military(client, sim_run_id, round_num))

    # 3. RELATIONSHIPS — wars, alliances
    sections.append(_section_relationships(client, sim_run_id))

    # 4. AGREEMENTS — all active (intelligence sees both public + secret)
    sections.append(_section_agreements(client, sim_run_id))

    # 5. RECENT EVENTS — last 3 rounds
    sections.append(_section_events(client, sim_run_id, round_num))

    # 6. RECENT TRANSACTIONS
    sections.append(_section_transactions(client, sim_run_id))

    # 7. NUCLEAR STATUS
    sections.append(_section_nuclear(client, sim_run_id, round_num))

    # 8. BLOCKADES
    sections.append(_section_blockades(client, sim_run_id))

    # 9. BASING RIGHTS
    sections.append(_section_basing_rights(client, sim_run_id))

    return "\n\n".join(s for s in sections if s)


def _section_rules() -> str:
    """Game mechanics and rules — for LLM analysis, never disclosed to players."""
    return """[GAME MECHANICS — USE FOR ANALYSIS, NEVER DISCLOSE EXACT FORMULAS]

STABILITY (0-10 scale):
- Core indicator of country health. Below 4.0 allows leadership change.
- Driven by: GDP growth, social spending, war involvement, sanctions, inflation.
- War and military losses reduce stability. High inflation erodes stability.
- Protests and regime instability trigger below 3.0.

ECONOMY:
- GDP grows based on budget allocation (social, military, tech spending).
- Inflation rises from excessive spending, sanctions, oil price shocks.
- Sanctions reduce trade revenue. Tariffs affect bilateral trade.
- Treasury = liquid funds. Debt burden affects long-term growth.
- OPEC members (Caribe, Mirage, Persia, Sarmatia, Solaria) can set oil production.

MILITARY:
- 5 unit types: ground, naval, tactical_air, strategic_missile, air_defense.
- Units are active (deployed) or reserve. Reserve units can be deployed between rounds.
- Combat is probabilistic with dice mechanics. Larger forces have advantage.
- Air defense intercepts missiles and air strikes.
- Naval blockades at chokepoints restrict trade.

NUCLEAR:
- 3 levels: L1 (basic), L2 (intermediate), L3 (advanced arsenal).
- Must be confirmed via nuclear test before launch capability.
- Nuclear launch requires 3-way authorization (HoS + 2 officers).
- Missile range: L1=2 hexes, L2=4 hexes, L3=global.
- Nuclear strike causes: unit destruction, GDP damage, stability drop.
- Countries with L2+ and confirmed can attempt interception.

POLITICAL:
- Leadership can change if stability drops below threshold.
- Assassination is possible but probabilistic and risky.
- Arrested leaders lose all actions temporarily.
- Columbia has democratic elections (mid-term R2, presidential R6).
- Opposition strength in elections grows during economic hardship.

RELATIONSHIPS:
- Types: Alliance, Economic Partnership, Neutral, Hostile, At War.
- Military alliances provide mutual defense obligations.
- War = open military conflict. Any attack auto-sets relationship to At War.
- Agreements: Military Alliance, Trade Agreement, Peace Treaty, Ceasefire.

COVERT OPERATIONS:
- Sabotage: can target infrastructure, nuclear sites, or military assets.
- Propaganda: can boost or undermine stability in any country.
- Intelligence: can gather information on any aspect of the world.
- All covert ops have detection risk. Attribution is not guaranteed.

GEOGRAPHY:
- 20 countries on a hex-based global map.
- 2 theater maps (Eastern Ereb, Mashriq) for detailed regional conflicts.
- 3 naval chokepoints that can be blockaded.
- Territory can be occupied by ground forces."""


def _section_countries(client, sim_run_id, round_num) -> str:
    """All 20 countries: economic + political + tech state."""
    # Use the countries table (live state, not country_states_per_round)
    res = client.table("countries").select(
        "id,sim_name,gdp,treasury,inflation,stability,"
        "nuclear_level,nuclear_confirmed,ai_level,debt_burden,"
        "mil_ground,mil_naval,mil_tactical_air,mil_strategic_missiles,mil_air_defense"
    ).eq("sim_run_id", sim_run_id).order("id").execute().data or []

    lines = ["[ALL COUNTRIES — Round " + str(round_num) + "]"]
    lines.append(f"{'Country':12} {'Name':15} {'GDP':>6} {'Tres':>5} {'Stab':>4} {'Infl':>5} {'Nuc':>5} {'AI':>3} {'Debt':>5}")
    for c in res:
        cc = c.get("id", "?")
        nuc_lvl = int(c.get('nuclear_level') or 0)
        nuc = f"L{nuc_lvl}" + ("ok" if c.get("nuclear_confirmed") else "") if nuc_lvl > 0 else "-"
        lines.append(
            f"{cc:12} {str(c.get('sim_name',''))[:15]:15} {float(c.get('gdp') or 0):6.0f} {float(c.get('treasury') or 0):5.0f} "
            f"{float(c.get('stability') or 0):4.1f} {float(c.get('inflation') or 0):5.1f} "
            f"{nuc:>5} {int(c.get('ai_level') or 0):3d} {float(c.get('debt_burden') or 0)*100:5.1f}%"
        )
    return "\n".join(lines)


def _section_military(client, sim_run_id, round_num) -> str:
    """Military unit counts per country per branch."""
    # Use deployments table (live state)
    res = client.table("deployments").select(
        "country_id,unit_type,unit_status"
    ).eq("sim_run_id", sim_run_id).execute().data or []

    counts: dict[str, dict[str, dict[str, int]]] = {}
    for r in res:
        cc = r.get("country_id", "")
        ut = r.get("unit_type", "")
        st = r.get("unit_status", "")
        counts.setdefault(cc, {}).setdefault(ut, {}).setdefault(st, 0)
        counts[cc][ut][st] += 1

    lines = ["[MILITARY FORCES]"]
    for cc in sorted(counts.keys()):
        branches = counts[cc]
        parts = []
        for branch in ("ground", "naval", "tactical_air", "strategic_missile", "air_defense"):
            statuses = branches.get(branch, {})
            active = statuses.get("active", 0)
            reserve = statuses.get("reserve", 0)
            if active + reserve > 0:
                parts.append(f"{branch}:{active}a+{reserve}r")
        if parts:
            lines.append(f"  {cc:12} {', '.join(parts)}")
    if len(lines) == 1:
        lines.append("  (no military data)")
    return "\n".join(lines)


def _section_relationships(client, sim_run_id) -> str:
    """Wars, alliances, tensions."""
    try:
        res = client.table("relationships").select(
            "from_country_id,to_country_id,status,relationship"
        ).eq("sim_run_id", sim_run_id).execute().data or []
    except Exception:
        res = []

    if not res:
        # Try without sim_run_id filter (legacy data)
        try:
            res = client.table("relationships").select(
                "from_country_id,to_country_id,status,relationship"
            ).execute().data or []
        except Exception:
            res = []

    lines = ["[RELATIONSHIPS]"]
    for r in res:
        status = r.get("status") or r.get("relationship") or "neutral"
        lines.append(f"  {r.get('from_country_id', '?'):12} → {r.get('to_country_id', '?'):12} : {status}")
    if len(lines) == 1:
        lines.append("  (no explicit relationships recorded)")
    return "\n".join(lines)


def _section_agreements(client, sim_run_id) -> str:
    """All agreements (intelligence sees both public AND secret)."""
    try:
        res = client.table("agreements").select(
            "agreement_name,agreement_type,visibility,signatories,terms,status"
        ).eq("sim_run_id", sim_run_id).execute().data or []
    except Exception:
        res = []

    lines = ["[AGREEMENTS (ALL — including secret)]"]
    for a in res:
        sigs = ", ".join(a.get("signatories") or [])
        vis = "SECRET" if a.get("visibility") == "secret" else "public"
        lines.append(
            f"  [{a.get('status', '?')}] {a.get('agreement_name', '?')} ({a.get('agreement_type', '?')}) "
            f"— {sigs} [{vis}]"
        )
        if a.get("terms"):
            lines.append(f"    Terms: {a['terms'][:200]}")
    if len(lines) == 1:
        lines.append("  (no agreements)")
    return "\n".join(lines)


def _section_events(client, sim_run_id, round_num) -> str:
    """Recent significant events (last 3 rounds)."""
    low_round = max(0, round_num - 3)
    try:
        res = client.table("observatory_events").select(
            "round_num,event_type,country_code,summary"
        ).eq("sim_run_id", sim_run_id) \
         .gte("round_num", low_round) \
         .order("round_num", desc=True) \
         .order("created_at", desc=True) \
         .limit(50).execute().data or []
    except Exception:
        res = []

    lines = [f"[RECENT EVENTS (R{low_round}–R{round_num})]"]
    for e in res:
        lines.append(
            f"  R{e.get('round_num', '?')} {e.get('event_type', '?'):25} "
            f"{e.get('country_code', '?'):10} {(e.get('summary') or '')[:100]}"
        )
    if len(lines) == 1:
        lines.append("  (no recent events)")
    return "\n".join(lines)


def _section_transactions(client, sim_run_id) -> str:
    """Recent exchange transactions."""
    try:
        res = client.table("exchange_transactions").select(
            "round_num,proposer,counterpart,offer,request,status"
        ).eq("sim_run_id", sim_run_id) \
         .order("created_at", desc=True) \
         .limit(20).execute().data or []
    except Exception:
        res = []

    lines = ["[RECENT TRANSACTIONS]"]
    for t in res:
        lines.append(
            f"  R{t.get('round_num', '?')} {t.get('proposer', '?')}→{t.get('counterpart', '?')} "
            f"[{t.get('status', '?')}]"
        )
    if len(lines) == 1:
        lines.append("  (no transactions)")
    return "\n".join(lines)


def _section_nuclear(client, sim_run_id, round_num) -> str:
    """Nuclear program status."""
    # Use countries table (live state)
    res = client.table("countries").select(
        "id,nuclear_level,nuclear_confirmed,nuclear_rd_progress"
    ).eq("sim_run_id", sim_run_id).execute().data or []

    lines = ["[NUCLEAR STATUS]"]
    for c in res:
        nuc_level = int(c.get("nuclear_level") or 0)
        if nuc_level > 0:
            confirmed = "confirmed" if c.get("nuclear_confirmed") else "UNCONFIRMED"
            progress = float(c.get("nuclear_rd_progress") or 0)
            lines.append(f"  {c['id']:12} Level {nuc_level} {confirmed} (R&D progress: {progress:.0%})")

    # Nuclear actions in this run
    try:
        actions = client.table("nuclear_actions").select(
            "action_type,country_code,status,round_num"
        ).eq("sim_run_id", sim_run_id).execute().data or []
        for a in actions:
            lines.append(f"  ACTION: {a.get('country_code')} {a.get('action_type')} R{a.get('round_num')} → {a.get('status')}")
    except Exception:
        pass

    if len(lines) == 1:
        lines.append("  (no nuclear-capable countries)")
    return "\n".join(lines)


def _section_blockades(client, sim_run_id) -> str:
    """Active blockades."""
    try:
        res = client.table("blockades").select(
            "zone_id,imposer_country_id,level,status"
        ).eq("sim_run_id", sim_run_id).eq("status", "active").execute().data or []
    except Exception:
        res = []

    lines = ["[ACTIVE BLOCKADES]"]
    for b in res:
        lines.append(f"  {b.get('zone_id', '?')} by {b.get('imposer_country_id', '?')} [{b.get('level', '?')}]")
    if len(lines) == 1:
        lines.append("  (no active blockades)")
    return "\n".join(lines)


def _section_basing_rights(client, sim_run_id) -> str:
    """Active basing rights."""
    try:
        res = client.table("basing_rights").select(
            "host_country,guest_country,source"
        ).eq("sim_run_id", sim_run_id).eq("status", "active").execute().data or []
    except Exception:
        res = []

    lines = ["[ACTIVE BASING RIGHTS]"]
    for b in res:
        lines.append(f"  {b.get('host_country', '?')} hosts {b.get('guest_country', '?')} ({b.get('source', '?')})")
    if len(lines) == 1:
        lines.append("  (no active basing rights)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def _call_intelligence_llm(question: str, context: str, requester_country: str) -> str:
    """Call LLM with world context + noise injection instructions."""
    try:
        from engine.services.llm import call_llm_sync
        from engine.config.settings import LLMUseCase

        prompt = (
            f"You are a senior intelligence analyst preparing a CLASSIFIED briefing.\n\n"
            f"REQUESTING COUNTRY: {requester_country.upper()}\n\n"
            f"QUESTION FROM LEADERSHIP:\n{question}\n\n"
            f"COMPLETE WORLD STATE (your intelligence database):\n{context}\n\n"
            f"INSTRUCTIONS:\n"
            f"- Write a 1-3 paragraph intelligence report answering the question.\n"
            f"- Use the real data as your base.\n"
            f"- INJECT approximately 20-25% misleading or imprecise information:\n"
            f"  * Slightly wrong numbers, plausible but false assessments, omissions.\n"
            f"- The requester does NOT know the noise level.\n"
            f"- Use SIM country names only (no real-world names).\n"
            f"- Style: professional intelligence briefing. Concise, analytical.\n"
            f"- Mark confidence level: HIGH / MODERATE / LOW for key assessments.\n"
            f"- Do NOT reveal that you are injecting noise or that you are an AI."
        )

        response = call_llm_sync(
            use_case=LLMUseCase.QUICK_SCAN,
            messages=[{"role": "user", "content": prompt}],
            system="You are a senior intelligence analyst. Write a classified briefing. Be concise and professional.",
            max_tokens=600,
            temperature=0.7,
        )
        return response.text
    except Exception as e:
        logger.warning("Intelligence LLM call failed: %s", e)
        return (
            f"INTELLIGENCE REPORT — {requester_country.upper()}\n\n"
            f"RE: {question}\n\n"
            f"Data collection is in progress. Preliminary assessment suggests "
            f"heightened activity in the relevant theater. Further analysis required. "
            f"Confidence: LOW.\n\n"
            f"[Report generation encountered technical difficulties. "
            f"Manual analysis recommended.]"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_scenario_id(client, sim_run_id):
    try:
        r = client.table("sim_runs").select("scenario_id").eq("id", sim_run_id).limit(1).execute()
        return r.data[0]["scenario_id"] if r.data else None
    except Exception:
        return None


def _write_event(client, sim_run_id, scenario_id, round_num, country_code, event_type, summary, payload):
    if not scenario_id:
        return
    try:
        client.table("observatory_events").insert({
            "sim_run_id": sim_run_id,
            "scenario_id": scenario_id,
            "round_num": round_num,
            "event_type": event_type,
            "country_code": country_code,
            "summary": summary,
            "payload": payload,
        }).execute()
    except Exception as e:
        logger.debug("event write failed: %s", e)
