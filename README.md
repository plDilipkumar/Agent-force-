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
1. Deploy `backend` as a Render Python web service: root directory `backend`, build command `pip install -r requirements.txt`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. Deploy `frontend` as a Vercel Vite project with root directory `frontend`, build command `npm run build`, output directory `dist`. Set `VITE_API_BASE_URL` to the Render API URL and redeploy.
3. In Render, add `GEMINI_API_KEY` under the backend service's Environment settings. Never put the key in GitHub or any `VITE_*` variable.

## Product safety & honesty
- AgentForge produces plans and suggested artifacts; it does not execute arbitrary generated code.
- Every run labels its provider/mode. Demo-mode results are explicitly identified.
- The verification checklist is a plan, not a claim that tests were executed.
- Input and output lengths are bounded. API keys remain on the server.
