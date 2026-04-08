# Round Engine — Spec Compliance (Phase 1 MVP)

**Source spec:** `1. CONCEPT/CONCEPT V 2.0/CON_C2_ACTION_SYSTEM_v2.frozen.md`
**Observatory spec:** `CONCEPT TEST/OBSERVATORY_SPEC_v0_1.md`
**Phase:** 1 — Unmanned Spacecraft MVP
**Date:** 2026-04-05

---

## Combat Rules

| Rule | Status | Notes |
|---|---|---|
| Ground combat RISK-style (3 atk dice vs 2 def dice) | Implemented | `combat.resolve_ground_combat` |
| Highest-die pair comparison, attacker loses ties | Implemented | |
| Defender +1 terrain (land_contested / die_hard) | Implemented | Via `hex_context.terrain` |
| Attacker +1 air superiority | Implemented | Via `hex_context.air_superiority` |
| Attacker +1 amphibious 3:1 ratio | Implemented | Via `hex_context.amphibious_3to1` |
| Air strike (60% base) | Implemented | `combat.resolve_air_strike` |
| AD absorbs strikes (-15% per active AD) | Implemented | |
| AD depletes after 3 strikes | Implemented | Tracked per unit via `ad_strikes_absorbed` |
| Air superiority bonus (+10% per unit) | Implemented | |
| Missile strike (50% base, 30% if AD) | Implemented | `combat.resolve_missile_strike` |
| Nuclear L1 (tactical) | Deferred | Phase 2 — will need troop-loss + economy hooks |
| Nuclear L2 (strategic) | Deferred | Phase 2 |
| Nuclear global stability shock | Deferred | Phase 2 |
| Naval ship-vs-ship dice | Implemented (basic) | `combat.resolve_naval`, +1 per unit advantage (cap +3) |
| Amphibious 3:1 ratio check | Implemented (basic) | Not Formosa-special-cased (4:1) |
| Formosa 4:1 amphibious | Deferred | Phase 2 |
| Blockade declaration | Deferred | Phase 2 |
| Blockade economic cascade (-10% GDP/round) | Deferred | Requires economic engine |

## Movement

| Rule | Status | Notes |
|---|---|---|
| Ground move to adjacent land hex | Implemented (simplified) | `movement.resolve_movement`, max 1 hex |
| Naval move between adjacent sea hexes | Implemented (simplified) | Max 2 hex range, terrain NOT validated |
| Air unit range up to 3 hops | Implemented | |
| Mobilize reserve to active (optional move) | Implemented | `movement.resolve_mobilization` |
| Terrain validation (land vs sea hex) | Deferred | Phase 2 — needs hex terrain map |
| Movement cost by terrain | Deferred | Phase 2 |

## R&D

| Rule | Status | Notes |
|---|---|---|
| Nuclear R&D: amount/10 -> progress; 1.0 = +1 level | Implemented | `rd.apply_rd_investment` |
| AI R&D: amount/10 -> progress; 1.0 = +1 level | Implemented | |

## Economic

| Rule | Status | Notes |
|---|---|---|
| Sanctions / tariffs (log only) | Implemented | Events written, no GDP effect |
| Sanctions → GDP cascade | Deferred | Phase 2 — economic engine |
| Tariffs → trade disruption | Deferred | Phase 2 |

## Resolution Order (per spec §Combat Engine)

The orchestrator `resolve_round.resolve_round` executes:

1. Diplomatic actions (log only to `observatory_events`) — Implemented
2. Movement + mobilization — Implemented
3. Ranged strikes (air, missile) — Implemented (resolved before ground)
4. Ground combat — Implemented
5. Naval engagements — Implemented (basic)
6. R&D increments — Implemented
7. Sanctions/tariffs (log only) — Implemented

## Persistence

| Target | Status |
|---|---|
| `unit_states_per_round` snapshot | Implemented (upsert on composite key) |
| `country_states_per_round` snapshot | Implemented |
| `observatory_combat_results` combat log | Implemented (renamed from spec `combat_results` — name taken) |
| `observatory_events` activity feed | Implemented |
| `round_states` status transitions (resolving → completed) | Implemented |

## Known Gaps / Follow-ups

- **No hex terrain data** — `hex_context.terrain` is plumbed but always empty until a terrain map is wired.
- **No `round_num` column on `agent_decisions`** — the resolver filters by `action_payload.round_num` as a convention. Adding a column would be cleaner (deferred per guardrail: do not modify existing tables).
- **Table name divergence**: spec calls the log `combat_results`; that table name was already in use with a different schema (`sim_run_id`, `zone_id`, `modifiers`), so this engine writes to `observatory_combat_results`. The Observatory UI must read from `observatory_combat_results`.
- **Defender auto-classification for attacks** — any enemy unit on the target hex is considered a defender. Nuanced targeting (e.g., strike infrastructure specifically) is Phase 2.
- **Stochastic tests** — dice-based modules should have Layer 1 tests with fixed `random.seed()` in `/app/tests/layer1/round_engine/`.
