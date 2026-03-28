# TTT Data Flows
## How Data Moves Through the System

**Version:** 1.0 | **Date:** 2026-03-28
**Status:** SEED Design (pre-implementation)
**Cross-references:** [F2 Data Architecture](SEED_F2_DATA_ARCHITECTURE_v1.md) | [F4 API Contracts](SEED_F4_API_CONTRACTS_v1.md) | [D Engine Interface](../D_ENGINES/SEED_D_ENGINE_INTERFACE_v1.md)

---

# 1. ROUND LIFECYCLE DATA FLOW

## Complete Round Flow

```
  +-----------------------------------------------------------------+
  |                        ROUND N START                             |
  |  Load: Snapshot(N-1) + Event Log                                |
  |  Derive: All DERIVED variables from CORE state                  |
  |  Push: Filtered dashboards to all participants                  |
  +-----------------------------------------------------------------+
                              |
                              v
  +-----------------------------------------------------------------+
  |                  PHASE A: FREE ACTION (Real-Time)                |
  |                  Duration: 30-60 minutes                         |
  |                                                                  |
  |  Participant ---[action]---> Backend                             |
  |      |                          |                                |
  |      |           +-----------------------------+                 |
  |      |           | Live Action Engine           |                |
  |      |           | - Validate action            |                |
  |      |           | - Compute result             |                |
  |      |           | - Generate state_changes     |                |
  |      |           | - Emit events                |                |
  |      |           +-----------------------------+                 |
  |      |                          |                                |
  |      |           +-----------------------------+                 |
  |      |           | Transaction Engine           |                |
  |      |           | - Validate bilateral deal    |                |
  |      |           | - Hold for counterparty      |                |
  |      |           | - Execute on confirmation     |                |
  |      |           | - Emit events                |                |
  |      |           +-----------------------------+                 |
  |      |                          |                                |
  |      v                          v                                |
  |  [Updated State]         [Event Log += new events]              |
  |      |                          |                                |
  |      +--------> Push filtered updates to affected participants  |
  +-----------------------------------------------------------------+
                              |
                              v
  +-----------------------------------------------------------------+
  |              PHASE B: WORLD MODEL (Batch)                        |
  |              Duration: < 5 minutes                               |
  |                                                                  |
  |  INPUT:                                                          |
  |    Full State + All Phase A Events + Country Actions             |
  |                                                                  |
  |  PASS 1: Deterministic (14 chained steps)                       |
  |    Step 0:  Apply submitted actions                              |
  |    Step 1:  Oil price (global)          ----+                    |
  |    Step 2:  GDP growth (per country)   <----+                    |
  |    Step 3:  Revenue (per country)      <----+                    |
  |    Step 4:  Budget execution           <----+                    |
  |    Step 5:  Military production        <----+                    |
  |    Step 6:  Technology advancement     <----+                    |
  |    Step 7:  Inflation update           <----+                    |
  |    Step 8:  Debt service update        <----+                    |
  |    Step 9:  Economic state transitions <----+                    |
  |    Step 10: Momentum update            <----+                    |
  |    Step 11: Contagion (cross-country)  <----+                    |
  |    Step 12: Stability update           <----+                    |
  |    Step 13: Political support update   <----+                    |
  |    Post:    Elections, market index, etc.                        |
  |                                                                  |
  |  PASS 2: AI Contextual Adjustments                              |
  |    Market psychology, capital flight, rallies, adaptation        |
  |    Total GDP adjustment capped at 30% per country               |
  |                                                                  |
  |  PASS 3: Coherence Check + Narrative                            |
  |    Flag implausible states, auto-fix HIGH severity               |
  |    Generate round briefing narrative                             |
  |                                                                  |
  |  OUTPUT:                                                         |
  |    New State + Events + Narrative + Expert Panel + Flags         |
  +-----------------------------------------------------------------+
                              |
                              v
  +-----------------------------------------------------------------+
  |              PHASE C: DEPLOYMENT (Real-Time, Structured)         |
  |              Duration: 10-15 minutes                             |
  |                                                                  |
  |  Participant ---[deploy orders]---> Backend                      |
  |      |                                 |                         |
  |      |                 Validate: unit availability, zone access  |
  |      |                 Apply: update zone forces                  |
  |      |                 Emit: deployment events                   |
  |      |                                 |                         |
  |      v                                 v                         |
  |  [Updated Map]              [Event Log += deployment events]    |
  +-----------------------------------------------------------------+
                              |
                              v
  +-----------------------------------------------------------------+
  |                        ROUND N END                               |
  |  Freeze: Snapshot(N) -- IMMUTABLE from this point               |
  |  Advance: round_num = N + 1                                     |
  |  Archive: Round summary for post-SIM analysis                   |
  +-----------------------------------------------------------------+
```

---

# 2. INFORMATION ASYMMETRY MATRIX

## What Each Participant Class Sees

This matrix defines the visibility rules that the API layer MUST enforce. See [F2 Data Architecture, Part 5](SEED_F2_DATA_ARCHITECTURE_v1.md) for the complete specification.

### Economic Data

```
                        VISIBILITY LEVEL
                  Public    Country   Role     Moderator
                  ------    -------   ----     ---------
Own GDP             --        EXACT     EXACT    EXACT
Own Treasury        --        EXACT     EXACT    EXACT
Own Inflation       --        EXACT     EXACT    EXACT
Own Debt            --        EXACT     EXACT    EXACT
Own Econ State      --        EXACT     EXACT    EXACT
Own Momentum        --        EXACT     EXACT    EXACT
Own Market Index    --        EXACT     EXACT    EXACT
Own Budget/Revenue  --        EXACT     EXACT    EXACT
Other GDP           TIER(*)   --        INTEL    EXACT
Other Treasury      HIDDEN    --        INTEL    EXACT
Other Inflation     LAG-1(**) --        INTEL    EXACT
Other Econ State    LAG-1     --        INTEL    EXACT
Other Debt          HIDDEN    --        INTEL    EXACT
Oil Price           EXACT     EXACT     EXACT    EXACT
Dollar Credibility  HIDDEN    HIDDEN    HIDDEN   EXACT
```

`(*) TIER = small (<10), medium (10-30), large (30-100), major (100+)`
`(**) LAG-1 = public with 1-round delay`
`INTEL = revealed by intelligence operations, may have +/-10-20% noise`

### Military Data

```
                        VISIBILITY LEVEL
                  Public    Country   Role     Moderator
                  ------    -------   ----     ---------
Own Unit Counts     --        EXACT     EXACT    EXACT
Own Positions       --        EXACT     EXACT    EXACT
Adjacent Zone       VISIBLE   VISIBLE   VISIBLE  EXACT
  Forces
Distant Zone        HIDDEN    HIDDEN    INTEL    EXACT
  Forces
Other Total Mil     TIER(*)   --        INTEL    EXACT
Combat Results      SUMMARY   EXACT(**) EXACT    EXACT
Nuclear Capability  DECLARED  DECLARED  INTEL    EXACT
```

`(*) TIER = weak (<10), moderate (10-25), strong (25-50), superpower (50+)`
`(**) EXACT for own-involvement combats only`

### Political Data

```
                        VISIBILITY LEVEL
                  Public    Country   Role     Moderator
                  ------    -------   ----     ---------
Own Stability       --        EXACT     EXACT    EXACT
Own Support         --        EXACT     EXACT    EXACT
Own War Tiredness   --        EXACT     EXACT    EXACT
Other Stability     HIDDEN    --        INTEL~   EXACT
Other Support       HIDDEN    --        INTEL~   EXACT
Elections           EXACT     EXACT     EXACT    EXACT
Regime Changes      EXACT     EXACT     EXACT    EXACT
```

`INTEL~ = approximate (+/-15% noise)`

### Diplomatic Data

```
                        VISIBILITY LEVEL
                  Public    Country   Role     Moderator
                  ------    -------   ----     ---------
Public Treaties     EXACT     EXACT     EXACT    EXACT
Secret Agreements   HIDDEN    PARTIES   PARTIES  EXACT
Negotiations        HIDDEN    OWN-ONLY  INTEL    EXACT
Tariff Levels       EXACT     EXACT     EXACT    EXACT
Sanction Levels     EXACT     EXACT     EXACT    EXACT
OPEC Decisions      EXACT     EXACT     EXACT    EXACT
```

### Role-Specific Data

```
                        VISIBILITY LEVEL
                  Public    Country   Role     Moderator
                  ------    -------   ----     ---------
Personal Coins      --        --        OWN      EXACT
Role Artefacts      --        --        OWN      EXACT
Covert Op Results   --        --        ORDERER  EXACT
Expert Panel        --        --        --       EXACT
Coherence Flags     --        --        --       EXACT
```

---

# 3. REAL-TIME vs BATCH DATA CLASSIFICATION

## Processing Mode by Data Type

| Data Category | Processing Mode | Latency Target | Update Trigger |
|--------------|----------------|----------------|----------------|
| **Combat results** | REAL-TIME | < 2 seconds | Player attack action |
| **Unit movement** | REAL-TIME | < 2 seconds | Player move/deploy action |
| **Blockade status** | REAL-TIME | < 2 seconds | Naval force positioning |
| **Bilateral transactions** | REAL-TIME | < 5 seconds | Both parties confirm |
| **Public statements** | REAL-TIME | < 1 second | Player submits statement |
| **Tariff/sanction changes** | REAL-TIME (Phase A) or BATCH (Phase B) | < 2 seconds or next round | Player action or submitted with budget |
| **GDP, revenue, budget** | BATCH | < 5 minutes (full round) | Round processing (Phase B) |
| **Inflation, debt** | BATCH | < 5 minutes | Round processing (Phase B) |
| **Economic state transitions** | BATCH | < 5 minutes | Round processing (Phase B) |
| **Stability, political support** | BATCH | < 5 minutes | Round processing (Phase B) |
| **Technology advancement** | BATCH | < 5 minutes | Round processing (Phase B) |
| **Contagion effects** | BATCH | < 5 minutes | Round processing (Phase B) |
| **Oil price** | BATCH | < 5 minutes | Round processing (Phase B) |
| **Expert panel adjustments** | BATCH | < 30 seconds (LLM) | Round processing (Phase B, Pass 2) |
| **Narrative generation** | BATCH | < 60 seconds (LLM) | Round processing (Phase B, Pass 3) |
| **Market index** | BATCH | < 5 minutes | Round processing (Phase B, post-step) |
| **Elections** | BATCH | < 5 minutes | Scheduled event (Phase B) |

## Data Flow by Engine

```
+-------------------+     +-------------------+     +-------------------+
|  LIVE ACTION      |     |  TRANSACTION      |     |  WORLD MODEL      |
|  ENGINE           |     |  ENGINE           |     |  ENGINE           |
|                   |     |                   |     |                   |
|  Mode: REAL-TIME  |     |  Mode: REAL-TIME  |     |  Mode: BATCH      |
|  Phase: A         |     |  Phase: A         |     |  Phase: B         |
|                   |     |                   |     |                   |
|  Reads:           |     |  Reads:           |     |  Reads:           |
|  - Current state  |     |  - Current state  |     |  - Full state     |
|  - Action params  |     |  - Deal params    |     |  - All events     |
|                   |     |  - Counterparty   |     |  - All actions    |
|  Writes:          |     |    confirmation   |     |                   |
|  - State changes  |     |                   |     |  Writes:          |
|  - Events         |     |  Writes:          |     |  - New state      |
|  - Combat results |     |  - State changes  |     |  - Events         |
|                   |     |  - Events         |     |  - Narrative      |
|  Touches:         |     |  - Transaction    |     |  - Expert panel   |
|  - Zone forces    |     |    records        |     |  - Coherence      |
|  - Unit counts    |     |                   |     |    flags          |
|  - Blockade state |     |  Touches:         |     |                   |
|  - War state      |     |  - Treasury       |     |  Touches:         |
|  - Nuclear flag   |     |  - Personal coins |     |  - ALL country    |
|                   |     |  - Treaties       |     |    economic,      |
+-------------------+     |  - Basing rights  |     |    military,      |
                          +-------------------+     |    political,     |
                                                    |    technology     |
                                                    |    variables      |
                                                    +-------------------+
```

---

# 4. STATE SNAPSHOT LIFECYCLE

```
                    MUTABLE                          IMMUTABLE
                    (current round)                  (past rounds)

Round 0 Start:   [Snapshot_0 = CSV seed data]
                       |
                  Phase A actions modify state
                  Phase B engine processes
                  Phase C deployments
                       |
Round 0 End:     [Snapshot_0 FROZEN] ---------> Archived, never modified
                       |
Round 1 Start:   [Snapshot_1 = copy(Snapshot_0)]
                       |
                  Phase A/B/C processing
                       |
Round 1 End:     [Snapshot_1 FROZEN] ---------> Archived, never modified
                       |
                  ... (repeat for 8 rounds) ...
                       |
Round 7 End:     [Snapshot_7 FROZEN] ---------> Final state for analysis
```

**Snapshot contents:**
- All CORE variables (global + per-country + per-role)
- Round metadata (round_num, phase timestamps)
- Event count for the round (events themselves stored separately)

**Snapshot does NOT contain:**
- DERIVED variables (recompute from CORE on demand)
- INTERMEDIATE values (exist only during processing)
- Event log (stored separately, append-only)

---

# 5. EVENT LOG AS DATA PIPELINE

The event log serves three purposes simultaneously:

```
+------------------+
|  EVENT LOG       |
|  (append-only)   |
+------------------+
        |
        +---------> [1] STATE RECONSTRUCTION
        |               Replay events from Snapshot(N) to reconstruct
        |               any state between snapshots. Used for debugging
        |               and moderator review.
        |
        +---------> [2] REAL-TIME NOTIFICATIONS
        |               New events pushed to participants via WebSocket
        |               (filtered by visibility). Used for live gameplay.
        |
        +---------> [3] ANALYTICS PIPELINE
                        Post-SIM behavioral analysis. Every decision,
                        every outcome, every state transition recorded.
                        This is the research data product.
```

## Event Log Query Patterns

| Query | Used By | Frequency |
|-------|---------|-----------|
| Events for round N, visible to role R | Participant dashboard | Every page load |
| Events for round N, all visibility | Moderator dashboard | On demand |
| Events by actor A across all rounds | Post-SIM analysis | After SIM |
| Events of type T (e.g., all attacks) | Analytics | After SIM |
| Events affecting country C | Country briefing generation | Each round |
| Latest N events (any) | Real-time feed | Continuous during Phase A |

---

# 6. DATA STORAGE STRATEGY BY PHASE

## SEED Phase (Current)

```
CSV files (data/)
    |
    v
world_state.py loads into memory
    |
    v
Engine processes in-memory
    |
    v
JSON snapshot written to disk
    |
    v
Event log written to JSON file
```

**Limitations:** No concurrent access, no real-time updates, no visibility filtering, no persistence beyond files.

## BUILD Phase (Target)

```
CSV files (data/)                 Supabase (PostgreSQL)
    |                                    ^
    v                                    |
One-time import ----------------------->|
                                         |
Web App (Next.js) <------ API --------->|
    |                                    |
    v                                    |
Participant Dashboard                    |
Moderator Dashboard                      |
    |                                    |
    v                                    |
Actions ------> Backend ------> Engine   |
                    |              |      |
                    |              v      |
                    |         Engine writes state + events
                    |              |      |
                    +<-------------+      |
                    |                     |
                    +---> Supabase ------>|
                    |                     |
                    +---> WebSocket push to participants
```

**Capabilities:** Concurrent multi-player access, real-time updates, role-based visibility, persistent state, event-driven architecture.

---

*This document specifies how data flows through the TTT system. For data structure definitions, see [F2 Data Architecture](SEED_F2_DATA_ARCHITECTURE_v1.md). For API interface specifications, see [F4 API Contracts](SEED_F4_API_CONTRACTS_v1.md).*
