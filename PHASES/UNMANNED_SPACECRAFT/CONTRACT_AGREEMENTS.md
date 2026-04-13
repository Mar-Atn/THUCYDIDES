# CONTRACT: Agreements

**Status:** 🔒 **LOCKED** (2026-04-13) | **Version:** 1.0 | **Owner:** Marat
**Source:** `CARD_ACTIONS.md` §5.2 + `TRANSACTION_LOGIC.md` Part 1.4

---

## 1. PURPOSE

Agreements are **written commitments** between countries. Unlike exchange
transactions (which move assets), agreements are promises recorded in
the system. They rely on trust, reputation, and consequences — NOT engine
enforcement.

All agreements are just **saved in the DB**. The system records them
faithfully. No special enforcement, no automatic consequences for breach.
Countries have full sovereignty and freedom of action.

---

## 2. THE FLOW

```
A drafts agreement (name, type, terms, signatories, visibility)
  → A sends to all signatories
    → Each signatory: CONFIRM (sign) or DECLINE (with comments)
      → ALL confirm → agreement ACTIVE
      → ANY decline → initiator can revise and re-send (new proposal)
```

No counter-offer mechanic for agreements (unlike transactions). A
signatory either signs or doesn't. The initiator can revise terms
based on feedback and send a new agreement.

---

## 3. AGREEMENT SCHEMA

### 3.1 propose_agreement

```json
{
  "action_type": "propose_agreement",
  "proposer_role_id": "dealer",
  "proposer_country_code": "columbia",
  "round_num": 3,
  "agreement_name": "Columbia-Sarmatia Non-Aggression Pact",
  "agreement_type": "non_aggression",
  "visibility": "public",
  "terms": "Both parties commit to cease all hostile military actions for 3 rounds. Any breach triggers automatic notification to all parties.",
  "signatories": ["columbia", "sarmatia"],
  "rationale": "De-escalation after the border crisis"
}
```

| Field | Type | Notes |
|---|---|---|
| `agreement_name` | string | Human-readable name |
| `agreement_type` | string | One of the pre-defined types or custom |
| `visibility` | `"public"` or `"secret"` | Public = all see. Secret = signatories only. |
| `terms` | string (free text) | Whatever the parties agree to |
| `signatories` | list[str] | Country codes. Must include proposer. |
| `rationale` | string | Proposer's reasoning (optional, private) |

### 3.2 Pre-defined agreement types

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
| `organization_creation` | Creates new org: name + members + purpose. |
| *(custom)* | Any free-text type. Recorded as-is. |

### 3.3 sign_agreement (per signatory)

```json
{
  "agreement_id": "uuid",
  "country_code": "sarmatia",
  "role_id": "pathfinder",
  "confirm": true,
  "comments": "Sarmatia agrees to the non-aggression terms"
}
```

| `confirm` | Effect |
|---|---|
| `true` | Signature added. If all signatories confirmed → ACTIVE. |
| `false` | Declined. Comments visible to initiator for revision. |

### 3.4 Visibility

- **Public:** all countries see agreement name, type, signatories, terms.
- **Secret:** only signatories see it. Others unaware it exists. Can be
  revealed later (voluntarily or via intelligence).

---

## 4. VALIDATION

| Code | Rule |
|---|---|
| `INVALID_PAYLOAD` | Must be dict |
| `INVALID_ACTION_TYPE` | `propose_agreement` |
| `MISSING_NAME` | agreement_name required |
| `INVALID_TYPE` | agreement_type required (any string accepted, pre-defined encouraged) |
| `INVALID_VISIBILITY` | `public` or `secret` |
| `MISSING_TERMS` | terms required (non-empty string) |
| `MISSING_SIGNATORIES` | at least 2 signatories |
| `PROPOSER_NOT_SIGNATORY` | proposer's country must be in signatories list |
| `INVALID_SIGNATORY` | each signatory must be a valid country_code |
| `UNAUTHORIZED_ROLE` | proposer must be authorized to sign agreements (HoS, FM, PM) |

---

## 5. PERSISTENCE

### 5.1 `agreements` table (enhanced)

```
agreements:
  id, sim_run_id, round_num,
  agreement_name, agreement_type, visibility,
  terms (text),
  signatories (text[]),
  proposer_country_code, proposer_role_id,
  signatures (jsonb) — {country_code: {confirmed: bool, role_id, comments, signed_at}}
  status (proposed|active|declined),
  created_at
```

### 5.2 Events

- `event_type='agreement_proposed'` — when sent to signatories
- `event_type='agreement_signed'` — when a signatory confirms
- `event_type='agreement_declined'` — when a signatory declines
- `event_type='agreement_activated'` — when all signatories confirmed

---

## 6. NO ENFORCEMENT

Per Marat's explicit direction: **no engine enforcement of any agreement
type.** All agreements are just saved. Countries have full sovereignty.

- Armistice: recorded. If a country attacks after signing, that's their
  choice. No auto-block, no auto-breach detection, no notifications.
- Peace treaty: recorded. Same — just a record.
- All others: recorded. Trust-based.

The agreements table is a historical record of what was agreed. The
Observatory and AI Participant Module can READ agreements to inform
decisions, but the engine NEVER uses them to constrain actions.

---

## 7. LOCKED INVARIANTS

1. All signatories must confirm for activation (unanimous)
2. Any single decline → agreement not activated (initiator can revise + retry as new proposal)
3. No counter-offer on agreements — confirm or decline only
4. No engine enforcement — all trust-based, full sovereignty
5. Agreements are just saved in DB — reconstruction always possible
6. Public/secret visibility is a flag, not access control (the data exists either way)
7. Pre-defined types are suggestions — any free-text type accepted
8. Actor-agnostic: same API for human, AI, moderator
