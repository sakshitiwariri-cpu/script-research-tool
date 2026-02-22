from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import get_db
from models.research import CompetitorPost, Trend

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict[str, object]:
    trends = db.query(Trend).order_by(Trend.captured_at.desc()).limit(50).all()
    competitor_posts = db.query(CompetitorPost).order_by(CompetitorPost.posted_at.desc()).limit(50).all()

    return {
        "trends": [
            {"source": trend.source, "topic": trend.topic, "captured_at": trend.captured_at.isoformat()}
            for trend in trends
        ],
        "competitor_posts": [
            {
                "username": post.username,
                "post_id": post.post_id,
                "caption": post.caption,
                "post_url": post.post_url,
                "posted_at": post.posted_at.isoformat(),
            }
            for post in competitor_posts
        ],
    }
