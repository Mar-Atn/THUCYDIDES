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

*Session by Marat Atn + Claude Opus 4.6*
