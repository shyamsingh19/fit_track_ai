from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="Fit Track AI", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}


    @app.on_event("startup")
    def _startup() -> None:
        # MVP requirement: run without PostgreSQL/Docker by creating tables on startup.
        from app.db.init_db import init_db

        init_db()


    app.add_middleware(

        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()


