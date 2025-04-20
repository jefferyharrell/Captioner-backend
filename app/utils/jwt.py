"""
JWT utility functions for encoding and decoding tokens.
"""
import os
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from authlib.jose import JoseError, jwt
from fastapi import HTTPException, status

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def get_secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        msg = "JWT_SECRET_KEY not set in environment"
        raise RuntimeError(msg)
    return secret


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = int(expire.timestamp())
    token = cast("str | bytes", jwt.encode({"alg": ALGORITHM}, to_encode, get_secret_key()))  # type: ignore[reportUnknownMemberType]  # noqa: E501
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return str(token)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode a JWT token and return the claims dict. Raises 401 if invalid.
    """
    try:
        claims = cast("Any", jwt.decode(token, get_secret_key()))  # type: ignore[reportUnknownMemberType]
        claims.validate()
    except JoseError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc
    return claims
