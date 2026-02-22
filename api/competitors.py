from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import SessionLocal
from models.competitor import Competitor, CompetitorPost

router = APIRouter(prefix="/api/competitors", tags=["competitors"])


class CompetitorCreate(BaseModel):
    name: str
    instagram_handle: str


class CompetitorOut(BaseModel):
    id: int
    name: str
    instagram_handle: str
    added_at: datetime
    last_checked_at: datetime | None

    class Config:
        from_attributes = True


class CompetitorPostOut(BaseModel):
    id: int
    competitor_id: int
    post_url: str
    caption: str | None
    post_type: str | None
    posted_at: datetime | None
    detected_at: datetime
    is_new: bool

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=CompetitorOut, status_code=status.HTTP_201_CREATED)
def add_competitor(payload: CompetitorCreate, db: Session = Depends(get_db)):
    handle = payload.instagram_handle.lstrip("@").strip()
    existing = db.query(Competitor).filter(Competitor.instagram_handle == handle).first()
    if existing:
        raise HTTPException(status_code=409, detail="Competitor already exists")

    competitor = Competitor(name=payload.name, instagram_handle=handle)
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@router.get("", response_model=list[CompetitorOut])
def list_competitors(db: Session = Depends(get_db)):
    return db.query(Competitor).order_by(Competitor.added_at.desc()).all()


@router.get("/{competitor_id}/posts", response_model=list[CompetitorPostOut])
def get_competitor_posts(competitor_id: int, db: Session = Depends(get_db)):
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    return (
        db.query(CompetitorPost)
        .filter(CompetitorPost.competitor_id == competitor_id)
        .order_by(CompetitorPost.posted_at.desc().nullslast(), CompetitorPost.detected_at.desc())
        .all()
    )


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_competitor(competitor_id: int, db: Session = Depends(get_db)):
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    db.delete(competitor)
    db.commit()
    return None
