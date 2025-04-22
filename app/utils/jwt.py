"""
JWT utility functions for encoding and decoding tokens.
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError

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
    to_encode["exp"] = expire  # PyJWT handles timestamp conversion
    # PyJWT encode function
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)  # type: ignore[return-value] # Pyright expects bytes, but runtime gives str


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode a JWT token and return the claims dict. Raises 401 if invalid.
    """
    try:
        # PyJWT decode function with algorithm validation
        # Return directly to fix Ruff RET504 and TRY300
        return jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
    except (ExpiredSignatureError, InvalidTokenError, PyJWTError) as exc:
        # Catch specific PyJWT errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc
