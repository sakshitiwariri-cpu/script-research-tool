from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from db import SessionLocal
from models.competitor import Competitor, CompetitorPost
from services.instagram_monitor import fetch_recent_posts
from services.notification import send_new_post_alert

scheduler = BackgroundScheduler()


def check_competitors_for_new_posts() -> None:
    session = SessionLocal()
    try:
        competitors = session.query(Competitor).all()
        for competitor in competitors:
            posts = fetch_recent_posts(competitor.instagram_handle)
            existing_urls = {
                row[0]
                for row in session.query(CompetitorPost.post_url)
                .filter(CompetitorPost.competitor_id == competitor.id)
                .all()
            }

            for post in posts:
                if post.post_url in existing_urls:
                    continue

                new_post = CompetitorPost(
                    competitor_id=competitor.id,
                    post_url=post.post_url,
                    caption=post.caption,
                    post_type=post.post_type,
                    posted_at=post.timestamp,
                    is_new=True,
                )
                session.add(new_post)
                session.flush()
                session.refresh(new_post)
                send_new_post_alert(new_post)

            competitor.last_checked_at = datetime.utcnow()

        session.commit()
    finally:
        session.close()


def start_competitor_checker() -> None:
    if not scheduler.get_jobs():
        scheduler.add_job(check_competitors_for_new_posts, "interval", minutes=30, id="competitor-checker")
    if not scheduler.running:
        scheduler.start()


def stop_competitor_checker() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
