"""Map / zone context for AI participants.

Gives AI agents real spatial awareness when making military decisions:
- Where their units are deployed (zone by zone)
- Which zones they can attack (adjacent to their forces)
- Visible enemy forces in those zones
- Theaters they are active in
- Home territory

Sources (CSV):
- 2 SEED/C_MECHANICS/C4_DATA/zones.csv
- 2 SEED/C_MECHANICS/C4_DATA/zone_adjacency.csv
- 2 SEED/C_MECHANICS/C4_DATA/deployments.csv
- 2 SEED/C_MECHANICS/C4_DATA/countries.csv

Feeds into:
- engine/agents/decisions.py : build_military_context (Layer 2)
- engine/agents/world_context.py : build_theater_map (Rich Block 1)

Design notes:
- Lazy loads with module-level caches (CSV files are small, tens of KB).
- Graceful handling of missing / malformed rows (empty ids, bad counts).
- Adjacency is undirected — stored symmetrically.
- No visibility filter yet; for now agents see all deployments in their
  theaters. Fog-of-war to be added in a later sprint.
"""

from __future__ import annotations

import csv
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "2 SEED", "C_MECHANICS", "C4_DATA",
)
ZONES_CSV = os.path.join(_DATA_DIR, "zones.csv")
ADJACENCY_CSV = os.path.join(_DATA_DIR, "zone_adjacency.csv")
DEPLOYMENTS_CSV = os.path.join(_DATA_DIR, "deployments.csv")
COUNTRIES_CSV = os.path.join(_DATA_DIR, "countries.csv")

# Module-level caches (lazy)
_zones_cache: Optional[dict[str, dict]] = None
_adjacency_cache: Optional[dict[str, list[str]]] = None
_deployments_cache: Optional[dict[str, dict[str, dict[str, int]]]] = None
_countries_cache: Optional[dict[str, dict]] = None


# ---------------------------------------------------------------------------
# LOADERS
# ---------------------------------------------------------------------------

def load_zones() -> dict[str, dict]:
    """Load all zones from zones.csv, keyed by zone id.

    Returns dict mapping zone_id -> {id, display_name, type, owner, theater,
    is_chokepoint, die_hard}. Rows with empty id are skipped.
    """
    global _zones_cache
    if _zones_cache is not None:
        return _zones_cache

    zones: dict[str, dict] = {}
    try:
        with open(ZONES_CSV) as f:
            for row in csv.DictReader(f):
                zone_id = (row.get("id") or "").strip()
                if not zone_id:
                    continue
                zones[zone_id] = {
                    "id": zone_id,
                    "display_name": (row.get("display_name") or "").strip(),
                    "type": (row.get("type") or "").strip(),
                    "owner": (row.get("owner") or "").strip(),
                    "theater": (row.get("theater") or "").strip(),
                    "is_chokepoint": (row.get("is_chokepoint") or "").strip().lower() == "true",
                    "die_hard": (row.get("die_hard") or "").strip().lower() == "true",
                }
    except FileNotFoundError:
        logger.warning("zones.csv not found at %s", ZONES_CSV)
        return {}
    _zones_cache = zones
    return zones


def load_adjacency() -> dict[str, list[str]]:
    """Load adjacency graph. Returns {zone_id: [neighbor_zone_id, ...]}.

    Adjacency is symmetric — each pair inserted twice.
    """
    global _adjacency_cache
    if _adjacency_cache is not None:
        return _adjacency_cache

    adj: dict[str, list[str]] = {}
    try:
        with open(ADJACENCY_CSV) as f:
            for row in csv.DictReader(f):
                a = (row.get("zone_a") or "").strip()
                b = (row.get("zone_b") or "").strip()
                if not a or not b:
                    continue
                adj.setdefault(a, [])
                adj.setdefault(b, [])
                if b not in adj[a]:
                    adj[a].append(b)
                if a not in adj[b]:
                    adj[b].append(a)
    except FileNotFoundError:
        logger.warning("zone_adjacency.csv not found at %s", ADJACENCY_CSV)
        return {}
    _adjacency_cache = adj
    return adj


def load_deployments() -> dict[str, dict[str, dict[str, int]]]:
    """Load starting unit deployments.

    Returns nested dict: {country_id: {zone_id: {unit_type: count}}}
    """
    global _deployments_cache
    if _deployments_cache is not None:
        return _deployments_cache

    result: dict[str, dict[str, dict[str, int]]] = {}
    try:
        with open(DEPLOYMENTS_CSV) as f:
            for row in csv.DictReader(f):
                country = (row.get("country_id") or "").strip()
                zone = (row.get("zone_id") or "").strip()
                unit_type = (row.get("unit_type") or "").strip()
                count_raw = (row.get("count") or "0").strip()
                if not country or not zone or not unit_type:
                    continue
                try:
                    count = int(float(count_raw))
                except (ValueError, TypeError):
                    logger.debug("bad deployment count %r for %s/%s", count_raw, country, zone)
                    continue
                if count <= 0:
                    continue
                result.setdefault(country, {}).setdefault(zone, {})
                result[country][zone][unit_type] = result[country][zone].get(unit_type, 0) + count
    except FileNotFoundError:
        logger.warning("deployments.csv not found at %s", DEPLOYMENTS_CSV)
        return {}
    _deployments_cache = result
    return result


def _load_countries() -> dict[str, dict]:
    """Load countries.csv keyed by id."""
    global _countries_cache
    if _countries_cache is not None:
        return _countries_cache
    result: dict[str, dict] = {}
    try:
        with open(COUNTRIES_CSV) as f:
            for row in csv.DictReader(f):
                cid = (row.get("id") or "").strip()
                if cid:
                    result[cid] = row
    except FileNotFoundError:
        logger.warning("countries.csv not found at %s", COUNTRIES_CSV)
        return {}
    _countries_cache = result
    return result


def clear_cache() -> None:
    """Clear all module caches (useful for tests)."""
    global _zones_cache, _adjacency_cache, _deployments_cache, _countries_cache
    _zones_cache = None
    _adjacency_cache = None
    _deployments_cache = None
    _countries_cache = None


# ---------------------------------------------------------------------------
# QUERIES
# ---------------------------------------------------------------------------

def get_country_home_zones(
    country_id: str,
    countries_dict: Optional[dict[str, dict]] = None,
) -> list[str]:
    """Return list of home zone ids for a country from countries.csv.

    Args:
        country_id: country id (e.g., "sarmatia").
        countries_dict: optional pre-loaded countries dict. If None, loads from CSV.
    """
    if countries_dict is None:
        countries_dict = _load_countries()
    country = countries_dict.get(country_id)
    if not country:
        return []
    raw = (country.get("home_zones") or "").strip()
    if not raw:
        return []
    return [z.strip() for z in raw.split(",") if z.strip()]


def get_country_deployed_zones(country_id: str) -> list[str]:
    """Return zone ids where this country has any deployed units."""
    deployments = load_deployments()
    return list(deployments.get(country_id, {}).keys())


def get_attackable_zones(country_id: str) -> list[str]:
    """Zones this country can attack — any zone adjacent to a zone where
    it has ground/naval/tactical_air units and that is NOT itself owned
    by the attacker AND has no friendly units of its own.

    More simply: adjacent zones to any zone containing attacker's forces,
    excluding zones where the attacker already has units (not attacking self).
    """
    deployments = load_deployments()
    adj = load_adjacency()
    my_zones = set(deployments.get(country_id, {}).keys())
    reachable: set[str] = set()
    for z in my_zones:
        for nbr in adj.get(z, []):
            if nbr not in my_zones:
                reachable.add(nbr)
    return sorted(reachable)


def get_country_theaters(country_id: str) -> list[str]:
    """Theaters where this country has units deployed."""
    zones = load_zones()
    deployments = load_deployments()
    theaters: set[str] = set()
    for zid in deployments.get(country_id, {}).keys():
        z = zones.get(zid)
        if z and z.get("theater"):
            theaters.add(z["theater"])
    return sorted(theaters)


def _format_units(units: dict[str, int]) -> str:
    """Compact unit count formatting."""
    parts = []
    for ut in ("ground", "naval", "tactical_air", "strategic_missile", "air_defense"):
        if units.get(ut):
            parts.append(f"{ut}:{units[ut]}")
    # include any other unit types not in preferred order
    for ut, n in units.items():
        if n and ut not in {"ground", "naval", "tactical_air", "strategic_missile", "air_defense"}:
            parts.append(f"{ut}:{n}")
    return ", ".join(parts) if parts else "(none)"


# ---------------------------------------------------------------------------
# CONTEXT BUILDERS (text for LLM consumption)
# ---------------------------------------------------------------------------

def build_zone_summary(zone_id: str, country_id: str) -> str:
    """Human-readable summary for a specific zone: owner, units there,
    adjacent zones, and whether the viewing country has forces there.
    """
    zones = load_zones()
    adj = load_adjacency()
    deployments = load_deployments()

    z = zones.get(zone_id)
    if not z:
        return f"Zone {zone_id}: UNKNOWN"

    lines = [f"**{zone_id}** ({z['display_name']}) — {z['type']}, "
             f"owner={z['owner'] or 'none'}, theater={z['theater']}"]
    if z["is_chokepoint"]:
        lines[-1] += " [CHOKEPOINT]"
    if z["die_hard"]:
        lines[-1] += " [DIE-HARD]"

    # Units present (all countries) — for now unfiltered
    forces_here: list[str] = []
    for cid, czones in deployments.items():
        if zone_id in czones:
            forces_here.append(f"{cid}({_format_units(czones[zone_id])})")
    if forces_here:
        lines.append("  Forces present: " + "; ".join(forces_here))
    else:
        lines.append("  Forces present: none known")

    # Adjacency
    neighbors = adj.get(zone_id, [])
    if neighbors:
        lines.append("  Adjacent: " + ", ".join(neighbors))

    # Your posture
    my_here = deployments.get(country_id, {}).get(zone_id)
    if my_here:
        lines.append(f"  YOUR forces here: {_format_units(my_here)}")

    return "\n".join(lines)


def build_country_military_context(country_id: str) -> str:
    """Formatted text showing country's deployments, attackable zones,
    visible enemy forces in those zones, and theaters of operation.

    Produces ~1-2K tokens suitable for Layer 2 military context.
    """
    zones = load_zones()
    deployments = load_deployments()
    my_deployments = deployments.get(country_id, {})

    if not my_deployments:
        return f"# Map Situation for {country_id}\n\n(No deployment data available.)"

    lines = [f"# Map Situation — {country_id}", ""]

    # Active theaters
    theaters = get_country_theaters(country_id)
    if theaters:
        lines.append(f"**Active theaters:** {', '.join(theaters)}")
        lines.append("")

    # Your deployments — grouped by theater
    lines.append("## Your Deployments (zone-by-zone)")
    by_theater: dict[str, list[tuple[str, dict[str, int]]]] = {}
    for zid, units in my_deployments.items():
        z = zones.get(zid, {})
        theater = z.get("theater", "unknown")
        by_theater.setdefault(theater, []).append((zid, units))

    for theater in sorted(by_theater.keys()):
        lines.append(f"\n_Theater: {theater}_")
        for zid, units in sorted(by_theater[theater]):
            z = zones.get(zid, {})
            tags = []
            if z.get("is_chokepoint"):
                tags.append("CHOKEPOINT")
            if z.get("die_hard"):
                tags.append("DIE-HARD")
            tag_str = f" [{','.join(tags)}]" if tags else ""
            owner = z.get("owner", "?")
            own_marker = " (home)" if owner == country_id else f" (owner: {owner})"
            lines.append(f"- `{zid}`{own_marker}{tag_str}: {_format_units(units)}")

    # Attackable zones
    attackable = get_attackable_zones(country_id)
    lines.append("")
    lines.append("## Attackable Zones (adjacent to your forces)")
    if not attackable:
        lines.append("(none — no adjacent hostile/neutral zones)")
    else:
        adj = load_adjacency()
        for zid in attackable:
            z = zones.get(zid, {})
            if not z:
                lines.append(f"- `{zid}`: UNKNOWN zone")
                continue
            owner = z.get("owner", "none") or "none"
            theater = z.get("theater", "?")
            tags = []
            if z.get("is_chokepoint"):
                tags.append("CHOKEPOINT")
            if z.get("die_hard"):
                tags.append("DIE-HARD")
            tag_str = f" [{','.join(tags)}]" if tags else ""

            # Which of your zones border this one? (attack-from options)
            from_zones = [fz for fz in adj.get(zid, []) if fz in my_deployments]
            from_str = f" | attack from: {', '.join(from_zones)}" if from_zones else ""

            # Enemy forces visible here
            forces_here: list[str] = []
            for cid, czones in deployments.items():
                if cid == country_id:
                    continue
                if zid in czones:
                    forces_here.append(f"{cid}({_format_units(czones[zid])})")
            force_str = f" | forces: {'; '.join(forces_here)}" if forces_here else " | forces: none known"

            lines.append(
                f"- `{zid}` ({z.get('display_name', '?')}) — owner: {owner}, theater: {theater}{tag_str}{force_str}{from_str}"
            )

    # Visible enemy forces in your theaters (situational awareness)
    lines.append("")
    lines.append("## Visible Enemy/Foreign Forces in Your Theaters")
    theater_set = set(theaters)
    any_enemy = False
    for cid, czones in deployments.items():
        if cid == country_id:
            continue
        for zid, units in czones.items():
            z = zones.get(zid, {})
            if z.get("theater") not in theater_set:
                continue
            any_enemy = True
            lines.append(f"- `{zid}` ({z.get('theater')}): {cid} — {_format_units(units)}")
    if not any_enemy:
        lines.append("(no foreign forces observed in your theaters)")

    # Home territory
    home_zones = get_country_home_zones(country_id)
    if home_zones:
        lines.append("")
        lines.append(f"## Home Territory ({len(home_zones)} zones)")
        lines.append(", ".join(home_zones))

    return "\n".join(lines)


def build_theater_map(country_id: str) -> str:
    """Theater overview for Rich Block 1 — key zones this country cares about.

    Shorter than build_country_military_context: just lists the zones
    this country holds and neighbors it can reach, grouped by theater.
    """
    zones = load_zones()
    deployments = load_deployments()
    my_deployments = deployments.get(country_id, {})
    home_zones = get_country_home_zones(country_id)

    # Zones of interest: my deployments + home zones + directly attackable
    relevant_ids: set[str] = set(my_deployments.keys()) | set(home_zones)
    attackable = get_attackable_zones(country_id)
    relevant_ids |= set(attackable)

    if not relevant_ids:
        return ""

    # Group by theater
    by_theater: dict[str, list[str]] = {}
    for zid in relevant_ids:
        z = zones.get(zid)
        if not z:
            continue
        by_theater.setdefault(z.get("theater") or "unknown", []).append(zid)

    lines = ["## Your Theater Map (zones you hold or can reach)", ""]
    for theater in sorted(by_theater.keys()):
        lines.append(f"**{theater}:**")
        for zid in sorted(by_theater[theater]):
            z = zones[zid]
            owner = z.get("owner") or "none"
            role_tags = []
            if zid in my_deployments:
                role_tags.append("YOURS")
            elif zid in home_zones:
                role_tags.append("HOME")
            if zid in attackable:
                role_tags.append("ATTACKABLE")
            if z.get("is_chokepoint"):
                role_tags.append("CHOKEPOINT")
            if z.get("die_hard"):
                role_tags.append("DIE-HARD")
            tag_str = f" [{','.join(role_tags)}]" if role_tags else ""
            lines.append(f"- `{zid}` — {z.get('display_name', '?')} (owner: {owner}){tag_str}")
        lines.append("")

    lines.append(
        "When targeting military actions, you MUST use exact zone ids from this "
        "list (e.g., `ruthenia_2`) — never abstract names like 'Ukraine border'."
    )
    return "\n".join(lines)
