import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data" / "protein.db"))
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()

if TURSO_DATABASE_URL:
    if not TURSO_AUTH_TOKEN:
        raise RuntimeError(
            "TURSO_AUTH_TOKEN is required when TURSO_DATABASE_URL is configured"
        )
    if not TURSO_DATABASE_URL.startswith("libsql://"):
        raise RuntimeError("TURSO_DATABASE_URL must start with libsql://")
    
    print("Using Turso database at", TURSO_DATABASE_URL)
    engine = create_engine(
        f"sqlite+{TURSO_DATABASE_URL}?secure=true",
        connect_args={"auth_token": TURSO_AUTH_TOKEN},
        pool_pre_ping=True,
    )
else:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
