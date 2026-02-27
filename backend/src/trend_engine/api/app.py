"""FastAPI application — lifecycle, CORS, and route registration."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from trend_engine.db.client import close_http_client, init_http_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage shared httpx.AsyncClient lifecycle."""
    logger.info("Trend Engine starting — initializing HTTP client")
    await init_http_client()
    yield
    logger.info("Trend Engine shutting down — closing HTTP client")
    await close_http_client()


app = FastAPI(
    title="Trend Intelligence Engine",
    description=(
        "Momentum detection system over a semantic corpus. "
        "Detects structural shifts in technical ecosystems via "
        "HDBSCAN clustering, temporal modeling, and trend scoring."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints
from trend_engine.api.endpoints import router  # noqa: E402

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    from trend_engine.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "trend_engine.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
