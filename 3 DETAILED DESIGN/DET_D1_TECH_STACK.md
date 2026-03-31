# DET_D1_TECH_STACK.md
## TTT Detailed Design -- Definitive Technology Stack
**Version:** 1.0 | **Date:** 2026-03-30 | **Status:** DRAFT
**Owner:** NOVA (Backend) + FELIX (Frontend)
**Cross-references:** [G1 Web App Architecture](../1.%20CONCEPT/CONCEPT%20V%202.0/CON_G1_WEB_APP_ARCHITECTURE_v2.frozen.md) | [SEED G Web App Spec](../2%20SEED/G_WEB_APP/SEED_G_WEB_APP_SPEC_v1.md) | [H1 UX Style](../2%20SEED/H_VISUAL/SEED_H1_UX_STYLE_v2.md) | [F4 API Contracts](../2%20SEED/F_DATA_ARCHITECTURE/SEED_F4_API_CONTRACTS_v1.md) | [KING Tech Guide](../../CODING/KING/app/KING_TECH_GUIDE.md)

---

# PURPOSE

This document is the single source of truth for every technology choice in the TTT web application. Developers follow this -- no technology may be introduced into the codebase that is not listed here or explicitly approved as an addition to this document.

Every choice is justified. Where alternatives were considered, they are noted. Where KING SIM provides precedent, it is cited.

---

# 1. FRONTEND

## 1.1 Framework: React 18+ with TypeScript

| Property | Value |
|----------|-------|
| **Package** | `react` ^18.3, `react-dom` ^18.3 |
| **Language** | TypeScript ~5.5+ (strict mode) |
| **Why React** | Proven in KING SIM (React 19). Largest ecosystem for real-time dashboards. Component model maps naturally to TTT's per-role, per-country, per-view architecture. Team has production experience. |
| **Why not Next.js** | TTT is a real-time SPA, not a content site. SSR adds complexity with no benefit -- all data comes from Supabase Realtime subscriptions, not static pages. Vercel deploys Vite SPAs natively. |
| **Why not Vue/Svelte** | No team precedent. React + Supabase integration is the most documented path. |

## 1.2 Build Tool: Vite

| Property | Value |
|----------|-------|
| **Package** | `vite` ^5.4+ |
| **Why Vite** | Proven in KING SIM (Vite 7.x). Near-instant HMR during development. Native TypeScript and JSX support. Tree-shaking and code splitting out of the box. |
| **Why not Webpack** | Slower dev server, more configuration. No advantage for this project. |

## 1.3 Styling: Tailwind CSS with TTT Theme

| Property | Value |
|----------|-------|
| **Package** | `tailwindcss` ^3.4+ |
| **Config** | TTT-specific theme as defined in `SEED_H1_UX_STYLE_v2.md` Section 10 |
| **Why Tailwind** | Proven in KING SIM. Utility-first approach maps directly to the design token system (colors, spacing, typography). The entire TTT color system (22 country palettes, dual theme, semantic colors) is already expressed as a Tailwind config. |
| **Theme tokens** | `base`, `card`, `border`, `text-primary`, `text-secondary`, `action`, `accent`, `success`, `warning`, `danger`, plus 22 `country.*` keys with `DEFAULT`/`map`/`light` variants. |
| **Dark mode** | CSS `class` strategy (not `media`). Toggle stored in localStorage. Both "Strategic Paper" (light) and "Midnight Intelligence" (dark) themes use the same Tailwind config with `dark:` prefixes. |
| **Font loading** | Google Fonts via `@fontsource` packages (self-hosted, no external CDN dependency during SIM): `@fontsource/playfair-display`, `@fontsource/dm-sans`, `@fontsource/jetbrains-mono`. |

### Tailwind Configuration (from H1 Style Guide)

```javascript
// tailwind.config.js -- TTT theme (frozen at SEED)
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        base: { DEFAULT: '#F5F6F8', dark: '#0D1B2A' },
        card: { DEFAULT: '#FFFFFF', dark: '#1B2A3E' },
        border: { DEFAULT: '#D8DCE5', dark: '#253D54' },
        text: { primary: '#1A2332', secondary: '#4A5568', muted: '#8494A7' },
        action: { DEFAULT: '#1A5276', dark: '#5B9BD5' },
        accent: { DEFAULT: '#C4922A', dark: '#E8B84D' },
        success: { DEFAULT: '#2E7D4F', dark: '#5BAD7A' },
        warning: { DEFAULT: '#B8762E', dark: '#D4A040' },
        danger: { DEFAULT: '#B03A3A', dark: '#D45B5B' },
        country: {
          // 22 countries -- see H1 Style Guide Section 3 for full list
          columbia: { DEFAULT: '#3A6B9F', map: '#9AB5D0', light: '#E8EFF6' },
          cathay:   { DEFAULT: '#C4A030', map: '#E8D5A3', light: '#F8F2E5' },
          // ... (all 22 country palettes per H1)
        }
      },
      fontFamily: {
        heading: ['Playfair Display', 'Georgia', 'serif'],
        body: ['DM Sans', 'system-ui', 'sans-serif'],
        data: ['JetBrains Mono', 'monospace'],
      },
    }
  }
}
```

## 1.4 State Management: Zustand

| Property | Value |
|----------|-------|
| **Package** | `zustand` ^4.5+ |
| **Why Zustand** | Proven in KING SIM (Zustand 5.x, 5 stores). Minimal boilerplate. Works naturally with Supabase Realtime -- subscription callbacks write directly to store, components re-render automatically. No provider nesting. TypeScript-friendly. |
| **Why not React Context** | Context causes re-renders in all consumers when any value changes. TTT has high-frequency state updates (real-time events, timer ticks, map updates). Zustand's selector-based subscriptions prevent unnecessary re-renders -- critical for 40+ concurrent users on potentially limited devices (phones). |
| **Why not Redux** | Excessive boilerplate for this use case. Zustand provides the same centralized store pattern with 90% less code. |

### Planned Stores

| Store | Responsibility | Update frequency |
|-------|---------------|-----------------|
| `worldStateStore` | Current world state (countries, zones, oil price, wars) | Per round + real-time deltas |
| `roleStore` | Current user's role, permissions, personal assets | Session + real-time |
| `eventStore` | Event log (paginated, filtered by visibility) | Real-time (high frequency during Phase A) |
| `timerStore` | Round phase, countdown, scheduled events | Every second during active play |
| `uiStore` | Theme, panel visibility, map zoom, selected filters | User interaction only |
| `mapStore` | Zone states, force positions, theater focus | Per round + real-time combat updates |

## 1.5 Real-Time: Supabase Realtime (WebSocket)

| Property | Value |
|----------|-------|
| **Package** | `@supabase/supabase-js` ^2.76+ (includes Realtime client) |
| **Transport** | WebSocket via Supabase Realtime |
| **Channels** | PostgreSQL Changes (table inserts/updates) + Broadcast (ephemeral events) |
| **Why Supabase Realtime** | Single infrastructure provider. RLS policies apply to Realtime subscriptions -- information asymmetry enforced at the database level. KING SIM proved this works for real-time multiplayer. |

### Channel Architecture (per F4 API Contracts Section 7)

| Channel | Subscribers | Content |
|---------|------------|---------|
| `public` | All authenticated users | Oil price, war declarations, election results, announcements |
| `country:{id}` | Country team members | Economic updates, military status, team messages |
| `role:{id}` | Specific role | Personal coin changes, intelligence reports, transaction notifications |
| `moderator` | Facilitator only | Engine diagnostics, coherence flags, AI agent status |
| `timer` (Broadcast) | All | Phase countdown ticks, phase transitions |

### Reconnection Protocol

On disconnect + reconnect:
1. Client stores last known `snapshot_version` per subscribed channel.
2. On reconnect, client fetches missed events via REST: `GET /api/v1/events/{round}?cursor={last_event_id}`.
3. Applies missed state deltas sequentially.
4. If version gap > 50, fetches full state snapshot instead.

## 1.6 Charts: Recharts

| Property | Value |
|----------|-------|
| **Package** | `recharts` ^2.12+ |
| **Why Recharts** | React-native component API (declarative JSX, not imperative canvas). Composable -- custom tooltips, responsive containers, animation control. Lighter than Chart.js for React integration (Chart.js requires a wrapper like `react-chartjs-2` and imperative config). |
| **Why not Chart.js** | Chart.js is canvas-based, which means custom styling (TTT fonts, country colors) requires more work. Recharts renders SVG, making it trivial to apply Tailwind classes and TTT color tokens. |
| **Why not D3 directly** | D3 is too low-level for dashboards. Recharts is built on D3 internals but provides the chart-level abstractions we need (line, bar, area, radar). |

### Chart Types Required

| Chart | Usage | Component |
|-------|-------|-----------|
| GDP comparison (Columbia vs Cathay) | W4 Global Dashboard | `<BarChart>` with country colors |
| Oil price trend | W4 Global Dashboard | `<LineChart>` with accent color |
| Budget allocation | Budget form + country dashboard | `<PieChart>` or stacked `<BarChart>` |
| Military strength comparison | Country dashboard | Horizontal `<BarChart>` |
| Stability / support trend | Country dashboard | `<AreaChart>` with danger zones |
| Economic indicators (multi-line) | Moderator dashboard | `<ComposedChart>` |

## 1.7 Maps: Custom SVG Hex Renderer

| Property | Value |
|----------|-------|
| **Implementation** | Custom React components rendering SVG hexagons |
| **No external map library** | Leaflet, Mapbox, D3-geo are all designed for geographic maps. TTT uses abstract hex grids (10x20 global, 10x10 theater) with fictional territories. A custom renderer is simpler and gives full control over the visual language defined in H1. |
| **Data source** | `SEED_C1_MAP_GLOBAL_STATE_v4.json` (zone definitions, adjacency, ownership) |
| **Rendering** | SVG `<polygon>` elements with country map colors at 55% opacity. Unit icons as SVG groups positioned at hex centroids. Chokepoint markers. Theater zoom views. |
| **Interaction** | Click hex to see zone details. Hover for tooltip (zone name, owner, visible forces). Pan/zoom via SVG `viewBox` manipulation. Theater toggle (global / Eastern Ereb / West Pacific / Gulf). |
| **Unit icons** | SVG paths from `UNIT_ICONS_CONFIRMED.svg` -- tank, warship, drone, radar, missile. Colored per owning country's UI color. Stacking rules per H1 Section 6. |

## 1.8 Additional Frontend Libraries

| Library | Purpose | Package |
|---------|---------|---------|
| React Router | Client-side routing (participant/facilitator/public routes) | `react-router-dom` ^6.23+ |
| Framer Motion | Panel transitions, dice animations, map zoom | `framer-motion` ^11+ |
| Lucide React | Icon set (consistent, tree-shakeable) | `lucide-react` |
| Headless UI | Accessible dropdowns, modals, tabs (unstyled) | `@headlessui/react` ^2+ |
| Zod | Runtime schema validation (form inputs, API responses) | `zod` ^3.23+ |
| TanStack Query | Server state caching + background refetch for REST calls | `@tanstack/react-query` ^5+ |
| date-fns | Date formatting (round timestamps, countdown) | `date-fns` ^3+ |

## 1.9 Deployment: Vercel

| Property | Value |
|----------|-------|
| **Platform** | Vercel (free tier sufficient for development; Pro for SIM day) |
| **Build** | `vite build` triggered on push to `main` |
| **Preview** | Automatic preview deployments on PRs |
| **Why Vercel** | Proven in KING SIM. Zero-config Vite deployment. Global CDN. Preview deployments for facilitator review. |

---

# 2. BACKEND / DATABASE

## 2.1 Database: Supabase (PostgreSQL)

| Property | Value |
|----------|-------|
| **Provider** | Supabase Cloud |
| **Engine** | PostgreSQL 15+ |
| **Client** | `@supabase/supabase-js` ^2.76+ |
| **Why Supabase** | Proven in KING SIM. Combines database, auth, real-time, storage, edge functions in one platform. RLS enforces information asymmetry at the database level -- critical for TTT where each participant sees different data. Eliminates the need for a separate backend for most CRUD operations. |
| **Why not Firebase** | PostgreSQL is required for relational data (countries, roles, zones, bilateral relationships, event log with complex queries). Firestore's document model does not support the join-heavy queries TTT needs (e.g., "all events visible to this role in this round affecting this country"). |
| **Why not raw PostgreSQL** | Would require building auth, real-time, storage, and API layer from scratch. Supabase provides all of these with the same PostgreSQL underneath. |

### Key Schema Areas

Per `SEED_F2_DATA_ARCHITECTURE_v1.md`:

| Area | Tables | RLS Policy |
|------|--------|-----------|
| World state | `world_state_snapshots`, `country_states`, `zone_states` | Moderator: full. Participant: own country + public tier. |
| Events | `events` | Filtered by `visibility` column (public/country/role/moderator) matched against JWT claims. |
| Users & roles | `users`, `role_assignments`, `sim_runs` | Own data + moderator. |
| Transactions | `transactions` | Proposer + counterparty + moderator. |
| AI state | `ai_cognitive_states`, `ai_decision_logs` | Moderator only. |
| Communications | `messages`, `meeting_transcripts` | Participants in the conversation + moderator. |
| Argus | `argus_conversations`, `argus_transcripts` | Owning participant + moderator. |

## 2.2 Auth: Supabase Auth

| Property | Value |
|----------|-------|
| **Method** | Email + magic link (passwordless) |
| **Why magic link** | Participants are non-technical corporate leaders. Password creation/management during a high-pressure SIM day is friction. Magic link: enter email, click link, done. KING SIM used the same approach. |
| **Fallback** | Email + password (for facilitators who log in repeatedly). |
| **JWT claims** | Custom claims include: `sim_id`, `role_id`, `country_id`, `access_level`. Set via Supabase Auth hooks on login. Used by RLS policies for row-level filtering. |
| **Access levels** | `participant` (role-filtered view), `moderator` (god view), `spectator` (public tier only), `admin` (system-level). |

## 2.3 Storage: Supabase Storage

| Property | Value |
|----------|-------|
| **Provider** | Supabase Storage |
| **Buckets** | `role-briefs` (PDF/HTML), `audio` (voice recordings), `maps` (SVG exports), `exports` (session reports) |
| **Access** | RLS policies mirror database access. Role briefs accessible only to assigned participant + moderator. Audio accessible only to conversation participants + moderator. |
| **Why Supabase Storage** | Same auth tokens, same RLS model, same dashboard. No additional infrastructure. |

## 2.4 Row-Level Security (RLS)

RLS is the enforcement mechanism for TTT's information asymmetry. Every database query is filtered server-side based on the JWT claims of the requesting user. This means:

- A participant querying `country_states` sees only their own country's data.
- A participant querying `events` sees only events where `visibility` matches their access (public, own country, own role).
- A moderator sees everything.
- A spectator sees only public-tier data.

**This is not optional.** RLS must be enabled on every table containing game data. The frontend UI also filters (for UX), but RLS is the security boundary. Even if the frontend is compromised, the database enforces information asymmetry.

## 2.5 Edge Functions: Supabase Edge Functions (Deno)

| Property | Value |
|----------|-------|
| **Runtime** | Deno (Supabase Edge Functions) |
| **Language** | TypeScript |
| **Use cases** | (1) Proxy calls to Python engine server. (2) AI API calls (Claude, ElevenLabs). (3) Server-side validation that cannot be done in RLS alone. (4) Webhook handlers (e.g., auth hooks for JWT custom claims). |
| **Why Edge Functions** | Keep server-side logic within the Supabase ecosystem. No separate backend needed for lightweight operations. Cold starts are acceptable for non-latency-critical paths. |
| **What they do NOT do** | Heavy computation. The Python engine runs on its own server (see Section 3). Edge Functions proxy requests to it. |

---

# 3. ENGINE LAYER

## 3.1 Language: Python 3.11+

| Property | Value |
|----------|-------|
| **Version** | Python 3.11+ (for performance improvements and `ExceptionGroup` support) |
| **Why Python** | The four engine files (`world_model_engine.py`, `live_action_engine.py`, `transaction_engine.py`, `world_state.py`) are already written and tested in Python. They contain ~3,000+ lines of validated, calibrated simulation logic. Rewriting in TypeScript/Deno would be high-risk with zero benefit. |
| **Dependencies** | Standard library only (no heavy frameworks). `math`, `random`, `copy`, `json`, `csv`. FastAPI added as the HTTP wrapper. |

## 3.2 Framework: FastAPI

| Property | Value |
|----------|-------|
| **Package** | `fastapi` ^0.111+, `uvicorn` ^0.30+ |
| **Why FastAPI** | Native async support. Automatic OpenAPI docs. Pydantic models for request/response validation. Type hints match the engine's existing type annotations. |
| **Why not Flask** | Flask is synchronous by default. FastAPI's async is needed for the AI API calls in Pass 2 (3 parallel LLM calls). |
| **Why not Django** | Too heavy. No ORM needed (engine reads from JSON/CSV, writes to JSON). No template rendering. |

## 3.3 Hosting: Railway (Dedicated Server)

| Property | Value |
|----------|-------|
| **Platform** | Railway (primary) or Render (fallback) |
| **Why dedicated server** | The World Model Engine processes all 20+ countries in a single batch (Pass 1 + Pass 2 + Pass 3). Pass 2 makes 3 parallel LLM API calls. Pass 3 runs coherence checks. Total processing: up to 5 minutes per round. This exceeds Supabase Edge Function limits (50s execution, 150MB memory). A dedicated server with persistent state also allows the engine to hold `WorldState` in memory between calls, avoiding re-serialization. |
| **Why not Supabase Edge Functions for engine** | Deno runtime does not run Python. Even if transpiled, the execution time limits (50 seconds) cannot accommodate a full round processing cycle. |
| **Why not AWS Lambda** | Cold starts unacceptable for live action engine (needs < 2 second response). Lambda's 15-minute timeout is fine, but cold start + Python dependency loading adds 3-5 seconds. Railway provides always-warm instances. |
| **Scaling** | Single instance sufficient. TTT runs one SIM at a time with 40 users. The engine processes sequentially (by design -- chained formulas). No horizontal scaling needed. |
| **Cost** | Railway Hobby plan (~$5/month) or Pro ($20/month). Negligible. |

### Deployment Architecture

```
Frontend (Vercel)
    |
    v
Supabase Edge Functions (Deno)
    |
    |-- Direct DB operations (reads, writes, auth)
    |-- AI API calls (Claude, ElevenLabs)
    |
    v
Python Engine Server (Railway)
    |
    |-- FastAPI endpoints
    |-- world_model_engine.py
    |-- live_action_engine.py
    |-- transaction_engine.py
    |-- world_state.py
    |
    v
Supabase PostgreSQL (via REST or direct connection)
```

**Communication flow:**

1. **Participant submits action** (frontend) --> Supabase Edge Function validates auth + writes to `events` table.
2. **Live action** (combat, covert op) --> Edge Function calls `POST /engine/action` on Railway server --> engine resolves --> result written to Supabase via REST.
3. **Transaction** --> Edge Function calls `POST /engine/transaction` on Railway --> engine validates + executes --> state changes written to Supabase.
4. **Round processing** (facilitator triggers) --> Edge Function calls `POST /engine/round/process` on Railway --> engine runs full 3-pass cycle --> new world state written to Supabase --> Realtime pushes updates to all clients.

## 3.4 Engine Files (from SEED)

| File | Lines | Role |
|------|-------|------|
| `world_state.py` | ~400 | Shared state model. Constants, data loading, serialization. |
| `world_model_engine.py` | ~2,500 | Between-round batch processing. 14-step chained formula pipeline + 3-pass architecture. |
| `live_action_engine.py` | ~800 | Real-time unilateral actions (combat, covert ops, political actions). |
| `transaction_engine.py` | ~400 | Real-time bilateral transfers (coins, arms, tech, treaties). |

These files are the validated SEED engine. They will be wrapped by FastAPI routes (defined in `DET_F5_ENGINE_API.md`) without modifying their internal logic.

---

# 4. AI LAYER

## 4.1 Primary LLM: Anthropic Claude

| Property | Value |
|----------|-------|
| **Provider** | Anthropic |
| **Model** | Claude Sonnet (primary for AI participants + Argus) |
| **Upgrade path** | Claude Opus for complex multi-agent reasoning if needed |
| **SDK** | `@anthropic-ai/sdk` (TypeScript, from Edge Functions) or `anthropic` (Python, from engine server) |
| **Why Claude** | Superior at following complex system prompts (critical for AI participant character fidelity). Better at maintaining persona consistency across long conversations. Structured output support (JSON mode) for action submissions. 200K context window accommodates full role brief + world state + conversation history. |
| **Why not Gemini as primary** | KING SIM used Gemini (2.5 Pro + 2.5 Flash). While functional, character consistency was harder to maintain across extended sessions. Claude's instruction-following is stronger for the complex persona + strategic reasoning + action output format TTT requires. |

### AI Use Cases

| Use Case | Model | Called From | Frequency |
|----------|-------|------------|-----------|
| AI participant deliberation | Claude Sonnet | Engine server (Python) | 10 calls per round (one per AI country) |
| AI participant negotiation | Claude Sonnet | Engine server (Python) | Variable (5-20 per round) |
| Argus advisory conversations | Claude Sonnet | Edge Function (TypeScript) | On-demand per participant |
| World Model Pass 2 (expert panel) | Claude Sonnet | Engine server (Python) | 3 parallel calls per round |
| World Model Pass 3 (coherence + narrative) | Claude Sonnet | Engine server (Python) | 1 call per round |
| Event summarization | Claude Haiku | Edge Function (TypeScript) | Per event batch |

### Context Management

Per the 7-block prompt structure from E4:

```
Block 1: System identity (character persona, 500-800 tokens)
Block 2: World state (current round, own country, visible world, 2000-4000 tokens)
Block 3: Role brief (objectives, powers, relationships, 1000-2000 tokens)
Block 4: Recent events (last 2 rounds, filtered by visibility, 500-1500 tokens)
Block 5: Conversation history (if in negotiation, 500-2000 tokens)
Block 6: Available actions (with constraints, 300-800 tokens)
Block 7: Output format instructions (200-400 tokens)

Total: ~5,000-11,500 tokens per call (well within 200K limit)
```

## 4.2 Secondary AI: Google Gemini

| Property | Value |
|----------|-------|
| **Provider** | Google |
| **Model** | Gemini 2.5 Flash (for secondary tasks) |
| **SDK** | `@google/genai` (TypeScript) |
| **Use cases** | Image generation (map illustrations for public display), backup if Claude API is down, translation of materials. |
| **Why kept as secondary** | KING SIM proved Gemini works. Having a fallback LLM provider prevents single-provider dependency during a live SIM. |

## 4.3 Voice: ElevenLabs

| Property | Value |
|----------|-------|
| **Provider** | ElevenLabs |
| **SDK** | `@elevenlabs/react` (frontend), ElevenLabs REST API (from Edge Functions) |
| **Use cases** | Argus voice output (text-to-speech for the AI assistant). AI participant voice in meetings (if voice mode enabled). |
| **Why ElevenLabs** | Proven in KING SIM. Low-latency streaming. Custom voice cloning for Argus character voice. Conversational AI mode supports real-time voice dialogue. |
| **Fallback** | Browser-native `SpeechSynthesis` API (lower quality, but zero-dependency). |

## 4.4 Voice Input: Web Speech API

| Property | Value |
|----------|-------|
| **API** | Browser-native `SpeechRecognition` / `webkitSpeechRecognition` |
| **Use case** | Argus voice input (participant speaks, browser transcribes, text sent to Claude). |
| **Why browser-native** | Zero additional infrastructure. Works offline-to-online. Sufficient accuracy for English conversational speech. |
| **Limitation** | Chrome/Edge only (Safari support is partial). Acceptable -- facilitator controls browser choice for SIM day. |

---

# 5. AUDIO / RECORDING

## 5.1 Meeting Recording

| Property | Value |
|----------|-------|
| **API** | Browser `MediaRecorder` API |
| **Format** | WebM/Opus (browser default) or WAV |
| **Storage** | Uploaded to Supabase Storage (`audio` bucket) on recording end |
| **Use case** | AI participant voice meetings. Argus voice sessions. Optional: facilitator records physical room audio via separate device. |

## 5.2 Transcription

| Property | Value |
|----------|-------|
| **Primary** | Deepgram API (real-time streaming transcription) |
| **Fallback** | OpenAI Whisper API (batch transcription) |
| **Why Deepgram primary** | Real-time streaming support (transcript appears as participant speaks). Lower latency than Whisper for live use. Speaker diarization built in. |
| **Why Whisper as fallback** | Higher accuracy for post-session batch processing. No real-time requirement for session export. |

## 5.3 Speaker Diarization

| Property | Value |
|----------|-------|
| **Provider** | Deepgram (built into transcription API) |
| **Fallback** | `pyannote` (Python, run on engine server for batch processing) |
| **Use case** | Identifying who said what in multi-party meetings (AI participant meetings with multiple human attendees). |

---

# 6. DEVOPS

## 6.1 Version Control

| Property | Value |
|----------|-------|
| **Platform** | GitHub (`https://github.com/Mar-Atn/THUCYDIDES`) |
| **Branch strategy** | `main` (production), feature branches for development |
| **Commit prefixes** | `app:`, `engine:`, `design:`, `fix:`, `docs:` (per CLAUDE.md Section 4.4) |
| **No force-pushes to main** | Enforced via branch protection rules |

## 6.2 CI/CD

| Property | Value |
|----------|-------|
| **Frontend** | Vercel auto-deploy on push to `main`. Preview deploys on PRs. |
| **Engine server** | Railway auto-deploy on push to `main` (from `APP/engine/` directory). |
| **Tests** | GitHub Actions: `vitest run` (frontend), `pytest` (engine) on every PR. |

## 6.3 Monitoring

| Property | Value |
|----------|-------|
| **Frontend** | Vercel Analytics (Web Vitals, traffic). |
| **Database** | Supabase Dashboard (query performance, connection count, storage usage). |
| **Engine** | Railway metrics (CPU, memory, request latency). |
| **Error tracking** | Sentry (`@sentry/react` for frontend, `sentry-sdk` for Python engine). |
| **Why Sentry** | During a live SIM with 40 users, errors must surface immediately. Sentry provides real-time error alerts with stack traces. Free tier sufficient for development; Team plan for SIM day. |

## 6.4 Testing

| Property | Value |
|----------|-------|
| **Frontend unit tests** | Vitest + React Testing Library |
| **Engine unit tests** | pytest (existing test suite from SEED: `run_seed_test.py`, `test_orchestrator.py`) |
| **Integration tests** | Playwright (end-to-end browser tests against Supabase local dev) |
| **Load testing** | k6 (simulate 40 concurrent WebSocket connections + API calls) |
| **Why Vitest** | Same config as Vite. Jest-compatible API. Proven in KING SIM. |

---

# 7. COMPLETE DEPENDENCY MANIFEST

## Frontend (`package.json`)

```
Core:
  react, react-dom                    ^18.3
  typescript                          ~5.5
  vite                                ^5.4

Routing & State:
  react-router-dom                    ^6.23
  zustand                             ^4.5
  @tanstack/react-query               ^5

UI:
  tailwindcss                         ^3.4
  @headlessui/react                   ^2
  lucide-react                        latest
  framer-motion                       ^11
  recharts                            ^2.12

Data:
  @supabase/supabase-js               ^2.76
  zod                                 ^3.23
  date-fns                            ^3

AI / Voice:
  @anthropic-ai/sdk                   latest
  @elevenlabs/react                   latest

Fonts:
  @fontsource/playfair-display        latest
  @fontsource/dm-sans                 latest
  @fontsource/jetbrains-mono          latest

Monitoring:
  @sentry/react                       latest

Dev:
  vitest                              ^1
  @testing-library/react              ^15
  playwright                          latest
```

## Engine Server (`requirements.txt`)

```
fastapi>=0.111
uvicorn>=0.30
pydantic>=2.7
httpx>=0.27              # Async HTTP client for Supabase REST + Claude API
anthropic>=0.25          # Claude SDK
sentry-sdk[fastapi]      # Error tracking
pytest>=8.2              # Testing
```

---

# 8. INTEGRATION MAP

```
                    +-----------------+
                    |    VERCEL       |
                    |  (React SPA)   |
                    +-------+---------+
                            |
              +-------------+-------------+
              |                           |
    +---------v---------+      +----------v----------+
    |  SUPABASE CLOUD   |      |  SUPABASE EDGE FN   |
    |                   |      |  (Deno/TypeScript)   |
    | PostgreSQL + RLS  |      |                      |
    | Realtime (WS)     |<---->| Auth hooks           |
    | Storage           |      | Claude API proxy     |
    | Auth              |      | ElevenLabs proxy     |
    +-------------------+      | Engine server proxy  |
                               +----------+-----------+
                                          |
                               +----------v-----------+
                               |  RAILWAY              |
                               |  (Python FastAPI)     |
                               |                       |
                               | world_model_engine    |
                               | live_action_engine    |
                               | transaction_engine    |
                               | world_state           |
                               |                       |
                               | Claude API (Pass 2/3) |
                               +-----------------------+
```

---

# 9. DECISION LOG

| Decision | Alternatives Considered | Rationale | Reversibility |
|----------|------------------------|-----------|---------------|
| React over Next.js | Next.js, Remix | SPA with real-time data; SSR adds no value | Low (framework change) |
| Zustand over Context | React Context, Redux, Jotai | Selector-based re-renders; KING precedent | Medium |
| Recharts over Chart.js | Chart.js, D3, Nivo | SVG output; React-native API; Tailwind integration | High (swap library) |
| Custom hex map | Leaflet, Mapbox, D3-geo | Abstract hex grid; full visual control | N/A (custom either way) |
| Claude over Gemini (primary) | Gemini 2.5 Pro, GPT-4o | Instruction-following; persona consistency | High (swap provider) |
| Railway over Lambda | AWS Lambda, Fly.io, Render | Always-warm; no cold starts; persistent state | High (swap host) |
| Deepgram over Whisper (real-time) | Whisper, AssemblyAI | Streaming transcription; built-in diarization | High (swap provider) |
| Sentry for error tracking | LogRocket, Datadog, none | Real-time alerts; free tier; proven | High (swap provider) |
| Magic link auth | Password, OAuth, SSO | Minimal friction for corporate participants | Medium |

---

*This document is the definitive technology reference for TTT app development. Any technology addition or substitution requires updating this document first, with justification. Follow the precedent: justify the choice, note alternatives, assess reversibility.*
