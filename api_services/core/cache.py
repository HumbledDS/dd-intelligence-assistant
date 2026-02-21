"""
Two-level cache:
  L1 — cachetools TTLCache (RAM, per-instance, fast)
  L2 — PostgreSQL cache_entries table (persistent, shared across instances)
  
When PostgreSQL is unavailable (dev mode without DB), L2 operations are
silently skipped — only L1 RAM cache is used.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from cachetools import TTLCache
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api_services.core.config import settings

logger = logging.getLogger(__name__)

# L1: in-process cache (per Cloud Run instance)
_l1: TTLCache = TTLCache(
    maxsize=settings.CACHE_MAX_SIZE,
    ttl=settings.CACHE_DEFAULT_TTL,
)

# TTL per source type (seconds) — used for L2 PostgreSQL cache
SOURCE_TTL: dict[str, int] = {
    "dinum":        30 * 24 * 3600,   # 30 days
    "insee":        30 * 24 * 3600,
    "infogreffe":   7  * 24 * 3600,   # 7 days
    "bodacc":       1  * 3600,        # 1 hour
    "news":         30 * 60,          # 30 minutes
}


async def get_cached(key: str, db: Optional[AsyncSession]) -> Optional[Any]:
    """Check L1 then L2 cache. Silently skips L2 if DB is unavailable."""
    # L1
    if key in _l1:
        logger.debug(f"L1 cache HIT: {key}")
        return _l1[key]

    # L2 — skip gracefully if no DB session or DB unavailable
    if db is None:
        return None
    try:
        row = await db.execute(
            text("SELECT value FROM cache_entries WHERE cache_key = :k AND expires_at > NOW()"),
            {"k": key},
        )
        result = row.fetchone()
        if result:
            logger.debug(f"L2 cache HIT: {key}")
            value = json.loads(result[0]) if isinstance(result[0], str) else result[0]
            _l1[key] = value  # warm L1
            return value
    except Exception as e:
        logger.debug(f"L2 cache read skipped (DB unavailable): {e}")

    return None


async def set_cached(
    key: str,
    value: Any,
    source_type: str,
    db: Optional[AsyncSession],
) -> None:
    """Store in L1 (RAM) and L2 (PostgreSQL). Silently skips L2 if DB unavailable."""
    ttl_seconds = SOURCE_TTL.get(source_type, 3600)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    # L1 — always works
    _l1[key] = value

    # L2 — skip gracefully if no DB
    if db is None:
        return
    try:
        await db.execute(
            text("""
                INSERT INTO cache_entries (cache_key, value, expires_at, source_type)
                VALUES (:k, :v, :exp, :src)
                ON CONFLICT (cache_key) DO UPDATE
                  SET value = EXCLUDED.value,
                      expires_at = EXCLUDED.expires_at,
                      source_type = EXCLUDED.source_type,
                      created_at = NOW()
            """),
            {
                "k": key,
                "v": json.dumps(value, ensure_ascii=False),
                "exp": expires_at,
                "src": source_type,
            },
        )
        await db.commit()
    except Exception as e:
        logger.debug(f"L2 cache write skipped (DB unavailable): {e}")


async def invalidate(key: str, db: Optional[AsyncSession]) -> None:
    """Remove entry from both cache levels."""
    _l1.pop(key, None)
    if db is None:
        return
    try:
        await db.execute(
            text("DELETE FROM cache_entries WHERE cache_key = :k"), {"k": key}
        )
        await db.commit()
    except Exception as e:
        logger.debug(f"L2 cache invalidate skipped: {e}")


async def cleanup_expired(db: AsyncSession) -> int:
    """Delete expired L2 entries — call periodically."""
    try:
        result = await db.execute(
            text("DELETE FROM cache_entries WHERE expires_at < NOW()")
        )
        await db.commit()
        count = result.rowcount
        if count:
            logger.info(f"Cache cleanup: removed {count} expired entries")
        return count
    except Exception:
        return 0
