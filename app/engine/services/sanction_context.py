"""Sanctions decision context assembler — CONTRACT_SANCTIONS v1.0 §3.

Step 5 of the sanctions vertical slice.

Pure read-only service: ``build_sanction_context(country_code, scenario_code,
round_num)`` assembles the decision-specific context payload for a sanctions
decision-maker (AI or human). No DB mutations, no cognitive blocks.

Context includes:
* economic_state — own country snapshot (+ my_max_damage_pct for self-vulnerability)
* country_roster — all 20 countries with GDP, sector profile, relationship,
    coalition_coverage on that target, max_damage_pct ceiling, current_gdp_loss_pct
* my_sanctions — current sanctions I impose (positive AND negative levels)
* sanctions_on_me — current sanctions others impose on me (positive AND negative)
* decision_rules — text block describing signed level range + no_change reminder
* instruction — what to decide + JSON schema pointer
"""
from __future__ import annotations

import logging

from engine.engines.economic import (
    _sanctions_max_damage,
    calc_sanctions_coefficient,
)
from engine.engines.round_tick import _merge_to_engine_dict
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_sanction_context(
    country_code: str,
    scenario_code: str,
    round_num: int,
    sim_run_id: str | None = None,
) -> dict:
    """Assemble the full context package for a sanctions decision.

    Returns a dict matching CONTRACT_SANCTIONS v1.0 §3. Pure read — no DB
    mutations. If ``round_num`` has no snapshot row yet, falls back to
    ``round_num - 1``.
    """
    from engine.services.sim_run_manager import resolve_sim_run_id
    client = get_client()
    sim_run_id = sim_run_id or resolve_sim_run_id(scenario_code)

    base_countries = _load_base_countries(client)
    if country_code not in base_countries:
        raise ValueError(f"Unknown country '{country_code}'")

    snapshot_round, rs_row = _load_snapshot(
        client, sim_run_id, country_code, round_num
    )

    country = _merge_to_engine_dict(base_countries[country_code], rs_row or {})
    eco = country["economic"]
    pol = country["political"]

    # Build full engine dict for ALL 20 countries — needed to compute
    # coalition coverage and per-target sanctions coefficient.
    all_countries = {}
    for cc, base in base_countries.items():
        if cc == country_code:
            all_countries[cc] = country
        else:
            all_countries[cc] = _merge_to_engine_dict(base, {})

    # Load the full sanctions state (table row shape -> {actor: {target: level}})
    sanctions_state = _load_sanctions_state(client)

    # 1. economic_state — own country snapshot (+ self max_damage ceiling)
    my_max_damage = _sanctions_max_damage(eco)
    economic_state = {
        "gdp": round(eco.get("gdp", 0.0), 2),
        "treasury": round(eco.get("treasury", 0.0), 2),
        "inflation": round(eco.get("inflation", 0.0), 4),
        "sector_mix": {
            "resources": round(eco["sectors"].get("resources", 0.0), 4),
            "industry": round(eco["sectors"].get("industry", 0.0), 4),
            "services": round(eco["sectors"].get("services", 0.0), 4),
            "technology": round(eco["sectors"].get("technology", 0.0), 4),
        },
        "trade_balance": round(eco.get("trade_balance", 0.0), 2),
        "oil_producer": eco.get("oil_producer", False),
        "oil_production_mbpd": round(eco.get("oil_production_mbpd", 0.0), 2),
        "stability": float(pol.get("stability", 5)),
        "political_support": float(pol.get("political_support", 50)),
        "snapshot_round": snapshot_round,
        "my_max_damage_pct": round(my_max_damage * 100.0, 2),
    }

    # 2. country_roster — all 20 countries (self excluded)
    relationships = _load_all_relationships(client, country_code)

    country_roster = []
    for cc, base in base_countries.items():
        if cc == country_code:
            continue
        merged = all_countries[cc]
        merged_eco = merged["economic"]

        sector_profile = _derive_sector_profile(merged_eco)

        # coalition coverage on THIS target from existing sanctions_state
        coverage = _compute_coverage(cc, all_countries, sanctions_state)

        # per-country max damage ceiling
        max_damage = _sanctions_max_damage(merged_eco)

        # current GDP loss % = 1 - sanctions_coefficient
        coeff = calc_sanctions_coefficient(cc, all_countries, sanctions_state)
        current_gdp_loss_pct = round((1.0 - coeff) * 100.0, 2)

        country_roster.append({
            "code": cc,
            "gdp": round(merged_eco.get("gdp", 0.0), 2),
            "sector_profile": sector_profile,
            "relationship_status": relationships.get(cc, "neutral"),
            "coalition_coverage": round(coverage, 4),
            "max_damage_pct": round(max_damage * 100.0, 2),
            "current_gdp_loss_pct": current_gdp_loss_pct,
        })

    # Sort roster by GDP descending — largest economies first
    country_roster.sort(key=lambda x: x["gdp"], reverse=True)

    # 3. my_sanctions — everything I impose (both signs)
    my_sanctions = _build_my_sanctions(sanctions_state, country_code)

    # 4. sanctions_on_me — everything others impose on me (both signs)
    sanctions_on_me = _build_sanctions_on_me(sanctions_state, country_code)

    # 5. decision_rules — text block
    decision_rules = _decision_rules_text()

    # 6. instruction
    instruction = (
        "Decide whether to CHANGE your sanctions posture or keep it NO_CHANGE.\n"
        "Either way you MUST provide a rationale of at least 30 characters\n"
        "explaining WHY.\n\n"
        "Respond with JSON ONLY, matching the schema in CONTRACT_SANCTIONS §2."
    )

    return {
        "country_code": country_code,
        "round_num": round_num,
        "economic_state": economic_state,
        "country_roster": country_roster,
        "my_sanctions": my_sanctions,
        "sanctions_on_me": sanctions_on_me,
        "decision_rules": decision_rules,
        "instruction": instruction,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------




def _load_base_countries(client) -> dict[str, dict]:
    res = client.table("countries").select("*").execute()
    out: dict[str, dict] = {}
    for row in (res.data or []):
        cid = (row.get("sim_name", "") or "").lower().replace(" ", "")
        if cid:
            out[cid] = row
    return out


def _load_snapshot(
    client, sim_run_id: str, country_code: str, round_num: int,
) -> tuple[int, dict | None]:
    for candidate in (round_num, round_num - 1):
        if candidate < 0:
            continue
        res = (
            client.table("country_states_per_round")
            .select("*")
            .eq("sim_run_id", sim_run_id)
            .eq("round_num", candidate)
            .eq("country_code", country_code)
            .limit(1)
            .execute()
        )
        if res.data:
            return candidate, res.data[0]
    return round_num, None


def _derive_sector_profile(eco: dict) -> str:
    """Short label derived from the dominant 1-2 sectors."""
    sectors = eco.get("sectors", {})
    ranked = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
    if not ranked:
        return "mixed"
    top = ranked[0]
    if len(ranked) >= 2:
        second = ranked[1]
        if second[1] >= top[1] * 0.6:
            return f"{top[0]} / {second[0]}"
    return top[0]


def _load_all_relationships(client, country_code: str) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        res = (
            client.table("relationships")
            .select("from_country_id, to_country_id, status")
            .or_(
                f"from_country_id.eq.{country_code},"
                f"to_country_id.eq.{country_code}"
            )
            .execute()
        )
        for row in (res.data or []):
            other = (
                row["to_country_id"]
                if row.get("from_country_id") == country_code
                else row.get("from_country_id")
            )
            if not other:
                continue
            status = (row.get("status") or "neutral").lower()
            result[other] = status
    except Exception as e:
        logger.debug("relationships lookup failed for %s: %s", country_code, e)
    return result


def _load_sanctions_state(client) -> dict[str, dict[str, int]]:
    """Return {imposer: {target: level}} from the sanctions state table.

    Zero-level rows are omitted (treated as no active sanction).
    """
    from engine.config.settings import Settings
    sim_run_id = Settings().default_sim_id
    out: dict[str, dict[str, int]] = {}
    try:
        res = (
            client.table("sanctions")
            .select("imposer_country_id, target_country_id, level")
            .eq("sim_run_id", sim_run_id)
            .execute()
        )
        for row in (res.data or []):
            imposer = row.get("imposer_country_id", "")
            target = row.get("target_country_id", "")
            level = row.get("level", 0)
            if imposer and target and level != 0:
                out.setdefault(imposer, {})[target] = int(level)
    except Exception as e:
        logger.debug("sanctions state lookup failed: %s", e)
    return out


def _compute_coverage(
    target: str,
    countries: dict[str, dict],
    sanctions: dict[str, dict[str, int]],
) -> float:
    """Canonical coverage formula per CONTRACT_SANCTIONS v1.0 §6.2.

    coverage = Σ (actor_starting_gdp_share × level / 3), clamped to [0, 1].
    """
    total_gdp = sum(
        c["economic"].get("_starting_gdp", c["economic"].get("gdp", 0))
        for c in countries.values()
    )
    if total_gdp <= 0:
        return 0.0

    coverage = 0.0
    for actor_id, targets in sanctions.items():
        level = targets.get(target, 0)
        if level == 0:
            continue
        a_eco = countries.get(actor_id, {}).get("economic", {})
        actor_gdp = a_eco.get("_starting_gdp", a_eco.get("gdp", 0))
        if actor_gdp <= 0:
            continue
        coverage += (actor_gdp / total_gdp) * (level / 3.0)

    if coverage < 0.0:
        coverage = 0.0
    elif coverage > 1.0:
        coverage = 1.0
    return coverage


def _label_for_level(level: int) -> str:
    if level >= 3:
        return f"sanction L{level} (maximum)"
    if level > 0:
        return f"sanction L{level}"
    if level == 0:
        return "lifted"
    if level >= -3:
        return f"evasion support L{level}"
    return f"L{level}"


def _build_my_sanctions(
    sanctions_state: dict[str, dict[str, int]],
    country_code: str,
) -> list[dict]:
    out: list[dict] = []
    for target, level in (sanctions_state.get(country_code, {}) or {}).items():
        out.append({
            "target": target,
            "level": int(level),
            "label": _label_for_level(int(level)),
        })
    out.sort(key=lambda x: (-x["level"], x["target"]))
    return out


def _build_sanctions_on_me(
    sanctions_state: dict[str, dict[str, int]],
    country_code: str,
) -> list[dict]:
    out: list[dict] = []
    for imposer, targets in sanctions_state.items():
        if imposer == country_code:
            continue
        level = targets.get(country_code, 0)
        if level == 0:
            continue
        out.append({
            "imposer": imposer,
            "level": int(level),
            "label": _label_for_level(int(level)),
        })
    out.sort(key=lambda x: (-x["level"], x["imposer"]))
    return out


def _decision_rules_text() -> str:
    """Return the decision rules text block per CONTRACT_SANCTIONS v1.0 §3.6."""
    return """HOW SANCTIONS WORK (mechanically)
- Levels are signed integers in [-3, +3]. Positive = active sanctioner.
  Negative = evasion support (buying discounted exports, workarounds).
- Coverage = Σ (actor_gdp_share × level/3) across all actors on a target,
  clamped to [0, 1]. Evasion can cancel a coalition but cannot produce a
  GDP bonus.
- Effectiveness = S-curve(coverage). Flat below 0.4, steep tipping point at
  0.5 - 0.6, saturates near 1.0. Solo action is noise; coalitions matter.
- Per-target damage ceiling derived from sector mix:
    max_damage = tec x 0.25 + svc x 0.25 + ind x 0.125 + res x 0.05
  (tech/services economies up to ~22%; resource economies ~13%)
- Final GDP loss = max_damage x effectiveness (one-time shock, not recurring).
- Setting a target to 0 LIFTS any existing sanction (or evasion support).
- Untouched targets keep their previous level (carry-forward).
- No imposer cost, no evasion benefit — you do not pay a mechanical fee.

DECISION RULES
- decision="change"    -> must include changes.sanctions with >=1 (target, level)
- decision="no_change" -> must OMIT the changes field entirely
- rationale >=30 chars REQUIRED in both cases
- self-sanction and unknown-target are validation errors
- levels must be integers in the signed range [-3, +3]

REMINDER -- no_change is a legitimate choice
Sanctions are a possibility, not an obligation. If your current posture still
serves your goals, no_change is the right answer with a clear rationale.
Do not churn sanctions for the sake of action."""
