from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# Always load apps/api/.env
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

# LOAD ENV BEFORE THIS LINE
from app.db import db_smoke_test  # noqa: E402

app = FastAPI(title="SRQ Happenings API")


@app.get("/api/health")
def health():
    return {"ok": True, "service": "api"}


@app.get("/api/db-health")
def db_health():
    return db_smoke_test()
