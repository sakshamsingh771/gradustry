# Gradustry — AI-Powered Academia–Industry Skill Intelligence Platform

## Fix report (registration / login / blank opportunities page)

Root cause found and fixed — the FastAPI backend was **crashing on startup**
in any fresh setup, which is why registration, login, and the opportunities
page all appeared broken at once (there was nothing wrong with any of those
features individually; the API simply wasn't running).

1. **Backend crash on startup — `CORS_ORIGINS` config parsing** (`backend/app/core/config.py`)
   *Root cause:* `CORS_ORIGINS` was typed `List[str]` in the pydantic-settings
   `Settings` model. pydantic-settings auto-JSON-decodes env values for any
   complex-typed (list/dict) field *before* custom validators run. The
   shipped `.env.example` sets `CORS_ORIGINS=http://localhost:5173`, a plain
   string, not JSON — so `json.loads("http://localhost:5173")` raised
   `SettingsError` and the app never started (`alembic upgrade head`,
   `uvicorn app.main:app`, and `docker compose up` all failed identically).
   *Fix:* `CORS_ORIGINS` is now stored as a raw `str`, with parsing into a
   list moved to a `cors_origins` property (used in `app/main.py`), which
   isn't subject to pydantic-settings' complex-type auto-decoding. Still
   accepts a single origin, a comma-separated list, or a JSON array.
   **Status: FIXED.**

2. **Docker Compose frontend couldn't reach the backend at all** (`frontend/Dockerfile`, `frontend/nginx.conf` — new)
   *Root cause:* the frontend API client (`src/lib/api.ts`) calls relative
   paths like `/api/auth/login`. In local dev, Vite's dev-server proxy
   forwards those to the backend — but the production Docker image built a
   static bundle and served it with `serve -s dist`, which does **no**
   proxying. Every `/api/...` call from the browser 404'd (or fell through
   to `index.html`), so `docker compose up --build` reproduced exactly the
   reported symptoms even with the config bug above fixed.
   *Fix:* the frontend's production image now serves the build behind
   **nginx** instead of `serve`, with `nginx.conf` proxying `/api/` to the
   `backend` container and falling back to `index.html` for client-side
   routes. `npm run dev` is unaffected (still uses Vite's own proxy).

3. **`vite.config.ts` dev proxy hardcoded to the Docker service name**
   *Root cause:* the dev-server proxy target was hardcoded to
   `http://backend:8000` (only resolvable inside the Docker network), which
   silently breaks `npm run dev` outside Docker — the documented "local dev
   without Docker" path just above.
   *Fix:* now defaults to `http://localhost:8000` (matches this README) and
   can be overridden via `VITE_API_PROXY_TARGET` if needed.

**Testing performed:** clean venv + `alembic upgrade head` + `python -m
app.seed` + `uvicorn`, then registration, login (all 4 seeded roles),
`GET /api/opportunities` (blank-page endpoint), hybrid opportunity matching,
apply, applications list, skill passport, and skill-gap report — all
verified directly against the running API and through the Vite dev proxy
(`npm run build` also passes). Everything else (AI fallbacks, roadmap,
evidence, assessments, admin/college/industry routes) was left untouched —
only the startup/connectivity bugs above were changed.


An SIH-ready MVP implementing the core loop:

**Evidence → Skill Passport → Skill Gap Engine → Gap Closure Roadmap → Assessment/Re-assessment → Explainable Opportunity Matching → Industry Feedback → updated Skill Passport.**

...now upgraded with a genuine AI layer: **AI Resume Analyzer, AI GitHub Analyzer, AI-assisted Evidence review, Adaptive AI Assessment, AI Personalized Roadmap, Hybrid (deterministic + AI) Opportunity Matching, a transparent Career Readiness score, and an AI Career Copilot** — all with deterministic fallbacks, so the platform is fully functional whether or not an AI API key is configured.

Roles: **Student, College, Industry, Super Admin** — each with a dedicated profile, dashboard, and RBAC-scoped API access.

## Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS v4 + shadcn-style components + React Router + TanStack Query + Framer Motion. Full dark/light/system theme.
- **Backend:** FastAPI + SQLAlchemy + Alembic + JWT auth + RBAC. Modular AI services with a vendor-agnostic provider abstraction (Gemini/OpenAI via env vars) and deterministic fallbacks for every feature.
- **Database:** SQLite by default (zero setup) or PostgreSQL (via Docker Compose).

## Quickest path: Docker Compose (Postgres, full stack)

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173
- The backend auto-seeds demo data on first boot.

## Local dev without Docker (SQLite, fastest for iterating)

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head        # creates the schema
python -m app.seed          # adds demo accounts + sample data
uvicorn app.main:app --reload --port 8000
```

**Frontend** (in a second terminal)
```bash
cd frontend
npm install
npm run dev
```
Vite is pre-configured to proxy `/api` to `http://localhost:8000`. Open http://localhost:5173.

## Turning on real AI (optional)

By default `AI_PROVIDER=none` in `.env` — every AI feature below runs on its deterministic fallback, and the UI honestly labels each result "Standard analysis" instead of "AI analysis" via `GET /api/ai/status`.

To enable real LLM calls, set in `backend/.env`:
```
AI_PROVIDER=gemini            # or "openai"
AI_API_KEY=your-key-here
AI_MODEL=gemini-2.0-flash     # or e.g. gpt-4o-mini
```
No code changes needed. If the key is missing, the call times out, rate-limits, or returns malformed JSON, the app silently falls back — it never crashes and never fakes an AI response.

## Demo logins (seeded)

| Role     | Email                     | Password    |
|----------|---------------------------|-------------|
| Student  | student@gradustry.dev     | student123  |
| College  | college@gradustry.dev     | college123  |
| Industry | industry@gradustry.dev    | industry123 |
| Admin    | admin@gradustry.dev       | admin123    |

The demo student (Aarav Sharma) already has evidence, computed proficiency scores, and a career goal of "Backend Developer" — log in as them to see the full loop populated immediately.

## AI features — what's real, what's the fallback

Every feature below has been tested end-to-end in fallback mode (no API key). With `AI_API_KEY` set, the same endpoints route through the configured LLM instead, validated through Pydantic before being trusted.

| Feature | Endpoint | AI path | Deterministic fallback |
|---|---|---|---|
| **Resume Analyzer** | `POST /api/ai/resume/analyze` | LLM extracts structured skills/education/experience from resume text | Keyword-matching extractor against a known skill vocabulary |
| **GitHub Analyzer** | `POST /api/ai/github/analyze` | LLM adds architecture/complexity narrative on top of real GitHub API data | Real GitHub API data (languages, README, dependency files) → deterministic tech + complexity detection. **This part is always real**, AI or not. |
| **Evidence Intelligence** | `POST /api/ai/evidence/{id}/analyze` | LLM scores relevance/consistency of an evidence description | Lexical-overlap heuristic |
| **Adaptive Assessment** | `POST /api/ai/assessment/adaptive/start`, `/next` | LLM generates each question targeted at the student's weak topic | Existing static question bank, filtered by topic |
| **AI Roadmap** | `POST /api/ai/roadmap/generate` | LLM builds a personalized week-by-week plan from actual scores/gaps | Existing per-skill template roadmap generator, stitched across all current gaps |
| **Hybrid Opportunity Matching** | `GET /api/opportunities/matches/for-me` | LLM recognizes related/adjacent skills and explains the match in plain language | Deterministic eligibility + weighted scoring (unchanged) + a synonym-cluster fallback (e.g. Django/Flask ~ FastAPI) |
| **Career Readiness** | `GET /api/ai/insights` | — (always deterministic, by design — "not a black box") | Weighted formula: Skills 35%, Assessments 20%, Evidence 15%, Projects 15%, Industry feedback 10%, Consistency 5% |
| **Career Copilot** | `POST /api/ai/copilot/chat` | LLM answers in natural language from a context object built from the student's real data | Template-based answer built from the exact same context object — never fabricates, says so if data is missing |

Adaptive assessment, evidence, and copilot results are never trusted blindly: LLM JSON output is parsed through Pydantic schemas in `app/ai/schemas/ai_schemas.py`; a validation failure triggers the fallback path automatically.

**Known environment limitation:** the GitHub Analyzer calls the real `api.github.com`, which rate-limits unauthenticated requests per IP (60/hour) — shared sandbox IPs can hit this quickly. Set `GITHUB_TOKEN` in `.env` to raise the limit for real deployments.

## What's intentionally scoped down for the MVP

Deferred (structure exists to extend into them later): Faculty role, curriculum-intelligence comparison, OCR-based certificate parsing, pgvector semantic search, real-time notifications/messaging, Google OAuth (UI placeholder present, not wired), and multi-turn conversational memory in the Career Copilot (each question is answered independently from fresh context, not a running conversation).

## Repo layout

```
backend/
  app/ai/              AI provider abstraction, all AI + deterministic engines, prompts/, schemas/
  app/models/           SQLAlchemy models (core + ai.py for AI-specific tables)
  app/routers/ai.py     All /api/ai/* endpoints
  alembic/              Migrations
  app/seed.py           Demo data
frontend/
  src/pages/student/    Resume/GitHub analyzers, Adaptive Assessment, AI Roadmap, Career Copilot, dashboards
docker-compose.yml       Full stack with Postgres
```
