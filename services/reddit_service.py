from __future__ import annotations

import os
from typing import Any

import praw


class RedditService:
    SUBREDDITS = ["india", "indiainvestments", "bollywood", "technology"]

    def __init__(self) -> None:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "script-research-tool/1.0")

        if not client_id or not client_secret:
            raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are required.")

        self.client = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    def fetch_hot_posts(self, limit_per_subreddit: int = 20) -> list[dict[str, Any]]:
        posts: list[dict[str, Any]] = []
        for subreddit_name in self.SUBREDDITS:
            subreddit = self.client.subreddit(subreddit_name)
            for post in subreddit.hot(limit=limit_per_subreddit):
                posts.append(
                    {
                        "title": post.title,
                        "subreddit": subreddit_name,
                        "score": float(post.score),
                        "url": post.url,
                    }
                )
        return posts
