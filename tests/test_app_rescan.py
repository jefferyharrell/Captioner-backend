import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main
from app.database import Base
from app.main import app

HTTP_200_OK = 200
HTTP_500_INTERNAL_SERVER_ERROR = 500
EXPECTED_NEW_PHOTOS = 3

def test_rescan_success(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(main, "get_storage_backend", lambda: MockStorage())
    response = client.post("/rescan")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data
