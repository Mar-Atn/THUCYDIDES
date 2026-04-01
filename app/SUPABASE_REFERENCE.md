# Supabase Reference — TTT Project
**Last checked:** 2026-04-01

## Project Details
- **Project:** THUKIDIDES
- **Project ID:** lukcymegoldprbovglmn
- **URL:** https://lukcymegoldprbovglmn.supabase.co
- **Region:** (set during creation)
- **Credentials:** See `.env` file (NOT committed to git)

## Client Library
- **Package:** `@supabase/supabase-js` v2.101.0 (latest)
- **No v3 yet** — v2 is current and stable
- **Requires:** Node.js 20+ (Node 18 support dropped in v2.79.0)
- **Install:** `npm install @supabase/supabase-js`

## Key Features Used
- **PostgREST:** Auto-generated REST API from schema
- **Realtime:** WebSocket subscriptions for live updates
- **Auth:** JWT-based with RLS enforcement
- **Storage:** File storage for maps, briefs, exports
- **Edge Functions:** Serverless functions (Deno runtime)

## Initialization Pattern
```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY  // Use anon key for client, service_role for server
)
```

## RLS Note
Automatic RLS is enabled — every new table gets RLS by default.
All data access goes through RLS policies. The `service_role` key
bypasses RLS (use only server-side, never in frontend).

## Documentation
- [JS API Reference](https://supabase.com/docs/reference/javascript/installing)
- [Realtime Guide](https://supabase.com/docs/guides/realtime)
- [RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Edge Functions](https://supabase.com/docs/guides/functions)
