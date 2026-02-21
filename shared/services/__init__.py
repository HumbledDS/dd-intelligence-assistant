"""Shared services package — lean adapters for French data sources."""

from shared.services.dinum import (
    dinum_search,
    dinum_get_company,
    dinum_get_dirigeants,
    dinum_get_finances,
)
from shared.services.bodacc import bodacc_get_announcements
from shared.services.news import news_get_articles

__all__ = [
    "dinum_search",
    "dinum_get_company",
    "dinum_get_dirigeants",
    "dinum_get_finances",
    "bodacc_get_announcements",
    "news_get_articles",
]
