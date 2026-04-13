# DET — Elections (Nominations, Voting, Resolution)

**Version:** 1.0 | **Status:** Active | **Date:** 2026-04-13
**Source contracts:** `CONTRACT_ELECTIONS.md` (locked), `CONTRACT_EARLY_ELECTIONS.md` (locked)
**Implementation:** `engine/services/election_engine.py`, `engine/engines/political.py`
**Formula reference:** `CARD_FORMULAS.md` B.4 Elections

---

## 1. PURPOSE

Elections are a core political mechanic for Columbia (Template v1.0). They provide the primary democratic mechanism through which participants compete for parliamentary seats and the presidency. The system consists of three phases:

1. **Nomination** -- self-nominate for a contested seat or presidency
2. **Voting** -- secret ballot by Columbia participants
3. **Resolution** -- count participant votes + population votes (AI-driven) to determine winner

Elections combine participant agency (direct votes) with simulated population behavior (AI score distributed by camp affiliation). This creates a 50/50 balance between player choice and world-state consequences.

Ruthenia elections follow a wartime variant triggered by player action, not a fixed schedule.

---

## 2. ELECTION SCHEDULE

Template v1.0 defines the following election schedule:

| Round | Election Type | Country | Nominations Round | What Is Contested |
|---|---|---|---|---|
| R2 | `columbia_midterms` | Columbia | R1 | One parliament seat (defined in scenario data) |
| R5 | `columbia_presidential` | Columbia | R4 | Presidency |
| -- | `ruthenia_wartime` | Ruthenia | -- | Not scheduled. Triggered by HoS voluntarily, or 2+ Ruthenian participants demand it, or full Ruthenian team consensus. One-off event. |

Midterm and presidential elections are automatic (triggered by the orchestrator at the designated round). Ruthenia wartime elections are triggered via the early elections mechanic (see section 10).

---

## 3. CAMP SYSTEM

Each Columbia role belongs to exactly one camp. Camp determines how population votes are distributed.

| Camp | Roles | Count |
|---|---|---|
| **president_camp** | dealer, volt, anchor, shadow, shield | 5 |
| **opposition** | tribune, challenger | 2 |

Camp assignment is fixed per Template v1.0. It is defined in code as:

```python
COLUMBIA_CAMPS = {
    "dealer": "president_camp",
    "volt": "president_camp",
    "anchor": "president_camp",
    "shadow": "president_camp",
    "shield": "president_camp",
    "tribune": "opposition",
    "challenger": "opposition",
}
```

All 7 Columbia roles are eligible to both nominate and vote.

---

## 4. NOMINATION MECHANICS

### Timing

Nominations must be submitted exactly 1 round before the election:
- R1 for R2 midterms
- R4 for R5 presidential

The engine enforces: `round_num == election_round - 1`. Any other round is rejected.

### Who Can Nominate

Any Columbia participant with an active role (`status == "active"`). Non-Columbia roles are rejected.

### Constraints

- One nomination per role per election (duplicate rejected)
- Camp is assigned automatically from role (not chosen by participant)

### Schema

```json
{
  "action_type": "submit_nomination",
  "role_id": "tribune",
  "election_type": "columbia_midterms",
  "election_round": 2
}
```

### Implementation

`election_engine.submit_nomination()` validates timing, role status, country, and uniqueness. On success, inserts into `election_nominations` and writes an observatory event of type `election_nomination`.

---

## 5. VOTING MECHANICS

### Secret Ballot

Votes are secret. Only the moderator can see individual vote choices via the database. Observatory events log that a vote was cast but do NOT reveal the candidate chosen.

### Constraints

- One vote per participant per election (duplicate rejected)
- Voter must be an active Columbia role
- Candidate must be a nominated candidate for that election
- Votes must be cast during the election round

### Schema

```json
{
  "action_type": "cast_vote",
  "voter_role_id": "dealer",
  "candidate_role_id": "tribune",
  "election_type": "columbia_midterms"
}
```

### Implementation

`election_engine.cast_vote()` validates voter status, candidate nomination, and uniqueness. On success, inserts into `election_votes` and writes an observatory event of type `election_vote_cast` (candidate NOT revealed in event payload).

---

## 6. RESOLUTION FORMULA

Resolution is orchestrator-triggered (not a player action). The formula combines participant votes with AI-driven population votes.

### Step 1: Count participant votes

Each vote cast by a Columbia participant counts as 1 vote for the chosen candidate.

```
participant_votes[candidate] = count of votes for that candidate
total_participant_votes = sum of all participant votes cast
```

### Step 2: Calculate population votes

Population votes represent "other people" (the broader electorate beyond participants).

```
population_vote_count = max(total_participant_votes, 1)
```

This ensures a 50/50 balance: the population pool equals the participant pool.

### Step 3: Distribute population votes by camp

The AI score (0-100) determines the split:

```
president_camp_population = (ai_score / 100) * population_vote_count
opposition_population     = (1 - ai_score / 100) * population_vote_count
```

Within each camp, population votes are split evenly among nominated candidates:

```
per_president_candidate = president_camp_population / count(president_camp candidates)
per_opposition_candidate = opposition_population / count(opposition candidates)
```

Candidates with unknown camp receive 0 population votes.

### Step 4: Total and winner

```
total_votes[candidate] = participant_votes[candidate] + population_votes[candidate]
winner = candidate with highest total_votes (plurality)
```

### Implementation

`election_engine.resolve_election()` performs this calculation. The `ai_score` is passed in as a parameter (computed by `process_election()` in `engines/political.py`).

---

## 7. AI SCORE CALCULATION

The AI score represents how the general population evaluates the incumbent government. Computed by `engines/political.py :: process_election()`.

### Input model: `ElectionInput`

| Field | Type | Description |
|---|---|---|
| `country_id` | str | Country code |
| `election_type` | str | `columbia_midterms`, `columbia_presidential`, `ruthenia_wartime`, `ruthenia_wartime_runoff` |
| `round_num` | int | Current round |
| `gdp_growth_rate` | float | Current GDP growth rate |
| `stability` | float | Current stability (1.0-9.0) |
| `economic_state` | str | `normal`, `stressed`, `crisis`, `collapse` |
| `oil_price` | float | Current oil price |
| `oil_producer` | bool | Whether country is an oil producer |
| `war_tiredness` | float | War tiredness score (0-10) |
| `wars` | list[dict] | Active wars the country is involved in |
| `events_log` | list[dict] | Political events (arrests, impeachments, ceasefires, etc.) |
| `incumbent_pct` | float | Player incumbent vote percentage (default 50.0) |

### Formula

```
econ_perf               = gdp_growth_rate * 10.0
stab_factor             = (stability - 5) * 5.0
war_penalty             = -5.0 per war involving the country
crisis_penalty          = 0 (normal), -5 (stressed), -15 (crisis), -25 (collapse)
oil_penalty             = -(oil_price - 150) * 0.1   [only if oil_price > 150 AND not oil_producer]
political_crisis_penalty= -5.0 per arrest in country - 10.0 per impeachment in country
foreign_policy_bonus    = +7.0 per ceasefire/agreement signed + 5.0 per territory capture

ai_score = clamp(
    50.0 + econ_perf + stab_factor + war_penalty + crisis_penalty
    + oil_penalty + political_crisis_penalty + foreign_policy_bonus,
    0.0, 100.0
)
```

### Modifier details

| Modifier | Source | Effect |
|---|---|---|
| **Economic performance** | `gdp_growth_rate * 10` | +10 per 1% growth |
| **Stability factor** | `(stability - 5) * 5` | Neutral at stability=5; +5 per point above, -5 per point below |
| **War penalty** | Each active war | -5 per war (attacker, defender, or allied) |
| **Economic crisis** | `economic_state` | 0 / -5 / -15 / -25 |
| **Oil shock** | `oil_price > 150`, non-producer | -(excess * 0.1) |
| **Arrests** | events_log type=arrest | -5 per arrest by incumbent |
| **Impeachments** | events_log type=impeachment | -10 per impeachment |
| **Ceasefire/Agreement** | events_log type=ceasefire/agreement | +7 per peace deal signed |
| **Territory capture** | events_log type=territory_capture | +5 per territorial gain |

### Final incumbent percentage (political.py legacy)

The `process_election()` function in `engines/political.py` also computes a legacy result:

```
final_incumbent = 0.5 * ai_score + 0.5 * player_incumbent_pct
incumbent_wins  = (final_incumbent >= 50.0)
```

This is used for automated resolution. In the player-facing election engine (`election_engine.py`), the `ai_score` alone is passed to `resolve_election()` which distributes population votes by camp (section 6).

### Ruthenia wartime adjustments

For `ruthenia_wartime` or `ruthenia_wartime_runoff` elections, additional modifiers apply:

```
territory_factor = -(count of occupied_zones) * 3    [for wars where Ruthenia is defender]
ai_score_adjusted = clamp(ai_score + territory_factor - war_tiredness * 2, 0, 100)
```

---

## 8. MIDTERM OUTCOMES

**Election type:** `columbia_midterms` (Round 2)

One parliament seat is contested (identified by `contested_seat_role` parameter). The winner takes that seat.

| Outcome | Effect |
|---|---|
| Winner is NOT the contested seat holder | `seat_changed` recorded. Winner replaces the role in the contested seat. Parliament majority may change. |
| Winner IS the contested seat holder | No change. Status quo maintained. |

In the `process_election()` legacy path:
- Opposition wins: Parliament becomes 3-2 opposition (Tribune + Challenger + NPC Seat 5)
- Incumbent wins: President's camp retains majority

No stability or support mechanical changes result from midterm outcomes in this contract.

---

## 9. PRESIDENTIAL OUTCOMES

**Election type:** `columbia_presidential` (Round 5)

The winner is recorded in `election_results`. The `process_election()` legacy path notes whether incumbent camp or opposition wins.

**Consequences deferred:** Head-of-State swap, power transfer, and downstream effects are specified in a separate contract. This contract only records the winner.

---

## 10. EARLY ELECTIONS

Any Head of State (HoS) can call early elections voluntarily. This is a deterministic action (no probability roll).

### Authorization

- Must be HoS (`is_head_of_state = true`)
- Role must be active (not arrested/killed/deposed)
- Rationale required (minimum 30 characters)

### Schema

```json
{
  "action_type": "call_early_elections",
  "role_id": "pathfinder",
  "country_code": "sarmatia",
  "rationale": "Public demands democratic renewal..."
}
```

### Effects

| What | Effect |
|---|---|
| `early_election_called` flag | Set to `true` on current round's `country_states_per_round` |
| Election timing | Orchestrator processes election in `round_num + 1` |
| Election engine | Uses same `process_election()` and `resolve_election()` as scheduled elections |
| Cost | None -- no stability/support cost for calling elections |

### Implementation

`engine/services/early_elections_engine.execute_early_elections()` sets the flag and logs an observatory event (`early_elections_called`). No `precomputed_rolls` needed (deterministic).

---

## 11. DB TABLES

### `election_nominations`

| Column | Type | Description |
|---|---|---|
| `id` | uuid (PK) | Auto-generated |
| `sim_run_id` | uuid (FK) | References `sim_runs.id` |
| `election_type` | text | `columbia_midterms`, `columbia_presidential`, etc. |
| `election_round` | int | Round when the election occurs |
| `role_id` | text | Nominating role (e.g., `tribune`) |
| `country_code` | text | Always `columbia` for Template v1.0 |
| `camp` | text | `president_camp` or `opposition` |
| `created_at` | timestamptz | Auto-generated |

**Unique constraint:** `(sim_run_id, election_type, role_id)` -- one nomination per role per election.

### `election_votes`

| Column | Type | Description |
|---|---|---|
| `id` | uuid (PK) | Auto-generated |
| `sim_run_id` | uuid (FK) | References `sim_runs.id` |
| `election_type` | text | Election identifier |
| `election_round` | int | Round when the vote is cast |
| `voter_role_id` | text | Who voted |
| `candidate_role_id` | text | Who they voted for (SECRET -- moderator only) |
| `country_code` | text | Always `columbia` for Template v1.0 |
| `created_at` | timestamptz | Auto-generated |

**Unique constraint:** `(sim_run_id, election_type, voter_role_id)` -- one vote per participant per election.

### `election_results`

| Column | Type | Description |
|---|---|---|
| `id` | uuid (PK) | Auto-generated |
| `sim_run_id` | uuid (FK) | References `sim_runs.id` |
| `election_type` | text | Election identifier |
| `election_round` | int | Round of the election |
| `country_code` | text | Always `columbia` for Template v1.0 |
| `winner_role_id` | text | Role that won the election |
| `ai_score` | float | AI incumbent score used for population vote distribution |
| `participant_votes` | jsonb | `{role_id: count}` -- participant vote breakdown per candidate |
| `population_votes` | jsonb | `{role_id: float}` -- population vote breakdown per candidate |
| `total_votes` | jsonb | `{role_id: float}` -- total (participant + population) per candidate |
| `seat_changed` | text | Midterms only: role_id of the seat that changed hands, or null |
| `created_at` | timestamptz | Auto-generated |

---

## 12. CROSS-REFERENCES

| Document | Relevance |
|---|---|
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_ELECTIONS.md` | Locked contract -- invariants, schemas, camp system, vote counting |
| `PHASES/UNMANNED_SPACECRAFT/CONTRACT_EARLY_ELECTIONS.md` | Locked contract -- HoS early election call |
| `PHASES/UNMANNED_SPACECRAFT/CARD_FORMULAS.md` B.4 | Formula summary for elections |
| `PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md` 6.6-6.7 | Action specifications (nominate, vote, resolve, early elections) |
| `app/engine/services/election_engine.py` | Implementation: nomination, voting, resolution |
| `app/engine/engines/political.py :: process_election()` | AI score formula (lines 449-565) |
| `app/engine/engines/political.py :: ElectionInput` | Input model (line 144) |
| `app/engine/engines/political.py :: ElectionResult` | Output model (line 166) |

---

*End of document.*
