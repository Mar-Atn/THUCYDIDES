# DET_EDGE_FUNCTIONS.md
## Supabase Edge Function Specification
**Version:** 1.0 | **Date:** 2026-03-30 | **Status:** DRAFT
**Owner:** NOVA (Backend)
**Cross-references:** [C3 API Spec](DET_C3_API_SPEC.yaml) | [F5 Engine API](DET_F5_ENGINE_API.md) | [Naming Conventions](DET_NAMING_CONVENTIONS.md) | [B1 Database Schema](DET_B1_DATABASE_SCHEMA.sql)

---

# PURPOSE

Edge Functions are the middleware layer between the participant-facing REST API (C3) and the Python engine server (F5). They are Supabase Edge Functions written in Deno/TypeScript, deployed on Supabase infrastructure.

This document specifies the Edge Function layer that was identified as a gap in DET_VALIDATION_LEVEL1 (Check 3) and DET_VALIDATION_LEVEL3 (Cross-Trace Issue X-3).

---

# 1. ARCHITECTURE

```
Browser (React)
    |
    | HTTPS + Supabase JWT
    v
Supabase Edge Function (Deno/TypeScript)
    |
    |--- JWT Validation (Supabase Auth)
    |--- Permission Check (calls DB function check_authorization)
    |--- Request Translation (C3 format -> F5 format)
    |--- Forward to Engine (HMAC-signed internal request)
    |--- Response Translation (F5 format -> C3 format)
    |--- Event Publishing (Supabase Realtime channels)
    |
    v
Engine Server (FastAPI on Railway)    OR    Supabase PostgreSQL (direct write)
```

---

# 2. EDGE FUNCTION INVENTORY

| # | Function Name | C3 Endpoint(s) | Routes To | Description |
|---|--------------|----------------|-----------|-------------|
| 1 | `submit-actions` | `POST /actions/{round_num}/{country_id}` | F5 + DB | Decomposes batch submission into individual engine calls |
| 2 | `submit-deployment` | `POST /deploy/{round_num}/{country_id}` | DB (via `deployment_validation()`) | Validates and writes deployments directly |
| 3 | `propose-transaction` | `POST /transactions` | F5 `POST /engine/transaction` | Translates C3 proposal to F5 format |
| 4 | `confirm-transaction` | `POST /transactions/{id}/confirm` | F5 `POST /engine/transaction/{id}/confirm` | Forwards confirmation |
| 5 | `trigger-engine` | `POST /moderator/engine/trigger` | F5 `POST /engine/round/process` | Collects actions from DB, assembles payload, forwards |
| 6 | `publish-results` | `POST /moderator/engine/publish` | F5 `POST /engine/round/publish` + DB | Publishes and broadcasts |
| 7 | `advance-round` | `POST /moderator/round/advance` | DB (`process_round_end()`) | Phase transitions |
| 8 | `moderator-override` | `POST /moderator/override` | DB | Direct state modification |
| 9 | `ai-deliberate` | `POST /ai/decision/{role_id}` | F5 `POST /engine/ai/deliberate` | AI participant decision |
| 10 | `ai-argus` | `POST /ai/argus` | F5 `POST /engine/ai/argus` | Argus conversation |
| 11 | `read-state` | `GET /state/{round_num}/{country_id}` | DB | Reads and filters state |
| 12 | `read-map` | `GET /map/{round_num}` | DB | Reads and filters map |
| 13 | `read-events` | `GET /events/{round_num}` | DB | Reads events with visibility filter |

---

# 3. COMMON MIDDLEWARE (shared by all Edge Functions)

## 3.1 JWT Validation

```typescript
async function validateJWT(req: Request): Promise<UserClaims> {
  const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    global: { headers: { Authorization: req.headers.get('Authorization')! } }
  })
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error || !user) throw new AuthError('AUTH_INVALID_TOKEN')

  return {
    user_id: user.id,
    sim_run_id: user.app_metadata.sim_run_id,
    role_id: user.app_metadata.role_id,
    country_id: user.app_metadata.country_id,
    access_level: user.app_metadata.access_level,
    permissions: user.app_metadata.permissions || [],
  }
}
```

## 3.2 Permission Checking

Two levels of permission checking:

**Level 1 -- JWT claim check (fast, in-memory):**
```typescript
function checkPermission(claims: UserClaims, action_type: string): boolean {
  if (claims.access_level === 'moderator' || claims.access_level === 'admin') return true
  return claims.permissions.includes(action_type)
}
```

**Level 2 -- Database authorization check (for critical actions):**
```typescript
async function checkDBAuthorization(
  supabase: SupabaseClient,
  sim_run_id: string,
  role_id: string,
  action_type: string
): Promise<boolean> {
  const { data } = await supabase.rpc('check_authorization', {
    p_sim_run_id: sim_run_id,
    p_role_id: role_id,
    p_action_type: action_type,
  })
  return data === true
}
```

Level 2 is used for: military actions, nuclear authorization, budget submission, transactions.

## 3.3 Engine Forwarding

```typescript
async function forwardToEngine(path: string, body: object): Promise<EngineResponse> {
  const bodyStr = JSON.stringify(body)
  const timestamp = Math.floor(Date.now() / 1000).toString()
  const signature = await hmacSign(ENGINE_AUTH_SECRET, bodyStr + timestamp)

  const response = await fetch(`${ENGINE_URL}/api/v1${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Engine-Auth': signature,
      'X-Engine-Timestamp': timestamp,
      'X-Request-Id': crypto.randomUUID(),
    },
    body: bodyStr,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new EngineError(error.error.code, error.error.message, response.status)
  }

  return await response.json()
}
```

## 3.4 Rate Limiting

Rate limits enforced per role_id using Supabase Edge Function's built-in rate limiter or a Redis-backed counter.

| Endpoint Group | Limit | Window |
|---------------|-------|--------|
| State reads | 60/min | Per role |
| Action submissions | 10/min | Per role |
| Transaction proposals | 20/min | Per role |
| AI requests | 30/min | Per role |
| Moderator endpoints | 120/min | Per user |

## 3.5 Error Handling

All Edge Functions return errors in the C3 Error schema:

```json
{
  "error": {
    "code": "AUTH_ROLE_MISMATCH",
    "message": "Role does not have permission for ground_attack",
    "details": { "role_id": "senator_1", "required_power": "authorize_attack" },
    "timestamp": "2026-04-15T14:23:07Z",
    "request_id": "req_abc123"
  }
}
```

Engine errors are translated to C3 error format. F5 error codes pass through directly (they use the same vocabulary from F4 API Contracts Section 1.3).

---

# 4. KEY EDGE FUNCTION SPECIFICATIONS

## 4.1 submit-actions (Batch Decomposition)

This is the most complex Edge Function. C3 sends a batch `ActionSubmission` with multiple action types. F5 processes one action at a time.

**Decomposition logic:**

```
ActionSubmission {
  budget: BudgetAction         -> DB function submit_budget()
  tariffs: TariffAction[]      -> Stored in DB (applied at round processing)
  sanctions: SanctionAction[]  -> Stored in DB (applied at round processing)
  military: MilitaryAction[]   -> Each -> F5 POST /engine/action
  diplomatic: DiplomaticAction[] -> Each -> Direct DB event write (no engine)
  political: PoliticalAction[]   -> Each -> F5 POST /engine/action
  covert: CovertAction[]         -> Each -> F5 POST /engine/action
}
```

**Processing order:**
1. Validate JWT + permissions for each action type in the batch
2. Budget -> call `submit_budget()` DB function
3. Tariffs/Sanctions -> write to DB tables directly (validated at write)
4. Military actions -> forward each to F5 sequentially (combat order matters)
5. Political actions (arrest, fire, impeachment, etc.) -> forward each to F5
6. Covert actions -> forward each to F5
7. Diplomatic actions (public_statement, meeting_call, election_nominate) -> write events directly to DB
8. Aggregate all results and events
9. Publish events to appropriate Realtime channels
10. Return aggregate response

**Field translation (C3 -> F5):**

| C3 Field | F5 Field | Notes |
|----------|----------|-------|
| `actions.military[].action_type: "attack"` | `action_type: "ground_attack"` | Canonical name expansion |
| `actions.military[].action_type: "blockade"` | `action_type: "blockade"` | No change |
| (batch container) | `sim_run_id` | Added from JWT claims |
| (batch container) | `round_num` | Added from path parameter |
| (batch container) | `actor_role_id` | Added from JWT claims |
| (batch container) | `actor_country_id` | Added from JWT claims |

## 4.2 submit-deployment (Validation + Direct Write)

Deployment does NOT route through the F5 Python engine. The Edge Function validates using the `deployment_validation()` database function and writes directly to the `deployments` table.

**Validation steps:**
1. JWT validation + permission check (`deploy_forces` power)
2. Phase check: must be Phase B
3. Call `deployment_validation()` DB function:
   - Zone territory access check (no adjacency requirement for deployment) (via `zone_adjacency` table)
   - Transit time calculation (domestic = 0, cross-theater = 1 round)
   - Unit availability check (units in `from_zone` >= requested count)
   - Basing rights check (if deploying to foreign zone, requires active basing_rights)
4. Write deployment changes to `deployments` table
5. Log `action.troop_deployment` event
6. Publish state update to country channel

## 4.3 propose-transaction (Field Translation)

**C3 -> F5 field mapping:**

| C3 `TransactionProposal` | F5 `/engine/transaction` | Transform |
|--------------------------|-------------------------|-----------|
| `transaction_type` | `transaction_type` | Use canonical name (see DET_NAMING_CONVENTIONS 1.2) |
| `proposer` (role_id string) | `proposer_role_id` | Rename |
| `counterparty` (role_id string) | `receiver_role_id` | Rename |
| (from JWT) | `proposer_country_id` | Added |
| (lookup from counterparty role) | `receiver_country_id` | Looked up from DB |
| `details` | `terms` | Rename top-level key |
| `details.from_country` | `terms.from_country` | Pass through |
| `details.to_country` | `terms.to_country` | Pass through |
| `details.amount` | `terms.amount` | Pass through |
| `idempotency_key` | `idempotency_key` | Pass through |

## 4.4 trigger-engine (Data Assembly)

The most critical facilitator operation. Assembles the complete round data from the database and forwards to the engine.

**Data assembly steps:**
1. Read all submitted budgets from `country_state.budget` for current round
2. Read all tariff changes from `tariffs` table
3. Read all sanction changes from `sanctions` table
4. Read all OPEC production decisions from `country_state.opec_production`
5. Read all Phase A events from `events` table
6. Assemble into F5 `country_actions` structure (one object per country)
7. For countries that did not submit actions, use previous round's settings
8. Forward assembled payload to F5 `POST /engine/round/process`
9. Return engine response to facilitator for review

## 4.5 Event Publishing (Post-Response)

After every state-modifying Edge Function receives a response, it publishes events to appropriate Realtime channels:

```typescript
async function publishEvents(supabase: SupabaseClient, events: EngineEvent[]) {
  for (const event of events) {
    // Determine channels based on visibility
    const channels = getChannelsForEvent(event)

    for (const channel of channels) {
      await supabase.channel(channel).send({
        type: 'broadcast',
        event: event.event_type.split('.')[0], // category
        payload: event,
      })
    }
  }
}

function getChannelsForEvent(event: EngineEvent): string[] {
  const sim = event.sim_run_id
  const channels: string[] = []

  switch (event.visibility) {
    case 'public':
      channels.push(`sim:${sim}:world`)
      // Also push to specific country channels if country-relevant
      if (event.actor_country_id && event.actor_country_id !== 'global') {
        channels.push(`sim:${sim}:country:${event.actor_country_id}`)
      }
      break
    case 'country':
      channels.push(`sim:${sim}:country:${event.actor_country_id}`)
      break
    case 'role':
      channels.push(`sim:${sim}:role:${event.actor_role_id}`)
      break
    case 'moderator':
      channels.push(`sim:${sim}:facilitator`)
      break
  }

  // Always push to facilitator channel
  channels.push(`sim:${sim}:facilitator`)

  // Check for alert-worthy events
  if (isAlertWorthy(event)) {
    channels.push(`sim:${sim}:alerts`)
  }

  return channels
}
```

**Alert-worthy events:** `action.nuclear_strike`, `engine.election_result`, `action.ground_attack` (first attack = war declaration), `action.agreement_sign` (peace), `engine.tech_advance` (level 4), `action.blockade` (chokepoint blocked/opened).

---

# 5. RETRY AND RESILIENCE

## 5.1 Engine Unavailable

If the engine server is unreachable or returns 5xx:
1. Retry once after 2 seconds
2. If still failing, return `503 Service Unavailable` to client with `Retry-After: 10` header
3. Log to `sim:{sim_run_id}:facilitator` channel as `engine_status: unavailable`

## 5.2 Idempotency

All state-modifying Edge Functions accept an `idempotency_key`. Before processing:
1. Check `events.idempotency_key` in DB for duplicate
2. If found, return the cached response (from the events table result column)
3. If not found, process and store result with the idempotency_key

## 5.3 Timeout

Edge Function timeout: 25 seconds (Supabase limit: 30s).
Engine timeout: 20 seconds for live actions, passed through to engine server.
Round processing timeout: Forward immediately, poll for result (engine processes up to 5 minutes; Edge Function returns `202 Accepted` with a polling URL).

---

# 6. ENVIRONMENT VARIABLES

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Supabase project URL (auto-injected) |
| `SUPABASE_ANON_KEY` | Anon key for client operations (auto-injected) |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key for privileged DB operations |
| `ENGINE_URL` | Python engine server URL (Railway) |
| `ENGINE_AUTH_SECRET` | Shared secret for HMAC signing |

---

*This document specifies the Edge Function middleware layer. It bridges the C3 participant-facing API and the F5 engine API. For the complete participant API, see DET_C3_API_SPEC.yaml. For the engine API, see DET_F5_ENGINE_API.md.*
