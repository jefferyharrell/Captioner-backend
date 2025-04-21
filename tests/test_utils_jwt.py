import pytest
from fastapi import HTTPException

from app.utils.jwt import create_access_token, decode_access_token, get_secret_key


def test_get_secret_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        get_secret_key()
    assert "JWT_SECRET_KEY not set in environment" in str(excinfo.value)


def test_create_and_decode_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "testkey")
    token = create_access_token({"sub": "user"})
    assert isinstance(token, str)
    claims = decode_access_token(token)
    assert claims.get("sub") == "user"


def test_decode_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "testkey")
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token("notatoken")
    from fastapi import status
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
