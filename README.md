# script-research-tool

FastAPI-based social media research tool scaffold.

## Project structure

- `api/` API routes and dashboard endpoint
- `services/` integrations for trends, Instagram monitoring, and Telegram alerts
- `models/` SQLite data models and database session setup
- `jobs/` APScheduler jobs for trend sync and competitor monitoring
- `main.py` FastAPI application entrypoint

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

The API is available at `http://localhost:8000` with docs at `/docs`.
