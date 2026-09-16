# GeM Bid Compliance Verification (SIH26100)

AI-assisted tool to check vendor documents against tender requirements, with
evidence, source page, and reasoning for every decision. This is a
verification aid, not an official GeM authority — uncertain cases are
flagged NEEDS_REVIEW rather than forced to a confident answer.

## Status: Phase 1 — Project Setup

At this stage the app only proves that the backend and frontend can talk to
each other. No auth, no database, no AI yet.

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (needed from Phase 2 onward, not required yet)

## Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and set `JWT_SECRET_KEY` to a real random value:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`DATABASE_URL` and `AI_API_KEY` can stay as placeholders for now — they're
not used until Phase 2 and Phase 6.

Run the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/api/health — you should see:
```json
{"status": "ok", "environment": "development"}
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 — the page should say
**"Backend says: ok (development)"**. If it says it can't reach the
backend, make sure the backend is running on port 8000.

## Project layout

See `backend/app/` for the FastAPI service (routes, services, AI layer,
document processing) and `frontend/src/` for the React app. Full
architecture notes live in project chat history / will be added to
`ARCHITECTURE.md` as phases progress.
