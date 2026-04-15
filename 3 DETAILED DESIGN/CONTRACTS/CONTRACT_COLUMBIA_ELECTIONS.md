# CONTRACT: Columbia Elections

**Version:** 2.0 | **Date:** 2026-04-15 | **Status:** LOCKED
**Replaces:** CONTRACT_ELECTIONS.md v1.0 (old camp system + population votes)

---

## 1. Overview

Columbia holds two types of elections: mid-term (one parliament seat) and presidential. Both use the same voting mechanics. Elections are scheduled events defined in the template's key_events.

## 2. Election Schedule (Canonical Template v1.0)

| Round | Election | Contested |
|---|---|---|
| R2 | Mid-term parliamentary | Shadow's parliament seat |
| R6 | Presidential | Presidency (Dealer cannot run) |

Nominations must be submitted 1 round before the election (R1 for mid-term, R5 for presidential).

## 3. Voting Mechanics

### 3.1 Base Votes

All 7 Columbia citizens vote:
- 5 non-opposition roles: **1 vote each** = 5 votes
- 2 opposition roles: **2 votes each** = 4 votes
- **Base total: 9 votes**

### 3.2 Economy Bonus (AI-driven)

```
economy_score = (stability / 10) × 0.5 + max(0, 1 − inflation / 20) × 0.5
```

- If `economy_score < 0.5` → each Opposition role receives **+1 bonus vote** for this election
- If `economy_score ≥ 0.5` → no bonus

With bonus: opposition has 3 votes each (6 total), others have 1 each (5 total) = **11 total votes**. Opposition needs no allies to win.

Without bonus: opposition has 2 votes each (4 total), others have 1 each (5 total) = **9 total votes**. Opposition needs at least 1 ally to reach majority (5).

### 3.3 Resolution

- **Simple majority wins** (more than half of total votes cast)
- Without bonus: majority = 5 of 9
- With bonus: majority = 6 of 11
- Ties: no winner (seat remains vacant / HoS stays for presidential)

## 4. Mid-Term Election (Parliament)

### 4.1 What's Contested

One parliament seat (canonical: Shadow's seat). The specific seat is defined in the template's key_events.

### 4.2 Who Can Nominate

Any Columbia citizen can self-nominate **EXCEPT:**
- Current parliament members whose seats are NOT up for re-election (Volt, Tribune)
- Shadow CAN run to defend the seat

### 4.3 Process

1. **R1 (nominations round):** Eligible citizens submit `self_nominate` action
2. **R2 (election round):** All 7 citizens cast votes for one nominated candidate
3. **Resolution:** Simple majority wins the seat
4. **Winner:** Joins parliament (or retains seat if defending)
5. **If Shadow loses:** Shadow leaves parliament, winner takes the seat. Parliament composition changes.

### 4.4 Parliament Impact

Starting: Volt (Rep, chair), Shadow (Ind), Tribune (Dem) = 2 Rep-aligned : 1 Dem

If opposition wins Shadow's seat: Volt (Rep), [Opposition winner] (Dem), Tribune (Dem) = 1 Rep : 2 Dem → opposition controls parliament.

Parliament has constitutional rights (budget approval, treaty ratification) that the president can bypass — but at political cost.

## 5. Presidential Election

### 5.1 What's Contested

The presidency of Columbia.

### 5.2 Who Can Nominate

Any Columbia citizen can self-nominate **EXCEPT:**
- The current HoS (Dealer cannot run — term-limited)

### 5.3 Process

1. **R5 (nominations round):** Eligible citizens submit `self_nominate` action
2. **R6 (election round):** All 7 citizens cast votes for one nominated candidate
3. **Resolution:** Simple majority wins the presidency
4. **Winner:** Immediately becomes HoS with full powers
5. **Dealer:** Loses HoS status, becomes ordinary citizen (position_type → other)

## 6. Economy Score Calibration

Starting conditions (Columbia, Round 0):
- Stability: 7.0 → component = 0.35
- Inflation: ~3.5% → component = 0.4125
- **Starting score: ~0.76 (well above 0.5 — no bonus)**

Scenarios that trigger opposition bonus:
- Stability 3.0, inflation 10% → score = 0.15 + 0.25 = **0.40** (bonus)
- Stability 5.0, inflation 15% → score = 0.25 + 0.125 = **0.375** (bonus)
- Stability 4.0, inflation 8% → score = 0.20 + 0.30 = **0.50** (borderline, no bonus)

The bonus requires both stability decline AND inflation rise — a sustained economic/political crisis, not just one bad round.

## 7. Implementation Notes

### M9 (Template level):
- `self_nominate` and `cast_vote` actions in role_actions (2 votes for opposition, 1 for others) ✅ DONE
- Election rounds in key_events_defaults: R2 mid-term (nominations R1), R6 presidential (nominations R5)
- Parliament composition in org_memberships

### M1 (Engine level):
- Economy score calculation from stability + inflation
- Vote counting with bonus logic
- No old camp system or population vote formulas

### M2 (Communication level):
- Update CONTRACT_ELECTIONS.md → this contract
- Nomination and vote action schemas (existing, no change needed)

### M4 (Sim Runner level):
- Nomination collection during nominations round
- Vote collection during election round
- Timer management
- Result announcement
- HoS transition on presidential election win
- Parliament seat transition on mid-term win

## 8. Deprecated

- **Camp system** (president_camp, opposition) — removed
- **Population votes** — removed
- **AI score calculation** — replaced by economy_score bonus
- **50/50 participant/population split** — removed
