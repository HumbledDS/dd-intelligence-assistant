"""
Async PostgreSQL database setup (SQLAlchemy + asyncpg).
Also creates tables on startup.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from api_services.core.config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Alias used by embedder and other internal callers
async_session_factory = AsyncSessionLocal


class Base(DeclarativeBase):
    pass


async def init_db():
    """
    Create all tables and ensure pgvector extension exists.
    In development, gracefully skips if no database is reachable.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")
    except Exception as e:
        from api_services.core.config import settings
        if settings.ENVIRONMENT == "development":
            logger.warning(
                f"[DEV] Database not available — starting without DB. "
                f"Set DATABASE_URL and run PostgreSQL to enable persistence. Error: {e}"
            )
        else:
            raise


async def get_db():
    """FastAPI dependency: async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
