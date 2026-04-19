# Nuclear Launch — Human Interface Design

**Date:** 2026-04-18 | **Status:** DESIGN — awaiting approval before build
**Depends on:** Nuclear Test (DONE), M2 Realtime (DONE), Combat system (DONE)

---

## Overview

Nuclear launch is a 4-phase multi-player action that pauses the simulation round timer and involves ALL participants. The engine (NuclearChainOrchestrator) is fully built — this spec covers the human interface layer.

---

## Phase 1: INITIATION (Launcher HoS)

**Where:** Nuclear Launch action in Military category (HoS only)

**UI Flow:**
1. Dark themed panel (same style as Nuclear Test)
2. Status bar: nuclear_level, confirmed, deployed missiles count
3. Map (global, 75% width) — click to select target hex(es)
4. Sidebar (25%): list of deployed strategic_missile units, click to select
5. For each selected missile → click target hex → pair queued
6. Review: list of missile→target pairs
7. Confirm → "LAUNCH SEQUENCE INITIATED"

**Constraints:**
- Must have `nuclear_confirmed = true`
- Missiles must be active + deployed (not reserve/embarked)
- No minimum count (1 missile is valid)
- Range per tier: T1≤2, T2≤4, T3 global

---

## Phase 2: AUTHORIZATION (10 min timer, configurable)

**Timer:** Real server-side. For testing: 40 seconds. Production: 10 minutes.
**Round timer PAUSED** during nuclear authorization window.

### Launcher's screen:
- Dark overlay with countdown timer
- Status per authorizer: "Awaiting [role]... ⏳" → "AUTHORIZED ✓" / "REJECTED ✗"
- On all authorized → "LAUNCH AUTHORIZED" dramatic flash
- On any rejection → "LAUNCH CANCELLED"

### Authorizers' screens (Shield + Shadow for Columbia, etc.):
- **Actions Expected Now:** Red urgent card "⚠ NUCLEAR LAUNCH AUTHORIZATION REQUIRED"
- Click → dark panel with:
  - Launcher country, target(s), missile count
  - Timer countdown
  - **AUTHORIZE** (red button) / **REJECT** (grey button)
  - Rationale text field (≥30 chars)

### Moderator sees:
- Pending action card: "NUCLEAR AUTHORIZATION" with timer
- Can see who authorized/rejected

### Auto-cancel on timer expiry:
- If not all authorized within timer → action cancelled
- Observatory event: "Authorization timed out"

---

## Phase 3: FLIGHT + INTERCEPTION (10 min timer)

**Timer:** Real server-side. Round timer remains PAUSED.
**This is the dramatic moment.**

### ALL participants' screens — persistent banner:
```
⚠ BALLISTIC MISSILE LAUNCH DETECTED — [COUNTRY]
[N] MISSILES INBOUND — Impact in [MM:SS]
```
- Red background, same position as moderator proxy banner
- Countdown to timer end (impact time)
- Stays until Phase 4 resolution

### T3+ countries' screens:
- **Actions Expected Now:** "⚠ NUCLEAR INTERCEPTION DECISION"
- Click → dark panel:
  - Launch details (who, how many, targets)
  - Your AD unit count, interception probability (25% per AD)
  - **INTERCEPT** / **DECLINE** buttons
  - Rationale text field

### Target country:
- Same banner + message: "Your air defense systems are engaging automatically"
- No decision needed (50% per AD, auto-fire)

### T3 HoS + military classified artefact:
- Auto-generated on launch authorization
- Details: launcher, targets, missile count, estimated capability

### Auto-decline on timer expiry:
- T3+ countries that don't respond → decline (no interception)

---

## Phase 4: RESOLUTION

### ALL participants' screens — dramatic overlay:
- Full-screen dark overlay (same as nuclear test countdown style)
- "RESOLVING NUCLEAR STRIKE..." in matrix green
- Per-missile results revealed one by one:
  - "Missile 1 → (row,col): INTERCEPTED" (green)
  - "Missile 2 → (row,col): IMPACT" (red, pulsing)
- Then damage summary:
  - "Military units destroyed: N"
  - "GDP impact: -X%"
  - "Nuclear site destroyed" (if applicable)
- T3 salvo effects (if ≥1 hit):
  - "GLOBAL STABILITY: -1.5"
  - "TARGET STABILITY: -2.5"
  - "Leader survival roll: [result]"

### Map:
- ☢ markers at all IMPACT hexes (dark red, pulsing)
- Intercepted missiles: no marker

### Public Screen:
- Red alert banner: "NUCLEAR STRIKE — [TARGET COUNTRY]" (60 seconds)
- News ticker: full event details

### Round timer resumes after Phase 4 completes.

---

## Technical Architecture

### Timer Implementation:
- `nuclear_actions.timer_started_at` + `timer_duration_sec` = deadline
- Server checks deadline on each authorization/interception submission
- Frontend polls `/api/sim/{id}/nuclear/{action_id}/status` every 2 seconds
- Auto-cancel/auto-decline triggered by:
  - Server-side: next submission after deadline checks expiry
  - OR: moderator can force-resolve via facilitator dashboard

### Global Banner:
- All clients subscribe to `nuclear_actions` table via Supabase Realtime
- When `status` changes to `awaiting_interception` → show banner
- Banner reads `timer_started_at + timer_duration_sec` for countdown
- When `status` changes to `resolved` → show resolution overlay

### Orchestrator Migration:
- Update `_resolve_launch()` to write to `deployments` table (not unit_states_per_round)
- Same field mapping as move_units: unit_id↔unit_code, country_id↔country_code, unit_status↔status

### Actions Expected Now:
- Authorization requests: check `nuclear_actions` where `status='awaiting_authorization'` and role matches authorizer
- Interception requests: check `nuclear_actions` where `status='awaiting_interception'` and country is T3+

### Round Timer Pause:
- When nuclear_launch_initiate succeeds → moderator's "pause" is triggered automatically
- Phase timer paused, "NUCLEAR EVENT IN PROGRESS" shown
- Resumes after Phase 4 resolution

---

## Configurable Parameters

| Parameter | Test Value | Production Value |
|-----------|-----------|-----------------|
| Authorization timer | 40 seconds | 10 minutes |
| Interception timer | 40 seconds | 10 minutes |
| Auto-cancel on expiry | Yes | Yes |
| Auto-decline on expiry | Yes | Yes |

Stored in `sim_runs.schedule` or `sim_runs` columns.

---

## Files to Create/Modify

| File | Change |
|------|--------|
| `ParticipantDashboard.tsx` | NuclearLaunchForm, AuthorizationPanel, InterceptionPanel, global banner, resolution overlay |
| `PublicScreen.tsx` | Nuclear strike alert banner (60s) |
| `FacilitatorDashboard.tsx` | Nuclear event card in pending area |
| `map-core.js` | ☢ markers for nuclear impacts |
| `action_dispatcher.py` | Already wired (nuclear_launch_initiate, authorize, intercept) |
| `nuclear_chain.py` | Migrate _resolve_launch to deployments table |
| `main.py` | Nuclear status API endpoint, round timer pause on launch |
| `queries.ts` | submitAction already works |

---

*This design requires Marat's approval before implementation.*
