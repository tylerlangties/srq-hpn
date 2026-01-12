import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def db_smoke_test() -> dict:
    with engine.connect() as conn:
        now = conn.execute(text("SELECT now()")).scalar_one()
    return {"db_ok": True, "now": str(now)}


def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
