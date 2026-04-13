# CARD: TEMPLATE SCHEMA

**What a Template IS:** The complete game definition — map, countries, roles, formulas, rules. Evolves over months. Versioned (semver + name).

**Current:** Template v1.0 "TTT Power Transition 2026"

---

## THREE-LEVEL HIERARCHY

```
TEMPLATE (the game itself — evolves over months)
  └── SCENARIO (one event's configuration — sparse override of template)
        └── SIM-RUN (one execution — immutable once started)
```

### Template owns (canonical defaults)
- Map topology (hexes, adjacency, theaters, chokepoints)
- Country master list + starting stats
- Role library + character sheets + personas
- Formula coefficients (per-country, LOCKED per version)
- Default relationship matrix
- Default unit deployment layout
- Allowed round-count range, oil-price range, theater set

### Scenario overrides (sparse — falls back to template if unset)
- Event metadata (venue, facilitator, participant profile)
- SIM starting date, max rounds, oil price starting value
- Country stat overrides (only changed fields)
- Relationship overrides (bilateral deltas)
- Role briefing/persona overrides
- Unit layout override (or NULL = use template default)
- Election schedule, scripted event timeline

### SIM-Run captures (immutable once started)
- Frozen scenario config snapshot
- User ↔ role bindings
- Per-round world state snapshots
- Per-round country state snapshots
- Append-only event log
- Agent memories, decisions, combat results

---

## TEMPLATE v1.0 CONTENTS

### Map
| Component | Size | Location |
|---|---|---|
| Global grid | 10 rows × 20 cols | `sim_templates.rules.map_global` |
| Eastern Ereb theater | 10 × 10 | `sim_templates.rules.map_eastern_ereb` |
| Mashriq theater | 10 × 10 | `sim_templates.rules.map_mashriq` |
| Theater↔global linkage | 12 link hexes | `engine/config/map_config.py` |
| Chokepoints | 9 named | In map grid data |

### Countries (20)
| Data | Location | Notes |
|---|---|---|
| Starting stats | `countries` table (Supabase) | GDP, treasury, inflation, stability, military counts, nuclear level, sectors, etc. |
| CSV backup | `2 SEED/C_MECHANICS/C4_DATA/countries.csv` | Must stay synced with DB |
| Per-country coefficients | In `countries` table columns | sanctions_coefficient, tariff_coefficient, sanctions_recovery_rounds, etc. |

**Country list:** albion, bharata, caribe, cathay, choson, columbia, formosa, freeland, gallia, hanguk, levantia, mirage, persia, phrygia, ponte, ruthenia, sarmatia, solaria, teutonia, yamato

### Roles (40)
| Data | Location | Notes |
|---|---|---|
| Character sheets | `roles` table (Supabase) | character_name, title, age, faction, powers[], objectives[], ticking_clock, public_bio |
| Covert op card pools | `roles` table columns | intelligence_pool (per round), sabotage_cards, disinfo_cards, election_meddling_cards, assassination_cards (per SIM) |
| Personal assets | `roles` table | personal_coins, fatherland_appeal (bool) |
| Permitted actions | `roles` table | permitted_actions[] (list of action_types this role can invoke) |
| CSV backup | `2 SEED/C_MECHANICS/C4_DATA/roles.csv` | |
| 21 HoS + mil chiefs + intel + diplomats + opposition + tycoons | | |

### Units (345 per layout)
| Data | Location | Notes |
|---|---|---|
| Template default layout | `layout_units` where layout_code='template_v1_0_default' | 345 units |
| Scenario layout (start_one) | `layout_units` where layout_code='start_one' | 345 units |
| CSV backup | `2 SEED/C_MECHANICS/C4_DATA/units.csv` | |
| 5 types | ground, naval, tactical_air, strategic_missile, air_defense | |
| 4 statuses | active, reserve, embarked, destroyed | |

### Country-Specific Data (beyond starting stats)
| Data | Location | Notes |
|---|---|---|
| Martial law mobilization pool | `countries` table | Ground units available via martial law. Sarmatia: 10, Ruthenia: 6, Persia: 8, Cathay: 10. Others: 0. |
| Nuclear site hex | `sim_templates.map_config.nuclear_sites` + `map_config.py::NUCLEAR_SITES` | Physical hex on map. Persia: (7,13), Choson: (3,18). Others: abstract (no map hex). Canonical since 2026-04-08. |
| Initial basing rights | `relationships` table | Reflects real alliance map (Western Treaty members host Columbia, Asian allies). |
| Nuclear level confirmed | `countries` table | Pre-set countries (Columbia T3, Sarmatia T3, Cathay T3, etc.) are confirmed by default. Others start unconfirmed. |

### Starting Relationships & Basing Rights (added 2026-04-08)

**Relationship status distribution (380 bilateral pairs):**
| Status | Count | Examples |
|---|---|---|
| neutral | 128 | Most non-aligned pairs |
| friendly | 126 | Western-aligned pairs, trade partners |
| hostile | 43 | Choson vs most countries, Persia adversaries + strategic_rival (Columbia-Cathay) |
| allied | 42 | Columbia hub: 11 allies; EU bloc mutual |
| tense | 35 | Border disputes, regional competition |
| military_conflict | 6 | Sarmatia-Ruthenia, Persia-Columbia, Persia-Levantia |

**Column semantics:** `relationship` column = the qualitative label (8 values). `status` column = the engine-readable state (8 values, derived from relationship). Engine code checks `status` for war/peace logic.

**Basing rights (12 records):**
| Host | Guest | Parallel |
|---|---|---|
| Yamato, Hanguk, Teutonia, Albion, Phrygia, Formosa, Mirage, Ponte, Freeland | Columbia | Global US base network |
| Choson | Sarmatia | Advisory presence |
| Sarmatia | Choson | Training presence |
| Mirage | Gallia | Djibouti |

Basing rights are tradeable during play. `basing_rights_a_to_b = true` means from_country_id (a) hosts to_country_id (b).

### Formula Coefficients
See CARD_FORMULAS.md. Key per-country values stored in `countries` table:
- `gdp_growth_base` — structural GDP growth rate
- `sanctions_coefficient` — GDP sensitivity to sanctions
- `tariff_coefficient` — GDP sensitivity to tariffs
- `sanctions_recovery_rounds` — rounds to start recovering
- `sanctions_adaptation_rounds` — rounds to full adaptation
- `tax_rate` — revenue extraction rate
- `social_baseline` — baseline social spending ratio
- `maintenance_per_unit` — military upkeep cost per unit
- `prod_cost_ground/naval/tactical` — production costs per unit type
- `prod_cap_ground/naval/tactical` — max production per round

### Pre-seeded Meetings (Scenario data)
3-4 meetings pre-scheduled for R1-R2 to kickstart play. Defined per scenario (can vary per event).
Format: `{round, meeting_type, organization_code, participants[], agenda, location}`

Examples (Template v1.0 / start_one scenario):
- UNSC urgent session — Persia nuclear crisis (R1)
- OPEC+ extraordinary meeting — oil production response (R1)
- Peace talks in Phrygia — Ruthenia, Columbia, Sarmatia reps (R1-R2)
- Columbia-Cathay bilateral summit (R1)

### Elections Schedule (Scenario data)
| Election | Country | Trigger |
|---|---|---|
| Mid-term parliamentary | Columbia | Automatic R2 |
| Presidential | Columbia | Automatic R5 |
| Wartime election | Ruthenia | Player-triggered (HoS or 2+ participants demand) |

### Methodology + Prompts
| Key | Category | Content length | Location |
|---|---|---|---|
| metacognitive_architecture | prompt_template | 1,139 chars | `sim_config` table |
| identity_generation | prompt_template | 898 chars | |
| conversation_behavior | prompt_template | 1,014 chars | |
| reflection_block_3 | prompt_template | 766 chars | |
| reflection_block_4 | prompt_template | 595 chars | |
| crisis_definition | methodology | 730 chars | |
| contagion_rules | methodology | 498 chars | |
| historical_examples | methodology | 573 chars | |
| anti_patterns | methodology | 601 chars | |

---

## SAMPLE DATA (Columbia, Template v1.0)

### Country record
```
sim_name: Columbia | parallel: United States | regime: democracy
GDP: 280 | treasury: 30 | inflation: 3.5% | debt_ratio: 1.25
stability: 7 | political_support: 38% | war_tiredness: 1.0
sectors: resources 8%, industry 18%, services 55%, technology 22%
tax_rate: 24% | social_baseline: 30% | formosa_dependency: 0.65
oil_producer: yes | oil_production: 13.0 mbpd | opec: no
military: 22 ground, 11 naval, 15 air, 12 missiles, 4 AD
nuclear: T3 (confirmed) | AI: L3 (progress 0.5)
production capacity: ground 4/round, naval 2, air 3
```

### Role record (Dealer — President of Columbia)
```
character_name: Dealer | title: President | age: 80 | faction: Presidents
powers: set_tariffs, authorize_attack, fire_team_member, approve_nuclear, sign_treaty, set_budget, endorse_successor
objectives: secure_legacy, manage_succession, contain_cathay
ticking_clock: Term-limited age 80. 10% per-round incapacitation risk. Legacy = reshaping world order.
cards: intelligence 4/round, sabotage 1, cyber 1, disinfo 1, election_meddling 1, assassination 1
personal_coins: 5 | fatherland_appeal: yes
```

### Relationship record
```
columbia → cathay: strategic_rival
  "THE Trap itself. Largest bilateral trade under ~47.5% tariff assault.
   Economic interdependence + military competition in Pacific."
columbia → sarmatia: hostile
  "Nuclear peer adversary. Sanctions regime. Proxy conflict via Ruthenia."
columbia → ruthenia: close_ally
  "Ally at war. Weapons and aid provider. Ruthenia fears abandonment."
```

### Global state (Round 0 baseline)
```
oil_price: $85 | stock_index: 100 | bond_yield: 4.20% | gold: $2400
```

### ⚠ KNOWN DATA ISSUE
Round 0 seeding bug: `political_support` seeded as 5 for ALL countries instead of master values (range 35-70). Most `stability` values also wrong (defaulted to 5). Master `countries` table has correct calibrated values. **Fix required in seeding code before next test run.**

---

## WHAT'S CONFIGURABLE vs HARDCODED

### Configurable (in DB, editable per template/scenario)
- All country starting stats (GDP, stability, military counts, sectors, etc.)
- All per-country formula coefficients (sanctions, tariff, tax, social baseline)
- Role objectives, powers, ticking clocks, covert op card pools
- Unit deployment layouts (which units where at game start)
- Map ownership (which country owns which hex)
- Methodology prompts (AI behavior guidance)
- Oil starting price, round count
- Martial law mobilization pools per country
- Nuclear site hexes (Persia, Choson)
- Initial basing rights map
- Initial bilateral relationships (war/peace/armistice status, tariff/sanction levels)
- Pre-seeded meetings (R1-R2 kickstart events)
- Election schedule (which rounds, which countries)
- Combat probabilities (air strike %, missile %, bombardment %, covert op success/detection %)
- AD coverage and interception probabilities
- Formosa blockade economic impact multipliers

### Hardcoded (in code, change = code release)
- 5 unit types (ground, naval, tactical_air, strategic_missile, air_defense)
- 4 unit statuses (active, reserve, embarked, destroyed)
- Action types (32 actions per CARD_ACTIONS)
- Combat dice mechanics (RISK pairing, iterative, ties → defender)
- Hex topology (pointy-top, odd-r offset)
- Map dimensions (10×20 global, 10×10 theater)
- Coordinate contract (global + local, dual-space adjacency)
- Engine processing order (economic → political → technology)
- 4-block cognitive model structure
- Round phase structure (active loop → resolve → tick → snapshot)
- Transaction mechanics (propose/accept/counter, asset validation, immediate execution)
- Agreement types and enforcement rules (ceasefire = engine-enforced, others = recorded only)
- Stability formula weights — in `political.py`
- R&D thresholds — in `technology.py`

These "in between" values should eventually move to `sim_config` table for facilitator adjustment. Currently hardcoded for speed.
