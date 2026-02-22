import os
from typing import Any

import praw
from newsapi import NewsApiClient
from pytrends.request import TrendReq


def fetch_google_trends() -> list[str]:
    pytrends = TrendReq(hl="en-US", tz=int(os.getenv("GOOGLE_TRENDS_TZ", "360")))
    trending = pytrends.trending_searches(pn=os.getenv("GOOGLE_TRENDS_GEO", "united_states"))
    return trending[0].tolist()[:10]


def fetch_newsapi_trends() -> list[str]:
    api_key = os.getenv("NEWSAPI_KEY", "")
    if not api_key:
        return []

    news_client = NewsApiClient(api_key=api_key)
    headlines = news_client.get_top_headlines(language="en", page_size=10)
    return [article["title"] for article in headlines.get("articles", []) if article.get("title")]


def fetch_reddit_trends() -> list[str]:
    reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "social-research-tool")

    if not reddit_client_id or not reddit_client_secret:
        return []

    reddit = praw.Reddit(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent,
    )
    return [submission.title for submission in reddit.subreddit("all").hot(limit=10)]


def collect_all_trending_topics() -> dict[str, list[str]]:
    return {
        "google_trends": fetch_google_trends(),
        "newsapi": fetch_newsapi_trends(),
        "reddit": fetch_reddit_trends(),
    }
