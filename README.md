# https://fit-track-ai-ultimate.vercel.app

🚀 **Fit Track AI** is a smart **multi-user Protein & Weight Tracker**. It helps you map your weekly diet matrix, then log real daily meals and weight to see clear progression trends over time.

---

## 🚀 PROJECT OVERVIEW
A smart multi-user Protein & Weight Tracker designed to map a weekly diet matrix and log real-time daily metrics. Your data stays separated per user, with authenticated access via secure HTTP-only cookies.

Live production app: **https://fit-track-ai-ultimate.vercel.app**

---

## 🛠️ TECH STACK
- **Backend:** FastAPI (Python)
- **Database:** Turso (Edge SQLite over HTTP via **libsql**)
- **ORM Layer:** SQLAlchemy
- **Frontend:** Jinja2 Templates + Vanilla CSS + Chart.js (no heavy front-end frameworks)
- **Deployment:** Vercel Cloud Platform

---

## 📂 CORE FEATURES
- **Secure Multi-User Authentication** (HTTP-only cookies + secure password hashing)
- **Dynamic Weekly Diet & Workout Matrix Planner** (organized chronologically by day)
- **Daily Meal & Macro Tracker** (log meals, calculate real-time protein totals)
- **Weight Logs Tracker** (track weight over time and view progression trends)

---

## ⚡ QUICK START SETUP
### 1) Clone & create a virtual environment
```bash
git clone <your-repo-url>
cd fit_track_ai
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure environment variables
Create a `.env` file in the project root:

```bash
# Required for Turso (multi-user backend storage)
TURSO_DATABASE_URL=libsql://your-turso-database-url
TURSO_AUTH_TOKEN=your-turso-auth-token

# Used to sign session cookies
SESSION_SECRET=your-long-random-secret
```

> If you don’t set Turso variables, the app falls back to local SQLite.

### 4) Run the app
```bash
uvicorn app:app --reload
```

Open the app at: **http://127.0.0.1:8000**

