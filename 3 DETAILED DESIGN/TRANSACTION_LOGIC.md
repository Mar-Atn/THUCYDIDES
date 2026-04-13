# Transaction Logic — Functional Specification

**Status:** Draft for Marat review
**Principle:** This spec describes WHAT the transaction system does — regardless of whether participants are human or AI. The system doesn't know or care.

---

## PART 1: THE TRANSACTION SYSTEM (universal)

### 1.1 Two types of transactions

**Exchange:** assets change hands. Coins, units, tech, basing rights. Immediate, irreversible once executed. Both sides must confirm. Engine validates assets exist.

**Agreement:** written commitment. Ceasefire, treaty, alliance, trade deal, or any free text. Recorded. Only armistice and peace treaty are engine-enforced. Everything else is trust-based.

### 1.2 Timing

**Transactions are available ANY TIME during rounds.** Any participant can propose a deal at any moment. There is no "transaction phase" — deals happen continuously alongside conversations, military actions, and everything else.

### 1.3 Exchange transaction flow

```
STEP 1: PROPOSE
  Any authorized participant creates a proposal:
    - Counterpart (who is this for)
    - Offer: what I give — selected from MY available assets
      (system shows proposer only THEIR OWN available assets to pick from)
    - Request: what I want in return — free choice
      (system does NOT reveal what the counterpart has)
    - Rationale (optional, private to proposer)

  System validates: proposer HAS the offered assets.
  If proposer's offer is invalid → rejected immediately ("you don't have this").
  If valid → proposal recorded as PENDING, counterpart notified.

  IMPORTANT: System does NOT validate the REQUEST side at this stage.
  The counterpart's assets are NOT checked until after they respond.
  (Prevents using proposals to probe what the other side has.)

  Proposal EXPIRES after 10 minutes (adjustable in Template).
  If no response → proposal disappears.

STEP 2: EVALUATE
  Counterpart sees the proposal (offer + request) and decides:
    - ACCEPT → proceed to validation + execution
    - DECLINE → proposal closed, both parties notified
    - COUNTER → new terms sent back to proposer (one round of counter max)

  Counterpart does NOT see a pre-validated "available" flag.
  They accept or decline based on their own judgment.

  If counter-proposed:
    Original proposer sees counter-terms and decides: ACCEPT or DECLINE.
    No further iterations — deal closes either way.

STEP 3: VALIDATE + EXECUTE (only if both sides confirmed)
  NOW the system validates BOTH sides:
    - Proposer still has the offered assets? (may have changed since proposal)
    - Counterpart has the requested assets?

  If EITHER side's assets are insufficient:
    → Deal fails. Both notified: "deal cannot complete — assets unavailable."
    → The side that lacks assets could not have accepted with "available"
      option — they could only decline or counter.

  If both valid:
    - Coins: deducted from sender, added to receiver
    - Units: ownership flips to receiver, status → reserve,
      reduced effectiveness for 1 round
    - Tech: receiver gains R&D progress boost
      (nuclear +0.20, AI +0.15 per CARD_FORMULAS C.4)
    - Basing: relationship table updated, revocable by host at any time

  Execution is IMMEDIATE.
  Reversibility depends on asset type:
    - Coins: IRREVERSIBLE (money spent)
    - Units: IRREVERSIBLE (ownership transferred permanently)
    - Technology: IRREVERSIBLE (knowledge shared cannot be unlearned)
    - Basing rights: REVOCABLE — host country can revoke at any time,
      unilaterally, as a separate action. This is the ONLY reversible asset.

  Both parties notified. Transaction logged. Observable in Observatory.

STEP 4: RECORD
  Completed transaction stored with:
    - Who proposed, who accepted
    - What was exchanged (structured)
    - Timestamp, round number
    - Status: executed | expired | declined | failed_validation
  Visible in Observatory Activity feed.
```

### 1.3 What can be traded (exhaustive)

| Asset | Direction | Validation | Effect |
|---|---|---|---|
| **Coins** | Exclusive (sender loses, receiver gains) | Sender treasury ≥ amount | Treasury balances updated |
| **Military units** | Exclusive (sender loses, receiver gains) | Unit exists, belongs to sender, not destroyed | Unit ownership flips, goes to reserve, -1 round effectiveness |
| **Technology** | Replicable (sender keeps, receiver gains) | None | Receiver R&D progress boosted |
| **Basing rights** | Replicable (host keeps sovereignty) | None | Relationship flag set. Host can revoke anytime. |

**Combinations are valid.** 3 coins + basing rights for 2 ground units + tech transfer = one transaction.

**NOT tradeable:** covert op cards, territory (use agreements), promises (use agreements).

### 1.4 Agreement flow

```
STEP 1: DRAFT
  Any authorized participant creates a draft agreement:
    - Agreement name (e.g., "Sarmatia-Ruthenia Ceasefire")
    - Type (armistice, peace_treaty, military_alliance, trade_agreement,
      arms_control, non_aggression, sanctions_coordination,
      mutual_defense, organization_creation, or custom)
    - Terms (free text — whatever the parties agree to)
    - Signatories (list of required parties)
    - Visibility (public or secret)

  Draft can be SAVED and EDITED before sending.
  Initiator can revise terms, add/remove signatories, reword —
  without retyping from scratch.

STEP 2: SEND FOR SIGNATURE
  When ready, initiator sends the draft to all required signatories.

STEP 3: EVALUATE
  Each signatory reviews and decides:
    - CONFIRM (sign) → their signature added
    - DECLINE — with comments explaining why
      (comments visible to initiator, who can revise and re-send)

  ALL signatories must confirm for agreement to activate.
  Any decline → initiator can revise draft based on feedback and re-send.

STEP 4: ACTIVATE
  When all signatories have confirmed → agreement recorded as ACTIVE.

  Engine-enforced types:
    - ARMISTICE: combat stops between signatories, territory frozen.
      Breach (attacking after signing) = automatic re-declaration +
      all countries notified.
    - PEACE TREATY: war formally ended between signatories. Permanent.

  All other types: recorded but NOT enforced.
  Parties rely on trust, reputation, and consequences.

STEP 5: RECORD
  Agreement stored with: name, type, terms, signatories, signatures,
  visibility, status (draft/proposed/active/breached/expired), timestamp.
  Public agreements visible to all. Secret agreements visible
  only to signatories (can be revealed via intelligence or voluntarily).
```

### 1.5 Authorization — who trades what

**Two modes of trading:**

| Mode | Who acts | What assets | Authorization |
|---|---|---|---|
| **On behalf of country** | Authorized officials (HoS, FM, PM, military chief — per role permissions in Template) | Country treasury, military units, technology, basing rights | Role must have permission for that asset type. HoS can trade anything. FM can trade coins. Military chief can trade units. |
| **On behalf of self** | Any individual participant | Personal coins only | No authorization needed — it's their money |

**Agreements** are always on behalf of countries. Only authorized officials (HoS, FM, PM — as defined in Template role data) can sign binding agreements. The specific authorization per role is Template data.

### 1.6 Transaction rules

- Available ANY TIME during rounds — no transaction phase
- Both sides must explicitly confirm — no assumed acceptance
- Proposer's assets validated at PROPOSAL. Counterpart's assets validated at EXECUTION (not before).
- Proposals expire after 10 minutes (adjustable in Template)
- Executed exchanges are permanent (except basing rights — revocable by host)
- Decline can include comments (feedback for revision)
- Agreement drafts can be saved, edited, re-sent
- Failed validation at execution → deal fails, both notified
- All transactions and agreements logged for Observatory

---

## PART 2: AI PARTICIPANT INTERACTION WITH TRANSACTIONS

The AI Participant module interacts with the Transaction System via the **same standard protocols and contracts** that a human participant's UI would use. See `AI_CONCEPT.md` for the full AI module architecture.

**Key principle:** The transaction system does NOT know whether a human or AI is acting. It receives proposals, evaluations, and confirmations through the same API. The AI module is one possible client of that API.

### 2.1 How an AI agent uses transactions

The AI agent operates via the active loop described in `AI_CONCEPT.md`. At each decision cycle, the agent sees its full context (situation, goals, memory, available actions, incoming events) and freely decides what to do. Proposing a transaction is one of many available actions — not a special mechanism.

If the agent decides to propose a deal, it submits through the standard decision API. If a proposal arrives for the agent, it appears as an incoming event — the agent evaluates and responds through the same API.

The transaction system processes these identically to human-originated proposals.

### 2.2 Simplified testing mode

For cost/time efficiency during unmanned testing, agents may operate in a simplified batch mode (e.g., "decide N actions this round" instead of continuous polling). This is a **testing optimization only** — not a design feature. The target architecture is the full active loop where agents freely decide at each cycle, with real-time awareness of context and events.

### 2.3 Standardization

The AI module communicates with the transaction system (and all other SIM systems) via the same real-time layer and contracts that the human player interface will use. No special AI-only pathways. This ensures:
- Human and AI participants can coexist in the same SIM
- The transaction system can be tested with either client type
- Switching a role from AI to human (or vice versa) requires zero system changes

---

## Decisions (Marat 2026-04-08)

1. **Counter-proposals:** Max 1 round of counter. A proposes → B counters → A accepts/declines. Done.
2. **Transaction without conversation:** YES. Transactions are a free action, no connection to conversations. Can propose to anyone anytime.
3. **Ceasefire/armistice timing:** No retroactive adjustment. Armistice is what participants agreed — the system does NOT enforce it. If they fire after armistice, that's their choice. All completed attacks are done and accounted for.
4. **Secret agreements:** MUST be implemented properly. Secret agreements visible ONLY to signatories. AI participants must have ONLY information appropriate to THEIR role — not full SIM context. (This implies broken context scoping needs fixing — AI agents currently may see too much.)
5. **Multiple transactions per pair:** As many as they want. No limit.

## Note on AI Participant design

The AI participant transaction behavior is part of a broader architectural question. See `AI_CONCEPT.md` in this directory for the standalone AI Participant module design — inputs, outputs, contracts, information scoping.
