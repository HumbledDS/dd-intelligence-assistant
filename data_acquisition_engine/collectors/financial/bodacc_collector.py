"""BODACC announcements collector (data.gouv.fr — free)."""

import logging
import aiohttp

from api_services.core.config import settings

logger = logging.getLogger(__name__)

BODACC_BASE = settings.BODACC_API_URL


class BodaccCollector:
    async def get_announcements(self, siren: str, limit: int = 20) -> list[dict]:
        """Fetch recent legal announcements for a company."""
        url = f"{BODACC_BASE}/catalog/datasets/bodacc-a/records"
        params = {
            "where": f'siret like "{siren}%"',
            "limit": limit,
            "order_by": "dateparution desc",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        logger.warning(f"BODACC returned {resp.status} for SIREN {siren}")
                        return []
                    data = await resp.json()
                    return [r["record"]["fields"] for r in data.get("records", [])]
            except Exception as e:
                logger.error(f"BODACC fetch failed for {siren}: {e}")
                return []
