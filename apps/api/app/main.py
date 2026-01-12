from fastapi import FastAPI

from app.db import db_smoke_test

app = FastAPI(title="SRQ Happenings API")


@app.get("/api/health")
def health():
    return {"ok": True, "service": "api"}


@app.get("/api/db-health")
def db_health():
    return db_smoke_test()
