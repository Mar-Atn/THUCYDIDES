# Country Seed Template
## Thucydides Trap SIM — Standard Format for All Countries
**Version:** 1.0 | **Date:** 2026-03-26

---

### Purpose
This template defines the standard structure for every country in the SIM. Each country seed is the canonical reference for that country's starting state, context, and relationships. It feeds: participant briefings, AI country profiles, engine starting data, and map deployment.

---

## SECTION 1: IDENTITY

| Field | Content |
|-------|---------|
| **SIM Name** | (e.g., Columbia) |
| **Real-World Parallel** | (e.g., United States of America) |
| **Territory** | Zones on map (reference zone IDs) |
| **Regime Type** | Democracy / Autocracy / Hybrid |
| **Team Type** | Team (multiple players) / Solo (1 human or AI) |
| **Team Size** | Min / Standard / Full (e.g., 7 / 7 / 9) |
| **Roles** | List of all role names in this country |

---

## SECTION 2: MEMBERSHIPS

| Organization | Role in Org | Voting/Decision Rights | Notes |
|-------------|------------|----------------------|-------|
| (e.g., Western Treaty / NATO) | Founding member, largest military contributor | Consensus — can block any decision | |
| (e.g., The Seven / G7) | Chair (rotates) | Non-binding coordination | |
| (e.g., The Council / UNSC) | Permanent member | Veto power | |

---

## SECTION 3: RELATIONSHIPS

| Country | Relationship | Key Dynamic |
|---------|:------------:|------------|
| Cathay | Strategic rival | Power transition — the Trap itself. Economic interdependence + military competition. |
| Nordostan | Adversary | Sanctions + proxy conflict via Heartland. Nuclear peer. |
| Gallia | Ally (with friction) | NATO but EU strategic autonomy aspirations create tension. |
| Bharata | Courtship | Need India on sanctions coalition. India plays both sides. |
| Formosa | Protectorate | Defend if attacked — but strategic ambiguity is the policy. |

**Relationship scale:**
- **Alliance/Treaty** — formal commitment (NATO Article 5, mutual defense)
- **Close ally** — deep cooperation, shared strategic vision
- **Friendly** — positive relations, some cooperation
- **Neutral** — no strong alignment
- **Tense** — competing interests, diplomatic friction
- **Hostile** — active opposition, sanctions, proxy conflict
- **At war** — direct military conflict

---

## SECTION 4: HISTORY & CONTEXT (Country Brief)

Narrative description (300-500 words) covering:
- Brief relevant history (how this country arrived at its current position)
- Current political situation (who's in charge, what's the domestic mood)
- Key challenges and opportunities at game start
- How this country relates to the Thucydides Trap central dynamic
- What makes this country interesting to play

*Written in third person, factual register. This becomes the basis for the participant's country briefing.*

---

## SECTION 5: ECONOMIC DATA

| Indicator | Value | Notes |
|-----------|-------|-------|
| GDP (game coins) | | 1 coin ≈ $100B real |
| GDP growth rate (base %) | | Before modifiers |
| Economic sectors | Resources: X%, Industry: X%, Services: X%, Technology: X% | |
| Tax/revenue rate | | Fraction of GDP → state revenue |
| Starting treasury (coins) | | Reserves available at game start |
| Inflation rate (%) | | |
| Trade balance (coins) | | Positive = surplus |
| Oil producer? | Yes/No | If yes: OPEC+ member? Starting production level? |
| Formosa semiconductor dependency | 0-1 | How much tech sector depends on Formosa chips |
| Debt burden (coins/round) | | Pre-existing debt service deducted from revenue |
| Social spending baseline (%) | | Minimum social spending to maintain stability |

---

## SECTION 6: MILITARY DATA

| Unit Type | Count | Deployment (zone IDs) | Notes |
|-----------|:-----:|----------------------|-------|
| Ground forces | | | |
| Naval forces | | | |
| Tactical air/missiles | | | |
| Strategic missiles | | | Fixed allocation (non-producible except Cathay) |
| Air defense | | | Fixed allocation (non-producible, scarce) |

| Military Parameter | Value | Notes |
|-------------------|-------|-------|
| Production costs (per unit type) | Ground: X, Naval: X, Tac Air: X | Country-specific |
| Production capacity (max per round) | Ground: X, Naval: X, Tac Air: X | |
| Maintenance cost (per unit/round) | | |
| Bases hosted | (e.g., Columbia base in Teutonia) | Foreign forces on your soil |
| Bases abroad | (e.g., Columbia bases in Yamato, Teutonia, Gulf) | Your forces on foreign soil |
| War status | (e.g., At war with Heartland) | Active conflicts |

---

## SECTION 7: POLITICAL DATA

| Indicator | Value | Notes |
|-----------|-------|-------|
| Stability Index (1-10) | | 8-10 stable, 4-5 crisis, 2-3 severe, 1 failed |
| Political Support (0-100%) | | Elite loyalty (autocracy) / public approval (democracy) |
| Dem/Rep split | | Columbia only |
| War tiredness | | 0 = no war fatigue, accumulates each round at war |
| Troop morale modifier | | Derived from stability |

**Internal dynamics summary:** (2-3 sentences describing the key internal tension — e.g., "Three camps within Columbia: president's loyalists control 3 of 5 parliamentary seats, but mid-term elections in Round 2 could flip the majority.")

---

## SECTION 8: TECHNOLOGY DATA

| Track | Level | R&D Progress | Notes |
|-------|:-----:|:------------:|-------|
| Nuclear | L0-L3 | X% toward next | |
| AI/Semiconductor | L0-L4 | X% toward next | |

| Tech Parameter | Value | Notes |
|---------------|-------|-------|
| Export restrictions in place | (e.g., Cathay rare earth restrictions on Columbia) | |
| Semiconductor dependency | (e.g., 70% dependent on Formosa) | |
| R&D investment capacity | (coins — how much can be allocated) | |

---

## NOTES ON USAGE

- **Country seeds are the data source** for `SEED_STARTING_DATA.json` — every number in this template maps to a field in the JSON.
- **Section 4 (Context)** feeds the participant country briefing and AI country cognitive Block 1.
- **Section 3 (Relationships)** feeds the bilateral relationship matrix and AI Block 3 (Memory).
- **Sections 5-8 (Data)** feed the engine starting state and map deployments.
- **Countries are developed before roles** — roles reference their country's context, resources, and relationships.
