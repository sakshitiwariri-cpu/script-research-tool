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
