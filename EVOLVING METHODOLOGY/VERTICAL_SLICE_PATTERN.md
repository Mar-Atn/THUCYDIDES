# Vertical Slice Pattern

## How to ship a polished mandatory-decision feature end-to-end

**Version:** 1.0 | **Date:** 2026-04-10 | **Status:** Proven (budget slice, 2026-04-10)
**Derived from:** The budget vertical slice (see `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_BUDGET.md`)

---

## Why this pattern exists

The TTT project has four mandatory per-round decisions on the participant side: **budget**, **sanctions**, **tariffs**, **OPEC**. Each touches the full stack: a contract document, a validator, an engine formula set, a DB migration, a persistence path, a context builder, an AI prompt, and LLM-level acceptance tests.

Building all four ad-hoc produces four inconsistent shapes. Building the first one as a **template**, then following it for the next three, produces a coherent decision subsystem.

**The rule:** when starting a new mandatory decision, copy the slice pattern. Don't invent a different shape unless the domain genuinely requires one, and even then first write down WHY in the domain's CHECKPOINT file.

---

## The 7 steps (in order — do not skip, do not reorder)

### Step 1 — Lock the contract

**Deliverable:** `PHASES/UNMANNED_SPACECRAFT/CONTRACT_{DOMAIN}.md`

A single document that specifies:
1. **Purpose** — one paragraph, what the decision is and when it fires.
2. **Decision schema** — the exact JSON shape (top-level envelope + `changes` payload) with a canonical example.
3. **Field specifications** — every field, its type, its range, its required/optional status, its semantics.
4. **Context package** — what the decision-maker (human or AI) sees before deciding. Sections, structure, sources in the DB.
5. **Validation rules** — every error code the validator can return, with the rule it enforces.
6. **Persistence** — which DB columns on which tables store the decision.
7. **Engine behavior** — how the engine consumes the decision, what it writes back, what it cascades into.
8. **Out of scope** — an explicit list of things this contract does NOT cover. Prevents scope creep.
9. **Standard output** — what the engine's result looks like (dataclass or dict) so tests can assert it.
10. **Acceptance criteria** — the list of tests that must pass before the contract is considered satisfied.

**Status header:** when the slice is done, the contract gets a `🔒 LOCKED` marker, and any future change requires Marat's explicit approval + version bump + reconciliation of all listed consumers in the same commit.

**Output of step 1:** A document that can be handed to a new agent who then builds steps 2-7 without asking clarifying questions.

---

### Step 2 — Validator (L1)

**Deliverable:** `app/engine/services/{domain}_validator.py` + `app/tests/layer1/test_{domain}_validator.py`

A pure function:

```python
def validate_{domain}_decision(payload: dict) -> dict:
    """Returns {valid: bool, errors: list[str], warnings: list[str], normalized: dict | None}"""
```

**Rules:**
- **Pure.** No DB, no LLM, no I/O. Pytest can run thousands of cases per second.
- **Accumulates all errors in one pass.** Never stop at the first failure. Participants need the full list.
- **Returns a normalized copy** when valid — cleaned types (ints as ints, floats as floats), stripped strings, no extra fields. The normalized shape is what persistence writes and the engine reads.
- **Every error code** from CONTRACT §4 has a test. Every boundary value has a test. Every shape variant (missing field, extra field, wrong type, out of range) has a test.

**Consumed by:** AI skill harness (step 6), human UI (future), test fixtures (everywhere).

---

### Step 3 — Engine (L1)

**Deliverable:** Extensions/rewrites to `app/engine/engines/{relevant_engine}.py` + `app/tests/layer1/test_{domain}_engine.py`

The pure formulas that consume a valid decision and produce outputs. Engine functions are **stateless** — they take `(country, decision, world_state)` and return a result object. No DB access, no global state.

**Rules:**
- **Match the contract.** If the engine computes something the contract doesn't specify, that's a contract gap — go back to Step 1 and fix it before touching code.
- **Constants at the top of the file.** Every magic number gets a named constant.
- **Side-effect semantics explicit.** If a formula mutates `country[...]` fields, document which ones in the docstring.
- **Tests go per formula.** One test class per formula, covering happy path, edge cases (zero, max, negative), boundary values, and the contract's canonical example (verbatim).

**Anti-pattern alert:** if you find yourself adding caps, limits, or "sanity checks" that aren't in the contract, STOP. Either (a) the contract is incomplete — go fix it, or (b) you're papering over a deeper issue. Don't silently clip values.

---

### Step 4 — Persistence (L2)

**Deliverable:** DB migration + updates to `resolve_round.py` + `round_tick.py` + `app/tests/layer2/test_{domain}_persistence.py`

**DB migration:**
- Add only what you need to persist. Use JSONB for structured decisions with many optional fields. Use explicit columns for frequently-queried scalars.
- Backfill existing R0 snapshots from structural data so the first round after the migration doesn't read NULL.
- Use `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`. Migrations are idempotent.
- Apply via Supabase MCP `apply_migration` so it shows up in the migration history.

**Persistence wiring:**
- `resolve_round.py` handles the `set_{domain}` action: runs the validator, writes validated fields to the snapshot row, emits a `{domain}_rejected` observatory event on validation failure, handles `no_change` via the previous round's values.
- `round_tick.py._merge_to_engine_dict` loads the new columns into the engine-format dict **preferring the snapshot** over structural base data (fall back to base only when snapshot is NULL — this matters for R0).
- `round_tick.py` write-back payload extended to include every engine output that needs to persist to the next round. **If the engine mutates it in memory and the next round needs it, it must be written back.** No exceptions — this is how Gap B (ai_rd_progress) was born.

**L2 tests:**
1. `test_{domain}_decision_persisted_and_read` — decision written to DB, read back with matching values.
2. `test_{domain}_no_change_carries_forward` — `no_change` in R+1 reuses R+0's values.
3. `test_invalid_{domain}_rejected` — invalid decision produces a `{domain}_rejected` event, no leakage into the snapshot, round still completes.

---

### Step 5 — Context builder + dry-run (L2)

**Deliverable:** `app/engine/services/{domain}_context.py` + `app/tests/layer2/test_{domain}_context.py`

Two pure-ish functions (DB reads allowed, no writes):

```python
def build_{domain}_context(country_code, scenario_code, round_num) -> dict:
    """Read-only: assemble the full context package per CONTRACT §3."""

def dry_run_{domain}(country_code, scenario_code, round_num, decision_override=None) -> dict:
    """Deep-copy the engine dict, run the relevant engine chain, capture deltas,
    discard. Used to show 'what happens if you don't change anything' AND
    'what happens if you make this specific change' — the single source of
    truth is the same engine code that runs the real round."""
```

**Rules:**
- **Single source of truth.** The dry-run MUST call the real engine functions on a deep copy of the state. Never duplicate formulas. If the real engine is wrong, the preview should also be wrong — consistency > correctness at this layer.
- **Deep copy, not reference.** A bug here can silently mutate the real game state. Use `copy.deepcopy` on the country dict before running.
- **Returns structured dict.** Not a rendered string. The AI prompt builder and the human UI both format it differently from the same structured data.

**L2 tests:** verify the context reads the right country state, the revenue forecast is right, mandatory costs are computed correctly, the dry-run with an override produces different outputs, the dry-run with no change matches the actual round outcome, and deficit warnings fire when appropriate.

---

### Step 6 — AI skill harness (L3)

**Deliverable:** Update `app/tests/layer3/test_skill_mandatory_decisions.py` for the new domain OR create a domain-specific harness file.

Per-domain prompt builder + per-domain LLM caller + per-domain payload assertion.

**Rules:**
- **One focused prompt per domain.** D1 budget = economic state. D2 sanctions = relationships + wars. D3 tariffs = trade partners. D4 OPEC = oil + geopolitics. **Do not** put all four in one giant call. The 4-call architecture is documented in the skill harness file header.
- **Use the real validator.** The test's payload assertion calls `validate_{domain}_decision()` and asserts `valid == True`. Do not hand-roll partial checks. This is how we catch prompt drift: if the prompt teaches a schema the validator doesn't accept, the LLM test fails.
- **Run against the full scenario roster** (10 leaders, covering the shape diversity: at war, peaceful, in crisis, rich, poor, OPEC member, etc.).
- **Print a rich per-leader report** with the decision, rationale excerpt, and a consolidated table so Marat can eyeball all 10 in one scan.

**Cost:** ~10-15 LLM calls per full run on Gemini Flash, < $0.10.

---

### Step 7 — AI acceptance gate (L3)

**Deliverable:** `app/tests/layer3/test_{domain}_full_chain_ai.py`

The definitive end-to-end proof: a single test that wires Step 6 (real LLM decision) into Step 4 (persistence + engine). The chain:

```
LeaderScenario (from Step 6 harness)
  -> prompt builder
    -> real LLM call
      -> real validator (Step 2)
        -> agent_decisions insert (Step 4)
          -> resolve_round
            -> run_engine_tick (Step 4 reads)
              -> country_states_per_round (Step 4 writes)
                -> hard DB-backed assertions matching the contract
```

**Rules:**
- **No human fixup.** The raw LLM JSON → validator → persistence. If the validator rejects it, the test fails. This is the whole point: the AI's output must be acceptable without cleaning.
- **One country, one decision, one round.** Keep it focused. Budget uses Columbia. Pick a different country for each subsequent domain so the tests don't fight over state.
- **Assert the decision persisted exactly.** Social_pct, production dict, research dict — all three must match the LLM's output byte-for-byte in the DB JSONB columns.
- **Assert at least one engine effect.** Treasury moved, stability moved, inflation moved — SOMETHING must show the engine actually consumed the decision.
- **Assert one contract-derived relationship.** For budget: "if social_pct < 1.0, stability should drop directionally." For sanctions/tariffs/OPEC: pick an equivalent contract clause.

If Step 7 passes, the slice is DONE. Write the CHECKPOINT doc (next section) and move on.

---

## Closing the loop: the CHECKPOINT document

After Step 7 passes, the slice owner writes `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_{DOMAIN}.md` — one page, durable record, containing:

1. Status + dates + contract pointer
2. Scope (what this decision covers)
3. Design decisions locked (Marat's answers to open questions)
4. Engine changes (bulleted file-level)
5. New services
6. Persistence changes (migration name, new columns, backfill)
7. Test coverage table (layers × counts × what each asserts)
8. **Concrete demo numbers** — at least 2 real runs with before/after tables
9. Known non-gap observations (behaviors that look weird but are correct)
10. Pointers (copy-pasteable list of every file)
11. Next — which domain to build next and why

The CHECKPOINT is the durable evidence. If the entire team gets hit by a bus and a new agent picks up, the CHECKPOINT + the contract + the test files should be enough to reconstruct the slice without reading any git history.

---

## Reconciliation obligations

When the slice is complete, update (in the same commit as the CHECKPOINT):

- **`PHASES/UNMANNED_SPACECRAFT/PHASE.md`** — mark the slice DONE, link to CHECKPOINT
- **`PHASES/UNMANNED_SPACECRAFT/CARD_FORMULAS.md`** — fix any formula section that contradicts the new contract
- **`PHASES/UNMANNED_SPACECRAFT/CARD_ACTIONS.md`** — fix the action spec if the schema changed
- **`CONCEPT TEST/CHANGES_LOG.md`** — append a milestone entry
- **`3 DETAILED DESIGN/DET_D8_*`** (or equivalent) — only fix DIRECT contradictions. Do NOT attempt a full rewrite mid-phase — that belongs in the post-phase architectural re-synthesis.

Do NOT touch `1. CONCEPT/` or `2 SEED/` during a mid-phase slice. Those are frozen by convention (see root `CLAUDE.md` §4) and only reopen for genuine conceptual changes, not implementation updates.

---

## What this pattern is NOT

- It is not a substitute for thinking. Every slice has surprises; the pattern shapes the approach but does not automate judgment.
- It is not a sprint template. The 7 steps can span hours or days depending on complexity.
- It is not for non-mandatory actions. Actions like `attack` or `propose_exchange` have their own architecture (the action catalog pattern). The vertical slice pattern is specifically for the four end-of-round mandatory decisions.
- It is not permission to redesign everything. The pattern locks the SHAPE of the work. It does not authorize rewriting engines or renegotiating contracts without explicit approval.

---

## Lessons already learned (from the budget slice)

1. **Running tests actually reveals hidden assumptions.** Multiple budget tests had quiet assumptions (Columbia not being an oil producer, caps silently scaling production) that only surfaced when we ran the tests end-to-end with real DB data. Run early, run often.
2. **"Known gaps" accumulate if not paid down immediately.** The budget slice originally documented two "KNOWN GAPS" in comments. They became invisible until explicitly asked about. If you document a gap, open a ticket for it in the same commit — or fix it. Don't leave it in a comment.
3. **Caps without contract backing are landmines.** The 40% military / 30% R&D caps were invented during implementation and never documented. They silently scaled participant decisions and hid real behavior. If you catch yourself adding a limit, check the contract. If it's not there, STOP and ask.
4. **`no_change` must be structurally distinct from `change`.** An explicit decision not to change is different from forgetting to decide. The contract enforces this (omit `changes` entirely on no_change, require rationale anyway).
5. **The dry-run is the participant's best friend.** Almost every AI budget in the demo over-ordered and triggered the deficit cascade. The dry-run forecast from Step 5 is what makes this legible to participants before they commit.
6. **Matching the countries-table naming convention matters.** We chose `mil_strategic_missiles` (plural) in the snapshot columns to match the `countries` table, even though the engine dict uses `strategic_missile` (singular). Inconsistent but honest — introducing a third convention would have been worse.
