from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import Response
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models.user import UserRole

AUTH_COOKIE_NAME = "srq_access_token"
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_EXPIRES_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret or not secret.strip():
        raise RuntimeError("JWT_SECRET is not set")
    return secret


def _jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM)


def _expires_minutes() -> int:
    raw = os.getenv("JWT_EXPIRES_MINUTES")
    if not raw:
        return DEFAULT_EXPIRES_MINUTES
    try:
        value = int(raw)
        return value if value > 0 else DEFAULT_EXPIRES_MINUTES
    except ValueError:
        return DEFAULT_EXPIRES_MINUTES


def _cookie_secure() -> bool:
    raw = os.getenv("COOKIE_SECURE")
    if raw is None:
        env = os.getenv("ENV", "development").lower()
        return env in {"prod", "production"}
    return raw.lower() in {"1", "true", "yes", "on"}


def _cookie_samesite() -> Literal["lax", "strict", "none"]:
    value = os.getenv("COOKIE_SAMESITE", "lax").lower()
    if value == "strict":
        return "strict"
    if value == "none":
        return "none"
    return "lax"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def validate_auth_config() -> None:
    _jwt_secret()


def create_access_token(*, user_id: int, role: UserRole) -> str:
    expire_at = datetime.now(UTC) + timedelta(minutes=_expires_minutes())
    payload = {
        "sub": str(user_id),
        "role": str(role),
        "exp": int(expire_at.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm())


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    return payload


def set_auth_cookie(response: Response, token: str) -> None:
    max_age = _expires_minutes() * 60
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
        path="/",
    )
