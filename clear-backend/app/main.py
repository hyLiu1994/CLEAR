# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
    )

    # CORS settings: Allow access to your front-end domain name
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Basic health check (convenient for K8s/docker/front-end self-test)
    @app.get("/health", summary="Health check")
    async def health_check():
        return {"status": "ok"}

    # Unified API v1 routing prefix
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()