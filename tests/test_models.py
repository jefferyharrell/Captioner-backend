from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Photo


@pytest.fixture
def in_memory_db() -> Generator[Session, None, None]:
    """Create a new database and session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # No explicit teardown needed; in-memory DB is discarded

def test_photo_table_schema(in_memory_db: Session) -> None:
    # Ensure the table exists and columns are as expected
    inspector = inspect(in_memory_db.get_bind())
    column_names = {col["name"] for col in inspector.get_columns("photos")}
    assert {"id", "hash", "filename", "caption"}.issubset(column_names)

def test_insert_and_query_photo(in_memory_db: Session) -> None:
    photo = Photo(hash="abc123", filename="foo.jpg", caption="A caption")
    in_memory_db.add(photo)
    in_memory_db.commit()
    found = in_memory_db.query(Photo).filter_by(hash="abc123").first()
    assert found is not None
    assert found.filename == "foo.jpg"
    assert found.caption == "A caption"

def test_unique_hash_constraint(in_memory_db: Session) -> None:
    photo1 = Photo(hash="dup", filename="bar.jpg")
    photo2 = Photo(hash="dup", filename="baz.jpg")
    in_memory_db.add(photo1)
    in_memory_db.commit()
    in_memory_db.add(photo2)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()

def test_nullable_caption(in_memory_db: Session) -> None:
    photo = Photo(hash="no_caption", filename="baz.jpg", caption=None)
    in_memory_db.add(photo)
    in_memory_db.commit()
    found = in_memory_db.query(Photo).filter_by(hash="no_caption").first()
    assert found is not None
    assert found.caption is None
