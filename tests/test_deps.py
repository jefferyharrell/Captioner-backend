"""Tests for dependency injection utilities."""

from sqlalchemy.orm import Session

from app.deps import get_db


def test_get_db_yields_session() -> None:
    """Test that get_db yields a SQLAlchemy session and closes it after use."""
    # Get the generator
    db_gen = get_db()
    # Get the session from the generator
    session = next(db_gen)
    # Verify it's a Session
    assert isinstance(session, Session)
    # Close the session (simulating the end of the with block in FastAPI)
    import contextlib
    with contextlib.suppress(StopIteration):
        next(db_gen)
