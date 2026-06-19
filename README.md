# Protein Tracker

A small, single-user FastAPI application for manually tracking daily protein
and body weight. It uses two SQLite tables, server-rendered Jinja templates,
vanilla CSS, and Chart.js.

## Features

- Dashboard with protein averages, current weight, goal progress, recent meals,
  and a current-week summary
- Daily meal log with automatic totals, search, edit, and delete
- Weight history with change calculations, edit, and delete
- 30-day protein charts, weekly averages, weight trend, and goal adherence
- Configurable daily goal (defaults to `120` grams)
- No accounts, nutrition APIs, JavaScript framework, or background services

## Local setup

Python 3.12 is recommended.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>. The database is created automatically at
`data/protein.db`.

With `uv`:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
uv run uvicorn app:app --reload
```

## Configuration

Environment variables:

- `PROTEIN_GOAL=120` sets the daily protein target.
- `DATABASE_PATH=/absolute/path/protein.db` changes the SQLite file location.
- `SEED_SAMPLE_DATA=1` inserts sample data on startup only when no meals exist.
- `TURSO_DATABASE_URL=libsql://...` connects to a Turso database.
- `TURSO_AUTH_TOKEN=...` authenticates the Turso connection.

If the Turso variables are absent, the app automatically uses local SQLite.

## Turso setup

Install and authenticate the [Turso CLI](https://docs.turso.tech/cli/installation),
then create a database:

```bash
turso auth login
turso db create protein-tracker
turso db show --url protein-tracker
turso db tokens create protein-tracker
```

Copy `.env.example` to `.env` and fill in the URL and token:

```bash
cp .env.example .env
```

The app loads `.env` automatically. Start it normally:

```bash
uvicorn app:app --reload --port 8001
```

The application creates the two required tables in Turso automatically during
startup. Do not commit `.env` or expose the authentication token.

To add the included sample data manually:

```bash
python seed.py
```

## Render deployment

1. Push this project to GitHub.
2. In Render, create a **Web Service** from the repository.
3. Choose the Python runtime.
4. Set the build command to `pip install -r requirements.txt`.
5. Set the start command to:

   ```bash
   uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

6. Add these environment variables:

   ```text
   PYTHON_VERSION=3.12.8
   PROTEIN_GOAL=120
   TURSO_DATABASE_URL=libsql://your-database-your-org.turso.io
   TURSO_AUTH_TOKEN=your-token
   ```

7. Set the health-check path to `/health`.

### Important SQLite persistence note

As of June 2026, Render free web services use an ephemeral filesystem and
Render persistent disks are available only for paid services. Using Turso
solves this for the free tier because the database is stored remotely.

If you prefer local SQLite on Render, use a paid web service, attach a disk at
`/opt/render/project/src/data`, and set:

```text
DATABASE_PATH=/opt/render/project/src/data/protein.db
```

SQLite also means the service should run as one instance with one Uvicorn
worker. Back up `protein.db` periodically. If permanent free-tier persistence
is a strict requirement, deploy on a provider that currently includes a
persistent volume and set `DATABASE_PATH` to that mounted volume.

Render references:

- [Deploy a FastAPI app](https://render.com/docs/deploy-fastapi)
- [Persistent disks](https://render.com/docs/disks)
- [Free instances](https://render.com/docs/free)

Turso references:

- [Python quickstart](https://docs.turso.tech/sdk/python/quickstart)
- [SQLAlchemy integration](https://docs.turso.tech/sdk/python/orm/sqlalchemy)

## Data and calculations

- The 7-day, current-week, and current-month averages include zero for days
  without meals.
- Goal adherence is calculated across tracked days in the last 30 days.
- The current week's high and low include days elapsed so far, including days
  without entries.
- Weight change compares the latest two weight records.

## Project structure

```text
.
├── app.py
├── crud.py
├── database.py
├── models.py
├── schemas.py
├── seed.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── log.html
│   ├── weight.html
│   └── analytics.html
├── static/
│   └── style.css
└── data/
    └── protein.db  # created at runtime
```

## Production note

This app intentionally has no authentication. Do not expose it publicly if
untrusted people can reach the URL, because anyone with access can add, edit,
or delete entries.
