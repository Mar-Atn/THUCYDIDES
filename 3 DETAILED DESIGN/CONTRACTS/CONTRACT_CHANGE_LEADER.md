# CONTRACT: Change Leader (Leadership Change)

**Version:** 1.0 | **Date:** 2026-04-15 | **Status:** LOCKED
**Replaces:** CONTRACT_COUP.md, CONTRACT_MASS_PROTEST.md

---

## 1. Overview

When a country's stability drops to a critical level, any citizen of that country can initiate a leadership change. This replaces the old probability-based coup and protest mechanics with a deterministic, team-vote system.

## 2. Preconditions

- Country must have **3 or more active roles** (solo countries cannot have leadership changes)
- Country stability must be **≤ 4.0** (configurable threshold, stored on template as `change_leader_threshold`)
- Initiator must be a **non-HoS citizen** of the country
- Initiator must have `change_leader` in their `role_actions`

## 3. Phase 1 — Initiation

**Who:** Any non-HoS role with `change_leader` action (Military, Economy, Diplomat, Security, Opposition).

**Action schema:**
```json
{
  "action_type": "change_leader",
  "role_id": "ironhand",
  "country_code": "sarmatia",
  "round_num": 3
}
```

**Effect:**
- All citizens of the country receive a notification: "A leadership change has been initiated in [Country]."
- A 10-minute timer starts (or until end of round, whichever is earlier).
- Phase 2 begins immediately.

## 4. Phase 2 — Removal Vote

**Who votes:** All citizens of the country, including the current HoS.

**Vote options:** YES (remove current HoS) or NO (keep current HoS).

**Resolution:**
- Count only non-HoS votes for the decision
- HoS vote is recorded but does not affect the outcome
- Need **strict majority of non-HoS citizens** to remove:
  - 3 roles (2 non-HoS): need 2 YES
  - 4 roles (3 non-HoS): need 2 YES
  - 5 roles (4 non-HoS): need 3 YES
  - 7 roles (6 non-HoS): need 4 YES
- **Equal votes → NO CHANGE** (HoS remains)
- **Timer expiry:** non-voters count as NO

**On removal:**
- Current HoS loses all HoS powers immediately
- Current HoS position_type reverts to `other` (ordinary citizen)
- All power assignments for the country are vacated
- Public event: "[Character] has been removed as Head of State of [Country]"
- Phase 3 begins immediately

**On failure (no majority):**
- Nothing happens. No penalty for initiator. No public announcement.
- Cannot re-initiate in the same round.

## 5. Phase 3 — Election of New HoS

**Trigger:** Only if Phase 2 succeeded (HoS removed).

**Who votes:** ALL citizens of the country, including the former HoS.

**Vote:** Each citizen selects one candidate from the list of ALL citizens (including themselves and the former HoS).

**Resolution:**
- Need **absolute majority** of total votes:
  - 3 roles: need 2 votes
  - 4 roles: need 3 votes
  - 5 roles: need 3 votes
  - 7 roles: need 4 votes
- **Winner:** becomes HoS immediately with full powers
- **No majority (split vote):** country remains leaderless until:
  - A new vote is triggered next round (if stability still ≤ threshold)
  - Moderator intervenes
- **Timer expiry:** non-voters are excluded from the count

**On new HoS elected:**
- Winner's `position_type` changes to `head_of_state`
- Winner's previous type is vacated (team loses that specialist)
- Winner receives all HoS actions immediately
- Winner can immediately reassign power types, make arrests, etc.
- Public event: "[Character] has been elected Head of State of [Country]"

## 6. Leaderless Country

If Phase 3 fails to produce a majority:
- Country has no HoS
- No one can perform HoS-only actions (arrest, reassign types, martial law, nuclear test initiation)
- Military, Economy, Diplomat, Security continue to function normally with their own actions
- The situation persists until a new leadership vote succeeds or moderator intervenes

## 7. Constraints

- Only one leadership change attempt per country per round
- Cannot be initiated in Round 1 (countries need at least one round to establish dynamics)
- The threshold is checked at initiation time (not continuously)
- If stability rises above threshold during the vote, the vote still completes

## 8. Implementation Notes

### M9 (Template level):
- `change_leader` action in `role_actions` table for all non-HoS types
- `change_leader_threshold` parameter in template schedule/config (default: 4.0)

### M1 (Engine level):
- Stability calculation continues as before
- Remove old coup/protest probability calculations
- Context blocks show "leadership change enabled" when stability ≤ threshold

### M2 (Communication level):
- Action schema for `change_leader` initiation
- Event types: `change_leader_initiated`, `change_leader_vote_removal`, `change_leader_vote_election`, `change_leader_resolved`
- Dispatcher routes to change_leader handler

### M4 (Sim Runner level):
- Real-time notification system for country citizens
- Vote collection with 10-minute timer
- Two-phase resolution (removal → election)
- Moderator visibility of vote progress and results
- WebSocket events for live updates

## 9. Deprecated Actions

The following actions are **deprecated** as of 2026-04-15:
- `coup_attempt` — replaced by change_leader Phase 2
- `lead_protest` — replaced by change_leader Phase 2

The following contracts are **superseded**:
- `CONTRACT_COUP.md` — superseded by this contract
- `CONTRACT_MASS_PROTEST.md` — superseded by this contract
