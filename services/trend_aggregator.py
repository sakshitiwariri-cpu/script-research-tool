from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from models.trend import Trend
from services.google_trends import fetch_google_trends_india
from services.news_service import fetch_india_headlines
from services.reddit_service import fetch_reddit_hot_posts


def _normalized_topic(topic: str) -> str:
    return " ".join(topic.lower().split())


def aggregate_trends(db: Session) -> list[Trend]:
    """Fetch, deduplicate, and persist trends from all sources."""
    google_items = fetch_google_trends_india()
    news_items = fetch_india_headlines()
    reddit_items = fetch_reddit_hot_posts()

    seen_topics: set[str] = set()
    trend_models: list[Trend] = []
    now = datetime.utcnow()

    for item in google_items:
        topic = item.get("topic")
        if not topic:
            continue
        key = _normalized_topic(topic)
        if key in seen_topics:
            continue
        seen_topics.add(key)
        trend_models.append(
            Trend(
                source="google",
                topic=topic,
                description=item.get("description"),
                url=item.get("url"),
                relevance_score=None,
                fetched_at=now,
                niche_tags="search,india",
            )
        )

    for item in news_items:
        topic = item.get("headline")
        if not topic:
            continue
        key = _normalized_topic(topic)
        if key in seen_topics:
            continue
        seen_topics.add(key)
        trend_models.append(
            Trend(
                source="news",
                topic=topic,
                description=item.get("description") or item.get("source"),
                url=item.get("url"),
                relevance_score=None,
                fetched_at=now,
                niche_tags=f"news,{item.get('category', 'general')}",
            )
        )

    for item in reddit_items:
        topic = item.get("title")
        if not topic:
            continue
        key = _normalized_topic(topic)
        if key in seen_topics:
            continue
        seen_topics.add(key)
        trend_models.append(
            Trend(
                source="reddit",
                topic=topic,
                description=item.get("description") or item.get("subreddit"),
                url=item.get("url"),
                relevance_score=float(item.get("score")) if item.get("score") is not None else None,
                fetched_at=now,
                niche_tags=f"reddit,{item.get('subreddit')}",
            )
        )

    if trend_models:
        db.add_all(trend_models)
        db.commit()

    return trend_models
