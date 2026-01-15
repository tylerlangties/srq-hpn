from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.core.env  # noqa: F401
from app.db import db_smoke_test  # noqa: E402
from app.routers.events import router as events_router

app = FastAPI(title="SRQ Happenings API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "api"}


@app.get("/api/db-health")
def db_health():
    return db_smoke_test()
