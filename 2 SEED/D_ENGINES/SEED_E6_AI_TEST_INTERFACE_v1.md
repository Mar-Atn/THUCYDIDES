# AI Test Interface — SEED Specification
## Thucydides Trap SIM
**Version:** 1.0 | **Date:** 2026-04-04 | **Status:** Active (Development Tool)
**Concept reference:** CON_C1 F1 (AI Participant Module)
**Implementation:** `app/test-interface/server.py`, `app/test-interface/templates/index.html`
**Dependencies:** SEED_E5 (AI Participant Module), DET_F5 (API endpoints)

---

## 1. Purpose

The AI Test Interface is a **development tool** for exercising the AI Participant Module in isolation. It is **NOT part of the production application** and is not deployed alongside the main platform.

**Goals:**
- Give developers a fast, visual way to test one role, one decision, or one conversation at a time
- Make the 4-block cognitive state directly inspectable and versionable
- Let prompt-engineering iterations run without spinning up the full FastAPI + DB + Realtime stack
- Provide a stable harness behind which the underlying AI module can be swapped (KING-style 4-block, Anthropic persistent agents, future alternatives)

**Form factor:** Standalone HTTP server on `localhost:8888`. Launched with `cd app && PYTHONPATH=. python3 test-interface/server.py`. No auth, no multi-user support, no persistence beyond process lifetime.

---

## 2. Architecture

**Server:** Python standard library `http.server.HTTPServer` + `SimpleHTTPRequestHandler`. No FastAPI, no Uvicorn, no ASGI. The interface deliberately uses the simplest possible HTTP stack so it can be read, modified, and debugged in minutes.

**Storage:** In-memory only.
- `_agents: dict[str, LeaderAgent]` — keyed by `role_id`, one agent per role
- `_live_bilateral: dict` — scratch space for streaming turns from a running bilateral
- No database, no file persistence. Restart the server and everything is gone.

**Imports:** Direct Python imports from `engine/agents/`:
- `LeaderAgent` from `engine.agents.leader`
- `load_all_roles`, `load_heads_of_state` from `engine.agents.profiles`
- Decision functions from `engine.agents.decisions`
- `ConversationEngine` from `engine.agents.conversations`
- `run_full_sim`, `run_round` from `engine.agents.runner`

**Frontend:** Single `templates/index.html` — static HTML + inline CSS + inline vanilla JavaScript. No React, no build step, no bundler. The browser talks to the server via `fetch` against the JSON endpoints.

**Separation principle:** The interface depends only on the public shape of `LeaderAgent` (`.initialize()`, `.chat()`, `.info()`, `.get_cognitive_state()`, `.get_state_history()`). A different AI module can be plugged in simply by providing a class with the same surface.

---

## 3. UI Layout

Dark desktop-only layout. The window is split 50/50.

**Left panel — Operator controls + transcript:**
- Header: title + "Development tool — not part of main app"
- Role selector: `<select>` populated from `/api/roles`, grouped by Heads of State vs. Other Roles
- Initialize button + "Use LLM" checkbox (toggle between sync init and LLM-generated identity)
- Agent info strip: character name, title, country, status, cognitive version, objectives
- Conversation controls: Start Conversation, End Conversation → Reflect
- Bilateral controls: counterpart dropdown, topic input, Test Bilateral button
- Decision controls: 8 buttons (Budget, Tariffs, Sanctions, OPEC, Military, Covert, Political, Active Loop) color-coded by domain
- SIM controls: Run Full Round, Run Full SIM, rounds selector, ticks selector
- Chat area: scrollable transcript with user / agent / system / bilateral-a / bilateral-b / intent-note message styles
- Chat input: single-line input + Send button

**Right panel — Cognitive state inspector:**
- Version navigator: current version label, ◀ ▶ Latest buttons
- Four collapsible blocks:
  - Block 1: Rules
  - Block 2: Identity
  - Block 3: Memory
  - Block 4: Goals & Strategy
- Each block shows char count + estimated tokens, expands to show full content

**Styling:** Thucydides dark theme — `#0a0e17` background, `#141b2d`/`#1a2340` surfaces, monospace font stack (SF Mono / Fira Code / Consolas), blue (`#4a9eff`) + gold (`#ffd700`) + orange (`#ff6b4a`) + green (`#4aff8b`) accents.

**Mobile:** Not supported. Desktop-only tool.

---

## 4. Capabilities

The interface lets the operator:

1. **Select and initialize any of 40 roles** — 20 Heads of State plus 20 other roles (military chiefs, intelligence directors, diplomats, opposition leaders) loaded from role profiles.
2. **Choose initialization mode** — sync mode (fast, deterministic, no LLM) or LLM mode (generates character identity and initial goals via LLM calls).
3. **Chat with any agent** — single message or full free-form conversation, either sync or LLM-backed.
4. **Start/end conversations** — explicitly frame a conversation so that End triggers the reflection pipeline and updates Memory/Goals/Identity blocks.
5. **Test 8 decision types** individually — budget, tariffs, sanctions, OPEC, military, covert, political, active_loop. Each calls the real decision function with a minimal `round_context` built from the agent's country data.
6. **Run bilateral conversations** between two agents — live-streamed turn by turn via polling (2s interval), with intent notes and reflections shown at the end.
7. **Run a single round** — full round across all 21 Heads of State, configurable active-loop ticks.
8. **Run a full SIM** — multiple rounds end-to-end, configurable rounds and ticks.
9. **Inspect cognitive blocks** — click to expand any of the four blocks, see content plus size metrics.
10. **Navigate block version history** — step backward/forward through every version the agent has been in, or jump to latest.
11. **See intent notes, reflections, and state deltas** — moderator-view output after bilateral conversations and reflection cycles.

---

## 5. API Endpoints

(Cross-reference: `DET_F5` for full request/response schemas.)

**GET endpoints:**
- `GET /` — serves `index.html`
- `GET /api/roles` — lists all roles, grouped by HoS vs. other
- `GET /api/agent/state?role_id=X` — current cognitive state
- `GET /api/agent/history?role_id=X` — full state version history
- `GET /api/agent/bilateral/live?since=N` — polling endpoint for streaming bilateral turns

**POST endpoints:**
- `POST /api/agent/init` — initialize agent (sync or LLM)
- `POST /api/agent/chat` — send single chat message
- `POST /api/agent/start_conversation` — open explicit conversation framing
- `POST /api/agent/end_conversation` — close conversation, trigger reflection
- `POST /api/agent/decide` — run one of the 8 decision types
- `POST /api/agent/bilateral` — run bilateral conversation between two agents
- `POST /api/sim/round` — run a single round (21 HoS)
- `POST /api/sim/run` — run full unmanned simulation (N rounds)

All responses are JSON with `Access-Control-Allow-Origin: *`. Errors surface as `{"error": "..."}` payloads; there is no structured error taxonomy — the interface is development-only.

---

## 6. When to Use

- **Early capability development** — test one decision type at a time as it is being built; see its output and the cognitive state it produced.
- **Prompt engineering** — iterate on prompts quickly without running a full SIM; compare output before and after.
- **Debugging** — inspect *why* an agent made a specific decision by reading Blocks 2–4 at the moment of the decision.
- **Module comparison** — swap AI module v1/v2 behind the same interface and compare behaviour on identical inputs.
- **Demos** — show stakeholders how the AI reasons, in a format that is readable without needing engine or DB context.

---

## 7. Future Versions

Planned enhancements (not yet implemented):
- **Module selector** — switch between KING 4-block, Anthropic persistent agent, and future AI module implementations from the UI.
- **Side-by-side comparison view** — two agents or two module versions reacting to the same prompt.
- **Transcript export** — save conversation + intent notes + reflections as JSON or markdown.
- **Automated test suite integration** — convert recorded interactions into Layer 2/3 regression tests.
- **DB-backed agent state** — optional Supabase persistence so agents survive server restart (currently in-memory only).
- **Multi-operator** — currently assumes one user; add role-based locking if multiple developers share a server.

---

## 8. Relationship to Production

The test interface and the production application **share the same `engine/agents/` module**. The production app wraps that module in FastAPI + Supabase Auth + Realtime channels + a full React frontend; the test interface wraps it in a 500-line stdlib HTTP server and a single HTML file.

**Positioning:**
- The test interface is **scaffolding for agent development**, not a user-facing product.
- As long as the AI Participant Module is under active development, the interface stays. It is the fastest way to see what the agents are doing.
- Once the module is production-ready and stable, the interface can either be (a) deleted or (b) retained as a permanent developer tool (current intent: retain).
- The interface must never accumulate logic that production depends on. If a piece of logic becomes important, it graduates into `engine/agents/` proper.

**Principle Zero implication:** The test interface is a dev tool, but it is a dev tool that ships inside this repository. It must not drift: if the `LeaderAgent` public surface changes, the test interface must be updated in the same commit. Any divergence is a documentation-implementation mismatch and must be reconciled immediately.
