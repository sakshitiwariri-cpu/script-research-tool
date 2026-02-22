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
