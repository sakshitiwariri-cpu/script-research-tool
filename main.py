from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.trends import router as trends_router
from core.database import Base, engine
from jobs.trend_scheduler import start_trend_scheduler, stop_trend_scheduler

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_trend_scheduler()
    try:
        yield
    finally:
        stop_trend_scheduler()


app = FastAPI(title="Script Research Tool", lifespan=lifespan)
app.include_router(trends_router)
