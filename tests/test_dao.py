from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.dao import PhotoDAO
from app.database import Base


@pytest.fixture
def in_memory_db(request: pytest.FixtureRequest) -> Generator[Session, None, None]:
    db_url = f"sqlite:///file:memdb_dao_{request.node.name}?mode=memory&cache=shared&uri=true"  # type: ignore[attr-defined]
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_and_get_photo(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    created = dao.create(object_key="photos/dao.jpg", caption="DAO test")
    fetched = dao.get(created.id)
    assert fetched is not None
    assert fetched.object_key == "photos/dao.jpg"
    assert fetched.caption == "DAO test"


def test_list_photos(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    dao.create(object_key="photos/one.jpg")
    dao.create(object_key="photos/two.jpg")
    photos = dao.list()
    expected_photo_count = 2
    assert len(photos) == expected_photo_count
    object_keys = {p.object_key for p in photos}
    assert {"photos/one.jpg", "photos/two.jpg"}.issubset(object_keys)


def test_update_caption(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    created = dao.create(object_key="photos/three.jpg", caption=None)
    updated = dao.update_caption(created.id, "Updated caption")
    assert updated is not None
    assert updated.caption == "Updated caption"


def test_delete_photo(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    created = dao.create(object_key="photos/four.jpg")
    deleted = dao.delete(created.id)
    assert deleted is True
    assert dao.get(created.id) is None


def test_update_caption_not_found(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    result = dao.update_caption(9999, "nope")
    assert result is None


def test_delete_not_found(in_memory_db: Session) -> None:
    dao = PhotoDAO(in_memory_db)
    result = dao.delete(9999)
    assert result is False
