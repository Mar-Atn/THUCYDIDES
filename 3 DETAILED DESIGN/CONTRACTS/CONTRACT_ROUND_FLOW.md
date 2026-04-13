# CONTRACT: Round Flow — Phase A / Phase B / Inter-Round

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** Marat's session directive (2026-04-13)

---

## 1. PURPOSE

Defines the canonical round flow for the Thucydides Trap simulation.
The orchestrator (core of the Moderator module) executes this flow each round.
Same flow for unmanned (AI-only) and manned (human+AI) modes — only the
participant interface layer differs.

---

## 2. ROUND N FLOW

### PHASE A — Free Actions + Regular Decisions

#### A.1 Free Actions (concurrent, real-time)

**Human participants:** Act freely — submit military actions, initiate conversations,
propose transactions, use cards, at their own pace throughout the round.

**AI participants:** The orchestrator asks each AI participant **2 times per round**
what actions they want to take from the full action menu. Each participant may
submit up to **5 actions per round** total across both asks.

**Action categories available:**

| Category | Actions | Resolution |
|---|---|---|
| **Military** | move_units, declare_attack (ground/air/naval/bombardment), missile_launch, nuclear_test, blockade, basing_rights | Immediate combat resolution + deferred effects to Phase B |
| **Covert** | intelligence, sabotage, propaganda, election_meddling | Immediate resolution (rolls + effects) |
| **Domestic** | arrest, martial_law, reassign_powers, lead_protest, coup_attempt, assassination | Immediate resolution |
| **Political** | submit_nomination, cast_vote, call_early_elections, public_statement | Immediate resolution |
| **Transactions** | propose_exchange, propose_agreement | Immediate proposal; counterpart responds asynchronously |

**Resolution timing:**
- **Immediate result:** intelligence, arrest, sabotage, propaganda, assassination, coup, protest, elections, public_statement
- **Immediate + Phase B input:** military attacks (combat resolves immediately; casualties/support effects feed Phase B), martial law (conscripts immediately; stability/WT costs in Phase B)
- **Phase B only:** budget allocations, R&D investment levels, OPEC production targets

#### A.2 Regular Decisions (mandatory, per-country)

Each country submits once per round:
- **Budget** — spending allocation across branches + social spending %
- **Sanctions** — bilateral sanction level changes
- **Tariffs** — bilateral tariff level changes
- **OPEC production** — oil producers only

**Human:** Can submit anytime during the round.
**AI:** Asked once near end of round (after free actions).

---

### PHASE B — Batch Processing (between rounds)

The orchestrator runs all engines in sequence. **No participant input during Phase B.**

```
Step 0:   Apply submitted regular decisions (tariff/sanction/OPEC changes)
Steps 1-11: Economic engine
            oil price → GDP → revenue → budget execution → production →
            tech progress → inflation → debt → crisis → momentum → contagion
Step 12:  Stability (per country)
Step 13:  Political support (per country)
Step 14:  War tiredness
Step 15:  Revolution checks
Step 16:  Health events
Step 17:  Scheduled elections + early election processing
Step 18:  Capitulation check
Step 19:  Persist all state to DB
```

**Phase B inputs from Phase A:**
- Combat casualties → affect stability, support, war tiredness
- Martial law → stability cost, war tiredness cost already applied
- Sabotage damage → affects GDP, nuclear_rd_progress
- Propaganda effects → already applied to stability
- Election results → parliament seat changes, recorded
- Assassination/coup outcomes → role status changes, support shifts

---

### INTER-ROUND — Unit Movement Window

**Duration:** 5-10 minutes while Phase B engine updates process.

Both human and AI participants may move their units on the map.
This is the ONLY time movement is submitted (not during Phase A).

**AI participants:** Orchestrator asks each AI participant once for movement orders.

---

## 3. AI PARTICIPANT ORCHESTRATION (Unmanned)

```
Per round, for each AI participant:
  Ask #1 (early round): "What actions do you want to take?" → up to 3 actions
  Ask #2 (mid round):   "Any additional actions?"           → up to 2 more actions
  Regular:              Mandatory decisions (budget/sanctions/tariffs/OPEC)
  Movement:             Unit movement orders (inter-round window)

Total: max 5 free actions + 1 set of regular decisions + 1 movement batch
```

---

## 4. ACTION RESOLUTION DISPATCH

The orchestrator dispatches each submitted action to its engine:

```python
IMMEDIATE_DISPATCH = {
    # Military (combat resolves immediately)
    "declare_attack":    resolve_round._process_attack,      # ground/air/naval/bombardment
    "launch_missile":    military.resolve_missile_strike,
    "blockade":          military.resolve_blockade,
    "basing_rights":     basing_rights_engine.execute,

    # Covert
    "intelligence":      intelligence_engine.generate_intelligence_report,
    "sabotage":          sabotage_engine.execute_sabotage,
    "propaganda":        propaganda_engine.execute_propaganda,
    "election_meddling": election_meddling_engine.execute_election_meddling,

    # Domestic/Political
    "arrest":            arrest_engine.request_arrest,
    "martial_law":       martial_law_engine.execute_martial_law,
    "reassign_powers":   power_assignments.reassign_power,
    "assassination":     assassination_engine.execute_assassination,
    "coup_attempt":      coup_engine.execute_coup,
    "lead_protest":      protest_engine.execute_mass_protest,
    "call_early_elections": early_elections_engine.execute_early_elections,
    "submit_nomination": election_engine.submit_nomination,
    "cast_vote":         election_engine.cast_vote,
    "public_statement":  _log_statement,  # no engine, just observatory event

    # Transactions (proposal; counterpart responds separately)
    "propose_exchange":  transaction_engine.propose_exchange,
    "propose_agreement": agreement_engine.propose_agreement,
}

BATCH_DISPATCH = {
    # Phase B regular decisions
    "set_budget":     orchestrator._apply_budget,
    "set_sanctions":  orchestrator._apply_sanctions,
    "set_tariffs":    orchestrator._apply_tariffs,
    "set_opec":       orchestrator._apply_opec,
}

MOVEMENT_DISPATCH = {
    "move_units":     resolve_round._process_movement,
}
```

---

## 5. NUCLEAR CHAIN (Special Multi-Step)

Nuclear actions follow a 4-phase state machine (see CONTRACT_NUCLEAR_CHAIN.md):
1. Initiate → 2. Authorize → 3. Alert + Intercept → 4. Resolve

The orchestrator manages the nuclear chain as a special sub-process within Phase A.
AI officer authorization and interception decisions are resolved via LLM calls.

---

## 6. LOCKED INVARIANTS

1. **Phase A → Phase B → Inter-Round** is the canonical round sequence
2. AI participants asked **2 times per round** for free actions, max **5 actions total**
3. Regular decisions (budget/sanctions/tariffs/OPEC) are **mandatory** once per country per round
4. Phase B batch processing runs **all engines in sequence** (economic → political → elections)
5. Unit movement happens ONLY during inter-round window
6. Same flow for unmanned and manned modes (only interface differs)
7. Orchestrator is the **core of the Moderator module**
8. All action results logged to `observatory_events`
9. All state changes persist to `country_states_per_round` / `unit_states_per_round`
10. Transaction responses (accept/decline) happen asynchronously within Phase A
