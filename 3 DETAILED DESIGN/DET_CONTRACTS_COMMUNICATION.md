# DET — Contracts & Communication Layer

**Version:** 1.0 | **Status:** Detailed Design | **Date:** 2026-04-13
**Sources:** `PHASES/UNMANNED_SPACECRAFT/CONTRACT_*.md` (27 locked contracts), `CARD_ARCHITECTURE.md`, `TRANSACTION_LOGIC.md`
**Related:** `DET_C1_SYSTEM_CONTRACTS.md` (event schemas), `DET_UNIT_MODEL_v1.md`, `DET_F5_ENGINE_API.md`

---

# PART A — TYPED CONTRACT LAYER

## 1. Purpose

All inter-module communication in the TTT codebase flows through **typed Pydantic contracts** — never ad-hoc dicts. Every action an agent or human submits, every engine result, every state mutation passes through a validate-then-normalize pipeline:

```
Raw payload (dict from LLM / UI / test)
  → Validator (pure function, returns {valid, errors, warnings, normalized})
    → Engine service (operates on normalized dict)
      → DB write (structured, auditable)
        → Observatory event (typed envelope)
```

This eliminates an entire class of bugs (typos in dict keys, missing fields, wrong types) and makes the system actor-agnostic: the same validator accepts input from a human UI, an AI agent, a test fixture, or a moderator override.

---

## 2. Architecture Principle: Engine State Isolation

**Invariant (locked 2026-04-08):** The engine tier (`round_tick.py`, `economic.py`, `political.py`, `military.py`, `technology.py`) NEVER reads from `agent_decisions`. It reads from **DB state tables** only.

```
CORRECT:
  Participant (human/AI) → agent_decisions
  resolve_round → reads agent_decisions → WRITES to state tables
  round_tick → reads state tables → runs engines → writes updated state

WRONG:
  round_tick → reads agent_decisions directly
```

Validators sit at every entry point between these layers:

| Boundary | Validator | Purpose |
|---|---|---|
| Agent/UI → resolve_round | `*_validator.py` (18 files) | Structural + authorization + asset checks |
| resolve_round → state tables | Engine service logic | Business rules, atomic execution |
| State tables → round_tick | Pydantic models | Type safety on engine inputs |
| Engine → Observatory | Event envelope (`DET_C1`) | Visibility, audit trail |

---

## 3. Contract Catalog (27 Locked Contracts)

All contracts live in `PHASES/UNMANNED_SPACECRAFT/CONTRACT_*.md`. Each is independently locked after Marat review. Together they specify every action a participant can take.

### 3.1 Mandatory Economic Decisions (4)

| Contract | Action | Scope |
|---|---|---|
| `CONTRACT_BUDGET` | `set_budget` | Social/military/tech allocation per round |
| `CONTRACT_TARIFFS` | `set_tariffs` | Bilateral tariff levels (0-4) |
| `CONTRACT_SANCTIONS` | `set_sanctions` | Bilateral sanction levels (0-4) |
| `CONTRACT_OPEC` | `set_opec_production` | OPEC members only: production quota |

### 3.2 Military Actions (7)

| Contract | Action(s) | Scope |
|---|---|---|
| `CONTRACT_MOVEMENT` | `move_unit`, `deploy_reserve`, `withdraw` | Unit positioning on global + theater grids |
| `CONTRACT_GROUND_COMBAT` | `attack_ground` | Unit-level ground combat with dice resolution |
| `CONTRACT_AIR_STRIKES` | `air_strike` | Tactical air vs ground/naval targets |
| `CONTRACT_NAVAL_COMBAT` | `naval_combat` | Fleet engagement in sea zones |
| `CONTRACT_NAVAL_BOMBARDMENT_BLOCKADE` | `naval_bombardment`, `declare_blockade`, `lift_blockade` | Shore bombardment + zone denial |
| `CONTRACT_NUCLEAR_CHAIN` | `nuclear_test`, `launch_nuclear` | Full nuclear chain: test, authorize, launch, intercept |
| `CONTRACT_MARTIAL_LAW` | `declare_martial_law` | One-off domestic troop boost |

### 3.3 Exchange & Diplomacy (3)

| Contract | Action(s) | Scope |
|---|---|---|
| `CONTRACT_TRANSACTIONS` | `propose_transaction`, `respond_to_transaction` | Coins, units, tech, basing rights exchange |
| `CONTRACT_AGREEMENTS` | `propose_agreement`, `sign_agreement` | Ceasefire, treaty, alliance, trade deal, custom |
| `CONTRACT_BASING_RIGHTS` | `basing_rights` (standalone) | Unilateral grant/revoke of basing access |

### 3.4 Covert Operations (4)

| Contract | Action | Scope |
|---|---|---|
| `CONTRACT_INTELLIGENCE` | `intelligence_operation` | Espionage: gather information on target country |
| `CONTRACT_SABOTAGE` | `sabotage_operation` | Infrastructure/military damage behind enemy lines |
| `CONTRACT_PROPAGANDA` | `propaganda_operation` | Stability/support manipulation in target country |
| `CONTRACT_ELECTION_MEDDLING` | `election_meddling` | Covert influence on foreign elections |

### 3.5 Domestic Political Actions (5)

| Contract | Action | Scope |
|---|---|---|
| `CONTRACT_ARREST` | `arrest_role` | HoS arrests a domestic official |
| `CONTRACT_ASSASSINATION` | `assassination` | Covert elimination of a foreign leader |
| `CONTRACT_COUP` | `coup` | Military overthrow of HoS |
| `CONTRACT_MASS_PROTEST` | `mass_protest` | Popular uprising (engine-triggered or moderator) |
| `CONTRACT_EARLY_ELECTIONS` | `call_early_elections` | HoS triggers snap election |

### 3.6 System & Governance (4)

| Contract | Action | Scope |
|---|---|---|
| `CONTRACT_ELECTIONS` | `process_election` | Scheduled election resolution (engine) |
| `CONTRACT_POWER_ASSIGNMENTS` | `reassign_powers` | HoS delegates military/economic/foreign powers |
| `CONTRACT_RUN_ROLES` | `seed_run_roles`, `update_role_status` | Per-run role lifecycle (active/arrested/killed/deposed) |
| `CONTRACT_ROUND_FLOW` | Round lifecycle | Phase A (free action) → Phase B (engine) → inter-round |

**Total: 27 locked contracts** covering all 32 consolidated actions plus system lifecycle.

---

## 4. Validator Catalog (18 Files)

All validators live in `app/engine/services/`. Each is a pure function returning `{valid, errors, warnings, normalized}`.

| Validator File | Contract(s) | Key Error Codes |
|---|---|---|
| `budget_validator.py` | Budget | `INVALID_PAYLOAD`, `RATIONALE_TOO_SHORT` |
| `tariff_validator.py` | Tariffs | `INVALID_PAYLOAD`, `RATIONALE_TOO_SHORT` |
| `sanction_validator.py` | Sanctions | `INVALID_PAYLOAD`, `RATIONALE_TOO_SHORT` |
| `opec_validator.py` | OPEC | `INVALID_PAYLOAD`, `RATIONALE_TOO_SHORT` |
| `movement_validator.py` | Movement | `INVALID_PAYLOAD` |
| `ground_combat_validator.py` | Ground combat | `INVALID_PAYLOAD` |
| `air_strike_validator.py` | Air strikes | `INVALID_PAYLOAD` |
| `naval_combat_validator.py` | Naval combat | `INVALID_PAYLOAD` |
| `bombardment_validator.py` | Bombardment/blockade | `INVALID_PAYLOAD` |
| `blockade_validator.py` | Blockade | `INVALID_PAYLOAD` |
| `missile_validator.py` | Missile launch | `INVALID_PAYLOAD` |
| `nuclear_validator.py` | Nuclear chain | `INVALID_PAYLOAD` |
| `transaction_validator.py` | Transactions | `INVALID_PAYLOAD`, `INVALID_SCOPE`, `INVALID_PROPOSER`, `INVALID_COUNTERPART`, `SELF_TRADE`, `INVALID_OFFER_REQUEST`, `UNKNOWN_ASSET_KEY`, `EMPTY_TRADE`, `PERSONAL_SCOPE_LIMIT`, `UNAUTHORIZED_ROLE`, `INSUFFICIENT_COINS`, `UNKNOWN_UNIT`, `NOT_OWN_UNIT`, `UNIT_DESTROYED` |
| `agreement_validator.py` | Agreements | `INVALID_PAYLOAD`, `INVALID_ACTION_TYPE`, `MISSING_NAME`, `INVALID_TYPE`, `INVALID_VISIBILITY`, `MISSING_TERMS`, `MISSING_SIGNATORIES`, `INVALID_SIGNATORY`, `PROPOSER_NOT_SIGNATORY`, `UNAUTHORIZED_ROLE` |
| `basing_rights_validator.py` | Basing rights | `INVALID_PAYLOAD`, `RATIONALE_TOO_SHORT`, `MISSING_CHANGES`, `UNEXPECTED_CHANGES` |
| `covert_ops_validator.py` | Intelligence, sabotage, propaganda, election meddling | `INVALID_PAYLOAD` |
| `political_validator.py` | Coup, mass protest, early elections | `INVALID_PAYLOAD`, `INVALID_ACTION_TYPE`, `RATIONALE_TOO_SHORT` |
| `domestic_validator.py` | Arrest, reassign powers | `INVALID_PAYLOAD`, `RATIONALE_TOO_SHORT`, `MISSING_ROLE`, `MISSING_TARGET` |

All validators share a common pattern:
1. Type check (`isinstance(payload, dict)`)
2. Structural checks (required fields, valid enums)
3. Authorization checks (role permissions, HoS status)
4. Asset/state checks (sufficiency, ownership)
5. Normalization (clean output dict for engine consumption)

---

## 5. Shared Helpers

**File:** `app/engine/services/common.py`

Eliminates duplication across all 18+ engine service modules.

| Helper | Signature | Purpose |
|---|---|---|
| `safe_int(val, default=0)` | `-> int` | Converts to int, treating only `None` as missing (not 0). Prevents the 0-is-falsy bug. |
| `safe_float(val, default=0.0)` | `-> float` | Same pattern for floats. |
| `get_scenario_id(client, sim_run_id)` | `-> str | None` | Looks up `scenario_id` from `sim_runs` table. Used by all services that write Observatory events. |
| `write_event(client, sim_run_id, scenario_id, round_num, country_code, event_type, summary, payload)` | `-> None` | Writes a structured event to `observatory_events`. Silently skips if no `scenario_id`. |

---

# PART B — EXCHANGE TRANSACTIONS

## 6. Transaction Flow

Exchange transactions are the economic backbone of the SIM. Any authorized participant (human, AI, or moderator) can propose a deal to any other participant at any time during a round. Deals execute instantly and atomically once both sides confirm.

```
A proposes  -->  B accepts   -->  VALIDATE BOTH --> EXECUTE (instant, atomic)
                 B declines  -->  CLOSED
                 B counters  -->  A accepts  -->  VALIDATE BOTH --> EXECUTE
                                  A declines -->  CLOSED
```

**Key rules:**
- Available ANY TIME during rounds -- no transaction phase
- Both sides must explicitly confirm -- no assumed acceptance
- Proposals do not expire in unmanned mode (no timers)
- The chain is participant-driven: each step happens when the participant decides

**Status lifecycle:**
```
pending --> accepted --> executed
pending --> declined
pending --> countered --> accepted --> executed
pending --> countered --> declined
pending --> expired (timer, human mode only)
accepted --> failed_validation (assets changed between accept and execute)
```

---

## 7. Asset Types

Four tradeable asset types, each with distinct transfer semantics:

| Asset | Transfer Mode | Reversible | Validation |
|---|---|---|---|
| **Coins** (treasury) | Exclusive: sender loses, receiver gains | No | Sender treasury >= amount |
| **Coins** (personal) | Exclusive: sender loses, receiver gains | No | Sender `personal_coins` >= amount |
| **Military units** | Exclusive: sender loses, receiver gains | No | Unit exists, belongs to sender, not destroyed |
| **Technology** | Replicable: sender keeps, receiver gains | No | Donor must be >= 1 level ahead |
| **Basing rights** | Replicable: host keeps sovereignty | **Yes** (revocable) | None at trade time |

**Technology transfer values** (per `CARD_FORMULAS` C.4):
- Nuclear R&D share: receiver gets **+0.20** `nuclear_rd_progress`
- AI R&D share: receiver gets **+0.15** `ai_rd_progress`

**NOT tradeable:** covert op cards, territory (use agreements), promises (use agreements).

**Combinations are valid.** A single transaction can include coins + units + tech + basing in any mix.

---

## 8. Dual Scope

Two modes of trading serve fundamentally different purposes:

### 8.1 Country Scope

Authorized officials trade **country assets** on behalf of their nation.

| Asset | Source | Written to |
|---|---|---|
| Coins | `country_states_per_round.treasury` | Same table, both countries |
| Units | `unit_states_per_round` (ownership) | Ownership flips, status -> reserve, coords cleared |
| Technology | `country_states_per_round.*_rd_progress` | Receiver's progress incremented |
| Basing rights | `basing_rights` table | New row or reactivated |

### 8.2 Personal Scope

**Any individual** trades their personal coins. No authorization needed -- it is their money.

| Asset | Source | Written to |
|---|---|---|
| Personal coins | `run_roles.personal_coins` | Same table, both roles |

**Hard constraint:** Personal scope can ONLY trade coins. Attempting to include units, technology, or basing rights in a personal-scope transaction triggers `PERSONAL_SCOPE_LIMIT` error.

---

## 9. Validation

### 9.1 Proposal Validation (proposer side only)

Performed by `transaction_validator.validate_proposal()`. Checks ONLY the proposer's side.

| Code | Rule |
|---|---|
| `INVALID_SCOPE` | scope must be `"country"` or `"personal"` |
| `INVALID_PROPOSER` | proposer country must be a valid canonical country |
| `INVALID_COUNTERPART` | counterpart country must be a valid canonical country |
| `SELF_TRADE` | cannot trade with yourself (same role + same country in country scope) |
| `INVALID_OFFER_REQUEST` | offer and request must be dicts |
| `UNKNOWN_ASSET_KEY` | only `coins`, `units`, `technology`, `basing_rights` allowed |
| `EMPTY_TRADE` | both offer and request are empty |
| `PERSONAL_SCOPE_LIMIT` | personal scope can only trade coins |
| `UNAUTHORIZED_ROLE` | role lacks permission for the asset types offered |
| `INSUFFICIENT_COINS` | offered coins exceed available treasury or personal wallet |
| `UNKNOWN_UNIT` | offered unit_code does not exist |
| `NOT_OWN_UNIT` | unit belongs to a different country |
| `UNIT_DESTROYED` | unit status is `'destroyed'` |

**Critical design decision:** The REQUEST side is NOT validated at proposal time. The counterpart's assets are not checked until execution. This prevents using proposals to probe what the other side has.

### 9.2 Execution Validation (both sides)

Performed by `transaction_validator.validate_execution()`. Called only after both parties confirmed.

- Proposer STILL has offered assets? (may have changed since proposal)
- Counterpart HAS the requested assets?
- If either fails: deal fails, both notified, status = `failed_validation`

Additional error codes at execution: `PROPOSER_INSUFFICIENT_COINS`, `PROPOSER_UNKNOWN_UNIT`, `PROPOSER_NOT_OWN_UNIT`, `PROPOSER_UNIT_DESTROYED`, `COUNTERPART_INSUFFICIENT_COINS`, `COUNTERPART_UNKNOWN_UNIT`, `COUNTERPART_NOT_OWN_UNIT`, `COUNTERPART_UNIT_DESTROYED`.

### 9.3 Role Authorization

| Role Type | Can Trade (country scope) |
|---|---|
| **HoS** | Everything: coins, units, tech, basing |
| **Military chief** | Units only |
| **FM / diplomat** | Coins + basing rights |
| **Tycoon / businessman** | Personal coins only (personal scope) |
| **Any role** | Personal coins (personal scope) |

Authorization is looked up from `run_roles`: `is_head_of_state`, `is_military_chief`, `powers` field.

---

## 10. Counter-Offer

**One iteration maximum.** The counter-offer mechanic prevents deadlock without infinite negotiation loops.

```
A proposes (offer + request)
  --> B responds with "counter" + counter_offer + counter_request
    --> A sees counter-terms, responds: ACCEPT or DECLINE
      --> No further iterations -- deal closes either way
```

A fresh proposal can always be started after a closed counter-offer.

Counter-offer schema:
```json
{
  "transaction_id": "uuid",
  "response": "counter",
  "counter_offer": { "coins": 3 },
  "counter_request": { "coins": 0, "units": ["col_g_05"], "basing_rights": true },
  "rationale": "I want fewer units and more basing rights"
}
```

---

# PART C — AGREEMENTS

## 11. Agreement Types

Agreements are **written commitments** between countries. Unlike exchange transactions (which move assets), agreements are promises recorded in the system. They rely on trust, reputation, and consequences -- NOT engine enforcement.

### 11.1 Pre-defined Types

| Type | Description |
|---|---|
| `armistice` | Combat stops, territory frozen at current lines. Temporary. |
| `peace_treaty` | War formally ended. Permanent. |
| `trade_agreement` | Participants expected to adjust tariffs. |
| `military_alliance` | Coordination commitment. |
| `mutual_defense` | "Attack on one = attack on all" pledge. |
| `arms_control` | Nuclear/missile limits (e.g., freeze at T1). |
| `non_aggression` | "We won't attack each other." |
| `sanctions_coordination` | "We both sanction X at level Y." |
| `organization_creation` | Creates new organization: name + members + purpose. |
| *(custom)* | Any free-text type. Recorded as-is. |

Pre-defined types are **suggestions**, not constraints. Any free-text type is accepted by the validator.

### 11.2 Agreement Flow

```
A drafts agreement (name, type, terms, signatories, visibility)
  --> A sends to all signatories
    --> Each signatory: CONFIRM (sign) or DECLINE (with comments)
      --> ALL confirm --> agreement ACTIVE
      --> ANY decline --> initiator can revise and re-send (new proposal)
```

**No counter-offer mechanic** for agreements (unlike transactions). A signatory either signs or declines. The initiator revises and creates a new proposal if needed.

### 11.3 Validation

| Code | Rule |
|---|---|
| `INVALID_PAYLOAD` | Must be dict |
| `INVALID_ACTION_TYPE` | Must be `propose_agreement` |
| `MISSING_NAME` | `agreement_name` required |
| `INVALID_TYPE` | `agreement_type` required (any string accepted) |
| `INVALID_VISIBILITY` | Must be `public` or `secret` |
| `MISSING_TERMS` | `terms` required (non-empty string) |
| `MISSING_SIGNATORIES` | At least 2 signatories |
| `INVALID_SIGNATORY` | Each signatory must be a valid country_code |
| `PROPOSER_NOT_SIGNATORY` | Proposer's country must be in signatories list |
| `UNAUTHORIZED_ROLE` | Proposer must be HoS, FM, or diplomat |

---

## 12. Signatory Tracking

Signatures are stored as a JSONB field on the `agreements` table:

```json
{
  "columbia": {
    "confirmed": true,
    "role_id": "dealer",
    "comments": "Columbia agrees to the terms",
    "signed_at": "2026-04-15T14:23:07Z"
  },
  "sarmatia": {
    "confirmed": true,
    "role_id": "pathfinder",
    "comments": "Sarmatia agrees",
    "signed_at": "2026-04-15T14:25:12Z"
  }
}
```

**Activation rule:** When ALL signatories have `confirmed: true`, the agreement status transitions from `proposed` to `active`. Any single `confirmed: false` means the agreement is not activated.

Each signatory's response is tracked independently with:
- `confirmed` (bool): signed or declined
- `role_id`: which role signed on behalf of the country
- `comments`: free text (visible to initiator, especially useful on decline)
- `signed_at`: timestamp of the signature

---

## 13. No Enforcement Principle

**Per Marat's explicit direction (locked 2026-04-08):** No engine enforcement of any agreement type.

All agreements are just **saved in the DB**. The system records them faithfully. No special enforcement, no automatic consequences for breach. Countries have full sovereignty and freedom of action.

Concrete implications:

| Agreement | What the engine does | What the engine does NOT do |
|---|---|---|
| Armistice | Records it. Updates `relationships.status` to `armistice`. | Does NOT block subsequent attack orders. |
| Peace treaty | Records it. Updates `relationships.status` to `peace`. | Does NOT prevent re-declaration of war. |
| Military alliance | Records it. | Does NOT auto-join allies in combat. |
| Trade agreement | Records it. | Does NOT enforce tariff levels. |
| Non-aggression | Records it. | Does NOT block hostile actions. |
| All others | Records it. | Nothing else. |

**A country can sign a peace treaty and attack the same round.** The SIM models real geopolitics: agreements are political instruments, not physical constraints. Breach has reputational consequences (other leaders remember), not mechanical ones.

The `Observatory` and `AI Participant Module` can READ agreements to inform decisions, but the engine NEVER uses them to constrain actions.

---

## 14. Visibility

| Level | Who Sees | Use Case |
|---|---|---|
| `public` | All countries, all roles, Observatory | Open diplomacy: treaties, alliances, declarations |
| `secret` | Signatories only | Back-channel deals, hidden alliances |

Secret agreements can be revealed later:
- Voluntarily by a signatory (public statement)
- Via intelligence operation (covert ops)
- By moderator override

**Implementation note:** Visibility is a flag on the DB row, not access control at the query layer. The data always exists -- the Context Assembly Service filters it based on the requesting role's visibility scope.

---

# PART D — SUPPORTING SYSTEMS

## 15. Basing Rights

Basing rights allow a guest country to deploy military units on the host country's territory.

### 15.1 Dual Entry Points

Two paths produce the same DB state:
- **Standalone action** (`basing_rights`): host grants/revokes directly, unilateral
- **Transaction** (`propose_transaction`): basing rights as part of a deal

Both route through `basing_rights_engine.py` -- single source of truth.

### 15.2 Grant

- Unilateral by host. No guest confirmation needed.
- Upserts `basing_rights` row: `(sim_run_id, host, guest)` with `status=active`
- If previously revoked, reactivates the same row (upsert)
- Events: host notified "granted", guest notified "received"

### 15.3 Revoke

- Unilateral by host.
- **BLOCKED if guest has active units on host territory.** Guest must withdraw first.
- Updates row: `status=revoked`, `revoked_round` set
- Events: host notified "revoked", guest notified "lost -- must withdraw"

### 15.4 Validation

| Code | Rule |
|---|---|
| `INVALID_PAYLOAD` | Standard structural check |
| `RATIONALE_TOO_SHORT` | Rationale must be >= 30 chars |
| `MISSING_CHANGES` | Changes object required |
| `UNEXPECTED_CHANGES` | Only `counterpart_country` and `action` allowed |
| `INVALID_GUEST` | Guest must be a valid country |
| `SELF_BASING` | Cannot grant to yourself |
| `INVALID_ACTION` | Must be `grant` or `revoke` |
| `GUEST_FORCES_PRESENT` | Cannot revoke if guest has active units on host territory |

### 15.5 Starting Basing Rights (Template v1.0)

12 pre-seeded records at sim_run start:
- Columbia hosted in: Yamato, Hanguk, Teutonia, Albion, Phrygia, Formosa, Mirage, Ponte, Freeland (9)
- Sarmatia-Choson mutual (2)
- Gallia in Mirage (1)

---

## 16. Power Assignments

Power assignments are the **authorization backbone** of the SIM. They determine which role can act on behalf of a country for three categories of actions.

### 16.1 Three Power Categories

| Power | Authorizes |
|---|---|
| **Military** | `move_units`, `attack_*`, `blockade`, `launch_missile`, `martial_law`, `basing_rights` |
| **Economic** | `set_budget`, `set_tariffs`, `set_sanctions`, `set_opec`, `propose_transaction` (country assets) |
| **Foreign Affairs** | `propose_agreement`, `propose_transaction` (deals), sign agreements |

### 16.2 HoS Implicit Rule

HoS is ALWAYS authorized for everything. Not stored in the `power_assignments` table. The authorization check function handles this:

```
check_authorization(role_id, action_type, sim_run_id, country_code):
  1. Action is unrestricted (public_statement, covert ops) --> authorized
  2. Role is HoS of the country --> authorized (always)
  3. Action maps to a power_type --> look up power_assignments table
  4. Role matches the assigned role --> authorized
  5. Slot is vacant (NULL) --> only HoS can act --> unauthorized
  6. Different role assigned --> unauthorized (error says who holds it)
```

### 16.3 Reassignment

Only HoS can reassign powers. Immediate and public. Both old and new holder notified.

Setting `new_role` to `null` vacates the slot -- HoS takes back the responsibility.

### 16.4 Canonical Starting Assignments (Template v1.0)

| Country | Military | Economic | Foreign Affairs |
|---|---|---|---|
| **Columbia** | `shield` | `volt` | `anchor` |
| **Cathay** | `rampart` | `abacus` | `sage` |
| **Sarmatia** | `ironhand` | `compass` | `compass` |
| **Ruthenia** | `bulwark` | `broker` | *(vacant -- HoS)* |
| **Persia** | `anvil` | *(vacant -- HoS)* | `dawn` |

Single-HoS countries (all others): HoS holds all three powers. No entries in the table.

---

## 17. Run Roles

Per-run mutable clones of template roles. Follows the KING pattern: template data is frozen, per-run copies are mutable.

### 17.1 Seed

`seed_run_roles(sim_run_id)` clones all 40 template roles into `run_roles` with `status='active'` and starting `personal_coins` from the template.

### 17.2 Status Lifecycle

```
active --> arrested    (by HoS or authorized role)
arrested --> active    (auto at round end, or by moderator)
active --> killed      (assassination success)
active --> deposed     (coup success)
active --> inactive    (fired -- powers reassigned, person stays in game)
```

### 17.3 Query/Mutate API

| Function | Purpose |
|---|---|
| `get_run_role(sim_run_id, role_id)` | Single role lookup |
| `get_run_roles(sim_run_id, country_code?, status?)` | Filtered list |
| `update_role_status(sim_run_id, role_id, new_status, by, reason, round)` | Status transition |
| `update_personal_coins(sim_run_id, role_id, delta)` | Coin balance change |

### 17.4 Cross-System Dependencies

| System | How It Uses run_roles |
|---|---|
| Power assignments | `check_authorization()` reads `is_head_of_state` flag |
| Transactions | Personal coin balance from `run_roles.personal_coins` |
| Arrest engine | Sets `status='arrested'` on target role |
| Assassination engine | Sets `status='killed'` on success |
| Coup engine | Sets `status='deposed'` on HoS if coup succeeds |
| Nuclear chain | Reads `run_roles` to find authorizer roles per country |
| AI Participant Module | Reads `run_roles` to know which character the agent plays |

---

## 18. DB Tables

### 18.1 `exchange_transactions`

```sql
exchange_transactions (
  id uuid PK,
  sim_run_id uuid FK --> sim_runs,
  round_num int,
  proposer_role_id text,
  proposer_country_code text,
  scope text,                    -- 'country' | 'personal'
  counterpart_role_id text,
  counterpart_country_code text,
  offer jsonb,                   -- {coins, units, technology, basing_rights}
  request jsonb,                 -- same structure
  status text,                   -- pending|accepted|declined|countered|executed|failed_validation|expired
  counter_offer jsonb,
  counter_request jsonb,
  proposer_rationale text,
  counterpart_rationale text,
  executed_at timestamptz,
  created_at timestamptz
)
```

### 18.2 `agreements`

```sql
agreements (
  id uuid PK,
  sim_run_id uuid FK --> sim_runs,
  round_num int,
  agreement_name text,
  agreement_type text,
  visibility text,               -- 'public' | 'secret'
  terms text,
  signatories text[],            -- list of country codes
  proposer_country_code text,
  proposer_role_id text,
  signatures jsonb,              -- {country: {confirmed, role_id, comments, signed_at}}
  status text,                   -- proposed|active|declined
  created_at timestamptz
)
```

### 18.3 `basing_rights`

```sql
basing_rights (
  id uuid PK,
  sim_run_id uuid FK --> sim_runs,
  host_country text,
  guest_country text,
  granted_by_role text,
  granted_round int,
  status text,                   -- 'active' | 'revoked'
  revoked_round int,
  source text,                   -- 'direct' | 'transaction' | 'template'
  created_at timestamptz,
  UNIQUE (sim_run_id, host_country, guest_country)
)
```

### 18.4 `power_assignments`

```sql
power_assignments (
  id uuid PK,
  sim_run_id uuid FK --> sim_runs,
  country_code text,
  power_type text,               -- 'military' | 'economic' | 'foreign_affairs'
  assigned_role_id text,         -- nullable: NULL = vacant (HoS holds)
  assigned_by_role text,
  assigned_round int,
  created_at timestamptz,
  UNIQUE (sim_run_id, country_code, power_type)
)
```

### 18.5 `run_roles`

```sql
run_roles (
  id uuid PK,
  sim_run_id uuid FK --> sim_runs,
  role_id text,                  -- references template roles.id
  country_code text,
  character_name text,
  title text,
  is_head_of_state boolean,
  is_military_chief boolean,
  is_diplomat boolean,
  status text,                   -- active|arrested|killed|deposed|inactive
  personal_coins integer,
  powers text,
  status_changed_round int,
  status_changed_by text,
  status_change_reason text,
  created_at timestamptz,
  UNIQUE (sim_run_id, role_id)
)
```

---

# PART E — CROSS-REFERENCES

## Source Contracts (PHASES/UNMANNED_SPACECRAFT/)

| Document | Sections in this DET |
|---|---|
| `CONTRACT_TRANSACTIONS.md` | 6, 7, 8, 9, 10, 18.1 |
| `CONTRACT_AGREEMENTS.md` | 11, 12, 13, 14, 18.2 |
| `CONTRACT_BASING_RIGHTS.md` | 15, 18.3 |
| `CONTRACT_POWER_ASSIGNMENTS.md` | 16, 18.4 |
| `CONTRACT_RUN_ROLES.md` | 17, 18.5 |
| `TRANSACTION_LOGIC.md` | 6, 7, 8, 9, 10, 11, 13 |
| `CARD_ARCHITECTURE.md` | 2, 3 (module map, state isolation) |

## Related DET Documents

| Document | Relationship |
|---|---|
| `DET_C1_SYSTEM_CONTRACTS.md` | Event envelope schema, visibility rules, relationship status model |
| `DET_UNIT_MODEL_v1.md` | Unit entity contract (traded units reference this schema) |
| `DET_F5_ENGINE_API.md` | Engine API -- how orchestrator calls engines |
| `DET_ROUND_WORKFLOW.md` | Round flow -- when transactions and agreements are processed |

## Implementation Files

| File | Role |
|---|---|
| `app/engine/services/transaction_validator.py` | Proposal + execution validation |
| `app/engine/services/transaction_engine.py` | Propose, respond, execute transaction |
| `app/engine/services/agreement_validator.py` | Agreement proposal validation |
| `app/engine/services/agreement_engine.py` | Propose, sign, activate agreement |
| `app/engine/services/basing_rights_validator.py` | Basing action validation |
| `app/engine/services/basing_rights_engine.py` | Grant/revoke basing rights |
| `app/engine/services/domestic_validator.py` | Arrest, reassign powers validation |
| `app/engine/services/political_validator.py` | Coup, protest, elections validation |
| `app/engine/services/common.py` | Shared helpers: safe_int, safe_float, get_scenario_id, write_event |

## Locked Invariants (consolidated)

1. All modules communicate via typed Pydantic contracts, never ad-hoc dicts
2. Engine tier NEVER reads `agent_decisions` -- only DB state tables
3. Validators at every entry point between layers
4. Both sides must explicitly confirm transactions -- no assumed acceptance
5. Execution is atomic -- all transfers succeed or all fail
6. One counter-offer maximum per transaction proposal
7. No engine enforcement of any agreement type -- full sovereignty
8. Basing rights are the ONLY reversible asset transfer
9. HoS is always authorized (implicit, not stored)
10. Run roles are mutable clones -- template roles are NEVER modified during a run
11. Transaction system is actor-agnostic: same API for human, AI, moderator

---

*End of document. Version 1.0, 2026-04-13.*
