from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from db.session import Base


class Trend(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    topic = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    relevance_score = Column(Float, nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    niche_tags = Column(String(255), nullable=True)
