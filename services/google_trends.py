from __future__ import annotations

from typing import Any

from pytrends.request import TrendReq


def fetch_google_trends_india() -> list[dict[str, Any]]:
    """Fetch realtime trending searches for India using pytrends."""
    pytrends = TrendReq(hl="en-IN", tz=330)

    trends: list[dict[str, Any]] = []

    try:
        realtime_df = pytrends.realtime_trending_searches(pn="IN")
        for _, row in realtime_df.iterrows():
            trends.append(
                {
                    "topic": str(row.get("title", "")).strip(),
                    "search_volume": row.get("formattedTraffic"),
                    "description": row.get("entityNames"),
                    "url": row.get("image", {}).get("newsUrl") if isinstance(row.get("image"), dict) else None,
                }
            )
    except Exception:
        fallback_df = pytrends.trending_searches(pn="india")
        for _, row in fallback_df.iterrows():
            topic = str(row.iloc[0]).strip()
            trends.append(
                {
                    "topic": topic,
                    "search_volume": None,
                    "description": None,
                    "url": None,
                }
            )

    return [trend for trend in trends if trend.get("topic")]
