# KING SIM AI Architecture Analysis — For TTT Port
## Deep codebase review of /Users/marat/CODING/KING
**Date:** 2026-04-01 | **Purpose:** Inform TTT AI agent design decisions

Full analysis saved separately. Key decisions below.

---

## What to KEEP from KING (direct port)

1. **4-Block Cognitive Model** — Block 1 (fixed rules), Block 2 (identity), Block 3 (memory), Block 4 (goals). Atomic versioning via PostgreSQL function. All versions preserved.
2. **Reflection Service** — event triggers update, LLM processes relevant blocks, atomic save. Priority queue (immediate vs. batched).
3. **Conversation Manager** — turn-by-turn with context caching (85% cost reduction). End conditions (max turns, AI decides to end, all pass).
4. **Intent Notes** — 6-field strategic memo before conversations. Replaces Block 1 in conversation context.
5. **Auto-triggers** — fire-and-forget async on phase transitions.
6. **Queue System** — database-level locking prevents race conditions across tabs.
7. **Model Health Monitoring** — automatic fallback when rate-limited.

## Critical KING Lesson to Apply

**Block 1 is NOT for conversations.** March 2026 "realism overhaul" found that 5000 chars of rules drowns personality. Solution: Block 1 for initialization + reflection ONLY. Conversations use Block 2 (identity) + intent notes.

## What to MODIFY

- Conversation types: add trade_negotiation, alliance_discussion, military_coordination
- Decision types: add budget, tariff, sanctions, military, covert ops (KING only had voting)
- Batch thresholds: 10→20 items, tune for 10+ agents
- Model config: add Anthropic Claude alongside Gemini (dual-provider from inception)

## What to REPLACE

- King Decision Service → Trade/War/Budget Decision Services
- Oracle System → Argus (already designed)

## Cost Estimate (10 AI agents, 8 rounds)

~$5-9 per simulation run. Context caching is essential — without it, costs 6× higher.

## Speed Estimate by Tier

| Tier | Conversations | Est. time per round | Full 8-round SIM |
|------|:---:|:---:|:---:|
| Tier 1 (quick-scan) | None | ~10 sec | ~2 min |
| Tier 2 (modelled) | Summarized | ~30 sec | ~5 min |
| Tier 3 (full dialogue) | Real turns | ~3-5 min | ~30-40 min |
| Tier 4 (production) | + voice | ~8-10 min | ~60-80 min |
