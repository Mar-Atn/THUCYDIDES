"""Smoke test for engine.agents.map_context.

Run from app/ directory:
    PYTHONPATH=. python3 tests/test_map_context_smoke.py
"""

from engine.agents.map_context import (
    build_country_military_context,
    build_theater_map,
    build_zone_summary,
    get_attackable_zones,
    get_country_home_zones,
    get_country_theaters,
    load_adjacency,
    load_deployments,
    load_zones,
)


def main() -> None:
    zones = load_zones()
    adj = load_adjacency()
    deployments = load_deployments()
    print(f"Zones loaded: {len(zones)}")
    print(f"Adjacency entries: {len(adj)}")
    print(f"Countries with deployments: {len(deployments)}")
    print(f"Deployments for Sarmatia: {deployments.get('sarmatia', {})}")
    print()
    print(f"Sarmatia theaters: {get_country_theaters('sarmatia')}")
    print(f"Sarmatia home zones: {get_country_home_zones('sarmatia')}")
    print(f"Attackable zones for Sarmatia: {get_attackable_zones('sarmatia')}")
    print()
    print("=== Sarmatia military context ===")
    print(build_country_military_context("sarmatia"))
    print()
    print("=== Sarmatia theater map (Block 1) ===")
    print(build_theater_map("sarmatia"))
    print()
    print("=== Zone summary: ruthenia_2 (viewed by sarmatia) ===")
    print(build_zone_summary("ruthenia_2", "sarmatia"))
    print()
    print("=== Ruthenia military context ===")
    print(build_country_military_context("ruthenia"))


if __name__ == "__main__":
    main()
