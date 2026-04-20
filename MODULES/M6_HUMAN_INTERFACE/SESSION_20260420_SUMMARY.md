# Session Summary — 2026-04-20 (continued)

**Scope:** Assassination, killed status, Phase B restrictions, election fixes, restart hardening

---

## Features Delivered

### 1. Assassination — Complete System
- **Who:** Security position only, 3 attempts per SIM
- **Target:** Any active role, any country (domestic + international)
- **Success:** 20% flat, Levantia bonus 50%
- **Outcome:** Success = target killed (out for rest of SIM)
- **Detection:** Always 100%, Attribution 50%
- **Martyr effect:** Kill → target country stability +1.5
- **UI:** Target list grouped by country, remaining attempts shown
- **Moderator:** Standard Confirm/Reject card with initiator → target names
- **Participant:** Form stays open, PendingResultPoller shows result when confirmed
- **Public news:** Attributed ("evidence [Name] was behind...") or anonymous ("perpetrators unknown")
- **DB:** Added 'killed' to roles_status_check constraint

### 2. Killed Status
- Banner: "You Have Been Killed" (permanent, red, full-width)
- Actions tab: "Eliminated" message, all actions blocked
- Other tabs (Confidential, Country, World, Map) remain visible
- Permanent for rest of SIM (unlike arrest which auto-releases)
- Moderator sees "Killed" status in participant management

### 3. Phase B Restriction
- During inter_round phase: only `move_units` allowed
- All other actions return 400: "Only unit movements are allowed during the inter-round phase"
- Enforced server-side in submit_action endpoint

---

## Fixes & Improvements

### Restart Hardening
- `uses_remaining` reset to `uses_total` for all limited actions on restart
- Countries restored via UPDATE (not DELETE — foreign key safe)
- Election schedule flags cleared on restart
- "Start Nominations" button clears all stale election flags

### Election Flow Fixes
- All election buttons use local state for immediate UI response (JSONB updates don't trigger realtime)
- Start Nominations, Close Nominations, Start Election, Stop Voting — all respond instantly
- Moderator can edit votes via dropdowns (optimistic local state)
- Simple majority (most votes wins, not threshold-based)
- Timer shows "Voting closed" when stopped (no more ticking)
- Tie handling: winner_role_id = "none" (DB NOT NULL constraint)

### Pending Actions
- Target character name resolved (not just role ID)
- target extracted from changes.target_role for arrest/assassination

---

## Database Migrations
1. `add_killed_to_roles_status_check` — added 'killed' to status constraint

---

---

## Session Continued — Evening 2026-04-20

### 10. Covert Operations — Sabotage + Propaganda
- **Who:** Security only, 7 shared uses per SIM
- **Sabotage:** target any foreign country — Infrastructure / Nuclear Site / Military
  - Success 50%, Detection 100%, Attribution 50%
  - Effects: -1 treasury / -30% R&D / 50% destroy random unit
- **Propaganda:** target any country (incl. own) — Support / Undermine stability
  - Success 55%, Detection 100%, Attribution 20%
  - Effect: ±0.3 stability (diminishing returns)
- **No election meddling** (covered by propaganda)
- UI: unified form with op type selector, target country, immediate execution
- Public news for detected operations (attributed / anonymous)

### 11. Intelligence — LLM-Powered Reports
- **Who:** Security(5), Military(5), Diplomat(1), Opposition(2) per SIM
- **Flow:** Free-form question → LLM generates classified briefing → artefact in Confidential tab
- **Context:** 24KB world state including:
  - All 20 countries (GDP, stability, inflation, nuclear, AI, debt)
  - Military deployments (all units per country per branch)
  - Relationships, agreements, recent events (last 3 rounds)
  - Nuclear status, blockades, basing rights
  - Game mechanics & rules (for analysis, not disclosed)
- **LLM:** Gemini Flash (cost-efficient), ~20-25% noise injection
- **Artefact:** Classified report styled as intelligence briefing
- **Systemic fix:** `call_llm_sync()` in llm.py handles async-from-sync context

### Systemic Improvements
- `call_llm_sync()` — reusable sync wrapper for async LLM calls from FastAPI sync endpoints
- Intelligence context builder migrated from deprecated tables to live `countries` + `deployments`
- `roles_status_check` constraint updated: added 'killed'
- Restart: resets `uses_remaining` for all limited actions

### 12. Public Statement — Official Org Decisions
- Chairman of any organization can publish "Official Decision of [Org Name]"
- Radio selector: personal statement vs org decision (one per chaired org)
- Event type: `org_decision` (distinct from `public_statement`)
- Appears on public screen as official organization announcement

### 13. Set Meetings — Unified 1:1 + Org Meetings
- **1:1 Meeting:** Select any role from any country + message (300 chars)
- **Organization Meeting:** Select org (member orgs only) + theme + message
- Invitee sees card in Actions Expected Now with Accept/Decline/Not now
- **10-minute expiry** — auto-expires if no response
- **Max 2 active invitations** per role
- Initiator sees responses in real-time (accepted/declined/later + messages)
- Org invitations: only shown to org members (not all participants)
- Phase B: meetings + communication allowed alongside move_units
- Future hook: AI-Human and AI-AI conversation endpoint

### Phase B Restriction Update
- Inter-round now allows: move_units + all communication actions
  (invite_to_meet, respond_meeting, public_statement, call_org_meeting)

---

## Complete Action Inventory — What's Built

| Action | Status | UI | Engine |
|--------|--------|-----|--------|
| Ground Attack | DONE | AttackForm | military.py |
| Air Strike | DONE | AttackForm | military.py |
| Naval Combat | DONE | AttackForm | military.py |
| Naval Bombardment | DONE | AttackForm | military.py |
| Missile (conventional) | DONE | AttackForm | military.py |
| Naval Blockade | DONE | BlockadeForm | blockade_engine.py |
| Move Units | DONE | MoveUnitsForm | movement.py |
| Ground Move | DONE | AttackForm | action_dispatcher.py |
| Nuclear Test | DONE | NuclearTestForm | nuclear_chain.py |
| Nuclear Launch | DONE | NuclearLaunchForm | nuclear_chain.py |
| Nuclear Authorize | DONE | reactive card | nuclear_chain.py |
| Nuclear Intercept | DONE | reactive card | nuclear_chain.py |
| Set Budget | DONE | BudgetForm | batch |
| Set Tariffs | DONE | TariffSanctionForm | batch |
| Set Sanctions | DONE | TariffSanctionForm | batch |
| Set OPEC | DONE | CartelProductionForm | batch |
| Declare War | DONE | DeclareWarForm | action_dispatcher.py |
| Propose Agreement | DONE | ProposeAgreementForm | agreement_engine.py |
| Sign Agreement | DONE | reactive card | agreement_engine.py |
| Propose Transaction | DONE | ProposeTransactionForm | transaction engine |
| Accept Transaction | DONE | reactive card | transaction engine |
| Basing Rights | DONE | BasingRightsForm | basing_rights_engine.py |
| Martial Law | DONE | MartialLawForm | martial_law_engine.py |
| Change Leader | DONE | ChangeLeaderForm | change_leader.py |
| Reassign Powers | DONE | ReassignPowersForm | action_dispatcher.py |
| Arrest | DONE | ArrestForm + release | arrest_engine.py |
| Assassination | DONE | AssassinationForm | assassination_engine.py |
| Covert Operation | DONE | CovertOpsForm | sabotage/propaganda engines |
| Intelligence | DONE | IntelligenceForm | intelligence_engine.py + LLM |
| Public Statement | DONE | PublicStatementForm + org | action_dispatcher.py |
| Set Meetings | DONE | SetMeetingsForm | action_dispatcher.py |
| Self-Nominate | DONE | election UI | election_engine.py |
| Cast Election Vote | DONE | election UI | election_engine.py |

**32 of 35 designed actions are fully implemented with human interfaces.**

---

*Session by Marat Atn + Claude Opus 4.6*
