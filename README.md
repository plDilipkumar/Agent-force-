# AgentForge — AI Engineering Workspace

AgentForge provides structured engineering plans and reviewable code/test artifacts through a React + TypeScript frontend and FastAPI API.

## Live services
- Frontend: https://agentforge-inky.vercel.app
- API: https://agentforge-api-ina0.onrender.com
- Health: https://agentforge-api-ina0.onrender.com/health

## Multi-provider AI routing
The API tries configured providers once each, in this order: Gemini, Cloudflare Workers AI, then OpenRouter. A timeout, network error, rate limit, HTTP failure, or malformed response moves to the next configured provider. There are no unbounded retry loops. If every configured provider fails, the API returns a sanitized error; provider credentials and response bodies are not logged. Gemini remains supported and does not need to be recreated.

## Render environment variables
Configure these on the Render backend service under **Environment**. Add secret values directly in Render, not GitHub, the frontend, or chat.

| Variable | Purpose | Default / notes |
| --- | --- | --- |
| GEMINI_API_KEY | Gemini credential | Existing server-side key |
| GEMINI_MODEL | Gemini model | gemini-3.8-flash; use a model enabled for the key |
| CLOUDFLARE_ACCOUNT_ID | Cloudflare account ID | Required with Cloudflare token |
| CLOUDFLARE_API_TOKEN | Cloudflare Workers AI token | Required; keep secret |
| CLOUDFLARE_MODEL | Workers AI model identifier | @cf/meta/llama-3.1-8b-instruct; confirm current availability |
| OPENROUTER_API_KEY | OpenRouter credential | Required for OpenRouter |
| OPENROUTER_MODEL | OpenRouter model identifier | openrouter/free; model availability may change |
| OPENROUTER_SITE_URL | OpenRouter attribution URL | Optional; defaults to production frontend |
| FRONTEND_ORIGIN | Single-origin fallback | http://localhost:5173 |
| FRONTEND_ORIGINS | Exact comma-separated CORS allowlist | Production frontend and optional local origin |

Each provider is optional; at least one must be configured. Cloudflare requires both account ID and token. The health endpoint reports provider names only, never secret values. After saving environment changes in Render, wait for the service restart/deploy and confirm /health lists the configured providers.

## Local development
Backend:
```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Frontend:
```bash
cd frontend
npm install
npm run dev
```
Use VITE_API_BASE_URL for the API URL if needed. Never use a VITE_* variable for provider secrets.

## API
- GET /health: health and configured provider names.
- POST /api/run: structured plan with specifications, prioritized tasks, decisions, risks, verification checklist, and assumptions.
- POST /api/artifacts: generated Python source plus pytest suggestion; returns verification_status=not_executed.
- Input/output limits, typed validation, provider failover, and bounded request timeouts.

## Safety and current limitations
- Generated source is untrusted and is not executed inside the API process. Review before use.
- Suggested tests and verification checklists are not evidence that tests have executed.
- Preview sign-in is not real identity-provider authentication and must not imply an account was created.
- No durable database-backed run history or usage analytics are implemented.
- Production deploy status must be verified independently from CI.

## Render deployment
Build: `pip install -r requirements.txt`
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
Vercel root: `frontend`; build: `npm run build`; output: `dist`.

## Smoke checks
```bash
curl -i https://agentforge-api-ina0.onrender.com/health
curl -i -X POST https://agentforge-api-ina0.onrender.com/api/run \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://agentforge-inky.vercel.app' \
  --data '{"task":"Design a secure document upload API","context":"PDF files up to 10 MB","stack":"FastAPI + React","mode":"balanced"}'
```
