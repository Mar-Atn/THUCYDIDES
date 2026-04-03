# Context Assembly Service — SEED Specification
## Thucydides Trap SIM
**Version:** 1.0 | **Date:** 2026-04-04 | **Status:** Active
**Concept reference:** CON_C1 (F1 AI Participant, F2 AI Assistant), SEED_E4 (Argus 7-block model)

---

## 1. Purpose

The Context Assembly Service is a **shared infrastructure module** that builds LLM-ready context from SIM run data. Every LLM consumer in the system (NOUS, leader agents, Argus, narrative generation, election AI voters) requests context through this service rather than assembling it independently.

**Why it exists:**
- Eliminates duplication (5+ consumers need overlapping context)
- Enforces information asymmetry at the source (visibility filtering)
- Enables moderator control (methodology is DB-stored, editable between rounds)
- Provides caching (rules don't change mid-SIM, world state changes per round)

---

## 2. Data Source Hierarchy

Context is assembled from three levels of the Template → Scenario → Run hierarchy:

| Level | What it provides | Changes when | Storage |
|-------|-----------------|-------------|---------|
| **Template** | Methodology, rules, prompt templates, judgment bounds | Between SIMs (moderator edits) | `sim_config` table |
| **Scenario** | Starting conditions, country configs, role definitions | At SIM setup | CSV seed data → DB |
| **Run** | Live world state, events, decisions, round outputs | Every round | `world_state`, `event_log`, `countries` tables |

**The assembler always operates on a specific `sim_run_id`** — it reads actual run data, not abstractions. Template-level content (methodology, rules) is loaded via the run's parent template.

---

## 3. Context Blocks

Every piece of context is a **named block** with defined scope, content, and caching behavior.

### 3.1 Block Registry

| Block Name | Content | Source | Visibility | Cache TTL |
|-----------|---------|--------|-----------|-----------|
| `sim_rules` | Game rules, mechanics, all parameters | `sim_config` (template) | ALL | Per SIM (immutable) |
| `methodology` | Judgment rules, definitions, examples, bounds | `sim_config` (template) | MODERATOR | Per version (refreshed on edit) |
| `world_state` | Current state of all countries, wars, oil, indexes | DB snapshot (run) | Filtered by role | Per round |
| `sim_history` | Summarized round-by-round events | `event_log` (run) | Filtered by role | Appended per round |
| `round_inputs` | This round's submitted actions/decisions | Actions table (run) | MODERATOR | Per round |
| `round_outputs` | Pass 1 formula results (GDP changes, oil, stability deltas) | Engine output (run) | MODERATOR | Per round |
| `role_context` | Role brief, powers, objectives, ticking clock, personal state | `roles` + `role_briefs` (run) | ROLE-specific | Per SIM (mostly static) |
| `available_actions` | What this role can do this round | Authorization rules + state | ROLE-specific | Per round |
| `conversation_history` | Previous Argus conversations with this participant | Conversation store (run) | ROLE-specific | Per session |
| `previous_decisions` | This leader's past actions and their outcomes | `event_log` filtered (run) | ROLE-specific | Per round |

### 3.2 Visibility Scoping

Blocks that contain world state are filtered by four tiers (per SEED_F3_DATA_FLOWS):

| Tier | Who sees | Example |
|------|---------|---------|
| **PUBLIC** | Everyone | Oil price, map zones, war declarations, tariffs, sanctions |
| **COUNTRY** | Country team + moderator | Own GDP (exact), treasury, stability, support, budget |
| **ROLE** | Specific role + moderator | Personal coins, intelligence results, covert op outcomes |
| **MODERATOR** | Facilitator only | All country internals, judgment recommendations, coherence flags |

When a consumer requests `world_state`, it must specify a visibility scope:
- `world_state` (no scope) → full MODERATOR view (for judgment, narrative)
- `world_state:columbia` → COUNTRY view for Columbia
- `world_state:anchor` → ROLE view for the Anchor role (Columbia president)

### 3.3 Caching Strategy

| Cache Level | Invalidation | Blocks |
|------------|-------------|--------|
| **Per-SIM** | Never (within a SIM) | `sim_rules` |
| **Per-version** | When moderator edits | `methodology` |
| **Per-round** | When new round is processed | `world_state`, `sim_history`, `round_inputs`, `round_outputs`, `available_actions` |
| **Per-session** | Each Argus conversation | `conversation_history` |
| **Never cached** | Always fresh | `previous_decisions` (filtered query) |

---

## 4. Consumer Profiles

### 4.1 NOUS (Pass 2)
**Frequency:** 1 call/round | **Token budget:** ~15K | **Visibility:** MODERATOR

```
Blocks: sim_rules + methodology + sim_history + world_state + round_inputs + round_outputs
```

NOUS gets full visibility — it needs to see everything to make good assessments. Methodology block contains "The Book" (definitions, principles, historical examples, bounds).

### 4.2 Leader Agent Decision
**Frequency:** 21 calls/round | **Token budget:** ~10K | **Visibility:** COUNTRY+ROLE

```
Blocks: sim_rules + role_context:{leader_id} + world_state:{country_id} + available_actions:{leader_id} + sim_history:{country_visible} + previous_decisions:{leader_id}
```

Each leader sees only what their country knows. Information asymmetry is critical — Cathay shouldn't know Columbia's exact treasury.

### 4.3 Argus (Participant Assistant)
**Frequency:** On demand (~50-100/round) | **Token budget:** ~12K | **Visibility:** ROLE

```
Blocks: sim_rules + role_context:{role_id} + world_state:{role_visible} + conversation_history:{role_id} + sim_history:{role_visible}
```

Argus respects the same visibility as the participant. Never reveals hidden information.

### 4.4 Narrative Generation (Pass 3)
**Frequency:** 1 call/round | **Token budget:** ~8K | **Visibility:** PUBLIC + MODERATOR

```
Blocks: world_state + round_outputs + sim_history + previous_narratives
```

Generates public-facing narrative (what everyone sees) plus moderator-only analysis.

### 4.5 Election AI Voters
**Frequency:** 7-14 calls at election rounds | **Token budget:** ~4K | **Visibility:** PUBLIC

```
Blocks: sim_rules:elections + world_state:public + voter_profile:{voter_id}
```

AI citizen voters see only public information — like real voters.

### 4.6 Moderator Brief
**Frequency:** 1/round | **Token budget:** ~12K | **Visibility:** MODERATOR

```
Blocks: world_state + round_outputs + judgment_recommendations + flags + comparison_to_previous
```

---

## 5. Token Budget Management

| Consumer | Blocks | Estimated Tokens | Model |
|----------|--------|-----------------|-------|
| NOUS | 6 blocks | ~15K | Claude Opus / Gemini Pro |
| Leader Agent | 6 blocks | ~10K | Claude Sonnet / Gemini Flash |
| Argus | 5 blocks | ~12K | Claude Sonnet (voice: Gemini Flash) |
| Narrative | 4 blocks | ~8K | Claude Sonnet |
| Election voter | 3 blocks | ~4K | Gemini Flash |
| Moderator brief | 5 blocks | ~12K | Claude Sonnet |

**Cost control:** Leader agents (21×/round) and Argus (high frequency) use cheaper models. NOUS (1×/round) uses the best model for quality.

---

## 6. Database Schema

### 6.1 sim_config (Template-level configuration)

```sql
CREATE TABLE sim_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL,
    category TEXT NOT NULL,             -- 'methodology' | 'prompt_template' | 'judgment_rule' | 'context_block'
    key TEXT NOT NULL,                  -- e.g. 'crisis_definition', 'pass2_system_prompt'
    content TEXT NOT NULL,              -- actual content (markdown, prompt text, JSON)
    version INT NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    updated_by TEXT DEFAULT 'system',   -- 'system' | 'moderator' | 'calibration'
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(template_id, key, version)
);
```

### 6.2 judgment_log (Run-level audit trail)

```sql
CREATE TABLE judgment_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id UUID NOT NULL REFERENCES sim_runs(id),
    round_num INT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'automatic',  -- 'automatic' | 'manual'
    raw_recommendation JSONB NOT NULL,       -- full LLM output
    applied_adjustments JSONB,               -- what was actually applied (null if rejected)
    moderator_decision TEXT,                 -- 'approved' | 'modified' | 'rejected' | null
    moderator_notes TEXT,
    llm_model TEXT,                          -- which model was used
    llm_tokens_used INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. Interface Contract

```python
class ContextAssembler:
    """Shared context assembly service. One instance per SIM run."""

    def __init__(self, sim_run_id: str, template_id: str):
        """Initialize with specific run and template."""

    def build(self, blocks: list[str], **params) -> str:
        """Assemble named blocks into a single context string.

        Args:
            blocks: List of block names, optionally scoped (e.g., "world_state:columbia")
            **params: Additional parameters (round_num, role_id, etc.)

        Returns:
            Concatenated context string ready for LLM prompt.
        """

    def get_block(self, name: str, **params) -> str:
        """Get a single context block. Uses cache when available."""

    def invalidate(self, block_name: str = None):
        """Invalidate cache. None = invalidate all."""

    def get_methodology(self, key: str) -> str:
        """Shortcut: get a methodology entry from sim_config."""

    def get_token_estimate(self, blocks: list[str], **params) -> int:
        """Estimate token count without building full context."""
```

---

## 8. Relationship to Existing Modules

```
                    ┌──────────────────────┐
                    │   sim_config (DB)     │ ← Moderator edits methodology
                    │   Template-level      │
                    └──────────┬───────────┘
                               │ loads
                    ┌──────────┴───────────┐
                    │  Context Assembler    │ ← Shared service
                    │  (per sim_run_id)     │
                    └──┬───┬───┬───┬───┬───┘
                       │   │   │   │   │
            ┌──────────┘   │   │   │   └──────────┐
            │              │   │   │              │
     ┌──────┴──────┐  ┌───┴───┴───┐  ┌───────┐  ┌┴──────────┐
     │  NOUS       │  │  Leader   │  │ Argus │  │ Narrative  │
     │  (Pass 2)   │  │  Agents   │  │       │  │ (Pass 3)   │
     └──────┬──────┘  └───────────┘  └───────┘  └────────────┘
            │
     ┌──────┴──────┐
     │ Orchestrator │ ← applies adjustments (auto or manual)
     │  Pass 1→2→3 │
     └─────────────┘
```
