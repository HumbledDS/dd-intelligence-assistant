"""Infogreffe adapter — financial & legal data (paid API)."""

import logging
import aiohttp
from typing import Any

from api_services.core.config import settings

logger = logging.getLogger(__name__)


async def infogreffe_get_company(siren: str) -> dict[str, Any]:
    """Get financial and legal data from Infogreffe (bilans, actes)."""
    if not settings.INFOGREFFE_API_KEY:
        logger.warning("INFOGREFFE_API_KEY not set — returning empty data")
        return {}

    url = f"https://opendata-rncs.intr.fr/api/data/actes/{siren}"
    headers = {
        "Authorization": f"Bearer {settings.INFOGREFFE_API_KEY}",
        "Accept": "application/json",
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return {}
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientResponseError as e:
            logger.warning(f"Infogreffe error {e.status} for SIREN {siren}")
            return {}
        except Exception as e:
            logger.error(f"Infogreffe fetch failed: {e}")
            return {}
