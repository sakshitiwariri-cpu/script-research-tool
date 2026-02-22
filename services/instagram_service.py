import os
from typing import Any


def get_competitor_usernames() -> list[str]:
    raw_competitors = os.getenv("INSTAGRAM_COMPETITORS", "")
    return [name.strip() for name in raw_competitors.split(",") if name.strip()]


def fetch_new_instagram_posts() -> list[dict[str, Any]]:
    """
    Placeholder for competitor post monitoring.

    In production, wire this up to the Instagram Graph API or a trusted data provider.
    """
    return [
        {
            "username": username,
            "post_id": f"{username}-latest",
            "caption": "New monitored post",
            "post_url": f"https://instagram.com/{username}/",
        }
        for username in get_competitor_usernames()
    ]
