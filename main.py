from fastapi import FastAPI

from api.trends import router as trends_router
from db.session import Base, engine
from jobs.trend_scheduler import init_trend_scheduler
from models.trend import Trend  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Script Research Tool")
app.include_router(trends_router)
init_trend_scheduler(app)
