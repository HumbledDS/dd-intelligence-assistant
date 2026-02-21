"""
Lean DINUM adapter — direct aiohttp calls to recherche-entreprises.api.gouv.fr
Free, 400 req/min, no API key required.
"""

import logging
import aiohttp
from typing import Any

from api_services.core.config import settings

logger = logging.getLogger(__name__)

DINUM_BASE = settings.DINUM_API_URL
HEADERS = {"Accept": "application/json", "User-Agent": "DD-Intelligence-Assistant/2.1"}


async def dinum_search(query: str, limit: int = 25) -> list[dict]:
    """Search companies by name or SIREN (free, no key required)."""
    params = {"q": query, "limite": limit}
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(
            f"{DINUM_BASE}/search", params=params, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("results", [])


async def dinum_get_company(siren: str) -> dict[str, Any]:
    """
    Get a full company profile by SIREN — includes:
    - Identité légale (RNE + SIRENE)
    - Tranche d'effectifs
    - Convention collective (IDCC)
    - Ratios financiers (si disponibles)
    """
    params = {"q": siren, "limite": 1}
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(
            f"{DINUM_BASE}/search", params=params, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            results = data.get("results", [])
            if not results:
                raise ValueError(f"Entreprise introuvable pour le SIREN {siren}")
            return results[0]


async def dinum_get_dirigeants(siren: str) -> list[dict]:
    """
    Fetch dirigeant list for a company from the DINUM /dirigeants endpoint.
    Returns [] if the endpoint is unavailable or returns no data.
    """
    url = f"{DINUM_BASE}/dirigeants"
    params = {"siren": siren}
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 404:
                    return []
                if resp.status != 200:
                    logger.warning(f"DINUM dirigeants: HTTP {resp.status} for {siren}")
                    return []
                data = await resp.json()
                return data.get("results", data if isinstance(data, list) else [])
        except Exception as e:
            logger.warning(f"DINUM dirigeants fetch failed for {siren}: {e}")
            return []


async def dinum_get_finances(siren: str) -> dict[str, Any]:
    """
    Fetch financial ratios / key indicators from DINUM.
    Returns {} if not available (many SMEs don't publish).
    """
    url = f"{DINUM_BASE}/finances"
    params = {"siren": siren}
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
                return data.get("results", data) if not isinstance(data, list) else {}
        except Exception as e:
            logger.warning(f"DINUM finances fetch failed for {siren}: {e}")
            return {}
