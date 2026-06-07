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

## Infrastructure (planned + current)
- **Docker Compose (`infra/docker-compose.yml`)**
  - **PostgreSQL** (`postgres:16`) as the database (Neon).
  - **Backend** container (FastAPI) with `DATABASE_URL` pointing to Postgres.
  - **Frontend** container (Next.js) with `NEXT_PUBLIC_API_BASE_URL` pointing to the backend.
  - Persistent Postgres data via the `fit_track_ai_pgdata` volume.

Future infra ideas (mentioned in code comments):
- JWT refresh token rotation
- Redis caching
- Additional components for scalability (to be added later)

## Dev Notes
Backend runs on `http://localhost:8000`.
Frontend runs on `http://localhost:3000`.

### API base paths
- API is mounted under `/api/v1`.
- Healthcheck is available at `GET /health`.

### JWT auth
- Auth endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`.
- Protected endpoints expect `Authorization: Bearer <access_token>`.

### UUID fix (important)
The backend uses UUID columns (`uuid.UUID`) for `user_id` in `FoodEntry`, `DailyMetric`, and `Workout`.
JWT `sub` values are decoded as strings, so `get_current_user_id()` now converts `sub` to `uuid.UUID` before returning it.
This prevents SQLAlchemy errors like `AttributeError: 'str' object has no attribute 'hex'` when filtering by `user_id`.

### Endpoints (high level)
- Dashboard: `GET /api/v1/dashboard`
- Foods: `POST /api/v1/foods`, `GET /api/v1/foods`, `GET /api/v1/foods/summary`, `DELETE /api/v1/foods/{entry_id}`
- Weights: `POST /api/v1/weights`, `GET /api/v1/weights/history`
- Workouts: `POST /api/v1/workouts`, `GET /api/v1/workouts`



