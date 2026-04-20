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

---

*Session by Marat Atn + Claude Opus 4.6*
