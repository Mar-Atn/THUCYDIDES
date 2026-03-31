# LLM Architecture Test -- Analysis Report
**Date:** 2026-03-27
**Architecture:** Role-brief-driven agent deliberation (no API calls; sophisticated heuristics reading actual role briefs)
**Rounds:** 8 | **Seed:** 42 | **Output:** `test_results/llm_test_1/`

---

## Executive Summary

The simulation ran 8 rounds (H2 2026 -- H1 2030) using a role-brief-driven decision architecture where each team's choices follow from their parsed objectives, ticking clocks, and internal dynamics. Key outcomes:

- **The Thucydides Trap materialized**: GDP gap ratio closed from 0.727 to 0.858. Cathay surpassed Columbia in naval strength by Round 2 and reached 1.27x naval superiority by Round 8.
- **Both wars persisted**: Neither the Eastern Europe nor Mashriq conflict resolved. No nuclear weapons were used.
- **No Formosa crisis triggered**: Despite Cathay reaching naval parity in Round 2 and sustained superiority thereafter, the Helmsman's deliberation model kept the Formosa window score below the blockade threshold until Round 5, then escalated to gray zone operations -- but never crossed into full blockade.
- **Columbia's stability eroded**: From 7.0 to 4.4 by Round 8, driven by sustained war costs and overstretch.
- **Multiple stability crises**: Sarmatia, Ruthenia, Persia, Phrygia, Caribe, Choson, and Levantia all fell below stability 2.0.
- **Oil price stable at ~$98**: Gulf Gate blockade maintained throughout by Persia.

---

## Round-by-Round Summary

| Round | Period | Oil | Gap Ratio | Naval Ratio | Deals | Combat | Key Event |
|-------|--------|-----|-----------|-------------|-------|--------|-----------|
| 1 | H2 2026 | $98 | 0.727 | 0.88 | 16 | 4 | Columbia strikes Persia. Sarmatia attacks Ruthenia. |
| 2 | H1 2027 | $98 | 0.751 | 1.00 | 18 | 8 | **Naval parity reached.** Columbia midterms. Cathay cyber succeeds on Columbia. |
| 3 | H2 2027 | $98 | 0.769 | 1.08 | 17 | 10 | Ruthenia wartime election. Cathay disinfo on Formosa succeeds. |
| 4 | H1 2028 | $98 | 0.783 | 1.14 | 17 | 10 | Ruthenia runoff. Gallia extends nuclear umbrella to Ruthenia. |
| 5 | H2 2028 | $98 | 0.798 | 1.19 | 18 | 9 | **Columbia presidential election.** Persia engagement signal to Columbia. |
| 6 | H1 2029 | $98 | 0.834 | 1.22 | 20 | 10 | **Sarmatia captures ruthenia_2.** Ruthenia explores peace back-channel. |
| 7 | H2 2029 | $98 | 0.856 | 1.25 | 17 | 11 | Sarmatia captures territory again. Persia retaliates on Levantia. |
| 8 | H1 2030 | $98 | 0.858 | 1.27 | 18 | 10 | Sarmatia secures position. Columbia stability at 4.4. |

---

## Key Dynamics Observed

### 1. The Thucydides Trap

The central mechanic performed as designed. Cathay's gap ratio closed steadily:
- **GDP**: Cathay grew from ~200 to 304 (+52%), while Columbia grew from ~280 to 354 (+26%). Cathay's higher base growth rate (~4%) compounded against Columbia's ~2%.
- **Naval**: Cathay's accelerated naval production (55% of military budget allocated to navy) overtook Columbia by Round 2. By Round 8, Cathay had 56 naval units vs Columbia's 44.
- **AI tech**: Both nations invested heavily in AI R&D. Columbia's starting advantage (L3 vs L2) created ongoing competition.

**Helmsman's Formosa calculation** (visible in reasoning files) shows the window score climbing from ~0.5 in Round 1 to 0.7+ by Round 5, triggering gray zone escalation. The model correctly held back from blockade despite naval superiority because the combined score required Columbia distraction + age urgency + economic trajectory alignment.

### 2. Eastern Europe Theater (Sarmatia vs Ruthenia)

The war ground on for all 8 rounds, producing the most consequential territorial change:
- **Sarmatia** maintained offensive pressure (4 units/round attacks), winning by attrition
- **Ruthenia** requested and received Western arms each round but could not match Sarmatia's production
- **Round 6-8**: Sarmatia captured territory as Ruthenia's military depleted
- **Pathfinder's deal window**: Probed Columbia for a grand bargain every round from R2 onward, but Columbia consistently rejected (deal likelihood never reached threshold)
- **Ironhand's attrition warning**: By mid-game, attrition exceeded replacement rate, but Pathfinder pushed attacks anyway
- **Ruthenia support**: Fell below 40% by Round 4, triggering Broker's back-channel exploration

### 3. Mashriq Theater (Columbia vs Persia)

Persia's Gulf Gate blockade was the defining mechanic:
- **Blockade maintained all 8 rounds**: Ground-based blockade kept oil prices at ~$98 (22% above baseline)
- **Columbia air strikes**: Hit Persia each round but couldn't break ground blockade
- **Levantia covert ops**: Mixed success against Persia nuclear program
- **Anvil vs Furnace**: Anvil dominated early rounds (R1-2), Furnace consolidated theological authority by R3+
- **Dawn's engagement push**: Only succeeded in reaching Columbia in R5-6 when economy hit "strained"
- **Nuclear R&D**: Persia invested 60% of tech budget in nuclear after R3 (Furnace's directive)

### 4. Columbia Internal Dynamics

The 7-role team model produced realistic internal tension:
- **Dealer (R1-4)**: Pursued all heritage targets simultaneously. Legacy urgency climbed from 0.6 to 0.9.
- **Shield**: Consistently warned of overstretch. Kept military budget at 40% when theater count stayed at 1.
- **Shadow**: Flagged Cathay naval parity as "dangerous" from Round 2 onward. Recommended Pacific pivot.
- **Anchor vs Volt**: Anchor pushed Caribe action, Volt pushed isolationism. Tension "high" from mid-game.
- **Tribune**: Never gained opposition majority (support stayed above 45%), limiting opposition leverage.
- **Budget evolution**: Social spending maintained near baseline (27-30%), preventing stability collapse until late game.

### 5. European Unity and Divisions

The EU unanimity mechanic with Ponte blocking produced realistic Alliance dynamics:
- **Ponte blocked** Sarmatia sanctions tightening ~30% of rounds, forcing reduced Ruthenia aid packages
- **Teutonia**: Gradual rearmament (military spending climbed from 15% to 20% over 8 rounds)
- **Gallia/Lumiere**: Extended nuclear umbrella to Ruthenia by Round 4 -- significant independent action
- **Freeland/Sentinel**: Pushed maximum security throughout, spending 30% on military
- **Albion/Mariner**: Consistent intelligence sharing with Columbia (executed every round)

### 6. Solo Country Highlights

- **Bharata**: Maintained non-alignment, trading with both Columbia and Cathay. GDP grew from 40 to 75 -- strongest growth percentage.
- **Levantia**: Sustained covert ops against Persia but stability collapsed to 1.3 (suspicious coherence flag: high support with low stability)
- **Formosa**: Quiet defense buildup, semiconductor leverage maintained
- **Phrygia**: Played all sides aggressively, stability collapsed
- **Solaria**: OPEC normal production, investment in Columbia
- **Choson**: Missile test in Round 6, stability at 1.2
- **Caribe**: Sought Cathay and Sarmatia patronage, stability collapsed

---

## Architecture Assessment

### What Role-Brief-Driven Decisions Produce (vs Simple Heuristics)

| Dimension | Old Heuristic Architecture | LLM Agent Architecture |
|-----------|---------------------------|----------------------|
| **Objective tracking** | Fixed aggression/deal parameters | Parsed from role brief text, evaluated against world state |
| **Ticking clocks** | Not modeled | Helmsman's age, Dealer's term limit, Pathfinder's deal window |
| **Internal dynamics** | Single HoS decides | Multi-role deliberation with faction conflict |
| **Budget reasoning** | Generic war/peace split | Shield's overstretch vs Volt's isolationism vs Anchor's hawkishness |
| **Formosa timing** | Static probability | 5-factor window score (naval ratio, distraction, age, trajectory, time) |
| **Negotiation logic** | Random proposals | Strategic assessment: deal window + urgency + leverage |
| **EU mechanics** | Generic European behavior | Unanimity with Ponte blocking, per-country national interests |
| **Reasoning trail** | None | Full JSON reasoning per team per round |

### Identified Issues for Next Iteration

1. **Stability floor**: Several countries hit stability 1.0 and stay there. Need to model regime collapse/change at stability <2.
2. **Oil price stickiness**: Price locked at ~$98 after Gulf Gate blockade. Needs more dynamic OPEC/demand response.
3. **Levantia coherence flag**: Support 95% with stability 1.3 -- autocracy support formula needs review.
4. **War resolution**: Neither war ended. Need more sophisticated peace deal mechanics and war exhaustion thresholds.
5. **Cathay Formosa**: Despite naval superiority from Round 2 and window score >0.7, never triggered blockade. The threshold may be too conservative.
6. **Election impact**: Elections were processed but their outcomes did not visibly change agent behavior. Need post-election policy shifts.

---

## Data Files

Results saved to `test_results/llm_test_1/`:

```
llm_test_1/
  initial_world_state.json
  final_world_state.json
  simulation_results.json
  round_1/ through round_8/
    round_N_world_state.json    -- complete world state
    round_N_actions.json        -- all agent decisions
    round_N_combat.json         -- combat results
    round_N_deals.json          -- negotiation outcomes
    round_N_narrative.txt       -- engine narrative
    round_N_summary.txt         -- printed round summary
    round_N_team_reasoning/     -- per-team reasoning trails (16 files)
```

Each team reasoning file contains: assessments, role positions, internal dynamics, and the final decision rationale.

---

## Source Files

- **Orchestrator**: `ENGINE/llm_orchestrator.py` -- round loop, engine coordination, output generation
- **Agent Runner**: `ENGINE/llm_agent_runner.py` -- role brief parsing, strategic assessment, team deliberation
- **Existing Engines**: `world_model_engine.py`, `live_action_engine.py`, `transaction_engine.py`, `world_state.py`
- **Role Briefs**: `role_briefs/COLUMBIA_ROLES.md` through `EUROPE_ROLES.md`
