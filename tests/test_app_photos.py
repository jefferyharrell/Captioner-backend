from typing import Never, NoReturn

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.dao import PhotoDAO
from app.database import Base
from app.deps import get_db
from app.main import app


def test_get_photos_returns_photo_ids() -> None:
    # Setup in-memory DB and override SessionLocal
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    # Override DB dependency
    app.dependency_overrides[get_db] = lambda: session
    # Seed two photos
    dao = PhotoDAO(session)
    photo1 = dao.create(object_key="foo.jpg", caption=None)
    photo2 = dao.create(object_key="bar.png", caption=None)
    client = TestClient(app)
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == [photo1.id, photo2.id]

def test_get_photos_empty() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == []

def test_get_photos_pagination() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    # Seed 10 photos
    dao = PhotoDAO(session)
    for i in range(10):
        dao.create(object_key=f"img_{i}.jpg", caption=None)
    client = TestClient(app)
    response = client.get("/photos?limit=5&offset=5")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == [6, 7, 8, 9, 10]

def test_get_photos_storage_error() -> None:
    # Simulate DB connection error
    class BoomError(Exception):
        pass
    def bad_session() -> NoReturn:
        error_msg: str = "db error"
        raise BoomError(error_msg)
    # Override DB dependency to simulate error
    app.dependency_overrides[get_db] = bad_session
    client = TestClient(app)
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data

# Tests for GET /photos/{id}
def test_get_photo_by_id_success() -> None:
    # Setup in-memory DB and override SessionLocal
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    # Seed two photos
    dao = PhotoDAO(session)
    photo1 = dao.create(object_key="foo.jpg", caption=None)
    photo2 = dao.create(object_key="bar.jpg", caption="Bar")
    client = TestClient(app)
    # Happy path for first photo
    response = client.get(f"/photos/{photo1.id}")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["id"] == photo1.id
    assert data["object_key"] == "foo.jpg"
    assert "caption" in data
    assert data["caption"] is None
    # Happy path for second photo (ensure line 68 is covered)
    response = client.get(f"/photos/{photo2.id}")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["id"] == photo2.id
    assert data["object_key"] == "bar.jpg"
    assert data["caption"] == "Bar"

def test_get_photo_by_id_not_found() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    response = client.get("/photos/1")
    assert response.status_code == HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Photo not found"

def test_get_photo_by_id_storage_error() -> None:
    class BoomError(Exception):
        pass
    def bad_session() -> NoReturn:
        error_msg: str = "db error"
        raise BoomError(error_msg)
    app.dependency_overrides[get_db] = bad_session
    client = TestClient(app)
    response = client.get("/photos/1")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data


def test_handle_db_errors_test_app_module() -> None:
    # Simulate an exception with __module__ containing 'test_app'
    class CustomTestAppError(Exception):
        __module__ = "test_app.custom"
    def bad_session() -> NoReturn:
        msg = "simulated test_app error"
        raise CustomTestAppError(msg)
    app.dependency_overrides[get_db] = bad_session
    client = TestClient(app)
    response = client.get("/photos/1")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data
    assert "simulated test_app error" in data["detail"]


def test_get_photo_by_id_generic_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch PhotoDAO.get to raise a generic exception
    class GenericError(Exception):
        pass
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )()
    app.dependency_overrides[get_db] = lambda: session
    dao = PhotoDAO(session)
    dao.create(object_key="foo.jpg", caption=None)
    def raise_generic_error(_self: PhotoDAO, _photo_id: int) -> Never:
        msg = "something went wrong!"
        raise GenericError(msg)
    monkeypatch.setattr(PhotoDAO, "get", raise_generic_error)
    client = TestClient(app)
    response = client.get("/photos/1")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "something went wrong!" in data["detail"]
