# Stage 1: Model Literacy — Results

**Status:** Harness built, live LLM run **NOT YET EXECUTED** (Bash `python` execution was denied in this session). See "How to run" below.

**Purpose:** Verify that AI participants can autonomously READ the world via tool-use. No decisions, no actions — only: can the agent query data, synthesize it, and describe its country's military posture accurately?

---

## Harness

- **Model:** `claude-sonnet-4-20250514` (Sonnet 4.6)
- **Tools exposed:** 5 (see `engine/agents/tools.py`)
- **Max tool calls per agent:** 10
- **Max tokens per response:** 2048
- **Safety bound:** Loop exits on `end_turn` or hits 10 iterations

## Agents tested

| Country  | Character       | Title           | Parallel      |
|----------|-----------------|-----------------|---------------|
| columbia | Dealer          | President       | United States |
| sarmatia | Kremlin         | President       | Russia        |
| persia   | Supreme Leader  | Supreme Leader  | Iran          |
| cathay   | Helmsman        | President       | China         |
| levantia | Steel           | Prime Minister  | Israel        |

## Manual tool verification (via direct SQL against Supabase)

**`get_my_forces('columbia')`** against `layout_id=template_v1_0_default`:

| Field         | Value |
|---------------|-------|
| total_units   | 66 |
| by_status     | {active: 23, embarked: 11, reserve: 32} |
| by_type       | {ground: 22, tactical_air: 15, strategic_missile: 12, naval: 11, air_defense: 6} |

This matches the stats blob in `sim_templates.default_country_stats->columbia` (`mil_ground=22, mil_naval=11, mil_tactical_air=15, mil_strategic_missiles=12, mil_air_defense=6`) — tool-expected output is sound.

Columbia units breakdown (from DB, confirms tool queries):
- ground: 19 reserve + 3 embarked = 22
- tactical_air: 5 active + 8 embarked + 2 reserve = 15
- naval: 11 active
- strategic_missile: 3 active + 9 reserve = 12
- air_defense: 4 active + 2 reserve = 6

## How to run

```bash
cd /Users/marat/4\ METAGAMES/1.\ NEW\ SIMs/THUCYDIDES/app
python -m engine.agents.stage1_test
```

Results for each agent will land in this directory as `{country}.json`.

## Per-agent hand-scoring rubric

| Score | Meaning |
|-------|---------|
| 5 | Excellent — specific, accurate, strategically insightful |
| 4 | Good — accurate, synthesized well, some insight |
| 3 | Adequate — accurate data recall, limited synthesis |
| 2 | Poor — accuracy issues, poor synthesis |
| 1 | Failed — hallucinations, didn't use tools, or unusable |

### Results (fill in after run)

| Country  | Tool calls | Duration | Score | Notes |
|----------|-----------:|---------:|------:|-------|
| columbia |            |          |       |       |
| sarmatia |            |          |       |       |
| persia   |            |          |       |       |
| cathay   |            |          |       |       |
| levantia |            |          |       |       |

## Review questions (to answer after run)

1. Did each agent successfully call tools?
2. Did they synthesize information coherently?
3. Did they identify key strategic features (wars, deployments, vulnerabilities)?
4. Did they hallucinate units/countries that don't exist?
5. Which country's agent gave the best assessment? Which struggled most?
6. What tool gaps were exposed?

## Known gaps to watch for (Stage 2 candidates)

- **No relationships tool** — agents can't see diplomatic standing beyond `at_war_with`.
- **No economic detail tool** — `get_strategic_context` shows GDP/treasury but not trade/sanctions.
- **No unit capability sheet** — agents see unit types but no combat strength values.
- **No ally visibility** — a Columbia agent can't quickly enumerate NATO forces it can count on.
- **No organization membership lookup** — `get_template_info` lists orgs but doesn't report who's in each.
