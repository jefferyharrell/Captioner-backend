from typing import Any

import pytest
from fastapi import APIRouter, Depends, status
from fastapi.testclient import TestClient

from app.deps import get_current_user
from app.main import HTTP_200_OK, app

client: TestClient = TestClient(app)


@pytest.fixture(autouse=True)
def set_password_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND_PASSWORD", "supersecret")
    monkeypatch.setenv("JWT_SECRET_KEY", "testsecret")


def test_login_success() -> None:
    client = TestClient(app)
    response = client.post("/login", json={"password": "supersecret"})
    assert response.status_code == HTTP_200_OK
    data: dict[str, Any] = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"  # noqa: S105


def test_protected_endpoint_requires_token() -> None:
    test_router = APIRouter()

    def protected_route() -> dict[str, Any]:
        return {"ok": True}

    test_router.add_api_route(
        "/protected",
        protected_route,
        methods=["GET"],
        dependencies=[Depends(get_current_user)],
    )

    app.include_router(test_router)
    test_client: TestClient = TestClient(app)

    # No token
    response = test_client.get("/protected")
    assert response.status_code in {
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    }

    # Invalid token
    response = test_client.get(
        "/protected", headers={"Authorization": "Bearer notatoken"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Valid token
    login_resp = test_client.post("/login", json={"password": "supersecret"})
    token: str = login_resp.json()["access_token"]
    response = test_client.get(
        "/protected", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"ok": True}


def test_login_failure() -> None:
    client = TestClient(app)
    response = client.post("/login", json={"password": "wrongpass"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == "Invalid password"
