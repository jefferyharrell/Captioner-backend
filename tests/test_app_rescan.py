
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

from app import main
from app.database import Base
from app.deps import get_db
from app.main import app

EXPECTED_NEW_PHOTOS = 3

def test_rescan_success(monkeypatch: pytest.MonkeyPatch) -> None:
    # Setup in-memory DB
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
    # Use dependency override instead of monkeypatching
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    class MockStorage:
        def list_photos(self) -> list[str]:
            return ["a.jpg", "b.png", "c.webp"]
    monkeypatch.setattr(main, "get_storage_backend", lambda: MockStorage())
    response = client.post("/rescan")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("num_new_photos") == EXPECTED_NEW_PHOTOS

def test_rescan_storage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    class BoomError(Exception):
        pass
    msg: str = "oops"
    def fail() -> list[str]:
        raise BoomError(msg)
    class MockStorage:
        def list_photos(self) -> list[str]:
            return fail()
    # Override both the DB dependency and the storage backend
    app.dependency_overrides[get_db] = lambda: None  # DB won't be used because of error
    monkeypatch.setattr(main, "get_storage_backend", lambda: MockStorage())
    response = client.post("/rescan")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data
