from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "apify/instagram-profile-scraper"


@dataclass
class InstagramPostData:
    post_url: str
    caption: str | None
    post_type: str | None
    timestamp: datetime | None
    likes_count: int | None
    views_count: int | None


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def fetch_recent_posts(instagram_handle: str, results_limit: int = 12) -> list[InstagramPostData]:
    api_key = os.getenv("APIFY_API_KEY")
    if not api_key:
        raise RuntimeError("APIFY_API_KEY is not set")

    endpoint = f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    payload = {
        "usernames": [instagram_handle.lstrip("@").strip()],
        "resultsLimit": results_limit,
        "resultsType": "posts",
        "searchType": "user",
    }

    response = requests.post(
        endpoint,
        params={"token": api_key, "clean": "true"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    items = response.json()

    posts: list[InstagramPostData] = []
    for item in items:
        post_url = item.get("url") or item.get("postUrl")
        if not post_url:
            continue
        posts.append(
            InstagramPostData(
                post_url=post_url,
                caption=item.get("caption"),
                post_type=item.get("type") or item.get("productType"),
                timestamp=_to_datetime(item.get("timestamp") or item.get("takenAtTimestamp")),
                likes_count=item.get("likesCount"),
                views_count=item.get("videoViewCount") or item.get("videoPlayCount"),
            )
        )

    return posts
