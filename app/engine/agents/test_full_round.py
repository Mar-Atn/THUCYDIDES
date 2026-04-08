"""Test: one full round with all 20 HoS agents in parallel.

Exercises ``run_full_round`` end-to-end — launches every HoS agent against
the ``start_one`` scenario, times the parallel phase, and reports summary
statistics.

Usage:
    cd app && PYTHONPATH=. python3 -m engine.agents.test_full_round
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import Counter

from engine.agents.full_round_runner import run_full_round

SCENARIO_CODE = "start_one"
ROUND_NUM = 1


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    print("\n" + "=" * 72)
    print(f" FULL-ROUND TEST: 20 agents, scenario={SCENARIO_CODE}, round={ROUND_NUM}")
    print("=" * 72)

    t0 = time.time()
    summary = await run_full_round(SCENARIO_CODE, ROUND_NUM)
    total = time.time() - t0

    agents = summary["agents"]
    successes = summary["successes"]
    failures = summary["failures"]

    print("\n--- Per-agent results ---")
    print(f"{'country':12s} {'character':20s} {'committed':10s} "
          f"{'action_type':24s} {'dur_s':>6s} {'calls':>5s} err")
    for a in sorted(agents, key=lambda r: r["country_code"]):
        err = a.get("error") or ""
        err = (err[:30] + "...") if len(err) > 30 else err
        print(
            f"{a['country_code']:12s} "
            f"{(a.get('character_name') or '-'):20s} "
            f"{str(a['committed']):10s} "
            f"{str(a.get('action_type') or '-'):24s} "
            f"{(a.get('duration_s') or 0):6.1f} "
            f"{(a.get('tool_calls') or 0):5d} "
            f"{err}"
        )

    # action type distribution
    action_dist = Counter(
        a.get("action_type") or "(none)" for a in agents
    )
    print("\n--- Action-type distribution ---")
    for action, n in action_dist.most_common():
        print(f"  {action:24s} {n}")

    # combat detection: declare_attack commits
    combat_events = sum(
        1 for a in agents if a.get("action_type") == "declare_attack"
    )

    durations = [
        a["duration_s"] for a in agents if a.get("duration_s")
    ]
    avg_dur = sum(durations) / len(durations) if durations else 0
    max_dur = max(durations) if durations else 0
    min_dur = min(durations) if durations else 0

    print("\n--- Totals ---")
    print(f"  Total wall-clock:    {total:6.1f}s")
    print(f"  Summary.total_s:     {summary['total_duration_s']:6.1f}s")
    print(f"  Successes:           {successes}/{len(agents)} "
          f"({100*successes/max(len(agents),1):.0f}%)")
    print(f"  Failures:            {failures}/{len(agents)}")
    print(f"  Combat declared:     {combat_events}")
    print(f"  Per-agent duration:  min={min_dur:.1f}s "
          f"avg={avg_dur:.1f}s max={max_dur:.1f}s")

    res = summary.get("resolution") or {}
    print("\n--- Round resolution handoff ---")
    print(f"  resolved: {res.get('resolved')}")
    if not res.get("resolved"):
        print(f"  reason:   {res.get('reason')}")
    else:
        print(f"  result:   {res.get('result')}")

    print("\n" + "=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
