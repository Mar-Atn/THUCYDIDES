# REFERENCES — Unmanned Spacecraft Phase

Pointers to all source material. **Check HERE first** before searching the full tree.

---

## Reference Cards (this directory) — PRIMARY working documents

| Doc | What | When to use |
|---|---|---|
| **`CARD_ACTIONS.md`** | All 32 actions: fields, mechanics, probabilities, role auth, consequence chains | Implementing any action, checking rules |
| **`CARD_FORMULAS.md`** | All calibrated constants, engine formulas, processing order, state transitions | Any engine formula work, calibration |
| **`CARD_ARCHITECTURE.md`** | Coordinate contract, module map, round walkthrough, round flow, DB schema | Any structural/wiring work, DB changes |
| **`CARD_TEMPLATE.md`** | Template/scenario/run hierarchy, all data items, sample data | Data seeding, scenario config, new Template items |
| **`CARD_OBSERVATORY.md`** | The ONLY interface: 3 screens, data sources, visual standards | Any UI/Observatory work |
| **`AI_CONCEPT.md`** | AI Participant module: vision, inputs/outputs, contracts, active loop | Any AI agent architecture work |
| **`TRANSACTION_LOGIC.md`** | Transaction system: exchange + agreement flows, authorization | Transaction/agreement implementation |
| **`INFORMATION_SCOPING.md`** | What each role can see: public/country/role tiers, relationship model | Any context assembly, tool scoping, UI filtering |

**Rule:** Check the cards FIRST. Go to heritage docs only if the cards don't answer your question.

---

## Canonical Data Sources

| What | Location | Format | Notes |
|---|---|---|---|
| **Countries starting data** | Supabase `countries` table | DB (20 rows) | GDP, stability, military, sectors, coefficients |
| **Countries CSV** | `2 SEED/C_MECHANICS/C4_DATA/countries.csv` | CSV | Must stay synced with DB |
| **Roles data** | Supabase `roles` table | DB (40 rows) | Character sheets + covert op card pools + permitted actions |
| **Roles CSV** | `2 SEED/C_MECHANICS/C4_DATA/roles.csv` | CSV | |
| **Unit layouts** | Supabase `layout_units` table | DB (345 units each) | Layouts: `template_v1_0_default`, `start_one` |
| **Units CSV** | `2 SEED/C_MECHANICS/C4_DATA/units.csv` | CSV (345 rows) | |
| **Map hex grid** | Supabase `sim_templates.rules` | JSONB | `map_global`, `map_eastern_ereb`, `map_mashriq` |
| **Map config (code)** | `app/engine/config/map_config.py` | Python | Canonical hex topology + theater↔global linkage |
| **Methodology prompts** | Supabase `sim_config` table | DB (13 entries) | Prompt templates + methodology rules |
| **Global state per round** | Supabase `global_state_per_round` | DB | Oil, stock, bond, gold per round |
| **Relationships** | Supabase `relationships` table | DB | Bilateral: war/peace, basing rights, tariffs, sanctions |
| **Agreements** | Supabase `agreements` table | DB | Bilateral/multilateral, public/secret, terms |
| **Exchange transactions** | Supabase `exchange_transactions` table | DB | Asset exchanges: coins, units, tech, basing |
| **Covert ops log** | Supabase `covert_ops_log` table | DB | Intelligence, sabotage, propaganda, meddling results |
| **Pre-seeded meetings** | Supabase `pre_seeded_meetings` table | DB | R1-R2 kickstart meetings (Template/scenario data) |
| **Supabase project** | `lukcymegoldprbovglmn` | Cloud DB | |

---

## Design Heritage (read for WHY, not for WHAT)

### Most relevant (check these when cards don't answer)

| Doc | What it covers | Location | Notes |
|---|---|---|---|
| **CON_C2** | Action system design — original 51 actions, authorization, processing systems | `1. CONCEPT/CONCEPT V 2.0/CON_C2_ACTION_SYSTEM_v2.frozen.md` | Consolidated to 32 actions in CARD_ACTIONS |
| **SEED_E5** | AI participant vision — 4-block model, active loop, conversations, autonomy | `2 SEED/D_ENGINES/SEED_E5_AI_PARTICIPANT_MODULE_v1.md` | The VISION document for AI participants |
| **SEED_D8** | All engine formulas (original + F1-F104 calibration) | `2 SEED/D_ENGINES/SEED_D8_ENGINE_FORMULAS_v1.md` | 98% match with code (see CARD_FORMULAS Appendix F) |
| **SEED_D9** | Context Assembly Service | `2 SEED/D_ENGINES/SEED_D9_CONTEXT_ASSEMBLY_v1.md` | |
| **SEED_C_MAP** | Map + units master spec | `2 SEED/C_MECHANICS/SEED_C_MAP_UNITS_MASTER_v1.md` | |
| **SEED_H1** | UX style guide (Midnight Intelligence) | `2 SEED/H_UX/SEED_H1_UX_STYLE_v2.md` | |

### Other heritage (less frequent reference)

| Doc | Location |
|---|---|
| SEED_D10 (NOUS/judgment) | `2 SEED/D_ENGINES/SEED_D10_ENGINE_JUDGMENT_v1.md` |
| SEED_D11 (judgment methodology) | `2 SEED/D_ENGINES/SEED_D11_JUDGMENT_METHODOLOGY_v1.md` |
| SEED_D13 (module architecture) | `2 SEED/D_ENGINES/SEED_D13_MODULE_ARCHITECTURE_v1.md` |
| SEED_E2 (AI conversations) | `2 SEED/D_ENGINES/SEED_E2_AI_CONVERSATIONS_v1.md` |
| SEED_C7 (time structure) | `2 SEED/C_MECHANICS/SEED_C7_TIME_STRUCTURE_v1.md` |
| DET_B1 (DB schema) | `3 DETAILED DESIGN/DET_B1_DATABASE_SCHEMA.sql` |
| DET_C1 (system contracts) | `3 DETAILED DESIGN/DET_C1_SYSTEM_CONTRACTS.md` |
| DET_E5 (module specs) | `3 DETAILED DESIGN/DET_E5_MODULE_SPECS.md` |

---

## Audit & Change History

| Doc | What | Location |
|---|---|---|
| **CHANGES_LOG** | All calibration changes with before/after | `CONCEPT TEST/CHANGES_LOG.md` |
| **Reunification Audit** | Module-by-module gap analysis (2026-04-06) | `3 DETAILED DESIGN/REUNIFICATION_AUDIT_2026-04-06.md` |
| **Strict Audit** | Action-by-action implementation status (2026-04-06) | `3 DETAILED DESIGN/STRICT_AUDIT_2026-04-06.md` |

---

## Code Entry Points

| What | File | Notes |
|---|---|---|
| **Round runner** (20 agents parallel) | `app/engine/agents/full_round_runner.py` | Calls leader_round + resolve_round + round_tick |
| **Single agent round** | `app/engine/agents/leader_round.py` | CANONICAL — LeaderAgent + llm_tools |
| **LeaderAgent** (4-block model) | `app/engine/agents/leader.py` | Cognitive blocks, conversations, decisions |
| **Decision functions** | `app/engine/agents/decisions.py` | Per-category LLM decisions (budget, tariff, etc.) |
| **Domain tools** (agent API) | `app/engine/agents/tools.py` | get_my_forces, commit_action, memory, etc. |
| **Action schema** | `app/engine/agents/stage4_test.py` | `COMMIT_ACTION_SCHEMA` — defines what agents can commit. NOTE: canonical schema, despite "test" filename. |
| **Transactions** | `app/engine/agents/transactions.py` | propose/evaluate/execute (exists, not wired) |
| **Conversations** | `app/engine/agents/conversations.py` | run_bilateral, intent notes, reflection (exists, not wired) |
| **Combat resolver** | `app/engine/round_engine/resolve_round.py` | DEPRECATED path — processes agent_decisions for combat/movement |
| **Engine tick** | `app/engine/engines/round_tick.py` | Bridge: per-round state → economic/political engines |
| **Economic engine** | `app/engine/engines/economic.py` | Pure function: process_economy() — 2011 lines |
| **Political engine** | `app/engine/engines/political.py` | Pure functions: calc_stability, process_election, etc. — 836 lines |
| **Military engine** | `app/engine/engines/military.py` | Zone v1 (live) + unit v2 (reference) + nuclear program — 2500+ lines |
| **Technology engine** | `app/engine/engines/technology.py` | calc_tech_advancement, etc. — 357 lines |
| **Context Assembly** | `app/engine/context/assembler.py` + `blocks.py` | Block-based context builder (exists, partially wired) |
| **LLM provider** | `app/engine/services/llm_tools.py` | Dual-provider tool-use (Gemini + Anthropic) |
| **Observatory server** | `app/test-interface/server.py` | HTTP server + all API endpoints |
| **Observatory JS** | `app/test-interface/static/observatory.js` | 3-screen UI (Maps/Dashboard/Activity) |
| **Observatory CSS** | `app/test-interface/static/observatory.css` | Midnight Intelligence styling |
| **Map config** | `app/engine/config/map_config.py` | Hex topology, theater linkage, coordinate contract |

---

## LLM Configuration

| Use case | Primary | Fallback | Cost |
|---|---|---|---|
| Agent decisions | Gemini 2.5 Flash | Anthropic Sonnet 4 | $0.30/MTok |
| Quick scan | Gemini 2.5 Flash-Lite | Anthropic Haiku 4.5 | $0.10/MTok |
| Narrative | Gemini 2.5 Flash | Anthropic Haiku 4.5 | $0.30/MTok |
| Moderator (NOUS) | Anthropic Sonnet 4 | Gemini 2.5 Pro | $3.00/MTok |
| Intelligence reports | Gemini 2.5 Flash | Anthropic Sonnet 4 | $0.30/MTok |

Set via `LLM_AGENT_PROVIDER=gemini` env var. Config in `app/engine/config/settings.py`.
See `app/config/LLM_MODELS.md` for full model reference.
