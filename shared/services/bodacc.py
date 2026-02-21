"""BODACC adapter — legal announcements (free, data.gouv.fr)."""

import logging
import aiohttp

from api_services.core.config import settings

logger = logging.getLogger(__name__)


async def bodacc_get_announcements(siren: str, limit: int = 20) -> list[dict]:
    """Fetch recent legal announcements (BODACC) for a company by SIREN."""
    url = f"{settings.BODACC_API_URL}/catalog/datasets/bodacc-a/records"
    params = {
        "where": f'registre like "{siren}%"',
        "limit": limit,
        "order_by": "dateparution desc",
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [r.get("record", {}).get("fields", r) for r in data.get("records", [])]
        except Exception as e:
            logger.error(f"BODACC fetch failed for {siren}: {e}")
            return []
