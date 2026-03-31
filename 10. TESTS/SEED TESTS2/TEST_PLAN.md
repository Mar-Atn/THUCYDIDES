# SEED TESTS2 — Test Plan
**Date:** 2026-03-27 | **Tester:** Independent Claude Code Instance

---

## Test Battery (6 tests, 8 rounds each)

| # | Name | Objective | Key Watch Items |
|---|------|-----------|-----------------|
| 1 | **GENERIC BASELINE** | Full system integration. 37 independent AI agents. | Oil ~$140+ R1, Ruthenia stability >2.5 by R8, elections firing, ceasefire possible |
| 2 | FORMOSA CRISIS | Cathay naval window, semiconductor disruption | Naval crossover, Columbia overstretch, semiconductor GDP hit |
| 3 | GULF GATE ECONOMICS | Oil price under sustained blockade | Producer revenue, importer pain, blockade breaking incentive |
| 4 | PEACE NEGOTIATION | Ceasefire mechanic validation | Terms emergence, engine handling, war status update |
| 5 | STABILITY CALIBRATION | War country stability fix | Ruthenia ~2.5-3.0 R8, Sarmatia ~3.5-4.5, peaceful 6-8 |
| 6 | RARE EARTH + TECH RACE | Technology competition dynamics | R&D slowdown, breakthroughs, GDP multipliers |

---

## Test 1 Architecture: 37 Independent Agents

### Agent Roster (37 roles)

**Columbia Team (7):**
DEALER (HoS), VOLT (VP), ANCHOR (SecState), SHIELD (SecDef), SHADOW (CIA), TRIBUNE (Opposition), CHALLENGER (Candidate)

**Cathay Team (5):**
HELMSMAN (Chairman), RAMPART (Marshal), ABACUS (Premier), CIRCUIT (Tech), SAGE (Elder)

**Europe Team (6):**
LUMIERE (Gallia), FORGE (Teutonia), SENTINEL (Freeland), PONTE (Ponte), MARINER (Albion), PILLAR (EU)

**Sarmatia Team (3):**
PATHFINDER (President), IRONHAND (Marshal), COMPASS (Oligarch)

**Ruthenia Team (3):**
BEACON (President), BULWARK (General), BROKER (Politician)

**Persia Team (3):**
FURNACE (Supreme Leader), ANVIL (IRGC), DAWN (Reformist)

**Solo Countries (10):**
SCALES (Bharata), CITADEL (Levantia), CHIP (Formosa), BAZAAR (Phrygia), SAKURA (Yamato), WELLSPRING (Solaria), PYRO (Choson), VANGUARD (Hanguk), HAVANA (Caribe), SPIRE (Mirage)

### Round Execution Flow

```
EACH ROUND (×8):
│
├─ 1. WORLD BRIEFING — I generate state summary from engine data
│
├─ 2. TEAM DELIBERATION (parallel, 6 teams)
│   Each team agent receives: all role briefs + world state + team instructions
│   Returns: internal positions, proposed actions, meeting requests, negotiation targets
│
├─ 3. SOLO DELIBERATION (parallel, 10 agents)
│   Each solo agent receives: role brief + country seed + world state
│   Returns: proposed actions, meeting requests, negotiation targets
│
├─ 4. BILATERAL NEGOTIATIONS (sequential, highest priority first)
│   I pair agents based on their meeting requests
│   Each pair exchanges proposals/counterproposals (2-3 exchanges max)
│   Outcomes: deals, rejections, or no-deal
│
├─ 5. ORGANIZATION MEETINGS (if called)
│   NATO, BRICS+, OPEC+, EU, UNSC — members deliberate collectively
│
├─ 6. LIVE ACTIONS — I process military, covert, domestic actions via engine
│
├─ 7. TRANSACTIONS — I process all agreed deals via engine
│
├─ 8. SCHEDULED EVENTS — Elections (R2, R3-4, R5)
│
├─ 9. WORLD MODEL ENGINE — Batch processing (economic, political, tech, narrative)
│
├─ 10. DEPLOYMENT — Units placed from production/mobilization
│
└─ 11. SAVE — Round results to MD + data files
```

### Practical Batching (37 agents = heavy)

To manage 37 agents across 8 rounds:
- **Team countries**: 1 agent per team, playing all internal roles. The agent models faction dynamics and returns per-role positions + team consensus.
- **Solo countries**: 1 agent per country.
- **Total per round: 16 agents** (6 teams + 10 solos)
- **Negotiations**: Spawn paired agents for key bilaterals (up to 10 per round)
- **Org meetings**: Spawn dedicated agent for each called meeting

This gives us true independence (each country has its own Claude instance with only its own information) while keeping coordination manageable.

### What Each Agent Receives

1. **Role brief** (from B2_ROLES/) — full character, objectives, ticking clock
2. **Country seed** (from B1_COUNTRIES/) — national situation, resources, challenges
3. **World state summary** — GDP, military, stability, oil price, wars, alliances (PUBLIC info only)
4. **Country-specific intel** — what their role would know (classified info per role)
5. **Round instructions** — what decisions are due, deadlines, available actions
6. **Previous round outcomes** — what happened last round (if not R1)

### What Each Agent Returns (structured)

```json
{
  "role": "DEALER",
  "country": "columbia",
  "round": 1,
  "budget": {"social": 40, "military": 35, "tech": 15, "reserve": 10},
  "tariffs": {"cathay": 3, ...},
  "sanctions": {"persia": 3, ...},
  "military_actions": [{"type": "attack", "target": "persia_1", ...}],
  "diplomatic_proposals": [{"to": "sarmatia", "type": "ceasefire", ...}],
  "meeting_requests": ["NATO", "bilateral_with_ruthenia"],
  "transactions": [{"type": "coin_transfer", "to": "ruthenia", "amount": 5}],
  "covert_ops": [{"type": "espionage", "target": "cathay"}],
  "public_statements": ["Columbia stands with Ruthenia..."],
  "internal_notes": "Shield warns overstretch. Shadow flags Cathay naval buildup.",
  "reasoning": "..."
}
```

---

## Engine Configuration

- **Data path**: `2 SEED/C_MECHANICS/C4_DATA/`
- **Engine path**: `2 SEED/D_ENGINES/`
- **Starting conditions**: Gulf Gate blockade ACTIVE, oil ~$140+, 2 active wars
- **Naval balance**: Columbia 10 flat, Cathay 6+1/round
- **Stability decay**: Defenders -0.10/R, democratic resilience +0.15/R
- **Semiconductor**: formosa_dependency × severity → GDP hit (floor 50%)
- **Rare earth**: restriction_level × 0.15 → R&D slowdown (floor 40%)
- **Elections**: R2 Columbia midterms, R3-4 Ruthenia, R5 Columbia presidential

---

## Output Structure

```
SEED TESTS2/
├── TEST_PLAN.md                    ← This file
├── test_1_generic/
│   ├── round_1/
│   │   ├── world_state_r1.md       ← State at round start
│   │   ├── team_columbia_r1.md     ← Columbia team deliberation + decisions
│   │   ├── team_cathay_r1.md       ← Cathay team deliberation + decisions
│   │   ├── ... (all 16 agents)
│   │   ├── negotiations_r1.md      ← All bilateral exchanges
│   │   ├── engine_results_r1.md    ← Engine processing output
│   │   └── round_summary_r1.md     ← Round narrative
│   ├── round_2/ ... round_8/
│   ├── TEST_1_RESULTS.md           ← Full test analysis
│   └── TEST_1_DATA.json            ← Machine-readable results
├── test_2_formosa/ ... test_6_tech_race/
└── DASHBOARD.html                  ← Visual comparison across all tests
```

---

## Success Criteria (Test 1 — Generic Baseline)

| Metric | Expected Range | Red Flag |
|--------|---------------|----------|
| Oil price R1 | $130-160 | <$100 (blockade not working) |
| Oil price R8 | $90-180 (depends on blockade status) | Static 68-72 (old bug) |
| Ruthenia stability R3 | >3.0 | ≤1.0 (old decay bug) |
| Ruthenia stability R8 | 2.0-4.0 | <1.5 (still too fast) |
| Sarmatia stability R8 | 3.0-5.0 | <2.0 (autocracy resilience failing) |
| Columbia stability R8 | 5.0-7.5 | <4.0 (peaceful country shouldn't decay) |
| Cathay GDP growth | 3.0-5.0% | >6% (ceiling not working) |
| Gap ratio R8 | 0.80-1.00 | >1.10 (Cathay runaway) or <0.75 (no convergence) |
| Cathay naval R4 | 8-10 | <7 (growth not working) |
| Elections fired | R2, R3/4, R5 | Any missing |
| Nuclear use | 0 | >0 (deterrence should hold) |
| Ceasefire proposals | ≥1 by R6 | 0 (agents should attempt diplomacy) |
| Total negotiations | >80 | <40 (agents not engaging) |
| Total combat events | 20-60 | <10 (wars not active) or >100 (unrealistic) |

---

## Pre-Start Checklist

- [x] Engine code reviewed (world_state, world_model, live_action, transaction)
- [x] Data CSVs verified (countries, deployments, zones, sanctions, tariffs)
- [x] Role briefs available (37 roles in 7 files)
- [x] Country seeds available (16 files)
- [x] Election procedure documented
- [x] Ceasefire mechanic implemented
- [x] Oil price formula updated (blockade +80%)
- [x] Stability decay slowed (defender -0.10/R)
- [x] Semiconductor disruption in GDP calc
- [x] Rare earth restrictions in R&D calc
- [x] Gulf Gate blockade ACTIVE at start
- [x] Naval deployments on water hexes
- [x] Test output folder created
- [ ] **READY TO EXECUTE**
