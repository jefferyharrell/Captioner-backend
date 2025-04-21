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
        "sqlite:///file:memdb_models?mode=memory&cache=shared&uri=true",
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
    assert {"id", "object_key", "description"}.issubset(column_names)

def test_insert_and_query_photo(in_memory_db: Session) -> None:
    photo = Photo(object_key="photos/foo.jpg", description="A description")
    in_memory_db.add(photo)
    in_memory_db.commit()
    found = in_memory_db.query(Photo).filter_by(object_key="photos/foo.jpg").first()
    assert found is not None
    assert found.object_key == "photos/foo.jpg"
    assert found.description == "A description"

def test_unique_object_key_constraint(in_memory_db: Session) -> None:
    photo1 = Photo(object_key="photos/bar.jpg")
    photo2 = Photo(object_key="photos/bar.jpg")
    in_memory_db.add(photo1)
    in_memory_db.commit()
    in_memory_db.add(photo2)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()

def test_nullable_description(in_memory_db: Session) -> None:
    photo = Photo(object_key="photos/baz.jpg", description=None)
    in_memory_db.add(photo)
    in_memory_db.commit()
    found = in_memory_db.query(Photo).filter_by(object_key="photos/baz.jpg").first()
    assert found is not None
    assert found.description is None
