from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database import SessionLocal


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
