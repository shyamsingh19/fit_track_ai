# Fit Track AI (End-to-End MVP)

Monorepo:
- `backend/` — FastAPI + SQLAlchemy + Alembic + JWT
- `frontend/` — Next.js + TypeScript + Tailwind
- `infra/` — docker-compose

## Prerequisites
- Docker + docker-compose (recommended)
- Node.js (for frontend)
- Python 3.11+ (for local backend dev)

## Quickstart (Docker)
```bash
docker compose -f infra/docker-compose.yml up --build
```

## Dev Notes
Backend runs on `http://localhost:8000`.
Frontend runs on `http://localhost:3000`.

JWT auth is implemented; frontend should call `/auth/*` and store access token in memory.


