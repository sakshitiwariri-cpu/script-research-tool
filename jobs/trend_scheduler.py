from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.database import SessionLocal
from services.trend_aggregator import aggregate_trends

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def _run_aggregation_job() -> None:
    db = SessionLocal()
    try:
        aggregate_trends(db)
        logger.info("Trend aggregation completed")
    except Exception as exc:
        logger.exception("Trend aggregation failed: %s", exc)
    finally:
        db.close()


def start_trend_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(_run_aggregation_job, "interval", hours=4, id="trend_aggregation", replace_existing=True)
    scheduler.start()


def stop_trend_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
