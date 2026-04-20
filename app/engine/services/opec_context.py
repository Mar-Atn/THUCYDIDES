"""OPEC production decision context assembler — CONTRACT_OPEC v1.0 §3.

Step 5 of the OPEC vertical slice.

Pure read-only service: ``build_opec_context(country_code, scenario_code,
round_num)`` assembles the decision-specific context payload for an OPEC+
production decision-maker (AI or human). No DB mutations, no cognitive
blocks, no commentary — facts only.

Context includes (CONTRACT_OPEC v1.0 §3):

* economic_state — own country snapshot, oil revenue focus
* oil_market_state — current oil price + total world supply + OPEC+ share
* oil_price_history — list of {round, oil_price} for rounds already played
* oil_producers_table — all oil producers (mbpd > 0 + oil_producer flag)
* chokepoint_blockades — gulf_gate / caribe_passage / formosa_strait status
* sanctions_on_producers — max sanctions level imposed on each producer
* tariffs_on_producers — active tariff rows involving an oil producer
* decision_rules — text block describing OPEC+ schema + no_change reminder
* instruction — what to decide + JSON schema pointer

Only OPEC+ members may call ``build_opec_context`` — non-members raise
``ValueError`` (matches the validator-layer ``NOT_OPEC_MEMBER`` error path).
"""
from __future__ import annotations

import logging

from engine.engines.round_tick import _merge_to_engine_dict
from engine.services.opec_validator import CANONICAL_OPEC_MEMBERS
from engine.services.supabase import get_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_opec_context(
    country_code: str,
    scenario_code: str,
    round_num: int,
    sim_run_id: str | None = None,
) -> dict:
    """Assemble the full context package for an OPEC+ production decision.

    Returns a dict matching CONTRACT_OPEC v1.0 §3. Pure read — no DB
    mutations. Raises ``ValueError`` if the country is not in the canonical
    OPEC+ roster.

    F1: if ``sim_run_id`` is provided, reads from that isolated run; else
    resolves to the legacy archived run for ``scenario_code``.
    """
    country_code = (country_code or "").strip().lower()

    if country_code not in CANONICAL_OPEC_MEMBERS:
        raise ValueError(
            f"NOT_OPEC_MEMBER: {country_code!r} is not in the OPEC+ roster "
            f"{sorted(CANONICAL_OPEC_MEMBERS)}"
        )

    from engine.services.sim_run_manager import resolve_sim_run_id
    client = get_client()
    sim_run_id = sim_run_id or resolve_sim_run_id(scenario_code)

    base_countries = _load_base_countries(client)
    if country_code not in base_countries:
        raise ValueError(f"Unknown country '{country_code}'")

    # Load the current-round snapshot for every country so we can read
    # opec_production (the live OPEC+ level per member).
    cs_rows = _load_country_states(client, sim_run_id, round_num)
    if not cs_rows:
        # Fall back to previous round if the target round isn't seeded yet.
        cs_rows = _load_country_states(client, sim_run_id, max(0, round_num - 1))

    # Merge base + snapshot into engine-shaped dicts keyed by country_code.
    all_countries: dict[str, dict] = {}
    for cc, base in base_countries.items():
        rs_row = cs_rows.get(cc, {})
        all_countries[cc] = _merge_to_engine_dict(base, rs_row)

    own_country = all_countries[country_code]
    own_eco = own_country["economic"]
    own_pol = own_country["political"]

    # Previous-round oil price (for "my oil revenue last round" calc).
    prev_round = max(0, round_num - 1)
    prev_oil_price = _load_oil_price(client, sim_run_id, prev_round)
    if prev_oil_price is None:
        # Try current round (e.g. round 0 case — no prior round).
        prev_oil_price = _load_oil_price(client, sim_run_id, round_num)
    if prev_oil_price is None:
        prev_oil_price = 80.0  # template default

    # Current oil price: same — prefer current round, else prev.
    current_oil_price = _load_oil_price(client, sim_run_id, round_num)
    if current_oil_price is None:
        current_oil_price = prev_oil_price

    # --- 1. economic_state -------------------------------------------------
    own_mbpd = float(own_eco.get("oil_production_mbpd", 0.0) or 0.0)
    total_world_mbpd = _compute_total_world_mbpd(all_countries)
    my_world_share = (
        (own_mbpd / total_world_mbpd * 100.0) if total_world_mbpd > 0 else 0.0
    )
    my_oil_revenue_last_round = 0.0
    if own_eco.get("oil_producer"):
        my_oil_revenue_last_round = prev_oil_price * own_mbpd * 0.009

    my_current_level = _read_opec_level(cs_rows, country_code)

    economic_state = {
        "gdp": round(float(own_eco.get("gdp", 0.0) or 0.0), 2),
        "treasury": round(float(own_eco.get("treasury", 0.0) or 0.0), 2),
        "inflation": round(float(own_eco.get("inflation", 0.0) or 0.0), 4),
        "stability": float(own_pol.get("stability", 5) or 5),
        "my_oil_production_mbpd": round(own_mbpd, 2),
        "my_world_oil_share_pct": round(my_world_share, 2),
        "my_oil_revenue_last_round": round(my_oil_revenue_last_round, 2),
        "my_current_production_level": my_current_level,
    }

    # --- 2. oil_market_state ----------------------------------------------
    opec_share_pct = _compute_opec_share_pct(all_countries, total_world_mbpd)
    oil_market_state = {
        "current_oil_price": round(float(current_oil_price), 2),
        "total_world_mbpd": round(total_world_mbpd, 2),
        "opec_share_pct": round(opec_share_pct, 2),
    }

    # --- 3. oil_price_history (rounds 0..round_num-1) ---------------------
    oil_price_history = _load_oil_price_history(client, sim_run_id, round_num)

    # --- 4. oil_producers_table -------------------------------------------
    oil_producers_table = _build_producers_table(
        all_countries, cs_rows, total_world_mbpd
    )

    # --- 5. chokepoint_blockades ------------------------------------------
    chokepoint_blockades = _load_chokepoint_blockades(client, sim_run_id)

    # --- 6. sanctions_on_producers ----------------------------------------
    sanctions_state = _load_sanctions_state(client, sim_run_id)
    sanctions_on_producers = _build_sanctions_on_producers(
        all_countries, sanctions_state
    )

    # --- 7. tariffs_on_producers ------------------------------------------
    tariffs_on_producers = _build_tariffs_on_producers(
        client, sim_run_id, all_countries
    )

    # --- 8. decision_rules + 9. instruction -------------------------------
    decision_rules = _decision_rules_text()

    instruction = (
        "Decide whether to CHANGE or NO_CHANGE. Rationale >= 30 chars "
        "required. Respond with JSON matching CONTRACT_OPEC §2."
    )

    return {
        "country_code": country_code,
        "round_num": round_num,
        "economic_state": economic_state,
        "oil_market_state": oil_market_state,
        "oil_price_history": oil_price_history,
        "oil_producers_table": oil_producers_table,
        "chokepoint_blockades": chokepoint_blockades,
        "sanctions_on_producers": sanctions_on_producers,
        "tariffs_on_producers": tariffs_on_producers,
        "decision_rules": decision_rules,
        "instruction": instruction,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------




def _get_sim_run_id() -> str:
    from engine.config.settings import Settings
    return Settings().default_sim_id


def _load_base_countries(client) -> dict[str, dict]:
    res = client.table("countries").select("*").execute()
    out: dict[str, dict] = {}
    for row in (res.data or []):
        cid = (row.get("sim_name", "") or "").lower().replace(" ", "")
        if cid:
            out[cid] = row
    return out


def _load_country_states(
    client, sim_run_id: str, round_num: int
) -> dict[str, dict]:
    """Return {country_code: country_states_per_round row} for the round."""
    out: dict[str, dict] = {}
    try:
        res = (
            client.table("country_states_per_round")
            .select("*")
            .eq("sim_run_id", sim_run_id)
            .eq("round_num", round_num)
            .execute()
        )
        for row in (res.data or []):
            cc = row.get("country_code", "")
            if cc:
                out[cc] = row
    except Exception as e:
        logger.debug("country_states_per_round lookup failed (R%d): %s", round_num, e)
    return out


def _load_oil_price(client, sim_run_id: str, round_num: int) -> float | None:
    try:
        res = (
            client.table("global_state_per_round")
            .select("oil_price")
            .eq("sim_run_id", sim_run_id)
            .eq("round_num", round_num)
            .limit(1)
            .execute()
        )
        if res.data:
            val = res.data[0].get("oil_price")
            if val is not None:
                return float(val)
    except Exception as e:
        logger.debug("global_state_per_round oil_price R%d lookup failed: %s",
                     round_num, e)
    return None


def _load_oil_price_history(
    client, sim_run_id: str, round_num: int
) -> list[dict]:
    """Return all oil prices for rounds [0, round_num - 1], ascending."""
    if round_num <= 0:
        return []
    try:
        res = (
            client.table("global_state_per_round")
            .select("round_num, oil_price")
            .eq("sim_run_id", sim_run_id)
            .lt("round_num", round_num)
            .gte("round_num", 0)
            .order("round_num", desc=False)
            .execute()
        )
        out: list[dict] = []
        for row in (res.data or []):
            price = row.get("oil_price")
            if price is None:
                continue
            out.append({
                "round": int(row["round_num"]),
                "oil_price": round(float(price), 2),
            })
        return out
    except Exception as e:
        logger.debug("oil_price_history lookup failed: %s", e)
        return []


def _compute_total_world_mbpd(all_countries: dict[str, dict]) -> float:
    total = 0.0
    for c in all_countries.values():
        eco = c.get("economic", {})
        if eco.get("oil_producer"):
            mbpd = float(eco.get("oil_production_mbpd", 0.0) or 0.0)
            if mbpd > 0:
                total += mbpd
    return total


def _compute_opec_share_pct(
    all_countries: dict[str, dict], total_world_mbpd: float
) -> float:
    if total_world_mbpd <= 0:
        return 0.0
    opec_mbpd = 0.0
    for cc, c in all_countries.items():
        if cc not in CANONICAL_OPEC_MEMBERS:
            continue
        eco = c.get("economic", {})
        if eco.get("oil_producer"):
            opec_mbpd += float(eco.get("oil_production_mbpd", 0.0) or 0.0)
    return opec_mbpd / total_world_mbpd * 100.0


def _read_opec_level(cs_rows: dict[str, dict], country_code: str) -> str:
    row = cs_rows.get(country_code, {})
    level = row.get("opec_production") or "na"
    return str(level)


def _build_producers_table(
    all_countries: dict[str, dict],
    cs_rows: dict[str, dict],
    total_world_mbpd: float,
) -> list[dict]:
    rows: list[dict] = []
    for cc, c in all_countries.items():
        eco = c.get("economic", {})
        if not eco.get("oil_producer"):
            continue
        mbpd = float(eco.get("oil_production_mbpd", 0.0) or 0.0)
        if mbpd <= 0:
            continue
        share_pct = (
            (mbpd / total_world_mbpd * 100.0) if total_world_mbpd > 0 else 0.0
        )
        level = _read_opec_level(cs_rows, cc)
        rows.append({
            "code": cc,
            "mbpd": round(mbpd, 2),
            "world_share_pct": round(share_pct, 2),
            "current_level": level,
        })
    rows.sort(key=lambda r: (-r["mbpd"], r["code"]))
    return rows


def _load_chokepoint_blockades(client, sim_run_id: str) -> dict[str, str]:
    """Return dict with gulf_gate / caribe_passage / formosa_strait status.

    Status values: 'none' | 'partial' | 'full'. Best-effort — if the
    blockades table is empty or inaccessible we report 'none'.
    """
    out = {
        "gulf_gate": "none",
        "caribe_passage": "none",
        "formosa_strait": "none",
    }

    # Map blockades.zone_id → context key.
    ZONE_MAP = {
        "cp_gulf_gate": "gulf_gate",
        "gulf_gate": "gulf_gate",
        "cp_caribe_passage": "caribe_passage",
        "caribe_passage": "caribe_passage",
        "caribbean": "caribe_passage",
        "cp_formosa_strait": "formosa_strait",
        "formosa_strait": "formosa_strait",
        "formosa": "formosa_strait",
    }

    try:
        res = (
            client.table("blockades")
            .select("zone_id, level, status")
            .eq("sim_run_id", sim_run_id)
            .eq("status", "active")
            .execute()
        )
        for row in (res.data or []):
            zone = (row.get("zone_id") or "").lower()
            key = ZONE_MAP.get(zone)
            if not key:
                continue
            level = (row.get("level") or "full").lower()
            if level not in ("none", "partial", "full"):
                level = "full"
            # Prefer the strongest level (full > partial > none)
            current = out[key]
            if current == "full":
                continue
            if level == "full" or (level == "partial" and current == "none"):
                out[key] = level
    except Exception as e:
        logger.debug("blockades lookup failed: %s", e)

    return out


def _load_sanctions_state(
    client, sim_run_id: str
) -> dict[str, dict[str, int]]:
    """Return {imposer: {target: level}}."""
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
            if imposer and target and level:
                out.setdefault(imposer, {})[target] = int(level)
    except Exception as e:
        logger.debug("sanctions lookup failed: %s", e)
    return out


def _build_sanctions_on_producers(
    all_countries: dict[str, dict],
    sanctions_state: dict[str, dict[str, int]],
) -> list[dict]:
    """One row per oil producer showing MAX sanctions level + num_sanctioners.

    ``triggers_supply_penalty`` is True when max_level >= 2 (engine's
    L2+ threshold that reduces that producer's output by 10% of share).
    """
    producers = [
        cc for cc, c in all_countries.items()
        if c.get("economic", {}).get("oil_producer")
        and float(c.get("economic", {}).get("oil_production_mbpd", 0) or 0) > 0
    ]
    producers.sort()

    rows: list[dict] = []
    for prod in producers:
        max_level = 0
        num_sanctioners = 0
        for imposer, targets in sanctions_state.items():
            lvl = targets.get(prod, 0)
            if lvl > 0:
                num_sanctioners += 1
                if lvl > max_level:
                    max_level = lvl
        rows.append({
            "code": prod,
            "max_level": int(max_level),
            "num_sanctioners": int(num_sanctioners),
            "triggers_supply_penalty": max_level >= 2,
        })
    return rows


def _build_tariffs_on_producers(
    client, sim_run_id: str, all_countries: dict[str, dict]
) -> list[dict]:
    producers = {
        cc for cc, c in all_countries.items()
        if c.get("economic", {}).get("oil_producer")
        and float(c.get("economic", {}).get("oil_production_mbpd", 0) or 0) > 0
    }
    out: list[dict] = []
    try:
        res = (
            client.table("tariffs")
            .select("imposer_country_id, target_country_id, level")
            .eq("sim_run_id", sim_run_id)
            .execute()
        )
        for row in (res.data or []):
            imposer = row.get("imposer_country_id", "")
            target = row.get("target_country_id", "")
            level = row.get("level", 0)
            if not imposer or not target:
                continue
            if not level:
                continue
            if imposer not in producers and target not in producers:
                continue
            out.append({
                "imposer": imposer,
                "target": target,
                "level": int(level),
            })
    except Exception as e:
        logger.debug("tariffs lookup failed: %s", e)

    out.sort(key=lambda r: (-r["level"], r["imposer"], r["target"]))
    return out


def _decision_rules_text() -> str:
    return """HOW OPEC+ WORKS
- 5 canonical members (caribe, mirage, persia, sarmatia, solaria)
  collectively control a majority of world oil production.
- Each member picks ONE level per round: min / low / normal / high / max.
- Engine applies 2x cartel leverage on top of each member's share of world
  oil — OPEC+ decisions move markets beyond their raw supply share.
- Effect is on the world oil price, which cascades into every country's
  GDP, oil revenue, inflation pressure. Cuts (min/low) push price UP;
  floods (high/max) push price DOWN.

YOUR AUTHORITY
- Only OPEC+ members can submit set_opec (you are one of the 5).
- Your decision affects every oil-importing and oil-exporting country.
- Non-OPEC members are rejected with NOT_OPEC_MEMBER at the validator.

DECISION RULES
- decision="change"    -> MUST include changes.production_level with one of
                          min / low / normal / high / max
- decision="no_change" -> MUST OMIT the changes field entirely
- rationale >=30 chars REQUIRED in both cases

REMINDER -- no_change is a legitimate choice
Market churn is expensive and signals weakness. If current level still
serves your goals, no_change with a clear rationale is the correct answer.
Do not churn OPEC posture for the sake of action."""
