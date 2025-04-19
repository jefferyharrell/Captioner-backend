import pytest
from fastapi.testclient import TestClient

from app.main import app

HTTP_200_OK = 200
HTTP_500_INTERNAL_SERVER_ERROR = 500
NOT_FOUND = 404

def test_get_photos_returns_photo_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    class MockStorage:
        def list_photos(self) -> list[str]:
            return ["foo.jpg", "bar.png"]
    monkeypatch.setattr("app.main.get_storage_backend", lambda: MockStorage())
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert "photo_ids" in data
    assert data["photo_ids"] == ["foo.jpg", "bar.png"]

def test_get_photos_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    class MockStorage:
        def list_photos(self) -> list[str]:
            return []
    monkeypatch.setattr("app.main.get_storage_backend", lambda: MockStorage())
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == []

def test_get_photos_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    photos = [f"img_{i}.jpg" for i in range(10)]
    class MockStorage:
        def list_photos(self) -> list[str]:
            return photos
    monkeypatch.setattr("app.main.get_storage_backend", lambda: MockStorage())
    response = client.get("/photos?limit=5&offset=5")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["photo_ids"] == photos[5:10]

def test_get_photos_storage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    class BoomError(Exception):
        pass
    def fail() -> list[str]:
        raise BoomError
    class MockStorage:
        def list_photos(self) -> list[str]:
            return fail()
    monkeypatch.setattr("app.main.get_storage_backend", lambda: MockStorage())
    response = client.get("/photos?limit=2&offset=0")
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data
