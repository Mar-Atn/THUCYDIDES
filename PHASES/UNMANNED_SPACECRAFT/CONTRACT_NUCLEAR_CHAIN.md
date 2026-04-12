# CONTRACT: Nuclear Decision Chain

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §1.9 + `CARD_FORMULAS.md` D.6, D.7

---

## 1. OVERVIEW

Nuclear actions are the ONLY multi-step chained decisions in the SIM.
Unlike all other actions (single decision → engine resolves), nuclear
follows a **4-phase state machine**:

```
INITIATE → AUTHORIZE (2 officials) → ALERT + INTERCEPT (T3+ countries) → RESOLVE
```

Each phase involves a separate decision by a different actor. The chain
orchestrator (`engine/orchestrators/nuclear_chain.py`) manages the flow,
triggers AI officer calls, enforces timers, and persists state.

---

## 2. PHASE 1 — INITIATION (HoS decision)

### 2.1 Nuclear Test (`nuclear_test`)

```json
{
  "action_type": "nuclear_test",
  "country_code": "persia",
  "round_num": 4,
  "decision": "change",
  "rationale": "string >= 30 chars",
  "changes": {
    "test_type": "underground",
    "target_global_row": 7,
    "target_global_col": 13
  }
}
```

| Field | Values | Notes |
|---|---|---|
| `test_type` | `"underground"` or `"surface"` | Surface has higher costs + global alert |
| `target` | Own territory hex | Must be a hex owned by the country |

**Prerequisite:** Country's `nuclear_level >= 1` AND either:
- `nuclear_confirmed = true` at the PREVIOUS level (testing to confirm CURRENT level), OR
- `nuclear_rd_progress` has reached the threshold for current level but `nuclear_confirmed = false` (this IS the confirmation test)

Countries with template-seeded confirmed levels (Columbia T3, Sarmatia T3, etc.) don't need to test — they're already confirmed.

### 2.2 Nuclear Missile Launch (`launch_missile` with `warhead: "nuclear"`)

```json
{
  "action_type": "launch_missile",
  "country_code": "sarmatia",
  "round_num": 5,
  "decision": "change",
  "rationale": "string >= 30 chars",
  "changes": {
    "warhead": "nuclear",
    "missiles": [
      {"missile_unit_code": "sar_m_01", "target_global_row": 3, "target_global_col": 3},
      {"missile_unit_code": "sar_m_02", "target_global_row": 3, "target_global_col": 3},
      {"missile_unit_code": "sar_m_03", "target_global_row": 6, "target_global_col": 15}
    ]
  }
}
```

| Field | Constraint |
|---|---|
| `warhead` | Must be `"nuclear"` |
| `missiles` | List of `{missile_unit_code, target_global_row, target_global_col}` |
| T1/T2 | Max 1 missile per decision |
| T3 | Any number of deployed missiles (salvo) |
| Range | T1: ≤2 hex, T2: ≤4 hex, T3: global |
| All missiles | Must be `strategic_missile`, status=`active` (deployed), owned by country |
| `nuclear_confirmed` | Must be `true` — cannot launch without confirmed tier |

### 2.3 `no_change` form — omit `changes`, just envelope + rationale.

---

## 3. PHASE 2 — 3-WAY AUTHORIZATION (10 min timer)

### 3.1 Who authorizes

| Country type | Authorizer 1 | Authorizer 2 |
|---|---|---|
| **Multi-role countries** | Military chief role | Senior official role |
| Columbia | `shield` (Sec of Defense) | `shadow` (CIA Director) |
| Cathay | `rampart` (Marshal) | `abacus` (senior official) |
| Sarmatia | `ironhand` (Chief of Staff) | `compass` (senior official) |
| Ruthenia | `bulwark` (Commander-in-Chief) | `broker` (Opposition Leader) |
| Persia | `anvil` (IRGC Commander) | `dawn` (senior official) |
| **Single-HoS countries** | **AI Officer** (one-off, created on demand) | — |

Single-HoS countries: HoS initiates + 1 AI Officer authorizes = 2-way.
Multi-role countries: HoS initiates + 2 named roles = 3-way.

### 3.2 Authorization request payload

Each authorizer receives:

```json
{
  "nuclear_action_id": "uuid",
  "action_type": "nuclear_test | launch_missile",
  "initiator": "pathfinder",
  "country_code": "sarmatia",
  "proposed_action": { ... full payload ... },
  "country_context": {
    "gdp": 85, "treasury": 20, "stability": 6,
    "nuclear_level": 3, "nuclear_confirmed": true,
    "at_war_with": ["columbia"],
    "recent_events_summary": "..."
  },
  "consequences_preview": {
    "stability_cost": -1.5,
    "gdp_cost": "target-dependent",
    "global_reaction": "global alert, all countries notified"
  },
  "instruction": "Do you CONFIRM this nuclear action? Respond YES or NO with rationale >= 30 chars."
}
```

### 3.3 Authorization response

```json
{
  "nuclear_action_id": "uuid",
  "role_id": "ironhand",
  "confirm": true,
  "rationale": "string >= 30 chars"
}
```

### 3.4 Rules

- **ANY rejection → action CANCELLED.** No partial authorization.
- **Timer expiry (10 min) without response → auto-CANCEL.**
- AI participants/officers are asked **immediately** (no mode distinction). Once all AI responses are in, the chain proceeds without waiting for the timer.
- Human participants have the full 10-minute window.
- If all authorizers are AI → chain proceeds instantly.

---

## 4. PHASE 3 — GLOBAL ALERT + INTERCEPTION DECISIONS (10 min timer)

### 4.1 Alert scoping

| Action | Who sees the alert |
|---|---|
| Underground test | **T3+ countries only** |
| Surface test | **ALL countries** |
| Nuclear launch | **ALL countries** |

Alert payload: `{action_type, launcher_country, target_hexes (for launch), missile_count}`.
Launcher identity IS revealed.

### 4.2 Interception decisions (LAUNCH only — not for tests)

Every T3+ country **(except the launcher)** receives an interception request:

```json
{
  "nuclear_action_id": "uuid",
  "launcher": "sarmatia",
  "targets": [{"row": 3, "col": 3}, {"row": 6, "col": 15}],
  "missile_count": 3,
  "your_ad_count": 4,
  "your_interception_probability_per_ad": 0.25,
  "political_context": "Intercepting reveals your capability and sides you against the launcher.",
  "instruction": "Do you attempt INTERCEPTION? Respond YES or NO with rationale >= 30 chars."
}
```

Response: `{country_code, intercept: bool, rationale}`.

### 4.3 Rules

- **Target country's own AD fires AUTOMATICALLY** (50% per unit, no decision needed).
- **Other T3+ countries:** voluntary decision (yes/no).
- **Timer expiry → auto-DECLINE** (does not intercept).
- AI decides immediately in all modes.
- **Launcher does NOT learn who intercepted.**

### 4.4 Tests skip interception

For `nuclear_test`, Phase 3 is alert-only (no missiles to intercept).
Chain proceeds directly to Phase 4.

---

## 5. PHASE 4 — ENGINE RESOLUTION

### 5.1 Nuclear Test Resolution

| Parameter | Underground | Surface |
|---|---|---|
| Success probability | Below T2: **70%**, T2+: **95%** | Same |
| On success | Tier CONFIRMED (`nuclear_confirmed = true`) | Same |
| On failure | No confirmation. Can retry next round. R&D progress NOT lost. | Same |
| Global stability | **-0.2** (all countries) | **-0.4** (all) + **-0.6** adjacent hex countries |
| Own GDP | — | **-5%** |
| Political support | **+5** (nationalist rally) | **+5** |

### 5.2 Nuclear Launch Resolution

**Per missile (in order):**

1. **T3+ interception** (T2/T3 launches only):
   - Target country own AD: **50%** per unit (automatic)
   - Each intercepting T3+ country: **25%** per AD unit they own
   - Each successful roll → 1 missile destroyed from salvo
   - T1 launches: local AD only (50% per unit, same as conventional)

2. **Hit roll** (surviving missiles): **80%** base

3. **Per hit:**
   - **50%** of all military units on target hex destroyed
   - **30% × (1 / target_country_hex_count)** of target GDP destroyed
   - Nuclear site on hex → auto-destroyed (100%)

4. **T3 salvo aggregate** (if ≥1 hit from a salvo of 3+ missiles):
   - Global stability: **-1.5**
   - Target country stability: **-2.5**
   - Leader death roll: **1/6** (logged as event, not mechanically resolved in unmanned mode)

### 5.3 `precomputed_rolls` hook

```json
{
  "test_success_roll": 0.55,
  "interception_rolls": {
    "columbia": [0.15, 0.88, 0.30, 0.92],
    "target_ad": [0.45, 0.60]
  },
  "hit_rolls": [0.12, 0.95, 0.40],
  "leader_death_roll": 0.85
}
```

---

## 6. STATE MACHINE — `nuclear_actions` TABLE

```sql
CREATE TABLE nuclear_actions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id uuid NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num integer NOT NULL,
    action_type text NOT NULL,         -- 'nuclear_test' | 'nuclear_launch'
    country_code text NOT NULL,
    initiator_role_id text NOT NULL,
    payload jsonb NOT NULL,
    status text NOT NULL DEFAULT 'awaiting_authorization',
    authorizer_1_role text,
    authorizer_1_response text,        -- 'confirm' | 'reject' | NULL
    authorizer_1_rationale text,
    authorizer_2_role text,
    authorizer_2_response text,
    authorizer_2_rationale text,
    interception_responses jsonb DEFAULT '{}',
    resolution jsonb,
    timer_started_at timestamptz,
    timer_duration_sec int DEFAULT 600,
    resolved_at timestamptz,
    created_at timestamptz DEFAULT now()
);
```

Status values: `awaiting_authorization → authorized | cancelled → awaiting_interception → resolved`

---

## 7. ORCHESTRATOR — `engine/orchestrators/nuclear_chain.py`

```python
class NuclearChainOrchestrator:
    def initiate(decision, sim_run_id) -> nuclear_action_id
    def request_authorization(action_id) -> list[auth_request]
    def submit_authorization(action_id, role_id, confirm, rationale) -> status_update
    def request_interceptions(action_id) -> list[intercept_request]
    def submit_interception(action_id, country_code, intercept, rationale) -> status_update
    def resolve(action_id) -> resolution_dict
    def run_unmanned(decision, sim_run_id) -> resolution_dict  # full chain, instant
```

---

## 8. AUTHORIZATION ROLE MAPPING

### Multi-role countries (3-way: HoS + 2 authorizers)

| Country | HoS (Initiator) | Auth 1 (Military) | Auth 2 (Senior) |
|---|---|---|---|
| Columbia | `dealer` | `shield` | `shadow` |
| Cathay | `helmsman` | `rampart` | `abacus` |
| Sarmatia | `pathfinder` | `ironhand` | `compass` |
| Ruthenia | `beacon` | `bulwark` | `broker` |
| Persia | `furnace` | `anvil` | `dawn` |

### Single-HoS countries (2-way: HoS + 1 AI Officer)

All others: Albion, Gallia, Teutonia, Freeland, Ponte, Formosa, Yamato,
Solaria, Bharata, Levantia, Phrygia, Choson, Hanguk, Caribe, Mirage.

If a named authorizer role is killed/removed during the SIM, they are
replaced by an AI Officer for that authorization only.

### AI Officer behavior

A one-off LLM call that receives the authorization/interception context
and responds confirm/reject. No persistent agent — created for the
single decision and discarded. Uses the same `call_llm` infrastructure
as other AI decisions.

---

## 9. NUCLEAR-CAPABLE COUNTRIES (Template v1.0 seed)

| Country | Level | Confirmed | Can initiate? |
|---|---|---|---|
| Columbia | T3 | ✅ yes | ✅ launch + test |
| Sarmatia | T3 | ✅ yes | ✅ launch + test |
| Cathay | T2 | ✅ yes | ✅ launch + test |
| Gallia | T2 | ✅ yes | ✅ launch + test |
| Albion | T2 | ✅ yes | ✅ launch + test |
| Bharata | T1 | ✅ yes | ✅ launch + test |
| Choson | T1 | ✅ yes | ✅ launch + test |
| Levantia | T1 | ✅ yes | ✅ launch + test |
| Others | T0 | — | ❌ (need R&D first) |

T3+ countries that can attempt interception: **Columbia, Sarmatia** (the only T3 in seed data).

---

## 10. PERSISTENCE

- `nuclear_actions` table: full state machine record per nuclear chain
- `country_states_per_round.nuclear_test_decision JSONB` / `nuclear_launch_decision JSONB` (audit)
- `observatory_combat_results` row(s): `combat_type='nuclear_test'` or `'nuclear_launch'`
- `observatory_events`: `event_type='nuclear_test_initiated'`, `'nuclear_authorized'`, `'nuclear_cancelled'`, `'nuclear_alert'`, `'nuclear_interception'`, `'nuclear_hit'`, `'nuclear_miss'`
- `country_states_per_round`: stability updates, GDP damage, `nuclear_confirmed` flip
- `unit_states_per_round`: destroyed missiles + destroyed military on target hex

---

## 11. LOCKED INVARIANTS

1. Nuclear is the ONLY multi-step chained decision in the SIM
2. Any single authorization rejection → entire action cancelled
3. Timer expiry → auto-cancel (auth) / auto-decline (interception)
4. AI participants/officers always asked immediately (no mode distinction)
5. Target country AD fires automatically (no decision)
6. Launcher does NOT learn who intercepted
7. T1 uses local AD (50%), T2/T3 uses T3+ voluntary interception (25%)
8. Hit probability: 80% (nuclear), vs 70% (conventional)
9. Missiles consumed on launch regardless of outcome
10. `precomputed_rolls` hook for all probability rolls
11. `nuclear_confirmed` must be `true` to launch nuclear warheads
12. Template-seeded countries are confirmed by default
