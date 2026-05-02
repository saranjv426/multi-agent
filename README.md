# MultiAgentSystem

Roof Design Validation System is a full-stack application for uploading roof plan images or PDFs, extracting relevant drawing panels, and generating AI-assisted Florida Building Code roof compliance reports.

## What This Project Includes

- FastAPI backend for upload handling, authentication, document extraction, AI validation, PDF report generation, and API routes.
- Next.js frontend for login/signup, file upload, model selection, validation progress, and report viewing/downloading.
- Multi-provider model configuration for OpenAI-compatible routes, including GPT and Mistral-style endpoints.
- Local development database fallback using `backend/local_dev.db` when PostgreSQL is not available.
- Automated tests for auth, CORS, database setup, PDF generation, document extraction, OpenAI compatibility, and validation report formatting.

## Recent Fixes And Verification

- Removed build-time dependency on Google Fonts so `npm run build` works in offline or network-restricted environments.
- Fixed Next.js App Router viewport metadata warning.
- Replaced hard-coded PDF fixture paths with repository-relative paths.
- Fixed PDF/drawing extraction edge cases for synthetic PDFs, title-based wall section crops, letter-spaced titles, and multi-panel detail rows.
- Improved validation report normalization so missing required sections are filled, accepted framing/sheathing notes are promoted consistently, and risky compliant claims are downgraded when evidence is incomplete.
- Added retry behavior for empty length-truncated AI validation responses.

Verified locally:

```bash
cd backend
conda run -n agent_env pytest
# 92 passed

cd ../frontend
npm run build
# build passed
```

## Requirements

- Conda or another Python environment manager
- Python 3.11 recommended for the current local test environment
- Node.js and npm
- At least one configured AI provider API key

## Backend Setup

```bash
conda create -n agent_env python=3.11 -y
conda activate agent_env
cd backend
pip install -r requirements.txt
cp env.example .env
```

Edit `backend/.env` and set at least:

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MAIN_MODEL=gpt-5
OPENAI_SUMMARY_MODEL=gpt-5-mini
JWT_SECRET_KEY=replace_with_a_long_random_secret
HOST=127.0.0.1
PORT=8000
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
LOCAL_DATABASE_URL=sqlite:///./local_dev.db
ENABLE_SQLITE_FALLBACK=true
```

If `DATABASE_URL` is not available or PostgreSQL cannot be reached in development, the backend can use SQLite at `backend/local_dev.db`.

Start the backend:

```bash
conda activate agent_env
cd backend
python start.py
```

Backend URLs:

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

## Frontend Setup

In a second terminal:

```bash
cd frontend
npm install
printf "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000\n" > .env.local
npm run dev
```

Frontend URL:

- App: `http://localhost:3000`

## Daily Run Commands

Terminal 1:

```bash
conda activate agent_env
cd backend
python start.py
```

Terminal 2:

```bash
cd frontend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 npm run dev
```

Then open `http://localhost:3000`.

## Test And Build Commands

Backend:

```bash
cd backend
conda run -n agent_env pytest
```

Frontend production build:

```bash
cd frontend
npm run build
```

Frontend development server:

```bash
cd frontend
npm run dev
```

## Important Notes

- Keep API keys and secrets in `.env` files only. Do not commit real secrets.
- The uploaded document can be an image or PDF. PDFs may be split into multiple drawing crops before validation.
- For multi-drawing PDFs, the backend prioritizes wall-section/title-based crops when available.
- `start.sh` exists as an interactive helper, but the two-terminal commands above are the clearest and most reliable local workflow.
- Some backend warnings remain from dependencies and FastAPI startup event deprecations; the current test suite still passes.
