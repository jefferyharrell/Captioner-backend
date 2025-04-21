from collections.abc import Generator
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.utils.jwt import decode_access_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # noqa: B008
) -> dict[str, Any]:
    """
    Dependency to get the current user from a JWT bearer token.
    Raises 401 if the token is invalid or missing.
    """
    return decode_access_token(credentials.credentials)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session and closes it when done.
    This function creates a new database session and ensures it's properly
    closed when the request is complete, regardless of whether an exception
    occurs. It uses FastAPI's dependency injection system.
    Yields:
        Session: SQLAlchemy database session
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
