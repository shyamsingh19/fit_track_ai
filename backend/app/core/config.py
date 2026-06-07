from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str

    jwt_secret: str
    jwt_alg: str = "HS256"

    access_token_expires_minutes: int = 30
    refresh_token_expires_days: int = 7

    cors_origins: list[str] = ["http://localhost:3000"]

    # Future: refresh token rotation, Redis caching, etc.


# Allow importing app without env vars in dev tooling.
# MVP requirement: run without PostgreSQL using SQLite fallback.
import os

if os.getenv("DATABASE_URL"):
    # Strict mode: when using an external DB, require explicit JWT_SECRET.
    # This prevents accidentally running PostgreSQL with a dev secret.
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise RuntimeError(
            "JWT_SECRET environment variable is required when using a non-SQLite database."
        )

    settings = Settings(
        database_url=os.environ["DATABASE_URL"],

        jwt_secret=jwt_secret,
    )

else:
    # Local SQLite dev fallback
    settings = Settings(
        database_url="sqlite:///./fittrack.db",
        jwt_secret="dev-only-change-me",
    )








