from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests


class NewsService:
    BASE_URL = "https://newsapi.org/v2/top-headlines"
    CATEGORIES = ["technology", "business", "entertainment"]

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("NEWSAPI_KEY")
        if not self.api_key:
            raise ValueError("NEWSAPI_KEY is not set.")

    def _fetch(self, category: str | None = None) -> list[dict[str, Any]]:
        params = {"apiKey": self.api_key, "country": "in", "pageSize": 50}
        if category:
            params["category"] = category

        response = requests.get(self.BASE_URL, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()

        articles = payload.get("articles", [])
        items: list[dict[str, Any]] = []
        for article in articles:
            items.append(
                {
                    "headline": article.get("title"),
                    "source": (article.get("source") or {}).get("name"),
                    "url": article.get("url"),
                    "published_date": self._parse_date(article.get("publishedAt")),
                    "description": article.get("description"),
                    "category": category or "general",
                }
            )
        return items

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def fetch_top_headlines(self) -> list[dict[str, Any]]:
        results = self._fetch()
        for category in self.CATEGORIES:
            results.extend(self._fetch(category=category))
        return results
