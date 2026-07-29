# Freight Predict Hub

React 19 + Vite frontend and FastAPI backend for Indian Railways freight
analytics. The repository deploys as one Vercel project: static frontend files
are served from `frontend/dist`, and `/api/*` is handled by `api/index.py`.

## Local development

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn server:app --port 8000 --env-file .env
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

For local development, `frontend/.env` can use:

```env
VITE_API_URL=/api
VITE_DEV_API_TARGET=http://localhost:8000
```

## Vercel deployment

Set these Vercel Production environment variables:

- `VITE_API_URL=/api`
- `MONGO_URL` to a reachable MongoDB Atlas connection string
- `DB_NAME=railway_twin`
- `CORS_ORIGINS` to the production Vercel origin
- `EMERGENT_LLM_KEY` only when the optional AI insight endpoint is enabled

Do not enable `USE_MONGOMOCK` in production. Vercel supplies the HTTP listener,
so `PORT` is not required by the serverless deployment.

Deploy from this repository root:

```powershell
vercel.cmd --prod
```

The 34.31 MiB Parquet dataset is bundled into the Python function. The backend
also loads the full dataset, builds a graph, generates live-rake state, and
trains models during a cold start, so the first API response can take several
minutes.
