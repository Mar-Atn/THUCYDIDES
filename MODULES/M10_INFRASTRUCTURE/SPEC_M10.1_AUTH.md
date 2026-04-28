# M10.1 — Authentication Module SPEC

**Version:** 1.2 | **Date:** 2026-04-28
**Status:** DONE — Updated: GDPR consent for Google OAuth, auto-redirect for participants
**KING source:** `/Users/marat/CODING/KING/app/src/contexts/AuthContext.tsx`, `pages/Login.tsx`, `pages/Register.tsx`, `components/ProtectedRoute.tsx`, `supabase/migrations/00001_*.sql`, `00006_rls_policies.sql`

---

## 1. What This Module Does

Auth is the front door to the entire application. It answers three questions:
1. **Who are you?** (login / registration)
2. **What can you do?** (moderator vs participant)
3. **Where do you go?** (redirect to the right dashboard)

No other module works without this one. Every page, every API call, every real-time subscription depends on the user's identity and role.

---

## 2. Two User Types

| | Moderator | Participant |
|---|---|---|
| **Who** | Game designer, facilitator — runs the simulation | Player — leads a country or holds a role in the SIM |
| **How they register** | Signs up, but CANNOT use the system until confirmed by an existing moderator | Self-registers freely, no approval needed |
| **What they see after login** | Pre-SIM Dashboard: template editor, scenario config, sim-run management, user management, system settings | Participant Dashboard: "Welcome, you're registered. You'll be assigned a role by the moderator before the simulation starts." |
| **Max rights?** | Yes — can see everything, change everything, assign roles, control rounds | No — sees only what their assigned role allows |

**Important distinction:** A "participant" who just registered is NOT yet playing. They become an active participant of a specific simulation only when the moderator assigns them a role. Until then, they're just a registered user waiting in the lobby.

---

## 3. How People Get In

### 3a. Sign Up (new user)

**Screen: Registration Page**

Fields:
- Display name (how they'll appear in the SIM)
- Email
- Password (with confirmation)
- Role selection: **"I'm a Moderator"** / **"I'm a Participant"**

If they choose **Participant** → account created immediately, redirected to participant dashboard.

If they choose **Moderator** → account created with status `pending_approval`. They see a waiting screen: *"Your moderator account is pending approval. An existing moderator will confirm your access."* An existing moderator sees them in User Management and can approve or reject.

**Google sign-in option** available as alternative to email/password.

**Data consent (GDPR)** — required for ALL sign-up paths:
- Data storage and processing (Supabase)
- AI processing of simulation data (Claude, Gemini)
- Voice recording during the SIM (if applicable)

**Implementation (2026-04-28):**
- DB trigger `handle_new_user` creates users with `data_consent=FALSE`
- Standard registration: consent modal shown in Register form → `grantConsent()` called after sign-up
- Google OAuth: user created without consent → `ProtectedRoute` consent gate shows `DataConsentModal` on first access → user accepts → `grantConsent()` writes TRUE to DB
- If authenticated user has no `public.users` row (e.g. deleted then re-login): AuthContext auto-creates profile with `data_consent=FALSE` → consent flow triggers

This is a hard gate — no consent, no access to any protected route.

### 3b. Sign In (returning user)

**Screen: Login Page**

- Email + password
- "Sign in with Google" button
- "Forgot password?" link → sends reset email
- "Don't have an account? Register" link

After successful login → redirect based on role:
- Moderator → Pre-SIM Dashboard
- Participant → Participant Dashboard

### 3c. Session Management

- JWT-based (Supabase Auth handles this automatically)
- Token auto-refreshes — user stays logged in across browser sessions
- Session persists in localStorage
- Sign out clears everything

---

## 4. What the Database Stores

### Users table (new — TTT-specific)

```
users
├── id              — links to Supabase auth system (UUID)
├── email           — unique
├── display_name    — shown in the SIM
├── avatar_url      — optional, for future use
├── system_role     — 'moderator' or 'participant'
├── status          — 'registered', 'pending_approval', 'active', 'suspended'
├── data_consent    — true/false (GDPR gate)
├── consent_given_at — timestamp
├── last_login_at   — timestamp
├── preferences     — JSON (UI preferences, future use)
├── created_at      — timestamp
└── updated_at      — timestamp
```

**Status lifecycle:**

For participants:
```
registered → active (immediate — self-service)
```

For moderators:
```
pending_approval → active (requires existing moderator to approve)
```

Both can be moved to `suspended` by a moderator at any time.

### First moderator problem

The very first moderator has no one to approve them. Solution: **the first user who registers as moderator is auto-approved.** After that, every moderator needs confirmation.

---

## 5. Row-Level Security (RLS)

This is the enforcement layer. Even if someone hacks the frontend, the database itself refuses to show data they shouldn't see.

**Users table policies:**
- You can always read your own profile
- Moderators can read all user profiles
- Only moderators can update another user's status (approve, suspend)
- You can update your own profile (display name, avatar, preferences)

**Helper functions (reusable across all future modules):**
- `is_moderator()` — checks if current user has system_role = 'moderator'
- `get_user_role_in_sim(sim_id)` — returns the user's assigned role in a specific simulation (used by M6+)

These functions are the building blocks for ALL future RLS policies. Every table we add in later modules will reference them.

---

## 6. Frontend Pages

All pages follow the TTT UX style guide (SEED_H1_UX_STYLE_v2):
- **Typography:** Playfair Display (headings), DM Sans (body), JetBrains Mono (data)
- **Colors:** Light theme default ("Strategic Paper" — #F5F6F8 base)
- **Tone:** "The Economist meets McKinsey" — clean, authoritative, no flashy elements

### Page List

| Page | Route | Auth Required? | Description |
|---|---|---|---|
| **Login** | `/login` | No | Email/password + Google + links to register/reset |
| **Register** | `/register` | No | Sign-up form with role selection + consent |
| **Reset Password** | `/reset-password` | No | Email input → sends reset link |
| **Update Password** | `/update-password` | No | New password form (after clicking reset link) |
| **Moderator Dashboard** | `/dashboard` | Yes (moderator) | Stub — will be built in M9. Shows: "Welcome, [name]. Simulation setup coming soon." |
| **Participant Dashboard** | `/participant` | Yes (participant) | Stub — will be built in M6. Shows: "Welcome, [name]. You'll be assigned a role when the simulation begins." |
| **Pending Approval** | `/pending` | Yes (moderator, pending) | "Your moderator account is pending approval." |

### Protected Route Logic

Every protected page goes through this sequence:
```
Loading? → Show spinner
Not logged in? → Redirect to /login
No data consent? → Show consent modal (accept or sign out)
Wrong role? → Show "Access Denied"
Pending approval? → Redirect to /pending
All clear → Show the page
```

---

## 7. Backend (FastAPI) Changes

Auth adds a thin layer to the Python backend:

### New: Auth middleware
- Reads JWT from request headers
- Verifies with Supabase
- Extracts user identity + role
- Makes it available to all endpoint handlers via `Depends(get_current_user)`

### New: Protected endpoint pattern
```python
# Before (any anonymous client can call this):
@app.get("/api/sim/{sim_id}/countries")
async def get_countries(sim_id: str): ...

# After (only authenticated users):
@app.get("/api/sim/{sim_id}/countries")
async def get_countries(sim_id: str, user: AuthUser = Depends(get_current_user)): ...

# Moderator-only:
@app.get("/api/admin/users")
async def list_users(user: AuthUser = Depends(require_moderator)): ...
```

### New endpoints

| Endpoint | Method | Who | What |
|---|---|---|---|
| `/api/admin/users` | GET | Moderator | List all registered users |
| `/api/admin/users/{id}/approve` | POST | Moderator | Approve a pending moderator |
| `/api/admin/users/{id}/suspend` | POST | Moderator | Suspend a user |
| `/api/auth/me` | GET | Any authenticated | Get own profile + role |

Note: Login, registration, password reset are handled entirely by Supabase Auth + the React frontend. The Python backend doesn't need login endpoints — it just validates the JWT that Supabase issues.

---

## 8. What This Module Does NOT Do

To keep scope clean, the following are **explicitly out of scope** for M10.1:

| Out of Scope | Which Module Handles It |
|---|---|
| Assigning users to SIM roles (Dealer, Shield, etc.) | M9 (Sim Setup) |
| SIM-specific permissions (who can see what country data) | M9 + M6 |
| Template / scenario / sim-run management screens | M9 |
| Participant's role dashboard, action submission | M6 |
| Public screen display | M8 |
| AI participant identity | M5 |
| Real-time WebSocket subscriptions to game state | M4+ |
| Magic link (passwordless) login | Postponed — revisit if needed before launch |

---

## 9. Acceptance Criteria

M10.1 is DONE when:

- [x] A new user can register as participant (email/password or Google) ✅
- [x] A new user can register as moderator → auto-approved if first, pending otherwise ✅
- [x] An existing moderator can approve a pending moderator (API endpoint) ✅
- [x] Login works (email/password and Google) ✅
- [x] Password reset works ✅
- [x] After login, moderators land on moderator dashboard (stub) ✅
- [x] After login, participants land on participant dashboard (stub) ✅
- [x] Unauthenticated users are redirected to /login on any protected route ✅
- [x] Data consent: full GDPR modal (5 sections, declaration, checkbox) ✅
- [x] RLS policies on users table (8 policies + 2 helper functions) ✅
- [x] FastAPI endpoints protected with JWT middleware ✅
- [x] All pages follow TTT UX style (Playfair/DM Sans/JetBrains Mono, Strategic Paper theme) ✅
- [x] L1 tests pass for auth middleware (11 tests) ✅
- [x] L2 test: manual registration → login → dashboard redirect verified by Marat ✅

---

## 10. Design Heritage

This spec draws from and is consistent with:

| Document | What It Provides |
|---|---|
| **CON_G1** Web App Architecture (frozen) | 3-layer platform model, access levels, RLS concept |
| **DET_D1** Tech Stack | Supabase Auth, JWT claims, magic link rationale |
| **DET_B1** Database Schema | Users table structure, facilitators table, RLS policy matrix |
| **SEED_G** Web App Spec | 4 user types, role-based visibility, authorization chains |
| **SEED_H1** UX Style v2 | Visual design system (colors, typography, emblem system) |
| **KING** Auth implementation | Complete working reference for Supabase Auth + React + RLS |

### Deviations from Design Heritage

1. **Magic link postponed.** DET_D1 specifies magic link as primary login. We're starting with email/password + Google (proven in KING) and adding magic link later if the executive audience demands it. Rationale: faster to ship, proven pattern, same Supabase Auth — can be added in a day.

2. **`admin` access level deferred.** CON_G1 specifies 4 levels (participant, moderator, spectator, admin). For now, moderator = admin. We'll split them if multi-organization support is needed. `spectator` will be added in M8 (Public Screen).

3. **`facilitators` table deferred.** DET_B1 defines a per-SIM facilitators table. Not needed until M9 — for now, `system_role = 'moderator'` on the users table is sufficient.

---

## 11. Resolved Questions (Marat, 2026-04-13)

| # | Question | Decision |
|---|----------|----------|
| Q1 | First moderator bootstrap | **Auto-approve first moderator.** All subsequent moderators require approval. |
| Q2 | Participant registration | **Open.** Anyone can self-register as participant, no invitation needed. |
| Q3 | Google OAuth in v1 | **Yes.** Include Google sign-in from the start. |
| Q4 | Display Name vs Full Name | **Keep "Display Name."** We don't require real names. |

### Additional decisions:
- **No magic link** — email/password + Google is sufficient
- **Two levels only** — moderator and participant. No admin, no spectator (spectator comes in M8)
- **Dashboard stubs are minimal** — moderator and participant dashboards are just landing patches in M10.1, real content comes in M9 and M6 respectively

---

## 12. Delivery Summary (2026-04-13)

### What was built

| Layer | Files | Details |
|---|---|---|
| **Database** | 1 migration (applied live) | 6 new columns on users, 8 RLS policies, 2 helper functions, 2 triggers (auto-approve + updated_at) |
| **Backend** | 3 Python files + main.py updated | `auth/models.py`, `auth/dependencies.py` (JWT middleware), 4 new API endpoints |
| **Frontend** | 20 files (full React app initialized) | Vite + TS + Tailwind, AuthContext, ProtectedRoute, 7 pages, DataConsentModal, TTT theme tokens |
| **Tests** | 1 file, 11 tests | L1 auth model tests — all passing |
| **Infra** | Google OAuth + Supabase Auth | Google Cloud project created, OAuth consent screen, credentials, Supabase provider enabled |

### External setup completed
- Supabase project `lukcymegoldprbovglmn` — users table extended, RLS live, email confirmation disabled
- Google Cloud project `THUCYDIDES` — OAuth 2.0 credentials, authorized origins (localhost + metagames.academy)
- Frontend runs at `localhost:5174`, proxies API to FastAPI at `localhost:8000`

### First user
- marat@metagames.academy — moderator, active (auto-approved as first moderator)
