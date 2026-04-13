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

import asyncio
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

    logger.info("[intelligence] report generated for %s: '%s' (%d chars)",
                requester_country, question[:60], len(report_text))

    return {
        "success": True,
        "report": report_text,
        "question": question,
        "round_num": round_num,
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


def _section_countries(client, sim_run_id, round_num) -> str:
    """All 20 countries: economic + political + tech state."""
    res = client.table("country_states_per_round").select(
        "country_code,gdp,treasury,inflation,stability,political_support,"
        "war_tiredness,nuclear_level,nuclear_confirmed,ai_level,"
        "opec_production,sanctions_coefficient,tariff_coefficient,"
        "martial_law_declared"
    ).eq("sim_run_id", sim_run_id).lte("round_num", round_num) \
     .order("round_num", desc=True).execute().data or []

    # Dedupe to latest per country
    by_cc: dict[str, dict] = {}
    for r in res:
        cc = r.get("country_code")
        if cc and cc not in by_cc:
            by_cc[cc] = r

    lines = ["[ALL COUNTRIES — Round " + str(round_num) + "]"]
    lines.append(f"{'Country':12} {'GDP':>6} {'Tres':>5} {'Stab':>4} {'Supp':>4} {'WT':>3} {'Nuc':>3} {'AI':>3} {'Inf':>6}")
    for cc in sorted(by_cc.keys()):
        c = by_cc[cc]
        nuc = f"T{c.get('nuclear_level', 0)}" + ("✓" if c.get("nuclear_confirmed") else "")
        lines.append(
            f"{cc:12} {float(c.get('gdp') or 0):6.0f} {float(c.get('treasury') or 0):5.0f} "
            f"{int(c.get('stability') or 0):4d} {int(c.get('political_support') or 0):4d} "
            f"{int(c.get('war_tiredness') or 0):3d} {nuc:>3} {int(c.get('ai_level') or 0):3d} "
            f"{float(c.get('inflation') or 0):6.3f}"
        )
    return "\n".join(lines)


def _section_military(client, sim_run_id, round_num) -> str:
    """Military unit counts per country per branch."""
    res = client.table("unit_states_per_round").select(
        "country_code,unit_type,status"
    ).eq("sim_run_id", sim_run_id).lte("round_num", round_num) \
     .order("round_num", desc=True).execute().data or []

    # Dedupe by unit (latest round snapshot)
    # Since we can't dedupe by unit_code here (no column), count from all rows
    # This gives approximate counts (good enough for intelligence)
    counts: dict[str, dict[str, dict[str, int]]] = {}  # cc → branch → status → count
    for r in res:
        cc = r.get("country_code", "")
        ut = r.get("unit_type", "")
        st = r.get("status", "")
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
    """Nuclear program status + tests/launches."""
    # Country nuclear levels from country_states
    res = client.table("country_states_per_round").select(
        "country_code,nuclear_level,nuclear_confirmed,nuclear_rd_progress"
    ).eq("sim_run_id", sim_run_id).lte("round_num", round_num) \
     .order("round_num", desc=True).execute().data or []

    by_cc: dict[str, dict] = {}
    for r in res:
        cc = r.get("country_code")
        if cc and cc not in by_cc and int(r.get("nuclear_level", 0) or 0) > 0:
            by_cc[cc] = r

    lines = ["[NUCLEAR STATUS]"]
    for cc in sorted(by_cc.keys()):
        c = by_cc[cc]
        confirmed = "confirmed" if c.get("nuclear_confirmed") else "UNCONFIRMED"
        progress = float(c.get("nuclear_rd_progress") or 0)
        lines.append(f"  {cc:12} T{c.get('nuclear_level', 0)} {confirmed} (progress: {progress:.2f})")

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
        from engine.services.llm import call_llm
        from engine.config.settings import LLMUseCase

        prompt = (
            f"You are a senior intelligence analyst preparing a CLASSIFIED report.\n\n"
            f"REQUESTING COUNTRY: {requester_country.upper()}\n\n"
            f"QUESTION FROM LEADERSHIP:\n{question}\n\n"
            f"COMPLETE WORLD STATE (your intelligence database):\n{context}\n\n"
            f"INSTRUCTIONS:\n"
            f"- Write a 1-3 paragraph intelligence report answering the question.\n"
            f"- Use the real data as your base.\n"
            f"- INJECT 10-30% misleading information (mandatory noise):\n"
            f"  * Simple factual questions: ~10% noise (slightly wrong numbers)\n"
            f"  * Moderate analysis: ~20% noise (plausible but false assessments)\n"
            f"  * Broad strategic questions: ~30% noise (significant omissions + false conclusions)\n"
            f"- Noise means: slightly wrong numbers, plausible but false assessments, omissions.\n"
            f"- The requester does NOT know the noise level.\n"
            f"- Use SIM country names only (no real-world names).\n"
            f"- Be professional, concise, and analytical.\n"
            f"- Mark confidence level: HIGH / MODERATE / LOW for key assessments."
        )

        response = asyncio.run(call_llm(
            use_case=LLMUseCase.AGENT_REFLECTION,
            messages=[{"role": "user", "content": prompt}],
            system="You are a senior intelligence analyst. Write a classified briefing. Be concise and professional.",
            max_tokens=600,
            temperature=0.7,
        ))
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
