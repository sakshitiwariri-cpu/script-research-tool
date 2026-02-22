from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from models.database import SessionLocal
from models.research import CompetitorPost, Trend
from services.instagram_service import fetch_new_instagram_posts
from services.telegram_service import send_telegram_notification
from services.trends_service import collect_all_trending_topics

scheduler = AsyncIOScheduler()


async def sync_trends() -> None:
    db: Session = SessionLocal()
    try:
        trends = collect_all_trending_topics()
        for source, topics in trends.items():
            for topic in topics:
                db.add(Trend(source=source, topic=topic))
        db.commit()
    finally:
        db.close()


async def monitor_competitors() -> None:
    db: Session = SessionLocal()
    try:
        new_posts = fetch_new_instagram_posts()
        for post in new_posts:
            exists = db.query(CompetitorPost).filter_by(post_id=post["post_id"]).first()
            if exists:
                continue

            db.add(
                CompetitorPost(
                    username=post["username"],
                    post_id=post["post_id"],
                    caption=post.get("caption"),
                    post_url=post.get("post_url"),
                )
            )
            await send_telegram_notification(
                f"New post from @{post['username']}: {post.get('post_url', 'link unavailable')}"
            )
        db.commit()
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(sync_trends, "interval", minutes=30, id="sync_trends", replace_existing=True)
    scheduler.add_job(
        monitor_competitors,
        "interval",
        minutes=5,
        id="monitor_competitors",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
