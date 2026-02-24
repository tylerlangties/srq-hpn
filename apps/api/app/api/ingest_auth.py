from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException, status


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization[7:].strip()
    return token or None


def require_ingest_token(authorization: str | None = Header(default=None)) -> str:
    expected_token = os.getenv("BIGTOP_INGEST_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingest bridge token is not configured",
        )

    provided_token = _extract_bearer_token(authorization)
    if not provided_token or not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ingest token",
        )

    return provided_token
