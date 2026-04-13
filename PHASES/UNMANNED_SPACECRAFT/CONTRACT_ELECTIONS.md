# CONTRACT: Elections (Nominations, Voting, Resolution)

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §6.5a, §6.5b, §6.5c

---

## 1. PURPOSE

Three player-facing election actions for Columbia participants:
1. **Nominate** — self-nominate for a contested seat (parliament) or presidency
2. **Vote** — cast a secret ballot for a nominated candidate
3. **Resolve** — count participant votes + population votes → determine winner

Elections apply to Columbia (Template v1.0). Ruthenia elections follow a
separate mechanic (wartime, forced by players).

---

## 2. SCHEMAS

### 2a. Nomination
```json
{
  "action_type": "submit_nomination",
  "role_id": "tribune",
  "election_type": "columbia_midterms",
  "election_round": 2
}
```
**Timing:** Must be submitted exactly 1 round before the election (round N-1 for election at round N).

### 2b. Vote
```json
{
  "action_type": "cast_vote",
  "voter_role_id": "dealer",
  "candidate_role_id": "tribune",
  "election_type": "columbia_midterms"
}
```
**Timing:** Must be cast during the election round.

### 2c. Resolution (orchestrator-triggered)
```json
{
  "election_type": "columbia_midterms",
  "ai_score": 42.5,
  "contested_seat_role": "volt"
}
```

---

## 3. CAMP SYSTEM

Each Columbia role belongs to a camp (Template v1.0):

| Camp | Roles |
|---|---|
| **president_camp** | dealer, volt, anchor, shadow, shield |
| **opposition** | tribune, challenger |

Camp determines how "other people" (population) votes are distributed.

---

## 4. VOTE COUNTING

### Participant votes
Each Columbia participant casts exactly 1 secret vote for a nominated candidate.
Only moderator can see individual votes. One vote per participant per election.

### Population votes ("other people")
- Total population votes = number of participant votes cast (ensures 50/50 balance)
- **president_camp** candidates share `ai_score%` of population votes (split evenly)
- **opposition** candidates share `(100 - ai_score)%` of population votes (split evenly)

### AI score
Calculated by existing `process_election()` formula from `engines/political.py`:
- Base 50 + economic performance + stability factor + war penalty + crisis penalty
  + oil penalty + political crisis penalty + foreign policy bonus
- Clamped [0, 100]

### Winner
Candidate with highest total (participant + population) votes wins.

---

## 5. ELECTION SCHEDULE (Template v1.0)

| Round | Election | Nominations | What's contested |
|---|---|---|---|
| R2 | `columbia_midterms` | R1 | One parliament seat (defined in scenario data) |
| R5 | `columbia_presidential` | R4 | Presidency |

---

## 6. OUTCOMES (this contract)

| Election | Winner effect |
|---|---|
| **Midterms** | Winner takes contested parliament seat. Parliament majority may change. |
| **Presidential** | Winner recorded. (HoS swap and power consequences deferred — separate contract.) |

No stability/support mechanical changes from election results in this contract.

---

## 7. DB TABLES

| Table | Purpose |
|---|---|
| `election_nominations` | Who nominated for which election. Unique per (sim_run, election, role). |
| `election_votes` | Secret ballots. Unique per (sim_run, election, voter). |
| `election_results` | Final outcome with full vote breakdown (participant + population + total). |

---

## 8. LOCKED INVARIANTS

1. Only Columbia participants can nominate and vote
2. Nominations exactly 1 round before election
3. One nomination per role per election (no duplicates)
4. One vote per participant per election (secret ballot)
5. Only nominated candidates can receive votes
6. Population votes = participant vote count (50/50 balance)
7. Population votes distributed by camp (president_camp / opposition)
8. Winner = highest total votes (plurality)
9. All three phases logged to `observatory_events`
10. Vote choice NOT revealed in observatory events (secret ballot — only moderator sees via DB)
