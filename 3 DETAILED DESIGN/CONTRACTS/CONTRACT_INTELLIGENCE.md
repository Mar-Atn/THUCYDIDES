# CONTRACT: Intelligence Reports

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §4.1

---

## 1. PURPOSE

Intelligence reports are the SIM's "oracle" function: any authorized role
can ask any question about the world, and the system returns a classified
briefing based on ALL real SIM data with 10-30% mandatory noise injection.

No target country required. Just a question. The LLM determines which
data domains are relevant and produces the analysis.

No detection/attribution mechanics for v1.0 (deferred).

---

## 2. SCHEMA

```json
{
  "action_type": "covert_op",
  "op_type": "intelligence",
  "role_id": "shadow",
  "country_code": "columbia",
  "round_num": 3,
  "rationale": ">= 30 chars",
  "question": "What is the current military balance between Columbia and Sarmatia?"
}
```

---

## 3. COMPREHENSIVE WORLD CONTEXT

The intelligence LLM receives ALL SIM data across 9 domains (~18KB):

| Domain | Data | Source table |
|---|---|---|
| **All countries** | GDP, treasury, stability, support, war tiredness, nuclear/AI levels, inflation | `country_states_per_round` |
| **Military forces** | Unit counts per country per branch (active + reserve) | `unit_states_per_round` |
| **Relationships** | Wars, alliances, tensions | `relationships` |
| **Agreements** | ALL active (public + secret — intelligence sees everything) | `agreements` |
| **Recent events** | Last 3 rounds of significant actions | `observatory_events` |
| **Transactions** | Recent exchange history | `exchange_transactions` |
| **Nuclear status** | Tier, confirmed/unconfirmed, R&D progress, tests/launches | `country_states_per_round` + `nuclear_actions` |
| **Blockades** | Active chokepoint blockades | `blockades` |
| **Basing rights** | Who deploys where | `basing_rights` |

Intelligence sees **secret agreements** that normal information scoping
would hide. This is a deliberate design decision — intelligence
penetrates secrets.

---

## 4. NOISE INJECTION

| Question complexity | Noise level | Examples |
|---|---|---|
| Simple, specific | ~10% | "Does Persia have nuclear capability?" |
| Moderate analysis | ~20% | "What is Cathay's military posture near Formosa?" |
| Broad strategic | ~30% | "Comprehensive threat assessment for Columbia" |

Noise = slightly wrong numbers + plausible but false assessments +
omissions. The requester does NOT know the noise level.

LLM marks confidence: HIGH / MODERATE / LOW per assessment.

---

## 5. ENGINE

`intelligence_engine.py`:
- `generate_intelligence_report(sim_run_id, round_num, question, requester_country, role)`
- `_build_full_world_context(client, sim_run_id, round_num)` — loads all 9 domains
- `_call_intelligence_llm(question, context, requester)` — LLM with noise instructions

---

## 6. PERSISTENCE

- `observatory_events`: `intelligence_report_received` event for requester
- Report text stored in event payload (not a separate table)

---

## 7. LOCKED INVARIANTS

1. Always returns a report (no probability roll — intelligence always produces something)
2. LLM has access to ALL world state (including secret agreements)
3. 10-30% noise is mandatory (LLM self-regulates based on question complexity)
4. No target country required — just a question
5. No detection/attribution in v1.0
6. Card pool: `intelligence_pool` (per round, replenishes) — checked by validator
7. Context is ~18KB structured text covering all 9 data domains
