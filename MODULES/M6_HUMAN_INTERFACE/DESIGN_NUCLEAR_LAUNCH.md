# Nuclear Launch — Human Interface Design

**Date:** 2026-04-18 | **Status:** APPROVED — ready to build
**Depends on:** Nuclear Test (DONE), M2 Realtime (DONE), Combat system (DONE)

---

## Overview

Nuclear launch is a 4-phase multi-player action. Phase 2 (authorization) is quiet — round continues normally. Phase 3 (flight) pauses the round timer and shows global alert. Phase 4 (resolution) is dramatic on the public screen with map-based impact visualization.

---

## Phase 1: INITIATION (Launcher HoS)

**Where:** Nuclear Launch action in Military category (HoS only)

**UI Flow:**
1. Dark themed panel (same style as Nuclear Test)
2. Status: nuclear_level, confirmed, deployed missiles
3. Map (75%): click target hex(es)
4. Sidebar (25%): deployed missile units, click to select + assign target
5. Review: missile→target pairs
6. Confirm → creates nuclear_action record

**Constraints:**
- Must have `nuclear_confirmed = true`
- Missiles must be active + deployed (not reserve/embarked)
- T1/T2: exactly 1 missile
- T3: any number of deployed missiles (1, 2, 3, ...)
- Range: T1≤2, T2≤4, T3 global

---

## Phase 2: AUTHORIZATION (timer configurable: 40s test / 10 min prod)

**Round timer KEEPS RUNNING** — the world doesn't know yet.

### Launcher's screen:
- Status panel (not full-screen overlay): "Awaiting authorization..."
- Per-authorizer status: ⏳ → ✓ / ✗
- On all authorized → brief "LAUNCH AUTHORIZED" notification
- On any rejection → "LAUNCH CANCELLED"

### Authorizers' screens:
- **Actions Expected Now:** Red urgent card "⚠ NUCLEAR LAUNCH AUTHORIZATION"
- Click → dark panel: target(s), missile count, timer, AUTHORIZE / REJECT buttons

### Auto-cancel on timer expiry.

---

## Phase 3: FLIGHT + INTERCEPTION (timer: 40s test / 10 min prod)

**Round timer PAUSES.** This is the dramatic moment.

### ALL participants' screens — persistent top banner:
```
⚠ BALLISTIC MISSILE LAUNCH DETECTED — [COUNTRY]
[N] MISSILES INBOUND — Impact in [MM:SS]
```
- Red background, same position as moderator proxy banner
- Real countdown to impact (reads timer from nuclear_actions)
- Stays until Phase 4 resolution

### T3+ countries:
- **Actions Expected Now:** "⚠ NUCLEAR INTERCEPTION DECISION"
- Click → dark panel: launch details, AD count, 25% per AD probability
- INTERCEPT / DECLINE buttons + rationale

### Target country:
- Banner + "Air defense systems engaging automatically" (50% per AD)

### T3 HoS + military: auto-generated classified artefact with launch details

### Auto-decline on timer expiry (no interception).

---

## Phase 4: RESOLUTION

### Public Screen — dramatic map-based visualization:
- Global map zooms/highlights impact area
- Per-missile results on map:
  - INTERCEPTED: brief flash, no marker
  - IMPACT: ☢ dark red pulsing marker appears at hex
- Damage summary overlay:
  - Units destroyed count
  - GDP impact %
  - Nuclear site destroyed (if applicable)
- T3 salvo effects: global stability drop, leader fate

### Participant screens:
- Banner changes: "NUCLEAR STRIKE RESOLVED" (fades after 30s)
- Map shows ☢ markers at impact hexes
- Observatory event in feed

### Round timer RESUMES after resolution.

---

## Technical Architecture

### Timer:
- `nuclear_actions.timer_started_at` + `timer_duration_sec`
- Configurable: `sim_runs.schedule.nuclear_auth_timer_sec` (default 600, test 40)
- Configurable: `sim_runs.schedule.nuclear_flight_timer_sec` (default 600, test 40)
- Server checks deadline on each submission
- Frontend polls status every 2s

### Global Banner (Phase 3):
- All clients subscribe to `nuclear_actions` via Realtime
- `status = 'awaiting_interception'` → show banner with countdown
- `status = 'resolved'` → show "RESOLVED" then fade

### Round Timer Pause (Phase 3 only):
- On launch authorized → auto-pause sim (set status=paused, store resume state)
- On resolution → auto-resume sim

### Orchestrator Migration:
- `_resolve_launch()` writes to `deployments` table (not unit_states_per_round)
- Field mapping: unit_id↔unit_code, country_id↔country_code, unit_status↔status
- Delete destroyed unit rows from deployments

### Actions Expected Now:
- Authorization: nuclear_actions where status='awaiting_authorization' + role matches
- Interception: nuclear_actions where status='awaiting_interception' + country is T3+

---

## Missile Count Rules

| Tier | Max Missiles | Range |
|------|-------------|-------|
| T1 (level 1) | 1 | ≤2 hexes |
| T2 (level 2) | 1 | ≤4 hexes |
| T3 (level 3+) | unlimited (all deployed) | global |

---

## Configurable Parameters

| Parameter | Test | Production |
|-----------|------|-----------|
| Auth timer | 40s | 600s (10 min) |
| Flight timer | 40s | 600s (10 min) |
| Auto-cancel on auth expiry | Yes | Yes |
| Auto-decline on flight expiry | Yes | Yes |

---

## Files to Create/Modify

| File | Change |
|------|--------|
| `ParticipantDashboard.tsx` | NuclearLaunchForm, AuthorizationPanel, InterceptionPanel, global flight banner |
| `PublicScreen.tsx` | Map-based impact visualization, dramatic resolution overlay |
| `FacilitatorDashboard.tsx` | Nuclear event card |
| `map-core.js` | ☢ impact markers (reuse existing) |
| `nuclear_chain.py` | Migrate to deployments table, timer config from sim_runs |
| `main.py` | Nuclear status endpoint, auto-pause on launch |
| `sim_run_manager.py` | Pause/resume for nuclear events |

---

*APPROVED by Marat 2026-04-18. Build can proceed.*
