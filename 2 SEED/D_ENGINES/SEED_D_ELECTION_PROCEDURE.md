# TTT SEED -- Election Procedure (Tester Verification Guide)

**Version:** 1.0 | **Date:** 2026-03-27

---

## Scheduled Elections

Elections are defined in `world_state.py` under `SCHEDULED_EVENTS`:

| Round | Election | Country | Subtype |
|-------|----------|---------|---------|
| 2 | Columbia Midterms | columbia | `columbia_midterms` |
| 3 | Heartland Wartime Election | heartland | `heartland_wartime` |
| 4 | Heartland Wartime Runoff | heartland | `heartland_wartime_runoff` |
| 5 | Columbia Presidential | columbia | `columbia_presidential` |

Elections are processed automatically by the World Model Engine at the end of the specified round, inside `deterministic_pass()`.

---

## How Election Outcomes Are Determined

Each election uses a **50/50 split** between AI scoring and player votes:

```
final_incumbent_pct = 0.5 * ai_score + 0.5 * player_incumbent_pct
incumbent_wins = (final_incumbent_pct >= 50.0)
```

### AI Score (50% weight)

The AI score represents "popular sentiment" derived from gameplay outcomes:

```
ai_score = clamp(50.0 + econ_perf + stab_factor + war_penalty, 0, 100)
```

Where:
- **econ_perf** = `gdp_growth_rate * 10.0` (strong economy helps incumbent)
- **stab_factor** = `(stability - 5) * 5.0` (above-5 stability helps, below-5 hurts)
- **war_penalty** = `-5.0` per active war the country is involved in

For **Heartland wartime elections**, additional modifiers apply:
- **territory_factor** = `-3` per occupied zone (losing territory hurts incumbent)
- **war_tiredness** = `-2 * war_tiredness` (prolonged war erodes support)

### Player Votes (50% weight)

Passed in via `actions["votes"][country_id]["incumbent_pct"]`. This represents team-level voting during the round. Default is 50.0 if no votes submitted.

---

## What Happens When Incumbent Loses

### Columbia Midterms (Round 2)
- **Incumbent wins:** Parliament stays status quo (President's camp retains majority).
- **Incumbent loses:** Opposition wins Seat 5. Parliament flips to 3-2 opposition majority (Tribune + Challenger + NPC Seat 5). This blocks the President's budget unless they negotiate.

### Heartland Wartime Election (Rounds 3-4)
- **Incumbent wins (Beacon survives):** No change. Beacon continues as president.
- **Incumbent loses:** Beacon is replaced by Bulwark as president. This triggers a leadership change and potential policy shift (more hawkish or dovish depending on Bulwark's character).

### Columbia Presidential (Round 5)
- **Incumbent wins:** President's camp continues. No structural change.
- **Incumbent loses:** New president from opposition. Full leadership transition. New HoS role assignment.

---

## Tester Verification Steps

### 1. Confirm SCHEDULED_EVENTS are defined

In `world_state.py`, verify:
```python
SCHEDULED_EVENTS = {
    2: [{"type": "election", "subtype": "columbia_midterms", "country": "columbia"}],
    3: [{"type": "election", "subtype": "heartland_wartime", "country": "heartland"}],
    4: [{"type": "election", "subtype": "heartland_wartime_runoff", "country": "heartland"}],
    5: [{"type": "election", "subtype": "columbia_presidential", "country": "columbia"}],
}
```

### 2. Run a test round with elections

```python
from world_state import WorldState
from world_model_engine import WorldModelEngine

ws = WorldState()
ws.load_from_csvs("2 SEED/C_MECHANICS/C4_DATA")

engine = WorldModelEngine(ws)

# Test Round 2 (midterms)
actions = {"votes": {"columbia": {"incumbent_pct": 40.0}}}
results, narrative, flags = engine.process_round(ws, actions, round_num=2)

# Check election result
print(results["deterministic"]["elections"])
# Expected: columbia entry with incumbent_wins True or False
```

### 3. Verify election results appear in event log

```python
election_events = [e for e in ws.events_log if e["type"] == "election"]
assert len(election_events) > 0
print(election_events[-1])
```

### 4. Test edge cases

- **High GDP + high stability:** AI score should be well above 50, helping incumbent.
- **Low GDP + war + low stability:** AI score drops, incumbent likely loses.
- **Player votes at 0%:** Pure AI-driven result (halved).
- **Player votes at 100%:** Incumbent guaranteed to win unless AI score is 0.

### 5. Verify Heartland war modifiers

Set up Heartland with occupied zones and high war_tiredness, then run Round 3:
```python
ws.countries["heartland"]["political"]["war_tiredness"] = 5
actions = {"votes": {"heartland": {"incumbent_pct": 45.0}}}
results, _, _ = engine.process_round(ws, actions, round_num=3)
print(results["deterministic"]["elections"]["heartland"])
# Expect: incumbent_wins = False (war-weary, territory lost, low voter support)
```

---

## Code References

- **SCHEDULED_EVENTS:** `world_state.py`, line ~55
- **_process_election():** `world_model_engine.py`, line ~720
- **Election call site:** `world_model_engine.py`, line ~177 (inside `deterministic_pass`)
