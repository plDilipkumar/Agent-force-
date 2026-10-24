# AgentForge — AI Engineering Workspace

AgentForge is an AI-assisted engineering workspace that turns a project brief into a structured implementation plan and reviewable code/test drafts. It uses a React + TypeScript frontend, a FastAPI backend, PostgreSQL-backed accounts and saved work, and a multi-provider AI workflow.

**Live application:** https://agentforge-inky.vercel.app  
**Backend API:** https://agentforge-api-ina0.onrender.com  
**Health endpoint:** https://agentforge-api-ina0.onrender.com/health

## What it does

- Generates structured engineering plans with specifications, prioritized tasks, architecture decisions, risks, verification steps, and assumptions.
- Uses separate AI workers for different planning responsibilities, then merges their structured outputs into a single plan.
- Supports an independent review pass when the reviewer provider is configured.
- Generates reviewable Python source and pytest drafts.
- Provides AI chat, account authentication, profile, and saved plans/artifacts.
- Handles partial provider failures, bounded retries/timeouts, input limits, and structured-output validation.
- Keeps generated code reviewable: the API does not execute user-requested or model-generated source code.

## Multi-provider orchestration

The planning workflow is designed around **task decomposition by role**, not simply sending the same prompt to one model and returning its answer.

1. **Parallel planning workers:** Cloudflare Workers AI receives an implementation-planning role focused on ordered tasks, acceptance criteria, and verification. OpenRouter receives an independent security/reliability role focused on edge cases, failure handling, risks, and assumptions.
2. **Structured response validation:** Worker responses are parsed and checked for required fields and valid task/decision structures. Cloudflare gets one bounded retry when its response does not meet the required structure.
3. **Result aggregation:** Successful worker outputs are merged, with duplicate items removed and list sizes capped. If one worker fails, the workflow retains successful contributions and reports the partial failure in the returned provider/status description. If every generation worker fails, the API returns a service error instead of presenting an empty result as success.
4. **Independent review:** When Gemini is configured, it reviews the merged plan for correctness, missing tests, security, and consistency. If the review times out or returns invalid output, the generated plan is retained and the response identifies that review was unavailable.
5. **Separate code-draft flow:** Code-artifact generation uses bounded sequential provider fallback, rather than the parallel planning-worker workflow. The result includes generated source and suggested tests; it is marked as not executed.

This approach lets different models contribute specialized perspectives while keeping the orchestration logic, validation, failure handling, and merging under the application's control. The system does not assume that a model response is correct just because it is valid JSON.

## Architecture

~~~text
React + TypeScript (Vercel)
        |
        | HTTPS / JSON API
        v
FastAPI backend (Render)
        |
        +--> Parallel planning workers
        |       +--> Cloudflare Workers AI: implementation plan
        |       +--> OpenRouter: security and reliability review
        |
        +--> Structured validation and result aggregation
        |
        +--> Optional Gemini review of merged plan
        |
        +--> Bounded code-artifact provider fallback
        |
        +--> PostgreSQL (Aiven): accounts and saved work
~~~

- **Frontend:** React, TypeScript, Vite.
- **Backend:** Python, FastAPI, Pydantic, HTTPX.
- **Persistence:** PostgreSQL through asyncpg; account and saved-work tables are initialized by the backend.
- **Authentication:** password hashes use scrypt; signed bearer tokens are issued by the backend. Use a strong private AUTH_SECRET_KEY in production.
- **Deployment:** Vercel for the frontend, Render for the API, Aiven PostgreSQL for persistence.
- **Testing:** pytest backend suite, frontend production build, and CI sandbox smoke checks.

## API overview

- GET /health — health status and configured provider names; does not return secret values.
- POST /api/run — generates a structured engineering plan.
- POST /api/artifacts — generates a Python source draft and pytest suggestion with verification_status=not_executed.
- POST /api/auth/register and POST /api/auth/login — account registration and sign-in.
- GET /api/saved-work — retrieves the authenticated user's saved plans and artifacts.
- PUT /api/saved-work/{item_type}/{item_id} — saves or updates a plan/artifact.
- DELETE /api/saved-work/{item_type}/{item_id} — deletes the authenticated user's saved item.

Check the backend routes for current request/response schemas and validation rules.

## Environment variables

Set secret values directly in the Render backend service under **Environment**. Do not commit secrets to GitHub or place provider credentials in frontend variables.

| Variable | Purpose | Notes |
| --- | --- | --- |
| GEMINI_API_KEY | Gemini credential | Keep server-side |
| GEMINI_MODEL | Gemini model | Must be available to the configured key |
| CLOUDFLARE_ACCOUNT_ID | Cloudflare account ID | Required for Workers AI |
| CLOUDFLARE_API_TOKEN | Cloudflare Workers AI token | Secret |
| CLOUDFLARE_MODEL | Workers AI model identifier | Must be available for the account |
| OPENROUTER_API_KEY | OpenRouter credential | Secret |
| OPENROUTER_MODEL | OpenRouter model identifier | Availability depends on the provider |
| OPENROUTER_SITE_URL | OpenRouter attribution URL | Optional |
| DATABASE_URL | PostgreSQL connection URL | Use TLS/SSL in production |
| AUTH_SECRET_KEY | Token-signing secret | At least 32 characters; keep private |
| FRONTEND_ORIGIN | Single allowed frontend origin fallback | Local-development fallback |
| FRONTEND_ORIGINS | Comma-separated CORS allowlist | Use exact trusted origins |
| VITE_API_BASE_URL | Frontend API base URL | Public URL only; never a provider secret |

Provider availability and free-tier limits can change. At least one supported generation provider must be configured for generation; Cloudflare requires both account ID and token. Review the health endpoint after changing backend environment variables and allow the service to restart.

## Local development

Backend:

~~~bash
cd backend
python -m venv .venv
# Activate the virtual environment, then:
pip install -r requirements.txt
uvicorn app.main:app --reload
~~~

Frontend:

~~~bash
cd frontend
npm install
npm run dev
~~~

Use frontend/.env.example to configure VITE_API_BASE_URL for local development. For a real authenticated local session, configure a PostgreSQL database and a private DATABASE_URL and AUTH_SECRET_KEY for the backend.

## Testing and verification

Run backend tests:

~~~bash
cd backend
pip install -r requirements.txt
pytest -q
~~~

Build the frontend:

~~~bash
cd frontend
npm install
npm run build
~~~

GitHub Actions runs the backend tests and frontend build. The isolated-artifact smoke workflow uses deterministic trusted fixtures to test the sandbox setup; this is **not** proof that AI-generated code has been executed or passed its suggested tests.

Production smoke checks:

~~~bash
curl -i https://agentforge-api-ina0.onrender.com/health
curl -i -X POST https://agentforge-api-ina0.onrender.com/api/run \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://agentforge-inky.vercel.app' \
  --data '{"task":"Design a secure document upload API","context":"PDF files up to 10 MB","stack":"FastAPI + React","mode":"balanced"}'
curl -i -X POST https://agentforge-api-ina0.onrender.com/api/artifacts \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://agentforge-inky.vercel.app' \
  --data '{"task":"Create a pure Python addition function and pytest cases","context":"No network or shell"}'
~~~

## Safety and known limitations

- Model outputs are untrusted suggestions and should be reviewed before use.
- Generated source and suggested tests are **not executed by the normal API workflow**. The response explicitly indicates that artifact verification has not been performed.
- A verification checklist is a proposed test plan, not evidence that those tests passed.
- Provider models, free-tier quotas, and availability may change. The workflow uses bounded timeouts/retries and can return partial results when a provider fails.
- A successful CI run or a deployment marked ready does not, by itself, prove every production integration works end to end.
- Restrict the PostgreSQL network allowlist to required sources where practical, use strong secrets, and never expose connection strings or API keys in client code, logs, screenshots, or commits.

## Deployment

- **Vercel:** set the project root to frontend, build command to npm run build, output directory to dist.
- **Render:** from backend, install with pip install -r requirements.txt and start with uvicorn app.main:app --host 0.0.0.0 --port $PORT.
- **Aiven:** provide the PostgreSQL connection URL through Render's DATABASE_URL environment variable and require TLS/SSL.

Always verify deployment status and run production smoke tests after a release.
