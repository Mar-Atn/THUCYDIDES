# CLAUDE.md — app/ Build Standards

**Scope:** All code under `/app/`. Subordinate to root CLAUDE.md.

---

## Languages & Frameworks

- **Backend/Engines:** Python 3.11+, FastAPI, async handlers
- **Frontend:** TypeScript, React 18+, Vite
- **Database:** Supabase (PostgreSQL + Realtime + Edge Functions + Auth)
- **AI/LLM:** Dual provider — Gemini + Claude, centrally configurable. **See `app/config/LLM_MODELS.md` for current model IDs, pricing, and usage guide.** This file is the single source of truth for all LLM model references — update it when new models launch.

## Check KING First

Before building any module, review `/Users/marat/CODING/KING/app/` for reusable patterns. This is a strong recommendation — critically evaluate what fits, adapt what almost fits, build fresh only when necessary. Track all reuse decisions in `EVOLVING METHODOLOGY/KING_REUSE_LOG.md`.

## Commit Conventions

Prefix every commit message:
- `engine:` — Engine code (formulas, world model, resolution)
- `api:` — API endpoints, Supabase Edge Functions
- `frontend:` — React components, UI logic, styles
- `test:` — Test files, test infrastructure
- `fix:` — Bug fixes (append module: `fix(engine):`)
- `docs:` — Documentation updates
- `config:` — Configuration, environment, CI/CD

## Branch Strategy

- `main` — stable, passing all Layer 1 tests
- Feature branches: `feature/[sprint]-[module]-[description]` (e.g., `feature/s1-engine-economic`)
- PR required for merge to main. LEAD reviews.
- No force-pushes to main.

## File Organization

```
app/
├── CLAUDE.md              ← THIS FILE
├── engine/                ← Python: FastAPI services, engine modules
│   ├── CLAUDE.md
│   ├── main.py           ← FastAPI app entry point
│   ├── engines/          ← Individual engine modules
│   ├── models/           ← Pydantic models (DB, API, internal)
│   ├── services/         ← Business logic, AI services
│   └── config/           ← Settings, environment, LLM config
├── frontend/              ← TypeScript: React app
│   ├── CLAUDE.md
│   ├── src/
│   │   ├── components/   ← Reusable UI components
│   │   ├── pages/        ← Page-level components
│   │   ├── stores/       ← Zustand state stores
│   │   ├── services/     ← API clients, Realtime subscriptions
│   │   ├── types/        ← TypeScript type definitions
│   │   └── theme/        ← Tailwind config, color tokens, fonts
│   └── public/
└── tests/                 ← All test suites
    ├── CLAUDE.md
    ├── layer1/            ← Formula unit tests (pytest)
    ├── layer2/            ← Integration tests
    └── layer3/            ← AI simulation tests
```

## Centralized Configuration Pattern

Cross-cutting structural constants (map dimensions, theater linkage, country lists, coord conventions) live in **`app/<layer>/config/`** modules — one per language layer, kept in lock-step:

- Python: `app/engine/config/map_config.py` — THE source for map grids + theater linkage for engines.
- JS: `app/test-interface/static/map_config.js` — THE source for the same constants in the viewer/editor.

Rule: **never hardcode a dimension, coord mapping, or enum list at a call site**. Import from the config module. When a constant changes, both layers must be updated in the same commit (Principle Zero — fight entropy).

## Dependency Management

- **Python:** `requirements.txt` (pinned versions). Update via `pip-compile`.
- **Node:** `package.json` + `package-lock.json`. No floating versions.
- **Lock files committed.** Always.

## Environment Variables

- `.env` file for local development. NEVER committed to git.
- `.env.example` with all required variables (no values). Committed.
- Supabase keys, LLM API keys, feature flags — all via environment.
- Access in Python: `pydantic-settings`. Access in TypeScript: `import.meta.env`.

## Code Quality

- Python: type hints on all function signatures. Pydantic models for all data structures.
- TypeScript: strict mode. No `any` types except at API boundaries with explicit casting.
- No `print()` in Python — use `logging`. No `console.log` in TypeScript production code.
- Every public function has a docstring (Python) or JSDoc comment (TypeScript).
