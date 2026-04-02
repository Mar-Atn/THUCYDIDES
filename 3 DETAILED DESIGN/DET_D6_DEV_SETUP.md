# DET D6 — Development Environment Setup
**Version:** v1.0 | **Date:** 2026-04-01 | **Status:** ACTIVE
**Owner:** LEAD
**Cross-references:** [DET_D1_TECH_STACK](DET_D1_TECH_STACK.md) | [app/CLAUDE.md](../app/CLAUDE.md) | [LLM_MODELS.md](../app/config/LLM_MODELS.md)

---

## 1. Prerequisites

| Tool | Version | Check command |
|------|---------|---------------|
| **Node.js** | 20+ (LTS) | `node -v` |
| **npm** | 10+ | `npm -v` |
| **Python** | 3.11+ | `python3 --version` |
| **pip** | latest | `pip3 --version` |
| **Git** | 2.40+ | `git --version` |
| **Supabase CLI** | latest | `supabase --version` |

Optional but recommended:
- **VS Code** with extensions: Python, ESLint, Tailwind CSS IntelliSense, Prettier
- **Vercel CLI** (`npm i -g vercel`) for deployment previews

---

## 2. Clone & Install

```bash
git clone <repo-url> THUCYDIDES
cd THUCYDIDES
```

---

## 3. Environment Variables

Copy the template and fill in values (get keys from Marat or the team vault):

```bash
cp .env.example .env
```

**Required variables:**

| Variable | Description |
|----------|-------------|
| `SUPABASE_PROJECT_ID` | Supabase project identifier |
| `SUPABASE_URL` | Full Supabase API URL (`https://<project-id>.supabase.co`) |
| `SUPABASE_ANON_KEY` | Supabase publishable/anon key (safe for client-side) |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (server-side only, NEVER expose to client) |
| `SUPABASE_DB_PASSWORD` | Direct database password (for migrations/admin tasks only) |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models (prefix `sk-ant-`) |
| `GOOGLE_AI_API_KEY` | Google AI API key for Gemini models (prefix `AIza`) |

**Phase 3+ (not required now):**

| Variable | Description |
|----------|-------------|
| `ELEVENLABS_API_KEY` | ElevenLabs API key for voice synthesis |
| `VERCEL_PROJECT_URL` | Vercel project dashboard URL (informational) |

**NEVER commit `.env` to git.** The `.env.example` file (no values) is committed.

---

## 4. Database — Supabase

The project uses a live Supabase instance at `lukcymegoldprbovglmn.supabase.co`. Seed data is already loaded.

**Verify connection:**

```bash
# Quick check via Supabase CLI
supabase db ping --project-ref lukcymegoldprbovglmn

# Or test from Python
python3 -c "
from supabase import create_client
import os
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_ANON_KEY'])
result = client.table('countries').select('*').limit(1).execute()
print(f'Connected. Rows: {len(result.data)}')
"
```

**Dashboard:** https://supabase.com/dashboard/project/lukcymegoldprbovglmn

Do NOT run destructive migrations without LEAD approval. All schema changes go through `supabase db push` from reviewed migration files.

---

## 5. Python Backend Setup

```bash
cd app/engine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run FastAPI dev server
uvicorn main:app --reload --port 8000
```

Server runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

**Python config access:** All environment variables are loaded via `pydantic-settings`. Do not use `os.getenv` directly — use the Settings class in `app/engine/config/`.

---

## 6. Frontend Setup

```bash
cd app/frontend

# Install dependencies
npm install

# Run Vite dev server
npm run dev
```

Dev server runs at `http://localhost:5173` with HMR enabled.

**TypeScript config access:** Environment variables accessed via `import.meta.env.VITE_*`. Only variables prefixed with `VITE_` are exposed to the client. Supabase anon key is safe to expose; service role key must NEVER be in frontend code.

---

## 7. Vercel Deployment

- **Auto-deploy:** Pushes to `main` trigger automatic Vercel deployment.
- **Preview deploys:** Every PR gets a preview URL automatically.
- **Manual deploy:** `vercel --prod` from the project root (requires Vercel CLI + auth).
- Environment variables are configured in the Vercel dashboard — do not rely on local `.env` for production.

---

## 8. LLM API Verification

Run these quick tests to confirm API access. See `app/config/LLM_MODELS.md` for full model reference.

**Anthropic (Claude):**

```python
# test_anthropic.py
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
msg = client.messages.create(
    model="claude-haiku-4-5-20251001",  # cheapest model for testing
    max_tokens=64,
    messages=[{"role": "user", "content": "Reply with 'TTT online'."}]
)
print(f"Claude: {msg.content[0].text}")
```

**Google (Gemini):**

```python
# test_gemini.py
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GOOGLE_AI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content("Reply with 'TTT online'.")
print(f"Gemini: {response.text}")
```

```bash
# Run both
source .env  # or export vars manually
python3 test_anthropic.py
python3 test_gemini.py
```

---

## 9. Common Issues / Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` in Python | Activate the venv: `source app/engine/venv/bin/activate` |
| Supabase connection refused | Check `SUPABASE_URL` has `https://` prefix. Verify project is not paused. |
| Vite env vars undefined | Only `VITE_`-prefixed vars are exposed. Restart dev server after `.env` changes. |
| CORS errors in browser | Backend must include frontend origin in allowed CORS origins. Check FastAPI middleware. |
| `401 Unauthorized` from Supabase | Anon key expired or wrong. Re-copy from Supabase dashboard > Settings > API. |
| LLM API returns 429 | Rate limit hit. Wait and retry. For batch testing use Anthropic Batch API (50% cheaper). |
| Port 8000/5173 already in use | Kill the existing process: `lsof -ti:8000 \| xargs kill` |
| `pip-compile` not found | Install: `pip install pip-tools` |
| Layer 1 tests fail after pull | Run `pip install -r requirements.txt` — dependencies may have changed. |
