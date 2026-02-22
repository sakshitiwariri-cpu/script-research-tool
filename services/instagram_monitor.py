from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests

APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "apify/instagram-profile-scraper"


class InstagramMonitorError(RuntimeError):
    pass


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).replace(tzinfo=None)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def fetch_recent_posts(instagram_handle: str, limit: int = 12) -> list[dict[str, Any]]:
    api_key = os.getenv("APIFY_API_KEY")
    if not api_key:
        raise InstagramMonitorError("APIFY_API_KEY environment variable is not set")

    actor_input = {
        "usernames": [instagram_handle.lstrip("@")],
        "resultsLimit": limit,
        "resultsType": "posts",
        "searchType": "user",
        "addParentData": False,
    }

    response = requests.post(
        f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/run-sync-get-dataset-items",
        params={"token": api_key, "clean": "true"},
        json=actor_input,
        timeout=60,
    )
    response.raise_for_status()

    items = response.json()
    posts: list[dict[str, Any]] = []
    for item in items:
        post_url = item.get("url") or item.get("postUrl")
        if not post_url:
            continue

        likes_count = item.get("likesCount") or item.get("likes")
        views_count = item.get("videoViewCount") or item.get("videoPlayCount") or item.get("viewsCount")
        post_type = item.get("type") or item.get("productType")
        timestamp = _parse_timestamp(item.get("timestamp") or item.get("takenAt") or item.get("createdAt"))

        posts.append(
            {
                "post_url": post_url,
                "caption": item.get("caption") or item.get("captionText") or "",
                "post_type": post_type,
                "timestamp": timestamp,
                "likes_count": likes_count,
                "views_count": views_count,
            }
        )

    return posts
