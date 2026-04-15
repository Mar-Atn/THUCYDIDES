# Simplification Change Plan

**Date:** 2026-04-15 | **Status:** IN PROGRESS
**Approach:** Make all changes, then test and clean

---

## Changes to make

### A. Drop political_support (use stability only)
- [ ] `engine/models/db.py` — mark field deprecated, keep for now
- [ ] `engine/engines/political.py` — stop calculating political_support
- [ ] `engine/engines/round_tick.py` — stop writing political_support
- [ ] `engine/engines/orchestrator.py` — stop writing political_support
- [ ] `engine/services/coup_engine.py` — REPLACED by change_leader (Step E)
- [ ] `engine/services/protest_engine.py` — REPLACED by change_leader (Step E)
- [ ] `engine/services/assassination_engine.py` — martyr effect: shift stability instead of support
- [ ] `engine/services/election_meddling_engine.py` — shift stability instead of support
- [ ] `engine/context/blocks.py` — remove support from context display (4 places)
- [ ] `engine/agents/profiles.py` — stop loading political_support from CSV
- [ ] `frontend/src/components/template/TabCountries.tsx` — remove political_support field
- [ ] `frontend/src/lib/queries.ts` — remove from Country interface

### B. Drop personal_coins
- [ ] `engine/models/db.py` — mark field deprecated
- [ ] `engine/services/transaction_validator.py` — remove personal scope validation
- [ ] `engine/agents/profiles.py` — stop loading personal_coins
- [ ] `engine/agents/decisions.py` — remove personal transaction logic
- [ ] `frontend/src/components/template/TabRoles.tsx` — remove personal_coins field
- [ ] `frontend/src/lib/queries.ts` — remove from Role interface

### C. Simplify agreement types (4) + relation types (6)
- [ ] Define canonical types:
  - Agreements: Military Alliance, Trade Agreement, Peace Treaty, Ceasefire
  - Relations: Alliance, Economic Partnership, Neutral, Hostile, At War, Strategic Rival
- [ ] `engine/services/agreement_engine.py` — constrain to 4 types
- [ ] `engine/services/agreement_validator.py` — validate 4 types only
- [ ] Automatic relation transitions (new logic):
  - Sign Military Alliance → relation = Alliance
  - Sign Trade Agreement → relation = Economic Partnership (unless Alliance exists)
  - Sign Peace Treaty → relation = Neutral (from War/Hostile)
  - Sign Ceasefire → relation = Hostile (from War)
  - Any attack action → relation = At War
  - 3 rounds no attacks → War downgrades to Hostile automatically
  - Preset: Cathay-Columbia = Strategic Rival

### D. Simplified leadership change (replaces coup + protest)
- [ ] New action: `change_leader` — any team member can initiate when stability < threshold
- [ ] Requires simple majority of real participants in that country
  - 3-person team: 2 votes needed
  - 4-person team: 3 votes needed
  - Solo countries: N/A (no team to vote)
- [ ] On success: initiator becomes HoS, old HoS becomes their type
- [ ] On failure: nothing happens (no arrest, no penalty)
- [ ] Replaces: coup_attempt, lead_protest actions
- [ ] `engine/services/coup_engine.py` — rewrite as change_leader_engine
- [ ] `engine/services/protest_engine.py` — remove (merged into change_leader)
- [ ] `engine/agents/action_schemas.py` — add change_leader, remove coup_attempt/lead_protest
- [ ] `engine/services/action_dispatcher.py` — update routing

### E. Columbia elections (9+2 votes, simple majority)
- [ ] 7 Columbia roles: each gets 1 vote
- [ ] 2 Opposition roles: each gets 2 votes
- [ ] 2 AI votes based on stability indicator
- [ ] Total: 11 votes, simple majority = 6 wins
- [ ] `engine/services/election_engine.py` — rewrite vote counting
- [ ] Remove camp system, population votes, ai_score calculation

### F. DB schema changes (do last, after engine changes)
- [ ] `countries` table: political_support → deprecated (don't drop yet)
- [ ] `roles` table: personal_coins → deprecated (don't drop yet)
- [ ] `role_actions` table: already updated for new action types
- [ ] Update agreement/relationship enums if constrained

---

## Files touched per change

| File | A | B | C | D | E |
|------|---|---|---|---|---|
| engine/models/db.py | X | X | | | |
| engine/engines/political.py | X | | | | |
| engine/engines/round_tick.py | X | | | | |
| engine/engines/orchestrator.py | X | | | | |
| engine/services/coup_engine.py | X | | | X | |
| engine/services/protest_engine.py | X | | | X | |
| engine/services/assassination_engine.py | X | | | | |
| engine/services/election_meddling_engine.py | X | | | | |
| engine/services/agreement_engine.py | | | X | | |
| engine/services/agreement_validator.py | | | X | | |
| engine/services/transaction_validator.py | | X | | | |
| engine/services/action_dispatcher.py | | | | X | |
| engine/services/election_engine.py | | | | | X |
| engine/agents/action_schemas.py | | | | X | |
| engine/agents/profiles.py | X | X | | | |
| engine/agents/decisions.py | | X | | | |
| engine/context/blocks.py | X | | | | |
| frontend TabCountries.tsx | X | | | | |
| frontend TabRoles.tsx | | X | | | |
| frontend queries.ts | X | X | | | |
