# PHASE: UNMANNED SPACECRAFT

**Status:** Active | **Started:** 2026-04-06 | **Owner:** Marat + Build Team

---

## Mission

Build a fully autonomous simulation where **all 40 AI roles** (20 HoS + military chiefs, intelligence directors, diplomats, opposition, tycoons) play 6-8 rounds of the Thucydides Trap with real consequences, observable in real time. The unmanned mode is a permanent product capability, not scaffolding.

**Phased approach:** Start with 20 HoS (one per country), prove the full loop works, then expand to all 40 roles with multi-role team dynamics.

---

## Definition of Done

### 1. Autonomous AI Participants (target: 8/10 on vision scale)
- All 40 AI roles play 6-8 rounds with genuine strategic reasoning
- 4-block cognitive model active (rules, identity, memory, goals)
- Active decision loop: agents proactively initiate actions, conversations, transactions
- Bilateral conversations (8-turn) with memory reflection after each
- Self-curated memory across rounds (strategic plans, relationship notes, lessons)
- Role-specific behavior: HoS makes strategy, military chief handles combat, tycoons invest, opposition blocks
- Assessed by independent reviewer vs SEED_E5 AI participant vision

### 2. Full Action Space with Real Consequences
- All 32 actions available (per CARD_ACTIONS): military, economic, communication, covert, transactions, domestic
- Exchange transactions: bilateral, asset-validated, immediate execution (coins, units, basing, tech)
- Agreements: bilateral/multilateral, public/secret, free-text terms
- All actions processed by engines with cascading effects
- Plausible outcomes assessed by reviewer (1-10) vs IDEA/CONCEPT

### 3. World Model Engines — Proper & Plausible
- **Economic engine:** oil, GDP, revenue, budget, inflation, debt, sanctions, tariffs, contagion
- **Political engine:** stability, elections, coups, mass protests, war tiredness, capitulation
- **Military engine:** ground combat (RISK iterative + chain), air strikes, missiles (conventional + nuclear T1-T3), naval 1v1, bombardment, blockades (Gulf Gate/Caribe/Formosa)
- **Transaction engine:** exchanges with asset validation + agreements with ceasefire enforcement
- **Real-time action engine:** covert ops (intelligence, sabotage, propaganda, election meddling), domestic political (arrest, assassination, coup, protest)
- All produce plausible, calibrated results. All moderator-dependent actions execute automatically in unmanned mode.

### 4. Observatory — Visual Excellence
- All main events, actions, transactions, military events on maps in real time
- Smart, informative dashboards: military, economic, political parameters
- Ability to see dynamics (round scrubber, charts, deltas)
- Map viewer: global + theater drill-down, battle markers, unit movements, blockade zones
- Follows UX high standards (SEED_H1 Midnight Intelligence style)

### 5. Architecture — Modular, Documented, Reliable
- All modules autonomous with standard communication contracts
- Any module switchable/updatable without major refactoring
- Properly documented (4 reference cards + architecture contracts)
- Dual LLM provider (Gemini + Anthropic) with automatic fallback

### 6. Testing & Calibration
- Systemic local + full test runs completed
- Combat, economic, political formulas calibrated against plausibility
- System and DATA ready for next stage (human interfaces)

---

## Scope Boundaries

### IN scope
- All 32 consolidated actions (per CARD_ACTIONS) — implemented and engine-processed
- All 40 AI roles (phased: 20 HoS first, then full roster)
- AI participant active loop with conversations + transactions
- Full economic/political/military/technology engine chain
- Observatory with 3 screens (Maps, Dashboard, Activity)
- Nuclear program (tests + T1-T3 launch + T3 interception)
- Blockade mechanics (Gulf Gate, Caribe, Formosa with semiconductor impact)
- Covert operations with outcomes (intelligence, sabotage, propaganda, election meddling)
- Domestic politics (arrest, assassination, coup, protest, elections)
- NOUS judgment layer (Pass 2 soft adjustments)
- Template v1.0 data fully seeded and validated

### NOT in scope (next phase)
- Human participant UI (role dashboards, login, real-time input)
- Facilitator controls (pause/adjust mid-sim)
- Voice integration (ElevenLabs)
- Multiple simultaneous sim runs
- Production deployment (Vercel, edge functions)
- Public-facing landing page
- Multilateral meetings (3+ participants — bilateral only for now)

---

## Working References

See `REFERENCES.md` in this directory for pointers to all source material.

See the reference documents (10 files in this directory):

**5 reference cards:**
- `CARD_ACTIONS.md` — complete action catalog (32 actions), current rules, role authorization, consequence chains
- `CARD_FORMULAS.md` — all calibrated coefficients, probabilities, engine formulas (62+ constants), state transitions
- `CARD_ARCHITECTURE.md` — coordinate contract, module contracts, DB schema, round walkthrough, round flow
- `CARD_TEMPLATE.md` — template/scenario/run hierarchy, all data items, sample data
- `CARD_OBSERVATORY.md` — the ONLY interface this phase: 3 screens, data sources, visual standards

**3 design specs:**
- `AI_CONCEPT.md` — AI Participant module: vision, inputs/outputs, contracts, active loop, information scoping
- `TRANSACTION_LOGIC.md` — transaction system: exchange flow, agreement flow, authorization, AI interaction
- `INFORMATION_SCOPING.md` — what each role can see: public/country/role tiers, relationship model, history rule

---

## Current Status (2026-04-10)

### 🟢 Budget vertical slice — DONE end-to-end (2026-04-10)
First mandatory-decision slice complete and locked. CONTRACT_BUDGET v1.1, validator, engine v1.1 (caps removed, level scale, social slider), DB migration (5 mil_* columns), context+dry-run service, AI skill harness, full-chain acceptance gate. All gaps closed (units now persist, R&D progress now persists). 37 L1+L2 tests passing, L3 AI acceptance gate passing. See `CHECKPOINT_BUDGET.md` for the durable record. The 7-step methodology used to ship this is documented as the template for sanctions/tariffs/OPEC in `EVOLVING METHODOLOGY/VERTICAL_SLICE_PATTERN.md`.



### Completed
- Economic engine: 9/10 (all formulas live, calibrated, 98% SEED match)
- Political engine: 8/10 (stability, elections, coups working)
- Technology engine: 7/10 (R&D, rare earth, advancement)
- Combat calibration: ground iterative RISK with chain + modifiers, air 12%/6% + 15% downed, conventional missile 70%, nuclear 80%, naval 1v1, bombardment 10%
- Nuclear program: T1-T3 tiers, tests (underground/surface), interception (voluntary T3+ decision)
- AI agent foundation: LeaderAgent with 4-block cognitive model on Gemini Flash
- Observatory v0.2: 3-screen layout, map viewer parity, battle markers, global dashboard with round scrubber
- Dual-provider LLM: Gemini + Anthropic with auto-fallback
- Engine tick wired: agent actions feed into economic/political engines
- **Phase reference cards completed** (CARD_ACTIONS, CARD_FORMULAS, CARD_ARCHITECTURE, CARD_TEMPLATE)
- Reunification sprint (Phases 0-4): audit, combat port, agent migration to LeaderAgent, deprecation

### In Progress
- Active loop integration (agents proactively decide, converse, transact)
- Expanding action catalog (7→32 wired actions, schema defined, engine wiring needed)
- Covert ops outcome propagation
- Transaction execution flow
- Blockade mechanics implementation (Gulf Gate ground, Formosa semiconductor)

### Not Started
- Full 40-role multi-role team dynamics (20 HoS working, other roles not yet)
- **Information scoping enforcement** (agents see too much — see INFORMATION_SCOPING.md)
- **Transaction execution** (propose/evaluate/execute via transactions.py — see TRANSACTION_LOGIC.md)
- **Agreement flow** (draft/sign/activate with ceasefire enforcement)
- NOUS judgment layer
- Cognitive state DB persistence
- Elections integration into round flow (Columbia scheduled, Ruthenia player-triggered)
- Pre-seeded meetings (Template data)
- Nuclear test confirmation flow
- Seeding CODE fix (data fixed, code still defaults wrong values for new scenarios)
- Remove bond_yield + gold_price from DB + Observatory (not part of SIM)
- Public bio field for roles (exists: name/title/age/faction; needed: 2-3 sentence public bio)
- Bilateral relationship auto-update engine (rule-based state transitions per INFORMATION_SCOPING.md)
- Full 50+ test run calibration cycle

---

## Plan of Work

### Testing Protocol (applies to ALL sprints)

| Layer | What | When | Cost | Duration |
|---|---|---|---|---|
| **L1: Unit tests** | Pure function tests — combat dice, formulas, probabilities, chain mechanics | After every code change | Free | Seconds |
| **L2: Integration tests** | DB round-trip — decisions → engine → snapshots written, schema validation | After wiring changes | Free (DB only) | Seconds |
| **L3: Single-agent smoke** | One agent on Gemini commits one action end-to-end | After agent/LLM code changes | ~$0.01 | ~15s |
| **L4: Full system test** | 20+ agents, 2-3 rounds, observatory review | When Marat review needed — plausibility, UX, behavior | ~$2-5 | 2-3 min |

**Rules:**
- L1 must pass before any commit. No exceptions.
- L2 must pass before wiring a new action type.
- L3 run once per sprint task completion.
- L4 run only at sprint milestones or when Marat's judgment needed.
- Test suites live in `app/tests/` mirroring engine structure.

**Acceptance gate (before reporting DONE):**
- Feature must produce REAL DB state change — not just event logs
- At least 1 concrete example verified by DB query
- Honest status: **DONE** (works e2e) vs **WIRED** (code exists, incomplete) vs **STUB** (placeholder)
- Never report event counts as outcomes (e.g., "29 transactions proposed" ≠ "29 deals done")

### Sprint A: Action Space + Engine Wiring (~3 days)
- Wire all 32 actions into agent tool schema + resolve_round processing
- Ground attack chain mechanic (RISK faithful)
- Connect sanctions/tariffs/blockades to economic engine with real cascade
- Covert ops outcomes affect stability/economy/tech
- Transaction execution (exchanges: asset validation + immediate execution; agreements: recording + ceasefire enforcement)

### Sprint B: Active Loop + Conversations (~3-4 days)
- ✅ B1: Multi-action per round (up to 3 commits per agent, prompt guides quality)
- B6: Mandatory decisions system (budget/sanctions/tariffs/OPEC prompt before round end): **BUDGET DONE** ✅ 2026-04-10 (CONTRACT v1.1, full vertical slice, AI acceptance gate green — see CHECKPOINT_BUDGET.md). Sanctions/tariffs/OPEC remaining — follow VERTICAL_SLICE_PATTERN.md.
- B7: Inter-round relocation phase (deploy/redeploy between rounds, separate from in-round): **NOT STARTED** *(added 2026-04-08)*
- B8: Scripted battery testing (pre-scripted decisions, no LLM, full engine chain validation in `app/tests/layer2/`): **IN PROGRESS** *(added 2026-04-08)*
- B2: Bilateral conversations — THE core feature:
  - Orchestrator pairs two agents for 8-turn exchange
  - Both generate intent notes before, reflect after
  - Code exists (`agents/conversations.py`) — needs orchestration wiring
  - Architecture: current parallel agents → need sequential pairing within round
  - Design: SEED_E5 §4 + §6
- B3: Memory reflection after each conversation (Block 3 update)
- B4: Event reactions (combat/sanction/alliance triggers agent response)
- B5: Context Assembly Service wired for intelligence reports + decision context

### Sprint C: Full Engine Chain + Multi-Role (~3 days)
- Expand from 20 HoS to all 40 roles
- Role-specific action permissions enforced (per CARD_ACTIONS role authorization)
- NOUS judgment (Pass 2) wired into round flow
- Elections: Columbia automatic (R2, R5), Ruthenia player-triggered
- Domestic political actions automatic in unmanned mode
- Post-round reflection updating Goals (Block 4)
- Cognitive state persisted to DB

### Sprint D: Observatory Polish (~2 days)
- Battle visualization in theater view
- Transaction/conversation feed in Activity
- Country detail drawer (full stats + agent reasoning + memory)
- Blockade visualization (from declared actions)
- Visual polish to UX guide standards

### Sprint E: Calibration at Scale (~3 days)
- 50+ unmanned runs (full 40-role roster)
- Plausibility assessment per domain
- Formula tuning based on outcomes
- Degenerate strategy detection
- Final documentation reconciliation
