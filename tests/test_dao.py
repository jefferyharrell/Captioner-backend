from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.dao import PhotoDAO
from app.database import Base


@pytest.fixture

def in_memory_db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_create_and_get_photo(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    created = dao.create(hash_="dao123", filename="dao.jpg", caption="DAO test")
    fetched = dao.get(created.id)
    assert fetched is not None
    assert fetched.hash == "dao123"
    assert fetched.filename == "dao.jpg"
    assert fetched.caption == "DAO test"

def test_list_photos(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    dao.create(hash_="dao1", filename="one.jpg")
    dao.create(hash_="dao2", filename="two.jpg")
    photos = dao.list()
    expected_photo_count = 2
    assert len(photos) == expected_photo_count
    hashes = {p.hash for p in photos}
    assert {"dao1", "dao2"}.issubset(hashes)

def test_update_caption(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    created = dao.create(hash_="dao3", filename="three.jpg", caption=None)
    updated = dao.update_caption(created.id, "Updated caption")
    assert updated is not None
    assert updated.caption == "Updated caption"

def test_delete_photo(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    created = dao.create(hash_="dao4", filename="four.jpg")
    deleted = dao.delete(created.id)
    assert deleted is True
    assert dao.get(created.id) is None

def test_get_by_hash_not_found(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    result = dao.get_by_hash("notarealhash")
    assert result is None

def test_update_caption_not_found(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    result = dao.update_caption(9999, "nope")
    assert result is None

def test_delete_not_found(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    result = dao.delete(9999)
    assert result is False
