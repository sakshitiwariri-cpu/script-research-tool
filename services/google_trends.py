from __future__ import annotations

from typing import Any

from pytrends.request import TrendReq


class GoogleTrendsService:
    """Fetches Google trending searches for India using pytrends."""

    def __init__(self, hl: str = "en-IN", tz: int = 330) -> None:
        self.client = TrendReq(hl=hl, tz=tz)

    def fetch_daily_trending_searches(self) -> list[dict[str, Any]]:
        """
        Returns daily trending topics for India.

        Output shape:
        [
          {"topic": "...", "search_volume": "...|None"}
        ]
        """
        trends_df = self.client.realtime_trending_searches(pn="IN")

        results: list[dict[str, Any]] = []
        if "title" in trends_df.columns:
            for _, row in trends_df.iterrows():
                title_data = row.get("title")
                topic = title_data.get("query") if isinstance(title_data, dict) else str(title_data)
                results.append(
                    {
                        "topic": topic,
                        "search_volume": row.get("formattedTraffic"),
                    }
                )
        else:
            # Fallback for older pytrends behavior.
            fallback_df = self.client.trending_searches(pn="india")
            for _, row in fallback_df.iterrows():
                results.append({"topic": row.iloc[0], "search_volume": None})

        return results
