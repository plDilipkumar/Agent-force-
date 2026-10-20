# AgentForge — AI Engineering Workspace

AgentForge turns a software task into a reviewable engineering plan: product brief, implementation tasks, architecture decisions, risk register, and verification checklist. Gemini is used server-side when configured; a deterministic demo mode keeps the product usable without a key.

## Stack
- Frontend: React, TypeScript, Vite
- API: FastAPI, Pydantic
- AI: Google Gemini API (server-side only)
- CI: GitHub Actions (frontend build + backend tests)
- Deployment: Vercel frontend, Render API

## Run locally
### API
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Copy `.env.example` to `.env` and set `GEMINI_API_KEY` only if you want live AI. The backend runs in demo mode otherwise.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Set `VITE_API_BASE_URL` to the backend URL (default local API: http://localhost:8000).

## Deploy
1. Deploy the repository root as a Render Python web service: build command `pip install -r requirements.txt`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. The root entrypoint forwards to `backend/app/main.py`.
2. Deploy `frontend` as a Vercel Vite project with root directory `frontend`, build command `npm run build`, output directory `dist`. Set `VITE_API_BASE_URL` to the Render API URL and redeploy.
3. In Render, add `GEMINI_API_KEY` under the backend service's Environment settings. Never put the key in GitHub or any `VITE_*` variable.

## Product safety & honesty
- AgentForge produces plans and suggested artifacts; it does not execute arbitrary generated code.
- Every run labels its provider/mode. Demo-mode results are explicitly identified.
- The verification checklist is a plan, not a claim that tests were executed.
- Input and output lengths are bounded. API keys remain on the server.

## Reviewable code artifacts (feature branch)

The feature branch adds `POST /api/artifacts`, which asks Gemini for a bounded Python source file and a separate pytest file. The endpoint returns `verification_status: not_executed`; it does not run generated code inside the API process. A configured backend `GEMINI_API_KEY` is required for artifact generation; the deterministic planning demo remains available without it.

**Current limitation:** artifact execution in an isolated CI sandbox is not yet part of the verified end-to-end workflow. Treat generated files as untrusted suggestions and review them before use. Do not interpret the suggested pytest file or verification checklist as evidence that tests have run.


## Environment variables

Configure these values on the backend service (Render), not in the frontend bundle:

| Variable | Purpose | Example / default |
| --- | --- | --- |
| `GEMINI_API_KEY` | Server-side Gemini credential; leave empty for deterministic planning demo mode | Secret value in Render |
| `GEMINI_MODEL` | Gemini model identifier | `gemini-3.8-flash` (configured default; verify availability for your key) |
| `FRONTEND_ORIGIN` | Single-origin compatibility fallback | `http://localhost:5173` |
| `FRONTEND_ORIGINS` | Comma-separated allowlist used for browser CORS | `https://agentforge-inky.vercel.app,http://localhost:5173` |

Set `FRONTEND_ORIGINS` to the exact production frontend origin plus any development origin you need. Do not add a trailing path (for example, `/dashboard`) or use a wildcard. After changing Render environment variables, redeploy/restart the API and verify preflight requests from the deployed frontend origin.

## Smoke checks

Replace the API URL if your Render service uses a different hostname:

```bash
curl -i https://agentforge-api-ina0.onrender.com/health
curl -i -X OPTIONS https://agentforge-api-ina0.onrender.com/api/run \
  -H 'Origin: https://agentforge-inky.vercel.app' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type'
curl -i -X POST https://agentforge-api-ina0.onrender.com/api/run \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://agentforge-inky.vercel.app' \
  --data '{"task":"Design a bounded file upload API with validation","stack":"FastAPI + React","mode":"balanced"}'
```

A successful `/health` response alone does not verify CORS or the task workflow. The preflight response must include `Access-Control-Allow-Origin: https://agentforge-inky.vercel.app`; the POST should return a structured plan. Without a configured Gemini key, the plan is deterministic demo output. Artifact generation requires Gemini and returns `verification_status: not_executed`.

## Explicit limitations

- No durable database-backed run history or usage metrics are implemented; run IDs and durations are returned per request only.
- Generated Python and suggested pytest files are not executed by the API. Do not treat `not_executed` as a successful verification result.
- A manual GitHub Actions workflow, `.github/workflows/isolated-artifact-check.yml`, has been added on the feature branch to run supplied source/tests in a separate Docker container with no network, a read-only root filesystem, a read-only artifact mount, non-root UID, dropped Linux capabilities, no-new-privileges, and CPU/memory/PID limits. It has not yet been exercised end-to-end or merged to `main`; treat it as unverified until a reviewed merge and a successful sandbox run. The API itself never executes generated code. Never execute generated artifacts on the web server.
- Public deployment state and live browser integration must be verified separately from CI and are not implied by a green build.


### Isolated artifact verification (feature branch)

After the workflow is reviewed and merged into `main`, open GitHub Actions → **AgentForge isolated artifact check** → **Run workflow**. Supply the source filename, base64-encoded source, test filename, and base64-encoded pytest file. Each decoded file is limited to 12 KB and filenames are validated. The workflow has read-only repository permissions and passes no application credentials into the sandbox. A passing run means only that the submitted tests passed inside that constrained container; it does not prove the artifact is secure or correct for every use.
