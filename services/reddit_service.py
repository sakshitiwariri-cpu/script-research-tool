from __future__ import annotations

import os
from typing import Any

import praw

TARGET_SUBREDDITS = ["india", "indiainvestments", "bollywood", "technology"]


def _build_reddit_client() -> praw.Reddit:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "script-research-tool/1.0")

    if not client_id or not client_secret:
        raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set")

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def fetch_reddit_hot_posts(limit_per_subreddit: int = 25) -> list[dict[str, Any]]:
    """Fetch hot posts from selected subreddits."""
    reddit = _build_reddit_client()

    posts: list[dict[str, Any]] = []
    for subreddit_name in TARGET_SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.hot(limit=limit_per_subreddit):
            posts.append(
                {
                    "title": post.title,
                    "subreddit": subreddit_name,
                    "score": post.score,
                    "url": post.url,
                    "description": getattr(post, "selftext", None),
                }
            )

    return posts
