import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.core.env  # noqa: F401
from app.core.auth import validate_auth_config  # noqa: E402
from app.core.logging import setup_logging  # noqa: E402
from app.db import db_smoke_test  # noqa: E402
from app.routers.admin import router as admin_router  # noqa: E402
from app.routers.admin_ingest_items import (
    router as admin_ingest_items_router,  # noqa: E402
)
from app.routers.admin_venues import router as admin_venues_router  # noqa: E402
from app.routers.auth import router as auth_router  # noqa: E402
from app.routers.events import router as events_router  # noqa: E402
from app.routers.venues import router as venues_router  # noqa: E402
from app.routers.weather import router as weather_router  # noqa: E402

# Configure logging before creating the app
setup_logging()
validate_auth_config()

app = FastAPI(title="SRQ Happenings API")

# CORS origins - support both local dev and Docker environments
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add any additional origins from environment variable (comma-separated)
extra_origins = os.getenv("CORS_ORIGINS", "")
if extra_origins:
    cors_origins.extend([origin.strip() for origin in extra_origins.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router)
app.include_router(weather_router)
app.include_router(venues_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_venues_router)
app.include_router(admin_ingest_items_router)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "api"}


@app.get("/api/db-health")
def db_health():
    return db_smoke_test()
