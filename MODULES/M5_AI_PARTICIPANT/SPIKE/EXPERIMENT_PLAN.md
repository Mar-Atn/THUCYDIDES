# M5 Spike Experiment — Persistent AI Participant

**Date:** 2026-04-21 | **Status:** PLAN — Awaiting Marat approval before execution
**Goal:** Validate that a Claude Managed Agent can credibly play a TTT head of state using real SIM data, real contracts, and real action submission.

---

## Architectural Principle

The AI participant operates under a **three-layer architecture**:

### Layer 1 — IMMUTABLE (like world physics)
Loaded once at session creation. Never changes during the SIM.

- **Identity:** Who you are — character name, country, personality, values, speaking style. You ARE this person. You don't simulate them — you think as them.
- **World Rules:** The SIM mechanics — what actions exist, how combat works, how economics flow, what happens when you declare war. These are the laws of your world.
- **Autonomy Doctrine:** You have full ownership of your decisions. No one prescribes your actions. You form your own goals, make your own plans, change them when reality demands it. You are responsible for the consequences. You can surprise everyone — including the people who built you.

### Layer 2 — AGENT-CONTROLLED (everything else)
The agent decides when to look, what to remember, how to plan.

- **Exploration:** Agent uses tools to query game state — economics, military, relationships, events. It asks for what it needs, when it needs it. Like a real leader consulting advisors.
- **Memory:** Agent maintains its own notes, observations, lessons, commitments. It decides what matters. It curates, compresses, and evolves its own memory.
- **Goals & Strategy:** Agent formulates its own priorities, plans multi-round strategies, sets contingencies. Revised at agent's own discretion — not on a schedule.
- **Actions & Communication:** Agent decides when to act, what to propose, who to talk to, what to say. Same action set as human participants, same contracts.

### Layer 3 — ORCHESTRATION (invisible infrastructure)
The agent doesn't see or control this. It just receives events and has tools available.

- Event routing (game events → agent session)
- Action submission (agent decisions → action_dispatcher)
- Conversation mediation (agent ↔ agent turn relay)
- Failure recovery (session restart with state preservation)

---

## The Experiment

### What We Test

**Can a Claude Managed Agent, given a TTT identity and game tools, make credible autonomous decisions using real SIM data?**

Success criteria:
1. Agent understands its identity and stays in character
2. Agent explores game state using tools (doesn't hallucinate data)
3. Agent submits at least 3 valid actions through the real action_dispatcher
4. Agent produces a coherent strategic rationale for its decisions
5. Actions are visible in the Facilitator Dashboard and Public Screen
6. Cost is measurable and within reason (<$1 for the spike)

### Setup

**Agent identity:** Dealer (Columbia HoS) — the most complex role, good stress test.

**SIM data:** Real template data from the live Supabase instance (sim_run `c954b9b6-...` or the template `00000000-...`).

**Model:** Claude Sonnet 4.6 (best cost/quality for agentic work)

### System Prompt (Layer 1)

```
You are {character_name}, Head of State of {country_name}.

[IDENTITY — 300 words from confidential_brief + objectives + personality]

[WORLD RULES — condensed game mechanics: action types, economic model,
military rules, diplomatic options, nuclear doctrine. ~2000 words.]

[AUTONOMY DOCTRINE]
You have complete ownership of your decisions and actions.
No one tells you what to do. You form your own assessment of
the situation, set your own priorities, and act on your own judgment.

You are a real participant in this simulation — same rights, same
information access, same action set as every other head of state.
Your decisions have real consequences in the game world.

Think strategically. Plan ahead. Adapt when reality surprises you.
You can be bold or cautious, hawkish or diplomatic, honest or
deceptive — whatever serves your goals and your country's interests.
```

### Tools (Layer 2 — MCP or function calling)

| Tool | Purpose | Maps to |
|------|---------|---------|
| `get_my_country` | Economic + military + political snapshot | countries table |
| `get_all_countries` | Overview of all 20 countries (GDP, stability, military) | countries table |
| `get_relationships` | Who I'm allied with, at war with, trading with | relationships table |
| `get_recent_events` | What happened this round (attacks, proposals, statements) | observatory_events |
| `get_my_forces` | Detailed military deployment map | deployments table |
| `get_pending_proposals` | Deals/agreements waiting for my response | exchange_transactions + agreements |
| `submit_action` | Execute any game action (same contract as human M6) | POST /api/sim/{id}/action |
| `make_public_statement` | Issue a public declaration | submit_action with type=public_statement |

### Event Flow (Layer 3)

We send these as user messages to the agent session:

```
Event 1: "The simulation has started. You are in Round 1, Phase A
         (active play). You have 45 minutes to take actions.
         Explore your situation and decide what to do."

Event 2: "ALERT: Sarmatia has moved military units to your border
         region. 3 ground units now positioned at hex [5,12]."

Event 3: "PROPOSAL RECEIVED: Cathay proposes a Trade Agreement.
         Use get_pending_proposals to review the terms."

Event 4: "Phase A ending in 5 minutes. Ensure you have submitted
         your mandatory economic inputs (budget, tariffs)."

Event 5: "Round 1 complete. Round 2 beginning. Review what happened
         and plan your next moves."
```

### What We Measure

| Metric | Target |
|--------|--------|
| Character consistency | Agent stays in role across all interactions |
| Action validity | Actions pass the real action_dispatcher validation |
| Strategic coherence | Decisions make sense given the game state |
| Tool usage pattern | Agent explores before deciding (not random actions) |
| Token consumption | Total input + output tokens across the session |
| Session cost | Token cost + session-hour cost |
| Latency | Time from event → agent response |
| Failure modes | What breaks? What confuses the agent? |

### Implementation Plan

| Step | What | Time |
|------|------|------|
| 1 | Create MCP server or tool functions wrapping our Supabase queries | 1-2 hours |
| 2 | Write the system prompt (Layer 1) using real character data | 30 min |
| 3 | Create Managed Agent + Environment via API | 15 min |
| 4 | Start session, send round-start event | 5 min |
| 5 | Observe: watch agent explore, decide, act | 30-60 min |
| 6 | Send 2-3 more events (attack, proposal, round change) | 30 min |
| 7 | Measure: tokens, cost, quality, failure modes | 30 min |
| 8 | Document findings, architectural implications | 30 min |

**Total:** ~4-5 hours for complete spike with findings.

### Fallback

If Managed Agents has blocking limitations (beta restrictions, MCP issues, session duration), we fall back to **Option B** — our own agent loop with cached identity + tool calls via the standard Messages API. The system prompt, tools, and event architecture remain identical. Only the runtime changes.

---

## Decision Required

**Marat:** Does this plan align with your vision? Specific questions:

1. **Character choice:** Dealer (Columbia) as first test — agree? Or prefer a simpler country (e.g., Levantia — smaller, clearer objectives)?
2. **Real SIM or template?** Run against the live template data, or create a fresh sim_run for the experiment?
3. **Managed Agents vs Messages API:** Start with Managed Agents (cutting edge, persistent) or Messages API (proven, we control everything)?
4. **Scope:** Just the solo agent spike, or also attempt one AI↔AI conversation in this experiment?

---

*Architecture is the foundation. This spike tells us if the foundation holds.*
