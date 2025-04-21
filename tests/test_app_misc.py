from fastapi.testclient import TestClient

from app.main import app

NOT_FOUND = 404


def test_app_instance_exists() -> None:
    assert app is not None


def test_root_returns_404() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == NOT_FOUND
