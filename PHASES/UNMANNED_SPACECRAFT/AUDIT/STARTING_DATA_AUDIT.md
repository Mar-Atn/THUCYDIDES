# Starting Data Audit — 2026-04-08

**Method:** Direct DB queries + code cross-reference. Not "table exists" — actual data verified.

---

## CRITICAL ISSUES (data wrong or missing, blocks correct operation)

### C1. ~~`status` column vs `relationship` column mismatch~~ FIXED 2026-04-08
Updated all 380 rows: status now derived from relationship column. Distribution: neutral 128, friendly 126, hostile 43, allied 42, tense 35, military_conflict 6. Engine war detection now works correctly.

### C2. ~~Zero basing rights defined~~ FIXED 2026-04-08
Seeded 12 basing rights records: Columbia hosted in 9 allied countries (Yamato, Hanguk, Teutonia, Albion, Phrygia, Formosa, Mirage, Ponte, Freeland), Sarmatia-Choson mutual, Gallia in Mirage.

### C3. Pre-seeded meetings: ZERO records
Table exists, 0 rows. R1 starts with no kickoff events — agents have no initial catalyst.

**Need:** UNSC emergency (Persia nuclear), OPEC+ extraordinary, peace talks (Ruthenia-Sarmatia mediation), Columbia-Cathay bilateral summit.

### C4. Elections: NO table, no logic
No `elections` table exists in the schema. Columbia mid-term (R2), Columbia presidential (R5), Ruthenia wartime (player-triggered) — none defined.

### ~~C5. `bond_yield` and `gold_price`~~ FIXED (2026-04-08)
Columns DROPPED from `global_state_per_round`. Were invented during implementation with no design basis (zero mentions in any SEED/CONCEPT document). Removed from Observatory UI and DB.

### ~~C6. Global state phantom data~~ FIXED (2026-04-08)
Phantom R3-R6 rows DELETED. Only R0-R2 remain (actual simulation data).

---

## MEDIUM ISSUES (incomplete data, affects quality but doesn't break)

### M1. Powers → action mapping not enforced
All 40 roles have `powers` arrays defined (good). Examples:
- Dealer: `[set_tariffs, authorize_attack, fire_team_member, approve_nuclear, sign_treaty, set_budget, endorse_successor]`
- Shadow (Intel Director): `[intelligence_briefing, covert_operations, information_control]`

**But:** The engine does NOT check if an agent has the power to perform an action. Any agent can commit any action. Powers are decorative.

**Impact:** In 20-HoS mode this is acceptable (HoS has most powers). In 40-role mode this is CRITICAL — an opposition politician shouldn't be able to launch attacks.

### M2. Covert op cards — defined but not consumed
All roles have card counts:
- Shadow (Columbia Intel): sabotage 3, cyber 3, disinfo 3, election_meddling 1, assassination 1
- Helmsman (Cathay): sabotage 1, cyber 1, disinfo 1, election_meddling 1, assassination 1
- Havana (Caribe): disinfo 1 only

**But:** The engine doesn't track card consumption. An agent can use unlimited covert ops regardless of their card pool.

### M3. Personal coins — defined but not tracked during play
All roles have personal_coins (range 1-5):
- Helmsman, Wellspring, Compass, Dealer: 5 coins each
- Pyro, Havana, Bulwark, Dawn: 1 coin each

**But:** No mechanism deducts personal coins when used. No transaction flow for personal (as opposed to country) coins.

### M4. Public biography field — ~~missing~~ FIXED (2026-04-08)
`public_bio` column added to `roles` table. All 40 roles populated with 2-3 sentence public-facing biographies (no secret objectives or ticking clocks). Column: `text NOT NULL DEFAULT ''`.

### M5. Nuclear site hex coordinates — ~~not in DB~~ FIXED (2026-04-08)
Already stored in `sim_templates.map_config.nuclear_sites` (JSONB): Persia (7,13), Choson (3,18). Verified correct. Also added to `app/engine/config/map_config.py::NUCLEAR_SITES` as code constant. Documented in SEED_C_MAP_UNITS_MASTER_v1.md section 1.3a.

---

## WHAT EXISTS AND IS CORRECT

### Countries (20) — VERIFIED COMPLETE
All economic, military, political, technology fields populated:
- GDP range: 0.3 (Choson) to 280 (Columbia)
- Treasury: 0 (Albion, Formosa) to 50 (Cathay)
- Nuclear: T0-T3 correctly assigned
- AI tech: L0-L3 correctly assigned
- OPEC flags, oil production, sectors, debt ratios — all present

### Roles (40) — VERIFIED COMPLETE
- 20 HoS + 20 secondary roles (military chiefs, intel directors, diplomats, tycoons, opposition)
- All have: character_name, title, country, powers, objectives, ticking_clock, personal_coins
- All have: covert op card pools (sabotage, cyber, disinfo, election_meddling, assassination, protest_stim)
- All have: intelligence_pool, fatherland_appeal flags
- Columbia has 8 roles (most complex team), Cathay 4, Sarmatia 4, Ruthenia 3, Persia 3, Gallia 2, others 1 each

### Relationships (380) — DATA EXISTS, COLUMN MISMATCH (see C1)
`relationship` column (the real data):
- 6 at_war pairs (Sarmatia↔Ruthenia, Persia↔Columbia, Persia↔Levantia)
- 42 alliance/close_ally pairs (Columbia hub: 11 allies)
- 41 hostile pairs (Choson hostile with 9 countries)
- 35 tense pairs
- 126 friendly pairs
- 128 neutral pairs
- 2 strategic_rival (Columbia↔Cathay)

### Sanctions (36 records) — VERIFIED COMPLETE & RICH
Properly differentiated:
- L3 (maximum): Columbia→Persia/Sarmatia/Caribe/Choson, Ruthenia↔Sarmatia, Levantia↔Persia, Hanguk→Choson, Yamato→Choson
- L2 (significant): EU bloc→Sarmatia, Columbia→Cathay trade restrictions
- L1 (symbolic): counter-sanctions, minor alignment
- L-1 (evasion support): Cathay→Sarmatia (-1 = sanctions undermining)
- Rich notes explaining each (e.g., "Comprehensive: financial SWIFT exclusion technology energy price cap asset freezes")

### Tariffs (29 records) — VERIFIED COMPLETE
- L3: Columbia→Cathay (47.5%), Columbia→Caribe/Persia (full embargo), Levantia↔Persia, Ruthenia→Sarmatia
- L2: Cathay→Columbia (retaliatory ~30%), Sarmatia counter-tariffs
- L1: EU de-risking, border restrictions

### Units (345 default layout) — VERIFIED
Active, reserve, embarked status. Positioned on map.

### Organizations (9) + memberships (60) — VERIFIED
Western Treaty, EU, UNSC, BRICS+, OPEC+, G7, Columbia Parliament, SCO, UNGA.

### Formulas — VERIFIED (all coefficients in countries table)
GDP growth, sanctions coefficients, tariff coefficients, tax rates, social baselines, production costs.

---

## SUMMARY TABLE

| Element | Exists | Correct | Action needed |
|---|---|---|---|
| Countries (20) | YES | YES | — |
| Roles (40) + powers | YES | YES | M1: enforce powers in engine |
| Roles covert cards | YES | NOT CONSUMED | M2: track card usage |
| Roles personal coins | YES | NOT TRACKED | M3: wire personal coin spending |
| Roles public_bio | YES | YES | ~~M4~~ FIXED 2026-04-08 |
| Relationships (380) | YES | YES | ~~C1~~ FIXED 2026-04-08 |
| Basing rights (12) | YES | YES | ~~C2~~ FIXED 2026-04-08 |
| Sanctions (36) | YES | YES | — |
| Tariffs (29) | YES | YES | — |
| Units (345) | YES | YES | — |
| Organizations (9) | YES | YES | — |
| Oil price | YES | YES | — |
| Stock indexes | YES | PLACEHOLDER | 3 named indexes not yet split |
| Bond yield | DROPPED | ~~INVENTED~~ | ~~C5~~ FIXED 2026-04-08 |
| Gold price | DROPPED | ~~INVENTED~~ | ~~C5~~ FIXED 2026-04-08 |
| Global state R3-R6 | DELETED | ~~PHANTOM~~ | ~~C6~~ FIXED 2026-04-08 |
| Pre-seeded meetings | NO | — | **C3: seed kickoff events** |
| Elections | NO TABLE | — | **C4: create table + logic** |
| Nuclear site hexes | YES | YES | ~~M5~~ FIXED 2026-04-08 |
