"""News collector — NewsAPI.org for press coverage."""

import logging
import aiohttp

from api_services.core.config import settings

logger = logging.getLogger(__name__)


class NewsCollector:
    BASE_URL = "https://newsapi.org/v2/everything"

    async def get_news(self, company_name: str, days: int = 90) -> list[dict]:
        """Fetch recent news articles about a company."""
        if not settings.NEWS_API_KEY:
            logger.warning("NEWS_API_KEY not set — skipping news collection")
            return []

        params = {
            "q": f'"{company_name}"',
            "language": "fr",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": settings.NEWS_API_KEY,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self.BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"NewsAPI returned {resp.status} for {company_name}")
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
