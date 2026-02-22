from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.trend import Trend
from services.google_trends import GoogleTrendsService
from services.news_service import NewsService
from services.reddit_service import RedditService


class TrendAggregator:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.google_service = GoogleTrendsService()
        self.news_service = NewsService()
        self.reddit_service = RedditService()

    @staticmethod
    def _normalize(text: str | None) -> str:
        return (text or "").strip().lower()

    def _dedupe(self, trends: Iterable[Trend]) -> list[Trend]:
        unique: dict[str, Trend] = {}
        for trend in trends:
            key = self._normalize(trend.topic)
            if key and key not in unique:
                unique[key] = trend
        return list(unique.values())

    def _collect(self) -> list[Trend]:
        now = datetime.now(timezone.utc)
        items: list[Trend] = []

        for item in self.google_service.fetch_daily_trending_searches():
            items.append(
                Trend(
                    source="google",
                    topic=item.get("topic"),
                    description=f"Search volume: {item.get('search_volume')}",
                    relevance_score=None,
                    fetched_at=now,
                    niche_tags="search",
                )
            )

        for item in self.news_service.fetch_top_headlines():
            items.append(
                Trend(
                    source="news",
                    topic=item.get("headline"),
                    description=item.get("description"),
                    url=item.get("url"),
                    relevance_score=None,
                    fetched_at=item.get("published_date") or now,
                    niche_tags=item.get("category"),
                )
            )

        for item in self.reddit_service.fetch_hot_posts():
            items.append(
                Trend(
                    source="reddit",
                    topic=item.get("title"),
                    description=f"Subreddit: r/{item.get('subreddit')}",
                    url=item.get("url"),
                    relevance_score=item.get("score"),
                    fetched_at=now,
                    niche_tags=item.get("subreddit"),
                )
            )

        return self._dedupe(items)

    def aggregate_and_store(self) -> list[Trend]:
        trends = self._collect()
        self.db.add_all(trends)
        self.db.commit()
        for trend in trends:
            self.db.refresh(trend)
        return trends
