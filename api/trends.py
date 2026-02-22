from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from models.trend import Trend

router = APIRouter(prefix="/api/trends", tags=["trends"])


class TrendResponse(BaseModel):
    id: int
    source: str
    topic: str
    description: str | None
    url: str | None
    relevance_score: float | None
    fetched_at: datetime
    niche_tags: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=list[TrendResponse])
def get_trends(source: str | None = Query(default=None), db: Session = Depends(get_db)):
    stmt = select(Trend)
    if source:
        stmt = stmt.where(Trend.source == source)
    stmt = stmt.order_by(Trend.fetched_at.desc())
    return db.execute(stmt).scalars().all()
