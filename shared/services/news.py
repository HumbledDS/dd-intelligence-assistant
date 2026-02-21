"""NewsAPI adapter — press coverage (paid, graceful when key absent)."""

import logging
import aiohttp

from api_services.core.config import settings

logger = logging.getLogger(__name__)


async def news_get_articles(company_name: str, page_size: int = 20) -> list[dict]:
    """Fetch recent news articles about a company."""
    if not settings.NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not set — skipping news collection")
        return []

    params = {
        "q": f'"{company_name}"',
        "language": "fr",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": settings.NEWS_API_KEY,
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                "https://newsapi.org/v2/everything",
                params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [
                    {
                        "title": a["title"],
                        "source": a["source"]["name"],
                        "published_at": a["publishedAt"],
                        "description": a.get("description", ""),
                        "url": a["url"],
                    }
                    for a in data.get("articles", [])
                ]
        except Exception as e:
            logger.error(f"News fetch failed for {company_name}: {e}")
            return []
