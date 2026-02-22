from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from models.competitor import Competitor, CompetitorPost
from services.instagram_monitor import fetch_recent_posts
from services.notification import send_new_post_alert


scheduler = BackgroundScheduler(timezone="UTC")


def _save_new_posts(db: Session, competitor: Competitor, posts: list[dict]) -> list[CompetitorPost]:
    existing_urls = {
        row[0]
        for row in db.execute(
            select(CompetitorPost.post_url).where(CompetitorPost.competitor_id == competitor.id)
        )
    }

    new_posts: list[CompetitorPost] = []
    for payload in posts:
        if payload["post_url"] in existing_urls:
            continue

        post = CompetitorPost(
            competitor_id=competitor.id,
            post_url=payload["post_url"],
            caption=payload.get("caption"),
            post_type=payload.get("post_type"),
            posted_at=payload.get("timestamp"),
            is_new=True,
        )
        db.add(post)
        new_posts.append(post)

    competitor.last_checked_at = datetime.utcnow()
    db.commit()

    for post in new_posts:
        db.refresh(post)

    return new_posts


def run_competitor_check(session_factory: sessionmaker) -> None:
    with session_factory() as db:
        competitors = db.scalars(select(Competitor)).all()

        for competitor in competitors:
            posts = fetch_recent_posts(competitor.instagram_handle)
            new_posts = _save_new_posts(db, competitor, posts)
            for post in new_posts:
                post.competitor = competitor
                send_new_post_alert(post)


def start_competitor_checker(session_factory: sessionmaker) -> None:
    if scheduler.get_job("competitor-checker"):
        return

    scheduler.add_job(
        run_competitor_check,
        "interval",
        minutes=30,
        args=[session_factory],
        id="competitor-checker",
        replace_existing=True,
    )
    scheduler.start()
