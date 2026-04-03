# Engine Judgment Layer (Pass 2) — SEED Specification
## Thucydides Trap SIM
**Version:** 1.0 | **Date:** 2026-04-04 | **Status:** Active
**Concept reference:** CON_C1 E1 (World Model Engine, Step 7: Moderator Review)
**Supersedes:** SEED_D_EXPERT_PANEL_TEST.md (rule-based heuristics → LLM judgment)

---

## 1. What This Is

The Engine Judgment Layer is a **sub-module of the World Model Engine** that applies AI judgment after deterministic formulas (Pass 1) run. It is NOT Argus (participant assistant). It is NOT a character. It is the world model's quality control and judgment layer.

**Position in the processing pipeline:**
```
Pass 1 (Deterministic)  →  Pass 2 (Judgment)  →  Pass 3 (Coherence + Narrative)
   Formulas                 AI reviews &           Plausibility check
   14 chained steps         adjusts results        + round summary
   < 1 second               < 30 seconds           < 60 seconds
```

---

## 2. What It Decides

During the parameter review (Cal-1 through Cal-22), several mechanics were **explicitly delegated from formulas to AI judgment** because they require narrative understanding, not threshold arithmetic:

| Responsibility | What the AI does | Bounds |
|---------------|-----------------|--------|
| **Crisis state** | Determines if a country enters/exits crisis based on compounding indicators | -1% to -2% GDP penalty when declared |
| **Momentum/confidence** | Assesses market confidence, investor sentiment, rally effects | Informational (feeds AI Pass 2 assessment) |
| **Contagion** | Decides when economic crisis spreads between trade partners | GDP impact: 0% to -2% per affected country |
| **Stability adjustment** | Nudges stability for factors formulas miss (scandals, leadership, morale) | ±0.5 per round |
| **Support adjustment** | Nudges political support for narrative events | ±5pp per round |
| **Capitulation** | Determines when a country surrenders or seeks ceasefire | Binary recommendation + argument |
| **Market index nudge** | Adjusts 3 regional indexes for sentiment beyond formula inputs | ±10 points per index |

**What it does NOT do:**
- Does not change GDP directly (only via crisis penalty)
- Does not override Pass 1 formula outputs (only adjusts soft variables)
- Does not make strategic decisions for countries (that's leader agents)
- Does not generate narrative (that's Pass 3)

---

## 3. How It Works

### 3.1 Input Assembly

The judgment module requests context from the Context Assembly Service (SEED_D9):

```
Blocks requested: sim_rules + methodology + sim_history + world_state + round_inputs + round_outputs
Visibility: MODERATOR (full access to all country data)
```

**Methodology block** ("The Book") contains:
- **Definitions**: What constitutes a crisis, contagion trigger, capitulation
- **Principles**: "Sanctions are a choke, not a spiral." "No country eliminated before R4." "Democratic resilience under invasion."
- **Bounds**: Maximum adjustment magnitudes per variable
- **Historical examples**: Real-world reference points (2008, 1973, 1997)
- **Anti-patterns**: "Don't double-count." "Don't create death spirals." "Don't override what Pass 1 handles."

### 3.2 LLM Call

Single LLM call with structured output (JSON schema enforced):

```
System: You are the World Model Judgment Layer for the Thucydides Trap simulation.
        You review deterministic engine outputs and apply bounded adjustments
        that formulas cannot capture. You are not a player or advisor.
        You are an analytical engine component.

Context: [assembled context — ~15K tokens]

Instruction: Review this round's outputs. For each country, assess whether
             adjustments are needed. Return a JSON response with the exact
             schema below. Include a compact argument for each adjustment.
```

### 3.3 Output Schema

```json
{
  "round_num": 4,
  "crisis_declarations": [
    {
      "country": "sarmatia",
      "crisis_state": "crisis",
      "gdp_penalty_pct": -1.5,
      "argument": "3rd consecutive round of GDP decline (-3.7%, -2.1%, -1.8%), inflation at 85% (80pp above baseline), stability 3.2 and falling. Meets crisis definition."
    }
  ],
  "contagion_effects": [
    {
      "from_country": "sarmatia",
      "to_country": "teutonia",
      "channel": "energy_dependency",
      "gdp_impact_pct": -0.5,
      "argument": "Teutonia has 10% trade exposure to Sarmatia. Gas supply disruption + sanctions compliance costs."
    }
  ],
  "stability_adjustments": [
    {
      "country": "columbia",
      "delta": -0.3,
      "argument": "Election in 2 rounds + market stress (Wall Street at 58) + war tiredness creating compounding pressure beyond formula capture."
    }
  ],
  "support_adjustments": [
    {
      "country": "ruthenia",
      "delta": 3.0,
      "argument": "Rally-around-flag effect: defending homeland against invasion, strong national identity, wartime democratic resilience."
    }
  ],
  "market_index_nudges": [
    {
      "index": "wall_street",
      "delta": -5,
      "argument": "Formosa crisis creating uncertainty beyond GDP impact — tech supply chain fears."
    }
  ],
  "capitulation_recommendations": [],
  "flags": [
    "persia_nuclear_breakout_imminent",
    "columbia_election_pressure_mounting",
    "sarmatia_economic_clock_ticking"
  ],
  "confidence": 0.82,
  "reasoning_summary": "Sarmatia enters crisis (clear indicators). Teutonia feels contagion via energy. Columbia under dual pressure (market + election). Ruthenia benefits from wartime solidarity."
}
```

### 3.4 Validation & Bounds

Before applying, the orchestrator validates:
- Stability delta within [-0.5, +0.5]
- Support delta within [-5, +5]
- GDP crisis penalty within [-2%, -1%] (only for declared crises)
- Contagion GDP impact within [-2%, 0%]
- Market index nudge within [-10, +10]
- No more than 5 countries affected by contagion per round

Any adjustment exceeding bounds is clamped and flagged.

---

## 4. Two Modes

### 4.1 Automatic Mode (Unmanned Runs)

```
Pass 1 → Judgment call → validate bounds → apply all adjustments → log → Pass 3
```

All recommendations applied automatically. Full output logged to `judgment_log` table. Used for unmanned test runs and calibration.

### 4.2 Manual Mode (Live SIM with Moderator)

```
Pass 1 → Judgment call → present to moderator → moderator approves/modifies/rejects each → apply → log → Pass 3
```

Moderator sees:
- Each recommended adjustment with argument
- Current country state for context
- Option to approve, modify value, or reject with notes
- "Apply all" shortcut for fast rounds

Moderator decisions logged with notes for post-SIM analysis.

---

## 5. Evolution from SEED Expert Panel

The SEED design had three rule-based expert personas (Keynes, Clausewitz, Machiavelli) with hard-coded checks and majority-rule synthesis. This is replaced by:

| SEED (rule-based) | BUILD (LLM judgment) |
|---|---|
| 3 separate function calls with if/then checks | 1 LLM call with full context |
| Fixed thresholds trigger fixed adjustments | AI evaluates holistically against methodology |
| Majority rule (2/3 agree = apply) | Single coherent assessment with arguments |
| 30% cap on all adjustments | Specific bounds per variable type |
| No explanation of reasoning | Compact argument required for every adjustment |
| No moderator review option | Two modes: automatic or moderator-controlled |

**Why the change:** Rule-based checks couldn't handle the complexity. "GDP declining + inflation rising + stability low" fires a crisis — but what if that's a sanctioned autocracy at war (Sarmatia) vs a peaceful democracy in recession (Ponte)? The context matters. LLM judgment handles this naturally.

---

## 6. Methodology Management

"The Book" (methodology) is stored in `sim_config` table, not hard-coded:

| Key | Content Summary |
|-----|----------------|
| `crisis_definition` | When to declare crisis: logical definition + examples |
| `contagion_rules` | When crisis spreads: trade exposure thresholds, channels |
| `capitulation_criteria` | When a country might surrender: military + economic + political |
| `stability_factors` | What affects stability beyond formulas: narrative, leadership, morale |
| `support_factors` | What affects support beyond formulas: scandals, rallies, events |
| `market_sentiment` | How to assess market psychology beyond index formula |
| `bounds` | JSON: maximum adjustment values per variable |
| `anti_patterns` | What NOT to do: double-counting, death spirals, premature elimination |
| `historical_examples` | Real-world reference points for calibrating judgment |
| `pass2_system_prompt` | The system prompt template |
| `pass2_instruction` | The instruction template with response schema |

Moderator can edit any entry between rounds. Changes are versioned. Old versions preserved for comparison.

---

## 7. Calibration Process

Like formula calibration, judgment calibration uses test runs:

1. **Run** scenario with automatic mode
2. **Review** judgment outputs — were adjustments reasonable?
3. **Adjust methodology** — refine definitions, add examples, tighten bounds
4. **Re-run** same scenario — compare judgment quality
5. **Iterate** until judgment consistently produces plausible, balanced results

The `judgment_log` table enables before/after comparison across methodology versions.

---

## 8. Relationship to Other Modules

- **Orchestrator** calls judgment after Pass 1, before Pass 3
- **Context Assembler** provides all context (judgment never reads DB directly)
- **LLM Service** handles the API call (dual-provider, failover)
- **Moderator API** exposes judgment recommendations for manual mode
- **Leader Agents** are NOT involved — judgment operates on world state, not player decisions
