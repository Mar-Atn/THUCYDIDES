# SEED D12 — Prompts Catalog (sim_config)

**Version:** 1 | **Date:** 2026-04-04 | **Status:** Reference
**Source of truth:** Supabase table `sim_config` (project: THUCYDIDES / lukcymegoldprbovglmn)

---

## 1. Purpose

The `sim_config` table is the unified configuration store for TTT. It holds methodology text, prompt templates, judgment rules, and reusable context blocks — every piece of natural-language or structured configuration consumed by the AI Super-Moderator (Argus) and the AI Participants.

**Why one table?**
- KING had a separate `ai_prompts` table plus scattered methodology files. TTT unifies all of it.
- Every entry is addressable by `(template_id, category, key)` and is versioned.
- Moderator-editable between rounds without a code deployment.
- Default `template_id = 00000000-0000-0000-0000-000000000001` holds the canonical master set.

**Categories in use:**
- `methodology` — judgment rules text, definitions, patterns, historical examples.
- `prompt_template` — LLM prompts with `{{placeholder}}` substitution for AI Participants.
- `judgment_rule` — structured JSON rules (bounds, intensity limits).
- `context_block` — (reserved) reusable context snippets.

---

## 2. Current Entries (13 active)

### 2.1 Methodology (5 entries)

Loaded by `app/engine/context/blocks.py::_build_methodology()` via `ContextAssembler.get_methodology(key)`. Assembled into the "Methodology" context block passed to Argus (the judgment LLM).

| Key | Len | Purpose | When used |
|---|---|---|---|
| `crisis_definition` | 730 | Defines when a country is in CRISIS (2+ indicators: 3 rounds GDP decline, inflation +20pp, stability <4, treasury depleted, max sanctions). Specifies crisis GDP penalties (-1 early, -1.5 deepening, -2 severe) and exit criteria. | Every judgment call (per round, per country review). |
| `contagion_rules` | 498 | Rules for crisis spreading via energy dependency, supply chain, financial contagion, trade collapse. Only when GDP>30 country enters crisis AND partner has >10% exposure. Channel-specific impact ranges. Max 5 countries/round. | Every judgment call — Argus evaluates contagion after crisis identification. |
| `anti_patterns` | 601 | NEVER-rules: no double-counting Pass-1 effects, no death spirals, no eliminations before R4, no blanket adjustments, no formula-gap compensation, no repetition. | Every judgment call — guards Argus against overreach. |
| `historical_examples` | 573 | Reference calibration patterns: Russia 2022, US-China 2018, Oil 1973, Asia 1997, Ukraine 2022. Used to anchor magnitudes. | Every judgment call — anchors Argus to realistic magnitudes. |
| `sim_rules` | (optional) | Game mechanics override for Block 1. Currently not seeded → default used. | AI Participant Block 1 (RULES) at init. |

Call path: `blocks.py:102` loops over `("crisis_definition", "contagion_rules", "capitulation_criteria", "escalation_rules", "historical_examples", "anti_patterns")` and concatenates whatever is present. Missing keys fall back to defaults baked into `blocks.py` (lines 371+).

### 2.2 Prompt Templates (7 entries) — AI Participant

Loaded per-call by the AI Participant module (`app/engine/agents/leader.py` and related). All use `{{placeholder}}` substitution.

| Key | Len | Purpose | Call site / trigger |
|---|---|---|---|
| `metacognitive_architecture` | 1139 | BLOCK 1 prompt. Explains the 4-block cognitive system (RULES/IDENTITY/MEMORY/GOALS), tells the leader it is autonomous, defines how blocks are updated. | Injected once at participant initialization (Block 1 seed). |
| `identity_generation` | 898 | BLOCK 2 generator. Takes `{{role_data}}`, asks LLM to produce 300-500 word identity: personality, communication style, emotional drivers, strategic tendency. | Per-participant, once at init after Block 1. |
| `intent_note_generation` | 775 | Private intent note before a conversation. Placeholders: `{{counterpart_name}}`, `{{counterpart_title}}`. Asks for goals, info-to-extract, what-to-share, approach, offers/threats, red lines. | Per-conversation, generated just before the leader enters a meeting. |
| `conversation_behavior` | 1014 | System-prompt style guide injected into every conversation turn. Enforces "you are a leader, not an assistant," time pressure, goal orientation, opportunity cost. | Per conversation turn (system prompt layer). |
| `meeting_decision` | 807 | Per-round action decision. Placeholders: `{{character_name}}`, `{{title}}`, `{{country_name}}`, `{{block_2_identity}}`, `{{block_4_goals}}`, `{{round_num}}`, `{{time_remaining}}`, `{{past_conversations}}`, `{{leaders_list}}`. Decides whether to initiate a conversation or take an action. | Per decision tick within a round. |
| `reflection_block_3` | 766 | Block 3 (MEMORY) update. Placeholders: `{{new_context}}`, `{{current_block_3}}`. Extracts facts/learnings/promises/relationship changes from new context, writes back consolidated memory. | After each conversation and at round close. |
| `reflection_block_4` | 595 | Block 4 (GOALS) update. Placeholders: `{{trigger_summary}}`, `{{current_block_4}}`, `{{world_summary}}`. Reviews objectives, reprioritizes, updates contingencies. | Triggered by significant events and at round close. |

### 2.3 Judgment Rules (2 entries)

Loaded by `app/engine/judgment/judge.py` and `schemas.py` to validate/clamp Argus output.

| Key | Len | Purpose | When used |
|---|---|---|---|
| `bounds` | 248 | JSON bounds for judgment deltas: `stability_delta ±0.5`, `support_delta ±5.0`, `gdp_crisis_penalty [-2,-1]`, `contagion_gdp_impact [-2,0]`, `market_index_nudge ±10`, `max_contagion_countries 5`, `max_crisis_declarations 5`. | Every judgment call — `validate_bounds()` enforces, clamps violations, logs warnings. |
| `intervention_intensity` | 1 | Scalar 1-5. Caps how aggressively Argus may intervene per round. Currently `3`. | Every judgment call — caps total number of interventions. |

---

## 3. How It Works

**Loading**
- At SIM-RUN init, `ContextAssembler` loads all `methodology` + `context_block` entries for the active `template_id` into `self._sim_config: dict[key → content]`.
- AI Participant prompts are fetched per-call by key (or cached at participant init).
- Judgment rules are loaded once per judgment pass.

**Substitution**
- Prompt templates use `{{placeholder}}` tokens. Callers format with Python `.replace()` or f-string equivalent against a payload dict.
- No Jinja. Plain string substitution keeps prompts auditable.

**Runtime knobs (set in code, not DB, for now)**
- `temperature`, `max_tokens`, model ID live in `app/config/LLM_MODELS.md` and per-call agent code.
- Future: move these to `sim_config` as a `prompt_runtime` category per key.

**Fallback**
- If a methodology key is missing from DB, `blocks.py` uses a hard-coded default so the SIM never crashes on a missing entry.

---

## 4. Versioning

- `version` (int) — incremented on each meaningful content change.
- `is_active` (bool) — exactly one version per `(template_id, category, key)` should be active.
- `updated_by` — `'system'` for seed, moderator user ID for live edits.
- Moderator edit flow: insert new row (version+1, is_active=true) → deactivate previous row (is_active=false). Old versions retained for audit/rollback.
- Between-round edits: moderator changes take effect at next load point (next judgment call or next participant init).

---

## 5. Future Additions

- **Per-run overrides** — mirror KING's `sim_run_prompts` by adding a `sim_run_id` nullable column or a sibling `sim_run_config` table. Enables scenario-specific tweaks without forking the master template.
- **Template library** — multiple `template_id`s per scenario archetype (Great Power, Regional, Pandemic, etc.), selectable at SIM creation.
- **A/B testing** — `variant` column with percentage split, capture performance per variant in test results.
- **Runtime metadata** — add `prompt_runtime` category storing `{temperature, max_tokens, model}` per prompt key.
- **Context blocks** — populate the `context_block` category for reusable snippets (e.g., canonical country briefings, domain glossaries).
- **Validation on write** — DB trigger or API-layer check that `{{placeholder}}` tokens in prompts match an allow-list declared by the call site.

---

*Catalog reflects DB state as of 2026-04-04. Rerun the audit query in Section 2 after any moderator edit to refresh this doc.*
