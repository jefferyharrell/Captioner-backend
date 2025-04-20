import os

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.utils.jwt import create_access_token

router = APIRouter()

class LoginRequest(BaseModel):
    password: str

@router.post("/login", summary="Login", response_model=dict)
async def login(body: LoginRequest) -> JSONResponse:
    """
    Authenticate user by password and return a JWT access token if successful.
    """
    env_password = os.getenv("BACKEND_PASSWORD")
    if body.password == env_password:
        access_token = create_access_token({"sub": "user"})
        return JSONResponse(
            {"access_token": access_token, "token_type": "bearer"},
            status_code=status.HTTP_200_OK,
        )
    return JSONResponse(
        {"detail": "Invalid password"},
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
