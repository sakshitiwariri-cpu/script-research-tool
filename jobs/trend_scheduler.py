from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from db.session import SessionLocal
from services.trend_aggregator import TrendAggregator


scheduler = BackgroundScheduler(timezone="UTC")


def run_trend_aggregation_job() -> None:
    db = SessionLocal()
    try:
        TrendAggregator(db).aggregate_and_store()
    finally:
        db.close()


def init_trend_scheduler(app: FastAPI) -> None:
    if not scheduler.get_job("trend-aggregation"):
        scheduler.add_job(
            run_trend_aggregation_job,
            trigger="interval",
            hours=4,
            id="trend-aggregation",
            replace_existing=True,
        )

    @app.on_event("startup")
    def _start_scheduler() -> None:
        if not scheduler.running:
            scheduler.start()

    @app.on_event("shutdown")
    def _stop_scheduler() -> None:
        if scheduler.running:
            scheduler.shutdown(wait=False)
