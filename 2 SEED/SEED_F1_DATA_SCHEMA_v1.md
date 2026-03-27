# Seed Data Schema
## Thucydides Trap SIM — Canonical Data Structure
**Version:** 1.0 | **Date:** 2026-03-26

---

### Principle
**Data in CSVs. Prose in MDs. Never duplicate.**

CSVs are the single source of truth for all quantitative and structural data. They feed: the simulation engine, the test harness, the future database (Supabase import), and validation scripts. MDs contain narrative content (country briefs, role bios, artefact text) and reference CSVs by ID.

### File Structure

```
2 SEED/
├── SEED_DATA_SCHEMA.md          ← THIS FILE: documents every column
├── data/
│   ├── countries.csv            ← 21 rows, ~45 columns
│   ├── roles.csv                ← 40+ rows, ~20 columns
│   ├── organizations.csv        ← 8+ rows, ~10 columns
│   ├── org_memberships.csv      ← Many rows (country × org), ~4 columns
│   ├── relationships.csv        ← ~420 rows (21×20), ~4 columns
│   ├── tariffs.csv              ← Non-zero pairs only, ~3 columns
│   ├── sanctions.csv            ← Non-zero pairs only, ~3 columns
│   ├── deployments.csv          ← ~170 rows (every unit placement), ~4 columns
│   ├── zones.csv                ← ~90 rows (all zones), ~6 columns
│   ├── zone_adjacency.csv       ← ~300+ rows (all connections), ~3 columns
│   └── artefacts.csv            ← Role pack items, ~6 columns
│
├── narratives/
│   ├── world_context.md         ← The "opening briefing" (~2000 words)
│   ├── COLUMBIA.md              ← Country brief (prose only)
│   ├── CATHAY.md
│   └── ... (21 files)
│
├── role_briefs/
│   ├── DEALER.md                ← Bio, views, ticking clock (prose)
│   ├── HELMSMAN.md
│   └── ... (40+ files)
│
└── role_packs/
    ├── DEALER_intel_cathay_buildup.md
    ├── DEALER_econ_forecast.md
    └── ... (artefact content files)
```

---

## CSV SCHEMAS

### 1. countries.csv

One row per country. The master country record.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | string | Unique identifier (lowercase, no spaces) | `columbia` |
| `sim_name` | string | Display name in SIM | `Columbia` |
| `parallel` | string | Real-world parallel | `United States` |
| `regime_type` | enum | `democracy` / `autocracy` / `hybrid` | `democracy` |
| `team_type` | enum | `team` / `solo` | `team` |
| `team_size_min` | int | Minimum human players | `7` |
| `team_size_max` | int | Maximum human players | `9` |
| `ai_default` | bool | Whether AI-operated by default | `false` |
| **Economic** |
| `gdp` | float | GDP in game coins (1 coin ≈ $100B) | `280` |
| `gdp_growth_base` | float | Base growth rate % per round | `1.8` |
| `sector_resources` | int | % of GDP from resources | `5` |
| `sector_industry` | int | % of GDP from industry | `18` |
| `sector_services` | int | % of GDP from services | `55` |
| `sector_technology` | int | % of GDP from technology | `22` |
| `tax_rate` | float | Revenue extraction rate (0-1) | `0.24` |
| `treasury` | float | Starting reserves (coins) | `50` |
| `inflation` | float | Starting inflation % | `3.5` |
| `trade_balance` | float | Starting trade balance (coins, +surplus/-deficit) | `-12` |
| `oil_producer` | bool | Whether oil producer | `true` |
| `opec_member` | bool | OPEC+ member | `false` |
| `opec_production` | enum | Starting level: `low`/`normal`/`high`/`na` | `na` |
| `formosa_dependency` | float | Semiconductor dependency (0-1) | `0.65` |
| `debt_burden` | float | Pre-existing debt service (coins/round) | `5` |
| `social_baseline` | float | Minimum social spending ratio (0-1) | `0.30` |
| **Military** |
| `mil_ground` | int | Ground force units | `22` |
| `mil_naval` | int | Naval units | `14` |
| `mil_tactical_air` | int | Tactical air/missile units | `15` |
| `mil_strategic_missiles` | int | Strategic missile count | `12` |
| `mil_air_defense` | int | Air defense units (non-producible) | `4` |
| `prod_cost_ground` | float | Production cost per ground unit | `3` |
| `prod_cost_naval` | float | Production cost per naval unit | `5` |
| `prod_cost_tactical` | float | Production cost per tactical air unit | `4` |
| `prod_cap_ground` | int | Max ground units producible per round | `4` |
| `prod_cap_naval` | int | Max naval units producible per round | `2` |
| `prod_cap_tactical` | int | Max tactical air producible per round | `3` |
| `maintenance_per_unit` | float | Cost per unit per round | `0.5` |
| `strategic_missile_growth` | int | Auto-produced per round (Cathay only) | `0` |
| **Political** |
| `stability` | float | Starting stability (1-10) | `7` |
| `political_support` | float | Starting support (0-100) | `38` |
| `dem_rep_split_dem` | int | Dem % (Columbia only, 0 for others) | `52` |
| `dem_rep_split_rep` | int | Rep % (Columbia only, 0 for others) | `48` |
| `war_tiredness` | float | Starting war fatigue (0+) | `0` |
| **Technology** |
| `nuclear_level` | int | Nuclear tech level (0-3) | `3` |
| `nuclear_rd_progress` | float | Progress toward next level (0-1) | `1.0` |
| `ai_level` | int | AI/Semiconductor level (0-4) | `3` |
| `ai_rd_progress` | float | Progress toward next level (0-1) | `0.60` |
| **Zones** |
| `home_zones` | string | Comma-separated zone IDs | `col_continental,col_pacific,col_alaska` |

---

### 2. roles.csv

One row per role. All 40+ roles in one file.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | string | Unique identifier | `dealer` |
| `character_name` | string | SIM character name | `Dealer` |
| `parallel` | string | Real-world parallel | `US President` |
| `country_id` | string | FK → countries.id | `columbia` |
| `team` | string | Team name | `Columbia` |
| `faction` | string | Internal faction/camp | `Presidents` |
| `title` | string | Formal title | `President of Columbia` |
| `age` | int | Character age | `80` |
| `gender` | string | `M`/`F` | `M` |
| `is_head_of_state` | bool | Head of state? | `true` |
| `is_military_chief` | bool | Military authority? | `false` |
| `parliament_seat` | int | Parliament seat # (0=none) | `1` |
| `personal_coins` | float | Starting personal wealth | `5` |
| `expansion_role` | bool | Optional/expansion role? | `false` |
| `ai_candidate` | bool | Can be AI-operated? | `false` |
| `brief_file` | string | Path to prose brief | `role_briefs/DEALER.md` |
| `powers` | string | Semicolon-separated power list | `set_tariffs;authorize_attack;fire_team_member;approve_nuclear` |
| `objectives` | string | Top 3 objectives (semicolon-sep) | `secure_legacy;manage_succession;contain_cathay` |
| `ticking_clock` | string | Personal urgency | `Term-limited, age 80. Legacy = reshaping world order.` |

---

### 3. organizations.csv

One row per organization.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | string | Unique identifier | `western_treaty` |
| `sim_name` | string | Display name | `Western Treaty` |
| `parallel` | string | Real-world parallel | `NATO` |
| `decision_rule` | string | How decisions are made | `consensus` |
| `chair_role_id` | string | Who chairs (role ID or empty) | `` |
| `voting_threshold` | string | What's needed to pass | `unanimous` |
| `meeting_frequency` | string | When it meets | `scheduled_r1_r4` |
| `can_be_created` | bool | Player-creatable? | `false` |
| `description` | string | Brief function description | `Military alliance with Article 5 collective defense` |

---

### 4. org_memberships.csv

One row per country-organization pair.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `country_id` | string | FK → countries.id | `columbia` |
| `org_id` | string | FK → organizations.id | `western_treaty` |
| `role_in_org` | string | Status/role | `founding_member` |
| `has_veto` | bool | Veto power? | `false` |

---

### 5. relationships.csv

One row per directed country pair. Captures asymmetric relationships.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `from_country` | string | FK → countries.id | `columbia` |
| `to_country` | string | FK → countries.id | `cathay` |
| `relationship` | enum | `alliance`/`close_ally`/`friendly`/`neutral`/`tense`/`hostile`/`at_war` | `hostile` |
| `dynamic` | string | Brief description of the relationship dynamic | `Strategic rival. Tariff war. Tech competition. Formosa tripwire.` |

---

### 6. tariffs.csv

Non-zero tariff pairs only. All unmentioned pairs default to 0.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `imposer` | string | Country imposing tariff | `columbia` |
| `target` | string | Country targeted | `cathay` |
| `level` | int | Tariff level (0-3) | `3` |

---

### 7. sanctions.csv

Non-zero sanctions pairs only. All unmentioned pairs default to 0.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `country` | string | Country's sanctions position | `columbia` |
| `target` | string | Target of sanctions | `nordostan` |
| `level` | int | Sanctions level (-3 to +3) | `3` |

---

### 8. deployments.csv

Every military unit placement at game start.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `country_id` | string | FK → countries.id | `columbia` |
| `unit_type` | enum | `ground`/`naval`/`tactical_air`/`strategic_missile`/`air_defense` | `ground` |
| `count` | int | Number of units | `8` |
| `zone_id` | string | FK → zones.id | `col_continental` |

---

### 9. zones.csv

Every zone on the global and theater maps.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | string | Unique identifier | `col_continental` |
| `display_name` | string | Name shown on map | `Columbia Continental` |
| `type` | enum | `land_home`/`land_contested`/`sea`/`chokepoint_sea` | `land_home` |
| `owner` | string | FK → countries.id (or `none`) | `columbia` |
| `theater` | string | Theater if applicable (`global`/`eastern_ereb`/`mashriq`/`taiwan`/`caribbean`/`thule`/`korea`) | `global` |
| `is_chokepoint` | bool | Maritime chokepoint? | `false` |

---

### 10. zone_adjacency.csv

Every connection between zones. Bidirectional — list each pair once.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `zone_a` | string | FK → zones.id | `col_continental` |
| `zone_b` | string | FK → zones.id | `sea_caribbean` |
| `connection_type` | enum | `land_land`/`sea_sea`/`land_sea` | `land_sea` |

---

### 11. artefacts.csv

Role pack items — unique information given to specific roles at game start.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | string | Unique identifier | `dealer_intel_cathay_buildup` |
| `role_id` | string | FK → roles.id (who receives it) | `dealer` |
| `title` | string | Artefact title | `CIA Assessment: Cathay Naval Buildup Timeline` |
| `classification` | enum | `role_specific`/`team_shared`/`public` | `role_specific` |
| `format` | string | In-game format | `Intelligence memo` |
| `content_file` | string | Path to content MD | `role_packs/DEALER_intel_cathay_buildup.md` |

---

## Validation Rules

These can be automated and run after every data update:

1. Every `country_id` in roles.csv exists in countries.csv
2. Every `country_id` in org_memberships.csv exists in countries.csv
3. Every `org_id` in org_memberships.csv exists in organizations.csv
4. Every `zone_id` in deployments.csv exists in zones.csv
5. Every zone in zone_adjacency.csv exists in zones.csv
6. Sum of units in deployments.csv per country per type = corresponding column in countries.csv
7. Sector percentages sum to 100 for each country
8. Every country in relationships.csv exists in countries.csv
9. Every role's `country_id` matches a country in countries.csv
10. No duplicate IDs in any CSV
11. Tariff levels are 0-3, sanctions levels are -3 to +3
12. Stability is 1-10, support is 0-100
13. Tech levels are within valid ranges (nuclear 0-3, AI 0-4)
14. Every country has at least one home zone
15. Every home zone has an owner matching the country

---

## Usage

**Engine loads:** countries.csv + tariffs.csv + sanctions.csv + deployments.csv + zones.csv + zone_adjacency.csv
**Test runner loads:** Above + roles.csv (for AI profiles) + organizations.csv + org_memberships.csv
**Validation script loads:** ALL CSVs, checks all rules above
**Future database import:** Each CSV maps to one Supabase table. Column names match field names.
**Narrative files:** Referenced by ID. DEALER.md contains prose for the role with id=`dealer`. COLUMBIA.md contains prose for country with id=`columbia`.
