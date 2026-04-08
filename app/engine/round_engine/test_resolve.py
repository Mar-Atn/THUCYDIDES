"""Test harness for the round resolver.

Creates a handful of fake committed ``agent_decisions`` for round 1 of
the 'start_one' scenario, runs ``resolve_round``, verifies snapshots
were written, and prints combat narratives.

Run::

    cd app && PYTHONPATH=. python3 -m engine.round_engine.test_resolve
"""

from __future__ import annotations

import json
import logging

from engine.services.supabase import get_client
from engine.round_engine.resolve_round import resolve_round, _resolve_scenario_id

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("test_resolve")

SCENARIO_CODE = "start_one"
TEST_ROUND = 1
TEST_TAG = "TEST_HARNESS_RESOLVE_ROUND"


def _pick_attacker_and_target(client, scenario_id: str) -> tuple[list[str], int, int, str]:
    """Find one country's ground/air units + an enemy target hex."""
    res = (
        client.table("unit_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 0)
        .execute()
    )
    units = res.data or []
    # columbia attacker
    col_air = [u for u in units if u["country_code"] == "columbia"
               and u["unit_type"] == "tactical_air"][:3]
    # persia target hex (pick one with multiple units)
    per_units = [u for u in units if u["country_code"] == "persia"]
    if not col_air or not per_units:
        raise RuntimeError("Could not find attacker or target units for test")
    # pick persia hex with densest units
    from collections import Counter
    hex_ct = Counter((u["global_row"], u["global_col"]) for u in per_units)
    (tr, tc), _ = hex_ct.most_common(1)[0]
    return [u["unit_code"] for u in col_air], tr, tc, "columbia"


def _pick_mover(client, scenario_id: str) -> tuple[str, int, int]:
    """Pick a reserve unit to mobilize."""
    res = (
        client.table("unit_states_per_round")
        .select("*")
        .eq("scenario_id", scenario_id)
        .eq("round_num", 0)
        .eq("status", "reserve")
        .limit(5)
        .execute()
    )
    if not res.data:
        # fallback to any active ground unit
        res = (
            client.table("unit_states_per_round")
            .select("*")
            .eq("scenario_id", scenario_id)
            .eq("round_num", 0)
            .eq("unit_type", "ground")
            .limit(1)
            .execute()
        )
    u = res.data[0]
    return u["unit_code"], u["global_row"], u["global_col"]


def seed_fake_decisions(client, scenario_id: str) -> list[str]:
    """Insert 4 test decisions for round 1. Returns list of inserted IDs."""
    attacker_codes, tr, tc, atk_country = _pick_attacker_and_target(client, scenario_id)
    mover_code, mr, mc = _pick_mover(client, scenario_id)

    fake = [
        {
            "scenario_id": scenario_id,
            "country_code": atk_country,
            "action_type": "declare_attack",
            "action_payload": {
                "round_num": TEST_ROUND,
                "action_type": "declare_attack",
                "attacker_unit_codes": attacker_codes,
                "target_global_row": tr,
                "target_global_col": tc,
                "test_tag": TEST_TAG,
            },
            "rationale": "TEST: strike Persian concentration",
            "validation_status": "pending",
        },
        {
            "scenario_id": scenario_id,
            "country_code": "cathay",
            "action_type": "rd_investment",
            "action_payload": {
                "round_num": TEST_ROUND,
                "action_type": "rd_investment",
                "domain": "ai",
                "amount": 3,
                "test_tag": TEST_TAG,
            },
            "rationale": "TEST: AI R&D push",
            "validation_status": "pending",
        },
        {
            "scenario_id": scenario_id,
            "country_code": mover_code.split("_")[0],  # first token is country prefix
            "action_type": "mobilize_reserve",
            "action_payload": {
                "round_num": TEST_ROUND,
                "action_type": "mobilize_reserve",
                "unit_code": mover_code,
                "target_global_row": mr,
                "target_global_col": mc,
                "test_tag": TEST_TAG,
            },
            "rationale": "TEST: mobilize reserve",
            "validation_status": "pending",
        },
        {
            "scenario_id": scenario_id,
            "country_code": "albion",
            "action_type": "issue_statement",
            "action_payload": {
                "round_num": TEST_ROUND,
                "action_type": "issue_statement",
                "statement": "We call for restraint.",
                "test_tag": TEST_TAG,
            },
            "rationale": "TEST: diplomatic log",
            "validation_status": "pending",
        },
    ]

    res = client.table("agent_decisions").insert(fake).execute()
    return [r["id"] for r in res.data]


def cleanup_test_decisions(client, decision_ids: list[str]) -> None:
    if not decision_ids:
        return
    client.table("agent_decisions").delete().in_("id", decision_ids).execute()


def cleanup_test_snapshots(client, scenario_id: str) -> None:
    """Remove round 1 snapshots/events/combats produced by this harness."""
    client.table("unit_states_per_round").delete().eq(
        "scenario_id", scenario_id
    ).eq("round_num", TEST_ROUND).execute()
    client.table("country_states_per_round").delete().eq(
        "scenario_id", scenario_id
    ).eq("round_num", TEST_ROUND).execute()
    client.table("observatory_combat_results").delete().eq(
        "scenario_id", scenario_id
    ).eq("round_num", TEST_ROUND).execute()
    client.table("observatory_events").delete().eq(
        "scenario_id", scenario_id
    ).eq("round_num", TEST_ROUND).execute()
    client.table("round_states").delete().eq(
        "scenario_id", scenario_id
    ).eq("round_num", TEST_ROUND).execute()


def main() -> None:
    client = get_client()
    scenario_id = _resolve_scenario_id(client, SCENARIO_CODE)
    print(f"== Scenario: {SCENARIO_CODE} ({scenario_id})")

    # Clean any previous test artifacts for round 1
    print("== Cleaning prior round 1 test artifacts...")
    cleanup_test_snapshots(client, scenario_id)
    prior = (
        client.table("agent_decisions")
        .select("id,action_payload")
        .eq("scenario_id", scenario_id)
        .execute()
    )
    tagged = [
        r["id"] for r in (prior.data or [])
        if (r.get("action_payload") or {}).get("test_tag") == TEST_TAG
    ]
    cleanup_test_decisions(client, tagged)

    # Seed fakes
    print("== Seeding fake decisions for round 1...")
    dec_ids = seed_fake_decisions(client, scenario_id)
    print(f"   inserted {len(dec_ids)} decisions")

    # Run resolver
    print("== Running resolve_round...")
    summary = resolve_round(SCENARIO_CODE, TEST_ROUND)
    print(f"   decisions_processed = {summary['decisions_processed']}")
    print(f"   combats             = {summary['combats']}")
    print(f"   events              = {summary['events']}")

    # Verify snapshots
    print("\n== Verifying round 1 snapshots...")
    u = (
        client.table("unit_states_per_round")
        .select("unit_code", count="exact")
        .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
    )
    c = (
        client.table("country_states_per_round")
        .select("country_code", count="exact")
        .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
    )
    print(f"   unit_states_per_round   (round 1): {u.count} rows")
    print(f"   country_states_per_round(round 1): {c.count} rows")

    # Print combat narratives
    print("\n== Combat narratives ==")
    cres = (
        client.table("observatory_combat_results")
        .select("*")
        .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
    )
    for row in cres.data or []:
        print(f"  [{row['combat_type']}] "
              f"{row['attacker_country']} -> {row['defender_country']} "
              f"@({row['location_global_row']},{row['location_global_col']})")
        print(f"    attacker_units={row['attacker_units']} "
              f"defender_units={row['defender_units']}")
        print(f"    attacker_losses={row['attacker_losses']} "
              f"defender_losses={row['defender_losses']}")
        print(f"    rolls: atk={row['attacker_rolls']} def={row['defender_rolls']}")
        print(f"    {row['narrative']}")

    # Print activity events
    print("\n== Events ==")
    eres = (
        client.table("observatory_events")
        .select("event_type,summary,country_code")
        .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND)
        .order("created_at").execute()
    )
    for row in eres.data or []:
        print(f"  [{row['event_type']:20s}] {row['country_code']:10s} {row['summary']}")

    # Round state
    print("\n== round_states ==")
    rs = (
        client.table("round_states").select("*")
        .eq("scenario_id", scenario_id).eq("round_num", TEST_ROUND).execute()
    )
    print(json.dumps(rs.data, default=str, indent=2))

    # Cleanup
    print("\n== Cleaning up test artifacts...")
    cleanup_test_snapshots(client, scenario_id)
    cleanup_test_decisions(client, dec_ids)
    print("   done.")


if __name__ == "__main__":
    main()
