from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from telegram import Bot

from models.competitor import CompetitorPost


async def _send_message(text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    bot = Bot(token=token)
    await bot.send_message(chat_id=chat_id, text=text)


def _time_ago(value: datetime | None) -> str:
    if value is None:
        return "unknown"
    delta = datetime.now(tz=timezone.utc).replace(tzinfo=None) - value
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def send_new_post_alert(post: CompetitorPost) -> None:
    handle = post.competitor.instagram_handle if post.competitor else "unknown"
    post_kind = (post.post_type or "Post").title()
    caption = (post.caption or "").strip()
    preview = caption[:100] + ("..." if len(caption) > 100 else "")

    message = (
        f"🚨 New {post_kind} from @{handle}!\n"
        f"Caption: {preview or '[no caption]'}\n"
        f"Link: {post.post_url}\n"
        f"Posted: {_time_ago(post.posted_at)}"
    )

    try:
        asyncio.run(_send_message(message))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_send_message(message))
