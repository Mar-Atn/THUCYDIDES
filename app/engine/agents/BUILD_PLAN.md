# AI Participant Module — Build Plan
**Status:** ACTIVE | **Started:** 2026-04-04 | **Target:** Working unmanned SIM
**Delete this file when AI Participant module v1 is complete.**

---

## Strategy: Gradual Learning & Skill Development

Build the AI module and test interface incrementally. Test each capability with a human operator before adding the next. Two AI implementations tested through the same interface.

---

## Phase 1: FOUNDATION

### 1A. Test Interface (web-based chat + inspector)
- [x] Select role to initialize (from SIM template/scenario)
- [x] Chat with agent (human ↔ AI in character)
- [x] View cognitive state (4 blocks, expandable)
- [ ] View context supplied for each decision (expandable) — not yet implemented
- [x] Navigate block version history
- [x] UX: Thucydides style guide
- [x] NOT part of main app (separate, standalone)

### 1B. AI Module v1 (KING 4-block) — skeleton
- [x] `leader.py` — LeaderAgent class implementing abstract interface from DET_C1 C6
- [x] `profiles.py` — Load role data from CSV, generate Block 2 identity via LLM
- [x] `memory.py` — Block 3/4 management (create, read, update, version history)
- [x] `initialize()` — full agent initialization (all 4 blocks)
- [x] `get_cognitive_state()` / `get_state_history()` — for test interface inspection
- [x] `chat()` — debug conversation (human talks to agent in character)
- [ ] **TEST:** Initialize 1 agent (Dealer/Columbia), chat with it, verify identity is coherent

---

## Phase 2: DECISIONS (one capability at a time)

For each capability: implement → test via interface → verify output format → next.

### 2A. Budget decisions
- [ ] `submit_mandatory_inputs()` — budget portion (social_pct, military, tech)
- [ ] Generate relevant context (country economic state, revenue, costs)
- [ ] Structured JSON output matching DET_C1 MandatoryInputs schema
- [ ] **TEST:** Ask agent to make budget decision, verify numbers are sensible

### 2B. Tariff & sanction decisions
- [ ] Tariff setting (per target country, L0-L3)
- [ ] Sanction setting (per target country, L0-L3)
- [ ] Context: bilateral relationships, trade exposure, strategic goals
- [ ] **TEST:** Verify agent sets tariffs/sanctions aligned with its objectives

### 2C. OPEC decisions
- [ ] Production level (min→max) for OPEC members
- [ ] Context: oil price, budget needs, geopolitical leverage
- [ ] **TEST:** OPEC member (e.g., Solaria) makes sensible production choice

### 2D. Military decisions
- [ ] `decide_action()` returning military actions (attack, blockade, mobilize)
- [ ] Context: military balance, zone control, war status
- [ ] **TEST:** War country (e.g., Sarmatia) makes attack/defend decisions

### 2E. Covert operations
- [ ] `decide_action()` returning covert ops (sabotage, propaganda)
- [ ] Context: intelligence pool, targets, detection risk
- [ ] **TEST:** Agent with intel pool uses it strategically

### 2F. Political actions
- [ ] Propaganda, repression, arrest decisions
- [ ] Context: stability, support, election proximity
- [ ] **TEST:** Leader under pressure uses political levers

### 2G. Active loop — proactive decisions
- [ ] `decide_action()` — full proactive decision (what to do RIGHT NOW)
- [ ] Implements the active loop from SEED E5 Section 4
- [ ] Status lifecycle: IDLE → DECIDING → ACTING → IDLE
- [ ] **TEST:** Agent proactively initiates actions across multiple loop ticks

---

## Phase 3: COMMUNICATION

### 3A. Bilateral conversations
- [ ] `generate_conversation_message()` — produce one turn of dialogue
- [ ] Intent notes (private reasoning before conversation)
- [ ] 8-turn bilateral protocol from DET_C1 C6 Section 5.5
- [ ] **TEST:** Two agents (e.g., Dealer ↔ Helmsman) have a conversation about Formosa

### 3B. Memory update after conversation
- [ ] Priority 1 update: summarize conversation → update Block 3
- [ ] Relationship score adjustment
- [ ] Verify: next decision uses updated memory
- [ ] **TEST:** Agent A talks to Agent B, then talks to Agent C — Agent A remembers what B said

### 3C. Public statements
- [ ] Agent issues public statement (visible to all)
- [ ] **TEST:** Statement is in character, strategically motivated

---

## Phase 4: TRANSACTIONS

### 4A. Transaction proposals
- [ ] Agent proposes deal (arms sale, treaty, basing rights, etc.)
- [ ] Structured output matching transaction types from SEED E5 Section 7
- [ ] **TEST:** Agent proposes arms sale to ally

### 4B. Transaction evaluation
- [ ] `evaluate_proposal()` — accept/reject/counter
- [ ] Context: own needs, relationship, strategic value
- [ ] **TEST:** Counterpart evaluates and responds to proposal

### 4C. Transaction execution
- [ ] Execute via standard Transaction Engine protocol
- [ ] State changes applied (coins, units transferred)
- [ ] Events logged
- [ ] **TEST:** Full cycle: propose → accept → execute → verify state changed

---

## Phase 5: ROUND INTEGRATION

### 5A. Full round loop (single agent)
- [ ] Active loop: deliberate → decide → act → reflect
- [ ] Mandatory submission at round end
- [ ] Memory update after round results
- [ ] **TEST:** One agent plays a full 6-round game solo

### 5B. Full round loop (21 agents)
- [ ] `runner.py` — orchestrate all 21 agents per round
- [ ] Parallel LLM calls where possible
- [ ] Action validation framework
- [ ] **TEST:** 21 agents produce valid actions for 1 round

### 5C. Full unmanned SIM
- [ ] 21 agents × 6 rounds → engine → NOUS → results → memory → next round
- [ ] Conversations between agents during Phase A
- [ ] Transactions proposed and resolved
- [ ] **TEST:** Complete 6-round SIM with all capabilities

---

## Phase 6: OPTION B (Anthropic Persistent Agent)

### 6A. AI Module v2 — Anthropic architecture
- [ ] Same abstract interface (DET_C1 C6)
- [ ] Persistent conversation instead of 4-block rebuild
- [ ] Tool use for actions (submit_budget, propose_treaty, etc.)
- [ ] **TEST:** Same test interface, selector switches between v1/v2

### 6B. Comparison
- [ ] Run same scenario with both implementations
- [ ] Compare: reasoning quality, cost, reliability, memory coherence
- [ ] Decision: adopt v1, v2, or hybrid

---

## Quality Gates

| Gate | Criteria | Required for |
|------|----------|-------------|
| **G1** | Agent initializes, chats coherently in character | Phase 2 |
| **G2** | All mandatory inputs produce valid JSON | Phase 3 |
| **G3** | Agent makes sensible military/covert decisions | Phase 3 |
| **G4** | Two agents converse, memory updates correctly | Phase 4 |
| **G5** | Transactions execute end-to-end | Phase 5 |
| **G6** | Full 6-round SIM completes without errors | Phase 6 |

---

## Documentation Checkpoints

Every 30 minutes of build time, ask:
- [ ] Are the communication interfaces documented?
- [ ] Do action schemas match DET_C1?
- [ ] Is the Context Assembly integration documented?
- [ ] Are any engine interface changes captured?
- [ ] Is the test interface approach documented?

---

## KING Patterns Adopted (from esplzaunxkehuankkwbx)

| Pattern | KING Source | TTT Location | Status |
|---------|-----------|-------------|--------|
| Metacognitive architecture | ai_prompts.block_1_metacognitive_architecture | sim_config prompt_template | ✅ Seeded |
| 4-block cognitive versioning | ai_context table | ai_context table (same pattern) | ✅ Created |
| Conversation behavior prompt | ai_prompts.conversation_behavior | sim_config prompt_template | ✅ Seeded |
| Intent notes | ai_prompts.generate_intent_note | sim_config prompt_template | ✅ Seeded |
| Block reflection prompts | ai_prompts.reflection_update_block_N | sim_config prompt_template | ✅ Seeded |
| Meeting decision prompt | ai_prompts.meeting_decision | sim_config prompt_template | ✅ Seeded |
| Block size limits | ai_prompts.target_block_max_length | memory.py (to implement) | ☐ TODO |
| Update queue (priority batching) | ai_update_queue table | agents/events.py (future) | ☐ TODO |
| Per-run prompt overrides | sim_run_prompts table | sim_config per template (existing) | Partial |
| Prompt management NOT in separate table | — | sim_config (category='prompt_template') | ✅ Decision |

---

## File Structure

```
app/engine/agents/          ← AI Participant module
├── BUILD_PLAN.md           ← THIS FILE (delete when done)
├── __init__.py
├── leader.py               ← LeaderAgent (4-block, abstract interface)
├── profiles.py             ← Role loading, identity generation
├── decisions.py            ← Action schemas, structured output
├── conversations.py        ← 8-turn bilateral engine
├── transactions.py         ← Propose → evaluate → execute
├── memory.py               ← Block management, versioning, compression
├── events.py               ← Event handling, priority queue
├── runner.py               ← Round orchestrator (all 21 agents)
└── chat.py                 ← Debug chat interface

app/test-interface/         ← Test Interface (separate from main app)
├── README.md
├── server.py               ← FastAPI dev server
├── static/                 ← HTML/CSS/JS (Thucydides style)
└── templates/              ← Chat UI, block inspector, context viewer
```
