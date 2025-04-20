from typing import NoReturn

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main
from app.dao import PhotoDAO
from app.database import Base
from app.main import app

HTTP_200_OK = 200
HTTP_500_INTERNAL_SERVER_ERROR = 500
NOT_FOUND = 404

def test_get_photos_returns_photo_ids(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    # Seed two photos
    dao = PhotoDAO(session)
    photo1 = dao.create(object_key="foo.jpg", caption=None)
    photo2 = dao.create(object_key="bar.png", caption=None)
    client = TestClient(app)
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == [photo1.id, photo2.id]

def test_get_photos_empty(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    client = TestClient(app)
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == []

def test_get_photos_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    # Seed 10 photos
    dao = PhotoDAO(session)
    for i in range(10):
        dao.create(object_key=f"img_{i}.jpg", caption=None)
    client = TestClient(app)
    response = client.get("/photos?limit=5&offset=5")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == [6, 7, 8, 9, 10]

def test_get_photos_storage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate DB connection error
    class BoomError(Exception):
        pass
    def bad_session() -> NoReturn:
        error_msg: str = "db error"
        raise BoomError(error_msg)
    monkeypatch.setattr(main, "SessionLocal", bad_session)
    client = TestClient(app)
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data

# Tests for GET /photos/{id}
def test_get_photo_by_id_success(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    # Seed a photo
    dao = PhotoDAO(session)
    photo = dao.create(object_key="foo.jpg", caption=None)
    client = TestClient(app)
    response = client.get(f"/photos/{photo.id}")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["id"] == photo.id
    assert data["object_key"] == "foo.jpg"
    assert "caption" in data
    assert data["caption"] is None

def test_get_photo_by_id_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    client = TestClient(app)
    response = client.get("/photos/1")
    assert response.status_code == NOT_FOUND
    data = response.json()
    assert data["detail"] == "Photo not found"

def test_get_photo_by_id_storage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BoomError(Exception):
        pass
    def bad_session() -> NoReturn:
        error_msg: str = "db error"
        raise BoomError(error_msg)
    monkeypatch.setattr(main, "SessionLocal", bad_session)
    client = TestClient(app)
    response = client.get("/photos/1")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data
