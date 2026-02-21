"""
Google News RSS adapter — free, no API key, no rate limit.
Replaces NewsAPI for press coverage.
"""

import logging
import asyncio
from datetime import datetime
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"


async def google_news_get_articles(
    company_name: str, max_results: int = 20
) -> list[dict[str, Any]]:
    """
    Fetch recent news articles about a company via Google News RSS.
    Free, unlimited, no API key required.
    Returns a list of {title, source, published_at, url, snippet}.
    """
    params = {
        "q": f'"{company_name}"',
        "hl": "fr",
        "gl": "FR",
        "ceid": "FR:fr",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                GOOGLE_NEWS_RSS,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"User-Agent": "DD-Intelligence-Assistant/2.1"},
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Google News RSS: HTTP {resp.status}")
                    return []
                xml_content = await resp.text()

        return _parse_rss(xml_content, max_results)

    except Exception as e:
        logger.error(f"Google News fetch failed for '{company_name}': {e}")
        return []


def _parse_rss(xml: str, max_results: int) -> list[dict]:
    """Parse Google News RSS XML without feedparser dependency."""
    import re

    articles = []
    items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)

    for item in items[:max_results]:
        title = _extract_tag(item, "title")
        link = _extract_tag(item, "link")
        pub_date = _extract_tag(item, "pubDate")
        source = _extract_tag(item, "source")
        description = _extract_tag(item, "description")

        # Strip HTML from description
        description = re.sub(r"<[^>]+>", "", description or "")

        articles.append(
            {
                "title": title or "Sans titre",
                "source": source or "Google News",
                "published_at": pub_date or "",
                "url": link or "",
                "snippet": description[:300] if description else "",
            }
        )

    return articles


def _extract_tag(text: str, tag: str) -> str:
    """Extract content between XML tags."""
    import re

    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        # Handle CDATA
        cdata = re.match(r"<!\[CDATA\[(.*?)\]\]>", content, re.DOTALL)
        return cdata.group(1).strip() if cdata else content
    return ""
