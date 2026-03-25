# Concept Stage Checklist
## Thucydides Trap SIM & Web App
**Version:** 3.2 | **Date:** 2026-03-25 | **Assessed by:** Vera (QC & Balance Lead)

---

### How to use
Each item requires: a concept document (or section within one), in .md format. Mark status as: ○ Not started | ◐ In progress | ● Complete | ⊘ Deferred to SEED stage. Notes column for key decisions, open questions, or version references.

### Assessment summary (v3.1)

| Section | Items | ● | ◐ | ○ | ⊘ | Coverage |
|---------|:-----:|:-:|:-:|:-:|:-:|:--------:|
| A — Scenario Foundation | 3 | 2 | 1 | 0 | 0 | **Strong** |
| B — Actors & Structure | 4 | 2 | 1 | 1 | 0 | **Strong** |
| C — Game Mechanics | 6 | 4 | 0 | 2 | 0 | **Strong** |
| D — Parameters & Starting Data | 2 | 1 | 0 | 0 | 1 | **Concept complete; data deferred** |
| E — Engine Specifications | 2 | 1 | 0 | 0 | 1 | **Concept complete; formulas deferred** |
| F — AI Modules | 2 | 2 | 0 | 0 | 0 | **Complete** |
| G — Web App Architecture | 1 | 1 | 0 | 0 | 0 | **Complete** |
| H — Delivery & Operations | 1 | 1 | 0 | 0 | 0 | **Complete** |
| **TOTAL** | **21** | **14** | **2** | **3** | **2** | |

**Bottom line:** The concept stage is substantially complete. 14 of 21 items are done, covering scenario design, game mechanics, engine architecture, both AI modules, web app architecture, and delivery operations. 2 items are in progress (world-building consolidation, AI country detailed profiles). 3 items remain open but are small (relationship matrix, public speaking protocol, press mechanic). 2 items are explicitly deferred to SEED stage (detailed starting data and engine formulas). 14 documents totaling ~390 pages of concept specification exist in the CONCEPT V 2.0 folder. **v3.2 resolves all 4 CRITICAL issues, 4 of 11 WARNING items, adds 3 missing mechanics, adds personal dimension mechanics, adds Cathay authority constraints, and adds amphibious assault rules. Also adds "Territorial claim→Public statement" rename in E1.**

---

### CONSISTENCY ISSUES

**CRITICAL (4 items):**

1. ~~**Ghost character "Spark".**~~ **RESOLVED (v3.2):** Scrubbed from E1 and C1. Now "Pioneer, Circuit" everywhere.

2. ~~**"Indistan" (Pakistan).**~~ **RESOLVED (v3.2):** Replaced with "regional rivals" in B2.

3. ~~**5th Columbia parliamentary seat undefined.**~~ **RESOLVED (v2.0):** Seat 5 defined as "The Contested Seat" in B2.

4. ~~**Production cost scaling contradiction.**~~ **RESOLVED (v3.2):** Standardized to escalating cost-per-unit model: Normal 1x/unit, Accelerated 2x/unit (4x total for 2x output), Maximum 4x/unit (12x total for 3x output). Updated in C1, C2, D0.

**WARNING (11 items):**

5. **Strategic missile starting counts are placeholders.** C1 gives approximate numbers (Columbia ~10, Nordostan ~10, Cathay ~3+growing, Gallia ~2, Albion ~2). Must be formalized when starting data (D-SEED) is created.

6. **Tech progress percentages appear only once.** C1 states "Cathay 70% toward next AI level" and "Persia at 60% toward L1 [nuclear]." Must be captured in starting data (D-SEED).

7. **Stability threshold discrepancies between C1 and E1.** Stability thresholds (trigger values for domestic crises, coups, etc.) differ between the domains document (C1) and the engine architecture (E1). Must be reconciled — one canonical table.

8. ~~**Nuclear authorization chain inconsistencies.**~~ **RESOLVED (v3.2):** Unified to "always 3 confirmations (HoS + military chief + one additional). AI military advisor fills gap in smaller teams." Updated in C1, C2, E1.

9. ~~**"Social score" legacy term in E1.**~~ **RESOLVED (v3.2):** All instances replaced with "Stability Index" or "stability" across E1, C3, C4, A1, B2 (11 replacements). SIM4 predecessor references preserved.

10. ~~**"Capacity investment" ghost in E1.**~~ **RESOLVED (v3.2):** Removed from E1 budget inputs.

11. ~~**Asset seizure orphaned in E1.**~~ **RESOLVED (v3.2):** Removed from E1 transaction table, revenue inputs, timing summary, and architecture diagram.

12. **UNGA omitted from D0 organization roster.** D0 (parameter structure) lists organizations but omits the UN General Assembly, which is referenced in B1 and C2. Must be added to D0.

13. **EU Commissioner duplicate in B2.** The EU Commissioner appears as both a base role and an optional structural role in B2. Clarify whether this is one role with two functions or a genuine duplication error.

14. **G7 membership should always include Ponte.** Ponte is now a base role (not AI-only), so G7 membership in B1 should explicitly list Ponte as a permanent member. Currently ambiguous.

---

### MISSING MECHANICS TRIAGE (decided 2026-03-25)

**Add to Concept (must be specified before SEED):**

| Mechanic | Target doc | Notes |
|----------|-----------|-------|
| Cost-to-sanctioner formula | C1 / E1 | Sanctions must impose a cost on the sender, not just the target. Concept-level formula needed. |
| Financial market consequences | C1 / E1 | Market reactions to major actions (sanctions, war, treaty collapse). At minimum: oil price shock rules, trade disruption multiplier. |
| Debt service mechanic | C1 / E1 | Countries carry debt; servicing costs consume budget. Simple model: debt level × interest rate = annual cost deducted from revenue. |

**Defer to SEED (too detailed for concept stage):**

| Mechanic | Reason |
|----------|--------|
| Dollar System Dependence | Requires detailed economic model and starting data. Design in E-SEED (economic model spec). |
| Inflation bands | Requires calibrated economic model. Design in E-SEED. |
| Debt (sovereign crisis beyond simple debt service) | Crisis triggers, IMF intervention, restructuring — all require SEED-level calibration. Concept only needs the basic debt service mechanic (above). |

**Drop / Not needed:**

| Mechanic | Reason |
|----------|--------|
| Escalation ladder document | Escalation is emergent from existing mechanics (alert levels, nuclear authorization chain, troop deployments). A separate document would over-prescribe. |
| De-escalation mechanic | De-escalation is the absence of escalation — no separate mechanic needed. Diplomatic actions in C2 already cover this. |
| Disinformation mechanic | Already covered by Veritas/press system and covert ops in C2. No separate mechanic needed. |
| Back-channels mechanic | Back-channels are natural human behavior in a live SIM. No mechanic needed — players will do this on their own. |
| Combat fatigue | Overly granular for this SIM's abstraction level. Unit attrition in C1 covers the same space. |
| Fog-of-war incidents | Interesting but adds complexity without proportional payoff. Can be introduced as a SEED-stage event card if desired. |

**Narrative only (AI engine handles, no player mechanic):**

| Mechanic | Notes |
|----------|-------|
| Refugee flows | AI World Model narrates refugee consequences of wars, sanctions, and instability. No player resource or decision point — purely narrative color generated by the engine. |

---

## A — SCENARIO FOUNDATION

| # | Element | Document | Status | Notes |
|---|---------|----------|:------:|-------|
| A1 | **Phenomenon reference** — Thucydides Trap theory, modern instance, three-layer model, design implications | **A1_TTT_THUCYDIDES_TRAP_REFERENCE_v2.md** | ● | Comprehensive. Three-layer model (structural / situational / personal). 6 flashpoints. Clocks and attractors. v1.1. |
| A2 | **World building & naming** — Fictional frame, country names, character names, naming principles, transparent fiction | Distributed across **B1** (country names) and **B2** (character names) | ◐ | All naming is complete and consistent. No standalone consolidation document — the information exists across B1 and B2. Low priority to consolidate; content is done. |
| A3 | **Core tension statement** — Central dynamic, clocks, attractors, catastrophe, success conditions | **A2_TTT_CORE_TENSIONS_v2.md** | ● | Clean one-pager. 5 focal attractors. Resolution conditions. v1.0. |

---

## B — ACTORS & STRUCTURE

| # | Element | Document | Status | Notes |
|---|---------|----------|:------:|-------|
| B1 | **Country roster, organizations & scaling** — All 21 countries with tiers, structural functions, AI/human default. 8 organizations with decision rules. Scaling from 27 to 39+. | **B1_TTT_COUNTRY_STRUCTURE_v2.md** | ● | 21 countries (6 teams + 10 solos). 8 organizations with decision mechanics. Complete scaling table. v2.0. **⚠ Verify G7 membership explicitly includes Ponte (now a base role).** |
| B2 | **Roles architecture** — All team structures with characters, titles, factions, decision rights, election mechanics | **B2_TTT_ROLES_ARCHITECTURE_v2.md** | ● | All 6 teams detailed. Columbia 7/9, Cathay 5, Europe 6/7, Nordostan 3/4, Heartland 3, Persia 3. 10 solo country profiles (skeleton). Team dynamics comparison. v2.0. **⚠ "Indistan" ghost still present. ⚠ EU Commissioner duplicate needs resolution.** |
| B3 | **AI country detailed profiles** — Per AI country: personality, communication style, negotiation approach, risk tolerance, red lines, operating modes | Not yet — skeleton in B2 | ◐ | B2 has basic profiles (character name, personality word, core interests, consequential moves). Full profiles needed for AI Participant Module initialization (F1). Overlaps with starting data. Can be developed early in SEED alongside D-SEED. |
| B4 | **Relationship matrix** — Bilateral relationships between all country pairs at game start | Not started | ○ | No document exists. Important for AI country behavior and scenario calibration. Needed before AI participant initialization. Small document — a matrix table with relationship types (allied/rival/dependent/tense/neutral). |

---

## C — GAME MECHANICS

| # | Element | Document | Status | Notes |
|---|---------|----------|:------:|-------|
| C1 | **Domains architecture** — Four domains (Military, Economy, Domestic Politics, Technology): resources, decisions, AI engine role, cross-domain connections | **C1_TTT_DOMAINS_ARCHITECTURE_v2.md** | ● | All 4 domains comprehensive. 5 unit types, budget cycle, tariffs/sanctions, oil pricing, stability/support model, tech levels, semiconductor chokepoint. v2.0. **⚠ "Spark" ghost still present. ⚠ Production cost scaling must match E1. ⚠ Must add: cost-to-sanctioner, financial market consequences, debt service.** |
| C2 | **Action system** — Complete list of player actions with timing, authorization chains, processing system assignment | **C2_TTT_ACTION_SYSTEM_v2.md** | ● | ~30 actions, 6 categories. Authorization chains. Role-specific exclusives. v3.0. |
| C3 | **Time structure** — Round structure, dramatic arc, formats, overnight, scheduled events | **C3_TTT_TIME_STRUCTURE_v2.md** | ● | 6-8 rounds × half-year. Variable compression. Two-day + single-day formats. Scheduled events calendar. v1.1. |
| C4 | **Map & theaters** — Global map, theater zoom-ins, chokepoints, activation conditions | **C4_TTT_MAP_CONCEPT_v2.md** | ● | Two-layer system. 8 chokepoints. 5-6 potential theaters. Digital + physical. v1.1. |
| C5 | **Public speaking & press** — Speech protocol (when, duration, audience, effect). Press mechanic (publication, censorship, Veritas role) | Not started | ○ | Speeches and press mentioned across B2, C1, C3 but no standalone specification. Small document combining both — they are related mechanics (public communication). |
| C6 | **Contracts, treaties & collective decisions** — Treaty format and enforcement. Organization decision mechanics per org. Election and coup procedures. | Partially covered across B1, C1, C2 | ○ | Core philosophy is clear (treaties stored not enforced, spot transactions irreversible). Election mechanics detailed in C1. Coup multi-step in C1. Missing: a single consolidated reference. Low priority — content exists, format doesn't. |

**Note:** Previous checklist had 8 items (C1-C8). C5 (public speaking) and C6 (press) consolidated into one item. C7 (contracts/treaties) and C8 (collective decisions) consolidated into one item. Content coverage unchanged.

---

## D — PARAMETERS & STARTING DATA

| # | Element | Document | Status | Notes |
|---|---------|----------|:------:|-------|
| D0 | **Parameter structure** — Complete inventory of all scenario parameters classified into three blocks: Seed Design (A), Scenario Configuration (B), SIM-Run Preset (C). 7 domains, 174 parameters. | **D0_TTT_PARAMETER_STRUCTURE_v2.md** | ● | All parameters identified and classified. Roadmap for D1-D5 SEED deliverables defined within. v1.1. **⚠ UNGA missing from organization roster.** |
| D-SEED | **Starting scenario data** — Public state of the world, starting resource allocations per country, starting sanctions/tariffs, private role brief seeds, AI country initial postures | Deferred to SEED stage | ⊘ | Previously listed as D1-D5 (5 separate items). All deferred to SEED stage by design — concept phase defines WHAT parameters exist; SEED phase assigns VALUES. D0 provides the complete structure these will fill. |

---

## E — ENGINE SPECIFICATIONS

| # | Element | Document | Status | Notes |
|---|---------|----------|:------:|-------|
| E0 | **Engine architecture** — Three systems (Transaction/Market, Live Action, World Model) + persistent DB. 8-step processing sequence. Complete I/O specification. Action timing. Output structure (World/Country/Individual levels). | **E1_TTT_ENGINE_ARCHITECTURE_v2.md** | ● | Comprehensive architecture. All three engines defined. Full processing sequence. Output tables. 11 detailed design elements identified for SEED stage. v0.3. **⚠ "Spark" ghost present. ⚠ Production cost scaling must match C1. ⚠ "Social score" → "Stability Index". ⚠ "Capacity investment" ghost in budget inputs. ⚠ Asset seizure orphan (parked in C2 v3). ⚠ Nuclear auth chain must match B2/C2.** |
| E-SEED | **Engine detail specifications** — National budget model, economic model, stability model, military production, technology model, combat resolution, covert ops, narrative generation, elections, transaction engine spec, live action engine spec | Deferred to SEED stage | ⊘ | Previously listed as E1.1-E1.11 (11 separate items). All require formulas, probability tables, and calibration values — this is SEED-level work. E0 defines what each specification must contain and how they interconnect. |

---

## F — AI MODULES

| # | Element | Document | Status | Notes |
|---|---------|----------|:------:|-------|
| F1 | **AI Participant Module** — Standalone reusable module. Three-layer architecture (Cognitive Core / SIM Adapter / Module Interface Protocol). 4-block cognitive model. Perceive→Think→Act cycle. Autonomous action loop. Conversation and voice engines. KING inheritance. | **F1_TTT_AI_PARTICIPANT_MODULE_v2.md** | ● | Covers cognitive architecture, decision framework, interaction protocol, conversation engine, voice engine, module interface (7 message types), TTT adapter, operating modes, moderator controls. v1.1. |
| F2 | **AI Assistant Module ("Navigator")** — Personal AI mentor for human participants. Three-phase lifecycle (intro/mid/outro). Prisoner/Tourist/Partner framework. Prompt assembly. Structured data extraction. Post-SIM analytics. | **F2_TTT_AI_ASSISTANT_MODULE_v2.md** | ● | Covers concept, participant-facing interaction, facilitator dashboard, post-game analysis pipeline. Direct/friendly communication style. Reusable module architecture. v1.0. |

**Note:** Previous checklist had sections F (5 items: cognitive architecture, character profiles, decision framework, interaction protocol, operating modes) and G (3 items: Oracle concept, participant advisory, post-game analysis) — 8 items total. These are now consolidated into 2 comprehensive documents covering all 8 areas at concept level.

---

## G — WEB APP ARCHITECTURE

| # | Element | Document | Status | Notes |
|---|---------|----------|:------:|-------|
| G1 | **Web app architecture** — Three-layer platform (Platform / Core Simulation / User-Facing). 15 modules: Auth & Identity, Database (Supabase), Real-Time Layer, Recording & Transcripts, File Storage, Transaction Engine, Live Action Engine, World Model Engine, Communication System, AI Participant Module, AI Assistant Module, Scenario Configurator (with AI-assisted context refresh), Participant Interface, Facilitator Dashboard, Public Display. Module dependencies. Data flow scenarios. KING inheritance. | **G1_TTT_WEB_APP_ARCHITECTURE_v2.md** | ● | Covers all 6 items from previous H section (scenario configurator, participant interface, facilitator dashboard, public display, communication system, data capture) plus platform infrastructure (auth, DB, real-time layer, storage). Technology stack. Information asymmetry enforcement. v1.0. |

**Note:** Previous checklist had section H with 6 items (H1-H6). All consolidated into one architecture document.

---

## H — DELIVERY & OPERATIONS

| # | Element | Document | Status | Notes |
|---|---------|----------|:------:|-------|
| H1 | **Delivery & operations** — Complete delivery package: facilitator model (3-5 people), customization/setup process, physical location requirements, participant pre-work, printed materials/artefacts, intro briefing, event schedule, reflection circles, structured debrief with awards, post-event deliverables, moderator instructions, training models, contingency procedures, marketing/registration, feedback collection, licensing model. Master delivery checklist. | **I1_TTT_DELIVERY_OPERATIONS_v2.md** | ● | 15 sections covering the full delivery lifecycle from marketing to post-event reports. Details to be refined after first delivery. v1.0. |

**Note:** Previous checklist had section I with 4 items (facilitator model, debrief structure, learning objectives, execution plan). All consolidated and expanded into one comprehensive document.

---

## Document Inventory (CONCEPT V 2.0 folder)

| # | File | Section | Size |
|---|------|---------|------|
| 1 | A1_TTT_THUCYDIDES_TRAP_REFERENCE_v2.md | A1 | ~30 KB |
| 2 | A2_TTT_CORE_TENSIONS_v2.md | A3 | ~6 KB |
| 3 | B1_TTT_COUNTRY_STRUCTURE_v2.md | B1 | ~18 KB |
| 4 | B2_TTT_ROLES_ARCHITECTURE_v2.md | B2 | ~23 KB |
| 5 | C1_TTT_DOMAINS_ARCHITECTURE_v2.md | C1 | ~32 KB |
| 6 | C2_TTT_ACTION_SYSTEM_v2.md | C2 | ~12 KB |
| 7 | C3_TTT_TIME_STRUCTURE_v2.md | C3 | ~20 KB |
| 8 | C4_TTT_MAP_CONCEPT_v2.md | C4 | ~11 KB |
| 9 | D0_TTT_PARAMETER_STRUCTURE_v2.md | D0 | ~38 KB |
| 10 | E1_TTT_ENGINE_ARCHITECTURE_v2.md | E0 | ~43 KB |
| 11 | F1_TTT_AI_PARTICIPANT_MODULE_v2.md | F1 | ~37 KB |
| 12 | F2_TTT_AI_ASSISTANT_MODULE_v2.md | F2 | ~24 KB |
| 13 | G1_TTT_WEB_APP_ARCHITECTURE_v2.md | G1 | ~53 KB |
| 14 | I1_TTT_DELIVERY_OPERATIONS_v2.md | H1 | ~43 KB |
| | **TOTAL** | | **~390 KB** |

---

## What Remains at CONCEPT Stage

### Open items (3):

1. **B4: Relationship matrix** — a bilateral relationship table across all country pairs. Small document. Useful for AI initialization and scenario calibration. Can be done quickly.

2. **C5: Public speaking & press** — speech protocol and press mechanic. Small document combining two related mechanics. Referenced in multiple places but never specified standalone.

3. **C6: Contracts, treaties & collective decisions** — consolidated reference for treaty mechanics, org decision procedures, elections, coups. Content mostly exists across B1, C1, C2 — needs consolidation into one reference. Low priority.

### In-progress items (2):

4. **A2: World building consolidation** — naming principles and fictional frame exist across B1 and B2. A standalone doc would consolidate but is low priority since all content is done.

5. **B3: AI country detailed profiles** — skeleton exists in B2. Full profiles (communication style, negotiation approach, risk tolerance, red lines) needed for F1 module initialization. Can be developed early in SEED alongside starting data.

### Mechanics to add to concept docs before SEED (3):

6. ~~**Cost-to-sanctioner formula**~~ **ADDED (v3.2):** Sanctions cost imposer 30-50% of damage via bilateral trade exposure. Coalition threshold at 60%. Financial sanctions carry de-dollarization cost. Tariffs net-negative for imposer. Added to C1.

7. ~~**Financial market consequences**~~ **ADDED (v3.2):** Crisis threshold triggers capital flight (5-10% GDP growth cost). Non-linear panic mechanic. Added to C1.

8. ~~**Debt service mechanic**~~ **ADDED (v3.2):** 10-15% of deficit becomes permanent debt service. Double hit for printing + deficits. Ponte starts with pre-existing debt. Added to C1.

### Deferred to SEED (2 blocks + 3 mechanics):

9. **D-SEED: Starting scenario data** — public world briefing, resource allocations, sanctions/tariffs, role briefs, AI postures. Structure defined in D0; values assigned in SEED.

10. **E-SEED: Engine detail specifications** — 11 formula/table specifications (budget, economic, stability, military production, technology, combat, covert ops, narrative, elections, transaction engine, live action engine). Architecture defined in E0; formulas and calibration in SEED.

11. **Dollar System Dependence** — requires detailed economic model. Design in E-SEED.

12. **Inflation bands** — requires calibrated economic model. Design in E-SEED.

13. **Debt sovereign crisis mechanics** — crisis triggers, IMF intervention, restructuring. Requires SEED-level calibration (concept only needs basic debt service, item 8 above).

### Dropped / Not needed (6):

- Escalation ladder document (emergent from existing mechanics)
- De-escalation mechanic (covered by diplomatic actions in C2)
- Disinformation mechanic (covered by Veritas/press + covert ops)
- Back-channels mechanic (natural human behavior)
- Combat fatigue (covered by unit attrition in C1)
- Fog-of-war incidents (low payoff; possible SEED event card)

### Narrative only — AI engine (1):

- **Refugee flows** — narrated by AI World Model as consequence of wars/sanctions/instability. No player mechanic.

---

## Recommended Path to SEED Stage

**To close out CONCEPT (required before SEED):**
1. ~~Resolve all CRITICAL consistency issues~~ — **DONE (v3.2)**
2. ~~Add three missing mechanics to C1~~ — **DONE (v3.2)**
3. B4: Relationship matrix (1 session)
4. C5: Public speaking & press protocol (1 session)

**To begin SEED:**
5. D-SEED starting with D2 (starting resource allocations) — the single most important deliverable. All engine specs and AI initialization depend on having concrete numbers.
6. E-SEED starting with E1.6 (combat resolution) and E1.2 (economic model) — the most complex specifications.
7. B3: AI country detailed profiles — needed before AI participant testing.

---

## Changelog
- **v3.2 (2026-03-25):** All fixes applied. CRITICAL items #1-#4 resolved (Spark scrubbed, Indistan scrubbed, production costs standardized to 1x/2x/4x per unit). WARNING items #8-#11 resolved (nuclear auth unified to always-3, social score→Stability Index, capacity investment removed, asset seizure removed). Territorial claim→Public statement in E1. Three mechanics added to C1: cost-to-sanctioner, financial market consequences, debt service. Personal dimension mechanics added to B2 and C1 (legacy objectives, succession anxiety, health events for Helmsman/Pathfinder/Dealer). Cathay authority constraints added to B2 and B1 (information dependency, implementation friction, purge costs, Sage activation). Amphibious assault rules added to C1, C2, D0 (3:1 standard, 4:1 Formosa, naval superiority prerequisite).
- **v3.1 (2026-03-25):** QC review by Vera. Re-opened CRITICAL items #1 (Spark ghost — still in E1, C1) and #2 (Indistan — still in B2). Added CRITICAL #4 (production cost scaling contradiction 1x/2x/3x vs 1x/4x/9x). Added 9 new WARNING items (#7–#14): stability thresholds, nuclear auth chain, "social score" legacy term, "capacity investment" ghost, asset seizure orphan, UNGA omission, EU Commissioner duplicate, G7/Ponte membership. Added MISSING MECHANICS TRIAGE section: 3 mechanics to add to concept (cost-to-sanctioner, financial market consequences, debt service), 3 deferred to SEED (dollar dependence, inflation bands, sovereign crisis), 6 dropped (escalation ladder, de-escalation, disinformation, back-channels, combat fatigue, fog-of-war), 1 narrative-only (refugee flows). Updated "What Remains" and "Recommended Path" sections accordingly. Warning annotations added to affected items in sections B, C, D, E.
- **v3.0 (2026-03-25):** Major restructure reflecting actual document production. Consolidated from 52 items to 21. Sections F (AI Participants, 5 items) and G (AI Assistant, 3 items) merged into F (AI Modules, 2 items) — both covered by F1 and F2 documents. Section H (Web App, 6 items) consolidated into G (1 item) — covered by G1 document. Section I (Delivery, 4 items) consolidated into H (1 item) — covered by I1 document. Section D: D0 (parameter structure) added as complete; D1-D5 deferred to SEED as single block. Section E: E1.1-E1.11 deferred to SEED as single block. Section C: 8 items consolidated to 6. Section B: 6 items consolidated to 4. Document inventory added. New documents assessed: D0, F1, F2, G1, I1 — all marked complete. Overall: 14 complete, 2 in-progress, 3 open, 2 deferred.
- **v2.0 (2026-03-25):** Complete reassessment. Section E restructured to 12 items. 3 critical consistency issues identified and resolved. 52 items total.
- **v1.0 (2026-03-20):** Initial checklist. 9 sections, 42 items.
