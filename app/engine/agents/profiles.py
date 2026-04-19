"""Role data loading and identity generation.

Loads role profiles from CSV, generates Block 2 identity via LLM.
Source: SEED_E5_AI_PARTICIPANT_MODULE_v1.md
"""

from __future__ import annotations

import csv
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

ROLES_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "2 SEED", "C_MECHANICS", "C4_DATA", "roles.csv",
)

COUNTRIES_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "2 SEED", "C_MECHANICS", "C4_DATA", "countries.csv",
)


def load_role(role_id: str) -> dict[str, Any]:
    """Load a single role from roles.csv."""
    with open(ROLES_CSV) as f:
        for row in csv.DictReader(f):
            if row["id"] == role_id:
                return _parse_role(row)
    raise ValueError(f"Role not found: {role_id}")


def load_all_roles() -> dict[str, dict]:
    """Load all roles from roles.csv."""
    roles = {}
    with open(ROLES_CSV) as f:
        for row in csv.DictReader(f):
            roles[row["id"]] = _parse_role(row)
    return roles


def load_heads_of_state() -> dict[str, dict]:
    """Load only heads of state (21 leaders)."""
    return {k: v for k, v in load_all_roles().items() if v["is_head_of_state"]}


def load_country_context(country_id: str) -> dict[str, Any]:
    """Load country starting data for context."""
    with open(COUNTRIES_CSV) as f:
        for row in csv.DictReader(f):
            if row["id"] == country_id:
                return {
                    "id": row["id"],
                    "sim_name": row["sim_name"],
                    "parallel": row["parallel"],
                    "regime_type": row["regime_type"],
                    "gdp": float(row["gdp"]),
                    "gdp_growth_base": float(row["gdp_growth_base"]),
                    "treasury": float(row["treasury"]),
                    "inflation": float(row["inflation"]),
                    "debt_burden": float(row.get("debt_burden", 0)),
                    "tax_rate": float(row.get("tax_rate", 0.24)),
                    "social_baseline": float(row.get("social_baseline", 0.30)),
                    "stability": float(row["stability"]),
                    # DEPRECATED 2026-04-15: political_support replaced by stability only
                    "political_support": 0,
                    "war_tiredness": float(row.get("war_tiredness", 0)),
                    "oil_producer": row["oil_producer"].lower() == "true",
                    "opec_member": row["opec_member"].lower() == "true",
                    "oil_production_mbpd": float(row.get("oil_production_mbpd", 0)) if row.get("oil_production_mbpd", "0") not in ("", "na") else 0,
                    "nuclear_level": int(row["nuclear_level"]),
                    "ai_level": int(row["ai_level"]),
                    "mil_ground": int(float(row["mil_ground"])),
                    "mil_naval": int(float(row["mil_naval"])),
                    "mil_tactical_air": int(float(row["mil_tactical_air"])),
                    "mil_strategic_missiles": int(float(row.get("mil_strategic_missiles", 0))),
                    "mil_air_defense": int(float(row.get("mil_air_defense", 0))),
                    "mobilization_pool": int(float(row.get("mobilization_pool", 0))),
                    "maintenance_per_unit": float(row.get("maintenance_per_unit", 0.05)),
                    "at_war_with": row.get("at_war_with", ""),
                }
    raise ValueError(f"Country not found: {country_id}")


def _derive_positions(row: dict) -> list[str]:
    """Derive positions list from CSV legacy boolean fields.

    Reads positions column if present; otherwise falls back to
    is_head_of_state, is_military_chief, is_diplomat booleans.
    """
    # If the CSV already has a positions column, use it
    raw = row.get("positions", "")
    if raw and raw.lower() not in ("", "false", "none"):
        return [p.strip() for p in raw.split(";") if p.strip()]
    # Derive from legacy booleans
    result: list[str] = []
    if row.get("is_head_of_state", "false").lower() == "true":
        result.append("head_of_state")
    if row.get("is_military_chief", "false").lower() == "true":
        result.append("military")
    if row.get("is_diplomat", "false").lower() == "true":
        result.append("diplomat")
    # position_type field may carry security/opposition/economy
    pt = row.get("position_type", "").strip().lower()
    if pt in ("security", "opposition", "economy") and pt not in result:
        result.append(pt)
    return result


def _parse_role(row: dict) -> dict[str, Any]:
    """Parse a CSV row into a role dict."""
    return {
        "id": row["id"],
        "character_name": row["character_name"],
        "parallel": row.get("parallel", ""),
        "country_id": row["country_id"],
        "team": row.get("team", ""),
        "faction": row.get("faction", ""),
        "title": row.get("title", ""),
        "age": int(row.get("age", 50)),
        "gender": row.get("gender", "M"),
        "is_head_of_state": row.get("is_head_of_state", "false").lower() == "true",
        "is_military_chief": row.get("is_military_chief", "false").lower() == "true",
        "positions": _derive_positions(row),
        "intelligence_pool": int(row.get("intelligence_pool", 0)),
        "personal_coins": float(row.get("personal_coins", 0)),
        "powers": [p.strip() for p in row.get("powers", "").split(";") if p.strip()],
        "objectives": [o.strip() for o in row.get("objectives", "").split(";") if o.strip()],
        "ticking_clock": "",  # DEPRECATED 2026-04-17
        "brief_file": row.get("brief_file", ""),
        "is_diplomat": row.get("is_diplomat", "false").lower() == "true",
        # Cards
        "sabotage_cards": int(row.get("sabotage_cards", 0)),
        "cyber_cards": int(row.get("cyber_cards", 0)),
        "disinfo_cards": int(row.get("disinfo_cards", 0)),
        "election_meddling_cards": int(row.get("election_meddling_cards", 0)),
        "assassination_cards": int(row.get("assassination_cards", 0)),
    }


IDENTITY_GENERATION_PROMPT = """Generate a character identity for a geopolitical simulation role.

Role: {character_name}
Title: {title}
Country: {country_name} ({parallel})
Age: {age}, Gender: {gender}
Faction: {faction}
Powers: {powers}
Objectives: {objectives}

Generate a 3-4 sentence personality description. Include:
1. Core personality traits and decision-making style
2. Communication style (how they speak in negotiations)
3. Key emotional drivers (what motivates them, what they fear)
4. Strategic tendency (aggressive/cautious, deal-maker/confrontational)

Write in second person ("You are..."). Be vivid and specific. This will be used as the agent's identity throughout the simulation."""


def build_identity_prompt(role: dict, country: dict) -> str:
    """Build the prompt for generating Block 2 identity."""
    return IDENTITY_GENERATION_PROMPT.format(
        character_name=role["character_name"],
        title=role["title"],
        country_name=country["sim_name"],
        parallel=country["parallel"],
        age=role["age"],
        gender=role["gender"],
        faction=role.get("faction", ""),
        powers=", ".join(role["powers"]),
        objectives=", ".join(role["objectives"]),
    )
