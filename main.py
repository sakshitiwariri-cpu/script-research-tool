
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from api.routes import router
from jobs.scheduler import start_scheduler, stop_scheduler
from models.database import Base, engine

load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "Social Media Research Tool"))
app.include_router(router, prefix="/api")


@app.on_event("startup")
async def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    stop_scheduler()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
=======

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

from fastapi import FastAPI

from api.competitors import router as competitors_router
from database import SessionLocal, engine
from jobs.competitor_checker import start_competitor_checker
from models.base import Base

app = FastAPI(title="Script Research Tool")
app.include_router(competitors_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    start_competitor_checker(SessionLocal)


