"""
DD Intelligence Assistant — FastAPI Backend
GCP Lean Stack: Cloud SQL (pgvector) + cachetools + Gemini API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from api_services.core.config import settings
from api_services.core.database import init_db
from api_services.routers import search, reports, chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Starting DD Intelligence Assistant API")
    await init_db()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="DD Intelligence Assistant",
    description="Due diligence automation platform for French companies",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.1.0"}
