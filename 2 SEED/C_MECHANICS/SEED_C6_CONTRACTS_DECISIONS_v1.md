# Contracts & Collective Decisions
## Thucydides Trap SIM — SEED Specification
**Version:** 1.0 | **Date:** 2026-03-28

---

## Principle

Agreements between participants are **free-form and socially enforced**. The engine records contracts and executes their mechanical effects (if any), but does NOT police compliance. Breaking a treaty has no engine penalty — it has diplomatic consequences.

This matches real geopolitics: treaties are binding because of relationships, reputation, and mutual interest — not because a referee enforces them.

---

## Transaction Types

All contracts are processed through the **Transaction Engine** during Phase A (real-time, on confirmation from both parties).

### 1. Treaty

A written agreement between two or more countries. Stored as text. No mechanical effect — purely diplomatic.

| Property | Value |
|----------|-------|
| **Authorization** | Head of State (both parties) |
| **Confirmation** | Both parties must confirm |
| **Mechanical effect** | None — stored in the event log |
| **Reversible** | No (can be publicly denounced, but the record remains) |
| **Visibility** | Parties decide: private or announced publicly |

**Use cases:** Mutual defense pacts, non-aggression agreements, economic cooperation frameworks, technology sharing agreements, resource extraction rights, neutrality pledges.

**Format:** Free text. The moderator does not review or approve treaty text. Participants write what they agree to. The engine logs it verbatim.

### 2. Agreement (with subtypes)

An agreement with potential mechanical effects, depending on subtype.

| Subtype | Mechanical Effect |
|---------|------------------|
| **ceasefire** | Ends active war between signatories on opposing sides |
| **peace** | Ends active war between signatories on opposing sides |
| **trade** | None — records terms, compliance is social |
| **alliance** | None — records commitment, compliance is social |
| **general** | None |

**Ceasefire/Peace mechanic:** When an agreement of subtype `ceasefire` or `peace` is confirmed, the engine scans all active wars. If the signatories are on opposing sides of a war, that war is removed. This is the ONLY mechanical effect of any contract type.

**Important:** A ceasefire stops the war but does NOT require troop withdrawal. Units remain where they are. Occupied territory stays occupied. These are separate decisions for the participants.

| Property | Value |
|----------|-------|
| **Authorization** | Head of State (both parties) |
| **Confirmation** | Both parties must confirm |
| **Reversible** | No (but a new war can be declared) |
| **Visibility** | Parties decide |

### 3. Basing Rights

Permission for one country to station military units in another's territory.

| Property | Value |
|----------|-------|
| **Authorization** | Head of State (both parties) |
| **Confirmation** | Both parties must confirm to grant |
| **Mechanical effect** | Guest country may deploy units to the specified zone |
| **Reversible** | Yes — **host can revoke unilaterally at any time** |
| **Visibility** | Public (unit presence visible on map) |

**Revocation:** The host country can revoke basing rights without the guest's consent. Upon revocation, guest units must redeploy within 1 round or are considered stranded (reduced effectiveness, cannot attack, can only defend).

### 4. Organization Creation

Founding a new international organization.

| Property | Value |
|----------|-------|
| **Authorization** | Head of State (all founding members) |
| **Confirmation** | All founding members must confirm |
| **Mechanical effect** | Organization appears in the system with member list |
| **Decision rule** | Set at creation: consensus, majority, or veto (configurable) |

**What an organization IS:** A communication channel with a member list. Organizations provide a structured venue for multilateral negotiation. They do NOT have budgets, armies, or independent agency.

**What an organization CAN DO:** Members can call meetings (during Phase A). Members can propose collective statements, joint sanctions, coordinated military action — but these are commitments by individual members, not "organization actions."

---

## Pre-existing Organizations

These exist at game start with established membership:

| Organization | Members | Decision Rule | Notes |
|-------------|---------|:------------:|-------|
| **NATO** | Columbia + European allies | Consensus | Collective defense commitment |
| **EU** | European member states | Qualified majority | Economic coordination |
| **BRICS+** | Cathay, Sarmatia, Persia, others | Consensus | Economic/political counterweight |
| **OPEC+** | Oil producers (Persia, Wellspring, others) | Consensus (production quotas) | Oil production coordination |
| **UNSC** | All (5 permanent with veto + rotating) | Veto (P5) | Symbolic — resolutions are non-binding in SIM |
| **SCO** | Cathay, Sarmatia, Central Asian states | Consensus | Security cooperation |
| **G7** | Columbia + major Western economies | Consensus | Economic policy coordination |

Exact membership lists are in `countries.csv` (org_memberships column) and `relationships.csv`.

---

## Collective Decision Making

### How Organizations Make Decisions

There is NO engine mechanic for organizational voting. Organizations work like this:

1. A member calls a meeting (announces to all members during Phase A)
2. Members who attend discuss the proposal
3. Members individually decide whether to support it
4. If the organization's decision rule is met (consensus/majority/veto), the decision is "adopted"
5. **Adoption = each member individually commits to the action**

**Example — NATO Article 5:**
- Ruthenia is attacked
- NATO member calls emergency session
- Members discuss response
- Each NATO member individually decides what military/economic support to provide
- The "NATO response" is the sum of individual member commitments
- There is no "NATO army" — there are individual country contributions

**Example — OPEC+ production:**
- Member calls OPEC+ session
- Members negotiate production levels
- Each member commits to a production level
- Compliance is monitored socially (cheating is visible in world update)
- No engine enforcement — a member CAN exceed their quota

**Example — BRICS+ currency union:**
- Requires all members to agree (consensus)
- If adopted: each member country adjusts trade settlement currency (parameter change)
- Non-compliance = continuing to trade in dollars (visible, damages trust)

### Veto Mechanics

For organizations with veto rules (UNSC):
- Any permanent member can block a resolution by stating their veto
- This is a social action, not an engine mechanic
- The moderator records it; the resolution is noted as "vetoed"
- Vetoed resolutions have no effect (they never had mechanical effect anyway)

### Organization Membership Changes

- **Joining:** Existing members must agree (per decision rule). New member confirms.
- **Leaving:** Unilateral. A member announces withdrawal. Effective immediately.
- **Expulsion:** Requires a decision per the organization's rule (without the target's vote).

All membership changes are recorded in the event log.

---

## Contract Enforcement Philosophy

| What happens when... | Engine response | Social response |
|---------------------|----------------|-----------------|
| Country breaks a treaty | Nothing | Trust erosion, alliance damage, public narrative |
| Country violates ceasefire (attacks) | Attack resolves normally (ceasefire doesn't prevent attacks) | Severe diplomatic damage, possible counter-alliance |
| Country cheats on OPEC+ quota | Oil price reflects actual production | Reputational damage within OPEC+ |
| Country violates trade agreement | Nothing (tariffs are set independently) | Retaliatory tariffs, sanctions |
| Country breaks alliance commitment | Nothing | Partner seeks other allies, possible betrayal narrative |

**The moderator notes broken commitments** in the world narrative but does not penalize them mechanically. The SOCIAL consequences — other participants' reactions — are the enforcement mechanism. This produces richer gameplay than automated penalties.

---

## What This Specification Does NOT Do

- Does NOT create a "contract editor" UI — contracts are free text, written by participants
- Does NOT enforce treaty compliance — social dynamics do that
- Does NOT give organizations independent agency — organizations are communication channels
- Does NOT create voting UI for organizations — voting happens in conversation
- Does NOT create "package deals" — each component of a complex deal is a separate transaction

---

## Integration with Other Systems

- **Transaction Engine** processes all contract types in real-time during Phase A
- **Event Log** records every contract with full text, signatories, and round
- **AI Participants** factor contracts into their Block 3 (Memory) and Block 4 (Strategy)
- **Public Speaking** (C5) captures any public announcements about contracts
- **World Model Engine** sees ceasefire/peace effects (war list changes) at next processing

---

*Contracts work best when they're free, recorded, and consequential through social dynamics — not through mechanics. Same principle as public speaking (C5).*
