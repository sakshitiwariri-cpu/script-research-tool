from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    instagram_handle: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    posts: Mapped[list["CompetitorPost"]] = relationship(
        "CompetitorPost",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )


class CompetitorPost(Base):
    __tablename__ = "competitor_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    post_url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_new: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    competitor: Mapped[Competitor] = relationship("Competitor", back_populates="posts")
