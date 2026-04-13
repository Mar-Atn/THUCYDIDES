# DET_ROUND_WORKFLOW.md
## Canonical Round Flow — Phase A / Phase B / Inter-Round
**Version:** 2.0 | **Date:** 2026-04-13 | **Status:** ACTIVE
**Owner:** BUILD Team
**Source of truth:** `PHASES/UNMANNED_SPACECRAFT/CONTRACT_ROUND_FLOW.md` (LOCKED v1.0)
**Cross-references:** [C1 System Contracts](DET_C1_SYSTEM_CONTRACTS.md) | [Action Dispatcher](DET_ACTION_DISPATCHER.md) | [F5 Engine API](DET_F5_ENGINE_API.md) | [CARD_ACTIONS](../PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md)

---

## PURPOSE

Specifies the canonical round flow for every simulation round. The same logical flow
applies to **unmanned** (AI-only, orchestrator-driven) and **manned** (human+AI,
facilitator-driven) modes — only the interface layer differs.

Supersedes DET_ROUND_WORKFLOW v1.0 (2026-03-30) which described a manned-only
17-step facilitator workflow. The manned workflow is retained as Section 6 (secondary).

---

## 1. ROUND OVERVIEW

```
ROUND N
  │
  ├── PHASE A — Free Actions + Regular Decisions (concurrent, real-time)
  │     ├── A.1 Free Actions (military, covert, domestic, political, transactions)
  │     └── A.2 Regular Decisions (budget, sanctions, tariffs, OPEC)
  │
  ├── PHASE B — Batch Processing (no participant input)
  │     └── Steps 0-19: Economic → Political → Elections → Persist
  │
  └── INTER-ROUND — Unit Movement Window
        └── All participants submit movement orders (5-10 minutes)
```

---

## 2. PHASE A — Free Actions + Regular Decisions

### A.1 Free Actions

Participants submit actions from the full action menu. Each action is dispatched
immediately to its engine via `action_dispatcher.dispatch_action()`.

**Human participants:** Act freely throughout the round — submit attacks, propose
transactions, use cards, initiate conversations at their own pace.

**AI participants (unmanned mode):** The orchestrator asks each AI participant
**2 times per round** for actions from the full menu. Each participant may submit
up to **5 actions per round** across both asks.

| Category | Actions | Resolution |
|---|---|---|
| **Military** | declare_attack (ground/air/naval/bombardment), launch_missile, blockade, basing_rights | Immediate combat resolution |
| **Covert** | intelligence, sabotage, propaganda, election_meddling | Immediate resolution (rolls + effects) |
| **Domestic** | arrest, martial_law, reassign_powers, lead_protest, coup_attempt, assassination | Immediate resolution |
| **Political** | submit_nomination, cast_vote, call_early_elections, public_statement | Immediate resolution |
| **Transactions** | propose_exchange, respond_exchange, propose_agreement, sign_agreement | Proposal immediate; counterpart responds asynchronously |

**Resolution timing:**
- **Immediate:** Result computed and persisted during Phase A. Participant sees outcome.
- **Immediate + Phase B input:** Combat resolves immediately; casualties/support effects also feed Phase B stability/support calculations.

### A.2 Regular Decisions (mandatory, per-country)

Each country submits once per round:

| Decision | Who | Schema |
|---|---|---|
| **Budget** | HoS or Finance Minister | Social spending %, production levels per branch, R&D coins |
| **Sanctions** | HoS or Finance Minister | Bilateral sanction level changes (-3 to +3) |
| **Tariffs** | HoS or Finance Minister | Bilateral tariff level changes (0-3) |
| **OPEC Production** | OPEC members only | Production posture (min/low/normal/high/max) |

**Human:** Can submit anytime during Phase A.
**AI:** Asked once near end of round (after free actions).

Missing submissions use previous round's settings as default.

---

## 3. PHASE B — Batch Processing

The orchestrator runs all engines in sequence. **No participant input during Phase B.**

```
Step 0:   Apply submitted regular decisions (tariff/sanction/OPEC changes to world_state dict)
Steps 1-11: ECONOMIC ENGINE
            1. Oil price (supply/demand with non-linear amplification)
            2. GDP growth (per-country with trade/sanctions/tariff coefficients)
            3. Revenue (tax on GDP)
            4. Budget execution (social spending + military maintenance + production + R&D)
            5. Military production (units built from budget allocation)
            6. Technology progress (nuclear/AI R&D advancement)
            7. Inflation (money supply, tariffs, oil-driven)
            8. Debt dynamics (deficit → borrowing → debt_burden)
            9. Economic state transitions (normal → stressed → crisis → collapse)
            10. Momentum (growth persistence)
            11. Contagion (crisis spreads through trade when major GDP enters crisis)
Step 12:  STABILITY per country (gdp_growth, inflation, war, social_spending, market_stress)
Step 13:  POLITICAL SUPPORT per country (stability, growth, economic_state, oil, war_tiredness)
Step 14:  WAR TIREDNESS (accumulates for belligerents, decays in peace)
Step 15:  REVOLUTION CHECKS (stability ≤ 2 AND support < 20% → protest auto-trigger)
Step 16:  HEALTH EVENTS (10% per round incapacitation for elderly leaders)
Step 17:  ELECTIONS — scheduled elections + early_election_called flag processing
Step 18:  CAPITULATION CHECK (sustained economic collapse → forced surrender)
Step 19:  PERSIST all state to DB (country_states_per_round, global_state_per_round, sim_runs)
```

**Inputs from Phase A that feed Phase B:**
- Combat casualties → affect stability, support, war tiredness (Step 12-14)
- Martial law → stability and war_tiredness costs already applied immediately
- Sabotage damage → affects GDP in Step 2 (infrastructure damage), nuclear_rd_progress in Step 6
- Propaganda effects → stability shifts already applied immediately
- Election results → parliament changes recorded
- Assassination/coup outcomes → role status changes, support shifts

---

## 4. INTER-ROUND — Unit Movement Window

**Duration:** 5-10 minutes while Phase B results are being reviewed/published.

Both human and AI participants may submit movement orders for their units.
This is the **ONLY time movement is submitted** — not during Phase A.

**AI participants:** Orchestrator asks each AI participant once for movement orders.

Movement is processed via `move_units` action type through the movement validator
(17 error codes) and persisted to `unit_states_per_round`.

---

## 5. ACTION DISPATCH FLOW

```
Participant submits action
        │
        ▼
  commit_action() validates via Pydantic schema (action_schemas.py)
        │
        ▼
  Persisted to agent_decisions table
        │
        ▼
  action_dispatcher.dispatch_action() routes to engine
        │
        ├── Validator checks (role authorization, asset sufficiency, etc.)
        │
        ├── Engine resolves (combat rolls, state changes, etc.)
        │
        ├── Observatory event logged
        │
        └── Result returned to participant
```

**Orchestrator Phase A integration:** At the start of Phase B, the orchestrator calls
`_dispatch_phase_a_actions()` which loads all unprocessed actions from `agent_decisions`
(where `processed_at IS NULL`) and dispatches each through the action dispatcher.
Processed actions are marked with `processed_at` timestamp.

---

## 6. MANNED MODE — Facilitator Workflow (Secondary)

In manned mode, a human facilitator controls the round flow with these additional steps:

1. **End Phase A:** Facilitator clicks "End Phase A" → `sim_runs.current_phase = 'B'`
2. **Review submissions:** Facilitator reviews per-country submission summary
3. **Trigger processing:** Facilitator clicks "Process Round" → Phase B runs
4. **Review results:** Facilitator reviews economic/political changes, combat outcomes
5. **Override (optional):** Facilitator can override any value with logged reason
6. **Publish:** Facilitator clicks "Publish" → results broadcast to all participants
7. **Movement window:** Inter-Round phase begins, participants move units
8. **Start next round:** Facilitator starts Phase A for next round

The manned workflow wraps the same Phase A → Phase B → Inter-Round logic with
facilitator gates between phases. All engines and dispatchers are identical.

---

## 7. AI PARTICIPANT CADENCE (Unmanned Mode)

```
Per round, for each of ~40 AI participants:

  Ask #1 (early round):  "What actions do you want to take?"  → up to 3 actions
  Ask #2 (mid round):    "Any additional actions?"             → up to 2 more actions
  Regular decisions:     Budget/sanctions/tariffs/OPEC          → mandatory, asked once
  Movement:              Unit movement orders                   → inter-round window

Total per participant: max 5 free actions + 1 set of regular decisions + 1 movement batch
```

---

## 8. NUCLEAR CHAIN (Special Multi-Step)

Nuclear actions follow a 4-phase state machine (see CONTRACT_NUCLEAR_CHAIN.md):

```
Phase 1: INITIATE    — launcher submits nuclear action
Phase 2: AUTHORIZE   — 3-way authorization (launcher HoS + military chief + officer)
Phase 3: ALERT       — target country + T3+ countries alerted, decide whether to intercept
Phase 4: RESOLVE     — interception rolls + hit rolls + damage assessment
```

The orchestrator manages the nuclear chain as a special sub-process within Phase A.
AI officer authorization and interception decisions are resolved via LLM calls.

---

## 9. TIMING SUMMARY

| Phase | Unmanned Duration | Manned Duration | What Happens |
|---|---|---|---|
| Phase A | ~2-5 min (AI processing) | 45-80 min (human play) | Free actions + regular decisions |
| Phase B | ~30 sec (engine batch) | 5-20 min (with facilitator review) | World model update |
| Inter-Round | ~1-2 min (AI movement) | 5-10 min (human movement) | Unit repositioning |
| **Total** | **~5 min per round** | **~60-100 min per round** | |

---

## 10. LOCKED INVARIANTS

1. **Phase A → Phase B → Inter-Round** is the canonical round sequence
2. AI participants asked **2 times per round** for free actions, max **5 actions total**
3. Regular decisions (budget/sanctions/tariffs/OPEC) are **mandatory** once per country per round
4. Phase B batch processing runs **all engines in sequence** (economic → political → elections)
5. Unit movement happens ONLY during Inter-Round window
6. Same flow for unmanned and manned modes (only interface differs)
7. Orchestrator is the **core of the Moderator module**
8. All action results logged to `observatory_events`
9. All state changes persist to `country_states_per_round` / `unit_states_per_round`
10. Transaction responses (accept/decline) happen asynchronously within Phase A

---

*Version History:*
- *v1.0 (2026-03-30): Manned facilitator workflow (17 steps)*
- *v2.0 (2026-04-13): Canonical Phase A/B/Inter-Round flow for both manned and unmanned modes. Source: CONTRACT_ROUND_FLOW.md.*
