# F1 — AI Decision Context Gaps

**Date:** 2026-04-12 | **Status:** Captured for future AI Participant Module v1.0
**Context:** Discovered while reviewing live AI movement decisions in M1-VIS demos

> The current `build_*_context()` services (budget, tariff, sanction, OPEC,
> movement) ship just enough information for the engine validator to accept
> a decision and for the AI to not produce nonsense. They do **not** ship
> enough for an AI to make *strategically meaningful* decisions. This is
> by design — the slice work is plumbing, not intelligence — but it has to
> be addressed before AI participants can be evaluated against the SEED_E5
> vision.

---

## Symptom

In the M1-VIS AI 4-countries / 2-rounds run, **7 of 8 LLM movement calls
returned `no_change`** with defensible-sounding rationales like "current
deployment provides strong defensive coverage". Only Columbia made an
actual change in R1.

This is not a model failure. It's the model correctly recognizing it has
**insufficient information to act with conviction** and falling back on
the "no_change is legitimate" escape hatch the contract gives it. A
strategic actor with this much fog would default to inaction too.

---

## What's in the current `build_movement_context()`

A **legality kit**, no more:

- Own units (positions, statuses)
- Own territory (zone names)
- Hexes I've previously occupied
- Basing rights granted to me
- 57-zone world map (flat: name, theater, type, owner)
- Zone-level adjacency (NOT hex-level)
- Move_units rules + decision rules
- Light economic snapshot (gdp, treasury, stability, war_tiredness, at_war_with)
- Last 3 rounds of combat events involving me

That's enough to validate. Nothing more.

---

## What's missing — by category

### 1. Geographic and physical reality
- Map dimensions (10×20) never stated
- Hex semantics (city? region? 500km zone?) never stated
- Scale (km/hex, time/round) never stated
- North orientation never stated
- Hex-level adjacency not provided (only zone-level)
- Hex-level land/sea map not provided (only zone-level aggregate)
- Chokepoints, terrain modifiers, theater linkage absent

### 2. Other countries' military posture (THE BIG ONE)
- **Zero visibility** into enemy or allied unit positions
- "At war with: X" doesn't tell me X has 5 grounds 2 hexes away vs 50 grounds across the map
- Cannot make a defensive deployment without knowing what's coming
- Cannot make an offensive deployment without knowing what I'm attacking
- This is the single largest blocker to meaningful AI movement

### 3. Unit semantics
- What does an "active ground" unit DO? (hold? ZoC? block?)
- Combat strength of one ground vs naval vs tactical_air — never stated
- Carrier capacity rules given without explaining WHY embarking matters (amphibious assault?)
- Air defense radius — undefined
- Strategic missile range, target type, cost — undefined

### 4. Strategic context — the "why"
- My country's doctrine (defensive crouch / forward projection / hegemon?)
- My objectives this round / this sim
- Allies vs neutrals vs rivals (beyond at_war list)
- Diplomatic state of the world
- Round position in arc (R1/8 = invest, R7/8 = lock-in)

### 5. Action consequences
- Rules tell me WHAT I can do, not what happens AFTER
- Cost of moves (treasury? maintenance? combat readiness?)
- Cost of withdraw to reserve in lost-round terms
- Diplomatic / economic consequences of forward deployment

### 6. Memory
- I see last 3 rounds of combat involving me
- I do NOT see my own past decisions or rationales
- Every round is amnesia

---

## Mapping to the cognitive blocks

The current context fills a sliver of Block 1 (rules + immediate state).
Everything missing maps cleanly to the other blocks already designed in
`AI_CONCEPT.md`:

| Block | What it should add |
|---|---|
| **1 — Rules & World** | Map dimensions, hex semantics, unit descriptions, combat odds, action consequences, time scale |
| **2 — Identity & Role** | Country doctrine, leader persona, national interests, redlines |
| **3 — Memory** | Past decisions, why made, what worked, observed patterns of others |
| **4 — Goals** | This round's objectives, multi-round strategic plan |

Plus a **cross-cutting layer**: information scoping per `INFORMATION_SCOPING.md`
(visible enemy positions filtered by intel level, public country profiles,
bilateral relationship state, treaty memberships).

---

## Lookup tools — pull, don't push

A flat dump of "everything an AI might want to know" would be enormous.
The clean architecture (already sketched in `AI_CONCEPT.md`) is **tool-use**:
the always-included header is small, and the AI calls lookup tools as needed.

Concrete lookup tools the movement decision would benefit from:

- `describe_country(code)` → public profile + doctrine + recent activity
- `intel_report(target)` → what my intel services believe about a target
- `describe_hex(row, col)` → terrain, owner, units, strategic value, neighbors
- `unit_specs(unit_type)` → combat strength, range, ZoC, costs
- `recent_history(rounds=5)` → what's happened
- `my_doctrine()` → my country's strategic posture
- `my_objectives_this_round()` → goals
- `compare_forces(a, b, theater)` → force balance
- `simulate_move(unit, target)` → validator-preview without committing
- `list_visible_units(country)` → what I can see of another country (intel-gated)

---

## Recommended path forward

**Don't retroactively bloat `build_movement_context()`** — that would
contaminate the slice-validator boundary the F1 plan deliberately drew.

Instead, when the AI Participant Module v1.0 is built (after all action
slices are done), it should:

1. **Wrap** the existing slice context builders (which stay decision-specific
   and validator-grade)
2. **Compose** the cognitive blocks 1-4 around them (rules / identity /
   memory / goals)
3. **Add** the lookup tools as bound function-calls (Anthropic / Gemini
   tool-use)
4. **Apply** information scoping per role tier (HoS / military chief /
   intel director / etc)

The slice-level context stays a *contract* between the engine and the
validator. The cognitive context is built ON TOP, by the AI module.

---

## What this means for the slices we still need to ship

**Nothing.** The remaining slices (M2 ground combat, M3 air, etc.) should
follow the same boundary discipline: their `build_*_context()` functions
ship validator-grade information for the slice's specific decision, full
stop. They are NOT responsible for cognitive context.

When we get to the AI module, the lift is to wrap all of them, add the
shared cognitive layer, and provide the lookup tools. The slices don't
need to be redone.

---

## Open question for the AI module phase

How "interactive" should the per-round AI loop be? Two extremes:

- **Pre-baked context, single LLM call** — assemble everything up front,
  one shot decision. Cheap, deterministic. What we do today.
- **Tool-use loop, multiple LLM turns** — model gets a small header,
  decides what to inspect, calls lookup tools, gets back results, decides
  more, finally commits the decision. More expensive, more realistic.

The right answer is probably a **hybrid**: a richer pre-baked header
(blocks 1-4 + scoped intel) + a small set of lookup tools available for
the model to call when it needs to "drill in" on a specific target.
This preserves a single primary turn for the common case while letting
the model reach for more when the situation warrants it.

To be decided when the AI module phase opens.
