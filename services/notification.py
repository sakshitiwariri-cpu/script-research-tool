from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from telegram import Bot

from models.competitor import CompetitorPost


def _format_time_ago(posted_at: datetime | None) -> str:
    if posted_at is None:
        return "unknown"

    now = datetime.now(timezone.utc)
    ts = posted_at if posted_at.tzinfo else posted_at.replace(tzinfo=timezone.utc)
    diff = now - ts

    minutes = int(diff.total_seconds() // 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def send_new_post_alert(post: CompetitorPost) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    handle = f"@{post.competitor.instagram_handle.lstrip('@')}" if post.competitor else "@unknown"
    post_type = (post.post_type or "Post").capitalize()
    caption = (post.caption or "").strip()
    caption_snippet = caption[:100] + ("..." if len(caption) > 100 else "")

    message = (
        f"🚨 New {post_type} from {handle}!\n"
        f"Caption: {caption_snippet or 'N/A'}\n"
        f"Link: {post.post_url}\n"
        f"Posted: {_format_time_ago(post.posted_at)}"
    )

    bot = Bot(token=token)
    asyncio.run(bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=False))
