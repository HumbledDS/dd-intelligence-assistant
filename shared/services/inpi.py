"""
INPI (entreprises.api.fr) adapter — official French business registry.
Free API, no key required.
Provides: dirigeants certifiés, actes officiels, conventions collectives.
"""

import logging
import aiohttp
from typing import Any

logger = logging.getLogger(__name__)

INPI_BASE = "https://entreprises.api.fr"


async def inpi_get_company(siren: str) -> dict[str, Any]:
    """
    Get official company data from INPI via entreprises.api.fr.
    Returns dirigeants, actes, conventions collectives, subventions.
    Falls back to {} if unavailable.
    """
    url = f"{INPI_BASE}/v3/composition"
    params = {"siren": siren}
    headers = {
        "Accept": "application/json",
        "User-Agent": "DD-Intelligence-Assistant/2.1",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                url, params=params, headers=headers,
                timeout=aiohttp.ClientTimeout(total=12)
            ) as resp:
                if resp.status == 404:
                    logger.info(f"INPI: SIREN {siren} not found")
                    return {}
                if resp.status != 200:
                    logger.warning(f"INPI: HTTP {resp.status} for {siren}")
                    return {}
                return await resp.json()
        except Exception as e:
            logger.warning(f"INPI fetch failed for {siren}: {e}")
            return {}


async def inpi_get_dirigeants(siren: str) -> list[dict]:
    """Get certified dirigeant list from INPI."""
    url = f"{INPI_BASE}/v3/dirigeants"
    params = {"siren": siren}
    headers = {
        "Accept": "application/json",
        "User-Agent": "DD-Intelligence-Assistant/2.1",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                url, params=params, headers=headers,
                timeout=aiohttp.ClientTimeout(total=12)
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return data if isinstance(data, list) else data.get("results", [])
        except Exception as e:
            logger.warning(f"INPI dirigeants failed for {siren}: {e}")
            return []
