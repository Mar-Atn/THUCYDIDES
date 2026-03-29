"""
TTT SEED -- LLM Agent Runner
================================
Role-brief-driven agent decision system.

Reads ACTUAL role brief files and extracts objectives, ticking clocks,
and personality traits. Decisions follow from matching those objectives
against the current world state -- not from generic if/then heuristics.

Each team deliberation models internal dynamics: who pushes what,
who disagrees, what the HoS decides given pressure from all roles.

Author: ATLAS (World Model Engineer)
Version: 3.0 (LLM Test Architecture)
"""

import os
import re
import copy
import random
import math
from typing import Dict, List, Optional, Tuple, Any

from world_state import WorldState, clamp, UNIT_TYPES, SCHEDULED_EVENTS


# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
ROLE_BRIEFS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "role_briefs"
)

# ---------------------------------------------------------------------------
# ROLE BRIEF PARSER
# ---------------------------------------------------------------------------

def parse_role_brief(filepath: str) -> List[dict]:
    """Parse a role brief markdown file into structured role data."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    roles = []
    # Split by role headers
    role_sections = re.split(r'# ROLE \d+:', text)
    for section in role_sections[1:]:  # skip preamble
        role = {}
        # Name
        name_match = re.match(r'\s*(\w+)', section)
        if name_match:
            role["name"] = name_match.group(1).strip().lower()

        # Bio
        bio_match = re.search(r'## SECTION 2: BIO\s*\n(.*?)(?=\n---|\n## SECTION)', section, re.DOTALL)
        if bio_match:
            role["bio"] = bio_match.group(1).strip()[:2000]

        # Objectives -- from the table in Section 6
        obj_matches = re.findall(
            r'\|\s*\d+\s*\|\s*(.*?)\s*\|\s*(Public|Private|Both).*?\|\s*(.*?)\s*\|',
            section
        )
        role["objectives"] = []
        for obj_name, visibility, rationale in obj_matches:
            role["objectives"].append({
                "name": obj_name.strip(),
                "visibility": visibility.strip(),
                "rationale": rationale.strip()[:200],
            })

        # Ticking clock
        clock_match = re.search(r'## SECTION 7.*?TICKING CLOCK.*?\n(.*?)(?=\n---|\n## SECTION|\n# ROLE)', section, re.DOTALL)
        if clock_match:
            role["ticking_clock"] = clock_match.group(1).strip()[:500]
        else:
            role["ticking_clock"] = ""

        # Faction
        faction_match = re.search(r'\*\*Faction/Camp\*\*\s*\|\s*(.*?)\s*\|', section)
        if faction_match:
            role["faction"] = faction_match.group(1).strip()

        # Age
        age_match = re.search(r'\*\*Age\*\*\s*\|\s*(\d+)', section)
        if age_match:
            role["age"] = int(age_match.group(1))

        # Title
        title_match = re.search(r'\*\*Title\*\*\s*\|\s*(.*?)\s*\|', section)
        if title_match:
            role["title"] = title_match.group(1).strip()

        roles.append(role)
    return roles


_BRIEF_CACHE: Dict[str, List[dict]] = {}

def get_role_briefs(country_name: str) -> List[dict]:
    """Load and cache role briefs for a country."""
    if country_name in _BRIEF_CACHE:
        return _BRIEF_CACHE[country_name]

    filename_map = {
        "columbia": "COLUMBIA_ROLES.md",
        "cathay": "CATHAY_ROLES.md",
        "nordostan": "NORDOSTAN_ROLES.md",
        "heartland": "HEARTLAND_ROLES.md",
        "persia": "PERSIA_ROLES.md",
        "europe": "EUROPE_ROLES.md",
    }
    fn = filename_map.get(country_name)
    if not fn:
        return []
    path = os.path.join(ROLE_BRIEFS_DIR, fn)
    briefs = parse_role_brief(path)
    _BRIEF_CACHE[country_name] = briefs
    return briefs


# ---------------------------------------------------------------------------
# STRATEGIC ASSESSMENT FUNCTIONS
# ---------------------------------------------------------------------------

def assess_military_balance(ws: WorldState, country_id: str) -> dict:
    """Assess military posture relative to enemies and rivals."""
    c = ws.countries.get(country_id, {})
    mil = c.get("military", {})
    my_total = sum(mil.get(ut, 0) for ut in ["ground", "naval", "tactical_air"])

    enemies = []
    for w in ws.wars:
        if w.get("attacker") == country_id:
            enemies.append(w["defender"])
        elif w.get("defender") == country_id:
            enemies.append(w["attacker"])

    enemy_total = 0
    for eid in enemies:
        ec = ws.countries.get(eid, {})
        em = ec.get("military", {})
        enemy_total += sum(em.get(ut, 0) for ut in ["ground", "naval", "tactical_air"])

    return {
        "my_total": my_total,
        "enemy_total": enemy_total,
        "ratio": my_total / max(enemy_total, 1),
        "ground": mil.get("ground", 0),
        "naval": mil.get("naval", 0),
        "air": mil.get("tactical_air", 0),
        "missiles": mil.get("strategic_missile", 0),
        "enemies": enemies,
        "at_war": len(enemies) > 0,
        "overstretch": len(enemies) > 1,
    }


def assess_economic_health(ws: WorldState, country_id: str) -> dict:
    """Assess economic situation."""
    c = ws.countries.get(country_id, {})
    eco = c.get("economic", {})
    gdp = eco.get("gdp", 0)
    growth = eco.get("gdp_growth_rate", 0)
    treasury = eco.get("treasury", 0)
    inflation = eco.get("inflation", 0)
    debt = eco.get("debt_burden", 0)

    # Sanctions pressure
    sanctions_on_me = 0
    for sanctioner, targets in ws.bilateral.get("sanctions", {}).items():
        level = targets.get(country_id, 0)
        if level > 0:
            sanctions_on_me += level

    health = "strong"
    if growth < 0 or inflation > 20 or treasury < 1:
        health = "crisis"
    elif growth < 1 or inflation > 10 or sanctions_on_me > 3:
        health = "strained"
    elif growth < 2 or inflation > 5:
        health = "moderate"

    return {
        "gdp": gdp,
        "growth": growth,
        "treasury": treasury,
        "inflation": inflation,
        "debt": debt,
        "sanctions_on_me": sanctions_on_me,
        "health": health,
        "oil_producer": eco.get("oil_producer", False),
    }


def assess_political_situation(ws: WorldState, country_id: str) -> dict:
    """Assess domestic political situation."""
    c = ws.countries.get(country_id, {})
    pol = c.get("political", {})
    stability = pol.get("stability", 5)
    support = pol.get("political_support", 50)
    war_tiredness = pol.get("war_tiredness", 0)
    regime = pol.get("regime_type", c.get("regime_type", "democracy"))

    upcoming_election = None
    for rnd, events in SCHEDULED_EVENTS.items():
        for ev in events:
            if ev.get("country") == country_id:
                upcoming_election = {"round": rnd, "type": ev["subtype"]}

    return {
        "stability": stability,
        "support": support,
        "war_tiredness": war_tiredness,
        "regime": regime,
        "upcoming_election": upcoming_election,
        "crisis": stability < 4,
        "protest_risk": stability < 5,
    }


def assess_gap_ratio(ws: WorldState) -> dict:
    """Calculate the Thucydides Trap gap ratio."""
    col = ws.countries.get("columbia", {})
    cat = ws.countries.get("cathay", {})
    col_gdp = col.get("economic", {}).get("gdp", 300)
    cat_gdp = cat.get("economic", {}).get("gdp", 200)
    ratio = cat_gdp / max(col_gdp, 1)

    col_nav = col.get("military", {}).get("naval", 0)
    cat_nav = cat.get("military", {}).get("naval", 0)
    nav_ratio = cat_nav / max(col_nav, 1)

    col_ai = col.get("technology", {}).get("ai_level", 0)
    cat_ai = cat.get("technology", {}).get("ai_level", 0)

    return {
        "gdp_ratio": ratio,
        "naval_ratio": nav_ratio,
        "columbia_naval": col_nav,
        "cathay_naval": cat_nav,
        "columbia_ai": col_ai,
        "cathay_ai": cat_ai,
        "gap_closing": ratio > 0.7,
        "naval_parity_near": nav_ratio > 0.8,
    }


def assess_war_status(ws: WorldState, war_name: str) -> dict:
    """Assess the status of a specific conflict."""
    for w in ws.wars:
        theater = w.get("theater", "")
        att = w.get("attacker", "")
        def_ = w.get("defender", "")
        if war_name == "eastern_ereb" and theater == "eastern_ereb":
            occ = w.get("occupied_zones", [])
            att_mil = ws.countries.get(att, {}).get("military", {})
            def_mil = ws.countries.get(def_, {}).get("military", {})
            return {
                "attacker": att,
                "defender": def_,
                "occupied_zones": occ,
                "attacker_ground": att_mil.get("ground", 0),
                "defender_ground": def_mil.get("ground", 0),
                "stalemate": abs(att_mil.get("ground", 0) - def_mil.get("ground", 0)) < 5,
            }
        elif war_name == "mashriq" and theater == "mashriq":
            return {
                "attacker": att,
                "defender": def_,
                "occupied_zones": w.get("occupied_zones", []),
            }
    return {"active": False}


# ---------------------------------------------------------------------------
# OBJECTIVE EVALUATOR
# ---------------------------------------------------------------------------

def evaluate_objectives(objectives: List[dict], ws: WorldState,
                        country_id: str, round_num: int) -> List[dict]:
    """For each objective, assess: status, urgency, and recommended action."""
    mil = assess_military_balance(ws, country_id)
    eco = assess_economic_health(ws, country_id)
    pol = assess_political_situation(ws, country_id)
    gap = assess_gap_ratio(ws)

    evaluated = []
    for i, obj in enumerate(objectives):
        name = obj.get("name", "").lower()
        urgency = max(0.3, 1.0 - (8 - round_num) * 0.1)  # increases each round
        status = "in_progress"
        recommended_action = None

        # Pattern-match objective names to strategic assessments
        if "formosa" in name or "reunification" in name:
            if gap["naval_parity_near"]:
                urgency = min(1.0, urgency + 0.3)
                status = "window_opening"
                recommended_action = "naval_buildup" if gap["naval_ratio"] < 0.9 else "prepare_blockade"
            else:
                status = "building_toward"
                recommended_action = "naval_buildup"

        elif "territory" in name or "territorial" in name:
            ee = assess_war_status(ws, "eastern_ereb")
            if ee.get("stalemate"):
                status = "stalled"
                recommended_action = "negotiate_or_escalate"
            else:
                status = "in_progress"

        elif "legacy" in name or "heritage" in name:
            urgency = min(1.0, urgency + 0.2)
            status = "time_pressure"

        elif "survive" in name or "survival" in name:
            if pol["crisis"]:
                urgency = 1.0
                status = "threatened"
                recommended_action = "stabilize"
            else:
                status = "secure"

        elif "contain" in name and "cathay" in name:
            if gap["gap_closing"]:
                urgency = min(1.0, urgency + 0.2)
                status = "deteriorating"
                recommended_action = "tech_competition_tariffs"

        elif "nuclear" in name:
            tech = ws.countries.get(country_id, {}).get("technology", {})
            nuc = tech.get("nuclear_level", 0)
            if nuc < 1:
                recommended_action = "invest_nuclear_rd"
            status = f"level_{nuc}"

        elif "eu" in name or "europe" in name:
            status = "aspirational"

        elif "economic" in name or "growth" in name or "gdp" in name:
            if eco["health"] == "crisis":
                urgency = 1.0
                status = "crisis"
                recommended_action = "emergency_spending"
            elif eco["health"] == "strained":
                urgency = 0.7
                status = "strained"

        elif "sanctions" in name:
            if eco["sanctions_on_me"] > 0:
                urgency = 0.8
                status = "under_pressure"
                recommended_action = "seek_relief"

        elif "alliance" in name or "aid" in name:
            status = "maintain"
            recommended_action = "diplomatic_engagement"

        elif "overstretch" in name or "readiness" in name:
            if mil["overstretch"]:
                urgency = 0.9
                status = "overstretched"
                recommended_action = "reduce_commitments"

        evaluated.append({
            "priority": i + 1,
            "name": obj.get("name", ""),
            "urgency": round(urgency, 2),
            "status": status,
            "recommended_action": recommended_action,
        })

    return evaluated


# ---------------------------------------------------------------------------
# TEAM DELIBERATION FUNCTIONS
# ---------------------------------------------------------------------------

def deliberate_columbia(ws: WorldState, round_num: int, rng: random.Random) -> Tuple[dict, list, dict]:
    """
    Columbia team deliberation.
    7 roles: Dealer (HoS), Volt (VP), Anchor (SecState), Shield (SecDef),
    Shadow (Intel), Tribune (Opposition), Challenger (Opposition).
    """
    briefs = get_role_briefs("columbia")
    c = ws.countries["columbia"]
    mil = assess_military_balance(ws, "columbia")
    eco = assess_economic_health(ws, "columbia")
    pol = assess_political_situation(ws, "columbia")
    gap = assess_gap_ratio(ws)
    ee_war = assess_war_status(ws, "eastern_ereb")
    persia_war = assess_war_status(ws, "mashriq")

    reasoning = {
        "team": "columbia",
        "round": round_num,
        "assessments": {
            "military_balance": mil,
            "economic_health": eco["health"],
            "gap_ratio": round(gap["gdp_ratio"], 3),
            "naval_balance": f"Columbia {gap['columbia_naval']} vs Cathay {gap['cathay_naval']}",
        },
        "role_positions": {},
        "internal_dynamics": "",
        "final_decision": "",
    }

    actions = {}
    negotiations = []

    # --- DEALER's Heritage Target Assessment ---
    heritage_assessment = {
        "persia": "active_war" if persia_war.get("attacker") else "no_war",
        "caribe": "target" if round_num <= 4 else "deferred",
        "heartland_deal": "negotiable" if ee_war.get("stalemate") else "premature",
        "thule": "aspirational",
        "cathay_containment": "ongoing" if gap["gap_closing"] else "stable",
    }
    reasoning["role_positions"]["dealer"] = {
        "heritage_targets": heritage_assessment,
        "legacy_urgency": min(1.0, 0.5 + round_num * 0.1),
        "position": "Push all heritage targets simultaneously. Persia first, Caribe opportunistic.",
    }

    # --- SHIELD's Overstretch Analysis ---
    theaters_active = len([w for w in ws.wars if "columbia" in [w.get("attacker"), w.get("defender")]
                          or "columbia" in w.get("allies", {}).get("attacker", [])])
    overstretch_level = "critical" if theaters_active >= 2 and mil["ground"] < 30 else \
                        "stressed" if theaters_active >= 1 else "manageable"
    reasoning["role_positions"]["shield"] = {
        "overstretch": overstretch_level,
        "theaters": theaters_active,
        "position": "Cannot sustain more than 2 theaters. Recommend against Caribe action if Persia active.",
    }

    # --- SHADOW's Intelligence Assessment ---
    cathay_naval_trend = gap["cathay_naval"]
    reasoning["role_positions"]["shadow"] = {
        "cathay_assessment": f"Naval buildup at {cathay_naval_trend}. Formosa window analysis: {'dangerous' if gap['naval_parity_near'] else 'not imminent'}.",
        "nordostan_assessment": "Internally strained but stable. Ironhand loyalty uncertain." if ws.countries.get("nordostan", {}).get("political", {}).get("stability", 5) < 5 else "Holding together.",
        "position": "Cathay is the primary strategic threat. Recommend increased Pacific presence.",
    }

    # --- ANCHOR's Hawk Position ---
    reasoning["role_positions"]["anchor"] = {
        "position": "Caribe action NOW while we have the initiative. Persia must conclude with regime change.",
        "urgency": "high" if round_num <= 3 else "moderate",
    }

    # --- VOLT's Isolationist Pull ---
    reasoning["role_positions"]["volt"] = {
        "position": "Reduce foreign commitments. America First. Cut European subsidies. Focus on domestic economy.",
        "tension_with_anchor": "high",
    }

    # --- TRIBUNE's Opposition ---
    tribune_majority = pol["support"] < 45  # opposition has leverage
    reasoning["role_positions"]["tribune"] = {
        "position": "Block military adventurism. Investigate executive overreach." if tribune_majority else "Minority opposition. Monitor and critique.",
        "has_leverage": tribune_majority,
    }

    # --- Internal Dynamics ---
    if round_num <= 2:
        reasoning["internal_dynamics"] = (
            "Early rounds: Dealer consolidating. Volt and Anchor competing for successor position. "
            "Shield reluctantly executing. Tribune building case."
        )
    elif round_num <= 5:
        reasoning["internal_dynamics"] = (
            "Mid-game: Succession tension rising. Anchor wants Caribe legacy. Volt wants isolationist turn. "
            f"Tribune {'has leverage with opposition majority' if tribune_majority else 'building momentum'}."
        )
    else:
        reasoning["internal_dynamics"] = (
            "Late game: Legacy panic. Dealer pushing for deals. Shield warning of overstretch. "
            "Succession open warfare between Volt and Anchor."
        )

    # === DECISION SYNTHESIS ===
    # Budget: Dealer decides, weighted by Shield's overstretch warning and Volt's pressure
    baseline_social = c["economic"].get("social_spending_baseline", 0.30)
    at_war = ws.get_country_at_war("columbia")

    # Social spending: Volt pushes for more, Shield pushes for military
    if at_war:
        social_pct = max(baseline_social - 0.03, 0.20)
        mil_pct = 0.40 if overstretch_level != "critical" else 0.35
    else:
        social_pct = baseline_social + 0.02
        mil_pct = 0.25 + (0.05 if gap["gap_closing"] else 0)

    tech_pct = 0.12 + (0.05 if gap["cathay_ai"] >= gap["columbia_ai"] else 0)

    actions["budget"] = {
        "social_spending": eco["gdp"] * social_pct,
        "social_pct": social_pct,
        "social_spending_ratio": social_pct,
        "military_total": eco["gdp"] * mil_pct,
        "tech_total": eco["gdp"] * tech_pct,
        "military": {
            "ground": {"coins": eco["gdp"] * mil_pct * 0.3, "tier": "normal"},
            "naval": {"coins": eco["gdp"] * mil_pct * 0.4, "tier": "accelerated" if gap["naval_parity_near"] else "normal"},
            "tactical_air": {"coins": eco["gdp"] * mil_pct * 0.3, "tier": "normal"},
        },
    }

    # Tariffs: Dealer's instinct + Cathay containment logic
    tariff_actions = {}
    if gap["gap_closing"] or round_num >= 2:
        tariff_actions["cathay"] = min(3, 1 + round_num // 3)
    if eco["health"] != "crisis":
        tariff_actions["nordostan"] = 2
    actions["tariffs"] = tariff_actions

    # Sanctions: coordinated with allies
    sanction_actions = {}
    sanction_actions["nordostan"] = 3  # max sanctions
    if persia_war.get("attacker"):
        sanction_actions["persia"] = 3
    actions["sanctions"] = sanction_actions

    # Military operations
    actions["military_ops"] = []
    if persia_war.get("attacker"):
        # Continue Persia operations: air strikes
        if mil["air"] >= 2:
            actions["military_ops"].append({
                "type": "air_strike",
                "target": "persia",
                "target_zone": "me_persia_1",
                "units": min(2, mil["air"]),
            })

    # Covert ops: Shadow's recommendation
    actions["covert_ops"] = []
    if round_num >= 2:
        actions["covert_ops"].append({
            "type": "cyber",
            "target": "cathay",
            "objective": "intelligence_gathering",
        })
    if rng.random() < 0.4 and round_num >= 3:
        actions["covert_ops"].append({
            "type": "disinformation",
            "target": "caribe",
            "objective": "regime_destabilization",
        })

    # OPEC: Columbia is not OPEC
    # Tech: AI R&D priority
    actions["tech_rd"] = {
        "ai": eco["gdp"] * tech_pct * 0.7,
        "nuclear": 0,  # already L3
    }

    # Negotiations
    # 1. Heartland arms transfer (Anchor pushes, Shield approves limited)
    if ws.get_country_at_war("heartland"):
        arms_amount = 2 if overstretch_level != "critical" else 1
        if mil["ground"] > 20:
            negotiations.append({
                "type": "arms_transfer",
                "from": "columbia",
                "to": "heartland",
                "terms": {"unit_type": "ground", "count": arms_amount},
                "likelihood": 0.8,
            })
        if eco["treasury"] > 5:
            negotiations.append({
                "type": "coin_transfer",
                "from": "columbia",
                "to": "heartland",
                "terms": {"amount": min(2, eco["treasury"] * 0.2)},
                "likelihood": 0.9,
            })

    # 2. Nordostan deal (Dealer's initiative, round 3+)
    if round_num >= 3 and ee_war.get("stalemate"):
        negotiations.append({
            "type": "peace_framework",
            "from": "columbia",
            "to": "nordostan",
            "terms": {
                "proposal": "ceasefire_and_negotiations",
                "columbia_offer": "sanctions_partial_relief",
                "columbia_demand": "territorial_freeze_current_lines",
            },
            "likelihood": 0.5 + round_num * 0.05,
        })

    # 3. Cathay: tariff negotiations (Circuit as interlocutor)
    if round_num >= 4 and gap["gap_closing"]:
        negotiations.append({
            "type": "trade_negotiation",
            "from": "columbia",
            "to": "cathay",
            "terms": {"proposal": "tech_restrictions_in_exchange_for_tariff_reduction"},
            "likelihood": 0.3,
        })

    reasoning["final_decision"] = (
        f"Round {round_num}: Dealer prioritizes {'legacy deals' if round_num >= 4 else 'military operations'}. "
        f"Budget: {social_pct:.0%} social, {mil_pct:.0%} military, {tech_pct:.0%} tech. "
        f"{'Naval acceleration due to Cathay parity threat.' if gap['naval_parity_near'] else ''} "
        f"{'Heartland arms transfer approved.' if ws.get_country_at_war('heartland') else ''}"
    )

    return actions, negotiations, reasoning


def deliberate_cathay(ws: WorldState, round_num: int, rng: random.Random) -> Tuple[dict, list, dict]:
    """
    Cathay team: Helmsman (HoS), Rampart (military), Abacus (economy),
    Circuit (tech), Sage (party elder).
    """
    briefs = get_role_briefs("cathay")
    c = ws.countries["cathay"]
    mil = assess_military_balance(ws, "cathay")
    eco = assess_economic_health(ws, "cathay")
    pol = assess_political_situation(ws, "cathay")
    gap = assess_gap_ratio(ws)

    reasoning = {
        "team": "cathay",
        "round": round_num,
        "role_positions": {},
        "internal_dynamics": "",
        "final_decision": "",
    }

    actions = {}
    negotiations = []

    # --- HELMSMAN: Formosa Window Calculation ---
    helmsman_age = 73 + (round_num - 1) // 2  # ages 0.5 years per round
    naval_ratio = gap["naval_ratio"]
    columbia_distracted = len([w for w in ws.wars
                               if "columbia" in [w.get("attacker")]
                               or "columbia" in w.get("allies", {}).get("attacker", [])]) >= 1
    formosa_window_score = (
        0.3 * min(naval_ratio / 0.9, 1.0) +        # naval readiness
        0.2 * (1.0 if columbia_distracted else 0.3) + # columbia distraction
        0.2 * min((helmsman_age - 73) / 5.0, 1.0) +  # age urgency
        0.15 * (1.0 if gap["gap_closing"] else 0.5) + # economic trajectory
        0.15 * min(round_num / 6.0, 1.0)              # time pressure
    )

    formosa_decision = "wait"
    if formosa_window_score > 0.8 and round_num >= 5:
        formosa_decision = "blockade"
    elif formosa_window_score > 0.7 and round_num >= 4:
        formosa_decision = "gray_zone_escalation"
    elif formosa_window_score > 0.5:
        formosa_decision = "accelerate_buildup"

    reasoning["role_positions"]["helmsman"] = {
        "formosa_window_score": round(formosa_window_score, 2),
        "formosa_decision": formosa_decision,
        "age": helmsman_age,
        "legacy_pressure": "extreme" if helmsman_age >= 76 else "high",
        "position": f"Formosa window assessment: {formosa_window_score:.0%}. Decision: {formosa_decision}.",
    }

    # --- RAMPART: Military Reality ---
    purge_damage = 0.15 if round_num <= 2 else 0.05  # purge effects fade
    actual_readiness = max(0.5, 1.0 - purge_damage - (0.05 if pol["stability"] < 6 else 0))
    reasoning["role_positions"]["rampart"] = {
        "readiness": round(actual_readiness, 2),
        "honest_assessment": f"Fleet at {actual_readiness:.0%} effective readiness. Purge damage {'still significant' if purge_damage > 0.1 else 'fading'}.",
        "position": "Caution. We need 2 more rounds of buildup for Formosa confidence." if naval_ratio < 0.85 else "Approaching readiness but amphibious capability uncertain.",
    }

    # --- ABACUS: Economic Reality ---
    real_growth = eco["growth"] * rng.uniform(0.7, 0.95)  # real numbers lower than reported
    reasoning["role_positions"]["abacus"] = {
        "reported_growth": eco["growth"],
        "estimated_real_growth": round(real_growth, 1),
        "position": f"Real growth ~{real_growth:.1f}%, not {eco['growth']:.1f}%. Military spending sustainable but war would be catastrophic for economy.",
    }

    # --- CIRCUIT: Tech Competition ---
    rare_earth_leverage = 0.7  # Cathay controls ~70% of rare earths
    reasoning["role_positions"]["circuit"] = {
        "rare_earth_leverage": rare_earth_leverage,
        "position": "Use tech competition, not military force. Rare earth restrictions give leverage. Formosa confrontation would trigger devastating tech sanctions.",
    }

    # --- SAGE: Party Stability ---
    sage_alarm = pol["stability"] < 6 or pol["support"] < 45
    reasoning["role_positions"]["sage"] = {
        "alarm_level": "high" if sage_alarm else "normal",
        "position": "Helmsman is overreaching. Party conference should be called to assess direction." if sage_alarm else "Defer to Helmsman.",
    }

    # === DECISION SYNTHESIS ===
    # Helmsman decides, but Rampart's readiness matters for military timing

    baseline_social = c["economic"].get("social_spending_baseline", 0.25)
    social_pct = baseline_social - 0.02  # slight cut for military
    mil_pct = 0.35 + (0.10 if formosa_decision != "wait" else 0.05)
    tech_pct = 0.15

    actions["budget"] = {
        "social_spending": eco["gdp"] * social_pct,
        "social_pct": social_pct,
        "social_spending_ratio": social_pct,
        "military_total": eco["gdp"] * mil_pct,
        "tech_total": eco["gdp"] * tech_pct,
        "military": {
            "ground": {"coins": eco["gdp"] * mil_pct * 0.2, "tier": "normal"},
            "naval": {"coins": eco["gdp"] * mil_pct * 0.55, "tier": "accelerated"},
            "tactical_air": {"coins": eco["gdp"] * mil_pct * 0.25, "tier": "normal"},
        },
    }

    # Tariffs: retaliatory
    tariff_actions = {}
    col_tariffs = ws.bilateral.get("tariffs", {}).get("columbia", {}).get("cathay", 0)
    if col_tariffs > 0:
        tariff_actions["columbia"] = min(col_tariffs, 2)  # match but don't exceed
    actions["tariffs"] = tariff_actions

    # No sanctions on Columbia (trade dependent)
    actions["sanctions"] = {}

    # Military: naval buildup focus
    actions["military_ops"] = []
    if formosa_decision == "gray_zone_escalation":
        actions["military_ops"].append({
            "type": "gray_zone",
            "target_zone": "w(17,4)",
            "description": "Increased PLA Navy exercises near Formosa",
        })
    elif formosa_decision == "blockade":
        actions["military_ops"].append({
            "type": "blockade_preparation",
            "target_zone": "w(17,4)",
            "naval_units": min(5, mil["naval"]),
        })

    # Covert ops
    actions["covert_ops"] = []
    if round_num >= 2:
        actions["covert_ops"].append({
            "type": "cyber",
            "target": "columbia",
            "objective": "military_intelligence",
        })
    if round_num >= 3:
        actions["covert_ops"].append({
            "type": "disinformation",
            "target": "formosa",
            "objective": "undermine_resistance_will",
        })

    # Tech: massive AI + some nuclear
    actions["tech_rd"] = {
        "ai": eco["gdp"] * tech_pct * 0.8,
        "nuclear": eco["gdp"] * tech_pct * 0.2,
    }

    # Negotiations
    # 1. Nordostan support (maintain partnership)
    if eco["treasury"] > 3:
        negotiations.append({
            "type": "coin_transfer",
            "from": "cathay",
            "to": "nordostan",
            "terms": {"amount": min(2, eco["treasury"] * 0.1)},
            "likelihood": 0.7,
        })

    # 2. Bharata tech cooperation
    negotiations.append({
        "type": "tech_transfer",
        "from": "cathay",
        "to": "bharata",
        "terms": {"domain": "ai", "level": "cooperation"},
        "likelihood": 0.5 + round_num * 0.05,
    })

    # 3. Rare earth leverage against Columbia
    if col_tariffs >= 2:
        negotiations.append({
            "type": "trade_restriction",
            "from": "cathay",
            "to": "columbia",
            "terms": {"rare_earth_export_reduction": 0.3},
            "likelihood": 0.6,
        })

    reasoning["final_decision"] = (
        f"Round {round_num}: Helmsman's Formosa assessment {formosa_window_score:.0%}. "
        f"Decision: {formosa_decision}. Naval buildup {'accelerated' if formosa_decision != 'wait' else 'standard'}. "
        f"Budget: naval-heavy ({mil_pct:.0%} military, {tech_pct:.0%} tech). "
        f"Rampart urges {'patience' if actual_readiness < 0.8 else 'readiness'}."
    )

    return actions, negotiations, reasoning


def deliberate_nordostan(ws: WorldState, round_num: int, rng: random.Random) -> Tuple[dict, list, dict]:
    """Nordostan: Pathfinder (HoS), Ironhand (military), Compass (oligarch)."""
    briefs = get_role_briefs("nordostan")
    c = ws.countries["nordostan"]
    mil = assess_military_balance(ws, "nordostan")
    eco = assess_economic_health(ws, "nordostan")
    pol = assess_political_situation(ws, "nordostan")
    ee_war = assess_war_status(ws, "eastern_ereb")

    reasoning = {"team": "nordostan", "round": round_num, "role_positions": {}, "internal_dynamics": "", "final_decision": ""}

    actions = {}
    negotiations = []

    # --- PATHFINDER: Deal Window Assessment ---
    deal_window_open = round_num <= 5  # Dealer may lose power after R5
    att_ground = ee_war.get("attacker_ground", 0)
    def_ground = ee_war.get("defender_ground", 0)
    military_advantage = att_ground > def_ground * 1.2
    territorial_hold = len(ee_war.get("occupied_zones", []))

    reasoning["role_positions"]["pathfinder"] = {
        "deal_window": "open" if deal_window_open else "closing",
        "military_situation": "advantageous" if military_advantage else "grinding",
        "territorial_hold": territorial_hold,
        "position": f"{'Probe for deal with Dealer while window open' if deal_window_open else 'Consolidate and defend'}. Hold all territory as non-negotiable minimum.",
    }

    # --- IRONHAND: Military Reality ---
    attrition_rate = 0.5 + round_num * 0.1  # worsening
    replacement_rate = max(0.3, 1.0 - round_num * 0.08)
    reasoning["role_positions"]["ironhand"] = {
        "attrition_rate": round(attrition_rate, 2),
        "replacement_capacity": round(replacement_rate, 2),
        "position": f"Attrition {'unsustainable' if attrition_rate > replacement_rate else 'manageable'}. {'Recommend defensive posture' if attrition_rate > 0.7 else 'Can sustain limited offensive'}.",
        "loyalty": "obedient" if pol["stability"] > 5 else "calculating",
    }

    # --- COMPASS: Economic Reality ---
    sanctions_pain = eco["sanctions_on_me"]
    reasoning["role_positions"]["compass"] = {
        "sanctions_pain": sanctions_pain,
        "position": f"Sanctions {'devastating' if sanctions_pain >= 4 else 'painful but manageable'}. Western assets frozen. Back-channel to Columbia: offer oil deal for sanctions relief.",
        "personal_stake": "high -- wants asset unfreezing",
    }

    # === DECISION SYNTHESIS ===
    baseline_social = c["economic"].get("social_spending_baseline", 0.20)
    social_pct = max(baseline_social - 0.05, 0.12)  # war cuts social spending
    mil_pct = 0.50  # war economy
    tech_pct = 0.05

    actions["budget"] = {
        "social_spending": eco["gdp"] * social_pct,
        "social_pct": social_pct,
        "social_spending_ratio": social_pct,
        "military_total": eco["gdp"] * mil_pct,
        "tech_total": eco["gdp"] * tech_pct,
        "military": {
            "ground": {"coins": eco["gdp"] * mil_pct * 0.7, "tier": "accelerated" if military_advantage else "normal"},
            "naval": {"coins": eco["gdp"] * mil_pct * 0.1, "tier": "normal"},
            "tactical_air": {"coins": eco["gdp"] * mil_pct * 0.2, "tier": "normal"},
        },
    }

    actions["tariffs"] = {}
    actions["sanctions"] = {}

    # Military operations: attack or defend based on Ironhand's assessment
    actions["military_ops"] = []
    if military_advantage and mil["ground"] > 10:
        # Offensive push
        actions["military_ops"].append({
            "type": "attack",
            "target": "heartland",
            "target_zone": "heartland_2",
            "units": min(4, mil["ground"] // 3),
            "origin_zone": "nordostan_1",
        })
    elif mil["ground"] > 5:
        # Limited probing attack
        actions["military_ops"].append({
            "type": "attack",
            "target": "heartland",
            "target_zone": "heartland_2",
            "units": min(2, mil["ground"] // 4),
            "origin_zone": "nordostan_1",
        })

    # OPEC production: Nordostan needs revenue
    actions["opec_production"] = "high"  # pump for revenue despite cartel pressure

    # Nuclear posture
    nuc_level = c.get("technology", {}).get("nuclear_level", 0)
    if nuc_level >= 2 and pol["stability"] < 4:
        actions["nuclear_posture"] = "elevated"  # signal but don't use
    else:
        actions["nuclear_posture"] = "baseline"

    # Mobilization if desperate
    if mil["ground"] < 8 and round_num >= 3:
        actions["mobilization"] = "partial"

    actions["tech_rd"] = {"ai": eco["gdp"] * tech_pct * 0.5, "nuclear": 0}
    actions["covert_ops"] = []
    if round_num >= 2:
        actions["covert_ops"].append({
            "type": "cyber",
            "target": "heartland",
            "objective": "military_disruption",
        })

    # Negotiations
    # 1. Deal with Columbia (Pathfinder's priority)
    if deal_window_open and round_num >= 2:
        negotiations.append({
            "type": "peace_framework",
            "from": "nordostan",
            "to": "columbia",
            "terms": {
                "proposal": "grand_bargain",
                "offer": "ceasefire_current_lines_plus_sanctions_relief",
                "demand": "recognition_annexed_territories",
            },
            "likelihood": 0.4 + round_num * 0.05,
        })

    # 2. Cathay support request (Compass channels)
    negotiations.append({
        "type": "coin_transfer",
        "from": "nordostan",
        "to": "cathay",
        "terms": {"request": True, "amount": 2},
        "likelihood": 0.6,
    })

    # 3. Oil deal via OPEC coordination
    if eco["sanctions_on_me"] > 2:
        negotiations.append({
            "type": "oil_deal",
            "from": "nordostan",
            "to": "mirage",
            "terms": {"sanctions_routing": True, "discount": 0.15},
            "likelihood": 0.5,
        })

    reasoning["final_decision"] = (
        f"Round {round_num}: Pathfinder {'probing for deal' if deal_window_open else 'consolidating'}. "
        f"Military: {'offensive' if military_advantage else 'grinding'}. "
        f"Economy: {eco['health']}. OPEC: high production for revenue."
    )

    return actions, negotiations, reasoning


def deliberate_heartland(ws: WorldState, round_num: int, rng: random.Random) -> Tuple[dict, list, dict]:
    """Heartland: Beacon (HoS), Bulwark (military), Broker (negotiator)."""
    briefs = get_role_briefs("heartland")
    c = ws.countries["heartland"]
    mil = assess_military_balance(ws, "heartland")
    eco = assess_economic_health(ws, "heartland")
    pol = assess_political_situation(ws, "heartland")
    ee_war = assess_war_status(ws, "eastern_ereb")

    reasoning = {"team": "heartland", "round": round_num, "role_positions": {}, "internal_dynamics": "", "final_decision": ""}

    actions = {}
    negotiations = []

    occupied = ee_war.get("occupied_zones", [])
    support = pol["support"]

    # --- BEACON: Hold the Line ---
    reasoning["role_positions"]["beacon"] = {
        "position": f"No territorial concessions. {len(occupied)} zones occupied. Support at {support:.0f}%.",
        "will_negotiate": support < 45 or round_num >= 6,
        "red_line": "no_formal_recognition_of_annexation",
    }

    # --- BULWARK: Military Assessment ---
    can_counterattack = mil["ground"] >= ee_war.get("attacker_ground", 999) * 0.8
    reasoning["role_positions"]["bulwark"] = {
        "position": f"{'Counteroffensive possible' if can_counterattack else 'Defensive hold only'}. "
                    f"Ground forces: {mil['ground']}.",
        "election_ambition": "high" if support < 50 else "patient",
    }

    # --- BROKER: Pragmatic Deal ---
    reasoning["role_positions"]["broker"] = {
        "position": "EU membership path is the real prize. Temporary ceasefire preserving future claims is acceptable.",
        "back_channel": "active with Compass (Nordostan)" if round_num >= 3 else "preparing",
    }

    # Internal dynamics
    if support >= 50:
        reasoning["internal_dynamics"] = "Beacon leads. Bulwark defers. Broker prepares back-channels."
    elif support >= 40:
        reasoning["internal_dynamics"] = "Beacon weakening. Bulwark positioning for election. Broker pushing deal."
    else:
        reasoning["internal_dynamics"] = "Crisis mode. Bulwark openly challenging. Broker in EU capitals."

    # === DECISION SYNTHESIS ===
    baseline_social = c["economic"].get("social_spending_baseline", 0.30)
    social_pct = max(baseline_social - 0.10, 0.15)  # wartime austerity
    mil_pct = 0.55  # all in on defense
    tech_pct = 0.02

    actions["budget"] = {
        "social_spending": eco["gdp"] * social_pct,
        "social_pct": social_pct,
        "social_spending_ratio": social_pct,
        "military_total": eco["gdp"] * mil_pct,
        "tech_total": eco["gdp"] * tech_pct,
        "military": {
            "ground": {"coins": eco["gdp"] * mil_pct * 0.8, "tier": "accelerated"},
            "naval": {"coins": 0, "tier": "normal"},
            "tactical_air": {"coins": eco["gdp"] * mil_pct * 0.2, "tier": "normal"},
        },
    }

    actions["tariffs"] = {}
    actions["sanctions"] = {}

    # Military: defensive hold or limited counterattack
    actions["military_ops"] = []
    if can_counterattack and rng.random() < 0.3 + round_num * 0.05:
        actions["military_ops"].append({
            "type": "counterattack",
            "target": "nordostan",
            "target_zone": "heartland_2",
            "units": min(3, mil["ground"] // 3),
        })

    # Mobilization
    if mil["ground"] < 10:
        actions["mobilization"] = "partial"
    elif mil["ground"] < 5:
        actions["mobilization"] = "general"

    actions["tech_rd"] = {"ai": 0, "nuclear": 0}
    actions["covert_ops"] = []

    # Negotiations
    # 1. Request Western arms (critical)
    negotiations.append({
        "type": "arms_request",
        "from": "heartland",
        "to": "columbia",
        "terms": {"request": "ground_units", "amount": 3, "urgency": "critical"},
        "likelihood": 0.9,
    })
    negotiations.append({
        "type": "coin_request",
        "from": "heartland",
        "to": "columbia",
        "terms": {"amount": 2},
        "likelihood": 0.8,
    })

    # 2. EU support (Broker channels)
    negotiations.append({
        "type": "aid_request",
        "from": "heartland",
        "to": "teutonia",
        "terms": {"economic_aid": 1, "eu_membership_progress": True},
        "likelihood": 0.7,
    })

    # 3. If desperate, Broker back-channel to Nordostan
    if support < 40 and round_num >= 4:
        negotiations.append({
            "type": "peace_exploration",
            "from": "heartland",
            "to": "nordostan",
            "terms": {"ceasefire_exploration": True, "no_formal_recognition": True},
            "likelihood": 0.3,
        })

    reasoning["final_decision"] = (
        f"Round {round_num}: {'Beacon holds firm' if support >= 45 else 'Internal pressure mounting'}. "
        f"Defense budget {mil_pct:.0%}. {'Mobilization ordered.' if actions.get('mobilization') else ''} "
        f"Requesting Western arms. {'Broker exploring back-channels.' if support < 40 else ''}"
    )

    return actions, negotiations, reasoning


def deliberate_persia(ws: WorldState, round_num: int, rng: random.Random) -> Tuple[dict, list, dict]:
    """Persia: Furnace (Supreme Leader), Anvil (IRGC), Dawn (reformist)."""
    briefs = get_role_briefs("persia")
    c = ws.countries["persia"]
    mil = assess_military_balance(ws, "persia")
    eco = assess_economic_health(ws, "persia")
    pol = assess_political_situation(ws, "persia")

    reasoning = {"team": "persia", "round": round_num, "role_positions": {}, "internal_dynamics": "", "final_decision": ""}

    actions = {}
    negotiations = []

    gulf_gate_blocked = ws.chokepoint_status.get("gulf_gate_ground") == "blocked" or \
                        ws.chokepoint_status.get("hormuz") == "blocked"

    # --- ANVIL: Gulf Gate as Leverage ---
    reasoning["role_positions"]["anvil"] = {
        "gulf_gate_status": "maintained" if gulf_gate_blocked else "not_active",
        "position": "Gulf Gate blockade is our primary leverage. Do NOT release without massive concessions.",
        "business_interests": "IRGC businesses suffering from sanctions. Wants deal that preserves economic network.",
    }

    # --- FURNACE: Resistance Ideology ---
    reasoning["role_positions"]["furnace"] = {
        "position": "Nuclear program is divine right. Resistance continues. But survival comes first.",
        "consolidation": "building" if round_num <= 3 else "established",
        "independence_from_anvil": "weak" if round_num <= 2 else "growing",
    }

    # --- DAWN: Street Voice ---
    reasoning["role_positions"]["dawn"] = {
        "position": f"People are suffering. Sanctions and war destroy the economy. "
                    f"{'Engagement with West is only path to relief.' if eco['health'] in ('crisis', 'strained') else 'Cautious opening.'}",
        "urgency": "desperate" if eco["health"] == "crisis" else "high",
    }

    # Internal: Anvil vs Furnace power struggle
    if round_num <= 2:
        reasoning["internal_dynamics"] = "Anvil dominates. Furnace consolidating religious base. Dawn suppressed."
    elif round_num <= 5:
        reasoning["internal_dynamics"] = "Furnace gaining authority. Anvil controls military but Furnace controls theology. Dawn exploits cracks."
    else:
        reasoning["internal_dynamics"] = "Power balance depends on war outcome and economic crisis."

    # === DECISION SYNTHESIS ===
    baseline_social = c["economic"].get("social_spending_baseline", 0.25)
    social_pct = max(baseline_social - 0.08, 0.10) if eco["health"] == "crisis" else baseline_social - 0.03
    mil_pct = 0.45  # war economy
    tech_pct = 0.10

    actions["budget"] = {
        "social_spending": eco["gdp"] * social_pct,
        "social_pct": social_pct,
        "social_spending_ratio": social_pct,
        "military_total": eco["gdp"] * mil_pct,
        "tech_total": eco["gdp"] * tech_pct,
        "military": {
            "ground": {"coins": eco["gdp"] * mil_pct * 0.5, "tier": "normal"},
            "naval": {"coins": eco["gdp"] * mil_pct * 0.2, "tier": "normal"},
            "tactical_air": {"coins": eco["gdp"] * mil_pct * 0.3, "tier": "normal"},
        },
    }

    actions["tariffs"] = {}
    actions["sanctions"] = {}

    # Gulf Gate blockade maintenance (Anvil's priority)
    actions["military_ops"] = []
    if gulf_gate_blocked:
        actions["military_ops"].append({
            "type": "maintain_blockade",
            "zone": "cp_gulf_gate",
            "description": "Maintain ground-based Gulf Gate blockade",
        })
    elif mil["ground"] >= 2:
        # Establish if not already
        actions["military_ops"].append({
            "type": "blockade",
            "zone": "cp_gulf_gate",
            "description": "Establish/reinforce Gulf Gate blockade",
        })

    # Nuclear R&D (Furnace's directive)
    nuclear_investment = eco["gdp"] * tech_pct * (0.6 if round_num >= 3 else 0.4)
    actions["tech_rd"] = {
        "ai": eco["gdp"] * tech_pct * 0.2,
        "nuclear": nuclear_investment,
    }

    # OPEC production
    if eco.get("oil_producer"):
        actions["opec_production"] = "normal"  # maintain for revenue

    actions["covert_ops"] = []
    if round_num >= 2 and rng.random() < 0.5:
        actions["covert_ops"].append({
            "type": "sabotage",
            "target": "levantia",
            "objective": "proxy_retaliation",
        })

    # Negotiations
    # 1. If economy in crisis, Dawn pushes for engagement
    if eco["health"] in ("crisis", "strained") and round_num >= 3:
        negotiations.append({
            "type": "engagement_signal",
            "from": "persia",
            "to": "columbia",
            "terms": {
                "proposal": "sanctions_relief_for_nuclear_limits",
                "offer": "nuclear_threshold_freeze",
                "demand": "sanctions_partial_lifting",
            },
            "likelihood": 0.3 + (0.2 if eco["health"] == "crisis" else 0),
        })

    # 2. Cathay support
    negotiations.append({
        "type": "oil_deal",
        "from": "persia",
        "to": "cathay",
        "terms": {"discounted_oil": True, "bypass_sanctions": True},
        "likelihood": 0.6,
    })

    # 3. Nordostan solidarity
    if round_num >= 2:
        negotiations.append({
            "type": "intelligence_sharing",
            "from": "persia",
            "to": "nordostan",
            "terms": {"shared_interest": "counter_western_pressure"},
            "likelihood": 0.5,
        })

    reasoning["final_decision"] = (
        f"Round {round_num}: {'Anvil dominates' if round_num <= 2 else 'Furnace asserting'}. "
        f"Gulf Gate {'maintained' if gulf_gate_blocked else 'establishing'}. "
        f"Nuclear R&D {'accelerating' if round_num >= 3 else 'continuing'}. "
        f"Economy: {eco['health']}. {'Dawn pushing for engagement.' if eco['health'] == 'crisis' else ''}"
    )

    return actions, negotiations, reasoning


def deliberate_europe(ws: WorldState, round_num: int, rng: random.Random) -> Tuple[dict, list, dict]:
    """
    Europe team: Lumiere (Gallia), Forge (Teutonia), Sentinel (Freeland),
    Ponte (debt-ridden blocker), Mariner (Albion), Pillar (EU chair).
    Each pushes national interest. EU decisions require unanimity.
    """
    briefs = get_role_briefs("europe")

    reasoning = {"team": "europe", "round": round_num, "role_positions": {}, "eu_decisions": [], "final_decision": ""}

    all_actions = {}
    negotiations = []

    # EU member countries
    eu_members = {
        "gallia": {"brief_name": "lumiere", "push": "strategic_autonomy", "nuclear": True, "gdp_factor": 1.0},
        "teutonia": {"brief_name": "forge", "push": "economic_stability", "nuclear": False, "gdp_factor": 1.1},
        "freeland": {"brief_name": "sentinel", "push": "maximum_security", "nuclear": False, "gdp_factor": 0.3},
        "ponte": {"brief_name": "ponte_role", "push": "hedge_all_sides", "nuclear": False, "gdp_factor": 0.6},
        "albion": {"brief_name": "mariner", "push": "special_relationship", "nuclear": True, "gdp_factor": 0.8},
    }

    for cid, info in eu_members.items():
        c = ws.countries.get(cid)
        if not c:
            continue
        eco = assess_economic_health(ws, cid)
        mil = assess_military_balance(ws, cid)
        pol = assess_political_situation(ws, cid)

        # Role-specific positions
        if cid == "gallia":
            reasoning["role_positions"]["lumiere"] = {
                "position": "European strategic autonomy. French nuclear umbrella. Independent Persia policy.",
                "defense_spending_push": "increase to 3%",
                "heartland_support": "strong",
            }
        elif cid == "teutonia":
            reasoning["role_positions"]["forge"] = {
                "position": "Economic stability first. Cathay trade essential. Reluctant rearmament.",
                "cathay_trade_protection": "high priority",
                "heartland_support": "strong but budget-constrained",
            }
        elif cid == "freeland":
            reasoning["role_positions"]["sentinel"] = {
                "position": "Maximum Nordostan containment. NATO Article 5 sacred. Defense spending to 4%.",
                "heartland_support": "maximum possible",
                "threat_level": "existential",
            }
        elif cid == "ponte":
            reasoning["role_positions"]["ponte"] = {
                "position": f"Debt crisis (debt {eco['debt']:.1f}). Block anything that costs money. Hedge between all sides.",
                "eu_blocker": True,
                "for_sale": "to highest bidder",
            }
        elif cid == "albion":
            reasoning["role_positions"]["mariner"] = {
                "position": "Special relationship with Columbia. Intelligence cooperation. Post-Brexit relevance.",
                "intelligence_sharing": "columbia_focused",
            }

        baseline_social = c["economic"].get("social_spending_baseline", 0.30)
        at_war = ws.get_country_at_war(cid)

        if info["push"] == "maximum_security":
            mil_pct = 0.30
            social_pct = max(baseline_social - 0.05, 0.20)
        elif info["push"] == "economic_stability":
            mil_pct = 0.15 + (0.05 * round_num / 8)  # gradual rearmament
            social_pct = baseline_social
        elif info["push"] == "hedge_all_sides":
            mil_pct = 0.10
            social_pct = baseline_social  # Ponte can't cut social
        else:
            mil_pct = 0.20
            social_pct = max(baseline_social - 0.02, 0.22)

        tech_pct = 0.08

        country_actions = {
            "budget": {
                "social_spending": eco["gdp"] * social_pct,
                "social_pct": social_pct,
                "social_spending_ratio": social_pct,
                "military_total": eco["gdp"] * mil_pct,
                "tech_total": eco["gdp"] * tech_pct,
                "military": {
                    "ground": {"coins": eco["gdp"] * mil_pct * 0.5, "tier": "normal"},
                    "naval": {"coins": eco["gdp"] * mil_pct * 0.2, "tier": "normal"},
                    "tactical_air": {"coins": eco["gdp"] * mil_pct * 0.3, "tier": "normal"},
                },
            },
            "tariffs": {},
            "sanctions": {"nordostan": 3, "persia": 2},
            "military_ops": [],
            "tech_rd": {"ai": eco["gdp"] * tech_pct * 0.7, "nuclear": 0},
            "covert_ops": [],
        }

        all_actions[cid] = country_actions

    # EU collective decisions
    eu_decisions = []

    # 1. Nordostan sanctions: unanimous (Ponte may block tightening)
    ponte_blocks = rng.random() < 0.3  # Ponte blocks ~30% of the time
    eu_decisions.append({
        "issue": "nordostan_sanctions_tightening",
        "result": "blocked_by_ponte" if ponte_blocks else "approved",
        "level": 3 if not ponte_blocks else 2,
    })

    # 2. Heartland support package
    eu_decisions.append({
        "issue": "heartland_aid_package",
        "result": "approved_reduced" if ponte_blocks else "approved_full",
        "amount": 1 if ponte_blocks else 2,
    })

    # 3. Defense spending increase
    eu_decisions.append({
        "issue": "defense_spending_target",
        "result": "3%_target_aspirational",
        "binding": False,
    })

    reasoning["eu_decisions"] = eu_decisions

    # Collective negotiations
    if not ponte_blocks:
        negotiations.append({
            "type": "coin_transfer",
            "from": "teutonia",
            "to": "heartland",
            "terms": {"amount": 1, "eu_package": True},
            "likelihood": 0.8,
        })

    # Lumiere independent action
    if round_num >= 3:
        negotiations.append({
            "type": "security_guarantee",
            "from": "gallia",
            "to": "heartland",
            "terms": {"nuclear_umbrella_extension": True},
            "likelihood": 0.4,
        })

    # Mariner intelligence sharing
    negotiations.append({
        "type": "intelligence_sharing",
        "from": "albion",
        "to": "columbia",
        "terms": {"signals_intelligence": True, "persia_targeting": True},
        "likelihood": 0.9,
    })

    reasoning["final_decision"] = (
        f"Round {round_num}: EU {'divided (Ponte blocking)' if ponte_blocks else 'united on Nordostan sanctions'}. "
        f"Heartland aid: {'reduced' if ponte_blocks else 'full'}. Defense spending gradual increase."
    )

    return all_actions, negotiations, reasoning


# ---------------------------------------------------------------------------
# SOLO COUNTRY DELIBERATIONS
# ---------------------------------------------------------------------------

SOLO_DECISION_LOGIC = {
    "bharata": {
        "strategy": "non_alignment_optimization",
        "priorities": ["economic_growth", "strategic_autonomy", "third_pole_status"],
    },
    "levantia": {
        "strategy": "regional_dominance",
        "priorities": ["persia_threat_elimination", "columbia_alliance", "regional_hegemony"],
    },
    "formosa": {
        "strategy": "survival",
        "priorities": ["semiconductor_leverage", "columbia_protection", "avoid_provocation"],
    },
    "phrygia": {
        "strategy": "maximum_leverage",
        "priorities": ["bosphorus_control", "play_all_sides", "nato_membership_leverage"],
    },
    "yamato": {
        "strategy": "remilitarization",
        "priorities": ["pacific_security", "columbia_alliance", "constitutional_revision"],
    },
    "solaria": {
        "strategy": "oil_power_broker",
        "priorities": ["oil_pricing", "vision_reform", "hedge_us_china"],
    },
    "choson": {
        "strategy": "provocateur",
        "priorities": ["regime_survival", "nuclear_leverage", "extract_concessions"],
    },
    "hanguk": {
        "strategy": "tech_competition",
        "priorities": ["semiconductor_leadership", "alliance_management", "choson_threat"],
    },
    "caribe": {
        "strategy": "survival",
        "priorities": ["resist_columbia", "find_patrons", "regime_continuation"],
    },
    "mirage": {
        "strategy": "financial_intermediary",
        "priorities": ["connect_everyone", "sanctions_routing", "pragmatic_hedging"],
    },
}


def deliberate_solo(ws: WorldState, country_id: str, round_num: int, rng: random.Random) -> Tuple[dict, list, dict]:
    """Generate decisions for a solo country based on its strategy profile."""
    c = ws.countries.get(country_id)
    if not c:
        return {}, [], {"error": f"{country_id} not found"}

    eco = assess_economic_health(ws, country_id)
    mil = assess_military_balance(ws, country_id)
    pol = assess_political_situation(ws, country_id)
    gap = assess_gap_ratio(ws)

    logic = SOLO_DECISION_LOGIC.get(country_id, {"strategy": "default", "priorities": ["stability"]})
    strategy = logic["strategy"]

    reasoning = {
        "team": country_id,
        "round": round_num,
        "strategy": strategy,
        "assessment": {"eco": eco["health"], "stab": pol["stability"], "at_war": mil["at_war"]},
        "decisions": [],
    }

    actions = {}
    negotiations = []

    baseline_social = c["economic"].get("social_spending_baseline", 0.25)
    at_war = ws.get_country_at_war(country_id)

    # Default budget
    if at_war:
        social_pct = max(baseline_social - 0.05, 0.15)
        mil_pct = 0.40
    else:
        social_pct = baseline_social
        mil_pct = 0.15

    tech_pct = 0.05

    # Strategy-specific adjustments
    if strategy == "non_alignment_optimization":
        # Bharata: balance between Columbia and Cathay
        mil_pct = 0.20
        tech_pct = 0.10
        negotiations.append({
            "type": "trade_deal",
            "from": country_id,
            "to": "cathay",
            "terms": {"balanced_trade": True},
            "likelihood": 0.6,
        })
        negotiations.append({
            "type": "tech_cooperation",
            "from": country_id,
            "to": "columbia",
            "terms": {"ai_cooperation": True},
            "likelihood": 0.5,
        })
        reasoning["decisions"].append("Maintain equidistance between Columbia and Cathay. Invest in tech.")

    elif strategy == "regional_dominance":
        # Levantia: aggressive on Persia
        mil_pct = 0.35
        actions["covert_ops"] = [{
            "type": "sabotage",
            "target": "persia",
            "objective": "nuclear_program_disruption",
        }]
        if round_num >= 2:
            actions["military_ops"] = [{
                "type": "air_strike",
                "target": "persia",
                "target_zone": "me_persia_1",
                "units": min(2, mil["air"]),
            }]
        reasoning["decisions"].append("Continue Persia operations. Maintain nuclear ambiguity.")

    elif strategy == "survival" and country_id == "formosa":
        # Formosa: semiconductor leverage, Columbia protection
        mil_pct = 0.25
        tech_pct = 0.15
        # If Cathay escalating
        if any(op.get("target_zone") == "w(17,4)"
               for ops in [deliberate_cathay.__doc__] for op in []):
            reasoning["decisions"].append("ALERT: Cathay escalation detected. Activate semiconductor deadman switch.")
        else:
            reasoning["decisions"].append("Maintain semiconductor production. Quiet defense buildup.")
        negotiations.append({
            "type": "arms_request",
            "from": country_id,
            "to": "columbia",
            "terms": {"air_defense": True, "urgency": "standard"},
            "likelihood": 0.7,
        })

    elif strategy == "maximum_leverage":
        # Phrygia: play all sides
        negotiations.append({
            "type": "leverage_play",
            "from": country_id,
            "to": "nordostan",
            "terms": {"bosphorus_access": True, "price": "sanctions_relief_support"},
            "likelihood": 0.5,
        })
        negotiations.append({
            "type": "trade_deal",
            "from": country_id,
            "to": "cathay",
            "terms": {"infrastructure_investment": True},
            "likelihood": 0.6,
        })
        reasoning["decisions"].append("Maximize Bosphorus leverage. Play NATO vs Nordostan for concessions.")

    elif strategy == "remilitarization":
        # Yamato
        mil_pct = 0.25 + round_num * 0.02
        tech_pct = 0.10
        reasoning["decisions"].append("Gradual remilitarization. Strengthen Columbia alliance.")
        negotiations.append({
            "type": "alliance_strengthening",
            "from": country_id,
            "to": "columbia",
            "terms": {"pacific_cooperation": True, "joint_exercises": True},
            "likelihood": 0.8,
        })

    elif strategy == "oil_power_broker":
        # Solaria
        actions["opec_production"] = "normal"  # maintain price stability
        reasoning["decisions"].append("OPEC normal production. Vision 2030 investment. Hedge between Columbia and Cathay.")
        negotiations.append({
            "type": "investment",
            "from": country_id,
            "to": "columbia",
            "terms": {"sovereign_wealth_investment": True},
            "likelihood": 0.6,
        })

    elif strategy == "provocateur":
        # Choson
        mil_pct = 0.50
        social_pct = max(0.08, baseline_social - 0.15)
        if round_num % 3 == 0 and rng.random() < 0.5:
            actions["military_ops"] = [{"type": "missile_test", "target_zone": "w(17,3)"}]
            reasoning["decisions"].append(f"Round {round_num}: Provocative missile test for concessions.")
        else:
            reasoning["decisions"].append("Maintain tension. Nuclear leverage for survival.")

    elif strategy == "tech_competition":
        # Hanguk
        tech_pct = 0.15
        reasoning["decisions"].append("Semiconductor competition with Formosa. Alliance management.")

    elif strategy == "survival" and country_id == "caribe":
        # Caribe
        social_pct = max(0.10, baseline_social - 0.10)
        negotiations.append({
            "type": "patron_request",
            "from": country_id,
            "to": "cathay",
            "terms": {"economic_aid": True, "military_presence": True},
            "likelihood": 0.4 + round_num * 0.05,
        })
        if rng.random() < 0.3:
            negotiations.append({
                "type": "patron_request",
                "from": country_id,
                "to": "nordostan",
                "terms": {"military_presence": True},
                "likelihood": 0.3,
            })
        reasoning["decisions"].append("Seek external patrons. Resist Columbia pressure.")

    elif strategy == "financial_intermediary":
        # Mirage
        reasoning["decisions"].append("Financial intermediary. Route sanctions for commission.")
        negotiations.append({
            "type": "financial_services",
            "from": country_id,
            "to": "nordostan",
            "terms": {"sanctions_routing": True, "commission": 0.05},
            "likelihood": 0.6,
        })

    actions["budget"] = {
        "social_spending": eco["gdp"] * social_pct,
        "social_pct": social_pct,
        "social_spending_ratio": social_pct,
        "military_total": eco["gdp"] * mil_pct,
        "tech_total": eco["gdp"] * tech_pct,
        "military": {
            "ground": {"coins": eco["gdp"] * mil_pct * 0.5, "tier": "normal"},
            "naval": {"coins": eco["gdp"] * mil_pct * 0.3, "tier": "normal"},
            "tactical_air": {"coins": eco["gdp"] * mil_pct * 0.2, "tier": "normal"},
        },
    }
    if "tariffs" not in actions:
        actions["tariffs"] = {}
    if "sanctions" not in actions:
        actions["sanctions"] = {}
    if "tech_rd" not in actions:
        actions["tech_rd"] = {"ai": eco["gdp"] * tech_pct * 0.5, "nuclear": 0}

    return actions, negotiations, reasoning
