# CLAUDE.md — Frontend Rules

**Scope:** All code under `/app/frontend/`. Subordinate to `/app/CLAUDE.md` and root CLAUDE.md.

---

## Language & Framework

- React 18+ with TypeScript (strict mode)
- Vite for build and dev server
- Tailwind CSS with TTT custom theme
- Zustand for state management
- Supabase Realtime for live data subscriptions

## Visual Standards — SEED H1 UX Style Guide

The H1 style guide (`2 SEED/`) is the visual source of truth. Do not improvise.

### Typography
- **Headings:** Playfair Display (serif, geopolitical gravitas)
- **Body text:** DM Sans (clean, modern, readable)
- **Data/numbers:** JetBrains Mono (monospace, dashboard precision)

### Colors
- **Country colors:** Each of the 21 countries has a designated primary + secondary color defined in H1. These are non-negotiable — they ensure visual consistency across map, panels, and charts.
- **Theme:** Dark background (`#0A0E1A` or similar from H1), high contrast text, subtle borders
- **Semantic colors:** Success (green), warning (amber), danger (red), info (blue) — defined in H1

### Layout Principles
- Large-screen primary (Public Display on projector/TV)
- Mobile-first for Participant Interface (Phase 3, future)
- Grid-based layouts, generous spacing, no clutter
- Information hierarchy: most important data largest and most prominent

## State Management

- **Zustand** for client state (UI state, selected filters, active panels)
- **Supabase Realtime** for server state (game state, round data, events)
- Never duplicate server state in client store — subscribe and render directly
- Optimistic updates only where latency is noticeable and rollback is safe

## Real-Time Data

- Subscribe to Supabase Realtime channels for all live game data
- Never poll. All updates are push-based.
- Handle connection drops gracefully: reconnect + full state refresh
- Channel naming convention: `game:{game_id}:state`, `game:{game_id}:events`

## Component Architecture

Build reusable components before composing pages:

| Component | Purpose |
|-----------|---------|
| `HexTile` | Single hex on the map, with country color, unit count, zone info |
| `HexMap` | Full hex grid with zoom/pan, click handlers, overlays |
| `CountryPanel` | Country summary: name, flag color, GDP, military, stability |
| `EventCard` | Single event in the timeline feed |
| `MetricBar` | Horizontal bar for comparative metrics |
| `RoundIndicator` | Current round display with phase info |

## File Structure

```
frontend/
├── CLAUDE.md            ← THIS FILE
├── index.html
├── vite.config.ts
├── tailwind.config.ts   ← TTT theme tokens (from H1)
├── src/
│   ├── App.tsx
│   ├── components/      ← Reusable UI components
│   ├── pages/           ← Page-level components (PublicDisplay, etc.)
│   ├── stores/          ← Zustand stores
│   ├── services/        ← Supabase client, Realtime subscriptions
│   ├── types/           ← Shared TypeScript types
│   └── theme/           ← Font imports, color constants, Tailwind extensions
└── public/
    └── fonts/           ← Self-hosted font files
```

## Data Freshness Rule — NO MANUAL REFRESH

**Users must NEVER need to refresh the page to see updated data.** This is a core UX requirement.

**Full specification:** `MODULES/M2_REALTIME/SPEC_REALTIME_DATA_STANDARDS.md` — the canonical source for all Realtime patterns, table requirements, connection resilience, and cross-browser testing requirements. Read it before writing any frontend code that displays data.

**Key rules:**
- Every table the frontend reads MUST have `REPLICA IDENTITY FULL` + be in `supabase_realtime` publication
- One-time fetches (`useEffect + fetch, [])`) are FORBIDDEN for changeable data
- Every feature MUST be tested on Safari (desktop + iOS) for tab-switch resilience

Every page that shows data which changes in the background MUST use Supabase Realtime:

| Pattern | When to use | Hook |
|---------|-------------|------|
| **Realtime table** | Lists that change (sim runs, events, sessions, actions) | `useRealtimeTable(table, simId, options)` |
| **Realtime row** | Single records that change (sim state, agent session) | `useRealtimeRow(table, id)` |
| **Direct channel** | Global data without sim_run_id (e.g., all sim runs) | `supabase.channel().on('postgres_changes', ...).subscribe()` |
| **Fallback poll** | Supplement to realtime (not replacement). 15-30s minimum. | `setInterval(refetch, 15000)` |

```tsx
// WRONG — stale on mount, requires manual refresh:
useEffect(() => { fetchData().then(setData) }, [])

// RIGHT — live updates via Supabase Realtime:
const { data, loading } = useRealtimeTable('observatory_events', simId, {
  orderBy: 'created_at.desc', limit: 50,
})

// RIGHT — global table (no simId filter):
useEffect(() => {
  loadData()
  const ch = supabase.channel('my-channel')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'sim_runs' }, () => loadData())
    .subscribe()
  return () => { supabase.removeChannel(ch) }
}, [])
```

**Reference implementations:**
- `FacilitatorDashboard.tsx` — comprehensive realtime (useRealtimeTable for 6+ tables)
- `PublicScreen.tsx` — realtime + 30s fallback poll (resilience pattern)
- `ModeratorDashboard.tsx` — direct channel for global sim_runs list

**Infrastructure:**
- `hooks/useRealtimeTable.ts` — initial fetch + INSERT/UPDATE/DELETE streaming
- `hooks/useRealtimeRow.ts` — single-row subscription
- `lib/channelManager.ts` — deduplication + ref counting (prevents resource exhaustion)

## Key References

| Spec | Content |
|------|---------|
| SEED H1 | UX Style Guide — colors, fonts, layout, country palette |
| SEED G1-G5 | Web app screen specifications |
| SEED C1 | Global hex map data (JSON) |
| SEED C3 | Theater map data (JSON) |
