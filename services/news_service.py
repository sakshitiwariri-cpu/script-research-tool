from __future__ import annotations

import os
from typing import Any

from newsapi import NewsApiClient

INDIA_CATEGORIES = ["technology", "business", "entertainment"]


def _map_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    for article in articles:
        mapped.append(
            {
                "headline": article.get("title"),
                "source": article.get("source", {}).get("name"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "description": article.get("description"),
            }
        )
    return mapped


def fetch_india_headlines() -> list[dict[str, Any]]:
    """Fetch top headlines for India and selected categories from NewsAPI."""
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        raise ValueError("NEWSAPI_KEY is not set")

    newsapi = NewsApiClient(api_key=api_key)

    all_articles: list[dict[str, Any]] = []
    general = newsapi.get_top_headlines(country="in", page_size=100)
    all_articles.extend(_map_articles(general.get("articles", [])))

    for category in INDIA_CATEGORIES:
        category_result = newsapi.get_top_headlines(country="in", category=category, page_size=100)
        for item in _map_articles(category_result.get("articles", [])):
            item["category"] = category
            all_articles.append(item)

    return all_articles
