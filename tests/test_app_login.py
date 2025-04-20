import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import HTTP_200_OK, app


@pytest.fixture
def set_password_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND_PASSWORD", "supersecret")

@pytest.mark.usefixtures("set_password_env")
def test_login_success() -> None:
    client = TestClient(app)
    response = client.post("/login", json={"password": "supersecret"})
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["detail"] == "Login successful"

@pytest.mark.usefixtures("set_password_env")
def test_login_failure() -> None:
    client = TestClient(app)
    response = client.post("/login", json={"password": "wrongpass"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == "Invalid password"
